"""Configurazione unica dell'applicazione.

Qui stanno, in un solo posto e leggibili a colpo d'occhio:
- la mappa agente -> tier e i modelli reali, letti da .env (mai scritti nel codice);
- i parametri di resilienza (timeout, retry, backoff);
- i limiti di iterazione e le soglie dei gate HITL di agents/ARCHITETTURA.md;
- i percorsi dello stato esternalizzato in agents/state/.

Nessun segreto in questo file: solo nomi di variabili d'ambiente (C1).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

RADICE = Path(__file__).resolve().parent.parent

# .env locale, non committato. Se manca, valgono i default qui sotto.
load_dotenv(RADICE / '.env')

# --------------------------------------------------------------------------
# Modelli e model tiering (C5)
# --------------------------------------------------------------------------

# I tre tier. Gli identificativi arrivano da .env (vedi .env.example): il codice
# porta solo un default allineato agli stessi valori, per non rompere la demo se
# la variabile manca.
MODELLI_PER_TIER: dict[str, str] = {
    'haiku': os.getenv('ANTHROPIC_MODEL_CHEAP', 'claude-haiku-4-5-20251001'),
    'sonnet': os.getenv('ANTHROPIC_MODEL_WORK', 'claude-sonnet-5'),
    'opus': os.getenv('ANTHROPIC_MODEL_DEEP', 'claude-opus-5'),
}

# Mappa esplicita agente -> tier. E' la trascrizione della tabella dei sette
# componenti in agents/ARCHITETTURA.md: chi legge il codice verifica il tiering
# senza inseguire le chiamate.
TIER_PER_AGENTE: dict[str, str] = {
    # Fase A - grounding del catalogo, gira una volta sola
    'source-analyzer': 'opus',      # destruttura la fonte ufficiale
    'explainer': 'sonnet',          # riscrive in lingua semplice
    'fidelity-validator': 'opus',   # verifica le cifre, separato da chi le ha scritte
    # Fase B - conversazione, gira a ogni sessione
    'orchestrator': 'haiku',        # instrada
    'profiler': 'haiku',            # normalizza le risposte
    'eligibility': 'sonnet',        # incrocia profilo e catalogo
    'navigator': 'haiku',           # compone i passi
}

# Tetto di output per agente (F2): nessuno riceve o produce piu' del necessario.
# I valori sono misurati sull'output reale piu' un margine, non scelti a occhio:
# un tetto troppo basso tronca la risposta a meta' JSON e costa una ri-richiesta,
# uno troppo alto lascia spazio a un ragionamento che qui non serve.
MAX_TOKEN_PER_AGENTE: dict[str, int] = {
    # Fase A: output lunghi e strutturati, con il ragionamento acceso (vedi sotto),
    # quindi il tetto deve contenere ANCHE i token di pensiero.
    'source-analyzer': 16000,
    'explainer': 8000,
    'fidelity-validator': 8000,
    # Fase B: solo JSON, pensiero spento, tetto sul contenuto effettivo.
    'orchestrator': 600,
    'profiler': 700,
    'eligibility': 2500,
    'navigator': 2500,
}

MAX_TOKEN_DEFAULT = 2000

# --------------------------------------------------------------------------
# Ragionamento esteso: acceso dove serve, spento dove costa e basta
# --------------------------------------------------------------------------

# Sui modelli correnti (Sonnet 5, Opus 5) il ragionamento esteso e' ATTIVO per
# default e i suoi token escono dallo stesso budget di 'max_tokens'. Con un tetto
# stretto il modello consuma tutto il budget pensando e la risposta torna senza
# nessun blocco di testo: la chiamata finisce a 'max_tokens' con zero contenuto.
# E' esattamente cio' che bloccava eligibility. Quindi la scelta va dichiarata
# per agente, come il tier, invece di essere subita:
#   'adattivo'    -> ragionamento acceso (Fase A: si giudica una fonte ufficiale)
#   'disattivato' -> nessun ragionamento (Fase B: si compila un JSON su un input
#                    gia' verificato, e la demo dal vivo ha un tetto di tempo)
PENSIERO_PER_AGENTE: dict[str, str] = {
    'source-analyzer': 'adattivo',
    'explainer': 'adattivo',
    'fidelity-validator': 'adattivo',
    'orchestrator': 'disattivato',
    'profiler': 'disattivato',
    'eligibility': 'disattivato',
    'navigator': 'disattivato',
}


def pensiero_di(agente: str) -> str:
    return PENSIERO_PER_AGENTE.get(agente, 'disattivato')


def parametri_pensiero(agente: str) -> dict:
    """Parametri di ragionamento da passare a messages.create per questo agente.

    Haiku 4.5 non ha il ragionamento adattivo e non accetta 'output_config':
    per lui la forma corretta e' non mandare niente, che equivale a spento.
    """
    modello = modello_di(agente)
    if 'haiku' in modello:
        return {}
    if pensiero_di(agente) == 'adattivo':
        return {'thinking': {'type': 'adaptive'}}
    return {'thinking': {'type': 'disabled'}}


def modello_di(agente: str) -> str:
    """Identificativo del modello da usare per un agente, via il suo tier."""
    tier = TIER_PER_AGENTE.get(agente)
    if tier is None:
        raise KeyError(
            f"agente sconosciuto: {agente!r}. "
            f"Agenti previsti: {', '.join(sorted(TIER_PER_AGENTE))}"
        )
    return MODELLI_PER_TIER[tier]


def max_token_di(agente: str) -> int:
    return MAX_TOKEN_PER_AGENTE.get(agente, MAX_TOKEN_DEFAULT)


# --------------------------------------------------------------------------
# Resilienza delle chiamate al modello (C2, C3)
# --------------------------------------------------------------------------

def _intero(nome: str, default: int) -> int:
    try:
        return int(os.getenv(nome, default))
    except (TypeError, ValueError):
        return default


def _decimale(nome: str, default: float) -> float:
    try:
        return float(os.getenv(nome, default))
    except (TypeError, ValueError):
        return default


TIMEOUT_S: float = _decimale('LLM_TIMEOUT_S', 60.0)
MAX_RETRY: int = max(0, _intero('LLM_MAX_RETRIES', 3))
BACKOFF_BASE_S: float = _decimale('LLM_BACKOFF_BASE_S', 1.0)
BACKOFF_MAX_S: float = _decimale('LLM_BACKOFF_MAX_S', 20.0)

API_KEY: str | None = os.getenv('ANTHROPIC_API_KEY') or None

# --------------------------------------------------------------------------
# Modalita demo (B3: il percorso di demo non dipende da servizi esterni)
# --------------------------------------------------------------------------

# Con DEMO_MODE=true nessuna chiamata all'API: gli output degli agenti vengono
# da app/demo/ e passano per la stessa validazione del percorso reale.
DEMO_MODE: bool = os.getenv('DEMO_MODE', 'false').strip().lower() in ('1', 'true', 'yes', 'si')
DEMO_DIR = Path(__file__).resolve().parent / 'demo'

# --------------------------------------------------------------------------
# Limiti di iterazione e gate HITL (D2, D3, D4)
# --------------------------------------------------------------------------

MAX_GIRI_FIDELITY = 2       # explainer <-> fidelity-validator, poi hitl_required
MAX_RICHIESTE_SCHEMA = 1    # una sola ri-richiesta dopo un output non conforme
MAX_MISURE_NAVIGATOR = 3    # misure guidate per sessione
SOGLIA_CONFIDENCE = 0.6     # sotto questa soglia eligibility non propone

# --------------------------------------------------------------------------
# Percorsi: contratti, prompt, stato esternalizzato (E3)
# --------------------------------------------------------------------------

SCHEMI_DIR = RADICE / 'agents' / 'schemas'
PROMPT_DIR = RADICE / '.claude' / 'agents'
STATE_DIR = RADICE / 'agents' / 'state'

CATALOGO_PATH = STATE_DIR / 'catalogo.json'
PROFILO_PATH = STATE_DIR / 'profilo.json'
MISURE_GREZZE_PATH = STATE_DIR / 'misure-grezze.json'
FONTI_DIR = STATE_DIR / 'fonti'


def run_path(run_id: str) -> Path:
    """File di stato della sessione: agents/state/run-<id>.json."""
    return STATE_DIR / f'run-{run_id}.json'


def assicura_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
