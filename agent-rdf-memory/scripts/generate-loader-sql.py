#!/usr/bin/env python3
"""
generate-loader-sql.py — regenerate load-agent-rdf-memory.sql from the current store.

Enumerates every .ttl under the master agent-rdf-memory store (excluding scripts/),
builds the 28-prefix load-time preamble (store-wide union + curated well-known
namespaces), verifies every file parses WITH the preamble (rdflib), and writes the
idempotent isql loader (CLEAR GRAPH + TTLP_MT per document, one named graph per file).

Zero-byte documents were added as an explicit WARNING 2026-09-16: an empty Turtle
document parses fine (so the parse gate cannot see it) but yields no triples, so its
graph is CLEARed and nothing is loaded. That is correct behaviour for a deliberately
emptied document, and indistinguishable from a truncated or abandoned write — so it is
reported loudly rather than silently absorbed. scripts/full-store-graph-gate.py reports
such a file as EMPTY_DOC rather than GRAPH_MISSING.

Usage:
  python3 generate-loader-sql.py [--store PATH] [--out PATH]
"""
import argparse, glob, os, re, sys
from collections import Counter

STORE = "/Users/kidehen/Documents/Management/Development/ai-agent-skills/agent-rdf-memory"
OUT   = STORE + "/scripts/load-agent-rdf-memory.sql"
DECL  = re.compile(r'@prefix\s+(\w*):\s*<([^>]+)>\s*\.')

def collect_files(store):
    files = sorted(glob.glob(store + "/**/*.ttl", recursive=True))
    # *.example.ttl are templates (people.example.ttl, preferences.private.example.ttl), not memory
    return [f for f in files if "/scripts/" not in f and not f.endswith(".example.ttl")]

def build_preamble(files):
    by = {}
    for f in files:
        for m in DECL.finditer(open(f, encoding="utf-8", errors="replace").read()):
            by.setdefault(m.group(1), Counter()).update([m.group(2)])
    parts = []
    for name in sorted(by):
        iri = by[name].most_common(1)[0][0]
        if name == "okf" and iri.startswith("okf-"):   # relative IRI; skip global binding
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

def verify(files, preamble):
    try:
        import rdflib
    except ImportError:
        print("WARNING: rdflib not installed — parse verification skipped")
        return True
    ok = 0
    for f in files:
        try:
            rdflib.Graph().parse(data=preamble + "\n\n" + open(f, encoding="utf-8", errors="replace").read(), format="turtle")
            ok += 1
        except Exception as e:
            print("FAILS:", os.path.relpath(f, os.path.dirname(os.path.dirname(f))), "->", str(e)[:90])
            return False
    print(f"verify: {ok}/{len(files)} parse OK with preamble")
    return True

def warn_empty(files, store):
    """Report zero-byte documents: they parse, load nothing, and leave no graph.

    Correct for a deliberately emptied document; indistinguishable from a truncated
    or abandoned write — hence a warning, not a silent pass and not an error.
    """
    empties = [f for f in files if os.path.getsize(f) == 0]
    if empties:
        print(f"WARNING: {len(empties)} zero-byte document(s) — an empty Turtle document yields no triples, so the")
        print("         loader CLEARs its graph and loads nothing (no graph results). Confirm each is intentional")
        print("         and not a truncated or abandoned write:")
        for f in empties:
            print("           " + os.path.relpath(f, store))
    return empties

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default=STORE)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    # Virtuoso resolves file_to_string_output() paths against ITS OWN cwd, so a
    # relative --store yields a loader that CLEARs every graph and loads nothing
    # (happened 2026-09-18). Always emit absolute paths.
    a.store = os.path.abspath(a.store)
    files = collect_files(a.store)
    preamble = build_preamble(files)
    if not verify(files, preamble):
        sys.exit(1)
    empties = warn_empty(files, a.store)
    sql = ["-- ============================================================================",
           "-- load-agent-rdf-memory.sql  (generated by scripts/generate-loader-sql.py)",
           f"-- {len(files)} Turtle documents ({len(empties)} zero-byte), one named graph each:",
           "--   urn:dav:/DAV/home/kidehen/agent-rdf-memory/<relpath>",
           "-- Usage:  isql 1111 dba <password> load-agent-rdf-memory.sql   (idempotent)",
           "--   The script is a POSITIONAL argument on Virtuoso 08.03.3335 isql.",
           "--   '-f <file>' CONNECTS SUCCESSFULLY and then aborts at line 0 with",
           "--   'Cannot open file \"-f\" for loading' — a syntax failure that reads like a",
           "--   credential failure. Do not add -f. See howto/agent-rdf-memory-loader-run.ttl.",
           "-- ============================================================================", ""]
    gb = "urn:dav:/DAV/home/kidehen/agent-rdf-memory/"
    for f in files:
        rel = os.path.relpath(f, a.store).replace(os.sep, "/")
        g = gb + rel
        sql += [f"-- {rel}", f"SPARQL CLEAR GRAPH <{g}>;",
                f"DB.DBA.TTLP_MT ('{preamble}' || file_to_string_output ('{f}'), '{g}', '{g}', 255);", ""]
    sql += ["-- ============================================================================",
            "-- Verification: per-graph triple counts",
            "-- (this output also feeds the orphan check: full-store-graph-gate.py --graphs-from <this log>)",
            "-- ============================================================================",
            "SPARQL",
            "SELECT ?g (COUNT(*) AS ?t) WHERE { GRAPH ?g { ?s ?p ?o }",
            "  FILTER (CONTAINS(STR(?g), 'agent-rdf-memory')) }",
            "GROUP BY ?g ORDER BY DESC(?t);"]
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(sql))
    print(f"WROTE {a.out} ({len(files)} files, preamble {len(preamble.splitlines())} prefixes)")

if __name__ == "__main__":
    main()
