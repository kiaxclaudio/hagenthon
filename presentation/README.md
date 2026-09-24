# presentation/

`index.html` — la presentazione da esporre in **3 minuti**, seguita da **2 minuti di demo dal vivo**
dell'applicazione reale. Cinque minuti in totale.

## Come si apre

Doppio clic su `index.html`, oppure trascinarlo in un browser.
File singolo, nessuna dipendenza esterna: nessuna CDN, nessun font remoto, nessuna immagine, nessun
build. Funziona offline e senza rete. Il controllo automatico è `python tools/check_repo.py`,
voce "presentazione offline".

## Come si naviga

| Comando | Effetto |
|---|---|
| Freccia destra, PagGiu, barra spaziatrice | sezione successiva |
| Freccia sinistra, PagSu | sezione precedente |
| Home / Fine | prima / ultima sezione |
| Pallini in basso a destra | salto diretto a una sezione |

L'indicatore in alto a destra mostra la posizione (`04 / 06`). La sezione corrente finisce
nell'URL (`index.html#4`): ricaricando la pagina si riparte da lì.
I telecomandi da presentazione inviano PagSu/PagGiu e funzionano senza configurazione.

## Le sei sezioni e il tempo assegnato

| # | Sezione | Punto del "Risultato atteso" | Tempo | Cumulato |
|---|---|---|---|---|
| 1 | Copertina | — | 0:10 | 0:10 |
| 2 | Il problema — Marco e la detrazione che non chiede | problema / utente | 0:30 | 0:40 |
| 3 | Perché è Tema 02 | aderenza al tema | 0:35 | 1:15 |
| 4 | Dove interviene l'agente AI (architettura) | come funziona / dove interviene | 1:00 | 2:15 |
| 5 | La prova, e i limiti | miglioramento / limiti e rischi | 0:35 | 2:50 |
| 6 | Adesso il prodotto (passaggio alla demo) | — | 0:10 | 3:00 |

Il tempo assegnato è ripetuto in un commento HTML all'inizio di ogni sezione; la somma è **3:00**.
La sezione 4 è volutamente la più lunga: è dove stanno i due criteri più pesanti (profondità
agentica 24%, qualità delle istruzioni 19%) e contiene il diagramma dell'architettura in SVG
inline, senza immagini esterne.

## Il rapporto con la demo

Il deck **non mostra schermate del prodotto** e non racconta il percorso utente passo per passo:
quello lo fa la demo dal vivo. Le slide danno il contesto, l'argomento di aderenza al tema e
l'architettura; la demo mostra il prodotto.

La sezione 6 è la cerniera ed è progettata come tale: dice alla giuria che cosa sta per vedere
(`python app/main.py`, non un mockup), su che cosa deve guardare (la fonte e la data su ogni cifra,
«per unità immobiliare» e «parte eccedente» rimessi dal `fidelity-validator`, il rimando al CAF come
campo dell'output, un caso che il sistema rifiuta) e che cosa non vedrà.

Se la demo salta per un problema di ambiente, la sezione 5 regge da sola: le divergenze e le cifre
che cita sono verificabili in `agents/state/verifica-fase-a.json` senza avviare nulla.

## Aderenza al Tema 02 — dove sta l'argomento

La sezione 3 è dedicata interamente a questo e si appoggia al testo della traccia citato alla
lettera. La tesi, in breve:

- detrazione, IRPEF, aliquota, imponibile e ISEE **sono** concetti di finanza personale di base:
  chi non sa cos'è una detrazione non legge la propria busta paga;
- non è teoria, sono soldi: non chiedere un'agevolazione a cui si ha diritto è una perdita
  economica reale;
- il documento che rendiamo leggibile è un documento finanziario, allo stesso titolo della bolletta
  e dell'estratto conto che il tema cita come esempi;
- il divieto di consulenza del tema è rispettato alla lettera e **codificato**: G-04, il
  `fidelity-validator` in Fase A, l'hook `PostToolUse` a runtime;
- la capability software non è la riscrittura del testo — che il tema mette fra le cose da evitare —
  ma la pipeline di ancoraggio alla fonte con verifica di fedeltà separata.

La stessa sezione indica dove stanno i tre deliverable che il tema chiede per nome: *User Difficulty
Statement* (`docs/ux/ux-spec.md` §1, `docs/validation/scenari.md`), *Before/After Simplicity
Evidence* (`docs/validation/prima-dopo.md`), *Risk & Clarity Note* (`docs/validation/gate-hitl.md`,
`agents/guardrails.md`).

## Coerenza con il repository

Nomi dei componenti, model tier, fasi, limiti di iterazione e soglie dei gate sono allineati a
`agents/ARCHITETTURA.md`, che è il file canonico — sette componenti, due fasi — e verificabili anche
in `agents/orchestrator.md`, `agents/workflows/main-pipeline.md` e `agents/guardrails.md`.

Le cifre della sezione 5 (6 misure lavorate, 8 giri di verifica, 4 divergenze bloccanti, 1 misura
esclusa) e le tre divergenze citate con il testo originale sono copiate da
`agents/state/verifica-fase-a.json` senza arrotondamenti. I numeri di Fase A e Fase B in token
vengono da `docs/token-budget.md`. Gli altri numeri a schermo — sette componenti, 24 guardrail,
15 contratti JSON Schema, tre hook, tre skill — sono contabili sui file.

## Brand ed estetica

Palette Accenture (`docs/ux/accenture-tokens.css`) con il trattamento di `docs/ux/estetica-v2.css`
inlinato e adattato: superfici in rilievo `#230B33`, tessere numero con gradiente bianco → `#D9B8FF`,
aloni radiali, card con filo di luce superiore.

**Niente logo Accenture.** In alto a sinistra c'è il wordmark del prodotto, `A cosa ho diritto` con
il `?` in `#BE82FF` come segno grafico; lo stesso `?` è la filigrana della copertina.

Contrasti: `#A100FF` come **testo** è 3.92:1 e sta sotto soglia, quindi nel file compare solo come
riempimento o bordo; il testo viola è `#BE82FF` (7.75:1). I badge pieni con testo bianco usano
`#8A00DB` (6.77:1). I numeri grandi sono bianco → `#D9B8FF` su `#230B33`.

## Verifica di impaginazione

Controllata con Chrome headless a **1920×1080** e **1366×768**, e per sicurezza anche a 1440×900,
1600×900 e 1280×720: nessuna sezione deborda dall'area utile e nessun testo finisce sotto la barra
inferiore. La soglia di compattazione tipografica è `@media (max-height:980px)`, così i proiettori
a 900px di altezza ricevono la variante densa.
