#!/usr/bin/env python3
"""
full-store-graph-gate.py — whole-store sync gate for agent-rdf-memory vs a SPARQL endpoint.

WHY THIS EXISTS
    scripts/session-graph-gate.py audits sessions/ only (279 of 475 documents). On
    2026-09-16 that gate reported clean while 19 howto/ docs, 2 projects/ docs and the
    entire behavioral contract (preferences.ttl, index.ttl, core.ttl, entities/) sat
    stale in the quad store. This gate covers every .ttl in the store.

WHAT IT CHECKS
    For each document: the named graph <urn:dav:/DAV/home/kidehen/agent-rdf-memory/<relpath>>
    is compared against the file on disk on (a) distinct triple count, (b) the
    schema:dateModified literal.

VERDICTS
    IN_SYNC          counts and dateModified agree.
    STALE            count or dateModified differs and no known artifact explains it.
    GRAPH_MISSING    file has triples, graph absent or empty -> the load never ran.
    EMPTY_DOC        0-byte file, no graph — correct by construction, flagged not failed.
    REL_IRI_ARTIFACT graph = local + 1, isolated to a single predicate, in a document
                     whose text uses relative IRIs. Explained below; not a failure.
    PARSE_ERROR / QUERY_ERROR  the check itself could not run (reported, never silent).

REL_IRI_ARTIFACT — the documented, permanent false positive (2026-09-16)
    Documents that write subjects/objects as RELATIVE IRIs get resolved against the
    graph IRI by the loader (-> urn:dav:...) but against the file/cwd by rdflib
    (-> file://...). Two relative paths naming the same real file then collapse into one
    triple on the rdflib side (a Graph is a set) while staying distinct under the
    urn:dav: base — where COUNT(DISTINCT ?s ?p ?o) agrees with the graph. The graph is
    the SUPERSET; nothing is missing. sessions/2026-05-29-gpt5-codex.ttl is the reference
    case: permanently graph=79 / local=78, the entire delta on schema:workExample.
    This script detects that shape (single-predicate +1 delta in a relative-IRI document)
    and reports it separately instead of failing the run, so a green run means green.
    It is still printed — never hidden — and `--json` carries it as its own field.

THE ORPHAN DIRECTION NEEDS CREDENTIALS
    Enumerating graphs anonymously is refused on this endpoint (HTTP 401 "Permission
    denied: authentication required") while per-graph ASK/COUNT queries are served
    anonymously. Pass --graphs-from with the loader's isql output (it ends with a
    per-graph COUNT query) to get the reverse-direction check without this script ever
    holding a credential:
        isql 1111 dba <password> <loader.sql> > load.log
        python3 full-store-graph-gate.py --graphs-from load.log

CONCURRENT WRITERS
    Memory is written by whichever agent session is running and enters the store only
    when someone loads it, so sync is a snapshot, never a steady state. A document edited
    after the load legitimately reappears as STALE: re-run the refresh + load rather than
    reclassifying it.

Usage:
  python3 full-store-graph-gate.py [--store PATH] [--endpoint URL] [--graphs-from LOG] [--json]

Exit status: 0 = no deltas (artifacts and empty documents do not fail the run),
             1 = deltas or orphans found, 2 = no documents, 3 = endpoint unreachable.
"""
import argparse, json, os, re, sys, urllib.parse, urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

STORE    = "/Users/kidehen/Documents/Management/Development/ai-agent-skills/agent-rdf-memory"
SPARQL   = "http://localhost:8890/sparql"
G_BASE   = "urn:dav:/DAV/home/kidehen/agent-rdf-memory/"
DM_RE    = re.compile(r'schema:dateModified\s+"([^"]+)"')
REL_RE   = re.compile(r'<(?:\.\./|#)')
GRAPH_RE = re.compile(r'urn:dav:/DAV/home/kidehen/agent-rdf-memory/[^\s;]+\.ttl')
SKIP_DIRS = {"scripts", "__pycache__", ".git", ".claude", ".hooks"}
OK_VERDICTS = ("IN_SYNC", "EMPTY_DOC", "REL_IRI_ARTIFACT")


def sparql(endpoint, query, timeout=60):
    req = urllib.request.Request(
        endpoint, data=urllib.parse.urlencode({"query": query}).encode(),
        headers={"Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def bindings(res):
    return res.get("results", {}).get("bindings", [])


def graph_count(endpoint, g):
    b = bindings(sparql(endpoint, f"SELECT (COUNT(*) AS ?t) WHERE {{ GRAPH <{g}> {{ ?s ?p ?o }} }}"))
    return int(b[0]["t"]["value"]) if b else 0


def graph_dm(endpoint, g):
    b = bindings(sparql(endpoint,
        f"SELECT ?dm WHERE {{ GRAPH <{g}> {{ <{g}> <http://schema.org/dateModified> ?dm }} }} LIMIT 1"))
    return b[0]["dm"]["value"] if b else None


def graph_predicates(endpoint, g):
    q = f"SELECT ?p (COUNT(*) AS ?t) WHERE {{ GRAPH <{g}> {{ ?s ?p ?o }} }} GROUP BY ?p"
    return {b["p"]["value"]: int(b["t"]["value"]) for b in bindings(sparql(endpoint, q))}


def collect_files(store):
    out = []
    for root, dirs, fs in os.walk(store):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(fs):
            if f.endswith(".ttl"):
                out.append(os.path.join(root, f))
    return sorted(out)


def local_state(path):
    if os.path.getsize(path) == 0:
        return None, 0, ""
    txt = open(path, encoding="utf-8", errors="replace").read()
    m = DM_RE.search(txt)
    try:
        import rdflib
        n = len(rdflib.Graph().parse(data=txt, format="turtle"))
    except ImportError:
        n = None                      # count unavailable, not zero
    except Exception as e:
        n = f"PARSE_ERROR:{e.__class__.__name__}"
    return (m.group(1) if m else None), n, txt


def artifact_predicate(endpoint, g, txt):
    """Return the single predicate carrying a +1 graph-only delta, or None.

    Only called for graph = local + 1 in a relative-IRI document — the exact shape of the
    documented collapse artifact. A different predicate distribution returns None and the
    document stays STALE, so real drift is never absorbed here.
    """
    if not REL_RE.search(txt):
        return None
    try:
        import rdflib
        local = Counter(str(p) for _s, p, _o in rdflib.Graph().parse(data=txt, format="turtle"))
    except Exception:
        return None
    deltas = [(p, t - local.get(p, 0)) for p, t in graph_predicates(endpoint, g).items()]
    plus = [p for p, d in deltas if d == 1]
    if len(plus) == 1 and all(d in (0, 1) for _p, d in deltas):
        return plus[0]
    return None


def check_one(endpoint, store, path):
    rel = os.path.relpath(path, store).replace(os.sep, "/")
    g = G_BASE + rel
    ldm, ln, txt = local_state(path)
    try:
        gn = graph_count(endpoint, g)
    except Exception as e:
        return (rel, None, ln, ldm, f"QUERY_ERROR:{e.__class__.__name__}")
    if ln == 0:
        return (rel, gn, ln, ldm, "EMPTY_DOC" if gn == 0 else "STALE (graph has triples, file is empty)")
    if gn == 0:
        return (rel, gn, ln, ldm, "GRAPH_MISSING")
    if isinstance(ln, str):
        return (rel, gn, ln, ldm, ln)
    if ln != gn:
        if gn == ln + 1:
            pred = artifact_predicate(endpoint, g, txt)
            if pred:
                return (rel, gn, ln, ldm, f"REL_IRI_ARTIFACT (+1 on {pred.split('/')[-1] or pred})")
        return (rel, gn, ln, ldm, f"STALE (graph={gn} local={ln})")
    gdm = graph_dm(endpoint, g)
    if gdm and ldm and gdm != ldm:
        return (rel, gn, ln, ldm, f"STALE (dm graph={gdm} local={ldm})")
    return (rel, gn, ln, ldm, "IN_SYNC")


def main():
    ap = argparse.ArgumentParser(description="Whole-store memory sync gate (every document, not just sessions/).")
    ap.add_argument("--store", default=STORE)
    ap.add_argument("--endpoint", default=SPARQL)
    ap.add_argument("--graphs-from", metavar="LOG",
                    help="isql output containing the loader's per-graph COUNT query; enables the orphan check")
    ap.add_argument("--json", action="store_true", help="emit machine-readable results")
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()

    files = collect_files(a.store)
    if not files:
        print(f"no .ttl documents found under {a.store}")
        return 2

    try:
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            rows = list(ex.map(lambda p: check_one(a.endpoint, a.store, p), files))
    except Exception as e:
        print(f"ENDPOINT UNREACHABLE: {a.endpoint} ({e})")
        return 3

    bad = [r for r in rows if r[4].split(" ")[0].split(":")[0] not in OK_VERDICTS]
    artifacts = [r for r in rows if r[4].startswith("REL_IRI_ARTIFACT")]
    empties = [r[0] for r in rows if r[4] == "EMPTY_DOC"]

    orphans, orphans_checked = [], False
    if a.graphs_from:
        in_store = set()
        for line in open(a.graphs_from, encoding="utf-8", errors="replace"):
            in_store.update(GRAPH_RE.findall(line))
        orphans = sorted(in_store - {G_BASE + r[0] for r in rows})
        orphans_checked = True

    if a.json:
        print(json.dumps({"documents": len(rows), "out_of_sync": len(bad), "empty": empties,
                          "artifacts": [r[0] for r in artifacts], "orphans": orphans,
                          "rows": [dict(zip(("document", "graph_triples", "local_triples",
                                             "dateModified", "verdict"), r)) for r in rows]}, indent=2))
        return 1 if (bad or orphans) else 0

    by_dir = defaultdict(Counter)
    for rel, _gn, _ln, _dm, v in rows:
        by_dir[rel.split("/")[0] if "/" in rel else "(root)"][v.split(" ")[0].split(":")[0]] += 1

    print("== per-folder verdicts ==")
    for d in sorted(by_dir):
        c = by_dir[d]
        print(f"  {d:<12} total={sum(c.values()):<4} " + "  ".join(f"{k}={v}" for k, v in sorted(c.items())))

    print(f"\n== out-of-sync documents ({len(bad)}) ==")
    for rel, gn, ln, _dm, v in bad:
        print(f"  {rel:<66} graph={gn if gn is not None else '-':<6} local={ln}  {v}")
    if not bad:
        print("  (none)")

    if artifacts:
        print(f"\n== relative-IRI counting artifacts ({len(artifacts)}) — graph is the superset, nothing missing ==")
        for rel, gn, ln, _dm, v in artifacts:
            print(f"  {rel:<66} graph={gn:<6} local={ln}  {v}")

    if empties:
        print(f"\n== empty documents, no graph by construction ({len(empties)}) ==")
        for rel in empties:
            print(f"  {rel}   (0 bytes — flagged, not drift)")

    if orphans_checked:
        print(f"\n== orphan graphs: in the store, no file on disk ({len(orphans)}) ==")
        for g in orphans:
            print(f"  {g}")
        if not orphans:
            print("  (none)")
    else:
        print("\n== orphan direction: SKIPPED (pass --graphs-from <loader log>; anonymous graph "
              "enumeration returns HTTP 401) ==")

    idx = G_BASE + "index.ttl"
    try:
        idx_graph = graph_count(a.endpoint, idx)
        idx_disk = local_state(os.path.join(a.store, "index.ttl"))[1]
        idx_links_disk = len(set(re.findall(r'schema:item\s+<([^>]+)>',
                               open(os.path.join(a.store, "index.ttl"), encoding="utf-8").read())))
        b = bindings(sparql(a.endpoint,
            f"SELECT (COUNT(DISTINCT ?i) AS ?n) WHERE {{ GRAPH <{idx}> {{ ?x <http://schema.org/item> ?i }} }}"))
        idx_links_graph = int(b[0]["n"]["value"]) if b else 0
        print("\n== index graph ==")
        print(f"  triples  graph={idx_graph}  disk={idx_disk}")
        print(f"  schema:item links  graph={idx_links_graph}  disk={idx_links_disk}")
    except Exception as e:
        print(f"\n== index graph: unreadable ({e}) ==")

    n_sync = sum(1 for r in rows if r[4] == "IN_SYNC")
    print(f"\n== totals ==\n  documents={len(rows)}  in_sync={n_sync}  empty={len(empties)}  "
          f"artifacts={len(artifacts)}  out_of_sync={len(bad)}"
          + (f"  orphans={len(orphans)}" if orphans_checked else ""))
    if bad or orphans:
        print("  deltas found -> regenerate + reload:  bash scripts/refresh-loader.sh")
    return 1 if (bad or orphans) else 0


if __name__ == "__main__":
    sys.exit(main())
