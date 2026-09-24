"""Modalita demo: stesso percorso, sorgente diversa.

Con DEMO_MODE=true l'app non chiama mai l'API. Al posto della risposta del
modello, `agents._chiama` riceve un output registrato letto da `app/demo/`.
Tutto il resto del percorso e' identico: parsing, validazione contro
`agents/schemas/`, gate HITL, stato su file. Non e' un ramo che aggira i
controlli: se un output registrato non rispetta il contratto, fallisce come
fallirebbe il modello.

Perche' si puo' fare: la Fase A e' gia' stata eseguita e il suo risultato e'
persistito in `agents/state/catalogo.json`. A runtime serve solo leggere il
catalogo verificato, quindi la demo non e' una scorciatoia ma la conseguenza
della separazione fra le due fasi.

Cosa e' registrato e cosa no:
- la conversazione dell'orchestratore e l'output del profiler sono registrati
  per intero nei file di scenario: non contengono nessun dato fiscale;
- le misure, i loro numeri e i loro riferimenti alla fonte non sono registrati:
  vengono dal catalogo verificato, e gli output di eligibility e navigator sono
  ricomposti da quello (G4, G5);
- l'unico output di dominio registrato per intero e' quello dello scenario di
  escalation, dove non c'e' nessuna misura da mostrare.
"""

import json
from functools import lru_cache
from pathlib import Path

import catalogo as catalogo_mod

# Testo vincolato da agents/schemas/navigator.output.json (const): non si riformula.
TESTO_SPID = "Non hai ancora lo SPID? Puoi attivarlo presso uno sportello di Poste Italiane, in una banca abilitata oppure da app. Ti servono un documento d'identità valido e il tuo numero di telefono. L'attivazione è gratuita."
from config import DEMO_DIR
from validation import disclaimer, valida_output

SEGNAPOSTO_VERSIONE = '@catalogo_versione@'


class DemoNonDisponibile(Exception):
    """Nessuna risposta registrata per questa richiesta."""


@lru_cache(maxsize=1)
def scenari() -> list[dict]:
    if not DEMO_DIR.exists():
        return []
    elenco = []
    for percorso in sorted(DEMO_DIR.glob('scenario-*.json')):
        try:
            elenco.append(json.loads(percorso.read_text(encoding='utf-8')))
        except json.JSONDecodeError as errore:
            print(f'[demo] scenario ignorato ({percorso.name}): {errore}')
    return elenco


def elenco_scenari() -> list[dict]:
    """Scenari disponibili, per la diagnostica e per l'interfaccia."""
    return [
        {'id': s['id'], 'etichetta': s['etichetta'], 'descrizione': s['descrizione']}
        for s in scenari()
    ]


_corrente: dict | None = None


def scenario_corrente() -> dict | None:
    return _corrente


def _prima_risposta(messaggi: list[dict]) -> str:
    """Solo la prima risposta della persona: e' quella che sceglie lo scenario.

    Guardare tutta la conversazione farebbe scattare la parola sbagliata (in
    'Sono proprietario di casa' c'e' 'casa' anche quando si parla d'altro).
    """
    for messaggio in messaggi:
        if messaggio.get('role') == 'user':
            return str(messaggio.get('content', '')).lower()
    return ''



def seleziona(messaggi: list[dict]) -> dict:
    """Sceglie lo scenario dalle parole della persona.

    Se nessuno scenario corrisponde si usa quello di escalation: in demo come
    nella realta', un caso non previsto si dichiara, non si improvvisa.
    """
    global _corrente
    disponibili = scenari()
    if not disponibili:
        raise DemoNonDisponibile(f'nessuno scenario in {DEMO_DIR}')

    testo = _prima_risposta(messaggi)
    for scenario in disponibili:
        if any(parola in testo for parola in scenario.get('innesco', [])):
            _corrente = scenario
            return scenario

    _corrente = next(
        (s for s in disponibili if s['id'] == 'escalation'), disponibili[0]
    )
    return _corrente


# --------------------------------------------------------------------------
# Ricomposizione dal catalogo verificato
# --------------------------------------------------------------------------


def _refs(misura: dict) -> list[str]:
    riferimenti = list(misura.get('source_refs') or [])
    if not riferimenti:
        riferimenti = list((misura.get('beneficio') or {}).get('source_refs') or [])
    return riferimenti or ['catalogo-verificato']


def _eligibility_dal_catalogo(profilo: dict) -> dict:
    catalogo = catalogo_mod.carica()
    candidate = catalogo_mod.misure_candidate(profilo, catalogo, limite=3)
    pertinenti = []
    for voce in candidate:
        misura = voce.get('misura', {})
        spiegazione = voce.get('spiegazione', {})
        pertinenti.append({
            'misura_id': misura.get('misura_id'),
            'nome': misura.get('nome'),
            'titolo_semplice': spiegazione.get('titolo_semplice') or misura.get('nome'),
            'tipo': misura.get('tipo'),
            # La confidenza non si inventa: e' quella con cui la Fase A ha
            # approvato la voce di catalogo.
            'confidence': float(voce.get('verifica', {}).get('confidence', 0.6)),
            'motivazione': (
                'Il catalogo verificato collega questa misura alla situazione '
                'di vita indicata nelle tue risposte.'
            ),
            'corrispondenze_profilo': ['situazione_vita'],
            'requisiti_da_verificare': [],
            'source_refs': _refs(misura),
        })

    payload = {
        'profilo_id': profilo.get('profilo_id', 'profilo-demo'),
        'catalogo_versione': catalogo_mod.versione(catalogo),
        'misure_pertinenti': pertinenti,
        'misure_escluse': [],
        'escalation': not pertinenti,
        'disclaimer': disclaimer(),
    }
    if not pertinenti:
        payload['ambito_escalation'] = 'sessione'
        payload['motivo_escalation'] = 'caso_non_coperto_dal_catalogo'
        payload['spiegazione_escalation'] = (
            'Il catalogo verificato non contiene misure collegate a questa '
            'situazione. Il sistema non ne inventa una.'
        )
    return {
        'status': 'hitl_required' if not pertinenti else 'ok',
        'confidence': 0.4 if not pertinenti else 0.88,
        'source_refs': sorted({r for m in pertinenti for r in m['source_refs']}),
        'payload': payload,
    }


def _navigator_dal_catalogo(voce: dict, profilo: dict) -> dict:
    misura = voce.get('misura', {})
    spiegazione = voce.get('spiegazione', {})
    canali = misura.get('canali_accesso') or ['caf']
    canale = 'caf' if profilo.get('caf') == 'si' and 'caf' in canali else canali[0]
    riferimenti = _refs(misura)
    documenti = misura.get('documenti_richiesti') or []
    tipi_documento = []
    for documento in documenti:
        tipo = documento.get('tipo_documento')
        if tipo and tipo not in tipi_documento:
            tipi_documento.append(tipo)

    passi = [
        {'ordine': 1,
         'azione': 'Metti insieme i documenti elencati qui sotto.',
         'dove': 'caf' if canale == 'caf' else canale,
         'documenti_necessari': tipi_documento[:5],
         'dipende_da': [],
         'source_refs': riferimenti},
        {'ordine': 2,
         'azione': 'Presenta la richiesta attraverso il canale indicato dalla fonte.',
         'dove': canale,
         'documenti_necessari': [],
         'dipende_da': [1],
         'source_refs': riferimenti},
        {'ordine': 3,
         'azione': 'Conserva la ricevuta e i giustificativi fino alla verifica.',
         'dove': canale,
         'documenti_necessari': [],
         'dipende_da': [2],
         'source_refs': riferimenti},
    ]

    richiede_spid = canale in ('inps_online', 'agenzia_entrate_online', 'spid')
    payload = {
        'misura_id': misura.get('misura_id'),
        'primo_passo_concreto': 'Raccogli i documenti richiesti dalla fonte ufficiale.',
        'passi': passi,
        'documenti_necessari': documenti,
        'glossario': spiegazione.get('glossario', []),
        'riquadro_spid': {
            'necessario': richiede_spid,
            'testo': (
                'Non hai ancora lo SPID? Puoi attivarlo presso uno sportello di '
                'Poste Italiane, in una banca abilitata oppure da app. Ti servono '
                'un documento d\'identità valido e il tuo numero di telefono. '
                'L\'attivazione è gratuita.'
            ),
        },
        'disclaimer': disclaimer(),
        # Obbligatorio dallo schema: si mostra sempre, anche se nessun passo
        # richiede l'identita digitale. E' il primo muro per chi non ce l'ha,
        # e scoprirlo al terzo passo significa fermarsi li.
        'riquadro_spid': {
            'necessario': any(
                'spid_cie_cns' in (passo.get('documenti_necessari') or [])
                for passo in passi
            ),
            'testo': TESTO_SPID,
        },
    }
    if misura.get('scadenza'):
        payload['scadenza_da_rispettare'] = misura['scadenza']

    return {'status': 'ok', 'confidence': 0.85,
            'source_refs': riferimenti, 'payload': payload}


# --------------------------------------------------------------------------
# Punto di ingresso usato da agents._chiama
# --------------------------------------------------------------------------


def _sostituisci_versione(registrato: dict) -> dict:
    testo = json.dumps(registrato, ensure_ascii=False)
    return json.loads(testo.replace(SEGNAPOSTO_VERSIONE, catalogo_mod.versione()))


def risposta_registrata(agente: str, messaggi: list[dict]) -> str:
    """Restituisce, come farebbe il modello, il testo JSON dell'output.

    Gli output registrati vengono validati con lo stesso codice del percorso
    reale prima di essere restituiti: un file di demo rotto si vede subito.
    """
    if agente == 'orchestrator':
        scenario = seleziona(messaggi)
        turni = [m for m in messaggi if m.get('role') == 'user']
        battute = scenario['conversazione']
        return battute[min(len(turni), len(battute)) - 1]

    scenario = scenario_corrente()
    if scenario is None:
        raise DemoNonDisponibile('nessuno scenario selezionato')

    ingresso = {}
    if messaggi:
        try:
            ingresso = json.loads(messaggi[0].get('content', '{}'))
        except (json.JSONDecodeError, TypeError):
            ingresso = {}

    if agente == 'profiler':
        uscita = _sostituisci_versione(scenario['profiler'])
    elif agente == 'eligibility':
        registrato = scenario.get('eligibility', {})
        if registrato.get('sorgente') == 'catalogo':
            uscita = _eligibility_dal_catalogo(ingresso.get('profilo', {}))
        else:
            uscita = _sostituisci_versione(registrato)
    elif agente == 'navigator':
        uscita = _navigator_dal_catalogo(
            ingresso.get('misura', {}), ingresso.get('profilo', {})
        )
    else:
        # Fase A: in demo non si ricostruisce il catalogo, lo si legge.
        raise DemoNonDisponibile(
            f'{agente} appartiene alla Fase A e non ha risposte registrate'
        )

    errori = valida_output(agente, uscita)
    if errori:
        raise DemoNonDisponibile(
            f'output registrato di {agente} non conforme allo schema: {errori[0]}'
        )
    return json.dumps(uscita, ensure_ascii=False)
