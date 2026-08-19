#!/usr/bin/env python3
"""route.py — Query the LLM routing graph for a routing decision.

Given a task type + cost tier + routing policy (+ optional latency or vendor
constraints), return the recommended model and the Pareto-frontier alternatives,
using the capability x cost x latency graph in references/routing-graph.json.

This is the executable companion to SKILL.md's routing workflow — the graph is
the source of truth; this CLI is one way to query it (SPARQL over the TTL is the
other, see SKILL.md 'Query templates').

Usage:
  python3 scripts/route.py code-generation medium
  python3 scripts/route.py code-generation low --policy quality-first
  python3 scripts/route.py summarization high --latency low --vendor openai
  python3 scripts/route.py --list-tasks
  python3 scripts/route.py --list-models
  python3 scripts/route.py code-generation medium --json

Policies:
  cost-first      — cheapest model meeting the required capability level
  balanced        — default; cheapest Pareto-frontier model at required level
  quality-first   — highest-capability model within the cost tier
  latency-first   — lowest latency among models meeting required level

Exit codes: 0 decision produced; 1 unknown task/tier/policy; 2 data error.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
GRAPH = os.path.join(SKILL, "references", "routing-graph.json")

LEVEL_ORDER = {"L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}
LATENCY_ORDER = {"very-low": 1, "low": 2, "medium": 3, "high": 4, "very-high": 5}
POLICIES = ("cost-first", "balanced", "quality-first", "latency-first")


def load_graph():
    if not os.path.exists(GRAPH):
        raise SystemExit(f"ERROR: graph not found at {GRAPH} — run scripts/build_routing_graph.py first")
    with open(GRAPH) as fh:
        return json.load(fh)


def find_task(graph, task_id):
    for t in graph["tasks"]:
        if t["id"] == task_id:
            return t
    return None


def model_map(graph):
    return {m["id"]: m for m in graph["models"]}


def capability_score(model, task):
    dims = task.get("dimensions", [])
    cap = model.get("capability", {})
    if not dims:
        return 0.0
    vals = [cap.get(d, 0) for d in dims]
    return round(sum(vals) / len(vals), 2)


def level_for(score):
    if score >= 4.5:
        return "L5"
    if score >= 3.5:
        return "L4"
    if score >= 2.5:
        return "L3"
    if score >= 1.5:
        return "L2"
    return "L1"


def decide(graph, task_id, tier, policy, latency_max=None, vendors=None):
    task = find_task(graph, task_id)
    if not task:
        raise SystemExit(f"ERROR: unknown task type '{task_id}' (see --list-tasks)")
    if tier not in ("low", "medium", "high", "max"):
        raise SystemExit(f"ERROR: unknown cost tier '{tier}' (low|medium|high|max)")
    if policy not in POLICIES:
        raise SystemExit(f"ERROR: unknown policy '{policy}' ({'|'.join(POLICIES)})")

    threshold = graph["cost_tier_thresholds"].get(tier, {})
    max_price = threshold.get("max_output_price")
    models = model_map(graph)
    required_level = task.get("required_level", "L3")

    cands = []
    for m in models.values():
        if vendors and m["vendor"] not in vendors:
            continue
        if latency_max and LATENCY_ORDER.get(m["latency_class"], 9) > LATENCY_ORDER.get(latency_max, 9):
            continue
        price = (m.get("prices") or {}).get("output_per_mtok")
        if price is None:
            continue
        if max_price is not None and price > max_price:
            continue
        score = capability_score(m, task)
        lvl = level_for(score)
        cands.append({
            "id": m["id"], "vendor": m["vendor"], "name": m["name"],
            "score": score, "level": lvl, "price": price,
            "latency": m["latency_class"], "tier": m["cost_tier"],
        })
    if not cands:
        raise SystemExit(f"ERROR: no model satisfies task={task_id} tier={tier} "
                         f"latency<={latency_max} vendors={vendors}")

    adequate = [c for c in cands if LEVEL_ORDER[c["level"]] >= LEVEL_ORDER[required_level]]
    if not adequate:
        raise SystemExit(
            f"ERROR: no model in tier '{tier}' meets required level {required_level} for {task_id} — "
            "raise the cost tier or relax constraints")

    if policy == "cost-first":
        pick = min(adequate, key=lambda c: c["price"])
    elif policy == "quality-first":
        pick = max(adequate, key=lambda c: (c["score"], -c["price"]))
    elif policy == "latency-first":
        pick = min(adequate, key=lambda c: (LATENCY_ORDER[c["latency"]], c["price"]))
    else:  # balanced
        frontier = task.get("pareto_frontier", [])
        on_frontier = [c for c in adequate if c["id"] in frontier]
        pool = on_frontier or adequate
        pick = min(pool, key=lambda c: c["price"])

    # escalation ladder from the task (advisor pattern)
    ladder_ids = task.get("escalation_ladder", [])
    ladder = [models[i] for i in ladder_ids if i in models]

    return {
        "task": task_id,
        "task_label": task.get("label"),
        "required_level": required_level,
        "cost_tier": tier,
        "policy": policy,
        "recommended": pick,
        "alternatives": sorted(adequate, key=lambda c: c["price"])[:8],
        "escalation_ladder": [
            {
                "id": m["id"], "name": m["name"],
                "output_per_mtok": (m.get("prices") or {}).get("output_per_mtok"),
                "latency": m["latency_class"],
            }
            for m in ladder
        ],
        "graph_updated_at": graph.get("updated_at"),
    }


def fmt(d):
    print(f"Task:            {d['task']} ({d['task_label']})")
    print(f"Required level:  {d['required_level']}")
    print(f"Cost tier:       {d['cost_tier']}  |  Policy: {d['policy']}")
    print(f"Graph prices:    updated {d['graph_updated_at']}")
    print()
    r = d["recommended"]
    print(f"RECOMMENDED:     {r['name']}  [{r['id']}]")
    print(f"  vendor={r['vendor']}  level={r['level']} (score {r['score']})  "
          f"${r['price']}/MTok out  latency={r['latency']}")
    print()
    print("Alternatives (cheapest first, all meet required level within tier):")
    for a in d["alternatives"][:6]:
        print(f"  - {a['name']:34s} [{a['id']}]  {a['level']}  ${a['price']}/MTok  {a['latency']}")
    print()
    if d["escalation_ladder"]:
        print("Escalation ladder (advisor pattern — try cheap first, escalate on failure):")
        for e in d["escalation_ladder"]:
            print(f"  - {e['name']:34s} [{e['id']}]  ${e['output_per_mtok']}/MTok  {e['latency']}")
    else:
        print("Escalation ladder: none available for this task in graph.")


def main():
    ap = argparse.ArgumentParser(description="Query the LLM routing graph")
    ap.add_argument("task", nargs="?", help="task type id (see --list-tasks)")
    ap.add_argument("tier", nargs="?", default="medium", help="cost tier: low|medium|high|max")
    ap.add_argument("--policy", default="balanced", choices=POLICIES)
    ap.add_argument("--latency", help="max latency class: very-low|low|medium|high|very-high")
    ap.add_argument("--vendor", action="append", help="restrict vendors (repeatable)")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--list-tasks", action="store_true")
    ap.add_argument("--list-models", action="store_true")
    args = ap.parse_args()

    graph = load_graph()

    if args.list_tasks:
        for t in graph["tasks"]:
            print(f"  {t['id']:28s} {t['required_level']}  {t['label']}")
        return 0
    if args.list_models:
        for m in sorted(graph["models"], key=lambda x: x["vendor"]):
            print(f"  {m['vendor']:12s} {m['id']:34s} ${(m.get('prices') or {}).get('output_per_mtok')}")
        return 0
    if not args.task:
        ap.error("task type required (use --list-tasks to see options)")

    d = decide(graph, args.task, args.tier, args.policy,
               latency_max=args.latency, vendors=args.vendor)
    if args.json:
        print(json.dumps(d, indent=2))
    else:
        fmt(d)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
