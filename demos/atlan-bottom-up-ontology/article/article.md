# AI Ontology: Bottom-Up Doesn't Mean Starting From Scratch

**Article KG companions:** [article.ttl](article.ttl) · [article.html](article.html) · [article-source.md](article-source.md)  
**Canonical URL:** [https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/)

| Entity | IRI |
|--------|-----|
| Article | [`#article`](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#article) |
| Emily Winks | [`#person-emily-winks`](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#person-emily-winks) |
| Atlan | [`#org-atlan`](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#org-atlan) |
| Ontology | [`#term-ontology`](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-ontology) → [DBpedia](http://dbpedia.org/resource/Ontology_(information_science)) / [Wikidata](http://www.wikidata.org/entity/Q324254) |
| Knowledge graph | [`#term-knowledge-graph`](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-knowledge-graph) |
| RDF | [`#term-rdf`](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-rdf) |
| SPARQL | [`#term-sparql`](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-sparql) |
| SKOS | [`#term-skos`](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-skos) |
| OWL | [`#term-owl`](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-owl) |
| SHACL | [`#term-shacl`](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-shacl) |
| Reification | [`#term-reification`](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-reification) |
| Named graph | [`#term-named-graph`](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-named-graph) |
| Validity interval | [`#term-validity-interval`](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-validity-interval) |
| Win rate | [`#term-win-rate`](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-win-rate) |
| Claim | [`#term-claim`](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-claim) |
| Provenance | [`#term-provenance`](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-provenance) |

## Thesis

Bottom-up ontology mining from real systems is right for discovering **local meaning**. The over-correction was skipping **inherited representation standards** — [SKOS](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-skos), [RDF-star / reification](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-reification), [named graphs](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-named-graph), [OWL](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-owl) / [SHACL](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-shacl), Dublin Core dates.

> [Discover meaning locally. Do not reinvent how meaning is represented.](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#thesis)

Author: [Emily Winks](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#person-emily-winks) · Publisher: [Atlan](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#org-atlan) · 2026-09-04

## Failure mode: competing [win rate](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-win-rate) definitions

Ask an agent for last quarter's win rate and it returns one confident answer. Inside the company there is no single definition:

| Claim | Definition | Source | Confidence | Validity |
|-------|------------|--------|------------|----------|
| [#claim-winrate-closed-won](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#claim-winrate-closed-won) | closed-won / all closed | Warehouse | 0.82 | 2024-01-01 → 2025-06-30 |
| [#claim-winrate-exclude-unqualified](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#claim-winrate-exclude-unqualified) | exclude never-qualified | CRM | 0.91 | 2024-07-01 → 2026-03-31 |
| [#claim-winrate-new-business](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#claim-winrate-new-business) | new-business only | BI | 0.74 | 2025-01-01 → (open) |

Competing definitions should **surface disagreement**, not silently reconcile.

## Experiment numbers

| Measure | Value | IRI |
|---------|------:|-----|
| Claims | [32,237](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#qv-claims) | mined from warehouse / CRM / BI / catalog |
| Entities | [14](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#qv-entities) | |
| Metrics | [79](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#qv-metrics) | |
| Properties | [61](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#qv-properties) | |
| Relationships | [35](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#qv-relationships) | |

## Three old arguments (plus the missing fourth)

1. **Open / closed world** — keep competing claims, then govern which one an agent may use.
2. **[Reification](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-reification)** — claim as entity; attach source + confidence (+ timestamp in RDF 1.2).
3. **[Named graphs](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-named-graph)** — partitioning for authority / access / provenance.
4. **Missing: [validity interval](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-validity-interval)** — every claim had source; none had when it stopped being true.

## Did we build an ontology?

Without [OWL](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-owl) axioms and [SHACL](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/#term-shacl) shapes, the honest description may be a careful account of tables, joins, and metrics — useful, but a lesser claim than *ontology*.

## How Virtuoso closes the gap

This demo collection shows:

1. **Bottom-up evidence** in `DB.kidehen` tables (`sql/`) — claims with source, confidence, **and** `valid_from` / `valid_to`.
2. **Inherited form** in OWL/RDFS + SKOS (`ontology/atlan-cc.ttl`).
3. **RDF Views** bridging SQL → graph `http://localhost:8890/atlan-cc#` (`rdfviews/`).
4. **One truth, three query languages** — SQL, SPASQL, SPARQL (`queries/`) with spasqlqb permalinks at `http://localhost:8890/spasqlqb/`.

See [../index.html](../index.html) and [../README.md](../README.md).
