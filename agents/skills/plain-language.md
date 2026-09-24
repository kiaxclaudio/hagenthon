---
name: plain-language
description: Regole di riscrittura in lingua semplice PL-01..PL-14 e checklist C1..C9 per l'explainer. Caricare al passo A2, alla prima stesura di una misura fiscale e a ogni correzione dopo un rifiuto del fidelity-validator; restituisce le regole applicabili, i nove controlli da superare prima di emettere il JSON e la procedura di correzione mirata per codice D-xx.
---

# Skill: plain-language

| | |
|---|---|
| **Caricata da** | `agents/subagents/explainer.md`. Unico consumatore. |
| **Quando** | Al passo A2 di `agents/workflows/main-pipeline.md`: alla prima riscrittura di una misura e a ogni correzione dopo un rifiuto di `fidelity-validator`. Fuori da A2 non sta in contesto. |
| **Cosa restituisce a chi la usa** | Le 14 regole `PL-01..PL-14`, applicabili e controllabili, e la **checklist C1..C9** da superare prima di emettere il JSON. Non tocca il contratto `agents/schemas/explainer.output.json`: vincola il contenuto dei campi testuali del `payload` (`titolo_semplice`, `cosa_e`, `quanto_vale`, `a_chi_spetta`, `attenzione`, `glossario[]`). Una violazione non sanabile si dichiara per codice `PL-xx`, con `status: hitl_required` (fallback previsto da `explainer.md`). |
| **Perché non è caricata da altri** | `eligibility` e `navigator` non riscrivono: citano il catalogo già verificato e le sue voci di glossario, prodotte in Fase A proprio con queste regole. `profiler` e `source-analyzer` non producono testo destinato alla persona, e `fidelity-validator` giudica con la propria tassonomia. |

---

## 0. Che cosa è già deciso altrove

Questa skill **non ridiscute** i vincoli dell'`explainer`: li rende eseguibili. Mappa esplicita,
per evitare che la stessa regola viva in due file.

| Vincolo | Dove è stabilito | Che cosa aggiunge questa skill |
|---|---|---|
| Semplificare senza cambiare il significato | G-02, `explainer.md` | Le operazioni di riscrittura che non lo violano mai (PL-07..PL-11) |
| Numeri, importi, date, scadenze invariati | G-03 | Le sei operazioni vietate sui numeri (PL-10) e il controllo C5 |
| Nessun consiglio professionale | G-04, `schemas/_envelope.json#/$defs/testo_senza_consulenza` | Come si riscrive una frase prescrittiva senza trasformarla in consiglio (PL-11) e quali formule il contratto rifiuta già prima del validator (PL-09) |
| Nessun calcolo sul caso di chi legge | G-18 | Perché l'esempio numerico costruito sul lettore è vietato anche quando le cifre vengono dalla fonte (PL-10) |
| Ogni termine tecnico ha una voce di glossario | G-22 | Forma e lunghezza massima della glossa, e in quale occorrenza si mette (PL-07) |
| Il disclaimer non si riformula | G-20, `schemas/_envelope.json#/$defs/disclaimer` (`const`) | L'unico testo esente dalle regole di forma: non si semplifica e non entra nel budget di PL-14 |
| Correggere il difetto segnalato, non riscrivere da capo | `explainer.md` | La procedura di correzione mirata (sezione 6) |
| Registro linguistico | `agents/subagents/explainer.md`, profilo di sessione (`schemas/profiler.output.json#/$defs/profilo`) | Registro fisso: seconda persona singolare, frasi sotto le 20 parole (PL-01), glossa obbligatoria per i termini elencati in `termini_non_noti` (PL-07) |

La nomenclatura delle divergenze (`D-xx`) è definita una volta sola in
`agents/skills/fidelity-diff-taxonomy.md`. Qui viene solo citata.

---

## 1. Regole di forma

- **PL-01 Lunghezza della frase.** Nessuna frase supera **20 parole**. La media della misura
  riscritta sta **entro 15**. Una frase più lunga si spezza in due frasi; non si accorcia
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
  sul modulo o sul sito dell'ente** resta nel testo, identico. Alla prima occorrenza si aggiunge una glossa
  di **massimo 15 parole**, nella forma: termine + "cioè" (oppure due punti) + spiegazione. Dalla
  seconda occorrenza si usa il termine da solo. Sostituire il termine con un sinonimo
  approssimativo è vietato: la persona non lo ritroverebbe sul modulo.
  - Ammesso: "l'ISEE, cioè l'indicatore della situazione economica della tua famiglia".
  - Vietato: "il tuo indicatore di reddito" (il termine sparisce: D-09).

  L'elenco chiuso dei termini intoccabili — denominazioni ufficiali delle misure, documenti e
  identità digitali, enti e canali, riferimenti normativi, termini del beneficio — sta in
  `agents/skills/fidelity-diff-taxonomy.md`, sezione 1. Qui non si ricopia: si applica.
- **PL-08 Il perimetro dell'informazione non cambia.** Non si aggiunge un esempio, un caso
  tipico, una rassicurazione o una stima di tempo che non siano nell'originale (G-01, D-02).
  Non si toglie un dettaglio perché sembra secondario (D-01). Il criterio non è
  "serve alla persona?", è "c'è nella fonte?".
- **PL-09 La forza del verbo si conserva.** Tabella di conversione obbligatoria.

  | Originale | Riscrittura ammessa | Riscrittura vietata |
  |---|---|---|
  | deve, è tenuto a, è obbligato a, è necessario | devi, sei obbligato a | ti conviene, è meglio, puoi |
  | può, ha facoltà di, è ammesso | puoi | devi |
  | è consigliabile, si raccomanda | la fonte consiglia di, l'ente raccomanda di | ti conviene, ti consiglio, devi |
  | non può, è vietato, non è ammesso | non puoi, è vietato | è sconsigliato |
  | entro | entro | preferibilmente entro, circa |

  Ogni scostamento da questa tabella è uno slittamento di modalità (D-03) ed è bloccante.
  Il consiglio della fonte resta **della fonte**: si riporta attribuendolo all'ente, mai in prima
  persona. Le formule in prima persona ("ti conviene", "ti consiglio", "dovresti") non arrivano
  nemmeno al validator: il contratto le esclude con un `not/pattern`
  (`schemas/_envelope.json#/$defs/testo_senza_consulenza`), quindi un testo che le contiene non è
  un output valido, e l'hook `agents/hooks/anti_consulenza.py` le segnala a chi scrive.
- **PL-10 Numeri, date, importi: sei operazioni vietate.** Su qualunque valore della fonte non si
  può: (1) arrotondare; (2) convertire unità o valuta; (3) cambiare il formato in modo che cambi
  la precisione ("01/03/2026" in "marzo 2026"); (4) tradurre una durata in un'altra unità
  ("30 giorni" in "un mese"); (5) sostituire il valore con un aggettivo ("15.000 euro" in "un
  reddito basso"); (6) omettere un estremo dell'intervallo ("da 2 a 5 giorni" in "pochi giorni").
  Il valore si **copia** dalla fonte, non si riscrive a memoria.
  L'esempio numerico costruito sul caso di chi legge ("se spendi 30.000 euro recuperi...") non è
  una settima operazione vietata: è già un calcolo personalizzato (G-18), e resta fuori anche
  quando ogni cifra viene dalla fonte.
- **PL-11 Conseguenze e prescrizioni restano tali.** La conseguenza negativa (decadenza,
  archiviazione, sanzione, sospensione, rifiuto) si riporta con il suo nome e si spiega con
  PL-07. Non diventa mai un'eventualità generica come "potrebbero esserci dei ritardi": è D-08.
  Spiegare che cosa comporta una regola non è un consiglio; suggerire che cosa convenga fare alla
  persona sì, ed è vietato (G-04).

## 3. Struttura della misura riscritta

- **PL-12 Ordine fisso dei blocchi.** Il testo vive nei campi testuali del `payload` e segue
  sempre questo ordine, saltando i blocchi che la misura non contiene:
  1. `titolo_semplice` — massimo 8 parole, il nome della misura in lingua corrente;
  2. `cosa_e` — una o due frasi: che cos'è e a che cosa serve;
  3. `quanto_vale` — percentuale, importo, tetto e base del tetto, copiati secondo PL-10;
  4. `a_chi_spetta` — array: una condizione della fonte per elemento, nella forma "Se... allora...";
  5. `attenzione` — array: scadenze, conseguenze e anni di recupero, secondo PL-10 e PL-11;
  6. `glossario[]` — i termini usati, con la glossa di PL-07 in `spiegazione_semplice`.

  Il blocco delle azioni non esiste qui: come si accede alla misura lo scrive `navigator` in
  Fase B, a partire dai canali del catalogo.
- **PL-13 Una misura resta una misura.** L'`explainer` non spezza, non unisce e non riordina le
  misure: il perimetro è deciso da `source-analyzer`. Gli elenchi vivono **dentro** la misura e
  non ne creano di nuove.
- **PL-14 Budget di lunghezza.** La misura riscritta può arrivare al **130%** delle parole
  della descrizione di origine. L'unica ragione ammessa per crescere sono le glosse di PL-07.
  Oltre il 130%, o si tolgono parole di servizio (non informazione), o si applica il fallback
  di `explainer.md`.

---

## 4. Esempi

**Esempio 1 — frase lunga con obbligo, scadenza e conseguenza.**

> *Originale:* "Il contribuente è tenuto a trasmettere la documentazione integrativa entro 30
> giorni dalla data di ricezione della presente comunicazione, decorsi i quali l'istanza di
> rimborso è archiviata."
>
> *Riscrittura:* "**Mandare i documenti che mancano.** Devi mandare i documenti che mancano. Hai
> 30 giorni di tempo dal giorno in cui hai ricevuto questa comunicazione. Se non li mandi entro
> 30 giorni, l'**istanza di rimborso** viene archiviata. Archiviata vuol dire chiusa senza una
> decisione. L'istanza di rimborso è la domanda con cui chiedi indietro dei soldi allo Stato."

Perché è corretta: soggetto esplicito (PL-03), obbligo conservato (PL-09), "30 giorni" identico
in entrambe le occorrenze (PL-10), conseguenza mantenuta e spiegata (PL-11 con PL-07), il termine
"istanza di rimborso" mantenuto e glossato invece che sostituito (PL-07, altrimenti D-09),
nessuna frase oltre 20 parole.

**Esempio 2 — la stessa frase, riscritta male.**

> "Ti conviene mandare i documenti entro un mese, altrimenti potrebbero esserci dei ritardi."

Tre violazioni in quindici parole: obbligo diventato consiglio (PL-09, cioè D-03), "30 giorni"
diventato "un mese" (PL-10, cioè D-04), archiviazione diventata ritardo (PL-11, cioè D-08).
Tutte e tre bloccanti: la misura viene respinta al primo giro. In più "ti conviene" fa fallire il
`not/pattern` di `testo_senza_consulenza`: quel testo non è nemmeno un output conforme allo
schema, e il rifiuto del validator sarebbe il secondo problema, non il primo.

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

La condizione sta in `a_chi_spetta` (PL-12.4), l'importo è identico (PL-10), il termine resta e
viene spiegato una volta sola (PL-07), il vincolo "previa presentazione" resta un obbligo
(PL-09).

`TODO-TEMA: gli esempi 1 e 2 sono formulazioni tipiche di una comunicazione dell'Agenzia delle Entrate, non citazioni verificate. Sostituirli con due estratti letterali delle pagine scaricate in agents/state/fonti/ appena il primo catalogo è stato costruito. Gli esempi 3 e 4 vengono già dal dominio fiscale e restano.`

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
applica il fallback dichiarato in `explainer.md`, dichiarando il codice `PL-xx` del controllo
fallito.

Regola di precedenza: **la fedeltà batte la leggibilità, sempre**. Una misura difficile da
leggere si escala; una misura facile e infedele arriva alla persona, ed è il danno che questo
sistema esiste per evitare.

---

## 6. Correzione dopo un rifiuto del validator

`explainer.md` stabilisce che al rifiuto si corregge **il difetto segnalato**, non si riscrive
da capo. In pratica:

1. Si legge il codice `D-xx` di ogni divergenza bloccante del verdetto.
2. Si individua la regola `PL-xx` corrispondente: la corrispondenza sta nella colonna
   "Correzione attesa" della tabella di riepilogo di `fidelity-diff-taxonomy.md` (sezione 6).
   Il codice `D-xx` si legge in apertura del campo `descrizione` della divergenza.
3. Si modifica **solo la frase citata** nella divergenza. Le altre restano invariate parola per
   parola: toccarle introduce divergenze nuove e brucia l'unico giro rimasto prima
   dell'escalation.
4. Si rieseguono i soli controlli C1..C9 toccati dalla modifica.
5. Le divergenze non bloccanti si correggono **solo** se la correzione non tocca frasi diverse da
   quelle già contestate.
6. Si porta `payload.iterazione` a 2 e si dichiara, per ogni frase cambiata, il codice `D-xx` a
   cui risponde. È l'ultimo giro disponibile (`orchestrator.md`, limiti di iterazione): se non
   basta, la misura esce `hitl_required` e non entra nel catalogo.
