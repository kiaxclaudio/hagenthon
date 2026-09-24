"""
Hook Stop: scrive un log della sessione corrente in logs/.
"""
import json
import os
from datetime import datetime
from pathlib import Path

LOGS_DIR = Path(__file__).parent.parent / 'logs'
APP_LOGS_DIR = Path(__file__).parent.parent / 'app' / 'logs'

def main():
    LOGS_DIR.mkdir(exist_ok=True)

    session_files = sorted(APP_LOGS_DIR.glob('*.json')) if APP_LOGS_DIR.exists() else []

    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'session_files': [str(f.name) for f in session_files],
        'session_count': len(session_files),
    }

    if session_files:
        latest = session_files[-1]
        try:
            with open(latest, encoding='utf-8') as f:
                log_entry['latest_session'] = json.load(f)
        except Exception:
            log_entry['latest_session'] = None

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_path = LOGS_DIR / f'session_{ts}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(log_entry, f, ensure_ascii=False, indent=2)

    print(f'[LOG] Sessione salvata in {out_path}')

if __name__ == '__main__':
    main()
