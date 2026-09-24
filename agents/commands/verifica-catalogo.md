---
description: Rilancia il giro explainer <-> fidelity-validator su una misura del catalogo, con il limite di 2 iterazioni e l'escalation HITL della Fase A.
argument-hint: [id o nome della misura, es. "bonus-ristrutturazione-50" oppure "assegno unico"]
allowed-tools: Read, Write, Task
model: haiku
---

# Fase A — rilancio del ciclo di fedelta' su una misura

Misura da riverificare: **$ARGUMENTS**

Questo comando esegue **solo il tratto A2-A3** di `agents/workflows/main-pipeline.md`, cioe'
il giro `explainer` <-> `fidelity-validator`, su una misura sola. Serve quando una misura e' stata corretta alla fonte, e' uscita `hitl_required`, o si
sospetta una riformulazione infedele. Non ricostruisce il catalogo e non esegue
`source-analyzer`: se il modello della fonte non esiste, questo comando non e' quello giusto.

Tu qui fai solo da orchestratore (haiku): non riscrivi e non giudichi tu il testo. Chi
produce e chi approva restano separati, ed e' una conseguenza dei permessi, non del prompt —
`fidelity-validator` ha **solo Read** e non puo' modificare cio' che giudica.

## Precondizioni

1. Se `$ARGUMENTS` e' vuoto: chiedi quale misura e fermati. Non verificare "tutto il
   catalogo": costa Opus per ogni misura e non e' quello che il comando promette.
2. Leggi `agents/state/catalogo.json` e individua **una sola** misura corrispondente.
   - nessuna corrispondenza -> fermati, dillo, elenca gli id disponibili;
   - piu' di una corrispondenza -> fermati ed elencale, fai scegliere. Non prendere la prima.
3. Serve il testo di origine della misura (`source_refs` nella voce di catalogo). Se manca,
   il confronto non e' possibile: `hitl_required`, motivo `fonte non tracciata` (G-07).

## Il ciclo — massimo 2 giri (G-08)

| Giro | Chi | Cosa |
|---|---|---|
| n | `explainer` (sonnet) | riscrive la misura in lingua semplice partendo dal testo di origine e, dal secondo giro, dai rilievi del validator. Carica la skill `plain-language` solo ora |
| n | `fidelity-validator` (opus, solo Read) | confronta origine e riscrittura e classifica ogni divergenza con la skill `fidelity-diff-taxonomy`. Verdetto `approved` / `rejected` con i rilievi |

- verdetto `approved` -> aggiorna la voce nel catalogo, `status: ok`, e riporta al giro quanti
  giri sono serviti;
- verdetto `rejected` al **secondo** giro -> **la misura non entra nel catalogo**. Si marca
  `status: hitl_required` con i rilievi del validator, e si chiama una persona. Non c'e' un
  terzo tentativo: al limite si escala, non si ritenta.

Tieni il conteggio dei giri in modo esplicito nella risposta. Un limite che non si vede
contato non e' un limite.

## Errori e degradazione

| Situazione | Cosa fare |
|---|---|
| un sub-agente restituisce prosa invece di JSON conforme (G-05) | 1 sola ri-richiesta con lo schema in chiaro; se fallisce ancora, `status: hitl_required` e si chiama una persona (G-08: al limite si escala, non si ritenta) |
| timeout del modello | fino a 3 tentativi con backoff esponenziale (G-16), poi `status: degraded` |
| il validator segnala un numero, una data o un riferimento normativo diverso dalla fonte | e' G-03: rifiuto immediato, non negoziabile, non conta come "differenza di stile" |

## Output

Non narrare il ciclo. Restituisci:

1. il JSON conforme a `agents/schemas/fidelity-validator.output.json` dell'ultimo verdetto;
2. una riga di esito: misura, giri usati su 2, `status` finale, e se il catalogo e' stato
   aggiornato oppure no;
3. se `hitl_required`: cosa deve guardare la persona, in una frase.
