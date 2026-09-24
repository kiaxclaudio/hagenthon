# Specifica UX — "A cosa ho diritto?"

Documento di consegna per l'implementazione in `app/`.
Sorgenti: `docs/inbox/chiara-idea.md` (flusso e scenari), `agents/ARCHITETTURA.md` (componenti e
stati), `agents/schemas/*.json` (contratti), `presentation/index.html` (linguaggio visivo).

Tre file compongono la consegna:

| File | Cosa contiene |
|---|---|
| `docs/ux/accenture-tokens.css` | i valori: colori, tipografia, spaziature, stati |
| `docs/ux/ux-spec.md` | questo documento: regole, schermate, componenti, criteri di verifica |
| `docs/ux/mockup.html` | il percorso completo navigabile, da cui copiare markup e stili |

---

## 1. Chi usa questa interfaccia, e cosa comporta

La persona a cui parliamo non e' un utente inesperto di software: e' un utente **inesperto di
burocrazia fiscale**. Ha spesso piu di sessant'anni, non ha mai aperto un cassetto fiscale, e la
sua esperienza precedente con i portali pubblici e' stata un fallimento. Arriva gia' convinta di
non capire. Il primo compito dell'interfaccia non e' informare: e' togliere la paura di sbagliare.

Quattro conseguenze progettuali, e sono vincolanti.

**Una decisione per schermata.** Non due domande affiancate, non un modulo. Chi legge lentamente
perde il filo se deve tenere aperte due domande contemporaneamente. La schermata contiene una
domanda, le sue risposte, e nient'altro di cliccabile oltre alla navigazione.

**Nessuna casella vuota.** Ogni risposta e' una scelta fra opzioni visibili. Un campo di testo
libero chiede all'utente di sapere gia' cosa scrivere: e' esattamente cio' che non sa. In tutto il
flusso di Fase B non esiste un solo `<input type="text">`.

**"Non so" e' sempre una risposta legittima.** Compare come opzione esplicita in ogni domanda dove
la tassonomia del `profiler` la prevede (`non_so`, `non_so_cosa_e`). Non e' un ripiego: e'
l'informazione che permette al sistema di spiegare invece di assumere.

**Il testo e' grande e le pagine sono corte.** Corpo a 20px, opzioni a 24px, altezza minima di un
bersaglio 64px. Meglio tre schermate brevi che una densa: scorrere e' piu facile che scegliere.

**Cosa NON assumiamo:** che l'utente sappia cos'e' una detrazione, un ISEE, una CU, un CAF, il
cassetto fiscale o la differenza fra detrazione e deduzione. Ogni volta che uno di questi termini
compare in interfaccia, porta con se' la sua spiegazione, e la spiegazione arriva dal catalogo
verificato, non dal modello (G-22, G-19).

---

## 2. Tensione con il brand, e come e' stata risolta

Il linguaggio Accenture e' scuro, stretto, elegante, pensato per una slide vista da lontano in una
sala. L'utente di questo prodotto e' agli antipodi. Le due cose si conciliano tenendo del brand
**cio' che e' identita** (viola, sfondo profondo, pillola eyebrow, `›` viola, titolo in gradiente,
etichette maiuscole spaziate) e sostituendo **cio' che e' densita da presentazione**.

Ogni scostamento e' dichiarato qui, con il motivo e il numero che lo giustifica.

| # | Regola del brand | Cosa facciamo | Perche' |
|---|---|---|---|
| D-1 | Testo secondario `rgba(255,255,255,0.64)`, terziario `0.25` | Secondario `#D0CCD3`, terziario `#9B999C`; il valore `0.25` **non si usa piu' per il testo** | `0.25` su `#050008` da' **2.05:1**: sotto il minimo di legge (4.5:1) e illeggibile per una vista presbite. Il `0.64` sarebbe conforme (8.31:1) ma resta trasparente: cambia significato appena lo sfondo cambia. I nostri valori sono opachi e misurati. |
| D-2 | `--purple #A100FF` come colore di accento anche sul testo | Il viola pieno **non e' mai testo**. Per il testo si usa `#BE82FF` (7.75:1). Il viola pieno resta su: riempimento del bottone primario, bordi, marcatori `›`, aloni | `#A100FF` su `#050008` da' **3.92:1**: sotto 4.5:1. Passa solo come "testo grande" o come componente non testuale. Il titolo in gradiente resta perche' e' sopra i 38px e non veicola informazione unica. |
| D-3 | Anello di focus viola | Anello di focus **bianco** 3px + alone viola decorativo | `#BE82FF` su un bottone `#A100FF` da' **1.98:1**: il focus sparirebbe proprio sul controllo principale. Il bianco tiene 5.30:1 sul viola e 20.79:1 sullo sfondo. L'alone viola conserva la firma di marca senza portare informazione. |
| D-4 | Tipografia fluida `clamp()` da 11px a 82px | Scala **fissa**, prosa mai sotto 18px, corpo 20px | Il `clamp()` fa cambiare dimensione al testo mentre si ridimensiona la finestra o si ruota il tablet. Chi legge lentamente perde il segno. E 11px come dimensione di etichetta e' fuori discussione. |
| D-5 | Griglie a 2 e 3 colonne, tabelle dense | **Colonna unica**, max 760px. Due colonne solo nella scheda finale su schermi ≥ 1000px, e solo per blocchi indipendenti | La griglia obbliga a scegliere dove guardare. Una colonna ha un solo ordine di lettura possibile, che e' anche l'ordine di tabulazione. |
| D-6 | `overflow:hidden` sul body, navigazione a slide | Scorrimento verticale normale, zoom del browser consentito fino al 200% senza perdita di contenuto | Bloccare lo scorrimento rompe l'ingrandimento, che e' la prima cosa che fa chi non vede bene. |
| D-7 | Sfondo unico `#050008` | Scala di superfici `#050008 → #140021 → #1C0A29 → #230B33` | Sul nero puro le card si distinguono solo per il bordo, e un bordo a 1.40:1 non si vede. Un fondale piu' chiaro dice "questo e' un oggetto" senza bisogno di una linea. Il bianco resta sopra 17:1 su tutte. |

Nessuno di questi scostamenti tocca i colori di marca: `#A100FF`, `#BE82FF`, `#0A0014`, `#050008`
e `Inter` restano identici a `presentation/index.html`. Cambia **dove** si usano, non quali sono.

---

## 3. Il flusso, schermata per schermata

Numerazione: `S0` … `S6`, piu' gli stati trasversali della sezione 6.
Mappatura sugli agenti di Fase B: `S1–S4` alimentano `profiler`, `S5` e' l'attesa di
`eligibility`, `S6` mostra `eligibility` + `navigator`.

### S0 — Apertura

| | |
|---|---|
| **Obiettivo** | dire in due frasi cosa succede e quanto dura, e togliere il timore di impegnarsi |
| **Contenuto** | logo `Accenture>`; eyebrow `ORIENTAMENTO AGLI AIUTI STATALI`; titolo in gradiente "A cosa ho diritto?"; sottotitolo: cosa fa, quante domande, che non serve nessun documento e nessuna registrazione; bottone primario **"Iniziamo"**; riga sotto: "Nessun dato personale viene salvato." |
| **Azione unica** | `Iniziamo` → S1 |
| **Banner** | disclaimer gia' presente, ancorato in basso (vedi 4.7) |
| **Nota** | la promessa "cinque domande" va mantenuta: il contatore che compare da S1 deve arrivare esattamente a quel numero (S1, S2, S3, S4a, S4b) |

### S1 — Situazione di vita (`situazione_vita`, scelta **multipla**)

| | |
|---|---|
| **Domanda** | "Cosa sta succedendo nella tua vita in questo momento?" |
| **Aiuto** | "Puoi scegliere piu' di una risposta." — sempre visibile, non un tooltip |
| **Opzioni** | `casa` Sto per comprare o ristrutturare casa · `figlio` Ho avuto o aspetto un figlio · `lavoro` Ho perso il lavoro o cerco lavoro · `spese_mediche` Ho spese mediche importanti · `auto` Voglio comprare un'auto · `under36` Ho meno di 36 anni · `non_so` Non so da dove partire, mostrami tutto |
| **Comportamento** | `non_so` e' **esclusiva**: selezionarla deseleziona le altre, e viceversa. Il cambio va annunciato in `aria-live` ("Le altre scelte sono state tolte.") |
| **Avanti** | bottone `Avanti` disabilitato finche' non c'e' almeno una scelta; disabilitato **visibile e con motivo** ("Scegli almeno una risposta"), mai nascosto |
| **Scrive** | `profilo.situazioni_vita[]` |

### S2 — Casa (`condizione_abitativa`, scelta **singola**)

Domanda: "Dove abiti in questo momento?"
Opzioni: `proprietario` In una casa di mia proprieta' · `affittuario` In affitto · `ospite_familiari`
A casa di familiari · `non_so` Preferisco non rispondere.
Selezione singola: la scelta **avanza automaticamente dopo 400 ms**, con eco della risposta
("Hai scelto: In affitto") e un `Indietro` sempre disponibile. L'avanzamento automatico non si
applica alle domande a scelta multipla.

### S3 — Reddito (`tipo_reddito`, scelta **singola**)

Domanda: "Da dove arrivano i tuoi soldi ogni mese?" — formulazione deliberatamente non tecnica.
Opzioni: `lavoro_dipendente` Uno stipendio da un datore di lavoro · `pensione` Una pensione ·
`partita_iva` Lavoro in proprio, ho la partita IVA · `nessun_reddito` In questo momento non ho
entrate · `non_so` Preferisco non rispondere.
Sotto: chip **"Cosa significa partita IVA?"**.
**Non si chiede mai un importo.** G-23 vieta di conservarlo e G-18 vieta di calcolarci sopra: un
campo che chiede un reddito e' un campo che promette un calcolo che non faremo.

### S4 — Quando e CAF (due micro-domande, una schermata per ciascuna)

**S4a `timing`** — "A che punto sei?": `da_iniziare` Devo ancora iniziare · `in_corso` Ho gia'
cominciato · `gia_concluso` Ho gia' finito e vorrei recuperare le spese passate.

**S4b `caf`** — "Hai gia' un CAF o un commercialista?": `si` Si' · `no` No · `non_so_cosa_e` Non
so cosa sia un CAF.
Se l'utente sceglie `non_so_cosa_e`, **non e' un errore e non blocca**: compare sotto l'opzione un
riquadro di spiegazione di due righe, l'opzione resta selezionata, e `Avanti` prosegue.
Il valore `non_so_cosa_e` entra in `profilo.termini_non_noti[]` e fa comparire la voce "CAF" nel
glossario finale.

> Spiegazione inline canonica (testo da usare tale e quale):
> **CAF** sta per Centro di Assistenza Fiscale. E' un ufficio, spesso gratuito o a costo basso, dove
> una persona compila per te le pratiche con lo Stato. Ce n'e' quasi sempre uno vicino a casa.

### S5 — Elaborazione

Sostituisce lo spinner generico. Mostra **cosa sta succedendo**, in tre righe che si accendono in
sequenza mentre gli agenti lavorano, con la barra di avanzamento indeterminata in `--loading-fill`:

1. Sto mettendo in ordine le tue risposte. *(`profiler`)*
2. Sto cercando le misure che riguardano la tua situazione. *(`eligibility`)*
3. Sto preparando i passi da fare. *(`navigator`)*

Regole: `role="status"` + `aria-live="polite"`; nessun tempo promesso; oltre **20 secondi** compare
"Ci sto mettendo piu' del previsto" con un `Annulla`; al terzo timeout (`status: degraded`,
`ARCHITETTURA.md` — limiti di iterazione) si passa allo stato 6.5.

### S6 — La scheda

L'unica schermata con piu' di un oggetto. Ordine fisso, dall'alto:

1. **Intestazione** — "Ecco cosa risulta per la tua situazione" + riepilogo del profilo in chiaro,
   con un link `Modifica` che riporta a S1 ("Casa da ristrutturare · Proprietario · Lavoro
   dipendente · Devo ancora iniziare").
2. **Conteggio neutro** — "Abbiamo trovato 3 misure che riguardano la tua situazione." Mai
   "ottimo!", mai "hai diritto a": **riguardano**, non spettano. La differenza fra le due parole
   e' la differenza fra orientamento e consulenza.
3. **Card misura**, una per `payload.misure_pertinenti[]`. Ordine: quello restituito
   dall'agente, che ordina per asse del profilo e poi per nome (G-21). **Mai per importo.**
   Un'etichetta sopra l'elenco dichiara il criterio: "In ordine di situazione, non di
   convenienza." — l'ordine e' un'informazione, e va detto quale.
4. **Cosa non ti riguarda, e perche'** — accordion chiuso, alimentato da `misure_escluse[]`.
   Serve a chiudere il dubbio "e questo bonus di cui mi hanno parlato?".
5. **Glossario contestuale** — solo i termini effettivamente comparsi
   (`navigator.payload.glossario[]` + `termini_non_noti[]`).
6. **Blocco CAF** — "Il prossimo passo lo fai con una persona", con il perche'.
7. **Ricomincia con un profilo diverso** — bottone secondario, sempre presente.
8. **Disclaimer** — ancorato, non in fondo alla pagina (vedi 4.7).

---

## 4. Anatomia dei componenti

Notazione: `stato` = classe CSS, `aria-*` = attributo obbligatorio.

### 4.1 Opzione di risposta

Il componente piu' usato del prodotto. E' un `<button>` reale, non un `div` cliccabile.

```
+--------------------------------------------------------------+
|  [ ]   Sto per comprare o ristrutturare casa                 |   <- 24px, bianco
|        Ristrutturazione, acquisto, lavori in condominio      |   <- 18px, secondario (opz.)
+--------------------------------------------------------------+
```

| Proprieta' | Valore |
|---|---|
| Altezza minima | `--target-comfort` (64px); in pratica 72–88px con la riga di esempio |
| Larghezza | 100% della colonna |
| Distanza fra due opzioni | `--gap-options` (16px), mai sotto: due bersagli attaccati si sbagliano |
| Testo | `--fs-400` (24px), `--text-primary`, allineato a sinistra, mai troncato — se e' lungo va a capo |
| Riposo | fondo `--surface-card`, bordo `2px --line-control` (4.58:1) |
| Hover | fondo `--surface-hover`, bordo `--acc-purple-light`, `translateY(-1px)` |
| Focus | anello bianco 3px, offset 3px, alone viola (mai rimosso) |
| Selezionato | fondo `--surface-selected`, bordo `3px --line-selected`, **+ spunta `✓` a sinistra** e testo in grassetto |
| Semantica | scelta singola: `role="radio"` in un `role="radiogroup"` con `aria-checked`; multipla: `<button aria-pressed>` o checkbox nativa |

**La spunta non e' decorazione.** Il fondale e il bordo cambiano colore quando si seleziona, ma per
un daltonico e in scala di grigi restano due grigi vicini. Il segno `✓` piu' il grassetto piu'
`aria-checked` sono i tre canali non cromatici che portano la stessa informazione (WCAG 1.4.1).

### 4.2 Chip "Cosa significa?"

Sta **sotto** il testo che spiega, mai dentro. E' un `<button aria-expanded>` che apre un riquadro
in linea: niente tooltip al passaggio del mouse, che su tablet non esiste e con la tastiera e'
inaccessibile.

- Aspetto a riposo: pillola, bordo `1px --line-control`, fondo `--surface-quiet`,
  testo `--fs-200` `--text-accent`, prefisso `›`, altezza 44px.
- Aperto: il riquadro compare sotto, fondo `--surface-card`, bordo sinistro `3px --acc-purple`,
  testo `--fs-200` `--lh-loose`.
- **Massimo due righe** — circa 180 caratteri. Se la spiegazione non ci sta in due righe, il
  termine va scomposto in due voci di glossario.
- La chiusura riporta il focus sul chip.
- Il contenuto viene da `catalogo.json → voce_glossario.spiegazione_semplice`. Mai generato al volo:
  G-22 vuole una voce verificata, non una parafrasi.

### 4.3 Card misura

Un ordine fisso, sempre lo stesso, perche' alla terza card l'utente sappia gia' dove guardare.

```
┌────────────────────────────────────────────────────────────┐
│ DETRAZIONE                                    ← tipo_misura │
│ Bonus Ristrutturazione                        ← nome        │
│ Ti torna una parte di quello che spendi...    ← titolo_semplice
│                                                             │
│  50%              96.000 €           10 anni                │
│  di quanto spendi tetto massimo      in quante rate         │
│                                                             │
│ COSA DEVI AVERE                               ← requisiti   │
│  › ...                                                      │
│ ENTRO QUANDO                                  ← scadenza    │
│ IL PRIMO PASSO                                ← navigator   │
│ [ Cosa significa "bonifico parlante"? ]                     │
└────────────────────────────────────────────────────────────┘
```

| Blocco | Sorgente (`agents/schemas/`) | Regole |
|---|---|---|
| Etichetta tipo | `misura.tipo` (`detrazione`, `credito_imposta`, `assegno`, `esenzione`, `contributo`) | maiuscoletto `--fs-100`, `--text-accent`, `--ls-wide` |
| Nome | `misura.nome` | `--fs-500`, bianco, **non in gradiente**: e' un dato, deve avere contrasto pieno |
| In parole semplici | `spiegazione.titolo_semplice` + `cosa_e` | `--fs-300`, `--text-secondary` |
| Cifre | `beneficio.percentuale`, `beneficio.importo_euro`, `beneficio.tetto_massimo_euro`, `recupero.rate_annuali` | riga di 2–3 riquadri; numero `--fs-500` bianco, etichetta sotto `--fs-200` `--text-tertiary`. **Il numero si scrive come sta nella fonte** (G-03) e ha sempre sotto la sua unita' a parole: "96.000 €" da solo non dice nulla, "96.000 € tetto massimo di spesa" si' |
| Cosa devi avere | `requisiti[].descrizione_fonte` + `requisiti_da_verificare[]` | elenco `›`; i requisiti che l'agente non ha potuto verificare portano l'etichetta testuale **"da verificare con un CAF"**, non un colore diverso |
| Entro quando | `scadenza` | se `tipo_scadenza = non_determinata` si scrive "Non risulta una scadenza fissa. Verificala sul sito dell'ente." — **mai lasciare il campo vuoto** |
| Attenzione | `spiegazione.attenzione[]` | riquadro con `--text-warning` **e** la parola "Attenzione" scritta |
| Il primo passo | `navigator.payload.primo_passo_concreto` | una frase sola, all'imperativo gentile |
| Glossario in linea | `navigator.payload.glossario[]` | chip 4.2, uno per termine comparso nella card |
| Fonte | `source_refs[]` | riga in fondo, `--fs-100` `--text-tertiary`: "Fonte: Agenzia delle Entrate, guida ristrutturazioni, consultata il 12/09/2026" — la data viene da G-24 |

**Cosa non compare mai in una card:** un totale, una somma di piu' misure, una stima di quanto
spetterebbe a questa persona, una percentuale di probabilita', una barra di "convenienza".
Sono tutti calcoli personalizzati, vietati da G-18.

### 4.4 Glossario contestuale

Sezione in fondo alla scheda, `role="list"`, una voce per termine effettivamente comparso.
Ogni voce: termine in grassetto bianco `--fs-300`, spiegazione `--fs-200` `--text-secondary`
`--lh-loose`, e — se `tipo_documento_collegato` e' valorizzato — la riga "Dove si trova: ...".
I termini gia' aperti in linea durante il percorso restano qui, cosi' l'utente li ritrova senza
ripercorrere le schermate.

### 4.5 Blocco "Cosa non ti riguarda"

`<details>` chiuso, riassunto: "Perche' non vedo altri bonus di cui ho sentito parlare?".
Dentro, una riga per `misure_escluse[]`: nome + motivo tradotto in italiano corrente.

| `motivo_esclusione` | Testo mostrato |
|---|---|
| `requisito_non_soddisfatto` | Serve una condizione che, da quello che hai risposto, non risulta. |
| `situazione_non_pertinente` | Riguarda una situazione diversa dalla tua. |
| `timing_non_compatibile` | Vale in un momento diverso da quello in cui ti trovi. |
| `scadenza_superata` | Il termine per chiederlo e' gia' passato. |

Chiude con: "Se pensi che una di queste ti riguardi comunque, e' esattamente il tipo di domanda da
fare a un CAF."

### 4.6 Blocco CAF ed escalation

Due usi, stessa forma, tono diverso.

**Chiusura normale** (in fondo a ogni scheda): "Il prossimo passo lo fai con una persona." + il
perche' + "Trova un CAF vicino a te" (link esterno, con `Si apre in una nuova pagina`).

**Escalation** (`escalation: true` oppure `status: hitl_required` oppure `confidence < 0.6`):
diventa il contenuto **principale** della schermata, non una nota a margine.
Il motivo si traduce cosi', senza mai scaricare la colpa sull'utente:

| `motivo_escalation` | Testo mostrato |
|---|---|
| `confidence_bassa` | La tua situazione ha dettagli che non possiamo verificare da qui. |
| `caso_non_coperto_dal_catalogo` | Non abbiamo informazioni verificate su questo caso. Preferiamo dirtelo invece di tirare a indovinare. |
| `profilo_incompleto` | Mancano alcune risposte. Puoi completarle, oppure andare direttamente da un CAF. |
| `requisiti_non_verificabili` | Per capire se ti spetta serve guardare documenti che non abbiamo. |
| `richiesta_di_consulenza` | Questa e' una decisione, e le decisioni le prende una persona con te. |

Il blocco di escalation porta sempre due azioni, mai una sola: `Trova un CAF vicino a te` e
`Torna indietro e cambia una risposta`. Un vicolo cieco con una sola uscita e' una schermata di
errore travestita.

### 4.7 Banner disclaimer permanente

Ancorato in fondo alla finestra (`position: sticky; bottom: 0`), presente su **tutte** le
schermate, fondo `--surface-banner`, bordo superiore `1px --line-soft`, testo `--fs-200`
`--text-secondary` — non `--text-tertiary`: e' un avviso, non una nota legale da nascondere.

> Questo strumento spiega quali misure esistono. Non da' consigli e non fa calcoli sul tuo caso.
> Verifica le scadenze su agenziaentrate.gov.it e parla con un CAF o un commercialista prima di
> decidere.

Non si chiude, non si comprime, non si anima. In stampa resta visibile. Sotto i 600px di altezza
di finestra torna in flusso normale in fondo alla pagina, per non mangiare lo schermo.
Il testo e' un campo dell'output (`payload.disclaimer`, G-20): l'interfaccia lo mostra, non lo
scrive.

### 4.8 Intestazione e indicatore di passo

In alto, fisso: logo `Accenture>` a sinistra; a destra `Domanda 2 di 5` in testo
(`--fs-200`, `--text-tertiary`) **piu'** una barra sottile a 5 segmenti. Il testo e' la fonte di
verita' — la barra da sola sarebbe informazione trasmessa dal solo colore.
Il cambio di passo si annuncia in `aria-live="polite"`.
`Indietro` sempre presente da S2 in poi, come testo con freccia, mai come sola icona.

---

## 5. Accessibilita' verificabile

Criteri controllabili guardando l'interfaccia, non intenzioni. Riferimento WCAG 2.2 livello AA,
con AAA dove il costo era nullo.

### 5.1 Contrasto — rapporti calcolati sui colori reali

Calcolati con la formula WCAG 2.x (luminanza relativa sRGB). Script di verifica in fondo alla
sezione: chi cambia un colore ricalcola e aggiorna questa tabella.

| Coppia | Primo piano | Sfondo | Rapporto | AA 4.5:1 | AAA 7:1 |
|---|---|---|---|---:|:---:|:---:|
| Testo principale su pagina | `#FFFFFF` | `#050008` | **20.79:1** | si' | si' |
| Testo principale su card | `#FFFFFF` | `#140021` | **19.97:1** | si' | si' |
| Testo principale su opzione scelta | `#FFFFFF` | `#230B33` | **17.99:1** | si' | si' |
| Testo secondario su card | `#D0CCD3` | `#140021` | **12.61:1** | si' | si' |
| Testo terziario su pagina | `#9B999C` | `#050008` | **7.36:1** | si' | si' |
| Etichetta di sezione viola | `#BE82FF` | `#050008` | **7.75:1** | si' | si' |
| Etichetta viola su card | `#BE82FF` | `#140021` | **7.44:1** | si' | si' |
| Testo del bottone primario | `#FFFFFF` | `#A100FF` | **5.30:1** | si' | no |
| Testo su fondo viola chiaro | `#0A0014` | `#BE82FF` | **7.65:1** | si' | si' |
| Testo disabilitato | `#807587` | `#140021` | **4.58:1** | si' | no |
| Errore | `#FF9F93` | `#140021` | **10.11:1** | si' | si' |
| Attenzione | `#FFC978` | `#140021` | **13.20:1** | si' | si' |
| Conferma | `#6FE3B0` | `#140021` | **12.64:1** | si' | si' |
| Anello di focus sullo sfondo | `#FFFFFF` | `#050008` | **20.79:1** | si' | si' |
| Anello di focus sul bottone viola | `#FFFFFF` | `#A100FF` | **5.30:1** | si' | si' |

Bordi e componenti non testuali, soglia 3:1 (WCAG 1.4.11):

| Elemento | Colori | Rapporto | ≥ 3:1 |
|---|---|---:|:---:|
| Bordo di un controllo a riposo | `#807587` su `#140021` | **4.58:1** | si' |
| Bordo dell'opzione selezionata | `#BE82FF` su `#140021` | **7.44:1** | si' |
| Bordo di accento viola | `#A100FF` su `#140021` | **3.76:1** | si' |
| Cornice di pannello non interattivo | `#64576C` su `#140021` | 2.97:1 | decorativo, mai unico segnale |
| Separatore estetico | `#2A262D` su `#050008` | 1.40:1 | decorativo, mai unico segnale |

Casi respinti, e sono il cuore delle deroghe della sezione 2:

| Combinazione del brand | Rapporto | Verdetto |
|---|---:|---|
| `rgba(255,255,255,0.25)` su `#050008` | **2.05:1** | respinta per qualsiasi testo (D-1) |
| `#A100FF` su `#050008` come testo | **3.92:1** | respinta sotto i 24px (D-2) |
| `#BE82FF` come anello di focus su bottone `#A100FF` | **1.98:1** | respinta come focus (D-3) |
| `#0A0014` su bottone `#A100FF` | **3.87:1** | respinta come testo del bottone |

Script usato (riproducibile, nessuna dipendenza):

```python
def srgb(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def lum(h):
    h = h.lstrip('#')
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return 0.2126*srgb(r) + 0.7152*srgb(g) + 0.0722*srgb(b)

def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

print(round(ratio('#FFFFFF', '#050008'), 2))   # 20.79
print(round(ratio('#A100FF', '#050008'), 2))   #  3.92  -> respinto come testo
print(round(ratio('#BE82FF', '#A100FF'), 2))   #  1.98  -> respinto come focus
```

### 5.2 Bersagli

- Minimo **44 × 44 px** su ogni elemento cliccabile, nessuna eccezione (WCAG 2.5.5).
- Opzioni di risposta: **64 px** di altezza minima, larghe quanto la colonna.
- Distanza minima fra due bersagli: **16 px**.
- L'area cliccabile e' tutta la card dell'opzione, non solo l'etichetta.
- I chip "Cosa significa?" hanno 44 px di altezza anche se il testo e' corto (padding, non font).

### 5.3 Tastiera e focus

- **Nessuna trappola.** Da ogni schermata si esce con `Tab`.
- Ordine di tabulazione = ordine visivo = ordine del DOM. Nessun `tabindex` positivo.
- Focus sempre visibile: anello bianco 3px, offset 3px. `outline: none` e' vietato senza
  sostituto verificato.
- Al cambio di schermata il focus va sul titolo della nuova domanda (`<h1 tabindex="-1">`), non
  sul corpo: chi usa lo screen reader deve sentire la domanda, non il logo.
- Gruppi a scelta singola: frecce per spostarsi dentro il gruppo, `Tab` per uscirne
  (schema radiogroup nativo).
- `Invio` e `Spazio` attivano ogni controllo. `Esc` chiude una spiegazione aperta e riporta il
  focus al chip che l'ha aperta.
- Link "Salta al contenuto" come primo elemento focalizzabile della pagina.

### 5.4 Semantica e testo alternativo

- Un `<h1>` per schermata: il testo della domanda.
- Il testo del bottone dice cosa succede: `Avanti`, `Vedi le misure`, `Ricomincia`. Mai `OK`,
  mai `Continua` da solo, mai `>`.
- Nessuna icona sola: ogni icona ha l'etichetta testuale accanto. Le icone decorative
  (`›`, aloni, barre) sono `aria-hidden="true"`.
- I marcatori `›` degli elenchi sono generati in `::before` e non finiscono nella lettura vocale.
- Gli aggiornamenti asincroni (passo cambiato, opzione esclusiva deselezionata, risultati pronti)
  vanno in `aria-live="polite"`; solo l'errore bloccante in `aria-live="assertive"`.
- `lang="it"` sul documento. Se una stringa contiene un termine straniero, `lang` locale.
- Zoom del browser al **200%** senza scorrimento orizzontale e senza contenuto tagliato
  (conseguenza della colonna unica a 760px).

### 5.5 Nessuna informazione dal solo colore

Regola verificabile: **una schermata in scala di grigi deve restare usabile.**

| Informazione | Canale cromatico | Canale non cromatico obbligatorio |
|---|---|---|
| Opzione selezionata | fondo e bordo | spunta `✓` + grassetto + `aria-checked` |
| Errore | testo `#FF9F93` | segno `!` + la parola "Errore" + `role="alert"` |
| Attenzione | testo `#FFC978` | la parola "Attenzione" |
| Requisito da verificare | — | etichetta testuale "da verificare con un CAF" |
| Passo corrente | barra viola | testo "Domanda 2 di 5" |
| Bottone disabilitato | colori spenti | `aria-disabled` + motivo scritto sotto |
| Escalation | nessuno | il blocco e' il contenuto principale della schermata |

---

## 6. Gli stati che l'interfaccia deve saper mostrare

Sono sei, e sono tutti disegnati. Uno stato non disegnato e' uno stato che verra' implementato
come `alert()` alle quattro del mattino.

### 6.1 Caricamento — `S5`
Tre righe che si accendono in sequenza, barra indeterminata, `role="status"`.
Oltre 20 secondi: "Ci sto mettendo piu' del previsto" + `Annulla`.
**Mai** una percentuale finta.

### 6.2 Nessuna misura pertinente — `misure_pertinenti: []`, `escalation: false`
Non e' un errore e non si scrive in rosso. Titolo: "Da quello che hai risposto non risultano
misure che riguardano la tua situazione." Poi, in quest'ordine:
il riepilogo delle risposte con `Modifica`; la frase "Questo non vuol dire che non ti spetti
niente: vuol dire che serve guardare il tuo caso da vicino."; il blocco CAF;
`Ricomincia con un profilo diverso`.

### 6.3 Escalation a CAF — `escalation: true` / `hitl_required` / `confidence < 0.6`
Il blocco 4.6 diventa la schermata. Nessuna misura viene mostrata accanto: mescolare un elenco di
misure a un "non lo sappiamo" fa leggere solo l'elenco.
Il motivo si scrive sempre. "Non posso aiutarti" senza perche' e' la frase che l'utente ha gia'
sentito allo sportello.

### 6.4 Errore tecnico
Pannello `--surface-error`, bordo `--error-border`, segno `!`, `role="alert"`, focus spostato sul
titolo del pannello. Testo: "Qualcosa non ha funzionato dalla nostra parte. Non e' colpa di
quello che hai scritto." Due azioni: `Riprova` (che non perde le risposte gia' date) e
`Vai a un CAF`. Nessun codice di errore, nessuno stack: il riferimento tecnico finisce nel log di
sessione (`agents/state/run-<id>.json`), non davanti alla persona.

### 6.5 Output `degraded` — `status: "degraded"`
Il caso piu' delicato: **c'e' un risultato, ma e' meno affidabile.**
La scheda si mostra, preceduta da una fascia dichiarata in cima, `--text-warning`, con la parola
"Attenzione" scritta:

> **Attenzione** — Alcune informazioni potrebbero non essere complete: non siamo riusciti a
> verificare tutto. Prima di muoverti, falle controllare da un CAF.

In piu': le card prive di `source_refs` o con `dati_mancanti` non mostrano riquadri numerici vuoti
ma la riga "Questo dato non risulta dalla fonte che abbiamo consultato" (G-01: `missing`, non
stimato); il blocco CAF sale **sopra** l'elenco delle misure; il bottone primario diventa
`Trova un CAF`, non `Stampa la scheda`.

### 6.6 Sessione ripresa o profilo gia' presente
Se `agents/state/profilo.json` esiste, S0 mostra una riga in piu': "L'ultima volta avevi risposto:
… — `Riprendi da li'` / `Ricomincia da capo`". Due azioni, entrambe esplicite: non si riprende
d'ufficio.

---

## 7. Lessico

Tre regole, e valgono su ogni stringa.

**Si sostituisce il termine e si spiega quello vero.** Non si finge che la parola tecnica non
esista — l'utente la incontrera' allo sportello.

| Non si scrive | Si scrive |
|---|---|
| Si decade dal beneficio | Perdi il diritto al rimborso se… |
| Detrazione IRPEF | Uno sconto sulle tasse che paghi (si chiama *detrazione*) |
| Requisiti soggettivi | Cosa devi avere |
| Termine perentorio | Entro questa data, senza proroghe |
| Presentare istanza | Fare domanda |
| Soggetto beneficiario | Chi puo' chiederlo |
| Adempimenti | Cosa devi fare |
| Congruita' della spesa | Se la spesa e' considerata normale per quel lavoro |

**Mai la seconda persona imperativa sulle decisioni.** "Fai domanda entro il 31" descrive una
scadenza: e' ammesso. "Ti conviene fare domanda" e' un consiglio: e' vietato (G-04).

**Le cifre non si arrotondano e non si riscrivono** (G-03). `96.000 €` resta `96.000 €`, non
diventa "quasi centomila".

---

## 8. Cosa non fare

- **Niente densita' da dashboard.** Nessun contatore in alto, nessun riquadro di statistiche,
  nessuna barra di completamento del profilo, nessun grafico. La scheda non e' un cruscotto.
- **Niente gergo non spiegato.** Ogni termine tecnico che compare ha la sua voce di glossario nel
  catalogo, altrimenti non compare (G-22).
- **Mai piu' di una domanda per schermata.** Nemmeno due campi "brevi" affiancati.
- **Nessun consiglio.** Nessuna stringa dell'interfaccia contiene "ti conviene", "dovresti",
  "la scelta migliore", "risparmi di piu' con". Vale anche per le etichette dei bottoni.
- **Nessun calcolo personalizzato** (G-18): niente totale, niente somma di misure, niente stima di
  quanto spetta. Si citano le cifre del catalogo come stanno.
- **Nessuna graduatoria** (G-21): l'ordine e' quello dell'agente, e il criterio si dichiara.
- **Nessuna misura fuori catalogo** (G-19): se non e' in `catalogo.json` non esiste, anche se il
  modello la ricorda.
- **Niente tooltip al passaggio del mouse** come unico modo per leggere una spiegazione.
- **Niente testo sotto 18px** in prosa, niente grigio sotto 4.5:1, niente `outline: none`.
- **Niente animazioni di ingresso** sul contenuto: il testo che arriva scorrendo costa lettura.
- **Nessun campo di testo libero** in Fase B, e nessuna richiesta di importi, codice fiscale,
  nome o indirizzo (G-17, G-23).

---

## 9. Consegna: cosa passa in `app/`

| Da `docs/ux/` | Dove | Come |
|---|---|---|
| `accenture-tokens.css` | `app/styles/accenture-tokens.css` | copia **identica**, nessuna modifica; importato per primo, prima di ogni altro foglio di stile |
| `mockup.html` — blocco `<style>` sotto il marcatore `COMPONENTI` | `app/styles/components.css` | e' gia' scritto solo con `var(--…)`: staccandolo dai token continua a funzionare |
| `mockup.html` — markup delle schermate | i template dell'app | classi e attributi `aria-*` vanno copiati come stanno: sono la parte verificata |
| `mockup.html` — oggetto `SCENARI` in fondo | dati finti per la demo | vanno sostituiti dall'output reale degli agenti; la forma rispecchia `eligibility.output.json` + `navigator.output.json` |
| Tabella 5.1 | `docs/ux/ux-spec.md` | va riaggiornata se si cambia un colore, con lo script della 5.1 |

Regola di manutenzione: un colore nuovo entra nel prodotto **solo** dopo essere passato dallo
script della sezione 5.1 ed essere stato aggiunto come token in `accenture-tokens.css`.
Nessun esadecimale scritto a mano dentro un componente.

---

*Specifica UX · "A cosa ho diritto?" · Hackathon Agentic Coding, Accenture Application Engineering*
