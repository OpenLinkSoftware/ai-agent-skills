#!/usr/bin/env python3
"""
session-graph-gate.py — SPARQL session-graph existence/state check + sync (RDF-graph based).

Compares the local master agent-rdf-memory store against the named graphs loaded in
Virtuoso (or any SPARQL endpoint), reports deltas, and offers two sync paths that use
YOUR credentials (never displayed): isql (dba password typed by you) or curl SPARQL
Graph Store PUT (password prompted by curl, trailing-colon -u form).

Usage:
  check        python3 session-graph-gate.py check [--session NAME|--all] [--endpoint URL]
  sync-sql     python3 session-graph-gate.py sync-sql [--session NAME|--all] [--out FILE] [--dry-run]
  sync-curl    python3 session-graph-gate.py sync-curl [--session NAME|--all] [--dry-run]

Modes:
  check     SPARQL ASK/COUNT/dateModified/index-linkage against the endpoint for each
            session graph; verdict: IN_SYNC | STALE (dateModified/count delta) |
            GRAPH_MISSING | LOCAL_MISSING | ENDPOINT_UNREACHABLE.
  sync-sql  Writes an idempotent isql script (CLEAR + TTLP_MT with prefix preamble) for
            every local->graph delta. Run:  isql 1111 dba <your-password> -f <out>
  sync-curl Executes curl SPARQL Graph Store PUT (preambled Turtle) for every delta.
            Credentials: -u dba:  -> curl prompts for the password (never in argv/logs).

Local store (canonical source of truth) defaults to the master repo path; override with --store.
Endpoint defaults to http://localhost:8890/sparql (SPARQL) and .../sparql-graph-crud-auth (CRUD).
"""
import argparse, os, re, subprocess, sys, tempfile, urllib.parse, urllib.request

STORE   = "/Users/kidehen/Documents/Management/Development/ai-agent-skills/agent-rdf-memory"
SPARQL  = "http://localhost:8890/sparql"
CRUD    = "http://localhost:8890/sparql-graph-crud-auth"
G_BASE  = "urn:dav:/DAV/home/kidehen/agent-rdf-memory/"
INDEX_G = G_BASE + "index.ttl"
DECL    = re.compile(r'@prefix\s+(\w*):\s*<([^>]+)>\s*\.')
DM_RE   = re.compile(r'schema:dateModified\s+"([^"]+)"')

# ----------------------------------------------------------------------------

def session_files(store, only=None):
    d = os.path.join(store, "sessions")
    if only:
        p = os.path.join(d, only)
        return [p] if os.path.exists(p) else []
    return sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".ttl"))

def local_state(path):
    txt = open(path, encoding="utf-8", errors="replace").read()
    dm = DM_RE.search(txt)
    n = None
    try:
        import rdflib
        n = len(rdflib.Graph().parse(data=txt, format="turtle"))
    except Exception:
        n = None  # rdflib missing or file malformed -> count unknown, not 0
    return {"dateModified": dm.group(1) if dm else None, "triples": n}

def build_preamble(store):
    from collections import Counter
    by = {}
    for root, _, fs in os.walk(store):
        for f in fs:
            if not f.endswith(".ttl") or "/scripts/" in os.path.join(root, f):
                continue
            for m in DECL.finditer(open(os.path.join(root, f), encoding="utf-8", errors="replace").read()):
                by.setdefault(m.group(1), Counter()).update([m.group(2)])
    parts = []
    for name in sorted(by):
        iri = by[name].most_common(1)[0][0]
        if name == "okf" and iri.startswith("okf-"):
            continue
        parts.append(f"@prefix {name}: <{iri}> .")
    curated = {"owl":"http://www.w3.org/2002/07/owl#","cert":"http://www.w3.org/ns/auth/cert#",
      "oplcert":"http://www.openlinksw.com/schemas/cert#","prov":"http://www.w3.org/ns/prov#",
      "rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#","rdfs":"http://www.w3.org/2000/01/rdf-schema#",
      "foaf":"http://xmlns.com/foaf/0.1/","skos":"http://www.w3.org/2004/02/skos/core#",
      "event":"http://purl.org/NET/c4dm/event.owl#","opal":"https://www.openlinksw.com/ontology/opal/",
      "dbr":"http://dbpedia.org/resource/","dbo":"http://dbpedia.org/ontology/",
      "wd":"http://www.wikidata.org/entity/","xsd":"http://www.w3.org/2001/XMLSchema#",
      "schema":"http://schema.org/","acl":"http://www.w3.org/ns/auth/acl#",
      "xlink":"http://www.w3.org/1999/xlink","atom":"http://www.w3.org/2005/Atom",
      "sioc":"http://rdfs.org/sioc/ns#","dct":"http://purl.org/dc/terms/","dcterms":"http://purl.org/dc/terms/"}
    for n, iri in sorted(curated.items()):
        if n not in by:
            parts.append(f"@prefix {n}: <{iri}> .")
    return "\n".join(parts) + "\n\n"

import json as _json

def sparql(endpoint, q):
    req = urllib.request.Request(endpoint, data=urllib.parse.urlencode({"query": q}).encode(),
                                 headers={"Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        body = r.read().decode("utf-8", "replace")
    return _json.loads(body)

def bindings(result):
    return result.get("results", {}).get("bindings", [])

def ask(endpoint, q):
    return sparql(endpoint, q).get("boolean") is True

def count(endpoint, g):
    q = f"SELECT (COUNT(*) AS ?t) WHERE {{ GRAPH <{g}> {{ ?s ?p ?o }} }}"
    b = bindings(sparql(endpoint, q))
    return int(b[0]["t"]["value"]) if b else 0

def graph_dm(endpoint, g):
    q = f"SELECT ?dm WHERE {{ GRAPH <{g}> {{ <{g}> <http://schema.org/dateModified> ?dm }} }} LIMIT 1"
    b = bindings(sparql(endpoint, q))
    return b[0]["dm"]["value"] if b else None

def indexed(endpoint, g):
    q = f"ASK {{ GRAPH <{INDEX_G}> {{ ?x <http://schema.org/item> <{g}> }} }}"
    return ask(endpoint, q)

def graph_iri(rel):
    return G_BASE + rel

# ----------------------------------------------------------------------------

def check(args):
    files = session_files(args.store, args.session)
    if not files:
        print("no session files found"); return 2
    rows, n_missing = [], 0
    try:
        for f in files:
            rel = os.path.relpath(f, args.store).replace(os.sep, "/")
            g = graph_iri(rel)
            loc = local_state(f)
            try:
                exists = count(endpoint=args.endpoint, g=g) if ask(args.endpoint, f"ASK {{ GRAPH <{g}> {{ ?s ?p ?o }} }}") else 0
            except Exception:
                print(f"ENDPOINT UNREACHABLE: {args.endpoint}"); return 3
            if exists == 0:
                verdict = "GRAPH_MISSING"; n_missing += 1
            else:
                gdm = graph_dm(args.endpoint, g)
                if gdm is not None and loc["dateModified"] is not None and gdm != loc["dateModified"]:
                    verdict = f"STALE (dm graph={gdm} local={loc['dateModified']})"
                elif loc["triples"] is not None and exists != loc["triples"]:
                    verdict = f"STALE (triples graph={exists} local={loc['triples']})"
                else:
                    verdict = "IN_SYNC"
            idx = indexed(args.endpoint, g) if exists else False
            rows.append((rel, exists, loc["triples"], loc["dateModified"], verdict, idx))
    except Exception as e:
        print(f"ENDPOINT ERROR: {e}"); return 3
    print(f"{'session file':<58} {'graph':>6} {'local':>6}  verdict")
    for rel, gn, ln, dm, v, idx in rows:
        print(f"{rel:<58} {gn if gn is not None else '-':>6} {str(ln if ln is not None else '?'):>6}  {v}" + ("" if idx or not gn else "  [not in index graph]"))
    n_sync = sum(1 for r in rows if r[4] == "IN_SYNC")
    n_stale = sum(1 for r in rows if r[4].startswith("STALE"))
    print(f"\n{len(rows)} sessions: {n_sync} IN_SYNC, {n_stale} STALE, {n_missing} GRAPH_MISSING")
    if n_stale or n_missing:
        print("deltas found -> sync with:  session-graph-gate.py sync-sql [--all]   |   sync-curl [--all]")
    return 0

def deltas(args):
    out = []
    for f in session_files(args.store, args.session):
        rel = os.path.relpath(f, args.store).replace(os.sep, "/")
        g = graph_iri(rel)
        try:
            exists = count(endpoint=args.endpoint, g=g) if ask(args.endpoint, f"ASK {{ GRAPH <{g}> {{ ?s ?p ?o }} }}") else 0
        except Exception:
            print(f"ENDPOINT UNREACHABLE: {args.endpoint}"); sys.exit(3)
        if exists == 0:
            out.append((rel, g, f, "GRAPH_MISSING")); continue
        loc, gdm = local_state(f), graph_dm(args.endpoint, g)
        stale = (gdm is not None and loc["dateModified"] is not None and gdm != loc["dateModified"]) or \
                (loc["triples"] is not None and exists != loc["triples"])
        if stale:
            out.append((rel, g, f, f"STALE (dm {gdm}->{loc['dateModified']})"))
    return out

def sync_sql(args):
    d = deltas(args)
    if not d:
        print("no deltas — graph store is in sync"); return 0
    preamble = build_preamble(args.store)
    lines = ["-- session-graph-sync.sql (generated by session-graph-gate.py sync-sql)",
             "-- Run:  isql 1111 dba <your-password> -f session-graph-sync.sql", ""]
    for rel, g, f, why in d:
        lines += [f"-- {rel}  ({why})", f"SPARQL CLEAR GRAPH <{g}>;",
                  f"DB.DBA.TTLP_MT ('{preamble}' || file_to_string_output ('{f}'), '{g}', '{g}', 255);", ""]
    if args.dry_run:
        print("\n".join(lines)); return 0
    out = args.out or "session-graph-sync.sql"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"wrote {out}: {len(d)} graph(s) to sync")
    print(f"run with your credentials:  isql 1111 dba <dba-password> -f {out}")
    return 0

def sync_curl(args):
    d = deltas(args)
    if not d:
        print("no deltas — graph store is in sync"); return 0
    preamble = build_preamble(args.store)
    for rel, g, f, why in d:
        body = preamble + open(f, encoding="utf-8", errors="replace").read()
        with tempfile.NamedTemporaryFile("w", suffix=".ttl", delete=False) as t:
            t.write(body); tmp = t.name
        url = f"{args.crud}?graph-uri={urllib.parse.quote(g, safe='')}"
        cmd = ["curl", "-sS", "-u", "dba:", "-X", "PUT", "-H", "Content-Type: text/turtle",
               "--data-binary", "@" + tmp, url]
        print(f"-- {rel} ({why})")
        if args.dry_run:
            print("   " + " ".join(cmd)); continue
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            print(f"   PUT ok (graph <{g}>)")
        else:
            print(f"   PUT FAILED: {r.stderr.strip()}")
        os.unlink(tmp)
    print("\ncredentials: curl -u dba: prompts for the password; it never appears in argv or logs.")
    return 0

# ----------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="SPARQL session-graph existence/state check + sync")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("check", "sync-sql", "sync-curl"):
        s = sub.add_parser(name)
        s.add_argument("--session", help="single session filename (e.g. 2026-08-14-deepseek_v4_flash-dsh.ttl); default: all")
        s.add_argument("--all", action="store_true", help="all session files (default)")
        s.add_argument("--store", default=STORE, help="local master store path")
        s.add_argument("--endpoint", default=SPARQL)
        s.add_argument("--crud", default=CRUD)
        s.add_argument("--out", help="sync-sql output file")
        s.add_argument("--dry-run", action="store_true", help="print instead of write/execute")
    args = p.parse_args()
    args.session = args.session if args.session else (None if args.all else None)
    return {"check": check, "sync-sql": sync_sql, "sync-curl": sync_curl}[args.cmd](args)

if __name__ == "__main__":
    sys.exit(main())
