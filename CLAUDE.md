# CLAUDE.md — cervello condiviso del team

Questo file è letto automaticamente da **entrambe** le sessioni Claude Code (Davide e Chiara).
Serve a farci lavorare in parallelo senza parlarci ogni cinque minuti e senza scrivere due volte la stessa cosa.
Se modifichi questo file, avvisa l'altra persona: è l'unico file a proprietà condivisa.

---

## 1. Cosa stiamo costruendo e per cosa veniamo giudicati

Hackathon Agentic Coding, Accenture Application Engineering. 5 ore, team da 2.

**La giuria NON valuta l'idea (peso 0%).** Valuta il sistema agentico che la produce:

| Peso | Criterio | Dove si guadagna nel repo |
|---|---|---|
| 24% | Profondità agentica | `agents/` — orchestrazione, sub-agenti, workflow multi-step, skills, stato esternalizzato, output strutturati |
| 19% | Qualità delle istruzioni | `agents/` — scope chiaro, output format, step-by-step, vincoli espliciti, coerenza, **no sovrapposizioni** |
| 15% | Robustezza | fallback, error handling, escalation umana (HITL), limiti di iterazione |
| 12% | Efficienza dei token | model tiering, isolamento di contesto, caricamento on-demand, output strutturati |
| 12% | Qualità tecnica | error handling, timeout, retry, secrets/env, model tiering |
| 11% | Adeguatezza strumenti | né troppi né ridondanti, ognuno giustificato |
| 7% | Documentazione | `README.md`, flusso agentico, setup, prerequisiti |
| 0% | Qualità dell'idea | — |

**Conseguenza operativa: `agents/` vale più di `app/`.** L'app deve funzionare quanto basta a
dimostrare il sistema agentico. Non si aggiungono funzionalità all'app finché `agents/` non è completo.

**Corollario anti-intuitivo:** un repo gonfio prende *meno* punti. Il criterio 02 penalizza
esplicitamente le sovrapposizioni tra file. Pochi file, ognuno con uno scope netto.

---

## 2. Proprietà dei file (regola anti-conflitto)

Lavoriamo sullo stesso branch `main`. Non usiamo pull request: in 5 ore sono troppo lente.
I conflitti si evitano **per costruzione**: ogni file ha un proprietario, e nessuno scrive nei file altrui.

| Area | Proprietario | Note |
|---|---|---|
| `agents/**` | Davide | cuore del punteggio |
| `app/**` | Davide | prototipo |
| `presentation/**` | Davide | HTML brand Accenture |
| `docs/validation/**` | Chiara | evidenza di validazione |
| `docs/ux/**` | Davide | specifica UX, token, mockup |
| `docs/process-note.md` | Davide | nota sul processo |
| `docs/status-davide.md` | Davide | solo Davide scrive |
| `docs/status-chiara.md` | Chiara | solo Chiara scrive |
| `README.md`, `CLAUDE.md`, `agents/schemas/**` | **condivisi** | si tocca solo dopo aver avvisato l'altra persona |

Se ti serve una modifica in un file che non è tuo: **non farla**. Scrivila come richiesta nel tuo
file di status e dillo alla sincronizzazione successiva.

## 3. Disciplina git

- `git pull --rebase` **prima** di ogni push. Sempre.
- Push ogni ~20 minuti, non alla fine. Un repo non pushato vale zero.
- Commit piccoli, messaggio in italiano all'imperativo: `aggiungi validator di fedelità`.
- Mai committare `.env`, chiavi, token. Solo `.env.example`.

## 4. Contract-first

Le interfacce tra i pezzi sono i file JSON Schema in `agents/schemas/`.
Vengono concordati **all'inizio** e poi congelati: chi lavora sull'app e chi lavora sugli agenti
programmano contro lo stesso contratto senza doversi aspettare a vicenda.
Cambiare uno schema dopo il congelamento richiede il consenso esplicito di entrambi.

## 5. Disciplina dei token (vale il 12%)

- **Model tiering dichiarato**: ogni agente in `agents/subagents/` dichiara il suo tier e il perché.
  Haiku 4.5 per classificazione/rilevamento, Sonnet 5 per trasformazione, Opus 5 solo per analisi e giudizio.
- Gli agenti si scambiano **JSON, non prosa**.
- Le istruzioni lunghe stanno in `agents/skills/`, caricate on-demand, non incollate nel contesto.
- Lo stato sta in `agents/state/*.json`, non nella conversazione.
- Non rileggere file già letti nello stesso run.

## 6. Regole di stile per i file in `agents/`

Ogni file agente segue `agents/subagents/_TEMPLATE.md`, senza eccezioni. Deve dichiarare:
scope (cosa fa **e cosa non fa**), input, output con schema, passi, vincoli, fallback,
gate HITL, limite di iterazioni, model tier.
