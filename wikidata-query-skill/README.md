# Wikidata Query Skill

Transform natural language questions into SPARQL queries for Wikidata and generate beautiful HTML results pages.

## Overview

This Claude Code skill enables you to query the Wikidata knowledge base using plain English. Simply describe what you want to know, and the skill will:

1. Convert your question to a SPARQL query
2. Execute it against Wikidata Query Service
3. Format results as JSON, Markdown, or HTML

## Installation

```bash
# Copy to Claude Code skills directory
cp -r wikidata-query-skill ~/.claude/skills/

# Or use as a skill bundle
# (ZIP file can be distributed)
```

## Usage

### Basic Query

```
User: "Show me all movies directed by Spike Lee with release dates"

Skill: Converts to SPARQL, executes query, returns results
```

### With HTML Output

```
User: "List Nobel Prize in Physics winners and save as HTML"

Skill: Generates beautiful HTML page with:
- Formatted table with Wikidata links
- SPARQL query display
- Professional Wikidata-themed styling
- CC0 license information
```

## Features

✅ Natural language to SPARQL conversion
✅ Automatic Wikidata entity lookup (Q-numbers)
✅ Label Service integration (human-readable results)
✅ Multiple output formats (JSON/Markdown/HTML)
✅ Beautiful HTML templates with Wikidata branding
✅ Error handling and timeout management
✅ Wikidata Query Service integration

## Examples

See `examples/sample-queries.md` for:
- Films by director
- Books by author
- Nobel Prize winners
- Geographic queries
- Scientists and discoveries
- Musicians and bands
- And more!

## File Structure

```
wikidata-query-skill/
├── SKILL.md                    # Main skill definition
├── README.md                   # This file
├── examples/
│   └── sample-queries.md       # Query examples with Q/P numbers
└── templates/
    └── html-template.html      # HTML output template
```

## How It Works

1. **User provides natural language prompt**
   - Example: "Who are the members of The Beatles?"

2. **Skill finds Wikidata entities**
   - Looks up Q-numbers (e.g., Q1299 for The Beatles)
   - Maps to appropriate properties (P-numbers)

3. **Constructs SPARQL with Label Service**
   - Creates valid Wikidata SPARQL
   - Includes label service for human-readable output

4. **Query execution**
   - Executes against https://query.wikidata.org/sparql
   - Uses proper headers (User-Agent required)

5. **Format output**
   - User chooses: JSON, Markdown table, or HTML
   - HTML uses Wikidata blue/green theme

## Wikidata Identifiers

### Properties (P-numbers)
- `P57` - director
- `P577` - publication date
- `P50` - author
- `P569` - date of birth
- `P2130` - budget
- `P106` - occupation

### Entities (Q-numbers)
- `Q51566` - Spike Lee
- `Q11424` - film
- `Q34660` - J.K. Rowling

## Output Examples

### JSON Output
Raw SPARQL results with entity URIs

### Markdown Table
```
| Film                    | Release Date | Budget    |
|------------------------|--------------|-----------|
| BlacKkKlansman         | 2018         | $15M      |
| Da 5 Bloods            | 2020         | N/A       |
```

### HTML Page
Beautiful, interactive page with:
- Blue gradient backgrounds (Wikidata theme)
- Hover effects
- Clickable Wikidata entity links
- Embedded SPARQL query with syntax highlighting
- CC0 license information
- Responsive design

## Common Use Cases

1. **Film Research**: Directors, release dates, budgets
2. **Book Information**: Authors, publication dates, series
3. **People Queries**: Birth dates, occupations, awards
4. **Geographic Data**: Cities, populations, countries
5. **Scientific Data**: Discoveries, inventors, elements
6. **Cultural Data**: Artworks, artists, museums

## Why Wikidata?

**Advantages over DBpedia:**
- ✅ Better temporal data (97% coverage for dates)
- ✅ Structured property system (P-numbers)
- ✅ Multilingual support
- ✅ More comprehensive coverage
- ✅ Collaborative, actively maintained

**When to use DBpedia instead:**
- Budget/financial data (better coverage)
- Wikipedia-specific content
- English-only queries

## Best Practices

1. **Use Label Service**: Always include for readable results
2. **Find Q-numbers**: Use Wikidata.org to find entity IDs
3. **Add User-Agent**: Required by Wikidata Query Service
4. **Use OPTIONAL**: Many properties may not exist
5. **Add LIMIT**: Start with LIMIT 100
6. **Test incrementally**: Build complex queries step-by-step

## Label Service

Always include this in queries:
```sparql
SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
```

This automatically creates `?variableLabel` for human-readable names.

## Limitations

- Read-only queries (no data modification)
- 60-second query timeout
- Rate limiting on Query Service
- Some entities may have incomplete data

## Data License

All Wikidata content is available under **CC0** (public domain).
You can use, modify, and distribute the data freely.

## Support

- Wikidata Homepage: https://www.wikidata.org
- Query Service: https://query.wikidata.org
- SPARQL Examples: https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples
- Property List: https://www.wikidata.org/wiki/Wikidata:List_of_properties

## Version

1.0.0

## License

This skill is provided as-is for use with Claude Code.
All Wikidata data is CC0 (public domain).
