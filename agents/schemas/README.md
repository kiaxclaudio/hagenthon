# Contratti

Un file JSON Schema (draft 2020-12) per ogni input e output di agente, nominato
`<agente>.input.json` / `<agente>.output.json`, più tre artefatti di stato.

I contratti si concordano **all'inizio** e poi si congelano: è ciò che permette a due persone
di lavorare in parallelo senza aspettarsi a vicenda. Chi costruisce l'app programma contro
lo schema; chi costruisce gli agenti produce quello schema. Nessuno dei due è bloccato dall'altro.

Modificare uno schema dopo il congelamento richiede il consenso esplicito di entrambi:
è l'unica cosa che può rompere il lavoro dell'altra persona senza preavviso.

## Campi comuni a tutti gli output (G-06, G-07)

```json
{
  "status":     "ok | degraded | hitl_required",
  "confidence": 0.0,
  "source_refs": ["identificatore del punto della fonte da cui proviene l'affermazione"],
  "payload":    { }
}
```

`payload` è l'unica parte specifica del singolo agente. Tutto il resto è uniforme,
così l'orchestratore può instradare e applicare i gate senza conoscere il dominio.
Ogni output concreto estende `_envelope.json` via `allOf` e chiude con
`unevaluatedProperties: false`; ogni oggetto del payload chiude con `additionalProperties: false`.

## Definizioni condivise

`_envelope.json` non contiene solo l'envelope: in `$defs` stanno le definizioni che gli altri
contratti referenziano invece di riscriverle, così una regola trasversale vive in un punto solo.

| `$defs` di `_envelope.json` | Che cosa vincola |
|---|---|
| `disclaimer` | Testo fisso con `const`: nessun agente può accorciarlo o ammorbidirlo (G-04) |
| `testo_senza_consulenza` | Stringa con `not/pattern` sulle formule di consulenza: è l'hook PostToolUse in forma dichiarativa |
| `source_refs_obbligatori` | `minItems: 1`, usato su ogni dato numerico e su ogni requisito (G-01, G-03) |
| `misura_id` | Identificatore stabile di una misura, in minuscolo con trattini |
| `timestamp` | Istante ISO 8601 |

Allo stesso modo `profiler.output.json` è la fonte di verità degli **enum del profilo** e
`source-analyzer.output.json` quella della **struttura di una misura**: entrambi vengono
referenziati per `$ref` dagli altri file. Un enum di dominio esiste in un posto solo.

## Invarianti scritte nello schema, non nel prompt

Gli `if/then` non sono decorazione: sono i gate dell'architettura resi verificabili su un output.

| Dove | Regola |
|---|---|
| `fidelity-validator.output` | Una divergenza su percentuale, importo, tetto, scadenza, requisito, obbligo o riferimento è **sempre** `bloccante` |
| `fidelity-validator.output` | Una sola divergenza bloccante impone `verdict: rejected` |
| `fidelity-validator.output` | Secondo rifiuto sulla stessa misura: `status: hitl_required` e `esito_misura: esclusa_hitl` |
| `eligibility.output` | `confidence < 0.6` impone `escalation: true` |
| `eligibility.output` | `escalation: true` impone `misure_pertinenti` vuoto, motivo e spiegazione presenti |
| `catalogo.json` | Una voce pubblicata ha `verifica.verdict: approved` e `confidence >= 0.6` |
| `source-analyzer.output` | Una porzione non interpretabile impedisce lo `status: ok` |
| `profiler.output` | Un profilo `completo` non può avere `risposte_mancanti` |
| `run-state.json` | Una escalation attiva chiude la sessione e porta motivo, momento e messaggio |

Nessun output contiene un campo di punteggio, priorità o convenienza: in `eligibility.output`
l'assenza di una graduatoria è parte del contratto, non una dimenticanza (G-04).

## Indice dei file di schema

| File | Agente | Fase | Descrizione |
|---|---|---|---|
| `_envelope.json` | — | — | Envelope comune + definizioni condivise (`allOf` base per tutti gli output) |
| `source-analyzer.input.json` | source-analyzer | A | Fonte ufficiale scaricata, con ente e data di consultazione |
| `source-analyzer.output.json` | source-analyzer | A | Misure destrutturate + struttura canonica `$defs/misura` |
| `explainer.input.json` | explainer | A | Una misura + le divergenze da correggere al secondo giro |
| `explainer.output.json` | explainer | A | Spiegazione in lingua semplice + glossario contestuale + disclaimer |
| `fidelity-validator.input.json` | fidelity-validator | A | Misura originale + spiegazione da verificare |
| `fidelity-validator.output.json` | fidelity-validator | A | Verdetto approved/rejected + divergenze tipizzate `$defs/divergenza` |
| `catalogo.json` | — | A→B | Artefatto persistito: misure verificate e pubblicate (`state/catalogo.json`) |
| `profiler.input.json` | profiler | B | Risposte grezze del flusso a scelta multipla |
| `profiler.output.json` | profiler | B | Profilo normalizzato + enum di dominio del profilo (`state/profilo.json`) |
| `eligibility.input.json` | eligibility | B | Profilo + voci di catalogo candidate |
| `eligibility.output.json` | eligibility | B | Misure pertinenti con motivazione, oppure escalation motivata |
| `navigator.input.json` | navigator | B | Profilo + una voce di catalogo |
| `navigator.output.json` | navigator | B | Passi operativi ordinati, documenti, dove si fa, disclaimer |
| `run-state.json` | — | B | Stato di sessione: passo, misure proposte, escalation (`state/run-<id>.json`) |
