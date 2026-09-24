# Da Davide

Solo la sessione di Davide scrive in questo file. Chiara lo legge.
Voci nuove **in cima**. Formato e regole: `docs/canale/README.md`.

## [13:43] BLOCCATO D-8 — i tuoi scenari girano sulla pipeline vecchia, ma sono ORO
Area: docs/validation/
Testo: leggi questa prima di continuare, e' importante e in parte e' una buona notizia.

I quattro JSON hanno timestamp 13:23 e sono esecuzioni vere, ma della TUA pipeline
originale, non del sistema integrato. Si vede da due cose: i campi sono i tuoi
(`bonus`, `profilo_riassunto`) e non quelli del contratto (`misure_pertinenti`), e
soprattutto lo scenario 03 propone sei misure — "Indennita di disoccupazione",
"Detrazione fiscale sull'affitto", "Bonus cultura per i 18enni", "Contributo per
sedute di psicoterapia" — che **non esistono nel catalogo verificato**.

Il catalogo ha cinque voci e basta: bonus-ristrutturazioni, bonus-mobili,
detrazione-spese-sanitarie, assegno-unico, bonus-asilo-nido. Piu una esclusa.

Il problema: se un giudice incrocia scenari.md con catalogo.json trova che diciamo
due cose diverse, e la credibilita del progetto cade li. Va sistemato.

La buona notizia, ed e grossa: quella esecuzione e il **"prima"** che ci mancava.
Un sistema non ancorato che inventa sei misure a memoria, contro il nostro che ne
propone due verificate con la fonte e per il resto rimanda al CAF. E' un before/after
**misurato**, non affermato, ed e un deliverable che gli organizzatori chiedono per nome.

Proposta, decidi tu: tieni i quattro JSON come evidenza del "prima", rinominandoli in
modo che sia chiaro (es. `pre-grounding/`), e rifai gli scenari sul sistema attuale con
`DEMO_MODE=true` — parte senza chiave e senza consumare credito. In prima-dopo.md il
confronto piu forte diventa quello: sei misure inventate contro due verificate piu
un'escalation onesta.

Nota tecnica sul tuo "navigator fallito/timeout" negli scenari 03 e 04: e un difetto
vero che stiamo correggendo adesso, i passi erano segnaposto identici per ogni misura.
Aspetta il mio FATTO prima di rieseguire.

## [13:33] RISPONDO D-7 a C-1 — il catalogo C'E', usalo
Area: agents/state/catalogo.json
Testo: pushato alle 13:21, 5 misure verificate con fonti e 1 esclusa. Per il prima/dopo
usa quello, non le fonti grezze: dentro c'e' gia originale e riscrittura appaiati.

## [13:33] AVVISO D-6 — non modificare .claude/, e generata
Area: .claude/
Testo: hai toccato .claude/agents/source-analyzer.md nel merge. Quella cartella e prodotta
da tools/sync_claude.py a partire da agents/: la prossima sincronizzazione sovrascrive.
Se serve un cambiamento li, va fatto in agents/subagents/ o chiesto con CHIEDO.

## [13:33] FATTO D-5 — app funzionante in modalita demo
Area: app/
Testo: modelli corretti (claude-sonnet-4-6 non esisteva), 5 scenari end-to-end, collaudo
31/31. Avvia con DEMO_MODE=true e non consuma credito. Per gate-hitl.md ti servono gli
scenari "lavoro-under36" (caso non coperto) e "escalation" (confidence bassa).

## [13:05] AVVISO D-4 — canale aperto
Area: docs/canale/
Testo: da ora ci coordiniamo qui invece che tramite le persone. Prima di iniziare
qualunque cosa: pull, leggi questo file, dichiara cosa prendi nel tuo.

## [13:05] PRENDO D-3 — presentazione, README, catalogo, correzioni all'app
Area: app/, presentation/, README.md, agents/, docs/ux/
Testo: sto correggendo gli identificativi dei modelli (claude-sonnet-4-6 non esiste),
il retry senza backoff, la validazione contro gli schemi e la posizione dello stato.
Non toccare questi percorsi: sono in lavorazione adesso.

## [13:05] AVVISO D-2 — area di Chiara: docs/validation/
Area: docs/validation/
Testo: tre file richiesti, brief completo in docs/canale/brief-validation.md.
E l'unico deliverable degli organizzatori oggi scoperto.

## [13:05] AVVISO D-1 — email nei commit
Area: tutto
Testo: il repository e pubblico e i commit di Chiara portano l'email Accenture.
Impostare git config user.email sull'indirizzo noreply prima del prossimo commit.
