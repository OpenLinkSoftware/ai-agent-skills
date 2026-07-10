#!/usr/bin/env python3
"""Validate generated RDF Turtle offer files against SHACL shapes. Exits 0=PASS, 1=FAIL."""
import argparse, sys, os
import rdflib
from pyshacl import validate

SHACL_DIR = os.path.join(os.path.dirname(__file__), "..", "shacl")

def load_graph(path):
    g = rdflib.Graph()
    try:
        g.parse(path, format="turtle")
    except Exception as e:
        print(f"SYNTAX FAIL: {path} - {e}", file=sys.stderr)
        sys.exit(1)
    return g

def main():
    parser = argparse.ArgumentParser(description="Validate RDF offer files with SHACL shapes.")
    parser.add_argument("offer_file")
    parser.add_argument("--shacl-dir", default=SHACL_DIR)
    parser.add_argument("--type", choices=["file","graph","api"])
    args = parser.parse_args()
    print(f"Parsing: {args.offer_file}")
    data_g = load_graph(args.offer_file)
    print(f"  OK - {len(data_g)} triples")
    common = os.path.join(args.shacl_dir, "common-offer-shape.ttl")
    shapes = {
        "file":  [common, os.path.join(args.shacl_dir, "file-access-offer-shape.ttl")],
        "graph": [common, os.path.join(args.shacl_dir, "graph-access-offer-shape.ttl")],
        "api":   [common, os.path.join(args.shacl_dir, "api-access-offer-shape.ttl")],
    }
    types = [args.type] if args.type else ["file","graph","api"]
    best_type, best_violations, best_result = None, None, None
    for ot in types:
        sf = shapes[ot]
        if not all(os.path.exists(s) for s in sf):
            continue
        sg = rdflib.Graph()
        for s in sf: sg.parse(s, format="turtle")
        conforms, rg, rt = validate(data_g, shacl_graph=sg, inference='rdfs', abort_on_first=False, meta_shacl=False)
        vc = sum(1 for _ in rg.query("SELECT (COUNT(?v) as ?c) WHERE { ?v a sh:ValidationResult }"))
        if best_violations is None or vc < best_violations:
            best_type, best_violations, best_result = ot, vc, (conforms, rt)
    if best_type is None:
        print("FAIL: No SHACL shapes applied.", file=sys.stderr)
        sys.exit(1)
    conforms, rt = best_result
    if args.type is None:
        print(f"  Auto-detected: {best_type}")
    if conforms:
        print(f"  SHACL PASS - {best_violations} violations")
        sys.exit(0)
    else:
        print(f"  SHACL FAIL - {best_violations} violation(s):", file=sys.stderr)
        print(rt, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
