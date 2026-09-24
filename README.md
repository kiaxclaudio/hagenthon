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
  config.py        mappa agente -> tier, timeout/retry/backoff, soglie dei gate, percorsi
  fase_a.py        Fase A eseguibile: dalle fonti al catalogo verificato
  agents.py        Fase B: invocazione degli agenti, resilienza, gate HITL
  validation.py    validazione degli output contro agents/schemas/, esiti degradati
  catalogo.py      lettura e selezione delle misure dal catalogo
  main.py          rotte Flask; session.py, templates/, static/
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
`python-dotenv>=1.0.0` e `jsonschema>=4.21.0`, quest'ultima per validare gli output degli agenti
contro i contratti in `agents/schemas/`.

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

Tutte le variabili sono lette in un solo posto, [`app/config.py`](app/config.py), che tiene anche
la mappa esplicita agente → tier: il model tiering si verifica leggendo quel file, senza inseguire
le chiamate.

| Variabile | Obbligatoria | A che cosa serve |
|---|---|---|
| `ANTHROPIC_API_KEY` | sì, per eseguire il prototipo | chiave del modello |
| `ANTHROPIC_MODEL_CHEAP` | no, ha un default | tier haiku: `orchestrator`, `profiler`, `navigator` |
| `ANTHROPIC_MODEL_WORK` | no, ha un default | tier sonnet: `explainer`, `eligibility` |
| `ANTHROPIC_MODEL_DEEP` | no, ha un default | tier opus: `source-analyzer`, `fidelity-validator` |
| `LLM_TIMEOUT_S` | no, default 60 | timeout per chiamata (G-16) |
| `LLM_MAX_RETRIES` | no, default 3 | numero di retry (G-16) |
| `LLM_BACKOFF_BASE_S` | no, default 1 | attesa del primo retry, poi raddoppia |
| `LLM_BACKOFF_MAX_S` | no, default 20 | tetto dell'attesa fra due tentativi |
| `FLASK_SECRET_KEY` | no | se manca, ne viene generato uno casuale a ogni avvio |
| `FLASK_PORT` | no, default 5000 | porta del server |
| `FLASK_DEBUG` | no, default `false` | modalità di sviluppo |

Gli identificativi di modello non sono mai scritti nel codice come segreti o come valori di
configurazione nascosti: `app/config.py` li legge da `.env` e porta solo un default allineato,
perché la demo non si rompa se una variabile manca.

### Avvio

```bash
python tools/sync_claude.py   # rigenera .claude/ da agents/: i prompt si caricano da li'
python app/fase_a.py          # FASE A: costruisce agents/state/catalogo.json dalle fonti
python app/main.py            # FASE B: stampa l'indirizzo e serve su http://localhost:5000
```

**La Fase A va eseguita prima della Fase B**, una volta sola: senza
`agents/state/catalogo.json` la conversazione non parte, perché le misure verrebbero dalla
memoria del modello invece che da una fonte verificata (G-19). Le fonti ufficiali di partenza —
pagine di Agenzia delle Entrate e circolari INPS — sono committate sotto `agents/state/fonti/`;
`python app/fase_a.py --fonti CARTELLA` ne usa un'altra.

Il prototipo serve una pagina e quattro endpoint (`/api/chat`, `/api/reset`,
`/api/session/<id>`, `/api/diagnostica`), ascolta su `127.0.0.1` e mantiene la sessione in
memoria di processo. Quando il modello non risponde o un contratto non è rispettato, la rotta
non restituisce un errore 500: restituisce un esito con `status: "degraded"` e il rimando al CAF.

**Limite aperto, dichiarato:** il catalogo è versionato in
[`agents/state/catalogo.json`](agents/state/catalogo.json) e contiene **cinque misure verificate
più una esclusa**. La sua copertura è quella delle fonti raccolte in `agents/state/fonti/`, non
l'insieme delle misure italiane: casa, figli e spese mediche sono coperte, lavoro, auto e
under 36 no. Il prodotto lo dichiara invece di riempire il vuoto, e per quei casi rimanda al CAF.

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
la carica, a quale passo e perché non sta nel file dell'agente (G-13). Sono 905 righe che non
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

**Stato dichiarato:** [`docs/validation/`](docs/validation/) contiene gli scenari eseguiti, il
confronto prima/dopo e la prova dei gate HITL. Gli artefatti di Fase A sono versionati in
`agents/state/`: catalogo, misure grezze, spiegazioni e le verifiche del `fidelity-validator`,
una per giro.

La prova che regge meglio è in [`agents/state/verifica-fase-a.json`](agents/state/verifica-fase-a.json):
su sei misure lavorate, il validator ne ha **respinte quattro con divergenze bloccanti** — a un
tetto di 96.000 euro era sparito «per unità immobiliare», un 19% sembrava calcolarsi sull'intera
spesa invece che sulla parte eccedente, e su una misura era comparsa una scadenza che nella fonte
non esiste. Tutte corrette al secondo giro. Una misura è rimasta **esclusa** perché la fonte non
era interpretabile. Il gate non è descritto: ha funzionato.

Il repository cambia durante la gara: se questa riga e i file non concordano, vale
`python tools/check_repo.py`, che misura lo stato nel momento in cui lo si esegue.

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
