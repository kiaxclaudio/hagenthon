---
description: Allinea il repository e mostra i messaggi dell'altra sessione prima di iniziare un compito
argument-hint: "[testo del messaggio da lasciare, opzionale]"
---

Coordinamento fra la sessione di Davide e quella di Chiara. Regole: `docs/canale/README.md`.

Esegui in quest'ordine, senza saltare passaggi:

1. `git pull --rebase` per allinearti. Se fallisce, fermati e segnalalo: non lavorare su una base divergente.
2. Leggi `.team-role` nella radice per sapere chi sei.
3. Leggi **il file dell'altra parte**: se sei `davide` leggi `docs/canale/da-chiara.md`, se sei `chiara` leggi `docs/canale/da-davide.md`. Guarda le voci in cima, sono le piu recenti.
4. Riporta in modo compatto: le voci `PRENDO` ancora senza il corrispondente `FATTO` (cioe i lavori in corso dall'altra parte, che non vanno toccati), le voci `CHIEDO` senza risposta (cioe cosa aspetta da noi) e ogni `BLOCCATO`, che ha la precedenza su tutto.
5. Se l'utente ha passato un argomento in `$ARGUMENTS`, aggiungi una voce **in cima** al **proprio** file del canale, nel formato descritto nel README, scegliendo il tipo corretto e il prossimo identificativo progressivo. Poi committa e pusha subito: un messaggio non pushato non esiste.
6. Se non c'e argomento, non scrivere nulla: limitati al rapporto.

Non scrivere mai nel file dell'altra parte, nemmeno per correggere un refuso: la guardia di proprieta lo rifiuta ed e un rifiuto voluto.
