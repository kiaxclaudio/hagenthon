import json
import uuid
from datetime import datetime
from pathlib import Path

LOGS_DIR = Path(__file__).parent / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

_sessions: dict = {}


def create_session() -> str:
    session_id = str(uuid.uuid4())[:8]
    _sessions[session_id] = {
        'id': session_id,
        'created_at': datetime.now().isoformat(),
        'conversation_history': [],
        'profile': None,
        'eligibility': None,
        'explainer': None,
        'navigator': None,
        'stage': 'chat',
    }
    return session_id


def get_session(session_id: str) -> dict | None:
    return _sessions.get(session_id)


def get_or_create_session(session_id: str | None) -> tuple[str, dict]:
    if session_id and session_id in _sessions:
        return session_id, _sessions[session_id]
    new_id = create_session()
    return new_id, _sessions[new_id]


def add_message(session_id: str, role: str, content: str):
    session = _sessions.get(session_id)
    if session:
        session['conversation_history'].append({'role': role, 'content': content})


def save_stage(session_id: str, stage: str, data: dict):
    session = _sessions.get(session_id)
    if session:
        session[stage] = data
        session['stage'] = stage
        _persist(session_id)


def _persist(session_id: str):
    session = _sessions.get(session_id)
    if not session:
        return
    path = LOGS_DIR / f'{session_id}.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(session, f, ensure_ascii=False, indent=2)


def reset_session(session_id: str) -> str:
    if session_id in _sessions:
        del _sessions[session_id]
    return create_session()
