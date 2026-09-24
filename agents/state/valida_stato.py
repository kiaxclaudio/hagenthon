# -*- coding: utf-8 -*-
"""Valida gli artefatti di agents/state/ contro gli schemi di agents/schemas/."""
import glob, io, json, os, sys

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = HERE
SCHEMAS = os.path.join(os.path.dirname(HERE), "schemas")
BASE = "https://hagenthon/agents/schemas/"

resources = []
for p in glob.glob(os.path.join(SCHEMAS, "*.json")):
    with io.open(p, encoding="utf-8") as f:
        doc = json.load(f)
    uri = doc.get("$id") or (BASE + os.path.basename(p))
    resources.append((uri, Resource.from_contents(doc)))
    # alias sul nome file, per i $ref relativi "./xxx.json"
    resources.append((BASE + os.path.basename(p), Resource.from_contents(doc)))

registry = Registry()
for uri, res in resources:
    registry = registry.with_resource(uri, res)

def validator_for(name):
    with io.open(os.path.join(SCHEMAS, name), encoding="utf-8") as f:
        schema = json.load(f)
    return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())

def check(label, schema_name, path):
    v = validator_for(schema_name)
    with io.open(path, encoding="utf-8") as f:
        inst = json.load(f)
    errs = sorted(v.iter_errors(inst), key=lambda e: list(e.absolute_path))
    if not errs:
        print("OK    %-52s <- %s" % (label, schema_name))
        return 0
    print("FAIL  %-52s <- %s  (%d errori)" % (label, schema_name, len(errs)))
    for e in errs[:12]:
        print("      path=%s" % ("/".join(str(x) for x in e.absolute_path) or "<root>"))
        print("        %s" % e.message[:300])
    return len(errs)

total = 0
total += check("catalogo.json", "catalogo.json", os.path.join(STATE, "catalogo.json"))
for p in sorted(glob.glob(os.path.join(STATE, "misure-grezze", "*.json"))):
    total += check("misure-grezze/" + os.path.basename(p), "source-analyzer.output.json", p)
for p in sorted(glob.glob(os.path.join(STATE, "spiegazioni", "*.json"))):
    total += check("spiegazioni/" + os.path.basename(p), "explainer.output.json", p)
for p in sorted(glob.glob(os.path.join(STATE, "verifiche", "*.json"))):
    total += check("verifiche/" + os.path.basename(p), "fidelity-validator.output.json", p)

print("\nERRORI TOTALI: %d" % total)
sys.exit(1 if total else 0)
