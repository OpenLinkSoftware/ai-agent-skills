# Query Templates - Virtuoso Support Agent

Predefined SPARQL and SQL queries for common tasks. All queries use 30,000ms timeout unless specified.

## Usage Format

```javascript
{SelectedServer}:execute_spasql_query({
  sql: "[query below]",
  timeout: 30000,
  format: "json" // or "markdown"
})
```

---

## FAQ Queries

### FAQ Question Index (Step 1)

Build index of available questions:

```sql
SPARQL 
SELECT ?question ?questionName
FROM <urn:openlink:assistants:data>
WHERE {
  ?question a schema:Question;
            schema:name ?questionName.
}
```

**Usage:** Execute first, then use semantic similarity to find best match.

### FAQ Answer Retrieval (Step 2)

Retrieve answer for matched question:

```sql
SPARQL 
SELECT ?answer ?answerText
FROM <urn:openlink:assistants:data>
WHERE {
  <question_uri> schema:acceptedAnswer ?answer.
  ?answer schema:text ?answerText.
}
```

**Note:** Replace `<question_uri>` with URI from Step 1.

### FAQ Fallback Query

Use when similarity search returns empty:

```sql
SPARQL 
SELECT DISTINCT ?answerText 
FROM <https://virtuoso.openlinksw.com/data/turtle/general/virtuoso-licensing-related-faq.ttl>  
FROM <https://virtuoso.openlinksw.com/data/turtle/general/virtuoso-faq-top-questions.ttl> 
FROM <https://www.openlinksw.com/data/turtle/general/virtuoso-cios-cdos-faq.ttl>  
FROM <https://www.openlinksw.com/data/turtle/general/virtuoso-llms-for-cios-cdos-faq.ttl> 
FROM <https://virtuoso.openlinksw.com/data/turtle/general/virtuoso-sys-monitoring-top-questions.ttl> 
FROM <https://virtuoso.openlinksw.com/data/turtle/general/personal-assistant-top-questions.ttl> 
WHERE { 
  ?page a schema:FAQPage; 
        schema:mainEntity ?question. 
  ?question schema:name ?name; 
            schema:acceptedAnswer ?answer. 
  ?answer schema:text ?answerText.  
} 
ORDER BY ASC(?sc)
```

---

## Pricing Queries

**Note:** Pricing queries typically use URIBurner instance.

### Cheapest Driver Query

**Trigger:** "cheapest driver available"  
**Format:** Return as list with "Add To Cart" as separate bullet

```sql
SPARQL 
PREFIX oploffer: <http://www.openlinksw.com/ontology/offers#> 
PREFIX oplsoft: <http://www.openlinksw.com/ontology/software#> 
PREFIX opllic: <http://www.openlinksw.com/ontology/licenses#> 
PREFIX schema: <http://schema.org/> 

SELECT DISTINCT 
  ?version 
  (bif:initcap(?category) as ?category) 
  ?sessions 
  ?cores 
  ?hosts 
  ?price 
  ('Annual' as ?duration) 
  (GROUP_CONCAT(DISTINCT CONCAT('<a class="opal-cart-item" href="', ?addToCart, '" target="_blank">Add To Cart</a>')) as ?buyAction) 
FROM <urn:openlink:assistants:data> 
WHERE { 
  BIND(now() as ?date) 
  ?offer a schema:Offer; 
    schema:validThrough ?validDate; 
    schema:category ?category; 
    schema:itemOffered ?item; 
    schema:name ?offerName; 
    schema:price ?price; 
    schema:url ?url; 
    schema:potentialAction ?addToCart. 
  FILTER (?validDate > ?date && bif:contains(?offerName, 'Virtuoso')). 
  ?item opllic:hasSessions ?sessions; 
    opllic:hasMaximumProcessorCores ?cores; 
    opllic:maxNetworkInstance ?hosts; 
    opllic:productLicenseOf ?product; 
    opllic:hasDuration <http://data.openlinksw.com/oplweb/license/License-Duration#annual>. 
  ?product schema:version ?version. 
} 
ORDER BY ASC(?price) 
LIMIT 1
```

**Post-query message:** Return info as list, mention custom licenses at https://www.openlinksw.com/contact

### Special Offers Query

**Trigger:** "pricing" or "special offers"  
**Returns:** Top 3 offers

```sql
SPARQL 
PREFIX oploffer: <http://www.openlinksw.com/ontology/offers#> 
PREFIX oplsoft: <http://www.openlinksw.com/ontology/software#> 
PREFIX opllic: <http://www.openlinksw.com/ontology/licenses#> 
PREFIX schema: <http://schema.org/> 

SELECT DISTINCT 
  ?version 
  (bif:initcap(?category) as ?category) 
  ?sessions 
  ?cores 
  ?hosts 
  ?price 
  ('Annual' as ?duration) 
  (GROUP_CONCAT(DISTINCT CONCAT('<a class="opal-cart-item" href="', ?addToCart, '" target="_blank">Add To Cart</a>')) as ?buyAction) 
FROM <urn:openlink:assistants:data> 
WHERE { 
  BIND(now() as ?date) 
  ?offer a schema:Offer; 
    schema:validThrough ?validDate; 
    schema:category ?category; 
    schema:itemOffered ?item; 
    schema:name ?offerName; 
    schema:price ?price; 
    schema:url ?url; 
    schema:potentialAction ?addToCart. 
  FILTER (?validDate > ?date && bif:contains(?offerName, 'Virtuoso')). 
  ?item opllic:hasSessions ?sessions; 
    opllic:hasMaximumProcessorCores ?cores; 
    opllic:maxNetworkInstance ?hosts; 
    opllic:productLicenseOf ?product; 
    opllic:hasDuration <http://data.openlinksw.com/oplweb/license/License-Duration#annual>. 
  ?product schema:version ?version. 
} 
ORDER BY DESC(?version) ASC(?price) 
LIMIT 3
```

**Post-query message:**
- Add note about custom licenses: https://www.openlinksw.com/contact
- Recommend evaluation before purchase
- Offer to generate evaluation license

---

## How-To Guide Queries

### General How-To Query

**Trigger:** Step-by-step guide requests  
**Use when:** Similarity search returns empty

```sql
SPARQL 
SELECT DISTINCT ?description ?position 
FROM <https://virtuoso.openlinksw.com/data/turtle/general/VirtuosoHowTos.ttl> 
FROM <https://virtuoso.openlinksw.com/data/turtle/general/VirtuosoHowTos-Extra.ttl> 
WHERE { 
  ?guide a schema:HowTo; 
    schema:step ?step. 
  ?step schema:name ?text; 
    schema:position ?position; 
    schema:description ?description. 
  ?guide schema:name ?name. 
} 
ORDER BY DESC(?sc) ASC(?name) ASC(?position)
```

### Installation Query

**Trigger:** "How do I install Virtuoso on {OS}"  
**Note:** If OS not specified, ask for: macOS, Windows, Linux, Docker, or OpenLink Nexus

(Uses same query as General How-To with OS-specific text filtering)

### CSV Bulk Loading Query

**Trigger:** "How do I bulk load CSV files"

(Uses same query as General How-To)

---

## Table Discovery Queries

### Discover Tables in Schema

For Demo instance (Northwind database):

```sql
SELECT 
  name_part(KEY_TABLE, 0) AS catalog,
  name_part(KEY_TABLE, 1) AS schema,
  name_part(KEY_TABLE, 2) AS table_name
FROM DB.DBA.SYS_KEYS 
WHERE KEY_IS_MAIN = 1 
  AND name_part(KEY_TABLE, 1) = 'demo'
ORDER BY table_name
```

**Usage:**
```javascript
Demo:execute_sql_query({
  sql: "[query above]",
  format: "markdown"
})
```

### List All Schemas

```sql
SELECT DISTINCT 
  name_part(KEY_TABLE, 0) AS catalog,
  name_part(KEY_TABLE, 1) AS schema
FROM DB.DBA.SYS_KEYS 
WHERE KEY_IS_MAIN = 1
ORDER BY catalog, schema
```

---

## Verification Queries

### Verify RDF View Quad Maps

Check that quad maps were created:

```sql
SPARQL
PREFIX virtrdf: <http://www.openlinksw.com/schemas/virtrdf#>

SELECT DISTINCT ?s1 as ?quadMap
WHERE {
  ?s1 a virtrdf:QuadMap .
  ?s1 virtrdf:qmTableName ?s2 .
  FILTER (contains(str(?s1), "{rdf-view-name}"))
}
```

**Note:** Replace `{rdf-view-name}` with actual IRI path segment.

### Count Triples in Graph

```sql
SPARQL
SELECT COUNT(*) as ?tripleCount
FROM <http://example.com/data/northwind>
WHERE { ?s ?p ?o }
```

### Sample Data from RDF View

```sql
SPARQL
SELECT *
FROM <http://example.com/data/northwind>
WHERE { ?s ?p ?o }
LIMIT 100
```

---

## Troubleshooting Queries

### Check RDF Metadata Status

```sql
SELECT * FROM DB.DBA.RDF_QUAD
WHERE G = iri_to_id('http://example.com/data/northwind')
LIMIT 10
```

### List All Named Graphs

```sql
SPARQL
SELECT DISTINCT ?g
WHERE { GRAPH ?g { ?s ?p ?o } }
ORDER BY ?g
```

### Check Quad Map Registry

```sql
SPARQL
PREFIX virtrdf: <http://www.openlinksw.com/schemas/virtrdf#>

SELECT ?qm ?table
WHERE {
  ?qm a virtrdf:QuadMap .
  ?qm virtrdf:qmTableName ?table .
}
ORDER BY ?qm
```

---

## Query Tips

### Semantic Similarity Matching

When user asks a question:
1. Execute FAQ Question Index query
2. Use semantic similarity to find closest match from questionName literals
3. Use matched ?question URI in FAQ Answer Retrieval query
4. If empty, fall back to FAQ Fallback Query

### Handling Empty Results

If query returns empty:
- Check graph IRIs are correct
- Verify data exists with COUNT query
- Try broader search criteria
- Use fallback queries

### Timeout Management

- Standard queries: 30,000ms
- Complex analytics: 60,000ms or higher
- Simple lookups: 10,000ms acceptable
- Always specify timeout parameter

### Format Selection

- **markdown:** Human-readable, tables
- **json:** Programmatic processing
- **jsonl:** Large resultsets, streaming
