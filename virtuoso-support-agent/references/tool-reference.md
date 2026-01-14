# Tool Reference - Virtuoso Support Agent

Complete parameter documentation for all 23 MCP tools.

## Tool Naming Convention

**Format:** `{ServerName}:{ToolName}`
- Demo instance: `Demo:{ToolName}`
- URIBurner instance: `URIBurner:{ToolName}`

---

## Entity Discovery Tools (4 tools)

### sparql_list_entity_types
List all entity types in the RDF graph.

**Tool Names:**
- `Demo:sparql_list_entity_types`
- `URIBurner:sparql_list_entity_types`

**Parameters:**
- `graph_iri` (optional, string) - Target graph IRI
- `format` (optional, string) - Response format: "json", "jsonl", "markdown"

**Example:**
```javascript
Demo:sparql_list_entity_types({ 
  format: "markdown"
})
```

### sparql_list_entity_types_detailed
Detailed entity type listing with labels and comments.

**Tool Names:**
- `Demo:sparql_list_entity_types_detailed`
- `URIBurner:sparql_list_entity_types_detailed`

**Parameters:**
- `graph_iri` (optional, string) - Target graph IRI
- `format` (optional, string) - Response format: "json", "jsonl", "markdown"

### sparql_list_entity_types_samples
Entity type samples with counts, grouped by type.

**Tool Names:**
- `Demo:sparql_list_entity_types_samples`
- `URIBurner:sparql_list_entity_types_samples`

**Parameters:**
- `graph_iri` (optional, string) - Target graph IRI
- `format` (optional, string) - Response format: "json", "jsonl", "markdown"

### sparql_list_ontologies
List all ontologies in the RDF graph.

**Tool Names:**
- `Demo:sparql_list_ontologies`
- `URIBurner:sparql_list_ontologies`

**Parameters:**
- `graph_iri` (optional, string) - Target graph IRI
- `format` (optional, string) - Response format: "json", "jsonl", "markdown"

---

## Database Script Tools (1 tool)

### EXECUTE_SQL_SCRIPT
Execute multi-statement SQL script with semicolon delimiters.

**Tool Names:**
- `Demo:EXECUTE_SQL_SCRIPT`
- `URIBurner:EXECUTE_SQL_SCRIPT`

**Parameters:**
- `sql_script` (required, string) - SQL script with multiple statements

**Returns:** State, message, metadata, and resultset for each statement

**Example:**
```javascript
Demo:EXECUTE_SQL_SCRIPT({
  sql_script: `
    -- Statement 1
    CREATE TABLE test (id INT);
    
    -- Statement 2
    INSERT INTO test VALUES (1);
  `
})
```

---

## RDF Views Generation Tools (7 tools)

### RDFVIEW_FROM_TABLES
Generate RDF View SQL script from SQL tables.

**Tool Names:**
- `Demo:RDFVIEW_FROM_TABLES`
- `URIBurner:RDFVIEW_FROM_TABLES`

**Parameters:**
- `tables` (required, array[string]) - List of table names (catalog.schema.table)
- `iri_path_segment` (required, string) - Path component for graph IRI
- `generate_void` (optional, integer) - 0 or 1 for VoID description

**Returns:** SQL script (retain ALL special markers and syntax)

**Example:**
```javascript
Demo:RDFVIEW_FROM_TABLES({
  tables: ["Demo.demo.Customers", "Demo.demo.Orders"],
  iri_path_segment: "northwind",
  generate_void: 1
})
```

### RDFVIEW_DROP_SCRIPT
Generate SQL script to drop RDF View quad maps.

**Tool Names:**
- `Demo:RDFVIEW_DROP_SCRIPT`
- `URIBurner:RDFVIEW_DROP_SCRIPT`

**Parameters:**
- `graph_iri` (required, string) - Graph IRI of RDF View to drop

**Returns:** DROP SQL script

**Example:**
```javascript
Demo:RDFVIEW_DROP_SCRIPT({
  graph_iri: "http://example.com/data/northwind"
})
```

### RDFVIEW_GENERATE_DATA_RULES
Generate HTTP virtual paths for RDF View access.

**Tool Names:**
- `Demo:RDFVIEW_GENERATE_DATA_RULES`
- `URIBurner:RDFVIEW_GENERATE_DATA_RULES`

**Parameters:**
- `iri_path_segment` (required, string) - Path component for URL rules
- `include_ontology_rules` (optional, integer) - 0 or 1 for ontology rules

**Returns:** SQL script for HTTP virtual paths

**Example:**
```javascript
Demo:RDFVIEW_GENERATE_DATA_RULES({
  iri_path_segment: "northwind",
  include_ontology_rules: 1
})
```

### RDFVIEW_ONTOLOGY_FROM_TABLES
Generate OWL ontology from SQL tables.

**Tool Names:**
- `Demo:RDFVIEW_ONTOLOGY_FROM_TABLES`
- `URIBurner:RDFVIEW_ONTOLOGY_FROM_TABLES`

**Parameters:**
- `tables` (required, array[string]) - List of table names
- `iri_path_segment` (required, string) - Path for ontology IRI
- `graphql_annotations` (optional, integer) - 0 or 1 for GraphQL annotations

**Returns:** Turtle format ontology

**Example:**
```javascript
Demo:RDFVIEW_ONTOLOGY_FROM_TABLES({
  tables: ["Demo.demo.Customers"],
  iri_path_segment: "northwind",
  graphql_annotations: 1
})
```

### RDFVIEW_SYNC_TO_PHYSICAL_STORE
Synchronize virtual RDF view to physical graph.

**Tool Names:**
- `Demo:RDFVIEW_SYNC_TO_PHYSICAL_STORE`
- `URIBurner:RDFVIEW_SYNC_TO_PHYSICAL_STORE`

**Parameters:**
- `source_virtual_graph_iri` (required, string) - Source RDF View IRI
- `target_physical_graph_iri` (required, string) - Target physical graph IRI
- `load_data` (optional, integer) - 0 or 1 for initial data copy
- `format` (optional, string) - Response format: "json", "jsonl", "markdown"

**Example:**
```javascript
Demo:RDFVIEW_SYNC_TO_PHYSICAL_STORE({
  source_virtual_graph_iri: "http://example.com/data/northwind",
  target_physical_graph_iri: "http://example.com/data/northwind-physical",
  load_data: 1,
  format: "json"
})
```

### R2RML_FROM_TABLES
Generate R2RML Turtle document from tables.

**Tool Names:**
- `Demo:R2RML_FROM_TABLES`
- `URIBurner:R2RML_FROM_TABLES`

**Parameters:**
- `tables` (required, array[string]) - List of table names
- `iri_path_segment` (required, string) - Path for graph IRI
- `generate_void` (optional, integer) - 0 or 1 for VoID description

**Returns:** R2RML Turtle document

### R2RML_GENERATE_RDFVIEW
Generate RDF View from R2RML document.

**Tool Names:**
- `Demo:R2RML_GENERATE_RDFVIEW`
- `URIBurner:R2RML_GENERATE_RDFVIEW`

**Parameters:**
- `rml_turtle_document_or_url` (required, string) - R2RML source
- `target_default_graph_iri` (optional, string) - Default graph IRI

**Returns:** SQL script

---

## RDF Operations Tools (2 tools)

### RDF_AUDIT_METADATA
Check and repair RDF metadata consistency.

**Tool Names:**
- `Demo:RDF_AUDIT_METADATA`
- `URIBurner:RDF_AUDIT_METADATA`

**Parameters:**
- `audit_level` (required, integer) - 1: test, 2: repair, 3: deep fix
- `format` (optional, string) - Response format: "json", "jsonl", "markdown"

**Levels:**
- **Level 1:** Test only (pre-operation check)
- **Level 2:** Repair (post-operation fix)
- **Level 3:** Deep fix (when level 2 insufficient)

**Example:**
```javascript
Demo:RDF_AUDIT_METADATA({ 
  audit_level: 1, 
  format: "json" 
})
```

### RDF_BACKUP_METADATA
Backup RDF metadata.

**Tool Names:**
- `Demo:RDF_BACKUP_METADATA`
- `URIBurner:RDF_BACKUP_METADATA`

**Parameters:** None

---

## Query Execution Tools (6 tools)

### execute_spasql_query
Execute SPASQL (SQL + SPARQL) query.

**Tool Names:**
- `Demo:execute_spasql_query`
- `URIBurner:execute_spasql_query`

**Parameters:**
- `sql` (required, string) - Query text (prefix SPARQL queries with "SPARQL")
- `max_rows` (optional, integer) - Maximum rows to return
- `timeout` (optional, integer) - Timeout in milliseconds (default: 30000)
- `format` (optional, string) - Response format: "json", "jsonl", "markdown"

**Important:** Do NOT terminate query with semicolon

**Example:**
```javascript
Demo:execute_spasql_query({
  sql: "SPARQL SELECT * WHERE { ?s ?p ?o } LIMIT 10",
  timeout: 30000,
  format: "markdown"
})
```

### execute_sql_query
Execute SQL query (Demo includes Northwind database).

**Tool Names:**
- `Demo:execute_sql_query`
- `URIBurner:execute_sql_query`

**Parameters:**
- `sql` (required, string) - SQL query text
- `max_rows` (optional, integer) - Maximum rows (or use TOP N in query)
- `timeout` (optional, integer) - Timeout in milliseconds
- `format` (optional, string) - Response format: "json", "jsonl", "markdown"

**Important:** Do NOT terminate query with semicolon

**Example:**
```javascript
Demo:execute_sql_query({
  sql: "SELECT TOP 10 * FROM Demo.demo.Customers",
  format: "markdown"
})
```

### sparqlQuery
Execute SPARQL query against local endpoint.

**Tool Names:**
- `Demo:sparqlQuery`
- `URIBurner:sparqlQuery`

**Parameters:**
- `query` (required, string) - SPARQL query text
- `timeout` (optional, integer) - Timeout in milliseconds (default: 30000)
- `format` (optional, string) - Response format: "json", "jsonl", "markdown"

**Example:**
```javascript
Demo:sparqlQuery({
  query: "SELECT * WHERE { ?s ?p ?o } LIMIT 10",
  timeout: 30000,
  format: "json"
})
```

### sparqlRemoteQuery
Execute SPARQL against remote endpoint.

**Tool Names:**
- `Demo:sparqlRemoteQuery`
- `URIBurner:sparqlRemoteQuery`

**Parameters:**
- `url` (required, string) - Remote SPARQL endpoint URL
- `query` (required, string) - SPARQL query text
- `timeout` (optional, integer) - Timeout in seconds
- `format` (optional, string) - Response format: "json", "jsonl", "markdown"
- `apiKey` (optional, string) - API key for authenticated endpoints

**Example:**
```javascript
Demo:sparqlRemoteQuery({
  url: "https://dbpedia.org/sparql",
  query: "SELECT * WHERE { ?s ?p ?o } LIMIT 10",
  timeout: 30,
  format: "json"
})
```

### graphqlQuery
Execute GraphQL query.

**Tool Names:**
- `Demo:graphqlQuery`
- `URIBurner:graphqlQuery`

**Parameters:**
- `query` (required, string) - GraphQL query text
- `url` (optional, string) - GraphQL endpoint URL
- `timeout` (optional, integer) - Timeout in milliseconds

### graphqlEndpointQuery
Execute GraphQL query against specific endpoint.

**Tool Names:**
- `Demo:graphqlEndpointQuery`
- `URIBurner:graphqlEndpointQuery`

**Parameters:**
- `query` (required, string) - GraphQL query text
- `url` (required, string) - Target GraphQL endpoint URL

---

## Utility Tools (3 tools)

### chatPromptComplete
Use LLM for complex reasoning tasks.

**Tool Names:**
- `Demo:chatPromptComplete`
- `URIBurner:chatPromptComplete`

**Parameters:**
- `prompt` (required, string) - Prompt text
- `model` (optional, string) - Model identifier
- `assistant_config_id` (optional, string) - Assistant configuration ID
- `api_key` (optional, string) - API key
- `max_tokens` (optional, integer) - Maximum response tokens
- `temperature` (optional, number) - Temperature (0.0-1.0)
- `top_p` (optional, number) - Top-p sampling
- `timeout` (optional, integer) - Timeout in milliseconds
- `file_urls` (optional, array[string]) - File URLs for context
- `function_names` (optional, array[string]) - Available function names

**Use cases:**
- Query optimization suggestions
- Semantic similarity matching
- Complex troubleshooting analysis

### getModels
List available LLM models.

**Tool Names:**
- `Demo:getModels`
- `URIBurner:getModels`

**Parameters:**
- `provider` (optional, string) - Filter by provider
- `filter` (optional, string) - Filter criteria

### assistantsConfigurations
Get assistant configurations.

**Tool Names:**
- `Demo:assistantsConfigurations`
- `URIBurner:assistantsConfigurations`

**Parameters:** None

---

## Tool Usage Best Practices

### Query Execution
- Use 30,000ms timeout for predefined queries
- Use "markdown" format for human-readable results
- Use "json" for programmatic processing
- Never terminate queries with semicolon
- Use TOP N in SQL or max_rows parameter for limits

### RDF Operations
- Always run Level 1 audit before operations
- Always run Level 2 audit after operations
- Never modify generated SQL scripts
- Present scripts to user before execution

### Entity Discovery
- Start with sparql_list_entity_types for overview
- Use samples for examples
- Use detailed for deep dive
- Specify graph_iri when known

### Error Handling
- Wrap tool calls in error checking
- Validate parameters before calling
- Check for table existence
- Verify Graph IRI uniqueness
