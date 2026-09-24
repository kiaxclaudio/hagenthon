# Slash command: le due sequenze che si rilanciano davvero

Un comando esiste solo se una sequenza di passi va rieseguita **identica** piu' volte. Se si
usa una volta sola, il posto giusto e' `agents/workflows/main-pipeline.md`, non qui.

Due comandi, uno per fase. Non ce n'e' un terzo perche' non c'e' un terzo tratto che si
ripete: duplicare in un comando cio' che sta gia' in un file agente costa punti sul criterio
"qualita' delle istruzioni", che penalizza esplicitamente le sovrapposizioni.

| Comando | Fase | Tratto eseguito | Tier | Argomento |
|---|---|---|---|---|
| `/analizza-profilo` | B | `profiler` -> `eligibility` -> `navigator` | haiku (instrada) | le risposte della persona |
| `/verifica-catalogo` | A | `explainer` <-> `fidelity-validator`, max 2 giri | haiku (instrada) | una misura del catalogo |

## `/analizza-profilo <risposte>`

Il giro completo della Fase B: normalizza le risposte in profilo, incrocia il profilo con il
catalogo verificato, produce i passi di accesso. Si rilancia a ogni nuova persona e a ogni
scenario di prova — sono i quattro casi della demo, quindi si esegue almeno quattro volte.

Si ferma prima di partire se `agents/state/catalogo.json` manca: senza catalogo verificato le
misure verrebbero dalla memoria del modello, che e' il rischio numero uno del progetto (G-01).
Misure con `confidence < 0.6` non entrano nella scheda: si rimanda a un CAF dicendo perche'.

## `/verifica-catalogo <misura>`

Il ciclo produci-giudica su **una** misura, con il limite di 2 giri e l'escalation HITL. Si
rilancia quando una fonte cambia, quando una misura e' uscita `hitl_required`, o quando si
sospetta una riformulazione infedele. Una misura alla volta apposta: il validator gira su
Opus e "riverifica tutto" e' una spesa che nessuno ha deciso.

Chi scrive non approva: `explainer` produce, `fidelity-validator` giudica con **solo Read**.
Il comando non aggira quella separazione, la esegue.

## Guardrail che i due comandi rendono eseguibili

| ID | Dove si vede |
|---|---|
| G-01 | nessuna misura inventata: senza catalogo ci si ferma |
| G-03 | importi, tetti e date riportati identici alla fonte |
| G-04 | la scheda spiega cosa esiste, non cosa conviene fare |
| G-05, G-06, G-07 | i sub-agenti si passano JSON con `status`, `confidence`, `source_refs` |
| G-08 | 2 giri sul ciclo di fedelta', 1 solo giro sulla Fase B |
| G-09 | i gate sono soglie numeriche (`confidence < 0.6`), non impressioni |
| G-13 | `plain-language` e `fidelity-diff-taxonomy` si caricano dentro il ciclo, non prima |
| G-16 | 3 tentativi con backoff sui timeout, poi `degraded` |

## Come si usano

I file sorgente stanno qui. Claude Code li carica da `.claude/commands/`, dove arrivano come
copia verbatim:

```bash
python tools/sync_claude.py          # genera .claude/ da agents/
python tools/sync_claude.py --check  # exit 1 se le due cartelle divergono
```

Poi, nella sessione:

```
/analizza-profilo compro casa, proprietario, lavoro dipendente, lavori da iniziare
/verifica-catalogo bonus-ristrutturazione-50
```

Senza argomento nessuno dei due indovina: chiede e si ferma.
