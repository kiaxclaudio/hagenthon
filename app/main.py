import os
from flask import Flask, jsonify, render_template, request, session

from agents import call_orchestrator, run_full_pipeline
from session import add_message, get_or_create_session, reset_session, save_stage

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'hackathon-secret-2024')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    session_id = data.get('session_id')

    session_id, sess = get_or_create_session(session_id)
    add_message(session_id, 'user', user_message)

    try:
        result = call_orchestrator(sess['conversation_history'])
        assistant_text = result['text']
        add_message(session_id, 'assistant', assistant_text)

        response = {
            'session_id': session_id,
            'message': assistant_text,
            'stage': 'chat',
            'pipeline': None,
        }

        if result.get('profile'):
            profile = result['profile']
            save_stage(session_id, 'profile', profile)

            if profile.get('escalation'):
                response['stage'] = 'escalation'
                response['escalation_message'] = profile.get('motivo_escalation') or 'La tua situazione richiede una consulenza personalizzata. Rivolgiti a un CAF.'
            else:
                pipeline = run_full_pipeline(profile)
                save_stage(session_id, 'pipeline', pipeline)
                response['stage'] = 'results' if not pipeline.get('escalation') else 'escalation'
                response['pipeline'] = pipeline
                if pipeline.get('escalation'):
                    response['escalation_message'] = pipeline.get('messaggio_escalation', '')

        return jsonify(response)

    except Exception as e:
        return jsonify({
            'session_id': session_id,
            'message': 'Si è verificato un errore. Riprova o contatta un CAF per assistenza.',
            'stage': 'error',
            'error': str(e),
        }), 500


@app.route('/api/reset', methods=['POST'])
def reset():
    data = request.get_json() or {}
    old_id = data.get('session_id')
    new_id = reset_session(old_id) if old_id else None
    from session import create_session
    if not new_id:
        new_id = create_session()
    return jsonify({'session_id': new_id})


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session_state(session_id):
    from session import get_session
    sess = get_session(session_id)
    if not sess:
        return jsonify({'error': 'Session not found'}), 404
    return jsonify({k: v for k, v in sess.items() if k != 'conversation_history'})


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    print(f'Avvio su http://localhost:{port}')
    app.run(host='0.0.0.0', port=port, debug=debug)
