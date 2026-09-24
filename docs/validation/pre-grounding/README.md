# pre-grounding/ — evidenza del "prima"

Questi quattro file JSON sono esecuzioni reali della pipeline originale (2026-09-24, ~13:23),
prima dell'integrazione con il catalogo verificato.

Si vede la differenza rispetto al sistema attuale:

- `scenario-03-disoccupato-under36.json` propone sei misure inventate
  ("Indennita di disoccupazione", "Bonus cultura per i 18enni", "Contributo per sedute di psicoterapia")
  che **non esistono nel catalogo verificato**.
- I campi usano il contratto della pipeline originale (`bonus`, `profilo_riassunto`) invece
  di quello integrato (`misure_pertinenti`, `confidence`).

## Confronto prima/dopo

| Metrica | Prima (questa cartella) | Dopo (scenari attuali) |
|---|---|---|
| Misure proposte per scenario | 4-6 inventate | 1-2 verificate da catalogo |
| Fonte misure | memoria LLM | catalogo.json v0.1.0 (5 misure, fonti citate) |
| Caso non coperto | propone misure anche senza corrispondenza | escalation HITL → CAF |
| Contratto output | schema non strutturato | schema JSON fisso con id, confidence, fonte |

Il confronto quantitativo e il deliverable D03 richiesto dagli organizzatori (before/after misurabile).
I file del sistema attuale stanno in `docs/validation/scenario-*.json`.
