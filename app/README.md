# app/ — il prototipo

Contiene la soluzione che la persona usa. È l'esecutore del sistema descritto in `agents/`,
non un'applicazione indipendente.

Principio: l'app implementa i contratti in `agents/schemas/`, non li ridefinisce.
Se serve un campo nuovo, si cambia lo schema (con il consenso di entrambi), non il codice da un lato solo.

## Prerequisiti

- Python 3.11 o superiore (testato su 3.14).
- Una chiave API Anthropic.
- Dipendenze: `anthropic`, `flask`, `python-dotenv`, `jsonschema` (in `requirements.txt`).

```bash
pip install -r requirements.txt
cp .env.example .env        # poi apri .env e metti ANTHROPIC_API_KEY
```

Tutte le variabili sono documentate in `.env.example`: identificativi dei modelli per i tre
tier, timeout, numero di retry, backoff, porta. Nel codice non c'è nessun segreto e nessun
identificativo di modello scritto a mano.

## Avvio

```bash
python app/main.py                 # http://localhost:5000
```

Con `FLASK_PORT` si cambia porta. Rotte disponibili:

| Rotta | Metodo | Cosa fa |
|---|---|---|
| `/` | GET | l'interfaccia |
| `/api/chat` | POST | un turno di conversazione, ed eventualmente la Fase B completa |
| `/api/reset` | POST | chiude la sessione e ne apre una nuova |
| `/api/session/<id>` | GET | lo stato della sessione, riletto da `agents/state/run-<id>.json` |
| `/api/diagnostica` | GET | tier, modelli configurati, presenza del catalogo (nessun segreto) |

## Le due fasi

**Fase A — costruzione del catalogo.** Offline, una volta sola, modelli capaci.

```bash
# salva le pagine ufficiali in agents/state/fonti/ come .txt o .html
python app/fase_a.py --anno 2026 --versione 1.0.0
```

`source-analyzer` (opus) destruttura la fonte, `explainer` (sonnet) la riscrive in lingua
semplice, `fidelity-validator` (opus) verifica che le cifre non siano cambiate. Il ciclo
explainer ⇄ fidelity-validator ha un limite di **2 giri**: alla seconda bocciatura la misura
non entra nel catalogo e finisce in `misure_escluse`, per una revisione umana.
Il risultato è `agents/state/catalogo.json`, validato prima di essere scritto.

Accanto a ogni fonte si può mettere un file `<nome>.<est>.meta.json` con `ente`, `url_fonte`
e `data_consultazione`: la provenienza non si indovina.

**Fase B — conversazione.** A ogni sessione, modelli economici, legge il catalogo da disco.

`orchestrator` (haiku) conduce le domande, `profiler` (haiku) normalizza le risposte sulla
tassonomia chiusa, `eligibility` (sonnet) incrocia profilo e catalogo, `navigator` (haiku)
compone i passi per al massimo 3 misure. Senza catalogo la Fase B non parte: rimanda a un CAF
invece di improvvisare.

## Modalità demo (nessuna chiamata all'API)

```bash
DEMO_MODE=true python app/main.py      # oppure DEMO_MODE=true in .env
```

Con `DEMO_MODE=true` l'app **non chiama mai il modello**: al posto della risposta dell'API,
`agents._chiama` legge un output registrato da `app/demo/`. Da lì in poi il percorso è lo
stesso di sempre — parsing, validazione contro `agents/schemas/`, gate HITL, stato su file —
quindi un file di demo che non rispetta il contratto fallisce esattamente come fallirebbe il
modello. L'interfaccia dichiara la modalità con una fascia gialla in alto: una demo finta non
dichiarata sarebbe un inganno.

**Perché è legittimo.** La Fase A è già stata eseguita e il suo risultato è persistito in
`agents/state/catalogo.json`. A runtime il sistema deve solo leggere il catalogo verificato:
la modalità demo non è una scorciatoia, è la conseguenza naturale della separazione fra le due
fasi. Quello che la demo evita è la spesa e il rischio di rete della Fase B, non un controllo.

**Cosa è registrato e cosa no.** Nei file di scenario stanno la conversazione dell'orchestratore
e l'output del profiler: nessun dato fiscale. Misure, percentuali, tetti e `source_refs`
vengono dal catalogo verificato, e gli output di `eligibility` e `navigator` sono ricomposti da
quello. L'unico output di dominio registrato per intero è quello dello scenario di escalation,
dove non c'è nessuna misura da mostrare. Se il catalogo non c'è, la demo non inventa misure:
scatta il gate e il sistema rimanda al CAF.

| Scenario | File | Esito osservato (catalogo 0.1.0) |
|---|---|---|
| Ristrutturazione casa | `app/demo/scenario-casa.json` | 2 schede: bonus ristrutturazioni, bonus mobili |
| Figlio appena nato | `app/demo/scenario-figlio.json` | 2 schede: assegno unico, bonus asilo nido |
| Cerca lavoro, under 36 | `app/demo/scenario-lavoro-under36.json` | escalation `caso_non_coperto_dal_catalogo`: il catalogo non copre il lavoro |
| Pensionato, spese mediche | `app/demo/scenario-spese-mediche.json` | 1 scheda: detrazione spese sanitarie |
| **Caso non risolvibile** | `app/demo/scenario-escalation.json` | escalation `confidence_bassa`: nessuna misura, rimando al CAF |

Lo scenario si sceglie dalla **prima** risposta della persona, per parole chiave. Un caso che
non corrisponde a nessuno scenario finisce su quello di escalation: anche in demo, un caso non
previsto si dichiara.

## Collaudo senza chiave API

```bash
python app/collaudo.py
```

Esegue 31 verifiche con le risposte del modello simulate: mappa dei tier, classificazione
degli errori, backoff, ri-richiesta dopo un output fuori schema, gate HITL della Fase B,
limite di iterazione della Fase A, stato su file, scenari della modalità demo. Non usa la rete.

## Dove stanno le cose

| File | Ruolo |
|---|---|
| `config.py` | mappa agente → tier, modelli da `.env`, timeout, retry, soglie, percorsi |
| `validation.py` | validazione contro `agents/schemas/`, buste e fallback degradati |
| `catalogo.py` | lettura del catalogo verificato e pre-filtro delle misure candidate |
| `agents.py` | chiamate al modello e Fase B con i suoi gate |
| `fase_a.py` | Fase A, eseguibile da riga di comando |
| `session.py` | stato della sessione su `agents/state/` |
| `main.py` | rotte Flask |
| `demo.py` | modalità demo: output registrati da `app/demo/`, ricomposizione dal catalogo |
| `collaudo.py` | verifiche offline |

Lo stato non sta in memoria né in `app/`: `agents/state/catalogo.json`,
`agents/state/profilo.json`, `agents/state/run-<id>.json`, come prescrive
`agents/ARCHITETTURA.md`. Ogni scrittura di `run-<id>.json` è validata contro
`agents/schemas/run-state.json`.

## Requisiti tecnici non negoziabili

- Nessun segreto nel codice: tutto da `.env` (vedi `.env.example`).
- Ogni chiamata al modello ha timeout e retry con backoff (G-16); gli errori non ritentabili
  (chiave, richiesta non valida) falliscono subito.
- Ogni output di agente è validato contro il suo schema prima dell'uso: una sola ri-richiesta
  con gli errori in chiaro, poi fallback con `status: degraded`.
- Il percorso di demo non dipende da login o servizi esterni che possono cadere.
- Senza chiave API l'app non restituisce 500: risponde con `status: "degraded"` e il rimando
  a un CAF.
