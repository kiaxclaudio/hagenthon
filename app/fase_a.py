"""Fase A - costruzione del catalogo verificato. Gira offline, una volta sola.

    fonte ufficiale -> source-analyzer (opus) -> explainer (sonnet) -> fidelity-validator (opus)
                                                       ^                        |
                                                       +------- respinto -------+
                                                          massimo 2 giri, poi HITL

Il ciclo explainer <-> fidelity-validator ha un limite duro di due giri: alla
seconda bocciatura la misura non entra nel catalogo, finisce in 'misure_escluse'
con verdetto hitl_required e la rivede una persona. Al superamento di un limite
si escala, non si ritenta (D3, D4).

Uso:
    python app/fase_a.py                 # legge agents/state/fonti/
    python app/fase_a.py --fonti CARTELLA
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from agents import call_explainer, call_fidelity_validator, esegui_agente
import catalogo as catalogo_mod
from config import FONTI_DIR, MAX_GIRI_FIDELITY, MISURE_GREZZE_PATH, assicura_state_dir
from validation import ora

ESTENSIONI = {'.txt', '.md', '.html', '.htm', '.json'}
FORMATO_PER_ESTENSIONE = {
    '.txt': 'testo', '.md': 'testo', '.html': 'html', '.htm': 'html', '.json': 'json',
}


def _metadati(percorso: Path) -> dict:
    """Metadati della fonte: da <nome>.meta.json se c'e', altrimenti i default.

    La provenienza non si indovina: se il file affianco non la dichiara, l'ente
    resta generico e la data di consultazione e' quella di oggi.
    """
    sidecar = percorso.with_suffix(percorso.suffix + '.meta.json')
    base = {
        'fonte_id': percorso.stem.lower().replace('_', '-'),
        'ente': 'altro_ente_pubblico',
        'data_consultazione': date.today().isoformat(),
    }
    if sidecar.exists():
        try:
            base.update(json.loads(sidecar.read_text(encoding='utf-8')))
        except (json.JSONDecodeError, OSError) as errore:
            print(f'  ! metadati ignorati ({sidecar.name}): {errore}')
    return base


def analizza_fonte(percorso: Path, anno: int) -> dict:
    """source-analyzer su una fonte: destruttura il testo in misure con i numeri."""
    meta = _metadati(percorso)
    ingresso = {
        'fonte_id': meta['fonte_id'],
        'ente': meta['ente'],
        'formato': FORMATO_PER_ESTENSIONE.get(percorso.suffix.lower(), 'testo'),
        'contenuto_grezzo': percorso.read_text(encoding='utf-8', errors='replace'),
        'data_consultazione': meta['data_consultazione'],
        'anno_imposta': anno,
    }
    if meta.get('url_fonte'):
        ingresso['url_fonte'] = meta['url_fonte']
    return esegui_agente('source-analyzer', ingresso)


def costruisci_voce(misura: dict) -> tuple[dict | None, dict | None]:
    """Ciclo explainer <-> fidelity-validator su una misura.

    Restituisce (voce_di_catalogo, None) se approvata, (None, esclusione) se
    dopo MAX_GIRI_FIDELITY giri il validatore la respinge ancora.
    """
    divergenze: list[dict] = []
    ultima_spiegazione: dict | None = None

    for giro in range(1, MAX_GIRI_FIDELITY + 1):
        uscita_explainer = call_explainer({
            'misura': misura,
            'iterazione': giro,
            'divergenze_da_correggere': divergenze,
        })
        if uscita_explainer.get('status') != 'ok':
            return None, _esclusione(misura, 'dati_numerici_mancanti', divergenze)

        ultima_spiegazione = uscita_explainer['payload']

        uscita_validator = call_fidelity_validator({
            'misura': misura,
            'spiegazione': ultima_spiegazione,
            'iterazione': giro,
            'divergenze_giro_precedente': divergenze,
        })
        if uscita_validator.get('status') != 'ok':
            return None, _esclusione(misura, 'fonte_non_interpretabile', divergenze)

        verdetto = uscita_validator['payload']
        divergenze = verdetto.get('divergenze', [])

        if verdetto.get('verdict') == 'approved':
            return {
                'misura': misura,
                'spiegazione': ultima_spiegazione,
                'verifica': {
                    'verdict': 'approved',
                    'iterazioni': giro,
                    'validato_il': ora(),
                    'confidence': max(0.6, float(uscita_validator.get('confidence', 0.6))),
                    'divergenze_residue': divergenze,
                },
                'pubblicata_il': ora(),
            }, None

        print(f"  - giro {giro}: respinta, {len(divergenze)} divergenze")

    # Limite superato: si escala, non si ritenta.
    return None, _esclusione(misura, 'doppio_rifiuto_validator', divergenze)


def _esclusione(misura: dict, motivo: str, divergenze: list[dict]) -> dict:
    return {
        'misura_id': misura.get('misura_id', 'misura-senza-id'),
        'nome': misura.get('nome', 'misura senza nome'),
        'motivo': motivo,
        'divergenze_residue': divergenze,
        'escluso_il': ora(),
        'source_refs': misura.get('source_refs') or ['fonte-non-dichiarata'],
    }


def costruisci_catalogo(cartella_fonti: Path, anno: int, versione: str) -> int:
    """Esegue la Fase A su tutte le fonti e scrive agents/state/catalogo.json."""
    assicura_state_dir()
    fonti_file = sorted(
        p for p in cartella_fonti.glob('*')
        if p.suffix.lower() in ESTENSIONI and not p.name.endswith('.meta.json')
    ) if cartella_fonti.exists() else []

    if not fonti_file:
        print(
            f'Nessuna fonte in {cartella_fonti}.\n'
            'Salva li\' le pagine ufficiali (Agenzia delle Entrate, INPS) come .txt o '
            '.html e rilancia. Senza fonti non si costruisce un catalogo: i numeri '
            'non si prendono dalla memoria del modello.'
        )
        return 1

    fonti_catalogo, voci, escluse, grezze = [], [], [], []

    for percorso in fonti_file:
        print(f'Fonte: {percorso.name}')
        meta = _metadati(percorso)
        uscita = analizza_fonte(percorso, anno)

        if uscita.get('status') != 'ok':
            # Gate HITL: fonte non interpretabile, la Fase A si ferma su questa fonte.
            print(f"  ! saltata: {uscita.get('payload', {}).get('motivo_tecnico', uscita.get('status'))}")
            continue

        payload = uscita['payload']
        fonti_catalogo.append({
            'fonte_id': payload['fonte_id'],
            'ente': meta['ente'],
            **({'url_fonte': meta['url_fonte']} if meta.get('url_fonte') else {}),
            'data_consultazione': payload['data_consultazione'],
        })
        grezze.extend(payload.get('misure', []))

        for misura in payload.get('misure', []):
            print(f"  misura: {misura.get('misura_id')}")
            voce, esclusione = costruisci_voce(misura)
            if voce:
                voci.append(voce)
            else:
                escluse.append(esclusione)

    MISURE_GREZZE_PATH.write_text(
        json.dumps(grezze, ensure_ascii=False, indent=2), encoding='utf-8'
    )

    catalogo = {
        'catalogo_id': 'catalogo-aiuti-italia',
        'versione': versione,
        'generato_il': ora(),
        'anno_imposta_riferimento': anno,
        'fonti': fonti_catalogo,
        'voci': voci,
        'misure_escluse': escluse,
    }

    errori = catalogo_mod.salva(catalogo)
    if errori:
        print('Catalogo NON scritto: non rispetta agents/schemas/catalogo.json')
        for errore in errori:
            print(f'  - {errore}')
        return 1

    print(
        f'\nCatalogo scritto: {len(voci)} voci approvate, '
        f'{len(escluse)} escluse (rivedibili da una persona).'
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Fase A: costruisce il catalogo verificato.')
    parser.add_argument('--fonti', type=Path, default=FONTI_DIR,
                        help='cartella con le fonti ufficiali salvate su file')
    parser.add_argument('--anno', type=int, default=date.today().year,
                        help='anno di imposta di riferimento')
    parser.add_argument('--versione', default='1.0.0', help='versione del catalogo (semver)')
    argomenti = parser.parse_args(argv)
    return costruisci_catalogo(argomenti.fonti, argomenti.anno, argomenti.versione)


if __name__ == '__main__':
    sys.exit(main())
