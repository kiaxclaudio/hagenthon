# Contratti

Un file JSON Schema per ogni input e output di agente, nominato
`<agente>.input.json` / `<agente>.output.json`.

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

## Indice dei file di schema

| File | Agente | Fase | Descrizione |
|---|---|---|---|
| `_envelope.json` | — | — | Schema base condiviso (allOf base per tutti gli output) |
| `profiler.input.json` | profiler | A | Descrizione della persona da profilare |
| `profiler.output.json` | profiler | A | Profilo strutturato dei bisogni (→ state/profile.json) |
| `source-analyzer.input.json` | source-analyzer | A | Artefatto reale da destrutturare |
| `source-analyzer.output.json` | source-analyzer | A | Sequenza di passi strutturati (→ state/source-model.json) |
| `simplifier.input.json` | simplifier | A | Un passo + profilo + feedback opzionale del validator |
| `simplifier.output.json` | simplifier | A | Passo riscritto per il profilo |
| `fidelity-validator.input.json` | fidelity-validator | A | Passo originale + passo semplificato |
| `fidelity-validator.output.json` | fidelity-validator | A | Verdetto approved/rejected + divergenze tipizzate |
| `block-detector.input.json` | block-detector | B | Evento utente + passo corrente + contatori sessione |
| `block-detector.output.json` | block-detector | B | blocked (bool) + cause (enum chiuso) |
| `intervener.input.json` | intervener | B | Diagnosi blocco + passo + profilo |
| `intervener.output.json` | intervener | B | Singolo intervento mirato |
| `journey.json` | — | A→B | Artefatto persistito: passi approvati (state/journey.json) |
| `run-state.json` | — | B | Stato runtime sessione con contatori HITL (state/run-\<id\>.json) |
