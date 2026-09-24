# Intake dell'idea

Compilato da Chiara, letto da tutti e due. Serve a una cosa sola: trasformare l'idea in
input utilizzabili dalla struttura, senza doverla raccontare due volte.

Regola: **una risposta per riga, concreta**. Dove non sai ancora, scrivi "non so" — è
un'informazione utile. Dove tiri a indovinare senza dirlo, ci costa un'ora alle 15:00.

Tempo di compilazione: 15 minuti. Non di più: il resto si scopre costruendo.

---

## A. La persona

| Campo | Risposta |
|---|---|
| A1. Nome e situazione (una riga, concreta) | |
| A2. Cosa sta cercando di fare | |
| A3. Perché oggi non ci riesce da sola | |
| A4. Quale barriera precisa: lettura, comprensione, vista, motoria, lingua, ansia da errore, altro | |
| A5. In quale momento esatto si ferma | |

Vincolo dagli organizzatori: "un utente disabile" non è un profilo. Serve una persona.

## B. L'artefatto reale

| Campo | Risposta |
|---|---|
| B1. Di cosa si tratta (pagina, modulo, bolletta, procedura) | |
| B2. Dove si trova / URL | |
| B3. È già scaricato in locale? In che formato (HTML, PDF, testo)? | |
| B4. Quanti passi ha, all'incirca | |
| B5. Contiene importi, date o scadenze? (se sì, sono dati intoccabili) | |

Vincolo: deve essere reale o realistico. Un artefatto inventato da noi è il modo più veloce
per farci dire che la demo non è collegata a un processo reale.

## C. Il percorso

| Campo | Risposta |
|---|---|
| C1. Il passo più difficile, quello su cui si gioca la demo | |
| C2. Perché è difficile: gergo, troppa informazione insieme, richiesta implicita, altro | |
| C3. Cosa deve saper fare la persona alla fine che prima non sapeva fare | |
| C4. Come lo dimostriamo a schermo in 30 secondi | |

## D. Dove si blocca (serve al `block-detector`)

Elenca le 4-6 cose che possono andare storte su quel passo. Diventano la tassonomia chiusa
delle cause di blocco: un enum nello schema, non una lista di esempi.

1.
2.
3.
4.

## E. Limiti che accettiamo

| Campo | Risposta |
|---|---|
| E1. Cosa la soluzione NON fa, per scelta | |
| E2. Su cosa preferiamo fermarci e chiamare una persona | |
| E3. Rischio principale se semplifichiamo male | |

Serve al deliverable 3 ("Autonomia & Limiti" / "Risk & Clarity Note") e ai gate HITL.
Un limite dichiarato vale più di un limite nascosto: l'AI che fa lo screening verifica,
e un'affermazione gonfiata costa più di una lacuna ammessa.

---

## Dove finisce ogni risposta

| Da | A |
|---|---|
| A1-A5 | `README.md` sezione "Il problema", `agents/subagents/profiler.md`, presentazione sez. 1-2 |
| B1-B5 | `agents/subagents/source-analyzer.md`, `app/` (ingestione) |
| C1-C4 | script della demo, presentazione sez. 3 e 5, `docs/validation/` |
| D | enum `cause` in `agents/schemas/block-detector.output.json` |
| E1-E3 | gate HITL in `agents/orchestrator.md`, presentazione sez. 6, `docs/process-note.md` |

Quando questo file è pieno, i marcatori `TODO-TEMA:` sparsi nel repo diventano tutti
compilabili. Il linter `tools/check_repo.py` verifica che non ne resti nessuno.
