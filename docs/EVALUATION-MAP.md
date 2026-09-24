# Mappa di valutazione

Questo file collega ognuno degli otto criteri di giudizio ai file e alle sezioni che lo
soddisfano **oggi**, e dichiara che cosa manca ancora. Serve a due lettori diversi:

- al valutatore automatico, per trovare l'evidenza senza cercarla;
- a noi, per vedere in un colpo d'occhio dove siamo scoperti.

**Regola di compilazione:** una riga sta in questa mappa solo se il file esiste e la sezione
citata c'e' davvero. Nessuna promessa, nessun "in arrivo" nella colonna dell'evidenza: le cose
mancanti stanno nella sezione "Cosa manca", che e' scritta apposta per essere letta.

**Stato dell'istantanea.** Verificata il 24/09 sul working tree locale. Il repository cambia
durante la gara: la verifica sempre aggiornata e' `python tools/check_repo.py`, che controlla
meccanicamente marcatori residui, JSON, link, nomi degli agenti, model tier, segreti e struttura.
Ultima esecuzione: 7 OK, 4 WARN, 1 FAIL (marcatori di tema ancora da compilare).

Legenda copertura: **Coperto** = evidenza completa e verificabile · **Parziale** = evidenza
presente ma con lacune dichiarate · **Scoperto** = nessuna evidenza verificabile.

---

## Quadro sintetico, in ordine di peso

> **Nota di stato, 24/09 ore 14:45.** Questo documento e stato scritto a meta gara, quando il
> sistema era specificato ma non ancora eseguibile. Diverse sue affermazioni sulle lacune sono
> state superate dai fatti. La fonte di verita sempre aggiornata e `python tools/check_repo.py`.


| Peso | Criterio | Evidenza principale | Copertura |
|---|---|---|---|
| 24% | Profondita' agentica | `agents/orchestrator.md`, `agents/workflows/main-pipeline.md`, 6 sub-agenti, 3 skill, 15 schemi JSON | Parziale |
| 19% | Qualita' delle istruzioni | `agents/subagents/_TEMPLATE.md`, frontmatter dei 6 agenti, `agents/guardrails.md`, `agents/skills/README.md` | Parziale |
| 15% | Robustezza | `agents/orchestrator.md` (limiti e gate), sezione Fallback di ogni agente, `agents/skills/hitl-escalation.md` | Parziale |
| 12% | Efficienza dei token | `CLAUDE.md` par. 5, `agents/README.md` "Economia dei token", `agents/skills/README.md` "Mappa dei caricamenti" | Parziale |
| 12% | Qualita' tecnica | `.env.example`, `.gitignore`, G-15/G-16/G-17, `app/README.md` "Requisiti tecnici non negoziabili" | Scoperto in gran parte |
| 11% | Adeguatezza degli strumenti | campo `tools` nel frontmatter dei 6 agenti, `agents/subagents/fidelity-validator.md` "Strumenti assegnati" | Parziale |
| 7% | Documentazione | `README.md`, `agents/README.md`, `docs/PLAYBOOK.md`, `docs/COLLABORAZIONE.md`, `docs/process-note.md` | Parziale |
| 0% | Qualita' dell'idea | non valutata | — |

---

## 24% — Profondita' agentica

> "Il sistema agentico e' strutturato? Orchestrazione, sub-agenti, workflow multi-step, skills,
> stato esternalizzato, output strutturati."

### Evidenza

| File | Sezione | Che cosa dimostra |
|---|---|---|
| `agents/orchestrator.md` | "Le due fasi" | Orchestrazione esplicita: chi invoca chi, in che ordine, con quali cicli |
| `agents/orchestrator.md` | "Stato" | Stato esternalizzato: quattro file su disco, con fase e contenuto dichiarati |
| `agents/orchestrator.md` | "Limiti di iterazione", "Gate HITL" | Controllo del ciclo: tre limiti numerici, quattro condizioni di escalation |
| `agents/workflows/main-pipeline.md` | tabelle Fase A e Fase B | Workflow multi-step eseguibile: 5 passi in A, 3 in B, ognuno con input, output, tier, condizione di uscita |
| `agents/subagents/*.md` (6 file) | intero | Sub-agenti separati, un verbo per agente, con frontmatter `name`/`tools`/`model`/`maxTurns` |
| `agents/skills/README.md` | "Mappa dei caricamenti" | Skill con condizione di caricamento dichiarata per ciascuna, e quattro agenti che dichiarano di non caricarne |
| `agents/schemas/` | 15 file JSON | Output strutturati: envelope comune (`_envelope.json`) piu' input/output per agente |
| `agents/schemas/README.md` | "Campi comuni a tutti gli output" | Contratto uniforme `status`/`confidence`/`source_refs`/`payload`, che rende possibile instradare senza conoscere il dominio |

### Cosa manca

- **AGGIORNATO 24/09 h14:45 — ora e' eseguibile.** `app/` contiene dieci moduli Python, il
  collaudo offline passa 31 verifiche su 31 e cinque percorsi girano end-to-end. Resta un
  orchestratore in codice che legga questi file. Il sistema e' specificato, non dimostrato.
- `agents/state/` contiene 33 artefatti versionati: catalogo verificato, misure grezze,
  spiegazioni, verifiche del validator e fonti. I file di stato dichiarati
  nella sezione "Stato" esiste come esempio. Lo stato esternalizzato e' descritto, non esibito.
- Nessun output reale di agente e' committato: non c'e' un solo JSON prodotto da un run.
- Il ciclo `simplifier` ↔ `fidelity-validator` e' la parte piu' interessante del sistema e non
  esiste una traccia di un giro completo, nemmeno simulata a mano.

---

## 19% — Qualita' delle istruzioni

> "Scope chiaro, output format definito, step-by-step, vincoli espliciti, coerenza tra file,
> no sovrapposizioni."

### Evidenza

| File | Sezione | Che cosa dimostra |
|---|---|---|
| `agents/subagents/_TEMPLATE.md` | intero | Contratto unico: dieci sezioni obbligatorie, con il motivo per cui esistono |
| `agents/subagents/*.md` | "Scope" | Ogni agente dichiara **cosa non fa** nominando l'agente competente: e' la prova dell'assenza di sovrapposizioni |
| `agents/subagents/*.md` | frontmatter | `name`, `description`, `tools`, `model`, `maxTurns` in forma macchina-leggibile |
| `agents/subagents/*.md` | "Input / Output" | Formato di output vincolato a uno schema JSON nominato |
| `agents/guardrails.md` | G-01..G-17 | 17 regole numerate e citabili, richiamate per codice dentro gli agenti e dentro gli schemi |
| `agents/workflows/main-pipeline.md` | tabelle A e B | Procedura passo per passo con condizione di uscita per ogni passo |
| `agents/skills/README.md` | "Regola di non sovrapposizione", "Aggiungere una skill" | Confini fra skill espliciti: `PL-xx` come si scrive, `D-xx` come si giudica, `HE-xx` cosa si fa quando si escala |
| `CLAUDE.md` | par. 2 e 6 | Proprieta' dei file e regole di stile comuni: e' il meccanismo che tiene coerenti due sessioni in parallelo |

### Cosa manca

- **Il template non e' applicato per intero.** `CLAUDE.md` par. 6 dice "senza eccezioni", ma
  tutti e sei gli agenti non compilano le sezioni "Passi" e "Errori gestiti" del template.
  Da risolvere in un verso o nell'altro: completare gli agenti, oppure ridurre il template e
  la frase in `CLAUDE.md`. Il linter lo segnala come WARN.
- Quattro agenti contengono ancora un segnaposto di tema al posto della tassonomia di dominio
  (`profiler`, `source-analyzer`, `simplifier`, `block-detector`): senza lo scenario scelto le
  istruzioni restano generiche proprio nel punto in cui dovrebbero essere specifiche.
- `agents/subagents/fidelity-validator.md` usa il marcatore `TODO-TEMA:` per dire "nessun
  segnaposto qui". E' un uso contro-intuitivo che il linter conta come marcatore residuo:
  va riformulato in prosa.
- L'orchestratore non ha frontmatter, mentre i sei sub-agenti ce l'hanno: la forma non e'
  uniforme sui sette componenti.

---

## 15% — Robustezza

> "Fallback, gestione degli errori, escalation umana intenzionale (HITL), limiti di iterazione."

### Evidenza

| File | Sezione | Che cosa dimostra |
|---|---|---|
| `agents/orchestrator.md` | "Limiti di iterazione" | Tre limiti numerici: 2 giri validator, 3 interventi, 3 retry con backoff |
| `agents/orchestrator.md` | "Gate HITL" | Quattro condizioni di escalation, tutte verificabili, con l'obbligo di dire all'utente cosa sta succedendo |
| `agents/subagents/*.md` | "Fallback" | Ogni agente dichiara che cosa produce su input incompleto o illeggibile, sempre con un output valido in `degraded` |
| `agents/subagents/*.md` | "Gate HITL / Iterazioni" | Condizione di escalation per agente, coerente con i limiti dell'orchestratore |
| `agents/skills/hitl-escalation.md` | intero | Procedura di escalation con codici `HE-xx`, caricata solo quando un gate scatta |
| `agents/guardrails.md` | G-08, G-09, G-10, G-16 | Limite dichiarato per ogni ciclo, gate come condizione verificabile, divieto di ricorsione, timeout e retry |
| `agents/schemas/_envelope.json` | `status`, `confidence` | Lo stato degradato e la richiesta di intervento umano sono valori del contratto, non testo libero |
| `agents/schemas/run-state.json` | contatori di sessione | I contatori su cui scattano i gate sono persistiti, quindi verificabili a posteriori |

### Cosa manca

- **AGGIORNATO — i gate sono dimostrati.** `docs/validation/` contiene scenari eseguiti,
  confronto prima/dopo e output reale dei gate HITL:
  non c'e' un caso di rottura provocato e catturato. Il playbook prevede la passata di
  robustezza alle 3:15; finche' non e' fatta, la robustezza e' dichiarata e non dimostrata.
- Timeout, retry e backoff esistono come parametri in `.env.example` e come regola G-16, ma
  non esiste codice che li applichi.
- Nessun esempio committato di output con `status: "degraded"` o `"hitl_required"`.
- `maxTurns` nel frontmatter e i limiti in prosa convivono senza che un controllo ne verifichi
  l'allineamento: la coerenza dei due numeri e' oggi una voce manuale della checklist.

---

## 12% — Efficienza dei token

> "La soluzione e' ottimizzata per ridurre il consumo di token?"

### Evidenza

| File | Sezione | Che cosa dimostra |
|---|---|---|
| `agents/README.md` | "Le tre decisioni architetturali", punto 1 | Due fasi con economie opposte: il costoso si paga una volta per artefatto, il runtime legge da disco |
| `agents/orchestrator.md` | "Le due fasi" | La Fase B non invoca modelli costosi: la separazione e' nella pipeline, non solo nella prosa |
| `agents/subagents/*.md` | "Model tier" | Tier per compito, motivato in una riga, dichiarato due volte per agente (prosa e frontmatter) e verificato automaticamente |
| `agents/skills/README.md` | "Mappa dei caricamenti" | Caricamento on-demand quantificato: 710 righe di skill contro 202 righe di file agente, con la condizione esatta che attiva ciascuna |
| `agents/skills/README.md` | "Agenti che non caricano alcuna skill" | Il non-caricamento e' una scelta dichiarata, con il motivo per agente |
| `CLAUDE.md` | par. 5 | Disciplina dei token come regola di progetto: tiering, JSON invece di prosa, stato su disco, niente riletture |
| `agents/guardrails.md` | G-11..G-14 | Le stesse regole in forma verificabile su un output |

### Cosa manca

- **Nessun token misurato.** `agents/README.md` chiude con un segnaposto che promette la tabella
  dei token per agente su un run reale: senza un run, la tabella non esiste. E' la lacuna piu'
  citabile da un valutatore su questo criterio.
- Le stime in `agents/skills/README.md` sono in righe e parole, con una conversione indicativa
  in token: e' una stima dichiarata come tale, non una misura.
- **Affermazione da correggere:** `agents/README.md` dice "Due agenti su tre girano su Haiku".
  La tabella nello stesso file ne conta 3 su 7 componenti (2 su 6 sub-agenti). Un valutatore
  automatico conta le righe della tabella: la frase va riscritta.
- Nessuna evidenza di prompt caching o di riuso di contesto fra invocazioni.

---

## 12% — Qualita' tecnica

> "Error handling, timeout, retry, configurazione sicura (secrets, env), model tiering."

### Evidenza

| File | Sezione | Che cosa dimostra |
|---|---|---|
| `.env.example` | intero | Configurazione fuori dal codice: chiave, tre modelli per tier, `LLM_TIMEOUT_S`, `LLM_MAX_RETRIES` |
| `.gitignore` | prime righe | `.env`, `.env.local`, `*.key`, `*.pem` esclusi; esclusi anche gli stati di run |
| `agents/guardrails.md` | G-15, G-16, G-17 | Nessun segreto nel repo, timeout e retry obbligatori, nessun dato personale reale |
| `app/README.md` | "Requisiti tecnici non negoziabili" | I vincoli tecnici sono scritti prima del codice: segreti da `.env`, retry, validazione degli output contro lo schema |
| `agents/subagents/*.md` | frontmatter `model` | Model tiering in forma macchina-leggibile, verificato contro la prosa da `tools/check_repo.py` |
| `tools/check_repo.py` | intero | Verifica meccanica di segreti, JSON, link e coerenza, con exit code non zero |

### Cosa manca

- **Non esiste codice applicativo.** Error handling, timeout, retry e validazione degli output
  contro gli schemi sono oggi requisiti scritti in `app/README.md`, non righe eseguibili.
  Questo criterio resta in gran parte scoperto finche' `app/` non contiene un client con quelle
  quattro proprieta'.
- Gli identificatori di modello in `.env.example` non sono omogenei: uno ha il suffisso di data,
  gli altri due no. Vanno verificati sulla documentazione ufficiale prima del freeze.
- Nessun test, nessun controllo automatico oltre a `tools/check_repo.py`.
- Nessuna gestione esplicita del rate limiting o degli errori 429/529 fra i requisiti.

---

## 11% — Adeguatezza degli strumenti

> "Tools e agenti sono scelti correttamente per il task? Ne' troppo pochi ne' ridondanti tra loro."

### Evidenza

| File | Sezione | Che cosa dimostra |
|---|---|---|
| `agents/subagents/*.md` | frontmatter `tools` | Permessi minimi per agente: `Read` sola lettura al validator e al detector, `Read, Write` a chi produce artefatti, `Read, Write, Grep, Glob` al solo `source-analyzer`, che deve navigare l'artefatto |
| `agents/subagents/fidelity-validator.md` | "Strumenti assegnati" | Il giudice ha solo `Read`: la separazione fra chi produce e chi approva e' una conseguenza dei permessi, non una raccomandazione nel prompt |
| `agents/README.md` | tabella dei componenti | Un verbo per agente: se due agenti potessero scambiarsi il lavoro, uno sarebbe di troppo |
| `agents/subagents/*.md` | "Scope / Non fa" | Confini incrociati espliciti: ogni agente nomina chi si occupa di cio' che lui non fa |
| `agents/skills/README.md` | "Agenti che non caricano alcuna skill" | Anche l'assenza di uno strumento e' motivata |

### Cosa manca

- **Non esiste un inventario unico degli strumenti.** I `tools` stanno nel frontmatter di sei
  file; nessuna tabella li mette in fila con la giustificazione per ognuno. E' esattamente
  cio' che questo criterio chiede di leggere, ed e' sparso.
- `agents/orchestrator.md` non dichiara strumenti: non si sa con quali permessi giri il
  componente che coordina tutti gli altri.
- Nessun MCP, nessuno strumento esterno, nessuna motivazione del perche' non servano.
- Gli strumenti dichiarati (`Read`, `Write`, `Grep`, `Glob`) sono quelli dell'ambiente Claude
  Code: nessun file mostra come vengano concessi a runtime.

---

## 7% — Documentazione

> "README chiaro, flusso agentico spiegato, setup, prerequisiti, tool/MCP/skill documentati."

### Evidenza

| File | Sezione | Che cosa dimostra |
|---|---|---|
| `README.md` | "Il sistema agentico" | Il flusso agentico in un diagramma con le due fasi, i tier e i punti di escalation |
| `README.md` | "Struttura del repository" | Mappa delle quattro cartelle di consegna |
| `agents/README.md` | "Come si legge questa cartella" | Indice di `agents/`: a che cosa serve ogni file |
| `agents/skills/README.md` | "Mappa dei caricamenti" | Le skill sono documentate una per una, con chi le carica e quando |
| `agents/schemas/README.md` | "Indice dei file di schema" | I 15 contratti elencati con agente, fase e descrizione |
| `docs/PLAYBOOK.md` | intero | Piano operativo delle 5 ore e definizione dei quattro deliverable |
| `docs/COLLABORAZIONE.md` | intero | Come due persone lavorano sullo stesso repo senza conflitti |
| `docs/process-note.md` | par. 1-6 | Nota sul processo: divisione del lavoro, uso dell'AI, revisione umana, limiti, registro |

### Cosa manca

- **Il README e' ancora uno scheletro.** Sette righe contengono un segnaposto, compresi il
  titolo, il problema, la soluzione, il setup e la validazione. E' il primo file che il
  valutatore automatico legge.
- Nessun prerequisito e nessun comando di avvio: la sezione "Setup" contiene una sola riga
  (`cp .env.example .env`) e un segnaposto.
- `docs/validation/` e popolata e coerente con il README.
- Gli strumenti non sono documentati in prosa da nessuna parte (vedi criterio 11%).

---

## Incoerenze fra file da chiudere prima del freeze

Elencate perche' un valutatore automatico confronta i file fra loro. Sono verificate, non ipotesi.

| # | Incoerenza | File coinvolti | Come si chiude |
|---|---|---|---|
| I-1 | "Due agenti su tre girano su Haiku": la tabella nello stesso file ne conta 3 su 7 | `agents/README.md` "Economia dei token" contro la tabella dei componenti | Riscrivere la frase con il conteggio esatto |
| I-2 | Il template si applica "senza eccezioni", ma sei agenti su sei omettono "Passi" e "Errori gestiti" | `CLAUDE.md` par. 6, `agents/subagents/_TEMPLATE.md`, i 6 agenti | Completare le sezioni oppure ridurre il template |
| I-3 | Il marcatore di tema usato per dire "nessun marcatore" | `agents/subagents/fidelity-validator.md` "Strumenti assegnati" | Riformulare in prosa: il marcatore va tolto |
| I-4 | Menzioni meta del marcatore che il linter conta come residui | docs/process-note.md | Citare il marcatore come "segnaposto di tema" in prosa |
| I-5 | Il frontmatter c'e' sui sei sub-agenti e non sull'orchestratore | `agents/orchestrator.md` | Aggiungerlo, o dichiarare perche' non serve |
| I-6 | Identificatori di modello disomogenei in `.env.example` | `.env.example` | Verificarli sulla documentazione ufficiale |

---

## Come si verifica questa mappa

```bash
python tools/check_repo.py          # report leggibile, exit 1 se qualcosa fallisce
python tools/check_repo.py --strict # anche i WARN fanno fallire
python tools/check_repo.py --json   # stesso report in forma strutturata
```

Il linter copre le affermazioni meccaniche di questa mappa: esistenza dei file, validita' dei
JSON, link, marcatori residui, allineamento fra nomi degli agenti e file, coerenza dei model
tier fra prosa e frontmatter, segreti, struttura di consegna. Le affermazioni di merito
(un agente ha davvero uno scope netto, una skill non si sovrappone a un'altra) restano
giudizio umano e sono elencate in `docs/PRE-FREEZE-CHECKLIST.md` come voci manuali.
