# Hook: i vincoli che non dipendono dal prompt

Un guardrail scritto in un file `.md` e' una richiesta al modello. Un hook e' un programma
che gira comunque, anche se il modello ha deciso diversamente. Qui stanno i tre controlli che
il sistema **non puo'** aggirare, perche' non passano dal suo giudizio.

Tre, non di piu': ogni hook e' un costo su ogni chiamata dello strumento che intercetta.
Sono registrati in `.claude/settings.json`, con `timeout: 10` ciascuno.

| Hook | Evento | Matcher | Blocca? | Guardrail |
|---|---|---|---|---|
| `ownership_guard.py` | `PreToolUse` | `Write\|Edit` | **si'**, `permissionDecision: deny` | CLAUDE.md par. 2, docs/COLLABORAZIONE.md par. 2 |
| `anti_consulenza.py` | `PostToolUse` | `Write\|Edit` | no, solo avviso | **G-04** (e G-05 sul formato dell'avviso) |
| `session_snapshot.py` | `Stop` | — | no, non puo' | **G-12**, G-17; evidenza di validazione (deliverable 03) |

## 1. `ownership_guard.py` — la mappa di proprieta' diventa eseguibile

**Cosa fa.** Prima di ogni `Write`/`Edit` confronta il file bersaglio con la mappa di
proprieta' di `docs/COLLABORAZIONE.md` e con il ruolo della sessione. Se il file e' dell'altra
persona, nega la scrittura e dice cosa fare invece: scrivere la richiesta nel proprio file di
status. Sui file condivisi (`CLAUDE.md`, `README.md`, `agents/schemas/**`) non blocca: ricorda
di avvisare l'altra persona.

**Perche' esiste.** Lavoriamo in due sullo stesso branch `main` senza pull request. La regola
"nessuno scrive nei file dell'altro" regge finche' entrambe le sessioni se la ricordano. Un
conflitto git a fine gara costa piu' di qualunque tempo risparmiato: qui la convenzione
diventa un controllo deterministico invece di una buona intenzione.

**Il ruolo.** Da `.team-role` nella radice, contenuto `davide` oppure `chiara`. Non e'
versionato (sta in `.gitignore`): e' la sola cosa che cambia fra le due macchine.

```bash
echo davide > .team-role     # da fare una volta, su ogni macchina
```

**Se `.team-role` manca non blocca niente**, e quando la scrittura tocca un'area contesa lo
dichiara in un `systemMessage`. Un repo appena clonato deve funzionare, non inciampare.

**Non emette mai `allow`.** Un `allow` scavalcherebbe il normale flusso dei permessi: una
guardia anti-conflitto puo' negare, o tacere. Autorizzare non e' compito suo.

## 2. `anti_consulenza.py` — il secondo strato contro il consiglio

**Cosa fa.** Dopo ogni scrittura sotto `agents/state/` o `app/` cerca nel file le formule da
consulenza finanziaria elencate in `frasi-vietate.txt` e le segnala con numero di riga.

**Solo segnalazione, mai blocco.** Distinguere "ti conviene chiedere il bonus" da "la misura
si chiede entro marzo" e' un giudizio linguistico, e un falso positivo che ferma il lavoro
costa piu' di quanto rende. Blocca il `fidelity-validator`, che e' semantico; qui si avvisa.

**Perche' esiste.** `agents/ARCHITETTURA.md` prevede due strati contro la consulenza: il
validator, semantico, in Fase A; questo hook, deterministico, a runtime. Il prodotto orienta
e spiega, **non dice cosa fare** (G-04). E' il vincolo che separa un servizio di
alfabetizzazione fiscale dall'abuso di professione.

**I pattern stanno in `frasi-vietate.txt`, non nel codice.** La lista cresce mentre si scrive
il catalogo: aggiungere una formula non deve voler dire toccare un programma. Formato:

```
<regex Python> => <motivo breve>
```

Righe vuote e righe con `#` ignorate, confronto sempre case-insensitive. Una regex invalida
viene segnalata e saltata: il controllo non si spegne per un refuso. Un pattern entra nella
lista solo se distingue il **consiglio** dalla **descrizione**; un falso positivo ricorrente
insegna a ignorare l'avviso, e allora tanto vale non averlo.

## 3. `session_snapshot.py` — l'evidenza si produce da sola

**Cosa fa.** Alla chiusura della sessione scrive `docs/validation/session-<timestamp>.json`
con: quando, `session_id`, ruolo di squadra, inventario di `agents/state/*.json` (nome,
dimensione, ultima modifica) e conteggi dalla trascrizione (messaggi, strumenti usati,
sub-agenti invocati).

**Riassunto minimo, non registro.** Del contenuto degli stati registra **solo i metadati**:
un profilo utente non finisce in un file committato (G-17). La trascrizione resta dove sta
(G-12).

**Perche' esiste.** La consegna chiede un'evidenza di validazione. Raccolta a mano a fine
gara non esiste; prodotta dal sistema a ogni sessione, c'e'.

**Non fa mai fallire la sessione.** Ogni operazione e' protetta, un errore finisce nel campo
`errori` dello snapshot e l'uscita e' sempre 0. Non emette mai `decision: block` (rimetterebbe
in moto il modello) e rispetta `stop_hook_active`, che e' la protezione contro il ciclo.

**Nota sulla mappa di proprieta'.** Scrive in `docs/validation/`, che e' area di Chiara. Non
e' un'eccezione alla regola: `ownership_guard` intercetta gli strumenti `Write`/`Edit` del
modello, non i file prodotti da un programma. Gli snapshot sono output della macchina, non
lavoro di una persona.

## Come si provano

I tre script leggono JSON da stdin e scrivono JSON su stdout: si provano senza Claude Code.
Ogni comando e' **una riga sola** (i `\` a fine riga valgono per bash).

```bash
# 1. caso bloccato: ruolo davide, scrittura in app/ (di Chiara)
echo davide > .team-role
echo '{"hook_event_name":"PreToolUse","tool_name":"Write","tool_input":{"file_path":"app/chat.py"},"cwd":"."}' | python agents/hooks/ownership_guard.py

# 2. caso permesso: ruolo davide, scrittura in agents/ (sua)
echo '{"hook_event_name":"PreToolUse","tool_name":"Write","tool_input":{"file_path":"agents/state/profilo.json"},"cwd":"."}' | python agents/hooks/ownership_guard.py
#    -> nessun output: nessuna decisione, la scrittura prosegue

# 3. caso senza ruolo
rm .team-role
echo '{"hook_event_name":"PreToolUse","tool_name":"Write","tool_input":{"file_path":"app/chat.py"},"cwd":"."}' | python agents/hooks/ownership_guard.py
#    -> systemMessage, nessun deny

# 4. anti-consulenza su un file con una formula vietata
mkdir -p agents/state && printf 'Ti consiglio di investire nel fondo.\n' > agents/state/prova.json
echo '{"hook_event_name":"PostToolUse","tool_name":"Write","tool_input":{"file_path":"agents/state/prova.json"},"cwd":"."}' | python agents/hooks/anti_consulenza.py
rm agents/state/prova.json

# 5. snapshot di sessione
echo '{"hook_event_name":"Stop","session_id":"prova-1","cwd":".","stop_hook_active":false}' | python agents/hooks/session_snapshot.py
ls docs/validation/
```

Per vedere cosa passa davvero agli hook dentro Claude Code: `claude --debug`, oppure il
comando `/hooks`.

## Prerequisito e portabilita'

Python 3 sul PATH come `python`, nessuna dipendenza esterna (solo libreria standard: `json`,
`os`, `re`, `sys`, `datetime`, `pathlib`).

Su una macchina dove l'eseguibile si chiama `python3` e non `python`, si cambia in un posto
solo: i tre `command` in `.claude/settings.json`. Gli script non vanno toccati.
