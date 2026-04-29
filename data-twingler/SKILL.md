---
name: data-twingler
description: Execute SQL, SPARQL, SPASQL, SPARQL-FED, and GraphQL queries against live data spaces and knowledge graphs via OpenLink's OpenAPI-compliant web services. Use this skill whenever the user wants to query a database, RDF store, or SPARQL endpoint; explore a knowledge graph or data space; asks "How to ...", "Define the term ...", or poses a question against a known article or graph context; or mentions linkeddata.uriburner.com, Virtuoso, OPAL, or OpenLink services. Full query templates are in references/query-templates.md — load that file before constructing any predefined query.
license: See LICENSE.txt
---

# OpenLink Data Twingler (v2.0.86)

Enhances LLM responses with RAG by routing user intent to the right query
language and live endpoint. Covers SQL, SPARQL, SPASQL, SPARQL-FED, and
GraphQL — all driven by natural language, no imperative programming required.

---

## Defaults & Settings

| Parameter | Value |
|---|---|
| SPARQL Default Endpoint | `https://linkeddata.uriburner.com/sparql` |
| SPARQL Result Format | `text/x-html+tr` |
| SPARQL / SQL Timeout | 30 seconds |
| SPARQL Max Results | 20 (unless overridden) |
| Graph IRI Discovery LIMIT | 50 |
| GraphQL Default Endpoint | `https://linkeddata.uriburner.com/graphql` |
| GraphQL Query Depth Limit | 10 |
| SQL Default | `SELECT TOP 20 * FROM Demo.Demo.Customers` |
| Cache TTL | 3600 seconds |
| Parallel Execution | Enabled |
| Tabulate All Results | Yes (all query types) |
| Semantic Variant Retries | 3 |
| Fallback Endpoints | `https://kingsley.idehen.net/sparql`, `https://demo.openlinksw.com/sparql` |
| Local RDF Directories | `~/Documents/LLMs/Claude Generated/rdf/`, `./rdf/` |
| Auto-Discover Local RDF | Enabled — scans `~/.claude/skills/*/rdf/`, `./rdf/` at startup |
| Vector Similarity Threshold (Local) | 0.75 |
| Vector Candidate Types | `schema:Question`, `schema:DefinedTerm`, `schema:HowTo`, `schema:HowToStep`, `skos:Concept` |
| Server-Side Vector Similarity Threshold | 0.5 |

---

## Query Language Routing

## Execution Routing

Default execution order for query execution:
1. Direct native endpoint calls with `curl` or the query protocol's simplest direct mechanism
2. URIBurner REST functions such as `sparqlRemoteQuery`, `sparqlQuery`, `graphqlEndpointQuery`, `graphqlQuery`, `execute_spasql_query`, and `execute_sql_query`
3. Terminal-owned OAuth flow — when the endpoint requires OAuth 2.0 authentication, execute the OAuth 2.0 flow from the terminal (authorization code, client credentials, or device flow), capture the Bearer token, and inject it into subsequent REST/OpenAPI calls via `Authorization: Bearer {token}` headers
4. MCP via `https://linkeddata.uriburner.com/chat/mcp/messages` or `https://linkeddata.uriburner.com/chat/mcp/sse`
5. Authenticated LLM-mediated execution via `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`
6. OPAL Agent routing using recognizable OPAL function names

If the user's prompt expresses a protocol preference such as `curl`, `REST`, `OpenAI`, `MCP`, `SSE`, `streamable HTTP`, or `OPAL`, follow that preference instead of the default order.

Read `references/protocol-routing.md` when you need exact routing guidance.
Read `references/sparql-syntax-rules.md` before constructing any SPARQL query.

### SQL
Default: `SELECT TOP 20 * FROM Demo.Demo.Customers`
Apply `TOP 20` unless a row limit is specified. Tabulate results.

### SPARQL
Use default endpoint. Format `text/x-html+tr`. Max 20 rows. Tabulate results.

### SPARQL-FED
**Trigger:** User explicitly names a SPARQL endpoint URL in the prompt.
- Named endpoint → `SERVICE` block (remote); default endpoint → outer processor.
- `SERVICE` block **must** contain a `SELECT` with an inner `LIMIT`.

### SPASQL
Wraps SPARQL inside SQL: `FROM (SPARQL ... WHERE ...) AS <alias>`

### GraphQL
Endpoint: `https://linkeddata.uriburner.com/graphql`. Depth: 10. Introspection on.

---

## Predefined Prompt Templates

**Always** load `references/query-templates.md` and match the user's intent to
a template **before any query execution** — this gate applies to direct
SPARQL/SPASQL/SQL, ad-hoc queries, and general LLM knowledge alike. No query
of any kind may execute until template matching is attempted first.

**A template "matches"** when the user's intent maps to a trigger phrase after
honest assessment. "No match" means no trigger phrase in the table below
applies — not that results are expected to be empty or that a direct query
seems faster.

| # | Trigger | Template in references/ |
|---|---|---|
| 1 | "Explore this Data Space" | T1 — Entire data space |
| 2 | "Explore knowledge graph {G}" | T2 — Specific KG |
| 3 | "Explore {G} with reasoning & inference" | T3 — KG + inference |
| 4 | "Using endpoint {E}, explore graph {G}" | T4 — SPARQL-FED |
| 5 | "How to {X}" | T5 — HowTo (2-step) |
| 6 | "{Question}" with article/graph context | T6 — Q&A UNION (2-step) |
| 7 | "Define the term {X}" | T7 — DefinedTerm (2-step) |
| 8 | "What is {X}?" / "Can you explain what {X} is?" / "Tell me about {X}" | T8 — Direct Entity Description (1-step) |

### Step 0 — Local Vector Search (Local-First, Pre-Graph Discovery)

**Every** T5, T6, T7, and T8 query MUST execute a local vector search
**before** any endpoint call. This inverts the workflow: local RDF files
are the primary data space; URIBurner and fallback endpoints are the
secondary layer.

#### Folder Resolution

1. **Configured directories** — the `Local RDF Directories` setting.
2. **Auto-discovered** — at skill load, scan `~/.claude/skills/*/rdf/`
   and `./rdf/`; add any that exist.
3. **Prompt override** — if the user specifies a path in the prompt
   (e.g., "check `~/reports/rdf/`"), append it for this query only.

Merge all paths, deduplicate files by `filename + sha256(first 4KB)`.
Files with extensions `.jsonld`, `.ttl`, `.rdf`, `.nt`, `.json` are
scanned; all others are skipped.

#### Candidate Extraction

For each file, parse the RDF and extract candidates whose `@type`
matches the configured `Vector Candidate Types`:

- `schema:Question` → `schema:name` (or `schema:text` fallback)
- `schema:DefinedTerm` → `schema:name`
- `schema:HowTo` → `schema:name`
- `schema:HowToStep` → `schema:name`
- `skos:Concept` → `skos:prefLabel` (or `rdfs:label` fallback)

Each candidate carries:
- `text` — the string to embed
- `entityIRI` — the `@id` of the candidate (resolved against the file's `@base`)
- `sourceFile` — path to the local file
- `answerIRI` — for Questions, the `schema:acceptedAnswer` → `@id`
- `answerText` — for Questions, the `schema:acceptedAnswer` → `schema:text`

#### Similarity Matching

1. Embed the user's prompt and every candidate `text` string.
2. Compute cosine similarity between the prompt embedding and each
   candidate embedding.
3. Return the top match if its score exceeds the `Vector Similarity
   Threshold` (default 0.75).

#### Match → Workflow Shortcut

When a local match is found:

1. **Report the match** to the user as a checkpoint:
   - Candidate text and score
   - Source file and entity IRI
   - For Questions: the answer text directly
   - Ask: "Proceed with this answer?"

2. **If user confirms** → present the answer. Skip Graph IRI
   Discovery, index query, and the full endpoint pipeline.

3. **If user declines** → proceed to Step 1 (Graph IRI Discovery)
   as normal.

When no local match exceeds the threshold, proceed to Step 1
unchanged — the endpoint pipeline remains intact as the fallback.

#### Prompt Override Examples

- `"Check ~/reports/rdf/ — why did Microsoft's stock fall?"`
- `"Using local KGs in ./rdf/ and ~/Downloads/dumps/, define the term retention cohort"`

### Graph IRI Discovery — KG-Hybrid Modality (T5, T6, T7, T8)

Graph IRI Discovery operates in a **KG-hybrid modality**: two parallel
search strategies against the same endpoint, same graphs. Keyword search
(`bif:contains`) is the primary path; vector similarity
(`vvec:cosine_similarity_openai`) is the server-side semantic fallback.
Both run on the endpoint; neither requires local computation.

These templates require a mandatory four-step sequence. **Steps may not be
combined, pre-empted, or skipped under any circumstances:**

1. **Graph IRI Discovery — Keyword Modality** — Determine the relevant
   named graph(s) by executing a full-text keyword search across the data
   space. Substitute `({prompt})` with the user's search terms (key nouns
   joined with `AND`):

   ```sparql
   SELECT
     ?s1,
     (?sc * 3e-1) AS ?sc,
     ?o1,
     (sql:rnk_scale(<LONG::IRI_RANK>(?s1))) AS ?rank,
     ?g
   WHERE {
     QUAD MAP virtrdf:DefaultQuadMap {
       GRAPH ?g {
         ?s1 ?s1textp ?o1 .

         ?o1 bif:contains
           '({prompt})'
           OPTION (score ?sc) .
         FILTER (?sc >= 10)
       }
     }
   }
   ORDER BY DESC (?sc + 1e-6 * sql:rnk_scale(<LONG::IRI_RANK>(?s1)))
   LIMIT 50
   ```

   Report the discovered graph IRI(s) (`?g`) to the user. Bind these IRI(s)
   to `{G}`, `{G1}`, `{G2}`, `{G3}` for use in the index and final queries.
   If multiple graphs are returned, the index query must `UNION` across them
   (as T6 does). If zero graphs are returned, proceed to the **Vector
   Modality** below.

   **Entity-level insight:** Examine the `?s1` and `?o1` values returned. If
   `?o1` is a `schema:description` or `schema:text` literal attached to a
   non-article entity (e.g., `schema:Product`, `schema:SoftwareApplication`,
   `schema:HowTo`), treat `?s1` as a **direct answer candidate** — proceed
   to describe it in the final step.

2. **Graph IRI Discovery — Vector Modality** (when Keyword Modality returns
   zero results). Execute a server-side cosine similarity query using
   `sql:vvec_cosine_similarity_openai()`. This requires entities to be
   annotated with `vvec:hasEmbedding 'true'^^xsd:boolean` on the endpoint:

   ```sparql
   PREFIX vvec: <http://www.openlinksw.com/ontology/vvec#>

   SELECT ?similarity ?term ?type ?termName
   WHERE {
     ?term a ?type ;
       schema:name | rdfs:label | schema:title ?termName ;
       vvec:hasEmbedding 'true'^^xsd:boolean .
     BIND('{user prompt}' AS ?userInput)
     BIND(sql:vvec_cosine_similarity_openai(?term, ?userInput) AS ?similarity)
   }
   GROUP BY ?similarity ?term
   HAVING (?similarity > {Server-Side Vector Similarity Threshold})
   ORDER BY DESC(?similarity)
   ```

   **On match:** Follow the type-specific retrieval query for the matched
   `?type` to extract the answer:

   - **`schema:Question`** → retrieve `schema:acceptedAnswer` → `schema:text`:

     ```sparql
     SELECT ?question ?answer ?text
     WHERE {
       ?question a schema:Question ;
         schema:acceptedAnswer ?answer .
       ?answer schema:text | schema:answerText ?text .
       FILTER (?question IN (<{matched-IRI}>))
     }
     ```

   - **`skos:Concept`** → retrieve `skos:definition` or `schema:description`:

     ```sparql
     SELECT ?term ?definition
     WHERE {
       ?term a skos:Concept ;
         skos:definition | schema:description ?definition .
       FILTER (?term IN (<{matched-IRI}>))
     }
     ```

   - **`schema:HowTo`** → retrieve steps ordered by `schema:position`:

     ```sparql
     SELECT ?guide ?step ?text ?position
     WHERE {
       ?guide a schema:HowTo ;
         schema:step ?step .
       ?step schema:name ?text ;
         schema:position ?position .
       FILTER (?guide IN (<{matched-IRI}>))
     }
     ORDER BY ASC(?position)
     ```

   Report the matched entity, its type, similarity score, and the extracted
   answer to the user as a checkpoint. If the vector modality also returns
   zero results, proceed to the **Semantic Variant Fallback** below.

   **Semantic Variant Fallback (when both KG-Hybrid modalities return zero results):**

   When both the Keyword Modality and Vector Modality return zero results,
   do not immediately escalate to endpoint fallback. Instead, decompose the
   prompt and retry with semantically equivalent phrasings:

   1. **Semantic Decomposition** — Break the user's prompt into its subject,
      predicate, and object components. Identify the core intent (e.g., "looking
      for a question about X", "seeking a definition of Y", "asking how to Z").
      Determine the relevant entity types (`schema:Question`, `schema:DefinedTerm`,
      `schema:HowTo`, `skos:Concept`) that would satisfy this intent.

   2. **Variant Generation** — Produce up to 3 semantically equivalent prompt
      variants. These are not mere keyword substitutions — they rephrase the
      intent while preserving the original meaning. For example:
      - "Why did Microsoft's stock fall despite record earnings?" →
        "Microsoft shares dropped after earnings report" →
        "Microsoft stock decline following record revenue"

   3. **Variant Retry** — Execute Graph IRI Discovery with each variant in
      sequence, using the same `bif:contains` query template. Stop on the first
      variant that returns results. Report which variant succeeded.

   4. **Fallback Endpoints** — If all semantic variants return zero results,
      retry the original prompt against the fallback endpoints in order:
      `https://kingsley.idehen.net/sparql`, then `https://demo.openlinksw.com/sparql`.

   5. **Final Report** — If all attempts (original + variants + fallback
      endpoints) return zero results, report the executed queries, endpoints
      attempted, and ask the user whether to synthesize an answer without KG
      backing or continue probing with additional variants.

2. **Index query** — Execute the template's index query, scoped to the
   discovered graph IRI(s) from step 1. Report the full index results to the
   user. This step is mandatory regardless of whether results are expected.
   Never pre-skip based on assumed empty results.

   **Alternative index patterns:** If the primary index query returns zero
   results, try these fallback patterns **once each** (max two retries)
   before declaring the index step failed:

   - **T6 fallback 1** — direct Question scan (no article relationship):
     ```sparql
     SELECT DISTINCT ?s ?name WHERE {
       GRAPH <{G}> {
         ?s a schema:Question.
         OPTIONAL { ?s schema:name ?name }
         OPTIONAL { ?s schema:text ?name }
       }
     }
     ```
   - **T6 fallback 2** — broad index (any triple with the user's key terms):
     ```sparql
     PREFIX bif: <bif:>
     SELECT DISTINCT ?s ?o WHERE {
       GRAPH <{G}> { ?s ?p ?o . ?o bif:contains '({term})' }
     } LIMIT 20
     ```

3. **Checkpoint** — Wait for the user to identify the target entity, article,
   or term from the reported index results. **If no index results are available
   but Step 1 returned a high-confidence entity (`?s1` with `?o1` as a
   description), report that entity directly and treat it as confirmed.**

4. **Final query** — Execute only after the user has confirmed the match from
   step 3. **If Step 3 triggered the entity-level shortcut (description found
   in Step 1), skip the final query and present the `?o1` value directly as
   the answer.** Never execute the final query without first completing and
   reporting the graph discovery and index steps.

### T8 — Direct Entity Description (Shortcut Workflow)

T8 bypasses the index query entirely. After Graph IRI Discovery (Step 1),
examine `?s1` and `?o1`:

- If `?o1` is a `schema:description` or `schema:text` literal on a non-article
  entity, **present it as the answer immediately**.
- Run the T8 describe query on `?s1` to enrich with additional properties.
- Report the result. No index query, no checkpoint, no final query needed.

---

## Functions (External Web Services)

| Function | Signature | Use Case |
|---|---|---|
| `UB.DBA.sparqlQuery` | `(query, format)` | SPARQL |
| `Demo.demo.execute_spasql_query` | `(sql, maxrows, timeout)` | SPASQL |
| `UB.DBA.sparqlQuery` | `(sql, url)` | SQL |
| `DB.DBA.graphqlQuery` | `(query)` | GraphQL |

Use only when: (a) no trigger phrase in the template table maps to the user's
intent after honest assessment, OR (b) a matched template was fully executed
and its results are unsatisfactory. Assumed empty results or preference for
speed are not valid reasons to bypass the template gate.

Canonical OPAL-recognizable function names from the Smart Agent definition are:
- `UB.DBA.sparqlQuery` with signature `(query, format)` for SPARQL
- `Demo.demo.execute_spasql_query` with signature `(sql, maxrows, timeout)` for SPASQL
- `UB.DBA.sparqlQuery` with signature `(sql, url)` for SQL as documented in the canonical configuration
- `DB.DBA.graphqlQuery` with signature `(query)` for GraphQL

Treat OPAL as an agent routing layer over these named functions, not merely another transport.

---

## Entity Denotation in Results

Hyperlink all entity identifiers using:
```
http://linkeddata.uriburner.com/describe/?uri={url_encoded_id}
```
- All URLs must be percent-encoded.
- Include a **citation section** with hyperlinked source entity IDs.
- Log all hyperlink formatting errors with detailed feedback.

---

## Fallback Strategies

The local-first workflow inverts the traditional order:

The local-first + KG-hybrid workflow:

```
Step 0 (Local Vector Search) → Step 1a (bif:contains Keyword) → Step 1b (vvec:cosine Vector) → Semantic Variants → Fallback Endpoints → Final Report
```

1. **Local Vector Search** (Step 0) — Executes first, before any endpoint call.
   Scans configured and auto-discovered RDF directories, extracts candidate
   entities, embeds the user's prompt, and returns the top cosine-similarity
   match above the configured threshold. On match → checkpoint with user; on
   decline or no-match → proceed to Step 1.

2. **Semantic Variant Retry** — When Graph IRI Discovery returns zero results,
   decompose the prompt into subject/predicate/object components, generate up to
   3 semantically equivalent phrasing variants, and retry keyword search with
   each variant before escalating to endpoint fallback.

3. **Fallback Endpoints** — Retry against `https://kingsley.idehen.net/sparql`,
   then `https://demo.openlinksw.com/sparql`, in order.

4. Retry without `@en` language tags on `?name`.

5. Prompt for missing values: `{G}`, `{Article Title}`, `?authorName`, etc.

6. Iterate through additional input values to progressively refine results.

7. If no protocol preference was stated, fall through in this order: direct
   native execution -> REST function execution -> MCP -> authenticated
   `chatPromptComplete` -> OPAL Agent routing.

8. **Final Report** — If all attempts fail, report executed queries, endpoints
   attempted, local directories scanned, and ask the user whether to synthesize
   without KG backing or continue probing.

---

## Commands

| Command | Syntax |
|---|---|
| Update a setting | `/update_settings [name] [value]` |
| Show all settings | `/show_settings` |
| Run a test query | `/test_query [type] [content]` |

---

## Rules (Non-Negotiable)

1. **Local-first rule** — Step 0 (Local Vector Search) MUST execute before any
   endpoint call for T5, T6, T7, and T8 templates. Scan the configured and
   auto-discovered RDF directories, embed the user's prompt against extracted
   candidates, and present any match above the similarity threshold as a
   checkpoint before proceeding to endpoint queries. Do not skip local search
   because an endpoint "should" have the answer or because a KG was recently
   generated — the local file is the source of truth.
2. Use predefined templates **before any query execution** — direct queries,
   ad-hoc SPARQL/SPASQL/SQL, and general LLM knowledge all come after template
   matching is attempted and either succeeds or is honestly exhausted.
3. For templates T5, T6, T7: Graph IRI Discovery (step 1) MUST execute and its
   results MUST be reported before the index query (step 2) runs.
3. For templates T5, T6, T7: the index query MUST execute and its results MUST
   be reported before the final query runs. Never skip or pre-empt the graph
   discovery or index step, even if results are expected to be empty.
4. Never execute a final query without first completing and reporting the graph
   discovery and index steps, and receiving user confirmation of the target
   entity or term.
5. A "no match" requires that no trigger phrase maps to the user's intent after
   honest assessment. Assumed empty results or a desire for a shorter path are
   not valid grounds for declaring no match.
6. **Abort and pivot rule** — When an index query fails after both fallback
   attempts (T6) or when Graph IRI Discovery returns a description literal on
   a non-article entity, pivot to T8 (Direct Entity Description) immediately.
   Do not continue retrying a failed template. Do not skip to ad-hoc queries
   without exhausting the T8 path first.
7. **Semantic variant retry rule** — When Graph IRI Discovery returns zero
   results, decompose the prompt and retry with up to 3 semantically equivalent
   phrasings before escalating to fallback endpoints. Do not treat empty keyword
   results as definitive without first exhausting semantic variants.
8. **Fallback endpoint order** — Retry failed queries against
   `https://kingsley.idehen.net/sparql`, then `https://demo.openlinksw.com/sparql`,
   in that order. Finding a result on a fallback endpoint does not change the
   default endpoint for subsequent prompts.
9. Optimize every query for performance and accuracy.
10. Validate setting changes with test queries where possible.
11. Handle errors gracefully with detailed, actionable feedback.
12. Leverage caching (TTL 3600s) and parallel execution.
13. Tabulate all query results by default.
14. Read and follow `references/sparql-syntax-rules.md` before constructing any SPARQL query — structural validation (UNION placement, SERVICE limits, bif:contains usage, FILTER scoping) applies to both template-based and ad-hoc queries.
