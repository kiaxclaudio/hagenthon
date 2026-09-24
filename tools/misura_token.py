#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Misura il costo in contesto delle istruzioni del sistema agentico.

Perche' esiste: il repository sostiene che l'architettura a due fasi e' efficiente
in token. Un'affermazione del genere va sostanziata con numeri riproducibili, non
lasciata come opinione.

Due modalita':

  - **esatta**, se e' presente ANTHROPIC_API_KEY: usa l'endpoint ufficiale di
    conteggio token. Nessuna stima.
  - **stimata**, altrimenti: rapporto caratteri/token dichiarato in RAPPORTO_STIMA,
    e ogni numero viene marcato come stima nel report.

Uso:  python tools/misura_token.py [--md]
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
SUBAGENTI = RADICE / "agents" / "subagents"
SKILLS = RADICE / "agents" / "skills"
ORCHESTRATORE = RADICE / "agents" / "orchestrator.md"

# Rapporto usato solo in modalita' stimata. Per il testo italiano, con la
# tokenizzazione dei modelli Claude, un token vale all'incirca 3,6 caratteri.
# E' una stima dichiarata: serve l'ordine di grandezza, non la precisione.
RAPPORTO_STIMA = 3.6

# Fase di appartenenza, da agents/ARCHITETTURA.md.
FASE = {
    "source-analyzer": "A", "explainer": "A", "fidelity-validator": "A",
    "profiler": "B", "eligibility": "B", "navigator": "B",
    "orchestrator": "A+B",
}


def frontmatter(testo: str) -> dict:
    """Estrae le chiavi del frontmatter YAML, senza dipendenze esterne."""
    if not testo.startswith("---"):
        return {}
    fine = testo.find("\n---", 3)
    if fine == -1:
        return {}
    chiavi = {}
    for riga in testo[3:fine].splitlines():
        if ":" in riga and not riga.startswith(" "):
            k, _, v = riga.partition(":")
            chiavi[k.strip()] = v.strip()
    return chiavi


def skill_caricate(testo: str) -> list[str]:
    """Le skill che l'agente dichiara di caricare, cercate per nome file."""
    trovate = []
    for skill in sorted(SKILLS.glob("*.md")):
        if skill.name == "README.md":
            continue
        if skill.stem in testo:
            trovate.append(skill.stem)
    return trovate


class Contatore:
    """Conta i token. Esatto se c'e' la chiave, stimato altrimenti."""

    def __init__(self) -> None:
        self.esatto = False
        self._client = None
        chiave = os.getenv("ANTHROPIC_API_KEY")
        if chiave:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=chiave, timeout=30.0)
                self.esatto = True
            except Exception as e:                      # rete assente, SDK vecchio, chiave non valida
                print(f"  nota: conteggio esatto non disponibile ({e}); passo alla stima",
                      file=sys.stderr)

    def conta(self, testo: str) -> int:
        if self._client is not None:
            try:
                r = self._client.messages.count_tokens(
                    model=os.getenv("ANTHROPIC_MODEL_CHEAP", "claude-haiku-4-5-20251001"),
                    messages=[{"role": "user", "content": testo}],
                )
                return int(r.input_tokens)
            except Exception:
                self._client = None                     # una volta sola, poi stima per tutti
                self.esatto = False
        return round(len(testo) / RAPPORTO_STIMA)


def raccogli(contatore: Contatore) -> list[dict]:
    righe = []
    file_agenti = sorted(SUBAGENTI.glob("*.md"))
    if ORCHESTRATORE.is_file():
        file_agenti.insert(0, ORCHESTRATORE)

    for percorso in file_agenti:
        if percorso.name.startswith("_"):               # _TEMPLATE.md non e' un agente
            continue
        testo = percorso.read_text(encoding="utf-8")
        fm = frontmatter(testo)
        nome = fm.get("name", percorso.stem)
        istruzioni = contatore.conta(testo)

        skill = skill_caricate(testo)
        token_skill = 0
        for s in skill:
            token_skill += contatore.conta((SKILLS / f"{s}.md").read_text(encoding="utf-8"))

        righe.append({
            "nome": nome,
            "fase": FASE.get(nome, "?"),
            "tier": fm.get("model", "?"),
            "istruzioni": istruzioni,
            "skill": ", ".join(skill) or "—",
            "token_skill": token_skill,
            "totale": istruzioni + token_skill,
        })
    return righe


def report(righe: list[dict], esatto: bool, markdown: bool) -> str:
    modo = ("conteggio **esatto** con l'endpoint ufficiale"
            if esatto else
            f"**stima** dichiarata, {RAPPORTO_STIMA} caratteri per token")

    a = sum(r["totale"] for r in righe if r["fase"] == "A")
    b = sum(r["totale"] for r in righe if r["fase"] == "B")
    orch = sum(r["totale"] for r in righe if r["fase"] == "A+B")

    out = []
    if markdown:
        out.append("# Costo in contesto delle istruzioni\n")
        out.append(f"Generato da `tools/misura_token.py`. Metodo: {modo}.\n")
        out.append("Misura il costo **fisso** che ogni agente porta in contesto a ogni")
        out.append("invocazione: le sue istruzioni piu' le skill che carica. Non misura")
        out.append("i dati di lavoro, che variano con l'input.\n")
        out.append("| Agente | Fase | Tier | Istruzioni | Skill caricate | Token skill | Totale |")
        out.append("|---|---|---|---:|---|---:|---:|")
        for r in righe:
            out.append(f"| `{r['nome']}` | {r['fase']} | {r['tier']} | {r['istruzioni']:,} "
                       f"| {r['skill']} | {r['token_skill']:,} | **{r['totale']:,}** |")
        out.append("")
        out.append("## Le due fasi\n")
        out.append(f"- **Fase A** (preparazione, una volta per catalogo): {a:,} token di istruzioni")
        out.append(f"- **Fase B** (conversazione, a ogni sessione): {b:,} token di istruzioni")
        out.append(f"- **Orchestratore** (entrambe): {orch:,} token")
        out.append("")
        if b and a:
            out.append(f"La Fase A costa **{a/b:.1f} volte** la Fase B in sole istruzioni, e usa")
            out.append("i due modelli piu' capaci. Per questo viene eseguita una volta sola per")
            out.append("catalogo e il risultato e' persistito in `agents/state/catalogo.json`.")
            out.append("A runtime resta la sola Fase B, che legge un JSON gia' verificato.")
    else:
        out.append(f"metodo: {modo}")
        for r in righe:
            out.append(f"{r['nome']:<20} {r['fase']:<4} {r['tier']:<28} {r['totale']:>7,}")
        out.append(f"{'FASE A':<20} {'':<4} {'':<28} {a:>7,}")
        out.append(f"{'FASE B':<20} {'':<4} {'':<28} {b:>7,}")
    return "\n".join(out)


def main() -> int:
    contatore = Contatore()
    righe = raccogli(contatore)
    if not righe:
        print("nessun file agente trovato", file=sys.stderr)
        return 1
    print(report(righe, contatore.esatto, "--md" in sys.argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
