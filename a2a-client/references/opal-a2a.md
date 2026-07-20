# OPAL Agent2Agent Client Reference

## Runtime Shape

OPAL exposes one A2A Agent Card at:

```text
https://{CNAME}/.well-known/agent.json
```

The default A2A JSON-RPC endpoint path is:

```text
https://{CNAME}/chat/api/a2a
```

Treat `{CNAME}` as a runtime variable. Do not silently choose a hostname unless the user supplied it for that run or it came from a verified config/env override.

## Recommended Endpoint Menu

When the user has not supplied a target, present this menu and elicit a selection:

1. `https://netid-qa.openlinksw.com:8443`
2. `https://linkeddata.uriburner.com`
3. `https://demo.openlinksw.com`
4. Custom base URL or full A2A endpoint

These are recommended endpoints, not ordered failover defaults. Use exactly the selected or configured endpoint for Agent Card discovery and A2A requests.


## Environment Overrides

The bundled client accepts explicit CLI arguments first, then these environment overrides:

- `OPAL_A2A_BASE_URL`: base URL such as `https://{CNAME}`.
- `OPAL_A2A_CNAME`: CNAME or URL; bare CNAMEs are expanded to `https://{CNAME}`.
- `OPAL_A2A_URL`: full `/chat/api/a2a` endpoint.
- `OPAL_A2A_CARD_URL`: explicit Agent Card URL.
- `OPAL_A2A_TOKEN_ENV`: name of the environment variable containing the bearer token.
- `OPAL_A2A_TOKEN`: bearer token value. Do not print it.

These overrides are configuration bindings, not built-in defaults.

Bearer token examples:

```bash
OPAL_A2A_TOKEN=... python3 scripts/a2a_client.py send \
  --agent-base https://{CNAME} \
  --message "What is Virtuoso?"

MY_OPAL_TOKEN=... python3 scripts/a2a_client.py send \
  --agent-base https://{CNAME} \
  --token-env MY_OPAL_TOKEN \
  --message "What is Virtuoso?"
```

## Dynamic OAuth Command

Use this when the user wants the client to obtain the client id and client secret dynamically:

```bash
python3 scripts/a2a_client.py send \
  --agent-base https://{CNAME} \
  --oauth-auth-code \
  --message "What is Virtuoso?"
```

The script discovers `https://{CNAME}/.well-known/openid-configuration`, registers a public client with `http://localhost:12345/callback`, prints the authorization URL, waits for the callback, exchanges the code for a bearer token, and sends the A2A task. Add `--open-browser` only when the runtime may open a browser.

Useful overrides:

- `--oauth-issuer https://{CNAME}` when the OAuth issuer differs from the A2A base URL.
- `--redirect-uri http://localhost:{PORT}/callback` if port 12345 is unavailable.
- `--scope "openid webid"` to adjust scopes.

To capture the OAuth bearer token for reuse, opt in explicitly:

```bash
python3 scripts/a2a_client.py send \
  --agent-base https://{CNAME} \
  --oauth-auth-code \
  --save-token-env OPAL_A2A_TOKEN \
  --save-token-env-file .opal-a2a.env \
  --message "What is Virtuoso?"

source .opal-a2a.env
python3 scripts/a2a_client.py send \
  --agent-base https://{CNAME} \
  --message "What is UDA?"
```

The env file is written with mode `0600` when the platform permits it. Do not commit it.

## Agent Card Fields

Expected OPAL card fields include:

- `name`: usually `OPAL Agent`.
- `description`: OpenLink AI Layer description.
- `url`: canonical JSON-RPC endpoint.
- `provider.organization`: OpenLink Software.
- `authentication.schemes`: commonly `OAuth2`.
- `authentication.credentials`: JSON string that may contain `authorizationUrl`, `tokenUrl`, and `scopes`.
- `capabilities.streaming`: whether streaming is advertised.
- `capabilities.pushNotifications`: whether push notifications are advertised.
- `skills`: OPAL assistant/agent configurations exposed as A2A skills.

The A2A client cannot designate the OPAL skill explicitly through `tasks/send`. OPAL chooses or continues an assistant configuration based on the user prompt, listed skills, and context/session continuity.

## Authentication

OPAL A2A requests normally require OAuth2 authorization. Supported client patterns:

- Bearer/API key supplied directly.
- Bearer/API key read from an environment variable.
- Dynamic OAuth Authorization Code flow: discover OIDC metadata from the selected endpoint, register a local CLI client, open or print the authorization URL, capture the localhost callback, exchange the code for an access token, then use it as Bearer.
- OAuth2 client credentials grant using `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET`, plus either the Agent Card token URL or an elicited token URL.

Do not print credentials. Redact Authorization headers in logs.

The token issuer must match the A2A resource server. A token issued by a different OpenLink host may be rejected by the selected OPAL endpoint.

## JSON-RPC Methods

Supported methods from the source design:

- `tasks/send`
- `tasks/sendSubscribe`
- `tasks/get`

Methods noted as TBD:

- `tasks/cancel`
- `tasks/pushNotification/get`
- `tasks/pushNotification/set`
- `tasks/resubscribe`

## Payload Notes

Use JSON-RPC 2.0. A text request should include a message with role `user` and a text part. OPAL deployments or SDK versions may use either `type: "text"` or `kind: "text"` in returned parts; parse both.

Typical send request shape:

```json
{
  "jsonrpc": "2.0",
  "id": "{request-id}",
  "method": "tasks/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "{prompt}"
        }
      ]
    }
  }
}
```

When continuing a session or context, include the returned context/session identifier only when the endpoint supports that field and the user wants continuity.

## Result Extraction

Look for answer text in these places:

- `result.status.message.parts[*].text`
- `result.artifacts[*].parts[*].text`
- Stream events containing `artifact`, `status`, `message`, or `parts`.

Preserve and report:

- task `id`
- `contextId`
- `sessionId`
- final `status.state`

## OPAL Session Behavior

A new A2A session can group related tasks. The first task may route the prompt to an OPAL assistant/skill. Later tasks can reuse context, so "Ditto" or similar shorthand may depend on the previous selected assistant.

For a new session, elicit whether to clear prior context. For a follow-up, include the returned context/session identifier when the endpoint and client support it.
