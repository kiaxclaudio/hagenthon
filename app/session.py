"""Stato della sessione, su file, dove il repository dichiara che sta.

agents/ARCHITETTURA.md e agents/schemas/run-state.json vogliono lo stato fuori
dalla finestra di contesto (E3):

    agents/state/profilo.json     profilo della persona, tassonomia chiusa
    agents/state/run-<id>.json    passo, misure proposte, escalation

In memoria resta solo la trascrizione della chat, che non e' stato di agente ma
il testo che l'orchestratore ha gia' visto. Ogni scrittura di run-<id>.json e'
validata contro il suo schema: se lo stato non e' conforme, il file non viene
scritto e il difetto si vede subito.
"""

import json
import uuid
from pathlib import Path

import catalogo as catalogo_mod
from config import PROFILO_PATH, STATE_DIR, assicura_state_dir, run_path
from validation import ora, valida

# Solo la conversazione: {run_id: [{'role':..., 'content':...}, ...]}
_conversazioni: dict[str, list[dict]] = {}

PASSI = ('situazione_vita', 'profilo_base', 'timing', 'scheda_misure',
         'come_accedere', 'chiusa')


def _stato_iniziale(run_id: str) -> dict:
    return {
        'run_id': run_id,
        'profilo_id': f'profilo-{run_id}',
        'catalogo_versione': catalogo_mod.versione(),
        'creato_il': ora(),
        'aggiornato_il': ora(),
        'stato_sessione': 'in_corso',
        'passo_corrente': 'situazione_vita',
        'passi_completati': [],
        'misure_proposte': [],
        'escalation': {'attiva': False},
        'tentativi_timeout_modello': 0,
        'ultimo_status': 'ok',
    }


def _scrivi_stato(stato: dict) -> list[str]:
    """Valida e scrive agents/state/run-<id>.json."""
    errori = valida('run-state', stato)
    if errori:
        print(f"[stato] run-{stato.get('run_id')} non conforme, non scritto: {errori[0]}")
        return errori
    assicura_state_dir()
    run_path(stato['run_id']).write_text(
        json.dumps(stato, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    return []


def _leggi_stato(run_id: str) -> dict | None:
    percorso = run_path(run_id)
    if not percorso.exists():
        return None
    try:
        return json.loads(percorso.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None


def create_session() -> str:
    run_id = str(uuid.uuid4())[:8]
    _conversazioni[run_id] = []
    _scrivi_stato(_stato_iniziale(run_id))
    return run_id


def get_session(session_id: str) -> dict | None:
    """Sessione completa: stato da disco piu' la conversazione in memoria."""
    stato = _leggi_stato(session_id)
    if stato is None:
        return None
    return {
        'id': session_id,
        'stato': stato,
        'conversation_history': _conversazioni.get(session_id, []),
    }


def get_or_create_session(session_id: str | None) -> tuple[str, dict]:
    if session_id:
        sessione = get_session(session_id)
        if sessione:
            _conversazioni.setdefault(session_id, [])
            return session_id, sessione
    nuovo = create_session()
    return nuovo, get_session(nuovo)


def add_message(session_id: str, role: str, content: str) -> None:
    _conversazioni.setdefault(session_id, []).append({'role': role, 'content': content})


def conversazione(session_id: str) -> list[dict]:
    return _conversazioni.get(session_id, [])


def salva_profilo(session_id: str, profilo: dict) -> None:
    """Scrive agents/state/profilo.json e aggiorna il passo della sessione."""
    assicura_state_dir()
    PROFILO_PATH.write_text(
        json.dumps(profilo, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    stato = _leggi_stato(session_id) or _stato_iniziale(session_id)
    stato['profilo_id'] = profilo.get('profilo_id') or stato['profilo_id']
    stato['passo_corrente'] = 'profilo_base'
    if 'situazione_vita' not in stato['passi_completati']:
        stato['passi_completati'].append('situazione_vita')
    stato['aggiornato_il'] = ora()
    _scrivi_stato(stato)


def salva_esito(session_id: str, esito: dict) -> None:
    """Riporta nello stato l'esito della Fase B: misure proposte o escalation."""
    stato = _leggi_stato(session_id) or _stato_iniziale(session_id)
    stato['catalogo_versione'] = esito.get('catalogo_versione', stato['catalogo_versione'])
    stato['ultimo_status'] = esito.get('status', 'ok')
    stato['aggiornato_il'] = ora()

    if esito.get('escalation'):
        stato['stato_sessione'] = 'hitl_escalated'
        stato['passo_corrente'] = 'chiusa'
        stato['escalation'] = {
            'attiva': True,
            'motivo': esito.get('motivo_escalation') or 'caso_non_coperto_dal_catalogo',
            'attivata_il': ora(),
            'messaggio_mostrato': (esito.get('messaggio_escalation') or '')[:600],
        }
    else:
        proposte = []
        pertinenti = esito.get('eligibility', {}).get('payload', {}).get('misure_pertinenti', [])
        guidate = {
            u.get('payload', {}).get('misura_id') for u in (esito.get('navigator') or [])
        }
        for misura in pertinenti:
            proposte.append({
                'misura_id': misura.get('misura_id'),
                'nome': misura.get('nome'),
                'proposta_il': ora(),
                'passi_generati': misura.get('misura_id') in guidate,
            })
        stato['misure_proposte'] = proposte
        stato['stato_sessione'] = 'completata'
        stato['passo_corrente'] = 'come_accedere'
        for passo in ('profilo_base', 'scheda_misure'):
            if passo not in stato['passi_completati']:
                stato['passi_completati'].append(passo)

    _scrivi_stato(stato)


def registra_degrado(session_id: str) -> None:
    """Conta i fallimenti tecnici della sessione (campo tentativi_timeout_modello)."""
    stato = _leggi_stato(session_id) or _stato_iniziale(session_id)
    stato['tentativi_timeout_modello'] = min(3, stato.get('tentativi_timeout_modello', 0) + 1)
    stato['ultimo_status'] = 'degraded'
    stato['aggiornato_il'] = ora()
    _scrivi_stato(stato)


def save_stage(session_id: str, stage: str, data: dict) -> None:
    """Punto unico di salvataggio usato dalle rotte (nome storico mantenuto)."""
    if stage == 'profile':
        salva_profilo(session_id, data)
    elif stage == 'pipeline':
        salva_esito(session_id, data)


def reset_session(session_id: str) -> str:
    """Chiude la sessione corrente e ne apre una nuova."""
    stato = _leggi_stato(session_id) if session_id else None
    if stato and stato.get('stato_sessione') == 'in_corso':
        stato['stato_sessione'] = 'abbandonata'
        stato['aggiornato_il'] = ora()
        _scrivi_stato(stato)
    _conversazioni.pop(session_id, None)
    return create_session()


def percorsi_stato() -> dict[str, Path]:
    """Dove sta lo stato: usato dalla diagnostica e dal README."""
    return {'stato': STATE_DIR, 'profilo': PROFILO_PATH}
