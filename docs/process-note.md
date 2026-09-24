# Nota sul processo

Quarto deliverable richiesto: come abbiamo usato l'AI, cosa e stato rivisto da persone,
quali decisioni tecniche abbiamo preso, quali limiti abbiamo identificato.

Team: Davide Polito, Chiara Gario. Scritta durante il lavoro, non ricostruita alla fine.

## Come abbiamo usato l'AI

Non come un autocomplete, ma come una squadra di agenti con mandati disgiunti.
Il lavoro e stato spezzato in compiti che non si toccavano — architettura, contratti,
cablaggio, interfaccia, codice, presentazione — e affidati a sub-agenti paralleli, ognuno
con il proprio perimetro di file dichiarato e vietato.

Tre scelte di metodo hanno fatto la differenza:

**Un documento canonico prima del codice.** `agents/ARCHITETTURA.md` e stato scritto per primo
e dichiarato vincente su ogni altro file. Senza, sei agenti in parallelo avrebbero prodotto sei
architetture leggermente diverse. Con, ognuno ci si e agganciato.

**Perimetri di scrittura espliciti.** A ogni agente e stato detto non solo cosa fare, ma quali
file **non** toccare, con i nomi. Gli unici conflitti che abbiamo avuto sono nati dove questa
regola non c'era ancora.

**Revisione avversariale.** Due passaggi sono stati affidati a un agente istruito a cercare
solo i difetti: uno sull'architettura, uno sull'esperienza d'uso con la persona in mente.
Entrambi hanno trovato cose che chi aveva scritto non vedeva.

## Cosa hanno corretto le persone

| Momento | Cosa l'AI aveva prodotto | Correzione umana |
|---|---|---|
| Scelta del tema | Consiglio di puntare sul tema con la demo piu forte | I criteri dicevano che l'idea pesa 0%: la scelta e stata riportata sul dominio piu difendibile |
| Struttura di consegna | Una cartella `agents/` di sola documentazione | Il training deck degli organizzatori chiedeva artefatti Claude Code reali: riscritti con frontmatter valido |
| Permessi | Un `allow: Bash(python *)` inserito per comodita | Rimosso: allargava i permessi della macchina senza portare punti |
| Proprieta dei file | Mappa che non rispecchiava chi stava lavorando su cosa | Riassegnata due volte durante la gara, a decisione umana esplicita |
| Email nei commit | Commit firmati con indirizzi aziendali su un repository pubblico | Storia riscritta e configurazione cambiata prima che il lavoro si accumulasse |
| Regole di riscrittura | Una regola ammetteva "ti conviene" come formulazione valida | Vietata: e esattamente la consulenza che il tema proibisce |

## Decisioni tecniche

| Decisione | Alternativa scartata | Perche |
|---|---|---|
| Due fasi con economie opposte | Una pipeline unica a runtime | Il lavoro costoso si paga una volta per catalogo; il runtime legge un JSON gia verificato |
| Chi scrive non approva | Un solo agente che semplifica e controlla | Un agente che controlla se stesso non controlla niente |
| `fidelity-validator` con il solo tool `Read` | Dargli anche `Write` per comodita | Il giudice non deve poter riscrivere cio che giudica: e una proprieta dei permessi, non del prompt |
| Catalogo ancorato a fonti ufficiali | Lasciare che il modello ricordi le percentuali | Una cifra sbagliata su un bonus e un danno a una persona, non un refuso |
| `agents/` fonte unica, `.claude/` generata | Mantenere due copie a mano | Due cartelle che dicono cose diverse sono il difetto piu facile da trovare |
| Guardia di proprieta come hook | Fidarsi della disciplina | La disciplina diventa configurazione: non si puo dimenticare |
| Modalita demo senza chiamate API | Demo dal vivo sull'API | Una demo che dipende da rete e credito puo fallire nel momento peggiore |

## Limiti identificati

- **Il catalogo copre poche misure.** Sono quelle degli scenari di test, verificate una per una.
  Ampliarlo richiede di ripetere la Fase A, non di chiedere al modello.
- **Nessun calcolo personalizzato.** Il sistema non calcola ISEE, non stima importi sul caso di chi
  legge, non simula detrazioni. E una scelta: sarebbe consulenza.
- **Nessun accesso ai sistemi reali.** Non parla con il cassetto fiscale ne con l'INPS: spiega e
  indirizza.
- **Le fonti invecchiano.** Ogni voce porta la data di consultazione; oltre quella data il dato
  va riverificato.
- **La Fase A del catalogo consegnato e stata eseguita seguendo le istruzioni degli agenti senza
  passare dalle chiamate API**, per non consumare credito. E dichiarato in `agents/state/README.md`.
- **Il prototipo e un prototipo.** Nessuna autenticazione, nessuna persistenza oltre la sessione,
  nessun carico reale.

## Cosa non abbiamo delegato all'AI

La scelta del tema e del business case. Le decisioni sui permessi e sulla sicurezza. La mappa di
chi lavora su cosa. Cosa dichiarare come limite invece che nascondere. E ogni volta che un agente
ha proposto di allargare i propri poteri, la risposta e arrivata da una persona.
