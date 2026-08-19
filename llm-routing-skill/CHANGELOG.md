# Changelog

All notable changes to this skill are documented here. Format: [Keep a
Changelog](https://keepachangelog.com/en/1.1.0/); versioning:
[SemVer](https://semver.org/).

## [1.4.0] - 2026-08-19

### Changed
- README Verification & Test Suite regenerated for the extended TBox: Test 1
  row 5 updated to **31 `llmr:` properties** (was 25; the trace feature added
  6 properties). All 14 hyperlinks (7 queries x local Virtuoso + public
  URIBurner) re-verified HTTP 200 with expected row counts after re-syncing
  both graph surfaces.

### Added
- **Session routing traces (private, local-only)** — the automatic half of the
  feedback loop, in line with agent-rdf-memory/preferences.ttl session-trace
  guidelines (Step 36 secret redaction, Step 25 intent-to-outcome via
  prov:wasInformedBy, Step 38 OPAL session linkage).
  - `llmr:RoutingTrace` class (rdfs:subClassOf llmr:FeedbackRecord) + 6 trace
    properties (`tracedTask`, `tracedModel`, `costTierUsed`, `policyUsed`,
    `costIncurred`, `escalationEvent`) added to the TBox (ontology-gate
    compliant: label/comment/domain/range/isDefinedBy; 6 classes, 31
    properties total).
  - `scripts/record_trace.py` — outcome-level trace emitter: task, tier,
    policy, model, score, latency, cost, escalation, session link. NEVER
    records prompts/messages/secrets. Writes to `references/traces/trace-log.ttl`
    (private; excluded from the published graph and any public upload).
  - `scripts/harvest_traces.py` — aggregates observed quality per (model, task),
    compares against the seed-implied capability score, proposes
    `explicit_overrides` deltas; `--apply` writes them, rebuilds the graph
    (live-prices cache), and runs the GATE. Fixed partial-override merge bug
    (override is merged over family-rule base so implied scores don't
    under-count).
- SKILL.md §7 split into 7a (session traces — automatic, preferred) and 7b
  (manual feedback records).

### Notes
- Traces are PRIVATE: demoed against the local Virtuoso instance only
  (`urn:llmr:traces`), never uploaded to URIBurner, never in the README test
  suite.

## [1.3.0] - 2026-08-19

### Added
- **Verification & Test Suite section in README.md**: Test 1 (end-to-end
  routing trace on `code-generation`) and Test 2 (feedback-loop refinement),
  each with **hyperlinked SPARQL URLs on BOTH surfaces** — local Virtuoso
  (`http://localhost:8890/sparql`, graph `urn:llmr:routing-graph`) and public
  URIBurner (`https://linkeddata.uriburner.com/sparql`, graph
  `.../DAV/demos/daas/llm-routing/routing-graph.ttl`, auto-sponged on upload).
  Data-twingler URL format (`format=text/x-html+tr`); **Setup assumptions**
  block makes the installation prerequisites explicit for each surface
  (local: Virtuoso on :8890 + graph loaded; UB: DAV upload + auto-sponge +
  anonymous SPARQL read ACL). All 14 links verified HTTP 200 at time of
  writing; local links resolve only on the hosting machine, UB links anywhere.

## [1.2.0] - 2026-08-19

### Added
- **Authoritative llmr: TBox** (`references/llm-routing-ontology.ttl`): every
  class and property now carries rdfs:label, rdfs:comment, rdfs:domain/range,
  rdfs:isDefinedBy, and verified external cross-references per the
  ontology-cross-reference gate (preferences.ttl). 31 used terms declared;
  the validator fails on any used-but-undeclared `llmr:` term. Embedded
  verbatim into the generated graph at build time.
- **Blank-node elimination** (preferences.ttl Step 37): `schema:ListItem` and
  `schema:PropertyValue` reification nodes are now named hash IRIs
  (`<.../tasks/{task}#rung-{n}>`, `<.../models/{id}#capability-{dim}>`) —
  1,246 blank-node objects reduced to 0. `priceUpdated` split into
  `llmr:priceUpdated` (Model) and `llmr:graphPriceUpdated` (Dataset) to avoid
  a blank-node owl:unionOf domain.
- **Validator gates**: blank-node check (0 subjects, 0 objects required) and
  ontology term-coverage check added to `validate_graph.py`.

### Changed
- Triple count 7,394 → 7,547 (TBox embedded + named reification nodes).
- SKILL.md encoding note documents the no-blank-node + TBox contract.

## [1.1.0] - 2026-08-19

### Changed
- **RDF-list encoding migrated to schema.org terms + set triples.** The graph
  previously serialized Pareto frontiers, escalation ladders, and capability
  profiles as RDF collections, which forced `rdf:rest*/rdf:first` traversal in
  every SPARQL query (three documented templates returned 0 rows until
  patched) and silently truncated frontiers at 12 members (data-analysis lost
  4 of 16 frontier models).
  - `paretoFrontier` (list) → `llmr:paretoFrontierModel` **repeated triples**
    (set semantics, no truncation).
  - `escalationLadder` (list) → **`schema:ItemList`/`schema:ListItem`/
    `schema:position`/`schema:item`** (schema.org's native ordered collection).
  - `capabilityProfile` (list of blank nodes with `llmr:dimension`/`llmr:score`)
    → **`schema:additionalProperty` + `schema:PropertyValue`** with
    `schema:name`/`schema:value`.
  - `dominantDimensions` (list) → `llmr:dominantDimension` repeated triples.
- Graph schema version bumped to `llm-routing-graph-v2` (JSON mirror);
  SPARQL templates T1/T2/T3/T5 rewritten for the new encoding and re-verified
  against the shipped graph; validator extended with legacy-form detection
  (fails if any RDF-list form reappears).
- Triple count 7,790 → 7,394 (reified ladder/PropertyValue nodes replaced
  list chains and blank-node profiles).

### Fixed
- Frontier truncation: full frontier now emitted for all 30 task types
  (previously capped at 12 members in the TTL).

## [1.0.0] - 2026-08-19

### Added
- Initial release of the LLM Routing Skill.
- **Living routing graph**: `references/routing-graph.ttl` (7,790 triples,
  rdflib-validated) + JSON mirror, generated by `scripts/build_routing_graph.py`
  from live llm-prices.com feeds.
- **Dynamic pricing pipeline**: `scripts/fetch_prices.py` pulls
  `current-v1.json` / `historical-v1.json` from llm-prices.com (verified live
  HTTP 200, feed `updated_at` 2026-08-13, 145 models / 11 vendors); offline
  fallback to the local `llm-prices` git checkout.
- **Task taxonomy**: 30 fine-grained task types with required capability levels
  (L1–L5), dominant dimensions, token sensitivity, overqualification risk
  (`references/task-types.json`).
- **Curated seed capability profiles**: 8-dimension capability vectors, latency
  classes, context windows, cost-tier thresholds, governance block
  (`references/capability-profiles.json`). Seeds only — refined via feedback.
- **Routing CLI**: `scripts/route.py` — classify → tier → policy → Pareto
  frontier recommendation + escalation ladder; `--json` output; vendor/latency
  constraints.
- **Validation GATE**: `scripts/validate_graph.py` — 0 failures required
  (freshness, model completeness, TTL/JSON parity, rdflib parse).
- **SPARQL query templates** (T1–T5) for graph interrogation.
- **Feedback loop**: `references/feedback-log.ttl` template + workflow to keep
  capability seeds fresh.
- **Governance**: approved/blocked models, residency constraints, cost caps.

### Notes
- Capability/latency values are curated estimates at first release, derived from
  model-family positioning. They are explicitly seeds: the feedback loop is the
  mechanism that converts them into measured, current values.
- The llm-prices data files in the local checkout are stale (Oct 2025, 7
  vendors); the skill's default path fetches live data instead.
