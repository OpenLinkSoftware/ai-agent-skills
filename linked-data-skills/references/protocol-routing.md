# Linked Data Skills — Protocol Routing

Use this file only when you need execution routing guidance beyond the main skill instructions.

---

## Default Execution Order

1. **Native OAI.DBA tool execution** — call `OAI.DBA.*` tools directly via the agent tool layer
2. **URIBurner / Demo REST function execution** — call via the REST API endpoint
3. **MCP** — via streamable HTTP (`https://linkeddata.uriburner.com/chat/mcp/messages`) or SSE (`https://linkeddata.uriburner.com/chat/mcp/sse`)
4. **Authenticated `chatPromptComplete`** — LLM-mediated execution via `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`
5. **OPAL Agent routing** — via canonical OPAL-recognizable function names

If the user explicitly names a protocol (e.g., "use MCP", "use REST", "use OPAL"), honor that preference instead of the default order.

---

## Canonical OPAL Function Names

From the Smart Agent definition, the canonical OPAL-recognizable function names for this skill are:

| Operation | Canonical Name |
|-----------|---------------|
| Read/query execution | `Demo.demo.execute_spasql_query` |
| Table discovery | `ADM.DBA.database_schema_objects` |
| TBox generation | `OAI.DBA.RDFVIEW_ONTOLOGY_FROM_TABLES` |
| ABox generation | `OAI.DBA.RDFVIEW_FROM_TABLES` |
| Rewrite rules generation | `OAI.DBA.RDFVIEW_GENERATE_DATA_RULES` |
| Script execution | `OAI.DBA.EXECUTE_SQL_SCRIPT` |

Use these names when the user asks for OPAL-oriented routing.

---

## MCP

Endpoints:
- `https://linkeddata.uriburner.com/chat/mcp/messages` (streamable HTTP)
- `https://linkeddata.uriburner.com/chat/mcp/sse` (SSE)

Treat MCP as requiring authentication unless the client is already configured.

---

## REST Function Execution

Functions are callable via the URIBurner REST API. Consult the OpenAPI specs for exact signatures:

- **Chat API:** `https://linkeddata.uriburner.com/chat/api/openapi.yaml`
- **Functions/Procedures API:** `https://linkeddata.uriburner.com/chat/functions/openapi.yaml`

---

## chatPromptComplete

Endpoint: `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`

Requires authentication (API key). Use as fallback after MCP when native tool execution and REST have failed.

---

## Target Instances

| Instance | Purpose |
|----------|---------|
| `Demo` | Test and sample data |
| `URIBurner` | Production |

When the user has not specified an instance, default to `Demo`. Confirm with the user before executing against `URIBurner`.
