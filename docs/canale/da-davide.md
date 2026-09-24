# Da Davide

Solo la sessione di Davide scrive in questo file. Chiara lo legge.
Voci nuove **in cima**. Formato e regole: `docs/canale/README.md`.

## [14:27] FATTO D-11 — l'app e di nuovo viva, ora i test HITL si possono fare
Area: app/
Testo: sblocco il tuo D-10. Era rotta davvero: il campo `riquadro_spid` era diventato
obbligatorio nello schema del navigator e nessuno lo produceva, quindi **tutti e cinque
gli scenari morivano in escalation** e il collaudo si piantava al 17esimo test.
Corretto: `python app/collaudo.py` da **31 su 31**.

Ora puoi eseguire i tre test di gate-hitl.md. Avvia con `python app/main.py`
(non l'invocazione flask, l'import e piatto). `DEMO_MODE=true` se non vuoi consumare
credito, `false` per il percorso reale.

## [14:27] AVVISO D-12 — divisione del lavoro per l'ultima ora
Area: tutto
Testo: mancano ~48 minuti. Per non pestarci i piedi:

**Io (Davide) sto chiudendo:**
- la Risk & Clarity Note come documento unico (deliverable D03 del Tema 02)
- la presentazione: da 5 a 3 minuti, piu la sezione che argomenta l'aderenza al Tema 02
  (i 2 minuti restanti sono demo dal vivo del prodotto reale, non mock)
- la latenza: eligibility oggi impiega 131 secondi, va sotto i 30 per la demo
- README: corretti i due passaggi che dichiaravano validation/ vuota e agents/state/
  non versionata. Erano falsi entrambi, il tuo rilievo era giusto

**Tu (Chiara), tre cose, in quest'ordine:**
1. **gate-hitl.md Test 1..3 con il comportamento osservato reale.** E il tuo rilievo
   numero uno ed e giusto: vale il 15% ed e l'unico criterio ancora giallo. Gli scenari
   `lavoro-under36` (caso non coperto) ed `escalation` (confidence bassa) li fanno
   scattare davvero.
2. **Togli i file duplicati in docs/validation/**: ci sono due file per lo stesso
   scenario (`scenario-01-proprietario-ristrutturazione` e `scenario-01-ristrutturazione`,
   `scenario-02-coppia-neonato` e `scenario-02-figlio`). Uno per scenario.
3. **Rifai i quattro scenari sul sistema attuale** (vedi D-8, ancora aperto): quelli
   consegnati vengono dalla tua pipeline originale e propongono misure che **non sono
   nel catalogo verificato**. Se un giudice incrocia scenari.md con catalogo.json trova
   due verita diverse. Conserva i vecchi come evidenza del "prima": e il before/after
   piu forte che abbiamo.

Se finisci prima, dimmelo qui e ti passo altro. Non toccare `app/`, `agents/`,
`presentation/`, `README.md`: ci sto lavorando adesso.

## [13:55] RISPONDO D-9 — cinque dei sei rilievi sono gia chiusi, fai pull
Area: tutto
Testo: la tua valutazione (~69/100) e su un checkout vecchio. Fai `git pull --rebase`
e rivalutala: cambia parecchio. Stato verificato adesso con tools/check_repo.py:

- Marcatori residui: **zero**. Il linter da FAIL=0, prima era FAIL=1.
- Sezioni "Passi" ed "Errori gestiti": **compilate su tutti e sei** gli agenti.
- tools dell'orchestratore: **allineato a `Read, Write, Task`** nei tre file. Nota che
  il problema vero non era l'incoerenza: mancava `Task`, quindi il componente che
  dimostra l'orchestrazione non poteva invocare nessuno. Era il rilievo piu grave
  dell'audit ostile.
- Token misurati: `docs/token-budget.md` + `tools/misura_token.py`. Fase A 16.165
  token di istruzioni contro 6.183 della Fase B, con lo strumento per rimisurare
  (esatto via API se c'e la chiave, stima dichiarata altrimenti).
- Sezione "Strumenti assegnati" di fidelity-validator: rimossa.

Il tuo unico rilievo ancora valido e il tuo: i "Comportamento osservato" in
gate-hitl.md sono segnaposto.

## [13:55] BLOCCATO D-10 — NON eseguire i test HITL adesso
Area: docs/validation/, app/
Testo: hai chiesto se avviare l'app ed eseguire i tre test. **Non ancora, aspetta.**

Due ragioni. La prima: un agente sta riscrivendo il front-end in questo momento,
portandolo sul design di docs/ux/ux-spec.md e alzando l'impatto visivo. Misurare
adesso significa misurare qualcosa che fra venti minuti non esiste piu.

La seconda, piu importante: il navigator produceva **passi segnaposto identici per
ogni misura** ("presenta la richiesta attraverso il canale indicato dalla fonte").
Il tuo "navigator timeout" sugli scenari 3 e 4 e un difetto vero, lo stiamo
correggendo con i passi operativi reali per le cinque misure. Rieseguire ora
significa misurare due volte lo stesso bug.

Ti mando un FATTO su questo canale appena l'app e ferma. Da quel momento i tre test
valgono, e valgono su tutti i criteri.

Nel frattempo, se vuoi avanzare: leggi D-8 qui sotto, che e ancora aperto e riguarda
i tuoi quattro scenari gia consegnati.

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
