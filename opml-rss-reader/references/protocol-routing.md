# OPML and RSS Reader Protocol Routing

Use this file only when you need execution routing guidance beyond the main skill instructions.

## Default Order

1. Direct native execution such as `curl` to the relevant feed or query endpoint
2. URIBurner REST function execution
3. Terminal-owned OAuth flow — authenticate via OAuth 2.0 from the terminal to enable authenticated REST/OpenAPI calls; obtain a Bearer token and inject via `Authorization: Bearer {token}` header
4. MCP via streamable HTTP or SSE
5. Authenticated `chatPromptComplete`
6. OPAL Agent routing via canonical function names

If the user explicitly asks for a protocol, honor that request instead of the default order.

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

## Canonical OPAL Function Name

From the Smart Agent definition, the canonical OPAL-recognizable function name is:
- `Demo.demo.execute_spasql_query`

Use this name when the user asks for OPAL-oriented routing.

## MCP

Endpoints:
- `https://linkeddata.uriburner.com/chat/mcp/messages`
- `https://linkeddata.uriburner.com/chat/mcp/sse`

Guidance:
- Treat MCP as requiring authentication unless the client is already configured. See Authentication section above.

## chatPromptComplete

Guidance:
- Keep authenticated `chatPromptComplete` as a separate routing option after MCP. See Authentication section above.
