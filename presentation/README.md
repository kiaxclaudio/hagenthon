# presentation/

`index.html` — la presentazione da esporre in 5 minuti.

## Come si apre

Doppio clic su `index.html`, oppure trascinarlo in un browser.
File singolo, nessuna dipendenza esterna: nessuna CDN, nessun font remoto, nessun build.
Funziona offline e senza rete.

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

| # | Sezione | Tempo | Cumulato |
|---|---|---|---|
| 1 | Cover | 0:15 | 0:15 |
| 2 | Il problema | 0:35 | 0:50 |
| 3 | Utente e scenario | 0:30 | 1:20 |
| 4 | Come funziona la soluzione | 0:40 | 2:00 |
| 5 | Dove interviene l'agente AI (architettura) | 1:30 | 3:30 |
| 6 | Il miglioramento prodotto | 0:40 | 4:10 |
| 7 | Limiti e rischi | 0:35 | 4:45 |
| 8 | Chiusura | 0:15 | 5:00 |

Il tempo suggerito è ripetuto in un commento HTML all'inizio di ogni sezione.
La sezione 5 è volutamente la più lunga: contiene il diagramma dell'architettura agentica,
disegnato in SVG inline (nessuna immagine).

## Prima della consegna

Nel file restano 13 segnaposto nella forma `TODO-TEMA: <cosa va scritto>`, evidenziati anche
a schermo. Vanno tutti sostituiti dopo la scelta del tema e della persona:

```bash
grep -o 'TODO-TEMA: [^<]*' presentation/index.html
```

Le sezioni architetturali (4, 5, 7, 8) non contengono segnaposto: i nomi degli agenti, i tier
e i limiti di iterazione sono allineati a `agents/orchestrator.md`,
`agents/workflows/main-pipeline.md` e `agents/guardrails.md`.
