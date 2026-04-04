# Wikidata Protocol Routing

Use this file only when you need exact execution routing guidance.

## Default Order

1. `curl` directly against Wikidata
2. URIBurner REST via `sparqlRemoteQuery`
3. Terminal-owned OAuth flow — authenticate via OAuth 2.0 from the terminal to enable authenticated REST/OpenAPI calls; obtain a Bearer token and inject via `Authorization: Bearer {token}` header
4. MCP via streamable HTTP or SSE
5. Authenticated LLM-mediated execution via `chatPromptComplete`
6. OPAL Agent routing via recognizable OPAL function names

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

## Direct curl

Pattern:

```bash
curl -s -G "https://query.wikidata.org/sparql" \
  -H "Accept: application/sparql-results+json" \
  -H "User-Agent: Claude-Code-Wikidata-Skill/1.0" \
  --data-urlencode "query=<SPARQL_QUERY>"
```

## REST via URIBurner

Endpoint:
- `https://linkeddata.uriburner.com/chat/functions/sparqlRemoteQuery`

Parameters:
- `url=https://query.wikidata.org/sparql`
- `query=<SPARQL_QUERY>`
- `format=application/sparql-results+json`

## Terminal-owned OAuth Flow

Use when the REST or OpenAPI endpoint requires OAuth 2.0 authentication before accepting requests.

**When to use:** REST call returns 401/403/500, or the user explicitly requests authenticated access before any REST call is attempted.

**Steps:**
1. Identify the OAuth 2.0 grant type: authorization code (user-facing), client credentials (service-to-service), or device flow (terminal-friendly)
2. Execute the OAuth flow from the terminal using `curl` or the agent's built-in OAuth tooling
3. Capture the returned Bearer token
4. Inject the token into subsequent REST/OpenAPI calls: `Authorization: Bearer {token}`

**Terminal-friendly pattern (device flow or client credentials):**
```bash
# Client credentials example
curl -s -X POST "https://{auth-server}/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id={id}&client_secret={secret}&scope={scope}"
# Then use token:
curl -s -G "https://linkeddata.uriburner.com/chat/functions/sparqlRemoteQuery" \
  -H "Authorization: Bearer {token}" \
  --data-urlencode "url=https://query.wikidata.org/sparql" \
  --data-urlencode "query=<SPARQL_QUERY>"
```

## MCP

Endpoints:
- Streamable HTTP: `https://linkeddata.uriburner.com/chat/mcp/messages`
- SSE: `https://linkeddata.uriburner.com/chat/mcp/sse`

Guidance:
- Treat MCP as requiring authentication unless the client is already configured. See Authentication section above.

## chatPromptComplete

Endpoint:
- `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`

Guidance:
- Use for authenticated LLM-mediated execution.
- See Authentication section above.

## OPAL Agent Routing

Recognizable OPAL functions for this skill:
- `OAI.DBA.sparqlRemoteQuery`
- `OAI.DBA.chatPromptComplete`
- `OAI.DBA.sparqlQuery`
