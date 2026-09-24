# TODO NOME PROGETTO

TODO una riga: chi aiuta, a fare cosa, su quale servizio reale.

Hackathon Agentic Coding - Accenture Application Engineering.
Team: Davide Polito, Chiara TODO. Tema TODO.

## Il problema

TODO: la persona concreta, il punto esatto in cui oggi si blocca, perché conta.

## La soluzione

TODO: cosa fa il prototipo, in tre righe.

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

TODO: prerequisiti, installazione, avvio, con i comandi esatti.

```bash
cp .env.example .env    # inserire la propria ANTHROPIC_API_KEY
```

## Validazione

TODO: cosa abbiamo verificato e come. Evidenze in [`docs/validation/`](docs/validation/).

## Come abbiamo usato l'AI

Vedi [`docs/process-note.md`](docs/process-note.md).
