"""Validazione degli output degli agenti contro i contratti in agents/schemas/.

Regola del repository: l'app implementa i contratti, non li ridefinisce (E5).
Per questo qui non c'e' nessuna copia degli schemi: si caricano dai file, i $ref
relativi (./_envelope.json#/$defs/...) si risolvono con un registry costruito
sugli $id dei file stessi, e anche il testo del disclaimer si legge dallo schema.

Uso tipico:
    errori = valida_output('eligibility', envelope)
    if errori:
        ...   # una sola ri-richiesta, poi fallback degradato
"""

import json
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from config import SCHEMI_DIR


@lru_cache(maxsize=1)
def _schemi() -> dict[str, dict]:
    """Tutti gli schemi di agents/schemas/, indicizzati per nome file senza estensione."""
    schemi: dict[str, dict] = {}
    for percorso in sorted(SCHEMI_DIR.glob('*.json')):
        schemi[percorso.stem] = json.loads(percorso.read_text(encoding='utf-8'))
    if not schemi:
        raise FileNotFoundError(f'nessuno schema trovato in {SCHEMI_DIR}')
    return schemi


@lru_cache(maxsize=1)
def _registry() -> Registry:
    """Registry dei $id locali: risolve i $ref fra file senza toccare la rete."""
    risorse = []
    for schema in _schemi().values():
        identificativo = schema.get('$id')
        if identificativo:
            risorse.append((identificativo, Resource.from_contents(schema)))
    return Registry().with_resources(risorse)


@lru_cache(maxsize=32)
def _validatore(nome_schema: str) -> Draft202012Validator:
    schemi = _schemi()
    if nome_schema not in schemi:
        raise KeyError(f'schema non trovato: {nome_schema}.json in {SCHEMI_DIR}')
    return Draft202012Validator(schemi[nome_schema], registry=_registry())


def schema_di(nome_schema: str) -> dict:
    return _schemi()[nome_schema]


# Il testo del disclaimer e' un const nello schema: si legge da li' (G2, E5).
def disclaimer() -> str:
    return _schemi()['_envelope']['$defs']['disclaimer']['const']


def valida(nome_schema: str, documento: Any, max_errori: int = 5) -> list[str]:
    """Valida un documento contro uno schema del repository.

    Restituisce la lista degli errori in forma leggibile, vuota se conforme.
    La forma leggibile serve due volte: nei log e, in chiaro, nella ri-richiesta
    all'agente che ha sbagliato.
    """
    try:
        validatore = _validatore(nome_schema)
    except (KeyError, FileNotFoundError, json.JSONDecodeError) as errore:
        return [f'schema non caricabile ({nome_schema}): {errore}']

    errori = []
    for errore in sorted(validatore.iter_errors(documento), key=lambda e: list(e.path)):
        posizione = '/'.join(str(p) for p in errore.path) or '(radice)'
        errori.append(f'{posizione}: {errore.message}')
        if len(errori) >= max_errori:
            errori.append('... altri errori omessi')
            break
    return errori


def valida_output(agente: str, documento: Any, max_errori: int = 5) -> list[str]:
    """Valida l'output di un agente contro agents/schemas/<agente>.output.json (E1)."""
    return valida(f'{agente}.output', documento, max_errori)


def valida_input(agente: str, documento: Any, max_errori: int = 5) -> list[str]:
    """Valida l'input di un agente prima di spedirlo: si sbaglia prima e costa meno."""
    return valida(f'{agente}.input', documento, max_errori)


def valida_envelope(documento: Any, max_errori: int = 5) -> list[str]:
    """Valida solo la busta: status, confidence, source_refs, payload (E2)."""
    return valida('_envelope', documento, max_errori)


def ora() -> str:
    """Timestamp ISO 8601 con fuso, come vuole _envelope.json#/$defs/timestamp."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def envelope(
    payload: dict,
    *,
    status: str = 'ok',
    confidence: float = 1.0,
    source_refs: list[str] | None = None,
) -> dict:
    """Costruisce una busta conforme a _envelope.json."""
    return {
        'status': status,
        'confidence': round(float(confidence), 2),
        'source_refs': list(source_refs or []),
        'payload': payload,
    }


# --------------------------------------------------------------------------
# Fallback degradati (D1)
# --------------------------------------------------------------------------

# Un fallback non puo' inventare il contenuto che l'agente non ha prodotto: i
# payload completi hanno campi obbligatori (i passi del navigator, per esempio,
# devono essere almeno uno) che riempiti a mano sarebbero dati falsi. Quindi il
# degradato garantisce la busta - status, confidence, source_refs, payload - e
# dichiara nel payload perche' non c'e' contenuto. E' quello che l'orchestratore
# legge per decidere, e non contiene mai numeri fiscali.

MESSAGGIO_CAF = (
    'Non siamo riusciti a completare questo passaggio in modo affidabile. '
    'Per la tua situazione rivolgiti a un CAF o a un commercialista: '
    'il servizio di un CAF è spesso gratuito.'
)


def degradato(agente: str, motivo: str, *, status: str = 'degraded') -> dict:
    """Busta valida che dichiara il fallimento, senza inventare contenuto."""
    busta = envelope(
        {
            'agente': agente,
            'motivo_tecnico': motivo,
            'messaggio_per_la_persona': MESSAGGIO_CAF,
            'disclaimer': disclaimer(),
        },
        status=status,
        confidence=0.0,
        source_refs=[],
    )
    return busta


def degradato_eligibility(profilo_id: str, catalogo_versione: str, motivo: str,
                          spiegazione: str, *, status: str = 'hitl_required') -> dict:
    """Degradato di eligibility: qui il payload completo resta esprimibile,
    perche' 'nessuna misura proposta' e' un contenuto legittimo (escalation).

    Lo schema lo impone: con escalation a true lo status e' hitl_required e le
    misure pertinenti sono zero. Meta' risposta piu' un rimando e' la forma
    peggiore, e il contratto la vieta."""
    return envelope(
        {
            'profilo_id': profilo_id,
            'catalogo_versione': catalogo_versione,
            'misure_pertinenti': [],
            'misure_escluse': [],
            'escalation': True,
            # L'ambito dichiara che si ferma l'intera sessione, non una misura.
            'ambito_escalation': 'sessione',
            'motivo_escalation': motivo,
            'spiegazione_escalation': spiegazione,
            'disclaimer': disclaimer(),
        },
        status=status,
        confidence=0.0,
        source_refs=[],
    )
