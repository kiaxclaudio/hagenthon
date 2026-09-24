"""
Genera i 4 file di validazione in docs/validation/ chiamando la pipeline direttamente.
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Aggiungi app/ al path per importare agents
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))
os.chdir(Path(__file__).parent.parent)

from agents import call_eligibility, call_navigator

SCENARIOS = [
    {
        "id": "scenario-01-ristrutturazione",
        "descrizione": "Proprietario, dipendente, ristrutturazione da iniziare",
        "profilo": {
            "situazione_vita": "Sto per comprare o ristrutturare casa",
            "situazione_abitativa": "Sono proprietario dell'immobile",
            "situazione_reddituale": "Sì, lavoro come dipendente (o sono in pensione)",
            "supporto_fiscale": "No, faccio tutto da solo",
            "timing": "Devo ancora iniziare, sto raccogliendo informazioni",
            "note_libere": "",
            "escalation": False,
            "motivo_escalation": None,
        },
        "bonus_attesi": ["Bonus Ristrutturazione 50%", "Ecobonus", "Bonus Mobili"],
    },
    {
        "id": "scenario-02-figlio",
        "descrizione": "Coppia con figlio appena nato, lavoro dipendente",
        "profilo": {
            "situazione_vita": "Ho avuto o aspetto un figlio",
            "situazione_abitativa": "Sono proprietario dell'immobile",
            "situazione_reddituale": "Sì, lavoro come dipendente (o sono in pensione)",
            "supporto_fiscale": "No, faccio tutto da solo",
            "timing": "Devo ancora iniziare, sto raccogliendo informazioni",
            "note_libere": "Figlio appena nato",
            "escalation": False,
            "motivo_escalation": None,
        },
        "bonus_attesi": ["Assegno Unico", "Bonus Nido"],
    },
    {
        "id": "scenario-03-disoccupato-under36",
        "descrizione": "Disoccupato under 36 in cerca di lavoro",
        "profilo": {
            "situazione_vita": "Ho perso il lavoro o sto cercando occupazione",
            "situazione_abitativa": "Sono in affitto",
            "situazione_reddituale": "No, sono disoccupato o in cerca di lavoro",
            "supporto_fiscale": "No, faccio tutto da solo",
            "timing": "Devo ancora iniziare, sto raccogliendo informazioni",
            "note_libere": "Under 36",
            "escalation": False,
            "motivo_escalation": None,
        },
        "bonus_attesi": ["Naspi", "Supporto Formazione Lavoro"],
    },
    {
        "id": "scenario-04-pensionato-salute",
        "descrizione": "Pensionato proprietario con spese mediche importanti",
        "profilo": {
            "situazione_vita": "Ho avuto spese mediche importanti",
            "situazione_abitativa": "Sono proprietario dell'immobile",
            "situazione_reddituale": "Sì, lavoro come dipendente (o sono in pensione)",
            "supporto_fiscale": "Sì, vado al CAF",
            "timing": "Ho già finito, voglio recuperare agevolazioni del passato",
            "note_libere": "Pensionato con spese mediche elevate",
            "escalation": False,
            "motivo_escalation": None,
        },
        "bonus_attesi": ["Detrazioni sanitarie 19%", "esenzione ticket"],
    },
]

OUT_DIR = Path(__file__).parent.parent / 'docs' / 'validation'
OUT_DIR.mkdir(exist_ok=True)


def run_scenario(scenario):
    print(f"\n>>> {scenario['id']}: {scenario['descrizione']}")
    profilo = scenario['profilo']

    print("  chiamata eligibility (Sonnet)...")
    eligibility = call_eligibility(profilo)

    if eligibility.get('error'):
        print(f"  ERRORE eligibility: {eligibility}")
        return {"error": True, "stage": "eligibility", "dettaglio": eligibility}

    bonus_trovati = [b['nome_semplice'] for b in eligibility.get('bonus', [])]
    print(f"  bonus trovati: {bonus_trovati}")

    print("  chiamata navigator (Haiku)...")
    navigator = call_navigator(eligibility)

    result = {
        "scenario": scenario['id'],
        "descrizione": scenario['descrizione'],
        "timestamp": datetime.now().isoformat(),
        "profilo_input": profilo,
        "bonus_attesi": scenario['bonus_attesi'],
        "bonus_trovati": bonus_trovati,
        "match_attesi": [b for b in scenario['bonus_attesi'] if any(b.lower() in t.lower() for t in bonus_trovati)],
        "eligibility_output": eligibility,
        "navigator_output": navigator,
    }

    path = OUT_DIR / f"{scenario['id']}.json"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  salvato in {path.name}")
    return result


if __name__ == '__main__':
    scenario_ids = sys.argv[1:] if sys.argv[1:] else [s['id'] for s in SCENARIOS]
    results = []
    for s in SCENARIOS:
        if s['id'] in scenario_ids:
            r = run_scenario(s)
            results.append(r)

    print(f"\n=== Completato: {len(results)} scenari ===")
    for r in results:
        if r.get('error'):
            print(f"  ❌ {r.get('scenario')}: errore")
        else:
            match = len(r.get('match_attesi', []))
            tot = len(r.get('bonus_attesi', []))
            print(f"  ✓ {r.get('scenario')}: {match}/{tot} bonus attesi trovati — {r.get('bonus_trovati')}")
