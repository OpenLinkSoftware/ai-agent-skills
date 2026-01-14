# Showcase Examples - Virtuoso Support Agent

Complete interaction examples demonstrating key workflows.

---

## Example 1: RDF Views Generation (Complete Workflow)

### Showcase Prompt

```
"Generate RDF Views from the Customers and Orders tables in the Demo.demo schema. 
Use 'northwind' as the IRI path segment and base URL http://demo.example.com/"
```

### Complete Interaction

```
Agent: "I'll help you generate RDF Views for the Northwind database. Just to confirm, 
we're working with the Demo instance, correct?"

User: "Yes, Demo instance."

Agent: "Perfect! Let me first discover the available tables in the Demo.demo schema."

[Calls: Demo:execute_sql_query with table discovery query]

Agent: "I found these tables in Demo.demo:
- Demo.demo.Customers
- Demo.demo.Orders
- Demo.demo.Order_Details
- Demo.demo.Products
- Demo.demo.Employees
- Demo.demo.Shippers
- Demo.demo.Suppliers
- Demo.demo.Categories

You mentioned Customers and Orders. Should I proceed with these two tables:
- Demo.demo.Customers
- Demo.demo.Orders"

User: "Yes, proceed."

Agent: "Great! Now let me set up the graph IRIs. Based on your specifications:
- Base URL: http://demo.example.com/
- RDF View Graph IRI: http://demo.example.com/data/northwind
- Ontology Graph IRI: http://demo.example.com/ontology/northwind
- Ontology IRI: http://demo.example.com/schema/northwind

Let me check if these IRIs already exist..."

[Calls: Demo:sparql_list_ontologies]

Agent: "No conflicts found. These IRIs are available. Shall I proceed with creating the RDF Views?"

User: "Yes."

Agent: "Excellent! I'll now:
1. Run a metadata audit (pre-check)
2. Generate the RDF View script
3. Execute the script
4. Run a metadata audit (post-check)
5. Verify the quad maps were created

Starting now..."

[Calls: Demo:RDF_AUDIT_METADATA with audit_level: 1, format: "json"]

Agent: "✓ Pre-audit complete (Level 1). No issues found.
Generating RDF View script..."

[Calls: Demo:RDFVIEW_FROM_TABLES with:
  tables: ["Demo.demo.Customers", "Demo.demo.Orders"],
  iri_path_segment: "northwind",
  generate_void: 1
]

Agent: "✓ Script generated (428 lines). Here's a preview:

```sql
-- RDF Views for Northwind
-- Quad Storage: http://demo.example.com/data/northwind
-- Generated: 2025-11-11

SPARQL
prefix northwind: <http://demo.example.com/schema/northwind#> 
prefix oplsioc: <http://www.openlinksw.com/schemas/oplsioc#> 
prefix sioc: <http://sioc-project.org/ontology#> 
prefix foaf: <http://xmlns.com/foaf/0.1/> 

create iri class northwind:Customers "http://demo.example.com/northwind/Customers/%d" (in customer_id varchar not null)
  option (bijection, deref)
...
[428 lines total]
```

The script will create:
- 2 RDF View quad maps (Customers, Orders)
- VoID dataset description
- HTTP virtual paths

Should I execute this script?"

User: "Yes, execute it."

[Calls: Demo:EXECUTE_SQL_SCRIPT with generated script]

Agent: "✓ Script executed successfully (2.3 seconds).
Results:
- Statement 1: QuadMap for Customers created
- Statement 2: QuadMap for Orders created  
- Statement 3: VoID metadata added
- All statements: 00000 (success)

Running post-audit..."

[Calls: Demo:RDF_AUDIT_METADATA with audit_level: 2, format: "json"]

Agent: "✓ Post-audit complete (Level 2). Metadata verified.
Verifying quad maps..."

[Calls: Demo:sparqlQuery with verification query:
  PREFIX virtrdf: <http://www.openlinksw.com/schemas/virtrdf#>
  SELECT DISTINCT ?s1 as ?quadMap
  WHERE {
    ?s1 a virtrdf:QuadMap .
    ?s1 virtrdf:qmTableName ?s2 .
    FILTER (contains(str(?s1), "northwind"))
  }
]

Agent: "✓ Success! RDF Views created and verified.

**Created Quad Maps:**
- virtrdf:northwind-Demo-demo-Customers
- virtrdf:northwind-Demo-demo-Orders

**Graph IRI:** http://demo.example.com/data/northwind

**Sample SPARQL Query:**
```sparql
SELECT * 
FROM <http://demo.example.com/data/northwind>
WHERE { ?s ?p ?o }
LIMIT 10
```

**Statistics:**
- Total triples: ~2,847 (91 customers × ~15 properties + 830 orders × ~8 properties)
- Quad maps: 2
- Execution time: 2.3 seconds

Would you like me to:
1. Generate HTTP access rules for REST/Linked Data access?
2. Create an OWL ontology for the schema?
3. Sync the virtual graph to a physical graph?
4. Run a sample SPARQL query to verify the data?"

User: "Generate the HTTP access rules."

Agent: "I'll generate the HTTP virtual paths for Linked Data access."

[Calls: Demo:RDFVIEW_GENERATE_DATA_RULES with:
  iri_path_segment: "northwind",
  include_ontology_rules: 1
]

Agent: "✓ HTTP rules script generated (87 lines). Executing..."

[Calls: Demo:EXECUTE_SQL_SCRIPT with generated rules]

Agent: "✓ HTTP virtual paths created!

Your RDF Views are now accessible via:

**Linked Data URIs:**
- http://demo.example.com/northwind/Customers/ALFKI
- http://demo.example.com/northwind/Orders/10248

**SPARQL Endpoint:**
- http://demo.example.com/sparql
  - Default graph: http://demo.example.com/data/northwind

**Content Negotiation:**
- HTML (browser): Human-readable view
- RDF/XML: application/rdf+xml
- Turtle: text/turtle
- JSON-LD: application/ld+json

**Example cURL Request:**
```bash
curl -H "Accept: text/turtle" \\
  http://demo.example.com/northwind/Customers/ALFKI
```

The RDF Views generation is complete! 🎉"
```

---

## Example 2: Pricing Inquiry

### User Request

```
"What's your cheapest Virtuoso option?"
```

### Interaction

```
Agent: "I'll help you find the most affordable Virtuoso option. Just to confirm,
which instance should I query? (Typically pricing is on URIBurner)"

User: "URIBurner"

Agent: "Perfect! Searching for the cheapest option..."

[Calls: URIBurner:execute_spasql_query with cheapest driver query, timeout: 30000]

Agent: "Here's the most affordable Virtuoso option currently available:

**Virtuoso Enterprise Edition - Annual License**

- **Version:** 8.3
- **Category:** Commercial  
- **Concurrent Sessions:** 10
- **Maximum Cores:** 4
- **Network Instances:** 1
- **Price:** $1,200/year
- **Duration:** Annual
- [Add To Cart](https://shop.openlinksw.com/cart?add=VOS-8.3-10-4-1-ANNUAL)

**What's Included:**
- Full Virtuoso Universal Server
- RDF Quad Store with SPARQL 1.1
- Relational database (SQL-92/ODBC/JDBC)
- Web application server
- Technical support (email)

**Recommendation:** 
We recommend evaluating the software before purchasing to ensure it meets your needs.
Would you like me to help generate an evaluation license?

**Custom Licensing:**
Need different specifications? Contact our sales team for custom licensing:
https://www.openlinksw.com/contact"
```

---

## Example 3: Entity Discovery

### User Request

```
"What kind of data is in my Demo RDF graph?"
```

### Interaction

```
Agent: "I'll explore the entity types in your Demo instance."

[Calls: Demo:sparql_list_entity_types_samples with format: "markdown"]

Agent: "I found several entity types in your Demo RDF graph:

| Entity Type | Sample Count | Example Entities |
|-------------|--------------|------------------|
| foaf:Person | 1,245 | John Smith, Jane Doe, Bob Wilson |
| schema:Organization | 342 | Acme Corp, Tech Industries, Global Ltd |
| schema:Product | 2,891 | Widget Alpha, Gadget Pro, Tool Deluxe |
| schema:Place | 156 | New York, London, Tokyo |
| schema:Event | 89 | Conference 2024, Webinar Series |

**Total entity types:** 5
**Total entities:** ~4,723

Would you like me to:
1. Show detailed information about a specific type?
2. List all properties for an entity type?
3. Show sample data for an entity type?
4. Query relationships between types?"

User: "Show detailed information about Products."

[Calls: Demo:sparql_list_entity_types_detailed with graph filter]

Agent: "Here's detailed information about Products:

**Entity Type:** schema:Product
**Total instances:** 2,891
**Namespace:** http://schema.org/

**Common Properties:**
- schema:name (2,891 values)
- schema:description (2,847 values)
- schema:price (2,891 values)
- schema:manufacturer (2,654 values)
- schema:category (2,891 values)
- schema:sku (2,891 values)

**Sample Product:**
```turtle
<http://demo.example.com/product/12345>
  a schema:Product ;
  schema:name "Professional Widget" ;
  schema:price "299.99" ;
  schema:manufacturer <http://demo.example.com/org/acme> ;
  schema:category "Tools" .
```

Would you like to see more examples or query specific products?"
```

---

## Example 4: Installation Help

### User Request

```
"How do I install Virtuoso?"
```

### Interaction

```
Agent: "I'd be happy to help with Virtuoso installation! 
Which operating system are you using?

- macOS
- Windows  
- Linux
- Docker
- OpenLink Nexus Repo"

User: "macOS"

Agent: "Great! Let me get the installation instructions for macOS..."

[Calls: Demo:execute_spasql_query with installation How-To query filtered for macOS]

Agent: "Here are the step-by-step installation instructions for Virtuoso on macOS:

### Option 1: Homebrew (Recommended)

**Step 1: Install Homebrew** (if not already installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Step 2: Install Virtuoso**
```bash
brew install virtuoso
```

**Step 3: Start Virtuoso**
```bash
virtuoso-t -f &
```

**Step 4: Verify Installation**
```bash
isql 1111 dba dba
```

### Option 2: Binary Download

**Step 1: Download**
Visit: https://virtuoso.openlinksw.com/download/
Select: macOS Universal Binary (Intel/Apple Silicon)

**Step 2: Extract**
```bash
tar -xzf virtuoso-opensource-mac.tar.gz
cd virtuoso-opensource
```

**Step 3: Configure**
```bash
./configure --prefix=/usr/local/virtuoso
make
sudo make install
```

**Step 4: Initialize Database**
```bash
cd /usr/local/virtuoso/var/lib/virtuoso/db
virtuoso-t -f
```

### Default Configuration

- **Port:** 1111 (SQL), 8890 (HTTP)
- **Default DBA password:** dba
- **Config file:** /usr/local/var/lib/virtuoso/db/virtuoso.ini

### First Steps After Installation

1. Change DBA password:
   ```sql
   SQL> UPDATE DB.DBA.SYS_USERS SET U_PASSWORD='newpass' WHERE U_NAME='dba';
   ```

2. Access Conductor: http://localhost:8890/conductor

3. Access SPARQL endpoint: http://localhost:8890/sparql

Need help with configuration or troubleshooting? Just ask!"
```

---

## Example 5: Troubleshooting VAD Packages

### User Request

```
"My Virtuoso application isn't working after update. How do I troubleshoot?"
```

### Interaction

```
Agent: "I'll help you troubleshoot your Virtuoso application (VAD package). 
Which instance? Demo or URIBurner?"

User: "Demo"

Agent: "Here's the diagnostic procedure for VAD package issues:

### Troubleshooting Steps

**Step 1: Start Virtuoso in Debug Mode**
```bash
# Stop current instance
virtuoso-t +shutdown

# Start in foreground debug mode
virtuoso-t -df
```

**Step 2: Enable Error Tracing**

Connect via iSQL or Conductor and run:
```sql
trace_on('errors');
```

**Step 3: Reproduce the Problem**
- Try to access your application
- Perform the action that fails
- Watch the debug output in the virtuoso-t window

**Step 4: Capture Debug Output**
The server console will show detailed errors including:
- SQL errors
- PL procedure errors
- HTTP request errors
- Resource issues

### Common VAD Issues

**Installation Failures:**
```sql
-- Check VAD status
SELECT * FROM DB.DBA.VAD_REGISTRY;

-- Check for conflicts
SELECT * FROM DB.DBA.SYS_PROCEDURES 
WHERE P_NAME LIKE 'YourApp%';
```

**Missing Dependencies:**
```sql
-- List all installed VADs
vad_list_packages();

-- Check VAD dependencies
SELECT * FROM DB.DBA.VAD_REGISTRY 
WHERE R_NAME = 'your_vad_name';
```

**Resource Problems:**
Check virtuoso.ini settings:
- NumberOfBuffers
- MaxDirtyBuffers
- MaxCheckpointRemap

### Need More Help?

Send me:
1. Error messages from debug output
2. VAD package name and version
3. Virtuoso version (run: status();)

And I can provide specific solutions."
```

---

## Usage Notes

### When to Use These Examples

- **Example 1 (RDF Views):** User asks to generate RDF Views or create semantic layer
- **Example 2 (Pricing):** User asks about costs, licenses, or cheapest option
- **Example 3 (Entity Discovery):** User wants to explore what data exists
- **Example 4 (Installation):** User needs help setting up Virtuoso
- **Example 5 (Troubleshooting):** User reports problems with applications

### Adapting Examples

These examples show complete workflows. Adapt based on:
- User's technical level
- Specific requirements
- Instance selection (Demo vs URIBurner)
- Context of conversation

### Best Practices

1. Always confirm instance at start
2. Show progress indicators (✓ checkmarks)
3. Provide clear next steps
4. Offer multiple options when relevant
5. Include sample queries/commands
6. End with "what next?" options
