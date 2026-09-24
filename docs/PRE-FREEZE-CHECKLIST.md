# Checklist di pre-freeze

Da eseguire negli **ultimi 30 minuti** prima della consegna, nell'ordine indicato.
Ogni voce e' binaria: o e' vera o non lo e'. Se una voce non e' vera e non c'e' tempo per
renderla vera, si applica la regola in fondo ("Se non c'e' tempo"): si dichiara, non si nasconde.

Motivo: la prima valutazione e' uno screening automatico dell'intero repository. Un'affermazione
non verificabile costa piu' di una lacuna dichiarata, e un'incoerenza fra due file e' esattamente
cio' che una lettura automatica trova per prima.

## Sequenza consigliata

| Minuti | Blocco | Perche' in questo punto |
|---|---|---|
| 0-3 | A. Verifica automatica | Produce la lista di lavoro dei 25 minuti successivi |
| 3-15 | B, C. Contenuti e coerenza | Sono le voci che richiedono di modificare file |
| 15-20 | D, E. Sicurezza e struttura | Veloci, ma bloccanti se falliscono |
| 20-25 | F. Presentazione | Va provata aperta davvero, non solo guardata |
| 25-30 | G. Pubblicazione | Push, poi verifica da fuori. Nessuna modifica dopo questo punto |

Proprieta' dei blocchi, come in `CLAUDE.md` par. 2: A, B, C a Davide; E (`app/`), F a Chiara;
D e G insieme, a voce.

---

## A. Verifica automatica

Prima cosa, sempre: il linter dice in trenta secondi quali voci meccaniche sono gia' a posto.

| ID | Voce | Come si verifica |
|---|---|---|
| PF-01 | `python tools/check_repo.py` esce con codice 0 (nessun FAIL) | `python tools/check_repo.py; echo $?` |
| PF-02 | Ogni WARN residuo e' stato letto e accettato consapevolmente, non ignorato | `python tools/check_repo.py --strict` e si discutono a voce le voci che restano |
| PF-03 | Il linter gira su una macchina pulita senza installare nulla | `python tools/check_repo.py` da una shell nuova: solo libreria standard, nessun `pip install` |

---

## B. Contenuti: marcatori, link, riferimenti

| ID | Voce | Come si verifica |
|---|---|---|
| PF-04 | Nessun marcatore `TODO-TEMA:` residuo in nessun file | Controllo "marcatori residui" del linter: deve essere OK |
| PF-05 | Nessun marcatore `TODO` residuo in nessun file | Stesso controllo: il linter distingue i due tipi e stampa file e riga |
| PF-06 | Le tre menzioni meta del marcatore (`docs/IDEA-INTAKE.md`, `docs/process-note.md`, `agents/subagents/fidelity-validator.md`) sono state riscritte in prosa | Il linter non le segnala piu'. **Non** aggiungerle a `FILE_META`: `presentation/index.html` contiene segnaposto veri e verrebbero nascosti |
| PF-07 | Nessun link relativo rotto nei file `.md` | Controllo "link relativi" del linter: OK |
| PF-08 | Ogni file citato fra backtick nei `.md` esiste | Controllo "riferimenti fra backtick" del linter: OK |
| PF-09 | Il `README.md` non contiene piu' frasi segnaposto: titolo, problema, soluzione, setup e validazione sono scritti | Lettura diretta del file dall'alto in basso, una volta sola, ad alta voce |
| PF-10 | La sezione "Setup" del README contiene i comandi esatti, eseguiti almeno una volta da chi non li ha scritti | L'altra persona li copia e li incolla in una shell nuova |

---

## C. Coerenza del sistema agentico

Le prime tre sono automatiche. Le altre no: vanno lette, perche' riguardano numeri e
affermazioni che un valutatore automatico ricalcola contando le righe dei file.

| ID | Voce | Come si verifica |
|---|---|---|
| PF-11 | Ogni agente citato in `agents/README.md`, `agents/orchestrator.md` e `agents/workflows/main-pipeline.md` ha un file in `agents/subagents/`, e viceversa | Controllo "coerenza dei nomi" del linter: OK |
| PF-12 | Il campo `name` del frontmatter coincide con il nome del file, per tutti gli agenti | Stesso controllo |
| PF-13 | Il model tier di ogni componente e' lo stesso in tutti i file che lo citano, frontmatter compreso | Controllo "coerenza dei model tier" del linter: OK |
| PF-14 | Tutti i file in `agents/schemas/` sono JSON validi | Controllo "validita' JSON" del linter: OK |
| PF-15 | Ogni agente ha lo schema di input e di output che dichiara di usare | `ls agents/schemas/` confrontato con la tabella "Indice dei file di schema" in `agents/schemas/README.md` |
| PF-16 | `maxTurns` nel frontmatter e il limite dichiarato in "Gate HITL / Iterazioni" dicono lo stesso numero per ogni agente | `grep -n "maxTurns" agents/subagents/*.md` e confronto con la sezione corrispondente di ciascun file |
| PF-17 | I limiti di iterazione in `agents/orchestrator.md` (2 giri, 3 interventi, 3 retry) coincidono con quelli scritti nei singoli agenti e nel `README.md` | `grep -rn "max 2\|massimo 2\|3 interventi\|3 blocchi" agents/ README.md` |
| PF-18 | Ogni conteggio dichiarato a parole coincide con il conteggio reale (agenti, guardrail, skill, schemi, passi del workflow) | `ls agents/subagents/*.md \| wc -l` (attesi 6 piu' il template), `grep -c '^- \*\*G-' agents/guardrails.md` (atteso 17), `ls agents/skills/*.md`, `ls agents/schemas/*.json \| wc -l` |
| PF-19 | La frase "Due agenti su tre girano su Haiku" in `agents/README.md` e' stata corretta con il conteggio reale | `grep -c "model: haiku" agents/subagents/*.md` e confronto con la tabella dei componenti nello stesso file |
| PF-20 | Il template `_TEMPLATE.md` e i sei agenti sono allineati: o gli agenti compilano tutte le sezioni, o il template e `CLAUDE.md` par. 6 non pretendono che lo facciano | Controllo "sezioni del template" del linter: OK, oppure decisione presa e scritta |
| PF-21 | Nessun agente descrive un compito che un altro agente dichiara come proprio | Lettura incrociata delle sezioni "Non fa" dei sei agenti: due minuti, e si fa in due |

---

## D. Sicurezza e configurazione

| ID | Voce | Come si verifica |
|---|---|---|
| PF-22 | Nessun segreto in chiaro in nessun file tracciato | Controllo "segreti in chiaro" del linter: OK |
| PF-23 | `.env` non e' tracciato da git | `git ls-files --error-unmatch .env` deve fallire; `git check-ignore -v .env` deve confermare la regola |
| PF-24 | `.env` non compare nella cronologia, non solo nell'ultimo commit | `git log --all --name-only --format= -- .env` non stampa nulla |
| PF-25 | `.env.example` contiene solo valori fittizi e tutte le variabili usate dal codice | Lettura del file; `grep -rn "getenv\|environ\|process.env" app/` e confronto uno a uno |
| PF-26 | Gli identificatori di modello in `.env.example` sono quelli ufficiali e omogenei fra loro | Verifica sulla documentazione ufficiale dei modelli, non a memoria |
| PF-27 | Nessun dato personale reale nei file committati, esempi e stati compresi (G-17) | `grep -rniE "@(gmail\|libero\|outlook)\." .` e lettura degli esempi in `agents/skills/` e `docs/validation/` |

---

## E. Struttura e completezza della consegna

| ID | Voce | Come si verifica |
|---|---|---|
| PF-28 | `app/`, `agents/`, `presentation/` esistono e contengono file veri, non solo `.gitkeep` | Controllo "cartelle obbligatorie" del linter: OK |
| PF-29 | `app/` contiene codice eseguibile, non solo il README | `ls -R app/` e un avvio reale seguendo la sezione Setup del README |
| PF-30 | `docs/validation/` contiene almeno una evidenza di validazione, con il caso provocato e il comportamento osservato | `ls docs/validation/` e apertura di ogni file |
| PF-31 | `docs/process-note.md` e' compilato, non piu' uno scheletro | Lettura: par. 3 e 6 sono quelli che restano vuoti piu' a lungo |
| PF-32 | `agents/README.md` contiene la tabella dei token misurati, oppure dichiara esplicitamente che sono stime e perche' | Lettura della sezione "Economia dei token" |
| PF-33 | Ogni cartella citata nel README esiste con il contenuto promesso | Controlli "link relativi" e "riferimenti fra backtick" del linter, piu' una lettura della sezione "Struttura del repository" |

---

## F. Presentazione

| ID | Voce | Come si verifica |
|---|---|---|
| PF-34 | `presentation/index.html` non carica risorse remote | Controllo "presentazione offline" del linter: OK |
| PF-35 | La presentazione si apre davvero senza rete | Si disattiva la connessione e si apre il file con doppio clic, non da un server locale |
| PF-36 | Nessun segnaposto visibile nelle slide | Il controllo "marcatori residui" copre l'HTML; in piu' una scorsa visiva di tutte le sezioni |
| PF-37 | I numeri nelle slide coincidono con quelli del repository (agenti, fasi, limiti, tier) | Confronto diretto con `agents/README.md` e `agents/orchestrator.md` |
| PF-38 | Il percorso della demo mostrato nelle slide e' quello che il repository sa davvero fare | Si esegue la demo con le slide aperte di fianco |

---

## G. Pubblicazione e visibilita'

Ultimo blocco. Dopo PF-43 non si tocca piu' niente.

| ID | Voce | Come si verifica |
|---|---|---|
| PF-39 | Nessuna modifica locale non committata | `git status --porcelain` non stampa nulla |
| PF-40 | Nessun commit locale non pushato | `git log --oneline @{u}..` non stampa nulla |
| PF-41 | Il ramo pushato e' quello che gli organizzatori guarderanno | `git rev-parse --abbrev-ref HEAD` e `git rev-parse --abbrev-ref @{u}` |
| PF-42 | Il repository e' pubblico e si apre da una finestra anonima, senza login | Si apre l'URL in una finestra di navigazione privata e si controlla che le quattro cartelle siano visibili |
| PF-43 | Il `README.md` si legge correttamente su GitHub: tabelle, diagrammi e link funzionano nella resa web | Stessa finestra anonima, si clicca ogni link del README |
| PF-44 | Il linter passa anche sul repository clonato da zero | `git clone <url> /tmp/verifica && cd /tmp/verifica && python tools/check_repo.py` |

---

## Se non c'e' tempo

Una voce che resta falsa si tratta cosi', in questo ordine:

1. **Si prova a renderla vera.** Quasi tutte costano meno di cinque minuti.
2. **Se costa di piu', si dichiara.** Una riga nel `README.md` o in `docs/process-note.md`
   par. 5 ("Limiti identificati") che dice esattamente che cosa manca e perche'.
3. **Non si cancella l'affermazione senza cancellare anche cio' che la promette.** Se si toglie
   una funzionalita', si tolgono anche le righe che la annunciano nel README, nella
   presentazione e nei file degli agenti: una promessa orfana e' peggio di una lacuna.

Non si fa mai il contrario: non si aggiunge un'affermazione al repository per coprire una voce
che non si e' riusciti a chiudere. Lo screening e' automatico e verifica; un'affermazione falsa
costa su tutti i criteri insieme, una lacuna dichiarata costa solo sul suo.
