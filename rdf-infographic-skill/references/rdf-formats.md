# RDF Formats Reference Guide

This guide covers RDF input formats and how to parse them for infographic generation.

## Supported RDF Formats

### 1. Turtle (.ttl)

**Characteristics**: Human-readable, concise syntax. Recommended for manual entry.

**Example**:
```turtle
@prefix ex: <http://example.org/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:Product1 a ex:SoftwareProduct ;
  rdfs:label "OPAL" ;
  rdfs:comment "AI-powered data integration layer" ;
  ex:version "2.0" ;
  ex:hasComponent ex:Component1 .

ex:Component1 a ex:Component ;
  rdfs:label "RDF View Generator" ;
  rdfs:comment "Automatically generates RDF views from relational data" .
```

**Parsing Tips**:
- Namespaces defined with `@prefix`
- Statements end with `.`
- Subjects, predicates, objects are IRIs, blank nodes, or literals
- `a` is shorthand for `rdf:type`

### 2. RDF/XML (.rdf)

**Characteristics**: XML serialization. Widely supported by tools.

**Example**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
         xmlns:ex="http://example.org/">
  <rdf:Description rdf:about="http://example.org/Product1">
    <rdf:type rdf:resource="http://example.org/SoftwareProduct"/>
    <rdfs:label>OPAL</rdfs:label>
    <rdfs:comment>AI-powered data integration layer</rdfs:comment>
    <ex:version>2.0</ex:version>
  </rdf:Description>
</rdf:RDF>
```

**Parsing Tips**:
- Each `rdf:Description` is a resource
- `rdf:type` indicates entity classification
- Nested elements represent properties
- Use XML parser first, then RDF extraction

### 3. JSON-LD (.jsonld)

**Characteristics**: JSON format with linked data semantics. Increasingly common.

**Example**:
```json
{
  "@context": {
    "@vocab": "http://example.org/",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
  },
  "@graph": [
    {
      "@id": "http://example.org/Product1",
      "@type": "SoftwareProduct",
      "rdfs:label": "OPAL",
      "rdfs:comment": "AI-powered data integration layer",
      "version": "2.0",
      "hasComponent": { "@id": "http://example.org/Component1" }
    },
    {
      "@id": "http://example.org/Component1",
      "@type": "Component",
      "rdfs:label": "RDF View Generator"
    }
  ]
}
```

**Parsing Tips**:
- `@context` defines namespace mappings
- `@type` indicates entity types
- `@id` is the resource IRI
- Nested objects reference related entities

### 4. N-Triples (.nt)

**Characteristics**: Line-based, statement-per-line format. Simple parsing.

**Example**:
```
<http://example.org/Product1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://example.org/SoftwareProduct> .
<http://example.org/Product1> <http://www.w3.org/2000/01/rdf-schema#label> "OPAL" .
<http://example.org/Product1> <http://www.w3.org/2000/01/rdf-schema#comment> "AI-powered data integration layer" .
```

**Parsing Tips**:
- Each line is one triple: subject predicate object .
- All IRIs in angle brackets `<>`
- Literals in quotes `""`
- Language tags: `"text"@en`

### 5. SPARQL Results (JSON)

**Characteristics**: Results from SPARQL queries. Includes variable bindings.

**Example**:
```json
{
  "head": {
    "vars": ["subject", "predicate", "object"]
  },
  "results": {
    "bindings": [
      {
        "subject": { "type": "uri", "value": "http://example.org/Product1" },
        "predicate": { "type": "uri", "value": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" },
        "object": { "type": "uri", "value": "http://example.org/SoftwareProduct" }
      }
    ]
  }
}
```

**Parsing Tips**:
- `head.vars` lists the queried variables
- `results.bindings` contains result rows
- Each value has `type` (uri, literal) and `value`
- Convert back to triple format for RDF parsing

## Key RDF Concepts for Infographic Generation

### Entity Types (Classes)

Extract with `rdf:type` predicates:

```turtle
ex:Product1 a ex:SoftwareProduct .  # Product1 is of type SoftwareProduct
```

**For Infographics**: Group entities by type for navigation sections and cards.

### Labels & Descriptions

Primary properties for display text:

- `rdfs:label` - Human-readable name (primary)
- `rdfs:comment` - Description or definition
- `dcterms:title` - Alternative title
- `dcterms:description` - Alternative description

```turtle
ex:Product1 rdfs:label "OPAL" ;
           rdfs:comment "OpenLink AI Layer for semantic data integration" .
```

### Properties & Relationships

Connect entities:

```turtle
ex:Product1 ex:hasFeature ex:Feature1 ;
           ex:createdBy ex:Company1 ;
           ex:deployedOn ex:Platform1 .
```

**For Infographics**: Use relationships to create connection diagrams or hierarchical layouts.

### Acronyms & Full Names

Extract from labels for glossary generation:

```turtle
ex:OPAL rdfs:label "OpenLink AI Layer" ;
        ex:acronym "OPAL" .
```

If acronym property missing, infer from capital letters in label:
- "OpenLink AI Layer" → OPAL
- "Semantic Query Language" → SQL

### Keywords & Domain Terms

Aggregate from labels and comments:

```turtle
ex:Product1 ex:keyword "semantic-web", "RDF", "knowledge-graph", "data-integration" .
```

If keywords not provided, extract unique significant terms from comments.

## Parsing Strategies

### Strategy 1: Direct Entity Extraction

```python
# For each entity (subject of triples):
# 1. Get rdf:type → Entity type
# 2. Get rdfs:label → Display name
# 3. Get rdfs:comment → Description
# 4. Get all properties → Attributes
# 5. Get object references → Related entities

entity = {
    "iri": "http://example.org/Product1",
    "type": "SoftwareProduct",
    "label": "OPAL",
    "comment": "AI-powered data integration layer",
    "properties": {
        "version": "2.0",
        "deployedOn": ["Platform1", "Platform2"]
    },
    "relatedEntities": ["Component1", "Company1"]
}
```

### Strategy 2: Type-Based Organization

```python
# Group entities by type for navigation:
entities_by_type = {
    "SoftwareProduct": [Product1, Product2],
    "Component": [Component1, Component2],
    "Company": [Company1]
}

# For each type, create a section in the infographic
```

### Strategy 3: Property-Based Filtering

```python
# Filter entities by specific properties:
# - Entities with images: ex:hasImage
# - Entities with documentation: ex:hasDocumentation
# - Featured entities: ex:isFeatured true

featured_products = [e for e in entities if e.get("isFeatured") == True]
products_with_images = [e for e in entities if "hasImage" in e.properties]
```

## Format Detection & Conversion

### Detecting Input Format

```python
def detect_format(data):
    if data.startswith("@prefix"):
        return "turtle"
    elif data.startswith("<?xml"):
        return "rdf-xml"
    elif data.startswith("{"):
        return "json-ld"  # or "sparql-json"
    elif data.startswith("<"):
        return "n-triples"
    return "unknown"
```

### Converting Between Formats

Most RDF libraries (rdflib in Python, Apache Jena in Java) support conversion:

```python
from rdflib import Graph

# Load any format
g = Graph()
g.parse("data.ttl", format="turtle")
# or: g.parse("data.rdf", format="xml")

# Convert to any other format
g.serialize("output.jsonld", format="json-ld")
```

## Handling Special Cases

### Blank Nodes

Unnamed resources referenced only by properties. Example:

```turtle
ex:Product1 ex:config [
  ex:parameter "value" ;
  ex:enabled true
] .
```

**For Infographics**: Generate temporary IDs or collapse into parent entity.

### Literal Value Types

```turtle
ex:Product1 ex:version "2.0"^^xsd:decimal ;
           ex:releaseDate "2024-01-15"^^xsd:date ;
           ex:isActive true .
```

**For Infographics**: Convert typed literals to appropriate display formats (dates, numbers, booleans).

### Language-Tagged Literals

```turtle
ex:Product1 rdfs:label "OPAL"@en, "OPAL"@fr, "OPAL"@de .
```

**For Infographics**: Select label by user language preference or default to English.

### Multi-valued Properties

```turtle
ex:Product1 ex:keyword "semantic-web" ;
           ex:keyword "RDF" ;
           ex:keyword "data-integration" .
```

**For Infographics**: Display as tag clouds, bullet lists, or comma-separated text.

## Extraction Checklist

When processing RDF data for infographic generation, ensure you extract:

- [ ] All entity IRIs (unique identifiers)
- [ ] Entity types from `rdf:type`
- [ ] Primary labels from `rdfs:label`
- [ ] Descriptions from `rdfs:comment`
- [ ] All properties and their values
- [ ] Relationships between entities (outgoing references)
- [ ] Image/media URLs (`ex:hasImage`, etc.)
- [ ] External links (`ex:url`, `foaf:homepage`, etc.)
- [ ] Keywords and tags
- [ ] Acronyms (stated or inferred)
- [ ] Organization/grouping information

## Resources

- W3C RDF Specification: https://www.w3.org/RDF/
- Turtle Syntax: https://www.w3.org/TR/turtle/
- JSON-LD: https://json-ld.org/
- Python rdflib: https://rdflib.readthedocs.io/
- SPARQL: https://www.w3.org/TR/sparql11-query/
