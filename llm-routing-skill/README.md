# llm-routing-skill

Intelligent LLM routing informed by a **living capability × cost × latency
graph**. Classify a task (or agent sub-step) → map to a required capability
level → apply a cost tier + policy → pick the model on the **cost–quality
Pareto frontier** → escalate only when needed.

Pricing is **dynamic**: the routing graph is rebuilt from live
[llm-prices.com](https://www.llm-prices.com/) feeds, so the Pareto frontier,
cost tiers, and escalation ladders track the market as models appear and prices
drop. Capability/latency values are curated **seeds** in
`references/capability-profiles.json`, refined over time via the feedback loop.

## Quick Start

```bash
# 1. Fetch latest prices + build the graph (145 models, 30 task types)
python3 scripts/fetch_prices.py
python3 scripts/build_routing_graph.py

# 2. Gate — must pass before routing
python3 scripts/validate_graph.py

# 3. Route a task
python3 scripts/route.py code-generation medium
python3 scripts/route.py logical-reasoning max --policy quality-first
python3 scripts/route.py summarization low --policy cost-first --latency medium --vendor google
```

## Example decision

```
$ python3 scripts/route.py code-generation medium
RECOMMENDED:     DeepSeek-V4-Flash
  vendor=deepseek  level=L3 (score 3.0)  $0.28/MTok out  latency=low
Escalation ladder: DeepSeek-V4-Flash ($0.28) → Codestral ($0.90) → Claude Opus 4.5 ($25)
```

## How it works

| Input | Source | Freshness |
|-------|--------|-----------|
| Prices (input/output/cached $/MTok) | live `llm-prices.com/current-v1.json` | market-driven; rebuilt on demand |
| Capability + latency seeds | `references/capability-profiles.json` | you, via feedback |
| Task taxonomy + required levels | `references/task-types.json` | you |
| Routing graph (TTL + JSON) | `scripts/build_routing_graph.py` | generated |

The graph (`references/routing-graph.ttl`) is queryable via SPARQL (see
SKILL.md §5 for templates); `scripts/route.py` is the dependency-free CLI
wrapper. Governance (approved models, residency, cost caps) stays with you —
see SKILL.md §6.

## Verification & Test Suite

Two verification demos exercise the skill end-to-end against either query
surface. Every query is a **hyperlinked SPARQL URL** (data-twingler format,
`format=text/x-html+tr`) — one click runs it. Both a local instance and the
public URIBurner deployment are covered; the same queries work on any other
SPARQL endpoint by swapping the host and the `GRAPH <...>` IRI.

### Setup assumptions

The links below assume the graph has been built and loaded into a SPARQL
endpoint. Two deployments are the documented exemplars:

| Surface | Endpoint | Graph IRI | Prerequisite |
|---|---|---|---|
| **Local Virtuoso** | `http://localhost:8890/sparql` | `urn:llmr:routing-graph` | Virtuoso running on `localhost:8890`; graph loaded via `scripts/load_graph.py` (or Graph Store `PUT` with the dba credential) |
| **Public URIBurner** (default public exemplar) | `https://linkeddata.uriburner.com/sparql` | `https://linkeddata.uriburner.com/DAV/demos/daas/llm-routing/routing-graph.ttl` | graph uploaded to the DAV path and auto-sponged into the quad store; ACL grants anonymous SPARQL read |

Both exemplars were live-verified (HTTP 200, expected rows) at the time of
writing. The local links only resolve on the machine running the local
instance; the URIBurner links resolve anywhere.

### Test 1 — End-to-end routing trace (`code-generation`)

Verifies task classification, Pareto-frontier computation, escalation-ladder
order, capability profiles, and ontology term definitions are all queryable and
correct.

| # | Step | Expected result | Run locally | Run on URIBurner |
|---|---|---|---|---|
| 1 | Task definition | `Code Generation`, req **L3**, dims `code, reasoning` | [run](http://localhost:8890/sparql?default-graph-uri=&query=PREFIX%20llmr%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%23%3E%20PREFIX%20llmrt%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%2Ftasks%2F%3E%20SELECT%20%3Flabel%20%3Freq%20%3Fdim%20WHERE%20%7B%20GRAPH%20%3Curn%3Allmr%3Arouting-graph%3E%20%7B%20llmrt%3Acode-generation%20rdfs%3Alabel%20%3Flabel%20%3B%20llmr%3ArequiredCapabilityLevel%20%3Freq%20%3B%20llmr%3AdominantDimension%20%3Fdim%20%7D%20%7D&format=text%2Fx-html%2Btr) | [run](https://linkeddata.uriburner.com/sparql?default-graph-uri=&query=PREFIX%20llmr%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%23%3E%20PREFIX%20llmrt%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%2Ftasks%2F%3E%20SELECT%20%3Flabel%20%3Freq%20%3Fdim%20WHERE%20%7B%20GRAPH%20%3Chttps%3A%2F%2Flinkeddata.uriburner.com%2FDAV%2Fdemos%2Fdaas%2Fllm-routing%2Frouting-graph.ttl%3E%20%7B%20llmrt%3Acode-generation%20rdfs%3Alabel%20%3Flabel%20%3B%20llmr%3ArequiredCapabilityLevel%20%3Freq%20%3B%20llmr%3AdominantDimension%20%3Fdim%20%7D%20%7D&format=text%2Fx-html%2Btr) |
| 2 | Pareto frontier (cheapest first) | **11 models**: ministral-3b ($0.04) → deepseek-v4-flash ($0.28, L3) → … → claude-opus-4-5/6/7/8 ($25) | [run](http://localhost:8890/sparql?default-graph-uri=&query=PREFIX%20llmr%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%23%3E%20PREFIX%20llmrt%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%2Ftasks%2F%3E%20SELECT%20%3Fmodel%20%3Fprice%20%3Flatency%20WHERE%20%7B%20GRAPH%20%3Curn%3Allmr%3Arouting-graph%3E%20%7B%20llmrt%3Acode-generation%20llmr%3AparetoFrontierModel%20%3Fmodel%20.%20%3Fmodel%20llmr%3AoutputPricePerMTok%20%3Fprice%20%3B%20llmr%3AlatencyClass%20%3Flatency%20%7D%20%7D%20ORDER%20BY%20%3Fprice&format=text%2Fx-html%2Btr) | [run](https://linkeddata.uriburner.com/sparql?default-graph-uri=&query=PREFIX%20llmr%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%23%3E%20PREFIX%20llmrt%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%2Ftasks%2F%3E%20SELECT%20%3Fmodel%20%3Fprice%20%3Flatency%20WHERE%20%7B%20GRAPH%20%3Chttps%3A%2F%2Flinkeddata.uriburner.com%2FDAV%2Fdemos%2Fdaas%2Fllm-routing%2Frouting-graph.ttl%3E%20%7B%20llmrt%3Acode-generation%20llmr%3AparetoFrontierModel%20%3Fmodel%20.%20%3Fmodel%20llmr%3AoutputPricePerMTok%20%3Fprice%20%3B%20llmr%3AlatencyClass%20%3Flatency%20%7D%20%7D%20ORDER%20BY%20%3Fprice&format=text%2Fx-html%2Btr) |
| 3 | Escalation ladder (ordered) | rung 1 `deepseek-v4-flash` → rung 2 `codestral-latest` → rung 3 `claude-opus-4-5` | [run](http://localhost:8890/sparql?default-graph-uri=&query=PREFIX%20llmrt%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%2Ftasks%2F%3E%20PREFIX%20schema%3A%20%3Chttp%3A%2F%2Fschema.org%2F%3E%20SELECT%20%3Fpos%20%3Fmodel%20WHERE%20%7B%20GRAPH%20%3Curn%3Allmr%3Arouting-graph%3E%20%7B%20llmrt%3Acode-generation%20schema%3AitemListElement%20%3Fli%20.%20%3Fli%20schema%3Aposition%20%3Fpos%20%3B%20schema%3Aitem%20%3Fmodel%20%7D%20%7D%20ORDER%20BY%20%3Fpos&format=text%2Fx-html%2Btr) | [run](https://linkeddata.uriburner.com/sparql?default-graph-uri=&query=PREFIX%20llmrt%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%2Ftasks%2F%3E%20PREFIX%20schema%3A%20%3Chttp%3A%2F%2Fschema.org%2F%3E%20SELECT%20%3Fpos%20%3Fmodel%20WHERE%20%7B%20GRAPH%20%3Chttps%3A%2F%2Flinkeddata.uriburner.com%2FDAV%2Fdemos%2Fdaas%2Fllm-routing%2Frouting-graph.ttl%3E%20%7B%20llmrt%3Acode-generation%20schema%3AitemListElement%20%3Fli%20.%20%3Fli%20schema%3Aposition%20%3Fpos%20%3B%20schema%3Aitem%20%3Fmodel%20%7D%20%7D%20ORDER%20BY%20%3Fpos&format=text%2Fx-html%2Btr) |
| 4 | Capability profile | deepseek-v4-flash: `code=3, reasoning=3, math=3, tools=3, knowledge=3, long_context=3, creative=2, vision=2` | [run](http://localhost:8890/sparql?default-graph-uri=&query=PREFIX%20llmr%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%23%3E%20PREFIX%20llmrm%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%2Fmodels%2F%3E%20PREFIX%20schema%3A%20%3Chttp%3A%2F%2Fschema.org%2F%3E%20SELECT%20%3Fdim%20%3Fval%20WHERE%20%7B%20GRAPH%20%3Curn%3Allmr%3Arouting-graph%3E%20%7B%20llmrm%3Adeepseek-v4-flash%20schema%3AadditionalProperty%20%3Fpv%20.%20%3Fpv%20schema%3Aname%20%3Fdim%20%3B%20schema%3Avalue%20%3Fval%20%7D%20%7D%20ORDER%20BY%20%3Fdim&format=text%2Fx-html%2Btr) | [run](https://linkeddata.uriburner.com/sparql?default-graph-uri=&query=PREFIX%20llmr%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%23%3E%20PREFIX%20llmrm%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%2Fmodels%2F%3E%20PREFIX%20schema%3A%20%3Chttp%3A%2F%2Fschema.org%2F%3E%20SELECT%20%3Fdim%20%3Fval%20WHERE%20%7B%20GRAPH%20%3Chttps%3A%2F%2Flinkeddata.uriburner.com%2FDAV%2Fdemos%2Fdaas%2Fllm-routing%2Frouting-graph.ttl%3E%20%7B%20llmrm%3Adeepseek-v4-flash%20schema%3AadditionalProperty%20%3Fpv%20.%20%3Fpv%20schema%3Aname%20%3Fdim%20%3B%20schema%3Avalue%20%3Fval%20%7D%20%7D%20ORDER%20BY%20%3Fdim&format=text%2Fx-html%2Btr) |
| 5 | Ontology TBox | **31 `llmr:` properties** declared (`rdf:Property`) | [run](http://localhost:8890/sparql?default-graph-uri=&query=PREFIX%20llmr%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%23%3E%20PREFIX%20rdf%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23%3E%20SELECT%20%3Fterm%20WHERE%20%7B%20GRAPH%20%3Curn%3Allmr%3Arouting-graph%3E%20%7B%20%3Fterm%20a%20rdf%3AProperty%20.%20FILTER%28STRSTARTS%28STR%28%3Fterm%29%2C%20STR%28llmr%3A%29%29%29%20%7D%20%7D%20ORDER%20BY%20%3Fterm&format=text%2Fx-html%2Btr) | [run](https://linkeddata.uriburner.com/sparql?default-graph-uri=&query=PREFIX%20llmr%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%23%3E%20PREFIX%20rdf%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23%3E%20SELECT%20%3Fterm%20WHERE%20%7B%20GRAPH%20%3Chttps%3A%2F%2Flinkeddata.uriburner.com%2FDAV%2Fdemos%2Fdaas%2Fllm-routing%2Frouting-graph.ttl%3E%20%7B%20%3Fterm%20a%20rdf%3AProperty%20.%20FILTER%28STRSTARTS%28STR%28%3Fterm%29%2C%20STR%28llmr%3A%29%29%29%20%7D%20%7D%20ORDER%20BY%20%3Fterm&format=text%2Fx-html%2Btr) |

Dominance check (computed from the graph, both surfaces): 11 of 145 models are
undominated; deepseek-v4-flash eliminates 52, codestral 53, gpt-5.6-luna 70,
gpt-5.1-codex-mini 71.

CLI parity: `python3 scripts/route.py code-generation medium` → `DeepSeek-V4-Flash`
($0.28, L3) on every surface.

### Test 2 — Feedback-loop refinement

Verifies the living-graph cycle: record feedback → refine seed profile →
rebuild → the frontier and recommendation change while the GATE stays green.

| # | Step | Expected result | Run locally | Run on URIBurner |
|---|---|---|---|---|
| 1 | Feedback records queryable | shipped `feedback-0001`: deepseek-v4-flash on code-generation, score 4 | [run](http://localhost:8890/sparql?default-graph-uri=&query=PREFIX%20llmr%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%23%3E%20PREFIX%20llmrt%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%2Ftasks%2F%3E%20SELECT%20%3Fr%20%3Fmodel%20%3Ftask%20%3Fscore%20WHERE%20%7B%20GRAPH%20%3Curn%3Allmr%3Afeedback-log%3E%20%7B%20%3Fr%20a%20llmr%3AFeedbackRecord%20%3B%20llmr%3AfeedbackModel%20%3Fmodel%20%3B%20llmr%3AfeedbackTask%20%3Ftask%20%3B%20llmr%3AqualityScore%20%3Fscore%20%7D%20%7D&format=text%2Fx-html%2Btr) | [run](https://linkeddata.uriburner.com/sparql?default-graph-uri=&query=PREFIX%20llmr%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%23%3E%20SELECT%20%3Fr%20%3Fmodel%20%3Ftask%20%3Fscore%20WHERE%20%7B%20GRAPH%20%3Chttps%3A%2F%2Flinkeddata.uriburner.com%2FDAV%2Fdemos%2Fdaas%2Fllm-routing%2Ffeedback-log.ttl%3E%20%7B%20%3Fr%20a%20llmr%3AFeedbackRecord%20%3B%20llmr%3AfeedbackModel%20%3Fmodel%20%3B%20llmr%3AfeedbackTask%20%3Ftask%20%3B%20llmr%3AqualityScore%20%3Fscore%20%7D%20%7D&format=text%2Fx-html%2Btr) |
| 2 | Frontier BEFORE refinement | deepseek-v4-flash present at $0.28 (11 models) | [run](http://localhost:8890/sparql?default-graph-uri=&query=PREFIX%20llmr%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%23%3E%20PREFIX%20llmrt%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%2Ftasks%2F%3E%20SELECT%20%3Fmodel%20%3Fprice%20WHERE%20%7B%20GRAPH%20%3Curn%3Allmr%3Arouting-graph%3E%20%7B%20llmrt%3Acode-generation%20llmr%3AparetoFrontierModel%20%3Fmodel%20.%20%3Fmodel%20llmr%3AoutputPricePerMTok%20%3Fprice%20%7D%20%7D%20ORDER%20BY%20%3Fprice&format=text%2Fx-html%2Btr) | [run](https://linkeddata.uriburner.com/sparql?default-graph-uri=&query=PREFIX%20llmr%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%23%3E%20PREFIX%20llmrt%3A%20%3Chttps%3A%2F%2Fwww.openlinksw.com%2Fontology%2Fllm-routing%2Ftasks%2F%3E%20SELECT%20%3Fmodel%20%3Fprice%20WHERE%20%7B%20GRAPH%20%3Chttps%3A%2F%2Flinkeddata.uriburner.com%2FDAV%2Fdemos%2Fdaas%2Fllm-routing%2Frouting-graph.ttl%3E%20%7B%20llmrt%3Acode-generation%20llmr%3AparetoFrontierModel%20%3Fmodel%20.%20%3Fmodel%20llmr%3AoutputPricePerMTok%20%3Fprice%20%7D%20%7D%20ORDER%20BY%20%3Fprice&format=text%2Fx-html%2Btr) |
| 3 | Refine seed (temp copy) | 3× qualityScore 2 → `explicit_overrides` code 3→1 → rebuild → **GATE PASSED 0 failures** (blank nodes 0/0, ontology terms 31/31) | — | — |
| 4 | Decision change | recommended: **DeepSeek-V4-Flash → Gemini 1.5 Flash** ($0.30); frontier −deepseek-v4-flash +gemini-1.5-flash | — | — |

### Gate (all surfaces)

```bash
python3 scripts/validate_graph.py   # GATE PASSED: 0 failures required
```

## Feedback loop

After each routed execution, append a record to
`references/feedback-log.ttl` (SKILL.md §7), adjust seed profiles when reality
disagrees, rebuild, re-validate. The graph is a living artifact — stale
profiles are the only thing that can rot it.

## Documentation

- Full contract: [`SKILL.md`](SKILL.md)
- Worked example: [`examples/routing-example.md`](examples/routing-example.md)
