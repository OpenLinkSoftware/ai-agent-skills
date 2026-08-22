#!/usr/bin/env python3
"""
build-memory-manifest.py — SPARQL-first session-start memory context pack.

Queries the agent-rdf-memory named graphs in local Virtuoso (the RDF graph is the
source of truth) and renders a COMPACT manifest for injection at dsh session start
via dsh-agent-instructions (AGENTS.local.md project overlay, or ~/.dsh/AGENTS.md
user-global). Falls back to filesystem counts when the endpoint is unreachable.

Usage:
  python3 build-memory-manifest.py --out /path/to/AGENTS.local.md
  python3 build-memory-manifest.py --endpoint http://localhost:8890/sparql --limit 8
"""
import argparse, datetime, glob, os, re, sys, urllib.parse, urllib.request

STORE = "/Users/kidehen/Documents/Management/Development/ai-agent-skills/agent-rdf-memory"
SPARQL = "http://localhost:8890/sparql"
G = "urn:dav:/DAV/home/kidehen/agent-rdf-memory/"
PREF, INDEX, CORE = G+"preferences.ttl", G+"index.ttl", G+"core.ttl"
PREFIX = "PREFIX schema: <http://schema.org/>\nPREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n"

def q(endpoint, query):
    req = urllib.request.Request(endpoint, data=urllib.parse.urlencode({"query": PREFIX+query}).encode(),
                                 headers={"Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        import json
        return json.loads(r.read().decode("utf-8", "replace"))

def one(res):  # first binding value, or None
    b = res.get("results", {}).get("bindings", [])
    if not b:
        return None
    k = list(b[0])[0]
    return b[0][k].get("value")

def rows(res):
    return [(list(r)[0], r[list(r)[0]]["value"]) for r in res.get("results", {}).get("bindings", [])]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default=SPARQL)
    ap.add_argument("--store", default=STORE)
    ap.add_argument("--limit", type=int, default=8, help="recent sessions to list")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ep_ok = True
    try:
        steps  = one(q(a.endpoint, f"SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE {{ GRAPH <{PREF}> {{ ?s a schema:HowToStep }} }}"))
        sessi  = one(q(a.endpoint, f"SELECT (COUNT(DISTINCT ?i) AS ?n) WHERE {{ GRAPH <{INDEX}> {{ ?i a schema:ListItem }} }}"))
        howtos = one(q(a.endpoint, f"SELECT (COUNT(DISTINCT ?g) AS ?n) WHERE {{ GRAPH ?g {{ ?s a schema:HowTo }} FILTER (CONTAINS(STR(?g), 'agent-rdf-memory/howto/')) }}"))
        user   = one(q(a.endpoint, f"SELECT ?name WHERE {{ GRAPH <{CORE}> {{ ?u a schema:Person ; schema:name ?name }} }} LIMIT 1"))
        dspath = one(q(a.endpoint, f"SELECT ?v WHERE {{ GRAPH <{CORE}> {{ ?p a schema:PropertyValue ; schema:name ?n ; schema:value ?v FILTER (CONTAINS(LCASE(STR(?n)), 'deepseek')) }} }} LIMIT 1"))
        recent = []
        for b in q(a.endpoint, f"SELECT ?pos ?name WHERE {{ GRAPH <{INDEX}> {{ ?l a schema:ListItem ; schema:position ?pos ; schema:name ?name }} }}").get("results", {}).get("bindings", []):
            recent.append((int(b["pos"]["value"]), b["name"]["value"]))
        recent = [n for _, n in sorted(recent, reverse=True)[:a.limit]]
    except Exception as e:
        ep_ok = False
        steps = sessi = howtos = user = dspath = None
        recent = []
        # filesystem fallback (counts + latest filenames)
        try:
            sess_dir = os.path.join(a.store, "sessions")
            files = sorted(glob.glob(os.path.join(sess_dir, "*.ttl")), reverse=True)
            sessi = str(len(files))
            steps = str(len(glob.glob(os.path.join(a.store, "preferences.ttl")))) or "?"
            howtos = str(len(glob.glob(os.path.join(a.store, "howto", "*.ttl"))))
            recent = [os.path.basename(f) for f in files[:a.limit]]
            user = "Kingsley Uyi Idehen"
            dspath = "{LLM_ROOT}/DeepSeek/"
        except Exception:
            pass
        err = str(e)[:120]

    lines = ["# Agent RDF Memory — Session-Start Context Pack (graph-derived)",
             f"Generated: {now} · Source: {a.endpoint}",
             "Derived from the agent-rdf-memory RDF graph (Virtuoso named graphs); the graph is the source of truth, not this file.",
             ""]
    if not ep_ok:
        lines += ["> NOTE: SPARQL endpoint unreachable — values from filesystem fallback. " + (err or ""), ""]
    lines += ["## Identity & routing",
              f"- Principal: {user or 'unresolved'}",
              f"- DeepSeek output root: {dspath or 'unresolved'} (core.ttl)",
              ""]
    lines += ["## Behavioral contract (load before tasks)",
              f"- preferences.ttl: {steps or '?'} standing HowToStep instructions",
              f"- howto/: {howtos or '?'} HowTo documents",
              f"- Sessions indexed: {sessi or '?'} (index.ttl)",
              "- Precedence: preferences.ttl > AGENTS.md > defaults",
              ""]
    lines += [f"## Recent sessions (most recent first, from index graph)",
              *[f"{i+1}. {n}" for i, n in enumerate(recent)],
              ""]
    lines += ["## Retrieval mandate (per AGENTS.md)",
              "Execute the 5-step Agent RDF Memory Protocol before tasks: list agent-rdf-memory/, read core.ttl + preferences.ttl + index.ttl, follow index references into sessions/projects/entities/howto.",
              "Learning is cross-LLM and cross-environment: the store is shared; {llm-id}-{agent-env} in filenames is provenance, not isolation.",
              "After meaningful work, write session memory to sessions/YYYY-MM-DD-{llm-id}-{agent-env}.ttl and keep the graph in sync (refresh-loader.sh + session-graph-gate.py).",
              ""]
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"WROTE {a.out} ({'SPARQL' if ep_ok else 'fallback'} source)")

if __name__ == "__main__":
    main()
