# Workflow: dalla fonte reale al task completato

Sequenza eseguibile. Ogni riga è una invocazione con input e output espliciti.
L'orchestratore (`agents/orchestrator.md`) esegue questo file; i contratti stanno in `agents/schemas/`.

## Fase A — Preparazione

| # | Agente | Input | Output | Tier | Condizione di uscita |
|---|---|---|---|---|---|
| A1 | `profiler` | descrizione della persona | `state/profile.json` | haiku | sempre |
| A2 | `source-analyzer` | artefatto reale | `state/source-model.json` | opus | `status != degraded`, altrimenti HITL |
| A3 | `simplifier` | un passo + profilo | passo semplificato | sonnet | per ogni passo di A2 |
| A4 | `fidelity-validator` | passo originale + semplificato | verdetto + diff | opus | `approved`, oppure torna ad A3 (max 2) |
| A5 | orchestratore | passi approvati | `state/journey.json` | — | tutti i passi risolti (approvati o `hitl_required`) |

A3 e A4 girano in coppia, passo per passo. Un passo respinto due volte non entra nel percorso:
esce marcato e viene segnalato a una persona.

## Fase B — Sessione guidata

| # | Agente | Input | Output | Tier | Condizione di uscita |
|---|---|---|---|---|---|
| B1 | orchestratore | `journey.json` + `run-<id>.json` | passo corrente | — | task completato |
| B2 | `block-detector` | evento utente + passo corrente | diagnosi del blocco | haiku | `blocked: false` → B1 |
| B3 | `intervener` | diagnosi + passo + profilo | intervento mirato | sonnet | max 3 sullo stesso passo → HITL |

## Perché questa separazione

Il lavoro semanticamente difficile (capire l'artefatto, verificare la fedeltà) usa i modelli
capaci e viene eseguito **una volta sola per artefatto**, con il risultato persistito su disco.
Il runtime, che è la parte ad alta frequenza, usa solo modelli economici e legge da file.

Questo è ciò che rende il sistema sostenibile in token (criterio 04, 12%) senza rinunciare
alla qualità dove serve davvero.
