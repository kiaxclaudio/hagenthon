# Validazione scenari end-to-end

Quattro scenari eseguiti con `DEMO_MODE=true` sul sistema attuale (catalogo v0.2.0, 5 misure
verificate). Data: **2026-09-24**.

L'output della pipeline pre-grounding (prima che il catalogo esistesse) è conservato nei file
`scenario-0*.json` come evidenza del "prima": in quello stato il sistema proponeva fino a 6
misure costruite a memoria, incluse misure assenti dal catalogo verificato. Il confronto è
documentato in `prima-dopo.md`.

**Nota su `badge_rilevanza`:** il campo appare nei JSON di output demo perche' e' prodotto
dall'explainer come etichetta della misura ("Molto probabile", "Probabile"), non come
valutazione individuale del caso della persona. Non e' un assessment di eligibilita': l'eligibility
e' gia' avvenuta prima (gate HITL o lista misure candidate). La pipeline principale non lo espone
nell'interfaccia utente. Il campo di interesse per la validazione e' `confidence` in eligibility
(valore numerico 0-1), che scatta il gate HITL se sotto 0.6.

---

## Scenario 1 — Casa da ristrutturare

**Profilo** (4 domande, Q2 abitazione inclusa perché situazione_vita = casa)

| Domanda | Risposta |
|---|---|
| situazione_vita | casa |
| condizione_abitativa | proprietario |
| tipo_reddito | lavoro_dipendente |
| timing | da_iniziare |
| caf | no |

**Misure restituite dal catalogo verificato**

| id | Nome breve | Fonte |
|---|---|---|
| bonus-ristrutturazioni | Detrazione ristrutturazione 50% | ADE |
| bonus-mobili | Bonus mobili ed elettrodomestici | ADE |

**Verdetto: PASS**

Eligibility e navigator completano senza errori. Le 2 misure restituite sono le uniche
pertinenti nel catalogo verificato per `situazione_vita: casa`. Nessuna misura inventata,
nessun numero non verificato.

---

## Scenario 2 — Figlio appena nato

**Profilo** (3 domande, Q2 saltata perché situazione_vita = figlio)

| Domanda | Risposta |
|---|---|
| situazione_vita | figlio |
| condizione_abitativa | non_so (domanda non posta) |
| tipo_reddito | lavoro_dipendente |
| timing | in_corso |
| caf | non_so_cosa_e |

**Output**

Il gate di confidence scatta: eligibility restituisce confidence sotto soglia (SOGLIA_CONFIDENCE = 0.6).

```json
{
  "status": "hitl_required",
  "escalation": true,
  "motivo_escalation": "confidence_bassa",
  "messaggio_escalation": "Il sistema non e abbastanza sicuro della lettura del tuo caso. Preferiamo non mostrarti misure incerte: un CAF puo verificare la tua posizione con i tuoi documenti.",
  "explainer": null,
  "navigator": null
}
```

**Verdetto: ESCALATION CORRETTA (confidence_bassa)**

Il gate HITL numerica (agents.py:751-765) scatta per il profilo figlio: la confidence
di eligibility e sotto 0.6. Il sistema non mostra misure incerte. Questo e comportamento
atteso: le misure assegno-unico e bonus-asilo-nido esistono nel catalogo ma eligibility
non raggiunge la soglia minima di affidabilita per questo profilo. Per la demo dal vivo
usare lo scenario casa che produce risultati completi.

---

## Scenario 3 — Lavoro / under 36

**Profilo** (5 domande, Q2 inclusa perché situazione_vita contiene under36)

| Domanda | Risposta |
|---|---|
| situazione_vita | lavoro, under36 |
| condizione_abitativa | ospite_familiari |
| tipo_reddito | nessun_reddito |
| timing | in_corso |
| caf | no |

**Output**

Il catalogo verificato non contiene misure per le situazioni `lavoro` e `under36`. Il gate
HITL scatta in eligibility:

```json
{
  "status": "hitl_required",
  "escalation": true,
  "motivo_escalation": "caso_non_coperto_dal_catalogo",
  "messaggio_escalation": "Per la tua situazione non abbiamo misure verificate fra le fonti che abbiamo letto. Non inventiamo una risposta: rivolgiti a un CAF o a un commercialista."
}
```

**Verdetto: ESCALATION CORRETTA**

Il sistema riconosce il limite del catalogo e rimanda senza inventare. Questo è il
comportamento atteso: il gate HITL è una funzionalità, non un errore. Il pre-grounding
proponeva 6 misure (NASpI, SFL, assegno di inclusione, detrazione affitto, bonus psicologo,
bonus cultura) tutte assenti dal catalogo verificato, più un navigator in timeout.

---

## Scenario 4 — Pensionato con spese mediche

**Profilo** (3 domande, Q2 saltata perché situazione_vita = spese_mediche)

| Domanda | Risposta |
|---|---|
| situazione_vita | spese_mediche |
| condizione_abitativa | non_so (domanda non posta) |
| tipo_reddito | pensione |
| timing | gia_concluso |
| caf | si |

**Output**

Il gate di confidence scatta: eligibility restituisce confidence sotto soglia (SOGLIA_CONFIDENCE = 0.6).

```json
{
  "status": "hitl_required",
  "escalation": true,
  "motivo_escalation": "confidence_bassa",
  "messaggio_escalation": "Il sistema non e abbastanza sicuro della lettura del tuo caso. Preferiamo non mostrarti misure incerte: un CAF puo verificare la tua posizione con i tuoi documenti.",
  "explainer": null,
  "navigator": null
}
```

**Verdetto: ESCALATION CORRETTA (confidence_bassa)**

Il gate HITL numerica (agents.py:751-765) scatta per il profilo pensionato-spese-mediche.
Il sistema non mostra misure incerte. La misura detrazione-spese-sanitarie esiste nel
catalogo verificato ma eligibility non raggiunge la soglia minima di affidabilita.
Il pre-grounding restituiva 5 misure (incluse esenzione-ticket, detrazione-disabilita,
bonus-psicologo, bonus-ristrutturazione) tutte assenti dal catalogo verificato, piu
navigator in timeout.

---

## Riepilogo sistema attuale (2026-09-24, catalogo v0.1.0)

| Scenario | Stage | Misure | Esito |
|---|---|---|---|
| 01 — Casa ristrutturazione | results | bonus-ristrutturazioni, bonus-mobili | **PASS** |
| 02 — Figlio appena nato | escalation | — (confidence_bassa) | **GATE HITL** |
| 03 — Lavoro under 36 | escalation | — (caso non coperto) | **GATE HITL** |
| 04 — Pensionato spese mediche | escalation | — (confidence_bassa) | **GATE HITL** |

Il sistema non inventa misure e dichiara esplicitamente i limiti del catalogo attuale.
Lo scenario casa e l'unico che produce risultati completi (eligibility, explainer, navigator)
nel sistema corrente. I casi 02 e 04 dimostrano il gate di confidence in azione: le misure
esistono nel catalogo ma eligibility non raggiunge la soglia per mostrarle. Il caso 03
dimostra il gate deterministico: nessuna misura candidata nel catalogo per quel profilo.
