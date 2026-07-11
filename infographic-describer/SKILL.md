---
name: infographic-describer
description: "Generate RDF-Turtle descriptions (schema:ImageObject, schema:VideoObject, schema:WebPage) for infographic files in a WebDAV directory, using SHACL shapes as the property contract. Trigger when: user asks to describe infographics, generate metadata for a DAV directory, create RDF descriptions for image/video collections, or apply a SHACL shape to bulk-describe files. Handles content negotiation (HTML describe pages vs SPARQL DESCRIBE), filename-derived metadata, thumbnail URL detection, and category inference."
---

# Infographic Describer

Generate RDF-Turtle descriptions for files in a WebDAV-hosted directory using a SHACL shape as the property contract.

## Workflow

### Step 1: Discover Files

List the target WebDAV directory to enumerate files:

```bash
curl -sL "https://www.openlinksw.com/data/{directory}/" | python3 -c "
import sys, re
html = sys.stdin.read()
files = re.findall(r'title=\"File - ([^\"]+)\"', html)
for f in files:
    print(f)
"
```

Classify by extension: `.png` → `schema:ImageObject`, `.mp4` → `schema:VideoObject`, `.html` → `schema:WebPage`.

### Step 2: Probe Describe Endpoint

Check which files have existing RDF data in the triplestore. Use the SPARQL DESCRIBE endpoint:

```python
import urllib.parse, urllib.request

iri = f'https://www.openlinksw.com/DAV/www2.openlinksw.com/data/{directory}/{stem}.{ext}'
query = f'DESCRIBE <{iri}>'
url = 'http://www.openlinksw.com/sparql?query=' + urllib.parse.quote(query) + '&output=text%2Fn3'

req = urllib.request.Request(url, headers={'Accept': 'text/n3, */*'})
resp = urllib.request.urlopen(req, timeout=30)
data = resp.read().decode()
has_data = 'Empty' not in data and len(data.strip()) > 50
```

### Step 3: Probe Thumbnails

Check for thumbnails using the content-explorer pattern:

```
https://www.openlinksw.com/data/content-explorer/thumbnails/{category}-{stem}.avif
```

Where `{category}` is the directory name (e.g., `infographics`). Probe with HTTP HEAD:

```bash
curl -sL -o /dev/null -w "%{http_code}" "$url"
```

Only files with `200` have thumbnails.

### Step 4: Generate Descriptions

For each file, construct RDF triples using the SHACL shape properties:

| Property | Source | Fallback |
|----------|--------|----------|
| `rdf:type` | File extension | `schema:CreativeWork` |
| `schema:name` | Filename stem (underscores/hyphens → spaces) | — |
| `schema:description` | Derived from name or describe page | `"Infographic: {name}"` |
| `schema:encodingFormat` | Content type from listing | Map extension to MIME |
| `schema:contentUrl` | Full DAV URL | — |
| `schema:thumbnailUrl` | Probe result (only if 200) | Omit |
| `schema:category` | Directory-based category IRI | Default to `#Infographic` |
| `wdrs:describedby` | Constructed describe endpoint URL | — |
| `schema:dateCreated` | Describe page (if available) | Omit |
| `schema:dateModified` | Describe page (if available) | Omit |

**Entity IRI pattern**: `{contentUrl}#this`

**Category IRIs** (content-explorer-metadata.ttl):
- `#Infographic` — default for `/data/infographics/`
- `#Guide` — filenames containing "guide"
- `#Demo` — filenames containing "demo"
- `#Survey` — filenames containing "survey"

**Encoding format mapping**:
- `.png` → `image/png`
- `.jpg`/`.jpeg` → `image/jpeg`
- `.mp4` → `video/mp4`
- `.html` → `text/html`

### Step 5: Generate Turtle

Use this template structure:

```turtle
@prefix schema: <http://schema.org/> .
@prefix rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix wdrs:   <http://www.w3.org/2007/05/powder-s#> .
@prefix xsd:    <http://www.w3.org/2001/XMLSchema#> .

<{contentUrl}#this>
    a {schemaType} ;
    schema:name "{name}" ;
    schema:description "{description}" ;
    schema:encodingFormat "{mimeType}" ;
    schema:contentUrl <{contentUrl}> ;
    schema:category <{categoryIri}> ;
    wdrs:describedby <{describeUrl}> .
```

Add `schema:thumbnailUrl` only if the probe returned 200.

### Step 6: Validate

Validate the generated Turtle:

```python
from rdflib import Graph
g = Graph()
g.parse('output.ttl', format='turtle')
print(f'{len(g)} triples, {len(set(g.subjects()))} entities')
```

### Step 7: Save

Save to the user-designated output path. Default:
- Shapes: `/Users/kidehen/Documents/RDF_DATA/shacl-shapes/`
- Descriptions: same directory as the shapes

## SHACL Shape Conventions

When generating or updating SHACL shapes to match describe output:

- Use `sh:minCount 0` for properties that may not exist for all files (`thumbnailUrl`, `dateCreated`, `dateModified`)
- Use `sh:minCount 1` for always-present properties (`name`, `contentUrl`, `encodingFormat`, `type`)
- Use `sh:hasValue` for fixed values (e.g., `encodingFormat = "image/png"`)
- Use `sh:targetClass` to match the schema type

## Notes

- The `/describe` endpoint requires a POST with `h=1` to bypass the confirmation dialog
- Most files in a DAV directory will have sparse or no RDF data — filename-derived metadata is the norm
- Thumbnails are rare — only files processed by the content-explorer system have them
- The SPARQL DESCRIBE endpoint (without CBD mode) returns more data than CBD mode for these resources
