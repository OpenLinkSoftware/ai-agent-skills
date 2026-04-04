---
name: uriburner-opal-agent-skills
description: Comprehensive toolkit for URIBurner MCP Server enabling semantic data discovery, Knowledge Graph exploration, SPARQL/SQL query execution, RDF sponging, and database management. Use native MCP tools for queries; ChatPromptComplete only when user explicitly requests Gemini-powered analysis.
---

# URIBurner OPAL Agent Skills

## Overview

This skill provides comprehensive guidance for using URIBurner MCP Server's suite of tools for semantic data operations, Knowledge Graph exploration, and database management. URIBurner offers powerful native tools that should be used directly for queries and data operations.

**Key Principle:** Use URIBurner's native MCP tools (execute_spasql_query, sparqlQuery, etc.) for all standard operations. Only invoke ChatPromptComplete when the user explicitly requests Gemini-powered AI analysis or when using SPARQL Agent 121's advanced features.

**→ For execution modalities and environment-specific routing:** Read `references/protocol-routing.md`

## Execution Routing

Default execution order:

1. URIBurner REST functions (unauthenticated or with existing session)
2. Terminal-owned OAuth flow — when the endpoint requires OAuth 2.0 authentication, execute the OAuth flow from the terminal (authorization code, client credentials, or device flow), capture the Bearer token, and inject it into subsequent REST/OpenAPI calls via `Authorization: Bearer {token}` headers
3. MCP via `https://linkeddata.uriburner.com/chat/mcp/messages` or `https://linkeddata.uriburner.com/chat/mcp/sse`
4. OPAL Agent routing using canonical OPAL-recognizable function names
5. Authenticated LLM-mediated execution via `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`
6. Direct `curl` as last resort

If the user explicitly names a protocol, honor that preference instead of the default order.

## Prerequisites

- Access to URIBurner MCP Server
- Understanding of SPARQL basics (recommended)
- Familiarity with semantic web concepts (helpful)
- Knowledge of SPARQL Agent 121 workflow (for advanced usage)

## Core URIBurner MCP Tools

URIBurner MCP Server provides these native tools, listed by frequency of use:

### Primary Query Tools

#### 1. execute_spasql_query
**Purpose:** Execute SPARQL-within-SQL queries against local Knowledge Graph  
**When to use:** Primary tool for KG queries on local URIBurner instance  
**Parameters:**
- `sql` (required) - SPASQL query text (prefix with "SPARQL" keyword)
- `format` (optional) - Response format: "json", "jsonl", "markdown" (default: "json")
- `max_rows` (optional) - Maximum rows to return (default: varies)
- `timeout` (optional) - Query timeout in seconds (default: 30)

**Example:**
```json
{
  "sql": "SPARQL SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10",
  "format": "json",
  "max_rows": 10
}
```

**With Inference Enabled:**
```json
{
  "sql": "SPARQL DEFINE input:inference 'urn:rdfs:subclass:subproperty:inference:rules' SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10",
  "format": "json"
}
```

#### 2. sparqlQuery
**Purpose:** Execute SPARQL queries against local endpoint  
**When to use:** Standard SPARQL queries on URIBurner's default endpoint  
**Parameters:**
- `query` (required) - SPARQL query text
- `format` (optional) - Response format: "json", "jsonl", "markdown"
- `timeout` (optional) - Query timeout in seconds

**Example:**
```json
{
  "query": "SELECT ?type (COUNT(?entity) AS ?count) WHERE { ?entity a ?type } GROUP BY ?type ORDER BY DESC(?count) LIMIT 10",
  "format": "json"
}
```

#### 3. sparqlRemoteQuery
**Purpose:** Execute SPARQL queries against remote endpoints  
**When to use:** Querying external SPARQL endpoints (DBpedia, Wikidata, etc.)  
**Parameters:**
- `url` (required) - Remote SPARQL endpoint URL
- `query` (required) - SPARQL query text
- `format` (optional) - Response format
- `timeout` (optional) - Query timeout in seconds
- `apiKey` (optional) - API key for authenticated endpoints

**Example:**
```json
{
  "url": "https://dbpedia.org/sparql",
  "query": "SELECT * WHERE { ?s a dbo:Person } LIMIT 5",
  "format": "json"
}
```

#### 4. execute_sql_query
**Purpose:** Execute SQL queries against local databases  
**When to use:** Querying relational databases (Northwind demo, etc.)  
**Parameters:**
- `sql` (required) - SQL query text (do NOT terminate with semicolon)
- `format` (optional) - Response format
- `max_rows` (optional) - Result limit
- `timeout` (optional) - Query timeout

**Example:**
```json
{
  "sql": "SELECT * FROM Demo.demo.Customers LIMIT 10",
  "format": "json"
}
```

### Data Retrieval Tools

#### 5. WEB_FETCH
**Purpose:** Fetch web content like a browser  
**When to use:** Retrieving web pages for analysis or RDF extraction  
**Parameters:**
- `url` (required) - URL to fetch
- `headers` (optional) - HTTP headers
- `timeout_seconds` (optional) - Request timeout
- `max_redirects` (optional) - Maximum redirects to follow

**Example:**
```json
{
  "url": "https://www.w3.org/",
  "timeout_seconds": 30
}
```

#### 6. SPONGE_URL
**Purpose:** Perform RDF extraction (sponging) on a URL  
**When to use:** Converting web content to RDF triples  
**Parameters:**
- `url` (required) - URL to sponge
- `format` (optional) - Response format
- `max_rows` (optional) - Result limit
- `timeout` (optional) - Query timeout

**Example:**
```json
{
  "url": "https://example.com/data",
  "format": "json"
}
```

### Schema Discovery Tools

#### 7. sparql_list_entity_types
**Purpose:** Retrieve all entity types in an RDF graph  
**When to use:** Discovering what kinds of entities exist in the Knowledge Graph  
**Parameters:**
- `graph_iri` (required) - Target graph IRI
- `format` (optional) - Response format

**Example:**
```json
{
  "graph_iri": "urn:default:graph",
  "format": "markdown"
}
```

#### 8. sparql_list_entity_types_samples
**Purpose:** Retrieve entity types with sample entities and counts  
**When to use:** Getting an overview of entity distribution  
**Parameters:**
- `graph_iri` (required) - Target graph IRI
- `format` (optional) - Response format

**Example:**
```json
{
  "graph_iri": "urn:default:graph",
  "format": "markdown"
}
```

## Tool Selection Guide

Use this decision tree to select the appropriate tool:

```
Query Type?
├─ Knowledge Graph Query
│  ├─ Local URIBurner data?
│  │  ├─ Need entity type discovery? → sparql_list_entity_types
│  │  ├─ Standard query? → execute_spasql_query (PREFERRED)
│  │  └─ No results? → Retry with inference pragma
│  └─ Remote endpoint? → sparqlRemoteQuery
│
├─ SQL Database Query → execute_sql_query
│
├─ Web Content Retrieval
│  ├─ Just fetch content? → WEB_FETCH
│  └─ Extract RDF? → SPONGE_URL
│
└─ User Explicitly Requests Gemini/SPARQL Agent 121? → ChatPromptComplete
```

## SPARQL Agent 121 KG-First Workflow

When using ChatPromptComplete with SPARQL Agent 121 (`assistant_config_id: "new-sparql-agent-121"`), the agent follows a structured **Knowledge Graph-First workflow**:

### Workflow Overview

The agent prioritizes finding answers in Knowledge Graphs before synthesizing responses, following these steps:

### Step 1: Basic Label Match
**Goal:** Find entities with labels matching the prompt

**Query Template (Virtuoso):**
```sparql
SELECT DISTINCT ?entity ?value
WHERE {
  ?entity ?attribute ?value.
  ?value bif:contains "'{{entire-prompt-text}}'" option (score ?sc)
}
ORDER BY DESC(?sc)
LIMIT 10
```

**Key Points:**
- Uses full-text search via `bif:contains()` for Virtuoso
- Searches entire prompt text as-is
- Returns scored results by relevance

### Step 2: Semantic Breakdown
**Goal:** If Step 1 yields no results, decompose the prompt

**Actions:**
1. Break prompt into subject, predicate, object components
2. Determine relevant entity types:
   - `schema:Question` / `schema:FAQPage`
   - `schema:DefinedTermSet`
   - `skos:ConceptScheme`
   - `schema:HowTo`
3. Identify target graphs to query

**Entity Type Discovery Template:**
```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX schema: <http://schema.org/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

SELECT ?type (COUNT(?entity) AS ?count) (SAMPLE(?entity) AS ?sampleEntity)
WHERE {
  ?entity rdf:type ?type .
  FILTER (?type IN (
    schema:FAQPage,
    schema:Question,
    schema:DefinedTermSet,
    skos:ConceptScheme,
    schema:HowTo
  ))
}
GROUP BY ?type
ORDER BY DESC(?count)
```

### Step 3: Explore & Identify
**Goal:** Try semantic variants of the prompt

**Actions:**
1. Generate up to 3 semantically similar prompt variants
2. Retry label match with each variant
3. Query configured remote endpoints in fallback order
4. Maximum queries per prompt: 6

**Fallback Endpoints (in order):**
1. `https://linkeddata.uriburner.com/sparql` (default)
2. `https://kingsley.idehen.net/sparql`
3. `https://demo.openlinksw.com/sparql`

### Step 4: Query for IRIs and Text
**Goal:** Construct targeted query for answers with provenance

**Query Pattern:**
```sparql
PREFIX schema: <http://schema.org/>

SELECT ?question ?answer ?questionIRI ?answerIRI
WHERE {
  ?questionIRI a schema:Question ;
               schema:name ?question ;
               schema:acceptedAnswer ?answerIRI .
  ?answerIRI schema:text ?answer .
  
  FILTER(bif:contains(?question, "'{{search_terms}}'"))
}
ORDER BY DESC(bif:score(?question))
LIMIT 10
```

**Returns:**
- Question and answer text
- Source IRIs for provenance
- Optional relevance scores

### Step 5: Format with Encoded Hyperlinks
**Goal:** Present results with clickable provenance links

**Link Generation Rules:**

For **local SPASQL queries** (same origin as instance):
```
https://linkeddata.uriburner.com/describe/?uri={URL_ENCODED_IRI}
```

For **remote SPARQL endpoints**:
```
https://{endpoint_host}/describe/?uri={URL_ENCODED_IRI}
```

**Example:**
- Entity IRI: `https://kingsley.idehen.net/DAV/home/file.pdf#Question_1`
- Query source: `https://kingsley.idehen.net/sparql`
- Correct link: `https://kingsley.idehen.net/describe/?uri=https%3A%2F%2Fkingsley.idehen.net%2FDAV%2Fhome%2Ffile.pdf%23Question_1`

**Markdown Format:**
```markdown
**Question:** [What is RDF?](https://linkeddata.uriburner.com/describe/?uri=...)

**Answer:** [RDF (Resource Description Framework) is...](https://linkeddata.uriburner.com/describe/?uri=...)
```

## Fallback Strategy (When KG-First Fails)

If the initial KG-first workflow yields no results, the agent follows this escalation:

### 1. Retry with Inference/Reasoning
**Action:** Enable RDFS reasoning for ontology-level equivalence and subsumption

**Virtuoso Pragma:**
```sparql
DEFINE input:inference 'urn:rdfs:subclass:subproperty:inference:rules'
SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10
```

**When to use:**
- Empty results from initial queries
- Domain with rich ontology hierarchies
- Need to infer subclass/subproperty relationships

### 2. Try Additional Remote Endpoints
**Action:** Query fallback endpoints in configured order

**Process:**
1. Execute same query against next endpoint
2. Keep entity IRIs scoped to originating endpoint
3. Sequential retry delay: 1 second between endpoints
4. Respect per-endpoint timeout: 30 seconds

### 3. Semantic Similarity Refinement
**Action:** Generate broader or narrower query variants

**Strategies:**
- Use broader terms (parent concepts)
- Use more specific terms (child concepts)
- Try synonyms and related terms
- Adjust filters to be less restrictive

**Maximum retries:** 2 semantic variants

### 4. Final Report to User
**Action:** If all attempts fail, provide audit block and options

**Audit Block Contents:**
```json
{
  "queries_executed": [
    {
      "query_text": "SPARQL SELECT...",
      "endpoint_url": "https://linkeddata.uriburner.com/sparql",
      "start_timestamp": "2025-10-27T10:30:00Z",
      "end_timestamp": "2025-10-27T10:30:02Z",
      "status": "no_results",
      "result_count": 0
    }
  ],
  "endpoints_attempted": [
    "https://linkeddata.uriburner.com/sparql",
    "https://kingsley.idehen.net/sparql"
  ],
  "failure_reason": "No matching entities found in any endpoint",
  "total_time_seconds": 45
}
```

**User Options:**
1. Synthesize answer without KG backing
2. Try more endpoints
3. Provide semantic variants manually
4. Refine the question

**Important:** Finding a result on a remote endpoint does NOT change the default data source for subsequent prompts. Processing always returns to the top of the workflow loop.

## SPARQL Query Syntax Rules

### For Virtuoso Backend (Default)

**Full-Text Search:**
```sparql
# ✅ PREFERRED - Use bif:contains()
SELECT ?entity ?value WHERE {
  ?entity ?attr ?value .
  ?value bif:contains "'search term'" option (score ?sc)
}
ORDER BY DESC(?sc)

# ❌ AVOID - REGEX is slower
SELECT ?entity ?value WHERE {
  ?entity ?attr ?value .
  FILTER(REGEX(?value, "search term", "i"))
}
```

**Combining Multiple Terms:**
```sparql
# ✅ PREFERRED - Single bif:contains with logical operators
SELECT ?entity ?value WHERE {
  ?entity ?attr ?value .
  ?value bif:contains "'term1 AND term2 OR term3'" option (score ?sc)
}

# ❌ AVOID - Multiple separate filters
SELECT ?entity ?value WHERE {
  ?entity ?attr ?value .
  FILTER(bif:contains(?value, "'term1'"))
  FILTER(bif:contains(?value, "'term2'"))
}
```

**Inference Pragma:**
```sparql
# Enable RDFS reasoning
DEFINE input:inference 'urn:rdfs:subclass:subproperty:inference:rules'
SELECT ?s ?p ?o WHERE { ?s ?p ?o }
```

### For Non-Virtuoso Backends

**Use Standard SPARQL:**
```sparql
SELECT ?entity ?value WHERE {
  ?entity ?attr ?value .
  FILTER(REGEX(?value, "search term", "i"))
}

# Combine with logical operators
FILTER(REGEX(?value, "term1", "i") && REGEX(?value, "term2", "i"))
```

## ChatPromptComplete (SPARQL Agent 121)

### When to Use ChatPromptComplete

**✅ USE when user explicitly requests:**
- "Use Gemini to analyze..."
- "Ask the SPARQL agent about..."
- "Use SPARQL Agent 121 to..."
- "Get AI-powered analysis of..."
- "/kg-verify" command for citation verification
- "/kg-on" to force KG workflow

**❌ DO NOT USE for:**
- Regular SPARQL queries → Use execute_spasql_query
- Database queries → Use execute_sql_query
- Web content retrieval → Use WEB_FETCH
- Standard KG exploration → Use native tools
- Simple entity lookups → Use native tools

### Configuration

**MCP Server:** URIBurner  
**Tool Name:** ChatPromptComplete  
**Assistant ID:** `new-sparql-agent-121`  
**Model:** `gemini-2.5-pro`

**Basic Parameters:**
```json
{
  "model": "gemini-2.5-pro",
  "assistant_config_id": "new-sparql-agent-121",
  "prompt": "Your query here",
  "max_tokens": 1000,
  "temperature": "0.5",
  "timeout": 30
}
```

### SPARQL Agent 121 Commands

All commands are prefixed with `/` and can be used in the prompt:

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Get help for common issues | "I need help with queries" |
| `/query` | Assist with formulating SPARQL-within-SQL queries | "/query How do I search for RDF types?" |
| `/config` | Guide through driver configuration | "/config" |
| `/troubleshoot` | Help debug connection/driver issues | "/troubleshoot connection timeout" |
| `/limit N` | Set SPARQL result limit (default: 10) | "/limit 50" |
| `/kg-on` | Force KG workflow for all prompts | "/kg-on" |
| `/kg-off` | Disable KG workflow | "/kg-off" |
| `/kg-verify` | Run KG workflow with provenance | "/kg-verify When was SPARQL standardized?" |

### Command Examples

**Citation Verification:**
```json
{
  "model": "gemini-2.5-pro",
  "assistant_config_id": "new-sparql-agent-121",
  "prompt": "/kg-verify What is the definition of RDF according to W3C?",
  "temperature": "0.0",
  "max_tokens": 2000
}
```

**Force KG Workflow:**
```json
{
  "model": "gemini-2.5-pro",
  "assistant_config_id": "new-sparql-agent-121",
  "prompt": "/kg-on Tell me about semantic web technologies",
  "temperature": "0.5"
}
```

**Query Assistance:**
```json
{
  "model": "gemini-2.5-pro",
  "assistant_config_id": "new-sparql-agent-121",
  "prompt": "/query How do I find all HowTo documents about SPARQL?",
  "temperature": "0.3"
}
```

### Agent Capabilities

**Multi-Query Execution:**
- SQL, SPARQL, SPASQL, GraphQL
- Maximum 6 queries per prompt
- 30-second timeout per query

**Ontology-Aware SPARQL:**
- Uses shared ontologies to inform queries
- Understands schema.org, SKOS, Dublin Core
- Automatic entity type detection

**Data Source Exploration:**
- Identifies entity types and prevalence
- Explores multiple endpoints
- Aggregates results from various sources

**Provenance Tracking:**
- Returns source IRIs for all answers
- Generates clickable /describe/ links
- URL-encodes all IRIs properly

### KG Enforcement Modes

**Default Mode (kg_mandatory_for_all_prompts: false):**
- KG workflow attempted but not required
- Can synthesize answer if KG fails
- User asked before fallback to synthesis

**Strict Mode (kg_mandatory_for_all_prompts: true):**
- KG workflow MUST complete successfully
- Agent aborts with audit if workflow fails
- No synthesis without KG backing

**Prompt-Class Enforcement:**
- Certain prompt types always trigger KG workflow
- Examples: fact_lookup, citation_request, citation_verification
- User can override with /kg-off

### Operational Limits

| Parameter | Value | Description |
|-----------|-------|-------------|
| max_queries_per_prompt | 6 | Maximum queries in one workflow |
| per_query_timeout_seconds | 30 | Timeout for each query |
| semantic_variant_retries | 2 | Number of query reformulations |
| result_limit_default | 10 | Default LIMIT clause value |
| max_parallel_endpoint_queries | 2 | Concurrent endpoint queries |
| sequential_retry_delay_seconds | 1 | Delay between endpoint retries |
| maximum_total_kg_time_seconds | 120 | Total workflow timeout |

## Direct Tool Usage Patterns

### Pattern 1: Simple KG Lookup (Native Tool)
**User Query:** "What is RDF?"

**Tool:** execute_spasql_query (NOT ChatPromptComplete)
```json
{
  "sql": "SPARQL SELECT DISTINCT ?entity ?value WHERE { ?entity ?attribute ?value. ?value bif:contains \"'RDF'\" option (score ?sc) } ORDER BY DESC(?sc) LIMIT 10",
  "format": "markdown"
}
```

### Pattern 2: Entity Type Discovery (Native Tool)
**User Query:** "What types of data are in the Knowledge Graph?"

**Tool:** sparql_list_entity_types_samples
```json
{
  "graph_iri": "urn:default:graph",
  "format": "markdown"
}
```

### Pattern 3: Remote Endpoint Query (Native Tool)
**User Query:** "Find information about Tim Berners-Lee in DBpedia"

**Tool:** sparqlRemoteQuery
```json
{
  "url": "https://dbpedia.org/sparql",
  "query": "SELECT ?s ?p ?o WHERE { ?s rdfs:label \"Tim Berners-Lee\"@en . ?s ?p ?o } LIMIT 20",
  "format": "json"
}
```

### Pattern 4: Citation Verification (ChatPromptComplete)
**User Query:** "Use SPARQL Agent to verify when SPARQL was standardized"

**Tool:** ChatPromptComplete (user explicitly requested agent)
```json
{
  "model": "gemini-2.5-pro",
  "assistant_config_id": "new-sparql-agent-121",
  "prompt": "/kg-verify When was SPARQL standardized?",
  "temperature": "0.0"
}
```

## Response Formatting

All tools support these format options:

| Format | Best For | Output Style |
|--------|----------|--------------|
| json | Processing, APIs | Structured JSON objects |
| jsonl | Streaming, logs | One JSON per line |
| markdown | User display | Formatted tables |

**Recommendations:**
- Use "markdown" for end-user results
- Use "json" for programmatic processing
- Use "jsonl" for large result sets

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| Timeout | Query too complex or slow endpoint | Increase timeout, add LIMIT, simplify query |
| No Results | No matching data in KG | Try broader terms, enable inference, check entity types |
| Syntax Error | Invalid SPARQL/SQL | Validate syntax, check prefixes, review templates |
| Connection Error | Endpoint unavailable | Verify URL, check network, try fallback endpoint |
| Authentication Error | Missing or invalid API key | Verify credentials, check endpoint requirements |
| Rate Limit | Too many requests | Add delay, reduce query frequency |

### Error Response Patterns

**Timeout Example:**
```json
{
  "error": "Query timeout after 30 seconds",
  "query": "SPARQL SELECT...",
  "endpoint": "https://linkeddata.uriburner.com/sparql",
  "suggestion": "Try increasing timeout or adding LIMIT clause"
}
```

**No Results Example:**
```json
{
  "status": "success",
  "results": [],
  "message": "No matching entities found",
  "suggestions": [
    "Try broader search terms",
    "Enable inference with DEFINE input:inference",
    "Check available entity types with sparql_list_entity_types"
  ]
}
```

## Advanced Features

### Multi-Endpoint Strategy

**Approach:**
1. Query local URIBurner first (fastest, most relevant)
2. Fall back to configured remote endpoints in order
3. Aggregate results from multiple sources
4. Maintain provenance for each result

**Example Implementation:**
```javascript
// Step 1: Try local
const local = await execute_spasql_query({
  sql: "SPARQL SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10",
  format: "json"
});

// Step 2: If no results, try remote
if (local.results.length === 0) {
  const remote = await sparqlRemoteQuery({
    url: "https://kingsley.idehen.net/sparql",
    query: "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10",
    format: "json"
  });
}

// Step 3: Combine and annotate with source
const combined = {
  local: local.results.map(r => ({...r, source: "local"})),
  remote: remote.results.map(r => ({...r, source: "kingsley.idehen.net"}))
};
```

### Query Optimization Techniques

**1. Use LIMIT Clauses:**
```sparql
-- Always limit result sets
SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10
```

**2. Filter Early:**
```sparql
-- Put FILTER clauses close to the pattern they filter
SELECT ?person ?name WHERE {
  ?person a schema:Person .
  FILTER(?person != <http://example.com/excluded>)
  ?person schema:name ?name .
}
```

**3. Use Virtuoso Indexes:**
```sparql
-- Prefer bif:contains() over REGEX
SELECT ?entity ?label WHERE {
  ?entity rdfs:label ?label .
  ?label bif:contains "'search term'" option (score ?sc)
}
ORDER BY DESC(?sc)
```

**4. Batch Queries:**
```sparql
-- Use VALUES for multiple lookups
SELECT ?entity ?label WHERE {
  VALUES ?entity { 
    <http://example.com/1> 
    <http://example.com/2> 
  }
  ?entity rdfs:label ?label .
}
```

### Caching Strategies

**Endpoint-Level Caching:**
- Results may be cached at SPARQL endpoint
- Cache duration varies by endpoint (typically 5-60 minutes)
- Modify query slightly to bypass cache if needed

**Application-Level Caching:**
- Cache frequently accessed results locally
- Implement TTL based on data volatility
- Use cache keys based on query + endpoint

**Invalidation:**
- Clear cache when data updates occur
- Use cache headers when available
- Implement selective invalidation for related queries

## Database Management Tools

### Schema Exploration

**List Tables:**
```json
{
  "type": "TABLES",
  "format": "markdown"
}
```
Tool: `database_schema_objects`

**List Views:**
```json
{
  "type": "VIEWS",
  "format": "markdown"
}
```

### RDF View Generation

**From SQL Tables:**
```json
{
  "tables": ["Demo.demo.Customers", "Demo.demo.Orders"],
  "iri_path_segment": "northwind",
  "generate_void": 1
}
```
Tool: `RDFVIEW_FROM_TABLES`

**Generate Ontology:**
```json
{
  "tables": ["Demo.demo.Customers"],
  "iri_path_segment": "northwind",
  "graphql_annotations": 1
}
```
Tool: `RDFVIEW_ONTOLOGY_FROM_TABLES`

### Database Statistics

**Server Stats:**
```json
{
  "stat_type": "db_server",
  "format": "markdown"
}
```

**Index Stats:**
```json
{
  "stat_type": "index",
  "format": "markdown"
}
```

Tool: `database_statistics`

## Security and Best Practices

### Input Validation
```javascript
// ✅ DO - Validate and sanitize user input
function buildQuery(userInput) {
  const sanitized = userInput.replace(/[;\\'"]/, '');
  return `SPARQL SELECT ?s WHERE { ?s rdfs:label "${sanitized}" }`;
}

// ❌ DON'T - Direct string concatenation
function badQuery(userInput) {
  return `SPARQL SELECT ?s WHERE { ?s rdfs:label "${userInput}" }`;
}
```

### API Key Handling
```javascript
// ✅ DO - Store API keys securely
const apiKey = process.env.SPARQL_API_KEY;

// ❌ DON'T - Hard-code credentials
const apiKey = "sk-12345"; // Never do this
```

### Rate Limiting
```javascript
// ✅ DO - Implement rate limiting
const rateLimiter = new RateLimit({
  windowMs: 60000, // 1 minute
  max: 60 // 60 requests per minute
});
```

### Error Handling
```javascript
// ✅ DO - Handle errors gracefully
try {
  const results = await execute_spasql_query({sql: query});
} catch (error) {
  console.error("Query failed:", error.message);
  // Provide user-friendly error message
  return {error: "Query execution failed. Please try again."};
}
```

### Timeout Configuration
```javascript
// ✅ DO - Set appropriate timeouts
const results = await execute_spasql_query({
  sql: complexQuery,
  timeout: 60, // 60 seconds for complex queries
  max_rows: 1000 // Limit result size
});
```

## SPARQL Endpoints Reference

### Default Local Endpoint
```
https://linkeddata.uriburner.com/sparql
```

**Features:**
- Virtuoso backend
- Full-text search with bif:contains()
- Inference support
- Fast response times

### Fallback Remote Endpoints

**1. Kingsley's Instance:**
```
https://kingsley.idehen.net/sparql
```
- Personal knowledge base
- Rich HowTo content
- Best for technical documentation

**2. Demo Instance:**
```
https://demo.openlinksw.com/sparql
```
- OpenLink Software demo data
- Sample datasets
- Testing and examples

### Public Endpoints

**DBpedia:**
```
https://dbpedia.org/sparql
```
- Wikipedia structured data
- 4.6M entities
- Multilingual

**Wikidata:**
```
https://query.wikidata.org/sparql
```
- 100M+ items
- Comprehensive knowledge base
- Strong for factual data

### Describe Service Pattern

**Template:**
```
https://{endpoint_host}/describe/?uri={URL_ENCODED_IRI}
```

**Examples:**
```
https://linkeddata.uriburner.com/describe/?uri=https%3A%2F%2Fexample.com%2Fresource

https://kingsley.idehen.net/describe/?uri=https%3A%2F%2Fkingsley.idehen.net%2FDAV%2Fhome%2Ffile.pdf%23Question_1

https://dbpedia.org/describe/?uri=http%3A%2F%2Fdbpedia.org%2Fresource%2FTim_Berners-Lee
```

## Troubleshooting Guide

### Issue: No Results from Query

**Diagnosis Steps:**
1. Check if entities exist: `sparql_list_entity_types`
2. Try broader search terms
3. Enable inference: add `DEFINE input:inference`
4. Check alternate endpoints

**Example:**
```json
// Step 1: Check entity types
{
  "graph_iri": "urn:default:graph",
  "format": "markdown"
}

// Step 2: Retry with inference
{
  "sql": "SPARQL DEFINE input:inference 'urn:rdfs:subclass:subproperty:inference:rules' SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"
}
```

### Issue: Query Timeout

**Diagnosis:**
- Query too complex
- Large result set
- Slow endpoint
- Network issues

**Solutions:**
```json
// Increase timeout
{
  "sql": "SPARQL SELECT ...",
  "timeout": 60
}

// Add LIMIT
{
  "sql": "SPARQL SELECT ... LIMIT 10"
}

// Simplify query
{
  "sql": "SPARQL SELECT ?s ?p ?o WHERE { ?s ?p ?o . FILTER(?s = <specific_entity>) }"
}
```

### Issue: Syntax Error

**Common Causes:**
- Missing PREFIX declarations
- Invalid IRI format
- Incorrect SPARQL syntax
- Wrong quote types

**Solutions:**
```sparql
-- ✅ Correct PREFIX usage
PREFIX schema: <http://schema.org/>
SELECT ?s WHERE { ?s a schema:Person }

-- ✅ Valid IRI format
SELECT ?s WHERE { 
  ?s a <http://schema.org/Person> 
}

-- ✅ Proper string literals
SELECT ?s WHERE { 
  ?s rdfs:label "Tim Berners-Lee"@en 
}
```

### Issue: Authentication Error

**Solutions:**
1. Verify API key is provided
2. Check key has correct permissions
3. Ensure key is not expired
4. Test with public endpoint first

```json
// With API key
{
  "url": "https://secure-endpoint.com/sparql",
  "query": "SELECT ...",
  "apiKey": "your-api-key-here"
}
```

## Integration Examples

### Example 1: Full KG Query Workflow with Native Tools

```javascript
// Step 1: Discover entity types
const types = await execute_spasql_query({
  sql: "SPARQL SELECT ?type (COUNT(?e) AS ?count) WHERE { ?e a ?type } GROUP BY ?type ORDER BY DESC(?count) LIMIT 10",
  format: "json"
});

console.log("Available types:", types);

// Step 2: Query specific type
const questions = await execute_spasql_query({
  sql: "SPARQL SELECT ?q ?label ?answer WHERE { ?q a <http://schema.org/Question> ; rdfs:label ?label ; schema:acceptedAnswer ?ans . ?ans schema:text ?answer } LIMIT 20",
  format: "markdown"
});

console.log("Questions found:", questions);

// Step 3: If no results, try with inference
if (questions.results.length === 0) {
  const withInference = await execute_spasql_query({
    sql: "SPARQL DEFINE input:inference 'urn:rdfs:subclass:subproperty:inference:rules' SELECT ?q ?label WHERE { ?q a <http://schema.org/Question> ; rdfs:label ?label } LIMIT 20",
    format: "json"
  });
}
```

### Example 2: Multi-Source Data Aggregation

```javascript
// Query local endpoint
const local = await sparqlQuery({
  query: "SELECT ?person ?name WHERE { ?person a schema:Person ; schema:name ?name } LIMIT 10",
  format: "json"
});

// Query DBpedia
const dbpedia = await sparqlRemoteQuery({
  url: "https://dbpedia.org/sparql",
  query: "SELECT ?person ?name WHERE { ?person a dbo:Person ; foaf:name ?name } LIMIT 10",
  format: "json"
});

// Combine results with provenance
const combined = [
  ...local.results.map(r => ({...r, source: "local"})),
  ...dbpedia.results.map(r => ({...r, source: "dbpedia"}))
];
```

### Example 3: Web to KG Pipeline

```javascript
// Step 1: Fetch web content
const content = await WEB_FETCH({
  url: "https://example.com/data.html",
  timeout_seconds: 30
});

// Step 2: Convert to RDF (sponge)
const rdf = await SPONGE_URL({
  url: "https://example.com/data.html",
  format: "json"
});

// Step 3: Query the sponged data
const results = await execute_spasql_query({
  sql: "SPARQL SELECT ?s ?p ?o FROM <urn:sponged:data> WHERE { ?s ?p ?o } LIMIT 50",
  format: "markdown"
});
```

### Example 4: Citation Verification with SPARQL Agent 121

```javascript
// User explicitly requests verification
const verification = await ChatPromptComplete({
  model: "gemini-2.5-pro",
  assistant_config_id: "new-sparql-agent-121",
  prompt: "/kg-verify What is the W3C definition of RDF?",
  temperature: "0.0",
  max_tokens: 2000
});

// Agent will:
// 1. Query local KG for W3C RDF definition
// 2. Try remote endpoints if needed
// 3. Return answer with provenance links
// 4. Provide audit trail of queries executed
```

## Quick Reference

### Most Common Operations

| Task | Tool | Quick Command |
|------|------|---------------|
| Query local KG | execute_spasql_query | `SPARQL SELECT...` |
| Query with inference | execute_spasql_query | Add `DEFINE input:inference` pragma |
| Query remote KG | sparqlRemoteQuery | Specify endpoint URL |
| List entity types | sparql_list_entity_types | Provide graph IRI |
| List entity samples | sparql_list_entity_types_samples | Provide graph IRI |
| SQL query | execute_sql_query | Standard SQL (no semicolon) |
| Fetch web page | WEB_FETCH | Provide URL |
| Convert to RDF | SPONGE_URL | Provide URL |
| DB schema | database_schema_objects | Type: "TABLES", "VIEWS", etc. |
| Verify citation | ChatPromptComplete | Use `/kg-verify` command |
| Force KG workflow | ChatPromptComplete | Use `/kg-on` command |

### Default Parameters

| Parameter | Default | Notes |
|-----------|---------|-------|
| format | "json" | Use "markdown" for display |
| timeout | 30 seconds | Increase for complex queries |
| max_rows | Varies | Usually 100-1000 |
| temperature | "0.5" | ChatPromptComplete only |
| max_tokens | 1000 | ChatPromptComplete only |
| limit (SPARQL) | 10 | SPARQL Agent 121 default |

### Decision Matrix

| User Request | Use Native Tool | Use ChatPromptComplete |
|--------------|----------------|------------------------|
| "What is RDF?" | ✅ execute_spasql_query | ❌ |
| "List entity types" | ✅ sparql_list_entity_types | ❌ |
| "Query DBpedia" | ✅ sparqlRemoteQuery | ❌ |
| "Verify this citation" | ❌ | ✅ with `/kg-verify` |
| "Use SPARQL Agent" | ❌ | ✅ |
| "Use Gemini to analyze" | ❌ | ✅ |

## Version Information

- **Skill Version:** 2.1.0
- **SPARQL Agent:** 121 (v1.0.121)
- **URIBurner MCP Server:** Compatible with current versions
- **Recommended Model:** gemini-2.5-pro
- **Last Updated:** 2025-10-27

---

## Summary

**Key Takeaways:**

1. **Use Native Tools First:** execute_spasql_query, sparqlQuery, and other native MCP tools are preferred for standard operations
2. **ChatPromptComplete is Specialized:** Only invoke SPARQL Agent 121 when user explicitly requests it or for citation verification
3. **KG-First Workflow:** SPARQL Agent 121 follows a structured workflow: label match → semantic breakdown → explore → targeted query → formatted output with provenance
4. **Fallback Strategy:** If KG-first fails, try inference, remote endpoints, semantic variants, then provide audit
5. **Provenance Matters:** Always provide /describe/ links for answers with properly URL-encoded IRIs
6. **Optimize Queries:** Use bif:contains() on Virtuoso, add LIMIT clauses, filter early
7. **Multi-Endpoint:** Try local first, fall back to remote, aggregate results with source attribution

**Remember:** URIBurner's native MCP tools handle 90% of use cases efficiently. SPARQL Agent 121 via ChatPromptComplete is powerful but should be reserved for advanced workflows requiring multi-query orchestration, ontology reasoning, or explicit citation verification.
