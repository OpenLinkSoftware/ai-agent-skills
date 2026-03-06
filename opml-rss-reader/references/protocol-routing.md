# OPML and RSS Reader Protocol Routing

Use this file only when you need execution routing guidance beyond the main skill instructions.

## Default Order

1. Direct native execution such as `curl` to the relevant feed or query endpoint
2. URIBurner REST function execution
3. MCP via streamable HTTP or SSE
4. Authenticated `chatPromptComplete`
5. OPAL Agent routing via canonical function names

If the user explicitly asks for a protocol, honor that request instead of the default order.

## Canonical OPAL Function Name

From the Smart Agent definition, the canonical OPAL-recognizable function name is:
- `Demo.demo.execute_spasql_query`

Use this name when the user asks for OPAL-oriented routing.

## MCP

Endpoints:
- `https://linkeddata.uriburner.com/chat/mcp/messages`
- `https://linkeddata.uriburner.com/chat/mcp/sse`

Guidance:
- Treat MCP as requiring authentication unless the client is already configured.
- From this environment, both MCP endpoints returned `401 Unauthorized` on March 6, 2026.

## chatPromptComplete

Guidance:
- Keep authenticated `chatPromptComplete` as a separate routing option after MCP.
- From this environment, unauthenticated calls failed on March 6, 2026 because no API key was supplied.
