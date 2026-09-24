# A cosa ho diritto?

Sistema multi-agente che aiuta persone con zero alfabetizzazione fiscale a scoprire quali bonus e aiuti statali italiani spettano loro — in linguaggio semplice, senza burocrazia.

Hackathon Agentic Coding - Accenture Application Engineering.
Team: Davide Polito, Chiara Gario. Tema 02 — Inclusione Finanziaria.

## Il problema

Milioni di italiani non accedono a bonus e incentivi a cui hanno diritto perché non capiscono il linguaggio burocratico, non sanno da dove partire e non hanno mai aperto il cassetto fiscale. Il punto di blocco è l'alfabetizzazione fiscale: il problema non è la burocrazia in sé, ma il fatto che nessuno la traduce.

## La soluzione

Un sistema conversazionale a 4 agenti che raccoglie il profilo dell'utente in 5 domande a scelta multipla, identifica i bonus pertinenti, li spiega senza termini tecnici e guida l'utente passo per passo verso l'accesso — rimandando sempre a un CAF per le decisioni finali.

## Il sistema agentico

Un orchestratore e sei sub-agenti, divisi in due fasi con economie opposte.

```
FASE A - preparazione (una volta per artefatto, modelli capaci)

  profiler ──▶ source-analyzer ──▶ simplifier ──▶ fidelity-validator ──▶ journey.json
   (haiku)         (opus)          (sonnet)   ▲         (opus)    │
                                              └── respinto ───────┘
                                                 max 2 giri, poi HITL

FASE B - sessione guidata (a ogni evento, modelli economici)

  evento ──▶ block-detector ──▶ intervener ──▶ passo successivo
               (haiku)           (sonnet)
                       3 interventi falliti ──▶ HITL
```

Dettaglio in [`agents/README.md`](agents/README.md). Contratti in [`agents/schemas/`](agents/schemas/).
Regole in [`agents/guardrails.md`](agents/guardrails.md).

## Struttura del repository

```
app/            il prototipo che la persona usa
agents/         orchestratore, sub-agenti, workflow, skill, schemi, stato
presentation/   presentazione HTML (5 minuti, brand Accenture)
docs/           evidenza di validazione e nota sul processo
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env    # inserire la propria ANTHROPIC_API_KEY
python app/main.py      # apre http://localhost:5000
```

## Validazione

4 scenari testati end-to-end. Evidenze in [`docs/validation/`](docs/validation/).

| Scenario | Bonus attesi |
|---------|-------------|
| Proprietario, dipendente, ristrutturazione | Bonus Ristrutturazione 50%, Ecobonus, Bonus Mobili |
| Coppia con figlio appena nato | Assegno Unico, Bonus Nido |
| Disoccupato under 36 | Naspi, Supporto Formazione Lavoro |
| Pensionato con spese mediche | Detrazioni sanitarie 19%, esenzione ticket |

## Come abbiamo usato l'AI

Vedi [`docs/process-note.md`](docs/process-note.md).
