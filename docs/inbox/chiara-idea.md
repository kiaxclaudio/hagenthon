# Hagenthon — Tema 02: Inclusione Finanziaria
> Documento di allineamento · Chiara & Davide

---

## L'idea

**"A cosa ho diritto?"** — un sistema agentico conversazionale che aiuta persone con zero alfabetizzazione fiscale a capire quali aiuti statali italiani esistono per la loro situazione, come funzionano, come accedervi e cosa sono i documenti che verranno richiesti (cassetto fiscale, ISEE, CU, ecc.).

**Il problema reale**: milioni di italiani non accedono a bonus e incentivi a cui hanno diritto perché non capiscono il linguaggio burocratico, non sanno da dove partire e non hanno mai aperto il cassetto fiscale. È un problema di alfabetizzazione fiscale-finanziaria.

**Framing rispetto al Tema 02** (importante per la valutazione): la soluzione educa l'utente su come funzionano gli incentivi statali in linguaggio accessibile a chi parte da zero — comprensione + autonomia finanziaria. NON dà consigli finanziari: orienta, informa, rimanda sempre a CAF o commercialista per le decisioni.

---

## Struttura repository (obbligatoria per la consegna)

```
/
├── .claude/
│   ├── agents/
│   │   ├── orchestrator.md      → agente principale
│   │   ├── eligibility.md       → sub-agente verifica bonus
│   │   ├── explainer.md         → sub-agente spiegazione
│   │   └── navigator.md         → sub-agente guida accesso
│   └── commands/
│       └── analizza-profilo.md  → slash command riutilizzabile
├── app/                         → codice del prototipo (chat web)
├── agents/                      → copia dei file .md + documentazione workflow
├── presentation/                → presentazione HTML brandizzata Accenture
├── CLAUDE.md                    → contesto progetto, convenzioni, comandi
└── README.md                    → setup, prerequisiti, flusso agentico spiegato
```

> **Nota**: la cartella `.claude/agents/` contiene i file funzionali usati da Claude Code. La cartella `agents/` nella root è la copia per la consegna + documentazione del flusso.

---

## Architettura agentica

Il criterio più pesante della giuria è **Profondità agentica (24%)**. Serve un sistema multi-agente reale, non un singolo chatbot con un prompt.

```
Utente (chat web)
      ↓
 ORCHESTRATORE  [Haiku]
 - raccoglie profilo utente step by step
 - salva stato in user_profile.json
 - decide quale sub-agente attivare
      ↓              ↓               ↓
 ELIGIBILITY    EXPLAINER       NAVIGATOR
 [Sonnet]       [Sonnet]        [Haiku]
 dato il        spiega in       guida passo
 profilo JSON,  linguaggio      per passo come
 lista i bonus  semplice ogni   accedere
 pertinenti     bonus, limiti   (cassetto fiscale,
                inclusi         CAF, documenti)
```

### Regole architetturali da rispettare

- **Stato esternalizzato**: il profilo utente viene salvato in `user_profile.json` tra un turno e l'altro — non ricalcolato ogni volta
- **Output strutturati**: ogni sub-agente restituisce un oggetto JSON tipizzato; l'orchestratore lo interpreta e lo passa al layer successivo
- **Model tiering**: Haiku per raccolta dati e passi procedurali, Sonnet per ragionamento e spiegazioni — dichiarato esplicitamente in ogni file `.md`
- **HITL esplicito**: quando un sub-agente non è sicuro su un caso edge, non inventa — restituisce `"escalation": true` e l'orchestratore mostra "Per questa situazione specifica ti consiglio di parlare con un CAF"
- **Fallback**: se un sub-agente restituisce output malformato → retry con prompt semplificato; se fallisce di nuovo → risposta di default + escalation

---

## I file agente — cosa deve contenere ognuno

Ogni file `.claude/agents/*.md` deve avere questi campi per guadagnare punti su **Qualità istruzioni (19%)**:

```
# Nome agente
**Modello**: claude-haiku-4-5 / claude-sonnet-4-6
**Tool consentiti**: [lista]
**Trigger**: quando viene attivato dall'orchestratore

## Obiettivo
Una riga chiara.

## Input atteso
Formato JSON del profilo utente che riceve.

## Output atteso
Schema JSON esatto che deve restituire.

## Istruzioni step-by-step
1. ...
2. ...

## Vincoli espliciti
- Non fare X
- Se Y allora Z
```

---

## Hooks da implementare

Copertura per **Robustezza (15%)** e **Qualità tecnica (12%)**:

**PostToolUse — validazione anti-consulenza**
Dopo ogni risposta di un sub-agente, grep sull'output per frasi da consulenza finanziaria ("ti consiglio di investire", "dovresti scegliere", "conviene fare"). Se trovato: blocca, forza risposta di fallback con rimando a CAF.

**Stop — logging sessione**
Al termine di ogni sessione, logga profilo utente + bonus restituiti in `logs/session_TIMESTAMP.json`. Serve come evidenza di validazione per il deliverable 03.

---

## Flusso conversazionale

Domande a **scelta multipla** ovunque possibile — chi non sa da dove partire si blocca su una casella vuota.

### Step 1 — Situazione di vita
> "Cosa sta succedendo nella tua vita in questo momento?"
- Sto per comprare o ristrutturare casa
- Ho avuto o aspetto un figlio
- Ho perso il lavoro o sono in cerca di occupazione
- Ho spese mediche importanti
- Voglio acquistare un'auto nuova
- Sono under 36 (lavoro o studio)
- Non so da dove partire — mostrami tutto

### Step 2 — Profilo base
- Sei proprietario di casa, affittuario o vivi con familiari?
- Hai un reddito (lavoro dipendente, pensione, partita IVA)?
- Hai già un CAF o un commercialista?
  - Se risponde "non so cos'è un CAF" → spiegazione inline: 2 righe, poi si continua

### Step 3 — Timing
- Devo ancora iniziare / sono in corso / ho già finito (voglio recuperare il passato)

### Output generato dalla scheda
1. **Lista bonus pertinenti** — nome, percentuale/importo, tetto massimo, anni di recupero
2. **Spiegazione semplice** di ogni bonus — niente gergo ("detrazione" = "sconto sulle tasse che paghi")
3. **Prossimo passo concreto** — cosa fare domani mattina
4. **Glossario contestuale** — cassetto fiscale, ISEE, CU, CILAS spiegati solo se rilevanti
5. **Disclaimer** sempre visibile — "Verifica le scadenze su agenziaentrate.gov.it. Per decisioni specifiche rivolgiti a un CAF."

### UX accorgimenti
- Ogni termine tecnico ha "Cosa significa?" → spiegazione in 2 righe
- "Ricomincia con un profilo diverso" sempre disponibile
- Linguaggio mai burocratico: mai "si decade dal beneficio", sempre "perdi il diritto al rimborso se..."

---

## Divisione del lavoro (5 ore)

| Ora | Chiara | Davide |
|-----|--------|--------|
| **1** | Scrive i 4 file `.md` degli agenti + CLAUDE.md | Setup repo con struttura corretta + UI chat base (domande a scelta multipla) |
| **2** | Slash command `analizza-profilo.md` + raffinamento prompt eligibility/explainer | Integrazione chiamate API, gestione stato `user_profile.json`, model tiering |
| **3** | Hooks (PostToolUse validazione + Stop logging) | UI output scheda bonus + "Cosa significa?" + rendering glossario |
| **4** | Test end-to-end su 4 scenari + fix prompt | Fix UI, fallback, retry logic |
| **5** | README con flusso agentico spiegato + cartella `agents/` per consegna | Presentazione HTML brandizzata Accenture |

### Metodo di lavoro consigliato (dal training)
- **Prima di iniziare a scrivere codice**: 15 minuti insieme a definire e concordare i 4 file `.md` degli agenti — è la parte più importante
- Usare **plan mode** (Shift+Tab in Claude Code) prima di ogni implementazione significativa
- Tenere **sessioni Claude Code separate** per frontend e backend per non inquinare il contesto
- `/clear` tra task scollegati, `/compact` se la sessione diventa lunga

---

## 4 scenari da testare prima della demo

| Scenario | Utente | Bonus attesi |
|----------|--------|--------------|
| Ristrutturazione casa | Proprietario, lavoro dipendente, lavori da iniziare | Bonus Ristrutturazione 50%, Ecobonus, Bonus Mobili |
| Figlio appena nato | Coppia, reddito medio | Assegno Unico, Bonus Nido, Congedo parentale |
| Cerca lavoro, under 36 | Disoccupato | Supporto Formazione Lavoro, incentivi assunzione, Naspi |
| Pensionato con spese mediche | Pensionato, proprietario | Detrazioni sanitarie 19%, esenzione ticket, Bonus Farmaci |

---

## Criteri di valutazione — come li copriamo

| Criterio | Peso | Come lo copriamo |
|----------|------|-----------------|
| Profondità agentica | **24%** | 4 agenti con file `.md` funzionali, stato JSON, output strutturati, esecuzione parallela possibile |
| Qualità istruzioni | **19%** | Ogni file agente: obiettivo, modello, input/output schema, step-by-step, vincoli espliciti |
| Robustezza | **15%** | Hook PostToolUse (validazione), Hook Stop (logging), HITL esplicito, retry su output malformato |
| Efficienza token | **12%** | Haiku per orchestratore e navigator, Sonnet solo per eligibility ed explainer |
| Qualità tecnica | **12%** | Secrets in `.env`, timeout, retry, error handling, model tiering dichiarato |
| Adeguatezza strumenti | **11%** | 3 sub-agenti con responsabilità chiare e non sovrapposte, slash command per flusso riutilizzabile |
| Documentazione | **7%** | README con setup + flusso agentico, CLAUDE.md, cartella `agents/` documentata |
| Qualità idea | **0%** | Non pesa nel punteggio — focus sul resto |

---

## Deliverable finali (checklist)

- [ ] 4 file agente in `.claude/agents/` funzionanti e ben strutturati
- [ ] Slash command `analizza-profilo.md` in `.claude/commands/`
- [ ] CLAUDE.md nella root con contesto progetto e convenzioni
- [ ] Prototipo funzionante con almeno 4 scenari dimostrabili
- [ ] Hook PostToolUse (validazione anti-consulenza) + Hook Stop (logging)
- [ ] README con setup, prerequisiti e flusso agentico spiegato
- [ ] Presentazione HTML brandizzata Accenture (5 minuti di demo)
- [ ] Almeno una evidenza di validazione (log sessioni o confronto before/after)
- [ ] Nota sul processo: come è stata usata l'AI, cosa è stato revisionato, limiti identificati

---

## Cosa NON fare

- Non dare consigli finanziari personalizzati ("ti conviene fare X")
- Non costruire un chatbot generico senza logica applicativa
- Non usare un solo agente monolitico — la giuria controlla la struttura
- Non nascondere limiti e condizioni dei bonus
- Non dimenticare il disclaimer in ogni scheda output

---

*Hagenthon · Accenture Application Engineering · 24 settembre 2026*
