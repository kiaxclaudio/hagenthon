import json
import os
import re
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'), timeout=60.0)

ORCHESTRATOR_MODEL = 'claude-haiku-4-5'
ANALYSIS_MODEL = 'claude-sonnet-4-6'

AGENTS_DIR = Path(__file__).parent.parent / '.claude' / 'agents'

_prompt_cache: dict[str, str] = {}


def _load_prompt(agent_name: str) -> str:
    if agent_name in _prompt_cache:
        return _prompt_cache[agent_name]
    path = AGENTS_DIR / f'{agent_name}.md'
    text = path.read_text(encoding='utf-8')
    # strip YAML frontmatter (--- ... ---)
    if text.startswith('---'):
        end = text.find('---', 3)
        text = text[end + 3:].lstrip()
    _prompt_cache[agent_name] = text
    return text


def _extract_json(text: str) -> dict:
    """Extract first JSON object from text, even if surrounded by prose."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise ValueError('No JSON object found in response')
    return json.loads(match.group())


def _call_with_retry(model: str, system: str, messages: list, max_retries: int = 2) -> str:
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=4096,
                system=system,
                messages=messages,
            )
            return resp.content[0].text
        except Exception as e:
            last_error = e
            if attempt == max_retries:
                raise
    raise last_error


def call_orchestrator(conversation_history: list) -> dict:
    """
    Multi-turn conversation with orchestrator.
    Returns {'text': str, 'profile': dict|None}
    profile is set when the orchestrator outputs the final JSON.
    """
    system = _load_prompt('orchestrator')
    text = _call_with_retry(ORCHESTRATOR_MODEL, system, conversation_history)

    profile = None
    try:
        candidate = _extract_json(text)
        if 'situazione_vita' in candidate:
            profile = candidate
    except (ValueError, json.JSONDecodeError):
        pass

    return {'text': text, 'profile': profile}


def call_eligibility(user_profile: dict) -> dict:
    system = _load_prompt('eligibility')
    messages = [{'role': 'user', 'content': json.dumps(user_profile, ensure_ascii=False)}]

    for attempt in range(3):
        try:
            text = _call_with_retry(ANALYSIS_MODEL, system, messages)
            result = _extract_json(text)
            if 'bonus' in result:
                return result
            raise ValueError('Missing bonus field')
        except (ValueError, json.JSONDecodeError):
            if attempt < 2:
                messages.append({'role': 'assistant', 'content': text})
                messages.append({
                    'role': 'user',
                    'content': 'Il tuo output precedente non era JSON valido secondo lo schema richiesto. Restituisci SOLO il JSON, nessun testo aggiuntivo.',
                })

    return {
        'profilo_riassunto': 'errore',
        'bonus': [],
        'avvertenza': 'Non è stato possibile analizzare il profilo. Rivolgiti a un CAF.',
        'error': True,
    }


def call_explainer(bonus_list: dict) -> dict:
    system = _load_prompt('explainer')
    messages = [{'role': 'user', 'content': json.dumps(bonus_list, ensure_ascii=False)}]

    for attempt in range(3):
        try:
            text = _call_with_retry(ANALYSIS_MODEL, system, messages)
            result = _extract_json(text)
            if 'spiegazioni' in result:
                return result
            raise ValueError('Missing spiegazioni field')
        except (ValueError, json.JSONDecodeError):
            if attempt < 2:
                messages.append({'role': 'assistant', 'content': text})
                messages.append({
                    'role': 'user',
                    'content': 'Il tuo output precedente non era JSON valido. Restituisci SOLO il JSON secondo lo schema.',
                })

    return {'error': True, 'messaggio': 'Non è stato possibile elaborare le spiegazioni. Rivolgiti a un CAF.'}


def call_navigator(explanations: dict) -> dict:
    system = _load_prompt('navigator')
    messages = [{'role': 'user', 'content': json.dumps(explanations, ensure_ascii=False)}]

    for attempt in range(3):
        try:
            text = _call_with_retry(ORCHESTRATOR_MODEL, system, messages)
            result = _extract_json(text)
            if 'percorsi' in result:
                return result
            raise ValueError('Missing percorsi field')
        except (ValueError, json.JSONDecodeError):
            if attempt < 2:
                messages.append({'role': 'assistant', 'content': text})
                messages.append({
                    'role': 'user',
                    'content': 'Il tuo output precedente non era JSON valido. Restituisci SOLO il JSON secondo lo schema.',
                })

    return {'error': True, 'messaggio': 'Non è stato possibile generare le istruzioni. Rivolgiti a un CAF.'}


def run_full_pipeline(user_profile: dict) -> dict:
    """Run eligibility → explainer → navigator in sequence."""
    eligibility = call_eligibility(user_profile)

    if eligibility.get('error') or not eligibility.get('bonus'):
        return {
            'eligibility': eligibility,
            'explainer': None,
            'navigator': None,
            'escalation': True,
            'messaggio_escalation': 'Non è stato possibile identificare i bonus. Ti consigliamo di rivolgerti a un CAF.',
        }

    # Check if all bonuses have low relevance — trigger HITL
    all_low = all(b.get('rilevanza') == 'bassa' for b in eligibility.get('bonus', []))
    if all_low:
        return {
            'eligibility': eligibility,
            'explainer': None,
            'navigator': None,
            'escalation': True,
            'messaggio_escalation': 'Per la tua situazione specifica non emergono bonus certi. Ti consigliamo di parlare con un CAF per una valutazione personalizzata.',
        }

    explainer = call_explainer(eligibility)
    if explainer.get('error'):
        return {
            'eligibility': eligibility,
            'explainer': explainer,
            'navigator': None,
            'escalation': True,
            'messaggio_escalation': explainer.get('messaggio', 'Errore nella spiegazione. Rivolgiti a un CAF.'),
        }

    navigator = call_navigator(explainer)

    return {
        'eligibility': eligibility,
        'explainer': explainer,
        'navigator': navigator,
        'escalation': navigator.get('error', False),
        'messaggio_escalation': navigator.get('messaggio') if navigator.get('error') else None,
    }
