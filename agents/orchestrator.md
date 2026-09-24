# Orchestratore

## Scope

**Fa:** decide quale sub-agente invocare, in che ordine, con quale input, e applica i limiti di
iterazione e i gate HITL. È l'unico componente che conosce l'intera pipeline.

**Non fa:** non analizza, non semplifica, non giudica la qualità di un contenuto. Tutto il lavoro
di dominio è delegato ai sub-agenti in `agents/subagents/`. L'orchestratore non produce mai
contenuto destinato all'utente finale.

## Model tier

`haiku-4.5`. Prende decisioni di routing su output già strutturati: non serve un modello
più capace. Tenere l'orchestratore economico è ciò che rende sostenibile il loop di validazione.

## Le due fasi

Il sistema è diviso in due fasi con economie opposte. Questa separazione è la scelta
architetturale principale: il lavoro costoso si paga **una volta sola**, il runtime resta leggero.

### Fase A — Preparazione (offline, una volta per artefatto)

Trasforma un artefatto reale in un percorso guidato verificato, salvato su disco.

```
profiler ──▶ source-analyzer ──▶ simplifier ──┐
 (haiku)         (opus)           (sonnet)    │
                                              ▼
                                     fidelity-validator (opus)
                                              │
                            ┌── respinto ─────┤
                            │   (max 2 giri)  │ approvato
                            ▼                 ▼
                       simplifier      journey.json su disco
                            │
                       2° rifiuto ──▶ GATE HITL
```

### Fase B — Sessione guidata (runtime, a ogni interazione)

Legge `journey.json` e accompagna la persona. Nessuna chiamata a modelli costosi.

```
evento utente ──▶ block-detector ──▶ bloccato? ──no──▶ passo successivo
                     (haiku)             │
                                        sì
                                         ▼
                                    intervener (sonnet)
                                         │
                            3 interventi falliti ──▶ GATE HITL
```

## Stato

Tutto lo stato è su disco, non in contesto (G-12):

| File | Fase | Contenuto |
|---|---|---|
| `agents/state/profile.json` | A | profilo della persona |
| `agents/state/source-model.json` | A | l'artefatto reale destrutturato in passi |
| `agents/state/journey.json` | A | percorso guidato approvato dal validator |
| `agents/state/run-<id>.json` | B | sessione in corso: passo, tentativi, interventi |

## Limiti di iterazione

| Ciclo | Limite | Al superamento |
|---|---|---|
| simplifier ↔ fidelity-validator | 2 giri per passo | HITL: il passo esce marcato `hitl_required` e non viene mostrato |
| interventi sullo stesso passo | 3 | HITL: si propone il contatto con una persona |
| retry su timeout modello | 3 con backoff | `status: degraded` |

## Gate HITL

L'escalation umana è **una funzionalità, non un errore**. L'orchestratore la attiva quando:

- `fidelity-validator` respinge due volte lo stesso passo → il contenuto non è affidabile: non si mostra;
- `block-detector` segnala tre blocchi consecutivi sullo stesso passo → il problema non è la spiegazione;
- un sub-agente restituisce `confidence < 0.6` su un passo che contiene importi, date o scadenze (G-03);
- l'artefatto sorgente non è interpretabile (`source-analyzer` in `degraded`).

In tutti i casi il sistema **dice all'utente cosa sta succedendo** e propone un'alternativa.
Non finge di sapere.
