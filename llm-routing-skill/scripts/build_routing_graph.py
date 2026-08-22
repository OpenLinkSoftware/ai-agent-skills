#!/usr/bin/env python3
"""build_routing_graph.py — Compile the LLM routing graph.

Merges three inputs into the capability x cost x latency routing graph:

  1. PRICES   — live llm-prices.com feeds (or local llm-prices checkout)  [cost]
  2. PROFILES — references/capability-profiles.json  [capability + latency seeds]
  3. TASKS    — references/task-types.json  [task taxonomy + required levels]

Outputs (both written to references/):
  routing-graph.ttl  — RDF-Turtle graph (queryable via SPARQL/rdflib)
  routing-graph.json — JSON mirror for programmatic routing (scripts/route.py)

The graph is deliberately a LIVING artifact: re-run this script whenever prices
change or profiles are refined via the feedback loop. See SKILL.md 'Build &
Refresh' and 'Feedback Loop'.

Usage:
  python3 scripts/build_routing_graph.py                 # live fetch (or .cache)
  python3 scripts/build_routing_graph.py --prices /tmp/current-v1.json
  python3 scripts/build_routing_graph.py --offline       # local llm-prices checkout only
  python3 scripts/build_routing_graph.py --out-dir /tmp  # custom output

Exit codes: 0 ok; 1 missing inputs; 2 build error.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
REFS = os.path.join(SKILL, "references")

# ── Ontology namespaces (documented pattern, see SKILL.md 'Ontology') ────────
NS = {
    "llmr": "https://www.openlinksw.com/ontology/llm-routing#",
    "llmrm": "https://www.openlinksw.com/ontology/llm-routing/models/",
    "llmrt": "https://www.openlinksw.com/ontology/llm-routing/tasks/",
    "llmrv": "https://www.openlinksw.com/ontology/llm-routing/vendors/",
    "llmrl": "https://www.openlinksw.com/ontology/llm-routing/levels/",
    "schema": "http://schema.org/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "prov": "http://www.w3.org/ns/prov#",
    "intel": "https://linkeddata.uriburner.com/DAV/demos/daas/ontology/intelligence-allocation#",
    "dbr": "http://dbpedia.org/resource/",
}

LLM_PRICING_REPO = os.path.expanduser(
    "~/Documents/Management/Development/llm-prices/data"
)
CURRENT_URL = "https://www.llm-prices.com/current-v1.json"

LEVELS = ["L1", "L2", "L3", "L4", "L5"]
LATENCY_RANK = {"very-low": 1, "low": 2, "medium": 3, "high": 4, "very-high": 5}


def load_prices(prices_path=None, offline=False):
    """Return {'updated_at': str, 'prices': [ {...} ]} from live feed or local data."""
    if prices_path and os.path.exists(prices_path):
        with open(prices_path) as fh:
            return json.load(fh)

    if offline:
        return load_prices_from_repo()

    # try cached fetch first, then live
    cache = os.path.join(HERE, ".cache", "current-v1.json")
    if os.path.exists(cache):
        with open(cache) as fh:
            return json.load(fh)

    import urllib.request
    try:
        with urllib.request.urlopen(CURRENT_URL, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        with open(cache, "w") as fh:
            json.dump(data, fh, indent=2)
        print(f"Fetched live prices from {CURRENT_URL}")
        return data
    except Exception as exc:
        print(f"WARN: live fetch failed ({exc}); falling back to local llm-prices checkout",
              file=sys.stderr)
        return load_prices_from_repo()


def load_prices_from_repo():
    """Merge data/*.json vendor files from the local llm-prices git checkout."""
    if not os.path.isdir(LLM_PRICING_REPO):
        raise SystemExit(
            f"ERROR: local llm-prices checkout not found at {LLM_PRICING_REPO} "
            "(use --prices, --offline with repo present, or network access)"
        )
    prices = []
    for fn in sorted(os.listdir(LLM_PRICING_REPO)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(LLM_PRICING_REPO, fn)) as fh:
            vendor = json.load(fh)
        for model in vendor.get("models", []):
            # current price = entry with to_date null (last one usually)
            hist = model.get("price_history", [])
            cur = next((h for h in reversed(hist) if h.get("to_date") is None), hist[-1] if hist else {})
            prices.append({
                "id": model["id"],
                "vendor": vendor.get("vendor", fn[:-5]),
                "name": model.get("name", model["id"]),
                "input": cur.get("input"),
                "output": cur.get("output"),
                "input_cached": cur.get("input_cached"),
            })
    print(f"Loaded {len(prices)} models from local llm-prices checkout")
    return {"updated_at": datetime.now(timezone.utc).date().isoformat(), "prices": prices}


def load_json(relpath):
    path = os.path.join(REFS, relpath)
    if not os.path.exists(path):
        raise SystemExit(f"ERROR: missing input {path}")
    with open(path) as fh:
        return json.load(fh)


def capability_for(model_id, vendor, profiles):
    """First matching family rule (regex) wins; then explicit overrides."""
    for rule in profiles.get("family_rules", []):
        if rule.get("vendor") and rule["vendor"] != vendor:
            continue
        if re.search(rule["pattern"], model_id):
            cap = dict(rule.get("capability", {}))
            override = profiles.get("explicit_overrides", {}).get(model_id, {})
            cap.update(override.get("capability", {}))
            return {
                "capability": cap,
                "latency_class": override.get("latency_class", rule.get("latency_class", "medium")),
                "context_window": override.get("context_window", rule.get("context_window", 128000)),
                "note": rule.get("note", ""),
            }
    # no rule matched
    return {
        "capability": {},
        "latency_class": "medium",
        "context_window": 128000,
        "note": "UNMATCHED family rule — capability seeds missing, treat as unknown",
    }


def cost_tier(output_price, thresholds):
    if output_price is None:
        return "unknown"
    for tier, spec in thresholds.items():
        if not isinstance(spec, dict):
            continue  # skip meta keys like "basis"
        mx = spec.get("max_output_price")
        if mx is None:
            continue
        if output_price <= mx:
            return tier
    return "max"


def task_score(model_cap, task):
    """Weighted average of the task's dominant dimensions -> 1..5."""
    dims = task.get("dimensions", [])
    if not dims:
        return 0.0
    vals = [model_cap.get(d, 0) for d in dims]
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


def dominates(a, b):
    """a dominates b if a is >= on every axis and strictly better on at least one.
    Axes: task score, output price, latency rank."""
    sa, pa, la = a["score"], a["price"], a["latency"]
    sb, pb, lb = b["score"], b["price"], b["latency"]
    if pa is None or pb is None:
        return False
    ge = sa >= sb and pa <= pb and la <= lb
    strict = sa > sb or pa < pb or la < lb
    return ge and strict


def build(profiles, tasks, prices, updated_at):
    cost_spec = profiles["cost_tier_thresholds"]
    latency_spec = profiles["latency_classes"]

    models = []
    for rec in prices:
        pid = rec["id"]
        vendor = rec.get("vendor", "unknown")
        profile = capability_for(pid, vendor, profiles)
        output_p = rec.get("output")
        models.append({
            "id": pid,
            "vendor": vendor,
            "name": rec.get("name", pid),
            "input": rec.get("input"),
            "output": output_p,
            "input_cached": rec.get("input_cached"),
            "capability": profile["capability"],
            "latency_class": profile["latency_class"],
            "latency_rank": LATENCY_RANK.get(profile["latency_class"], 3),
            "context_window": profile["context_window"],
            "cost_tier": cost_tier(output_p, cost_spec),
            "note": profile.get("note", ""),
        })

    # per-task-type scoring + Pareto frontier
    for task in tasks["task_types"]:
        tid = task["id"]
        scored = []
        for m in models:
            if task.get("special") == "embedding-only" and "embedding" not in m["id"]:
                continue
            s = task_score(m["capability"], task)
            scored.append({
                "model": m["id"],
                "score": s,
                "level": level_for(s),
                "price": m["output"],
                "latency": m["latency_rank"],
            })
        # Pareto frontier: keep non-dominated models
        frontier = [x for x in scored if not any(dominates(y, x) for y in scored if y["model"] != x["model"])]
        task["_scored"] = scored
        task["_frontier"] = frontier
        task["_required_level"] = task.get("required_level", "L3")

    return {"models": models, "tasks": tasks, "profiles": profiles,
            "cost_spec": cost_spec, "latency_spec": latency_spec,
            "updated_at": updated_at}


def esc(text):
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def emit_turtle(graph):
    L = []
    A = L.append
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for pfx, uri in NS.items():
        A(f"@prefix {pfx}: <{uri}> .")
    A("")
    A(f"# LLM Routing Graph — generated {ts} from llm-prices (updated {graph['updated_at']})")
    A("# Capability/latency values are curated SEEDS (capability-profiles.json);")
    A("# cost values are live from llm-prices.com. Rebuild to refresh.")
    A("# Ontology TBox (llmr:) embedded verbatim from references/llm-routing-ontology.ttl.")
    A("")

    # ontology TBox — embedded verbatim from the canonical ontology file
    tbox_path = os.path.join(REFS, "llm-routing-ontology.ttl")
    if os.path.exists(tbox_path):
        with open(tbox_path) as fh:
            tbox = fh.read()
        # strip the file's own @prefix block (graph already declares all prefixes)
        lines = [ln for ln in tbox.splitlines()
                 if not ln.startswith("@prefix") and not ln.startswith("# ═")]
        A("\n".join(lines).strip())
        A("")
        A(f'llmr: schema:dateModified "{ts}"^^xsd:dateTime .')
        A("")

    # capability levels
    for lvl, desc in graph["profiles"]["scale"].items():
        A(f'llmrl:L{lvl} a llmr:CapabilityLevel ;')
        A(f'    rdfs:label "Capability Level {lvl}"@en ;')
        A(f'    rdfs:comment "{esc(desc)}"@en .')
        A("")

    # vendors
    vendors = sorted({m["vendor"] for m in graph["models"]})
    for v in vendors:
        A(f'llmrv:{v.replace("-", "_")} a schema:Organization ;')
        A(f'    schema:name "{esc(v)}"@en .')
        A("")

    # task types
    for task in graph["tasks"]["task_types"]:
        tid = task["id"]
        A(f'llmrt:{tid} a llmr:TaskType ;')
        A(f'    rdfs:label "{esc(task["label"])}"@en ;')
        A(f'    rdfs:comment "{esc(task["description"])}"@en ;')
        A(f'    llmr:requiredCapabilityLevel llmrl:{task["_required_level"]} ;')
        A(f'    llmr:tokenSensitivity "{task.get("token_sensitivity", "medium")}"@en ;')
        A(f'    llmr:overqualificationRisk "{task.get("overqualification_risk", "medium")}"@en .')
        # dominant dimensions as a SET of triples (no RDF list)
        for d in task.get("dimensions", []):
            A(f'llmrt:{tid} llmr:dominantDimension "{esc(d)}"@en .')
        A("")

    # models
    for m in graph["models"]:
        mid = re.sub(r"[^A-Za-z0-9_.-]", "_", m["id"])
        A(f'llmrm:{mid} a llmr:Model, schema:SoftwareApplication ;')
        A(f'    schema:name "{esc(m["name"])}"@en ;')
        A(f'    llmr:modelId "{esc(m["id"])}"@en ;')
        A(f'    llmr:vendor llmrv:{m["vendor"].replace("-", "_")} ;')
        if m["input"] is not None:
            A(f'    llmr:inputPricePerMTok "{m["input"]}"^^xsd:decimal ;')
        if m["output"] is not None:
            A(f'    llmr:outputPricePerMTok "{m["output"]}"^^xsd:decimal ;')
        if m["input_cached"] is not None:
            A(f'    llmr:cachedInputPricePerMTok "{m["input_cached"]}"^^xsd:decimal ;')
        A(f'    llmr:costTier "{m["cost_tier"]}"@en ;')
        A(f'    llmr:latencyClass "{m["latency_class"]}"@en ;')
        A(f'    llmr:contextWindowTokens "{m["context_window"]}"^^xsd:integer ;')
        A(f'    llmr:priceUpdated "{graph["updated_at"]}"^^xsd:date ;')
        if m["note"]:
            A(f'    llmr:profileNote "{esc(m["note"])}"@en ;')
        A('    schema:url <https://www.llm-prices.com/> .')
        # capability vector as schema:PropertyValue via schema:additionalProperty
        # (SET of named-hash-IRI reification nodes — NO blank nodes per Step 37;
        # full <IRI> syntax because '#' is not legal in a prefixed-name local part)
        for dim in graph["profiles"]["dimensions"]:
            val = m["capability"].get(dim)
            if val is not None:
                pv = f"<{NS['llmrm']}{m['id']}#capability-{dim}>"
                A(f'llmrm:{mid} schema:additionalProperty {pv} .')
                A(f'{pv} a schema:PropertyValue ;')
                A(f'    schema:name "{esc(dim)}"@en ;')
                A(f'    schema:value "{val}"^^xsd:integer .')
        A("")

    # Pareto frontier (SET of triples — no truncation) + escalation ladders per task
    for task in graph["tasks"]["task_types"]:
        tid = task["id"]
        frontier_ids = [f["model"] for f in task["_frontier"]]
        if frontier_ids:
            for i in frontier_ids:
                A(f'llmrt:{tid} llmr:paretoFrontierModel llmrm:{re.sub(r"[^A-Za-z0-9_.-]", "_", i)} .')
            A("")
        # escalation ladder: cheapest adequate -> cheapest next-level -> best
        req = task["_required_level"]
        req_idx = LEVELS.index(req)
        scored = task["_scored"]
        def cheapest_at_level(lvl):
            cands = [s for s in scored if s["level"] == lvl and s["price"] is not None]
            if not cands:
                return None
            return min(cands, key=lambda s: s["price"])
        rung1 = cheapest_at_level(req)
        rung2 = None
        for lvl in LEVELS[req_idx + 1:]:
            rung2 = cheapest_at_level(lvl)
            if rung2:
                break
        if scored:
            top = max(scored, key=lambda s: (s["score"], -(s["price"] or 0)))
        else:
            top = None
        ladder = [r for r in (rung1, rung2, top) if r]
        seen = set()
        uniq = []
        for r in ladder:
            if r["model"] not in seen:
                seen.add(r["model"])
                uniq.append(r)
        # ordered ladder as schema:ItemList with NAMED ListItem nodes
        # (hash-IRIs on the task — NO blank nodes per Step 37; full <IRI>
        # syntax because '#' is not legal in a prefixed-name local part)
        for pos, r in enumerate(uniq, start=1):
            li = f"<{NS['llmrt']}{tid}#rung-{pos}>"
            A(f'llmrt:{tid} schema:itemListElement {li} .')
            A(f'{li} a schema:ListItem ;')
            A(f'    schema:position "{pos}"^^xsd:integer ;')
            A(f'    schema:item llmrm:{re.sub(r"[^A-Za-z0-9_.-]", "_", r["model"])} .')
        A("")

    # provenance + governance knobs
    A("llmr:routingGraph a schema:Dataset ;")
    A('    schema:name "LLM Routing Graph"@en ;')
    A(f'    schema:dateModified "{ts}"^^xsd:dateTime ;')
    A(f'    llmr:graphPriceUpdated "{graph["updated_at"]}"^^xsd:date ;')
    A('    schema:isBasedOn <https://www.llm-prices.com/current-v1.json> ;')
    A('    prov:wasGeneratedBy <https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/llm-routing-skill#this> .')
    A("")
    A("llmr:governance a llmr:GovernancePolicy ;")
    A('    rdfs:label "Routing governance knobs (editable)"@en ;')
    A('    rdfs:comment "Approved models, blocked models, and residency constraints live in capability-profiles.json governance block and are projected here by the builder."@en ;')
    gov = graph["profiles"].get("governance", {})
    for am in gov.get("approved_models", []):
        A(f'    llmr:approvesModel "{esc(am)}"@en ;')
    for bm in gov.get("blocked_models", []):
        A(f'    llmr:blocksModel "{esc(bm)}"@en ;')
    for region, models in gov.get("residency_constraints", {}).items():
        A(f'    llmr:residencyConstraint "{esc(region)}"@en ;')
    A("    a llmr:GovernancePolicy .")
    return "\n".join(L) + "\n"


def emit_json(graph):
    out = {
        "schema": "llm-routing-graph-v2",
        "updated_at": graph["updated_at"],
        "capability_levels": graph["profiles"]["scale"],
        "cost_tier_thresholds": graph["cost_spec"],
        "latency_classes": graph["latency_spec"],
        "tasks": [
            {
                "id": t["id"],
                "label": t["label"],
                "required_level": t["_required_level"],
                "dimensions": t.get("dimensions", []),
                "pareto_frontier": [f["model"] for f in t["_frontier"]],
                "escalation_ladder": _ladder_ids(t),
            }
            for t in graph["tasks"]["task_types"]
        ],
        "models": [
            {
                "id": m["id"],
                "vendor": m["vendor"],
                "name": m["name"],
                "prices": {
                    "input_per_mtok": m["input"],
                    "output_per_mtok": m["output"],
                    "cached_input_per_mtok": m["input_cached"],
                },
                "cost_tier": m["cost_tier"],
                "latency_class": m["latency_class"],
                "context_window_tokens": m["context_window"],
                "capability": m["capability"],
            }
            for m in graph["models"]
        ],
    }
    return out


def _ladder_ids(task):
    req = task["_required_level"]
    req_idx = LEVELS.index(req)
    scored = task["_scored"]
    def cheapest_at_level(lvl):
        cands = [s for s in scored if s["level"] == lvl and s["price"] is not None]
        return min(cands, key=lambda s: s["price"])["model"] if cands else None
    rung1 = cheapest_at_level(req)
    rung2 = None
    for lvl in LEVELS[req_idx + 1:]:
        rung2 = cheapest_at_level(lvl)
        if rung2:
            break
    if scored:
        top = max(scored, key=lambda s: (s["score"], -(s["price"] or 0)))["model"]
    else:
        top = None
    out, seen = [], set()
    for r in (rung1, rung2, top):
        if r and r not in seen:
            seen.add(r)
            out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser(description="Build the LLM routing graph")
    ap.add_argument("--prices", help="path to current-v1.json (or any {id,vendor,input,output} list)")
    ap.add_argument("--offline", action="store_true", help="use local llm-prices checkout only")
    ap.add_argument("--out-dir", default=REFS, help="output directory (default: references/)")
    args = ap.parse_args()

    profiles = load_json("capability-profiles.json")
    tasks = load_json("task-types.json")
    prices_data = load_prices(args.prices, args.offline)

    graph = build(profiles, tasks, prices_data["prices"], prices_data.get("updated_at", "unknown"))
    os.makedirs(args.out_dir, exist_ok=True)

    ttl = emit_turtle(graph)
    ttl_path = os.path.join(args.out_dir, "routing-graph.ttl")
    with open(ttl_path, "w") as fh:
        fh.write(ttl)

    js = emit_json(graph)
    js_path = os.path.join(args.out_dir, "routing-graph.json")
    with open(js_path, "w") as fh:
        json.dump(js, fh, indent=2)

    nm = len(graph["models"])
    print(f"Wrote {ttl_path}  ({nm} models, {len(tasks['task_types'])} task types)")
    print(f"Wrote {js_path}")
    print("Run scripts/validate_graph.py to verify.")

    # surface models with no family rule — capability seeds missing
    unmatched = [m["id"] for m in graph["models"] if not m["capability"]]
    if unmatched:
        print(f"WARN: {len(unmatched)} models have NO capability seed (add family rules):")
        for u in unmatched[:20]:
            print(f"  - {u}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
