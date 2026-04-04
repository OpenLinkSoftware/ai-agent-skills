# DBpedia Protocol Routing

Use this file only when you need exact execution routing guidance.

## Default Order

1. `curl` directly against DBpedia
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

Use when:
- no protocol preference is stated
- simple DBpedia execution is sufficient
- you want the least moving parts

Pattern:

```bash
curl -s -G "https://dbpedia.org/sparql" \
  --data-urlencode "query=<SPARQL_QUERY>" \
  --data-urlencode "format=json"
```

## REST via URIBurner

Use when:
- the user asks for REST or OpenAI-compatible endpoint execution
- you need execution routed through the URIBurner service
- direct DBpedia `curl` is unavailable or should be avoided

Endpoint:
- `https://linkeddata.uriburner.com/chat/functions/sparqlRemoteQuery`

Parameters:
- `url=https://dbpedia.org/sparql`
- `query=<SPARQL_QUERY>`
- `format=application/sparql-results+json`
- `timeout=<seconds>` when needed

Pattern:

```bash
curl -s -G "https://linkeddata.uriburner.com/chat/functions/sparqlRemoteQuery" \
  --data-urlencode "url=https://dbpedia.org/sparql" \
  --data-urlencode "query=<SPARQL_QUERY>" \
  --data-urlencode "format=application/sparql-results+json"
```

Notes:
- This path was validated against the Christopher Nolan example.
- `chatPromptComplete` is not the default execution route; it may require an API key.

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
- Keep the DBpedia task the same: generate SPARQL first, then submit execution through the MCP tool surface.
- Treat MCP as requiring authentication unless the client is already configured. See Authentication section above.

## chatPromptComplete

Use when:
- the user explicitly asks for OpenAI-compatible or LLM-mediated execution
- you need the model to broker tool selection or function calling
- earlier routes are unavailable and credentials are available

Endpoint:
- `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`

Notes:
- This is part of the routing order and comes after MCP.
- Treat it as requiring authentication unless a valid API key or equivalent OAuth-backed credential is available. See Authentication section above.

## OPAL Agent Routing

Use when:
- the user explicitly asks for OPAL
- the task should be framed as agent routing through named OPAL tools
- recognizable OPAL function names are important to the workflow

Recognizable OPAL functions for this skill:
- `OAI.DBA.sparqlRemoteQuery`
- `OAI.DBA.chatPromptComplete`
- `OAI.DBA.sparqlQuery`

Guidance:
- Treat OPAL as an agent routing layer over tools/functions, not merely another transport.
- For remote DBpedia execution, prefer `OAI.DBA.sparqlRemoteQuery`.
- For authenticated LLM-mediated execution, prefer `OAI.DBA.chatPromptComplete`.
- Use `OAI.DBA.sparqlQuery` only when the data is local to the OPAL/Virtuoso service rather than remote DBpedia.

## Preference Override Examples

- "Use MCP for this DBpedia query" -> use MCP first
- "Route this through the REST endpoint" -> use `sparqlRemoteQuery`
- "Use the OpenAI-compatible route" -> use authenticated `chatPromptComplete`
- "Use OPAL tools for this DBpedia query" -> use OPAL Agent routing and name the OPAL functions explicitly
- "Just hit DBpedia with curl" -> use direct `curl`
