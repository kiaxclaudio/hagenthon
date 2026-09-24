# Costo in contesto delle istruzioni

Generato da `tools/misura_token.py`. Metodo: **stima** dichiarata, 3.6 caratteri per token.

Misura il costo **fisso** che ogni agente porta in contesto a ogni
invocazione: le sue istruzioni piu' le skill che carica. Non misura
i dati di lavoro, che variano con l'input.

| Agente | Fase | Tier | Istruzioni | Skill caricate | Token skill | Totale |
|---|---|---|---:|---|---:|---:|
| `orchestrator` | A+B | haiku | 1,830 | hitl-escalation | 4,906 | **6,736** |
| `eligibility` | B | sonnet | 2,489 | — | 0 | **2,489** |
| `explainer` | A | sonnet | 1,658 | plain-language | 4,266 | **5,924** |
| `fidelity-validator` | A | opus | 1,834 | fidelity-diff-taxonomy | 6,328 | **8,162** |
| `navigator` | B | haiku | 1,843 | — | 0 | **1,843** |
| `profiler` | B | haiku | 1,851 | — | 0 | **1,851** |
| `source-analyzer` | A | opus | 2,079 | — | 0 | **2,079** |

## Le due fasi

- **Fase A** (preparazione, una volta per catalogo): 16,165 token di istruzioni
- **Fase B** (conversazione, a ogni sessione): 6,183 token di istruzioni
- **Orchestratore** (entrambe): 6,736 token

La Fase A costa **2.6 volte** la Fase B in sole istruzioni, e usa
i due modelli piu' capaci. Per questo viene eseguita una volta sola per
catalogo e il risultato e' persistito in `agents/state/catalogo.json`.
A runtime resta la sola Fase B, che legge un JSON gia' verificato.

## Cosa dice davvero questa tabella

E' il costo **fisso** che ogni agente porta in contesto a ogni invocazione. Non misura i dati
di lavoro: quelli variano con l'input e non sono una proprieta dell'architettura.

Tre osservazioni oneste, comprese quelle che non ci fanno comodo.

**La tesi delle due fasi regge.** La preparazione costa piu del doppio della conversazione in
sole istruzioni, e usa i due modelli piu capaci: `source-analyzer` e `fidelity-validator` girano
su Opus. Ma viene eseguita **una volta per catalogo**, non per sessione. A runtime resta la sola
Fase B, tre agenti su Haiku e Sonnet che leggono un JSON gia verificato. Il costo non cresce
con l'uso: cresce con il numero di misure in catalogo, che cambia raramente.

**Il `fidelity-validator` e l'agente piu pesante del sistema**, ed e voluto. Porta con se la
tassonomia completa delle divergenze, perche il suo compito e accorgersi di una percentuale
cambiata o di un obbligo diventato consiglio. E' anche l'unico che gira su Opus senza scrivere
niente: ha il solo tool `Read`. E' il punto dove abbiamo deciso di non risparmiare.

**L'orchestratore e piu pesante di quanto dovrebbe.** Gira su Haiku e fa solo instradamento,
ma porta con se l'intera descrizione della pipeline. E' il candidato naturale per un
alleggerimento: una parte delle sue istruzioni descrive comportamenti che gli agenti gia
conoscono dai propri file. Lo dichiariamo come debito invece di nasconderlo.

## Come rifare la misura

```
python tools/misura_token.py --md > docs/token-budget.md
```

Con `ANTHROPIC_API_KEY` nell'ambiente lo strumento usa l'endpoint ufficiale di conteggio e i
numeri diventano esatti; senza chiave usa la stima dichiarata in testa al file. In entrambi i
casi il metodo e stampato nel report, cosi si sa sempre che cosa si sta leggendo.
