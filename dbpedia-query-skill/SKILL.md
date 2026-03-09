---
name: dbpedia-query-skill
description: Transform natural language questions into SPARQL queries for DBpedia and generate beautiful HTML results pages. Query the DBpedia knowledge graph using plain English prompts.
---

# DBpedia Query Skill

## When to Use This Skill

Use this skill when users want to:
- Query DBpedia using natural language
- Ask questions about people, places, movies, books, organizations, etc.
- Get structured data from Wikipedia via DBpedia
- Create visualizations of DBpedia query results
- Generate HTML reports from SPARQL queries

## Core Capabilities

✅ **Natural Language to SPARQL**: Convert user questions into valid SPARQL queries
✅ **Protocol-Aware Execution**: Route execution through `curl`, URIBurner REST, or MCP
✅ **HTML Generation**: Create beautiful, interactive HTML result pages
✅ **Multiple Output Formats**: JSON, Markdown tables, or HTML
✅ **Error Handling**: Graceful handling of malformed queries or no results

## DBpedia Endpoint

**SPARQL Endpoint**: `https://dbpedia.org/sparql`
**Format**: JSON results (`format=json`)
**Method**: HTTP GET with URL-encoded query

## Execution Routing

Default execution order:
1. **SPASQL via `execute_spasql_query`** (when connected to a Virtuoso instance) — prepend the SPARQL query with the keyword `SPARQL` and submit to `https://linkeddata.uriburner.com/chat/functions/execute_spasql_query`. Parameters: `sql` (required — the `SPARQL <query>` string), `max_rows`, `timeout`, `format` (`json`, `jsonl`, or `markdown`).
2. `curl` directly against `https://dbpedia.org/sparql`
3. URIBurner REST via `https://linkeddata.uriburner.com/chat/functions/sparqlRemoteQuery`
4. MCP via `https://linkeddata.uriburner.com/chat/mcp/messages` or `https://linkeddata.uriburner.com/chat/mcp/sse`
5. Authenticated LLM-mediated execution via `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`
6. OPAL Agent routing using recognizable OPAL function names

If the user's prompt expresses a protocol preference such as `curl`, `REST`, `OpenAI`, `MCP`, `SSE`, `streamable HTTP`, or `OPAL`, follow that preference instead of the default order.

Read [protocol-routing.md](./references/protocol-routing.md) when you need exact endpoint patterns.

## Common DBpedia Prefixes

```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX dbp: <http://dbpedia.org/property/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX dct: <http://purl.org/dc/terms/>
```

## Query Conversion Workflow

When a user provides a natural language prompt:

### 1. Analyze the Question
- Identify the **subject** (who/what is being asked about)
- Identify the **predicate** (what information is requested)
- Determine if filtering, sorting, or limiting is needed

### 2. Map to DBpedia Properties

**Common mappings:**
- "directed by" → `dbo:director`
- "release date" → `dbp:date` or `dbo:releaseDate`
- "budget" → `dbo:budget`
- "born in" → `dbo:birthPlace`
- "population" → `dbo:populationTotal`
- "capital of" → `dbo:capital`
- "written by" → `dbo:author`
- "starring" → `dbo:starring`

### 3. Construct SPARQL Query

**Template:**
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?variable ?label
WHERE {
  ?variable <predicate> <object> ;
           rdfs:label ?label .
  FILTER(LANG(?label) = 'en')
}
ORDER BY <sort_criteria>
LIMIT <number>
```

### 4. Execute Query

Choose the execution protocol using the routing rules above.

Primary path (Virtuoso instance), SPASQL via `execute_spasql_query`:
- Call the `execute_spasql_query` function with `sql` set to `SPARQL <SPARQL_QUERY>` (the keyword `SPARQL` followed by a space and the query text), plus optional `max_rows`, `timeout`, and `format` (`json`, `jsonl`, or `markdown`).

Direct `curl` against DBpedia (when not on a Virtuoso instance):
```bash
curl -s -G "https://dbpedia.org/sparql" \
  --data-urlencode "query=<SPARQL_QUERY>" \
  --data-urlencode "format=json"
```

REST fallback via URIBurner:
```bash
curl -s -G "https://linkeddata.uriburner.com/chat/functions/sparqlRemoteQuery" \
  --data-urlencode "url=https://dbpedia.org/sparql" \
  --data-urlencode "query=<SPARQL_QUERY>" \
  --data-urlencode "format=application/sparql-results+json"
```

MCP path:
- Use MCP only when the user asks for it, when the local environment is already wired for MCP, or when the higher-priority routes are unavailable.
- Prefer the streamable HTTP endpoint first: `https://linkeddata.uriburner.com/chat/mcp/messages`
- Use the SSE endpoint when the client expects server-sent events: `https://linkeddata.uriburner.com/chat/mcp/sse`
- Treat MCP as auth-gated by default. From this environment, both MCP endpoints returned `401 Unauthorized` on March 6, 2026.

Authenticated `chatPromptComplete` path:
- Use when the user asks for OpenAI-compatible, LLM-mediated, or function-brokered execution, or when the earlier routes are unavailable.
- Endpoint: `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`
- Treat this path as auth-gated by default. From this environment, unauthenticated requests failed because no API key was available on March 6, 2026.

OPAL Agent routing path:
- Use when the user asks for OPAL, agent routing, or recognizable OPAL tools/functions.
- Treat OPAL as an agent layer that routes through named functions rather than just a raw transport.
- Recognizable DBpedia-relevant OPAL functions include:
  - `OAI.DBA.sparqlRemoteQuery`
  - `OAI.DBA.chatPromptComplete`
  - `OAI.DBA.sparqlQuery` when execution is scoped to the service's local graph rather than remote DBpedia
- When using OPAL routing, refer to the function by its OPAL-recognizable name and match the execution path to the user's requested agent behavior.

### 5. Generate Output

**Options:**
- **JSON**: Raw query results
- **Markdown Table**: Formatted for terminal display
- **HTML Page**: Interactive, styled results page

## Example Query Patterns

### Pattern 1: Films by Director
**User**: "Show me movies directed by Christopher Nolan"

**SPARQL**:
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?film ?title ?releaseDate
WHERE {
  ?film dbo:director dbr:Christopher_Nolan ;
        a dbo:Film ;
        rdfs:label ?title .
  OPTIONAL { ?film dbo:releaseDate ?releaseDate }
  FILTER(LANG(?title) = 'en')
}
ORDER BY DESC(?releaseDate)
```

**Execution options**:
- Virtuoso instance (default): prepend query with `SPARQL` and send via `execute_spasql_query`
- Direct: run with `curl` against DBpedia
- REST: send the same query through `sparqlRemoteQuery`
- MCP: invoke through the configured MCP transport when requested
- `chatPromptComplete`: use authenticated LLM-mediated routing when requested
- OPAL Agent: route through recognizable OPAL function names when requested

### Pattern 2: Population Queries
**User**: "What are the 10 most populous cities in France?"

**SPARQL**:
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?city ?name ?population
WHERE {
  ?city dbo:country dbr:France ;
        a dbo:City ;
        rdfs:label ?name ;
        dbo:populationTotal ?population .
  FILTER(LANG(?name) = 'en')
}
ORDER BY DESC(?population)
LIMIT 10
```

### Pattern 3: Person Information
**User**: "Tell me about Albert Einstein - when was he born and where?"

**SPARQL**:
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?birthDate ?birthPlace ?placeLabel
WHERE {
  dbr:Albert_Einstein dbo:birthDate ?birthDate ;
                      dbo:birthPlace ?birthPlace .
  ?birthPlace rdfs:label ?placeLabel .
  FILTER(LANG(?placeLabel) = 'en')
}
```

## HTML Template Generation

When generating HTML results:

### Required Elements
1. **Title**: Question or query description
2. **Statistics**: Number of results, query execution time
3. **Table**: Results with hyperlinked DBpedia URIs
4. **SPARQL Query Display**: Show the executed query
5. **Footer**: Link to DBpedia, data source attribution

### Styling Guidelines
- Use gradient backgrounds
- Responsive design (mobile-friendly)
- Hover effects on table rows
- Hyperlink all DBpedia resources
- Color-code different data types
- Include icons for visual appeal

### HTML Template Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>[Query Description] - DBpedia</title>
    <style>
        /* Modern, responsive styling */
        /* Gradient backgrounds */
        /* Hover effects */
        /* Mobile-first design */
    </style>
</head>
<body>
    <div class="container">
        <h1>[Question/Title]</h1>
        <div class="stats">[Results count]</div>
        <table>[Results]</table>
        <div class="sparql-query">[Query code]</div>
        <div class="footer">[Attribution]</div>
    </div>
</body>
</html>
```

## Error Handling

### No Results
If query returns 0 results:
- Inform user clearly
- Suggest alternative phrasings
- Check for typos in entity names

### Query Errors
If SPARQL syntax error:
- Display error message
- Show attempted query
- Offer to reformulate

### Timeout
If query times out:
- Add LIMIT clause
- Simplify query complexity
- Suggest narrowing criteria

### Protocol Failure
If the selected execution route fails:
- Honor explicit user preference first; do not silently switch protocols if the user asked for a specific one
- If no preference was stated, fall through in this order: `curl` -> `sparqlRemoteQuery` -> MCP -> `chatPromptComplete` -> OPAL Agent routing
- Report which protocol failed and which fallback you are trying next

## Output Preferences

Always ask the user:
```
"Would you like the results as:
1. JSON (raw data)
2. Markdown table (terminal display)
3. HTML page (interactive visualization)"
```

## Best Practices

1. **Always use DISTINCT**: Avoid duplicate results
2. **Filter by language**: Use `FILTER(LANG(?label) = 'en')`
3. **Add LIMIT**: Default to LIMIT 100 unless specified
4. **Use OPTIONAL**: For properties that may not exist
5. **Order results**: Make results meaningful with ORDER BY
6. **Hyperlink in HTML**: All DBpedia URIs should be clickable
7. **State the chosen protocol**: Mention whether execution used direct `curl`, REST, or MCP
8. **Keep `chatPromptComplete` available**: Use it after MCP in the default routing order, and only when credentials are available
9. **Use OPAL names when routing through OPAL**: Prefer recognizable names such as `OAI.DBA.sparqlRemoteQuery` and `OAI.DBA.chatPromptComplete`

## Example Session

**User**: "List books written by J.K. Rowling with publication dates"

**Assistant**:
"I'll query DBpedia for books authored by J.K. Rowling.

Executing the SPARQL query with direct `curl` against the DBpedia endpoint..."

[Constructs and executes query]

"Found 15 books! Would you like the results as:
1. JSON
2. Markdown table
3. HTML page"

**User**: "HTML page"

**Assistant**:
[Generates beautiful HTML page with results]

"✓ HTML page generated and saved to: ./jk_rowling_books.html
✓ 15 books found with publication dates"

## Scope

**This skill handles:**
- Queries about entities in DBpedia
- Structured data extraction
- Result formatting and visualization

**This skill does NOT handle:**
- Text search (use DBpedia Lookup API instead)
- Data modification (read-only queries)
- Real-time data (DBpedia updates periodically)

---

**Version**: 1.0.0
**Endpoint**: https://dbpedia.org/sparql
**Data Source**: DBpedia (Wikipedia structured data)
