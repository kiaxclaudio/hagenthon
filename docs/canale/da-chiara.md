# Da Chiara

Solo la sessione di Chiara scrive in questo file. Davide lo legge.
Voci nuove **in cima**. Formato e regole: `docs/canale/README.md`.

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
