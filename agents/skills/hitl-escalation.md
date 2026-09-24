---
name: hitl-escalation
description: Procedura di escalation a una persona quando scatta un gate HITL, con i codici HE-01..HE-17. Caricare dall'orchestratore alla transizione verso hitl_required o all'attivazione del rimando a un CAF; restituisce il dossier per chi cura il catalogo, i quattro blocchi del messaggio per la persona, la traccia da scrivere nello stato e le regole di chiusura del ciclo.
---

# Skill: hitl-escalation

| | |
|---|---|
| **Caricata da** | `agents/orchestrator.md`, quando scatta uno dei gate HITL che il file dichiara. Nessun sub-agente la carica: i sub-agenti dichiarano `status: hitl_required` nel proprio output e si fermano lì. |
| **Quando** | Alla transizione verso `status: hitl_required`, o all'attivazione del rimando a un CAF, prima di qualunque messaggio e prima di chiudere la misura o la sessione. Mai preventivamente: finché nessun gate scatta, questa skill non sta in contesto. |
| **Cosa restituisce a chi la usa** | Tre artefatti e una procedura: il **dossier per l'operatore** (sezione 3), il **messaggio per la persona** (sezione 4), la **traccia da scrivere nello stato** (sezione 5), e le regole di chiusura del ciclo (sezione 6). |
| **Perché non è caricata da altri** | `profiler`, `source-analyzer`, `explainer`, `fidelity-validator`, `eligibility` e `navigator` non gestiscono l'escalation: la dichiarano e si fermano. Decidere che cosa succede dopo è dell'orchestratore (G-10). Distribuire questa skill su sei agenti significherebbe sei copie della stessa procedura e sei modi diversi di eseguirla. |

---

## 1. Principio

L'escalation umana è un **esito progettato**, non un errore (vedi `agents/README.md`, terza
decisione architetturale). Una risposta che si ferma dicendo perché vale più di una che tira a
indovinare su una detrazione vera.

Da qui discendono due conseguenze operative che valgono per tutta la skill:

- **Un'escalation senza destinatario non è un'escalation.** Fermarsi e basta è un errore con un
  nome gentile. Ogni gate deve produrre qualcosa per qualcuno: una persona che legge un
  messaggio, un operatore che riceve un caso, o entrambi.
- **Un'escalation che perde il contesto costa più di quanto salva.** Se l'operatore deve
  ricostruire che cosa è successo, il sistema ha spostato il lavoro invece di gestirlo.

I gate e le loro condizioni numeriche sono dichiarati in `agents/orchestrator.md` (G-09) e non si
ridefiniscono qui. Questa skill dice che cosa fare **dopo** che uno di essi è scattato.

**I due destinatari.** L'**operatore** è il curatore del catalogo: la persona del team che
mantiene la Fase A e che può correggere una misura o segnalare una fonte difettosa. Il
destinatario esterno è il **CAF o il commercialista**, ed è dove si manda la persona quando il
sistema non può rispondere (G-20). Non sono intercambiabili: al primo si consegna un dossier, al
secondo si indirizza una persona.

---

## 2. I gate, e che cosa cambia per ciascuno

| Gate (condizione in `orchestrator.md`) | Fase | Chi riceve | Che cosa vede la persona | Dossier | `escalation.motivo` in `run-state.json` |
|---|---|---|---|---|---|
| Secondo rifiuto del `fidelity-validator` sulla stessa misura | A | operatore | niente in quel momento: la Fase A è offline e la misura non entra nel catalogo | completo, con le divergenze del secondo giro | nessuno: non esiste una sessione. Nel catalogo la misura esce con `motivo: doppio_rifiuto_validator` |
| `source-analyzer` in `degraded`, o misura senza percentuale **oppure** senza tetto | A | operatore | niente: la Fase A si ferma sulla fonte e nessuna misura viene pubblicata | ridotto: non esiste una misura completa, si allega la porzione di fonte non interpretabile | nessuno: nel catalogo `motivo: fonte_non_interpretabile` oppure `dati_numerici_mancanti` |
| `eligibility` con `confidence < 0.6` su una misura | B | persona **e** operatore | messaggio della sezione 4: la misura non viene proposta e si indica il CAF | completo, con il valore di `confidence` e i requisiti rimasti da verificare | `confidence_bassa` |
| `eligibility` senza misure pertinenti, o domanda su una misura assente dal catalogo | B | persona; operatore in forma aggregata | messaggio della sezione 4, con il rimando al CAF | ridotto: profilo non identificante e misura cercata | `caso_non_coperto_dal_catalogo` |
| `navigator` senza alcun passo componibile | B | persona **e** operatore | messaggio della sezione 4: la procedura non è documentata | completo, con la voce di catalogo incompleta | `caso_non_coperto_dal_catalogo` |
| `profiler` con cinque risposte mancanti dopo la ri-domanda | B | persona | messaggio della sezione 4: le informazioni non bastano a orientare | ridotto | `profilo_incompleto` |
| La persona chiede che cosa le conviene fare | B | persona | messaggio della sezione 4: il sistema orienta, non consiglia (G-04) | nessuno: non è un difetto del sistema | `richiesta_di_consulenza` |

I motivi sono due enum chiusi e distinti, uno per fase, e nessuno dei due si riscrive a parole.
In Fase B vale `escalation.motivo` di `agents/schemas/run-state.json`, che punta all'enum di
`eligibility.output.json`: il campo si copia, non si traduce. In Fase A vale
`misure_escluse[].motivo` di `agents/schemas/catalogo.json`, con i suoi quattro valori
(`doppio_rifiuto_validator`, `fonte_non_interpretabile`, `dati_numerici_mancanti`,
`fuori_perimetro`). Tenere separati i due enum è ciò che permette di contare quante misure sono
uscite dal catalogo senza confonderle con le sessioni finite al CAF: sono due code di lavoro
diverse.

Regola derivata: **in Fase A non si parla mai alla persona**, perché non c'è nessuna sessione in
corso; si parla al team che prepara il catalogo. In Fase B si parla a entrambi, e i due messaggi
hanno contenuti diversi perché rispondono a domande diverse.

---

## 3. Il dossier per l'operatore

**Criterio di completezza:** un operatore che non ha seguito la sessione deve capire il caso in
meno di 60 secondi e decidere senza aprire il sistema. Se manca anche solo uno degli elementi
seguenti, dovrà chiedere, e l'escalation avrà generato lavoro invece di risolverlo.

| # | Elemento | Perché serve |
|---|---|---|
| 1 | Identificativo della sessione o della fonte (`run_id`, `fonte_id`) | Ritrovare il caso senza cercarlo |
| 2 | Gate scattato, nella formulazione esatta di `orchestrator.md` | Distinguere "misura non affidabile" da "persona senza risposta": sono due problemi diversi |
| 3 | Fase (A o B) e `misura_id` | Sapere se si sta correggendo il catalogo o assistendo qualcuno adesso |
| 4 | `source_refs` verso il punto esatto della fonte (G-07) | Andare alla pagina ufficiale senza cercarla a mano |
| 5 | Dati della misura come li ha estratti `source-analyzer` | È la sola versione certamente fedele alla fonte |
| 6 | Versione semplificata respinta, marcata come **non approvata** | Far vedere il tentativo, senza che possa essere scambiato per contenuto valido |
| 7 | Le divergenze dell'ultimo verdetto, con codice `D-xx` e gravità | È già la diagnosi: l'operatore corregge, non indaga |
| 8 | Cronologia: numero di giri consumati, `iterazione`, esiti precedenti | Distinguere un caso difficile da un caso ripetuto |
| 9 | `confidence` e agente che l'ha emessa | Capire se il sistema sapeva di non sapere |
| 10 | Model tier usato e versione delle istruzioni (file agente e skill) | Rendere il caso riproducibile e capire se è un problema di configurazione |
| 11 | Profilo in forma **non identificante**: solo i valori della tassonomia chiusa | Capire il caso senza trattare dati personali |
| 12 | Data e ora dell'escalation | Ordinare la coda |

Vincoli sul dossier:

- **HE-01 Nessun dato personale in chiaro** (G-17, G-23). Il riferimento alla persona è il
  `run_id`. Se un dato personale compare nel testo della fonte, si allega il riferimento alla
  fonte, non il valore.
- **HE-02 Niente prosa esplicativa.** Il dossier è una scheda di campi, non una relazione: è
  materiale per un operatore, non per un lettore.
- **HE-03 Il dossier si scrive anche quando nessuno lo leggerà subito.** In Fase A la coda può
  essere vuota: il dossier resta come evidenza di validazione del gate.

---

## 4. Il messaggio per la persona

Vale solo in Fase B. Lo compone l'orchestratore a partire dai quattro blocchi qui sotto: i blocchi
sono fissi e varia solo il motivo, perché nessun componente di Fase B scrive prosa libera alla
persona. Vale il registro di `plain-language.md` (PL-01..PL-06) e il vincolo di contratto
`testo_senza_consulenza`, che rifiuta le formule da consulenza.

**Struttura in quattro blocchi, in quest'ordine.**

1. **Che cosa è successo**, detto in termini della persona e con il sistema come soggetto:
   "non riesco a dirti con sicurezza se questa misura ti riguarda", non "confidence sotto soglia".
2. **Che cosa non deve fare**: non presentare domanda sulla base di questa conversazione, non
   dare per scontato di avere o non avere diritto. È il blocco che evita il danno concreto.
3. **Che cosa succede adesso**: il rimando a un CAF o a un commercialista, con il motivo.
4. **Che cosa può fare intanto**: almeno un'alternativa praticabile subito (vedi HE-07).

**Regole.**

- **HE-04 Il soggetto è il sistema, mai la persona.** Nessuna formulazione che suggerisca un
  errore di chi legge. Non "non hai risposto correttamente", ma "con le informazioni che ho non
  posso risponderti".
- **HE-05 Non si mostra il contenuto non verificato**, nemmeno accompagnato da un avviso (G-02,
  G-19). Un testo marcato "forse impreciso" viene letto comunque. L'alternativa ammessa è
  rimandare al punto esatto della fonte ufficiale tramite `source_refs`, dichiarando che è il
  testo dell'ente e non una spiegazione.
- **HE-06 Niente informazioni inventate sull'escalation stessa** (G-01). Tempi di risposta,
  orari, nomi di uffici, indirizzi di CAF: se non li abbiamo come dato, non si scrivono. "Non so
  dirti quanto ci vorrà" è una frase accettabile; una stima inventata no.
- **HE-07 Sempre almeno un'alternativa praticabile ora.** In ordine di preferenza: rispondere a
  una domanda rimasta aperta del profilo; vedere le misure per un'altra situazione dichiarata;
  ripartire con un profilo diverso; portare a un CAF il riepilogo di quanto raccolto. Un'escalation
  senza alternativa è un vicolo cieco con buone maniere.
- **HE-08 Nessun consiglio professionale nemmeno qui** (G-04). L'escalation è il momento in cui è
  più forte la tentazione di aggiungere "io al posto tuo farei".
- **HE-09 La persona sa che cosa viene passato a un'altra persona.** Il messaggio dice in una riga
  che il caso viene segnalato a chi cura le schede e che cosa contiene.

**Esempio, scritto male.**

> "Errore: eligibility confidence 0.42. I risultati potrebbero non essere accurati.
> Riprova più tardi o contatta l'assistenza."

Cinque difetti: gergo di sistema, nessun soggetto, la persona non sa che cosa non fare, nessun
canale reale, nessuna alternativa.

**Esempio, scritto bene.**

> "Questa misura dipende da un requisito che non mi hai detto, e riguarda un importo. Preferisco
> non dirti che ti spetta quando non ne sono sicuro. **Non presentare domanda sulla base di
> questa conversazione.**
> Per il tuo caso specifico il posto giusto è un CAF o un commercialista: possono verificare il
> requisito con i tuoi documenti. Segnalo la scheda a chi la cura: non invio i tuoi dati.
> Intanto puoi vedere le altre misure collegate alla tua situazione, oppure ricominciare
> indicando una situazione diversa."

---

## 5. Registrazione nello stato

Lo stato vive su disco (G-12). L'escalation si registra **dentro i file di stato già dichiarati in
`orchestrator.md`**, nei campi previsti dai contratti: non introduce nuovi file e non aggiunge
campi (gli schemi hanno `additionalProperties: false`).

| Fase | File e schema | Che cosa si scrive |
|---|---|---|
| A | `agents/state/catalogo.json` (`agents/schemas/catalogo.json`) | la misura **non** entra in `voci[]`; si appende una voce a `misure_escluse[]` con `misura_id`, `nome`, `motivo`, `escluso_il` e `source_refs`, più `divergenze_residue[]` quando il motivo è il doppio rifiuto. La spiegazione respinta non si scrive da nessuna parte nel catalogo, così nessun consumatore può mostrarla per errore: resta solo nel dossier |
| B | `agents/state/run-<id>.json` (`agents/schemas/run-state.json`) | si valorizza `escalation` con `attiva: true`, `motivo`, `attivata_il` e `messaggio_mostrato`, si porta `stato_sessione` a `hitl_escalated` e `ultimo_status` a `hitl_required` |

Il **dossier non è un campo dello stato**: gli schemi sono chiusi. Si compone al momento
dell'escalation leggendo il catalogo, `run-<id>.json` e l'ultimo output del validator o di
`eligibility`, e viene consegnato sul canale dell'operatore. Nello stato resta il fatto che
l'escalation è avvenuta, che è quanto serve per non perderla e per ricostruirla.

Regole.

- **HE-10 Prima si scrive, poi si parla.** La traccia nello stato si scrive **prima** di mostrare
  il messaggio e prima di restituire il controllo. Il contratto lo impone già da sé: con
  `attiva: true` diventano obbligatori `motivo`, `attivata_il` e `messaggio_mostrato`, quindi il
  messaggio va composto e scritto prima di poter essere mostrato. Se la sessione cade subito dopo, il caso deve
  esistere lo stesso: un'escalation persa è peggio di un'escalation non fatta, perché la persona
  crede che qualcuno stia guardando.
- **HE-11 Idempotenza.** Una sola escalation attiva per sessione: un secondo evento con lo stesso
  `motivo` aggiorna `aggiornato_il` e non genera un secondo dossier. Due dossier per lo stesso
  caso producono due operatori che lavorano sulla stessa cosa.
- **HE-12 I contatori non si azzerano.** Dopo un'escalation, `tentativi_timeout_modello` e il
  numero di giri consumati restano al valore raggiunto. Azzerarli riaprirebbe il ciclo che il gate
  ha appena chiuso.
- **HE-13 Nessun tentativo automatico dopo l'escalation** (G-08). Al limite si escala, non si
  ritenta. La misura si riapre solo con l'esito umano della sezione 6.
- **HE-14 Lo stato registra i fatti, non il giudizio.** Nessuna valutazione sulla persona, nessuna
  ipotesi sulle sue capacità o sulla sua situazione economica: eventi, contatori, codici.
- **HE-15 Il messaggio mostrato si conserva.** `messaggio_mostrato` è ciò che la persona ha
  davvero letto: è l'evidenza di che cosa è stato detto, non una ricostruzione a posteriori.

---

## 6. Chiusura del ciclo

Un'escalation di Fase A resta aperta finché non riceve uno di questi tre esiti. Nessuno di essi è
automatico: li decide una persona.

| Esito | Che cosa cambia | Che cosa vede la persona |
|---|---|---|
| **Misura corretta a mano** | la voce entra in `voci[]` con il testo scritto dall'operatore e il `source_refs` invariato, e sparisce da `misure_escluse[]`: la stessa misura non può stare nei due elenchi | la misura compare nelle schede |
| **Misura ritirata** | la misura resta in `misure_escluse[]` con il suo motivo: dichiarata, non sparita | le sessioni non la propongono e non la nominano come esistente (G-19); sul tema si rimanda al CAF |
| **Problema alla fonte** | la fonte è segnalata come difettosa e la Fase A va rieseguita su una versione aggiornata: nuova `versione` di catalogo e nuova data di consultazione (G-24) | nessuna misura di quella fonte viene proposta finché il catalogo non è rigenerato |

Nota di contratto: `catalogo.json#/$defs/voce_catalogo` vincola `verifica.verdict` a
`const: "approved"` e gli schemi sono chiusi. Il catalogo quindi **non distingue** una
spiegazione approvata dal validator da una scritta a mano dopo l'escalation. Finché lo schema
resta congelato (`CLAUDE.md`, sezione 4), la distinzione vive nel dossier archiviato in
`docs/validation/`, non nel catalogo: è una perdita accettabile, perché in entrambi i casi il
testo è passato da una verifica prima di essere pubblicato.

- **HE-16 Il testo corretto a mano non passa dall'`explainer`.** È già stato verificato da una
  persona; rimandarlo nel ciclo riaprirebbe la possibilità di un rifiuto su un contenuto che non è
  più generato dal sistema. Resta soggetto a G-24: porta comunque la data di consultazione.
- **HE-17 Ogni escalation chiusa resta nello storico.** È il materiale che dice quali misure e
  quali tipi di divergenza si ripetono, cioè dove il sistema va corretto.

Le escalation di Fase B non si "chiudono" dal lato del sistema: la persona è stata indirizzata a
un CAF, e il sistema non sa, né può sapere, che cosa succede dopo. Dichiararlo è più onesto che
simulare una presa in carico.

---

## 7. Come si dimostra che funziona

Un gate dichiarato e mai visto scattare non è una funzionalità: è una frase. Tre prove
riproducibili, da eseguire nella passata di robustezza e da catturare come evidenza in
`docs/validation/`:

1. **Misura non affidabile.** Si dà in pasto all'`explainer` una misura con una conseguenza
   pesante e si forza una riscrittura che la ammorbidisce (D-08). Atteso: due rifiuti,
   `esito_misura: "esclusa_hitl"`, dossier completo, testo mai pubblicato.
2. **Caso non coperto.** Si esegue una sessione con un profilo che il catalogo non copre. Atteso:
   nessuna misura proposta, messaggio della sezione 4 con almeno un'alternativa, `escalation`
   scritta **prima** della risposta, con `stato_sessione: "hitl_escalated"` e
   `motivo: "caso_non_coperto_dal_catalogo"`.
3. **Fonte illeggibile.** Si fornisce una pagina ufficiale parzialmente illeggibile. Atteso:
   `source-analyzer` in `degraded`, Fase A fermata sulla fonte, nessuna misura pubblicata,
   dossier ridotto.

Per ogni prova l'evidenza utile è la coppia: che cosa ha visto la persona, che cosa è finito nello
stato.
