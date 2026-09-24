# `agents/state/` — lo stato esternalizzato della Fase A

Questa cartella contiene il risultato di una **esecuzione reale della Fase A** del sistema
"A cosa ho diritto?": fonti ufficiali scaricate, misure destrutturate, spiegazioni in lingua
semplice, verdetti di fedeltà e il catalogo che la Fase B leggerà. Prima di questa esecuzione la
cartella era vuota: il repository descriveva un sistema agentico senza mostrarne un output.

## Dichiarazione di modalità

**La Fase A è stata eseguita manualmente il 24 settembre 2026, seguendo alla lettera le istruzioni
degli agenti, e non tramite chiamate API ai sottoagenti.** I tre ruoli — `source-analyzer`,
`explainer`, `fidelity-validator` — sono stati interpretati uno dopo l'altro applicando
`agents/subagents/*.md`, `agents/skills/plain-language.md` (PL-01..PL-14, checklist C1..C9) e
`agents/skills/fidelity-diff-taxonomy.md` (procedura V-1..V-4, tassonomia D-01..D-10 e D-99).

Cosa è vero e cosa non lo è, detto senza ammorbidirlo:

- **vere** le fonti, i numeri, le citazioni, le divergenze trovate, i verdetti e la conformità
  agli schemi;
- **non reale** il meccanismo di invocazione: nessun processo ha chiamato un sottoagente, e la
  separazione dei permessi fra chi scrive e chi approva (`fidelity-validator` con solo `Read`)
  è stata rispettata come disciplina, non imposta dal runtime.

Questa cartella dimostra che il ciclo produce artefatti conformi e utili. Non dimostra che
l'orchestrazione automatica esista già.

## Che cosa c'è

| File o cartella | Che cos'è | Contratto |
|---|---|---|
| `fonti/*.txt` (8) | Estratti delle pagine e dei PDF ufficiali, con URL e data di consultazione in testa | — |
| `misure-grezze/*.json` (6) | Output di `source-analyzer`, uno per fonte analizzata | `schemas/source-analyzer.output.json` |
| `spiegazioni/*.json` (5) | Output di `explainer`: la versione in lingua semplice approvata | `schemas/explainer.output.json` |
| `verifiche/*.json` (8) | Output di `fidelity-validator`, un file per giro di verifica | `schemas/fidelity-validator.output.json` |
| `catalogo.json` | Il catalogo pubblicato: 5 misure verificate, 1 esclusa con motivo | `schemas/catalogo.json` |
| `verifica-fase-a.json` | La traccia del ciclo: giri, divergenze con il loro codice, verdetti, note | — |
| `valida_stato.py` | Rivalida tutti gli artefatti contro i loro schemi | — |

`profilo.json` e i file `run-*.json` non appartengono a questa esecuzione: sono stato di **Fase B**
(profilo di sessione e sessioni di collaudo), prodotti altrove e lasciati dove sono.

## Come è stato prodotto

```
fonti ufficiali -> source-analyzer -> explainer -> fidelity-validator -> catalogo.json
                                          ^                |
                                          +--- respinto ---+   max 2 giri, poi HITL
```

1. **Fonti.** Pagine dell'Agenzia delle Entrate lette con WebFetch; documenti INPS presi dai PDF
   ufficiali (circolare e comunicato stampa) ed estratti con `pdfminer`, perché le schede HTML di
   `inps.it` restituiscono solo la struttura di navigazione. Ogni estratto porta in testa URL,
   ente, data di consultazione e il modo in cui è stato raccolto.
2. **`source-analyzer`.** Ogni misura è stata destrutturata nel formato canonico, con
   `source_refs` su ogni dato numerico e su ogni requisito. Dove la fonte non dice, il campo è
   finito in `dati_mancanti`: non è stato stimato (G-01, G-03).
3. **`explainer`.** Riscrittura in lingua semplice: frasi sotto le 20 parole, soggetto esplicito,
   termini tecnici mantenuti e glossati, numeri copiati e non riformulati.
4. **`fidelity-validator`.** Confronto avversariale della riscrittura con la misura, inventario
   prima e lettura dopo. Quattro divergenze bloccanti trovate su tre misure, tutte corrette al
   secondo giro.

## Esito

- **5 misure pubblicate:** Ristrutturazioni edilizie, Bonus mobili ed elettrodomestici, Spese
  sanitarie, Assegno Unico e Universale per i figli a carico (AUU), Bonus Asilo Nido.
- **1 misura esclusa:** Detrazione per canoni di locazione ai giovani, motivo
  `fonte_non_interpretabile`. La stessa riga della fonte delimita l'età in due modi incompatibili
  ("tra i 20 e 30 anni" e "nel limite del compimento dei 31 anni") e il documento non è datato.
  Il perimetro anagrafico è un requisito, quindi un dato sempre bloccante: si dichiara il problema
  e si passa a una persona. Lo scenario "ricerca lavoro under 36" resta perciò senza misura a
  catalogo, ed è un buco dichiarato.
- **4 divergenze bloccanti**, tutte registrate in `verifica-fase-a.json` con il loro codice:
  due `D-01` (omissione), una `D-06` (perdita di condizione), una `D-04` (alterazione di data).

## Validazione

```
python agents/state/valida_stato.py
```

Valida i 20 artefatti JSON contro gli schemi di `agents/schemas/`, risolvendo i `$ref` locali con
un `referencing.Registry` costruito sui file della cartella. Ultimo esito: **20 su 20 validi,
0 errori**, con `FormatChecker` attivo e `rfc3339-validator` installato, quindi `date` e
`date-time` sono asseriti davvero e non ignorati.

Per non fidarsi di una validazione che passa a vuoto, sul catalogo integro sono state provate nove
mutazioni (data non valida, `verdict` diverso da `approved`, `confidence` sotto 0.6, una frase di
consulenza, il disclaimer accorciato, `iterazioni` a 3, un motivo di esclusione fuori enum, un
beneficio senza `source_refs`, un tetto senza `base_tetto`): **tutte respinte dallo schema**.

## Limiti noti di questo stato

- Il catalogo copre 5 misure su 4 scenari: è un primo catalogo, non l'insieme degli aiuti statali.
- Gli importi dell'AUU vengono da un PDF tabellare la cui estrazione restituisce le colonne e non
  le righe: l'abbinamento soglia-importo è una ricostruzione, dichiarata in testa a
  `fonti/inps-circolare-7-2026-auu-allegato-1.txt`, e la `confidence` della misura è abbassata a
  0.75 per questo.
- Sul Bonus Asilo Nido due pagine INPS non concordano: una pagina non datata riporta 3.000 euro,
  il comunicato stampa del 31 marzo 2026 riporta "fino a 3.600 euro annui". È entrato 3.600, cioè
  il valore della fonte datata, e il conflitto è scritto in `verifica-fase-a.json`.
- Tre attriti fra le fonti reali e i contratti sono emersi durante l'esecuzione
  (`recupero.anni_pregressi_recuperabili` obbligatorio e senza valore "non determinato",
  `canali_accesso` con `minItems: 1` su fonti che non nominano un canale, `tipo_scadenza` che non
  esprime un termine ricorrente). Sono elencati in `verifica-fase-a.json`, sezione
  `note_di_esecuzione`: gli schemi non sono stati modificati.
- Nessun dato personale è presente in questi file (G-17), e nessuna stringa contiene una
  raccomandazione: il contratto stesso la rifiuterebbe (G-04).
