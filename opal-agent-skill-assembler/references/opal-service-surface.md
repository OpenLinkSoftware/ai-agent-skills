# OPAL Service Surface Reference

## Core Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat/api` | POST | Main chat completion endpoint |
| `/chat/api/openapi.yaml` | GET | OpenAPI spec for chat API |
| `/chat/functions/openapi.yaml` | GET | OpenAPI spec for functions/tools |
| `/listAgents` | GET | List available agents |
| `/listSkills` | GET | List available skills |
| `/listFunctions` | GET | List available function tools |
| `/chat/mcp/messages` | POST | MCP streamable HTTP endpoint |
| `/chat/mcp/sse` | GET | MCP Server-Sent Events endpoint |

## Agent/Skill Storage (WebDAV)

Agents and skills are stored as `.json` + `.md` pairs in WebDAV:
- `https://{host}/DAV/VAD/personal_assistant/json/` — JSON definitions
- `https://{host}/DAV/VAD/personal_assistant/md/` — Markdown docs

## Authentication

| Method | How |
|--------|-----|
| API Key | `Authorization: Bearer {key}` header |
| OAuth 2.1 | Authorization Code flow via `https://{host}/OAuth2/` |

## Session Flow

1. `GET /listAgents` (or /listSkills, /listFunctions) — discover what's available
2. Choose agent or skill, instantiate: `POST /chat/api` with `agent` or `skills` in body
3. Bind functions: `POST /chat/api` with `functions` array
4. Send prompts to the instantiated session
5. Create new: PUT agent/skill JSON + MD to WebDAV

## Known OPAL Instances

| Instance | Host |
|----------|------|
| URIBurner | `linkeddata.uriburner.com` |
| Demo | `demo.openlinksw.com` |
| NetID QA | `netid-qa.openlinksw.com` |
| ODS-QA | `ods-qa.openlinksw.com` |
