# Il sistema agentico

Sette componenti: un orchestratore e sei sub-agenti, ognuno con un verbo solo.
Se due agenti potessero scambiarsi il lavoro, uno dei due è di troppo.

| Componente | Verbo | Tier | Fase |
|---|---|---|---|
| `orchestrator.md` | instrada | haiku-4.5 | A + B |
| `subagents/profiler.md` | profila | haiku-4.5 | A |
| `subagents/source-analyzer.md` | destruttura | opus-5 | A |
| `subagents/simplifier.md` | riscrive | sonnet-5 | A |
| `subagents/fidelity-validator.md` | verifica | opus-5 | A |
| `subagents/block-detector.md` | diagnostica | haiku-4.5 | B |
| `subagents/intervener.md` | suggerisce | sonnet-5 | B |

## Le tre decisioni architetturali

**1. Due fasi con economie opposte.** La Fase A (preparazione) usa i modelli capaci una volta
sola per artefatto e persiste il risultato su disco. La Fase B (sessione con la persona) è ad alta
frequenza e usa solo modelli economici che leggono da file. Il costo non cresce con l'uso.

**2. Chi scrive non approva.** `simplifier` produce, `fidelity-validator` giudica, e sono
separati. Il vincolo della sfida — semplificare senza cambiare il significato — diventa così
una proprietà verificabile del sistema invece di una raccomandazione dentro un prompt.

**3. L'escalation umana è una funzionalità.** Ogni gate HITL ha una condizione numerica
(`agents/orchestrator.md`). Quando scatta, il sistema dice alla persona cosa sta succedendo.
Un percorso che si ferma onestamente vale più di uno che tira a indovinare su una pratica vera.

## Come si legge questa cartella

| File | Cosa contiene |
|---|---|
| `orchestrator.md` | pipeline, stato, limiti di iterazione, gate HITL |
| `workflows/main-pipeline.md` | la sequenza eseguibile passo per passo |
| `subagents/_TEMPLATE.md` | il contratto che ogni agente deve compilare |
| `guardrails.md` | 17 regole numerate valide per tutti |
| `schemas/` | i contratti JSON fra i componenti |
| `skills/` | istruzioni lunghe caricate on-demand |
| `state/` | stato esternalizzato, fuori dal contesto |

## Economia dei token

Tre leve, tutte visibili nel codice e non solo dichiarate qui:

- **Tiering per compito, non per abitudine.** Due agenti su tre girano su Haiku. Opus è riservato
  ai due punti dove sbagliare costa davvero: capire l'artefatto e verificare la fedeltà.
- **Costo pagato una volta.** La Fase A non si ripete: `journey.json` è il risultato persistito.
- **JSON, non conversazione.** Gli agenti si passano payload strutturati; lo stato sta su disco.
  Nessun componente porta con sé la storia degli altri.

TODO prima del freeze: tabella con i token misurati per agente su un run reale.
