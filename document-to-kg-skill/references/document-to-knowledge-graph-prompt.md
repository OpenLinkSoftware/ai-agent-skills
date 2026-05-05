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
14. Whenever you encounter images, handle using schema:image on the relevant entity. For each distinct image found in the source content, create a schema:ImageObject describing it with properties such as name, description, contentUrl, thumbnailUrl, uploadDate, and caption where available -- don't guess and insert non-existent information. Associate each ImageObject with its relevant article section or HowTo step via schema:hasPart or schema:about.
15. Whenever you encounter video, handle using the VideoObject type, specifying properties such as name, description, thumbnailUrl, uploadDate, contentUrl, and embedUrl -- don't guess and insert non-existent information.
16. Whenever you encounter audio, handle using the AudioObject type, specifying properties such as name, description, thumbnailUrl, uploadDate, contentUrl, and embedUrl -- don't guess and insert non-existent information.
17. For every person entity (authors, commentators, or explicitly mentioned individuals): (a) if a LinkedIn profile URL is found in the source, use {linkedin-url}#this as the primary person IRI with schema:url pointing to the bare profile URL; (b) if an X/Twitter profile URL is found and no LinkedIn URL exists, use {x-url}#this as the primary person IRI; (c) otherwise derive a hash-based IRI from {page_url}. In every case, ALL discovered platform identities MUST be linked via owl:sameAs -- e.g., owl:sameAs <https://www.linkedin.com/in/name/#this>, <https://x.com/handle/#this> -- ensuring the person is resolvable from any direction. For JSON-LD, use @id for all owl:sameAs values.
18. Where relevant, include additional entity types when discovered e.g., Product, Offer, and Service etc.
19. Language tag the values of annotation attributes; apply properly according to JSON-LD syntax rules.
20. Describe article authors and publishers in detail.
21. Use a relatedLink attribute to comprehensively handle all inline urls. Unless told otherwise, it should be a maximum of 20 relevant links.
22. You MUST ensure smart quotes are replaced with single quotes.
23. You MUST check and fix any JSON-LD usage errors based on its syntax rules e.g., missing @id designation for IRI values of attributes that only accept IRI values (e.g., schema:sameAs, owl:sameAs, etc.)
24. You MUST use http://schema.org/ (HTTP, not HTTPS) as the schema: namespace URI. Never use https://schema.org/.
25. You MUST wrap FAQ questions in a schema:FAQPage with schema:mainEntity listing all question IRIs. The FAQPage MUST be linked from the main article via schema:hasPart.
26. You MUST wrap glossary terms in a schema:DefinedTermSet with schema:hasDefinedTerm listing all term IRIs. The DefinedTermSet MUST be linked from the main article via schema:hasPart.
27. ALL DBpedia, Wikidata, and Wikipedia entity references MUST use fully expanded IRIs (e.g., http://dbpedia.org/resource/Tim_Berners-Lee) — never CURIEs or prefixed names.
28. You MUST NOT use file: scheme IRIs anywhere. The @base or @prefix : MUST use the canonical https: URL of the source document with a # suffix.
29. You MUST NOT use blank nodes for schema:Answer instances. Every schema:Answer MUST be a named entity with its own hash-based IRI (e.g., :a1, :a2) connected via schema:acceptedAnswer :aN — never schema:acceptedAnswer [ a schema:Answer ; ... ].
30. When you assert a directional relationship (e.g., schema:isPartOf), you MUST also assert its inverse on the target entity (e.g., schema:hasPart) — RDF does not infer inverses automatically, so both directions are needed for completeness.
31. If the response includes a lightweight ontology (custom classes, properties, or an owl:Ontology declaration), you MUST: (a) name and describe the ontology using schema:name and schema:description alongside rdfs:label and rdfs:comment; (b) add schema:identifier with the canonical source URL; (c) associate every class and property with the ontology using rdfs:isDefinedBy : .
33. The main article MUST include prov:wasGeneratedBy linking to a schema:SoftwareApplication entity representing the skill that produced it. Declare @prefix prov: <http://www.w3.org/ns/prov#> . The skill entity MUST have schema:name (e.g., "document-to-kg-skill"), schema:url pointing to its GitHub source (e.g., https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/document-to-kg-skill), and schema:description. If multiple skills were used, use multiple prov:wasGeneratedBy triples.

32. Every logical entity group beyond FAQ/glossary/HowTo (e.g., use cases, technologies, architectural layers, key concepts) MUST be wrapped in a schema:ArticleSection and linked to the main article via schema:hasPart. No entity should be orphaned — every entity must be reachable from the main article through some path.

"""
{selected_text}
"""

Following your initial response, perform the following tasks:
1. Check and fix any syntax errors in the response.
2. Provide a list of additional questions, defined terms, or howtos for my approval.
3. Provide a list of additional entity types that could be described for my approval.
4. If the suggested additional entity types are approved, you MUST then return a revised final description comprising the original and added entity descriptions.

CRITICAL — Before presenting the final output, you MUST perform a compliance self-audit. Verify each of these items and report the result (PASS or FAIL with the specific violation):
1. schema: namespace uses http://schema.org/ (not https://schema.org/)
2. FAQ questions are wrapped in a schema:FAQPage linked via schema:mainEntity
3. Glossary terms are wrapped in a schema:DefinedTermSet linked via schema:hasDefinedTerm
4. The main article has schema:hasPart linking to FAQPage, DefinedTermSet, and any HowTo
5. All DBpedia/Wikidata/Wikipedia IRIs are fully expanded (not CURIEs)
6. No file: scheme IRIs exist anywhere in the output
7. owl:sameAs is used for DBpedia cross-references (never schema:sameAs)
8. @base or @prefix : is the canonical https: source URL with # suffix
9. No blank nodes used for schema:Answer — every answer is a named entity (:a1, :a2, ...)
10. Inverse relationships are explicit: for every schema:isPartOf there is a corresponding schema:hasPart
11. If ontology present: schema:name + schema:description, schema:identifier, all classes/properties have rdfs:isDefinedBy :
Report: "COMPLIANCE SELF-AUDIT: X/11 passed. [list any FAIL items with the specific fix applied]. Final output follows."```

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
