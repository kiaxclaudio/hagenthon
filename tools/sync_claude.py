#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_claude.py - genera `.claude/` da `agents/`. Copia verbatim, nessuna logica duplicata.

Perche' esiste
--------------
Due vincoli incompatibili:

1. la consegna dell'hackathon vuole la struttura agentica dentro `agents/`
   (vedi docs/inbox/chiara-idea.md: `agents/` e' la cartella consegnata);
2. Claude Code carica sub-agenti, comandi e skill **solo** da `.claude/`.

Tenere due copie scritte a mano significa che divergono: e' questione di ore, e
una divergenza fra `agents/orchestrator.md` e `.claude/agents/...` e' esattamente
il genere di incoerenza che un valutatore automatico trova al primo confronto
(criterio "coerenza fra i file", 19%).

Qui `agents/` e' la **fonte unica** e `.claude/` e' un artefatto generato:
- la copia e' byte per byte, senza trasformazioni. Nessuna regola vive in due
  posti, quindi non ci sono due posti in cui puo' essere sbagliata;
- `--check` rende la coerenza verificabile in un comando, quindi controllabile
  prima di una consegna.

Mappatura
---------
    agents/subagents/*.md  ->  .claude/agents/<nome>.md
    agents/commands/*.md   ->  .claude/commands/<nome>.md
    agents/skills/*.md     ->  .claude/skills/<nome>/SKILL.md

Esclusi dalla copia: `README.md` (documenta la cartella, non e' un componente),
i file che iniziano con `_` (es. `_TEMPLATE.md`) e `.gitkeep`.

Uso
---
    python tools/sync_claude.py            # genera/aggiorna .claude/
    python tools/sync_claude.py --check    # non scrive nulla; exit 1 se disallineato
    python tools/sync_claude.py --quiet    # solo le differenze

Exit code:
    0  allineato (o sincronizzazione riuscita)
    1  disallineato (solo con --check)
    2  errore interno

Solo libreria standard.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
SORGENTE = RADICE / "agents"
DESTINAZIONE = RADICE / ".claude"

# File che non sono componenti e non vanno copiati.
ESCLUSI = {"README.md", ".gitkeep"}

# Intestazione del file che segnala la natura generata della cartella.
# E' l'unico file prodotto da questo script che non e' una copia: serve a
# impedire che qualcuno modifichi `.claude/` credendo di lavorare sulla fonte.
NOME_AVVISO = "GENERATO.md"
AVVISO = """<!-- generato da tools/sync_claude.py - non modificare a mano -->
# Cartella generata

Il contenuto di `.claude/agents/`, `.claude/commands/` e `.claude/skills/` e' una **copia
verbatim** di `agents/subagents/`, `agents/commands/` e `agents/skills/`, prodotta da
`tools/sync_claude.py`.

La fonte unica e' `agents/`. Le modifiche fatte qui vengono perse alla prossima
sincronizzazione. Per verificare l'allineamento:

    python tools/sync_claude.py --check

`.claude/settings.json` **non** e' generato: e' scritto a mano ed e' l'unico file
di questa cartella che si modifica direttamente.
"""


def e_componente(percorso: Path) -> bool:
    """Un file .md e' un componente se non e' un README ne' un template."""
    return (percorso.suffix == ".md"
            and percorso.name not in ESCLUSI
            and not percorso.name.startswith("_"))


def pianifica() -> dict[Path, bytes]:
    """Costruisce la mappa {destinazione assoluta: contenuto atteso}.

    Nessuna trasformazione: il contenuto atteso e' esattamente il byte per byte
    del file sorgente.
    """
    piano: dict[Path, bytes] = {}

    mappature = [
        (SORGENTE / "subagents", lambda p: DESTINAZIONE / "agents" / p.name),
        (SORGENTE / "commands", lambda p: DESTINAZIONE / "commands" / p.name),
        (SORGENTE / "skills",
         lambda p: DESTINAZIONE / "skills" / p.stem / "SKILL.md"),
    ]

    for cartella, destina in mappature:
        if not cartella.is_dir():
            continue
        for sorgente in sorted(cartella.iterdir()):
            if not sorgente.is_file() or not e_componente(sorgente):
                continue
            piano[destina(sorgente)] = sorgente.read_bytes()

    piano[DESTINAZIONE / NOME_AVVISO] = AVVISO.encode("utf-8")
    return piano


def obsoleti(piano: dict[Path, bytes]) -> list[Path]:
    """File generati in passato che oggi non hanno piu' una sorgente.

    Si guarda solo dentro le tre cartelle gestite: `.claude/settings.json` e
    qualsiasi altro file scritto a mano non viene mai toccato.
    """
    attesi = set(piano)
    avanzi: list[Path] = []
    for sotto in ("agents", "commands", "skills"):
        radice = DESTINAZIONE / sotto
        if not radice.is_dir():
            continue
        for percorso in sorted(radice.rglob("*")):
            if percorso.is_file() and percorso not in attesi:
                avanzi.append(percorso)
    return avanzi


def avvisi_skill(piano: dict[Path, bytes]) -> list[str]:
    """Segnala le skill senza frontmatter `name:`.

    Claude Code carica una skill solo se `SKILL.md` apre con un frontmatter YAML
    che dichiara almeno `name` e `description`. Qui si **segnala** e basta: questo
    script copia, non corregge. Correggere significherebbe mettere una regola di
    formato in due posti, che e' esattamente cio' che si vuole evitare.
    """
    problemi: list[str] = []
    for destinazione, contenuto in piano.items():
        if destinazione.name != "SKILL.md":
            continue
        testa = contenuto[:400].decode("utf-8", errors="replace").lstrip()
        if not testa.startswith("---") or "name:" not in testa:
            rel = destinazione.relative_to(RADICE).as_posix()
            problemi.append(
                "%s: manca il frontmatter YAML con name/description, "
                "Claude Code non caricherebbe la skill" % rel)
    return problemi


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Genera .claude/ da agents/ (copia verbatim).")
    ap.add_argument("--check", action="store_true",
                    help="non scrive nulla; exit 1 se .claude/ e' disallineato")
    ap.add_argument("--quiet", action="store_true",
                    help="stampa solo le differenze")
    args = ap.parse_args(argv)

    if not SORGENTE.is_dir():
        print("errore: cartella sorgente assente: %s" % SORGENTE,
              file=sys.stderr)
        return 2

    piano = pianifica()
    avanzi = obsoleti(piano)

    da_creare: list[Path] = []
    da_aggiornare: list[Path] = []
    invariati = 0

    for destinazione, atteso in piano.items():
        if not destinazione.exists():
            da_creare.append(destinazione)
        elif destinazione.read_bytes() != atteso:
            da_aggiornare.append(destinazione)
        else:
            invariati += 1

    def rel(p: Path) -> str:
        return p.relative_to(RADICE).as_posix()

    differenze = len(da_creare) + len(da_aggiornare) + len(avanzi)

    if args.check:
        if differenze == 0:
            if not args.quiet:
                print("allineato: %d file generati da agents/ -> .claude/"
                      % len(piano))
            for problema in avvisi_skill(piano):
                print("  avviso: %s" % problema)
            return 0
        print(".claude/ DISALLINEATO rispetto ad agents/ (%d %s):"
              % (differenze,
                 "differenza" if differenze == 1 else "differenze"))
        for p in da_creare:
            print("  mancante:   %s" % rel(p))
        for p in da_aggiornare:
            print("  diverso:    %s" % rel(p))
        for p in avanzi:
            print("  di troppo:  %s  (nessuna sorgente in agents/)" % rel(p))
        print("Rigenera con: python tools/sync_claude.py")
        return 1

    # --- scrittura -------------------------------------------------------
    try:
        for destinazione in da_creare + da_aggiornare:
            destinazione.parent.mkdir(parents=True, exist_ok=True)
            destinazione.write_bytes(piano[destinazione])
        for percorso in avanzi:
            percorso.unlink()
            # Rimuove anche la cartella della skill, se resta vuota.
            genitore = percorso.parent
            if (genitore != DESTINAZIONE and genitore.is_dir()
                    and not any(genitore.iterdir())):
                genitore.rmdir()
    except OSError as errore:
        print("errore di scrittura: %s" % errore, file=sys.stderr)
        return 2

    if not args.quiet:
        print("sync agents/ -> .claude/")
    for p in da_creare:
        print("  creato:     %s" % rel(p))
    for p in da_aggiornare:
        print("  aggiornato: %s" % rel(p))
    for p in avanzi:
        print("  rimosso:    %s  (sorgente sparita da agents/)" % rel(p))
    if not args.quiet:
        print("  invariati:  %d" % invariati)
    for problema in avvisi_skill(piano):
        print("  avviso: %s" % problema)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as errore:  # nessuna traccia illeggibile all'utente
        print("sync_claude: errore interno (%s)" % errore, file=sys.stderr)
        sys.exit(2)
