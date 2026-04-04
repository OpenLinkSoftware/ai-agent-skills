# Linked Data Skills — Protocol Routing

Use this file only when you need execution routing guidance beyond the main skill instructions.

---

## Default Execution Order

1. **Native OAI.DBA tool execution** — call `OAI.DBA.*` tools directly via the agent tool layer
2. **URIBurner / Demo REST function execution** — call via the REST API endpoint
3. **Terminal-owned OAuth flow** — when the REST or OpenAPI endpoint requires OAuth 2.0 authentication, execute the OAuth flow from the terminal (authorization code, client credentials, or device flow), capture the Bearer token, and inject via `Authorization: Bearer {token}` header into subsequent REST/OpenAPI calls
4. **MCP** — via streamable HTTP (`https://linkeddata.uriburner.com/chat/mcp/messages`) or SSE (`https://linkeddata.uriburner.com/chat/mcp/sse`)
5. **Authenticated `chatPromptComplete`** — LLM-mediated execution via `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`
6. **OPAL Agent routing** — via canonical OPAL-recognizable function names

If the user explicitly names a protocol (e.g., "use MCP", "use REST", "use OPAL"), honor that preference instead of the default order.

---

## Authentication

Both REST and MCP endpoints support **OAuth**. If a tool call or REST request returns 401, 403, or 500 (which may indicate an unauthenticated session), initiate the OAuth flow before retrying.

### OAuth Flow — MCP

| Instance | Authenticate via |
|----------|-----------------|
| `demo.openlinksw.com` | Call `mcp__claude_ai_OpenLink_Demo__authenticate` |
| `linkeddata.uriburner.com` | Call `mcp__claude_ai_URIBurner__authenticate` |

These tools start the OAuth flow and return an authorization URL. Share the URL with the user. Once the user completes authorization in their browser, the MCP tools become available automatically.

### OAuth Flow — REST

The REST endpoints (`/chat/functions/*`) also support OAuth. If REST calls return 401/403/500 and MCP OAuth is not available, direct the user to authenticate via the MCP flow above — successful MCP OAuth also covers REST on the same instance.

### When to trigger authentication

- Any tool call or REST request returns 401, 403, or unexpected 500
- `database_schema_objects`, `RDFVIEW_*`, or `EXECUTE_SQL_SCRIPT` fail while `execute_spasql_query` succeeds (indicates partial auth — discovery and write tools require an authenticated session)
- User explicitly asks to authenticate or switch accounts

Do not retry a failed call more than once before triggering the OAuth flow.

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
- `https://demo.openlinksw.com/chat/mcp/messages` (streamable HTTP — Demo instance)
- `https://linkeddata.uriburner.com/chat/mcp/messages` (streamable HTTP — URIBurner)
- `https://linkeddata.uriburner.com/chat/mcp/sse` (SSE — URIBurner)

Treat MCP as requiring authentication unless the client is already configured. Use the OAuth flow above if not.

---

## REST Function Execution

Functions are callable via the REST API. Consult the OpenAPI specs for exact signatures:

| Instance | Functions/Procedures API | Chat API |
|----------|--------------------------|----------|
| `demo.openlinksw.com` | `https://demo.openlinksw.com/chat/functions/openapi.yaml` | `https://demo.openlinksw.com/chat/api/openapi.yaml` |
| `linkeddata.uriburner.com` | `https://linkeddata.uriburner.com/chat/functions/openapi.yaml` | `https://linkeddata.uriburner.com/chat/api/openapi.yaml` |

---

## chatPromptComplete

Endpoint: `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`

Requires authentication. Use as fallback after MCP when native tool execution and REST have failed.

---

## Target Instances

| Instance | Purpose |
|----------|---------|
| `Demo` (`demo.openlinksw.com`) | Test and sample data — default |
| `URIBurner` (`linkeddata.uriburner.com`) | Production |

When the user has not specified an instance, default to `Demo`. Confirm with the user before executing against `URIBurner`.
