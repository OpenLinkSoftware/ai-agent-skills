#!/usr/bin/env python3
"""
memory-maintenance.py - deterministic, report-only maintenance checks for agent-rdf-memory.

Needs no model and writes nothing. It reads preferences.ttl, the howto/entities/projects
documents and ontology.ttl, and reports:

  1. superseded   steps that a later step marks as superseded, reversed or corrected
                  (candidates to retire, by hand and with approval)
  2. dead-links   rdfs:seeAlso links whose target file is missing, or whose #fragment names
                  a subject that is not in the target document
  3. duplicates   howto documents with the same name, and steps with the same name
  4. unrouted     steps attached to no topic howto, each with the topic that the ontology's
                  trigger phrases suggest (a suggestion only)

Usage:
  python3 memory-maintenance.py                 summary with the first 10 rows of each check
  python3 memory-maintenance.py --all           every row
  python3 memory-maintenance.py --json          machine-readable
  python3 memory-maintenance.py --check dead-links
  python3 memory-maintenance.py --strict        exit 1 when dead links are found
  python3 memory-maintenance.py --sessions      also scan sessions/ for dead links (slow)

Drift between the files and the endpoint is a different check: scripts/full-store-graph-gate.py.
"""
import argparse
import json
import os
import pathlib
import re
import sys
import urllib.parse
from collections import defaultdict

import rdflib
from rdflib import Namespace, RDF, RDFS, URIRef

STORE = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = Namespace("http://schema.org/")
SUPERSEDE = re.compile(r"\b(SUPERSEDES|SUPERSEDED|REVERSED|REVERSES|CORRECTION to|TIGHTENED|HISTORICAL)\b")
STEP_REF = re.compile(r"\bSteps? (\d+)(?:\s*(?:,|and|-|–)\s*(\d+))?")
_graphs = {}


def load(path):
    path = pathlib.Path(path).resolve()
    if path not in _graphs:
        g = rdflib.Graph()
        try:
            g.parse(str(path), format="turtle", publicID=path.as_uri())
        except Exception as exc:  # report, never crash on one bad file
            _graphs[path] = (None, str(exc).splitlines()[0][:120])
            return _graphs[path]
        _graphs[path] = (g, None)
    return _graphs[path]


def literal(g, s, p):
    v = g.value(s, p)
    return str(v) if v is not None else ""


def collect_steps():
    g, err = load(STORE / "preferences.ttl")
    if g is None:
        sys.exit("preferences.ttl does not parse: " + err)
    attached = set(g.objects(None, SCHEMA.step))
    steps = {}
    for s in g.subjects(RDF.type, SCHEMA.HowToStep):
        pos = g.value(s, SCHEMA.position)
        steps[s] = {
            "iri": str(s),
            "id": str(s).rsplit("#", 1)[-1],
            "position": int(pos) if pos is not None else None,
            "name": literal(g, s, SCHEMA.name),
            "text": literal(g, s, SCHEMA.text),
            "attached": s in attached,
            "seeAlso": [str(o) for o in g.objects(s, RDFS.seeAlso)],
        }
    return g, steps


def check_superseded(steps):
    by_pos = {v["position"]: v for v in steps.values() if v["position"] is not None}
    rows = []
    for v in sorted(steps.values(), key=lambda x: x["position"] or 0):
        head = v["name"] + " " + v["text"][:400]
        m = SUPERSEDE.search(head)
        if not m:
            continue
        targets = sorted({int(n) for pair in STEP_REF.findall(head) for n in pair if n} - {v["position"]})
        rows.append({
            "step": v["position"], "marker": m.group(1), "name": v["name"][:110],
            "refers_to": targets,
            "refers_to_exist": [t for t in targets if t in by_pos],
        })
    return rows


def local_path(iri):
    if not iri.startswith("file:"):
        return None, None
    parsed = urllib.parse.urlparse(iri)
    return pathlib.Path(urllib.parse.unquote(parsed.path)), parsed.fragment


def ttl_files(include_sessions):
    out = [p for p in sorted(STORE.glob("*.ttl"))]
    for sub in ("howto", "entities", "projects", "shapes"):
        out += sorted((STORE / sub).glob("*.ttl"))
    if include_sessions:
        out += sorted((STORE / "sessions").glob("*.ttl"))
    return [p for p in out if not p.name.endswith(".example.ttl")]


def check_dead_links(include_sessions):
    rows, seen = [], set()
    for path in ttl_files(include_sessions):
        g, err = load(path)
        if g is None:
            rows.append({"file": str(path.relative_to(STORE)), "link": "(file does not parse)", "problem": err})
            continue
        for s, o in g.subject_objects(RDFS.seeAlso):
            if not isinstance(o, URIRef):
                continue
            target, frag = local_path(str(o))
            if target is None:
                continue
            key = (path, str(o))
            if key in seen:
                continue
            seen.add(key)
            rel = str(path.relative_to(STORE))
            if not target.exists():
                rows.append({"file": rel, "link": str(o).replace(STORE.as_uri() + "/", ""), "problem": "target file missing"})
            elif frag and target.suffix == ".ttl":
                tg, terr = load(target)
                if tg is None:
                    rows.append({"file": rel, "link": str(o).replace(STORE.as_uri() + "/", ""), "problem": "target does not parse"})
                else:
                    node = URIRef(target.as_uri() + "#" + frag)
                    if not any(True for _ in tg.predicate_objects(node)):
                        rows.append({"file": rel, "link": str(o).replace(STORE.as_uri() + "/", ""), "problem": "fragment not in target"})
    return rows


def check_duplicates(steps):
    names = defaultdict(list)
    for p in sorted((STORE / "howto").glob("*.ttl")):
        g, _ = load(p)
        if g is None:
            continue
        doc = URIRef(p.as_uri())
        n = literal(g, doc, SCHEMA.name)
        if n:
            names[n.strip().lower()].append(p.name)
    rows = [{"kind": "howto name", "name": k[:90], "where": v} for k, v in names.items() if len(v) > 1]
    sn = defaultdict(list)
    for v in steps.values():
        if v["name"]:
            sn[v["name"].strip().lower()].append(v["position"])
    rows += [{"kind": "step name", "name": k[:90], "where": sorted(x for x in v if x is not None)} for k, v in sn.items() if len(v) > 1]
    return rows


def check_unrouted(steps):
    og, err = load(STORE / "ontology.ttl")
    phrases = defaultdict(list)   # topic -> trigger phrases
    if og is not None:
        for s, p, o in og:
            if str(p).endswith("#routesToTopic"):
                topic = str(o).rsplit("#", 1)[-1].replace("topic-", "")
                for tp in og.objects(s, URIRef(str(p).rsplit("#", 1)[0] + "#triggerPhrase")):
                    phrases[topic].append(str(tp).lower())
    rows = []
    for v in sorted(steps.values(), key=lambda x: x["position"] or 0):
        if v["attached"]:
            continue
        hay = (v["name"] + " " + v["text"][:600]).lower()
        scores = {t: sum(1 for ph in lst if ph in hay) for t, lst in phrases.items()}
        best = max(scores.items(), key=lambda kv: kv[1]) if scores else (None, 0)
        rows.append({"step": v["position"], "id": v["id"], "name": v["name"][:100],
                     "suggested_topic": best[0] if best[1] else None, "matched_phrases": best[1]})
    return rows


def show(title, rows, limit, cols):
    print(f"\n== {title} ({len(rows)}) ==")
    for r in rows[: len(rows) if limit is None else limit]:
        print("  " + " | ".join(str(r.get(c, "")) for c in cols))
    if limit is not None and len(rows) > limit:
        print(f"  ... {len(rows) - limit} more (use --all)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", choices=["superseded", "dead-links", "duplicates", "unrouted"])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--sessions", action="store_true")
    a = ap.parse_args()
    limit = None if a.all else 10
    _, steps = collect_steps()
    result = {}
    if a.check in (None, "superseded"):
        result["superseded"] = check_superseded(steps)
    if a.check in (None, "dead-links"):
        result["dead-links"] = check_dead_links(a.sessions)
    if a.check in (None, "duplicates"):
        result["duplicates"] = check_duplicates(steps)
    if a.check in (None, "unrouted"):
        result["unrouted"] = check_unrouted(steps)
    if a.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"preferences.ttl: {len(steps)} steps, {sum(1 for v in steps.values() if v['attached'])} attached to a topic howto")
        if "superseded" in result:
            show("steps that mark another step superseded, reversed or corrected", result["superseded"], limit, ["step", "marker", "refers_to", "name"])
        if "dead-links" in result:
            show("dead rdfs:seeAlso links", result["dead-links"], limit, ["file", "link", "problem"])
        if "duplicates" in result:
            show("duplicate names", result["duplicates"], limit, ["kind", "name", "where"])
        if "unrouted" in result:
            rows = result["unrouted"]
            show("steps attached to no topic (suggestion from trigger phrases)", rows, limit, ["step", "suggested_topic", "matched_phrases", "name"])
            print(f"  with a suggestion: {sum(1 for r in rows if r['suggested_topic'])} of {len(rows)}")
    if a.strict and result.get("dead-links"):
        sys.exit(1)


if __name__ == "__main__":
    main()
