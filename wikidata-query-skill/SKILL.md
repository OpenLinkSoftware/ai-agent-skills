---
name: wikidata-query-skill
description: Transform natural language questions into SPARQL queries for Wikidata and generate beautiful HTML results pages. Query the Wikidata knowledge base using plain English prompts.
---

# Wikidata Query Skill

## When to Use This Skill

Use this skill when users want to:
- Query Wikidata using natural language
- Get comprehensive, multilingual data about entities
- Access property-rich information (Wikidata has extensive properties)
- Create visualizations of Wikidata query results
- Generate HTML reports from SPARQL queries
- Query data with better temporal coverage than DBpedia

## Core Capabilities

✅ **Natural Language to SPARQL**: Convert user questions into valid Wikidata SPARQL
✅ **Query Execution**: Execute queries against Wikidata Query Service
✅ **HTML Generation**: Create beautiful, interactive HTML result pages
✅ **Multiple Output Formats**: JSON, Markdown tables, or HTML
✅ **Label Service**: Automatic label resolution for human-readable results

## Wikidata Endpoint

**SPARQL Endpoint**: `https://query.wikidata.org/sparql`
**Accept Header**: `application/sparql-results+json`
**Method**: HTTP GET with URL-encoded query
**User-Agent**: Required (use `Claude-Code-Wikidata-Skill/1.0`)

## Wikidata Naming Convention

**Properties**: `wdt:P###` (e.g., `wdt:P57` for director)
**Entities**: `wd:Q###` (e.g., `wd:Q51566` for Spike Lee)
**Service**: `wikibase:label` for automatic label resolution

## Common Wikidata Properties

```
P31  - instance of
P57  - director
P577 - publication date
P2130 - cost/budget
P50  - author
P170 - creator
P19  - place of birth
P20  - place of death
P569 - date of birth
P570 - date of death
P27  - country of citizenship
P106 - occupation
P735 - given name
P734 - family name
P1082 - population
P36  - capital
```

## Query Conversion Workflow

When a user provides a natural language prompt:

### 1. Identify Entity

Find the Wikidata Q-number for the main subject:
- Use descriptive search if needed
- Example: "Spike Lee" → `wd:Q51566`

### 2. Map to Wikidata Properties

**Common mappings:**
- "directed by" → `wdt:P57`
- "release date" / "published" → `wdt:P577`
- "budget" → `wdt:P2130`
- "born in" → `wdt:P19`
- "author" / "written by" → `wdt:P50`
- "population" → `wdt:P1082`
- "capital" → `wdt:P36`

### 3. Construct SPARQL Query

**Template with Label Service:**
```sparql
SELECT DISTINCT ?item ?itemLabel ?property
WHERE {
  ?item wdt:P### wd:Q### ;     # property: entity
        wdt:P31 wd:Q### .       # instance of: type
  OPTIONAL { ?item wdt:P### ?property . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY <sort_criteria>
LIMIT <number>
```

**CRITICAL**: Always include the label service for human-readable output!

### 4. Execute Query

Use curl with proper headers:
```bash
curl -s -G "https://query.wikidata.org/sparql" \
  -H "Accept: application/sparql-results+json" \
  -H "User-Agent: Claude-Code-Wikidata-Skill/1.0" \
  --data-urlencode "query=<SPARQL_QUERY>"
```

### 5. Generate Output

**Options:**
- **JSON**: Raw query results
- **Markdown Table**: Formatted for terminal display
- **HTML Page**: Interactive, styled results page with Wikidata branding

## Example Query Patterns

### Pattern 1: Films by Director
**User**: "Show me movies directed by Spike Lee"

**SPARQL**:
```sparql
SELECT DISTINCT ?film ?filmLabel ?publicationDate ?budget
WHERE {
  ?film wdt:P57 wd:Q51566 ;        # director: Spike Lee
        wdt:P31 wd:Q11424 .         # instance of: film
  OPTIONAL { ?film wdt:P577 ?publicationDate . }
  OPTIONAL { ?film wdt:P2130 ?budget . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?publicationDate)
```

### Pattern 2: Books by Author
**User**: "List books written by J.K. Rowling"

**SPARQL**:
```sparql
SELECT DISTINCT ?book ?bookLabel ?publicationDate
WHERE {
  ?book wdt:P50 wd:Q34660 ;        # author: J.K. Rowling
        wdt:P31 wd:Q7725634 .      # instance of: literary work
  OPTIONAL { ?book wdt:P577 ?publicationDate . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY ?publicationDate
```

### Pattern 3: People by Occupation
**User**: "Who are famous physicists born in the 20th century?"

**SPARQL**:
```sparql
SELECT ?person ?personLabel ?birthDate ?birthPlaceLabel
WHERE {
  ?person wdt:P106 wd:Q169470 ;     # occupation: physicist
          wdt:P569 ?birthDate .     # date of birth
  OPTIONAL { ?person wdt:P19 ?birthPlace . }
  FILTER(YEAR(?birthDate) >= 1900 && YEAR(?birthDate) < 2000)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY ?birthDate
LIMIT 50
```

### Pattern 4: Geographic Queries
**User**: "What are the capitals of European countries?"

**SPARQL**:
```sparql
SELECT ?country ?countryLabel ?capital ?capitalLabel ?population
WHERE {
  ?country wdt:P30 wd:Q46 ;         # continent: Europe
           wdt:P36 ?capital .       # capital
  ?capital wdt:P1082 ?population .  # population
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?population)
```

### Pattern 5: Award Winners
**User**: "List Nobel Prize in Literature winners"

**SPARQL**:
```sparql
SELECT ?person ?personLabel ?awardYear
WHERE {
  ?person wdt:P166 wd:Q37922 ;      # award received: Nobel Prize in Literature
          wdt:P569 ?birthDate .
  OPTIONAL { ?person wdt:P166 ?award .
             ?award wdt:P585 ?awardYear . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?awardYear)
```

## Finding Wikidata Entities

If you need to find a Q-number for an entity:

**Method 1: Search Query**
```sparql
SELECT ?item ?itemLabel ?itemDescription
WHERE {
  ?item rdfs:label "Spike Lee"@en .
  ?item wdt:P106 wd:Q2526255 .      # occupation: film director
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 5
```

**Method 2: Use Wikidata search**
- Go to https://www.wikidata.org
- Search for the entity
- Note the Q-number in the URL

## HTML Template Generation

When generating HTML results:

### Required Elements
1. **Title**: Question or query description
2. **Statistics**: Number of results
3. **Table**: Results with hyperlinked Wikidata entities
4. **SPARQL Query Display**: Show the executed query with syntax highlighting
5. **Footer**: Link to Wikidata, attribution, license info

### Wikidata Branding
- Use blue/green color scheme (Wikidata colors)
- Include Wikidata logo reference
- Link to https://www.wikidata.org
- Mention collaborative nature

### HTML Template Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>[Query Description] - Wikidata</title>
    <style>
        /* Blue/green Wikidata theme */
        /* Responsive design */
        /* Interactive elements */
    </style>
</head>
<body>
    <div class="container">
        <h1>[Question/Title]</h1>
        <div class="wikidata-badge">Wikidata</div>
        <div class="stats">[Results count]</div>
        <table>[Results with Wikidata links]</table>
        <div class="sparql-query">[Query code]</div>
        <div class="footer">[Attribution + CC0 license]</div>
    </div>
</body>
</html>
```

## Error Handling

### Timeout Errors
Wikidata Query Service has query timeout limits:
- Add LIMIT clause (default: 100)
- Simplify complex joins
- Remove unnecessary OPTIONAL clauses

### No Results
- Check entity Q-numbers
- Verify property P-numbers
- Suggest using Wikidata search

### Label Service Issues
- Always include: `SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }`
- Use `?variableLabel` to get human-readable names

## Best Practices

1. **Always use Label Service**: Makes results human-readable
2. **Check Q/P numbers**: Verify entity and property identifiers
3. **Add LIMIT**: Default to LIMIT 100
4. **Use OPTIONAL**: For properties that may not exist
5. **Filter by language**: When not using label service
6. **Order results**: Make output meaningful
7. **Include User-Agent**: Required by Wikidata Query Service

## Wikidata vs DBpedia

**Use Wikidata when:**
- Need better temporal data (publication dates, birth dates)
- Want multilingual support
- Need comprehensive property coverage
- Require structured identifiers (Q/P system)

**Use DBpedia when:**
- Querying Wikipedia-specific data
- Need budget/financial information (better coverage)
- Working with English-only queries

## Example Session

**User**: "List all films directed by Christopher Nolan with release dates and budgets"

**Assistant**:
"I'll query Wikidata for Christopher Nolan's films.

First, I need to find his Wikidata ID..."
[Searches and finds wd:Q25191]

"Executing SPARQL query against Wikidata Query Service..."

[Constructs and executes query]

"Found 12 films! Would you like the results as:
1. JSON
2. Markdown table
3. HTML page"

**User**: "HTML page"

**Assistant**:
[Generates beautiful HTML page with Wikidata branding]

"✓ HTML page generated and saved to: ./christopher_nolan_films.html
✓ 12 films found
✓ 10 films with release dates
✓ 5 films with budget information"

## Output Preferences

Always ask the user:
```
"Would you like the results as:
1. JSON (raw data)
2. Markdown table (terminal display)
3. HTML page (interactive visualization)"
```

## Scope

**This skill handles:**
- Queries about entities in Wikidata
- Structured data extraction with properties
- Multi-property queries
- Temporal queries (dates, years)
- Result formatting and visualization

**This skill does NOT handle:**
- Full-text search (use Wikidata search instead)
- Data modification (read-only queries)
- Non-English labels (configure in label service)

## Important Notes

- **User-Agent Required**: Always include User-Agent header
- **Rate Limiting**: Be respectful of query service limits
- **Query Timeout**: 60 seconds maximum
- **License**: All Wikidata data is CC0 (public domain)

---

**Version**: 1.0.0
**Endpoint**: https://query.wikidata.org/sparql
**Data Source**: Wikidata (collaborative knowledge base)
**License**: CC0 (public domain)
