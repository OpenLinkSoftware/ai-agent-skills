# schema:identifier Patterns by Entity Type

This reference documents the `schema:identifier` conventions used in Knowledge Graph outputs.
The pattern was established from the HTML doc approach: use the **most canonical, authoritative URI** for each entity type.

---

## Principle

`schema:identifier` should resolve to the **single most authoritative identifier** for an entity.
Priority order:
1. Official canonical URL (homepage, spec page, product page)
2. Standards body designation (e.g. ISO codes, NAICS lookup URLs, ISBN notation)
3. Profile URL at the entity's primary platform
4. Plain code string for unambiguous, well-known designations (e.g. ISO 3166-1 alpha-2 country codes)

---

## Patterns by Entity Type

### Industry Verticals (`:Industry` instances)

Use the **US Census Bureau NAICS canonical lookup URL**.
See [`naics-identifier-pattern.md`](naics-identifier-pattern.md) for the full reference.

```turtle
schema:naics "524210" ;
schema:identifier "https://www.census.gov/naics/?input=524210&year=2022&details=524210" .
```

---

### Countries (`schema:Country`)

Use the **ISO 3166-1 alpha-2 code** as a plain literal.

```turtle
:unitedStates a schema:Country ;
    schema:name "United States" ;
    schema:identifier "US" .
```

| Country | Code |
|---|---|
| United States | `"US"` |
| United Kingdom | `"GB"` |
| Germany | `"DE"` |
| France | `"FR"` |
| Canada | `"CA"` |

---

### Books (`schema:Book`)

Use the **ISBN in prefixed notation** as `schema:identifier`, alongside `schema:isbn` for the raw number.

```turtle
:innovatorsDilemma a schema:Book ;
    schema:isbn "9780060521998" ;
    schema:identifier "ISBN:9780060521998" .
```

---

### People (`schema:Person`)

Use the person's **canonical profile URL** at their primary authoritative platform.

```turtle
:julienBek a schema:Person ;
    schema:url <https://x.com/JulienBek> ;
    schema:identifier "https://x.com/JulienBek" .
```

| Platform | Pattern |
|---|---|
| X (Twitter) | `https://x.com/{handle}` |
| LinkedIn | `https://www.linkedin.com/in/{slug}/` |
| GitHub | `https://github.com/{username}` |
| ORCID | `https://orcid.org/{id}` |
| Personal site | Homepage URL |

---

### Organizations (`org:Organization`, `schema:Organization`)

Use the **organization's official homepage URL**.

```turtle
:withCoverage a org:Organization ;
    schema:url <https://withcoverage.com> ;
    schema:identifier "https://withcoverage.com" .
```

---

### Software Applications and Products

Use the **product's official homepage or canonical product page URL**.

```turtle
:cursorExample a schema:SoftwareApplication ;
    schema:identifier "https://www.cursor.com" .
```

---

### Web Standards and Specifications

Use the **canonical specification URL** from the standards body.

| Standard | `schema:identifier` value |
|---|---|
| RDF 1.1 | `https://www.w3.org/TR/rdf11-concepts/` |
| SPARQL 1.1 | `https://www.w3.org/TR/sparql11-overview/` |
| OWL 2 | `https://www.w3.org/TR/owl2-overview/` |
| JSON-LD | `https://www.w3.org/TR/json-ld11/` |
| Linked Data | `https://www.w3.org/DesignIssues/LinkedData.html` |
| schema.org (namespace) | `http://schema.org/` (HTTP, not HTTPS) |
| schema.org (docs) | `https://schema.org/` |

---

### Formal Standards (ISO, IEC, IETF, etc.)

Use the **standards designation string** as a plain literal when no single canonical URL exists.

```turtle
schema:identifier "ISO/IEC 9075" .    # SQL standard
schema:identifier "ISO 8601" .        # Date/time
schema:identifier "ISO 3166-1" .      # Country codes
schema:identifier "RFC 3986" .        # URIs
```

---

### Social Media Posts and Threads

Use the **canonical permalink URL** of the post.

```turtle
:originalXPost a schema:SocialMediaPosting ;
    schema:url <https://x.com/JulienBek/status/2029680516568600933> ;
    schema:identifier "https://x.com/JulienBek/status/2029680516568600933" .
```

---

### AI/LLM Conversation Documents

Use the **canonical conversation URL** as both `schema:url` and `schema:identifier`.

```turtle
:analysis a schema:CreativeWork ;
    schema:identifier "https://x.com/i/grok?conversation=2032429977895829654" .
```

---

## Anti-Patterns to Avoid

| Anti-pattern | Correct approach |
|---|---|
| `schema:identifier "https://www.census.gov/naics/?code=524210"` | Use `?input=&year=2022&details=` pattern |
| `schema:identifier <http://dbpedia.org/resource/Foo>` | Use `rdfs:seeAlso` for DBpedia cross-refs |
| Omitting `schema:identifier` when a canonical URL exists | Always add `schema:identifier` alongside `schema:url` |
| Using `schema:PropertyValue` wrapper for simple codes | Use plain literal directly unless disambiguation is needed |
| Using `schema:sameAs` for DBpedia links | Use `owl:sameAs` or `rdfs:seeAlso` |
