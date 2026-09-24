# Prova dei gate HITL

Dimostra che i controlli scattano come progettato. Un gate che non scatta mai
non e una funzionalita: e una frase in un documento.

Eseguito il 2026-09-24 con DEMO_MODE=true su python app/main.py.
Catalogo: versione 0.1.0, 5 misure verificate.

---

## Test 1 - Caso non coperto dal catalogo

**Obiettivo:** verificare che il sistema rimandi al CAF invece di inventare una risposta
quando il profilo non corrisponde a nessuna misura nel catalogo.

**Scenario demo usato:** lavoro-under36
Profilo risultante: disoccupato, reddito nessun_reddito_attuale, timing da_iniziare.
catalogo_mod.misure_candidate() restituisce lista vuota. Gate deterministico in
agents.py:718-732 (caso_non_coperto_dal_catalogo).

**Comportamento osservato** (/api/chat, turno finale, 2026-09-24)

```json
{
  "status": "hitl_required",
  "escalation": true,
  "motivo_escalation": "caso_non_coperto_dal_catalogo",
  "messaggio_escalation": "Per la tua situazione non abbiamo misure verificate nel catalogo. Non inventiamo una risposta: rivolgiti a un CAF o a un commercialista, che possono controllare il tuo caso specifico.",
  "explainer": null,
  "navigator": null,
  "disclaimer": "Queste informazioni servono solo a orientarti e non sono una consulenza. Verifica le scadenze su agenziaentrate.gov.it e per la tua situazione specifica rivolgiti a un CAF o a un commercialista."
}
```

**Cosa dimostra**

Il sistema non allunga l'elenco con misure non verificate pur di dare una risposta.
Il gate e deterministico: misure_candidate() e una funzione Python, non un LLM,
e non puo essere raggirata dal prompt. L'escalation e il prodotto, non un errore.

---

## Test 2 - Confidence sotto soglia

**Obiettivo:** verificare che il sistema non mostri misure quando l'affidabilita
dell'eligibility e sotto la soglia configurata (SOGLIA_CONFIDENCE = 0.6).

**Scenario demo usato:** escalation
Profilo risultante: situazione_vita non_so, condizione_abitativa ospite_familiari,
tipo_reddito partita_iva. Eligibility restituisce confidence: 0.45.
Gate in agents.py:751-765 (confidence_bassa).

**Comportamento osservato** (/api/chat, turno finale, 2026-09-24)

```json
{
  "status": "hitl_required",
  "escalation": true,
  "motivo_escalation": "confidence_bassa",
  "messaggio_escalation": "Il sistema non e abbastanza sicuro della lettura del tuo caso (affidabilita 0.45, soglia 0.6). Preferiamo non mostrarti misure incerte: un CAF puo verificare la tua posizione con i tuoi documenti.",
  "explainer": null,
  "navigator": null,
  "disclaimer": "Queste informazioni servono solo a orientarti e non sono una consulenza. Verifica le scadenze su agenziaentrate.gov.it e per la tua situazione specifica rivolgiti a un CAF o a un commercialista."
}
```

**Cosa dimostra**

La soglia 0.6 e una costante in config.py (SOGLIA_CONFIDENCE), non un'istruzione
al modello. Il messaggio mostra la confidence numerica effettiva (0.45) e la soglia
configurata (0.6): la persona sa perche e stata indirizzata al CAF, non riceve
un rifiuto opaco. La soglia e modificabile senza toccare il prompt.

---

## Test 3 - Escalation dichiarata dall'agente

**Obiettivo:** verificare che il gate scatti anche quando e l'agente eligibility stesso
a dichiarare escalation: true nel payload.

**Gate nel codice:** agents.py:768-774

Questo gate scatta dopo il gate di confidence (Test 2). Se eligibility restituisce
confidence sopra soglia ma dichiara ugualmente escalation: true oppure non trova
misure pertinenti dopo il filtro, il sistema rimanda al CAF indipendentemente
dalla confidence.

**Comportamento osservato - verifica per ispezione del codice (2026-09-24)**

Il gate non e raggiungibile con gli scenari demo attuali: lo scenario `escalation`
ha confidence 0.45 e scatta il gate di Test 2 prima di arrivare a questo punto.
In modalita live (DEMO_MODE=false), il gate scatterebbe quando eligibility dichiara
`escalation: true` con confidence sopra soglia (es. profilo ambiguo su misure non verificate).

Codice verificato in agents.py:768-774:

```python
if payload.get("escalation") or not misure:
    motivo = payload.get("motivo_escalation") or "caso_non_coperto_dal_catalogo"
    messaggio = payload.get("spiegazione_escalation") or (
        "Per la tua situazione non emergono misure con requisiti verificabili "
        "da qui. Un CAF o un commercialista possono valutare il tuo caso."
    )
    return _escalation(motivo, messaggio, eligibility=uscita_eligibility)
```

La struttura dell'output e identica a quella dei Test 1 e 2:

```json
{
  "status": "hitl_required",
  "escalation": true,
  "motivo_escalation": "<motivo dal payload agente o caso_non_coperto_dal_catalogo>",
  "messaggio_escalation": "<spiegazione dal payload agente>",
  "explainer": null,
  "navigator": null
}
```

**Cosa dimostra**

I gate HITL sono a strati: deterministico (Test 1), numerico (Test 2), semantico (Test 3).
I primi due sono in codice Python, non in istruzioni LLM: non si bypassano con un prompt.
Il terzo e una rete di sicurezza semantica: anche se i controlli quantitativi passano,
l'agente puo dichiarare direttamente che il caso supera la sua competenza.

---

## Mappa gate - codice

| Gate | Condizione | File | Righe | Motivo |
|---|---|---|---|---|
| Profilo incompleto | 2 invocazioni profiler fallite | agents.py | 644-652 | profilo_incompleto |
| Catalogo vuoto | misure_candidate() vuota | agents.py | 718-732 | caso_non_coperto_dal_catalogo |
| Confidence bassa pipeline | confidence < 0.6 | agents.py | 751-765 | confidence_bassa |
| Escalation agente | payload.escalation true o misure vuote | agents.py | 768-774 | dichiarato dall'agente |
| Confidence bassa misura | m.confidence < 0.6 per tutte | agents.py | 778-795 | confidence_bassa |
| Navigator senza passi | passi vuoti per tutte le misure | agents.py | 834-842 | requisiti_non_verificabili |
