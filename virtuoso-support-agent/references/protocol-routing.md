# Protocol Routing - Virtuoso Support Agent

Covers execution modalities and environment-specific guidance for invoking the 25 available tools.

---

## Invocation Modalities

The tools in this skill can be invoked through any of the following modalities. Choose based on what the host environment supports.

### 1. MCP (Model Context Protocol) — Primary

Use when the host environment is MCP-enabled (e.g., Claude Code, MCP-compatible agent frameworks).

Endpoints:
- Streamable HTTP (preferred): `https://demo.openlinksw.com/chat/mcp/messages` (Demo instance)
- Streamable HTTP (preferred): `https://linkeddata.uriburner.com/chat/mcp/messages` (URIBurner)
- SSE: `https://linkeddata.uriburner.com/chat/mcp/sse` (URIBurner)
- Streamable HTTP: `http://localhost:{port}/chat/mcp/messages` (Localhost — confirm port with user; default 8890)

Tool naming convention: `{ServerName}:{ToolName}`
- `Demo:execute_spasql_query`
- `URIBurner:sparqlQuery`
- `Localhost:sparqlQuery`

All 25 tools are available via MCP on Demo, URIBurner, and Localhost servers.

Guidance:
- Prefer streamable HTTP unless the client specifically expects SSE.
- Treat MCP as requiring authentication unless the client is already configured. See Authentication section below.

---

### 2. URIBurner REST Functions

Use when the host environment supports HTTP REST calls but not MCP, or when a specific function is more naturally called as a REST endpoint.

Base URL: `https://linkeddata.uriburner.com/chat/functions/`

Key function endpoints:

| Function | Endpoint |
|---|---|
| SPASQL query | `/execute_spasql_query` |
| SQL query | `/execute_sql_query` |
| SPARQL (local) | `/sparqlQuery` |
| SPARQL (remote) | `/sparqlRemoteQuery` |
| GraphQL | `/graphqlQuery` |
| Web fetch | `/WEB_FETCH` |
| RDF sponge/extract | `/SPONGE_URL` |
| LLM completion | `/chatPromptComplete` |

Full OpenAPI spec: `https://linkeddata.uriburner.com/chat/functions/openapi.yaml`

Guidance:
- REST calls use GET with URL-encoded parameters unless the spec specifies POST.
- Equivalent to MCP tool calls for query execution and utility functions.
- RDF Views generation tools (`RDFVIEW_FROM_TABLES`, etc.) are MCP-only; use REST query functions for validation steps.

---

### 3. Terminal-owned OAuth Flow

Use when REST or OpenAPI endpoints require OAuth 2.0 authentication before accepting requests. This modality sits above MCP in the routing order so that authenticated REST calls can be established from the terminal without depending on the MCP client's OAuth mechanism.

**When to use:**
- REST call returns 401, 403, or unexpected 500
- User explicitly requests authenticated access before any call is attempted
- MCP client OAuth is not available or not yet configured

**Steps:**
1. Identify the OAuth 2.0 grant type: authorization code (user-facing), client credentials (service-to-service), or device flow (terminal-friendly)
2. Execute the OAuth flow from the terminal using `curl` or the agent's built-in OAuth tooling
3. Capture the returned Bearer token
4. Inject the token into subsequent REST/OpenAPI calls: `Authorization: Bearer {token}`

**Terminal-friendly pattern (client credentials):**
```bash
curl -s -X POST "https://{auth-server}/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id={id}&client_secret={secret}&scope={scope}"
# Use returned access_token in subsequent REST calls:
curl -s -G "https://linkeddata.uriburner.com/chat/functions/execute_spasql_query" \
  -H "Authorization: Bearer {token}" \
  --data-urlencode "sql=SPARQL SELECT * WHERE { ?s ?p ?o } LIMIT 10"
```

---

### 4. OPAL Agent Routing

Use when the host environment is an OPAL-enabled agent, or when the user explicitly asks for OPAL routing.

Canonical OPAL-recognizable function names:

| Category | OPAL Function |
|---|---|
| SPASQL | `Demo.demo.execute_spasql_query` |
| SQL | `Demo.demo.execute_sql_query` |
| SPARQL (local) | `UB.DBA.sparqlQuery` |
| SPARQL (remote) | `OAI.DBA.sparqlRemoteQuery` |
| GraphQL | `DB.DBA.graphqlQuery` |
| LLM completion | `OAI.DBA.chatPromptComplete` |

Guidance:
- OPAL is an agent routing layer over named functions, not merely a transport.
- Use qualified function names (catalog.schema.function) when routing through OPAL.
- Server selection (Demo vs URIBurner) is expressed through the function qualifier, not a prefix.

---

### 5. OpenAI-Compatible API (chatPromptComplete)

Use when the host environment supports OpenAI-compatible function/tool calling, or when LLM-mediated execution is needed.

Endpoint: `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`

Also available via the Chat API:
Full OpenAPI spec: `https://linkeddata.uriburner.com/chat/api/openapi.yaml`

Guidance:
- Requires a valid API key or OAuth-backed credential.
- Use for complex multi-step reasoning tasks or when agent orchestration is needed.
- See Authentication section below.

---

### 6. Direct curl (Query Execution Only)

Use as a fallback for query execution when no other modality is available. Not applicable to RDF Views generation or database management tools.

SPASQL:
```bash
curl -s -G "https://linkeddata.uriburner.com/chat/functions/execute_spasql_query" \
  --data-urlencode "sql=SPARQL SELECT * WHERE { ?s ?p ?o } LIMIT 10" \
  --data-urlencode "format=json"
```

SPARQL (local):
```bash
curl -s -G "https://linkeddata.uriburner.com/chat/functions/sparqlQuery" \
  --data-urlencode "query=SELECT * WHERE { ?s ?p ?o } LIMIT 10" \
  --data-urlencode "format=json"
```

#### 6a. mTLS curl Variant — Protected Resources

Use this variant when the resource server requires a client certificate (Mutual
TLS) rather than, or in addition to, a Bearer token.

**Trigger conditions:**
- User supplies or mentions a PKCS#12 file (`.p12`, `.pfx`), mTLS, or client certificate
- Endpoint returns HTTP 495 (SSL Certificate Error), 496 (SSL Certificate Required), or a TLS handshake error
- The target SPARQL endpoint or REST resource is known to enforce WebID-TLS

**SPARQL endpoint with mTLS:**
```bash
curl -iLk \
  --cert-type P12 \
  --cert "{pkcs12-file}:${MTLS_PWD}" \
  -H "Accept: application/sparql-results+json" \
  "{sparql-endpoint}?query={url-encoded-sparql}"
```

**SPASQL / REST function with mTLS:**
```bash
curl -s -G "https://{host}/chat/functions/execute_spasql_query" \
  --cert-type P12 \
  --cert "{pkcs12-file}:${MTLS_PWD}" \
  --data-urlencode "sql=SPARQL SELECT * WHERE { ?s ?p ?o } LIMIT 10" \
  --data-urlencode "format=json"
```

**mTLS + Bearer token combined** (some endpoints require both):
```bash
curl -iLk \
  --cert-type P12 \
  --cert "{pkcs12-file}:${MTLS_PWD}" \
  -H "Authorization: Bearer {token}" \
  "{endpoint-url}"
```

Replace `-k` with `--cacert {ca-bundle}` when a trusted CA bundle is available.

**PKCS#12 elicitation:** If the file path or password are not already known, collect
the password with `read -s` (masked input — never log or echo it). Full elicitation,
CA bundle auto-detection, and bundle validation logic: load the `mtls-curl` skill.

---

### 7. iSQL mTLS + WebID (Virtuoso SQL Sessions)

Use when the user needs an **interactive or batch SQL session** against a
Virtuoso instance that is protected by Mutual TLS and WebID-based access control.
This is distinct from HTTP/SPARQL access — it opens a direct Virtuoso protocol
connection on port 1111 (or the configured iSQL port) with identity asserted via
a WebID URI.

**Trigger conditions:**
- User mentions iSQL, Virtuoso SQL session, port 1111, or the `-X`/`-T`/`-W` flag syntax
- Endpoint returns `Cannot login` or TLS errors from the `isql` client
- User wants to run SQL, SPASQL, or administrative commands against a cert-protected Virtuoso instance

**Command pattern:**
```
isql {host}:{port} "" {pkcs12-pwd} -X {pkcs12-file} -T {ca-bundle} -W {user-webid}
```

**Argument reference:**

| Position / Flag | Value | Notes |
|-----------------|-------|-------|
| `{host}:{port}` | e.g., `localhost:1111` | Connection target; default port 1111 |
| `""` | empty string | Username **must be empty** — signals cert/WebID auth, not SQL-layer auth |
| `{pkcs12-pwd}` | password | Third positional; use a shell variable, never a literal |
| `-X {pkcs12-file}` | path to `.p12`/`.pfx` | Client cert bundle for TLS handshake |
| `-T {ca-bundle}` | path to CA cert file | Server certificate verification |
| `-W {user-webid}` | WebID URI | Identity asserted after TLS — must match a key in the server's VAL ACL graph |

**Interactive session example:**
```bash
read -s -p "PKCS#12 password: " MTLS_PWD; echo
isql "localhost:1111" "" "${MTLS_PWD}" \
  -X "${MTLS_PKCS12_FILE}" \
  -T "${MTLS_CA_BUNDLE}" \
  -W "${MTLS_WEBID}"
```

After connecting, run `SELECT USER;` to confirm the WebID identity is active.

**Batch / non-interactive:**
```bash
echo "SPARQL SELECT * WHERE { ?s ?p ?o } LIMIT 10;" \
  | isql "{host}:{port}" "" "${MTLS_PWD}" \
      -X "{pkcs12-file}" -T "{ca-bundle}" -W "{user-webid}"
```

**Security note:** The password is a positional argument and is briefly visible
in `ps` output. Always pass it via a shell variable rather than a literal string,
and never persist it to environment or history.

**Virtuoso's `isql` vs unixODBC's `isql`:** Only Virtuoso's binary supports the
`-X`/`-T`/`-W` flags. If both are on PATH, prefer `isql-v` (Virtuoso):
```bash
which isql-v isql 2>/dev/null
```

Full elicitation, CA bundle auto-detection, WebID extraction from SAN, and
troubleshooting: load the `mtls-curl` skill.

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
- User explicitly asks to authenticate or switch accounts

Do not retry a failed call more than once before triggering the OAuth flow.

---

## Environment Reference

| Environment | Recommended Modality |
|---|---|
| Claude Code (MCP-enabled) | Terminal-owned OAuth flow → REST, then MCP |
| REST/HTTP client | URIBurner REST Functions + Terminal-owned OAuth flow |
| OPAL agent | OPAL Agent Routing |
| OpenAI-compatible client | chatPromptComplete |
| CLI / scripting | Terminal-owned OAuth flow → Direct curl |
| mTLS-protected HTTP/SPARQL endpoint | mTLS curl variant (§6a) — PKCS#12 + optional Bearer token |
| mTLS-protected Virtuoso SQL session | iSQL mTLS + WebID (§7) — PKCS#12 + CA bundle + WebID URI |

---

## Instance Selection and Routing

All modalities support both Virtuoso instances. Confirm the target instance before any operation:

| Instance | MCP Prefix | OPAL Qualifier | REST Base |
|---|---|---|---|
| Demo | `Demo:` | `Demo.demo.` | `https://demo.openlinksw.com/chat/functions/` |
| URIBurner | `URIBurner:` | `UB.DBA.` / `OAI.DBA.` | `https://linkeddata.uriburner.com/chat/functions/` |
| Localhost | `Localhost:` | `localhost.` | `http://localhost:{port}/chat/functions/` |

---

## Preference Override

If the user explicitly names a modality, honor it:
- "Use MCP" → MCP with `{ServerName}:{ToolName}`
- "Use REST" → URIBurner REST Functions
- "Use OPAL" → OPAL Agent Routing with canonical function names
- "Use the OpenAI-compatible route" → `chatPromptComplete`
- "Just use curl" → Direct curl (query execution only)
- "Use mTLS curl" / "use my cert" / "use my P12" → mTLS curl variant (§6a)
- "Use iSQL" / "open a SQL session" / "use my agent cert for SQL" → iSQL mTLS + WebID (§7)
