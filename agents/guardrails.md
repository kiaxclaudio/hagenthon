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
