# Workflow: dalla fonte ufficiale alla risposta della persona

Sequenza eseguibile. Ogni riga è una invocazione con input e output espliciti.
L'orchestratore (`agents/orchestrator.md`) esegue questo file; la tabella canonica dei componenti
sta in `agents/ARCHITETTURA.md`; i contratti stanno in `agents/schemas/`.

## Fase A — grounding del catalogo (offline, una volta per fonte)

| # | Agente | Input | Output | Tier | Condizione di uscita |
|---|---|---|---|---|---|
| A1 | `source-analyzer` | pagina ufficiale scaricata | `agents/state/misure-grezze.json` | opus | `status != degraded`, altrimenti HITL sulla fonte |
| A2 | `explainer` | una misura di A1 | misura riscritta in lingua semplice | sonnet | per ogni misura di A1 |
| A3 | `fidelity-validator` | misura originale e misura riscritta | verdetto e divergenze | opus | `approved`, oppure torna ad A2 (massimo 2 giri) |
| A4 | orchestratore | misure approvate | `agents/state/catalogo.json` | haiku | tutte le misure risolte: approvate oppure `hitl_required` |

A2 e A3 girano in coppia, misura per misura. Una misura respinta due volte non entra nel
catalogo: esce marcata e la rivede una persona. Il validator ha solo `Read`, quindi non può
correggere ciò che respinge.

## Fase B — conversazione (runtime, a ogni sessione)

| # | Agente | Input | Output | Tier | Condizione di uscita |
|---|---|---|---|---|---|
| B1 | `profiler` | risposte a scelta multipla | `agents/state/profilo.json` | haiku | almeno due assi valorizzati, altrimenti una sola ri-domanda |
| B2 | `eligibility` | profilo e catalogo | misure pertinenti con il motivo | sonnet | almeno una misura con `confidence >= 0.6`, altrimenti rimando al CAF |
| B3 | `navigator` | una misura proposta da B2 | passi, documenti, glossario, disclaimer | haiku | massimo 3 misure per sessione |
| B4 | orchestratore | uscite di B2 e B3 | `agents/state/run-<id>.json` | haiku | scheda mostrata oppure rimando al CAF dichiarato |

La Fase B non parte se il catalogo non esiste: senza misure verificate non c'è risposta
ammissibile, e l'orchestratore lo dichiara invece di ricostruire i dati a memoria.

## Precondizioni e postcondizioni

| Passo | Precondizione | Postcondizione |
|---|---|---|
| A1 | la pagina è stata scaricata e ne è nota la data di consultazione | ogni misura ha `source_refs` verso il punto esatto della pagina |
| A2 | la misura ha il blocco dati completo | nessun numero modificato rispetto ad A1 |
| A3 | esistono entrambe le versioni della stessa misura | verdetto motivato per ogni divergenza |
| A4 | nessuna misura in sospeso | il catalogo contiene solo misure approvate |
| B1 | la sessione ha raccolto almeno una risposta | il profilo usa solo valori della tassonomia chiusa |
| B2 | il catalogo esiste e non è vuoto | ogni misura proposta porta il requisito che la rende pertinente |
| B3 | la misura viene da B2 | ogni passo ha un riferimento al catalogo; il disclaimer è sempre presente |

## Perché questa separazione

Il lavoro semanticamente difficile — capire una pagina dell'Agenzia delle Entrate o dell'INPS e
verificare che la riscrittura non abbia cambiato una percentuale — usa i modelli capaci e viene
eseguito **una volta sola per fonte**, con il risultato persistito su disco. Il runtime, che è la
parte ad alta frequenza, usa solo modelli economici e legge da file.

È ciò che rende il sistema sostenibile in token senza rinunciare alla qualità dove un errore
diventa il danno di una persona che sbaglia una pratica vera.
