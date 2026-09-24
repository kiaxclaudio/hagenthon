# presentation/

`index.html` — la presentazione da esporre in 5 minuti.

## Come si apre

Doppio clic su `index.html`, oppure trascinarlo in un browser.
File singolo, nessuna dipendenza esterna: nessuna CDN, nessun font remoto, nessun build.
Funziona offline e senza rete. Il controllo automatico è
`python tools/check_repo.py`, voce "presentazione offline".

## Come si naviga

| Comando | Effetto |
|---|---|
| Freccia destra, PagGiu, barra spaziatrice | sezione successiva |
| Freccia sinistra, PagSu | sezione precedente |
| Home / Fine | prima / ultima sezione |
| Pallini in basso a destra | salto diretto a una sezione |

L'indicatore in alto a destra mostra la posizione (`05 / 08`). La sezione corrente finisce
nell'URL (`index.html#5`): ricaricando la pagina si riparte da lì.
I telecomandi da presentazione inviano PagSu/PagGiu e funzionano senza configurazione.

## Le otto sezioni e il tempo assegnato

| # | Sezione | Punto del "Risultato atteso" | Tempo | Cumulato |
|---|---|---|---|---|
| 1 | Cover | — | 0:15 | 0:15 |
| 2 | Il problema | problema | 0:35 | 0:50 |
| 3 | Utente e scenario | utente / scenario | 0:30 | 1:20 |
| 4 | Come funziona la soluzione | come funziona | 0:40 | 2:00 |
| 5 | Dove interviene l'agente AI (architettura) | dove interviene l'agente | 1:30 | 3:30 |
| 6 | Il miglioramento prodotto | quale miglioramento | 0:40 | 4:10 |
| 7 | Limiti e rischi | limiti e rischi | 0:35 | 4:45 |
| 8 | Chiusura | — | 0:15 | 5:00 |

Il tempo assegnato è ripetuto in un commento HTML all'inizio di ogni sezione; la somma è 5:00.
La sezione 5 è volutamente la più lunga: è dove stanno i due criteri più pesanti
(profondità agentica 24%, qualità delle istruzioni 19%) e contiene il diagramma
dell'architettura in SVG inline, senza immagini esterne.

## Coerenza con il repository

Nomi dei componenti, model tier, fasi, limiti di iterazione e soglie dei gate sono allineati a
`agents/ARCHITETTURA.md`, che è il file canonico, e verificabili anche in
`agents/orchestrator.md`, `agents/workflows/main-pipeline.md` e `agents/guardrails.md`.
I numeri citati a schermo — sette componenti, 24 guardrail, 15 contratti JSON Schema,
tre hook, tre skill — sono contabili sui file.

Il file non contiene segnaposto: i contenuti di dominio (misure, glossario, scenari) sono
quelli del prodotto "A cosa ho diritto?" descritto in `agents/ARCHITETTURA.md` e
`docs/inbox/chiara-idea.md`.

## Brand

Colori e tipografia sono gli stessi di `docs/ux/accenture-tokens.css`: viola `#A100FF`,
viola chiaro `#BE82FF`, inchiostro `#0A0014`, fondo `#050008`, Inter con fallback di sistema,
chevron `›` come segno di elenco. Il logotipo in alto a sinistra usa il chevron `>` di marca.
