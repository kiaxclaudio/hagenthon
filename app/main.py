"""Rotte dell'applicazione. Le stesse di prima, con un comportamento in piu':

quando il modello non risponde o un contratto non e' rispettato, la rotta non
restituisce 500 ma un esito degradato con `status: "degraded"` e il rimando a un
CAF. Un servizio pubblico che si rompe deve dire alla persona cosa fare (D1).
"""

import os
import secrets

from flask import Flask, jsonify, render_template, request

import catalogo as catalogo_mod
import demo
from agents import (
    avanza_questionario,
    domande_poste,
    esegui_profilazione,
    run_full_pipeline,
    vista_interfaccia,
)
from config import DEMO_MODE, MODELLI_PER_TIER, TIER_PER_AGENTE
from session import (
    add_message,
    conversazione,
    create_session,
    get_or_create_session,
    get_session,
    registra_degrado,
    reset_session,
    save_stage,
)
from validation import MESSAGGIO_CAF, disclaimer

app = Flask(__name__)
# Nessun segreto nel codice: se FLASK_SECRET_KEY manca, se ne genera uno a ogni
# avvio (le sessioni non sopravvivono al riavvio, ed e' accettabile qui).
app.secret_key = os.getenv('FLASK_SECRET_KEY') or secrets.token_hex(32)

# Risposte raccolte per sessione. Non sono stato di agente - il profilo, quello
# si', sta in agents/state/profilo.json (E3) - sono le caselle del questionario
# in attesa di essere normalizzate dal profiler.
_risposte_sessione: dict[str, dict] = {}


@app.route('/')
def index():
    return render_template('index.html')


def _risposta_degradata(session_id: str, messaggio: str, motivo: str) -> dict:
    """Forma unica delle uscite degradate: l'interfaccia ne legge sempre una sola."""
    registra_degrado(session_id)
    return {
        'session_id': session_id,
        'message': messaggio,
        'stage': 'escalation',
        'status': 'degraded',
        'escalation_message': MESSAGGIO_CAF,
        'motivo_escalation': motivo,
        'disclaimer': disclaimer(),
        'pipeline': None,
    }


@app.route('/api/chat', methods=['POST'])
def chat():
    dati = request.get_json(silent=True) or {}
    messaggio_utente = str(dati.get('message', '')).strip()
    session_id = dati.get('session_id')

    session_id, _ = get_or_create_session(session_id)

    # Un messaggio vuoto non e' un errore: e' l'apertura della sessione, ed e'
    # il momento in cui va posta la PRIMA domanda. Rispondere "scrivi qualcosa"
    # qui era il modo in cui la domanda su cui si regge tutto il resto -
    # la situazione di vita - spariva dal percorso.
    raccolte = _risposte_sessione.get(session_id, {})
    if messaggio_utente:
        add_message(session_id, 'user', messaggio_utente)

    try:
        # Passo 1: il questionario. Cinque domande fisse, nell'ordine della
        # specifica, con le etichette di agents/subagents/profiler.md. Nessuna
        # chiamata al modello: una domanda generata a ogni sessione cambia
        # parole, salta un passo e non e' riproducibile in collaudo.
        turno = avanza_questionario(raccolte, messaggio_utente or None)
        _risposte_sessione[session_id] = turno['risposte']
        add_message(session_id, 'assistant', turno['testo'])

        risposta = {
            'session_id': session_id,
            'message': turno['testo'],
            'stage': 'chat',
            'status': 'ok',
            'pipeline': None,
            'disclaimer': disclaimer(),
            # Le opzioni viaggiano anche strutturate: chi disegna l'interfaccia
            # fa dei bottoni invece di far digitare a mano una persona che ha
            # gia' abbastanza da fare.
            'domanda_id': turno['domanda_id'],
            'opzioni': turno['opzioni'],
            # Il contatore riflette le domande previste per QUESTO percorso:
            # una condizionale che non si pone non si conta.
            'numero_domanda': turno['numero_domanda'],
            'totale_domande': turno['totale_domande'],
        }

        if not turno['completo']:
            return jsonify(risposta), 200

        # Passo 2: profiler normalizza le risposte sulla tassonomia chiusa.
        profilo, escalation = esegui_profilazione(
            session_id, turno['risposte'], domande_poste(turno['risposte'])
        )
        if escalation is not None:
            save_stage(session_id, 'pipeline', escalation)
            risposta.update({
                'stage': 'escalation',
                'status': escalation['status'],
                'escalation_message': escalation['messaggio_escalation'],
                'motivo_escalation': escalation['motivo_escalation'],
            })
            return jsonify(risposta), 200

        save_stage(session_id, 'profile', profilo)

        # Passo 3: Fase B completa, con i suoi gate.
        esito = run_full_pipeline(profilo, session_id)
        save_stage(session_id, 'pipeline', esito)

        risposta['pipeline'] = vista_interfaccia(esito)
        risposta['status'] = esito.get('status', 'ok')
        if esito.get('escalation'):
            risposta['stage'] = 'escalation'
            risposta['escalation_message'] = esito.get('messaggio_escalation', '')
            risposta['motivo_escalation'] = esito.get('motivo_escalation')
        else:
            risposta['stage'] = 'results'
        return jsonify(risposta), 200

    except Exception as errore:  # rete, disco, contratto: nessuna 500 in faccia alla persona
        app.logger.exception('errore non previsto su /api/chat')
        return jsonify(_risposta_degradata(
            session_id,
            'Si è verificato un problema tecnico. ' + MESSAGGIO_CAF,
            f'{type(errore).__name__}',
        )), 200


@app.route('/api/reset', methods=['POST'])
def reset():
    dati = request.get_json(silent=True) or {}
    vecchio = dati.get('session_id')
    nuovo = reset_session(vecchio) if vecchio else create_session()
    return jsonify({'session_id': nuovo, 'disclaimer': disclaimer()})


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session_state(session_id):
    sessione = get_session(session_id)
    if not sessione:
        return jsonify({'error': 'Session not found'}), 404
    # Lo stato e' quello su disco: la rotta lo rilegge, non tiene una copia.
    return jsonify(sessione['stato'])


@app.route('/api/diagnostica', methods=['GET'])
def diagnostica():
    """Stato della configurazione, senza segreti: utile in demo e in collaudo."""
    catalogo = catalogo_mod.carica()
    return jsonify({
        'chiave_api_configurata': bool(os.getenv('ANTHROPIC_API_KEY')),
        'demo_mode': DEMO_MODE,
        'scenari_demo': demo.elenco_scenari() if DEMO_MODE else [],
        'tier_per_agente': TIER_PER_AGENTE,
        'modelli_per_tier': MODELLI_PER_TIER,
        'catalogo_presente': catalogo is not None,
        'catalogo_versione': catalogo_mod.versione(catalogo),
        'voci_catalogo': len(catalogo_mod.voci(catalogo)),
    })


if __name__ == '__main__':
    porta = int(os.getenv('FLASK_PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    print(f'Avvio su http://localhost:{porta}')
    app.run(host='127.0.0.1', port=porta, debug=debug)
