# Come lavoriamo in due

Il problema di un hackathon in coppia non è dividersi i compiti: è non bloccarsi a vicenda
e non riscrivere la stessa cosa due volte. Qui ci sono i quattro meccanismi che lo impediscono.

## 1. Il repo è il canale, non la chat

Entrambi usiamo Claude Code sullo stesso repository clonato. Nella radice c'è `CLAUDE.md`:
lo leggono **automaticamente entrambe le sessioni**. Dentro ci sono i pesi di valutazione,
la mappa di proprietà dei file, la disciplina git e le regole di stile.

Conseguenza concreta: le due sessioni AI ottimizzano verso lo stesso obiettivo e rispettano gli
stessi vincoli senza che ce lo diciamo. Se cambiamo una regola, la cambiamo lì e vale per entrambi
al pull successivo.

Questo, oltre a farci risparmiare tempo, è direttamente il criterio "coerenza tra file" (19%).

## 2. Proprietà dei file: i conflitti si evitano, non si risolvono

Niente pull request: in 5 ore sono troppo lente. Lavoriamo entrambi su `main`.
Funziona solo se **nessuno scrive nei file dell'altro**. La mappa sta in `CLAUDE.md`, in sintesi:

- Davide: `agents/**`, `presentation/**`, `docs/ux/**`, `docs/process-note.md`, `docs/status-davide.md`
- Chiara: `app/**`, `docs/validation/**`, `docs/status-chiara.md`
- Condivisi (si avvisa prima di toccarli): `README.md`, `CLAUDE.md`, `agents/schemas/**`

Se ti serve una modifica in un file non tuo, **non farla**: scrivila nel tuo file di status.
Un conflitto git alle 4:30 costa più di qualsiasi tempo risparmiato adesso.

Anche i file di status sono due file separati apposta: due persone che scrivono nello stesso
file di appunti si generano conflitti da sole.

## 3. Contract-first: si lavora in parallelo senza aspettarsi

Alle 0:50 congeliamo gli JSON Schema in `agents/schemas/`. Da quel momento chi fa l'app
programma contro il contratto e chi fa gli agenti produce quel contratto: nessuno dei due
resta fermo ad aspettare che l'altro finisca.

È l'unica dipendenza vera fra noi, e la togliamo di mezzo nella prima ora.
Cambiare uno schema dopo è l'unica cosa che può rompere il lavoro dell'altro senza preavviso:
si fa solo dicendolo.

## 4. Sincronizzazioni a orario fisso, non continue

Chiamata Teams **aperta per tutte e 5 le ore**, microfono libero: la domanda da dieci secondi
si fa a voce, non si scrive. Ma le sincronizzazioni vere sono quattro, e sono brevi:

| Quando | Durata | Cosa |
|---|---|---|
| 0:50 | fine | i contratti sono congelati, si parte |
| 1:45 | 5 min | si **mostra a schermo** cosa gira. Non si racconta: si mostra |
| 2:45 | 5 min | primo end-to-end, e si decide cosa si taglia |
| 3:50 | 5 min | feature freeze, si passa a documentazione e presentazione |

Fuori da questi momenti si scrive nel proprio file di status, non si interrompe l'altro.

## Disciplina git, in quattro righe

```bash
git pull --rebase        # sempre prima di ogni push
git add -A
git commit -m "aggiungi validator di fedelità"
git push                 # ogni 20 minuti, non alla fine
```

Se il rebase dà conflitto su un file che non è tuo: fermati e chiedi a voce.
Non risolverlo da solo, stai per cancellare il lavoro dell'altra persona.

## Setup iniziale, una volta sola

```bash
git clone <url-repo>
cd <repo>
cp .env.example .env     # ognuno la propria chiave, .env non si committa mai
git config user.name "Nome Cognome"
git config user.email "nome.cognome@accenture.com"
```
