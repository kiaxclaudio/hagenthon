# Architettura — decisione canonica

Questo file vince su ogni altro in caso di divergenza. Fonde la proposta di Chiara
(`docs/inbox/chiara-idea.md`) con la struttura in due fasi gia in repository.

## Il prodotto

**"A cosa ho diritto?"** — orientamento sugli aiuti statali italiani per chi parte da zero
di alfabetizzazione fiscale. Spiega quali misure esistono per la sua situazione, cosa
significano e come si accede. **Non consiglia**: rimanda a CAF o commercialista per ogni
decisione (G-04).

## I sette componenti

| Componente | Verbo | Tier | Fase | Tool | Perche quel set |
|---|---|---|---|---|---|
| `orchestrator` | instrada | haiku | A + B | Read, Write, Task | Task per invocare i sub-agenti (limite di iterazioni + parallelismo); Read/Write per lo stato su disco tra un passo e l'altro |
| `source-analyzer` | destruttura | opus | A | Read, Write, Grep, Glob | Grep e Glob per navigare le fonti nel filesystem; unico agente che cerca testo nelle sorgenti |
| `explainer` | riscrive | sonnet | A | Read, Write | Riceve l'input dall'orchestratore, non cerca nel filesystem |
| `fidelity-validator` | verifica | opus | A | **solo Read** | Non puo modificare cio che giudica: la separazione produttore/giudice e imposta dai permessi, non dal prompt |
| `profiler` | normalizza | haiku | B | Read, Write | Legge gli schemi di tassonomia, scrive profilo.json |
| `eligibility` | incrocia | sonnet | B | Read, Write | Legge il catalogo verificato, scrive l'output con confidence e misure pertinenti |
| `navigator` | guida | haiku | B | Read, Write | Legge catalogo e profilo, scrive i percorsi con passi e documenti |

Eliminati: `block-detector` e `intervener`. Nel flusso a scelta multipla non servono, e un
agente che non serve costa punti sul criterio "Adeguatezza degli strumenti".
Rinominato: `simplifier` diventa `explainer` (nome di Chiara, stesso compito).

## Le due fasi

**FASE A — grounding del catalogo.** Offline, una volta, modelli capaci.
```
fonti ufficiali -> source-analyzer(opus) -> explainer(sonnet) -> fidelity-validator(opus)
                                                  ^                       |
                                                  +----- respinto --------+
                                                       max 2 giri, poi HITL
                                            -> state/catalogo.json
```
Il `fidelity-validator` ha solo `Read`: non puo riscrivere cio che giudica. La separazione
fra chi produce e chi approva e una conseguenza dei permessi, non del prompt.

**FASE B — conversazione.** Runtime, modelli economici, legge il catalogo verificato.
```
risposte utente -> profiler(haiku) -> eligibility(sonnet) -> navigator(haiku)
                   state/profilo.json    misure pertinenti     come accedere
```

## Perche questa forma

1. **Il rischio numero uno e l'allucinazione di una cifra.** Percentuali, tetti e scadenze
   non possono venire dalla memoria del modello: in Fase A si ancorano a fonti scaricate,
   ogni dato porta il suo `source_refs`, e la fedelta della riformulazione e verificata da un
   agente separato. Una detrazione sbagliata non e un refuso: e un danno a una persona.
2. **Economia opposta fra le fasi.** Opus gira una volta per catalogo, non per conversazione.
   Il runtime e Haiku e Sonnet che leggono un JSON.
3. **Difesa a due strati contro la consulenza.** `fidelity-validator` semantico in Fase A,
   hook deterministico a runtime (`PostToolUse`).

## Stato esternalizzato

| File | Fase | Contenuto |
|---|---|---|
| `agents/state/catalogo.json` | A | misure verificate, in lingua semplice, con riferimenti |
| `agents/state/profilo.json` | B | profilo dell'utente della sessione |
| `agents/state/run-<id>.json` | B | sessione: passo, misure proposte, escalation |

## Gate HITL

Le due tabelle che seguono sono l'**estratto** dei casi che hanno deciso la forma
dell'architettura, non l'elenco completo: i sette gate HITL e i quattro limiti di iterazione
effettivamente applicati stanno in `agents/orchestrator.md`, che resta coerente con questo file
e lo dettaglia. Qui vince la decisione; li' si legge l'elenco intero.

| Condizione | Azione |
|---|---|
| `fidelity-validator` respinge 2 volte la stessa misura | la misura non entra nel catalogo, esce `hitl_required` |
| `eligibility` con `confidence < 0.6` | non propone: rimanda a CAF dichiarando il perche |
| caso non coperto dal catalogo | rimanda a CAF, non inventa |
| fonte non interpretabile | Fase A si ferma, chiama una persona |

## Limiti di iterazione

| Ciclo | Limite | Al superamento |
|---|---|---|
| explainer <-> fidelity-validator | 2 giri per misura | HITL |
| retry su timeout modello | 3 con backoff | `status: degraded` |
