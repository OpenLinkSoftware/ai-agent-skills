# Wikidata Protocol Routing

Use this file only when you need exact execution routing guidance.

## Default Order

1. `curl` directly against Wikidata
2. URIBurner REST via `sparqlRemoteQuery`
3. MCP via streamable HTTP or SSE
4. Authenticated LLM-mediated execution via `chatPromptComplete`
5. OPAL Agent routing via recognizable OPAL function names

If the user explicitly asks for a protocol, honor that request instead of the default order.

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

## MCP

Endpoints:
- Streamable HTTP: `https://linkeddata.uriburner.com/chat/mcp/messages`
- SSE: `https://linkeddata.uriburner.com/chat/mcp/sse`

Guidance:
- Treat MCP as requiring authentication unless the client is already configured.
- From this environment, both MCP endpoints returned `401 Unauthorized` on March 6, 2026.

## chatPromptComplete

Endpoint:
- `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`

Guidance:
- Use for authenticated LLM-mediated execution.
- From this environment, unauthenticated calls failed on March 6, 2026 because no API key was supplied.

## OPAL Agent Routing

Recognizable OPAL functions for this skill:
- `OAI.DBA.sparqlRemoteQuery`
- `OAI.DBA.chatPromptComplete`
- `OAI.DBA.sparqlQuery`
