# Data Twingler Protocol Routing

Use this file only when you need execution routing guidance beyond the main skill instructions.

## Default Order

This is the **transport** order for executing a query. Retrieval order for
T5–T8 is set in `SKILL.md` (UB-first; local RDF files are a fallback only after
endpoint keyword search, probe-gated vector search, semantic variants and
fallback endpoints are exhausted). Local RDF files are never scanned before the
network.

1. Direct native execution such as `curl` to the target endpoint
2. URIBurner REST functions
3. Terminal-owned OAuth flow — authenticate via OAuth 2.0 from the terminal to enable authenticated REST/OpenAPI calls; obtain a Bearer token and inject via `Authorization: Bearer {token}` header. Also the route when the Vector Capability Probe records `vvec_cosine = auth-required` (`SR186`) and the user wants the legacy cosine path
4. MCP via streamable HTTP or SSE
5. Authenticated `chatPromptComplete`
6. OPAL Agent routing via recognizable function names

### Vector-search endpoint routing

Before any vector query, run the VP probe (`references/query-templates.md`)
against the endpoint chosen above and cache the result for the session. Vector
queries go only to endpoints whose probe passed. When the user's endpoint
fails, offer `https://vec.demo.openlinksw.com/sparql` (the configured
`Vector Search Endpoint`) and say that the switch changes the data being
searched.

---

## Authentication

Both REST and MCP endpoints support **OAuth**. If a tool call or REST request returns 401, 403, or 500 (which may indicate an unauthenticated session), initiate the OAuth flow before retrying.

### OAuth Flow — MCP

| Instance | Authenticate via |
|----------|-----------------|
| `linkeddata.uriburner.com` | Call `mcp__claude_ai_URIBurner__authenticate` |

This tool starts the OAuth flow and returns an authorization URL. Share the URL with the user. Once the user completes authorization in their browser, the MCP tools become available automatically.

### OAuth Flow — REST

The REST endpoints (`/chat/functions/*`) also support OAuth. If REST calls return 401/403/500 and MCP OAuth is not available, direct the user to authenticate via the MCP flow above — successful MCP OAuth also covers REST on the same instance.

### When to trigger authentication

- Any tool call or REST request returns 401, 403, or unexpected 500
- User explicitly asks to authenticate or switch accounts

Do not retry a failed call more than once before triggering the OAuth flow.

---

## REST Functions

Use the URIBurner REST function surface when direct native execution is not the selected route. Keep OPAL naming distinct from raw REST endpoint naming.

### Required Parameters

Before calling a REST, MCP, OPAL, or A2A backend function, construct and verify
the required structured parameters for the chosen function.

| Intent | Function | Required parameters |
|---|---|---|
| Local SPARQL | `UB.DBA.sparqlQuery` | `query`, `format` |
| Remote SPARQL | `OAI.DBA.sparqlRemoteQuery` | `url`, `query` |
| SPASQL | `Demo.demo.execute_spasql_query` | `sql` |
| SQL | `Demo.demo.execute_sql_query` | `sql` |
| GraphQL | `DB.DBA.graphqlQuery` | `query` |

Known remote KG aliases:

| Alias | Endpoint URL |
|---|---|
| `DBpedia` | `https://dbpedia.org/sparql` |
| `Wikidata` | `https://query.wikidata.org/sparql` |

If a user asks "Using DBpedia, ...", treat that as remote SPARQL intent and
bind `url=https://dbpedia.org/sparql` plus a generated SPARQL `query` before
calling the backend. Do not forward only the natural-language prompt to a
function that requires `url`, `query`, or `sql`.

## MCP

Endpoints:
- `https://linkeddata.uriburner.com/chat/mcp/messages`
- `https://linkeddata.uriburner.com/chat/mcp/sse`

Guidance:
- Treat MCP as requiring authentication unless the client is already configured. See Authentication section above.

## OPAL Agent Routing

Treat OPAL as an agent layer over recognizable tools/functions. Use the canonical Smart Agent function names when the user asks for OPAL-oriented routing:
- `UB.DBA.sparqlQuery`
- `OAI.DBA.sparqlRemoteQuery`
- `Demo.demo.execute_spasql_query`
- `DB.DBA.graphqlQuery`

Keep authenticated `chatPromptComplete` as a separate routing option after MCP; do not present it as one of the canonical Data Twingler tool names unless the source configuration is updated.

### OPAL/A2A Guard

For OPAL/A2A routing, perform a preflight check immediately before the backend
function call:

1. Identify the intended function.
2. Build the concrete argument object.
3. Verify all required parameters are non-empty strings or valid values.
4. If anything is missing, return an actionable error naming the missing
   parameter and function instead of making the backend call.

Example preflight result for "Using DBpedia, list movies by Spike Lee":

```json
{
  "function": "OAI.DBA.sparqlRemoteQuery",
  "arguments": {
    "url": "https://dbpedia.org/sparql",
    "query": "PREFIX dbr: <http://dbpedia.org/resource/>\\nPREFIX dbo: <http://dbpedia.org/ontology/>\\nSELECT DISTINCT ?movie WHERE { ?movie a dbo:Film ; dbo:director dbr:Spike_Lee . } LIMIT 20"
  }
}
```
