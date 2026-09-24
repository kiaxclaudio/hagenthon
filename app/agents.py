"""Esecuzione degli agenti: tiering, resilienza, validazione, gate HITL.

Tre cose, in quest'ordine, per ogni chiamata:
1. il modello si sceglie dalla mappa agente -> tier di config.py (C5);
2. la chiamata ha timeout e retry con backoff esponenziale, e ritenta solo cio'
   che ha senso ritentare (C2, C3);
3. l'output viene validato contro agents/schemas/<agente>.output.json prima di
   essere usato: se non passa si ri-chiede una volta sola con gli errori in
   chiaro, poi si degrada (E1, D1).

La Fase B (conversazione) sta qui. La Fase A (costruzione del catalogo) sta in
fase_a.py perche' gira una volta sola, offline.
"""

import json
import random
import time
from typing import Any

import anthropic

import catalogo as catalogo_mod
from config import (
    API_KEY,
    BACKOFF_BASE_S,
    BACKOFF_MAX_S,
    MAX_MISURE_NAVIGATOR,
    MAX_RETRY,
    MAX_RICHIESTE_SCHEMA,
    PROMPT_DIR,
    SOGLIA_CONFIDENCE,
    TIMEOUT_S,
    TIER_PER_AGENTE,
    max_token_di,
    modello_di,
)
from validation import (
    MESSAGGIO_CAF,
    degradato,
    degradato_eligibility,
    disclaimer,
    ora,
    schema_di,
    valida_input,
    valida_output,
)

# --------------------------------------------------------------------------
# Errori e classificazione
# --------------------------------------------------------------------------


class ErroreModello(Exception):
    """Fallimento di una chiamata al modello, gia' classificato."""

    def __init__(self, messaggio: str, *, motivo: str, ritentabile: bool):
        super().__init__(messaggio)
        self.motivo = motivo
        self.ritentabile = ritentabile


def _eccezioni(*nomi: str) -> tuple[type, ...]:
    """Tipi di eccezione del SDK, saltando quelli assenti nella versione installata."""
    trovati = [getattr(anthropic, n, None) for n in nomi]
    return tuple(t for t in trovati if isinstance(t, type))


# Si ritenta cio' che passa da solo: limiti di frequenza, sovraccarico, rete, 5xx.
RITENTABILI = _eccezioni(
    'RateLimitError', 'APITimeoutError', 'APIConnectionError', 'InternalServerError'
)
# Non si ritenta cio' che ritenterebbe lo stesso errore: chiave, permessi,
# richiesta malformata, modello inesistente. Fallire subito e' la cosa utile.
FATALI = _eccezioni(
    'AuthenticationError', 'PermissionDeniedError', 'BadRequestError',
    'NotFoundError', 'UnprocessableEntityError',
)


def _classifica(errore: Exception) -> ErroreModello:
    codice = getattr(errore, 'status_code', None)
    if isinstance(errore, FATALI) and codice != 429:
        return ErroreModello(
            f'{type(errore).__name__}: {errore}', motivo='richiesta_non_valida',
            ritentabile=False,
        )
    if isinstance(errore, RITENTABILI) or codice == 429 or (isinstance(codice, int) and codice >= 500):
        return ErroreModello(
            f'{type(errore).__name__}: {errore}', motivo='temporaneo', ritentabile=True,
        )
    return ErroreModello(
        f'{type(errore).__name__}: {errore}', motivo='sconosciuto', ritentabile=False,
    )


def _attesa(tentativo: int, errore: Exception) -> float:
    """Backoff esponenziale con jitter; se il server dice quanto aspettare, si ascolta."""
    intestazioni = getattr(getattr(errore, 'response', None), 'headers', None)
    if intestazioni:
        try:
            return min(BACKOFF_MAX_S, float(intestazioni.get('retry-after')))
        except (TypeError, ValueError):
            pass
    base = min(BACKOFF_MAX_S, BACKOFF_BASE_S * (2 ** tentativo))
    return base * (0.5 + random.random() / 2)


# --------------------------------------------------------------------------
# Client e prompt
# --------------------------------------------------------------------------

_client: anthropic.Anthropic | None = None


def _client_anthropic() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not API_KEY:
            # Nessuna chiave: e' un errore di configurazione, non un guasto.
            raise ErroreModello(
                'ANTHROPIC_API_KEY non configurata (vedi .env.example)',
                motivo='configurazione', ritentabile=False,
            )
        # max_retries=0: il backoff lo governa questo modulo, in un posto solo.
        _client = anthropic.Anthropic(
            api_key=API_KEY, timeout=TIMEOUT_S, max_retries=0
        )
    return _client


_cache_prompt: dict[str, str] = {}


def _prompt(agente: str) -> str:
    """Prompt di sistema dell'agente, da .claude/agents/<agente>.md senza frontmatter."""
    if agente in _cache_prompt:
        return _cache_prompt[agente]
    testo = (PROMPT_DIR / f'{agente}.md').read_text(encoding='utf-8')
    if testo.startswith('---'):
        fine = testo.find('---', 3)
        if fine != -1:
            testo = testo[fine + 3:].lstrip()
    _cache_prompt[agente] = testo
    return testo


def _schema_compatto(agente: str) -> str:
    """Schema di output senza le descrizioni: si spedisce solo in ri-richiesta."""
    def pulisci(nodo: Any) -> Any:
        if isinstance(nodo, dict):
            return {k: pulisci(v) for k, v in nodo.items() if k != 'description'}
        if isinstance(nodo, list):
            return [pulisci(x) for x in nodo]
        return nodo

    return json.dumps(pulisci(schema_di(f'{agente}.output')), ensure_ascii=False)


# --------------------------------------------------------------------------
# Chiamata al modello
# --------------------------------------------------------------------------


def _chiama(agente: str, messaggi: list[dict], sistema: str) -> str:
    """Una chiamata al modello dell'agente, con timeout e retry con backoff.

    Alza ErroreModello quando ha finito i tentativi o quando l'errore non e'
    ritentabile. Non restituisce mai una stringa vuota.
    """
    modello = modello_di(agente)
    ultimo: ErroreModello | None = None

    for tentativo in range(MAX_RETRY + 1):
        try:
            risposta = _client_anthropic().messages.create(
                model=modello,
                max_tokens=max_token_di(agente),
                # Il prompt di sistema e' lungo e identico a ogni turno: la cache
                # lo fa pagare una volta sola (F2).
                system=[{
                    'type': 'text',
                    'text': sistema,
                    'cache_control': {'type': 'ephemeral'},
                }],
                messages=messaggi,
            )
            testo = ''.join(
                blocco.text for blocco in risposta.content
                if getattr(blocco, 'type', '') == 'text'
            ).strip()
            if not testo:
                raise ErroreModello(
                    'risposta vuota dal modello', motivo='risposta_vuota',
                    ritentabile=True,
                )
            return testo

        except ErroreModello as errore:
            ultimo = errore
            if not errore.ritentabile or tentativo == MAX_RETRY:
                raise
            time.sleep(_attesa(tentativo, errore))

        except Exception as grezzo:  # eccezioni del SDK e della rete
            errore = _classifica(grezzo)
            ultimo = errore
            if not errore.ritentabile or tentativo == MAX_RETRY:
                raise errore from grezzo
            time.sleep(_attesa(tentativo, grezzo))

    raise ultimo or ErroreModello(
        'chiamata fallita', motivo='sconosciuto', ritentabile=False
    )


def _estrai_json(testo: str) -> dict:
    """Primo oggetto JSON del testo, anche se avvolto in un blocco di codice."""
    grezzo = testo.strip()
    if grezzo.startswith('```'):
        grezzo = grezzo.split('```')[1]
        if grezzo.startswith('json'):
            grezzo = grezzo[4:]
        grezzo = grezzo.strip()
    try:
        return json.loads(grezzo)
    except json.JSONDecodeError:
        pass
    inizio = grezzo.find('{')
    fine = grezzo.rfind('}')
    if inizio == -1 or fine <= inizio:
        raise ValueError('nessun oggetto JSON nella risposta')
    return json.loads(grezzo[inizio:fine + 1])


ISTRUZIONE_FORMATO = (
    "\n\nFormato della risposta: un solo oggetto JSON, senza testo intorno e senza "
    "blocchi di codice, conforme a agents/schemas/{agente}.output.json. Chiavi di "
    "primo livello obbligatorie: status, confidence, source_refs, payload."
)


def esegui_agente(agente: str, contenuto_utente: Any, *, valida: bool = True) -> dict:
    """Esegue un agente e restituisce un output gia' validato, o un degradato.

    Il percorso e': chiamata (con retry) -> parsing -> validazione di schema ->
    al massimo una ri-richiesta con gli errori in chiaro -> fallback degradato.
    Non alza mai: chi chiama legge 'status' e decide (D1).
    """
    if agente not in TIER_PER_AGENTE:
        raise KeyError(f'agente non previsto dall\'architettura: {agente}')

    sistema = _prompt(agente) + ISTRUZIONE_FORMATO.format(agente=agente)
    if isinstance(contenuto_utente, str):
        messaggi = [{'role': 'user', 'content': contenuto_utente}]
    else:
        messaggi = [{
            'role': 'user',
            'content': json.dumps(contenuto_utente, ensure_ascii=False),
        }]

    for giro in range(MAX_RICHIESTE_SCHEMA + 1):
        try:
            testo = _chiama(agente, messaggi, sistema)
        except ErroreModello as errore:
            # I retry tecnici sono gia' stati fatti dentro _chiama: qui si degrada.
            return degradato(agente, f'{errore.motivo}: {errore}')

        try:
            uscita = _estrai_json(testo)
            errori = valida_output(agente, uscita) if valida else []
        except (ValueError, json.JSONDecodeError) as errore:
            uscita, errori = None, [f'(radice): output non e\' JSON ({errore})']

        if not errori:
            return uscita

        if giro >= MAX_RICHIESTE_SCHEMA:
            return degradato(
                agente,
                'output non conforme allo schema dopo la ri-richiesta: '
                + '; '.join(errori),
            )

        messaggi = messaggi + [
            {'role': 'assistant', 'content': testo},
            {'role': 'user', 'content': (
                'Il tuo output non rispetta agents/schemas/' + agente + '.output.json.\n'
                'Errori di validazione:\n- ' + '\n- '.join(errori) + '\n\n'
                'Schema da rispettare:\n' + _schema_compatto(agente) + '\n\n'
                'Correggi e restituisci solo il JSON. Non inventare dati per '
                'riempire un campo: se un dato non ce l\'hai, usa status '
                '"degraded" o "hitl_required".'
            )},
        ]

    return degradato(agente, 'esaurite le ri-richieste')


def _degradato(uscita: dict) -> bool:
    return uscita.get('status') != 'ok'


# --------------------------------------------------------------------------
# Fase B - conversazione
# --------------------------------------------------------------------------


def call_orchestrator(conversation_history: list) -> dict:
    """Turno di conversazione con l'orchestratore (haiku).

    Restituisce {'text': str, 'risposte': dict|None}: 'risposte' e' valorizzato
    quando l'orchestratore dichiara chiuso il questionario ed emette il JSON con
    le risposte raccolte. Da li' in poi si passa al profiler, che le normalizza.
    """
    sistema = _prompt('orchestrator')
    try:
        testo = _chiama('orchestrator', list(conversation_history), sistema)
    except ErroreModello as errore:
        return {
            'text': MESSAGGIO_CAF,
            'risposte': None,
            'status': 'degraded',
            'motivo_tecnico': f'{errore.motivo}: {errore}',
        }

    risposte = None
    try:
        candidato = _estrai_json(testo)
        if isinstance(candidato, dict):
            # L'orchestratore chiude il questionario emettendo le risposte grezze.
            grezze = candidato.get('risposte', candidato)
            if isinstance(grezze, dict) and 'situazione_vita' in grezze:
                risposte = grezze
    except (ValueError, json.JSONDecodeError):
        pass

    return {'text': testo, 'risposte': risposte, 'status': 'ok'}


def call_profiler(sessione_id: str, risposte: dict, domande_poste: list[str]) -> dict:
    """Normalizza le risposte nella tassonomia chiusa di profiler.output.json."""
    ingresso = {
        'sessione_id': sessione_id,
        'risposte': {k: v for k, v in risposte.items() if k in (
            'situazione_vita', 'condizione_abitativa', 'tipo_reddito', 'timing', 'caf'
        )},
        'domande_poste': domande_poste or ['situazione_vita'],
    }
    errori_ingresso = valida_input('profiler', ingresso)
    if errori_ingresso:
        # Input non conforme: non si spreca una chiamata, si degrada subito.
        return degradato('profiler', 'input non conforme: ' + '; '.join(errori_ingresso))
    return esegui_agente('profiler', ingresso)


def esegui_profilazione(sessione_id: str, risposte: dict,
                        domande_poste: list[str]) -> tuple[dict | None, dict | None]:
    """profiler con il suo limite di iterazione: due invocazioni, poi si escala.

    Restituisce (profilo, None) se il profilo e' utilizzabile, (None, esito) se
    dopo la seconda invocazione mancano ancora risposte: in quel caso il caso va
    a una persona con motivo 'profilo_incompleto'.
    """
    ultimo: dict | None = None
    for invocazione in (1, 2):
        uscita = call_profiler(sessione_id, risposte, domande_poste)
        if _degradato(uscita):
            ultimo = uscita
            continue
        profilo = uscita.get('payload', {})
        if profilo.get('completo') or invocazione == 2:
            # Alla seconda invocazione si accetta anche un profilo parziale:
            # eligibility ha comunque i suoi gate a valle.
            return profilo, None
        # Ri-domanda mirata: si dichiarano come poste anche le domande che il
        # profiler ha segnalato come mancanti, cosi' la seconda invocazione sa
        # che quelle risposte non arriveranno.
        mancanti = profilo.get('risposte_mancanti') or []
        if not mancanti:
            return profilo, None
        domande_poste = sorted({*domande_poste, *mancanti})

    motivo = 'profilo_incompleto'
    messaggio = (
        'Non siamo riusciti a capire abbastanza della tua situazione per '
        'orientarti senza rischio di sbagliare. ' + MESSAGGIO_CAF
    )
    return None, _escalation(
        motivo, messaggio, status='degraded',
        eligibility=ultimo or degradato('profiler', 'profilo non normalizzabile'),
    )


def call_eligibility(profilo: dict, candidate: list[dict], catalogo_versione: str) -> dict:
    """Incrocia profilo e catalogo verificato (sonnet)."""
    ingresso = {
        'profilo': profilo,
        'catalogo_versione': catalogo_versione,
        'misure_candidate': candidate,
    }
    return esegui_agente('eligibility', ingresso)


def call_navigator(profilo: dict, voce: dict) -> dict:
    """Compone i passi di accesso a una singola misura (haiku)."""
    ingresso = {'profilo': profilo, 'misura': voce}
    return esegui_agente('navigator', ingresso)


def call_explainer(ingresso: dict) -> dict:
    """Riscrittura in lingua semplice di una misura (sonnet). Usato in Fase A."""
    return esegui_agente('explainer', ingresso)


def call_fidelity_validator(ingresso: dict) -> dict:
    """Verifica avversariale della riscrittura (opus). Usato in Fase A."""
    return esegui_agente('fidelity-validator', ingresso)


# --------------------------------------------------------------------------
# Gate HITL della Fase B (D2, D3, D4)
# --------------------------------------------------------------------------


def _escalation(motivo: str, messaggio: str, *, status: str = 'hitl_required',
                eligibility: dict | None = None) -> dict:
    """Esito di sessione che rimanda a una persona. Non e' un errore: e' il prodotto."""
    return {
        'status': status,
        'escalation': True,
        'motivo_escalation': motivo,
        'messaggio_escalation': messaggio,
        'eligibility': eligibility,
        'explainer': None,
        'navigator': None,
        'disclaimer': disclaimer(),
    }


def run_full_pipeline(profilo: dict, sessione_id: str = 'sessione') -> dict:
    """Fase B completa: catalogo -> eligibility -> navigator, con i gate.

    Riceve un profilo gia' normalizzato dal profiler. Restituisce la struttura
    che l'interfaccia consuma; ogni uscita porta status e disclaimer.
    """
    catalogo = catalogo_mod.carica()
    versione = catalogo_mod.versione(catalogo)

    # Gate: senza catalogo verificato non si risponde (regola di routing 1, G4).
    candidate = catalogo_mod.misure_candidate(profilo, catalogo)
    if not candidate:
        motivo = 'caso_non_coperto_dal_catalogo'
        messaggio = (
            'Per la tua situazione non abbiamo misure verificate nel catalogo. '
            'Non inventiamo una risposta: rivolgiti a un CAF o a un commercialista, '
            'che possono controllare il tuo caso specifico.'
        )
        return _escalation(
            motivo, messaggio,
            eligibility=degradato_eligibility(
                profilo.get('profilo_id', sessione_id), versione, motivo, messaggio,
                status='hitl_required',
            ),
        )

    uscita_eligibility = call_eligibility(profilo, candidate, versione)

    if _degradato(uscita_eligibility):
        motivo = 'requisiti_non_verificabili'
        return _escalation(
            motivo,
            'Non siamo riusciti a verificare quali misure ti riguardano. '
            + MESSAGGIO_CAF,
            status='degraded',
            eligibility=uscita_eligibility,
        )

    payload = uscita_eligibility.get('payload', {})
    confidence = float(uscita_eligibility.get('confidence', 0.0))
    misure = payload.get('misure_pertinenti', [])

    # Gate: sotto soglia non si propone nulla, e si dice perche' (G-09).
    if confidence < SOGLIA_CONFIDENCE:
        motivo = 'confidence_bassa'
        messaggio = (
            f'Il sistema non e\' abbastanza sicuro della lettura del tuo caso '
            f'(affidabilita\' {confidence:.2f}, soglia {SOGLIA_CONFIDENCE}). '
            'Preferiamo non mostrarti misure incerte: un CAF puo\' verificare la '
            'tua posizione con i tuoi documenti.'
        )
        return _escalation(
            motivo, messaggio,
            eligibility=degradato_eligibility(
                payload.get('profilo_id', profilo.get('profilo_id', sessione_id)),
                versione, motivo, messaggio, status='hitl_required',
            ),
        )

    # Gate: l'agente stesso puo' dichiarare escalation, oppure non trovare nulla.
    if payload.get('escalation') or not misure:
        motivo = payload.get('motivo_escalation') or 'caso_non_coperto_dal_catalogo'
        messaggio = payload.get('spiegazione_escalation') or (
            'Per la tua situazione non emergono misure con requisiti verificabili '
            'da qui. Un CAF o un commercialista possono valutare il tuo caso.'
        )
        return _escalation(motivo, messaggio, eligibility=uscita_eligibility)

    # Limite di iterazione: al massimo tre misure guidate per sessione.
    misure = misure[:MAX_MISURE_NAVIGATOR]

    percorsi: list[dict] = []
    for misura in misure:
        voce = catalogo_mod.voce_per_id(misura.get('misura_id'), catalogo)
        if voce is None:
            continue
        uscita_navigator = call_navigator(profilo, voce)
        if _degradato(uscita_navigator):
            continue
        percorsi.append(uscita_navigator)

    if not percorsi:
        motivo = 'requisiti_non_verificabili'
        return _escalation(
            motivo,
            'Le misure che ti riguardano ci sono, ma non siamo riusciti a '
            'ricostruire la procedura passo per passo. ' + MESSAGGIO_CAF,
            status='degraded',
            eligibility=uscita_eligibility,
        )

    return {
        'status': 'ok',
        'escalation': False,
        'motivo_escalation': None,
        'messaggio_escalation': None,
        'eligibility': uscita_eligibility,
        'navigator': percorsi,
        'disclaimer': disclaimer(),
        'catalogo_versione': versione,
        'generato_il': ora(),
    }


# --------------------------------------------------------------------------
# Adattamento per l'interfaccia
# --------------------------------------------------------------------------


def vista_interfaccia(esito: dict) -> dict:
    """Traduce l'esito della Fase B nella forma che app/static/app.js disegna.

    Gli agenti si parlano con i contratti di agents/schemas/ (E4); la vista e'
    un livello a parte, cosi' il front-end non dipende dalla forma interna. Le
    spiegazioni non si rigenerano: sono quelle gia' verificate in Fase A e
    conservate nel catalogo (F1, G4).
    """
    vista = {
        'status': esito.get('status', 'ok'),
        'escalation': esito.get('escalation', False),
        'messaggio_escalation': esito.get('messaggio_escalation'),
        'motivo_escalation': esito.get('motivo_escalation'),
        'disclaimer': esito.get('disclaimer', disclaimer()),
        'explainer': None,
        'navigator': None,
    }
    if esito.get('escalation') or not esito.get('navigator'):
        return vista

    catalogo = catalogo_mod.carica()
    pertinenti = {
        m['misura_id']: m
        for m in esito['eligibility'].get('payload', {}).get('misure_pertinenti', [])
    }

    spiegazioni, percorsi = [], []
    for uscita in esito['navigator']:
        payload = uscita.get('payload', {})
        misura_id = payload.get('misura_id')
        voce = catalogo_mod.voce_per_id(misura_id, catalogo) or {}
        spiegazione = voce.get('spiegazione', {})
        pertinente = pertinenti.get(misura_id, {})

        spiegazioni.append({
            'id': misura_id,
            'titolo': spiegazione.get('titolo_semplice') or pertinente.get('nome', ''),
            # Un requisito ancora da verificare non e' una certezza: si dichiara.
            'badge_rilevanza': (
                'Da verificare' if pertinente.get('requisiti_da_verificare')
                else 'Molto probabile'
            ),
            'cosa_e': spiegazione.get('cosa_e', ''),
            'quanto_vale': spiegazione.get('quanto_vale', ''),
            'chi_puo_accedervi': ' '.join(spiegazione.get('a_chi_spetta', [])),
            'attenzione': ' '.join(spiegazione.get('attenzione', [])),
            'glossario': [
                {'termine': g.get('termine', ''),
                 'spiegazione': g.get('spiegazione_semplice', '')}
                for g in spiegazione.get('glossario', [])
            ],
            'source_refs': spiegazione.get('source_refs', []),
            'disclaimer': spiegazione.get('disclaimer') or disclaimer(),
        })

        percorsi.append({
            'id': misura_id,
            'passi': [
                {'numero': p.get('ordine'),
                 'azione': p.get('azione', ''),
                 'obbligatorio_prima': not p.get('dipende_da'),
                 'nota': p.get('dove_dettaglio')}
                for p in payload.get('passi', [])
            ],
            'avvertenza_timing': _avvertenza_timing(payload.get('scadenza_da_rispettare')),
        })

    primo = esito['navigator'][0].get('payload', {}).get('primo_passo_concreto')
    vista['explainer'] = {'spiegazioni': spiegazioni}
    vista['navigator'] = {
        'percorsi': percorsi,
        'prossimo_passo_prioritario': primo,
        'riquadro_spid': {'mostra': _serve_spid(esito), 'testo': (
            'Molte pratiche si aprono solo con SPID, CIE o CNS. Se non li hai, '
            'un CAF puo\' aiutarti a ottenerli.'
        )},
    }
    return vista


def _avvertenza_timing(scadenza: dict | None) -> str | None:
    if not scadenza:
        return None
    tipo = scadenza.get('tipo_scadenza')
    if tipo == 'data_fissa' and scadenza.get('data'):
        return f"Scadenza indicata dalla fonte: {scadenza['data']}."
    if tipo == 'entro_giorni_da_evento' and scadenza.get('giorni'):
        return (
            f"Termine: {scadenza['giorni']} giorni da "
            f"{scadenza.get('evento_di_riferimento', 'l\'evento')}."
        )
    if tipo == 'a_sportello_fino_esaurimento':
        return 'Fondi a sportello: la fonte indica che si esauriscono.'
    return None


def _serve_spid(esito: dict) -> bool:
    for uscita in esito.get('navigator') or []:
        for passo in uscita.get('payload', {}).get('passi', []):
            if 'spid_cie_cns' in (passo.get('documenti_necessari') or []):
                return True
    return False
