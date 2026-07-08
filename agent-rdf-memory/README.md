# Agent RDF Memory

Queryable behavioral contract for AI agents, encoded as RDF-Turtle. All standing instructions live here — never in the platform's flat markdown memory store.

## Folder structure

```
agent-rdf-memory/
├── README.md              ← this file
├── core.ttl               ← user identity, agent identity template, output paths
├── preferences.ttl        ← hub: 9 sub-HowTos, 105 HowToStep definitions
├── ontology.ttl           ← custom vocabulary (triggers, prompt types)
├── index.ttl              ← session index (one schema:ListItem per session)
├── howto/                 ← companion specification files (one per sub-HowTo)
│   ├── agent-identity.ttl
│   ├── artifact-routing.ttl
│   ├── canonical-entity-iri-denotation.ttl
│   ├── …                  ← (40+ files, see § Sub-HowTo map below)
│   └── youid-validation-gates.ttl
├── sessions/              ← episodic memory (YYYY-MM-DD-{llm}-{env}.ttl)
├── projects/              ← project-specific knowledge
├── entities/              ← people, organizations, tools, concepts
└── scripts/               ← validation & utility scripts
```

## Retrieval protocol (mandatory)

Before any task, the agent must:

1. List `agent-rdf-memory/` and all subfolders
2. Read `core.ttl`
3. Read `preferences.ttl`
4. Read `index.ttl`
5. Follow `index.ttl` references to relevant `sessions/` or `projects/` files

See `howto/session-governance.ttl` for the full protocol.

## Preferences structure

`preferences.ttl` is a **hub-and-spoke** model:

```
:agentBehaviorGuide (hub)
├── schema:about    → 9 topic entities (conceptual grouping)
└── schema:hasPart  → 9 sub-HowTos (each owns its own schema:step list)
```

Each sub-HowTo has `rdfs:seeAlso` links to companion `howto/*.ttl` files that contain the full specification text. Steps in `preferences.ttl` are sparse pointers (name + one-sentence `schema:text` + `rdfs:seeAlso`). All rationale, code, gates, and incident notes live in the howto files.

## Sub-HowTo map

| # | Sub-HowTo | Steps | Primary howto files |
|---|-----------|-------|---------------------|
| 1 | `:howto-identity-webid` | 14 | agent-identity, verified-identity, youid-delegation, webid-verification-services, webid-verification-table, delegation-insert-gate, youid-validation-gates |
| 2 | `:howto-memory-management` | 16 | session-governance, memory-protocol-gate, token-optimized-session-handoff, sparql-memory-loading, no-unauthorized-deletion, no-memory-md-write |
| 3 | `:howto-artifact-routing` | 7 | artifact-routing, remote-webdav-upload |
| 4 | `:howto-rdf-authoring` | 19 | canonical-entity-iri-denotation, entity-iri-denotation-mechanics, canonical-iri-compliance-gate, entity-type-gate, external-iri-verification, entity-link-placement, concept-entity-hyperlinking, faq-entity-iri-gate, sparql-absolute-prefix-iri, entity-href-companion-ttl, owl-sameas-vs-skos-related, entity-lookup-disambiguation, rdf-residence-vs-birthplace, no-blank-nodes-resolver-entities, rdf-document-authoring |
| 5 | `:howto-html-kg-explorer` | 38 | infographic-authoring, kg-explorer-ui-patterns, kg-explorer-d3-patterns, kg-explorer-reuse-first, harness-contract-compliance, rdf-infographic-compliance-gate, rdf-infographic-gated-workflow, footer-sparql-explorer-gate, sparql-html-escape-gate, study-prior-patterns, kg-curation-attribution, ui-ux-expert-persona |
| 6 | `:howto-ontology-generation` | 2 | ontology-cross-reference-gate, owl-property-characterization, ontology-discovery |
| 7 | `:howto-skill-workflows` | 6 | skill-invocation, opal-session-vocabulary, uriburner-oauth-authcode-flow |
| 8 | `:howto-virtuoso-sparql` | 2 | virtuoso-sparql-formats, virtuoso-workbench-query-dedup |
| 9 | `:howto-terminology` | 1 | artifact-routing, rdf-document-authoring |

**Total: 105 steps across 9 themes.**

## Querying preferences

### SPARQL (if loaded into a triplestore)

```sparql
# All steps for a specific domain
SELECT ?step ?pos ?name WHERE {
    :howto-rdf-authoring schema:step ?step .
    ?step schema:position ?pos ; schema:name ?name .
} ORDER BY ?pos
```

### File-based (grep)

```bash
# Find which sub-HowTo owns a step
grep -l "schema:step.*step-whoamiFormat" agent-rdf-memory/preferences.ttl
# → :howto-identity-webid
```

## Adding a new rule

1. Decide which sub-HowTo it belongs to (or create a new one if none fit)
2. Add a `schema:HowToStep` entry to `preferences.ttl`
3. Add the step to the sub-HowTo's `schema:step` list
4. Write the full specification to the companion `howto/<topic>.ttl`
5. If creating a new sub-HowTo: add it to `:agentBehaviorGuide` `schema:hasPart`, add a topic entity, and update this README

## Related

- `CLAUDE.md` / `AGENT.md` — prose reference (authoritative upon conflict: `preferences.ttl` wins)
- `SESSION-START-HOOK.md` — runtime injection mechanism for session initialization
- `scripts/validate-memory-protocol.py` — post-session audit gate
