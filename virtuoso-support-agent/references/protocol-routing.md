# Protocol Routing - Virtuoso Support Agent

Covers execution modalities and environment-specific guidance for invoking the 25 available tools.

---

## Invocation Modalities

The tools in this skill can be invoked through any of the following modalities. Choose based on what the host environment supports.

### 1. MCP (Model Context Protocol) — Primary

Use when the host environment is MCP-enabled (e.g., Claude Code, MCP-compatible agent frameworks).

Endpoints:
- Streamable HTTP (preferred): `https://linkeddata.uriburner.com/chat/mcp/messages`
- SSE: `https://linkeddata.uriburner.com/chat/mcp/sse`

Tool naming convention: `{ServerName}:{ToolName}`
- `Demo:execute_spasql_query`
- `URIBurner:sparqlQuery`

All 25 tools are available via MCP on both Demo and URIBurner servers.

Guidance:
- Prefer streamable HTTP unless the client specifically expects SSE.
- Treat MCP as requiring authentication unless the client is already configured.
- From this environment, both MCP endpoints returned `401 Unauthorized` on March 6, 2026.

---

### 2. URIBurner REST Functions

Use when the host environment supports HTTP REST calls but not MCP, or when a specific function is more naturally called as a REST endpoint.

Base URL: `https://linkeddata.uriburner.com/chat/functions/`

Key function endpoints:

| Function | Endpoint |
|---|---|
| SPASQL query | `/execute_spasql_query` |
| SQL query | `/execute_sql_query` |
| SPARQL (local) | `/sparqlQuery` |
| SPARQL (remote) | `/sparqlRemoteQuery` |
| GraphQL | `/graphqlQuery` |
| Web fetch | `/WEB_FETCH` |
| RDF sponge/extract | `/SPONGE_URL` |
| LLM completion | `/chatPromptComplete` |

Full OpenAPI spec: `https://linkeddata.uriburner.com/chat/functions/openapi.yaml`

Guidance:
- REST calls use GET with URL-encoded parameters unless the spec specifies POST.
- Equivalent to MCP tool calls for query execution and utility functions.
- RDF Views generation tools (`RDFVIEW_FROM_TABLES`, etc.) are MCP-only; use REST query functions for validation steps.

---

### 3. OPAL Agent Routing

Use when the host environment is an OPAL-enabled agent, or when the user explicitly asks for OPAL routing.

Canonical OPAL-recognizable function names:

| Category | OPAL Function |
|---|---|
| SPASQL | `Demo.demo.execute_spasql_query` |
| SQL | `Demo.demo.execute_sql_query` |
| SPARQL (local) | `UB.DBA.sparqlQuery` |
| SPARQL (remote) | `OAI.DBA.sparqlRemoteQuery` |
| GraphQL | `DB.DBA.graphqlQuery` |
| LLM completion | `OAI.DBA.chatPromptComplete` |

Guidance:
- OPAL is an agent routing layer over named functions, not merely a transport.
- Use qualified function names (catalog.schema.function) when routing through OPAL.
- Server selection (Demo vs URIBurner) is expressed through the function qualifier, not a prefix.

---

### 4. OpenAI-Compatible API (chatPromptComplete)

Use when the host environment supports OpenAI-compatible function/tool calling, or when LLM-mediated execution is needed.

Endpoint: `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`

Also available via the Chat API:
Full OpenAPI spec: `https://linkeddata.uriburner.com/chat/api/openapi.yaml`

Guidance:
- Requires a valid API key or OAuth-backed credential.
- Use for complex multi-step reasoning tasks or when agent orchestration is needed.
- From this environment, unauthenticated calls failed on March 6, 2026 because no API key was supplied.

---

### 5. Direct curl (Query Execution Only)

Use as a fallback for query execution when no other modality is available. Not applicable to RDF Views generation or database management tools.

SPASQL:
```bash
curl -s -G "https://linkeddata.uriburner.com/chat/functions/execute_spasql_query" \
  --data-urlencode "sql=SPARQL SELECT * WHERE { ?s ?p ?o } LIMIT 10" \
  --data-urlencode "format=json"
```

SPARQL (local):
```bash
curl -s -G "https://linkeddata.uriburner.com/chat/functions/sparqlQuery" \
  --data-urlencode "query=SELECT * WHERE { ?s ?p ?o } LIMIT 10" \
  --data-urlencode "format=json"
```

---

## Environment Reference

| Environment | Recommended Modality |
|---|---|
| Claude Code (MCP-enabled) | MCP |
| REST/HTTP client | URIBurner REST Functions |
| OPAL agent | OPAL Agent Routing |
| OpenAI-compatible client | chatPromptComplete |
| CLI / scripting | Direct curl (query execution only) |

---

## Instance Selection and Routing

All modalities support both Virtuoso instances. Confirm the target instance before any operation:

| Instance | MCP Prefix | OPAL Qualifier | REST Base |
|---|---|---|---|
| Demo | `Demo:` | `Demo.demo.` | `https://linkeddata.uriburner.com/chat/functions/` |
| URIBurner | `URIBurner:` | `UB.DBA.` / `OAI.DBA.` | `https://linkeddata.uriburner.com/chat/functions/` |

---

## Preference Override

If the user explicitly names a modality, honor it:
- "Use MCP" → MCP with `{ServerName}:{ToolName}`
- "Use REST" → URIBurner REST Functions
- "Use OPAL" → OPAL Agent Routing with canonical function names
- "Use the OpenAI-compatible route" → `chatPromptComplete`
- "Just use curl" → Direct curl (query execution only)
