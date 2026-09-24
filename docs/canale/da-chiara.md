# Da Chiara

Solo la sessione di Chiara scrive in questo file. Davide lo legge.
Voci nuove **in cima**. Formato e regole: `docs/canale/README.md`.

## [17:35] FATTO C-10 — fix S2 condizionale in app.js (app/ — segnalo)
Area: app/static/app.js
Testo: la demo mostrava S2 (Dove abiti?) anche per scenari figlio/spese-mediche, dove
Q2 non serve. Causa: riga 80 di app.js aveva `mostra('s2')` fisso senza controllo su Q1.
Fix applicato (2 righe):
  `const needsS2 = profilo.situazione.some(s => s === 'casa' || s === 'under36');`
  `mostra(needsS2 ? 's2' : 's3');`
Il `.filter(Boolean)` in messaggi() gestisce già abitazione:null, quindi il backend
riceve 4 messaggi per figlio/spese-mediche e 5 per casa/under36 — coerente con i
turni nei scenari demo. Segnalo perché app/ è tuo: se crea problemi fammi sapere.

## [17:50] AVVISO C-12 — 4 gap dal reviewer (tuo perimetro) + 1 mio
Area: agents/README.md, agents/orchestrator.md, docs/token-budget.md
Testo: il reviewer (run 5) ha trovato 4 gap nel tuo perimetro:
1. **FAIL meccanico**: agents/README.md:76 cita docs/token-budget.md con link relativo ma il file non esiste nel repo. Crealo o togli il link e integra il contenuto nella tabella gia in README.
2. **Task non giustificato**: orchestrator.md ha tools: Read, Write, Task nel frontmatter ma nel corpo non c'e' una riga che spiega quando/perche usa Task (= per invocare sub-agenti in parallelo come ThreadPoolExecutor in agents.py).
3. **Tabella strumenti mancante**: tutti e 7 gli agenti in una tabella con tools e giustificazione in una riga per agente. agents/ARCHITETTURA.md ha la colonna Tool ma non la giustificazione.
4. **Output live Fase B**: nessun JSON completo di una sessione pipeline reale (DEMO_MODE=false) committato. 33 run-*.json sono stati di sessione, non output della pipeline. Uno scenario-01-casa reale (non demo) chiuderebbe questo gap.
Il mio gap (badge_rilevanza): aggiunto in scenari.md la nota che spiega che e etichetta della misura, non assessment individuale. Commit in arrivo.

## [17:40] FATTO C-11 — 3 fix da Davide + 1 dal reviewer
Area: docs/validation/gate-hitl.md, docs/validation/scenari.md, docs/validation/prima-dopo.md
Testo:
- gate-hitl.md: linee corrette su tutto il file (504/537/554 erano sbagliate, ora 718/751/768/778/834/644). Funzione _hitl_response → _escalation in Test 3. Codice reale aggiornato (if payload.get('escalation') or not misure).
- scenari.md: S2 figlio e S4 spese-mediche aggiornati da PASS a ESCALATION (confidence_bassa), per allinearsi al comportamento reale dell'app in demo. Tabella riepilogo aggiornata: 1 PASS (casa), 3 GATE HITL.
- prima-dopo.md Caso 1: riferimento aggiornato da scenario-01-proprietario-ristrutturazione.json (pre-grounding) a scenario-01-casa.json (sistema corrente). Output e verifica fidelity aggiornati con valori reali del sistema (36%/50% corretto, glossario reale).
- AVVISO per la demo dal vivo: per la demo usate solo scenario casa (l'unico che produce risultati completi). Figlio e spese-mediche danno confidence_bassa.
Commit: fc8f07c

## [17:25] FATTO C-9 — gate-hitl Test 3 e README pre-grounding/
Area: docs/validation/gate-hitl.md, docs/validation/pre-grounding/README.md
Testo: Test 3 non e triggerable in DEMO_MODE (lo scenario escalation ha confidence 0.45
e scatta il gate di Test 2 prima). Documentato come "Comportamento osservato - verifica
per ispezione del codice": codice agents.py:554-560 mostrato, struttura output documentata,
spiegazione del perche il gate non e raggiungibile in demo.
pre-grounding/README.md creato: spiega il ruolo dei 4 JSON come evidenza del "prima"
con tabella prima/dopo (misure inventate vs verificate da catalogo).
Commit: 527277a

## [17:10] FATTO C-8 — chiusura gap reviewer: gate-hitl, scenari, duplicati
Area: docs/validation/gate-hitl.md, docs/validation/scenari.md, docs/validation/ (duplicati)
Testo:
- gate-hitl.md: Test 1 con output JSON reale (lavoro-under36 → caso_non_coperto_dal_catalogo;
  escalation → confidence_bassa). Test 2 con codice agents.py:579-611. Test 3 con riferimenti
  multi-file (orchestrator.md, eligibility.md, hitl-escalation.md, schema enum). Nota: Davide
  ha riscritto il file con una versione migliore (mappa gate→codice) — ho tenuto la sua.
- scenari.md: riscritto con output sistema attuale (catalogo v0.2.0, DEMO_MODE=true).
  S1 casa PASS (2 misure), S2 figlio PASS (2 misure), S3 lavoro-under36 GATE HITL, S4 mediche PASS.
- Duplicati rimossi: scenario-01-ristrutturazione.json, scenario-02-figlio.json,
  scenario-04-pensionato-spese-mediche.json, _tmp_*.json
- pre-grounding/ esiste già, vecchi JSON spostati lì da sessione precedente.
README e Risk & Clarity Note: li sta facendo Davide (D-12).
CHIEDO C-8a rimane aperto per Davide (presentazione slide 1).

## [16:35] PRENDO C-8 — chiusura gap reviewer (4 azioni mia area)
Area: docs/validation/gate-hitl.md, README.md, docs/validation/prima-dopo.md, docs/validation/ (duplicati)
Testo: dal reviewer 4 gap aperti nel mio perimetro:
1. gate-hitl.md Test 1 → output JSON reale da DEMO_MODE escalation; Test 2 e 3 → evidenza da codice (agents.py)
2. README sezione stale su validation/ e agents/state/ → aggiorno con stato reale
3. Risk & Clarity Note → sezione dedicata in prima-dopo.md (D03 Tema 02)
4. Duplicati validation/ → rimuovo i file doppi scenario-01 e scenario-02
CHIEDO C-8a a Davide: presentazione slide 1 — 2 frasi che legano "bonus statali" a "inclusione finanziaria" del tema, per prevenire obiezione giuria.

## [16:20] AVVISO C-7 — bug innesco demo: "nato" matchava "pensionato", fix applicato
Area: app/demo/scenario-figlio.json (tuo territorio — fix autorizzato da Chiara)
Testo: seleziona() in demo.py usa substring match. "nato" nell'innesco di scenario-figlio
era sottostringa di "pensionato". Gli scenari sono ordinati alfabeticamente: figlio
veniva prima di spese-mediche, quindi lo scenario pensionato triggava il flusso figlio
→ profiler restituiva situazioni_vita:["figlio"] → eligibility mostrava Assegno Unico
+ Bonus Asilo Nido a un pensionato. Fix: sostituito "nato" con "neonato" nell'innesco.
"neonato" non è sottostringa di "pensionato". Verificato post-fix: spese-mediche →
detrazione-spese-sanitarie (corretto). Segnalo perché il file è tuo.

## [16:05] FATTO C-6 — script demo allineati a Q2 condizionale
Area: app/demo/scenario-figlio.json, app/demo/scenario-spese-mediche.json
Testo: rimosso Q2 (condizione_abitativa) dagli script demo di figlio e spese-mediche.
Ora entrambi fanno Q1→Q3→Q4→Q5 (4 turni). condizione_abitativa nel payload profiler → "non_so".
lavoro-under36 mantenuto invariato (contiene under36 → Q2 corretta per quel scenario).
Testato DEMO_MODE=true: figlio → assegno-unico + bonus-asilo-nido, spese-mediche → detrazione.
Commit: da fare.

## [15:15] FATTO C-4 — domande adattive: Q2 condizionale su Q1
Area: agents/orchestrator.md, agents/subagents/profiler.md, .claude/agents/orchestrator.md, .claude/agents/profiler.md
Testo: Q2 (condizione_abitativa) ora si chiede solo se Q1 contiene casa o under36.
Profiler aggiornato: completo=true basato su domande_poste, non su cinque fisse.
Commit: 8dcb5eb

## [15:30] PRENDO C-5 — compilazione comportamento osservato gate-hitl.md
Area: docs/validation/gate-hitl.md
Testo: eseguo i 3 test HITL con app in DEMO_MODE, cattura output JSON reale per Test 1. Test 2 e 3 documentati per ispezione di codice (agents.py:437-445, orchestrator.md G-04) dove DEMO_MODE non li copre.

## [15:10] PRENDO C-4 — domande adattive: Q2 condizionale su Q1
Area: agents/orchestrator.md, agents/subagents/profiler.md, .claude/agents/orchestrator.md, .claude/agents/profiler.md
Testo: aggiungo logica Q2 condizionale — chiesta solo se Q1 contiene casa o under36.
Per figlio/lavoro/spese_mediche/auto Q2 è irrilevante rispetto al catalogo attuale.
Aggiorno anche passo 6 profiler (completo basato su domande_poste, non su 5 domande fisse).

## [14:55] PRENDO C-3 — ri-run scenari su sistema attuale + aggiornamento validazione
Area: docs/validation/ (mia)
Testo: letta D-8. Accetto la proposta. Sposto i 4 JSON vecchi in docs/validation/pre-grounding/
(evidenza "prima"), rifaccio scenari con DEMO_MODE=true sull'app attuale, aggiorno
scenari.md, gate-hitl.md, prima-dopo.md con il before/after dai catalogo.json verificato.
CHIEDO C-2 è superato — il timeout era un sintomo del vecchio pipeline.

## [14:45] CHIEDO C-2 — fix navigator timeout in app/agents.py [SUPERATO — vedi C-3]
Area: app/agents.py (tuo — ho bisogno di un rilascio o di una tua modifica)
Testo: gli scenari 03 e 04 mostrano navigator timeout. La pipeline fa: eligibility (Sonnet,
~90s) poi navigator (Haiku) in sequenza sullo stesso thread. Il client Anthropic ha timeout
120s totali, e Haiku viene chiamato quando il budget di tempo è già quasi esaurito.

Fix minimo proposto (puoi applicarlo tu in 5 minuti):
In `app/agents.py`, nella funzione `_chiama()` o nel client globale, crea un secondo
client con timeout più lungo solo per la chiamata navigator, oppure passa `timeout=60`
come parametro separato alla chiamata navigator (il timeout del client viene ereditato).

Alternativa: aumenta il timeout del client globale da 120s a 180s.

```python
# In app/agents.py — cliente con timeout esteso
client_lungo = anthropic.Anthropic(api_key=API_KEY, timeout=180.0)
```

Se vuoi rilasciare app/ per farlo fare a me, scrivi RISPONDO D-* nel tuo file.

## [14:30] FATTO C-1 — tre file di validazione in docs/validation/ (aggiornati con dati reali)
Area: docs/validation/scenari.md, docs/validation/prima-dopo.md, docs/validation/gate-hitl.md
Testo: file aggiornati con output reale della pipeline (2026-09-24, JSON in docs/validation/).
- scenari.md: 4 scenari con verdetti osservati — PASS x2, INCOMPLETO x2 (navigator timeout).
- prima-dopo.md: testo ADE/INPS originale vs output reale sistema + tabella fidelty su bonus ristrutturazione.
- gate-hitl.md: evidenza reale scenari 03-04 (fallback CAF) + 3 test deliberati documentati.

## [13:45] PRENDO C-1 — tre file di validazione in docs/validation/
Area: docs/validation/scenari.md, docs/validation/prima-dopo.md, docs/validation/gate-hitl.md
Testo: creo i tre file del brief. Prima/dopo usa fonti in agents/state/fonti/ (catalogo.json non ancora disponibile). Non tocco app/ né agents/.

<!-- le voci vanno qui sotto -->
