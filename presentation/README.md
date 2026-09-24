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
| 4 | Dove interviene l'AI — il lavoro difficile si fa una volta sola | come funziona / dove interviene | 1:00 | 2:15 |
| 5 | La prova — su sei misure il controllo ne ha fermate quattro | miglioramento / limiti e rischi | 0:35 | 2:50 |
| 6 | Adesso il prodotto (passaggio alla demo) | — | 0:10 | 3:00 |

Il tempo assegnato è ripetuto in un commento HTML all'inizio di ogni sezione; la somma è **3:00**.
La sezione 4 è volutamente la più lunga: è dove stanno i due criteri più pesanti (profondità
agentica 24%, qualità delle istruzioni 19%) e contiene il diagramma dell'architettura in SVG
inline, senza immagini esterne.

## Registro linguistico

Le slide sono scritte per chi non ha letto il repository e ha tre minuti. Regola applicata:
**ogni slide deve poter essere letta in silenzio in dieci secondi.**

Dal testo a schermo sono spariti i codici dei guardrail (G-04, G-18…), i nomi degli hook, le
parole *schema JSON*, *tier*, *envelope*, e i percorsi dei file. Gli agenti non sono più soggetti
di frase con il loro nome tecnico: sul diagramma sono **cosa fanno** ("legge ed estrae i numeri",
"li riscrive", "controlla che non sia cambiato niente"). I sette nomi propri restano una volta
sola, in una riga piccola in fondo alla sezione 4, per chi vorrà incrociarli con il repository.

L'architettura si racconta in quattro frasi:

1. un agente legge le pagine ufficiali di Agenzia delle Entrate e INPS e ne tira fuori i numeri;
2. un secondo agente li riscrive in parole che capisce chiunque;
3. un terzo controlla che riscrivendo non sia cambiato niente — **e non ha il permesso di
   riscrivere**: può solo approvare o respingere;
4. quando la persona arriva, tre agenti leggeri fanno cinque domande, cercano nell'elenco già
   verificato e spiegano come fare.

Frase che chiude il senso: *il lavoro difficile si fa una volta sola, prima; quando arriva la
persona il sistema legge un elenco già controllato.* Per questo è veloce e per questo non inventa.

Il diagramma della sezione 4 è pensato per essere capito in tre secondi: **due righe, una per
tempo**, cinque riquadri ciascuna, due parole per riquadro, nessuna legenda e nessun badge di
modello.

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
- il divieto di consulenza del tema è rispettato alla lettera, e sulla slide si dice in una riga:
  «non diciamo mai cosa conviene fare: spieghiamo, e per le decisioni mandiamo al CAF».

I tre deliverable che il tema chiede per nome non sono più citati con il titolo inglese e il
percorso: la slide chiude con una riga piccola che dice che nel repository ci sono la difficoltà
dell'utente (`docs/ux/ux-spec.md`, `docs/validation/scenari.md`), il confronto prima/dopo su quattro
casi (`docs/validation/prima-dopo.md`) e la nota su rischi e chiarezza (`docs/validation/gate-hitl.md`,
`agents/guardrails.md`).

## Coerenza con il repository

Nomi dei componenti, model tier, fasi, limiti di iterazione e soglie dei gate sono allineati a
`agents/ARCHITETTURA.md`, che è il file canonico — sette componenti, due fasi — e verificabili anche
in `agents/orchestrator.md`, `agents/workflows/main-pipeline.md` e `agents/guardrails.md`.

Le cifre della sezione 5 (6 misure lavorate, 8 controlli, 4 errori gravi, 1 misura esclusa) e i tre
errori citati con il testo della fonte sono copiati da `agents/state/verifica-fase-a.json` senza
arrotondamenti.

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
