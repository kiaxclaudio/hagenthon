Esegui il flusso completo di analisi del profilo utente:

1. Attiva l'agente orchestratore per raccogliere il profilo in 5 step (situazione vita, abitativa, reddituale, supporto fiscale, timing)
2. Passa il profilo JSON all'agente eligibility per identificare i bonus pertinenti
3. Passa l'output di eligibility all'agente explainer per tradurre in linguaggio semplice
4. Passa l'output di explainer all'agente navigator per generare le istruzioni pratiche
5. Restituisci la scheda finale all'utente con bonus, spiegazioni e percorsi

Se `escalation: true` nel profilo prodotto dall'orchestratore, interrompi la pipeline e mostra il messaggio di rimando al CAF invece di procedere con eligibility.

Argomenti opzionali: $ARGUMENTS può contenere un profilo JSON pre-compilato per saltare la fase di raccolta e avviare direttamente dalla chiamata a eligibility.
