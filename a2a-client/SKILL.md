---
name: a2a-client
description: Use OPAL Agent2Agent (A2A) clients against OpenLink OPAL A2A endpoints. Trigger when Codex needs to discover an OPAL Agent Card, authenticate with OAuth2 bearer/API key or client-credentials flow, send A2A JSON-RPC tasks, subscribe to streamed task events, fetch task status, attach files, or test OPAL agents/skills exposed through /.well-known/agent.json and /chat/api/a2a. Present recommended endpoints when helpful, but always elicit the target CNAME/base URL/endpoint and credentials before requests.
---

# OPAL A2A Client

Use this skill to interact with an OPAL backend that implements the Agent2Agent protocol.

## Required Elicitations

Before making any request, obtain these runtime values from the user, environment, or an already verified project config:

- Target endpoint: either an HTTPS base URL such as `https://{CNAME}` or a full A2A URL such as `https://{CNAME}/chat/api/a2a`; CLI args win over `OPAL_A2A_BASE_URL`, `OPAL_A2A_CNAME`, `OPAL_A2A_URL`, and `OPAL_A2A_CARD_URL`.
- Authentication mode: bearer/API key, dynamic OAuth Authorization Code, OAuth2 client credentials, or no request until credentials are supplied.
- Credential source: environment variable name, secret manager reference, dynamic OAuth flow, or user-provided value. The script recognizes `OPAL_A2A_TOKEN_ENV` and `OPAL_A2A_TOKEN`; do not echo secrets.
- Interaction mode: `tasks/send`, `tasks/sendSubscribe`, or `tasks/get`.
- Session behavior: new context/session or continue with a supplied `contextId` or `sessionId`.

Do not silently substitute a default CNAME. Present the recommended endpoints below as choices, accept a custom endpoint, or use a verified override such as `OPAL_A2A_BASE_URL` or `OPAL_A2A_CNAME`.

## Recommended Endpoints

Offer these as non-exclusive choices when the user has not supplied a target:

1. `https://netid-qa.openlinksw.com:8443`
2. `https://linkeddata.uriburner.com`
3. `https://demo.openlinksw.com`

Also offer a custom base URL or full `/chat/api/a2a` endpoint. Do not assume the first endpoint is the default; wait for the user's selection or a verified config/env override.

## Workflow

1. Normalize the target:
   - If the user gives a base URL, fetch the Agent Card from `/.well-known/agent.json` and derive the A2A endpoint from the card's `url` field.
   - If the user gives a full `/chat/api/a2a` URL, derive the Agent Card URL from the same origin unless the user supplies a separate card URL.
2. Fetch and inspect the Agent Card before sending tasks. Confirm name, provider, auth schemes, capabilities, input modes, output modes, and listed `skills`.
3. Authenticate:
   - For bearer/API key, send `Authorization: Bearer {token}`.
   - Prefer bearer tokens via `--token-env`, `OPAL_A2A_TOKEN_ENV`, or `OPAL_A2A_TOKEN` rather than raw `--token`.
   - For interactive OAuth, use dynamic client registration plus Authorization Code flow with `--oauth-auth-code`; register against the selected endpoint's own issuer, not a different host.
   - To reuse an OAuth-acquired bearer token, use `--save-token-env OPAL_A2A_TOKEN --save-token-env-file .opal-a2a.env`, then source the file in a shell you control.
   - For OAuth2 client credentials, use the card's token URL when present, or elicit an explicit token URL.
   - Never log tokens, client secrets, or complete Authorization headers.
4. Choose the task method:
   - Use `tasks/send` for a single request/response task.
   - Use `tasks/sendSubscribe` when the user asks for streaming or the card advertises streaming support and the user chooses it.
   - Use `tasks/get` to check an existing task ID.
5. Build JSON-RPC 2.0 payloads with text parts by default. Include attachments only from user-approved file paths.
6. Preserve returned `task id`, `contextId`, and `sessionId` values. Ask whether to continue the same context when the next request depends on prior task state.
7. Summarize results from `status.message.parts`, `artifacts.parts`, and final task state. Include IDs needed for follow-up, but keep secrets redacted.

## Bundled Resources

- Read `references/opal-a2a.md` when you need protocol details, JSON-RPC payload examples, Agent Card field interpretation, or OPAL-specific behavior.
- Use `scripts/a2a_client.py` for repeatable command-line testing. Run `python3 scripts/a2a_client.py --help` before first use.

## Validation

For skill changes, run:

```bash
python3 scripts/a2a_client.py --help
```

For live endpoint validation, use a user-approved target and credentials, then perform this minimum sequence:

```bash
python3 scripts/a2a_client.py card --agent-base https://{CNAME}
python3 scripts/a2a_client.py send --agent-base https://{CNAME} --token-env OPAL_A2A_TOKEN --message "What is Virtuoso?"
python3 scripts/a2a_client.py send --agent-base https://{CNAME} --oauth-auth-code --message "What is Virtuoso?"
python3 scripts/a2a_client.py send --agent-base https://{CNAME} --oauth-auth-code --save-token-env OPAL_A2A_TOKEN --save-token-env-file .opal-a2a.env --message "What is Virtuoso?"
```

Replace `{CNAME}` and token sources only with elicited values.
