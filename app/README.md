# app/ — il prototipo

Contiene la soluzione che la persona usa. È l'esecutore del sistema descritto in `agents/`,
non un'applicazione indipendente.

Principio: l'app implementa i contratti in `agents/schemas/`, non li ridefinisce.
Se serve un campo nuovo, si cambia lo schema (con il consenso di entrambi), non il codice da un lato solo.

## Requisiti tecnici non negoziabili
- Nessun segreto nel codice: tutto da `.env` (vedi `.env.example`).
- Ogni chiamata al modello ha timeout e retry con backoff (G-16).
- Ogni output di agente è validato contro il suo schema prima dell'uso.
- Il percorso di demo non dipende da login o servizi esterni che possono cadere.

TODO: stack e istruzioni di avvio, dopo la scelta del tema.
