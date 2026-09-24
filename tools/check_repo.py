#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_repo.py - linter di consegna del repository.

Esegue le verifiche meccaniche della checklist in docs/PRE-FREEZE-CHECKLIST.md
e stampa un report leggibile. Solo libreria standard: nessuna dipendenza.

Uso:
    python tools/check_repo.py              # report testuale
    python tools/check_repo.py --strict     # anche i WARN fanno fallire
    python tools/check_repo.py --json       # report strutturato su stdout

Exit code:
    0  nessun FAIL (con --strict: nessun FAIL e nessun WARN)
    1  almeno un controllo fallito
    2  errore interno del linter

Filosofia: un controllo e' FAIL solo quando il difetto e' oggettivo (file
mancante, JSON invalido, link rotto, segreto committato, nome incoerente).
Quando la verifica dipende da una scelta editoriale ancora aperta il controllo
e' WARN: segnala senza imporre.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

# --------------------------------------------------------------------------
# Configurazione
# --------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

# Cartelle mai attraversate: metadati git e artefatti di build.
DIR_ESCLUSE = {".git", "node_modules", "__pycache__", ".venv", "venv",
               "dist", "build", ".idea", ".vscode", ".pytest_cache"}

# Estensioni trattate come testo. Tutto il resto viene ignorato dalle
# scansioni testuali (marcatori, segreti) per non leggere binari.
EST_TESTO = {".md", ".py", ".json", ".txt", ".yml", ".yaml", ".html", ".htm",
             ".css", ".js", ".ts", ".jsx", ".tsx", ".sh", ".example", ".cfg",
             ".ini", ".toml", ".env"}

# Dimensione massima di un file letto in memoria (1 MB).
MAX_BYTE_FILE = 1_000_000

# File che PARLANO dei marcatori e quindi li contengono per forza.
# Escluderli e' l'unico modo per non generare un falso positivo permanente.
# L'elenco viene stampato nel report: nessuna esclusione nascosta.
FILE_META = {
    "tools/check_repo.py",
    "docs/PRE-FREEZE-CHECKLIST.md",
    "docs/EVALUATION-MAP.md",
}

# Cartelle e file la cui presenza e' richiesta dal bando dell'hackathon.
STRUTTURA_RICHIESTA = ["app", "agents", "presentation", "README.md"]

# Termini con trattino che NON sono nomi di agente: servono a evitare che il
# riconoscimento dei nomi scambi un valore di dominio per un agente.
TERMINI_NON_AGENTE = {
    "sonnet-5", "opus-5", "haiku-4", "main-pipeline", "kebab-case",
    "end-to-end", "contract-first", "source-model", "run-id", "pull-request",
    "hitl-required", "source-refs",
}

# I tre file che devono citare tutti gli agenti e nessun agente inesistente.
FILE_CITAZIONE = [
    "agents/README.md",
    "agents/orchestrator.md",
    "agents/workflows/main-pipeline.md",
]

# Pattern di segreti. Il quantificatore minimo evita di segnalare i
# segnaposto (es. la chiave fittizia di .env.example, che termina con punti).
PATTERN_SEGRETI = [
    ("chiave Anthropic", re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}")),
    ("chiave OpenAI", re.compile(r"sk-[A-Za-z0-9]{32,}")),
    ("token GitHub", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("access key AWS", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("chiave privata PEM", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]

# File esclusi dalla scansione segreti: il template (contiene segnaposto) e
# il .env locale (non e' tracciato da git, quindi non viene consegnato).
FILE_ESCLUSI_SEGRETI = {".env.example", ".env", ".env.local"}

# Esiti possibili di un controllo.
OK, WARN, FAIL = "OK", "WARN", "FAIL"


# --------------------------------------------------------------------------
# Infrastruttura di reporting
# --------------------------------------------------------------------------

class Report:
    """Raccoglie l'esito dei controlli e li stampa in coda."""

    def __init__(self) -> None:
        self.voci: list[dict] = []

    def aggiungi(self, area: str, nome: str, esito: str,
                 sintesi: str, dettagli: list[str] | None = None) -> None:
        self.voci.append({
            "area": area,
            "controllo": nome,
            "esito": esito,
            "sintesi": sintesi,
            "dettagli": dettagli or [],
        })

    def conteggi(self) -> dict[str, int]:
        c = {OK: 0, WARN: 0, FAIL: 0}
        for v in self.voci:
            c[v["esito"]] += 1
        return c

    def stampa(self) -> None:
        print("=" * 78)
        print("CHECK REPO - linter di consegna")
        print(f"radice: {ROOT}")
        print("=" * 78)
        area_corrente = None
        for v in self.voci:
            if v["area"] != area_corrente:
                area_corrente = v["area"]
                print(f"\n--- {area_corrente} " + "-" * max(0, 72 - len(area_corrente)))
            print(f"[{v['esito']:^4}] {v['controllo']}: {v['sintesi']}")
            for d in v["dettagli"]:
                print(f"         {d}")
        c = self.conteggi()
        print("\n" + "=" * 78)
        print(f"RIEPILOGO  OK={c[OK]}  WARN={c[WARN]}  FAIL={c[FAIL]}"
              f"  (controlli: {len(self.voci)})")
        print("=" * 78)


def tronca(testo: str, n: int = 90) -> str:
    """Accorcia una riga lunga per tenere il report leggibile."""
    testo = testo.strip()
    return testo if len(testo) <= n else testo[: n - 3] + "..."


def rel(p: Path) -> str:
    """Path relativo alla radice, sempre con separatore POSIX."""
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return p.as_posix()


# --------------------------------------------------------------------------
# Accesso al filesystem (tollerante agli errori)
# --------------------------------------------------------------------------

FILE_ILLEGGIBILI: list[str] = []


def leggi(p: Path) -> str | None:
    """Legge un file di testo. Restituisce None se illeggibile.

    Un file illeggibile non deve far esplodere il linter: viene registrato e
    riportato in fondo come nota, i controlli proseguono sugli altri file.
    """
    try:
        if p.stat().st_size > MAX_BYTE_FILE:
            FILE_ILLEGGIBILI.append(f"{rel(p)} (oltre {MAX_BYTE_FILE} byte, saltato)")
            return None
        return p.read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError) as err:
        FILE_ILLEGGIBILI.append(f"{rel(p)} ({type(err).__name__}: {err})")
        return None


def file_testo() -> list[Path]:
    """Tutti i file di testo del repo, escluse le cartelle di servizio."""
    trovati: list[Path] = []
    for radice, cartelle, nomi in os.walk(ROOT):
        cartelle[:] = [c for c in cartelle if c not in DIR_ESCLUSE]
        for n in nomi:
            p = Path(radice) / n
            if p.suffix.lower() in EST_TESTO or n.startswith(".env"):
                trovati.append(p)
    return sorted(trovati)


def file_markdown() -> list[Path]:
    return [p for p in file_testo() if p.suffix.lower() == ".md"]


def senza_blocchi_codice(testo: str) -> str:
    """Azzera il contenuto dei blocchi ``` ``` mantenendo il numero di righe.

    Serve ai controlli su link e path: un comando di esempio dentro un blocco
    di codice non e' un riferimento a un file esistente.
    """
    righe = testo.splitlines()
    dentro = False
    fuori: list[str] = []
    for r in righe:
        if r.lstrip().startswith("```"):
            dentro = not dentro
            fuori.append("")
            continue
        fuori.append("" if dentro else r)
    return "\n".join(fuori)


def git(*args: str) -> tuple[int, str]:
    """Esegue un comando git in sola lettura. Non solleva mai."""
    try:
        res = subprocess.run(("git", *args), cwd=ROOT, capture_output=True,
                             text=True, timeout=20)
        return res.returncode, (res.stdout or "") + (res.stderr or "")
    except (OSError, subprocess.SubprocessError) as err:
        return 127, f"git non eseguibile: {err}"


# --------------------------------------------------------------------------
# Controlli - struttura
# --------------------------------------------------------------------------

def c_struttura(rep: Report) -> None:
    """Le tre cartelle richieste dal bando piu' il README esistono e non sono vuote."""
    mancanti, vuote, dettagli = [], [], []
    for nome in STRUTTURA_RICHIESTA:
        p = ROOT / nome
        if not p.exists():
            mancanti.append(nome)
            continue
        if p.is_dir():
            # .gitkeep e' un segnaposto: non conta come contenuto.
            contenuto = [f for f in p.rglob("*")
                         if f.is_file() and f.name != ".gitkeep"]
            if not contenuto:
                vuote.append(nome)
            else:
                dettagli.append(f"{nome}/: {len(contenuto)} file")
        else:
            if p.stat().st_size == 0:
                vuote.append(nome)
            else:
                dettagli.append(f"{nome}: {p.stat().st_size} byte")
    if mancanti or vuote:
        for n in mancanti:
            dettagli.append(f"MANCANTE: {n}")
        for n in vuote:
            dettagli.append(f"VUOTA (solo segnaposto o 0 byte): {n}")
        rep.aggiungi("struttura", "cartelle obbligatorie", FAIL,
                     f"{len(mancanti)} mancanti, {len(vuote)} vuote", dettagli)
    else:
        rep.aggiungi("struttura", "cartelle obbligatorie", OK,
                     "app/, agents/, presentation/, README.md presenti e non vuoti",
                     dettagli)


# --------------------------------------------------------------------------
# Controlli - marcatori residui
# --------------------------------------------------------------------------

def c_marcatori(rep: Report) -> None:
    """Nessun marcatore TODO-TEMA: o TODO residuo fuori dai file meta."""
    re_tema = re.compile(r"TODO-TEMA:")
    re_todo = re.compile(r"\bTODO\b")
    occorrenze: list[str] = []
    n_tema = 0
    for p in file_testo():
        if rel(p) in FILE_META:
            continue
        testo = leggi(p)
        if testo is None:
            continue
        for i, riga in enumerate(testo.splitlines(), start=1):
            if re_tema.search(riga):
                n_tema += 1
                occorrenze.append(f"TODO-TEMA  {rel(p)}:{i}  {tronca(riga)}")
            elif re_todo.search(riga):
                occorrenze.append(f"TODO       {rel(p)}:{i}  {tronca(riga)}")
    if occorrenze:
        rep.aggiungi("contenuti", "marcatori residui", FAIL,
                     f"{len(occorrenze)} occorrenze ({n_tema} TODO-TEMA)",
                     occorrenze)
    else:
        rep.aggiungi("contenuti", "marcatori residui", OK,
                     "nessun TODO-TEMA / TODO residuo",
                     [f"file esclusi perche' descrivono i marcatori: "
                      f"{', '.join(sorted(FILE_META))}"])


# --------------------------------------------------------------------------
# Controlli - JSON
# --------------------------------------------------------------------------

def c_json(rep: Report) -> None:
    """Tutti i .json del repo sono sintatticamente validi."""
    schemi_dir = ROOT / "agents" / "schemas"
    tutti = [p for p in file_testo() if p.suffix.lower() == ".json"]
    rotti, dettagli = [], []
    for p in tutti:
        testo = leggi(p)
        if testo is None:
            rotti.append(f"{rel(p)}: illeggibile")
            continue
        try:
            json.loads(testo)
        except json.JSONDecodeError as err:
            rotti.append(f"{rel(p)}: riga {err.lineno} col {err.colno}: {err.msg}")
    schemi = [p for p in tutti if schemi_dir in p.parents]
    if rotti:
        rep.aggiungi("contratti", "validita' JSON", FAIL,
                     f"{len(rotti)} file non parsabili su {len(tutti)}", rotti)
    elif not schemi:
        dettagli.append("agents/schemas/ non contiene ancora file .json")
        dettagli.append("attesi: uno schema per input e output di ogni agente")
        rep.aggiungi("contratti", "validita' JSON", WARN,
                     "nessuno schema JSON presente (contratti non congelati)",
                     dettagli)
    else:
        rep.aggiungi("contratti", "validita' JSON", OK,
                     f"{len(tutti)} file JSON validi, di cui {len(schemi)} in agents/schemas/",
                     [rel(p) for p in schemi])


# --------------------------------------------------------------------------
# Controlli - link e riferimenti
# --------------------------------------------------------------------------

RE_LINK_MD = re.compile(r"\[[^\]]*\]\(\s*<?([^)>\s]+)>?(?:\s+\"[^\"]*\")?\s*\)")
RE_BACKTICK = re.compile(r"`([^`\n]+)`")


def _link_esterno(dest: str) -> bool:
    return dest.startswith(("http://", "https://", "mailto:", "tel:", "data:", "#"))


def c_link(rep: Report) -> None:
    """Ogni link relativo nei .md punta a un file o a una cartella esistente."""
    rotti, totale = [], 0
    for p in file_markdown():
        testo = leggi(p)
        if testo is None:
            continue
        pulito = senza_blocchi_codice(testo)
        for i, riga in enumerate(pulito.splitlines(), start=1):
            for dest in RE_LINK_MD.findall(riga):
                if _link_esterno(dest):
                    continue
                totale += 1
                bersaglio = dest.split("#", 1)[0]
                if not bersaglio:
                    continue
                base = ROOT if bersaglio.startswith("/") else p.parent
                target = (base / bersaglio.lstrip("/")).resolve()
                if not target.exists():
                    rotti.append(f"{rel(p)}:{i} -> {dest} (inesistente)")
    if rotti:
        rep.aggiungi("documentazione", "link relativi", FAIL,
                     f"{len(rotti)} link rotti su {totale}", rotti)
    else:
        rep.aggiungi("documentazione", "link relativi", OK,
                     f"{totale} link relativi verificati, nessuno rotto")


def c_path_readme(rep: Report) -> None:
    """Ogni path citato fra backtick nel README esiste davvero.

    Vengono ignorati i blocchi di codice (comandi di esempio) e i link
    markdown, gia' coperti dal controllo precedente.
    """
    p = ROOT / "README.md"
    testo = leggi(p) if p.exists() else None
    if testo is None:
        rep.aggiungi("documentazione", "path citati nel README", FAIL,
                     "README.md assente o illeggibile")
        return
    pulito = RE_LINK_MD.sub("", senza_blocchi_codice(testo))
    mancanti = []
    for i, riga in enumerate(pulito.splitlines(), start=1):
        for tok in RE_BACKTICK.findall(riga):
            tok = tok.strip()
            sembra_path = ("/" in tok) or re.fullmatch(r"[\w.\-]+\.\w{1,5}", tok)
            if not sembra_path or " " in tok or tok.startswith((".env", "http")):
                continue
            if not (ROOT / tok).exists():
                mancanti.append(f"README.md:{i} -> `{tok}` (inesistente)")
    if mancanti:
        rep.aggiungi("documentazione", "path citati nel README", WARN,
                     f"{len(mancanti)} riferimenti senza file corrispondente",
                     mancanti)
    else:
        rep.aggiungi("documentazione", "path citati nel README", OK,
                     "tutti i path citati nel README esistono")


# --------------------------------------------------------------------------
# Controlli - segreti e configurazione
# --------------------------------------------------------------------------

def c_segreti(rep: Report) -> None:
    """Nessun segreto in chiaro fuori da .env / .env.example."""
    trovati = []
    for p in file_testo():
        if p.name in FILE_ESCLUSI_SEGRETI:
            continue
        testo = leggi(p)
        if testo is None:
            continue
        for i, riga in enumerate(testo.splitlines(), start=1):
            for etichetta, pat in PATTERN_SEGRETI:
                if pat.search(riga):
                    trovati.append(f"{etichetta}: {rel(p)}:{i}")
    if trovati:
        rep.aggiungi("sicurezza", "segreti in chiaro", FAIL,
                     f"{len(trovati)} possibili segreti", trovati)
    else:
        rep.aggiungi("sicurezza", "segreti in chiaro", OK,
                     "nessun segreto rilevato fuori da .env / .env.example")


def c_env(rep: Report) -> None:
    """.env ignorato da git, non tracciato, e coerente con .env.example."""
    dettagli, esito = [], OK
    gitignore = leggi(ROOT / ".gitignore") or ""
    if not re.search(r"^\.env\s*$", gitignore, re.M):
        dettagli.append("FAIL: .gitignore non contiene la riga '.env'")
        esito = FAIL
    else:
        dettagli.append("ok: .env presente in .gitignore")

    rc, out = git("ls-files", "--error-unmatch", ".env")
    if rc == 0 and out.strip():
        dettagli.append("FAIL: .env risulta TRACCIATO da git")
        esito = FAIL
    else:
        dettagli.append("ok: .env non tracciato da git")

    if not (ROOT / ".env").exists():
        dettagli.append("warn: .env assente dal working tree "
                        "(atteso in locale: cp .env.example .env)")
        esito = WARN if esito == OK else esito

    if not (ROOT / ".env.example").exists():
        dettagli.append("FAIL: .env.example assente")
        esito = FAIL
    rep.aggiungi("sicurezza", "gestione .env",
                 esito, "configurazione dei segreti", dettagli)


# --------------------------------------------------------------------------
# Controlli - coerenza del sistema agentico
# --------------------------------------------------------------------------

RE_PATH_AGENTE = re.compile(r"subagents/([a-z][a-z0-9\-]*)(?:\.md)?")
RE_TOKEN_AGENTE = re.compile(r"`([a-z][a-z0-9]*(?:-[a-z0-9]+)*)`")


def agenti_su_disco() -> list[str]:
    """Nomi degli agenti = file .md in agents/subagents/, template escluso."""
    d = ROOT / "agents" / "subagents"
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.md") if not p.name.startswith("_"))


def _citazioni(testo: str, noti: set[str]) -> set[str]:
    """Nomi di agente citati in un testo.

    Due segnali: il path 'subagents/<nome>', e il token fra backtick in
    kebab-case. I token di una sola parola sono accettati solo se
    corrispondono a un agente esistente: un nome inventato di una parola sola
    (es. `degraded`) non e' distinguibile da un valore di dominio, quindi la
    verifica di quel caso resta manuale (vedi PRE-FREEZE-CHECKLIST).
    """
    trovati = set(RE_PATH_AGENTE.findall(testo))
    for tok in RE_TOKEN_AGENTE.findall(testo):
        if tok in TERMINI_NON_AGENTE:
            continue
        if "-" in tok or tok in noti:
            trovati.add(tok)
    trovati.discard("orchestrator")
    return trovati


def c_nomi_agenti(rep: Report) -> None:
    """Ogni agente citato ha un file, e ogni file e' citato nei tre indici."""
    noti = set(agenti_su_disco())
    if not noti:
        rep.aggiungi("agenti", "coerenza dei nomi", FAIL,
                     "agents/subagents/ non contiene file di agente")
        return
    dettagli, esito = [f"agenti su disco ({len(noti)}): {', '.join(sorted(noti))}"], OK
    for nome_file in FILE_CITAZIONE:
        p = ROOT / nome_file
        testo = leggi(p) if p.exists() else None
        if testo is None:
            dettagli.append(f"FAIL: {nome_file} assente o illeggibile")
            esito = FAIL
            continue
        citati = _citazioni(testo, noti)
        fantasma = sorted(citati - noti)
        assenti = sorted(noti - citati)
        if fantasma:
            dettagli.append(f"FAIL: {nome_file} cita agenti senza file: "
                            f"{', '.join(fantasma)}")
            esito = FAIL
        if assenti:
            dettagli.append(f"FAIL: {nome_file} non cita: {', '.join(assenti)}")
            esito = FAIL
        if not fantasma and not assenti:
            dettagli.append(f"ok: {nome_file} cita tutti e soli i {len(noti)} agenti")
    rep.aggiungi("agenti", "coerenza dei nomi", esito,
                 "nomi allineati fra indici e file" if esito == OK
                 else "disallineamento fra nomi citati e file presenti", dettagli)


RE_TIER = re.compile(r"\b(haiku|sonnet|opus)(?:[-\s]?(\d+(?:\.\d+)?))?\b", re.I)


def _tier_riga(riga: str) -> tuple[str, str] | None:
    """Primo tier citato in una riga: (famiglia normalizzata, testo grezzo)."""
    m = RE_TIER.search(riga)
    if not m:
        return None
    return m.group(1).lower(), m.group(0).strip()


def _tier_dichiarato(testo: str) -> tuple[str, str] | None:
    """Tier dalla sezione '## Model tier' del file dell'agente (fonte autorevole)."""
    righe = testo.splitlines()
    for i, r in enumerate(righe):
        if re.match(r"^#{2,3}\s*model tier", r.strip(), re.I):
            for r2 in righe[i + 1: i + 6]:
                if r2.strip().startswith("#"):
                    break
                t = _tier_riga(r2)
                if t:
                    return t
    return None


def c_tier(rep: Report) -> None:
    """Il tier di un agente e' lo stesso in tutti i file che lo citano."""
    componenti = agenti_su_disco()
    sorgenti: dict[str, list[tuple[str, str, str]]] = {c: [] for c in componenti}
    sorgenti["orchestrator"] = []

    # 1) dichiarazione autorevole nel file del componente
    for nome in componenti:
        testo = leggi(ROOT / "agents" / "subagents" / f"{nome}.md")
        if testo:
            t = _tier_dichiarato(testo)
            if t:
                sorgenti[nome].append((f"agents/subagents/{nome}.md", t[0], t[1]))
    testo_orch = leggi(ROOT / "agents" / "orchestrator.md")
    if testo_orch:
        t = _tier_dichiarato(testo_orch)
        if t:
            sorgenti["orchestrator"].append(("agents/orchestrator.md", t[0], t[1]))

    # 2) citazioni sparse: si registra il tier solo se la riga nomina un solo
    #    componente, altrimenti l'attribuzione sarebbe ambigua (diagrammi).
    matcher = {c: re.compile(r"(?<![a-z0-9\-])" + re.escape(c) + r"(?![a-z0-9\-])")
               for c in sorgenti}
    for p in file_markdown():
        testo = leggi(p)
        if testo is None:
            continue
        for i, riga in enumerate(testo.splitlines(), start=1):
            presenti = [c for c, rx in matcher.items() if rx.search(riga)]
            if len(presenti) != 1:
                continue
            t = _tier_riga(riga)
            if t:
                sorgenti[presenti[0]].append((f"{rel(p)}:{i}", t[0], t[1]))

    dettagli, esito = [], OK
    for comp in sorted(sorgenti):
        voci = sorgenti[comp]
        if not voci:
            dettagli.append(f"WARN: {comp}: nessun model tier dichiarato (G-11)")
            esito = WARN if esito == OK else esito
            continue
        famiglie = {v[1] for v in voci}
        if len(famiglie) > 1:
            esito = FAIL
            dettagli.append(f"FAIL: {comp}: tier discordanti {sorted(famiglie)}")
            for f_, fam, raw in voci:
                dettagli.append(f"       {f_}: {raw}")
        else:
            fam = famiglie.pop()
            dettagli.append(f"ok: {comp}: {fam} (coerente in {len(voci)} riferimenti)")
    rep.aggiungi("agenti", "coerenza dei model tier", esito,
                 "un solo tier per componente" if esito != FAIL
                 else "tier discordanti fra file", dettagli)


def c_sezioni_template(rep: Report) -> None:
    """Ogni sub-agente compila le sezioni previste da _TEMPLATE.md.

    CLAUDE.md paragrafo 6 dichiara che il template si applica 'senza
    eccezioni': la divergenza fra template e istanze e' un rischio diretto sul
    criterio 'coerenza tra file'. Esito WARN perche' la soluzione puo' essere
    sia completare gli agenti sia ridurre il template: e' una scelta editoriale.
    """
    # chiave logica -> parole accettate in un titolo di sezione
    richieste = {
        "scope": ("scope",),
        "model tier": ("model tier",),
        "input": ("input",),
        "output": ("output",),
        "passi": ("passi", "procedura"),
        "vincoli": ("vincoli",),
        "fallback": ("fallback",),
        "hitl": ("hitl", "escalation"),
        "iterazioni": ("iterazion",),
        "errori": ("errori",),
    }
    dettagli, esito = [], OK
    for nome in agenti_su_disco():
        testo = leggi(ROOT / "agents" / "subagents" / f"{nome}.md")
        if testo is None:
            continue
        titoli = " | ".join(
            unicodedata.normalize("NFKD", t).lower()
            for t in re.findall(r"^#{2,4}\s*(.+)$", testo, re.M)
        )
        mancanti = [k for k, alias in richieste.items()
                    if not any(a in titoli for a in alias)]
        if mancanti:
            esito = WARN
            dettagli.append(f"warn: {nome}.md: sezioni assenti -> {', '.join(mancanti)}")
        else:
            dettagli.append(f"ok: {nome}.md: tutte le sezioni del template")
    if esito == WARN:
        dettagli.append("nota: o si completano gli agenti, o si allinea "
                        "_TEMPLATE.md e CLAUDE.md paragrafo 6")
    rep.aggiungi("agenti", "sezioni del template", esito,
                 "template applicato da tutti gli agenti" if esito == OK
                 else "alcuni agenti non compilano tutte le sezioni", dettagli)


# --------------------------------------------------------------------------
# Controlli - stato di consegna
# --------------------------------------------------------------------------

def c_git(rep: Report) -> None:
    """Il repo e' consegnabile: commit presenti, remote configurato, albero pulito."""
    dettagli, esito = [], OK
    rc, _ = git("rev-parse", "--git-dir")
    if rc != 0:
        rep.aggiungi("consegna", "stato git", FAIL,
                     "la cartella non e' un repository git")
        return
    rc, out = git("rev-list", "--count", "HEAD")
    if rc != 0:
        dettagli.append("WARN: nessun commit nel repository")
        esito = WARN
    else:
        dettagli.append(f"ok: {out.strip()} commit")
    rc, out = git("remote", "-v")
    if rc == 0 and out.strip():
        dettagli.append(f"ok: remote: {out.strip().splitlines()[0]}")
    else:
        dettagli.append("WARN: nessun remote configurato (repo non pubblicabile)")
        esito = WARN
    rc, out = git("rev-parse", "--abbrev-ref", "HEAD")
    ramo = out.strip() if rc == 0 else "?"
    dettagli.append(f"info: ramo corrente: {ramo}")
    rc, out = git("status", "--porcelain")
    sporchi = [r for r in out.splitlines() if r.strip()] if rc == 0 else []
    if sporchi:
        dettagli.append(f"WARN: {len(sporchi)} file non committati")
        esito = WARN
    rep.aggiungi("consegna", "stato git", esito,
                 "repository consegnabile" if esito == OK
                 else "il repository non e' ancora in stato di consegna", dettagli)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

CONTROLLI = [
    c_struttura,
    c_marcatori,
    c_json,
    c_link,
    c_path_readme,
    c_segreti,
    c_env,
    c_nomi_agenti,
    c_tier,
    c_sezioni_template,
    c_git,
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Linter di consegna del repository (solo libreria standard).")
    parser.add_argument("--strict", action="store_true",
                        help="considera fallimento anche i WARN")
    parser.add_argument("--json", action="store_true", dest="come_json",
                        help="stampa il report in JSON invece che in testo")
    args = parser.parse_args(argv)

    # L'output puo' contenere accenti: su console Windows evita UnicodeEncodeError.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

    rep = Report()
    for controllo in CONTROLLI:
        try:
            controllo(rep)
        except Exception as err:  # un controllo rotto non ferma gli altri
            rep.aggiungi("linter", controllo.__name__, FAIL,
                         f"errore interno: {type(err).__name__}: {err}")

    if FILE_ILLEGGIBILI:
        rep.aggiungi("linter", "file non analizzati", WARN,
                     f"{len(FILE_ILLEGGIBILI)} file saltati", FILE_ILLEGGIBILI)

    conteggi = rep.conteggi()
    if args.come_json:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
        print(json.dumps({"radice": str(ROOT), "conteggi": conteggi,
                          "controlli": rep.voci}, ensure_ascii=False, indent=2))
    else:
        rep.stampa()
        if conteggi[FAIL]:
            print("ESITO: NON CONSEGNABILE - risolvere i FAIL elencati sopra.")
        elif conteggi[WARN]:
            print("ESITO: consegnabile con riserve - valutare i WARN.")
        else:
            print("ESITO: tutti i controlli superati.")

    if conteggi[FAIL]:
        return 1
    if args.strict and conteggi[WARN]:
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
    except Exception as err:  # errore non previsto: exit code dedicato
        print(f"errore interno del linter: {type(err).__name__}: {err}",
              file=sys.stderr)
        sys.exit(2)
