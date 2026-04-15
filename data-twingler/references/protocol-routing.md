# Data Twingler Protocol Routing

Use this file only when you need execution routing guidance beyond the main skill instructions.

## Default Order

1. Direct native execution such as `curl` to the target endpoint
   - 1a. Plain `curl` for open or OAuth-protected endpoints
   - 1b. **mTLS `curl`** — when the resource server requires a client certificate (see mTLS section below)
2. URIBurner REST functions
3. Terminal-owned OAuth flow — authenticate via OAuth 2.0 from the terminal to enable authenticated REST/OpenAPI calls; obtain a Bearer token and inject via `Authorization: Bearer {token}` header
4. MCP via streamable HTTP or SSE
5. Authenticated `chatPromptComplete`
6. OPAL Agent routing via recognizable function names

---

## mTLS curl Variant (Step 1b)

Use this variant whenever a resource server requires **Mutual TLS** — i.e., the server demands a client certificate in addition to (or instead of) a Bearer token.

### Trigger conditions

- User mentions a PKCS#12 file, `.p12`, `.pfx`, mTLS, or client certificate
- Endpoint returns HTTP 495 (SSL Certificate Error), 496 (SSL Certificate Required), or a TLS handshake error
- The target resource is known to be protected by WebID-TLS or an mTLS gateway

### Command pattern

```bash
curl -iLk \
  --cert-type P12 \
  --cert "{pkcs12-file}:${MTLS_PWD}" \
  "{endpoint-url}"
```

Replace `-k` with `--cacert {ca-bundle}` when a trusted CA bundle is available.

### SPARQL endpoint with client cert

```bash
curl -iLk \
  --cert-type P12 \
  --cert "{pkcs12-file}:${MTLS_PWD}" \
  -H "Accept: application/sparql-results+json" \
  "{sparql-endpoint}?query={url-encoded-sparql}"
```

### Combining mTLS with Bearer token

Some endpoints require both a client certificate and a Bearer token:

```bash
curl -iLk \
  --cert-type P12 \
  --cert "{pkcs12-file}:${MTLS_PWD}" \
  -H "Authorization: Bearer {token}" \
  "{endpoint-url}"
```

In this case run step 3 (OAuth flow) first to obtain the token, then inject both credentials.

### PKCS#12 elicitation

If the PKCS#12 file path or password is not already known, elicit them
interactively using masked input — never log or echo the password:

```bash
read -s -p "PKCS#12 password: " MTLS_PWD; echo
```

Full elicitation and validation logic: load the `mtls-curl` skill.

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
