# Prima / dopo: confronto testo originale → sistema

Mostra cosa riesce a fare la persona dopo che prima non riusciva a fare.
Non "il testo è più chiaro" — ma "sa quali documenti servono e dove andare".

Fonti: `agents/state/fonti/`. Testi originali citati alla lettera dalla fonte.
Versione semplificata: prodotta dall'agente `explainer` in Fase A e verificata da
`fidelity-validator`. Nota: catalogo.json non ancora disponibile — le versioni
semplificate qui sotto sono generate direttamente dalla fonte, non dal catalogo.

---

## Caso 1 — Bonus Ristrutturazione: aliquota e tetto di spesa

**Testo originale**
*(fonte: agenziaentrate.gov.it, sezione `[aliquote-2025-2026]` e `[limite-di-spesa]`)*

> "Per le spese sostenute negli anni 2025 e 2026, la detrazione spetta nella misura del
> 36% (ovvero del 50% in caso di abitazione principale)"
>
> "Su un massimo di 96.000 euro per unità immobiliare"
>
> "Da ripartire in 10 quote annuali di pari importo"

**Versione semplificata (explainer)**

> **Quanto puoi recuperare con il Bonus Ristrutturazione**
>
> Se hai fatto lavori in casa nel 2025 o nel 2026, puoi recuperare parte di quello
> che hai speso come sconto sulle tasse (detrazione IRPEF).
>
> Se la casa è la tua abitazione principale: recuperi il **50%** della spesa.
> Se è un'altra proprietà: recuperi il **36%**.
>
> Lo sconto si calcola su un massimo di **96.000 euro** di spesa per ogni immobile.
> Lo ricevi in **10 quote uguali** ogni anno, quando fai il 730 o la dichiarazione
> dei redditi.
>
> Esempio: hai speso 20.000 euro sulla tua casa principale.
> Recuperi 20.000 × 50% = 10.000 euro, in rate da 1.000 euro/anno per 10 anni.

**Cosa riesce a fare la persona dopo**

Prima: leggeva "detrazione IRPEF ripartita in 10 quote annuali su massimo 96.000 euro"
e non sapeva se si applicava alla sua casa né quanto avrebbe ricevuto in concreto.

Dopo: sa che per la sua abitazione principale l'aliquota è 50%, conosce il tetto, sa
che riceve lo sconto spalmato in 10 anni sul 730 e può stimare l'importo annuo.

**Verifica fidelity-validator**

| Valore originale | Valore semplificato | Esito |
|---|---|---|
| "36%" | "36%" | ✅ identico |
| "50% in caso di abitazione principale" | "50% se è la tua abitazione principale" | ✅ condizione conservata |
| "96.000 euro" | "96.000 euro" | ✅ identico |
| "10 quote annuali" | "10 quote uguali ogni anno" | ✅ significato invariato |

Nessuna divergenza bloccante. Verdetto: **approvato**.

---

## Caso 2 — Bonus Asilo Nido: domanda e scadenza

**Testo originale**
*(fonte: INPS, comunicato stampa marzo 2026, `inps-cs-bonus-asilo-nido-2026.txt`)*

> "La domanda deve essere presentata dal genitore che sostiene la spesa della retta,
> esclusivamente online tramite il portale INPS — utilizzando SPID, CIE o CNS —
> oppure tramite patronato."
>
> "Ogni anno sarà possibile scegliere le mensilità per le quali si intende richiedere
> il contributo, caricando i relativi documenti di spesa entro il 30 aprile dell'anno
> successivo a quello a cui si riferiscono le mensilità."
>
> "Il beneficio può arrivare fino a 3.600 euro annui"
>
> "Se la struttura non risulta abilitata, il contributo non verrà riconosciuto."

**Versione semplificata (explainer)**

> **Come fare domanda per il Bonus Asilo Nido**
>
> Il **Bonus Asilo Nido** può arrivare fino a **3.600 euro all'anno**.
>
> Devi fare domanda tu — il genitore che paga la retta — in uno di questi due modi:
>
> 1. **Online sul portale INPS** (inps.it), con SPID, CIE o CNS.
>    Lo SPID è la tua identità digitale per i siti della pubblica amministrazione.
> 2. **Tramite patronato**, se preferisci l'aiuto di uno sportello.
>
> Ogni anno scegli per quali mesi vuoi il contributo e carichi le ricevute di pagamento
> della retta. Le ricevute devono essere caricate **entro il 30 aprile** dell'anno
> successivo.
>
> Attenzione: **prima di presentare domanda**, chiedi alla struttura educativa i
> riferimenti precisi della sua abilitazione. Se la struttura non è abilitata, il
> contributo non ti verrà riconosciuto.

**Cosa riesce a fare la persona dopo**

Prima: sapeva che esisteva un bonus ma non capiva chi dovesse fare domanda, come,
dove, entro quando, e cosa rischiava se la struttura non era "abilitata".

Dopo: sa che tocca a lei fare domanda, conosce i due canali (INPS online o patronato),
sa la scadenza del 30 aprile, capisce cosa significa "abilitazione" e sa come verificarla.

**Verifica fidelity-validator**

| Valore originale | Valore semplificato | Esito |
|---|---|---|
| "esclusivamente online tramite il portale INPS" | "Online sul portale INPS (inps.it)" | ✅ canale conservato |
| "oppure tramite patronato" | "Tramite patronato" | ✅ alternativa conservata |
| "entro il 30 aprile" | "entro il 30 aprile" | ✅ identico |
| "3.600 euro annui" | "3.600 euro all'anno" | ✅ valore identico, unità invariata |
| "il contributo non verrà riconosciuto" | "il contributo non ti verrà riconosciuto" | ✅ conseguenza conservata |

Nessuna divergenza bloccante. Verdetto: **approvato**.

---

## Caso 3 — Spese sanitarie: franchigia e pagamento tracciabile

**Testo originale**
*(fonte: agenziaentrate.gov.it, `ade-spese-sanitarie-aspetti-generali.txt`)*

> "È possibile portare in detrazione dall'Irpef il 19% delle spese sanitarie per la
> parte eccedente l'importo di 129,11 euro."
>
> "la detrazione del 19%...è fruibile soltanto se il pagamento è effettuato con
> versamento bancario o postale o altri sistemi tracciabili"
>
> "il versamento in contanti continua a essere ammesso...per l'acquisto di medicinali
> e di dispositivi medici e per pagare tutte le prestazioni sanitarie rese dalle
> strutture pubbliche o dalle strutture private accreditate al Servizio sanitario
> nazionale"

**Versione semplificata (explainer)**

> **Detrazione spese mediche: il 19% di quello che hai speso**
>
> Se hai pagato spese mediche, puoi recuperare il **19%** come sconto sulle tasse,
> quando fai il 730 o la dichiarazione dei redditi (detrazione IRPEF).
>
> Lo sconto si calcola solo sulla parte che supera **129,11 euro**: quella soglia
> non si detrae.
>
> Esempio: hai speso 800 euro. Il 19% si calcola su 670,89 euro (800 meno 129,11).
> Recuperi 127,47 euro.
>
> Regola di pagamento: per avere lo sconto devi aver pagato con bonifico, carta o
> altro sistema tracciabile. **Eccezione:** per farmaci, dispositivi medici e visite
> nelle strutture del Servizio Sanitario Nazionale puoi pagare anche in contanti e
> lo sconto spetta lo stesso.

**Cosa riesce a fare la persona dopo**

Prima: sapeva che le spese mediche "si detraggono" ma non sapeva calcolare quanto,
non conosceva la franchigia da 129,11 €, e non sapeva che pagare in contanti poteva
farle perdere la detrazione.

Dopo: sa calcolare l'importo (19% sull'eccedente 129,11 €), sa quando il contante
è ammesso e quando no, e può controllare le proprie ricevute prima di fare il 730.

**Verifica fidelity-validator**

| Valore originale | Valore semplificato | Esito |
|---|---|---|
| "19%" | "19%" | ✅ identico |
| "129,11 euro" | "129,11 euro" | ✅ identico alla virgola |
| "versamento bancario o postale o altri sistemi tracciabili" | "bonifico, carta o altro sistema tracciabile" | ✅ sostanza invariata, D-09 assente (i termini tecnici chiave restano) |
| "medicinali e di dispositivi medici" | "farmaci, dispositivi medici" | ✅ sinonimo comune, significato invariato (N-1) |

Nessuna divergenza bloccante. Verdetto: **approvato**.
