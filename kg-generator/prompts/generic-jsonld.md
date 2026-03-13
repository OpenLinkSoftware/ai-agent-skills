# Generic Knowledge Graph Prompt — JSON-LD Output

Use this template for general web pages, articles, blog posts, and documentation.
Substitute `{page_url}` and `{selected_text}` before sending.

---

## Placeholders

| Placeholder | Description |
|---|---|
| `{page_url}` | Canonical URL of the source page — used as `@base` |
| `{selected_text}` | Full extracted text content of the source page or document |

---

## Prompt Template

```
Using a code block, generate a comprehensive representation of this information in JSON-LD using valid terms from <http://schema.org>. You MUST use {page_url} for @base, which is then used in deriving relative hash-based hyperlinks that denote subjects and objects. This rule doesn't apply to entities that are already denoted by hyperlinks (e.g., DBpedia, Wikidata, Wikipedia, etc), and expand @context accordingly. Note the following guidelines:
1. Use @vocab appropriately.
2. If applicable, include at least 10 Questions and associated Answers.
3. Utilize annotation properties to enhance the representations of Questions, Answers, Defined Term Set, HowTos, and HowToSteps, if they are included in the response, and associate them with article sections (if they exist) or article using schema:hasPart.
4. Where relevant, add attributes for about, abstract, article body, and article section limited to a maximum of 30 words.
5. Denote values of about using hash-based IRIs derived from entity home page or Wikipedia page URL.
6. Where possible, if confident, add a DBpedia IRI to the list of about attribute values and then connect the list using owl:sameAs; note, never use schema:sameAs in this regard. In addition, never assign literal values to this attribute i.e., they MUST be IRIs by properly using @id.
7. Where relevant, add article sections and fleshed out body to ensure richness of literal objects.
8. Where possible, align images with relevant article and howto step sections.
9. Add a label to each how-to step.
10. Add descriptions of any other relevant entity types.
11. If not generating JSON-LD, triple-quote literal values containing more than 20 words.
12. Whenever you encounter inline double quotes within the value of an annotation attribute, change the inline double quotes to single quotes.
13. Whenever you encounter video, handle using the VideoObject type, specifying properties such as name, description, thumbnailUrl, uploadDate, contentUrl, and embedUrl — don't guess and insert non-existent information.
14. Whenever you encounter audio, handle using the AudioObject type, specifying properties such as name, description, thumbnailUrl, uploadDate, contentUrl, and embedUrl — don't guess and insert non-existent information.
15. Where relevant, include additional entity types when discovered e.g., Product, Offer, and Service etc.
16. Language-tag the values of annotation attributes; apply properly according to JSON-LD syntax rules.
17. Describe article authors and publishers in detail.
18. Use a relatedLink attribute to comprehensively handle all inline URLs. Unless told otherwise, it should be a maximum of 20 relevant links.
19. You MUST ensure smart quotes are replaced with single quotes.
20. You MUST check and fix any JSON-LD usage errors based on its syntax rules e.g., missing @id designation for IRI values of attributes that only accept IRI values (e.g., schema:sameAs, owl:sameAs, etc.).

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

## Post-Generation Checklist

After generating output, verify:

- [ ] `@base` is set to `{page_url}`
- [ ] All subject/object IRIs are hash-based relative IRIs (except known authority entities)
- [ ] At least 10 `schema:Question` + `schema:Answer` pairs present
- [ ] `owl:sameAs` used (not `schema:sameAs`) for DBpedia cross-references
- [ ] All IRI-valued attributes use `@id` — no plain string literals for IRI-only properties
- [ ] Inline double quotes within literals converted to single quotes
- [ ] Smart/curly quotes replaced with straight single quotes
- [ ] `relatedLink` includes up to 20 relevant inline URLs
- [ ] Language tags applied to annotation literals where applicable
- [ ] JSON-LD is syntactically valid (balanced braces, correct `@context` expansion)
- [ ] No non-existent `thumbnailUrl`, `contentUrl`, or `embedUrl` values guessed for media
