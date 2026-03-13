# Protocol Routing - URIBurner OPAL Agent Skills

Covers execution modalities and environment-specific guidance for invoking URIBurner tools.

---

## Invocation Modalities

URIBurner tools can be invoked through any of the following modalities. Choose based on what the host environment supports.

### 1. MCP (Model Context Protocol) — Primary

Use when the host environment is MCP-enabled (e.g., Claude Code, MCP-compatible agent frameworks).

Endpoints:
- Streamable HTTP (preferred): `https://linkeddata.uriburner.com/chat/mcp/messages`
- SSE: `https://linkeddata.uriburner.com/chat/mcp/sse`

All native tools are invoked by name directly:
- `execute_spasql_query`
- `sparqlQuery`
- `sparqlRemoteQuery`
- `execute_sql_query`
- `WEB_FETCH`
- `SPONGE_URL`
- `sparql_list_entity_types`
- `sparql_list_entity_types_samples`
- `database_schema_objects`
- `ChatPromptComplete`

Guidance:
- Prefer streamable HTTP unless the client specifically expects SSE.
- Treat MCP as requiring authentication unless the client is already configured.
- Use native tools directly for standard operations; reserve `ChatPromptComplete` for when the user explicitly requests Gemini/SPARQL Agent 121.

---

### 2. URIBurner REST Functions

Use when the host environment supports HTTP REST calls but not MCP.

Base URL: `https://linkeddata.uriburner.com/chat/functions/`

Full OpenAPI spec: `https://linkeddata.uriburner.com/chat/functions/openapi.yaml`

Key endpoints:

| Tool | REST Endpoint |
|---|---|
| SPASQL query | `/execute_spasql_query` |
| SQL query | `/execute_sql_query` |
| SPARQL (local) | `/sparqlQuery` |
| SPARQL (remote) | `/sparqlRemoteQuery` |
| Web fetch | `/WEB_FETCH` |
| RDF sponge/extract | `/SPONGE_URL` |
| LLM completion | `/chatPromptComplete` |
| Schema objects | `/database_schema_objects` |

Guidance:
- REST calls use GET with URL-encoded parameters unless the spec specifies POST.
- Equivalent to MCP for query and data retrieval operations.

---

### 3. OPAL Agent Routing

Use when the host environment is an OPAL-enabled agent, or when the user explicitly requests OPAL routing.

Canonical OPAL-recognizable function names:

| Tool | OPAL Function |
|---|---|
| SPASQL | `Demo.demo.execute_spasql_query` |
| SQL | `Demo.demo.execute_sql_query` |
| SPARQL (local) | `UB.DBA.sparqlQuery` |
| SPARQL (remote) | `OAI.DBA.sparqlRemoteQuery` |
| GraphQL | `DB.DBA.graphqlQuery` |
| LLM completion | `OAI.DBA.chatPromptComplete` |

Guidance:
- OPAL is an agent routing layer over named functions, not merely a transport.
- Use fully-qualified function names (catalog.schema.function) when routing through OPAL.

---

### 4. OpenAI-Compatible API (chatPromptComplete / SPARQL Agent 121)

Use when the user explicitly requests Gemini-powered analysis, citation verification, or SPARQL Agent 121's KG-first workflow.

Endpoint: `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`

Also available via the Chat API:
Full OpenAPI spec: `https://linkeddata.uriburner.com/chat/api/openapi.yaml`

Configuration for SPARQL Agent 121:
```json
{
  "model": "gemini-2.5-pro",
  "assistant_config_id": "new-sparql-agent-121",
  "prompt": "Your query here",
  "temperature": "0.5",
  "timeout": 30
}
```

Guidance:
- Requires a valid API key or OAuth-backed credential.
- Do NOT use for standard queries — use native MCP tools instead.
- Use for: `/kg-verify`, `/kg-on`, citation verification, multi-endpoint KG orchestration.

---

### 5. Direct curl (Query Execution Only)

Use as a last-resort fallback when no other modality is available.

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

WEB_FETCH:
```bash
curl -s -G "https://linkeddata.uriburner.com/chat/functions/WEB_FETCH" \
  --data-urlencode "url=https://example.com"
```

---

## Environment Reference

| Environment | Recommended Modality |
|---|---|
| Claude Code (MCP-enabled) | MCP |
| REST/HTTP client | URIBurner REST Functions |
| OPAL agent | OPAL Agent Routing |
| OpenAI-compatible client | chatPromptComplete (SPARQL Agent 121) |
| CLI / scripting | Direct curl (query execution only) |

---

## SPARQL Endpoints Reference

| Endpoint | URL | Notes |
|---|---|---|
| URIBurner (default) | `https://linkeddata.uriburner.com/sparql` | Virtuoso; bif:contains() supported |
| Kingsley's Instance | `https://kingsley.idehen.net/sparql` | Rich HowTo/technical content |
| Demo | `https://demo.openlinksw.com/sparql` | OpenLink sample datasets |
| DBpedia | `https://dbpedia.org/sparql` | Wikipedia structured data |
| Wikidata | `https://query.wikidata.org/sparql` | 100M+ items |

---

## Preference Override

If the user explicitly names a modality, honor it:
- "Use MCP" → MCP, invoke tools by name directly
- "Use REST" → URIBurner REST Functions
- "Use OPAL" → OPAL Agent Routing with canonical function names
- "Use Gemini / SPARQL Agent 121" → `chatPromptComplete` with `assistant_config_id: "new-sparql-agent-121"`
- "Just use curl" → Direct curl (query execution only)
