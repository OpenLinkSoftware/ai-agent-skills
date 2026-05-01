# Data Twingler Protocol Routing

Use this file only when you need execution routing guidance beyond the main skill instructions.

## Default Order

1. **Local RDF files** — scan configured directories (`~/Documents/LLMs/Claude Generated/rdf/`, `./rdf/`) and auto-discovered paths for `.jsonld`, `.ttl`, `.rdf`, `.nt` files. Extract candidates matching `Vector Candidate Types` and run vector similarity against the user prompt. If a match exceeds the `Vector Similarity Threshold` (0.75), offer it to the user before making any network call. If no local match or user declines, proceed to step 2.
2. Direct native execution such as `curl` to the target endpoint
3. URIBurner REST functions
4. Terminal-owned OAuth flow — authenticate via OAuth 2.0 from the terminal to enable authenticated REST/OpenAPI calls; obtain a Bearer token and inject via `Authorization: Bearer {token}` header
5. MCP via streamable HTTP or SSE
6. Authenticated `chatPromptComplete`
7. OPAL Agent routing via recognizable function names

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

## MCP

Endpoints:
- `https://linkeddata.uriburner.com/chat/mcp/messages`
- `https://linkeddata.uriburner.com/chat/mcp/sse`

Guidance:
- Treat MCP as requiring authentication unless the client is already configured. See Authentication section above.

## OPAL Agent Routing

Treat OPAL as an agent layer over recognizable tools/functions. Use the canonical Smart Agent function names when the user asks for OPAL-oriented routing:
- `UB.DBA.sparqlQuery`
- `Demo.demo.execute_spasql_query`
- `DB.DBA.graphqlQuery`

Keep authenticated `chatPromptComplete` as a separate routing option after MCP; do not present it as one of the canonical Data Twingler tool names unless the source configuration is updated.
