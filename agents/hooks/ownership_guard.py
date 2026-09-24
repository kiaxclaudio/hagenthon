#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ownership_guard.py - hook PreToolUse (matcher Write|Edit).

A che serve
-----------
Rende eseguibile la mappa di proprieta' dei file di docs/COLLABORAZIONE.md
(sintesi in CLAUDE.md, paragrafo 2). Due sessioni Claude Code lavorano sullo
stesso branch `main` senza pull request: i conflitti si evitano per
costruzione, non si risolvono. Questo hook trasforma quella convenzione in un
controllo deterministico eseguito prima di ogni scrittura.

Contratto con Claude Code
-------------------------
- stdin : JSON con `tool_name`, `tool_input`, `hook_event_name`, `cwd`.
- stdout: JSON. Per negare la scrittura:
          {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                  "permissionDecision": "deny",
                                  "permissionDecisionReason": "..."}}
- exit  : sempre 0. Una guardia che va in errore non deve mai fermare il
          lavoro: in caso di eccezione lascia passare e lo dice su stderr.

Non emette mai `permissionDecision: "allow"`. Un "allow" scavalca il normale
flusso dei permessi, e una guardia anti-conflitto non ha titolo per
autorizzare nulla: puo' solo negare, o tacere.

Ruolo
-----
Letto da `.team-role` nella radice del progetto (contenuto: `davide` oppure
`chiara`). Il file non e' versionato (sta in .gitignore): e' la sola cosa che
cambia fra le due macchine.
Se `.team-role` manca, l'hook NON blocca nulla e lo dichiara in un
systemMessage quando la scrittura tocca un'area contesa.

Prova manuale (una riga sola su stdin):
    echo {"hook_event_name":"PreToolUse","tool_name":"Write", ...} | python agents/hooks/ownership_guard.py
Esempi completi in agents/hooks/README.md.
"""

from __future__ import annotations

import json
import os
import sys

# --------------------------------------------------------------------------
# La mappa di proprieta'. Unica fonte: docs/COLLABORAZIONE.md paragrafo 2.
# Prefissi in minuscolo, separatore `/`. Un prefisso che finisce con `/` e'
# una cartella, altrimenti e' un file singolo.
# --------------------------------------------------------------------------
PROPRIETA: list[tuple[str, str]] = [
    ("agents/", "davide"),
    ("docs/process-note.md", "davide"),
    ("docs/status-davide.md", "davide"),
    ("app/", "davide"),
    ("presentation/", "davide"),
    ("docs/ux/", "davide"),
    ("docs/validation/", "chiara"),
    ("docs/status-chiara.md", "chiara"),
    # Aree condivise: si scrivono, ma avvisando l'altra persona.
    # Vince il prefisso piu' lungo, quindi agents/schemas/ batte agents/
    # indipendentemente dall'ordine di questo elenco.
    ("agents/schemas/", "condiviso"),
    ("claude.md", "condiviso"),
    ("readme.md", "condiviso"),
]

# Dove ognuno scrive le richieste di modifica sui file altrui.
FILE_STATUS = {
    "davide": "docs/status-davide.md",
    "chiara": "docs/status-chiara.md",
}

RUOLI_NOTI = set(FILE_STATUS)

# Chiavi di `tool_input` che possono contenere il percorso bersaglio.
# Write ed Edit usano file_path; NotebookEdit usa notebook_path ed e'
# intercettato dallo stesso matcher regex "Write|Edit".
CHIAVI_PERCORSO = ("file_path", "notebook_path", "path")


def esci(payload: dict | None = None) -> None:
    """Stampa l'eventuale payload JSON e termina sempre con exit 0."""
    if payload:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.exit(0)


def nega(motivo: str) -> None:
    esci({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": motivo,
    }})


def avvisa(messaggio: str) -> None:
    """Avviso all'utente senza alcuna decisione: la scrittura prosegue."""
    esci({"systemMessage": messaggio})


def radice_progetto(dati: dict) -> str:
    """Radice del repository: variabile di Claude Code, poi cwd dell'evento."""
    for candidato in (os.environ.get("CLAUDE_PROJECT_DIR"),
                      dati.get("cwd"),
                      os.getcwd()):
        if candidato:
            return os.path.abspath(candidato)
    return os.getcwd()


def percorso_relativo(bersaglio: str, radice: str) -> str | None:
    """Percorso relativo alla radice, in minuscolo e con separatore `/`.

    None se il file sta fuori dal repository: la mappa di proprieta' vale
    dentro il progetto, fuori non abbiamo titolo per decidere.
    """
    assoluto = os.path.abspath(os.path.join(radice, bersaglio))
    try:
        rel = os.path.relpath(assoluto, radice)
    except ValueError:  # unita' disco diverse su Windows
        return None
    if rel.startswith(".."):
        return None
    return rel.replace(os.sep, "/").lower()


def proprietario(rel: str) -> str | None:
    """Proprietario dell'area che contiene il file, o None se area libera."""
    migliore: tuple[int, str] | None = None
    for prefisso, chi in PROPRIETA:
        if prefisso.endswith("/"):
            corrisponde = rel.startswith(prefisso)
        else:
            corrisponde = rel == prefisso
        if corrisponde and (migliore is None or len(prefisso) > migliore[0]):
            migliore = (len(prefisso), chi)
    return migliore[1] if migliore else None


def leggi_ruolo(radice: str) -> str | None:
    """Ruolo dichiarato in `.team-role`. None se assente o illeggibile."""
    percorso = os.path.join(radice, ".team-role")
    try:
        with open(percorso, "r", encoding="utf-8", errors="replace") as f:
            valore = f.read(64).strip().lower()
    except OSError:
        return None
    return valore or None


def main() -> None:
    try:
        grezzo = sys.stdin.read()
    except Exception:
        esci()
    try:
        dati = json.loads(grezzo) if grezzo.strip() else {}
    except (ValueError, TypeError):
        # Input non interpretabile: non e' colpa di chi scrive. Si lascia
        # passare e lo si dichiara, invece di bloccare alla cieca.
        avvisa("ownership_guard: input dell'hook non interpretabile, "
               "guardia di proprieta' non applicata a questa scrittura.")

    if not isinstance(dati, dict):
        esci()

    entrata = dati.get("tool_input") or {}
    if not isinstance(entrata, dict):
        esci()
    bersaglio = next((entrata[k] for k in CHIAVI_PERCORSO
                      if isinstance(entrata.get(k), str) and entrata[k]), None)
    if not bersaglio:
        esci()  # nessun percorso da giudicare

    radice = radice_progetto(dati)
    rel = percorso_relativo(bersaglio, radice)
    if rel is None:
        esci()  # fuori dal repository: non e' materia di questa mappa

    chi = proprietario(rel)
    if chi is None:
        esci()  # area libera: nessuno la rivendica

    ruolo = leggi_ruolo(radice)

    if ruolo is None:
        # Requisito esplicito: senza .team-role non si blocca niente.
        # Lo si dichiara solo sulle aree contese, per non fare rumore.
        if chi in RUOLI_NOTI:
            avvisa(
                "ownership_guard: `.team-role` assente nella radice del "
                "progetto, guardia di proprieta' disattivata. "
                f"`{rel}` risulta di {chi} (docs/COLLABORAZIONE.md par. 2). "
                "Per riattivarla scrivi `davide` oppure `chiara` in "
                "`.team-role` (non versionato)."
            )
        esci()

    if ruolo not in RUOLI_NOTI:
        avvisa(
            f"ownership_guard: ruolo '{ruolo}' non riconosciuto in "
            "`.team-role` (attesi: davide, chiara). Guardia disattivata."
        )

    if chi == "condiviso":
        avvisa(
            f"ownership_guard: `{rel}` e' a proprieta' condivisa "
            "(CLAUDE.md par. 2). Si puo' modificare, ma va detto all'altra "
            "persona alla prossima sincronizzazione."
        )

    if chi != ruolo:
        altro = "Chiara" if chi == "chiara" else "Davide"
        status = FILE_STATUS[ruolo]
        nega(
            f"Scrittura negata su `{rel}`: quell'area e' di {altro} "
            "(mappa in docs/COLLABORAZIONE.md par. 2, sintesi in CLAUDE.md "
            f"par. 2). Il ruolo di questa sessione e' '{ruolo}', letto da "
            "`.team-role`. "
            "Cosa fare invece: non modificare il file, scrivi la richiesta in "
            f"`{status}` (tuo) dicendo cosa serve e perche', e portala alla "
            "prossima sincronizzazione. Lavoriamo sullo stesso branch senza "
            "pull request: un conflitto qui cancella il lavoro dell'altra "
            "persona."
        )

    esci()  # area propria: nessuna decisione, si prosegue normalmente


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as errore:  # rete di sicurezza: mai bloccare per un bug
        sys.stderr.write("ownership_guard: errore ignorato (%s)\n" % errore)
        sys.exit(0)
