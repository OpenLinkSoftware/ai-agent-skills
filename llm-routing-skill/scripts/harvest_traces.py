#!/usr/bin/env python3
"""harvest_traces.py — Turn session routing traces into seed-profile refinements.

Reads the private trace log (references/traces/trace-log.ttl), aggregates
quality outcomes per (model, task), compares the observed average against the
seed capability profile's implied score for that task, and either:

  --report   shows the harvest summary and proposed explicit_overrides deltas
             (default, no writes)
  --apply    writes the deltas into references/capability-profiles.json, then
             rebuilds the graph and runs the GATE — the automatic feedback loop

This is the mechanical half of the 'feedback loop keeps the graph alive'
design: traces are the evidence, the seed profile is the hypothesis, and the
rebuild produces the corrected Pareto frontier. Traces are PRIVATE and local;
nothing here touches URIBurner or any public surface.

Usage:
  python3 scripts/harvest_traces.py               # report only
  python3 scripts/harvest_traces.py --apply       # apply + rebuild + GATE
  python3 scripts/harvest_traces.py --min-samples 3 --delta 1
  python3 scripts/harvest_traces.py --traces /path/to/trace-log.ttl

Exit codes: 0 ok; 1 no traces / parse error; 2 build/gate failure (--apply).
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
REFS = os.path.join(SKILL, "references")
TRACE_LOG = os.path.join(REFS, "traces", "trace-log.ttl")
PROFILES = os.path.join(REFS, "capability-profiles.json")
TASKS = os.path.join(REFS, "task-types.json")

LLMR = "https://www.openlinksw.com/ontology/llm-routing#"
LLMRM = "https://www.openlinksw.com/ontology/llm-routing/models/"
LLMRT = "https://www.openlinksw.com/ontology/llm-routing/tasks/"

# how much observed quality must deviate from the seed-implied score (in 1-5
# capability units) before a refinement is proposed
DEFAULT_DELTA = 1.0
DEFAULT_MIN_SAMPLES = 2


def load_traces(path=TRACE_LOG):
    """Parse the trace log with rdflib; return list of dicts."""
    try:
        import rdflib
    except ImportError:
        sys.exit("ERROR: rdflib required for harvest_traces.py")
    if not os.path.exists(path):
        return []
    g = rdflib.Graph()
    g.parse(path, format="turtle")
    traces = []
    for s in g.subjects(rdflib.RDF.type, rdflib.URIRef(LLMR + "RoutingTrace")):
        task = g.value(s, rdflib.URIRef(LLMR + "tracedTask"))
        model = g.value(s, rdflib.URIRef(LLMR + "tracedModel"))
        score = g.value(s, rdflib.URIRef(LLMR + "qualityScore"))
        if task is None or model is None or score is None:
            continue
        traces.append({
            "task": str(task).split("/")[-1],
            "model": str(model).split("/")[-1],
            "score": int(score),
            "tier": str(g.value(s, rdflib.URIRef(LLMR + "costTierUsed")) or "medium"),
            "policy": str(g.value(s, rdflib.URIRef(LLMR + "policyUsed")) or "balanced"),
            "cost": g.value(s, rdflib.URIRef(LLMR + "costIncurred")),
            "latency": str(g.value(s, rdflib.URIRef(LLMR + "observedLatency")) or ""),
            "date": str(g.value(s, rdflib.URIRef(LLMR + "feedbackDate")) or ""),
        })
    return traces


def implied_score(model_cap, task_dims):
    """The seed profile's implied capability score for this task (0-5)."""
    if not task_dims:
        return 0.0
    vals = [model_cap.get(d, 0) for d in task_dims]
    return round(sum(vals) / len(vals), 2)


def harvest(traces, tasks, delta, min_samples):
    """Aggregate traces -> proposed overrides."""
    # aggregate observed avg score per (model, task)
    agg = {}
    for t in traces:
        key = (t["model"], t["task"])
        agg.setdefault(key, []).append(t["score"])
    task_dims = {t["id"]: t.get("dimensions", []) for t in tasks["task_types"]}

    proposals = {}  # model -> {dimension: new_value}
    rows = []
    for (model, task), scores in sorted(agg.items()):
        n = len(scores)
        avg = round(sum(scores) / n, 2)
        if n < min_samples:
            rows.append((model, task, n, avg, None, "insufficient samples"))
            continue
        # find the model's current seed capability (family rule or override)
        cap = _current_capability(model, tasks)
        if not cap:
            rows.append((model, task, n, avg, None, "no seed capability for model"))
            continue
        implied = implied_score(cap, task_dims.get(task, []))
        # map observed 1-5 quality to the same scale as implied 1-5 capability
        dev = round(avg - implied, 2)
        if abs(dev) >= delta:
            # refine the most relevant dimension: the task's first dominant dim
            dim = (task_dims.get(task) or ["reasoning"])[0]
            new_val = max(1, min(5, round(cap.get(dim, 3) + dev)))
            proposals.setdefault(model, {})[dim] = new_val
            rows.append((model, task, n, avg, implied,
                         f"propose {dim} {cap.get(dim,3)} -> {new_val}"))
        else:
            rows.append((model, task, n, avg, implied, "within delta"))
    return rows, proposals


def _current_capability(model, tasks):
    """Current effective capability for a model (explicit override wins).

    An explicit override may be PARTIAL (e.g. only {'code': 2}); it is merged
    over the matching family-rule base so missing dimensions keep their seed
    values — otherwise implied scores under-count (0 for every un-overridden
    dimension) and harvest proposes bogus refinements.
    """
    profiles = json.load(open(PROFILES))
    base = {}
    for rule in profiles.get("family_rules", []):
        if re.search(rule["pattern"], model):
            base = dict(rule.get("capability", {}))
            break
    override = profiles.get("explicit_overrides", {}).get(model, {})
    cap = dict(base)
    cap.update(override.get("capability", {}))
    return cap


def main():
    ap = argparse.ArgumentParser(description="Harvest routing traces into seed refinements")
    ap.add_argument("--apply", action="store_true", help="apply overrides + rebuild + GATE")
    ap.add_argument("--traces", default=TRACE_LOG)
    ap.add_argument("--delta", type=float, default=DEFAULT_DELTA)
    ap.add_argument("--min-samples", type=int, default=DEFAULT_MIN_SAMPLES)
    args = ap.parse_args()

    traces = load_traces(args.traces)
    if not traces:
        print(f"no traces found in {args.traces}")
        return 0
    tasks = json.load(open(TASKS))
    rows, proposals = harvest(traces, tasks, args.delta, args.min_samples)

    print(f"harvest: {len(traces)} traces, {len(rows)} (model, task) groups")
    print()
    print(f"{'model':28s} {'task':20s} {'n':>2} {'avg':>5} {'implied':>7}  note")
    print("-" * 90)
    for model, task, n, avg, implied, note in rows:
        print(f"{model:28s} {task:20s} {n:>2} {avg:>5} {str(implied):>7}  {note}")

    if proposals:
        print()
        print("proposed explicit_overrides:")
        print(json.dumps(proposals, indent=2))
    else:
        print()
        print("no refinements proposed (all within delta or insufficient samples)")

    if args.apply and proposals:
        print()
        print("== applying + rebuilding + GATE ==")
        profiles = json.load(open(PROFILES))
        overrides = profiles.setdefault("explicit_overrides", {})
        for model, dims in proposals.items():
            entry = overrides.setdefault(model, {})
            entry.setdefault("capability", {})
            for dim, val in dims.items():
                entry["capability"][dim] = val
            entry["note"] = (entry.get("note", "") +
                             f"; harvested from traces {args.traces} "
                             f"({date.today().isoformat()})").strip("; ")
        with open(PROFILES, "w") as fh:
            json.dump(profiles, fh, indent=2)
        print(f"wrote explicit_overrides to {PROFILES}")
        # rebuild with the same live-prices source the skill uses: the
        # fetch_prices cache if present, else the live feed (never the stale
        # local llm-prices checkout, which has fewer models)
        cache = os.path.join(HERE, ".cache", "current-v1.json")
        build_cmd = [sys.executable, os.path.join(HERE, "build_routing_graph.py")]
        if os.path.exists(cache):
            build_cmd += ["--prices", cache]
        r = subprocess.run(build_cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr[-800:], file=sys.stderr)
            return 2
        g = subprocess.run([sys.executable, os.path.join(HERE, "validate_graph.py")],
                           capture_output=True, text=True)
        print(g.stdout[-600:])
        if g.returncode != 0:
            return 2
        print("GATE PASSED after harvest-apply.")
    return 0


if __name__ == "__main__":
    try:
        from datetime import date  # noqa: F401 (used in apply branch)
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
