---
name: resource-access-offers-generator
description: "Generate RDF Turtle offer/license/price bundles for File Access, Graph Access, and API Access products. Trigger on phrases like 'generate offers', 'create license bundle', 'make a file access offer', 'generate graph access offer', 'create API access offers', or any request to produce resource-access offers in Turtle format."
---
# Resource Access Offers Generator
Generate valid RDF Turtle documents containing File Access, Graph Access, or API Access offers.
## Minimum Input Requirements
| Input | Required | Example |
|-------|----------|---------|
| License resource IRI | Yes | URL of protected file/graph |
| Price | Yes | `2.99` |
| Description | Yes | Free text — name/prefLabel/comment auto-derived |
| Host platform | No (default: URIBurner) | `linkeddata.uriburner.com` |
## Host Platform Profiles
URIBurner (`linkeddata.uriburner.com`), ODS-QA (`ods-qa.openlinksw.com`), Localhost (`localhost`)
## Workflow
1. Elicit offer type (file/graph/api), host, license IRI, price, description
2. Derive name, prefLabel, comment from description
3. Load prompt template from `prompts/`
4. Substitute placeholders, generate Turtle
5. Validate syntax (rdflib), validate SHACL (`scripts/validate-offers-shacl.py`)
6. Run Post-Generation Checklist, save, provide loading instructions
## Auto-Derivation
- name: First sentence ≤80 chars
- pref_label: Abbreviated ≤60 chars
- comment: "Purchasing this offer grants {description}"
## GATE: 0 FAIL
`python3 scripts/validate-offers-shacl.py output.ttl --type {file|graph|api}` — must pass before delivery.
## Loading into Shop
```sql
SPARQL define get:soft "no-sponge" LOAD <file:///path/to/output.ttl> INTO <urn:opl:shop:offering:sponging:cache:official> ;
```
## License
AGPL-3.0
