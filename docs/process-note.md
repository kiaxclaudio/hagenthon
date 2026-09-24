# Nota sul processo

> **Come si tiene aggiornato questo file.** Si annota **mentre si lavora**, non alla fine: due
> righe subito dopo ogni decisione presa e dopo ogni correzione umana a un output dell'AI, più un
> passaggio breve a ogni sincronizzazione prevista dal playbook (0:50, 1:45, 2:45, 3:50).
> Ricostruire a posteriori produce un racconto plausibile e falso: le cose che contano qui — che
> cosa abbiamo scartato, che cosa l'AI ha sbagliato — sono esattamente quelle che alle 4:30 non si
> ricordano più. Le sezioni 4 e 8 sono registri: si scrive in fondo, non si riscrive sopra.
> Proprietario del file: Davide (`CLAUDE.md`, mappa di proprietà).

Quarto deliverable richiesto dagli organizzatori, insieme alla soluzione funzionante, alla
presentazione e all'evidenza di validazione (`docs/PLAYBOOK.md`).

---

## 1. Il team e la divisione del lavoro

Team di due: **Davide Polito** e **Chiara**.
`TODO-TEMA: completare il cognome di Chiara, come in README.md.`

La divisione non è per fasi ma per aree di proprietà dei file, definite in `CLAUDE.md`: Davide su
`agents/**` e sulla documentazione di processo, Chiara su `app/**`, `presentation/**` e
`docs/validation/**`. Nessuno scrive nei file dell'altro. I file condivisi sono tre
(`README.md`, `CLAUDE.md`, `agents/schemas/**`) e si toccano solo dopo essersi avvisati.

Il meccanismo che tiene insieme le due sessioni è `CLAUDE.md`: viene letto automaticamente da
entrambe le istanze di Claude Code, quindi i pesi di valutazione, i vincoli di stile e la mappa
di proprietà valgono per entrambi senza doverli ripetere a voce. Il ragionamento completo sta in
`docs/COLLABORAZIONE.md`.

---

## 2. Come abbiamo usato l'AI

**Impianto, vero fin dall'inizio.**

- Due sessioni di Claude Code sullo stesso repository clonato, una per persona, con un file di
  istruzioni condiviso (`CLAUDE.md`) come unico punto di allineamento fra le due.
- L'AI è usata in due modi diversi, che teniamo distinti anche nel racconto: **come strumento di
  lavoro** (scrivere i file del repository) e **come materiale del progetto** (il sistema
  agentico in `agents/`, che è il prodotto). Le decisioni prese sul secondo non dipendono dalla
  comodità del primo.
- Model tiering dichiarato per compito, non per abitudine: Haiku per classificazione e
  rilevamento, Sonnet per trasformazione, Opus per analisi e giudizio (`CLAUDE.md`, sezione 5).
  Ogni agente dichiara il proprio tier e lo motiva in una riga (G-11).
- Prima di scrivere codice abbiamo scritto i vincoli: 17 guardrail numerati in
  `agents/guardrails.md` e un template obbligatorio per ogni agente
  (`agents/subagents/_TEMPLATE.md`).

**Domande guida per completare la sezione durante le 5 ore.**

- Quali parti del repository sono state generate dall'AI a partire da una nostra specifica, e
  quali sono state scritte a mano perché la specifica era più lunga del risultato?
- Dove abbiamo dato all'AI un contesto sbagliato o incompleto, e come ce ne siamo accorti?
- Quali prompt sono stati riusati più volte, e sono diventati un file invece di restare in chat?

`TODO-TEMA: elencare gli usi concreti dell'AI durante la gara, distinguendo generazione, revisione, refactoring e ricerca. Per ciascuno: che cosa abbiamo chiesto, che cosa abbiamo ottenuto, che cosa abbiamo tenuto.`

`TODO-TEMA: dichiarare esplicitamente che cosa NON abbiamo delegato all'AI e perché (scelta del tema, scelta dell'artefatto reale, decisione su che cosa mostrare alla persona nei casi dubbi).`

---

## 3. Che cosa hanno rivisto o corretto le persone

La sezione che la giuria legge per capire se c'è stato un giudizio umano o solo accettazione.
Si compila **nel momento in cui la correzione avviene**, una riga per correzione.

| Ora | Output dell'AI | Chi ha rivisto | Che cosa è stato cambiato | Perché |
|---|---|---|---|---|
| | | | | |

**Domande guida.**

- Qual è la correzione più significativa che abbiamo fatto, cioè quella che senza di noi avrebbe
  lasciato nel repository qualcosa di sbagliato?
- Ci sono stati output plausibili ma falsi, o coerenti in sé ma incoerenti con un altro file?
- Abbiamo rifiutato una proposta dell'AI per una ragione di merito (non di gusto)? Quale?
- Abbiamo accettato qualcosa senza verificarlo? Se sì, va detto qui: è un limite, non una colpa.

`TODO-TEMA: compilare la tabella durante le 5 ore. Almeno tre righe, con una correzione di sostanza e non solo di forma.`

---

## 4. Decisioni tecniche

Ognuna nella stessa forma: che cosa abbiamo deciso, che cosa abbiamo scartato, perché, dove si
vede nel repository, che cosa costa. La colonna "che cosa costa" esiste perché una decisione
senza svantaggi, di solito, non è stata presa davvero.

**DT-1 — Due fasi con economie opposte.**
Il sistema è diviso in Fase A (preparazione offline di un artefatto, una volta sola) e Fase B
(sessione con la persona, ad alta frequenza).
*Alternativa scartata:* pipeline unica che gira a ogni interazione.
*Perché:* il lavoro semanticamente difficile si paga una volta e si persiste; il runtime legge da
file e usa solo modelli economici, quindi il costo non cresce con l'uso.
*Dove:* `agents/orchestrator.md`, `agents/workflows/main-pipeline.md`.
*Costo:* il percorso è legato a un artefatto specifico; se l'artefatto cambia, la Fase A va
rifatta.

**DT-2 — Chi scrive non approva.**
`simplifier` produce, `fidelity-validator` giudica, e sono due agenti separati con due tier
diversi.
*Alternativa scartata:* un solo agente che semplifica e si auto-verifica in un passaggio.
*Perché:* il vincolo centrale del problema — semplificare senza cambiare il significato — diventa
una proprietà verificabile del sistema invece di una raccomandazione dentro un prompt. Un agente
che controlla sé stesso non controlla niente.
*Dove:* `agents/subagents/simplifier.md`, `agents/subagents/fidelity-validator.md`,
`agents/skills/fidelity-diff-taxonomy.md`.
*Costo:* almeno una chiamata in più per passo, su un modello del tier più alto.

**DT-3 — L'escalation umana è una funzionalità, non un errore.**
Quattro gate con condizione numerica; quando scattano, il sistema si ferma, lo dice e produce un
dossier per una persona.
*Alternativa scartata:* degradare silenziosamente, mostrando il contenuto migliore disponibile
con un avviso.
*Perché:* su una pratica vera, un contenuto non verificato con un avviso viene letto lo stesso.
Fermarsi onestamente è l'unico comportamento difendibile.
*Dove:* `agents/orchestrator.md` (gate e limiti), `agents/skills/hitl-escalation.md` (procedura).
*Costo:* il sistema, in alcuni casi, non completa il compito; e serve una persona a valle.

**DT-4 — Model tiering per compito.**
Haiku per l'orchestratore, il profiler e il block-detector; Sonnet per le trasformazioni; Opus
solo per capire l'artefatto e per verificare la fedeltà.
*Alternativa scartata:* il modello più capace ovunque, per semplicità.
*Perché:* i due punti in cui sbagliare costa davvero sono la comprensione della fonte e il
giudizio di fedeltà. Tutto il resto è routing e classificazione su output già strutturati.
*Dove:* `CLAUDE.md` sezione 5, `.env.example`, sezione "Model tier" di ogni file agente.
*Costo:* tre modelli da configurare e da tenere allineati, invece di uno.

**DT-5 — Stato esternalizzato su disco.**
Profilo, modello della fonte, percorso approvato e sessione vivono in `agents/state/*.json`.
*Alternativa scartata:* tenere il contesto nella conversazione.
*Perché:* nessun componente deve portarsi dietro la storia degli altri; la sessione si può
interrompere e riprendere; lo stato è ispezionabile, quindi il comportamento è dimostrabile.
*Dove:* G-12, tabella dello stato in `agents/orchestrator.md`.
*Costo:* serializzazione e schemi da mantenere; lo stato può divergere dalla realtà se un agente
non lo aggiorna.

**DT-6 — Istruzioni lunghe fuori dai file degli agenti.**
Tre skill in `agents/skills/`, caricate solo dall'agente che le usa e solo nel punto in cui
servono.
*Alternativa scartata:* prompt lunghi dentro ciascun file agente.
*Perché:* i file agente restano contratti leggibili in trenta secondi, e 710 righe di procedura
non pesano su ogni invocazione. Le tre skill valgono più di cinque volte i quattro file agente
che le caricano.
*Dove:* G-13, `agents/skills/README.md`.
*Costo:* un livello di indirezione in più; la mappa dei caricamenti va tenuta aggiornata in un
punto solo.

**DT-7 — Contract-first.**
Gli JSON Schema in `agents/schemas/` si concordano all'inizio e si congelano.
*Alternativa scartata:* definire le interfacce man mano, di comune accordo, durante lo sviluppo.
*Perché:* è l'unica dipendenza reale fra due persone che lavorano in parallelo, e toglierla nella
prima ora vale più del tempo che costa.
*Dove:* `CLAUDE.md` sezione 4, `agents/schemas/README.md` e i 15 file di schema in
`agents/schemas/`, con un envelope comune (`_envelope.json`) esteso via `allOf` da ogni output.
*Costo:* mezz'ora iniziale senza codice, e rigidità se ci accorgiamo tardi che manca un campo.
Un caso reale: la tassonomia delle divergenze distingue undici tipi, l'enum `tipo` dello schema
ne ammette sei. Invece di cambiare il contratto, il codice fine viaggia nel campo `descrizione`
(`agents/skills/fidelity-diff-taxonomy.md`, sezione 5). Il congelamento ha funzionato: ha
costretto a una soluzione, non a una rinegoziazione.

`TODO-TEMA: aggiungere le decisioni tecniche legate allo scenario (formato e strategia di ingestione dell'artefatto reale, stack dell'app, tassonomie di dominio del profiler e del block-detector).`

---

## 5. Limiti identificati

Elencati come limiti, non come funzionalità future. Stato al momento in cui si scrive.

- **L-1 Il dominio non è ancora scelto.** I file degli agenti e le skill contengono marcatori
  `TODO-TEMA:` nei punti in cui serve un aggancio allo scenario: le tassonomie di dominio e gli
  esempi reali sono da riempire.
- **L-2 Il controllore è un modello.** `fidelity-validator` riduce il rischio di infedeltà, non
  lo annulla: un modello che verifica un modello può condividerne i punti ciechi. Le mitigazioni
  sono strutturali (agente separato, tassonomia chiusa, gravità assolute su numeri e obblighi,
  escalation al secondo rifiuto), non formali.
- **L-3 `confidence` è auto-dichiarata.** I gate numerici la usano come se fosse una misura, ma
  non è calibrata su dati. Un valore alto non è una garanzia.
- **L-4 Fedeltà verificata sul testo, non sull'esito.** Verifichiamo che il passo semplificato
  dica quanto dice l'originale. Non abbiamo verificato che una persona, seguendo il percorso,
  porti davvero a termine la pratica.
- **L-5 Nessun test con persone del gruppo destinatario.** Nessuna verifica di accessibilità
  strumentale, nessuna sessione osservata.
- **L-6 L'operatore umano non esiste nella demo.** I gate producono il dossier e lo registrano
  nello stato, ma la coda non ha un destinatario reale né un tempo di risposta dichiarabile.
- **L-7 Un solo artefatto.** Il sistema non è stato provato su una fonte diversa da quella della
  demo: la generalità è un'ipotesi, non un risultato.
- **L-8 Consumo di token dichiarato ma non misurato.** L'architettura è pensata per contenerlo e
  le leve sono visibili nei file, ma la tabella con i valori misurati su un run reale è ancora da
  produrre (`agents/README.md`).
- **L-9 Contratti scritti, non ancora esercitati.** Gli JSON Schema in `agents/schemas/` esistono
  e sono congelati, ma nessun output reale di agente è ancora stato validato contro di essi: la
  loro adeguatezza è un'ipotesi di progettazione.

`TODO-TEMA: aggiornare L-1, L-8 e L-9 quando decadono, e aggiungere i limiti emersi durante la passata di robustezza (3:15-3:50), con il comportamento osservato e non solo la descrizione del rischio.`

**Domande guida.**

- Qual è la cosa che questo sistema sembra fare e non fa?
- In quale situazione realistica il sistema fa un danno, e che cosa lo impedisce oggi?
- Che cosa abbiamo tagliato per stare nelle 5 ore, e che cosa cambierebbe se non l'avessimo
  tagliato?

---

## 6. Registro cronologico

Una riga per evento che ha cambiato la direzione del lavoro. Serve alla sezione 4 e alla
presentazione: è la fonte da cui si estraggono le decisioni, non un diario.

| Ora | Evento o decisione | Chi | Conseguenza |
|---|---|---|---|
| T-0 | Impianto del repository prima del via: `CLAUDE.md` condiviso, guardrail, template degli agenti, workflow, skill | Davide | Le 5 ore partono dai contenuti, non dalla struttura |
| | | | |

`TODO-TEMA: compilare il registro durante le 5 ore, almeno a ogni sincronizzazione.`
