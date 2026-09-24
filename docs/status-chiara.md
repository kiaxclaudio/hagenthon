# Status - Chiara

Solo Chiara scrive in questo file. Davide lo legge.
Serve per non interrompere l'altra persona fuori dalle sincronizzazioni.

## Sto facendo

Niente, in attesa di sincronizzazione con Davide.

## Fatto

- `.claude/agents/` — 4 file agente pronti (orchestrator, eligibility, explainer, navigator)
  - orchestrator e navigator su `claude-haiku-4-5`
  - eligibility ed explainer su `claude-sonnet-4-6`
  - tutti con sezione "Gestione output malformato" e vincoli espliciti
- `.claude/commands/analizza-profilo.md` — slash command flusso completo
- `.claude/settings.json` — hooks PostToolUse (validate_output.py) + Stop (log_session.py)
- `app/` — Flask completo: main.py, agents.py (pipeline + retry max 2 + HITL), session.py, UI chat
- `app/static/` — CSS tema scuro viola Accenture + JS con scelte multiple e rendering schede bonus
- `app/templates/index.html` — layout due pannelli chat/risultati
- `presentation/index.html` — 5 slide brandizzate Accenture (#A100FF)
- `scripts/validate_output.py` — validazione anti-consulenza finanziaria
- `scripts/log_session.py` — logging sessioni
- `requirements.txt` — anthropic, flask, python-dotenv
- App testata e avviata su localhost:5000

## Mi serve da Davide

- Conferma che l'architettura 4-agenti in `.claude/agents/` è allineata con quello che ha in testa per `agents/`
- Se vuole che `app/agents.py` referenzi gli schema JSON in `agents/schemas/` per la validazione output

## Bloccato su

Niente al momento.
