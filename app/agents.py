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
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from typing import Any

import anthropic

import catalogo as catalogo_mod
import demo
from config import (
    API_KEY,
    DEMO_MODE,
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
    parametri_pensiero,
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


def _risolvi_ref(riferimento: str) -> dict | None:
    """Risolve un $ref locale del repository (./file.json#/$defs/nome o #/$defs/nome).

    Serve perche' uno schema spedito con i $ref intatti non e' un contratto: i
    valori che contano - il testo esatto del disclaimer, gli enum chiusi delle
    corrispondenze di profilo - stanno dentro i $defs referenziati, e chi legge
    lo schema senza risolverli non li vede. Erano esattamente i due campi su cui
    l'output sbagliava.
    """
    percorso, _, puntatore = riferimento.partition('#')
    nome = percorso.strip('./').removesuffix('.json')
    try:
        nodo: Any = schema_di(nome) if nome else None
    except (KeyError, FileNotFoundError):
        return None
    if nodo is None:
        return None
    for pezzo in [p for p in puntatore.split('/') if p]:
        if not isinstance(nodo, dict) or pezzo not in nodo:
            return None
        nodo = nodo[pezzo]
    return nodo if isinstance(nodo, dict) else None


@lru_cache(maxsize=16)
def _schema_compatto(agente: str, radice: str | None = None) -> str:
    """Schema di output senza descrizioni e con i $ref locali risolti.

    Due operazioni, con lo stesso scopo: far stare il contratto in un prompt.
    Via le `description` (prosa per chi legge lo schema, non vincoli) e dentro
    i `$defs` referenziati (vincoli veri: const, enum, pattern).
    """
    def pulisci(nodo: Any, visti: frozenset[str], profondita: int) -> Any:
        if isinstance(nodo, dict):
            riferimento = nodo.get('$ref')
            if isinstance(riferimento, str):
                # Ricorsione limitata: un $ref gia' espanso in questo ramo, o
                # troppo in profondita', resta un $ref. Meglio un contratto
                # parziale che uno schema che non finisce mai.
                if riferimento in visti or profondita > 6:
                    return {'$ref': riferimento}
                risolto = _risolvi_ref(riferimento)
                if risolto is None:
                    return {'$ref': riferimento}
                unito = {k: v for k, v in nodo.items() if k != '$ref'}
                unito.update(risolto)
                return pulisci(unito, visti | {riferimento}, profondita + 1)
            return {
                k: pulisci(v, visti, profondita)
                for k, v in nodo.items()
                if k not in ('description', '$schema', '$id', 'title')
            }
        if isinstance(nodo, list):
            return [pulisci(x, visti, profondita) for x in nodo]
        return nodo

    try:
        schema = schema_di(radice or f'{agente}.output')
    except (KeyError, FileNotFoundError):
        # Un agente senza schema di uscita (l'orchestratore conduce una
        # conversazione, non produce un documento) non ha contratto da citare.
        return ''
    return json.dumps(pulisci(schema, frozenset(), 0), ensure_ascii=False)


# --------------------------------------------------------------------------
# Chiamata al modello
# --------------------------------------------------------------------------

# Traccia delle chiamate: serve a rendere misurabile quello che il repository
# afferma (tempi e token per agente). Non e' logging di servizio, e' l'evidenza
# numerica del model tiering e del pre-filtro. Nessun contenuto, solo metriche.
TRACCIA: list[dict] = []


def azzera_traccia() -> None:
    TRACCIA.clear()


def _registra(voce: dict) -> None:
    TRACCIA.append(voce)



def _chiama(agente: str, messaggi: list[dict], sistema: str) -> str:
    """Una chiamata al modello dell'agente, con timeout e retry con backoff.

    Alza ErroreModello quando ha finito i tentativi o quando l'errore non e'
    ritentabile. Non restituisce mai una stringa vuota.
    """
    if DEMO_MODE:
        # Stessa funzione, sorgente diversa: da qui in poi il percorso e'
        # identico a quello reale, validazione di schema compresa.
        return demo.risposta_registrata(agente, messaggi)

    modello = modello_di(agente)
    ultimo: ErroreModello | None = None

    for tentativo in range(MAX_RETRY + 1):
        avvio = time.perf_counter()
        try:
            risposta = _client_anthropic().messages.create(
                model=modello,
                max_tokens=max_token_di(agente),
                # Acceso o spento per agente, da config.PENSIERO_PER_AGENTE: sui
                # modelli correnti il ragionamento e' attivo di default e i suoi
                # token escono da 'max_tokens' (C5).
                **parametri_pensiero(agente),
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
            uso = getattr(risposta, 'usage', None)
            _registra({
                'agente': agente,
                'modello': modello,
                'tentativo': tentativo,
                'secondi': round(time.perf_counter() - avvio, 2),
                'token_in': getattr(uso, 'input_tokens', None),
                'token_out': getattr(uso, 'output_tokens', None),
                'stop': getattr(risposta, 'stop_reason', None),
            })
            if not testo:
                # Distinzione che vale novanta secondi: una risposta vuota per
                # troncamento ('max_tokens') e' deterministica, e ritentarla
                # produce quattro volte lo stesso nulla. Si fallisce subito e si
                # dice quale parametro va corretto (C3).
                troncata = getattr(risposta, 'stop_reason', None) == 'max_tokens'
                raise ErroreModello(
                    'risposta senza testo: budget di max_tokens esaurito '
                    f'({max_token_di(agente)}) prima del contenuto'
                    if troncata else 'risposta vuota dal modello',
                    motivo='budget_esaurito' if troncata else 'risposta_vuota',
                    ritentabile=not troncata,
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

# Il contratto si spedisce con la domanda, non dopo il rifiuto. Prima lo schema
# compariva solo nella ri-richiesta: l'agente scopriva i campi obbligatori dopo
# aver sbagliato, e quell'errore costava una seconda chiamata intera. Lo schema
# compattato e' deterministico e viaggia nel blocco di sistema, quindi la cache
# lo fa pagare una volta sola (F2).
ISTRUZIONE_SCHEMA = (
    "\n\nSchema di output da rispettare alla lettera (JSON Schema, descrizioni "
    "rimosse). Ogni voce di 'required' e' obbligatoria, ogni 'enum' e' chiuso, e "
    "ogni blocco 'if/then' e' una regola condizionale che vale quanto gli altri "
    "vincoli. Un valore 'const' si copia carattere per carattere. Un campo "
    "facoltativo che non sai valorizzare si OMETTE: scriverlo a null non lo "
    "rende facoltativo, lo rende non conforme.\n{schema}"
)

# Le regole che legano fra loro piu' campi non si leggono bene in un if/then
# annidato, e sono esattamente quelle su cui un output sbaglia. Si ripetono in
# chiaro, per il solo agente che le ha.
REGOLE_CONDIZIONALI = {
    'eligibility': (
        "\n\nRegole condizionali di eligibility, da verificare prima di "
        "rispondere:\n"
        "1. payload.escalation false -> NON mettere ne' 'ambito_escalation' ne' "
        "'motivo_escalation': i campi vanno omessi, non messi a null.\n"
        "2. payload.escalation true -> servono tutti e tre: 'ambito_escalation', "
        "'motivo_escalation', 'spiegazione_escalation'.\n"
        "3. ambito_escalation 'sessione' -> status vale 'hitl_required' e "
        "'misure_pertinenti' e' vuoto.\n"
        "4. ambito_escalation 'misura' -> status resta 'ok' e ogni misura in "
        "'misure_pertinenti' ha confidence almeno 0.6.\n"
        "5. confidence dell'envelope sotto 0.6 -> payload.escalation deve essere "
        "true.\n"
        "6. Ogni voce di 'misure_pertinenti' richiede: misura_id, nome, "
        "titolo_semplice, tipo, confidence, motivazione, corrispondenze_profilo "
        "(almeno uno), requisiti_da_verificare (array, anche vuoto), source_refs "
        "(almeno uno). 'rilevanza' e' facoltativo: 'alta' solo con confidence "
        "almeno 0.85, 'media' solo fra 0.6 e 0.85.\n"
        "7. 'misure_escluse' e' obbligatorio (array, anche vuoto); con "
        "motivo_esclusione 'requisito_non_soddisfatto' serve anche "
        "'requisito_id'.\n"
        "8. 'disclaimer' va copiato alla lettera dallo schema, senza una virgola "
        "di differenza.\n"
        "9. Nessun campo fuori da quelli elencati: additionalProperties e' "
        "false.\n"
        "10. Un requisito che il profilo non permette di verificare va in "
        "'requisiti_da_verificare' della misura: non e' un motivo di "
        "esclusione. Si esclude una misura solo quando una risposta del "
        "profilo contraddice davvero un requisito obbligatorio "
        "('requisito_non_soddisfatto') o quando la misura non risponde a "
        "nessuna delle situazioni di vita dichiarate "
        "('situazione_non_pertinente').\n"
        "11. 'situazione_non_pertinente' e' un confronto fra due liste, non un "
        "giudizio: vale solo se NESSUNA delle "
        "'situazioni_vita_collegate' della misura compare in "
        "'situazioni_vita' del profilo. Se la situazione combacia, la misura "
        "si valuta sui requisiti."
    ),
    'navigator': (
        "\n\nRegole condizionali di navigator, da verificare prima di "
        "rispondere:\n"
        "1. 'passi' deve contenere almeno un passo: un percorso senza passi "
        "non viene mostrato alla persona e la misura sparisce dalla scheda. Se "
        "la fonte non basta per ricostruire l'intera procedura, scrivi i passi "
        "che la fonte sostiene e dichiara il resto nella 'nota' del passo, con "
        "status 'degraded'. 'degraded' qualifica un percorso parziale, non "
        "sostituisce il percorso.\n"
        "2. Ogni passo richiede 'ordine' (progressivo da 1), 'azione', 'dove' "
        "(enum) e 'source_refs' (almeno uno).\n"
        "3. 'primo_passo_concreto' e' il primo passo di QUESTA misura, non una "
        "priorita' fra misure diverse.\n"
        "4. 'difficolta' (dell'intero percorso) e 'autonomia' (del singolo "
        "passo) sono campi diversi con enum diversi: non scambiare i valori "
        "dell'uno con quelli dell'altro.\n"
        "5. Al massimo sei passi, e ogni 'azione' e' una frase sola. Non e' un "
        "risparmio di spazio: un elenco di dodici passi con tre righe l'uno "
        "non si segue, e una persona che non capisce il passo due non arriva "
        "al passo tre."
    ),
}


# L'ultima riga del contesto e' quella che pesa di piu'. Una regola su un
# singolo campo, sepolta in fondo a ventimila caratteri di prompt di sistema,
# viene ignorata: misurato, quattro volte su cinque. Gli stessi caratteri messi
# in coda al messaggio - cioe' l'ultima cosa che il modello legge prima di
# rispondere - reggono. Qui stanno solo gli errori osservati davvero, uno per
# riga: non e' un secondo prompt, e' l'errata corrige del primo.
PROMEMORIA_FINALE = {
    'navigator': (
        "\n\nPrima di rispondere, tre controlli sui campi che si sbagliano "
        "piu' spesso:\n"
        "- 'difficolta' e' dell'intero percorso e ammette SOLO 'facile', "
        "'medio' o 'richiede_professionista'. I valori 'da_soli', "
        "'con_assistenza' e 'serve_professionista' appartengono ad "
        "'autonomia', che e' un campo del singolo passo: non scambiarli.\n"
        "- 'passi' non puo' essere vuoto.\n"
        "- nessun campo valorizzato a null: se non lo sai e' facoltativo, "
        "omettilo."
    ),
    'eligibility': (
        "\n\nPrima di rispondere, due controlli:\n"
        "- 'disclaimer' va copiato dallo schema carattere per carattere.\n"
        "- 'corrispondenze_profilo' usa gli identificativi delle domande "
        "('situazione_vita', 'condizione_abitativa', 'tipo_reddito', "
        "'timing', 'caf'), non i nomi dei campi del profilo."
    ),
}


def esegui_agente(agente: str, contenuto_utente: Any, *, valida: bool = True) -> dict:
    """Esegue un agente e restituisce un output gia' validato, o un degradato.

    Il percorso e': chiamata (con retry) -> parsing -> validazione di schema ->
    al massimo una ri-richiesta con gli errori in chiaro -> fallback degradato.
    Non alza mai: chi chiama legge 'status' e decide (D1).
    """
    if agente not in TIER_PER_AGENTE:
        raise KeyError(f'agente non previsto dall\'architettura: {agente}')

    sistema = (
        _prompt(agente)
        + ISTRUZIONE_FORMATO.format(agente=agente)
        + (ISTRUZIONE_SCHEMA.format(schema=_schema_compatto(agente))
           if _schema_compatto(agente) else '')
        + REGOLE_CONDIZIONALI.get(agente, '')
    )
    corpo = (
        contenuto_utente if isinstance(contenuto_utente, str)
        else json.dumps(contenuto_utente, ensure_ascii=False)
    )
    messaggi = [{'role': 'user', 'content': corpo + PROMEMORIA_FINALE.get(agente, '')}]

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

        _registra({'agente': agente, 'giro': giro, 'errori_schema': list(errori)})

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


def e_fallback(uscita: dict) -> bool:
    """Distingue il fallback tecnico dall'esito legittimo.

    Un agente che restituisce 'hitl_required' sta facendo il suo lavoro: ha un
    payload conforme e dichiara che serve una persona. Il fallback costruito da
    questo modulo, invece, non ha contenuto di dominio e si riconosce da
    'motivo_tecnico'. Trattarli allo stesso modo farebbe sparire i gate dietro
    un messaggio di errore.
    """
    return 'motivo_tecnico' in (uscita.get('payload') or {})


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


CAMPI_RISPOSTA = ('situazione_vita', 'condizione_abitativa', 'tipo_reddito', 'timing', 'caf')


def _valori_ammessi(campo: str) -> set[str]:
    """Valori della tassonomia chiusa, letti dallo schema (E5)."""
    return set(schema_di('profiler.output')['$defs'][campo]['enum'])


def _ingresso_profiler(sessione_id: str, risposte: dict, domande_poste: list[str]) -> dict:
    """Prepara l'input del profiler separando la tassonomia dal testo libero.

    profiler.input.json accetta solo valori della tassonomia nei campi tipizzati
    e ha un campo apposta, 'testo_libero', per quello che la persona ha scritto
    o scelto in altre parole. Cosi' l'input resta conforme e il profiler ha
    comunque il materiale da normalizzare, che e' il suo mestiere.
    """
    tipizzate: dict[str, object] = {}
    residui: list[str] = []

    for campo in CAMPI_RISPOSTA:
        valore = risposte.get(campo)
        if valore is None:
            continue
        ammessi = _valori_ammessi(campo)
        if campo == 'situazione_vita':
            elenco = valore if isinstance(valore, list) else [valore]
            validi = [v for v in elenco if v in ammessi]
            residui += [str(v) for v in elenco if v not in ammessi]
            if validi:
                tipizzate[campo] = sorted(set(validi))
        elif isinstance(valore, str) and valore in ammessi:
            tipizzate[campo] = valore
        else:
            residui.append(f'{campo}: {valore}')

    ingresso = {
        'sessione_id': sessione_id,
        'risposte': tipizzate,
        'domande_poste': domande_poste or ['situazione_vita'],
    }
    if residui:
        ingresso['testo_libero'] = ' | '.join(residui)[:2000]
    return ingresso


def call_profiler(sessione_id: str, risposte: dict, domande_poste: list[str]) -> dict:
    """Normalizza le risposte nella tassonomia chiusa di profiler.output.json."""
    ingresso = _ingresso_profiler(sessione_id, risposte, domande_poste)
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
        if e_fallback(uscita):
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
    """Incrocia profilo e catalogo verificato (sonnet).

    Le voci candidate non si passano intere: si passa la proiezione ridotta di
    catalogo.proiezione_per_eligibility, cioe' l'identita' della misura piu' le
    condizioni da confrontare. Il resto della voce - la spiegazione per la
    persona, l'esito della verifica di fedelta' - non entra in questa decisione
    e costava quattro volte i token dell'informazione utile.
    """
    ingresso = {
        'profilo': profilo,
        'catalogo_versione': catalogo_versione,
        'misure_candidate': catalogo_mod.proiezione_per_eligibility(candidate),
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

    if e_fallback(uscita_eligibility):
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
            f'Il sistema non è abbastanza sicuro della lettura del tuo caso '
            f'(affidabilità {confidence:.2f}, soglia {SOGLIA_CONFIDENCE}). '
            'Preferiamo non mostrarti misure incerte: un CAF può verificare la '
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

    # Gate per singola misura: quella sotto soglia non si propone, le altre si'
    # (agents/schemas/eligibility.output.json, ambito_escalation 'misura').
    sotto_soglia = [
        m for m in misure if float(m.get('confidence', 1.0)) < SOGLIA_CONFIDENCE
    ]
    misure = [m for m in misure if m not in sotto_soglia]
    if not misure:
        motivo = 'confidence_bassa'
        messaggio = (
            'Le misure emerse hanno un margine di incertezza troppo alto per '
            'essere mostrate. Un CAF o un commercialista possono verificarle '
            'con i tuoi documenti.'
        )
        return _escalation(
            motivo, messaggio,
            eligibility=degradato_eligibility(
                payload.get('profilo_id', profilo.get('profilo_id', sessione_id)),
                versione, motivo, messaggio, status='hitl_required',
            ),
        )

    # Limite di iterazione: al massimo tre misure guidate per sessione.
    misure = misure[:MAX_MISURE_NAVIGATOR]

    # Il navigator gira una volta per misura e le misure non si parlano fra
    # loro: sono chiamate indipendenti, quindi si fanno insieme. In sequenza
    # ogni misura aggiungeva il suo tempo pieno a quello della sessione, e la
    # persona aspettava la somma invece del massimo. I gate restano gli stessi
    # e l'ordine del risultato resta quello del catalogo: si ricompone per
    # indice, non per ordine di arrivo (un ordine che cambia a ogni run
    # sarebbe una graduatoria involontaria).
    voci_da_guidare = [
        (i, v) for i, v in (
            (i, catalogo_mod.voce_per_id(m.get('misura_id'), catalogo))
            for i, m in enumerate(misure)
        ) if v is not None
    ]
    uscite: dict[int, dict] = {}
    if len(voci_da_guidare) == 1:
        indice, voce = voci_da_guidare[0]
        uscite[indice] = call_navigator(profilo, voce)
    elif voci_da_guidare:
        with ThreadPoolExecutor(max_workers=len(voci_da_guidare)) as pool:
            futuri = {
                pool.submit(call_navigator, profilo, voce): indice
                for indice, voce in voci_da_guidare
            }
            for futuro in as_completed(futuri):
                uscite[futuri[futuro]] = futuro.result()

    percorsi: list[dict] = []
    for indice, _ in voci_da_guidare:
        uscita_navigator = uscite[indice]
        # Gate: un percorso senza passi non si mostra, la misura si salta.
        if e_fallback(uscita_navigator) or not uscita_navigator.get('payload', {}).get('passi'):
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

    Tre scelte di questo livello vale la pena dichiararle:

    1. non esce nessun punteggio, nessuna etichetta di probabilita' e nessun
       ordinamento per valore. Dire a una persona "molto probabile" e' una
       previsione sul suo caso, e mettere una misura sopra un'altra e' una
       raccomandazione implicita: il tema vieta entrambe (G-04, G-18, G-21).
       L'unica sfumatura che sopravvive e' per requisito, neutra: "da
       verificare con un CAF";
    2. gli elenchi restano elenchi. Il catalogo tiene `a_chi_spetta` e
       `attenzione` come array, una frase per riga: appiattirli in un
       paragrafo unico produceva blocchi da cinquecento caratteri;
    3. il primo passo e' di ogni misura, non della sessione. Un "da fare
       subito" unico prende la prima misura dell'elenco e ne fa una priorita'
       che nessuno ha calcolato.
    """
    vista = {
        'status': esito.get('status', 'ok'),
        'escalation': esito.get('escalation', False),
        'messaggio_escalation': _per_la_persona(esito.get('messaggio_escalation')),
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

    spiegazioni, percorsi, riquadro = [], [], None
    for uscita in esito['navigator']:
        payload = uscita.get('payload', {})
        misura_id = payload.get('misura_id')
        voce = catalogo_mod.voce_per_id(misura_id, catalogo) or {}
        spiegazione = voce.get('spiegazione', {})
        misura = voce.get('misura', {})
        pertinente = pertinenti.get(misura_id, {})
        riferimenti = spiegazione.get('source_refs', [])

        spiegazioni.append({
            'id': misura_id,
            'titolo': spiegazione.get('titolo_semplice') or pertinente.get('nome', ''),
            'tipo': (misura.get('tipo') or pertinente.get('tipo') or '').replace('_', ' '),
            'categoria': _categoria(misura),
            'cosa_e': spiegazione.get('cosa_e', ''),
            'quanto_vale': spiegazione.get('quanto_vale', ''),
            # I numeri non si estraggono dalla prosa: stanno gia' strutturati
            # nel catalogo, ed e' l'unico posto da cui possono venire (G4).
            'cifre': _cifre(misura),
            # "Dove vado a chiederlo": la domanda che oggi resta senza risposta.
            'dove_si_fa': _dove_si_fa(misura, payload.get('passi', [])),
            # Array nel catalogo, array qui: il front-end li disegna come <ul>.
            'a_chi_spetta': list(spiegazione.get('a_chi_spetta', [])),
            'attenzione': list(spiegazione.get('attenzione', [])),
            # L'unica sfumatura ammessa: sul singolo requisito, e neutra.
            'da_verificare': _requisiti_aperti(pertinente.get('requisiti_da_verificare')),
            'glossario': [
                {'termine': g.get('termine', ''),
                 'spiegazione': g.get('spiegazione_semplice', ''),
                 'dove': g.get('dove_si_trova') or None}
                for g in spiegazione.get('glossario', [])
            ],
            'source_refs': riferimenti,
            # G-24: una fonte senza data di consultazione non e' una fonte.
            'fonti': _fonti_leggibili(riferimenti, catalogo),
            'disclaimer': spiegazione.get('disclaimer') or disclaimer(),
        })

        percorsi.append({
            'id': misura_id,
            # Il primo passo e' di questa misura: non e' la priorita' della sessione.
            'primo_passo': payload.get('primo_passo_concreto'),
            'passi': _passi_leggibili(payload.get('passi', [])),
            'avvertenza_timing': (
                payload.get('avvertenza_timing')
                or _avvertenza_timing(payload.get('scadenza_da_rispettare'))
            ),
        })
        riquadro = payload.get('riquadro_spid') or riquadro

    vista['explainer'] = {'spiegazioni': spiegazioni}
    vista['navigator'] = {
        'percorsi': percorsi,
        # Il riquadro lo scrive il contratto del navigator: e' testo di sistema,
        # non un dato della misura, e non si riformula qui.
        'riquadro_spid': {
            'mostra': bool(riquadro) or _serve_spid(esito),
            'necessario': bool((riquadro or {}).get('necessario', _serve_spid(esito))),
            'testo': (riquadro or {}).get('testo') or (
                'Molte pratiche si aprono solo con SPID, CIE o CNS. Se non li '
                'hai, un CAF puo aiutarti a ottenerli.'
            ),
        },
    }
    # Quello che non compare, e perche': e' la parte che insegna il confine.
    vista['misure_escluse'] = _misure_escluse(
        esito, catalogo, [s['id'] for s in spiegazioni]
    )
    return vista


# --- dettagli della composizione ------------------------------------------

_ENTI = {
    'agenzia_entrate': 'Agenzia delle Entrate',
    'inps': 'INPS',
    'inail': 'INAIL',
    'ministero_salute': 'Ministero della Salute',
    'comune': 'Comune',
    'regione': 'Regione',
    'altro': 'Ente pubblico',
}

_SITUAZIONI = {
    'casa': 'lavori o acquisto della casa',
    'figlio': 'figli',
    'lavoro': 'lavoro e disoccupazione',
    'spese_mediche': 'spese mediche',
    'auto': "acquisto di un'auto",
    'under36': 'avere meno di 36 anni',
    'non_so': 'una situazione non ancora definita',
}

_MOTIVI_CATALOGO = {
    'fonte_non_interpretabile': (
        "L'abbiamo cercata, ma la pagina ufficiale non era abbastanza chiara "
        'da riportarne i numeri senza rischio di sbagliare. Preferiamo non '
        'dirti niente piuttosto che dirti una cosa sbagliata.'
    ),
    'divergenza_non_risolta': (
        'Le pagine ufficiali che abbiamo letto non dicevano la stessa cosa, e '
        'non siamo riusciti a capire quale valesse. Non abbiamo scelto a caso.'
    ),
    'fonte_non_raggiungibile': (
        'La pagina ufficiale non era raggiungibile quando abbiamo controllato. '
        'Senza fonte non la mostriamo.'
    ),
}


def _data_leggibile(iso: str | None) -> str | None:
    """'2026-09-24' diventa '24/09/2026': una data che si legge, non un ISO."""
    if not iso:
        return None
    parti = str(iso)[:10].split('-')
    if len(parti) != 3:
        return str(iso)
    anno, mese, giorno = parti
    return f'{giorno}/{mese}/{anno}'


def _fonti_leggibili(source_refs: list, catalogo: dict | None) -> list[dict]:
    """Da 'ade-ristrutturazioni-cittadini#limite-di-spesa' a una riga leggibile.

    Un riferimento interno non dice niente a nessuno. Quello che serve alla
    persona e' chi lo dice e quando l'abbiamo guardato (G-24).
    """
    registro = {f.get('fonte_id'): f for f in (catalogo or {}).get('fonti', [])}
    viste, fonti = set(), []
    for riferimento in source_refs or []:
        fonte_id = str(riferimento).split('#')[0]
        if fonte_id in viste:
            continue
        viste.add(fonte_id)
        voce = registro.get(fonte_id, {})
        fonti.append({
            'ente': _ENTI.get(voce.get('ente'), voce.get('ente') or 'Fonte ufficiale'),
            'url': voce.get('url_fonte'),
            'data_consultazione': _data_leggibile(voce.get('data_consultazione')),
            'riferimento': fonte_id,
        })
    return fonti


def _passi_leggibili(passi: list) -> list[dict]:
    """I passi nella forma che il front-end disegna.

    Sulla dipendenza: un elenco numerato dice gia' che il passo 1 viene prima
    del 2. Si segnala solo il legame che l'ordine non mostra, cioe' un passo
    che dipende da un altro che non e' quello subito precedente. La versione
    precedente marcava "prima degli altri" proprio il passo 1, che e' l'unico
    per cui non serviva dirlo.
    """
    leggibili = []
    for passo in passi:
        ordine = passo.get('ordine')
        precedente = (ordine or 0) - 1
        dipendenze = [d for d in (passo.get('dipende_da') or []) if d != precedente]
        leggibili.append({
            'numero': ordine,
            'azione': passo.get('azione', ''),
            # Solo se il contratto lo dichiara: non si deduce da 'dipende_da'
            # vuoto, che e' semplicemente come si presenta il passo numero 1.
            'obbligatorio_prima': bool(passo.get('obbligatorio_prima')),
            'dopo_il_passo': dipendenze[0] if dipendenze else None,
            'nota': passo.get('nota') or passo.get('dove_dettaglio'),
        })
    return leggibili


_CATEGORIE = {
    'casa': 'casa', 'figlio': 'famiglia', 'spese_mediche': 'salute',
    'lavoro': 'lavoro', 'under36': 'lavoro', 'auto': 'auto',
}


def _categoria(misura: dict) -> str:
    """Una categoria per l'accento visivo. Non porta informazione da sola:
    accanto c'e' sempre il tipo di misura scritto in lettere."""
    for situazione in misura.get('situazioni_vita_collegate', []):
        if situazione in _CATEGORIE:
            return _CATEGORIE[situazione]
    return 'generico'


def _euro(valore: float) -> str:
    """96000 -> '96.000 €'; 203.8 -> '203,80 €'. Come si scrivono in italiano."""
    intero = float(valore)
    if abs(intero - round(intero)) < 0.005:
        testo = f'{round(intero):,}'.replace(',', '.')
    else:
        testo = f'{intero:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.')
    return testo + ' €'


def _cifre(misura: dict) -> list[dict]:
    """Le due o tre cifre che una persona cerca per prime, dal catalogo.

    Restano tre al massimo: una tessera in piu' e' una tabella, e una tabella
    non si legge in piedi davanti allo sportello.
    """
    beneficio = misura.get('beneficio') or {}
    recupero = misura.get('recupero') or {}
    forma = beneficio.get('forma')
    cifre: list[dict] = []

    if beneficio.get('percentuale') is not None:
        cifre.append({'valore': f"{beneficio['percentuale']}%",
                      'etichetta': 'di quanto spendi'})
    if beneficio.get('tetto_massimo_euro') is not None:
        cifre.append({
            'valore': _euro(beneficio['tetto_massimo_euro']),
            'etichetta': ('importo massimo indicato dalla fonte'
                          if forma == 'importo_massimo' else 'tetto massimo di spesa'),
            'dettaglio': beneficio.get('base_tetto'),
        })
    if recupero.get('rate_annuali'):
        anni = recupero['rate_annuali']
        cifre.append({'valore': f'{anni} anni',
                      'etichetta': 'in quante rate ti torna'})
    return cifre[:3]


# Canale -> come ci si arriva. La tabella e' di interfaccia, non di dominio:
# traduce i codici dell'enum in un posto dove una persona puo' andare davvero.
# Dove il collegamento esatto non e' nel catalogo si rimanda alla home
# dell'ente e lo si dice: un indirizzo inventato manda la persona a sbattere.
_CANALI = {
    'portale_inps': (
        'online', "Il sito dell'INPS", 'https://www.inps.it',
        "Entra nell'area riservata, cerca la prestazione per nome nella barra "
        'di ricerca del sito e apri la voce della domanda.',
        'SPID, CIE o CNS'),
    'portale_agenzia_entrate': (
        'online', "Il sito dell'Agenzia delle Entrate",
        'https://www.agenziaentrate.gov.it',
        "Entra nell'area riservata e cerca la sezione della misura.",
        'SPID, CIE o CNS'),
    'dichiarazione_redditi': (
        'online', 'Con la dichiarazione dei redditi',
        'https://www.agenziaentrate.gov.it',
        'Non si presenta una domanda a parte: la spesa si indica nella '
        'dichiarazione dei redditi (modello 730 o Redditi PF). Puoi farlo da '
        'solo con la dichiarazione precompilata, oppure portare i documenti a '
        'un CAF o a un commercialista, che la compilano per te.',
        'SPID, CIE o CNS per la precompilata; se ci vai di persona basta un '
        'documento e il codice fiscale'),
    'caf': ('persona', 'Un CAF', None,
            'Si va di persona, quasi sempre su appuntamento.',
            'Documento di identita e codice fiscale'),
    'commercialista': ('persona', 'Un commercialista', None,
                       'Si va di persona, su appuntamento.',
                       'Documento di identita e codice fiscale'),
    'sportello_fisico': ('persona', "Uno sportello dell'ente", None,
                         'Si va di persona: controlla gli orari prima di andare.',
                         'Documento di identita e codice fiscale'),
    'comune': ('persona', 'Il tuo Comune', None,
               "Si va all'ufficio indicato dal Comune, spesso su appuntamento.",
               'Documento di identita e codice fiscale'),
    'banca_o_posta': ('persona', 'La banca o un ufficio postale', None,
                      'Si fa allo sportello.',
                      'Documento di identita e codice fiscale'),
    'datore_di_lavoro': ('persona', "L'ufficio del personale di chi ti paga", None,
                         'La richiesta passa da chi ti paga lo stipendio.', None),
    'automatico_in_fattura': ('automatico', 'Non devi chiedere niente', None,
                              'Lo sconto lo applica direttamente chi ti fa la fattura.',
                              None),
    'altro': ('ignoto', 'La fonte non dice da dove si passa', None,
              "Non lo inventiamo. Chiedilo a un CAF o direttamente all'ente "
              'che eroga la misura.', None),
}


def _dove_si_fa(misura: dict, passi: list) -> dict:
    """Dove si va a chiederla: online, di persona, o da nessuna parte.

    Tre cose e basta: come ci si arriva, cosa serve per entrare, cosa portare.
    I documenti sono quelli del catalogo con il nome che la fonte gli da',
    non una lista di buon senso.
    """
    canali = []
    for codice in misura.get('canali_accesso') or ['altro']:
        modo, nome, url, percorso, serve = _CANALI.get(codice, _CANALI['altro'])
        canali.append({'modo': modo, 'nome': nome, 'url': url,
                       'percorso': percorso, 'serve': serve})

    # Se un passo porta un dettaglio sul luogo, vale piu' della tabella.
    dettagli = [p.get('dove_dettaglio') for p in passi if p.get('dove_dettaglio')]

    documenti = [
        {'nome': d.get('nome') or d.get('tipo_documento'),
         'obbligatorio': bool(d.get('obbligatorio'))}
        for d in (misura.get('documenti_richiesti') or [])
        if d.get('nome') or d.get('tipo_documento')
    ]
    return {'canali': canali, 'dettagli': dettagli, 'documenti': documenti}


def _requisiti_aperti(requisiti: list | None) -> list[str]:
    """I requisiti che il sistema non puo' verificare, in frasi leggibili.

    Non e' una probabilita' sul caso della persona: e' l'elenco di cosa
    manca per saperlo, che e' l'unica sfumatura che il tema consente.
    """
    aperti = []
    for requisito in requisiti or []:
        if isinstance(requisito, str):
            aperti.append(requisito)
            continue
        testo = (requisito.get('da_verificare_perche')
                 or requisito.get('descrizione')
                 or requisito.get('requisito_id'))
        if testo:
            aperti.append(str(testo))
    return aperti


def _misure_escluse(esito: dict, catalogo: dict | None, mostrate: list) -> list[dict]:
    """Cosa non compare nella scheda, e perche'.

    Tre origini, tutte oneste e tutte diverse: quello che l'agente ha valutato
    e scartato per questo profilo, quello che il catalogo contiene ma non
    riguarda la situazione descritta, e quello che la Fase A non e' riuscita a
    verificare e ha tenuto fuori dal catalogo.
    """
    escluse, viste = [], set(mostrate)

    payload = (esito.get('eligibility') or {}).get('payload', {})
    for misura in payload.get('misure_escluse', []) or []:
        identificativo = misura.get('misura_id')
        if identificativo in viste:
            continue
        viste.add(identificativo)
        dal_catalogo = catalogo_mod.voce_per_id(identificativo, catalogo) or {}
        escluse.append({
            'nome': (dal_catalogo.get('spiegazione', {}).get('titolo_semplice')
                     or dal_catalogo.get('misura', {}).get('nome')
                     or misura.get('nome') or identificativo),
            'motivo': (
                misura.get('motivo_leggibile')
                or misura.get('motivo_esclusione')
                or _MOTIVI_CATALOGO.get(misura.get('motivo'))
                or 'Da quello che hai risposto non risulta la condizione che chiede.'
            ),
        })

    for voce in catalogo_mod.voci(catalogo):
        misura = voce.get('misura', {})
        identificativo = misura.get('misura_id')
        if identificativo in viste:
            continue
        viste.add(identificativo)
        collegate = [
            _SITUAZIONI.get(s, s)
            for s in misura.get('situazioni_vita_collegate', [])
        ]
        escluse.append({
            'nome': (voce.get('spiegazione', {}).get('titolo_semplice')
                     or misura.get('nome')),
            'motivo': (
                'Riguarda una situazione diversa da quella che hai descritto: '
                + ', '.join(collegate) + '.'
                if collegate else
                'Da quello che hai risposto non risulta la condizione che chiede.'
            ),
        })

    for misura in (catalogo or {}).get('misure_escluse', []) or []:
        escluse.append({
            'nome': misura.get('nome') or misura.get('misura_id'),
            'motivo': _MOTIVI_CATALOGO.get(
                misura.get('motivo'),
                'Non siamo riusciti a verificarla su una fonte ufficiale, '
                'quindi non la mostriamo.',
            ),
        })

    return escluse


def _per_la_persona(messaggio: str | None) -> str | None:
    """Toglie dal messaggio di escalation quello che parla solo a noi.

    'affidabilita 0.45, soglia 0.6' e' una soglia interna: alla persona non
    dice niente e sembra un verdetto sul suo caso.
    """
    if not messaggio:
        return messaggio
    ripulito = re.sub(
        r'\s*\([^)]*(?:affidabilit|soglia|confidence)[^)]*\)', '', messaggio
    )
    ripulito = ripulito.replace(
        'catalogo verificato', 'le fonti ufficiali che abbiamo letto'
    )
    ripulito = ripulito.replace('nel catalogo', 'fra le fonti che abbiamo letto')
    return re.sub(r'\s{2,}', ' ', ripulito).strip()


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


# --------------------------------------------------------------------------
# Questionario deterministico (Fase B, passo 0)
# --------------------------------------------------------------------------

# Le cinque domande non le genera il modello: stanno qui, fisse, nell'ordine
# della specifica, con le etichette copiate alla lettera dalla tabella di
# agents/subagents/profiler.md. Il motivo non e' il risparmio di token, anche
# se il risparmio c'e' (quattro invocazioni in meno per sessione): una domanda
# riformulata a ogni sessione e' un difetto di prodotto. Chi usa questo
# servizio sta gia' affrontando un problema, e un questionario che cambia
# parole a ogni giro lo disorienta, salta la domanda che regge tutto e non e'
# riproducibile in collaudo.
#
# Al modello resta il lavoro che e' suo: il profiler normalizza le risposte
# sulla tassonomia chiusa e produce il profilo. Qui si sceglie fra opzioni
# gia' scritte, e questo un dizionario lo fa meglio di un LLM.

QUESTIONARIO: tuple[dict, ...] = (
    {
        'id': 'situazione_vita',
        'testo': 'Cosa sta succedendo nella tua vita in questo momento?',
        'nota': 'Puoi indicare piú di una cosa.',
        'multipla': True,
        'opzioni': (
            ('casa', 'Sto per comprare o ristrutturare casa',
             ('casa', 'ristruttur', 'immobile', 'abitazione')),
            ('figlio', 'Ho avuto o aspetto un figlio',
             ('figlio', 'figli', 'bambin', 'nato', 'nascita')),
            ('lavoro', 'Ho perso il lavoro o sto cercando occupazione',
             ('lavoro', 'disoccupat', 'licenziat', 'occupazione')),
            ('spese_mediche', 'Ho avuto spese mediche importanti',
             ('medic', 'salute', 'sanitar', 'ospedale')),
            ('auto', 'Voglio acquistare un’auto nuova',
             ('auto', 'macchina', 'veicolo')),
            ('under36', 'Ho meno di 36 anni e voglio sapere a cosa ho diritto',
             ('under36', 'under 36', '36 anni', 'giovane')),
            ('non_so', 'Non so da dove partire, mostrami tutto',
             ('non so', 'non lo so', 'mostrami tutto', 'boh')),
        ),
    },
    {
        'id': 'condizione_abitativa',
        'testo': 'Riguardo alla casa in cui vivi:',
        # Condizionale, come prescrive profiler.md: chiederla a chi ha parlato
        # di figli o di spese mediche vuol dire chiedere un dato che non entra
        # in nessuna misura del catalogo.
        'solo_se': ('casa', 'under36'),
        'opzioni': (
            ('proprietario', 'Sono proprietario dell’immobile',
             ('propriet', 'é mia', 'di mia propriet')),
            ('affittuario', 'Sono in affitto', ('affitt', 'inquilin')),
            ('ospite_familiari', 'Vivo in una casa di un familiare',
             ('familiar', 'ospite', 'genitor')),
            ('non_so', 'Non lo so con certezza', ('non so', 'non lo so', 'boh')),
        ),
    },
    {
        'id': 'tipo_reddito',
        'testo': 'Hai un reddito in questo momento?',
        'opzioni': (
            ('lavoro_dipendente', 'Sì, lavoro come dipendente',
             ('dipendent', 'assunt', 'stipendio')),
            ('pensione', 'Sì, sono in pensione', ('pension',)),
            ('partita_iva', 'Sì, ho la partita IVA',
             ('partita iva', 'p.iva', 'piva', 'autonom', 'libero profession')),
            ('nessun_reddito',
             'No: sono disoccupato, oppure a carico di un familiare',
             ('nessun reddito', 'disoccupat', 'a carico', 'non lavoro')),
            ('non_so', 'Non lo so', ('non so', 'non lo so', 'boh')),
        ),
    },
    {
        'id': 'caf',
        'testo': 'Hai già qualcuno che ti aiuta con le tasse e la burocrazia?',
        'opzioni': (
            ('si', 'Sì, ho un commercialista oppure vado al CAF',
             ('commercialista', 'vado al caf', 'ho un caf', 'patronato')),
            ('no', 'No, faccio tutto da solo',
             ('faccio tutto da solo', 'da solo', 'da sola', 'nessuno')),
            ('non_so_cosa_e', 'Non so cos’è un CAF',
             ('non so cos', 'che cos’è un caf', 'cosa e un caf', 'cos\'e un caf')),
        ),
    },
    {
        'id': 'timing',
        'testo': 'A che punto sei con quello che vuoi fare?',
        # Condizionale come la precedente, e per lo stesso motivo. 'A che punto
        # sei' presuppone che ci sia un prima e un dopo: vale per dei lavori o
        # per l'acquisto di un'auto. Non vale per un figlio gia' nato, per una
        # spesa medica gia' sostenuta o per chi ha appena detto che non sa da
        # dove partire: a quella persona la domanda arriva come una domanda
        # senza senso, e un sistema che fa domande senza senso perde la fiducia
        # di chi lo sta usando per la prima volta.
        'solo_se': ('casa', 'auto'),
        'opzioni': (
            ('da_iniziare', 'Devo ancora iniziare, sto raccogliendo informazioni',
             ('ancora', 'devo iniziare', 'non ho iniziato', 'raccogliendo')),
            ('in_corso', 'Ho già iniziato: lavori, pratiche o acquisti in corso',
             ('in corso', 'già iniziat', 'gia iniziat', 'sto facendo')),
            ('gia_concluso',
             'Ho già finito, voglio recuperare agevolazioni del passato',
             ('finito', 'concluso', 'passato', 'recuperare')),
            ('non_so', 'Non lo so', ('non so', 'non lo so', 'boh')),
        ),
    },
)

# Glossario imposto dalla specifica: chi non sa che cosa sia un CAF riceve la
# spiegazione subito, prima di proseguire, non alla fine.
SPIEGAZIONE_CAF = (
    'Il CAF, Centro di Assistenza Fiscale, è uno sportello dove dei '
    'professionisti ti aiutano con la dichiarazione dei redditi, i bonus e le '
    'pratiche. Lo trovi nei patronati, nei sindacati e in molti comuni.'
)

SALUTO = (
    'Ciao. Ti faccio cinque domande per capire quali aiuti pubblici riguardano '
    'la tua situazione. Nessuna richiede documenti, e a ognuna puoi rispondere '
    '"non lo so".'
)


def domanda_da_porre(risposte: dict) -> dict | None:
    """Prima domanda del questionario ancora senza risposta, o None se finito.

    Salta la domanda condizionale quando la specifica dice di saltarla: una
    domanda che non cambia nessuna risposta e' tempo tolto alla persona.
    """
    situazioni = set(risposte.get('situazione_vita') or [])
    for domanda in QUESTIONARIO:
        if domanda['id'] in risposte:
            continue
        vincolo = domanda.get('solo_se')
        if vincolo and not situazioni.intersection(vincolo):
            continue
        return domanda
    return None


def domande_previste(risposte: dict) -> list[str]:
    """Le domande che questo percorso porra' davvero, condizionali comprese.

    Serve al contatore dell'interfaccia: promettere cinque domande e farne
    quattro e' una piccola bugia, e a un servizio pubblico le piccole bugie si
    pagano tutte. Finche' la situazione di vita non e' nota le condizionali non
    sono decidibili, e si dichiara il numero massimo.
    """
    situazioni = set(risposte.get('situazione_vita') or [])
    if not situazioni:
        return [d['id'] for d in QUESTIONARIO]
    return [
        d['id'] for d in QUESTIONARIO
        if not d.get('solo_se') or situazioni.intersection(d['solo_se'])
    ]


def testo_domanda(domanda: dict) -> str:
    """La domanda come la legge la persona: testo, opzioni numerate, nota."""
    righe = [domanda['testo']]
    righe += [
        f'{i}. {etichetta}'
        for i, (_, etichetta, _) in enumerate(domanda['opzioni'], start=1)
    ]
    if domanda.get('nota'):
        righe.append(domanda['nota'])
    return '\n'.join(righe)


def opzioni_domanda(domanda: dict) -> list[dict]:
    """Le opzioni in forma strutturata, per chi disegna dei bottoni."""
    return [
        {'valore': valore, 'etichetta': etichetta}
        for valore, etichetta, _ in domanda['opzioni']
    ]


def _riconosci(domanda: dict, testo: str) -> list[str]:
    """Valori della tassonomia riconosciuti nella risposta, senza modello.

    Tre modi, in quest'ordine: il numero dell'opzione, il valore o l'etichetta
    per intero, una parola chiave. Nessuna inferenza: cio' che non corrisponde
    non produce un valore, produce una ri-domanda.
    """
    pulito = ' '.join(str(testo or '').lower().split()).strip(' .')
    if not pulito:
        return []
    trovati: list[str] = []
    for indice, (valore, etichetta, parole) in enumerate(domanda['opzioni'], start=1):
        # Il numero vale solo se e' tutta la risposta: in "ho 36 anni" non c'e'
        # l'opzione 3.
        esatti = {str(indice), f'{indice})', valore, valore.replace('_', ' '),
                  etichetta.lower()}
        if pulito in esatti:
            trovati.append(valore)
            continue
        if etichetta.lower() in pulito or any(p in pulito for p in parole):
            trovati.append(valore)
    ordinati = [v for v, _, _ in domanda['opzioni'] if v in trovati]
    if not domanda.get('multipla'):
        return ordinati[:1]
    # 'non_so' vuol dire "mostrami tutto": accanto a una scelta precisa e' rumore.
    if len(ordinati) > 1 and 'non_so' in ordinati:
        ordinati = [v for v in ordinati if v != 'non_so']
    return ordinati


def avanza_questionario(risposte: dict, messaggio_utente: str | None) -> dict:
    """Un turno di questionario, senza nessuna chiamata al modello.

    Restituisce sempre la stessa forma: che cosa dire alla persona, quali
    opzioni mostrarle, le risposte raccolte finora e se il questionario e'
    finito. Chi chiama non deve sapere com'e' fatto il questionario.
    """
    risposte = dict(risposte or {})
    premessa: list[str] = []
    in_attesa = domanda_da_porre(risposte)

    if messaggio_utente is not None and in_attesa is not None:
        riconosciuti = _riconosci(in_attesa, messaggio_utente)
        if riconosciuti:
            risposte[in_attesa['id']] = (
                riconosciuti if in_attesa.get('multipla') else riconosciuti[0]
            )
            if in_attesa['id'] == 'caf' and riconosciuti[0] == 'non_so_cosa_e':
                premessa.append(SPIEGAZIONE_CAF)
            in_attesa = domanda_da_porre(risposte)
        else:
            # Non si indovina: si ripete la domanda. Registrare qui un valore a
            # caso significherebbe orientare una persona su un profilo falso.
            premessa.append(
                'Non sono sicuro di aver capito: scegli una delle opzioni qui '
                'sotto, con il numero o con le tue parole.'
            )

    previste = domande_previste(risposte)
    if in_attesa is None:
        return {
            'testo': '\n\n'.join(premessa + [
                'Ho raccolto le tue risposte. Sto controllando il catalogo verificato.'
            ]),
            'opzioni': [],
            'domanda_id': None,
            'numero_domanda': len(previste),
            'totale_domande': len(previste),
            'risposte': risposte,
            'completo': True,
        }

    if messaggio_utente is None:
        premessa.insert(0, SALUTO)
    return {
        'testo': '\n\n'.join(premessa + [testo_domanda(in_attesa)]),
        'opzioni': opzioni_domanda(in_attesa),
        'domanda_id': in_attesa['id'],
        # Posizione reale nel percorso di questa persona, non in un percorso
        # ideale di cinque domande che quasi nessuno fa per intero.
        'numero_domanda': (previste.index(in_attesa['id']) + 1
                           if in_attesa['id'] in previste else len(previste)),
        'totale_domande': len(previste),
        'risposte': risposte,
        'completo': False,
    }


def domande_poste(risposte: dict) -> list[str]:
    """Le domande mostrate davvero: distingue 'non chiesto' da 'non risposto'."""
    poste = [d['id'] for d in QUESTIONARIO if d['id'] in risposte]
    return poste or ['situazione_vita']
