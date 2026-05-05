# Document to Knowledge Graph Prompt Template

Used in Path D (Document → RDF) to generate a Knowledge Graph representation from a document source.

---

## Format Selection

Default options presented to the user: **JSON-LD** or **Turtle**.
Other formats (N-Triples, RDF/XML, etc.) are accepted if explicitly stated by the user.

Substitute `{chosen_format}` in the prompt header line below when the user selects a format other than JSON-LD.

---

## Prompt Template

```
Using a code block, generate a comprehensive representation of this information in JSON-LD using valid terms from <http://schema.org>. You MUST use {page_url} for @base, which is then used in deriving relative hash-based hyperlinks that denote subjects and objects. This rule doesn't apply to entities that are already denoted by hyperlinks (e.g., DBpedia, Wikidata, Wikipedia, etc), and expand @context accordingly. Note the following guidelines:

1. Use @vocab appropriately.
2. If applicable, include at least 10 Questions and associated Answers.
3. Utilize annotation properties to enhance the representations of Questions, Answers, Defined Term Set, HowTos, and HowToSteps, if they are included in the response and associate them with article sections (if they exist) or article using schema:hasPart.
4. Where relevant, add attributes for about, abstract, article body, and article section limited to a maximum of 30 words.
5. Denote values of about using hash-based IRIs derived from entity home page or wikipedia page url.
6. Any person associated with the document such as authors, commentators, or explicitly mentioned people MUST be denoted using a hash-based identity IRI derived from that person's associated document URL. Example: use `https://de.linkedin.com/in/vvoss/#this` as the person identity and keep `https://de.linkedin.com/in/vvoss/` as the profile document via `schema:url` or an equivalent document-linking property.
7. Where possible, if confident, add a DBpedia IRI to the list of about attribute values and then connect the list using owl:sameAs; note, never use schema:sameAs in this regard. In addition, never assign literal values to this attribute i.e., they MUST be IRIs by properly using @id.
8. Where relevant, add article sections and fleshed out body to ensure richness of literal objects.
9. Where possible, align images with relevant article and howto step sections.
10. Add a label to each how-to step.
11. Add descriptions of any other relevant entity types.
12. If not generating JSON-LD, triple quote literal values containing more than 20 words.
13. Whenever you encounter inline double quotes within the value of an annotation attribute, change the inline double quotes to single quotes.
14. Whenever you encounter video, handle using the VideoObject type, specifying properties such as name, description, thumbnailUrl, uploadDate, contentUrl, and embedUrl -- don't guess and insert non-existent information.
15. Whenever you encounter audio, handle using the AudioObject type, specifying properties such as name, description, thumbnailUrl, uploadDate, contentUrl, and embedUrl -- don't guess and insert non-existent information.
16. Where relevant, include additional entity types when discovered e.g., Product, Offer, and Service etc.
17. Language tag the values of annotation attributes; apply properly according to JSON-LD syntax rules.
18. Describe article authors and publishers in detail.
19. Use a relatedLink attribute to comprehensively handle all inline urls. Unless told otherwise, it should be a maximum of 20 relevant links.
20. You MUST ensure smart quotes are replaced with single quotes.
21. You MUST check and fix any JSON-LD usage errors based on its syntax rules e.g., missing @id designation for IRI values of attributes that only accept IRI values (e.g., schema:sameAs, owl:sameAs, etc.)

"""
{selected_text}
"""

Following your initial response, perform the following tasks:
1. Check and fix any syntax errors in the response.
2. Provide a list of additional questions, defined terms, or howtos for my approval.
3. Provide a list of additional entity types that could be described for my approval.
4. If the suggested additional entity types are approved, you MUST then return a revised final description comprising the original and added entity descriptions.
```

---

## Turtle Variant

When the user selects Turtle, replace the opening line with:

```
Using a code block, generate a comprehensive representation of this information in Turtle using valid terms from <http://schema.org>. You MUST use {page_url} as @base ...
```

All 21 guidelines apply unchanged. Guideline 12 activates: triple-quote literal values containing more than 20 words.

---

## Substitution Variables

| Variable | Source |
|----------|--------|
| `{page_url}` | Confirmed by user in Step 1D — used as `@base` |
| `{selected_text}` | Document text provided by user (pasted or fetched from URL) |

---

## Output Filename Convention

Derived from `{page_url}` by slugifying the path component:

| Format | Extension |
|--------|-----------|
| JSON-LD | `.jsonld` |
| Turtle | `.ttl` |
| N-Triples | `.nt` |
| RDF/XML | `.rdf` |
