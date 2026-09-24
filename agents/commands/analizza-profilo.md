---
description: Esegue la Fase B completa (profiler -> eligibility -> navigator) sulle risposte di una persona e produce la scheda "a cosa ho diritto".
argument-hint: [risposte al questionario, es. "compro casa, proprietario, dipendente, lavori da iniziare, no CAF"]
allowed-tools: Read, Write, Task
model: haiku
---

# Fase B — dal profilo alla scheda

Risposte della persona: **$ARGUMENTS**

Sei l'orchestratore descritto in `agents/orchestrator.md`. Questo comando esegue **solo la
Fase B** di `agents/ARCHITETTURA.md`: il catalogo e' gia' verificato, qui non si produce
contenuto nuovo, si incrocia quello esistente. Tier haiku perche' instradi output gia'
strutturati (G-11).

## Precondizione — si verifica prima di tutto

Leggi `agents/state/catalogo.json`.
Se manca o non e' JSON valido: **fermati**. Non inventare misure (G-01), non ricostruire il
catalogo al volo (costa Opus e non e' questo il comando). Rispondi:
`status: hitl_required`, motivo `catalogo assente`, e indica che va eseguita prima la Fase A.

Se `$ARGUMENTS` e' vuoto: poni le domande a scelta multipla dello Step 1 di
`agents/orchestrator.md` e fermati in attesa. Non indovinare un profilo.

## Passi

1. **profiler** (sub-agente `profiler`, haiku) — normalizza `$ARGUMENTS` sulla tassonomia
   chiusa. Input e output secondo `agents/schemas/profiler.input.json` e
   `profiler.output.json`. Scrive `agents/state/profilo.json`.
   Se una risposta non e' mappabile sulla tassonomia: si marca `missing`, non si stima.
2. **eligibility** (sonnet) — incrocia `agents/state/profilo.json` con
   `agents/state/catalogo.json`. Restituisce le misure pertinenti con `confidence` e
   `source_refs` (G-06, G-07).
3. **navigator** (haiku) — per ogni misura trattenuta, i passi concreti di accesso e i
   documenti richiesti. Nessun passo inventato: solo quanto presente nel catalogo.

Ogni passo riceve **JSON, non prosa** (G-14), e legge lo stato da file, non dalla
conversazione (G-12). Non rileggere un file gia' letto in questo run.

## Gate HITL — condizioni numeriche, non impressioni (G-09)

| Condizione | Azione |
|---|---|
| `catalogo.json` assente o invalido | stop, `hitl_required` |
| una misura con `confidence < 0.6` | non entra nella scheda; si dice che il caso va portato a un CAF |
| nessuna misura con `confidence >= 0.6` | scheda vuota dichiarata: "la tua situazione non e' coperta dal catalogo", rinvio a CAF |
| un sub-agente restituisce JSON non conforme allo schema | 1 solo nuovo tentativo con input ridotto; se fallisce, `status: degraded` e si prosegue con i passi rimasti |

Limite di iterazione dell'intero comando: **un solo giro**. Non si richiama `eligibility`
per "provare con un profilo diverso": quello e' un nuovo invio del comando.

## Output

Scrivi `agents/state/run-<id>.json` conforme a `agents/schemas/run-state.json`, poi mostra la
scheda: misure con importi e tetti **identici alla fonte** (G-03), spiegazione in lingua
semplice, prossimo passo concreto, glossario solo dei termini effettivamente usati, e il
disclaimer finale.

Vincolo che vale su tutta la risposta: si spiega cosa esiste e come funziona, **non cosa
conviene fare** (G-04). Ogni decisione va a un CAF o a un commercialista.
