# Prima / dopo: confronto testo originale → sistema

Mostra cosa riesce a fare la persona dopo che prima non riusciva a fare.
Non "il testo è più chiaro" — ma "sa quali documenti servono e dove andare".

Fonti ufficiali: `agents/state/fonti/`. Testi originali citati alla lettera.
Output di sistema: prodotto dalla pipeline reale il 2026-09-24 (JSON in `docs/validation/`).

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

**Output reale del sistema** *(da `scenario-01-proprietario-ristrutturazione.json`, eligibility_output)*

> **cosa_e:**
> "Uno sconto sulle tasse che paghi ogni anno. Se hai ristrutturato casa, recuperi il 50% di quello che hai speso, suddiviso in 10 rate annuali uguali quando fai la dichiarazione dei redditi."
>
> **quanto_vale:**
> "Se hai speso 20.000€ di lavori, recuperi 10.000€ totali: 1.000€ all'anno per 10 anni. Il tetto massimo di spesa su cui calcolare il 50% è 96.000€ per immobile."
>
> **chi_puo_accedervi:**
> "Proprietari di casa o chi ha un diritto reale sull'immobile (es. usufrutto). Anche chi affitta può accedere se ha sostenuto le spese. L'immobile deve essere a uso residenziale."
>
> **attenzione:**
> "I pagamenti devono essere stati fatti con bonifico bancario o postale 'parlante' (che riporta causale, codice fiscale del beneficiario e P.IVA dell'impresa). Pagamenti in contanti non sono detraibili."
>
> **Glossario generato automaticamente:**
> - *detrazione IRPEF* → "uno sconto sulle tasse che paghi a fine anno"
> - *bonifico parlante* → "bonifico con causale specifica richiesta dall'Agenzia delle Entrate per i bonus edilizi"

**Cosa riesce a fare la persona dopo**

| Prima (testo ADE) | Dopo (output sistema) |
|---|---|
| Sa che esiste una "detrazione del 50% con limite 96.000€" | Sa che recupererà 1.000€/anno per 10 anni su 20.000€ di lavori |
| Legge "diritto reale di godimento" | Sa che "anche chi affitta può accedere" |
| Non sa cosa fare con "articolo 16-bis del Tuir" | Ha passi concreti: raccogliere fatture, portare al CAF, ricevere lo sconto in busta paga |
| Non sa che il bonifico deve essere "parlante" | Sa controllare la causale delle ricevute prima di andare al CAF |

**Verifica fidelty**

| Valore originale | Valore restituito | Esito |
|---|---|---|
| "50% per abitazione principale" | "50%" (profilo proprietario + abitazione principale) | ✅ corretto |
| "96.000 euro" | "96.000€ per immobile" | ✅ identico |
| "10 quote annuali" | "10 rate annuali uguali" | ✅ significato invariato |
| "bonifico parlante" | presente in `attenzione` con spiegazione | ✅ conservato e spiegato |

Verdetto: **approvato**.

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
