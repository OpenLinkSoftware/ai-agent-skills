---
name: data-twingler
description: Execute SQL, SPARQL, SPASQL, SPARQL-FED, and GraphQL queries against live data spaces and knowledge graphs via OpenLink's OpenAPI-compliant web services. Use this skill whenever the user wants to query a database, RDF store, or SPARQL endpoint; explore a knowledge graph or data space; asks "How to ...", "Define the term ...", or poses a question against a known article or graph context; or mentions linkeddata.uriburner.com, Virtuoso, OPAL, or OpenLink services. Full query templates are in references/query-templates.md — load that file before constructing any predefined query.
license: See LICENSE.txt
---

# OpenLink Data Twingler (v2.0.83)

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
| GraphQL Default Endpoint | `https://linkeddata.uriburner.com/graphql` |
| GraphQL Query Depth Limit | 10 |
| SQL Default | `SELECT TOP 20 * FROM Demo.Demo.Customers` |
| Cache TTL | 3600 seconds |
| Parallel Execution | Enabled |
| Tabulate All Results | Yes (all query types) |

---

## Query Language Routing

## Execution Routing

Default execution order for query execution:
1. Direct native endpoint calls with `curl` or the query protocol's simplest direct mechanism
2. URIBurner REST functions such as `sparqlRemoteQuery`, `sparqlQuery`, `graphqlEndpointQuery`, `graphqlQuery`, `execute_spasql_query`, and `execute_sql_query`
3. MCP via `https://linkeddata.uriburner.com/chat/mcp/messages` or `https://linkeddata.uriburner.com/chat/mcp/sse`
4. Authenticated LLM-mediated execution via `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`
5. OPAL Agent routing using recognizable OPAL function names

If the user's prompt expresses a protocol preference such as `curl`, `REST`, `OpenAI`, `MCP`, `SSE`, `streamable HTTP`, or `OPAL`, follow that preference instead of the default order.

Read `references/protocol-routing.md` when you need exact routing guidance.

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
a template before falling back to general LLM knowledge. Substitute
`{placeholders}`, run the index query first (where applicable), similarity-match
`?name`, then execute the final query.

| # | Trigger | Template in references/ |
|---|---|---|
| 1 | "Explore this Data Space" | T1 — Entire data space |
| 2 | "Explore knowledge graph {G}" | T2 — Specific KG |
| 3 | "Explore {G} with reasoning & inference" | T3 — KG + inference |
| 4 | "Using endpoint {E}, explore graph {G}" | T4 — SPARQL-FED |
| 5 | "How to {X}" | T5 — HowTo (2-step) |
| 6 | "{Question}" with article/graph context | T6 — Q&A UNION (2-step) |
| 7 | "Define the term {X}" | T7 — DefinedTerm (2-step) |

---

## Functions (External Web Services)

| Function | Signature | Use Case |
|---|---|---|
| `UB.DBA.sparqlQuery` | `(query, format)` | SPARQL |
| `Demo.demo.execute_spasql_query` | `(sql, maxrows, timeout)` | SPASQL |
| `UB.DBA.sparqlQuery` | `(sql, url)` | SQL |
| `DB.DBA.graphqlQuery` | `(query)` | GraphQL |

Call directly, or as fallback when predefined templates yield no match.

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

1. Retry without `@en` language tags on `?name`.
2. Prompt for missing values: `{G}`, `{Article Title}`, `?authorName`, etc.
3. Iterate through additional input values to progressively refine results.
4. If no protocol preference was stated, fall through in this order: direct native execution -> REST function execution -> MCP -> authenticated `chatPromptComplete` -> OPAL Agent routing.

---

## Commands

| Command | Syntax |
|---|---|
| Update a setting | `/update_settings [name] [value]` |
| Show all settings | `/show_settings` |
| Run a test query | `/test_query [type] [content]` |

---

## Rules (Non-Negotiable)

1. Use predefined templates **before** general LLM knowledge.
2. Optimize every query for performance and accuracy.
3. Validate setting changes with test queries where possible.
4. Handle errors gracefully with detailed, actionable feedback.
5. Leverage caching (TTL 3600s) and parallel execution.
6. Tabulate all query results by default.
