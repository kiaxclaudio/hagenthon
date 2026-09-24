# Canale fra le due sessioni

Serve a far parlare la sessione Claude di Davide e quella di Chiara **senza passare
da una persona** e **senza generare conflitti git**.

Il problema che risolve non e la cortesia: e la collisione. Due sessioni che iniziano lo stesso
compito senza saperlo producono due versioni dello stesso file, e a un'ora dalla consegna
quella e la cosa che fa perdere piu tempo di qualunque bug.

## Come e fatto

Due file, uno per parte. **Ognuno scrive solo nel proprio e legge quello dell'altro.**
Non esiste un file condiviso: e cosi che i conflitti diventano impossibili per costruzione,
invece che improbabili per attenzione.

| File | Ci scrive | Lo legge |
|---|---|---|
| `docs/canale/da-davide.md` | solo la sessione di Davide | Chiara |
| `docs/canale/da-chiara.md` | solo la sessione di Chiara | Davide |

La guardia di proprieta (`agents/hooks/ownership_guard.py`) lo impone: se la sessione sbagliata
prova a scrivere nel file dell'altra, la scrittura viene rifiutata.

## Il protocollo, cinque regole

1. **Prima di iniziare qualunque compito**: `git pull --rebase`, poi leggi il file dell'altra
   parte. Se sta gia facendo quella cosa, non iniziarla.
2. **Prima di toccare qualcosa, dichiaralo**: scrivi una voce `PRENDO` nel tuo file e
   **pusha subito**, prima di scrivere il codice. Una dichiarazione arrivata dopo non serve a niente.
3. **Quando hai finito**, scrivi `FATTO` con lo stesso identificativo.
4. **Le domande si fanno qui**, non a voce: `CHIEDO` con un identificativo. La risposta va
   nel file di chi risponde, con `RISPONDO` e lo stesso identificativo.
5. **Non modificare mai il file dell'altra parte**, nemmeno per correggere un refuso.

## Formato di una voce

Le voci si aggiungono **in cima**, cosi l'ultima e sempre la prima che si legge.

```
## [HH:MM] TIPO id — titolo in una riga
Area: percorsi toccati
Testo: due righe al massimo.
```

`TIPO` e uno fra: `PRENDO`, `FATTO`, `CHIEDO`, `RISPONDO`, `AVVISO`, `BLOCCATO`.
`id` e progressivo per autore: `D-1`, `D-2`... per Davide, `C-1`, `C-2`... per Chiara.

## Regole di cortesia che evitano danni

- Se devi toccare un file dell'altra area, **non farlo**: scrivi `CHIEDO` e aspetta.
- `BLOCCATO` ha la precedenza su tutto: chi lo legge risponde prima di riprendere il proprio lavoro.
- Push ogni volta che scrivi qui. Un messaggio non pushato non esiste.
- Mai `git push --force`: cancelleresti il lavoro dell'altra parte.
