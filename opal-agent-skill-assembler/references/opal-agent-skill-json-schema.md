# OPAL Agent/Skill JSON Registration Format

## Agent JSON

```json
{
  "id": "my-agent",
  "title": "My Agent",
  "version": "1.0.0",
  "description": "An agent that orchestrates skills for data analysis",
  "skills": ["data-twingler-config", "virtuoso-support-assistant-config"],
  "model": "gpt-5",
  "modelApiKey": "",
  "enabled": true
}
```

## Skill JSON

```json
{
  "id": "my-skill",
  "title": "My Skill", 
  "version": "1.0.0",
  "description": "A skill that bundles SQL and SPARQL tools",
  "functions": [
    {"function": "Demo.demo.execute_sql_query"},
    {"function": "UB.DBA.sparqlQuery"}
  ],
  "model": "gpt-5",
  "modelApiKey": "",
  "enabled": true
}
```

## WebDAV Storage Paths

Agent JSON: `https://{host}/DAV/VAD/personal_assistant/json/{agent_id}.json`
Agent MD:   `https://{host}/DAV/VAD/personal_assistant/md/{agent_id}.md`
Skill JSON: `https://{host}/DAV/VAD/personal_assistant/json/{skill_id}.json`
Skill MD:   `https://{host}/DAV/VAD/personal_assistant/md/{skill_id}.md`
