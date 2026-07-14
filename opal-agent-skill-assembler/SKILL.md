---
name: opal-agent-skill-assembler
description: "Assemble or exercise OPAL Agents and Skills. Trigger on phrases like 'assemble an agent', 'create an AGENTS.md', 'build a skill', 'exercise an agent', 'test a skill', 'list OPAL agents', 'instantiate an agent', or any request to work with OPAL agents, skills, or function tools."
---

# OPAL Agent & Skill Assembler

Dual-purpose skill for working with OPAL (OpenLink AI Layer) agents, skills, and function tools. Assemble new agent/skill configurations or exercise existing ones against any OPAL endpoint.

## What OPAL Provides

OPAL exposes `/chat/api` on any OPAL-enabled Virtuoso instance. An **Agent** orchestrates one or more **Skills**; a **Skill** bundles one or more **Tools** (functions). See `references/opal-service-surface.md` for the full API surface.

## Elicitation Flow

### 1. OPAL Endpoint

Present these options and ask the user to choose or enter a custom host:

| Shortcut | Host |
|----------|------|
| URIBurner | `linkeddata.uriburner.com` |
| Demo | `demo.openlinksw.com` |
| NetID QA | `netid-qa.openlinksw.com` |
| ODS-QA | `ods-qa.openlinksw.com` |
| Custom | (enter any hostname) |

All endpoints are constructed as `https://{host}/chat/api`, `https://{host}/listAgents`, etc.

### 2. Authentication

Ask the user to choose:
- **OAuth 2.1**: Run Authorization Code flow (see `preferences.ttl` howto for OAuth flow). Use dynamic client registration at `https://{host}/OAuth2/register`, capture code on `localhost:12345/callback`, exchange for Bearer token.
- **API Key**: Prompt user to paste their Bearer token directly.

### 3. Mode

Ask the user to choose:

| Mode | What it does |
|------|-------------|
| **Assemble Agent** | List Skills → select → generate AGENTS.md + JSON → upload to WebDAV |
| **Assemble Skill** | List Tools → select → generate SKILLS.md + JSON → upload to WebDAV |
| **Exercise Agent** | List Agents → select one → instantiate → send test prompt → report |
| **Exercise Skill** | List Skills → select one → instantiate → send test prompt → report |

### 4A. Assemble Mode Details

**Agent Assembly:**
1. `GET https://{host}/listSkills` — fetch available skills
2. Present skills as a multi-select list with their descriptions
3. Ask for: agent ID, title, version, optional model key override
4. Generate AGENTS.md using `prompts/agents-md-template.md`
5. Generate companion `.json` per `references/opal-agent-skill-json-schema.md`
6. Offer to upload both to `https://{host}/DAV/VAD/personal_assistant/json/{agent_id}.json` and `.../md/{agent_id}.md`
7. Provide curl commands for the upload

**Skill Assembly:**
1. `GET https://{host}/listFunctions` — fetch available function tools
2. Present tools as a multi-select list with descriptions
3. Ask for: skill ID, title, version
4. Generate SKILLS.md using `prompts/skills-md-template.md`
5. Generate companion `.json`
6. Offer to upload to WebDAV

### 4B. Exercise Mode Details

**Exercise Agent:**
1. `GET https://{host}/listAgents` — fetch available agents
2. Present as single-select list
3. Ask for optional model API key override and test prompt text (default: "Introduce yourself and your capabilities.")
4. Instantiate: `POST https://{host}/chat/api` with `{"agent": "{selected_id}"}` and the test message
5. Display the response

**Exercise Skill:**
1. `GET https://{host}/listSkills` — fetch available skills
2. Same flow as agent exercise but with `{"skills": ["{selected_id}"]}`

## OAuth Flow Reference

Per `preferences.ttl` howto (`uriburner-oauth-authcode-flow.ttl`):

```bash
# 1. Register client
curl -X POST https://{host}/OAuth2/register \
  -H "Content-Type: application/json" \
  -d '{"client_name":"OPAL Assembler","redirect_uris":["http://localhost:12345/callback"],"grant_types":["authorization_code"],"token_endpoint_auth_method":"none"}'

# 2. Authorize (open browser)
open "https://{host}/OAuth2/authorize?response_type=code&client_id={client_id}&redirect_uri=http://localhost:12345/callback&scope=openid"

# 3. Exchange code for token
curl -X POST https://{host}/OAuth2/token \
  -d "grant_type=authorization_code&code={code}&redirect_uri=http://localhost:12345/callback&client_id={client_id}&client_secret={client_secret}"
```

## WebDAV Upload

```bash
# Upload AGENTS.md / SKILLS.md
curl -X PUT https://{host}/DAV/VAD/personal_assistant/md/{id}.md \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: text/markdown" \
  --data-binary @{local_file}

# Upload JSON companion
curl -X PUT https://{host}/DAV/VAD/personal_assistant/json/{id}.json \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  --data-binary @{local_file}
```

## Verification

After assembly or exercise:
- Assemble: confirm both `.md` and `.json` exist at the WebDAV paths
- Assemble: `GET https://{host}/listAgents` (or `/listSkills`) should include the newly created agent/skill
- Exercise: confirm the instantiated session returns a meaningful response

## References

- `references/opal-service-surface.md` — full OPAL API surface
- `references/opal-agent-skill-json-schema.md` — JSON registration format
- OPAL Playground: `https://linkeddata.uriburner.com/chat/api`
- OAuth howto: `preferences.ttl` → `howto/uriburner-oauth-authcode-flow.ttl`

## License

AGPL-3.0
