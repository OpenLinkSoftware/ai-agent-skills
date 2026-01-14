# Workflow Details - Virtuoso Support Agent

Detailed step-by-step workflows for complex operations.

---

## RDF Views Generation Workflow (Detailed)

Complete 9-step process for generating RDF Views, OWL ontology, and Linked Data access rules from relational tables using high-level RDF Views tools.

### Prerequisites

- Target instance selected (Demo or URIBurner)
- Database and schema exist and are accessible in Virtuoso (e.g., `sqlserver.northwind`)
- Base URL decided
- User has identified source tables

### Assumptions

- **Database/schema assumed to exist:** If discovery fails, remote DSN verification is attempted (error recovery)
- **High-level tools used:** This workflow uses RDF Views generation tools, not low-level SQL tools
- **Qualified table names:** Tables are referenced with full qualification (e.g., `sqlserver.northwind.Customers`)

---

### Step 1: Confirm Target Instance

**Purpose:** Ensure correct Virtuoso instance is being used

**Actions:**
```
"I'll help you generate a Knowledge Graph. Just to confirm, we're working with the [Demo/URIBurner] instance, correct?"
```

**If user hasn't specified:**
```
"Which Virtuoso instance would you like to use?
- Demo (test/sample data)
- URIBurner (production)"
```

---

### Step 2: Table Discovery (MANDATORY)

**Purpose:** Get exact table names from database schema using qualified naming

**Tool:** `{Server}:database_schema_objects`

**Parameters:**
- `type`: "TABLES"
- `qualifier`: "sqlserver" (or appropriate database)
- `schema_filter`: "northwind" (or target schema)

**Example:**
```javascript
Demo:database_schema_objects({
  type: "TABLES",
  qualifier: "sqlserver",
  schema_filter: "northwind",
  format: "markdown"
})
```

**Expected result:**
```
Catalog: sqlserver
Schema: northwind
Tables found:
- Customers
- Orders
- Products
- Employees
- Shippers
- Categories
```

**Present to user:**
```
"I found these tables in sqlserver.northwind:
- sqlserver.northwind.Customers
- sqlserver.northwind.Orders
- sqlserver.northwind.Products
[... etc ...]

Which tables should I use for the Knowledge Graph? (Or approve all listed)"
```

**Wait for explicit approval.** Do not proceed without confirmation.

**If table discovery fails (error recovery):**
1. Verify remote DSN: `database_remote_datasources` (command: 'list')
2. If not connected, request parameters and link via `database_remote_datasources` (command: 'link')
3. Re-attempt table discovery

---

### Step 3: Graph IRI Assignments

**Purpose:** Define IRIs for RDF Views, ontology, and entity access

**IRIs to assign:**

1. **Base URL**
   - Default: `http://example.com/`
   - User may provide custom

2. **RDF View Graph IRI**
   - Format: `{base_url}/data/{iri_path_segment}`
   - Example: `http://demo.openlinksw.com/data/northwind`

3. **Ontology Graph IRI**
   - Format: `{base_url}/ontology/{iri_path_segment}`
   - Example: `http://demo.openlinksw.com/ontology/northwind`

4. **Ontology IRI**
   - Format: `{base_url}/schema/{iri_path_segment}`
   - Example: `http://demo.openlinksw.com/schema/northwind`

**Present to user:**
```
"Based on the iri_path_segment 'northwind', here are the assigned IRIs:
- RDF View Graph: http://demo.openlinksw.com/data/northwind
- Ontology Graph: http://demo.openlinksw.com/ontology/northwind
- Ontology: http://demo.openlinksw.com/schema/northwind

Are these acceptable, or would you like to modify them?"
```

**Conflict checking:**

Tool: `{Server}:sparql_list_ontologies`

```javascript
Demo:sparql_list_ontologies({
  format: "json"
})
```

**If conflicts found:**
```
"Warning: The graph IRI http://demo.openlinksw.com/data/northwind already exists.
Would you like to:
1. Use a different IRI path segment
2. Override the existing graph (requires deletion)
3. Cancel this operation"
```

**If user chooses override:**
```javascript
Demo:RDFVIEW_DROP_SCRIPT({
  graph_iri: "http://demo.openlinksw.com/data/northwind"
})
```

Then execute the DROP script with `Demo:EXECUTE_SQL_SCRIPT`.

---

### Step 4: Pre-Operation Metadata Audit

**Purpose:** Ensure RDF metadata is consistent before changes

**Tool:** `{Server}:RDF_AUDIT_METADATA`

**Parameters:**
- `audit_level`: 1 (test only)
- `format`: "json"

**Example:**
```javascript
Demo:RDF_AUDIT_METADATA({
  audit_level: 1,
  format: "json"
})
```

**Expected result:** Clean bill of health

**If issues found:**
```
"Pre-audit detected [N] metadata issues. Would you like me to:
1. Run Level 2 audit to repair
2. Proceed with RDF View creation anyway
3. Cancel operation"
```

**If user chooses repair:**
```javascript
Demo:RDF_AUDIT_METADATA({
  audit_level: 2,
  format: "json"
})
```

---

### Step 5: Generate RDF Views, Ontology, and Data Rules

**Purpose:** Generate all three required artifacts using high-level RDF Views tools

This step generates three complete SQL scripts using specialized RDF Views generation tools.

#### 5a: Generate RDF View Script

**Tool:** `{Server}:RDFVIEW_FROM_TABLES`

**Parameters:**
- `tables`: Array of approved qualified table names
- `iri_path_segment`: "northwind"
- `generate_void`: 1 (recommended for metadata)

**Example:**
```javascript
Demo:RDFVIEW_FROM_TABLES({
  tables: [
    "sqlserver.northwind.Customers",
    "sqlserver.northwind.Orders",
    "sqlserver.northwind.Products"
  ],
  iri_path_segment: "northwind",
  generate_void: 1
})
```

**Output:** SQL script with SPARQL prefix definitions and quad map creation statements

#### 5b: Generate OWL Ontology (REQUIRED)

**Tool:** `{Server}:RDFVIEW_ONTOLOGY_FROM_TABLES`

**Parameters:**
- `tables`: Same array as 5a
- `iri_path_segment`: "northwind"
- `graphql_annotations`: 1 (optional GraphQL support)

**Example:**
```javascript
Demo:RDFVIEW_ONTOLOGY_FROM_TABLES({
  tables: [
    "sqlserver.northwind.Customers",
    "sqlserver.northwind.Orders",
    "sqlserver.northwind.Products"
  ],
  iri_path_segment: "northwind",
  graphql_annotations: 1
})
```

**Output:** OWL ontology (Turtle format) with class and property definitions

#### 5c: Generate Linked Data Access Rules (REQUIRED)

**Tool:** `{Server}:RDFVIEW_GENERATE_DATA_RULES`

**Parameters:**
- `iri_path_segment`: "northwind"
- `include_ontology_rules`: 1

**Example:**
```javascript
Demo:RDFVIEW_GENERATE_DATA_RULES({
  iri_path_segment: "northwind",
  include_ontology_rules: 1
})
```

**Output:** SQL script with HTTP rewrite rules for entity lookup

**Present to user:**
```
"✓ All scripts generated successfully!

Generated artifacts:
1. RDF View SQL script ([N] lines)
2. OWL Ontology ([M] lines)
3. Data Rules/Rewrite script ([P] lines)

This will create:
- Quad maps for all northwind tables
- OWL ontology with entity types and properties
- HTTP access paths for Linked Data discovery
- Content negotiation support (RDF/XML, N-Triples, JSON-LD)

HTTP Access patterns:
- /about/resource/Customers/[id]
- /about/resource/Orders/[id]
- /data/northwind (RDF Graph)

Should I execute these scripts?"
```

**CRITICAL:** Never modify generated scripts. Present exactly as returned.

---

### Step 6: Execute All Generated Scripts

**Purpose:** Apply all generated scripts to create quad maps, ontology, and data rules

**Tool:** `{Server}:EXECUTE_SQL_SCRIPT`

**Execute each script in order:**

#### 6a: Execute RDF View Script
```javascript
Demo:EXECUTE_SQL_SCRIPT({
  sql_script: "[exact RDF View script from Step 5a]"
})
```

#### 6b: Execute Data Rules Script (Ontology embedded in rules)
```javascript
Demo:EXECUTE_SQL_SCRIPT({
  sql_script: "[exact Data Rules script from Step 5c]"
})
```

**Monitor execution:**
- Check each statement's return code
- 00000 = success
- Any other code = error

**Report results:**
```
"✓ Scripts executed successfully!

Results:
- RDF Views created: [N] quad maps
- Ontology loaded: [M] classes and properties
- Data rules deployed: [P] HTTP access paths
- All statements: Success (00000)"
```

**If errors occur:**
```
"⚠ Execution encountered errors:
- Statement [N]: [error_code] - [error_message]

This may indicate:
1. Table permissions issue
2. Conflicting quad map
3. Invalid IRI format
4. Resource constraint

Would you like me to:
1. Show full error details
2. Attempt to fix and retry
3. Roll back changes"
```

---

### Step 7: Post-Operation Metadata Audit

**Purpose:** Verify metadata consistency after all changes

**Tool:** `{Server}:RDF_AUDIT_METADATA`

**Parameters:**
- `audit_level`: 2 (repair mode)
- `format`: "json"

**Example:**
```javascript
Demo:RDF_AUDIT_METADATA({
  audit_level: 2,
  format: "json"
})
```

**Expected result:** All checks pass, any minor issues auto-repaired

**If issues found:**
```
"Post-audit results:
- [N] issues detected
- [M] issues auto-repaired
- [P] issues require attention

[Details of remaining issues]

Would you like me to run Level 3 audit (deep repair)?"
```

---

### Step 8: Verify Quad Maps and Ontology Created

**Purpose:** Confirm quad maps and ontology exist in registry

**Tool:** `{Server}:sparqlQuery`

**Query for quad maps:**
```sparql
PREFIX virtrdf: <http://www.openlinksw.com/schemas/virtrdf#>

SELECT DISTINCT ?s1 as ?quadMap ?table
WHERE {
  ?s1 a virtrdf:QuadMap .
  ?s1 virtrdf:qmTableName ?table .
  FILTER (contains(str(?s1), "northwind"))
}
ORDER BY ?quadMap
```

**Example:**
```javascript
Demo:sparqlQuery({
  query: "PREFIX virtrdf: <http://www.openlinksw.com/schemas/virtrdf#> SELECT DISTINCT ?s1 as ?quadMap ?table WHERE { ?s1 a virtrdf:QuadMap . ?s1 virtrdf:qmTableName ?table . FILTER (contains(str(?s1), 'northwind')) } ORDER BY ?quadMap",
  timeout: 30000,
  format: "json"
})
```

**Expected result:**
```
[
  {
    "quadMap": "http://www.openlinksw.com/schemas/virtrdf#northwind-sqlserver-northwind-Customers",
    "table": "sqlserver.northwind.Customers"
  },
  {
    "quadMap": "http://www.openlinksw.com/schemas/virtrdf#northwind-sqlserver-northwind-Orders",
    "table": "sqlserver.northwind.Orders"
  }
]
```

**Query for ontology:**
```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT DISTINCT ?class
WHERE {
  GRAPH <http://demo.openlinksw.com/ontology/northwind> {
    ?class a owl:Class .
  }
}
ORDER BY ?class
```

**Report:**
```
"✓ Verification Complete!

Quad Maps Created:
- virtrdf:northwind-sqlserver-northwind-Customers
- virtrdf:northwind-sqlserver-northwind-Orders
- virtrdf:northwind-sqlserver-northwind-Products
[... etc ...]

Ontology Classes Defined:
- northwind:Customers
- northwind:Orders
- northwind:Products
[... etc ...]

RDF Graph IRI: http://demo.openlinksw.com/data/northwind
Ontology IRI: http://demo.openlinksw.com/schema/northwind"
```

---

### Step 9: Validate Knowledge Graph

**Purpose:** Confirm Knowledge Graph is coherent and accessible

**Tool:** `{Server}:sparqlQuery`

**Query to sample entities by type:**
```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?entityType (SAMPLE(?entity) AS ?sampleEntity) (COUNT(?entity) AS ?count)
WHERE {
  GRAPH <http://demo.openlinksw.com/data/northwind> {
    ?entity rdf:type ?entityType .
  }
}
GROUP BY ?entityType
ORDER BY DESC(?count)
LIMIT 20
```

**Example:**
```javascript
Demo:sparqlQuery({
  query: "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> SELECT ?entityType (SAMPLE(?entity) AS ?sampleEntity) (COUNT(?entity) AS ?count) WHERE { GRAPH <http://demo.openlinksw.com/data/northwind> { ?entity rdf:type ?entityType . } } GROUP BY ?entityType ORDER BY DESC(?count) LIMIT 20",
  timeout: 30000,
  format: "markdown"
})
```

**Present results:**
```
"Knowledge Graph Validation Complete!

Entity Distribution:
| Entity Type | Sample Entity | Count |
|---|---|---|
| northwind:Customers | northwind:Customers/ALFKI | 91 |
| northwind:Orders | northwind:Orders/10248 | 830 |
| northwind:Products | northwind:Products/1 | 77 |
| northwind:Employees | northwind:Employees/1 | 9 |
| northwind:Shippers | northwind:Shippers/1 | 3 |
| northwind:Categories | northwind:Categories/1 | 8 |

Total entities: ~1,018
Estimated triples: ~15,500+

RDF Graph: http://demo.openlinksw.com/data/northwind
Ontology: http://demo.openlinksw.com/schema/northwind

Linked Data Access Enabled:
✅ SPARQL queries: http://demo.openlinksw.com/sparql
✅ GraphQL queries: Yes (ontology annotations enabled)
✅ HTTP entity access: http://demo.openlinksw.com/about/resource/Customers/ALFKI
✅ Content negotiation: RDF/XML, N-Triples, JSON-LD, HTML

Your Knowledge Graph is production-ready!"
```

---

## Error Recovery Procedures

### Table Not Found (Step 2 failure)

1. Verify table name spelling and case sensitivity
2. Confirm schema name: `database_schema_objects` with `schema_filter`
3. Verify table permissions
4. **If still not found, attempt remote DSN verification:**
   - Run: `database_remote_datasources` (command: 'list')
   - Check if database is in connected sources
   - If not: Link/attach via `database_remote_datasources` (command: 'link')
   - Retry table discovery

### IRI Conflict (Step 3)

1. Use different `iri_path_segment` value
2. OR delete existing RDF Views first:
   - `RDFVIEW_DROP_SCRIPT` for old graph IRI
   - Execute drop script with `EXECUTE_SQL_SCRIPT`
3. Retry with new IRI

### Script Execution Failure (Step 6)

1. Check error code and message
2. Verify table access: `SELECT * FROM [table] LIMIT 1`
3. Check Virtuoso logs
4. Verify SPARQL_SELECT permissions
5. Re-run pre-audit (Step 4) and retry

### Metadata Audit Failures (Steps 4, 7)

1. Run Level 2 audit (repair)
2. If still failing, run Level 3 (deep repair)
3. Check RDF metadata tables manually
4. Consider database restart

### Remote DSN Connection Issues

**When table discovery fails and remote DSN is attempted:**

1. Verify connection parameters (host, port, database)
2. Check database user permissions
3. Verify network connectivity
4. Check Virtuoso logs for connection details
5. Try alternate DSN parameters

---

## Best Practices

1. **Always follow steps in order** - Each step depends on previous
2. **Get user approval** - At Steps 2 (tables), 3 (IRIs), 6 (execution)
3. **Never skip audits** - Steps 4 and 7 are critical for metadata health
4. **Retain scripts** - Never modify generated SQL or ontology scripts
5. **Verify each stage** - Steps 8 and 9 validate your Knowledge Graph
6. **Use qualified names** - Always reference tables with full qualification (e.g., `sqlserver.northwind.Customers`)
7. **Document IRIs** - Keep record of all assigned IRIs
8. **Test Linked Data** - After Step 6, test HTTP entity access via `/about/resource/[type]/[id]`
9. **Use high-level tools** - RDF Views tools handle all complexity
10. **Assume database exists** - Only attempt remote DSN on discovery failure

**Purpose:** For external databases (SQL Server, PostgreSQL, MySQL, Oracle), establish connectivity before proceeding

**When required:** Only if source database is NOT native to Virtuoso

**Tool:** `{Server}:database_remote_datasources` (command: 'list')

**Actions:**

1. **List existing connections:**
```javascript
Demo:database_remote_datasources({
  command: "list",
  format: "markdown"
})
```

2. **If source database not connected:**
```
"I need to verify connection to your [sqlserver/postgresql/mysql] database.
Please provide:
- Host: [hostname or IP]
- Port: [port number]
- Database: [database name]
- Schema: [schema name]
- Username: [database user]
- Password: [encrypted or request from secure store]"
```

3. **Link/Attach the remote source:**
```javascript
Demo:database_remote_datasources({
  command: "link",
  dsn: "sqlserver_northwind",
  user_name: "sa",
  user_password: "[password]",
  format: "markdown"
})
```

4. **Verify connectivity:**
```javascript
Demo:execute_sql_query({
  sql: "SELECT * FROM sqlserver.information_schema.tables WHERE table_schema = 'dbo' LIMIT 5",
  format: "markdown"
})
```

**Expected result:**
```
"✓ Connection established to SQL Server
Available schemas in [database]:
- dbo
- sales
- hr
[... etc ...]

Proceeding to table discovery in schema '[schema_name]'."
```

**If connection fails:**
```
"⚠ Connection failed. Possible causes:
1. Incorrect host/port
2. Database user permissions
3. Network connectivity
4. Firewall restrictions

Would you like to:
1. Retry with different parameters
2. Check Virtuoso logs for details
3. Cancel operation"
```

**Store connection details for future reference:**
```
"✓ Remote data source 'sqlserver_northwind' is now available for use."
```

---

### Step 1: Confirm Target Instance

**Purpose:** Ensure correct instance is being used

**Actions:**
```
"I'll help you generate RDF Views. Just to confirm, we're working with the [Demo/URIBurner] instance, correct?"
```

**If user hasn't specified:**
```
"Which Virtuoso instance would you like to use?
- Demo (test/sample data)
- URIBurner (production)"
```

---

### Step 2: Table Discovery (MANDATORY)

**Purpose:** Get exact table names from database schema

**Why mandatory:** User-provided table names may be incorrect or incomplete. Always verify against actual schema.

**For remote databases:** Scope discovery to the linked schema (e.g., `sqlserver.dbo`)

**Tool:** `{Server}:execute_sql_query`

**Query (local schema):**
```sql
SELECT 
  name_part(KEY_TABLE, 0) AS catalog,
  name_part(KEY_TABLE, 1) AS schema,
  name_part(KEY_TABLE, 2) AS table_name
FROM DB.DBA.SYS_KEYS 
WHERE KEY_IS_MAIN = 1 
  AND name_part(KEY_TABLE, 1) = 'demo'  -- Replace with target schema
ORDER BY table_name
```

**Query (remote schema example):**
```sql
SELECT * FROM sqlserver.information_schema.tables 
WHERE table_schema = 'dbo'
ORDER BY table_name
```

**Example (local):**
```javascript
Demo:execute_sql_query({
  sql: "SELECT name_part(KEY_TABLE, 0) AS catalog, name_part(KEY_TABLE, 1) AS schema, name_part(KEY_TABLE, 2) AS table_name FROM DB.DBA.SYS_KEYS WHERE KEY_IS_MAIN = 1 AND name_part(KEY_TABLE, 1) = 'demo' ORDER BY table_name",
  format: "markdown"
})
```

**Example (remote):**
```javascript
Demo:execute_sql_query({
  sql: "SELECT * FROM sqlserver.information_schema.tables WHERE table_schema = 'dbo'",
  format: "markdown"
})
```

**Present results:**
```
"I found these tables in Demo.demo:
- Demo.demo.Customers
- Demo.demo.Orders
- Demo.demo.Products
[... etc ...]

You mentioned [X and Y]. Should I proceed with:
- Demo.demo.[X]
- Demo.demo.[Y]"
```

**Wait for explicit approval.** Do not proceed without confirmation.

**Error handling:**
- If table not found, inform user and re-list available tables
- If schema doesn't exist, check catalog name
- Always use full catalog.schema.table format

---

### Step 3: Graph IRI Assignments

**Purpose:** Define all IRIs with user approval

**IRIs to assign:**

1. **Base URL**
   - Default: `http://example.com/`
   - User may provide custom

2. **RDF View Graph IRI**
   - Format: `{base_url}/data/{iri_path_segment}`
   - Example: `http://demo.example.com/data/northwind`

3. **Ontology Graph IRI**
   - Format: `{base_url}/ontology/{iri_path_segment}`
   - Example: `http://demo.example.com/ontology/northwind`

4. **Ontology IRI**
   - Format: `{base_url}/schema/{iri_path_segment}`
   - Example: `http://demo.example.com/schema/northwind`

**Present to user:**
```
"Based on your IRI path segment 'northwind' and base URL, here are the assigned IRIs:
- RDF View Graph: http://demo.example.com/data/northwind
- Ontology Graph: http://demo.example.com/ontology/northwind  
- Ontology: http://demo.example.com/schema/northwind

Are these acceptable, or would you like to modify them?"
```

**Conflict checking:**

Tool: `{Server}:sparql_list_ontologies`

```javascript
Demo:sparql_list_ontologies({
  format: "json"
})
```

**If conflicts found:**
```
"Warning: The graph IRI http://demo.example.com/data/northwind already exists.
Would you like to:
1. Use a different IRI path segment
2. Override the existing graph (requires deletion)
3. Cancel this operation"
```

**If user chooses override:**
Must first delete existing quad maps:

```javascript
Demo:RDFVIEW_DROP_SCRIPT({
  graph_iri: "http://demo.example.com/data/northwind"
})
```

Then execute the DROP script with `Demo:EXECUTE_SQL_SCRIPT`.

---

### Step 4: Pre-Operation Metadata Audit

**Purpose:** Ensure RDF metadata is consistent before changes

**Tool:** `{Server}:RDF_AUDIT_METADATA`

**Parameters:**
- `audit_level`: 1 (test only)
- `format`: "json"

**Example:**
```javascript
Demo:RDF_AUDIT_METADATA({
  audit_level: 1,
  format: "json"
})
```

**Expected result:** Clean bill of health

**If issues found:**
```
"Pre-audit detected [N] metadata issues. Would you like me to:
1. Run Level 2 audit to repair
2. Proceed with RDF View creation anyway
3. Cancel operation"
```

**If user chooses repair:**
```javascript
Demo:RDF_AUDIT_METADATA({
  audit_level: 2,
  format: "json"
})
```

---

### Step 5: Generate RDF View Script

**Purpose:** Create SQL script for RDF View quad maps

**Tool:** `{Server}:RDFVIEW_FROM_TABLES`

**Parameters:**
- `tables`: Array of full table names from Step 2
- `iri_path_segment`: From Step 3
- `generate_void`: 1 (recommended for metadata)

**Example:**
```javascript
Demo:RDFVIEW_FROM_TABLES({
  tables: [
    "Demo.demo.Customers",
    "Demo.demo.Orders"
  ],
  iri_path_segment: "northwind",
  generate_void: 1
})
```

**Script structure:**
```sql
-- RDF Views for [iri_path_segment]
-- Quad Storage: [graph_iri]
-- Generated: [timestamp]

SPARQL
prefix [prefix]: <[namespace]>
...

create iri class [class_name] "[IRI_template]" (...)
  option (bijection, deref)

create quad storage [virtrdf:storage_name]
  ...

grant select on [table] to SPARQL_SELECT
...
```

**Present to user:**
```
"✓ Script generated ([N] lines). Preview:
[Show first 20 lines]
...
[Show last 10 lines]

This script will create:
- [N] RDF View quad maps
- VoID dataset description
- SPARQL access grants

Should I execute this script?"
```

**CRITICAL:** Never modify the generated script. Present exactly as returned.

---

### Step 6: Execute RDF View Script

**Purpose:** Apply the generated script to create quad maps

**Tool:** `{Server}:EXECUTE_SQL_SCRIPT`

**Parameters:**
- `sql_script`: Exact output from Step 5

**Example:**
```javascript
Demo:EXECUTE_SQL_SCRIPT({
  sql_script: "[exact script from Step 5]"
})
```

**Monitor execution:**
- Check each statement's return code
- 00000 = success
- Any other code = error

**Report results:**
```
"✓ Script executed successfully ([time] seconds).
Results:
- Statement 1: QuadMap for Customers created (00000)
- Statement 2: QuadMap for Orders created (00000)
- Statement 3: VoID metadata added (00000)
- All statements: Success"
```

**If errors occur:**
```
"⚠ Execution encountered errors:
- Statement [N]: [error_code] - [error_message]

This may indicate:
1. Table permissions issue
2. Conflicting quad map
3. Invalid IRI format
4. Resource constraint

Would you like me to:
1. Show full error details
2. Attempt to fix and retry
3. Roll back changes"
```

---

### Step 7: Post-Operation Metadata Audit

**Purpose:** Verify metadata consistency after changes

**Tool:** `{Server}:RDF_AUDIT_METADATA`

**Parameters:**
- `audit_level`: 2 (repair mode)
- `format`: "json"

**Example:**
```javascript
Demo:RDF_AUDIT_METADATA({
  audit_level: 2,
  format: "json"
})
```

**Expected result:** All checks pass, any minor issues auto-repaired

**If issues found:**
```
"Post-audit results:
- [N] issues detected
- [M] issues auto-repaired
- [P] issues require attention

[Details of remaining issues]

Would you like me to run Level 3 audit (deep repair)?"
```

---

### Step 8: Verify Quad Maps Created

**Purpose:** Confirm quad maps exist in registry

**Tool:** `{Server}:sparqlQuery`

**Query:**
```sparql
PREFIX virtrdf: <http://www.openlinksw.com/schemas/virtrdf#>

SELECT DISTINCT ?s1 as ?quadMap ?table
WHERE {
  ?s1 a virtrdf:QuadMap .
  ?s1 virtrdf:qmTableName ?table .
  FILTER (contains(str(?s1), "[iri_path_segment]"))
}
ORDER BY ?quadMap
```

**Example:**
```javascript
Demo:sparqlQuery({
  query: "PREFIX virtrdf: <http://www.openlinksw.com/schemas/virtrdf#> SELECT DISTINCT ?s1 as ?quadMap ?table WHERE { ?s1 a virtrdf:QuadMap . ?s1 virtrdf:qmTableName ?table . FILTER (contains(str(?s1), 'northwind')) } ORDER BY ?quadMap",
  timeout: 30000,
  format: "json"
})
```

**Expected result:**
```
[
  {
    "quadMap": "http://www.openlinksw.com/schemas/virtrdf#northwind-Demo-demo-Customers",
    "table": "Demo.demo.Customers"
  },
  {
    "quadMap": "http://www.openlinksw.com/schemas/virtrdf#northwind-Demo-demo-Orders",
    "table": "Demo.demo.Orders"
  }
]
```

**Report:**
```
"✓ Verification complete!

Created Quad Maps:
- virtrdf:northwind-Demo-demo-Customers
- virtrdf:northwind-Demo-demo-Orders

Graph IRI: http://demo.example.com/data/northwind"
```

---

### Step 9: Sample Data Verification

**Purpose:** Confirm data is accessible via SPARQL

**Tool:** `{Server}:sparqlQuery`

**Query:**
```sparql
SELECT *
FROM <http://demo.example.com/data/northwind>
WHERE { ?s ?p ?o }
LIMIT 10
```

**Example:**
```javascript
Demo:sparqlQuery({
  query: "SELECT * FROM <http://demo.example.com/data/northwind> WHERE { ?s ?p ?o } LIMIT 10",
  timeout: 30000,
  format: "markdown"
})
```

**Present results:**
```
"Sample data from RDF View:

| Subject | Predicate | Object |
|---------|-----------|--------|
| northwind:Customers/ALFKI | rdf:type | northwind:Customers |
| northwind:Customers/ALFKI | northwind:CompanyName | "Alfreds Futterkiste" |
[... 10 rows ...]

Total triples estimated: ~[N]"
```

---

### Step 10: Generate OWL Ontology (REQUIRED)

### Step 10: Generate OWL Ontology (REQUIRED)

**Purpose:** Create OWL ontology from relational schema for semantic understanding and optional GraphQL access

**Tool:** `{Server}:RDFVIEW_ONTOLOGY_FROM_TABLES`

**Parameters:**
- `tables`: Same array from Step 2
- `iri_path_segment`: Same as Step 3
- `graphql_annotations`: 1 (recommended for GraphQL support)

**Example:**
```javascript
Demo:RDFVIEW_ONTOLOGY_FROM_TABLES({
  tables: ["Demo.demo.Customers", "Demo.demo.Orders"],
  iri_path_segment: "northwind",
  graphql_annotations: 1
})
```

**Output:**
```turtle
@prefix northwind: <http://demo.example.com/schema/northwind#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

northwind:Customers a owl:Class ;
  rdfs:label "Customers" ;
  rdfs:comment "Customer entity" .

northwind:CompanyName a owl:DatatypeProperty ;
  rdfs:domain northwind:Customers ;
  rdfs:range xsd:string .
```

**Present to user:**
```
"✓ OWL Ontology generated ([N] lines)
- Entity types: [N]
- Properties: [N]
- Classes: [N]

Graph IRI: http://demo.example.com/ontology/northwind
Ontology IRI: http://demo.example.com/schema/northwind

The ontology defines semantic structure for your Knowledge Graph and enables GraphQL queries."
```

---

### Step 11: Generate Linked Data Access Rules (REQUIRED)

**Purpose:** Create HTTP/Linked Data rewrite rules for entity lookups via HTTP content negotiation

**Tool:** `{Server}:RDFVIEW_GENERATE_DATA_RULES`

**Parameters:**
- `iri_path_segment`: Same as Step 3
- `include_ontology_rules`: 1 (recommended)

**Example:**
```javascript
Demo:RDFVIEW_GENERATE_DATA_RULES({
  iri_path_segment: "northwind",
  include_ontology_rules: 1
})
```

**Output:** SQL script with HTTP virtual paths:
```sql
-- HTTP Virtual Paths for Linked Data Entity Lookups
-- Generated: [timestamp]

DB.DBA.URLREWRITE_CREATE_RULELIST (
  'northwind_rules',
  1,
  vector(
    'about/resource/Customers/(.*)',
    'about/resource/$U1',
    vector('id'),
    2,
    '/sparql?query=...',
    vector('_accept', 'output'),
    '',
    '',
    NULL,
    303
  )
)
...
```

**Present to user:**
```
"✓ Linked Data rewrite rules generated ([N] rules)

Access patterns enabled:
1. Entity URIs: http://demo.example.com/about/resource/Customers/[id]
2. Property URIs: http://demo.example.com/about/property/[property]
3. Data URIs: http://demo.example.com/data/northwind
4. Ontology URIs: http://demo.example.com/ontology/northwind

Content negotiation:
- Accept: application/rdf+xml → RDF/XML
- Accept: application/n-triples → N-Triples
- Accept: application/ld+json → JSON-LD
- Accept: text/html → HTML representation

Should I execute these rules?"
```

**Execute rules:**
```javascript
Demo:EXECUTE_SQL_SCRIPT({
  sql_script: "[exact script from RDFVIEW_GENERATE_DATA_RULES]"
})
```

---

### Step 12: Validate Knowledge Graph Entity Distribution

**Purpose:** Sample entities by type to verify Knowledge Graph coherence and completeness

**Tool:** `{Server}:sparqlQuery`

**Query:**
```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?entityType (SAMPLE(?entity) AS ?sampleEntity) (COUNT(?entity) AS ?count)
WHERE {
  GRAPH <http://demo.example.com/data/northwind> {
    ?entity rdf:type ?entityType .
  }
}
GROUP BY ?entityType
ORDER BY DESC(?count)
LIMIT 20
```

**Example:**
```javascript
Demo:sparqlQuery({
  query: "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> SELECT ?entityType (SAMPLE(?entity) AS ?sampleEntity) (COUNT(?entity) AS ?count) WHERE { GRAPH <http://demo.example.com/data/northwind> { ?entity rdf:type ?entityType . } } GROUP BY ?entityType ORDER BY DESC(?count) LIMIT 20",
  timeout: 30000,
  format: "markdown"
})
```

**Expected result:**
```
| Entity Type | Sample Entity | Count |
|---|---|---|
| northwind:Customers | northwind:Customers/ALFKI | 91 |
| northwind:Orders | northwind:Orders/10248 | 830 |
| northwind:Products | northwind:Products/1 | 77 |
| northwind:Employees | northwind:Employees/1 | 9 |

Total entities: ~1,007
Total triples: ~15,342
```

**Present to user:**
```
"✓ Knowledge Graph Validation Complete!

Entity Type Distribution:
- Customers: 91 entities
- Orders: 830 entities
- Products: 77 entities
- Employees: 9 entities

Total entities: ~1,007
Estimated triples: ~15,342

RDF View Graph: http://demo.example.com/data/northwind
Ontology: http://demo.example.com/ontology/northwind
Linked Data Access: http://demo.example.com/about/resource/Customers/[id]

Your Knowledge Graph is ready for:
1. SPARQL querying
2. GraphQL querying (if ontology has GraphQL annotations)
3. Linked Data entity discovery via HTTP content negotiation
4. Semantic reasoning and RDFS/OWL inference"
```

---
