# Data Twingler Skill — Journey from Prompt to Answer

The workflow steps in the section that follows breaks down how this skill is used to interact with a progressively maintained knowledge graph from initial prompt all the way to final response:

1. Encounter a document of interest  
2. Transform the content into a knowledge graph, typically comprising an article description, FAQ, glossary, and how-to  
3. Upload the result to a Virtuoso instance via its SPARQL endpoint or WebDAV-based filesystem interface  

## Related

1. [Slide deck about Document-to-Knowledge-Graph Skill](https://www.openlinksw.com/data/screencasts/doc-to-knowledge-graph-deck.mp4)  
2. [Screencast Demo: Generating a Knowledge Graph from an Article about S3 Files](https://www.openlinksw.com/data/screencasts/amazon-s3-files-doc-via-codex-using-doc-kg-skill.mp4)

---

## Step 1 — Receive Prompt

User submits a natural language prompt.

---

## Step 2 — KG Harness Gate (Template Matching)

Load `references/query-templates.md`. Assess the user's intent honestly against every trigger phrase in the template table (T1–T8).

- **Match found** → proceed to Step 3 with the matched template.
- **No match** → skip to Step 9 (Execution Routing Fallback). A "no match" means no trigger phrase applies — not that results are expected to be empty or that a direct query seems faster.

**This gate applies before any query execution of any kind — direct SPARQL, ad-hoc queries, and general LLM knowledge all sit behind it.**

---

## Step 3 — Route by Template Type

| Templates | Path |
|-----------|------|
| T1, T2, T3, T4 | Single-step → proceed directly to Step 8 (Execute Query) |
| T5, T6, T7, T8 | Multi-step → proceed to Step 4 (Graph IRI Discovery) |

---

## Step 4 — Graph IRI Discovery (T5 / T6 / T7 / T8)

Execute a full-text search SPARQL query against `virtrdf:DefaultQuadMap`. Extract key substantive terms from the user's prompt, join with `AND`, drop stop words. Use `bif:contains` with boolean operators — never bare natural language.

Report the discovered graph IRI(s) (`?g`) to the user. Bind to `{G}`, `{G1}`, `{G2}`, `{G3}` for use in subsequent queries.

**Outcomes:**

- **Description literal found on a non-article entity** (`schema:description` or `schema:text` on e.g. `schema:DefinedTerm`, `schema:SoftwareApplication`) → T8 Shortcut triggered. Skip to Step 7.
- **Named graph IRI(s) returned** → proceed to Step 5.
- **Zero graphs returned** → report to user and skip to Step 9 (Fallback).

---

## Step 5 — Index Query (T5 / T6 / T7)

Execute the template's index query scoped to the discovered graph IRI(s) from Step 4. Report the full results to the user.

**This step is mandatory regardless of whether results are expected. Never pre-skip.**

If multiple graphs were returned, the index query must `UNION` across them.

**Outcomes:**

- **Results returned** → proceed to Step 6 (Checkpoint).
- **Zero results (T6)** → attempt Fallback 1: direct `schema:Question` scan on `{G}`. If still zero, attempt Fallback 2: broad `bif:contains` scan on `{G}`. If both fail → abort and pivot to T8 (Step 7) or proceed to Step 9.

---

## Step 6 — Checkpoint (T5 / T6 / T7)

Present the full index results to the user. Wait for the user to identify and confirm the target entity, article, or term.

**Never proceed to the final query without this confirmation.**

Exception: if Step 4 returned a high-confidence description literal on a non-article entity, that entity is treated as confirmed and Step 6 is bypassed via the T8 shortcut.

---

## Step 7 — T8 Shortcut (Direct Entity Description)

Triggered when Graph IRI Discovery returns a `schema:description` or `schema:text` literal on a non-article entity, or when the index query fails after all fallbacks.

Run the T8 describe query on `?s1`. Present the `?o1` value directly as the answer. No index query, no checkpoint, no final query needed. Proceed to Step 10 for output formatting.

---

## Step 8 — Execute Query (T1–T4) or Final Query (T5 / T6 / T7)

Execute the matched template's query using the confirmed entity/article IRI and the discovered graph IRI(s). Apply `references/sparql-syntax-rules.md` before constructing any query — validate UNION placement, SERVICE limits, `bif:contains` boolean expressions, and FILTER scoping.

Use the execution routing order unless the user has named a preferred protocol:
1. `curl` / direct endpoint call
2. URIBurner REST functions
3. Terminal-owned OAuth flow (if endpoint requires it)
4. MCP
5. `chatPromptComplete` (authenticated, LLM-mediated)
6. OPAL Agent routing

---

## Step 9 — Execution Routing Fallback (no template match or exhausted retries)

No predefined template matched, or all retries were exhausted. Execute directly using the routing order in Step 8. This is the only point at which general LLM knowledge or ad-hoc query construction is permitted.

---

## Step 10 — Format and Return

1. Tabulate all query results.
2. Hyperlink every entity identifier: `http://linkeddata.uriburner.com/describe/?uri={percent_encoded_IRI}`
3. Include a citation section with hyperlinked source entity IRIs.
4. Return the formatted response to the user.


# Additional Information
- [Routing Guide used for Protocol Selection](https://github.com/OpenLinkSoftware/ai-agent-skills/blob/main/data-twingler/references/protocol-routing.md)
- [Query Templates](https://github.com/OpenLinkSoftware/ai-agent-skills/blob/main/data-twingler/references/query-templates.md)
- [SPARQL Syntax Rules for Virtuoso](https://github.com/OpenLinkSoftware/ai-agent-skills/blob/main/data-twingler/references/sparql-syntax-rules.md)
