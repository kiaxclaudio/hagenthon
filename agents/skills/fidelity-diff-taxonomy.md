# Skill: fidelity-diff-taxonomy

| | |
|---|---|
| **Caricata da** | `agents/subagents/fidelity-validator.md`. Unico consumatore. |
| **Quando** | Al passo A4 di `agents/workflows/main-pipeline.md`, a ogni invocazione del validator, compreso il secondo giro sullo stesso passo. Non è in contesto in Fase B. |
| **Cosa restituisce a chi la usa** | La procedura di confronto `V-1..V-4`, la **tassonomia chiusa** `D-01..D-10` più `D-99`, con gravità e test di rilevazione, la regola di precedenza che determina il verdetto, e l'elenco di ciò che **non** è una divergenza. Ogni voce dell'elenco di divergenze prodotto dal validator porta un codice di questa tassonomia: un tipo fuori elenco non esiste. |
| **Perché non è caricata da altri** | Il `simplifier` non classifica: riceve i codici già assegnati e li usa come indirizzo di correzione (vedi `plain-language.md`, sezione 6). Caricare la tassonomia da entrambe le parti duplicherebbe il contesto e, peggio, permetterebbe a chi scrive di auto-assolversi. |

---

## 0. Che cosa è già deciso altrove

| Vincolo | Dove è stabilito | Che cosa aggiunge questa skill |
|---|---|---|
| Il validator non riscrive e non giudica la leggibilità | `fidelity-validator.md` | Nulla: resta il perimetro |
| Ogni divergenza è motivata | `fidelity-validator.md` | Il formato minimo della motivazione (sezione 5) |
| Divergenze su importi, date, scadenze, obblighi: sempre bloccanti | `fidelity-validator.md`, G-03 | La definizione operativa di che cosa **conta come** importo, data, scadenza, obbligo e riferimento (sezione 1) |
| In dubbio si respinge | `fidelity-validator.md` | Il codice da usare quando il dubbio non è classificabile: `D-99` |
| Secondo rifiuto consecutivo: escalation | `fidelity-validator.md`, `orchestrator.md` | Che cosa cambia e che cosa non cambia al secondo giro (sezione 7) |

---

## 1. Le cinque categorie sempre bloccanti

La regola di gravità assoluta sta in `fidelity-validator.md` e non si ridiscute qui. Serve però
sapere che cosa ci rientra, perché la maggior parte dei falsi negativi nasce da un elemento non
riconosciuto come appartenente a queste categorie.

1. **Importo** — qualunque valore monetario, soglia, percentuale, aliquota, tasso, massimale,
   minimale, numero di rate.
2. **Data** — data assoluta, giorno di decorrenza, periodo di validità, orario di apertura o di
   chiusura di una finestra temporale.
3. **Scadenza** — durata ("entro 30 giorni"), termine finale, momento a partire dal quale la
   durata si conta, e la conseguenza del mancato rispetto.
4. **Obbligo** — qualunque enunciato che imponga, vieti o consenta un comportamento, con il suo
   soggetto e le sue eccezioni. Un permesso è un obbligo in forma negativa: trattarlo come
   opzionale è D-03.
5. **Riferimento** — norma, articolo, codice pratica, numero di modulo, nome esatto dell'ufficio o
   del canale, identificativo che la persona dovrà riportare o cercare.

`TODO-TEMA: aggiungere l'elenco chiuso dei riferimenti e dei termini tecnici dello scenario scelto che non possono essere sostituiti, parafrasati o abbreviati.`

---

## 2. Procedura di confronto

Il confronto è una verifica di copertura, non una lettura di impressione. Quattro passi, in
quest'ordine.

- **V-1 Inventario dell'originale.** Si estrae dall'originale l'elenco delle unità di
  significato: ogni obbligo, ogni condizione, ogni eccezione, ogni valore numerico o data, ogni
  soggetto che compie un'azione, ogni conseguenza, ogni riferimento. L'inventario si costruisce
  **sull'originale, prima** di leggere la versione semplificata: leggerla prima induce a
  riconoscere solo ciò che c'è già.
- **V-2 Allineamento.** Ogni unità dell'inventario si cerca nella versione semplificata e si
  segna come presente, alterata o assente. Il testo semplificato si scorre poi una seconda volta
  in senso inverso: ogni affermazione che non risale a nessuna unità dell'inventario è
  un'aggiunta.
- **V-3 Classificazione.** Ogni non corrispondenza riceve **un solo** codice `D-xx`, quello più
  specifico. Se un difetto ne soddisfa due, vince il più grave; se hanno la stessa gravità,
  vince quello più in basso nella tabella della sezione 3 (l'ordine è per specificità crescente).
- **V-4 Verdetto.** Si applica la regola di precedenza della sezione 4.

Vincolo di ordine: non si emette un verdetto prima di aver completato V-1 su tutto il passo.
Un inventario parziale produce un `approved` che non vale niente.

---

## 3. La tassonomia

Tassonomia **chiusa**: dieci tipi più un residuo. Nessun tipo si inventa a runtime.

### D-01 Omissione

Un'unità di significato presente nell'originale non compare nella versione semplificata.

- **Gravità:** bloccante se l'unità omessa appartiene a una delle cinque categorie della
  sezione 1. Non bloccante negli altri casi (esempi illustrativi, ripetizioni della fonte,
  formule di cortesia).
- **Test:** un elemento dell'inventario V-1 resta senza corrispondenza in V-2.
- **Esempio:** originale "entro 30 giorni dalla ricezione"; semplificato "entro 30 giorni".
  Sparisce il momento da cui si contano i giorni: la scadenza non è più calcolabile. Bloccante.
- **Correzione attesa:** PL-08.

### D-02 Aggiunta non supportata

La versione semplificata afferma qualcosa che la fonte non dice: un esempio, una stima di tempo,
una rassicurazione, un caso tipico, un canale alternativo.

- **Gravità:** sempre bloccante (G-01). Anche quando l'aggiunta è vera nel mondo: il sistema non
  ha modo di verificarla e non ha `source_refs` da citare (G-07).
- **Test:** un'affermazione del testo semplificato non risale a nessuna unità dell'inventario.
- **Esempio:** originale "presenta la domanda allo sportello"; semplificato "presenta la domanda
  allo sportello, oppure online dal sito". Bloccante.
- **Correzione attesa:** PL-08.

### D-03 Slittamento di modalità

La forza deontica del verbo cambia: obbligo che diventa consiglio o possibilità, possibilità che
diventa obbligo, divieto che diventa sconsiglio.

- **Gravità:** sempre bloccante.
- **Test:** confronto uno a uno dei verbi modali con la tabella PL-09 di `plain-language.md`.
- **Esempio:** originale "il richiedente è tenuto a"; semplificato "ti conviene". Bloccante.
  Vale anche il verso opposto: originale "puoi allegare"; semplificato "devi allegare" fa fare
  alla persona un lavoro che nessuno le ha chiesto.
- **Correzione attesa:** PL-09.

### D-04 Alterazione numerica o di data

Un valore cambia, o cambia in modo da non essere più lo stesso valore.

- **Gravità:** sempre bloccante (G-03).
- **Test:** confronto carattere per carattere di ogni valore; conteggio delle occorrenze;
  verifica delle sei operazioni vietate di PL-10.
- **Esempio:** "15.000 euro" che diventa "circa 15 mila euro"; "dal 1° marzo" che diventa "da
  marzo"; "da 2 a 5 giorni lavorativi" che diventa "pochi giorni". Tutti bloccanti.
- **Correzione attesa:** PL-10.

### D-05 Cambio di soggetto responsabile

Cambia chi deve fare la cosa, oppure il soggetto sparisce e la persona non capisce se tocchi a lei.

- **Gravità:** bloccante quando l'azione è un obbligo, un divieto o una condizione per ottenere
  qualcosa. Non bloccante quando la frase è puramente informativa.
- **Test:** ogni obbligo dell'inventario ha un soggetto; il soggetto nella versione semplificata
  è lo stesso. Attenzione al passivo senza agente e all'impersonale ("si deve", "va inviato"),
  che sono il modo tipico in cui il soggetto si perde.
- **Esempio:** originale "l'ufficio trasmette l'esito al richiedente"; semplificato "devi
  chiedere l'esito all'ufficio". Il carico si sposta sulla persona. Bloccante.
- **Correzione attesa:** PL-03.

### D-06 Perdita di condizione o eccezione

Una regola condizionata diventa una regola generale, oppure un'eccezione scompare.

- **Gravità:** sempre bloccante. È la divergenza più pericolosa, perché il testo risultante è
  più chiaro dell'originale e sembra migliore.
- **Test:** conteggio e allineamento 1:1 di tutti i marcatori condizionali ed eccettuativi
  ("se", "salvo", "tranne", "a condizione che", "solo per", "esclusi", "in mancanza di",
  "fatta eccezione per").
- **Esempio:** originale "la riduzione spetta ai nuclei con ISEE non superiore a 15.000 euro";
  semplificato "hai diritto alla riduzione". Bloccante: la persona chiede un beneficio che non
  le spetta e si vede rifiutare la pratica.
- **Correzione attesa:** PL-12.3 (la condizione apre il passo).

### D-07 Cambio di ordine con effetto sul significato

La sequenza cambia e la nuova sequenza non è eseguibile o cambia il risultato.

- **Gravità:** bloccante quando l'ordine è vincolante, cioè quando un passo è prerequisito di un
  altro, quando una scadenza dipende da un evento precedente, o quando un'azione è irreversibile.
  Non bloccante quando l'ordine è solo espositivo.
- **Test:** per ogni coppia di azioni, verificare se l'originale dichiara una dipendenza
  ("dopo aver", "una volta ottenuto", "prima di", "a seguito di"). Se la dichiara, l'ordine è
  vincolante.
- **Esempio:** originale "dopo aver ricevuto il codice, compila il modulo"; semplificato
  "compila il modulo e richiedi il codice". Bloccante.
- **Correzione attesa:** PL-13 (il `simplifier` non riordina; se l'ordine appare sbagliato nella
  fonte, è materia di `source-analyzer`, non di riscrittura).

### D-08 Ammorbidimento di una conseguenza

La conseguenza del mancato adempimento resta, ma perde forza: diventa incerta, generica o
rinviata.

- **Gravità:** sempre bloccante. La conseguenza è ciò che determina se la persona agisce oggi o
  fra due settimane.
- **Test:** ogni conseguenza dell'inventario mantiene (a) il suo nome, (b) la sua certezza,
  (c) il suo momento. La comparsa di "potrebbe", "rischi di", "in alcuni casi" davanti a una
  conseguenza dichiarata certa è il segnale.
- **Esempio:** originale "la domanda è archiviata"; semplificato "potrebbero esserci dei
  ritardi". Bloccante, e cumula con D-01 se il nome della conseguenza sparisce del tutto: in
  quel caso prevale D-08, che è più specifico.
- **Correzione attesa:** PL-11.

### D-09 Riferimento reso generico

Norma, articolo, numero di modulo, nome dell'ufficio o del canale sostituiti da una descrizione
generica, oppure termine tecnico rimpiazzato da un sinonimo approssimativo.

- **Gravità:** bloccante (categoria 5 della sezione 1). Il riferimento è ciò che la persona deve
  ritrovare identico sull'artefatto reale o dire a uno sportello.
- **Test:** ogni riferimento dell'inventario compare identico almeno una volta nel testo
  semplificato.
- **Esempio:** "modulo RD-12" che diventa "il modulo giusto"; "autocertificazione" che diventa
  "una tua dichiarazione".
- **Correzione attesa:** PL-07 (il termine resta e si aggiunge la glossa).

### D-10 Cambio del grado di certezza

Un enunciato incerto o condizionato nella fonte diventa una promessa, o viceversa un fatto certo
diventa un'ipotesi. Distinto da D-03, che riguarda la forza dell'obbligo, e da D-08, che riguarda
le conseguenze negative.

- **Gravità:** bloccante quando produce un'aspettativa su esito, tempi o importi. Non bloccante
  negli altri casi.
- **Test:** confronto dei marcatori epistemici ("di norma", "salvo verifica", "può essere
  concesso", "è concesso").
- **Esempio:** originale "il contributo può essere riconosciuto previa verifica"; semplificato
  "riceverai il contributo". Bloccante.
- **Correzione attesa:** PL-08.

### D-99 Non classificabile

Differenza percepita che non rientra in nessuno dei dieci tipi.

- **Gravità:** bloccante per definizione. `fidelity-validator.md` stabilisce che in dubbio si
  respinge: `D-99` è la forma in cui quel dubbio diventa un output leggibile invece di un verdetto
  senza motivo.
- **Obbligo aggiuntivo:** la motivazione descrive la differenza in una frase e dice perché non
  rientra negli altri codici. Un `D-99` ricorrente su più passi è il segnale che alla tassonomia
  manca un tipo: si aggiunge fra i giri, non durante un giro.

---

## 4. Verdetto

Il contratto `agents/schemas/fidelity-validator.output.json` gradua la gravità su tre livelli
(`bloccante`, `major`, `minor`). La regola di verdetto li usa così:

- **Precedenza.** Una sola divergenza `bloccante` rende il verdetto `rejected`, a prescindere da
  quante altre ce ne sono e da quanto il resto è buono.
- **Due o più `major` sullo stesso passo:** `rejected`. Una `major` isolata non forza il rifiuto,
  ma si elenca e il `simplifier` la corregge al giro successivo se ne fa uno.
- **Solo `minor`.** Verdetto `approved`, con le divergenze comunque elencate: servono al
  `simplifier` e restano come traccia nell'evidenza di validazione.
- **Nessuna divergenza.** Verdetto `approved` con elenco vuoto. Un elenco vuoto va bene solo se
  V-1 è stato completato: un inventario mai costruito produce sempre zero divergenze.
- **Confidenza.** `confidence` esprime quanto è affidabile **il confronto**, non quanto è buono il
  testo. Si abbassa quando l'originale è ambiguo, incompleto o contraddittorio. Sotto `0.6` su un
  passo che contiene importi, date o scadenze scatta il gate HITL dell'orchestratore (G-03):
  conviene ricordarlo, perché è un caso in cui un `approved` sincero non basta comunque.
- **Incomparabile.** Originale mancante o illeggibile: si applica il fallback di
  `fidelity-validator.md` (`rejected`, `tipo: uncomparable`); non si usa `D-99`, che serve per
  differenze osservate, non per confronti impossibili.

---

## 5. Come si scrive una divergenza

La forma è fissata dal contratto `agents/schemas/fidelity-validator.output.json`, che è congelato:
questa skill vincola il **contenuto** dei campi, non i campi.

| Campo dello schema | Che cosa ci va |
|---|---|
| `tipo` | Il valore dell'enum corrispondente al codice `D-xx`, secondo la tabella della sezione 6 |
| `gravita` | `bloccante`, `major` o `minor`, secondo la sezione 3 e la regola di conversione qui sotto |
| `testo_originale` | Citazione letterale dall'originale: la più breve che contenga il problema |
| `testo_semplificato` | Citazione letterale dal testo riscritto; per D-01 la stringa `assente` |
| `descrizione` | Il codice `D-xx` in apertura, poi una frase che dice **quale effetto pratico** ha la differenza sulla persona |
| `passo_id`, `verdict`, `iterazione` | Identificatore del passo (identico all'input), esito, numero del giro (1 o 2) |

**Conversione della gravità.** L'enum dello schema ha tre livelli; la sezione 3 ne usa due.
Le divergenze dichiarate bloccanti restano `bloccante`. Le altre diventano `major` se la
differenza cambia ciò che la persona capisce o fa, `minor` se resta sul piano espositivo.

**Perché il codice `D-xx` sta nella descrizione.** L'enum `tipo` ha sei valori e la tassonomia ne
distingue undici: il codice è il livello di dettaglio che serve al `simplifier` per sapere quale
regola `PL-xx` applicare (vedi `plain-language.md`, sezione 6), e la descrizione è l'unico campo
libero del contratto. Nessuno dei due file va modificato per ottenere entrambe le cose.

Esempio compilato, in forma leggibile:

> `tipo: slittamento_senso` · `gravita: bloccante` · `testo_originale`: "ai nuclei con ISEE non
> superiore a 15.000 euro" · `testo_semplificato`: "hai diritto alla riduzione" ·
> `descrizione`: "D-06 perdita di condizione. La condizione di accesso è sparita: chi ha un ISEE
> più alto presenterebbe una domanda destinata a essere respinta."

Motivazioni non valide, in nessun caso: "non mi convince", "si può migliorare", "poco chiaro",
"tono diverso". La leggibilità non è materia di questo agente.

---

## 6. Riepilogo: codice, gravità, valore di `tipo`, correzione attesa

| Codice | Divergenza | Gravità | `tipo` nello schema | Correzione attesa |
|---|---|---|---|---|
| D-01 | Omissione | bloccante se tocca una categoria della sezione 1 | `omissione` | PL-08 |
| D-02 | Aggiunta non supportata | sempre bloccante | `aggiunta_non_autorizzata` | PL-08 |
| D-03 | Slittamento di modalità | sempre bloccante | `obbligo_diventato_consiglio` | PL-09 |
| D-04 | Alterazione numerica o di data | sempre bloccante | `numero_cambiato` | PL-10 |
| D-05 | Cambio di soggetto responsabile | bloccante se l'azione è obbligo, divieto o condizione | `slittamento_senso` | PL-03 |
| D-06 | Perdita di condizione o eccezione | sempre bloccante | `slittamento_senso` | PL-12.3 |
| D-07 | Cambio di ordine con effetto sul significato | bloccante se l'ordine è vincolante | `slittamento_senso` | PL-13 |
| D-08 | Ammorbidimento di una conseguenza | sempre bloccante | `slittamento_senso` | PL-11 |
| D-09 | Riferimento reso generico | sempre bloccante | `slittamento_senso` | PL-07 |
| D-10 | Cambio del grado di certezza | bloccante se crea aspettative su esito, tempi o importi | `slittamento_senso` | PL-08 |
| D-99 | Non classificabile | sempre bloccante | `slittamento_senso` | nessuna automatica: va all'operatore |

Il sesto valore dell'enum, `uncomparable`, non corrisponde a nessun codice: è il fallback per
confronto impossibile (sezione 4).

---

## 7. Che cosa cambia al secondo giro

Il secondo giro sullo stesso passo è l'ultimo (`orchestrator.md`, limiti di iterazione).

1. Si riesegue **l'intera** procedura V-1..V-4 sul nuovo testo. Non si verifica solo la
   divergenza segnalata al primo giro: la correzione può averne introdotte di nuove.
2. Per ogni divergenza del primo giro si dichiara se è **risolta**, **persistente** o
   **trasformata** in un altro codice.
3. La soglia non si abbassa. Approvare al secondo giro un testo che al primo sarebbe stato
   respinto è il modo più semplice di svuotare di senso questo agente: l'escalation esiste
   esattamente per non doverlo fare.
4. Se il verdetto è di nuovo `rejected`, l'elenco delle divergenze del secondo giro è ciò che
   finisce nel dossier per l'operatore umano (`hitl-escalation.md`, sezione 3): va scritto
   pensando a chi non ha visto il primo giro.

---

## 8. Che cosa NON è una divergenza

Elencato perché un validator avversariale senza limiti produce rifiuti a raffica, consuma i due
giri disponibili e manda in escalation passi che andavano bene. Non si segnala:

- **N-1** la sostituzione di una parola con un sinonimo di registro più comune, quando forza,
  perimetro e soggetto restano identici ("trasmettere" che diventa "inviare");
- **N-2** l'esplicitazione di un soggetto implicito e univoco nella fonte ("va presentata" che
  diventa "devi presentarla", quando l'originale dice altrove che è il richiedente a presentarla);
- **N-3** la glossa di un termine tecnico mantenuto, se aggiunge solo la definizione del termine
  e nessun fatto nuovo (PL-07);
- **N-4** lo scioglimento di una frase lunga in più frasi brevi, a parità di contenuto;
- **N-5** il riordino espositivo quando l'originale non dichiara dipendenze (vedi D-07);
- **N-6** la formattazione: elenchi, titoli, grassetti, numerazione dei blocchi di PL-12.

In caso di dubbio fra N-x e D-xx vale comunque la regola del validator: si respinge. Ma il dubbio
deve riguardare il **significato**, non lo stile.
