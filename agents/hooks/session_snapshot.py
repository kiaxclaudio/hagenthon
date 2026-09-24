#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
session_snapshot.py - hook Stop.

A che serve
-----------
Alla fine di ogni sessione scrive `docs/validation/session-<timestamp>.json`:
un riassunto minimo di cosa e' successo. E' l'evidenza di validazione chiesta
dalla consegna (deliverable 03) prodotta dal sistema stesso, invece che
raccolta a mano alla fine quando non c'e' piu' tempo.

Riassunto minimo, non registro completo: la trascrizione resta dove sta
(G-12, lo stato non vive nel contesto). Qui finiscono solo i fatti che
servono a dimostrare che il sistema ha girato: quando, quali file di stato
esistevano, quali agenti e strumenti sono stati usati.

Contratto con Claude Code
-------------------------
- stdin : JSON con `session_id`, `transcript_path`, `cwd`, `hook_event_name`,
          `stop_hook_active`.
- stdout: niente (o un `systemMessage` breve).
- exit  : sempre 0, senza eccezioni. Un hook Stop che fallisce fa fallire la
          chiusura della sessione: qui ogni operazione e' protetta e
          l'eventuale errore finisce dentro lo snapshot come campo `errori`,
          non come codice di uscita.

Non emette mai `decision: "block"`: bloccare su Stop rimette in moto il
modello e puo' generare un ciclo. Per la stessa ragione rispetta il flag
`stop_hook_active` e in quel caso non fa nulla.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

CARTELLA_USCITA = os.path.join("docs", "validation")

# Tetti espliciti: lo snapshot deve costare pochi millisecondi anche a fine
# di una sessione lunga.
MAX_RIGHE_TRANSCRIPT = 20_000
MAX_BYTE_TRANSCRIPT = 8_000_000
MAX_VOCI_ELENCO = 25


def radice_progetto(dati: dict) -> str:
    for candidato in (os.environ.get("CLAUDE_PROJECT_DIR"),
                      dati.get("cwd"),
                      os.getcwd()):
        if candidato:
            return os.path.abspath(candidato)
    return os.getcwd()


def stato_esternalizzato(radice: str, errori: list[str]) -> list[dict]:
    """Inventario di agents/state/*.json: nomi, dimensioni, ultima modifica.

    Il contenuto NON viene copiato: puo' contenere un profilo, e G-17 vieta
    dati personali reali nei file committati. Qui serve solo la prova che lo
    stato e' stato prodotto e quanto pesa.
    """
    cartella = os.path.join(radice, "agents", "state")
    voci: list[dict] = []
    try:
        nomi = sorted(os.listdir(cartella))
    except OSError:
        return voci
    for nome in nomi[:MAX_VOCI_ELENCO]:
        if not nome.endswith(".json"):
            continue
        percorso = os.path.join(cartella, nome)
        try:
            st = os.stat(percorso)
            voci.append({
                "file": "agents/state/" + nome,
                "byte": st.st_size,
                "modificato_utc": datetime.fromtimestamp(
                    st.st_mtime, timezone.utc).isoformat(timespec="seconds"),
            })
        except OSError as errore:
            errori.append("stato %s: %s" % (nome, errore))
    return voci


def riassunto_transcript(percorso: str | None, errori: list[str]) -> dict:
    """Conteggi dalla trascrizione JSONL: messaggi, strumenti, sub-agenti.

    Lettura a righe con tetto: una trascrizione lunga non deve mai diventare
    il costo dominante della chiusura di sessione.
    """
    riassunto: dict = {"disponibile": False}
    if not percorso:
        return riassunto
    try:
        if os.path.getsize(percorso) > MAX_BYTE_TRANSCRIPT:
            riassunto["troncato"] = True
    except OSError:
        return riassunto

    strumenti: dict[str, int] = {}
    sottoagenti: dict[str, int] = {}
    messaggi = 0
    righe_lette = 0
    try:
        with open(percorso, "r", encoding="utf-8", errors="replace") as f:
            for riga in f:
                righe_lette += 1
                if righe_lette > MAX_RIGHE_TRANSCRIPT:
                    riassunto["troncato"] = True
                    break
                riga = riga.strip()
                if not riga:
                    continue
                try:
                    voce = json.loads(riga)
                except ValueError:
                    continue
                if not isinstance(voce, dict):
                    continue
                if voce.get("type") in ("user", "assistant"):
                    messaggi += 1
                messaggio = voce.get("message")
                if not isinstance(messaggio, dict):
                    continue
                contenuto = messaggio.get("content")
                if not isinstance(contenuto, list):
                    continue
                for blocco in contenuto:
                    if not isinstance(blocco, dict):
                        continue
                    if blocco.get("type") != "tool_use":
                        continue
                    nome = str(blocco.get("name") or "?")
                    strumenti[nome] = strumenti.get(nome, 0) + 1
                    if nome in ("Task", "Agent"):
                        ingresso = blocco.get("input") or {}
                        if isinstance(ingresso, dict):
                            tipo = str(ingresso.get("subagent_type")
                                       or ingresso.get("description") or "?")
                            sottoagenti[tipo] = sottoagenti.get(tipo, 0) + 1
    except OSError as errore:
        errori.append("transcript: %s" % errore)
        return riassunto

    riassunto.update({
        "disponibile": True,
        "righe": righe_lette,
        "messaggi": messaggi,
        "strumenti_usati": dict(sorted(strumenti.items(),
                                       key=lambda kv: -kv[1])[:MAX_VOCI_ELENCO]),
        "sub_agenti_invocati": dict(sorted(sottoagenti.items(),
                                           key=lambda kv: -kv[1])[:MAX_VOCI_ELENCO]),
    })
    return riassunto


def main() -> None:
    errori: list[str] = []
    try:
        grezzo = sys.stdin.read()
        dati = json.loads(grezzo) if grezzo.strip() else {}
    except Exception as errore:
        dati = {}
        errori.append("input hook non interpretabile: %s" % errore)
    if not isinstance(dati, dict):
        dati = {}

    # Protezione anti-ciclo: se siamo qui perche' un hook Stop precedente ha
    # rimesso in moto il modello, non si scrive un secondo snapshot.
    if dati.get("stop_hook_active"):
        sys.exit(0)

    radice = radice_progetto(dati)
    adesso = datetime.now(timezone.utc)

    snapshot = {
        "schema": "hagenthon/session-snapshot/1",
        "generato_da": "agents/hooks/session_snapshot.py (hook Stop)",
        "timestamp_utc": adesso.isoformat(timespec="seconds"),
        "session_id": dati.get("session_id"),
        "evento": dati.get("hook_event_name", "Stop"),
        "progetto": os.path.basename(radice),
        "team_role": None,
        "stato_esternalizzato": [],
        "sessione": {},
        "errori": errori,
    }

    try:
        with open(os.path.join(radice, ".team-role"), "r",
                  encoding="utf-8", errors="replace") as f:
            snapshot["team_role"] = f.read(64).strip().lower() or None
    except OSError:
        pass  # assente: lo snapshot lo registra come null, non e' un errore

    snapshot["stato_esternalizzato"] = stato_esternalizzato(radice, errori)
    snapshot["sessione"] = riassunto_transcript(dati.get("transcript_path"),
                                                errori)

    nome = "session-%s.json" % adesso.strftime("%Y%m%dT%H%M%SZ")
    destinazione = os.path.join(radice, CARTELLA_USCITA, nome)
    try:
        os.makedirs(os.path.dirname(destinazione), exist_ok=True)
        with open(destinazione, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except OSError as errore:
        # Non si puo' scrivere l'evidenza: lo si dice, non si fa fallire
        # la chiusura della sessione.
        sys.stdout.write(json.dumps(
            {"systemMessage": "session_snapshot: snapshot non scritto (%s)"
                              % errore},
            ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as errore:
        sys.stderr.write("session_snapshot: errore ignorato (%s)\n" % errore)
        sys.exit(0)
