# Validazione scenari end-to-end

Quattro profili eseguiti sulla pipeline Fase B (profiler → eligibility → navigator).
Data: **2026-09-24**. Output completi in `docs/validation/scenario-0*.json`.
I verdetti riflettono il comportamento osservato, non quello atteso.

---

## Scenario 1 — Proprietario, dipendente, ristrutturazione

**Profilo in ingresso (5 risposte a scelta multipla)**

| Domanda | Risposta |
|---|---|
| situazione_vita | proprietario_immobile |
| condizione_abitativa | abitazione_principale |
| tipo_reddito | dipendente |
| timing | ho_già_fatto_i_lavori |
| caf | no_non_ho_un_caf |

**Misure attese**

| id | Nome | Rilevanza attesa |
|---|---|---|
| bonus-ristrutturazioni | Bonus Ristrutturazione | alta |
| ecobonus | Ecobonus | media (dipende dal tipo di lavori) |
| bonus-mobili | Bonus Mobili e Elettrodomestici | media (collegato alla ristrutturazione) |

**Misure restituite dal sistema**

| id | Nome semplice | Rilevanza | Importo max |
|---|---|---|---|
| `bonus-ristrutturazione-50` | Bonus Ristrutturazione 50% | Alta — Molto probabile | fino a 96.000€ di spesa |
| `ecobonus-50` | Ecobonus | Media — Da verificare | dipende dall'intervento |
| `bonus-mobili-50` | Bonus Mobili | Alta — Molto probabile | fino a 5.000€ di spesa |

**Verdetto: CORRETTO — PASS**

I tre bonus attesi sono presenti. L'aliquota Bonus Ristrutturazione è 50% per abitazione
principale, coerente con la fonte (`ade-ristrutturazioni-misura-detrazione.txt`).
L'Ecobonus ha rilevanza media con `nota_incertezza` valorizzata: il sistema segnala
correttamente che la pertinenza dipende dal tipo di lavori al bagno — comportamento onesto.

Il navigator ha prodotto percorsi completi per i due bonus principali (Ristrutturazione
e Mobili), con passi numerati, documenti richiesti e avviso sul bonifico parlante.

Controlli automatici: 6/6 pass.

---

## Scenario 2 — Coppia con figlio appena nato

**Profilo in ingresso (5 risposte a scelta multipla)**

| Domanda | Risposta |
|---|---|
| situazione_vita | genitore_figlio_minore |
| condizione_abitativa | affitto |
| tipo_reddito | dipendente |
| timing | adesso_subito |
| caf | no_non_ho_un_caf |

**Misure attese**

| id | Nome | Rilevanza attesa |
|---|---|---|
| assegno-unico-universale | Assegno Unico Universale | alta |
| bonus-asilo-nido | Bonus Asilo Nido | alta |
| congedo-parentale | Congedo parentale | media |

**Misure restituite dal sistema**

| id | Nome semplice | Rilevanza | Importo max |
|---|---|---|---|
| `assegno-unico-universale` | Assegno Unico | Alta — Molto probabile | fino a 199,40€/mese per figlio |
| `bonus-nido` | Bonus Nido | Alta — Molto probabile | fino a 3.000€/anno |
| `congedo-parentale` | Congedo parentale retribuito | Alta — Molto probabile | fino all'80% della retribuzione |

**Verdetto: CORRETTO con nota — PASS**

I due bonus prioritari sono presenti con rilevanza alta. Il sistema ha aggiunto il
Congedo Parentale (non negli attesi iniziali ma pertinente al profilo: moglie in congedo).
Gli importi Assegno Unico sono corretti (199,40€ max, 57€ senza ISEE, +30€ nei primi
12 mesi). L'ISEE è identificato come prerequisito trasversale e primo passo obbligatorio.

Nota: il navigator include percorsi per i primi due bonus (Assegno Unico e Bonus Nido)
ma non per Congedo Parentale — lacuna minore, non blocca l'utilizzo.

Controlli automatici: 6/6 pass.

---

## Scenario 3 — Disoccupato under 36

**Profilo in ingresso (5 risposte a scelta multipla)**

| Domanda | Risposta |
|---|---|
| situazione_vita | disoccupato |
| condizione_abitativa | affitto |
| tipo_reddito | nessun_reddito_attuale |
| timing | adesso_subito |
| caf | no_non_ho_un_caf |

**Misure attese**

| id | Nome | Rilevanza attesa |
|---|---|---|
| naspi | NASpI | alta (se ex-dipendente) |
| supporto-formazione-lavoro | Supporto per la Formazione e il Lavoro | media |

**Misure restituite dal sistema**

| id | Nome semplice | Rilevanza | Note |
|---|---|---|---|
| `naspi` | Indennità di disoccupazione | Alta | con `nota_incertezza` su tipo perdita lavoro |
| `supporto-formazione-lavoro` | Sussidio per chi cerca lavoro | Alta | ISEE non verificato segnalato |
| `assegno-inclusione` | Sussidio per famiglie in difficoltà | Media | nota: potrebbe non applicarsi a single |
| `detrazione-affitto-inquilini` | Detrazione fiscale affitto | Media | nota: IRPEF potrebbe essere zero |
| `bonus-psicologo` | Contributo psicoterapia | Media | pertinente al contesto |
| `carta-cultura-giovani` | Bonus cultura per i 18enni | Bassa | fuori target (età non verificabile) |

**Verdetto: INCOMPLETO — navigator fallito**

Eligibility (Sonnet): output ricco e onesto. La NASpI è proposta con rilevanza "alta" e
`nota_incertezza` su tipo di perdita ("non è verificabile se volontaria o involontaria")
— comportamento corretto. I requisiti ISEE non noti sono segnalati esplicitamente.

Navigator (Haiku): errore tecnico — timeout dopo i retry.
```json
{"error": true, "messaggio": "Non è stato possibile generare le istruzioni. Rivolgiti a un CAF."}
```
Il fallback al CAF è corretto (nessuna risposta inventata), ma l'utente perde
le istruzioni dettagliate per NASpI e SFL. Problema tecnico: chiamata Haiku in timeout
dopo il ciclo Sonnet lungo. Fix: chiamate parallele o timeout differenziato per agente.

---

## Scenario 4 — Pensionato con spese mediche

**Profilo in ingresso (5 risposte a scelta multipla)**

| Domanda | Risposta |
|---|---|
| situazione_vita | pensionato |
| condizione_abitativa | proprietario_immobile |
| tipo_reddito | pensione |
| timing | ho_già_sostenuto_le_spese |
| caf | no_non_ho_un_caf |

**Misure attese**

| id | Nome | Rilevanza attesa |
|---|---|---|
| detrazione-spese-sanitarie | Detrazione spese sanitarie 19% | alta |
| esenzione-ticket | Esenzione ticket sanitario | media (dipende da reddito/età) |

**Misure restituite dal sistema**

| id | Nome semplice | Rilevanza | Note |
|---|---|---|---|
| `detrazione-spese-sanitarie-19` | Rimborso spese mediche 19% | Alta | nota su dichiarazione integrativa anni precedenti |
| `esenzione-ticket-sanitario` | Esenzione ticket SSN | Alta | over 60 con reddito familiare basso |
| `detrazione-spese-disabilita` | Agevolazioni L.104 | Media | nota: richiede certificazione non verificata |
| `bonus-psicologo` | Rimborso psicoterapia | Bassa | incluso per completezza |
| `bonus-ristrutturazione-50` | Detrazione lavori in casa | Media | nota: lavori non confermati dal profilo |

**Verdetto: INCOMPLETO — navigator fallito**

Eligibility: output corretto. Le due misure prioritarie (detrazione 19% e esenzione ticket)
sono a rilevanza "alta". Il sistema segnala la possibilità di dichiarazione integrativa per
anni precedenti (pertinente al profilo "vuole recuperare agevolazioni del passato").

Navigator: stesso errore dello scenario 3 — timeout.
```json
{"error": true, "messaggio": "Non è stato possibile generare le istruzioni. Rivolgiti a un CAF."}
```
Stessa causa tecnica. Il CAF è il riferimento corretto per un pensionato, ma l'istruzione
passo per passo sarebbe stata più utile.

---

## Riepilogo

| Scenario | Eligibility | Navigator | Esito |
|---|---|---|---|
| 01 — Proprietario ristrutturazione | ✓ corretto | ✓ completo | **PASS** |
| 02 — Coppia neonato | ✓ corretto | ✓ quasi completo | **PASS con nota** |
| 03 — Disoccupato under 36 | ✓ corretto | ✗ timeout | **INCOMPLETO** |
| 04 — Pensionato spese mediche | ✓ corretto | ✗ timeout | **INCOMPLETO** |

La fase eligibility (Sonnet) produce output di qualità in tutti e 4 i casi, con note
di incertezza oneste dove i requisiti non sono verificabili. Il collo di bottiglia è il
navigator in timeout sulle sessioni più lunghe. Il fallback al CAF evita risposte
inventate — il controllo di qualità è operativo anche in condizioni degradate.
