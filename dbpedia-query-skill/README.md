# DBpedia Query Skill

Transform natural language questions into SPARQL queries for DBpedia and generate beautiful HTML results pages.

## Overview

This Claude Code skill enables you to query the DBpedia knowledge graph using plain English. Simply describe what you want to know, and the skill will:

1. Convert your question to a SPARQL query
2. Execute it against DBpedia
3. Format results as JSON, Markdown, or HTML

## Installation

```bash
# Copy to Claude Code skills directory
cp -r dbpedia-query-skill ~/.claude/skills/

# Or use as a skill bundle
# (ZIP file can be distributed)
```

## Usage

### Basic Query

```
User: "Show me all movies directed by Spike Lee"

Skill: Converts to SPARQL, executes query, returns results
```

### With HTML Output

```
User: "List books by Agatha Christie and save as HTML"

Skill: Generates beautiful HTML page with:
- Formatted table
- DBpedia links
- SPARQL query display
- Professional styling
```

## Features

✅ Natural language to SPARQL conversion
✅ Automatic query execution
✅ Multiple output formats (JSON/Markdown/HTML)
✅ Beautiful HTML templates
✅ Error handling and suggestions
✅ DBpedia endpoint integration

## Examples

See `examples/sample-queries.md` for:
- Films by director
- Books by author
- Geographic queries
- Population data
- Sports teams
- And more!

## File Structure

```
dbpedia-query-skill/
├── SKILL.md                    # Main skill definition
├── README.md                   # This file
├── examples/
│   └── sample-queries.md       # Query examples
└── templates/
    └── html-template.html      # HTML output template
```

## How It Works

1. **User provides natural language prompt**
   - Example: "What are the most populous cities in France?"

2. **Skill analyzes and maps to DBpedia**
   - Identifies entities and properties
   - Constructs valid SPARQL query

3. **Query execution**
   - Executes against https://dbpedia.org/sparql
   - Retrieves JSON results

4. **Format output**
   - User chooses: JSON, Markdown table, or HTML
   - HTML includes beautiful styling and interactivity

## DBpedia Prefixes

The skill knows common DBpedia prefixes:

- `dbo:` - DBpedia Ontology
- `dbr:` - DBpedia Resource
- `dbp:` - DBpedia Property
- `rdfs:` - RDF Schema
- `foaf:` - Friend of a Friend

## Output Examples

### JSON Output
Raw SPARQL results in JSON format

### Markdown Table
```
| Film Title              | Release Date | Budget    |
|------------------------|--------------|-----------|
| Do the Right Thing     | 1989         | $6.2M     |
| Malcolm X              | 1992         | $35M      |
```

### HTML Page
Beautiful, interactive page with:
- Gradient backgrounds
- Hover effects
- Clickable DBpedia links
- Embedded SPARQL query
- Responsive design

## Common Use Cases

1. **Film Research**: Directors, actors, budgets, release dates
2. **Geographic Data**: Cities, countries, populations
3. **Book Information**: Authors, publication dates, genres
4. **Person Queries**: Birth dates, occupations, achievements
5. **Organization Data**: Founding dates, locations, members

## Best Practices

- Start with simple queries
- Be specific about entities (use full names)
- Request HTML output for better visualization
- Check example queries for patterns
- DBpedia uses underscores in names (e.g., "Spike_Lee")

## Limitations

- Read-only queries (no data modification)
- DBpedia updates periodically (not real-time)
- Some entities may have incomplete data
- Complex queries may timeout

## Support

- DBpedia Homepage: https://dbpedia.org
- SPARQL Endpoint: https://dbpedia.org/sparql
- DBpedia Documentation: https://www.dbpedia.org/resources/documentation/

## Version

1.0.0

## License

This skill is provided as-is for use with Claude Code.
DBpedia data is available under CC BY-SA 3.0 license.
