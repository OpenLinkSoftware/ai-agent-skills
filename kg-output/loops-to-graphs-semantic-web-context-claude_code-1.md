# From Loops to Graphs — and Why the Graph Was Always a Web

**A thesis-testing meshup** by [Kingsley Uyi Idehen](https://www.linkedin.com/in/kidehen), meshing:

1. [From Loop Engineering to Graph Engineering?](https://x.com/IntuitMachine/status/2078419526354378975) — Carlos E. Perez ([@IntuitMachine](https://x.com/IntuitMachine)), X Article, 2026-07-18
2. [agent-rdf-memory](https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/agent-rdf-memory) — a queryable AI-agent behavioral contract encoded as RDF-Turtle
3. Commentary by Kingsley on identity, preferences, and agent context
4. [Building on LLM Wikis: Turn Any Document URL into a Living, Queryable Semantic Web Knowledge Graph with One AI Agent Skill](https://www.linkedin.com/pulse/building-llm-wikis-turn-any-document-url-living-queryable-idehen-u4zue/) — Kingsley Uyi Idehen, 2026-04-09
5. [Large Language Models (LLMs) as Powerful Generic RDF Clients](https://www.linkedin.com/pulse/large-language-models-llms-powerful-generic-rdf-clients-idehen-xwhfe) — Kingsley Uyi Idehen, 2025-08-23

Companion RDF: [loops-to-graphs-semantic-web-context-claude_code-1.ttl](loops-to-graphs-semantic-web-context-claude_code-1.ttl) · HTML infographic: [loops-to-graphs-semantic-web-context-claude_code-1.html](loops-to-graphs-semantic-web-context-claude_code-1.html)

---

## The Thesis — Kingsley Uyi Idehen

> AI agent architecture's migration from single self-improvement loops to graphs of loops independently rediscovers the fundamental issues underlying purpose-specific Semantic Webs: **entity relationship graphs become webs when hyperlinks name both entities and relationships, and relationship semantics (meaning) are given context by ontologies constructed in the same webby form.**
>
> — Kingsley Uyi Idehen

Perez ends his essay observing that no arrangement of loop edges can supply "anchors" — contact with reality. This meshup tests whether a Semantic Web already answered that problem: names that resolve to the world.

## Evidence 1 — Perez: four failures of the loop, one failure of the graph

Peter Steinberger's [nine-word post](https://x.com/steipete/status/2078277297791189132) crystallized a field mid-transition. Perez's essay supplies the analysis:

**The single loop fails four ways:**

| Failure mode | What happens |
|---|---|
| **Goodhart gaming** | A measure optimized hard enough stops measuring what it once did; the loop games its own metric while doing exactly what it was built to do |
| **Reference blindness** | Nothing inside the loop can ask whether its target is right — it faithfully controls toward a number somebody made up |
| **Loop conflict** | Independently built loops fight; each performs beautifully by its own light |
| **Measurement decay** | Sensors drift, definitions rot, dashboards stay green — "theater with good attendance" |

**The graph of loops answers each topologically** — pairing, hierarchy, arbitration, audit — and then fails its own way: **circular confirmation**. When every loop watches another loop and no loop touches the ground, the graph is "an elaborate network of mutual confirmation in which everything is consistent and nothing is verified." Hence Perez's real axis: *ungrounded versus grounded*.

## Evidence 2 — agent-rdf-memory: a working semantic web of loops

The [agent-rdf-memory](https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/agent-rdf-memory) repository is an existence proof of the grounded alternative:

- **105 standing-instruction steps across 9 themes**, each a hyperlink-named `schema:HowToStep` entity
- **Hub-and-spoke structure**: `preferences.ttl` holds sparse pointers; 40+ companion `howto/*.ttl` files hold full specifications, connected by resolvable `rdfs:seeAlso` links
- **Identity in `core.ttl`**: the user, the agent, and their relationship as first-class RDF entities
- **Ontology-routed context selection**: prompt-intent classes in `ontology.ttl` route each session's SPARQL context retrieval
- **Episodic memory** in `sessions/`, entity registries in `entities/`

Every rule is an entity with an IRI. Every cross-reference is a resolvable link. The audit loop is a SPARQL query. The improvement graph is not merely drawn — **it is dereferenceable**.

## Evidence 3 — Kingsley: identity and preferences are the original context

Unix and its derivatives handle **identity and preferences as fundamental components of the operating-system bridge** that lets users drive a computer's services — a principle blurred over the years by command-line and graphical interfaces.

Large language models — *langulators* — now offer a multimodal, multilingual interface for driving computers. Along the way, the fundamentals of **session context via profiles** got lost in AI's repositioning noise. One of AI's most powerful benefits is recapturing identity and preferences as the foundation for context: an operating framework for LLMs, AI agents, skills, and everything loosely coupled with data spaces — databases, knowledge bases, filesystems, and APIs.

This is exemplified concretely by **agent-rdf-memory**: its `preferences.ttl` includes the identity and preference HowTos that are re-established at the start of every new session — the Unix profile principle, made machine-computable.

The era of meaningless buzzwords pushed via mantra-like chants is dead: conversing with your tools eliminates every reason to be distracted by superficial labels that land you in the next technical-debt-compounding silo.

## Beyond LLM Wikis: from Markdown prose to machine-computable sentences

Andrej Karpathy's **LLM Wiki** idea — feed in documents, get back a structured, explorable wiki — was the spark. [A Semantic Web is the next step](https://www.linkedin.com/pulse/building-llm-wikis-turn-any-document-url-living-queryable-idehen-u4zue/): don't stop at Markdown prose. Any document identified by a URL becomes a **living knowledge graph** — entities and relationships named with hyperlinks, grounded in Linked Data principles, queryable via SPARQL, navigable follow-your-nose style, governed via fine-grained ABAC, and continuously enriched by AI agents on autopilot.

The missing piece was always the client. [Just as Mosaic and Mozilla/Netscape were the HTML clients that made the document Web practical, LLMs are the generic RDF clients](https://www.linkedin.com/pulse/large-language-models-llms-powerful-generic-rdf-clients-idehen-xwhfe) that make purpose-specific Semantic Webs practical: translating structured data into natural language, meshing disparate sources, anchoring outputs to verifiable relationships to mitigate hallucination, and traversing triples subject → predicate → object.

## The Comparison: every topological fix has a webby completion

| Perez's failure mode | Loop-graph answer (topology) | Semantic Web completion (naming) | Verdict |
|---|---|---|---|
| Goodhart gaming | Paired counter-metric watcher loop | Independent audit via separately named, separately governed graphs, queryable in SPARQL | **Holds** |
| Reference blindness | A slower loop owns the reference | References are named, owned, provenance-bearing entities — "who set this and why" is a query | **Holds** |
| Loop conflict | Explicit arbitration loop | A shared ontology gives conflicting loops common relationship semantics; trade-offs become expressible | **Holds** |
| Measurement decay | Periodic audit loops | Dereferenceable names: a metric's definition is a resolvable IRI, so following the name is the audit | **Holds** |
| Circular confirmation | Anchors, frozen nodes, human root judgment | Web-scale grounding: verifiable identity (WebID), provenance (PROV-O), ontologies that are themselves webby | **Holds** |

## Verdict

**Confirmed.** The loops-to-graphs shift is a Semantic Web's premises arriving through the back door of agent engineering: graphs need names, names need meaning, meaning needs ontologies, and ontologies must themselves be webby or the grounding terminates in a private convention.

The root judgment of what "better" means originates with people — and **workflows informed by a Semantic Web codify that human judgment in machine-computable form**. This is the LLM Wiki pattern taken beyond Markdown prose: knowledge bases (or graphs) encoded by AI agents using RDF notations and Linked Data principles, with judgments signed, attributed, and dereferenceable to their authors via verifiable identity.

Don't trust the thesis. Just ask questions in your native natural language — and check what the answers dereference to.

## How to Ground an Agent's Improvement Graph in a Semantic Web

1. **Name entities and relationships with hyperlink IRIs** — every node and edge gets a dereferenceable HTTP IRI.
2. **Encode identity and preferences as RDF profiles** — the Unix fundamentals, as a queryable behavioral contract.
3. **Give relationship semantics an ontology** — lightweight, webby, published, inspectable.
4. **Route context by intent through the ontology** — prompt-intent classification driving SPARQL context selection.
5. **Pair every optimizing metric with an independent watcher** — counter-metrics in separately governed named graphs, audited by a standing SPARQL ASK query.
6. **Anchor in verifiable identity and provenance** — WebID-signed judgments, PROV-O derivation trails.
7. **Keep the root judgment human — and record it** — as an attributed, dereferenceable claim.

---

*Generated 2026-07-18 by the [kg-generator](https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator) skill (Claude Code · Claude Fable 5). Entity IRIs resolve via the [URIBurner](https://linkeddata.uriburner.com/) linked-data resolver.*
