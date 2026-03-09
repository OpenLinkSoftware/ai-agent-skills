# RSS Feed Generator Protocol Routing

Use this file only when you need exact execution routing guidance for the page fetch step.

## Default Order

1. `WEB_FETCH` function via URIBurner REST
2. MCP via streamable HTTP or SSE
3. Authenticated LLM-mediated execution via `chatPromptComplete`
4. OPAL Agent routing via recognizable OPAL function names
5. `bash` (curl/wget) directly against the target URL

If the user explicitly asks for a protocol, honor that request instead of the default order.

## WEB_FETCH via URIBurner REST

Use when:
- fetching the source page to generate a feed from
- no protocol preference is stated

Endpoint:
- `https://linkeddata.uriburner.com/chat/functions/WEB_FETCH`

Parameters:
- `url=<TARGET_URL>` (required)
- `headers=<JSON_HEADERS>` (optional)
- `max_redirects=<n>` (optional)
- `timeout_seconds=<n>` (optional)

`WEB_FETCH` retrieves the page just like a web browser and returns the full page content for subsequent processing.

## MCP

Use when:
- the user explicitly asks for MCP
- the client environment is already configured to speak MCP
- the earlier routes are not appropriate and MCP is available

Endpoints:
- Streamable HTTP: `https://linkeddata.uriburner.com/chat/mcp/messages`
- SSE: `https://linkeddata.uriburner.com/chat/mcp/sse`

Guidance:
- Prefer streamable HTTP unless the client specifically expects SSE.
- Treat MCP as requiring authentication unless the client is already configured.

## chatPromptComplete

Use when:
- the user explicitly asks for OpenAI-compatible or LLM-mediated execution
- earlier routes are unavailable and credentials are available

Endpoint:
- `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`

Notes:
- Treat as requiring authentication unless a valid API key or OAuth-backed credential is available.

## OPAL Agent Routing

Use when:
- the user explicitly asks for OPAL
- the task should be framed as agent routing through named OPAL tools

Recognizable OPAL functions for this skill:
- `OAI.DBA.WEB_FETCH`
- `OAI.DBA.chatPromptComplete`

## Direct bash (curl/wget)

Use as a last resort when none of the above are available.

```bash
curl -s -L "<TARGET_URL>" -A "Mozilla/5.0"
```

## Preference Override Examples

- "Use MCP to fetch the page" → use MCP first
- "Route through the REST endpoint" → use `WEB_FETCH` via REST
- "Use the OpenAI-compatible route" → use authenticated `chatPromptComplete`
- "Use OPAL tools" → use OPAL Agent routing and name the OPAL functions explicitly
- "Just curl the page" → use direct `bash` curl
