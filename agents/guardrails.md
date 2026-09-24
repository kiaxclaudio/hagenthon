# Guardrail del sistema agentico

Regole numerate, verificabili, valide per tutti gli agenti. Un guardrail che non si può
controllare guardando un output non è un guardrail: è un auspicio.

## Integrità del contenuto

- **G-01** Nessun agente inventa informazioni assenti nella fonte. Se un dato manca, va marcato
  `missing`, non stimato.
- **G-02** Semplificare non può cambiare il significato. Ogni semplificazione passa dal
  `fidelity-validator` prima di raggiungere l'utente.
- **G-03** Numeri, importi, date, scadenze e riferimenti normativi si riportano **identici**
  alla fonte. Mai arrotondati, mai riformulati.
- **G-04** Nessun agente dà consigli professionali (finanziari, legali, sanitari, fiscali).
  Spiega cosa significa una cosa; non dice cosa fare.

## Forma degli output

- **G-05** Ogni agente restituisce solo JSON conforme al proprio schema. Prosa fuori dal JSON = output non valido.
- **G-06** Ogni output porta `status` ∈ {`ok`, `degraded`, `hitl_required`} e `confidence` ∈ [0,1].
- **G-07** Ogni output porta `source_refs`: da dove viene ciò che afferma. Nessun riferimento = G-01 violato.

## Controllo del ciclo

- **G-08** Ogni ciclo agente↔agente ha un limite di iterazioni dichiarato. Al limite si escala, non si ritenta.
- **G-09** Un gate HITL è una condizione numerica o booleana verificabile, mai un giudizio soggettivo.
- **G-10** Nessun agente chiama sé stesso. La ricorsione la governa l'orchestratore.

## Economia

- **G-11** Ogni agente dichiara il suo model tier e lo giustifica in una riga.
- **G-12** Lo stato vive in `agents/state/*.json`, non nella finestra di contesto.
- **G-13** Le istruzioni lunghe stanno nelle skill, caricate on-demand.
- **G-14** Gli agenti si passano JSON, mai trascrizioni di conversazione.

## Sicurezza e tecnica

- **G-15** Nessun segreto nel repository. Solo `.env.example` con valori fittizi.
- **G-16** Ogni chiamata esterna ha timeout e retry con backoff esponenziale.
- **G-17** Nessun dato personale reale nei file di esempio o negli stati committati.

## Dominio: orientamento fiscale, non consulenza

Regole specifiche del prodotto. Non ripetono le precedenti: le applicano al caso in cui
l'informazione sbagliata diventa una pratica sbagliata di una persona vera.

- **G-18** Nessun calcolo personalizzato. I dati di una misura si citano come stanno nel catalogo;
  non si stima quanto spetterebbe a questa persona, non si sommano benefici, non si simulano
  importi. Il calcolo sul caso concreto è consulenza (G-04), non orientamento.
- **G-19** Nessuna misura fuori dal catalogo verificato. Ciò che non sta in
  `agents/state/catalogo.json` non viene nominato come esistente, nemmeno se il modello lo
  ricorda: la risposta corretta è il rimando a un CAF.
- **G-20** Ogni output destinato alla persona porta il rimando a un CAF o a un commercialista per
  le decisioni, e l'invito a verificare le scadenze sul sito dell'ente. È un campo dell'output,
  non una frase lasciata al modello.
- **G-21** Nessuna graduatoria fra misure. Gli elenchi si ordinano per criterio dichiarato e
  neutro (l'asse del profilo, poi il nome), mai per importo o beneficio: ordinare per valore è
  raccomandare senza dirlo.
- **G-22** Nessun termine tecnico senza voce di glossario verificata. Un documento che la persona
  non sa che cosa sia è un passo che non può compiere.
- **G-23** Il profilo contiene solo valori della tassonomia chiusa dichiarata in
  `agents/subagents/profiler.md`: nessun campo libero, nessun identificativo, nessun importo.
  Ciò che non è stato chiesto non viene dedotto (G-01) e non viene conservato (G-17).
- **G-24** Ogni misura del catalogo porta la data di consultazione della fonte. Un catalogo non
  datato non è verificabile: le scadenze fiscali cambiano e una misura corretta l'anno scorso è
  un'informazione sbagliata oggi.
