# Validazione scenari end-to-end

Quattro scenari eseguiti con `DEMO_MODE=true` sul sistema attuale (catalogo v0.2.0, 5 misure
verificate). Data: **2026-09-24**.

L'output della pipeline pre-grounding (prima che il catalogo esistesse) è conservato nei file
`scenario-0*.json` come evidenza del "prima": in quello stato il sistema proponeva fino a 6
misure costruite a memoria, incluse misure assenti dal catalogo verificato. Il confronto è
documentato in `prima-dopo.md`.

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

**Misure restituite dal catalogo verificato**

| id | Nome breve | Fonte |
|---|---|---|
| assegno-unico | Assegno Unico e Universale | INPS |
| bonus-asilo-nido | Bonus asilo nido | INPS |

**Verdetto: PASS**

Q2 (condizione abitativa) non posta perché irrilevante per le misure "figlio" del catalogo:
questo è il comportamento corretto dopo la modifica C-4. Le 2 misure sono verificate nel
catalogo. Il pre-grounding invece restituiva 3 misure incluso `congedo-parentale`, assente
dal catalogo verificato.

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

**Misure restituite dal catalogo verificato**

| id | Nome breve | Fonte |
|---|---|---|
| detrazione-spese-sanitarie | Detrazione spese sanitarie 19% | ADE |

**Verdetto: PASS**

1 misura pertinente nel catalogo. Navigator completo con passi e documenti. Il pre-grounding
restituiva 5 misure (incluse esenzione-ticket, detrazione-disabilità, bonus-psicologo,
bonus-ristrutturazione) tutte assenti dal catalogo verificato, più navigator in timeout.

---

## Riepilogo sistema attuale (2026-09-24, catalogo v0.2.0)

| Scenario | Stage | Misure | Esito |
|---|---|---|---|
| 01 — Casa ristrutturazione | results | bonus-ristrutturazioni, bonus-mobili | **PASS** |
| 02 — Figlio appena nato | results | assegno-unico, bonus-asilo-nido | **PASS** |
| 03 — Lavoro under 36 | escalation | — (caso non coperto) | **GATE HITL** |
| 04 — Pensionato spese mediche | results | detrazione-spese-sanitarie | **PASS** |

Tutte le misure restituite sono nel catalogo verificato. Il sistema non inventa misure
e dichiara esplicitamente i limiti del catalogo attuale.
