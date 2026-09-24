# Skill: hitl-escalation

| | |
|---|---|
| **Caricata da** | `agents/orchestrator.md`, quando scatta uno dei gate HITL che il file dichiara. In più, **solo la sezione 4**, da `agents/subagents/intervener.md` al terzo intervento fallito sullo stesso passo: è l'unico componente che scrive testo destinato alla persona in Fase B. |
| **Quando** | Alla transizione verso `status: hitl_required`, prima di qualunque messaggio e prima di chiudere il passo. Mai preventivamente: finché nessun gate scatta, questa skill non sta in contesto. |
| **Cosa restituisce a chi la usa** | Tre artefatti e una procedura: il **dossier per l'operatore** (sezione 3), il **messaggio per la persona** (sezione 4), la **traccia da scrivere nello stato** (sezione 5), e le regole di chiusura del ciclo (sezione 6). |
| **Perché non è caricata da altri** | `profiler`, `source-analyzer`, `simplifier`, `fidelity-validator` e `block-detector` non gestiscono l'escalation: dichiarano `status: hitl_required` nel proprio output e si fermano. Decidere che cosa succede dopo è dell'orchestratore (G-10). Distribuire questa skill su sei agenti significherebbe sei copie della stessa procedura e sei modi diversi di eseguirla. |

---

## 1. Principio

L'escalation umana è un **esito progettato**, non un errore (vedi `agents/README.md`, terza
decisione architetturale). Un percorso che si ferma dicendo perché vale più di uno che tira a
indovinare su una pratica vera.

Da qui discendono due conseguenze operative che valgono per tutta la skill:

- **Un'escalation senza destinatario non è un'escalation.** Fermarsi e basta è un errore con un
  nome gentile. Ogni gate deve produrre qualcosa per qualcuno: una persona che legge un
  messaggio, un operatore che riceve un caso, o entrambi.
- **Un'escalation che perde il contesto costa più di quanto salva.** Se l'operatore deve
  ricostruire che cosa è successo, il sistema ha spostato il lavoro invece di gestirlo.

I gate e le loro condizioni numeriche sono dichiarati in `agents/orchestrator.md` (G-09) e non
si ridefiniscono qui. Questa skill dice che cosa fare **dopo** che uno di essi è scattato.

---

## 2. I gate, e che cosa cambia per ciascuno

| Gate (condizione in `orchestrator.md`) | Fase | Chi riceve | Che cosa vede la persona | Dossier | `motivo` in `run-state.json` |
|---|---|---|---|---|---|
| Secondo rifiuto del `fidelity-validator` sullo stesso passo | A | operatore | niente in quel momento: la Fase A è offline e il passo non entra nel percorso | completo, con le divergenze del secondo giro | `passo_hitl_required`, se in Fase B la persona arriva su quel passo |
| Tre interventi falliti sullo stesso passo | B | persona **e** operatore | messaggio della sezione 4, scritto da `intervener` | completo, con i tre interventi tentati | `max_interventi` |
| Tre blocchi consecutivi sullo stesso passo | B | persona **e** operatore | messaggio della sezione 4, scritto da `intervener` | completo, con le tre cause diagnosticate | `max_blocchi` |
| `confidence < 0.6` su un passo con importi, date o scadenze | A o B | operatore; in Fase B anche la persona | in Fase B: messaggio della sezione 4 | completo, con il valore di `confidence` e l'agente che l'ha emesso | `confidence_bassa` |
| `source-analyzer` in `degraded`: artefatto non interpretabile | A | operatore | niente: la Fase A si ferma, nessun percorso viene pubblicato | ridotto: non esiste ancora un passo, si allega la porzione illeggibile | nessuno: non esiste una sessione |

I primi due sono distinti anche nel contratto (`agents/schemas/run-state.json`, enum `motivo`):
tre interventi che non sbloccano e tre blocchi consecutivi sono due problemi diversi, il primo
della spiegazione e il secondo del passo. `passo_hitl_required` non è un quinto gate: è il modo in
cui un'escalation decisa in Fase A si manifesta in Fase B, quando la sessione incontra il passo
che non era stato approvato.

Regola derivata: **in Fase A non si parla mai alla persona**, perché non c'è nessuna sessione in
corso; si parla al team che prepara il percorso. In Fase B si parla a entrambi, e i due messaggi
hanno contenuti diversi perché rispondono a domande diverse.

`TODO-TEMA: chi è l'operatore umano nello scenario scelto (ruolo, non nome), attraverso quale canale riceve il dossier, e quale tempo di risposta possiamo dichiarare onestamente alla persona.`

---

## 3. Il dossier per l'operatore

**Criterio di completezza:** un operatore che non ha seguito la sessione deve capire il caso in
meno di 60 secondi e decidere senza aprire il sistema. Se manca anche solo uno degli elementi
seguenti, dovrà chiedere, e l'escalation avrà generato lavoro invece di risolverlo.

| # | Elemento | Perché serve |
|---|---|---|
| 1 | Identificativo della sessione o dell'artefatto (`run_id`, id dell'artefatto) | Ritrovare il caso senza cercarlo |
| 2 | Gate scattato, nella formulazione esatta di `orchestrator.md` | Distinguere "contenuto non affidabile" da "persona bloccata": sono due problemi diversi |
| 3 | Fase (A o B) e identificativo del passo | Sapere se si sta correggendo un percorso o assistendo qualcuno adesso |
| 4 | `source_refs` verso il punto esatto dell'originale (G-07) | Andare alla fonte senza cercarla a mano |
| 5 | Testo originale del passo | È la sola versione certamente fedele |
| 6 | Versione semplificata respinta, marcata come **non approvata** | Far vedere il tentativo, senza che possa essere scambiato per contenuto valido |
| 7 | Le divergenze dell'ultimo verdetto, con codice `D-xx` e gravità | È già la diagnosi: l'operatore corregge, non indaga |
| 8 | Cronologia dei tentativi: quanti giri, quante cause di blocco, quali interventi | Distinguere un caso difficile da un caso ripetuto |
| 9 | `confidence` e agente che l'ha emessa | Capire se il sistema sapeva di non sapere |
| 10 | Model tier usato e versione delle istruzioni (file agente e skill) | Rendere il caso riproducibile e capire se è un problema di configurazione |
| 11 | Profilo in forma **non identificante**: solo i bisogni rilevanti per il passo | Scrivere la correzione nel registro giusto, senza trattare dati personali |
| 12 | Data e ora dell'escalation | Ordinare la coda |

Vincoli sul dossier:

- **HE-01 Nessun dato personale in chiaro** (G-17). Il riferimento alla persona è il `run_id`. Se
  un dato personale compare dentro il testo dell'artefatto, si allega il riferimento alla fonte,
  non il valore.
- **HE-02 Niente prosa esplicativa.** Il dossier è una scheda di campi, non una relazione: è
  materiale per un operatore, non per un lettore.
- **HE-03 Il dossier si scrive anche quando nessuno lo leggerà subito.** In Fase A la coda può
  essere vuota: il dossier resta come evidenza di validazione del gate.

---

## 4. Il messaggio per la persona

Vale solo in Fase B. Lo scrive `intervener`, nel registro del profilo e con le regole di forma di
`plain-language.md` (PL-01..PL-06).

**Struttura in quattro blocchi, in quest'ordine.**

1. **Che cosa è successo**, detto in termini della persona e con il sistema come soggetto:
   "non riesco a spiegarti questo passaggio in modo sicuro", non "il contenuto ha fallito la
   validazione".
2. **Che cosa non deve fare**: non tirare a indovinare, non ricompilare, non inviare. È il blocco
   che evita il danno concreto.
3. **Che cosa succede adesso**: il canale, e un tempo **solo se lo conosciamo**.
4. **Che cosa può fare intanto**: almeno un'alternativa praticabile subito (vedi HE-07).

**Regole.**

- **HE-04 Il soggetto è il sistema, mai la persona.** Nessuna formulazione che suggerisca un
  errore di chi legge. Non "non hai completato correttamente", ma "questo passaggio non è chiaro
  abbastanza perché io te lo faccia fare".
- **HE-05 Non si mostra il contenuto non verificato**, nemmeno accompagnato da un avviso (G-02).
  Un testo marcato "forse impreciso" viene letto comunque. L'alternativa ammessa è rimandare al
  punto esatto della fonte originale tramite `source_refs`, dichiarando che è il testo originale,
  non una spiegazione.
- **HE-06 Niente informazioni inventate sull'escalation stessa** (G-01). Tempi di risposta,
  orari, nomi di uffici: se non li abbiamo come dato, non si scrivono. "Non so dirti quanto ci
  vorrà" è una frase accettabile; una stima inventata no.
- **HE-07 Sempre almeno un'alternativa praticabile ora.** In ordine di preferenza: continuare da
  un passo successivo indipendente; salvare il punto e riprendere; scaricare il riepilogo di
  quello che è già stato fatto; contattare una persona. Un'escalation senza alternativa è un
  vicolo cieco con buone maniere.
- **HE-08 Nessun consiglio professionale nemmeno qui** (G-04). L'escalation è il momento in cui è
  più forte la tentazione di aggiungere "io al posto tuo farei".
- **HE-09 La persona sa che cosa viene passato a un'altra persona.** Il messaggio dice che il
  caso viene inoltrato e che cosa contiene, in una riga.

**Esempio, scritto male.**

> "Errore: validazione fallita (confidence 0.42). Il contenuto potrebbe non essere accurato.
> Riprova più tardi o contatta l'assistenza."

Cinque difetti: gergo di sistema, nessun soggetto, la persona non sa che cosa non fare, nessun
tempo e nessun canale reale, nessuna alternativa.

**Esempio, scritto bene.**

> "Questo passaggio parla di una scadenza e di un importo. Non riesco a spiegartelo con
> sicurezza, quindi preferisco non farlo. **Non inviare il modulo per adesso.**
> Passo il caso a un operatore, insieme al punto del documento di cui stiamo parlando: non
> invio i tuoi dati personali. Non so dirti quanto ci vorrà, ma ti avviso qui.
> Intanto puoi salvare e riprendere da qui, oppure andare avanti con il passo 5, che non dipende
> da questo."

`TODO-TEMA: canale di contatto reale, eventuale tempo di risposta dichiarabile, e forma dell'avviso di ritorno per lo scenario scelto.`

---

## 5. Registrazione nello stato

Lo stato vive su disco (G-12). L'escalation si registra **dentro i file di stato già dichiarati
in `orchestrator.md`**, nei campi previsti dai contratti: non introduce nuovi file e non aggiunge
campi (entrambi gli schemi hanno `additionalProperties: false`).

| Fase | File e schema | Che cosa si scrive |
|---|---|---|
| A | `agents/state/journey.json` (`schemas/journey.json`) | il passo resta in `passi[]` con `stato: "hitl_required"`, `testo_semplificato: null` e `iterazioni_usate: 2`; `hitl_passi_count` viene incrementato. Il testo respinto **non entra nel percorso**: resta solo nel dossier, così nessun consumatore può mostrarlo per errore. `source_refs` è obbligatorio ed è ciò che rende possibile il rimando alla fonte di HE-05 |
| B | `agents/state/run-<id>.json` (`schemas/run-state.json`) | si appende una voce a `hitl_triggers[]` con `triggered_at`, `passo_id` e `motivo` preso dall'enum della sezione 2, e si porta `stato_sessione` a `hitl_escalated` |

Il **dossier non è un campo dello stato**: i due schemi sono chiusi. Si compone al momento
dell'escalation leggendo `journey.json`, `run-<id>.json` e l'ultimo output del validator, e viene
consegnato sul canale dell'operatore. Nello stato resta il fatto che l'escalation è avvenuta, che
è quanto serve per non perderla e per ricostruirla.

Regole.

- **HE-10 Prima si scrive, poi si parla.** La traccia nello stato si scrive **prima** di
  mostrare il messaggio e prima di restituire il controllo. Se la sessione cade subito dopo, il
  caso deve esistere lo stesso: un'escalation persa è peggio di un'escalation non fatta, perché
  la persona crede che qualcuno stia guardando.
- **HE-11 Idempotenza.** Una sola voce in `hitl_triggers[]` per coppia (`passo_id`, `motivo`).
  Un secondo evento identico non ne appende un'altra e non genera un secondo dossier: due dossier
  per lo stesso caso producono due operatori che lavorano sulla stessa cosa.
- **HE-12 I contatori non si azzerano.** Dopo un'escalation, i contatori di tentativi e interventi
  restano al valore raggiunto. Azzerarli riaprirebbe il ciclo che il gate ha appena chiuso.
- **HE-13 Nessun tentativo automatico dopo l'escalation** (G-08). Al limite si escala, non si
  ritenta. Il passo si riapre solo con l'esito umano della sezione 6.
- **HE-14 Lo stato registra i fatti, non il giudizio.** Nessuna valutazione sulla persona, nessuna
  ipotesi sulle sue capacità: eventi, contatori, codici.

---

## 6. Chiusura del ciclo

Un'escalation resta aperta finché non riceve uno di questi tre esiti. Nessuno di essi è
automatico: li decide una persona.

| Esito | Che cosa cambia nello stato | Che cosa vede la persona |
|---|---|---|
| **Passo corretto a mano** | in `journey.json` il passo passa a `stato: "approved"` e `testo_semplificato` contiene il testo scritto dalla persona; `hitl_passi_count` viene decrementato | il passo compare nel percorso |
| **Passo ritirato** | il passo resta `stato: "hitl_required"` con `testo_semplificato: null`: non è mostrabile | il percorso salta quel passo e rimanda alla fonte tramite `source_refs` |
| **Problema alla fonte** | l'artefatto è segnalato come difettoso; la Fase A va rieseguita e produce un nuovo `journey_id` | il percorso resta sospeso, e la persona ne è informata |

Nota di contratto: `schemas/journey.json` non prevede un campo che distingua un testo scritto da
una persona da uno approvato dal validator, e ha `additionalProperties: false`. Finché resta
così, la distinzione vive nel dossier e non nel percorso. Aggiungerla richiederebbe una modifica
concordata dello schema (`CLAUDE.md`, sezione 4).

- **HE-15 Il testo corretto a mano non passa dal `simplifier`.** È già stato validato da una
  persona; rimandarlo nel ciclo riaprirebbe la possibilità di un nuovo rifiuto su un contenuto
  che non è più generato dal sistema.
- **HE-16 Ogni escalation chiusa resta nello storico.** È il materiale che dice quali passi e
  quali tipi di divergenza si ripetono, cioè dove il sistema va corretto.

---

## 7. Come si dimostra che funziona

Un gate dichiarato e mai visto scattare non è una funzionalità: è una frase. Tre prove
riproducibili, da eseguire nella passata di robustezza e da catturare come evidenza in
`docs/validation/`:

1. **Contenuto non affidabile.** Si dà in pasto al `simplifier` un passo con una conseguenza
   pesante e si forza una riscrittura che la ammorbidisce (D-08). Atteso: due rifiuti,
   `hitl_required`, dossier completo, testo mai mostrato.
2. **Persona bloccata.** Si simulano tre blocchi consecutivi sullo stesso passo. Atteso: tre
   interventi distinti, poi il messaggio della sezione 4 con almeno un'alternativa, e la voce in
   `hitl_triggers[]` scritta **prima** della risposta, con `stato_sessione: "hitl_escalated"`.
3. **Fonte illeggibile.** Si fornisce un artefatto parzialmente illeggibile. Atteso:
   `source-analyzer` in `degraded`, Fase A fermata, nessun percorso pubblicato, dossier ridotto.

Per ogni prova l'evidenza utile è la coppia: che cosa ha visto la persona, che cosa è finito nello
stato.
