# AI Ontology: Bottom-Up Doesn't Mean Starting From Scratch

**Canonical URL:** https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/

**Author:** Emily Winks (Data Governance / Context & Chaos)  
**Publisher:** Atlan — Context & Chaos  
**Date published:** 2026-09-04  
**Source excerpt cleaned for demo use (UTF-8).**

---

> We mined 32,237 claims into a business ontology. Every claim carried a source and a confidence score. Not one could say when it stopped being true.

## Opening

For most of my career, the ontology problem I saw ran in the opposite direction: the model came first, and reconciling it with real data came later, if at all.

I came to data from library and information science, and what I kept meeting were models built carefully in the abstract that nobody could reconcile with a real database. You built the model. Then you reached the physical tables underneath and found the two did not connect, and the model sat there being correct and useless. An ontology describes how a business is supposed to work. The data records how it actually ran.

That is part of why, when we began exploring whether a business ontology could be induced from a company's own data, we chose to work strictly bottom-up. No hand-authored schema, no seeded set of business concepts. Everything had to come from systems the business already used. The bigger reason was that we were designing for agents to consume the output first and people second. Nobody consulted a standard or brought in a specialist on the way in.

**We over-corrected.** Bottom-up answered the question of where definitions should come from. We treated it as an answer to how they should be represented too.

The design records where every business definition came from and how strongly the evidence supports it. It has no way to record when that definition was valid.

What follows is a review of a design, not an account of a working system.

## The failure we were trying to correct

Ask an agent what a team's win rate was last quarter and it produces one answer with complete confidence. Inside a company there is usually no single definition to retrieve. One team computes win rate as closed-won over all closed opportunities. Another excludes deals that never reached qualification. A third counts only new-business pipeline. The definitions sit in SQL analysts wrote, in dashboard formulas, and in a deal-desk playbook, and they disagree without any of them being obviously wrong. A model that cannot see the disagreement picks one reading and states it as fact.

So the goal was narrow. Mine the definitions already in use, keep each one attached to its source, score the evidence behind it, and where sources disagree, **show the disagreement instead of quietly reconciling it**. Contested cases go to a person who can approve, change, split, or reject them. Lineage at the column level fills in what a mined query cannot tell you on its own, which is the specific columns a formula runs on.

## What the experiment actually produced

We pointed it at four of our own systems: a cloud warehouse, a CRM, a BI tool, and our own metadata catalog. The exercise yielded **32,237 claims**, reconciled into **14 entities**, **79 metrics**, **61 properties**, and **35 relationships**.

The output lands in two separate places, not one. There is an exploration tool, where the candidate ontology takes shape: entities, their relationships, and the metrics tied to each, browsable as a graph. And there is a plainer destination, where results drop into the same catalog the claims were mined from, and anyone can edit them there like any other entry, adding what is missing or removing what is wrong. Those two are not the same thing yet.

It has not been implemented or tested as a system, and we are still well inside the design phase. We are still experimenting with what we can do, and actively trying to break our own initial hypothesis. It is early enough to throw any of this out.

## Three old arguments already in the design

Ontology engineering has spent decades on a set of questions that are still unsettled. The design was never checked against them. Reading it back against them afterwards, four turned out to be relevant. Kurt Cagle recently made the broader case that AI teams are rediscovering these fault lines without knowing the history behind them.

### Open and closed worlds

Open-world systems let knowledge stay incomplete and let multiple descriptions coexist. Closed-world systems work inside a bounded model for a particular task. Ours keeps competing claims during discovery and then narrows what can be served through human review, which is not a formal implementation of either. What it does is walk into the governance question underneath both: when several definitions are defensible, who decides which one an agent may use?

### Reification

Reification means treating a claim as an entity in its own right, so you can make further statements about it. Our claim records are closer in spirit to the RDF-star work now reflected in RDF 1.2, where a reifier lets further statements be attached to a triple. The standard's own illustration of what you would attach to a statement is its **source**, its **confidence level**, and a **timestamp**. We arrived at a similar mechanism without using the standard, and we took the source and the confidence.

### Partitioning and authority

Multi-tenancy, access, provenance, and authority all need boundaries. Our design says what is in scope and logs what falls outside it. That resembles part of what a **named graph** does rather than amounting to one. Named graphs are one part of the approach now being considered.

Each of those problems had at least a rough counterpart in the design. The fourth did not.

## The missing dimension was time

Every claim carries a source. None carries a validity period.

Knowledge graphs often describe either one moment or a set of assertions treated as permanently true, and retrieval systems inherit the same weakness. The business changes while the retrieved definition goes on looking current.

Our design has no validity intervals, no effective dates, no supersession. A definition of win rate is mined, scored, reviewed, and served, and nothing anywhere records that it applied during a particular period.

Detecting a change is not the same as describing the period before it. Without that, the system cannot answer a question about last quarter without silently assuming that today's definition also held then.

The fix may be smaller than it sounds. Claims already carry evidence and confidence; getting them to carry a validity date too may not need a new mechanism, just **two dates and a rule for who sets them**.

## Did we build an ontology at all?

Time was the clearest omission and not the only one. Had we built an ontology, or a well-documented model of our own data?

After extraction, the system pulls variant names together under one canonical entity — resembling authority control. An authority record holds the established form of a name, the variants pointing to it, and the source and date that established it. We have the first two. The third (provenance and time) is missing.

Standards sitting unused:

- **SKOS** — concepts, hierarchies, preferred vs alternate labels
- **BARTOC** — registry of thesauri, ontologies and classifications
- **Dublin Core** — creator and date among its original fifteen elements
- **OWL** — axioms and constraints a reasoner can check
- **SHACL** — shapes to validate against

The honest description may be smaller: a careful account of tables, joins, and metrics — useful, but a lesser claim than the word *ontology* makes. One ontologist said flatly that we should not be calling it an ontology. I did not disagree.

## What should bottom-up inherit?

The bottom-up commitment still was not the error. No inherited ontology was going to tell us how a particular deal desk computes win rate — that meaning has to come from the organization. The error was letting the first answer settle the second.

> **Discover meaning locally. Do not reinvent how meaning is represented.**

How should a system keep local business meaning while adopting established ways to represent time, authority, provenance and change?

---

*Source: Context & Chaos / Atlan. Cleaned extract for Virtuoso showcase demo. All rights remain with Atlan / original author.*
