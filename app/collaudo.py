"""Collaudo offline: verifica che i meccanismi non funzionali facciano quello che dichiarano.

Non chiama il modello e non usa la rete: le risposte degli agenti sono finte e
messe in coda, cosi' si puo' provocare a comando un output fuori schema, una
bocciatura del fidelity-validator o una confidenza sotto soglia.

I dati fiscali qui dentro sono inventati e marcati come tali: servono a far
scattare i gate, non sono un catalogo. Il catalogo vero lo costruisce fase_a.py
dalle fonti ufficiali.

Uso:
    python app/collaudo.py
"""

import json
import sys

import agents
import catalogo as catalogo_mod
import config
import session as sessione_mod
from validation import disclaimer, valida, valida_envelope, valida_output

# const di agents/schemas/navigator.output.json
TESTO_SPID_COLLAUDO = "Non hai ancora lo SPID? Puoi attivarlo presso uno sportello di Poste Italiane, in una banca abilitata oppure da app. Ti servono un documento d'identità valido e il tuo numero di telefono. L'attivazione è gratuita."

ESITI: list[tuple[bool, str]] = []


def verifica(condizione: bool, descrizione: str, dettaglio: str = '') -> None:
    ESITI.append((bool(condizione), descrizione))
    segno = 'OK  ' if condizione else 'FAIL'
    print(f'[{segno}] {descrizione}' + (f'\n       {dettaglio}' if dettaglio else ''))


# --------------------------------------------------------------------------
# Dati finti, riconoscibili
# --------------------------------------------------------------------------

MISURA_FINTA = {
    'misura_id': 'misura-di-collaudo',
    'nome': 'Misura di collaudo (dato non reale)',
    'tipo': 'detrazione',
    'descrizione_fonte': 'Testo di collaudo, non proveniente da una fonte ufficiale.',
    'anno_riferimento': 2026,
    'beneficio': {'tipo_beneficio': 'percentuale', 'percentuale': 1.0,
                  'source_refs': ['collaudo#par-1']},
    'requisiti': [],
    'documenti_richiesti': [],
    'canali_accesso': ['caf'],
    'situazioni_vita_collegate': ['casa'],
    'timing_compatibile': ['da_iniziare'],
    'dati_mancanti': [],
    'source_refs': ['collaudo#par-1'],
}

SPIEGAZIONE_FINTA = {
    'misura_id': 'misura-di-collaudo',
    'titolo_semplice': 'Misura di collaudo',
    'cosa_e': 'Voce di prova usata solo per il collaudo tecnico.',
    'quanto_vale': 'Valore di prova, non utilizzabile.',
    'a_chi_spetta': ['Nessuno: è una voce di collaudo.'],
    'attenzione': [],
    'glossario': [],
    'iterazione': 1,
    'disclaimer': disclaimer(),
    'source_refs': ['collaudo#par-1'],
}

CATALOGO_FINTO = {
    'catalogo_id': 'catalogo-di-collaudo',
    'versione': '0.0.1',
    'generato_il': '2026-01-01T00:00:00+00:00',
    'anno_imposta_riferimento': 2026,
    'fonti': [{'fonte_id': 'collaudo', 'ente': 'altro_ente_pubblico',
               'data_consultazione': '2026-01-01'}],
    'voci': [{
        'misura': MISURA_FINTA,
        'spiegazione': SPIEGAZIONE_FINTA,
        'verifica': {'verdict': 'approved', 'iterazioni': 1,
                     'validato_il': '2026-01-01T00:00:00+00:00',
                     'confidence': 0.9, 'divergenze_residue': []},
        'pubblicata_il': '2026-01-01T00:00:00+00:00',
    }],
    'misure_escluse': [],
}

PROFILO_FINTO = {
    'profilo_id': 'profilo-collaudo',
    'creato_il': '2026-01-01T00:00:00+00:00',
    'situazioni_vita': ['casa'],
    'condizione_abitativa': 'proprietario',
    'tipo_reddito': 'lavoro_dipendente',
    'timing': 'da_iniziare',
    'caf': 'no',
    'termini_non_noti': [],
    'completo': True,
    'risposte_mancanti': [],
}


def busta(payload: dict, status: str = 'ok', confidence: float = 0.9) -> str:
    return json.dumps({'status': status, 'confidence': confidence,
                       'source_refs': ['collaudo#par-1'], 'payload': payload},
                      ensure_ascii=False)


class ModelloFinto:
    """Sostituisce agents._chiama: restituisce le risposte in coda e le conta."""

    def __init__(self, risposte: list[str]):
        self.risposte = list(risposte)
        self.chiamate: list[str] = []

    def __call__(self, agente, messaggi, sistema):
        self.chiamate.append(agente)
        if not self.risposte:
            raise agents.ErroreModello('coda esaurita', motivo='collaudo', ritentabile=False)
        return self.risposte.pop(0)


def con_modello(risposte: list[str]) -> ModelloFinto:
    finto = ModelloFinto(risposte)
    agents._chiama = finto
    return finto


# --------------------------------------------------------------------------
# 1. Model tiering
# --------------------------------------------------------------------------

def prova_tiering() -> None:
    print('\n--- model tiering -------------------------------------------------')
    attesi = {
        'orchestrator': 'haiku', 'profiler': 'haiku', 'navigator': 'haiku',
        'explainer': 'sonnet', 'eligibility': 'sonnet',
        'source-analyzer': 'opus', 'fidelity-validator': 'opus',
    }
    verifica(config.TIER_PER_AGENTE == attesi,
             'la mappa agente -> tier coincide con agents/ARCHITETTURA.md')
    verifica(len(set(config.MODELLI_PER_TIER.values())) == 3,
             'i tre tier puntano a tre modelli distinti',
             json.dumps(config.MODELLI_PER_TIER, ensure_ascii=False))
    verifica(all(config.modello_di(a) for a in attesi),
             'ogni agente risolve il proprio identificativo di modello')
    verifica(config.modello_di('fidelity-validator') != config.modello_di('explainer'),
             'chi verifica le cifre non e\' lo stesso tier di chi le ha scritte')


# --------------------------------------------------------------------------
# 2. Retry, backoff e classificazione degli errori
# --------------------------------------------------------------------------

def prova_retry() -> None:
    print('\n--- retry e backoff -----------------------------------------------')
    import anthropic

    def errore(nome, **kwargs):
        classe = getattr(anthropic, nome)
        return classe.__new__(classe)

    ritentabile = agents._classifica(errore('APITimeoutError'))
    fatale = agents._classifica(errore('AuthenticationError'))
    verifica(ritentabile.ritentabile, 'un timeout viene ritentato')
    verifica(not fatale.ritentabile,
             'un errore di autenticazione NON viene ritentato e fallisce subito')

    attese: list[float] = []
    originale_sleep = agents.time.sleep
    agents.time.sleep = attese.append
    chiamate = {'n': 0}

    def sempre_in_timeout(*_a, **_k):
        chiamate['n'] += 1
        raise agents.ErroreModello('timeout finto', motivo='temporaneo', ritentabile=True)

    client_originale = agents._client_anthropic
    agents._client_anthropic = sempre_in_timeout
    try:
        agents._chiama('navigator', [{'role': 'user', 'content': 'x'}], 'sistema')
        esito = 'nessuna eccezione'
    except agents.ErroreModello:
        esito = 'ErroreModello'
    finally:
        agents.time.sleep = originale_sleep
        agents._client_anthropic = client_originale

    verifica(esito == 'ErroreModello' and chiamate['n'] == config.MAX_RETRY + 1,
             f'i tentativi si fermano a LLM_MAX_RETRIES ({config.MAX_RETRY}) + 1',
             f'tentativi: {chiamate["n"]}, attese: {[round(a, 2) for a in attese]}')
    verifica(len(attese) == config.MAX_RETRY and all(
        attese[i] < attese[i + 1] * 2.5 for i in range(len(attese) - 1)),
        'fra un tentativo e l\'altro c\'e\' un\'attesa crescente (backoff esponenziale)')


# --------------------------------------------------------------------------
# 3. Validazione di schema e ri-richiesta
# --------------------------------------------------------------------------

def prova_validazione() -> None:
    print('\n--- validazione contro gli schemi ---------------------------------')
    finto = con_modello(['non sono JSON', '{"status":"ok"}'])
    uscita = agents.esegui_agente('navigator', {'prova': True})
    verifica(len(finto.chiamate) == 2,
             'output non conforme: una sola ri-richiesta, non tre',
             f'chiamate al modello: {len(finto.chiamate)}')
    verifica(uscita['status'] == 'degraded',
             'dopo la ri-richiesta fallita l\'uscita e\' status degraded')
    verifica(valida_envelope(uscita) == [],
             'anche l\'uscita degradata rispetta la busta status/confidence/source_refs/payload')

    finto = con_modello([busta({
        'misura_id': 'misura-di-collaudo',
        'primo_passo_concreto': 'Prenota un appuntamento al CAF.',
        'passi': [{'ordine': 1, 'azione': 'Prenota un appuntamento al CAF.',
                   'dove': 'caf', 'documenti_necessari': ['documento_identita'],
                   'dipende_da': [], 'source_refs': ['collaudo#par-1']}],
        'documenti_necessari': [], 'glossario': [], 'disclaimer': disclaimer(),
        'riquadro_spid': {'necessario': False, 'testo': TESTO_SPID_COLLAUDO},
    })])
    uscita = agents.esegui_agente('navigator', {'prova': True})
    verifica(valida_output('navigator', uscita) == [],
             'un output conforme passa la validazione e viene usato cosi\' com\'e\'')


# --------------------------------------------------------------------------
# 4. Gate HITL della Fase B
# --------------------------------------------------------------------------

def prova_gate_fase_b() -> None:
    print('\n--- gate HITL della Fase B ----------------------------------------')
    carica_originale = catalogo_mod.carica

    # Gate 1: caso non coperto dal catalogo.
    catalogo_mod.carica = lambda: None
    con_modello([])
    esito = agents.run_full_pipeline(PROFILO_FINTO)
    verifica(esito['escalation'] and esito['motivo_escalation'] == 'caso_non_coperto_dal_catalogo',
             'catalogo assente: si rimanda al CAF invece di rispondere')
    verifica('CAF' in esito['messaggio_escalation'],
             'il messaggio di escalation nomina il CAF')

    # Gate 2: confidenza sotto 0.6.
    catalogo_mod.carica = lambda: CATALOGO_FINTO
    con_modello([busta({
        'profilo_id': 'profilo-collaudo', 'catalogo_versione': '0.0.1',
        'misure_pertinenti': [], 'misure_escluse': [], 'escalation': True,
        'ambito_escalation': 'sessione', 'motivo_escalation': 'confidence_bassa',
        'spiegazione_escalation': 'Il caso non e\' abbastanza chiaro da qui.',
        'disclaimer': disclaimer(),
    }, status='hitl_required', confidence=0.4)])
    esito = agents.run_full_pipeline(PROFILO_FINTO)
    verifica(esito['escalation'] and esito['motivo_escalation'] == 'confidence_bassa',
             f'confidence 0.4 < {config.SOGLIA_CONFIDENCE}: escalation, nessuna misura proposta')
    verifica(esito['eligibility']['payload']['misure_pertinenti'] == [],
             'con la confidenza sotto soglia la lista delle misure resta vuota')

    # Percorso completo: eligibility propone, navigator compone i passi.
    eligibility_ok = busta({
        'profilo_id': 'profilo-collaudo', 'catalogo_versione': '0.0.1',
        'misure_pertinenti': [{
            'misura_id': 'misura-di-collaudo',
            'nome': 'Misura di collaudo (dato non reale)',
            'titolo_semplice': 'Misura di collaudo',
            'tipo': 'detrazione',
            'confidence': 0.85,
            'motivazione': 'Il profilo indica la situazione casa.',
            'corrispondenze_profilo': ['situazione_vita'],
            'requisiti_da_verificare': [],
            'source_refs': ['collaudo#par-1'],
        }],
        'misure_escluse': [], 'escalation': False, 'disclaimer': disclaimer(),
    })
    navigator_ok = busta({
        'misura_id': 'misura-di-collaudo',
        'primo_passo_concreto': 'Prenota un appuntamento al CAF.',
        'passi': [{'ordine': 1, 'azione': 'Prenota un appuntamento al CAF.',
                   'dove': 'caf', 'documenti_necessari': ['spid_cie_cns'],
                   'dipende_da': [], 'source_refs': ['collaudo#par-1']}],
        'documenti_necessari': [], 'glossario': [], 'disclaimer': disclaimer(),
        'riquadro_spid': {'necessario': False, 'testo': TESTO_SPID_COLLAUDO},
    })
    con_modello([eligibility_ok, navigator_ok])
    esito = agents.run_full_pipeline(PROFILO_FINTO)
    verifica(not esito['escalation'] and esito['status'] == 'ok',
             'percorso completo: eligibility propone e navigator compone i passi')

    vista = agents.vista_interfaccia(esito)
    scheda = vista['explainer']['spiegazioni'][0]
    verifica(scheda['disclaimer'] == disclaimer(),
             'ogni scheda mostrata porta il disclaimer del contratto (G2)')
    verifica(bool(scheda['source_refs']),
             'ogni scheda mostrata porta i riferimenti alla fonte (G5)')
    verifica(vista['navigator']['percorsi'][0]['passi'][0]['numero'] == 1,
             'i passi arrivano all\'interfaccia nella forma che disegna')

    catalogo_mod.carica = carica_originale


# --------------------------------------------------------------------------
# 5. Limite di iterazione della Fase A
# --------------------------------------------------------------------------

def prova_limite_fase_a() -> None:
    print('\n--- limite explainer <-> fidelity-validator ------------------------')
    import fase_a

    divergenza = {
        'tipo': 'numero_cambiato',
        'categoria_dato': 'percentuale',
        'gravita': 'bloccante',
        'campo': '/quanto_vale',
        'testo_originale': 'valore di prova A',
        'testo_semplificato': 'valore di prova B',
        'descrizione': 'D-01 numero di prova diverso da quello della fonte di collaudo.',
    }
    spiegazione = busta(SPIEGAZIONE_FINTA)

    def rifiuto(giro: int) -> str:
        # Alla seconda bocciatura il contratto impone hitl_required ed esclusa_hitl.
        return busta({
            'misura_id': 'misura-di-collaudo', 'verdict': 'rejected', 'iterazione': giro,
            'inventario_completato': True, 'divergenze': [divergenza],
            'esito_misura': 'da_riscrivere' if giro == 1 else 'esclusa_hitl',
        }, status='ok' if giro == 1 else 'hitl_required')

    finto = con_modello([spiegazione, rifiuto(1), spiegazione, rifiuto(2),
                         spiegazione, rifiuto(2)])
    voce, esclusione = fase_a.costruisci_voce(MISURA_FINTA)

    verifica(voce is None and esclusione is not None,
             'due bocciature: la misura non entra nel catalogo')
    verifica(esclusione and esclusione['motivo'] == 'doppio_rifiuto_validator',
             'l\'esclusione dichiara il motivo doppio_rifiuto_validator')
    verifica(finto.chiamate.count('explainer') == config.MAX_GIRI_FIDELITY,
             f'explainer invocato {config.MAX_GIRI_FIDELITY} volte, non di piu\': si escala, non si ritenta',
             f'chiamate: {finto.chiamate}')


# --------------------------------------------------------------------------
# 6. Stato esternalizzato
# --------------------------------------------------------------------------

def prova_stato() -> None:
    print('\n--- stato su file --------------------------------------------------')
    run_id = sessione_mod.create_session()
    percorso = config.run_path(run_id)
    verifica(percorso.exists(), f'la sessione scrive {percorso.relative_to(config.RADICE)}')

    sessione_mod.salva_profilo(run_id, PROFILO_FINTO)
    verifica(config.PROFILO_PATH.exists(),
             f'il profilo sta in {config.PROFILO_PATH.relative_to(config.RADICE)}')

    stato = json.loads(percorso.read_text(encoding='utf-8'))
    verifica(valida('run-state', stato) == [],
             'lo stato della sessione rispetta agents/schemas/run-state.json')
    verifica(not (config.RADICE / 'app' / 'logs').exists(),
             'lo stato non sta piu\' in app/logs/')
    percorso.unlink(missing_ok=True)


def prova_demo() -> None:
    print('\n--- modalita demo --------------------------------------------------')
    import demo

    scenari = demo.scenari()
    verifica(len(scenari) >= 5,
             'gli scenari registrati sono almeno cinque (4 casi + escalation)',
             ', '.join(s['id'] for s in scenari))
    verifica(any(s['id'] == 'escalation' for s in scenari),
             'esiste lo scenario di escalation, quello che dimostra il gate HITL')

    conformi = True
    for scenario in scenari:
        for agente in ('profiler', 'eligibility'):
            registrato = scenario.get(agente)
            if not isinstance(registrato, dict) or registrato.get('sorgente') == 'catalogo':
                continue
            documento = demo._sostituisci_versione(registrato)
            errori = valida_output(agente, documento)
            if errori:
                conformi = False
                print(f"       {scenario['id']}/{agente}: {errori[0]}")
    verifica(conformi,
             'ogni output registrato passa la stessa validazione del percorso reale')

    catalogo = catalogo_mod.carica()
    verifica(catalogo is not None,
             'il catalogo verificato esiste in agents/state/catalogo.json',
             f"voci: {len(catalogo_mod.voci(catalogo))}" if catalogo else
             'assente: in demo il sistema rimanda al CAF invece di inventare misure')


def main() -> int:
    print('Collaudo offline di "A cosa ho diritto?" - nessuna chiamata al modello.')
    prova_tiering()
    prova_retry()
    prova_validazione()
    prova_gate_fase_b()
    prova_limite_fase_a()
    prova_stato()
    prova_demo()

    passate = sum(1 for ok, _ in ESITI if ok)
    falliti = [d for ok, d in ESITI if not ok]
    print(f'\nRIEPILOGO: {passate}/{len(ESITI)} verifiche passate')
    for descrizione in falliti:
        print(f'  FAIL: {descrizione}')
    return 0 if not falliti else 1


if __name__ == '__main__':
    sys.exit(main())
