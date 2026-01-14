# URIBurner OPAL Agent Skills

**Version:** 2.1.0  
**Created:** 2025-10-27

## Description

Comprehensive toolkit for URIBurner MCP Server enabling semantic data discovery, Knowledge Graph exploration, SPARQL/SQL query execution, RDF sponging, and database management. Use native MCP tools for queries; ChatPromptComplete only when user explicitly requests Gemini-powered analysis.

## Features

- **Native MCP Tool Usage:** Direct execution of SPARQL, SQL, and SPASQL queries
- **SPARQL Agent 121 Integration:** Advanced KG-first workflow with citation verification
- **Multi-Endpoint Support:** Query local and remote SPARQL endpoints
- **RDF Sponging:** Convert web content to RDF triples
- **Database Management:** Schema exploration, RDF view generation, statistics
- **Comprehensive Documentation:** Query templates, examples, and troubleshooting

## Key Components

### Native Tools (Primary Usage)
- `execute_spasql_query` - Execute SPARQL-within-SQL queries locally
- `sparqlQuery` - Standard SPARQL against local endpoint
- `sparqlRemoteQuery` - Query remote SPARQL endpoints
- `execute_sql_query` - SQL database queries
- `WEB_FETCH` - Retrieve web content
- `SPONGE_URL` - Convert web content to RDF

### SPARQL Agent 121 (Advanced Usage)
- **Assistant ID:** `new-sparql-agent-121`
- **Model:** `gemini-2.5-pro`
- **Features:** KG-first workflow, ontology-aware queries, citation verification
- **Commands:** `/kg-verify`, `/kg-on`, `/kg-off`, `/help`, `/query`, etc.

## Quick Start

### Basic KG Query
```json
{
  "sql": "SPARQL SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10",
  "format": "markdown"
}
```

### Citation Verification (Agent 121)
```json
{
  "model": "gemini-2.5-pro",
  "assistant_config_id": "new-sparql-agent-121",
  "prompt": "/kg-verify What is RDF?",
  "temperature": "0.0"
}
```

## Installation

1. Copy this skill to your skills directory
2. Restart your MCP server or reload skills
3. Verify URIBurner MCP Server is accessible

## Documentation

See `SKILL.md` for complete documentation including:
- Tool selection guide
- KG-first workflow details
- Query optimization techniques
- Error handling
- Integration examples
- Troubleshooting guide

## Requirements

- URIBurner MCP Server access
- SPARQL endpoint availability
- Optional: API keys for authenticated endpoints

## Support

For issues or questions:
- Review troubleshooting section in SKILL.md
- Check URIBurner MCP Server documentation
- Use SPARQL Agent 121's `/help` command

## Version History

- **2.1.0** (2025-10-27): Comprehensive update reflecting SPARQL Agent 121 v1.0.121 guidelines
- **2.0.0**: Initial structured release

## License

See your URIBurner MCP Server license terms.
