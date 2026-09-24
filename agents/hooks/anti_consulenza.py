#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anti_consulenza.py - hook PostToolUse (matcher Write|Edit).

A che serve
-----------
Secondo strato della difesa prevista da agents/ARCHITETTURA.md par. "Perche'
questa forma", punto 3: il `fidelity-validator` giudica in modo semantico in
Fase A, questo hook controlla in modo deterministico a runtime.

Cerca formule da consulenza finanziaria (G-04: nessun agente da' consigli
professionali; spiega cosa significa una cosa, non dice cosa fare) nei file
scritti sotto `agents/state/` e `app/`, cioe' dove nasce il testo che finisce
davanti alla persona.

**Segnala e basta: non blocca mai.** Il giudizio su una frase e' linguistico e
un falso positivo che ferma il lavoro costerebbe piu' di quanto rende. La
decisione resta a chi scrive, che pero' la prende informato.

Contratto con Claude Code
-------------------------
- stdin : JSON con `tool_name`, `tool_input`, `hook_event_name`, `cwd`.
- stdout: JSON con `systemMessage` (per la persona) e
          `hookSpecificOutput.additionalContext` (per il modello).
          Mai `decision: "block"`.
- exit  : sempre 0.

Pattern
-------
In `agents/hooks/frasi-vietate.txt`, non nel codice: la lista cresce durante
la gara e aggiornarla non deve significare toccare un programma. Formato di
ogni riga:  <regex> => <motivo breve>

Prova manuale: vedi agents/hooks/README.md.
"""

from __future__ import annotations

import json
import os
import re
import sys

# Solo qui dentro nasce testo destinato alla persona. Il resto del repo
# (documentazione, file degli agenti, questi hook) parla *di* consulenza per
# vietarla: scandirlo produrrebbe solo falsi positivi.
AREE_SORVEGLIATE = ("agents/state/", "app/")

# Il file dei pattern, accanto a questo script.
FILE_PATTERN = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "frasi-vietate.txt")

SEPARATORE = "=>"

# Limiti espliciti: un hook non deve mai diventare il passo lento della
# sessione ne' caricarsi un file enorme in memoria.
MAX_BYTE_FILE = 400_000      # oltre questa soglia si legge solo l'inizio
MAX_PATTERN = 200            # pattern oltre i quali si smette di leggere
MAX_SEGNALAZIONI = 10        # righe citate nel messaggio

CHIAVI_PERCORSO = ("file_path", "notebook_path", "path")


def esci(payload: dict | None = None) -> None:
    """Stampa l'eventuale payload JSON e termina sempre con exit 0."""
    if payload:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.exit(0)


def radice_progetto(dati: dict) -> str:
    for candidato in (os.environ.get("CLAUDE_PROJECT_DIR"),
                      dati.get("cwd"),
                      os.getcwd()):
        if candidato:
            return os.path.abspath(candidato)
    return os.getcwd()


def percorso_relativo(bersaglio: str, radice: str) -> str | None:
    assoluto = os.path.abspath(os.path.join(radice, bersaglio))
    try:
        rel = os.path.relpath(assoluto, radice)
    except ValueError:
        return None
    if rel.startswith(".."):
        return None
    return rel.replace(os.sep, "/").lower()


def carica_pattern() -> tuple[list[tuple[re.Pattern, str]], list[str]]:
    """Legge frasi-vietate.txt. Restituisce (pattern validi, problemi).

    Una riga malformata non fa fallire l'hook: viene elencata fra i problemi
    e si continua con le altre. Un controllo che si spegne al primo refuso
    non e' un controllo.
    """
    pattern: list[tuple[re.Pattern, str]] = []
    problemi: list[str] = []
    try:
        with open(FILE_PATTERN, "r", encoding="utf-8", errors="replace") as f:
            righe = f.readlines()
    except OSError as errore:
        return [], ["file dei pattern non leggibile (%s)" % errore]

    for numero, riga in enumerate(righe, start=1):
        testo = riga.strip()
        if not testo or testo.startswith("#"):
            continue
        if len(pattern) >= MAX_PATTERN:
            problemi.append("oltre %d pattern: righe successive ignorate"
                            % MAX_PATTERN)
            break
        if SEPARATORE in testo:
            grezzo, motivo = testo.split(SEPARATORE, 1)
        else:
            grezzo, motivo = testo, "formula da consulenza"
        try:
            pattern.append((re.compile(grezzo.strip(), re.IGNORECASE),
                            motivo.strip()))
        except re.error as errore:
            problemi.append("riga %d: regex non valida (%s)" % (numero, errore))
    return pattern, problemi


def main() -> None:
    try:
        grezzo = sys.stdin.read()
        dati = json.loads(grezzo) if grezzo.strip() else {}
    except Exception:
        esci()  # input illeggibile: un hook di sola segnalazione tace

    if not isinstance(dati, dict):
        esci()
    entrata = dati.get("tool_input") or {}
    if not isinstance(entrata, dict):
        esci()
    bersaglio = next((entrata[k] for k in CHIAVI_PERCORSO
                      if isinstance(entrata.get(k), str) and entrata[k]), None)
    if not bersaglio:
        esci()

    radice = radice_progetto(dati)
    rel = percorso_relativo(bersaglio, radice)
    if rel is None or not rel.startswith(AREE_SORVEGLIATE):
        esci()  # fuori dalle aree sorvegliate: nessun controllo, nessun costo

    pattern, problemi = carica_pattern()

    if not pattern:
        # Degradato, non muto: se il controllo non e' attivo bisogna saperlo.
        esci({"systemMessage":
              "anti_consulenza: nessun pattern caricato da "
              "agents/hooks/frasi-vietate.txt, controllo G-04 non eseguito "
              "su `%s`. %s" % (rel, "; ".join(problemi) or "file vuoto")})

    try:
        with open(os.path.join(radice, rel), "r",
                  encoding="utf-8", errors="replace") as f:
            contenuto = f.read(MAX_BYTE_FILE)
    except OSError:
        esci()  # il file puo' essere gia' sparito: non e' un problema nostro

    trovati: list[str] = []
    for numero, riga in enumerate(contenuto.splitlines(), start=1):
        if len(trovati) >= MAX_SEGNALAZIONI:
            trovati.append("... altre occorrenze non elencate "
                           "(tetto: %d)" % MAX_SEGNALAZIONI)
            break
        for regola, motivo in pattern:
            trovato = regola.search(riga)
            if trovato:
                trovati.append("riga %d: \"%s\" -> %s"
                               % (numero, trovato.group(0).strip(), motivo))
                break  # una segnalazione per riga: basta a farla riscrivere

    if not trovati and not problemi:
        esci()  # caso normale: nessun output, nessun rumore

    quante = ("c'e' 1 formula che somiglia" if len(trovati) == 1
              else "ci sono %d formule che somigliano" % len(trovati))
    testa = ("anti_consulenza (G-04): in `%s` %s a consulenza "
             "finanziaria. Il sistema orienta e spiega, non dice cosa fare: "
             "riformula in descrizione (\"la misura prevede X\") e rimanda a "
             "CAF o commercialista per la decisione. Avviso, non blocco: "
             "valuta tu." % (rel, quante)) if trovati else \
            ("anti_consulenza: controllo G-04 eseguito su `%s` in modo "
             "parziale." % rel)

    corpo = [testa]
    corpo.extend("  - " + t for t in trovati)
    if problemi:
        corpo.append("  problemi nel file dei pattern: " + "; ".join(problemi))
    messaggio = "\n".join(corpo)

    esci({
        "systemMessage": messaggio,
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": messaggio,
        },
    })


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as errore:
        sys.stderr.write("anti_consulenza: errore ignorato (%s)\n" % errore)
        sys.exit(0)
