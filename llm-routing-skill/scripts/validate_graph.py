#!/usr/bin/env python3
"""validate_graph.py — GATE for the LLM routing graph.

Checks that references/routing-graph.ttl and routing-graph.json are consistent,
complete, and fresh. Run this after every build before using the graph for
routing decisions (see SKILL.md 'GATE: 0 failures required').

Checks:
  1. JSON mirror parses and has expected top-level keys.
  2. TTL parses (rdflib if available; otherwise lightweight structural checks).
  3. Every model in JSON has: id, vendor, prices.input/output, cost_tier,
     latency_class, non-empty capability vector.
  4. Every task has: required_level in L1..L5, non-empty pareto_frontier
     (except tasks with zero eligible models, e.g. embedding), escalation_ladder.
  5. TTL/JSON model-count parity and price parity spot-check.
  6. Freshness: graph priceUpdated is not older than the prices feed used.

Usage:
  python3 scripts/validate_graph.py
  python3 scripts/validate_graph.py --graph references/routing-graph.json
  python3 scripts/validate_graph.py --max-age-days 30

Exit codes: 0 = PASS (0 failures required); 1 = FAIL.
"""
import argparse
import json
import os
import re
import sys
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
REFS = os.path.join(SKILL, "references")

FAILURES = []


def fail(msg):
    FAILURES.append(msg)
    print(f"  FAIL: {msg}")


def ok(msg):
    print(f"  ok:   {msg}")


def load_json(path):
    with open(path) as fh:
        return json.load(fh)


def check_graph(graph):
    ok(f"graph schema: {graph.get('schema')}")
    ok(f"priceUpdated: {graph.get('updated_at')}")

    tasks = graph.get("tasks", [])
    models = graph.get("models", [])
    ok(f"{len(models)} models, {len(tasks)} task types")

    # freshness vs today (warn-only if feed unknown)
    updated = graph.get("updated_at")
    if updated and updated != "unknown":
        try:
            age = (date.today() - date.fromisoformat(updated)).days
            if age > args.max_age_days:
                fail(f"graph prices are {age} days old (> {args.max_age_days}); run fetch_prices.py + rebuild")
            else:
                ok(f"price freshness: {age} days old (limit {args.max_age_days})")
        except ValueError:
            ok("priceUpdated not ISO date — skipped freshness check")

    # models
    for m in models:
        mid = m.get("id")
        if not mid:
            fail("model with no id")
            continue
        if not m.get("vendor"):
            fail(f"{mid}: missing vendor")
        prices = m.get("prices") or {}
        if prices.get("input_per_mtok") is None:
            fail(f"{mid}: missing input price")
        if prices.get("output_per_mtok") is None:
            fail(f"{mid}: missing output price")
        if not m.get("cost_tier"):
            fail(f"{mid}: missing cost_tier")
        if not m.get("latency_class"):
            fail(f"{mid}: missing latency_class")
        if not m.get("capability"):
            fail(f"{mid}: empty capability vector (no family rule matched)")
    if not models:
        fail("no models in graph")

    # tasks
    for t in tasks:
        tid = t.get("id")
        req = t.get("required_level")
        if req not in ("L1", "L2", "L3", "L4", "L5"):
            fail(f"{tid}: required_level {req!r} not in L1..L5")
        if not t.get("dimensions"):
            fail(f"{tid}: no dimensions")
        # embedding task legitimately has an empty frontier/ladder (no embedding models in feed)
        if t.get("id") != "embedding" and not t.get("pareto_frontier"):
            fail(f"{tid}: empty pareto_frontier")
        if t.get("id") != "embedding" and not t.get("escalation_ladder"):
            fail(f"{tid}: empty escalation_ladder")
    if not tasks:
        fail("no tasks in graph")

    return models, tasks


def check_ttl(models, tasks):
    ttl_path = os.path.join(REFS, "routing-graph.ttl")
    if not os.path.exists(ttl_path):
        fail(f"missing {ttl_path}")
        return
    with open(ttl_path) as fh:
        ttl = fh.read()
    if "a llmr:Model, schema:SoftwareApplication" not in ttl:
        fail("TTL: no llmr:Model declarations found")
    model_blocks = ttl.count("a llmr:Model")
    if model_blocks != len(models):
        fail(f"TTL model count {model_blocks} != JSON model count {len(models)}")
    else:
        ok(f"TTL/JSON model count parity: {model_blocks}")
    for t in tasks:
        if f"llmrt:{t['id']}" not in ttl:
            fail(f"TTL: task {t['id']} missing")
    if "llmr:paretoFrontierModel" not in ttl:
        fail("TTL: no llmr:paretoFrontierModel assertions (set-triple frontier)")
    if "schema:itemListElement" not in ttl or "schema:ListItem" not in ttl:
        fail("TTL: no schema:ItemList escalation-ladder assertions")
    if "schema:additionalProperty" not in ttl or "schema:PropertyValue" not in ttl:
        fail("TTL: no schema:additionalProperty/PropertyValue capability assertions")
    if "llmr:dominantDimension" not in ttl:
        fail("TTL: no llmr:dominantDimension assertions")
    # verify no legacy RDF-list forms remain
    if "llmr:paretoFrontier (" in ttl or "llmr:escalationLadder (" in ttl or "llmr:capabilityProfile (" in ttl:
        fail("TTL: legacy RDF-list forms still present (llmr:paretoFrontier/escalationLadder/capabilityProfile lists)")
    for lvl in ("L1", "L2", "L3", "L4", "L5"):
        if f"llmrl:{lvl} a llmr:CapabilityLevel" not in ttl:
            fail(f"TTL: capability level {lvl} missing")
    # GATE: zero blank nodes (preferences.ttl Step 37 — absolute prohibition)
    try:
        import rdflib
        g = rdflib.Graph()
        g.parse(ttl_path, format="turtle")
        ok(f"rdflib Turtle parse OK ({len(g)} triples)")
        bn_subj = len(list(g.subjects(rdflib.BNode())))
        bn_obj = len([o for s, p, o in g if isinstance(o, rdflib.BNode)])
        if bn_subj + bn_obj > 0:
            fail(f"Step 37 violation: {bn_subj} blank-node subjects + {bn_obj} blank-node objects — all resources must be named IRIs")
        else:
            ok("blank-node check: 0 subjects, 0 objects")
        # GATE: every llmr: term used in the graph must be declared in the TBox
        tbox_path = os.path.join(REFS, "llm-routing-ontology.ttl")
        if os.path.exists(tbox_path):
            tb = rdflib.Graph()
            tb.parse(tbox_path, format="turtle")
            declared = set()
            for s in tb.subjects(None, None):
                if isinstance(s, rdflib.URIRef) and str(s).startswith("https://www.openlinksw.com/ontology/llm-routing#"):
                    declared.add(str(s))
            used = set()
            for s, p, o in g.triples((None, None, None)):
                for term in (s, p, o):
                    if isinstance(term, rdflib.URIRef) and str(term).startswith("https://www.openlinksw.com/ontology/llm-routing#"):
                        used.add(str(term))
            # instances (llmr:routingGraph, llmr:governance) are minted as individuals, not ontology terms
            instances = {
                "https://www.openlinksw.com/ontology/llm-routing#routingGraph",
                "https://www.openlinksw.com/ontology/llm-routing#governance",
            }
            missing = (used - declared) - instances
            if missing:
                fail(f"ontology gate: {len(missing)} llmr: term(s) used but NOT declared in llm-routing-ontology.ttl: " +
                     ", ".join(sorted(m.split('#')[-1] for m in missing)))
            else:
                ok(f"ontology gate: all {len(used - instances)} used llmr: terms declared in TBox")
        else:
            fail(f"ontology gate: missing TBox file {tbox_path}")
    except ImportError:
        ok("rdflib not installed — blank-node/ontology gates skipped (structural checks only)")
    except Exception as exc:
        fail(f"rdflib parse/check error: {exc}")


def main():
    global args
    ap = argparse.ArgumentParser(description="Validate the LLM routing graph (GATE)")
    ap.add_argument("--graph", default=os.path.join(REFS, "routing-graph.json"))
    ap.add_argument("--max-age-days", type=int, default=30)
    args = ap.parse_args()

    print("LLM Routing Graph — validation gate")
    graph = load_json(args.graph)
    models, tasks = check_graph(graph)
    check_ttl(models, tasks)

    print()
    if FAILURES:
        print(f"GATE FAILED: {len(FAILURES)} failure(s) — fix before using the graph.")
        return 1
    print("GATE PASSED: 0 failures.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
