# RSS Feed Generator Protocol Routing

Use this file only when you need exact execution routing guidance for the page fetch step.

## Default Order

1. `WEB_FETCH` function via URIBurner REST
2. Terminal-owned OAuth flow — when the endpoint requires OAuth 2.0 authentication, execute the OAuth flow from the terminal (authorization code, client credentials, or device flow), capture the Bearer token, and inject via `Authorization: Bearer {token}` header into subsequent REST/OpenAPI calls
3. MCP via streamable HTTP or SSE
4. Authenticated LLM-mediated execution via `chatPromptComplete`
5. OPAL Agent routing via recognizable OPAL function names
6. `bash` (curl/wget) directly against the target URL

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
