# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

A collection of reusable AI agent skills, each packaged as a directory + ZIP bundle. Skills encapsulate domain-specific execution knowledge for querying semantic web data sources, knowledge graphs, and databases — primarily in the OpenLink/Virtuoso/URIBurner ecosystem.

## Repository Structure

Each skill lives in its own directory with a corresponding `.zip` bundle:

```
<skill-name>/         # Skill source directory
  SKILL.md            # Primary skill definition — capabilities, routing rules, query templates
  README.md           # (optional) Quick-start guide
  CHANGELOG.md        # (optional) Version history
  examples/           # (optional) Sample queries and worked examples
  references/         # (optional) Query templates, protocol routing, extraction rules
  templates/          # (optional) HTML output templates
<skill-name>.zip      # Distributable bundle
```

**No build system, package manager, or test runner.** Skills are loaded directly into AI agent environments as-is.

## Skill Architecture

### SKILL.md Structure
Every SKILL.md defines:
1. **Metadata** — name, version, description
2. **Execution routing** (priority order): direct curl → URIBurner REST functions → MCP tools → chatPromptComplete (LLM-mediated) → OPAL Agent
3. **Query templates** — numbered (P1–P4, T1–T7, etc.) matched to trigger phrases with substitutable placeholders
4. **Output formats** — JSON, Markdown tables, or styled HTML pages

### Protocol Functions Referenced by Skills
- `Demo.demo.execute_spasql_query` — SPASQL execution (SQL + SPARQL hybrid)
- `UB.DBA.sparqlQuery` — Pure SPARQL against URIBurner
- `DB.DBA.graphqlQuery` — GraphQL against Virtuoso
- MCP tools (23 for virtuoso-support-agent, others for uriburner-opal-agent-skills)

### Authoritative Function/Procedure References
When adding or updating function references in any skill, consult these OpenAPI specs first:
- **Chat API:** https://linkeddata.uriburner.com/chat/api/openapi.yaml
- **Functions/Procedures API:** https://linkeddata.uriburner.com/chat/functions/openapi.yaml

### Key Routing Principle
Skills specify a fallback hierarchy. If a user explicitly names a protocol (e.g., "use MCP"), honor that preference over defaults.

## Skills in This Repo

| Skill | Purpose |
|-------|---------|
| `dbpedia-query-skill` | Natural language → SPARQL → DBpedia knowledge graph |
| `wikidata-query-skill` | Natural language → SPARQL → Wikidata knowledge base |
| `data-twingler` | SQL/SPARQL/SPASQL/SPARQL-FED/GraphQL against live data spaces |
| `opml-rss-reader` | Explore OPML/RSS/Atom feeds via predefined SPASQL queries |
| `rss-feed-generator` | Generate RSS 2.0 / Atom 1.0 feeds from pages lacking native feeds |
| `virtuoso-support-agent` | Technical support + RDF Views generation for OpenLink Virtuoso |
| `uriburner-opal-agent-skills` | URIBurner toolkit with SPARQL Agent 121 + OPAL routing |

## Adding or Updating a Skill

1. Create or edit the skill directory and its `SKILL.md`
2. Update version metadata and CHANGELOG.md if applicable
3. **Always repackage the ZIP after any change** — delete first, then recreate:
   `rm <skill-name>.zip && zip -r <skill-name>.zip <skill-name>/ -x "*.DS_Store"`
   Deleting first is required: `zip -r` on an existing archive updates entries but does not remove deleted files. Always exclude `.DS_Store` with `-x "*.DS_Store"`.
   - Note: the RSS feed generator bundle is named `rss-feed-generator-skill.zip` (not `rss-feed-generator.zip`)
4. The root `README.md` intentionally stays minimal — detailed docs belong in each skill's `SKILL.md`

## Loading a Skill

Per the root README:
1. Ask the AI agent environment to load the skill bundle from its path: `file://<absolute-path>/<skill-name>.zip` or the directory path
2. Test using the usage examples in the skill's `SKILL.md`
3. Optionally schedule for automated runs
