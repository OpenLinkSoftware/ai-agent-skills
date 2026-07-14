# Agent Assembly Prompt

Generate an AGENTS.md document for an OPAL agent that orchestrates the selected skills.

## Selected Skills
{skills_list}

## Configuration
- **Agent ID**: {agent_id}
- **Agent Title**: {agent_title}
- **Version**: {version}
- **Model**: {model}
- **Endpoint**: {endpoint}
- **WebDAV Base**: {webdav_base}

## Output Template

```markdown
# Agent: {agent_title}

**ID**: `{agent_id}`
**Version**: {version}
**Endpoint**: {endpoint}
**Model**: {model}
**Created**: {date}

## Description

{description}

## Skills

{skills_table}

## Usage

To exercise this agent via the OPAL API:

```bash
curl -X POST {endpoint}/chat/api \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"agent": "{agent_id}", "message": "Your test prompt here"}'
```

## JSON Registration

Stored at `{webdav_base}/{agent_id}.json`
```

Also generate the companion JSON file per `references/opal-agent-skill-json-schema.md`.
