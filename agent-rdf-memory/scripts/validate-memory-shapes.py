#!/usr/bin/env python3
"""
validate-memory-shapes.py — SHACL validation for the agent-rdf-memory store.

Checks session files, index.ttl and preferences.ttl against shapes/memory-shapes.ttl
using pyshacl. Each file is parsed with its own file URI as base, so relative IRIs
such as <> resolve the same way they do when the file is loaded into Virtuoso.

Usage:
  python3 scripts/validate-memory-shapes.py                 # report all, exit 0
  python3 scripts/validate-memory-shapes.py --strict        # exit 1 on any violation
  python3 scripts/validate-memory-shapes.py sessions/2026-10-08-claude_haiku_5_5-claude_code.ttl
  python3 scripts/validate-memory-shapes.py --json report.json

Default mode is report-only. --strict is for CI and for the Stop-hook switch
after the baseline is clean (see howto/memory-shacl-validation.ttl).
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter
from pathlib import Path

import rdflib
from pyshacl import validate

HERE = Path(__file__).resolve().parent
STORE = HERE.parent
SHAPES = STORE / "shapes" / "memory-shapes.ttl"
SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")


def group_of(rel: str) -> str:
    if rel.startswith("sessions/"):
        return "sessions"
    if rel == "index.ttl":
        return "index"
    if rel == "preferences.ttl":
        return "preferences"
    return "other"


def default_files() -> list[Path]:
    files = sorted(Path(p) for p in glob.glob(str(STORE / "sessions" / "*.ttl")))
    files += [STORE / "index.ttl", STORE / "preferences.ttl"]
    return files


def check_file(path: Path, shapes_graph: rdflib.Graph) -> dict:
    rel = path.relative_to(STORE).as_posix()
    result = {"file": rel, "group": group_of(rel), "conforms": None, "violations": []}
    try:
        data = rdflib.Graph().parse(path.as_uri(), format="turtle")
    except Exception as exc:  # parse failure is itself a violation
        result["conforms"] = False
        result["violations"].append(f"parse error: {str(exc)[:160]}")
        return result
    conforms, report_graph, _ = validate(
        data,
        shacl_graph=shapes_graph,
        data_graph_format="turtle",
        shacl_graph_format="turtle",
        inference=None,
        abort_on_first=False,
        advanced=True,
    )
    result["conforms"] = bool(conforms)
    for res in report_graph.subjects(rdflib.RDF.type, SH.ValidationResult):
        msg = report_graph.value(res, SH.resultMessage)
        focus = report_graph.value(res, SH.focusNode)
        path_ = report_graph.value(res, SH.resultPath)
        text = str(msg) if msg is not None else f"{path_} constraint failed"
        result["violations"].append(f"{focus} :: {text}")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="SHACL-validate agent-rdf-memory files")
    ap.add_argument("files", nargs="*", help="files to check (default: sessions, index, preferences)")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any file violates")
    ap.add_argument("--json", metavar="PATH", help="write the full report as JSON")
    args = ap.parse_args()

    shapes_graph = rdflib.Graph().parse(SHAPES.as_uri(), format="turtle")
    paths = [Path(os.path.abspath(f)) for f in args.files] if args.files else default_files()
    results = [check_file(p, shapes_graph) for p in paths]

    by_group: dict[str, Counter] = {}
    for r in results:
        c = by_group.setdefault(r["group"], Counter())
        c["files"] += 1
        c["conforming" if r["conforms"] else "failing"] += 1
    print(f"{'group':<12} {'files':>6} {'conforming':>11} {'failing':>8}")
    for g in sorted(by_group):
        c = by_group[g]
        print(f"{g:<12} {c['files']:>6} {c['conforming']:>11} {c['failing']:>8}")

    rules = Counter()
    for r in results:
        for v in r["violations"]:
            rules[v.split(" :: ", 1)[-1]] += 1
    if rules:
        print("\ntop violations:")
        for text, n in rules.most_common(8):
            print(f"  {n:>4}  {text}")

    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nwrote {args.json}")

    failing = [r for r in results if not r["conforms"]]
    if args.strict and failing:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
