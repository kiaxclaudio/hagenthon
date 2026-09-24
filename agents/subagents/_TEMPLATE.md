# Agente: <nome-kebab-case>

> Template obbligatorio. Ogni sub-agente compila **tutte** le sezioni.
> Se una sezione non si applica, scrivi "non applicabile" e il perché: mai lasciarla vuota.
> Motivo: il criterio "Qualità delle istruzioni" (19%) premia scope chiaro, formato di output
> definito, vincoli espliciti e assenza di sovrapposizioni tra agenti.

## Scope

**Fa:** una frase, un solo verbo principale.

**Non fa:** l'elenco esplicito di ciò che è competenza di un altro agente, con il nome dell'agente.
Questa sezione è ciò che dimostra alla giuria che non ci sono sovrapposizioni.

## Model tier

`haiku-4.5` | `sonnet-5` | `opus-5` — più una riga sul perché questo tier basta.
Salire di tier senza motivo costa punti sul criterio "Efficienza dei token" (12%).

## Input

| Campo | Tipo | Origine |
|---|---|---|
| | | |

Schema: `agents/schemas/<nome>.input.json`

## Output

Esclusivamente JSON conforme a `agents/schemas/<nome>.output.json`.
Nessuna prosa fuori dal JSON. Nessun commento. Nessun blocco markdown attorno.

## Passi

1.
2.
3.

## Vincoli

- (vincoli di dominio: cosa non deve mai fare)
- (vincoli di forma: lunghezza, lingua, livello di lettura)

## Fallback

Cosa produce quando l'input è incompleto, ambiguo o illeggibile.
Deve restituire un output **valido** con `status: "degraded"`, mai un errore non gestito.

## Gate HITL (escalation umana)

Condizione esatta che ferma l'agente e chiama una persona. Deve essere verificabile, non "se è incerto".
Esempio: `confidence < 0.6` oppure `il validator ha respinto due volte di seguito`.

## Limite di iterazioni

Numero massimo di cicli. Al superamento: HITL, non un altro tentativo.

## Errori gestiti

| Errore | Comportamento |
|---|---|
| timeout modello | retry con backoff, max 3, poi `status: "degraded"` |
| output non conforme allo schema | 1 ri-richiesta con lo schema in chiaro, poi HITL |
