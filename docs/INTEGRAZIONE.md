# Protocollo di integrazione del codice

Cosa viene verificato quando la parte funzionale entra nel repository. Ogni voce risale a un
requisito preciso dei documenti degli organizzatori: non sono preferenze di stile.

Chi scrive codice puo leggere questa lista **prima**, ed evitare il giro di correzioni.

## A. Struttura e consegna
Fonte: *Modalita di consegna*.

| # | Verifica |
|---|---|
| A1 | La soluzione sta in `app/`. Niente codice sparso in altre cartelle. |
| A2 | Le tre cartelle obbligatorie restano `app/`, `agents/`, `presentation/`. Nessuna quarta cartella di primo livello senza motivo scritto nel README. |
| A3 | Nessuna copia divergente di file gia presenti altrove. `agents/` resta fonte unica, `.claude/` e generato. |

## B. Il prototipo deve funzionare
Fonte: *Risultato atteso* punto 01.

| # | Verifica |
|---|---|
| B1 | Esiste un comando di avvio documentato nel README che parte da zero su una macchina pulita. |
| B2 | Il percorso della demo gira dall'inizio alla fine senza intervento manuale. |
| B3 | Nessuna dipendenza da login o servizi esterni dentro il percorso di demo. |
| B4 | Prerequisiti dichiarati: versione runtime, dipendenze, variabili d'ambiente. |

## C. Qualita tecnica (criterio 12%)
Fonte: *Criteri di valutazione* 05.

| # | Verifica |
|---|---|
| C1 | Nessun segreto nel codice. Tutto da `.env`, con `.env.example` aggiornato. |
| C2 | Ogni chiamata al modello ha **timeout** esplicito. |
| C3 | Ogni chiamata ha **retry con backoff**, con un tetto. |
| C4 | Gli errori sono gestiti: nessuna eccezione non catturata sul percorso principale. |
| C5 | **Model tiering** applicato davvero nel codice, coerente con `agents/ARCHITETTURA.md`, non solo dichiarato. |
| C6 | File in UTF-8 senza BOM. Gli accenti italiani vanno verificati, non dati per scontati. |

## D. Robustezza (criterio 15%)
Fonte: *Criteri di valutazione* 03.

| # | Verifica |
|---|---|
| D1 | Ogni agente ha un **fallback** che produce output valido con `status: degraded`. |
| D2 | I **gate HITL** di `agents/ARCHITETTURA.md` sono implementati e scattano davvero. |
| D3 | I **limiti di iterazione** sono nel codice, non solo nella documentazione. |
| D4 | Al superamento di un limite si **escala**, non si ritenta. |
| D5 | Esiste almeno una esecuzione catturata in `docs/validation/` che mostra un gate che scatta. |

## E. Contratti e stato (criterio 24%)
Fonte: *Criteri di valutazione* 01, piu i contratti in `agents/schemas/`.

| # | Verifica |
|---|---|
| E1 | Ogni output di agente e **validato contro il suo schema** prima dell'uso. |
| E2 | Envelope rispettato: `status`, `confidence`, `source_refs`, `payload`. |
| E3 | Lo stato sta su **file** in `agents/state/`, non nella finestra di contesto. |
| E4 | Gli agenti si scambiano JSON, non prosa. |
| E5 | Il codice non ridefinisce i contratti: se serve un campo, si cambia lo schema. |

## F. Efficienza dei token (criterio 12%)
Fonte: *Criteri di valutazione* 04.

| # | Verifica |
|---|---|
| F1 | La Fase A non viene rieseguita a ogni conversazione: il catalogo si legge da disco. |
| F2 | Nessun agente riceve piu contesto di quanto gli serve. |
| F3 | Le istruzioni lunghe stanno nelle skill, caricate quando servono. |

## G. Vincoli del tema (Tema 02)
Fonte: *Temi della sfida*, Tema 02.

| # | Verifica |
|---|---|
| G1 | **Nessuna raccomandazione finanziaria** in nessuna stringa prodotta o mostrata. |
| G2 | Ogni scheda mostra il **disclaimer** e il rimando a CAF o commercialista. |
| G3 | Esiste una **capability software concreta**, non solo riscrittura di testi. |
| G4 | Percentuali, tetti, scadenze e requisiti provengono dal catalogo verificato, **mai** dalla memoria del modello. |
| G5 | Ogni dato numerico mostrato ha il suo `source_refs` risalibile. |

## H. Interfaccia
Fonte: `docs/ux/ux-spec.md` e brand Accenture dei documenti degli organizzatori.

| # | Verifica |
|---|---|
| H1 | I token di `docs/ux/accenture-tokens.css` sono usati, non riscritti a mano. |
| H2 | Contrasto, dimensione dei target e focus visibile rispettano la specifica. |
| H3 | Una domanda per schermata. Nessuna densita da dashboard. |
| H4 | Ogni termine tecnico ha la sua spiegazione a portata di clic. |

## Come si chiude la revisione

1. `python tools/check_repo.py` senza FAIL.
2. `python tools/sync_claude.py --check` allineato.
3. Il percorso di demo eseguito una volta davanti a entrambi.
4. Le voci non soddisfatte diventano correzioni assegnate, non appunti generici.
