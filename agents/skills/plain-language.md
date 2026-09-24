# Skill: plain-language

| | |
|---|---|
| **Caricata da** | `agents/subagents/simplifier.md`. Unico consumatore. |
| **Quando** | Al passo A3 di `agents/workflows/main-pipeline.md`: alla prima riscrittura di un passo e a ogni correzione dopo un rifiuto di `fidelity-validator`. Fuori da A3 non sta in contesto. |
| **Cosa restituisce a chi la usa** | Le 14 regole `PL-01..PL-14`, applicabili e controllabili, e la **checklist C1..C9** da superare prima di emettere il JSON. Non cambia lo schema di output del `simplifier`: ne vincola il contenuto testuale. Una violazione non sanabile si cita per codice `PL-xx` nella ragione del fallback previsto da `simplifier.md`. |
| **Perché non è caricata da altri** | `intervener` produce una frase sola, già vincolata dalla causa diagnosticata e dal registro del profilo: caricare questa skill costerebbe più di quanto renda. `profiler`, `source-analyzer` e `block-detector` non producono testo destinato alla persona. |

---

## 0. Che cosa è già deciso altrove

Questa skill **non ridiscute** i vincoli del `simplifier`: li rende eseguibili. Mappa esplicita,
per evitare che la stessa regola viva in due file.

| Vincolo | Dove è stabilito | Che cosa aggiunge questa skill |
|---|---|---|
| Semplificare senza cambiare il significato | G-02, `simplifier.md` | Le operazioni di riscrittura che non lo violano mai (PL-07..PL-11) |
| Numeri, importi, date, scadenze invariati | G-03 | Le sei operazioni vietate sui numeri (PL-10) e il controllo C5 |
| Nessun consiglio professionale | G-04 | Come si riscrive una frase prescrittiva senza trasformarla in consiglio (PL-11) |
| Correggere il difetto segnalato, non riscrivere da capo | `simplifier.md` | La procedura di correzione mirata (sezione 6) |
| Registro linguistico del profilo | `state/profile.json` | `TODO-TEMA: registro (tu/lei), lunghezza massima del passo e modalità preferita per lo scenario scelto` |

La nomenclatura delle divergenze (`D-xx`) è definita una volta sola in
`agents/skills/fidelity-diff-taxonomy.md`. Qui viene solo citata.

---

## 1. Regole di forma

- **PL-01 Lunghezza della frase.** Nessuna frase supera **20 parole**. La media del passo
  riscritto sta **entro 15**. Una frase più lunga si spezza in due frasi; non si accorcia
  togliendo informazione.
- **PL-02 Una informazione per frase.** Una frase contiene **un fatto o un'azione**, non due.
  Al massimo **una subordinata**. Le catene "che... il quale... in quanto..." si sciolgono in
  frasi separate.
- **PL-03 Voce attiva con soggetto esplicito.** Ogni frase che descrive un'azione dice **chi la
  fa**. Il passivo è ammesso solo quando l'agente è realmente ignoto o irrilevante, e mai in una
  frase che esprime un obbligo. "La domanda deve essere presentata" diventa "Devi presentare la
  domanda". Il passivo che cancella l'agente è la causa più frequente di D-05.
- **PL-04 Verbi al posto dei nomi.** Le nominalizzazioni tornano verbi: "la presentazione della
  domanda deve avvenire entro..." diventa "devi presentare la domanda entro...".
- **PL-05 Negazioni.** Al massimo **una negazione per frase**, mai due ("non è escluso che
  non..."). La negazione diventa affermazione solo se il senso resta identico: "non è ammesso
  l'invio via e-mail" si può riformulare come "puoi inviare solo per posta" **soltanto se**
  l'originale dichiara che la posta è l'unico canale. Se non lo dichiara, è D-02.
- **PL-06 Riferimenti e pronomi.** Vietati "esso", "il medesimo", "di cui sopra", "quanto
  precede". Si ripete il nome della cosa, anche tre volte di fila. La ripetizione costa meno
  di un rimando.

## 2. Regole di contenuto

- **PL-07 Il gergo si spiega, non si elimina.** Il termine tecnico che la persona **vedrà
  sull'artefatto reale** resta nel testo, identico. Alla prima occorrenza si aggiunge una glossa
  di **massimo 15 parole**, nella forma: termine + "cioè" (oppure due punti) + spiegazione. Dalla
  seconda occorrenza si usa il termine da solo. Sostituire il termine con un sinonimo
  approssimativo è vietato: la persona non lo ritroverebbe sul modulo.
  - Ammesso: "l'ISEE, cioè l'indicatore della situazione economica della tua famiglia".
  - Vietato: "il tuo indicatore di reddito" (il termine sparisce: D-09).
- **PL-08 Il perimetro dell'informazione non cambia.** Non si aggiunge un esempio, un caso
  tipico, una rassicurazione o una stima di tempo che non siano nell'originale (G-01, D-02).
  Non si toglie un dettaglio perché sembra secondario (D-01). Il criterio non è
  "serve alla persona?", è "c'è nella fonte?".
- **PL-09 La forza del verbo si conserva.** Tabella di conversione obbligatoria.

  | Originale | Riscrittura ammessa | Riscrittura vietata |
  |---|---|---|
  | deve, è tenuto a, è obbligato a, è necessario | devi, sei obbligato a | ti conviene, è meglio, puoi |
  | può, ha facoltà di, è ammesso | puoi | devi |
  | è consigliabile, si raccomanda | ti conviene, è consigliato | devi |
  | non può, è vietato, non è ammesso | non puoi, è vietato | è sconsigliato |
  | entro | entro | preferibilmente entro, circa |

  Ogni scostamento da questa tabella è uno slittamento di modalità (D-03) ed è bloccante.
- **PL-10 Numeri, date, importi: sei operazioni vietate.** Su qualunque valore della fonte non si
  può: (1) arrotondare; (2) convertire unità o valuta; (3) cambiare il formato in modo che cambi
  la precisione ("01/03/2026" in "marzo 2026"); (4) tradurre una durata in un'altra unità
  ("30 giorni" in "un mese"); (5) sostituire il valore con un aggettivo ("15.000 euro" in "un
  reddito basso"); (6) omettere un estremo dell'intervallo ("da 2 a 5 giorni" in "pochi giorni").
  Il valore si **copia** dalla fonte, non si riscrive a memoria.
- **PL-11 Conseguenze e prescrizioni restano tali.** La conseguenza negativa (decadenza,
  archiviazione, sanzione, sospensione, rifiuto) si riporta con il suo nome e si spiega con
  PL-07. Non diventa mai un'eventualità generica come "potrebbero esserci dei ritardi": è D-08.
  Spiegare che cosa comporta una regola non è un consiglio; suggerire che cosa convenga fare alla
  persona sì, ed è vietato (G-04).

## 3. Struttura del passo

- **PL-12 Ordine fisso dei blocchi.** Un passo riscritto ha sempre questo ordine e salta i
  blocchi che l'originale non contiene:
  1. **titolo** — massimo 8 parole, comincia con un verbo all'infinito o con il nome della cosa;
  2. **a che serve** — una frase: che cosa ottieni completando il passo;
  3. **condizioni** — "Se... allora...", **prima** delle azioni, mai in coda;
  4. **azioni** — elenco numerato, un'azione per punto, verbo in apertura;
  5. **che cosa ti serve** — documenti o dati richiesti dall'originale;
  6. **attenzione** — scadenze e conseguenze, riportate secondo PL-10 e PL-11.
- **PL-13 Un passo resta un passo.** Il `simplifier` non spezza, non unisce e non riordina i
  passi: la sequenza è decisa da `source-analyzer`. L'elenco numerato del blocco 4 vive **dentro**
  il passo e non ne crea di nuovi.
- **PL-14 Budget di lunghezza.** Il passo riscritto può arrivare al **130%** delle parole
  dell'originale. L'unica ragione ammessa per crescere sono le glosse di PL-07. Oltre il 130%,
  o si tolgono parole di servizio (non informazione), o si applica il fallback di `simplifier.md`.

---

## 4. Esempi

**Esempio 1 — frase lunga con obbligo, scadenza e conseguenza.**

> *Originale:* "Il richiedente è tenuto a trasmettere la documentazione integrativa entro 30
> giorni dalla data di ricezione della presente comunicazione, decorsi i quali la domanda è
> archiviata."
>
> *Riscrittura:* "**Inviare i documenti mancanti.** Devi inviare i documenti che mancano. Hai 30
> giorni di tempo dal giorno in cui hai ricevuto questa comunicazione. Se non li invii entro 30
> giorni, la domanda viene archiviata: cioè chiusa senza una decisione."

Perché è corretta: soggetto esplicito (PL-03), obbligo conservato (PL-09), "30 giorni" identico
in entrambe le occorrenze (PL-10), conseguenza mantenuta e spiegata (PL-11 con PL-07), nessuna
frase oltre 20 parole.

**Esempio 2 — la stessa frase, riscritta male.**

> "Ti conviene mandare i documenti entro un mese, altrimenti potrebbero esserci dei ritardi."

Tre violazioni in quindici parole: obbligo diventato consiglio (PL-09, cioè D-03), "30 giorni"
diventato "un mese" (PL-10, cioè D-04), archiviazione diventata ritardo (PL-11, cioè D-08).
Tutte e tre bloccanti: il passo viene respinto al primo giro.

**Esempio 3 — gergo e riferimento.**

> *Originale:* "La dichiarazione può essere resa in regime di autocertificazione ai sensi
> dell'art. 46 del d.P.R. 445/2000."
>
> *Riscrittura vietata:* "Basta che lo dichiari tu." Sparisce il termine che la persona leggerà
> sul modulo e sparisce il riferimento normativo (D-09), e "può" diventa un fatto (D-03).
>
> *Riscrittura corretta:* "Puoi usare l'**autocertificazione**: una dichiarazione che firmi tu, al
> posto del certificato. La regola è l'articolo 46 del d.P.R. 445/2000."

**Esempio 4 — condizione portata in testa.**

> *Originale:* "La riduzione è applicata ai nuclei familiari con ISEE non superiore a 15.000 euro,
> previa presentazione della relativa attestazione."
>
> *Riscrittura:* "Se il tuo **ISEE** non supera 15.000 euro, hai diritto alla riduzione. L'ISEE è
> l'indicatore della situazione economica della tua famiglia. Per ottenere la riduzione devi
> presentare l'attestazione ISEE."

La condizione apre il passo (PL-12.3), l'importo è identico (PL-10), il termine resta e viene
spiegato una volta sola (PL-07), il vincolo "previa presentazione" resta un obbligo (PL-09).

`TODO-TEMA: sostituire questi quattro esempi con quattro estratti dell'artefatto reale dello scenario scelto, conservando un esempio di riscrittura sbagliata.`

---

## 5. Checklist di auto-controllo

Si esegue **prima** di emettere l'output. Nove controlli, tutti verificabili contando o
confrontando. Un controllo fallito non è un'opinione: è un difetto da correggere.

| # | Controllo | Soglia |
|---|---|---|
| C1 | Frase più lunga | ≤ 20 parole |
| C2 | Lunghezza media delle frasi | ≤ 15 parole |
| C3 | Frasi con più di una subordinata | 0 |
| C4 | Frasi di obbligo senza soggetto esplicito | 0 |
| C5 | Valori numerici, date e importi confrontati carattere per carattere con l'originale | corrispondenza totale, stesso numero di occorrenze |
| C6 | Condizioni ed eccezioni dell'originale ritrovate nel testo riscritto | 1:1, nessuna in meno |
| C7 | Termini tecnici dell'originale presenti almeno una volta identici, con glossa alla prima occorrenza | 100% |
| C8 | Verbi modali conformi alla tabella PL-09 | nessuno scostamento |
| C9 | Lunghezza totale rispetto all'originale | ≤ 130% |

Se un controllo fallisce e correggerlo costerebbe significato, **non si emette il testo**: si
applica il fallback dichiarato in `simplifier.md`, indicando nella ragione il codice `PL-xx` del
controllo fallito.

Regola di precedenza: **la fedeltà batte la leggibilità, sempre**. Un passo difficile da leggere
si escala; un passo facile e infedele arriva alla persona, ed è il danno che questo sistema
esiste per evitare.

---

## 6. Correzione dopo un rifiuto del validator

`simplifier.md` stabilisce che al rifiuto si corregge **il difetto segnalato**, non si riscrive da
capo. In pratica:

1. Si legge il codice `D-xx` di ogni divergenza bloccante del verdetto.
2. Si individua la regola `PL-xx` corrispondente: la corrispondenza sta nella colonna
   "correzione attesa" di `fidelity-diff-taxonomy.md`.
3. Si modifica **solo la frase citata** nella divergenza. Le altre restano invariate parola per
   parola: toccarle introduce divergenze nuove e brucia l'unico giro rimasto prima
   dell'escalation.
4. Si rieseguono i soli controlli C1..C9 toccati dalla modifica.
5. Le divergenze non bloccanti si correggono **solo** se la correzione non tocca frasi diverse da
   quelle già contestate.
