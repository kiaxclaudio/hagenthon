# Skill: istruzioni lunghe caricate on-demand

Una skill è un blocco di istruzioni specialistiche che **non** sta nel file dell'agente e viene
letto solo quando quell'agente arriva al punto in cui serve (G-13). Il file dell'agente resta un
contratto leggibile in trenta secondi; la procedura dettagliata sta qui e pesa solo quando viene
usata.

Tre skill, non una di più. Una quarta skill che ripetesse una regola già scritta altrove
toglierebbe punti invece di darne: il criterio sulla qualità delle istruzioni penalizza
esplicitamente le sovrapposizioni tra file.

## Mappa dei caricamenti

| Skill | Caricata da | Condizione di caricamento | Peso | Perché non sta nel file dell'agente |
|---|---|---|---|---|
| `plain-language.md` | `subagents/explainer.md` | passo A2, a ogni riscrittura di una misura e a ogni correzione dopo un rifiuto | 207 righe, 1.962 parole | Sono 14 regole più una checklist di 9 controlli: quasi il doppio del file dell'`explainer` (115 righe). Inline, verrebbero caricate anche quando l'`explainer` non gira, cioè in tutta la Fase B |
| `fidelity-diff-taxonomy.md` | `subagents/fidelity-validator.md` | passo A3, a ogni verifica, compreso il secondo giro | 349 righe, 3.008 parole | La tassonomia serve a **classificare**, e classificare è un lavoro che fa solo il validator. Tenerla fuori dall'`explainer` è anche una scelta di separazione: chi scrive non deve conoscere in anticipo la griglia con cui verrà giudicato, o la ottimizza invece di rispettarla |
| `hitl-escalation.md` | `orchestrator.md` | quando scatta uno dei gate HITL dichiarati in `orchestrator.md`, in Fase A come in Fase B | 226 righe, 2.434 parole | È il percorso eccezionale: nel caso normale non serve mai. Caricarla sempre significherebbe pagare in ogni invocazione un contenuto che riguarda una frazione dei casi |

Totale: **782 righe, 7.404 parole** (conteggi con `wc -lw`; stima di circa 11.000 token).
I tre file che le caricano ne contano insieme 361 e 2.629. Inline, le istruzioni peserebbero
**più del triplo**, in ogni invocazione. Con il caricamento on-demand nessuna invocazione ne
carica più di una, e le invocazioni di Fase B non ne caricano nessuna finché non scatta un gate.

## Agenti che non caricano alcuna skill

Dichiarato apposta: un agente senza skill è una scelta, non una dimenticanza.

| Agente | Perché no |
|---|---|
| `profiler` | Normalizzazione su tassonomia chiusa, gira una volta per sessione. La tassonomia sta nel suo file e nel suo schema di output, non in una skill |
| `source-analyzer` | Produce struttura, non testo per la persona: le regole di linguaggio non lo riguardano. Le regole di estrazione sono i suoi passi, e sono otto righe |
| `eligibility` | Non scrive contenuto nuovo: cita il catalogo già verificato. Le sue regole di dominio stanno tutte nei guardrail G-18..G-21 |
| `navigator` | È il componente più frequente della Fase B e assembla materiale già verificato. Aggiungergli contesto è esattamente ciò che la separazione in due fasi serve a evitare |

## Convenzione: l'intestazione dichiara il caricamento

Ogni skill si apre con una tabella di quattro righe, ed è ciò che rende il caricamento on-demand
verificabile leggendo il file e non solo dichiarato a parole:

1. **Caricata da** — l'agente o gli agenti, con il percorso del file. Se sono più di uno, si dice
   quale parte carica ciascuno.
2. **Quando** — il punto esatto del workflow (`agents/workflows/main-pipeline.md`) o la condizione
   che la attiva.
3. **Cosa restituisce a chi la usa** — che cosa il chiamante ha in mano dopo averla letta:
   regole citabili, una procedura, un artefatto. Mai "linee guida generali".
4. **Perché non è caricata da altri** — la giustificazione del confine. È la riga che dimostra
   che il perimetro è stato scelto e non subìto.

Il caricamento è un'operazione reale, non una figura retorica: i due sub-agenti che caricano una
skill (`explainer`, `fidelity-validator`) hanno `Read` fra i `tools` dichiarati nel frontmatter,
e aprono il file solo nel momento indicato nella riga "Quando". Chi non carica nessuna skill non
legge nessuno di questi file.

## Regola di non sovrapposizione

Una skill **approfondisce**, non ripete. Se una regola sta già nel file dell'agente, in
`guardrails.md` o in `CLAUDE.md`, la skill non la riscrive: la cita e la rende operativa.

Ogni skill ha in testa una sezione "Che cosa è già deciso altrove", con la mappa
vincolo → dove è stabilito → che cosa aggiunge la skill. Se una riga di quella mappa ha la colonna
di destra vuota, quel contenuto va cancellato dalla skill.

Divisione delle responsabilità fra le tre, in una riga ciascuna:

- `plain-language.md` dice **come si scrive** una misura in lingua semplice (codici `PL-xx`);
- `fidelity-diff-taxonomy.md` dice **come si giudica** una misura riscritta (codici `D-xx`);
- `hitl-escalation.md` dice **che cosa si fa quando non si può né scrivere né approvare**
  (codici `HE-xx`).

I tre insiemi di codici sono disgiunti e si citano a vicenda per riferimento: la corrispondenza
`D-xx` → `PL-xx` sta solo nella tassonomia, la procedura di correzione mirata sta solo in
`plain-language.md`, i contenuti del dossier stanno solo in `hitl-escalation.md`.

## Perché la mappa dei caricamenti sta qui e non nei file degli agenti

Un solo punto di verità sul **chi carica che cosa**. Il file dell'agente dichiara il **vincolo**
("numeri e date invariati") e il passo in cui apre la skill; la skill rende il vincolo
**eseguibile**; questa tabella dice **quanto pesa e perché non sta altrove**. Tre ruoli, tre
posti, nessuna ripetizione.

## Aggiungere una skill

Prima di creare un file nuovo, tre domande in ordine. Basta un "sì" alla prima o alla seconda per
non crearlo:

1. Il contenuto esiste già in un altro file di `agents/`? Allora si cita, non si duplica.
2. È corto abbastanza da stare nel file dell'agente senza appesantirlo (indicativamente sotto le
   30 righe)? Allora ci sta bene lì.
3. Serve a più di un agente? Allora va scritto una volta e si dichiarano **entrambi** i
   caricamenti nell'intestazione, indicando quale parte legge ciascuno.

Poi: intestazione a quattro righe, sezione "Che cosa è già deciso altrove", regole numerate con
un prefisso nuovo e non ambiguo, e una riga in questa tabella.
