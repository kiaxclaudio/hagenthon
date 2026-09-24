# Il sistema agentico

Sette componenti: un orchestratore e sei sub-agenti, ognuno con un verbo solo.
Se due agenti potessero scambiarsi il lavoro, uno dei due è di troppo.
La decisione canonica sta in `agents/ARCHITETTURA.md`: in caso di divergenza vince quel file.

Il prodotto è "A cosa ho diritto?": orientamento sugli aiuti statali italiani per chi parte da
zero di alfabetizzazione fiscale. Spiega quali misure esistono per una situazione, che cosa
significano e come si accede. Non consiglia: per le decisioni rimanda a un CAF o a un
commercialista (G-04).

| Componente | Verbo | Tier | Fase | Strumenti |
|---|---|---|---|---|
| `orchestrator.md` | instrada | haiku-4.5 | A + B | nessuno |
| `subagents/source-analyzer.md` | destruttura | opus-5 | A | Read, Write, Grep, Glob |
| `subagents/explainer.md` | riscrive | sonnet-5 | A | Read, Write |
| `subagents/fidelity-validator.md` | verifica | opus-5 | A | solo Read |
| `subagents/profiler.md` | normalizza | haiku-4.5 | B | Read, Write |
| `subagents/eligibility.md` | incrocia | sonnet-5 | B | Read, Write |
| `subagents/navigator.md` | guida | haiku-4.5 | B | Read, Write |

La Fase A costruisce offline il catalogo delle misure verificate; la Fase B è la conversazione
con la persona e legge quel catalogo. La sequenza eseguibile sta in
`agents/workflows/main-pipeline.md`.

## Le tre decisioni architetturali

**1. Due fasi con economie opposte.** La Fase A usa i modelli capaci una volta sola per fonte e
persiste il catalogo su disco. La Fase B è ad alta frequenza e usa solo modelli economici che
leggono da file. Il costo non cresce con il numero di conversazioni.

**2. Chi scrive non approva.** `explainer` riformula, `fidelity-validator` giudica, e sono
separati anche nei permessi: il validator ha **solo `Read`** e non può correggere ciò che
respinge. Il vincolo del dominio — semplificare una percentuale senza cambiarla — diventa una
proprietà verificabile del sistema invece di una raccomandazione dentro un prompt.

**3. L'escalation umana è una funzionalità.** Ogni gate HITL ha una condizione numerica o
booleana (`agents/orchestrator.md`). Quando scatta, il sistema dice che cosa sta succedendo e
indica il CAF. Una risposta che si ferma onestamente vale più di una che tira a indovinare su
una detrazione vera.

## Come si legge questa cartella

| File | Cosa contiene |
|---|---|
| `ARCHITETTURA.md` | la decisione canonica: componenti, fasi, gate, limiti |
| `orchestrator.md` | routing, stato, limiti di iterazione, gate HITL |
| `workflows/main-pipeline.md` | la sequenza eseguibile, passo per passo |
| `subagents/_TEMPLATE.md` | il contratto che ogni agente compila, senza eccezioni |
| `guardrails.md` | 24 regole numerate valide per tutti, di cui 7 di dominio fiscale |
| `schemas/` | i contratti JSON fra i componenti |
| `skills/` | istruzioni lunghe caricate on-demand |
| `state/` | stato esternalizzato, fuori dal contesto |

## Economia dei token

Tre leve, tutte verificabili leggendo i file e non solo dichiarate qui:

- **Tiering per compito, non per abitudine.** Dei sette componenti, tre girano su Haiku
  (orchestratore, `profiler`, `navigator`), due su Sonnet (`explainer`, `eligibility`) e due su
  Opus (`source-analyzer`, `fidelity-validator`). Opus è riservato ai due punti dove sbagliare
  costa davvero: leggere una pagina ufficiale e verificare che la riscrittura non abbia cambiato
  un numero. Entrambi girano solo in Fase A, mai durante una conversazione.
- **Costo pagato una volta.** La Fase A non si ripete a ogni sessione: il catalogo verificato è
  il risultato persistito, e la Fase B lo legge. Una conversazione costa tre invocazioni di
  modelli economici, non una rilettura delle fonti.
- **JSON, non conversazione.** I componenti si passano payload conformi agli schemi in
  `agents/schemas/` e lo stato sta su disco (G-12, G-14). Nessun componente porta con sé la
  storia degli altri.
- **Istruzioni lunghe fuori dai prompt.** Le regole di riscrittura e la tassonomia delle
  divergenze stanno in `skills/` e vengono aperte solo nel passo che le usa (G-13): la mappa dei
  caricamenti è in `agents/skills/README.md`.
