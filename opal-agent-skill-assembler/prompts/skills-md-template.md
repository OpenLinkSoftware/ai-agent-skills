# Skill Assembly Prompt

Generate a SKILLS.md document for an OPAL skill that orchestrates the selected function tools.

## Selected Tools
{tools_list}

## Configuration
- **Skill ID**: {skill_id}
- **Skill Title**: {skill_title}
- **Version**: {version}
- **Model**: {model}
- **Endpoint**: {endpoint}
- **WebDAV Base**: {webdav_base}

## Output Template

```markdown
# Skill: {skill_title}

**ID**: `{skill_id}`
**Version**: {version}
**Endpoint**: {endpoint}
**Model**: {model}
**Created**: {date}

## Description

{description}

## Tools

{tools_table}

## Usage

To exercise this skill via the OPAL API:

```bash
curl -X POST {endpoint}/chat/api \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"skills": ["{skill_id}"], "message": "Your test prompt here"}'
```

## JSON Registration

Stored at `{webdav_base}/{skill_id}.json`
```

Also generate the companion JSON file per `references/opal-agent-skill-json-schema.md`.
