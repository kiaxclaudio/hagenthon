# A cosa ho diritto?

Sistema agentico che orienta chi non ha alfabetizzazione fiscale sugli aiuti statali italiani —
bonus, detrazioni, assegni: quali misure esistono per la sua situazione, che cosa significano e
come si accede. **Non consiglia**: per ogni decisione rimanda a un CAF o a un commercialista.

Hackathon Agentic Coding — Accenture Application Engineering. Tema 02, inclusione finanziaria.
Team: Davide Polito, Chiara Gario.

---

## Il problema e la persona

L'aiuto pubblico esiste, è documentato e gratuito da richiedere. Chi ne avrebbe diritto si ferma
prima: non sa da dove partire, non riconosce le parole, e teme di sbagliare una pratica vera.
«Detrazione IRPEF ripartita in dieci quote annuali di pari importo» è una frase corretta e
inutilizzabile per chi non ha mai aperto un cassetto fiscale.

La persona a cui parliamo non è inesperta di software: è inesperta di burocrazia fiscale. Spesso
non ha un commercialista e non sa che cosa sia un CAF. Ne discendono i vincoli di interfaccia
descritti in [`docs/ux/ux-spec.md`](docs/ux/ux-spec.md): una decisione per schermata, nessuna
casella di testo libero, «non so» sempre ammesso come risposta.

Il rischio di dominio è asimmetrico: **una percentuale sbagliata su un bonus non è un refuso, è
un danno a una persona**. Per questo le cifre vengono da fonti ufficiali con riferimento puntuale,
passano da un verificatore separato e il sistema rimanda sempre a un professionista.

---

## Il sistema agentico

Sette componenti — un orchestratore e sei sub-agenti — divisi in due fasi con economie opposte.
La decisione canonica è [`agents/ARCHITETTURA.md`](agents/ARCHITETTURA.md): in caso di divergenza
fra file, vince quello.

```
FASE A — grounding del catalogo        offline, una volta per fonte, modelli capaci

  fonte ufficiale
        |
        v
  source-analyzer (opus-5)      destruttura la misura: percentuali, tetti, requisiti,
        |                       scadenze, anni di recupero, riferimenti alla fonte
        v
  explainer (sonnet-5)          riscrive la misura in lingua comune
        |
        v
  fidelity-validator (opus-5)   confronta riscrittura e originale — ha SOLO Read
        |
        +-- respinta --> explainer (max 2 giri) --> 2o rifiuto --> GATE HITL
        |
        +-- approvata --> agents/state/catalogo.json


FASE B — conversazione                 a ogni sessione, modelli economici, legge il catalogo

  5 risposte a scelta multipla
        |
        v
  profiler (haiku-4.5)          normalizza su tassonomia chiusa -> profilo.json
        |
        v
  eligibility (sonnet-5)        incrocia profilo e catalogo, con il requisito che rende
        |                       pertinente ogni misura
        |
        +-- confidence < 0.6 oppure caso non coperto --> rimando al CAF, dichiarato
        |
        v
  navigator (haiku-4.5)         passi di accesso, documenti, glossario, disclaimer
```

| Componente | Verbo | Tier | Fase | Strumenti |
|---|---|---|---|---|
| [`orchestrator`](agents/orchestrator.md) | instrada | haiku-4.5 | A + B | Read, Write |
| [`source-analyzer`](agents/subagents/source-analyzer.md) | destruttura | opus-5 | A | Read, Write, Grep, Glob |
| [`explainer`](agents/subagents/explainer.md) | riscrive | sonnet-5 | A | Read, Write |
| [`fidelity-validator`](agents/subagents/fidelity-validator.md) | verifica | opus-5 | A | **solo Read** |
| [`profiler`](agents/subagents/profiler.md) | normalizza | haiku-4.5 | B | Read, Write |
| [`eligibility`](agents/subagents/eligibility.md) | incrocia | sonnet-5 | B | Read, Write |
| [`navigator`](agents/subagents/navigator.md) | guida | haiku-4.5 | B | Read, Write |

Tre proprietà spiegano la forma, e si verificano leggendo i file:

1. **Chi scrive non approva.** `explainer` produce, `fidelity-validator` giudica, e il giudice ha
   solo `Read` fra i `tools` del frontmatter: non può riscrivere ciò che respinge. La separazione
   è una conseguenza dei permessi, non una raccomandazione dentro un prompt.
2. **Due economie opposte.** Opus gira una volta per fonte e il catalogo è persistito su disco;
   una conversazione sono tre invocazioni economiche su un JSON già verificato. Il costo non
   cresce con il numero di sessioni.
3. **L'escalation umana è una funzionalità.** Ogni gate ha una condizione numerica o booleana:
   2 giri sul ciclo di fedeltà, `confidence < 0.6`, 3 misure guidate per sessione, 3 retry con
   backoff. Al limite il sistema dichiara che cosa sta succedendo e indica il CAF.

Altri riferimenti:
[`agents/README.md`](agents/README.md) (indice della cartella ed economia dei token),
[`agents/workflows/main-pipeline.md`](agents/workflows/main-pipeline.md) (la sequenza eseguibile
A1-A4 e B1-B4, con input, output, tier e condizione di uscita per ogni passo),
[`agents/guardrails.md`](agents/guardrails.md) (24 regole numerate, di cui G-18..G-24 di dominio
fiscale), [`agents/schemas/`](agents/schemas/README.md) (15 contratti JSON Schema).

---

## Struttura del repository

```
agents/            fonte unica del sistema agentico
  ARCHITETTURA.md  decisione canonica: componenti, fasi, gate, limiti
  orchestrator.md  routing, stato esternalizzato, limiti di iterazione, gate HITL
  subagents/       i 6 sub-agenti + _TEMPLATE.md, il contratto che tutti compilano
  workflows/       main-pipeline.md, la sequenza eseguibile
  skills/          3 skill: istruzioni lunghe caricate on-demand
  commands/        2 slash command: le sequenze che si rilanciano identiche
  schemas/         15 contratti JSON Schema fra i componenti
  hooks/           3 hook + frasi-vietate.txt
  guardrails.md    24 regole numerate, citate per codice dentro gli agenti
  state/           stato esternalizzato a runtime (vuoto nel repository)
.claude/           GENERATA da agents/ — vedi sotto. Solo settings.json e' scritto a mano
app/               prototipo Flask che la persona usa
docs/              specifica UX, mappa di valutazione, nota sul processo, evidenze
presentation/      presentazione HTML, 8 sezioni, 5:00, file singolo offline
tools/             check_repo.py (linter di consegna), sync_claude.py (generatore di .claude/)
```

### Perché `.claude/` è generata da `agents/`

Due vincoli incompatibili: la consegna vuole la struttura agentica dentro `agents/`, mentre
Claude Code carica sub-agenti, comandi e skill **solo** da `.claude/`. Tenere due copie scritte
a mano significa che divergono, ed è esattamente l'incoerenza che un valutatore automatico trova
al primo confronto fra file.

Qui `agents/` è la fonte unica e `.claude/` è un artefatto generato da
[`tools/sync_claude.py`](tools/sync_claude.py), con copia **byte per byte**:

```
agents/subagents/*.md   ->  .claude/agents/<nome>.md
agents/orchestrator.md  ->  .claude/agents/orchestrator.md
agents/commands/*.md    ->  .claude/commands/<nome>.md
agents/skills/*.md      ->  .claude/skills/<nome>/SKILL.md
```

Nessuna regola vive in due posti, quindi non ci sono due posti in cui può essere sbagliata.
`.claude/settings.json` non è generato: registra i tre hook ed è l'unico file di quella cartella
che si modifica direttamente. Il promemoria sta in [`.claude/GENERATO.md`](.claude/GENERATO.md).

---

## Setup e avvio

### Prerequisiti

- **Python 3** sul `PATH` come `python`. I tre hook e i due strumenti in `tools/` usano solo la
  libreria standard e non richiedono installazione.
- Una **chiave API Anthropic**, necessaria solo per eseguire il prototipo in `app/`.
- Nessun altro servizio: niente database, niente build, niente login esterni.

### Dipendenze

Da [`requirements.txt`](requirements.txt): `anthropic>=0.40.0`, `flask>=3.0.0`,
`python-dotenv>=1.0.0`.

```bash
pip install -r requirements.txt
```

### Variabili d'ambiente

Si copia [`.env.example`](.env.example) in `.env` e si riempie. `.env` è in
[`.gitignore`](.gitignore) e non va mai committato (G-15); `.claude/settings.json` nega anche la
lettura del file da parte del modello.

```bash
cp .env.example .env
```

| Variabile | In `.env.example` | Usata da | Note |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | sì | `app/agents.py` | obbligatoria per eseguire il prototipo |
| `ANTHROPIC_MODEL_CHEAP` | sì | — | tier economico dichiarato per la configurazione |
| `ANTHROPIC_MODEL_WORK` | sì | — | tier di lavoro |
| `ANTHROPIC_MODEL_DEEP` | sì | — | tier di analisi e giudizio |
| `LLM_TIMEOUT_S` | sì | — | timeout per chiamata, previsto da G-16 |
| `LLM_MAX_RETRIES` | sì | — | retry con backoff, previsto da G-16 |
| `FLASK_PORT` | no | `app/main.py` | default 5000 |
| `FLASK_DEBUG` | no | `app/main.py` | default `false` |
| `FLASK_SECRET_KEY` | no | `app/main.py` | ha un default di sviluppo |

**Limite aperto, dichiarato:** oggi `app/agents.py` legge da `.env` solo `ANTHROPIC_API_KEY`;
gli identificatori di modello, il timeout e il numero di retry sono costanti nel codice invece
di venire dalle tre variabili `ANTHROPIC_MODEL_*` e dalle due `LLM_*`. Le tre variabili
`FLASK_*` sono lette dal codice ma non compaiono in `.env.example`. È una divergenza fra
configurazione dichiarata e configurazione applicata, non ancora chiusa.

### Avvio

```bash
python app/main.py          # stampa l'indirizzo e serve su http://localhost:5000
```

Il prototipo espone una pagina e tre endpoint (`/api/chat`, `/api/reset`,
`/api/session/<id>`), carica i prompt degli agenti da `.claude/agents/` — quindi la
sincronizzazione va fatta prima — e mantiene la sessione in memoria di processo.

**Limite aperto, dichiarato:** il prototipo esegue oggi quattro dei sette componenti
(`orchestrator`, `eligibility`, `explainer`, `navigator`). La Fase A di grounding del catalogo
è specificata in `agents/` e non ancora eseguita end-to-end, e `agents/state/` non contiene
ancora un `catalogo.json`.

---

## Gli strumenti

### Tre hook — i vincoli che non dipendono dal prompt

Un guardrail scritto in un `.md` è una richiesta al modello; un hook è un programma che gira
comunque. Sono registrati in `.claude/settings.json` con `timeout: 10` ciascuno e documentati in
[`agents/hooks/README.md`](agents/hooks/README.md).

| Hook | Evento | Che cosa fa | Perché |
|---|---|---|---|
| [`ownership_guard.py`](agents/hooks/ownership_guard.py) | `PreToolUse` su `Write\|Edit` | nega la scrittura sui file dell'altra persona, secondo la mappa di proprietà di `CLAUDE.md` e il ruolo in `.team-role` | due sessioni su `main` senza pull request: la convenzione anti-conflitto diventa un controllo deterministico. Non emette mai `allow` |
| [`anti_consulenza.py`](agents/hooks/anti_consulenza.py) | `PostToolUse` su `Write\|Edit` | cerca nelle scritture sotto `agents/state/` e `app/` le formule da consulenza elencate in [`frasi-vietate.txt`](agents/hooks/frasi-vietate.txt) e le segnala con il numero di riga | è il secondo strato contro il consiglio (G-04), quello deterministico a runtime. Segnala e non blocca: il giudizio semantico spetta al `fidelity-validator` |
| [`session_snapshot.py`](agents/hooks/session_snapshot.py) | `Stop` | scrive `docs/validation/session-<timestamp>.json` con metadati di sessione e inventario di `agents/state/` | l'evidenza di validazione si produce da sola. Registra solo metadati: nessun dato personale nei file committati (G-17) |

I tre script leggono JSON da stdin e scrivono JSON su stdout: si provano senza Claude Code, con i
comandi in `agents/hooks/README.md`, sezione "Come si provano".

### Due slash command — le sequenze che si rilanciano identiche

Documentati in [`agents/commands/README.md`](agents/commands/README.md). Un comando esiste solo
se una sequenza va rieseguita identica più volte; una sequenza che si usa una volta sta nel
workflow.

| Comando | Fase | Tratto eseguito | Perché si rilancia |
|---|---|---|---|
| [`/analizza-profilo`](agents/commands/analizza-profilo.md) | B | `profiler` → `eligibility` → `navigator` | una volta per persona e per scenario di prova |
| [`/verifica-catalogo`](agents/commands/verifica-catalogo.md) | A | `explainer` ↔ `fidelity-validator`, max 2 giri | quando una fonte cambia o una misura è uscita `hitl_required` |

### Tre skill — istruzioni lunghe caricate on-demand

Documentate in [`agents/skills/README.md`](agents/skills/README.md), che dichiara per ognuna chi
la carica, a quale passo e perché non sta nel file dell'agente (G-13). Sono 782 righe che non
pesano finché non servono, e nessuna invocazione ne carica più di una.

| Skill | Caricata da | Quando |
|---|---|---|
| [`plain-language`](agents/skills/plain-language.md) | `explainer` | passo A2, a ogni riscrittura e a ogni correzione dopo un rifiuto |
| [`fidelity-diff-taxonomy`](agents/skills/fidelity-diff-taxonomy.md) | `fidelity-validator` | passo A3, a ogni verifica |
| [`hitl-escalation`](agents/skills/hitl-escalation.md) | `orchestrator` | quando scatta un gate HITL, in Fase A come in Fase B |

Lo stesso file dichiara i quattro agenti che non caricano alcuna skill, con il motivo: un agente
senza skill è una scelta, non una dimenticanza.

### Il linter di consegna

[`tools/check_repo.py`](tools/check_repo.py) esegue dodici controlli meccanici: struttura,
marcatori residui, validità dei JSON, link relativi, riferimenti fra backtick, presentazione
senza risorse remote, segreti, gestione di `.env`, coerenza fra i nomi degli agenti citati nei
vari indici, coerenza dei model tier fra prosa e frontmatter, sezioni obbligatorie del template,
stato git. Un difetto oggettivo è `FAIL`; una scelta editoriale ancora aperta è `WARN`.

---

## Come si verifica il repository

```bash
python tools/check_repo.py            # report leggibile, exit 1 se c'e' un FAIL
python tools/check_repo.py --strict   # anche i WARN fanno fallire
python tools/check_repo.py --json     # stesso report in forma strutturata
python tools/sync_claude.py --check   # exit 1 se .claude/ e agents/ divergono
python tools/sync_claude.py           # rigenera .claude/ da agents/
```

Nessuna dipendenza esterna: entrambi gli strumenti usano solo la libreria standard.
Le affermazioni di merito che nessun linter può controllare — se uno scope è davvero netto, se
due skill non si sovrappongono — sono voci manuali in
[`docs/PRE-FREEZE-CHECKLIST.md`](docs/PRE-FREEZE-CHECKLIST.md).

---

## Validazione e nota sul processo

Gli scenari previsti per la prova end-to-end sono quattro, descritti in
[`docs/inbox/chiara-idea.md`](docs/inbox/chiara-idea.md): proprietario che ristruttura, coppia
con figlio appena nato, disoccupato under 36, pensionato con spese mediche.

**Stato dichiarato:** [`docs/validation/`](docs/validation/) è oggi vuota. Le evidenze di
sessione sono prodotte automaticamente dall'hook `session_snapshot.py` a ogni chiusura di
sessione Claude Code, ma nessuno snapshot è stato ancora committato, e non è committato alcun
output reale di agente. La robustezza è oggi specificata e non ancora dimostrata da un caso di
rottura catturato.

- [`docs/EVALUATION-MAP.md`](docs/EVALUATION-MAP.md) — ogni criterio di giudizio collegato al
  file e alla sezione che lo soddisfa, con una sezione "Cosa manca" scritta apposta per essere
  letta. È l'inventario onesto delle lacune aperte.
- [`docs/process-note.md`](docs/process-note.md) — come è stata usata l'AI, che cosa non le è
  stato delegato, che cosa è stato revisionato a mano, i limiti identificati.
- [`docs/ux/ux-spec.md`](docs/ux/ux-spec.md) — la specifica di interfaccia, con i contrasti
  calcolati e le deroghe al brand motivate una per una;
  [`docs/ux/accenture-tokens.css`](docs/ux/accenture-tokens.css) ne contiene i valori.
- [`docs/COLLABORAZIONE.md`](docs/COLLABORAZIONE.md) e [`CLAUDE.md`](CLAUDE.md) — come due
  persone lavorano sullo stesso branch senza conflitti, e la mappa di proprietà dei file che
  l'hook `ownership_guard.py` rende eseguibile.
- [`presentation/index.html`](presentation/index.html) — la presentazione in 8 sezioni da
  5 minuti, file singolo che si apre offline;
  [`presentation/README.md`](presentation/README.md) ne elenca sezioni e tempi.
