# Brief: evidenza di validazione (area di Chiara)

Deliverable richiesto dagli organizzatori: *"Un'evidenza di validazione — almeno una prova che
il risultato funziona"*. Oggi `docs/validation/` e vuota, ed e l'unica casella scoperta.
Copre il criterio Robustezza (15%) e il punto D5 di `docs/INTEGRAZIONE.md`.

Proprieta: `docs/validation/**` e di Chiara. Nessun altro ci scrive.

## Tre file

### 1. `docs/validation/scenari.md`
I quattro scenari di `docs/inbox/chiara-idea.md` eseguiti e catturati. Per ciascuno:
il profilo in ingresso (le cinque risposte), le misure proposte dal sistema, il verdetto —
corretto, incompleto, sbagliato.

Onesta prima di tutto: **uno scenario che fallisce e viene documentato vale piu di quattro
che "funzionano" senza prova**. Lo screening e automatico e verifica: una lacuna dichiarata
costa meno di un'affermazione gonfiata.

### 2. `docs/validation/prima-dopo.md`
Il confronto richiesto dal tema. A sinistra il testo originale di una misura come lo scrive
l'Agenzia delle Entrate, a destra come lo restituisce il sistema. Le misure vere, con le fonti,
sono in `agents/state/catalogo.json`.

La parte che conta e l'ultima riga: **cosa la persona riesce a fare dopo che prima non riusciva
a fare**. Non "il testo e piu chiaro", ma "sa quali documenti servono e dove andare".

### 3. `docs/validation/gate-hitl.md`
La prova che i controlli scattano. Provoca un fallimento di proposito: un profilo che non
corrisponde a nessuna misura, o un caso ambiguo. Cattura cosa fa il sistema.
Se rimanda al CAF invece di inventare una risposta, quella cattura da sola dimostra che
l'escalation umana e una funzionalita progettata e non un errore.

## Note pratiche

- L'app e in correzione: gli identificativi dei modelli erano sbagliati e non partiva.
  Arriva un `AVVISO` sul canale appena gira. Nel frattempo si possono gia scrivere la
  struttura dei tre file e i profili in ingresso.
- Per il prima/dopo si puo partire subito da `agents/state/catalogo.json`.
- Prima di ogni commit: `git config user.email` sull'indirizzo noreply. Il repository e pubblico.
