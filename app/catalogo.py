"""Accesso al catalogo verificato: agents/state/catalogo.json.

Il catalogo e' il prodotto della Fase A (fase_a.py) e l'unica fonte di numeri
per la Fase B: percentuali, tetti e scadenze arrivano da qui, mai dalla memoria
del modello (G4). La Fase B lo legge da disco e non lo ricalcola mai (F1).
"""

import json
from typing import Any

from config import CATALOGO_PATH, assicura_state_dir
from validation import valida

VERSIONE_ASSENTE = '0.0.0'

_cache: dict[str, Any] = {'mtime': None, 'dati': None}


def carica() -> dict | None:
    """Catalogo da disco, con cache invalidata dalla data di modifica del file.

    Restituisce None se il catalogo non esiste: senza catalogo verificato la
    Fase B non parte e si rimanda a un CAF (regola di routing 1).
    """
    if not CATALOGO_PATH.exists():
        return None
    mtime = CATALOGO_PATH.stat().st_mtime
    if _cache['mtime'] == mtime and _cache['dati'] is not None:
        return _cache['dati']
    try:
        dati = json.loads(CATALOGO_PATH.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None
    _cache['mtime'] = mtime
    _cache['dati'] = dati
    return dati


def versione(catalogo: dict | None = None) -> str:
    cat = catalogo if catalogo is not None else carica()
    if not cat:
        return VERSIONE_ASSENTE
    ver = cat.get('versione') or VERSIONE_ASSENTE
    return ver


def salva(catalogo: dict) -> list[str]:
    """Scrive il catalogo dopo averlo validato contro agents/schemas/catalogo.json.

    Un catalogo non conforme non viene scritto: e' l'unico file che la Fase B
    considera verita'.
    """
    errori = valida('catalogo', catalogo)
    if errori:
        return errori
    assicura_state_dir()
    CATALOGO_PATH.write_text(
        json.dumps(catalogo, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    _cache['mtime'] = None
    return []


def voci(catalogo: dict | None = None) -> list[dict]:
    cat = catalogo if catalogo is not None else carica()
    if not cat:
        return []
    return cat.get('voci', [])


def misure_candidate(profilo: dict, catalogo: dict | None = None,
                     limite: int = 8) -> list[dict]:
    """Pre-filtro delle voci di catalogo sulle situazioni di vita del profilo.

    Serve a due cose: eligibility riceve solo cio' che gli serve (F2) e il
    filtro grossolano resta deterministico, fuori dal modello. Con 'non_so'
    passano tutte, come prescrive eligibility.input.json.
    """
    elenco = voci(catalogo)
    if not elenco:
        return []

    situazioni = set(profilo.get('situazioni_vita') or [])
    timing = profilo.get('timing')
    if 'non_so' in situazioni or not situazioni:
        candidate = list(elenco)
    else:
        candidate = [
            v for v in elenco
            if situazioni & set(v.get('misura', {}).get('situazioni_vita_collegate', []))
        ]

    if timing:
        compatibili = [
            v for v in candidate
            if timing in (v.get('misura', {}).get('timing_compatibile') or [timing])
        ]
        # Se il filtro sul timing azzera tutto, meglio lasciare decidere
        # eligibility che presentare un catalogo vuoto per un dettaglio.
        candidate = compatibili or candidate

    return candidate[:limite]


def voce_per_id(misura_id: str, catalogo: dict | None = None) -> dict | None:
    for v in voci(catalogo):
        if v.get('misura', {}).get('misura_id') == misura_id:
            return v
    return None
