#!/usr/bin/env python3
"""
apply-step-routing.py - attach steps to topic howtos in preferences.ttl, from a reviewed plan.

Input is a JSON file {"<topic>": ["step-id", ...], ...}, for example
  {"memory-management": ["step-memoryShaclValidation"], "terminology": ["step-theSemanticWeb"]}
where <topic> names a block `:howto-<topic> a schema:HowTo` in preferences.ttl and each id is a
`:step-...` that exists in preferences.ttl.

For each topic it appends the missing step ids to that howto's `schema:step` list. It is
idempotent (a step already in the list is skipped), refuses an unknown topic or step id, and
re-parses the result with rdflib before keeping it: if the new file does not parse, or a step
is not attached afterwards, the original is left untouched.

Usage:
  python3 apply-step-routing.py plan.json --dry-run     show what would change
  python3 apply-step-routing.py plan.json               apply to preferences.ttl
  python3 apply-step-routing.py plan.json --file PATH   apply to another copy

It edits only the schema:step lists; no step text, name or position changes. Removing a line
undoes an assignment.
"""
import argparse
import json
import pathlib
import re
import sys

import rdflib
from rdflib import Namespace, RDF

STORE = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = Namespace("http://schema.org/")


def parse(text, path):
    g = rdflib.Graph()
    g.parse(data=text, format="turtle", publicID=pathlib.Path(path).resolve().as_uri())
    return g


def apply(text, plan, known_steps):
    lines = text.split("\n")
    changes = {}
    for topic, ids in plan.items():
        start = next((i for i, l in enumerate(lines) if re.match(rf"^:howto-{re.escape(topic)} a schema:HowTo\b", l)), None)
        if start is None:
            sys.exit(f"no topic howto :howto-{topic} in the file")
        end = start
        while not lines[end].rstrip().endswith(" ."):
            end += 1
        s = next((k for k in range(start, end + 1) if "schema:step" in lines[k]), None)
        if s is None:
            sys.exit(f":howto-{topic} has no schema:step list")
        e = s
        while not (lines[e].rstrip().endswith(" ;") or lines[e].rstrip().endswith(" .")):
            e += 1
        block = "\n".join(lines[s:e + 1])
        present = set(re.findall(r":(step-[A-Za-z0-9_-]+)", block))
        new = []
        for sid in ids:
            if sid not in known_steps:
                sys.exit(f"unknown step id {sid}")
            if sid not in present and sid not in new:
                new.append(sid)
        if not new:
            continue
        terminator = lines[e].rstrip()[-1]                    # ';' or '.'
        body = lines[e].rstrip()[:-2]                         # drop ' ;' or ' .'
        lines[e] = body + "," + "".join("\n        :" + sid + "," for sid in new[:-1]) + "\n        :" + new[-1] + " " + terminator
        changes[topic] = new
    return "\n".join(lines), changes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--file", default=str(STORE / "preferences.ttl"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    plan = json.load(open(a.plan))
    path = pathlib.Path(a.file)
    old = path.read_text(encoding="utf-8")
    g0 = parse(old, path)
    known = {str(s).rsplit("#", 1)[-1] for s in g0.subjects(RDF.type, SCHEMA.HowToStep)}
    new_text, changes = apply(old, plan, known)
    g1 = parse(new_text, path)                                  # must still parse
    attached = {str(o).rsplit("#", 1)[-1] for o in g1.objects(None, SCHEMA.step)}
    missing = [sid for ids in changes.values() for sid in ids if sid not in attached]
    if missing:
        sys.exit(f"not attached after the edit, nothing written: {missing}")
    total = sum(len(v) for v in changes.values())
    for topic, ids in changes.items():
        print(f"  {topic}: +{len(ids)}")
    print(f"{total} step(s) newly attached; triples {len(g0)} -> {len(g1)}")
    if a.dry_run or not total:
        print("(dry run: nothing written)" if a.dry_run else "(nothing to do)")
        return
    path.write_text(new_text, encoding="utf-8")
    print("written", path)


if __name__ == "__main__":
    main()
