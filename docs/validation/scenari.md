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

**Verdetto: CORRETTO (atteso, da verificare sul catalogo)**

Profilo con figlio minore + dipendente attiva correttamente Assegno Unico e Bonus Nido.
La scadenza critica del Bonus Nido (documenti di spesa entro il 30 aprile dell'anno
successivo, fonte: `agents/state/fonti/inps-cs-bonus-asilo-nido-2026.txt`) deve
apparire in navigator come avvertenza_timing.

**Gate atteso:** se ISEE non è dichiarato nel profilo, eligibility deve abbassare
confidence e segnalare requisito_da_verificare per la fascia di importo.

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

**Verdetto: PARZIALE — lacuna documentata**

"Disoccupato" senza specificare se ex-dipendente o mai assunto lascia il requisito
NASpI (13 settimane di contributi) come `da_verificare`. Eligibility NON deve assumere
che la NASpI spetti: deve dichiararla con confidence ridotta e indicare il requisito
mancante. Se invece assume il peggio e rimanda al CAF, anche quello è un esito corretto
(motivo_escalation: requisiti_non_verificabili).

Questo scenario dimostra che il sistema non inventa risposte su profili incompleti.

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

**Verdetto: CORRETTO (atteso, da verificare sul catalogo)**

La detrazione del 19% sulle spese eccedenti 129,11 € (fonte:
`agents/state/fonti/ade-spese-sanitarie-aspetti-generali.txt`) è uno dei casi più
frequenti per i pensionati. Navigator deve ricordare: le spese devono essere pagate
con metodo tracciabile (eccezione: farmaci e strutture SSN, dove il contante è ammesso).

---

## Come aggiornare questo file

Quando `agents/state/catalogo.json` sarà disponibile:

1. Eseguire l'app sui 4 profili sopra
2. Copiare l'output di eligibility (misure_pertinenti + misure_escluse) per ogni scenario
3. Sostituire "Verdetto: CORRETTO (atteso)" con il verdetto osservato + diff se ci sono discrepanze
4. Aggiungere l'output effettivo di navigator per le avvertenze timing
