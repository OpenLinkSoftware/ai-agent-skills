---
name: kg-generator
description: "Generate comprehensive Knowledge Graphs from file: or http(s): sources, using RDF-Turtle by default or another requested RDF serialization. Supports general documents, business and market analysis, event recaps, thesis and framework articles, social-media threads, and news commentary. Use when asked to generate a knowledge graph, create RDF or JSON-LD, convert a URL to semantic data, or extract schema.org data from a page or document."
---

# Knowledge Graph Generator Skill

Generate comprehensive, standards-compliant Knowledge Graphs from any `file:` or `http[s]:` URL. Produces **RDF-Turtle by default**; JSON-LD and other serializations available on request.

---

## When to Use This Skill

- "Generate a knowledge graph from [URL]"
- "Generate RDF / RDF-Turtle from [URL]"
- "Generate JSON-LD from [URL]"
- "Convert this page to structured semantic data"
- "Extract schema.org data from [URL]"
- "Create an RDF rendition of this post/article/report"

---

## Harness Alignment

This skill is a Knowledge Graph generation entry point. For document/source-to-RDF requests, interpret the request through the `document-to-kg-skill` **Document-to-KG Harness Mode** contract when that skill is available. For requests that also ask for HTML, Markdown, an infographic, or a KG Explorer, hand off to the `rdf-infographic-skill` **RDF Infographic Harness Mode** after RDF generation.

Do not let this skill drift into standalone HTML generation, source summarization, or manually invented graph visualization. RDF remains the source of truth, and companion HTML/Markdown artifacts must satisfy the RDF/HTML/MD pairing contract in `rdf-infographic-skill`.

### Narrative and Visual-Communication Contract

When the RDF will drive a reader-facing document, model a coherent evidence-backed narrative spine rather than an undifferentiated fact inventory. Preserve the source's thesis, contrasts, causal chain, quantitative evidence, limitations, and conclusion as ordered, queryable entities and relationships. Model comparison dimensions, metric observations, claims, provenance, and SPARQL recipes explicitly so the companion document can communicate them through the most appropriate visual form.

For any visual or interactive companion, operate as a UI/UX expert, visual-communications designer, and storyteller, and inherit the full `rdf-infographic-skill` operating modality. The reader journey must determine hierarchy and pacing; tables serve exact comparisons, flows serve sequence or causality, diagrams serve architecture, charts serve quantitative patterns, and prose serves interpretation. Live SPARQL interaction is part of the story surface when it lets readers test or extend the document's claims; it must not be relegated to decorative or disconnected query text.

If this skill produces or templates any HTML directly, it must inherit the `rdf-infographic-skill` open-tab contract: every generated HTML `<a>` whose `href` is not a same-page fragment (`#section`) uses `target="_blank" rel="noopener noreferrer"`, while same-page fragment navigation remains same-tab. Attribution links must hyperlink the attributed label itself, not generic labels such as `Visit` or `Learn more`.

### SoftwareApplication IRI Alignment

When generated RDF introduces or normalizes a `schema:SoftwareApplication`, use the denotation priority rule shared with `document-to-kg-skill` and `rdf-infographic-skill`:

1. DBpedia IRI if a confident DBpedia resource exists.
2. Wikidata IRI if no confident DBpedia resource exists but a confident Wikidata entity exists.
3. Official product/application homepage URL with `#this` appended when neither can be confirmed.

When using a homepage fallback and a confirmed DBpedia/Wikidata identity exists, add `owl:sameAs` and declare `owl:` as `http://www.w3.org/2002/07/owl#`. Do not fabricate DBpedia or Wikidata IRIs.

### Country IRI Alignment

When generated RDF introduces or normalizes a `schema:Country`, use the denotation priority rule shared with `document-to-kg-skill` and `rdf-infographic-skill`:

1. DBpedia country IRI if a confident DBpedia resource exists.
2. Wikidata country IRI if no confident DBpedia resource exists but a confident Wikidata entity exists.
3. Source-grounded document hash IRI only when neither DBpedia nor Wikidata can be confirmed.

When using DBpedia as the primary country IRI and a confirmed Wikidata equivalent exists, add `owl:sameAs` to the Wikidata entity. When using Wikidata as a fallback and a DBpedia equivalent later becomes available, normalize to DBpedia or add `owl:sameAs` if preserving an existing artifact is necessary. Do not use local document hash IRIs for known countries when DBpedia or Wikidata authority IRIs are available. Visible country names in HTML/Markdown companions and KG Explorer nodes must use the selected country IRI via the resolver pattern.

### DefinedTerm / Glossary IRI Alignment

When generated RDF introduces `schema:DefinedTerm` or `skos:Concept` glossary entries, choose the subject IRI using this priority order:

1. **Standards-body or platform IRI first** — if the term has a well-known W3C, schema.org, IANA, or other standards-body IRI (e.g., Semantic Web → `https://www.w3.org/2001/sw/#this`), use that as the primary IRI with `owl:sameAs` linking to the document-local representation.
2. **DBpedia IRI second** — if no standards-body IRI exists but a confident DBpedia resource exists for the term, use via `owl:sameAs` from the document-local IRI.
3. **Wikidata IRI third** — if no confident DBpedia resource exists but a confident Wikidata entity exists, use the Wikidata IRI as the primary subject.
4. **Document-local hash IRI** — the most common case: use a source-grounded hash IRI derived from `{page_url}` with a mnemonic fragment.

**Canonical subject rule (applies to tiers 1–3):** When a confirmed DBpedia IRI (tier 2) or Wikidata IRI (tier 3) exists, that IRI IS the entity's subject — use it directly as the primary subject, **never** create a document-local alias and add `owl:sameAs dbr:X`. The entity IS `dbr:X`; the local alias is redundant and bloats the graph. Use `owl:sameAs` only for genuine cross-vocabulary alignment: `dbr:SPARQL owl:sameAs wd:Q54871` is correct (DBpedia ↔ Wikidata); `:sparqlConcept owl:sameAs dbr:SPARQL` is the anti-pattern to avoid. Document-local IRIs (tier 4) are correct only when no confirmed authority IRI exists. Do not hardcode a fixed list of cross-referenceable terms — evaluate each term against DBpedia/Wikidata at generation time. Do not fabricate external IRIs.

### Collection and Service Detection

When generating RDF from a documentation collection, manual, docs portal, sitemap-backed site, MkDocs/Docusaurus/VitePress collection, GitBook, or source mesh:

1. Inspect available sitemap, search index, navigation, table of contents, and strongly linked child pages before finalizing the graph.
2. Treat child pages about APIs, SPARQL, endpoints, query examples, services, reporting workflows, data models, server/runtime platforms, authentication, and integration instructions as high-signal sources that must be summarized into the RDF unless the user explicitly narrows scope.
3. If source content mentions a SPARQL endpoint, REST API, query service, data service, server platform, or runtime infrastructure, model it explicitly using appropriate entities such as `schema:WebAPI`, `schema:DataCatalog`, `schema:DataFeed`, `schema:SoftwareApplication`, `schema:Service`, or `schema:SoftwareSourceCode`.
4. For query-example pages, represent major query families or named queries as distinct resources when they are central to the document. Link each query to its target endpoint/service and to the concepts it reports on.
5. Apply the SoftwareApplication denotation rule to server/software platforms such as Virtuoso, PostgreSQL, Databricks, Snowflake, GitLab Pages, MkDocs, or application connectors. Prefer confident DBpedia/Wikidata IRIs for known platforms; otherwise use the official homepage URL with `#this`.
6. For SPARQL examples, preserve executable query text in RDF using `schema:SoftwareSourceCode`, `schema:programmingLanguage "SPARQL"`, `schema:text`, `schema:codeSampleType`, and `schema:target` pointing to the endpoint/service. Model live execution links as `schema:SearchAction` or equivalent `schema:potentialAction` resources with correctly URL-encoded query parameters for the endpoint. If placeholders remain in the source query, keep them visibly marked and do not imply the query is executable without user edits.

## Template Selection

| Content type | Template | Default output |
|---|---|---|
| General articles, blog posts, documentation | Generic | JSON-LD |
| Business strategy, market analysis, industry threads | Business & Market Analysis | RDF-Turtle |
| Conference/event recaps, panel summaries, case-study-driven narrative articles | Conference & Event Recap | RDF-Turtle |
| Opinion/thesis pieces proposing a named framework (pillars/practices), especially with an added critical-perspective response | Thesis & Framework Article | RDF-Turtle |
| A single social media post plus its comment thread | Social Media Post & Comment Thread | RDF-Turtle |
| Third-party news/magazine articles, optionally with an agent-authored framework-application commentary section | News Article with Framework Commentary | RDF-Turtle |
| User requests JSON-LD explicitly | Generic | JSON-LD |
| User requests RDF-Turtle explicitly | Whichever RDF-Turtle template's content shape fits (Business & Market Analysis, Conference & Event Recap, Thesis & Framework Article, Social Media Post & Comment Thread, or News Article with Framework Commentary) | RDF-Turtle |

When uncertain, default to the **Generic** template and ask the user which RDF-Turtle variant fits better.

### RDF Format Elicitation

Before generation, elicit the RDF serialization format unless already specified by the user:

> "Output format: (1) RDF-Turtle only, (2) JSON-LD only, or (3) Both?"

Do NOT default to dual-format generation. Only produce both when explicitly requested or when the user asks for HTML/MD companions that require a format toggle in the footer. Producing an unneeded format wastes tokens on rdflib conversion and file I/O.

### Generation Modality

Before generation, elicit the modality unless the user has already specified one:

> "Generate via: (1) **LLM-Direct** — I write all artifacts end-to-end, (2) **Script-Assisted** — I extract entities as JSON, Python builds RDF deterministically, then I generate HTML+MD from validated RDF, or (3) **Agent's Choice** — I pick the most token-efficient mode based on content complexity?"

| Mode | Mechanism | Best for |
|------|-----------|----------|
| **LLM-Direct** | LLM writes TTL/JSON-LD, HTML, MD end-to-end | Small posts, <15 entities, simple structure, quick iterations |
| **Script-Assisted** | LLM outputs structured JSON entity map → Python/rdflib constructs Graph, serializes, runs compliance audit → LLM generates HTML+MD from validated RDF | Large posts, many entities, comments, images, SPARQL queries |
| **Agent's Choice** | Agent evaluates source: entity count, comment count, media count, SPARQL presence → picks optimal mode | Default — removes decision burden, minimizes token spend |

**Agent's Choice heuristic:**
- Entities > 20, comments > 3, or SPARQL queries present → **Script-Assisted**
- Entities ≤ 20, no comments, no SPARQL → **LLM-Direct**

### Plan Presentation Rule

Before executing any generation, present a tabulated plan with every item checked against the applicable validation gates. Use this format:

| # | Requirement | Skill Source | Status |
|---|---|---|---|
| 1 | `@prefix :` = canonical source URL with `#` | kg-gen checklist | ✓ |
| 2 | `schema:` = `http://schema.org/` (HTTP) | kg-gen checklist | ✓ |
| ... | ... | ... | ... |

If any gate has no corresponding check in the skills, mark it **MISSING GATE** and pause for the user to resolve before proceeding. Do not execute until the user approves the plan.

---

## Execution Routing

Default execution order for fetching content and invoking web services:

1. Direct native access (file read, WebFetch, or `curl`) to the source URL
2. **PinchTab browser automation** — for JS-heavy pages, login-protected content, or sites requiring browser interaction (e.g., LinkedIn posts, X/Twitter feeds). Use when curl returns 401, 403, or empty content but the page loads in a browser.
   > **Installation check:** If `pinchtab` is not found in PATH, ask the user for permission to install it before proceeding.
   > **Install options:** `brew install pinchtab` (macOS) or `cargo install pinchtab` (via Rust)
   - Start PinchTab server: `pinchtab server` (or `pinchtab daemon install` for persistent service)
   - Start instance: `pinchtab instance start` or `curl -X POST http://localhost:9867/instances/start`
   - Navigate: `curl -X POST http://localhost:9867/navigate -d '{"url":"..."}'`
   - Extract text: `curl http://localhost:9867/text` or `curl http://localhost:9867/snapshot`
   - Cleanup: `pinchtab instance stop` when done
3. URIBurner REST functions for content retrieval and RDF services
4. Terminal-owned OAuth flow — when the endpoint requires OAuth 2.0 authentication, execute the OAuth flow from the terminal (authorization code, client credentials, or device flow), capture the Bearer token, and inject it into subsequent REST/OpenAPI calls via `Authorization: Bearer {token}` headers
5. MCP via `https://linkeddata.uriburner.com/chat/mcp/messages` or `https://linkeddata.uriburner.com/chat/mcp/sse`
6. Authenticated LLM-mediated execution via `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`
7. OPAL Agent routing using recognizable OPAL function names

If the user explicitly names a protocol, follow that preference instead.

> **Important:** This routing applies only to the **content FETCH phase** (steps 1-7 above). Once source content is retrieved (via curl, PinchTab, WebFetch, or file read), the **transformation to RDF/JSON-LD** proceeds directly using the template prompts in section 2 — no further routing through steps 2-7 is needed unless you specifically need to query a live endpoint for additional data during transformation.

---

## Workflow

1. **Identify the source URL** — extract the `file:` or `http[s]:` URL from the user's request.
2. **Fetch content** — retrieve page or document text using available tools (browser automation, WebFetch, file read, etc.).
   > **PinchTab fallback:** Use when curl/WebFetch returns 401, 403, empty content, or clearly JS-rendered output. Common scenarios:
   > - LinkedIn profiles, posts, company pages
   > - X/Twitter profiles, threads, replies
   > - Sites with login walls or infinite scroll
   > - Pages requiring JavaScript execution to render content
   > **Important:** If PinchTab is not installed, ask the user explicitly for permission to install it before proceeding.
3. **Select template** — use the table above; check for explicit user preference.
4. **Determine output format** — RDF-Turtle is the default; respect explicit requests.
5. **Populate and apply the template** — substitute all `{placeholders}` and generate the output.
6. **Validate** — confirm syntactic correctness (balanced braces/brackets for JSON-LD; valid prefixes and triple syntax for Turtle).
7. **Compliance check** — run the automated compliance audit (see `scripts/validate-kg-compliance.sh` or the inline checklist below) against the generated output. Fix all FAIL items before proceeding.
8. **Deliver** — output in a single code block. If saving to file, use `{slug}-1.ttl` or `{slug}-1.jsonld`, incrementing as needed, saved to `{output-directory}`.
9. **Final validation** — validate the RDF syntax for the requested format (Turtle, JSON-LD, RDF/XML, etc.) before responding.

---

## Template 1 — Generic (JSON-LD)

Use for general web pages, articles, blog posts, and documentation.

⛔ **PRE-BUILD CHECK**: Before producing JSON-LD, re-read the "Post-Generation Checklist" below and the "Compliance Self-Audit" in the prompt. Confirm: `@base` = `{page_url}`, `schema:` = `http://schema.org/` (HTTP), `"@language": "en"` in `@context`, FAQ → `schema:FAQPage` + `schema:mainEntity`, glossary → `schema:DefinedTermSet` + `schema:hasDefinedTerm`, person IRI priority (LinkedIn → X → Substack → hash fallback), organization IRI priority (DBpedia 1st → Wikidata 2nd → LinkedIn `#this` 3rd → X `#this` 4th → Homepage `#this` 5th — primary subject must be canonical, not document-local; `owl:sameAs` for all remaining platform identities), concept/DefinedTerm IRI priority (standards-body/platform → DBpedia → Wikidata → document-local; document-local is default, `owl:sameAs` for external authorities), no `file:` IRIs, `owl:sameAs` not `schema:sameAs`, no blank nodes for `schema:Answer`. Build to pass every item — do not retro-fit.

### Placeholders

| Placeholder | Value |
|---|---|
| `{page_url}` | Canonical URL of the source — used as `@base` |
| `{selected_text}` | Full extracted text content of the source |

### Prompt

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
13. Whenever you encounter images, handle using schema:image on the relevant entity. For each distinct image found in the source content, create a schema:ImageObject describing it with properties such as name, description, contentUrl, thumbnailUrl, uploadDate, and caption where available — don't guess and insert non-existent information. Associate each ImageObject with its relevant article section or HowTo step via schema:hasPart or schema:about.
14. Whenever you encounter video, handle using the VideoObject type, specifying properties such as name, description, thumbnailUrl, uploadDate, contentUrl, and embedUrl — don't guess and insert non-existent information.
15. Whenever you encounter audio, handle using the AudioObject type, specifying properties such as name, description, thumbnailUrl, uploadDate, contentUrl, and embedUrl — don't guess and insert non-existent information.
16. For every person entity (authors, commentators, or explicitly mentioned individuals): use the highest-priority platform profile URL found in the source as the primary person IRI with `#this` appended, in this order: (a) LinkedIn profile URL → `{linkedin-url}#this`; (b) X/Twitter profile URL → `{x-url}#this`; (c) Substack author profile URL → `{substack-url}#this`; (d) Reddit user profile URL → `{reddit-url}#this`; (e) other social media or blog platform author/profile URL → `{platform-url}#this`; (f) otherwise derive a hash-based IRI from {page_url}. Add `schema:url` pointing to the bare profile URL and `schema:identifier` with the canonical profile URL. In every case, ALL discovered platform identities MUST be linked via owl:sameAs — e.g., owl:sameAs <https://www.linkedin.com/in/name/#this>, <https://x.com/handle/#this>, <https://substack.com/@handle/#this> — ensuring the person is resolvable from any direction. For JSON-LD, use @id for all owl:sameAs values.
    16a. **NEVER fabricate person names.** Use names exactly as they appear in the source document — character for character. Never guess, infer, or complete a partial name. If the source says only "Mr. Lutkus", the person's name is "Lutkus" (or whatever exact form appears). Do not add a first name unless the source explicitly provides it. If only a handle or username is given (e.g., "@jdoe"), use that handle as the name. Fabricating names produces wrong IRIs, wrong search results, and wrong attribution.
    16b. **Actively search for LinkedIn profiles.** When no platform profile URL is found in the source for a named person, attempt to find their LinkedIn profile via web search before falling back to a hash-based IRI. Search for the person's exact name as it appears in the source plus their organizational context (company, role, publication). Use the highest-confidence LinkedIn URL found. If no LinkedIn profile can be confidently matched, proceed to search for X/Twitter, then Substack, then other platforms. Only use the hash-based fallback after search attempts are exhausted.
     16c. **Actively resolve organization identities.** For every named organization, use the highest-priority identity in this order as the PRIMARY SUBJECT IRI: (a) DBpedia resource IRI → `http://dbpedia.org/resource/{name}`; (b) Wikidata entity IRI → `http://www.wikidata.org/entity/Q{...}`; (c) LinkedIn company page URL → `{linkedin-company-url}#this`; (d) X/Twitter org account URL → `{x-org-url}#this`; (e) official homepage URL → `{homepage-url}#this`; (f) otherwise derive a hash-based IRI from {page_url}. Never use a document-local IRI as the primary subject when a canonical platform IRI is available. Add `owl:sameAs` for all remaining discovered platform identities — e.g., owl:sameAs <http://dbpedia.org/resource/OpenAI>, <https://www.linkedin.com/company/openai/> — ensuring the organization is resolvable from any direction. For JSON-LD, use @id for all owl:sameAs values.
     16d. **NEVER fabricate organization names.** Use names exactly as they appear in the source document. If the source says "Google", use "Google" — not "Google LLC" or "Alphabet Inc." unless the source explicitly states the full legal name.
     16e. **Reconcile LinkedIn www and non-www forms.** When a person's primary LinkedIn IRI uses `linkedin.com/in/` (no www), add `owl:sameAs` to the `www.linkedin.com/in/` form, and vice versa. Both `https://linkedin.com/in/username#this` and `https://www.linkedin.com/in/username#this` denote the same profile and MUST be linked via `owl:sameAs` to ensure the person is resolvable from both forms.
17. Where relevant, include additional entity types when discovered e.g., Product, Offer, and Service etc.
18. Language-tag all annotation attribute values. In Turtle, every string literal MUST carry an `@en` language tag (e.g., `"text"@en`). In JSON-LD, the `@context` MUST include `"@language": "en"` so all string values inherit the tag implicitly. Both serializations MUST be semantically equivalent — untagged JSON-LD strings are a contract violation.
19. Describe article authors and publishers in detail.
20. Use a relatedLink attribute to comprehensively handle all inline URLs. Unless told otherwise, it should be a maximum of 20 relevant links.
21. You MUST ensure smart quotes are replaced with single quotes.
22. You MUST check and fix any JSON-LD usage errors based on its syntax rules e.g., missing @id designation for IRI values of attributes that only accept IRI values (e.g., schema:sameAs, owl:sameAs, etc.).
23. You MUST use http://schema.org/ (HTTP, not HTTPS) as the schema: namespace URI. Never use https://schema.org/.
24. You MUST wrap FAQ questions in a schema:FAQPage with schema:mainEntity listing all question IRIs. The FAQPage MUST be linked from the main article via schema:hasPart.
25. You MUST wrap glossary terms in a schema:DefinedTermSet with schema:hasDefinedTerm listing all term IRIs. The DefinedTermSet MUST be linked from the main article via schema:hasPart.
26. ALL DBpedia, Wikidata, and Wikipedia entity references MUST use fully expanded IRIs (e.g., http://dbpedia.org/resource/Tim_Berners-Lee) — never CURIEs or prefixed names.
27. For every country entity modeled as `schema:Country`, use a DBpedia country IRI as the primary subject IRI when confidently known; otherwise use a Wikidata country IRI when confidently known; only use a `{page_url}` hash IRI when neither can be confirmed. Add `owl:sameAs` between the selected country IRI and any confirmed DBpedia/Wikidata equivalent.
28. You MUST NOT use file: scheme IRIs anywhere. The @base or @prefix : MUST use the canonical https: URL of the source document with a # suffix.
29. If the response includes a lightweight ontology (custom classes, properties, or an owl:Ontology declaration), you MUST: (a) name and describe the ontology using schema:name and schema:description alongside rdfs:label and rdfs:comment; (b) add schema:identifier with the canonical source URL; (c) associate every class and property with the ontology using rdfs:isDefinedBy : . The owl:Ontology entity MUST be its own distinct resource — never a second rdf:type added to the document's `<>` schema:CreativeWork entity — and its schema:name/schema:description MUST be textually differentiated from the document entity's, never identical strings on both (e.g. document: "{Ontology Name} Document" / "Document about ..."; ontology: "{Ontology Name}" / the actual substantive TBox description). See agent-rdf-memory/howto/ontology-document-name-differentiation.ttl.
30. You MUST NOT use blank nodes for schema:Answer instances. Every schema:Answer MUST be a named entity with its own hash-based IRI (e.g., :a1, :a2) connected via schema:acceptedAnswer :aN — never schema:acceptedAnswer [ a schema:Answer ; ... ].
31. When you assert a directional relationship (e.g., schema:isPartOf), you MUST also assert its inverse on the target entity (e.g., schema:hasPart) — RDF does not infer inverses automatically, so both directions are needed for completeness.
32. Every logical entity group beyond FAQ/glossary/HowTo (e.g., use cases, technologies, architectural layers, key concepts) MUST be wrapped in a schema:CreativeWork and linked to the main article via schema:hasPart. No entity should be orphaned — every entity must be reachable from the main article through some path.
33. The main article MUST include prov:wasGeneratedBy linking to a schema:SoftwareApplication entity representing the skill that produced it. Declare @prefix prov: <http://www.w3.org/ns/prov#> . The skill entity IRI MUST use the canonical GitHub repository URL with #this appended: <https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator#this> for kg-generator, and <https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/rdf-infographic-skill#this> for rdf-infographic-skill. The skill entity MUST have schema:name (e.g., "kg-generator skill"), schema:url pointing to its GitHub source without #this (e.g., <https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator>), and schema:description. If multiple skills were used, use multiple prov:wasGeneratedBy triples. Do not mint document-local hash IRIs such as {source-url}#kgGeneratorSkill or {source-url}#rdfInfographicSkill for these skill entities.
33. For documentation/manual collections, inspect sitemap/search index/navigation for high-signal child pages. Pages covering APIs, SPARQL endpoints, query examples, services, data models, server/runtime platforms, and reporting workflows MUST be incorporated when they materially change the graph.
34. When a SPARQL endpoint, API endpoint, query service, or server platform is present, model it explicitly. SPARQL endpoints SHOULD use `schema:WebAPI` or another appropriate service class with `schema:url`; query families MAY use `schema:SoftwareSourceCode` and SHOULD link to the endpoint with `schema:target` or an equivalent property.
35. When SPARQL query examples or recipes are present, the query body MUST be preserved as `schema:text` on a `schema:SoftwareSourceCode` resource with `schema:programmingLanguage "SPARQL"`, linked to its endpoint via `schema:target`, and linked to a URL-encoded live query action via `schema:potentialAction` where the endpoint supports a GET query URL.

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
4. The main article has schema:hasPart linking to FAQPage, DefinedTermSet, HowTo, the ontology (:), and all entity group sections (use cases, technologies, etc.)
5. All DBpedia/Wikidata/Wikipedia IRIs are fully expanded (not CURIEs)
6. No file: scheme IRIs exist anywhere in the output
7. owl:sameAs is used for DBpedia cross-references (never schema:sameAs)
7a. All organization entities use the highest-priority canonical platform IRI as their primary subject (DBpedia 1st, Wikidata 2nd, LinkedIn `#this` 3rd, X `#this` 4th, Homepage `#this` 5th) — never a document-local IRI with `owl:sameAs` pointing to the canonical one. `owl:sameAs` links all remaining discovered platform identities.
7b. Organization names match source document exactly — no fabricated legal names or suffixes
8. @base or @prefix : is the canonical https: source URL with # suffix
9. If an ontology is present: (a) it has schema:name and schema:description, (b) schema:identifier with canonical URL, (c) all classes and properties have rdfs:isDefinedBy :
10. No blank nodes used for schema:Answer — every answer is a named entity (:a1, :a2, ...) with schema:acceptedAnswer :aN
11. Inverse relationships are explicit: for every schema:isPartOf there is a corresponding schema:hasPart, etc.
12. prov:wasGeneratedBy links the main article to a skill entity using the canonical IRI with #this (e.g., <https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator#this>), with schema:name, schema:url (GitHub without #this), and schema:description
13. Every entity's rdf:type matches its semantic role: HowToStep entities are a schema:HowToStep, FAQ questions are a schema:Question, FAQ answers are a schema:Answer, glossary terms are a schema:DefinedTerm (or appropriate type), sections are a schema:CreativeWork. No entity has a generic or mismatched type when a specific type is available.
14. owl:sameAs never has the same IRI in both subject and object positions — including www/non-www variants of the same platform (e.g., `https://www.linkedin.com/in/kidehen#this` owl:sameAs `https://linkedin.com/in/kidehen#this` is forbidden). Self-referential sameAs is a data integrity error, not a cross-reference.
15. Every entity type category uses the correct canonical IRI priority ladder as its primary subject: Organization (DBpedia → Wikidata → vendor site `#this` → LinkedIn `#this` → X `#this` → document-local), SoftwareApplication (vendor `#this` → DBpedia → Wikidata → document-local), Concept/DefinedTerm (standards-body/platform → DBpedia → Wikidata → document-local). `owl:sameAs` links all remaining discovered identities. No entity uses a document-local IRI as primary subject when a higher-priority canonical IRI exists.
Report: "COMPLIANCE SELF-AUDIT: X/16 passed. [list any FAIL items with the specific fix applied]. Final output follows."

GATE: 0 FAIL required before delivery. Every numbered rule in this prompt has a corresponding check in this audit. No rule without verification — unchecked rules are aspirational, not enforceable.```

### Post-Generation Checklist

- [ ] `@base` set to `{page_url}`
- [ ] `schema:` namespace uses `http://schema.org/` (HTTP, not HTTPS)
- [ ] All subject/object IRIs are hash-based relative IRIs (except known authority entities)
- [ ] FAQ questions wrapped in `schema:FAQPage` with `schema:mainEntity`
- [ ] Each FAQ question has `schema:isPartOf :faqSection` linking back to the FAQ section
- [ ] Glossary terms wrapped in `schema:DefinedTermSet` with `schema:hasDefinedTerm`
- [ ] Main article has `schema:hasPart` linking FAQPage, DefinedTermSet, HowTo, the ontology (:), and all entity group sections
- [ ] At least 10 `schema:Question` + `schema:Answer` pairs present
- [ ] Every entity's rdf:type matches its semantic role: HowToStep → schema:HowToStep, Question → schema:Question, Answer → schema:Answer, DefinedTerm → schema:DefinedTerm, ArticleSection → schema:CreativeWork. No entity typed as schema:Thing when a specific type is appropriate.
- [ ] `owl:sameAs` used (not `schema:sameAs`) for DBpedia cross-references
- [ ] All DBpedia/Wikidata/Wikipedia IRIs fully expanded (not CURIEs)
- [ ] Every `schema:Country` subject IRI follows the country denotation priority rule: DBpedia IRI if confirmed, else Wikidata IRI if confirmed, else source-grounded document IRI; add `owl:sameAs` for confirmed DBpedia/Wikidata equivalents.
- [ ] No `file:` scheme IRIs anywhere
- [ ] All IRI-valued attributes use `@id` — no plain string literals for IRI-only properties
- [ ] Inline double quotes within literals converted to single quotes
- [ ] Smart/curly quotes replaced with straight single quotes
- [ ] `relatedLink` includes up to 20 relevant inline URLs
- [ ] `@context` includes `"@language": "en"` so all string literals inherit the English language tag
- [ ] JSON-LD is syntactically valid
- [ ] No guessed media URLs (thumbnailUrl, contentUrl, embedUrl)
- [ ] Images from source content described using `schema:image` with `schema:ImageObject` where distinct
- [ ] Person names used exactly as they appear in source — no fabrication, no guessing first names from surnames
- [ ] LinkedIn profile actively searched for each named person without a platform URL in source before hash-based fallback
- [ ] Person IRIs derived from LinkedIn/X/Substack/Reddit/other-platform profile URLs where found; all platform identities linked via `owl:sameAs`
- [ ] Organization IRIs follow priority: DBpedia → Wikidata → LinkedIn → X → homepage → hash fallback. The highest-priority IRI is the primary subject — not a document-local IRI with `owl:sameAs`. `owl:sameAs` for all remaining discovered platform identities.
- [ ] Organization names match source exactly — no fabricated legal names
- [ ] Concept/DefinedTerm IRIs follow priority: standards-body/platform → DBpedia → Wikidata → document-local hash. When a standards-body/platform IRI exists, it is the primary subject; otherwise document-local is the primary subject with `owl:sameAs` for confirmed DBpedia/Wikidata equivalents.
- [ ] If ontology present: `schema:name` + `schema:description`, `schema:identifier`, all classes/properties have `rdfs:isDefinedBy :`
- [ ] `prov:wasGeneratedBy` links article to a skill entity using the canonical IRI with `#this` (e.g., `<https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator#this>`), with `schema:name`, `schema:url` (GitHub without `#this`), `schema:description`
- [ ] SPARQL query examples are preserved as `schema:SoftwareSourceCode` with query text, target endpoint/service, and correctly encoded live query actions when applicable
- [ ] `owl:sameAs` never has the same IRI in both subject and object (including www/non-www variants of the same platform)
- [ ] Entity canonical IRI priority ladders enforced: Organization (DBpedia 1st → Wikidata 2nd → vendor site `#this` 3rd → LinkedIn `#this` 4th → X `#this` 5th → document-local), SoftwareApplication (vendor `#this` 1st → DBpedia 2nd → Wikidata 3rd → document-local), Concept/DefinedTerm (standards-body/platform 1st → DBpedia 2nd → Wikidata 3rd → document-local)

## Template 2 — Business & Market Analysis (RDF-Turtle)

Use for business strategy posts, X/social threads, market analyses, and industry deep-dives.

⛔ **PRE-BUILD CHECK**: Before producing RDF-Turtle, re-read the "Post-Generation Checklist" below and the "Compliance Self-Audit" in the prompt. Confirm: `@prefix :` = `{post-url}#`, `schema:` = `http://schema.org/` (HTTP), ontology with `schema:name` + `schema:description` + `schema:identifier`, all custom classes/properties have `rdfs:isDefinedBy :`, at least 12 FAQ + at least 10 glossary + all procedural steps present as HowTo — covering every distinct question-worthy claim and defined term in the source, never capped at a fixed number once reached, organization IRI priority (DBpedia 1st → Wikidata 2nd → LinkedIn `#this` 3rd → X `#this` 4th → Homepage `#this` 5th — primary subject must be canonical, not document-local; `owl:sameAs` for all remaining platform identities), concept/DefinedTerm IRI priority (standards-body/platform → DBpedia → Wikidata → document-local; document-local is default, `owl:sameAs` for external authorities), NAICS codes with `?input=&year=2022&details=` pattern, no blank nodes for `schema:Answer`, `prov:wasGeneratedBy` on `:analysis`, no `file:` IRIs, all string literals carry `@en` language tags. Build to pass every item — do not retro-fit.

### Placeholders

| Placeholder | Value |
|---|---|
| `{url}` | URL of the original post or content being analysed |
| `{post-url}` | Used as the Turtle `@prefix :` base (append `#`) |
| `{selected_text}` | Full extracted text content of the source (post + thread/replies, if any) |
| `{current date}` | ISO 8601 date e.g. `2026-03-13` |

> `{post-url}` and `{url}` are often the same value.

**Example — X post (Robert Scoble vishing incident):**
```
{url} = "https://x.com/Scobleizer/status/2053367142045847649"
{post-url} = "https://x.com/Scobleizer/status/2053367142045847649"

RDF: @prefix : <https://x.com/Scobleizer/status/2053367142045847649#> .
HTML footer: RDF Resolver → https://x.com/Scobleizer/status/2053367142045847649
MD header: RDF Resolver → https://x.com/Scobleizer/status/2053367142045847649
Glossary terms: [Vishing](https://x.com/Scobleizer/status/2053367142045847649#vishing)
```

**Output file footer requirements:**
- HTML: Include `RDF: <a href="{source-url}">Resolver</a>` link in footer, plus link to Turtle file
- MD: Include `**RDF Resolver:** [URL](URL)` in header, plus `#term` fragment links in glossary

**Example — worked application of this template:** see "Example — Business Analysis Worked Example" below for a full illustration of how these generic instructions apply to a real source (a Julien Bek X-thread on AI "autopilots" disrupting services markets). That block is reference material only — do not copy its entity names, class names, or figures into an unrelated source's output.

### Example — Business Analysis Worked Example

This is a **worked illustration**, not part of the prompt the model executes. It shows how the generic instructions above resolve when applied to one specific source — a Julien Bek X-thread discussing AI-driven "autopilots" disrupting services markets by selling outcomes rather than tools, starting with outsourced intelligence-heavy tasks such as NDA drafting, insurance brokerage (~$140–200B labor TAM), and accounting (~$50–80B labor TAM), with structural shortages like the loss of ~340k U.S. accountants, data compounding enabling eventual judgment handling, debates around copilots vs. full autopilots, the innovator's dilemma, and founder collaboration opportunities.

Applying step 3 (lightweight ontology) to this source produced:
- Base class `:Industry` (the source's central recurring category — services verticals)
- Subclasses `:InsuranceBrokerageIndustry` and `:AccountingIndustry` (the two verticals the source compares)
- Custom properties `:hasLaborTAM` (range `xsd:string`) and `:hasAutomationReadiness` (range `xsd:string`) — the two recurring structured attributes the source assigns to each vertical
- Instances `:insuranceBrokerageVertical` and `:accountingVertical` holding the concrete TAM, readiness, NAICS, and offer data

Applying step 5 (core entities) to this source produced:
- The main analysis (`:analysis`), author (`:grok`), original post reference (`:originalXPost`), and Julien Bek as the person entity
- `:aiAutopilotDisruption` (Product), `:marketDisruptionAction`, `:servicesMarketDisruption` — the central phenomenon/thesis entities
- `:ndaExample` as a concrete illustrative task
- Organizations `:withCoverage` and `:rillet` and their respective autopilot products
- `:shortageEvent` for the U.S. accountant shortage statistic
- `:unitedStates` with its ISO code
- `:threadReplies`, `:cursorExample`, `:scalingChallenges` for discussion/example entities raised in the thread
- `:innovatorsDilemma` as a `CreativeWork` with `schema:isbn "9780060521998"`

Applying step 7 (preserve original details) to this source meant retaining, verbatim: the `$140-200B` and `$50-80B` TAM ranges, "High" automation readiness for both verticals, the 340,000 accountant shortage figure, the data-compounding explanation, the "Outcome-as-a-Service" model name, the innovator's-dilemma framing, the copilot-to-autopilot transition debate, and the founder-collaboration call to action.

### Prompt

```
You are an expert in semantic web modeling, RDF/Turtle serialization, and schema.org + lightweight ontology design.
Given the post/content at {url} (and its thread or surrounding discussion, if any):
"""
{selected_text}
"""
produce a **comprehensive RDF/Turtle document** that represents the full business & strategy analysis.
Follow ALL of these final design requirements exactly:
1. Base URI: Use relative hash URIs grounded in {post-url} as the namespace prefix :
2. Use schema.org as the primary vocabulary — use http://schema.org/ (HTTP, not HTTPS) as the schema: namespace URI — supplemented by:
   - skos: for glossary/concept definitions
   - org: for organizations
   - dbo: for selected DBpedia cross-references (via rdfs:seeAlso)
   - rdfs: for class/property definitions
3. Create a small custom lightweight ontology in the same namespace, derived from the actual structure of the source:
   - Identify the source's central recurring category (e.g., an industry, a technology domain, a product line, a comparison dimension) and define it as a base `rdfs:Class` in the local namespace.
   - Define one subclass `rdfs:Class` resource for each distinct instance of that category the source discusses (e.g., if the source compares several industry verticals, define one subclass per vertical; if it compares several technologies, define one subclass per technology).
   - Define custom properties on the base class for the recurring structured attributes the source assigns to each category instance (e.g., a size/market metric, a readiness/maturity rating, a status) — choose property names and `xsd:` ranges that fit what the source actually measures.
   - Create explicit instances of these subclasses to hold the concrete data the source provides (figures, ratings, identifiers, cross-references). Do NOT put instance data directly on the class definitions.
   - If the source has no natural category/vertical structure, a minimal ontology (base class + one or two properties, no subclasses) is acceptable — do not force an artificial hierarchy.
4. Use low-redundancy schema.org identifier modeling (Option 3 style):
   - Use dedicated properties when they exist: schema:naics (on industry instances), schema:isbn (on books), schema:identifier with a plain literal for unambiguous codes (e.g. an ISO 3166-1 alpha-2 country code)
   - When the source discusses one or more industry verticals, pair schema:naics (plain code string) with schema:identifier using the Census Bureau canonical lookup URL: https://www.census.gov/naics/?input={code}&year=2022&details={code}
   - Avoid unnecessary schema:PropertyValue wrappers unless genuinely required for disambiguation or extra metadata
5. Core entities that must be included:
   - The main analysis CreativeWork (:analysis)
   - The author/speaker entity and the original post/document reference, using the person/organization IRI priority rules in item 13 below
   - Identify the core entities, concepts, actions, and named things the source actually discusses (e.g., the central phenomenon or thesis being analyzed, any products/services named, any organizations named, any statistical/structural events cited, any countries or jurisdictions referenced, any books/works cited) and model each as an instance of the most specific applicable schema.org (or local ontology) class. Do not invent entities the source does not mention, and do not omit an entity the source treats as significant.
6. Mandatory structured sections (all must be present and complete — counts are a floor covering every distinct question-worthy claim/term/step in the source, not a fixed target):
   - schema:FAQPage (:faqSection) with **at least 12** schema:Question items (:q1, :q2, :q3, … numbered sequentially; extend the range as needed to cover every distinct question-worthy claim in the source)
   - skos:ConceptScheme + schema:DefinedTermSet (:glossarySection) with **at least 10** terms (:term1, :term2, … or mnemonic fragments; extend as needed to cover every distinct term the source introduces or defines)
   - schema:HowTo (:howtoSection) with schema:HowToStep items covering every procedural step in the source (:step1, :step2, … numbered sequentially)
7. Include all original details:
   - Preserve every quantitative detail exactly as stated in the source — statistics, monetary figures/ranges, dates, percentages, counts — do not paraphrase, round, or approximate them.
   - Preserve every named claim, model, or framework the source references (e.g., a named business model, a named theory, a named transition or debate it describes) as a distinct entity or literal, not folded into generic prose.
   - Preserve any concrete example, case, or anecdote the source uses to illustrate its argument.
   - Preserve any call to action, collaboration opportunity, or forward-looking statement the source makes.
8. Keep descriptions concise yet precise; avoid unnecessary verbosity in literals.
9. Output **only** the complete, valid Turtle document inside a single code block. Do not include explanations, comments outside Turtle, or any other text before/after the code block.
10. The main analysis CreativeWork (:analysis) MUST have schema:hasPart linking to :faqSection, :glossarySection, :howtoSection, and ALL other entity group sections (e.g., industry verticals, use cases, technologies).
11. All DBpedia references MUST use fully expanded IRIs (e.g., http://dbpedia.org/resource/...) — never CURIEs or prefixed names.
12. All Wikidata references MUST use fully expanded IRIs (e.g., http://www.wikidata.org/entity/...) — never CURIEs or prefixed names.
13. For every person entity: use the highest-priority platform profile URL found in the source as the primary person IRI with `#this` appended, in this order: (a) LinkedIn profile URL → `{linkedin-url}#this`; (b) X/Twitter profile URL → `{x-url}#this`; (c) Substack author profile URL → `{substack-url}#this`; (d) Reddit user profile URL → `{reddit-url}#this`; (e) other social media or blog platform author/profile URL → `{platform-url}#this`; (f) otherwise derive a hash-based IRI from {post-url}. Add `schema:url` pointing to the bare profile URL and `schema:identifier` with the canonical profile URL. In every case, ALL discovered platform identities MUST be linked via owl:sameAs — e.g., owl:sameAs <https://www.linkedin.com/in/name/#this>, <https://x.com/handle/#this>, <https://substack.com/@handle/#this>.
    13a. **NEVER fabricate person names.** Use names exactly as they appear in the source — character for character. Never guess, infer, or complete a partial name. If the source says "Mr. Lutkus", the person's name is "Lutkus" — do not add a first name. If only a handle is given, use that handle.
    13b. **Actively search for LinkedIn profiles.** When no platform profile URL is in the source for a named person, search for their LinkedIn via web search using their exact name and organizational context before falling back to a hash-based IRI. Only use the hash fallback after search attempts are exhausted.
     13c. **Actively resolve organization identities.** For every named organization, use the highest-priority identity in this order as the PRIMARY SUBJECT IRI: (a) DBpedia resource IRI → `http://dbpedia.org/resource/{name}`; (b) Wikidata entity IRI → `http://www.wikidata.org/entity/Q{...}`; (c) LinkedIn company page URL → `{linkedin-company-url}#this`; (d) X/Twitter org account URL → `{x-org-url}#this`; (e) official homepage URL → `{homepage-url}#this`; (f) otherwise derive a hash-based IRI from {page_url}. Never use a document-local IRI as the primary subject when a canonical platform IRI is available. Add `owl:sameAs` for all remaining discovered platform identities — ensuring the organization is resolvable from any direction. For JSON-LD, use @id for all owl:sameAs values.
     13d. **NEVER fabricate organization names.** Use names exactly as they appear in the source document. If the source says "Google", use "Google" — not "Google LLC" or "Alphabet Inc." unless the source explicitly states the full legal name.
     13e. **Reconcile LinkedIn www and non-www forms.** When a person's primary LinkedIn IRI uses `linkedin.com/in/` (no www), add `owl:sameAs` to the `www.linkedin.com/in/` form, and vice versa. Both denote the same profile and MUST be linked via `owl:sameAs` to ensure resolvability from both forms.
14. The lightweight ontology MUST be named and described using schema:name and schema:description alongside rdfs:label/rdfs:comment, with schema:identifier carrying the canonical source URL. Every class and property MUST have rdfs:isDefinedBy : linking it to the ontology.
15. You MUST NOT use blank nodes for schema:Answer instances. Every schema:Answer MUST be a named entity with its own hash-based IRI (e.g., :a1, :a2) connected via schema:acceptedAnswer :aN — never schema:acceptedAnswer [ a schema:Answer ; ... ].
16. For every directional relationship you assert (e.g., schema:isPartOf), you MUST also assert its inverse on the target entity (e.g., schema:hasPart) — RDF does not infer inverses, so both directions are necessary.
17. The main analysis (:analysis) MUST include prov:wasGeneratedBy linking to a schema:SoftwareApplication entity representing the kg-generator skill. Declare @prefix prov: <http://www.w3.org/ns/prov#> . The skill entity IRI MUST be <https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator#this>. The skill entity MUST have schema:name "kg-generator skill", schema:url <https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator>, and schema:description. Do not mint document-local hash IRIs such as {source-url}#kgGeneratorSkill for skill entities.
Current date for metadata: {current date}.

CRITICAL — Before outputting the Turtle, you MUST perform a compliance self-audit. Verify each item and report PASS or FAIL (with the violation fixed):
1. schema: namespace is http://schema.org/ (not https://schema.org/)
2. :analysis has schema:hasPart linking :faqSection, :glossarySection, :howtoSection
3. :faqSection is a schema:FAQPage with schema:mainEntity listing at least 12 schema:Question items, covering every distinct question-worthy claim in the source (not capped at 12)
4. :glossarySection is a schema:DefinedTermSet with schema:hasDefinedTerm listing at least 10 terms, covering every distinct term the source introduces or defines (not capped at 10)
5. :howtoSection is a schema:HowTo with schema:step listing every procedural step in the source, numbered sequentially
6. All DBpedia/Wikidata IRIs are fully expanded (not CURIEs)
6a. All organization entities use the highest-priority canonical platform IRI as their primary subject (DBpedia 1st, Wikidata 2nd, LinkedIn `#this` 3rd, X `#this` 4th, Homepage `#this` 5th) — never a document-local IRI with `owl:sameAs` pointing to the canonical one. `owl:sameAs` links all remaining discovered platform identities.
6b. Organization names match source document exactly — no fabricated legal names or suffixes
7. NAICS codes use ?input=&year=2022&details= pattern (not ?code=)
8. No file: scheme IRIs exist anywhere
9. Ontology has schema:name + schema:description + schema:identifier; all custom classes/properties have rdfs:isDefinedBy :
10. No blank nodes for schema:Answer — every answer is a named entity (:aN) with schema:acceptedAnswer :aN
11. Inverse relationships explicit: every schema:isPartOf has a corresponding schema:hasPart, etc.
12. prov:wasGeneratedBy links :analysis to a skill entity using the canonical IRI <https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator#this>, with schema:name, schema:url (GitHub without #this), and schema:description
13. Every entity's rdf:type matches its semantic role: HowToStep entities are a schema:HowToStep, FAQ questions are a schema:Question, FAQ answers are a schema:Answer, glossary terms are a schema:DefinedTerm, sections are a schema:CreativeWork. No entity has a generic or mismatched type when a specific type is available.
14. owl:sameAs never has the same IRI in both subject and object positions — including www/non-www variants of the same platform (e.g., `https://www.linkedin.com/in/kidehen#this` owl:sameAs `https://linkedin.com/in/kidehen#this` is forbidden). Self-referential sameAs is a data integrity error, not a cross-reference.
15. Every entity type category uses the correct canonical IRI priority ladder as its primary subject: Organization (DBpedia → Wikidata → vendor site `#this` → LinkedIn `#this` → X `#this` → document-local), SoftwareApplication (vendor `#this` → DBpedia → Wikidata → document-local), Concept/DefinedTerm (standards-body/platform → DBpedia → Wikidata → document-local). `owl:sameAs` links all remaining discovered identities. No entity uses a document-local IRI as primary subject when a higher-priority canonical IRI exists.
Report: "COMPLIANCE SELF-AUDIT: X/16 passed. [list any FAIL items, already fixed]. Output follows."

GATE: 0 FAIL required before delivery. Every numbered rule in this prompt has a corresponding check in this audit. No rule without verification — unchecked rules are aspirational, not enforceable.```

### NAICS Identifier Pattern

Always use **both** `schema:naics` and `schema:identifier` together on industry vertical instances:

```turtle
:insuranceBrokerageVertical a :InsuranceBrokerageIndustry ;
    schema:naics "524210" ;
    schema:identifier "https://www.census.gov/naics/?input=524210&year=2022&details=524210" .

:accountingVertical a :AccountingIndustry ;
    schema:naics "541211" ;
    schema:identifier "https://www.census.gov/naics/?input=541211&year=2022&details=541211" .
```

**Never** use the deprecated `?code={code}` URL pattern.

### schema:identifier Patterns by Entity Type

| Entity type | Pattern | Example |
|---|---|---|
| Industry vertical | Census Bureau NAICS URL | `https://www.census.gov/naics/?input=524210&year=2022&details=524210` |
| Country | ISO 3166-1 alpha-2 plain literal | `"US"` |
| Book | ISBN prefixed notation | `"ISBN:9780060521998"` |
| Person | Canonical profile URL | `"https://x.com/JulienBek"` |
| Organization | Official homepage URL | `"https://withcoverage.com"` |
| Software/Product | Product homepage URL | `"https://www.cursor.com"` |
| Social media post | Canonical permalink | `"https://x.com/user/status/123"` |
| Web standard | Spec URL | `"https://www.w3.org/TR/sparql11-overview/"` |
| Formal standard | Standards designation string | `"ISO/IEC 9075"` |

**Anti-patterns to avoid:**

- ❌ `schema:sameAs` for DBpedia links → use `owl:sameAs` or `rdfs:seeAlso`
- ❌ `schema:PropertyValue` wrappers for simple codes → use plain literals
- ❌ `?code={code}` NAICS URL pattern → use `?input={code}&year=2022&details={code}`
- ❌ Plain string literals for IRI-only properties → always use `@id` in JSON-LD

### Post-Generation Checklist

- [ ] `@prefix :` set to `{post-url}#`
- [ ] `schema:` namespace uses `http://schema.org/` (HTTP, not HTTPS)
- [ ] `:analysis schema:hasPart :faqSection, :glossarySection, :howtoSection`
- [ ] Lightweight ontology present: base class derived from the source's central category, subclasses per distinct instance of that category (or none, if the source has no natural category structure), and custom properties for the source's recurring structured attributes
- [ ] Instance data on instances only — not on class definitions
- [ ] Both `schema:naics` and `schema:identifier` (Census URL) on each industry vertical instance, when the source discusses industry verticals
- [ ] At least 12 FAQ questions (numbered sequentially, extended if the source supports more distinct questions) wrapped in `schema:FAQPage` with `schema:mainEntity` — count covers every distinct question-worthy claim, not capped once 12 is reached
- [ ] Each FAQ question has `schema:isPartOf :faqSection` linking back to the FAQ section
- [ ] At least 10 glossary terms (extended if more distinct terms exist) wrapped in `schema:DefinedTermSet` with `schema:hasDefinedTerm` — count covers every distinct term, not capped once 10 is reached
- [ ] All procedural steps present as HowTo steps (numbered sequentially) wrapped in `schema:HowTo` with `schema:step`
- [ ] Each HowTo step has `schema:isPartOf :howtoSection` linking back to the HowTo section
- [ ] All DBpedia/Wikidata IRIs fully expanded (not CURIEs)
- [ ] Organization IRIs follow priority: DBpedia → Wikidata → LinkedIn → X → homepage → hash fallback. The highest-priority IRI is the primary subject — not a document-local IRI with `owl:sameAs`. `owl:sameAs` for all remaining discovered platform identities.
- [ ] Organization names match source exactly — no fabricated legal names
- [ ] Concept/DefinedTerm IRIs follow priority: standards-body/platform → DBpedia → Wikidata → document-local hash. When a standards-body/platform IRI exists, it is the primary subject; otherwise document-local is the primary subject with `owl:sameAs` for confirmed DBpedia/Wikidata equivalents.
- [ ] All quantitative details (statistics, monetary figures/ranges, dates, percentages, counts) preserved exactly as stated in the source — not paraphrased, rounded, or approximated
- [ ] `schema:isbn` present on any book/work entity the source cites with an ISBN
- [ ] `schema:identifier` present with the appropriate plain-literal code (e.g. ISO 3166-1 alpha-2) on any country entity the source references
- [ ] NAICS URLs use `?input=&year=2022&details=` pattern (not `?code=`)
- [ ] All string literals carry `@en` language tags (e.g., `"text"@en`)
- [ ] No `file:` scheme IRIs anywhere
- [ ] `prov:wasGeneratedBy` links :analysis to a skill entity using the canonical IRI `<https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator#this>`, with `schema:name`, `schema:url` (GitHub without `#this`), `schema:description`
- [ ] Ontology has `schema:name` + `schema:description` + `schema:identifier`; all classes/properties have `rdfs:isDefinedBy :`
- [ ] Every entity's rdf:type matches its semantic role: HowToStep → schema:HowToStep, Question → schema:Question, Answer → schema:Answer, DefinedTerm → schema:DefinedTerm, ArticleSection → schema:CreativeWork, ontology classes → their declared types. No entity typed as schema:Thing when a specific type exists.
- [ ] Output is the Turtle code block only — no surrounding text
- [ ] `owl:sameAs` never has the same IRI in both subject and object (including www/non-www variants of the same platform)
- [ ] Entity canonical IRI priority ladders enforced: Organization (DBpedia 1st → Wikidata 2nd → vendor site `#this` 3rd → LinkedIn `#this` 4th → X `#this` 5th → document-local), SoftwareApplication (vendor `#this` 1st → DBpedia 2nd → Wikidata 3rd → document-local), Concept/DefinedTerm (standards-body/platform 1st → DBpedia 2nd → Wikidata 3rd → document-local)

---

## Template 3 — Conference & Event Recap (RDF-Turtle)

Use for conference/event recaps, multi-speaker panel summaries, case-study-driven narrative articles, and "takeaways" or "lessons learned" write-ups organized around sessions, speakers, and organizations.

⛔ **PRE-BUILD CHECK**: Before producing RDF-Turtle, re-read the "Post-Generation Checklist" below and the "Compliance Self-Audit" in the prompt. Confirm: `@prefix :` = `{post-url}#`, `schema:` = `http://schema.org/` (HTTP), ontology with `schema:name` + `schema:description` + `schema:identifier`, all custom classes/properties have `rdfs:isDefinedBy :`, at least 12 FAQ + at least 10 glossary — covering every distinct question-worthy claim and defined term in the source, never capped at a fixed number once reached, organization IRI priority (DBpedia 1st → Wikidata 2nd → LinkedIn `#this` 3rd → X `#this` 4th → Homepage `#this` 5th — primary subject must be canonical, not document-local; `owl:sameAs` for all remaining platform identities), person IRI priority (LinkedIn → X → Substack → Reddit → other platforms → hash fallback), concept/DefinedTerm IRI priority (standards-body/platform → DBpedia → Wikidata → document-local), every quote/case-study/panel/question entity typed with its specific local class (never left as a bare `schema:CreativeWork` when a more specific local class applies), no blank nodes for `schema:Answer`, `prov:wasGeneratedBy` on the main article, no `file:` IRIs, all string literals carry `@en` language tags. Build to pass every item — do not retro-fit.

### Placeholders

| Placeholder | Value |
|---|---|
| `{url}` | URL of the original article/post being analysed |
| `{post-url}` | Used as the Turtle `@prefix :` base (append `#`) |
| `{selected_text}` | Full extracted text content of the source article |
| `{current date}` | ISO 8601 date e.g. `2026-03-13` |

> `{post-url}` and `{url}` are often the same value.

**Example — worked application of this template:** see "Example — Conference & Event Recap Worked Example" below for a full illustration of how these generic instructions apply to a real source (Juan Sequeda's "CDOIQ 2026: My Honest, No-BS Takeaways" Substack recap). That block is reference material only — do not copy its entity names, class names, or figures into an unrelated source's output.

### Example — Conference & Event Recap Worked Example

This is a **worked illustration**, not part of the prompt the model executes. It shows how the generic instructions below resolve when applied to one specific source — Juan Sequeda's CDOIQ 2026 conference recap, structured as five narrative parts covering foundational governance case studies (Nationwide, KeyBank, Leidos, Farm Credit Services of America), a tech-vs-non-tech contrast (ADP, Capital One), a CDO panel on the changing role (Humana, Ford, Lowe's), an agentic-AI reality-check panel (CVS, CSL, The Hartford, JPMorgan Chase), and a closing section on semantics as infrastructure ending in three strategic questions for data executives.

Applying the ontology step to this source produced a base set of local classes and properties reusable for any conference/event recap:
- `:CaseStudy` — an organizational case study or initiative presented at the event, with `:hasOutcome` (measured/reported result) and `:featuresOrganization` (the org profiled)
- `:PanelSession` — a multi-speaker panel, with `:hasModerator` and `:hasPanelist` (both range `schema:Person`)
- `:Quotation` — a direct or closely paraphrased statement attributed to a named speaker (modeled as `schema:CreativeWork` subtype with `schema:creator` and `schema:text`)
- `:StrategicQuestion` — one of a closing set of questions the author poses to readers (included only because this source ends with exactly that; omit this class for sources that don't)

Applying the "identify the source's narrative structure" step produced one `schema:Event` (`:cdoiqConference`) for the conference itself, one `schema:Article` (`:article`) as the main entity, and six `schema:CreativeWork` part-sections (`:partOneSection` … `:partFiveSection`, `:closingSection`) each linked via `schema:hasPart` to the case studies, panel sessions, and quotations discussed in that part — e.g. `:partOneSection schema:hasPart :nationwideCaseStudy, :keyBankCaseStudy, :leidosCaseStudy, :farmCreditCaseStudy`.

Applying the "preserve original details" step meant retaining, verbatim: each case study's measured outcome (e.g. "Writing time cut roughly in half; estimated 20,000-24,000 hours saved per year"), each named speaker's role and organization, each direct quotation's exact wording, and the three closing strategic questions exactly as posed.

### Prompt

```
You are an expert in semantic web modeling, RDF/Turtle serialization, and schema.org + lightweight ontology design.
Given the article/post at {url}:
"""
{selected_text}
"""
produce a **comprehensive RDF/Turtle document** that represents the full conference/event recap as a knowledge graph.
Follow ALL of these final design requirements exactly:
1. Base URI: Use relative hash URIs grounded in {post-url} as the namespace prefix :
2. Use schema.org as the primary vocabulary — use http://schema.org/ (HTTP, not HTTPS) as the schema: namespace URI — supplemented by:
   - skos: for glossary/concept definitions
   - rdfs: for class/property definitions
   - prov: for generation provenance
3. Create a small custom lightweight ontology in the same namespace, derived from the actual structure of the source. Typical recurring local classes for this content type (define only the ones the source actually uses; do not force unused classes into the ontology):
   - `:CaseStudy` — an organizational case study or initiative discussed in the source, with a custom property `:hasOutcome` (range `xsd:string`) for its measured/reported result and `:featuresOrganization` (range `schema:Organization`) for the org it profiles
   - `:PanelSession` — a multi-speaker panel or discussion, with custom properties `:hasModerator` and `:hasPanelist` (both range `schema:Person`)
   - `:Quotation` — a direct or closely paraphrased statement attributed to a named speaker (use `schema:creator` for the speaker and `schema:text` for the exact wording)
   - `:StrategicQuestion` (or a source-appropriate equivalent name) — an author-posed question directed at readers, only if the source actually closes with or poses such questions
   - If the source's narrative introduces a different recurring structured pattern not covered above (e.g., a recurring "lesson," "prediction," or "recommendation" unit), define a local class for it following the same pattern: a class plus whatever custom properties capture its recurring structured attributes.
   - Create explicit instances of these classes to hold the concrete data (organization, outcome, speaker, exact wording). Do NOT put instance data directly on the class definitions.
   - Every quote/case-study/panel/question entity in the graph MUST be typed with its specific local class, not left as a generic `schema:CreativeWork`.
4. Identify the source's own narrative structure (its sections/parts, however the source itself divides them) and represent each as a `schema:CreativeWork` linked from the main article via `schema:hasPart`, with each part in turn linking to the case studies, panel sessions, quotations, and other entities discussed within it.
5. If the source discusses a named conference, summit, or event, model it as a `schema:Event` with `schema:name` and, where stated, `schema:startDate`/`schema:location`. Link the main article to it via `schema:about`.
6. Core entities that must be included — identify the core entities the source actually discusses and model each as an instance of the most specific applicable class:
   - The main analysis `schema:Article` (:article), its author, and the original post/document reference, using the person/organization IRI priority rules in item 11 below
   - Every organization named as the subject of a case study or panel discussion
   - Every named speaker, panelist, or moderator quoted or attributed
   - Every distinct case study, panel session, and quotation the source presents
   - Any closing questions, calls to action, or forward-looking statements the source poses to its readers
   - Do not invent entities the source does not mention, and do not omit an entity the source treats as significant.
7. Mandatory structured sections (all must be present and complete — counts are a floor covering every distinct question-worthy claim/term in the source, not a fixed target):
   - schema:FAQPage (:faqSection) with **at least 12** schema:Question items (:q1, :q2, :q3, … numbered sequentially; extend as needed to cover every distinct question-worthy claim in the source)
   - skos:ConceptScheme + schema:DefinedTermSet (:glossarySection) with **at least 10** terms (extend as needed to cover every distinct term the source introduces or defines)
   - schema:HowTo is OPTIONAL for this content type — include it only if the source contains genuine procedural steps; a narrative recap with no procedural content does not need one.
8. Include all original details:
   - Preserve every quantitative outcome exactly as stated in the source — statistics, counts, percentages, time/cost savings — do not paraphrase, round, or approximate them.
   - Preserve every direct or closely paraphrased quotation's exact wording, attributed to its speaker via `schema:creator`.
   - Preserve every named speaker's role and organization exactly as the source states them.
   - Preserve any closing questions or calls to action exactly as posed.
9. Keep descriptions concise yet precise; avoid unnecessary verbosity in literals.
10. Output **only** the complete, valid Turtle document inside a single code block. Do not include explanations, comments outside Turtle, or any other text before/after the code block.
11. For every person entity: use the highest-priority platform profile URL found in the source as the primary person IRI with `#this` appended, in this order: (a) LinkedIn profile URL → `{linkedin-url}#this`; (b) X/Twitter profile URL → `{x-url}#this`; (c) Substack author profile URL → `{substack-url}#this`; (d) Reddit user profile URL → `{reddit-url}#this`; (e) other social media or blog platform author/profile URL → `{platform-url}#this`; (f) otherwise derive a hash-based IRI from {post-url}. Add `schema:url` pointing to the bare profile URL and `schema:identifier` with the canonical profile URL. ALL discovered platform identities MUST be linked via owl:sameAs.
    11a. **NEVER fabricate person names.** Use names exactly as they appear in the source.
    11b. **Actively search for LinkedIn profiles.** When no platform profile URL is in the source for a named speaker/panelist, search for their LinkedIn via web search using their exact name and organizational context before falling back to a hash-based IRI.
    11c. **Actively resolve organization identities.** For every named organization, use the highest-priority identity in this order as the PRIMARY SUBJECT IRI: (a) DBpedia resource IRI; (b) Wikidata entity IRI; (c) LinkedIn company page URL `#this`; (d) X/Twitter org account URL `#this`; (e) official homepage URL `#this`; (f) otherwise derive a hash-based IRI from {post-url}. Add `owl:sameAs` for all remaining discovered platform identities.
    11d. **NEVER fabricate organization names.** Use names exactly as they appear in the source document.
    11e. **Reconcile LinkedIn www and non-www forms** with `owl:sameAs` in both directions.
12. All DBpedia references MUST use fully expanded IRIs (e.g., http://dbpedia.org/resource/...) — never CURIEs or prefixed names. All Wikidata references MUST use fully expanded IRIs.
13. The lightweight ontology MUST be named and described using schema:name and schema:description alongside rdfs:label/rdfs:comment, with schema:identifier carrying the canonical source URL. Every class and property MUST have rdfs:isDefinedBy : linking it to the ontology.
14. You MUST NOT use blank nodes for schema:Answer instances. Every schema:Answer MUST be a named entity with its own hash-based IRI (e.g., :a1, :a2) connected via schema:acceptedAnswer :aN.
15. For every directional relationship you assert (e.g., schema:isPartOf), you MUST also assert its inverse on the target entity (e.g., schema:hasPart).
16. The main article MUST include prov:wasGeneratedBy linking to a schema:SoftwareApplication entity representing the kg-generator skill. Declare @prefix prov: <http://www.w3.org/ns/prov#> . The skill entity IRI MUST be <https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator#this>, with schema:name "kg-generator skill", schema:url <https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator>, and schema:description.
Current date for metadata: {current date}.

CRITICAL — Before outputting the Turtle, you MUST perform a compliance self-audit. Verify each item and report PASS or FAIL (with the violation fixed):
1. schema: namespace is http://schema.org/ (not https://schema.org/)
2. The main article has schema:hasPart linking every narrative section, :faqSection, and :glossarySection
3. :faqSection is a schema:FAQPage with schema:mainEntity listing at least 12 schema:Question items, covering every distinct question-worthy claim in the source
4. :glossarySection is a schema:DefinedTermSet with schema:hasDefinedTerm listing at least 10 terms, covering every distinct term the source introduces or defines
5. All DBpedia/Wikidata IRIs are fully expanded (not CURIEs)
5a. All organization entities use the highest-priority canonical platform IRI as their primary subject (DBpedia 1st, Wikidata 2nd, LinkedIn `#this` 3rd, X `#this` 4th, Homepage `#this` 5th)
5b. Organization names match source document exactly — no fabricated legal names or suffixes
6. No file: scheme IRIs exist anywhere
7. Ontology has schema:name + schema:description + schema:identifier; all custom classes/properties have rdfs:isDefinedBy :
8. No blank nodes for schema:Answer — every answer is a named entity (:aN) with schema:acceptedAnswer :aN
9. Inverse relationships explicit: every schema:isPartOf has a corresponding schema:hasPart
10. prov:wasGeneratedBy links the main article to a skill entity using the canonical IRI <https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator#this>, with schema:name, schema:url (GitHub without #this), and schema:description
11. Every case study, panel session, quotation, and closing-question entity is typed with its specific local class — none is left as a bare schema:CreativeWork
12. owl:sameAs never has the same IRI in both subject and object positions — including www/non-www variants of the same platform
13. Every entity type category uses the correct canonical IRI priority ladder as its primary subject: Organization (DBpedia → Wikidata → vendor site `#this` → LinkedIn `#this` → X `#this` → document-local), Concept/DefinedTerm (standards-body/platform → DBpedia → Wikidata → document-local)
Report: "COMPLIANCE SELF-AUDIT: X/13 passed. [list any FAIL items, already fixed]. Output follows."

GATE: 0 FAIL required before delivery. Every numbered rule in this prompt has a corresponding check in this audit. No rule without verification — unchecked rules are aspirational, not enforceable.```

### Post-Generation Checklist

- [ ] `@prefix :` set to `{post-url}#`
- [ ] `schema:` namespace uses `http://schema.org/` (HTTP, not HTTPS)
- [ ] Main article `schema:hasPart` links every narrative section, `:faqSection`, and `:glossarySection`
- [ ] Lightweight ontology present, derived from the source's own recurring structure (e.g. `:CaseStudy`, `:PanelSession`, `:Quotation`, `:StrategicQuestion` where applicable) — no unused classes forced in, no needed class omitted
- [ ] Instance data on instances only — not on class definitions
- [ ] Every case study/panel/quotation/question entity typed with its specific local class, not a bare `schema:CreativeWork`
- [ ] If the source names a conference/event, it is modeled as `schema:Event` and linked from the article via `schema:about`
- [ ] At least 12 FAQ questions (numbered sequentially, extended if the source supports more distinct questions) wrapped in `schema:FAQPage` with `schema:mainEntity`
- [ ] Each FAQ question has `schema:isPartOf :faqSection` linking back to the FAQ section
- [ ] At least 10 glossary terms (extended if more distinct terms exist) wrapped in `schema:DefinedTermSet` with `schema:hasDefinedTerm`
- [ ] All DBpedia/Wikidata IRIs fully expanded (not CURIEs)
- [ ] Organization IRIs follow priority: DBpedia → Wikidata → LinkedIn → X → homepage → hash fallback
- [ ] Organization names match source exactly — no fabricated legal names
- [ ] Person IRIs derived from LinkedIn/X/Substack/Reddit/other-platform profile URLs where found; all platform identities linked via `owl:sameAs`
- [ ] Every quantitative outcome preserved exactly as stated in the source — not paraphrased, rounded, or approximated
- [ ] Every quotation's exact wording preserved, attributed via `schema:creator`
- [ ] No `file:` scheme IRIs anywhere
- [ ] All string literals carry `@en` language tags
- [ ] `prov:wasGeneratedBy` links the main article to a skill entity using the canonical IRI `<https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator#this>`, with `schema:name`, `schema:url` (GitHub without `#this`), `schema:description`
- [ ] Ontology has `schema:name` + `schema:description` + `schema:identifier`; all classes/properties have `rdfs:isDefinedBy :`
- [ ] Output is the Turtle code block only — no surrounding text
- [ ] `owl:sameAs` never has the same IRI in both subject and object (including www/non-www variants of the same platform)

---

## Template 4 — Thesis & Framework Article (RDF-Turtle)

Use for opinion/thesis articles that propose a named framework — a small, ordered set of named pillars, principles, or practices — especially when the response should include an agent-authored critical-perspective section that engages the thesis on its merits, potentially reusing ontology terms already minted in companion Knowledge Graphs on a related topic.

⛔ **PRE-BUILD CHECK**: Before producing RDF-Turtle, re-read the "Post-Generation Checklist" below and the "Compliance Self-Audit" in the prompt. Confirm: `@prefix :` = `{post-url}#`, `schema:` = `http://schema.org/` (HTTP), ontology with `schema:name` + `schema:description` + `schema:identifier`, all custom classes/properties have `rdfs:isDefinedBy :`, at least 12 FAQ + at least 10 glossary + HowTo present if the thesis implies actionable steps, organization/person IRI priority ladders, any critical-perspective entity's `schema:author` set to the generating skill (never the human principal directly) with `schema:accountablePerson` on the principal's WebID, reused external ontology terms referenced via their own namespace prefix (never re-minted locally), no blank nodes for `schema:Answer`, `prov:wasGeneratedBy`, no `file:` IRIs, all string literals carry `@en` language tags. Build to pass every item — do not retro-fit.

### Placeholders

| Placeholder | Value |
|---|---|
| `{url}` | URL of the original article/post being analysed |
| `{post-url}` | Used as the Turtle `@prefix :` base (append `#`) |
| `{selected_text}` | Full extracted text content of the source article |
| `{current date}` | ISO 8601 date e.g. `2026-03-13` |
| `{principal-webid}` | The human principal's canonical WebID IRI (e.g. `https://www.linkedin.com/in/kidehen#this`), used for `schema:accountablePerson`/`prov:actedOnBehalfOf` on any agent-authored critical-perspective entity |

> `{post-url}` and `{url}` are often the same value.

**Example — worked application of this template:** see "Example — Thesis & Framework Article Worked Example" below for a full illustration of how these generic instructions apply to a real source (sn scratchpad's "The Reverse Information Paradox"). That block is reference material only — do not copy its entity names, class names, or figures into an unrelated source's output.

### Example — Thesis & Framework Article Worked Example

This is a **worked illustration**, not part of the prompt the model executes. It shows how the generic instructions below resolve when applied to one specific source — sn scratchpad's "The Reverse Information Paradox," which argues AI inverts Kenneth Arrow's Information Paradox (the buyer, not the seller, now risks giving away proprietary knowledge) and prescribes a named five-part framework — Control, Capability, Choice, Cost, Compound — as the trust boundary enterprises need.

Applying the ontology step to this source produced:
- Base class `:TrustBoundaryPillar` (the source's named framework unit) with custom property `:addressesRisk` (range `xsd:string`) capturing the specific risk each pillar mitigates
- Five instances (`:controlPillar` … `:compoundPillar`), each `schema:position`-ordered, each linked via a reused custom property `:standardsBasedMechanism` to existing open-standard/Linked-Data concepts

Applying the "critical perspective" step to this source produced a distinct `:criticalPerspectivesSection`, containing `:standardsAlreadySolveTrustBoundary` — typed with an **externally reused** class, `karp:CriticalPerspective`, minted in a prior companion Knowledge Graph on a related topic (theCUBE Research's Alex Karp analysis), rather than re-minting an equivalent local class. That entity's `schema:author` is set to the kg-generator skill entity (not the human principal directly), with `schema:accountablePerson` pointing to the principal's WebID — the correct delegation pattern for agent-synthesized commentary (see the `kg-curation-attribution` pattern: never set `schema:author` of agent-authored content directly to the principal). The critical perspective also reused `avc:enterpriseKnowledgeGraph`, `avc:abac`, and `avc:reasoningLearningSeparation` — concepts already minted in a different companion KG (`ai-value-capture-response`) — via their own namespace prefix, linked with `rdfs:seeAlso` back to both companion documents, rather than duplicating those definitions locally.

Applying the "preserve original details" step meant retaining, verbatim: each pillar's exact description and risk statement, the direct quotations from Kenneth Arrow's NBER paper and Alex Karp's social post (each modeled as `schema:Quotation` with `schema:citation` to its source), and the five-layer "Operating Environment" (Identity, Identification, Authentication, Authorization, Storage) the critical perspective proposes as the concrete mechanism.

### Prompt

```
You are an expert in semantic web modeling, RDF/Turtle serialization, and schema.org + lightweight ontology design.
Given the article/post at {url}:
"""
{selected_text}
"""
produce a **comprehensive RDF/Turtle document** that represents the full thesis article as a knowledge graph.
Follow ALL of these final design requirements exactly:
1. Base URI: Use relative hash URIs grounded in {post-url} as the namespace prefix :
2. Use schema.org as the primary vocabulary — use http://schema.org/ (HTTP, not HTTPS) as the schema: namespace URI — supplemented by:
   - skos: for glossary/concept definitions
   - rdfs: for class/property definitions
   - prov: for generation provenance
   - Any namespace prefix needed to reuse an existing external ontology term (see item 3c)
3. Create a small custom lightweight ontology in the same namespace, derived from the actual structure of the source:
   a. Identify the source's central named framework — the ordered set of pillars, principles, or practices it prescribes — and define a base `rdfs:Class` for it (e.g. `:TrustBoundaryPillar`). Define one custom property capturing the risk, benefit, or rationale the source assigns to each framework element, with an appropriate `xsd:` range.
   b. Create explicit `schema:position`-ordered instances of that class, one per named framework element, holding the source's own description and rationale for each. Do NOT put instance data on the class definition.
   c. **Before minting any new class or property for a concept the source discusses, check whether an equivalent term already exists in a companion Knowledge Graph on a related topic.** If the source's argument responds to, cites, or is thematically continuous with a topic already modeled elsewhere (a prior thesis, a prior rebuttal, a prior glossary), reuse that term via its own namespace prefix bound to the companion document's URL — do not re-mint a document-local alias for a term that already has a canonical home. Link back to the companion document via `rdfs:seeAlso`.
4. If, and only if, the user has asked for (or the source clearly calls for) an agent-authored critical-perspective response to the thesis:
   a. Model it as a distinct `schema:CreativeWork` section, separate from the main article summary, containing one or more perspective entities.
   b. If a reusable `CriticalPerspective`-style class already exists in a companion KG from prior critical-response work, reuse it via its namespace prefix rather than minting a new local class for the same concept.
   c. Every critical-perspective entity's `schema:author` MUST be the generating skill entity (e.g. the kg-generator `schema:SoftwareApplication`/`prov:SoftwareAgent`), NEVER the human principal's WebID directly. Add `schema:accountablePerson` pointing to `{principal-webid}` to record whose perspective/accountability the commentary represents. This is agent-synthesized content, not a transcription of something the principal personally wrote — the delegation chain must say so.
   d. Reuse any external concepts the critical perspective invokes (open standards, prior companion-KG terms) via their own namespace prefix rather than re-describing them locally.
5. Identify every direct or closely paraphrased quotation the source cites and model each as a `schema:Quotation` with `schema:text` (exact wording) and `schema:citation` pointing to a `schema:CreativeWork`/`schema:ScholarlyArticle`/`schema:SocialMediaPosting` entity describing its source (author, URL, description).
6. Core entities that must be included — identify the core entities the source actually discusses and model each as an instance of the most specific applicable class: the main analysis (`:analysis`), its author and publisher, every named person and organization the source discusses, every concept the source coins or invokes, and any structural mechanism the source describes (e.g. a proposed layered architecture) as a set of `schema:position`-ordered part entities. Do not invent entities the source does not mention.
7. Mandatory structured sections (all must be present and complete — counts are a floor covering every distinct question-worthy claim/term in the source, not a fixed target):
   - schema:FAQPage (:faqSection) with **at least 12** schema:Question items (:q1, :q2, :q3, … numbered sequentially; extend as needed)
   - skos:ConceptScheme + schema:DefinedTermSet (:glossarySection) with **at least 10** terms (extend as needed) — include both document-local coined terms and reused external terms (each `schema:isPartOf :glossarySection` regardless of which namespace its subject IRI lives in)
   - schema:HowTo (:howtoSection) with schema:HowToStep items, one per framework element from item 3, if the source's framework implies a sequence of actions the reader should take; omit if the framework is descriptive/critical rather than actionable
8. Include all original details:
   - Preserve every framework element's exact description and stated rationale/risk — do not paraphrase, generalize, or compress them into a shorter summary.
   - Preserve every quotation's exact wording, attributed to its source.
   - Preserve any named prior work, economist, theory, or precedent the source explicitly invokes to ground its argument.
9. Keep descriptions concise yet precise; avoid unnecessary verbosity in literals.
10. Output **only** the complete, valid Turtle document inside a single code block. Do not include explanations, comments outside Turtle, or any other text before/after the code block.
11. The main analysis (:analysis) MUST have schema:hasPart linking to :faqSection, :glossarySection, the framework-pillars section, the critical-perspectives section (if present), and ALL other entity group sections.
12. All DBpedia references MUST use fully expanded IRIs. All Wikidata references MUST use fully expanded IRIs.
13. For every person entity: use the highest-priority platform profile URL found in the source as the primary person IRI with `#this` appended, in this order: (a) LinkedIn → (b) X/Twitter → (c) Substack → (d) Reddit → (e) other platform → (f) hash-based fallback from {post-url}. ALL discovered platform identities MUST be linked via owl:sameAs. For every organization: DBpedia → Wikidata → LinkedIn `#this` → X `#this` → homepage `#this` → hash fallback, as the primary subject IRI. NEVER fabricate names — use them exactly as they appear in the source.
14. The lightweight ontology MUST be named and described using schema:name and schema:description alongside rdfs:label/rdfs:comment, with schema:identifier carrying the canonical source URL. Every locally-minted class and property MUST have rdfs:isDefinedBy : linking it to the ontology. Reused external terms (item 3c, 4b, 4d) do NOT get a local rdfs:isDefinedBy — they keep their own provenance.
15. You MUST NOT use blank nodes for schema:Answer instances. Every schema:Answer MUST be a named entity connected via schema:acceptedAnswer :aN.
16. For every directional relationship you assert (e.g., schema:isPartOf), you MUST also assert its inverse (e.g., schema:hasPart).
17. The main analysis (:analysis) MUST include prov:wasGeneratedBy linking to a schema:SoftwareApplication entity representing the kg-generator skill, with schema:name, schema:url, and schema:description. If a critical-perspective section is present, it separately carries its own prov:wasGeneratedBy to the same skill entity per item 4c.
Current date for metadata: {current date}.

CRITICAL — Before outputting the Turtle, you MUST perform a compliance self-audit. Verify each item and report PASS or FAIL (with the violation fixed):
1. schema: namespace is http://schema.org/ (not https://schema.org/)
2. :analysis has schema:hasPart linking :faqSection, :glossarySection, the framework-pillars section, and the critical-perspectives section (if present)
3. :faqSection is a schema:FAQPage with schema:mainEntity listing at least 12 schema:Question items
4. :glossarySection is a schema:DefinedTermSet with schema:hasDefinedTerm listing at least 10 terms, including both locally-coined and reused external terms
5. All DBpedia/Wikidata IRIs are fully expanded (not CURIEs)
5a. Organization/person entities use the highest-priority canonical platform IRI as their primary subject; names match the source exactly
6. No file: scheme IRIs exist anywhere
7. Ontology has schema:name + schema:description + schema:identifier; all LOCALLY-MINTED classes/properties have rdfs:isDefinedBy : — reused external terms do not
8. No blank nodes for schema:Answer
9. Inverse relationships explicit: every schema:isPartOf has a corresponding schema:hasPart
10. prov:wasGeneratedBy links :analysis (and any critical-perspective section) to the kg-generator skill entity
11. Every critical-perspective entity's schema:author is the generating skill entity, NEVER the human principal's WebID directly; schema:accountablePerson is set to {principal-webid}
12. Before minting any new class/property, an existing companion-KG term was checked for and reused via its own prefix where one exists — no duplicate re-minting of an already-canonical term
13. Every quotation is a schema:Quotation with exact schema:text and a schema:citation to its source entity
14. owl:sameAs never has the same IRI in both subject and object positions
Report: "COMPLIANCE SELF-AUDIT: X/14 passed. [list any FAIL items, already fixed]. Output follows."

GATE: 0 FAIL required before delivery. Every numbered rule in this prompt has a corresponding check in this audit. No rule without verification — unchecked rules are aspirational, not enforceable.```

### Post-Generation Checklist

- [ ] `@prefix :` set to `{post-url}#`
- [ ] `schema:` namespace uses `http://schema.org/` (HTTP, not HTTPS)
- [ ] `:analysis schema:hasPart` links `:faqSection`, `:glossarySection`, the framework-pillars section, and the critical-perspectives section (if present)
- [ ] Lightweight ontology present: base class for the source's named framework, custom property for its per-element rationale/risk, `schema:position`-ordered instances
- [ ] Instance data on instances only — not on class definitions
- [ ] Existing companion-KG terms checked for and reused via their own namespace prefix before minting a new local term for the same concept
- [ ] If a critical-perspective section is present: `schema:author` is the generating skill entity (never the principal's WebID directly); `schema:accountablePerson` is `{principal-webid}`
- [ ] At least 12 FAQ questions wrapped in `schema:FAQPage` with `schema:mainEntity`
- [ ] Each FAQ question has `schema:isPartOf :faqSection`
- [ ] At least 10 glossary terms (local + reused external) wrapped in `schema:DefinedTermSet` with `schema:hasDefinedTerm`
- [ ] HowTo present only if the framework implies actionable steps; each step maps to a framework element
- [ ] All DBpedia/Wikidata IRIs fully expanded (not CURIEs)
- [ ] Organization/person IRIs follow the standard priority ladders; names match source exactly
- [ ] Every quotation modeled as `schema:Quotation` with exact wording and a `schema:citation` to its source
- [ ] No `file:` scheme IRIs anywhere
- [ ] All string literals carry `@en` language tags
- [ ] `prov:wasGeneratedBy` links `:analysis` to the kg-generator skill entity
- [ ] Ontology has `schema:name` + `schema:description` + `schema:identifier`; locally-minted classes/properties have `rdfs:isDefinedBy :` — reused external terms do not
- [ ] Output is the Turtle code block only — no surrounding text
- [ ] `owl:sameAs` never has the same IRI in both subject and object

---

## Template 5 — Social Media Post & Comment Thread Collection (RDF-Turtle)

Use for a single social media post (LinkedIn, X, etc.) plus its comment thread — full or a curated sampling — including interaction counters, an analytical thesis/argument restructuring of the post, and any reference links surfaced in the thread.

⛔ **PRE-BUILD CHECK**: Before producing RDF-Turtle, re-read the "Post-Generation Checklist" below and the "Compliance Self-Audit" in the prompt. Confirm: `@prefix :` (or a `post:` prefix bound to `{post-url}#`) is used consistently, `schema:` = `http://schema.org/` (HTTP), the post's `schema:text` is reproduced verbatim (not paraphrased), every comment is a `schema:Comment` with `schema:parentItem` correctly threaded and `schema:position` sequential across the whole thread, every quoted spec/code example is reproduced verbatim and marked as such, at least 12 FAQ + at least 10 glossary, person IRI priority ladder, no blank nodes for `schema:Answer`, `prov:wasGeneratedBy`, no `file:` IRIs, all string literals carry `@en` language tags. Build to pass every item — do not retro-fit.

### Placeholders

| Placeholder | Value |
|---|---|
| `{url}` | URL of the original social media post |
| `{post-url}` | Used as the Turtle `@prefix :` base (append `#`) |
| `{selected_text}` | Full extracted text of the post plus every comment to be included, in thread order |
| `{current date}` | ISO 8601 date e.g. `2026-03-13` |
| `{principal-webid}` | The human principal's canonical WebID IRI, used for `schema:author`/`schema:accountablePerson` on this curated collection document itself |

**Example — worked application of this template:** see "Example — Social Media Post & Comment Thread Worked Example" below for a full illustration of how these generic instructions apply to a real source (Tony Seale's LinkedIn post on YAML-LD and Vault-LD, with its full comment thread). That block is reference material only — do not copy its entity names or comment content into an unrelated source's output.

### Example — Social Media Post & Comment Thread Worked Example

This is a **worked illustration**, not part of the prompt the model executes. It shows how the generic instructions below resolve when applied to one specific source — Tony Seale's LinkedIn post "This week YAML-LD advanced down the W3C standards track," reproduced verbatim as `schema:text` on a `schema:SocialMediaPosting` entity, with 24 threaded comments (Kingsley Uyi Idehen's multi-part comment thread featured first, followed by a sampling of other public comments), each modeled as a `schema:Comment` with `schema:parentItem` (linking to the post or to the comment it replies to) and a thread-wide sequential `schema:position`.

Applying the "analytical restructuring" step to this source produced a `:thesisSection` (one-sentence statement of the post's core claim) and an `:argumentSection` typed as `schema:ItemList`, whose `schema:itemListElement` is a `schema:position`-ordered sequence of `schema:CreativeWork` evidence entities (the objection, the overlooked asset, the precedent, the move, the principle, the implication) — a structured restructuring of the post's own argument, not the verbatim text itself.

Applying the "verbatim example reproduction" step to this source meant reproducing the W3C YAML-LD spec's own introductory example (the Proxima Centauri b example) exactly as published, as a `schema:SoftwareSourceCode` entity with `schema:programmingLanguage "YAML"` and `rdfs:comment` explicitly noting it is reproduced verbatim from the spec, not invented — including using the spec's own real, dereferenceable DBpedia/schema.org IRIs rather than substituting placeholder `urn:` identifiers.

Applying the "reference links" step to this source meant modeling the in-thread `SeeAlso` links one commenter posted as a `:referenceLinksSection` (`schema:ItemList`), each entry a `schema:position`-ordered `schema:CreativeWork`/`schema:SoftwareApplication` entity with its own URL, author, and description — preserving them as first-class, separately citable entities rather than folding them into the comment's prose alone.

Applying interaction-counter modeling meant giving the post (and any comment with visible reactions) a `schema:interactionStatistic` pointing to one or more `schema:InteractionCounter` entities (`schema:interactionType schema:LikeAction`/`schema:CommentAction`, `schema:userInteractionCount` as an integer) — preserving the exact counts shown, not estimating them.

### Prompt

```
You are an expert in semantic web modeling, RDF/Turtle serialization, and schema.org + lightweight ontology design.
Given the social media post at {url} and its comment thread:
"""
{selected_text}
"""
produce a **comprehensive RDF/Turtle document** that represents the post and its comment thread as a knowledge graph.
Follow ALL of these final design requirements exactly:
1. Base URI: Use relative hash URIs grounded in {post-url} as the namespace prefix :
2. Use schema.org as the primary vocabulary — use http://schema.org/ (HTTP, not HTTPS) as the schema: namespace URI — supplemented by rdfs:, skos:, owl:, and prov: as needed.
3. Model the post itself as a `schema:SocialMediaPosting` with `schema:author`, `schema:datePublished`, and `schema:text` reproduced **verbatim** — do not paraphrase, summarize, or truncate the post's own wording in this field. Add `schema:headline` as a short label for the post.
4. Model every comment to be included as a `schema:Comment` with:
   - `schema:author` (the commenter's person IRI, per item 11)
   - `schema:parentItem` pointing to the post (top-level comments) or to the specific comment it is replying to (threaded replies)
   - `schema:position` as a sequential integer across the WHOLE thread in display order (not reset per branch)
   - `schema:text` reproduced verbatim
   - If a comment continues across multiple LinkedIn/X-style posted parts by the same author, model each part as its own `schema:Comment` linked back to the first part of that same author's turn via `schema:isPartOf`, in addition to `schema:parentItem` pointing to the post/parent comment.
   - `rdfs:comment` noting if the source marks the comment as edited.
5. If the post is one of several by the same author on related themes, model the author's blog/channel as a `schema:Blog` (or appropriate type) with `schema:hasPart` linking any other referenced posts by the same author, even if only briefly cited.
6. Restructure the post's own argument analytically (do not simply repeat the verbatim text): create a `:thesisSection` (a one-sentence statement of the post's core claim) and an `:argumentSection` typed `schema:ItemList`, whose `schema:itemListElement` is a `schema:position`-ordered sequence of `schema:CreativeWork` entities, one per distinct logical step in the post's argument (e.g., the objection it addresses, the evidence it offers, the precedent it cites, the move it proposes, the underlying principle, the implication).
7. If the post or thread reproduces or references a formal specification, standard, or code example verbatim, reproduce it exactly as a `schema:SoftwareSourceCode` (or appropriate type) entity, with `rdfs:comment` explicitly stating it is reproduced verbatim from its named source — never invent a substitute or simplified example when a real one is available and named in the source.
8. If a commenter posts a curated list of reference links (a "SeeAlso" or "further reading" list), model it as its own `:referenceLinksSection` (`schema:ItemList`), with each entry a `schema:position`-ordered entity carrying its own URL, name, author, and description — not folded only into the comment's prose text.
9. Model interaction statistics (likes, comment counts) wherever visibly shown in the source, via `schema:interactionStatistic` pointing to `schema:InteractionCounter` entities with `schema:interactionType` and `schema:userInteractionCount` as an integer — use the exact counts shown, never estimate.
10. Core entities that must be included: the post, every included comment, every named commenter and any person mentioned within a comment (via `schema:mentions`), any spec/standard/code example reproduced, and any reference links surfaced in the thread.
11. For every person entity: use the highest-priority platform profile URL found in the source as the primary person IRI with `#this` appended, in this order: (a) LinkedIn → (b) X/Twitter → (c) Substack → (d) Reddit → (e) other platform → (f) hash-based fallback from {post-url}. ALL discovered platform identities MUST be linked via owl:sameAs. NEVER fabricate names.
12. All DBpedia/Wikidata references MUST use fully expanded IRIs.
13. Mandatory structured sections (counts are a floor, not a fixed target):
    - schema:FAQPage (:faqSection) with **at least 12** schema:Question items, covering the post's and thread's distinct question-worthy claims
    - skos:ConceptScheme + schema:DefinedTermSet (:glossarySection) with **at least 10** terms the post/thread introduces or invokes
    - schema:HowTo (:howtoSection) with schema:HowToStep items, if the post/thread implies an actionable sequence (e.g. a migration path or adoption pattern); omit if purely descriptive
14. Keep descriptions concise yet precise; avoid unnecessary verbosity in literals not reproduced verbatim.
15. Output **only** the complete, valid Turtle document inside a single code block. Do not include explanations, comments outside Turtle, or any other text before/after the code block.
16. This curated collection document itself carries prov:wasGeneratedBy linking to the kg-generator/rdf-infographic-skill entity as applicable, with schema:author set to the generating skill and schema:accountablePerson set to {principal-webid} — never schema:author set to the principal directly for the act of curation, since the principal did not write the post or comments being collected.
17. You MUST NOT use blank nodes for schema:Answer instances. Every schema:Answer MUST be a named entity connected via schema:acceptedAnswer :aN.
18. For every directional relationship you assert (e.g., schema:isPartOf), you MUST also assert its inverse (e.g., schema:hasPart), except schema:parentItem (a comment-threading property with no required inverse).
Current date for metadata: {current date}.

CRITICAL — Before outputting the Turtle, you MUST perform a compliance self-audit. Verify each item and report PASS or FAIL (with the violation fixed):
1. schema: namespace is http://schema.org/ (not https://schema.org/)
2. The post's schema:text is reproduced verbatim, not paraphrased or truncated
3. Every comment is a schema:Comment with schema:parentItem correctly threaded and a sequential schema:position across the whole thread
4. Any reproduced spec/code example is verbatim and marked as such via rdfs:comment
5. :faqSection is a schema:FAQPage with schema:mainEntity listing at least 12 schema:Question items
6. :glossarySection is a schema:DefinedTermSet with schema:hasDefinedTerm listing at least 10 terms
7. All DBpedia/Wikidata IRIs are fully expanded (not CURIEs)
8. No file: scheme IRIs exist anywhere
9. No blank nodes for schema:Answer
10. Inverse relationships explicit except schema:parentItem
11. prov:wasGeneratedBy present; schema:author on the collection document is the generating skill, schema:accountablePerson is {principal-webid} — never schema:author set to the principal for content the principal did not author
12. Interaction counters use exact shown counts, modeled via schema:InteractionCounter
13. owl:sameAs never has the same IRI in both subject and object positions
Report: "COMPLIANCE SELF-AUDIT: X/13 passed. [list any FAIL items, already fixed]. Output follows."

GATE: 0 FAIL required before delivery. Every numbered rule in this prompt has a corresponding check in this audit. No rule without verification — unchecked rules are aspirational, not enforceable.```

### Post-Generation Checklist

- [ ] `@prefix :` set to `{post-url}#`
- [ ] `schema:` namespace uses `http://schema.org/` (HTTP, not HTTPS)
- [ ] Post modeled as `schema:SocialMediaPosting` with `schema:text` reproduced verbatim
- [ ] Every comment is `schema:Comment` with correct `schema:parentItem` threading and a sequential `schema:position` across the whole thread
- [ ] Multi-part same-author comment turns linked via `schema:isPartOf` in addition to `schema:parentItem`
- [ ] Edited comments flagged via `rdfs:comment`
- [ ] `:thesisSection` and `:argumentSection` (ItemList) present as an analytical restructuring, not a repeat of verbatim text
- [ ] Any reproduced spec/code example is verbatim and explicitly marked as such
- [ ] Any in-thread reference-link list modeled as its own `:referenceLinksSection` (ItemList) with position-ordered entries
- [ ] Interaction counters modeled via `schema:InteractionCounter` with exact shown counts
- [ ] At least 12 FAQ questions wrapped in `schema:FAQPage` with `schema:mainEntity`
- [ ] At least 10 glossary terms wrapped in `schema:DefinedTermSet` with `schema:hasDefinedTerm`
- [ ] HowTo present only if the post/thread implies an actionable sequence
- [ ] All DBpedia/Wikidata IRIs fully expanded (not CURIEs)
- [ ] Person IRIs follow the standard priority ladder; names match source exactly; all platform identities linked via `owl:sameAs`
- [ ] No `file:` scheme IRIs anywhere
- [ ] All string literals (other than verbatim reproductions) carry `@en` language tags
- [ ] `prov:wasGeneratedBy` present; `schema:author` on the collection is the generating skill, `schema:accountablePerson` is `{principal-webid}`
- [ ] Output is the Turtle code block only — no surrounding text
- [ ] `owl:sameAs` never has the same IRI in both subject and object

---

## Template 6 — News Article with Agent-Authored Framework Commentary (RDF-Turtle)

Use for third-party news/magazine articles (a `schema:NewsArticle` from an identifiable publisher), optionally extended with an agent-authored analytical section that applies a named external framework (e.g., a book's thesis) as critical commentary on the article's claims — added only when the user requests that lens, kept clearly delegated and separate from the article's own reported content.

⛔ **PRE-BUILD CHECK**: Before producing RDF-Turtle, re-read the "Post-Generation Checklist" below and the "Compliance Self-Audit" in the prompt. Confirm: `@prefix :` = `{post-url}#`, `schema:` = `http://schema.org/` (HTTP), the article is `schema:NewsArticle` with publisher/author/dates faithfully captured, every direct quotation attributed to its named speaker, related/companion coverage linked as separate `schema:NewsArticle` entities (not just bare URLs), any agent-authored framework-commentary section has `schema:author` set to the generating skill (never the principal directly) with `schema:accountablePerson` on the principal, at least 12 FAQ + at least 10 glossary + HowTo if the article supports actionable takeaways, no blank nodes for `schema:Answer`, `prov:wasGeneratedBy`, no `file:` IRIs, all string literals carry `@en` language tags. Build to pass every item — do not retro-fit.

### Placeholders

| Placeholder | Value |
|---|---|
| `{url}` | URL of the original news/magazine article |
| `{post-url}` | Used as the Turtle `@prefix :` base (append `#`) |
| `{selected_text}` | Full extracted text of the article |
| `{current date}` | ISO 8601 date e.g. `2026-03-13` |
| `{framework-name}` | Optional — name of the external framework/book to apply as commentary, only if the user requests this lens |
| `{principal-webid}` | The human principal's canonical WebID IRI, used for `schema:accountablePerson` on any agent-authored commentary section |

**Example — worked application of this template:** see "Example — News Article with Framework Commentary Worked Example" below for a full illustration of how these generic instructions apply to a real source (The Atlantic's "Generative AI Is an Engineering Disaster," with an added Blitzscaling-framework commentary lens). That block is reference material only — do not copy its entity names or figures into an unrelated source's output.

### Example — News Article with Framework Commentary Worked Example

This is a **worked illustration**, not part of the prompt the model executes. It shows how the generic instructions below resolve when applied to one specific source — The Atlantic's "Generative AI Is an Engineering Disaster," a `schema:NewsArticle` by staff writer Alex Reisner arguing that generative AI's quadratic (not merely large-scale) resource growth is driving a memory shortage and price spikes, part of The Atlantic's "AI Watchdog" `schema:CreativeWorkSeries`.

Applying the "core article modeling" step to this source produced content sections for cost/scarcity, the scaling problem, industry efficiency claims, market saturation, and expert quotes — each a `schema:CreativeWork` with `schema:abstract`, linked from the main article via `schema:hasPart` — plus a `:relatedCoverageSection` modeling each companion Atlantic article as its own `schema:NewsArticle` entity (headline, URL, publisher), not a bare `schema:relatedLink` string.

Applying the "agent-authored framework commentary" step to this source — added because the user explicitly asked for a Blitzscaling-framework lens on the article — produced a distinct `:blitzscalingSection`, containing four `schema:CreativeWork` argument entities (the brute-force bet as a blitzscaling choice, externalized cost, inverted marginal-cost returns, bubble-economy risk) that connect the article's own reported facts and quotations (via `schema:mentions`/`schema:about`) to concepts from Reid Hoffman and Chris Yeh's book "Blitzscaling" (modeled as a `schema:Book` with `schema:isbn`). Critically, `:blitzscalingSection`'s `schema:author` is the kg-generator skill entity, with `schema:accountablePerson` on the principal's WebID and its own `prov:wasGeneratedBy` — kept structurally distinct from the article's own `schema:author` (Alex Reisner) so the commentary is never misattributed as something the article's actual author wrote or endorsed.

Applying the "verbatim quotations" step to this source meant modeling each expert quote (Sam Altman, Ilya Sutskever, Alexia Jolicoeur-Martineau, Yann LeCun) as its own `schema:CreativeWork` with exact `schema:text` and `schema:author`, grouped under an `:expertVoicesSection`.

### Prompt

```
You are an expert in semantic web modeling, RDF/Turtle serialization, and schema.org + lightweight ontology design.
Given the news/magazine article at {url}:
"""
{selected_text}
"""
produce a **comprehensive RDF/Turtle document** that represents the article as a knowledge graph.
Follow ALL of these final design requirements exactly:
1. Base URI: Use relative hash URIs grounded in {post-url} as the namespace prefix :
2. Use schema.org as the primary vocabulary — use http://schema.org/ (HTTP, not HTTPS) as the schema: namespace URI — supplemented by rdfs:, skos:, owl:, and prov: as needed.
3. Model the article as a `schema:NewsArticle` with `schema:headline`, `schema:abstract`, `schema:datePublished`/`schema:dateModified`, `schema:author` (the byline), `schema:publisher`, and `schema:url`/`schema:mainEntityOfPage`. If the article belongs to a named ongoing series/column, model that series as a `schema:CreativeWorkSeries` with `schema:hasPart` linking the article.
4. Identify the article's own section structure (however the source itself organizes its argument — by topic, by claim, by chronology) and represent each as a `schema:CreativeWork` with `schema:abstract`, linked from the main article via `schema:hasPart`.
5. Model every direct quotation from a named speaker as its own `schema:CreativeWork` (or `schema:Quotation`) with exact `schema:text` and `schema:author`, grouped under an expert-voices or quotations section if the article features multiple.
6. If the article links to companion/related coverage (its own outlet's other articles on the same or adjacent topics), model each as its own `schema:NewsArticle` entity with `schema:headline` and `schema:url` — do not reduce them to bare `schema:relatedLink` URL strings when the article names them.
7. If, and only if, the user has explicitly requested applying a named external framework (`{framework-name}`) as a commentary lens on the article:
   a. Model it as a distinct `schema:CreativeWork` section, structurally separate from the article's own reported sections.
   b. Model the framework's source (e.g. a book) as its own entity (`schema:Book` with `schema:isbn` if applicable, or the appropriate type) with its author(s).
   c. Create one commentary entity per distinct point the framework-lens analysis makes, each connecting specific facts/quotations already modeled elsewhere in the graph (via `schema:mentions`/`schema:about`) to a concept from the framework — do not simply restate the article's own claims under a new heading.
   d. This section's `schema:author` MUST be the generating skill entity, NEVER the article's own byline and NEVER the human principal's WebID directly — it is agent-synthesized commentary, not part of the article and not something the principal personally wrote. Add `schema:accountablePerson` set to `{principal-webid}` and give the section its own `prov:wasGeneratedBy`.
   e. Do not add a framework-commentary section unless requested — an unrequested critical lens misrepresents a third-party news article's own reported content.
8. Core entities that must be included: the article, its author and publisher, every named person quoted or discussed, every named organization discussed, any companion/related coverage, and (only if requested) the framework-commentary section and the framework's source work.
9. For every person entity: use the highest-priority platform profile URL found in the source as the primary person IRI with `#this` appended, in this order: (a) LinkedIn → (b) X/Twitter → (c) Substack → (d) Reddit → (e) other platform → (f) hash-based fallback from {post-url}. For the article's own byline, also add `schema:identifier` pointing to the outlet's own author-bio page if named in the source. ALL discovered platform identities MUST be linked via owl:sameAs. NEVER fabricate names.
10. All DBpedia/Wikidata references MUST use fully expanded IRIs.
11. Mandatory structured sections (counts are a floor, not a fixed target):
    - schema:FAQPage (:faqSection) with **at least 12** schema:Question items covering every distinct question-worthy claim in the article
    - skos:ConceptScheme + schema:DefinedTermSet (:glossarySection) with **at least 10** terms the article introduces or relies on
    - schema:HowTo (:howtoSection) with schema:HowToStep items, if the article supports actionable reader takeaways (e.g. how to evaluate a claim it discusses); omit if purely descriptive reporting with no actionable angle
12. Keep descriptions concise yet precise; avoid unnecessary verbosity in literals.
13. Output **only** the complete, valid Turtle document inside a single code block. Do not include explanations, comments outside Turtle, or any other text before/after the code block.
14. The main article MUST have schema:hasPart linking to every content section, :faqSection, :glossarySection, and the framework-commentary section if present.
15. The article itself carries prov:wasGeneratedBy linking to the kg-generator skill entity, with schema:name, schema:url, and schema:description. A framework-commentary section (if present) carries its own prov:wasGeneratedBy per item 7d.
16. You MUST NOT use blank nodes for schema:Answer instances. Every schema:Answer MUST be a named entity connected via schema:acceptedAnswer :aN.
17. For every directional relationship you assert (e.g., schema:isPartOf), you MUST also assert its inverse (e.g., schema:hasPart).
Current date for metadata: {current date}.

CRITICAL — Before outputting the Turtle, you MUST perform a compliance self-audit. Verify each item and report PASS or FAIL (with the violation fixed):
1. schema: namespace is http://schema.org/ (not https://schema.org/)
2. Article is schema:NewsArticle with publisher, byline author, and dates captured; series membership modeled if applicable
3. The main article has schema:hasPart linking every content section, :faqSection, :glossarySection, and the framework-commentary section if present
4. Every direct quotation is attributed to its named speaker with exact wording
5. Companion/related coverage modeled as distinct schema:NewsArticle entities, not bare relatedLink strings, where the source names them
6. :faqSection is a schema:FAQPage with schema:mainEntity listing at least 12 schema:Question items
7. :glossarySection is a schema:DefinedTermSet with schema:hasDefinedTerm listing at least 10 terms
8. All DBpedia/Wikidata IRIs are fully expanded (not CURIEs)
9. No file: scheme IRIs exist anywhere
10. If present, the framework-commentary section's schema:author is the generating skill entity — NEVER the article's byline and NEVER the principal's WebID directly; schema:accountablePerson is {principal-webid}; it was added only because explicitly requested
11. No blank nodes for schema:Answer
12. Inverse relationships explicit: every schema:isPartOf has a corresponding schema:hasPart
13. prov:wasGeneratedBy present on the article and on the framework-commentary section (if present)
14. owl:sameAs never has the same IRI in both subject and object positions
Report: "COMPLIANCE SELF-AUDIT: X/14 passed. [list any FAIL items, already fixed]. Output follows."

GATE: 0 FAIL required before delivery. Every numbered rule in this prompt has a corresponding check in this audit. No rule without verification — unchecked rules are aspirational, not enforceable.```

### Post-Generation Checklist

- [ ] `@prefix :` set to `{post-url}#`
- [ ] `schema:` namespace uses `http://schema.org/` (HTTP, not HTTPS)
- [ ] Article modeled as `schema:NewsArticle` with publisher, byline, dates; series modeled as `schema:CreativeWorkSeries` if applicable
- [ ] Article's own section structure represented as `schema:hasPart`-linked `schema:CreativeWork` entities with `schema:abstract`
- [ ] Every direct quotation modeled with exact wording and attributed author
- [ ] Companion/related coverage modeled as distinct `schema:NewsArticle` entities where named in the source
- [ ] Framework-commentary section present ONLY if explicitly requested; structurally separate from the article's own sections
- [ ] If present: framework-commentary `schema:author` is the generating skill entity (never the article's byline, never the principal directly); `schema:accountablePerson` is `{principal-webid}`; framework's source work (e.g. book) modeled as its own entity
- [ ] At least 12 FAQ questions wrapped in `schema:FAQPage` with `schema:mainEntity`
- [ ] At least 10 glossary terms wrapped in `schema:DefinedTermSet` with `schema:hasDefinedTerm`
- [ ] HowTo present only if the article supports actionable reader takeaways
- [ ] All DBpedia/Wikidata IRIs fully expanded (not CURIEs)
- [ ] Person/organization IRIs follow the standard priority ladders; names match source exactly
- [ ] No `file:` scheme IRIs anywhere
- [ ] All string literals carry `@en` language tags
- [ ] `prov:wasGeneratedBy` present on the article and on the framework-commentary section (if present)
- [ ] Output is the Turtle code block only — no surrounding text
- [ ] `owl:sameAs` never has the same IRI in both subject and object

---

## HTML Infographic Companion Requirements

When the user asks for an HTML infographic companion to a generated Knowledge Graph, invoke the `rdf-infographic-skill` **RDF Infographic Harness Mode** requirements.

⛔ **PRE-BUILD CHECK**: Before generating HTML, load `rdf-infographic-skill` and re-read the "Harness Contract" (13-point checklist) and "Validation Checklist." Confirm: shared stem, resolver-backed entity links, POSH + JSON-LD pairing, floating nav (collapsed by default), theme toggle, KG Explorer (Basic + Advanced), attribution footer, MD parity, authority denotation rules (SoftwareApplication, Country), 0-failure delivery gate. Every item is a build target, not a post-delivery check. For the complete HTML/RDF/Markdown pairing specification including resolver configuration, KG Explorer behavior, navigation panel behavior, localStorage correctness, attribution, dark mode, and the full validation checklist, see the `rdf-infographic-skill` SKILL.md.

### Output Paths

- Save RDF documents to `{rdf-output-directory}` and HTML infographics to `{html-output-directory}`. Resolve from explicit user instructions or session defaults.
- Confirm resolved full file paths before saving.

### Entity IRIs and Resolver Links

- Use `{page_url}` or `{post-url}` as the source-grounded namespace. Never use `file:` scheme IRIs when a canonical HTTPS URL exists.
- Resolver priority: URIBurner (`https://linkeddata.uriburner.com/describe/?url={entity-iri}`) by default; user-designated resolver if specified; or none if user explicitly opts out.
- Encode `#` as `%23` exactly once in resolver `url` parameters. `%2523` (double-encoded) is invalid.
- Entity links open in new tabs: `target="_blank" rel="noopener noreferrer"`.
- FAQ questions, FAQ answers, glossary terms, glossary definitions, HowTo section title, and every HowTo step heading are ALL hyperlinked to their KG entity IRIs.
- Visible semantic entities route through the configured resolver using their selected RDF IRIs, including DBpedia/Wikidata IRIs selected under the SoftwareApplication denotation rule.

### POSH and JSON-LD Metadata

- POSH link: `<link rel="related" href="../rdf/{rdf-file}" type="text/turtle">`
- JSON-LD `relatedLink` must use IRI form: `{"@id": "../rdf/{rdf-file}"}` — never a plain string literal.
- `prov:wasGeneratedBy` must reference a `schema:SoftwareApplication` entity per skill.
- Attributions in footer must include: AI Agent (OpenCode), each Skill used, LLM used, Server Platform (Virtuoso)

```html
<!-- Premium footer with 4-column grid design -->
<footer class="footer">
<p style="margin-bottom:20px"><a href="https://linkeddata.uriburner.com/sparql?query=..." target="_blank" rel="noopener noreferrer" class="cta-btn" style="display:inline-flex;align-items:center;gap:8px;padding:12px 24px;background:var(--accent);color:#fff;border-radius:12px;text-decoration:none;font-weight:600;font-size:0.95rem">Explore Knowledge Graph <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M9.5 3.5a1.5 1.5 0 0 1 0 3h-5l-.5.5 1 1a1 1 0 0 0 1.414 1.414l-2-2a1 1 0 0 0 0-1.414l-2-2a1 1 0 0 0-1.414 1.414l1 1-.5.5h5z"/></svg></a></p>
<div class="tech-grid" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:24px;border-top:1px solid var(--line);padding-top:24px">
<div class="tech-card" style="text-align:center;padding:16px;background:var(--panel);border-radius:12px;border:1px solid var(--line)">
<h4 style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:8px">AI Agent</h4>
<a href="https://opencode.ai" target="_blank" rel="noopener noreferrer" style="color:var(--accent);font-family:'Space Grotesk';font-weight:600;font-size:0.95rem;text-decoration:none">OpenCode</a>
</div>
<div class="tech-card" style="text-align:center;padding:16px;background:var(--panel);border-radius:12px;border:1px solid var(--line)">
<h4 style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:8px">AI Agent Skills</h4>
<div style="font-size:0.8rem"><a href="https://github.com/anomalyco/opencode/tree/main/skill-name" target="_blank" rel="noopener noreferrer" style="color:var(--accent);text-decoration:none">skill-name</a></div>
</div>
<div class="tech-card" style="text-align:center;padding:16px;background:var(--panel);border-radius:12px;border:1px solid var(--line)">
<h4 style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:8px">Language Model</h4>
<a href="https://opencode.ai/models/minimax_m2.5free" target="_blank" rel="noopener noreferrer" style="color:var(--accent);font-family:'Space Grotesk';font-weight:600;font-size:0.95rem;text-decoration:none">minimax_m2.5free</a>
</div>
<div class="tech-card" style="text-align:center;padding:16px;background:var(--panel);border-radius:12px;border:1px solid var(--line)">
<h4 style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:8px">Server Platform</h4>
<a href="https://virtuoso.openlinksw.com/" target="_blank" rel="noopener noreferrer" style="color:var(--accent);font-family:'Space Grotesk';font-weight:600;font-size:0.95rem;text-decoration:none">Virtuoso</a>
</div>
</div>
</footer>
```

For HTML dashboards from SPARQL named graph queries, also include "Explore Knowledge Graph" link.

### About Section Template

Every HTML infographic generated from a named graph should include an About section explaining how the page was created. Use this template:

```html
<section class="section" id="about">
<div class="eyebrow-dark">About</div>
<div class="section-title"><h2>About This Page</h2></div>
<p style="color:var(--muted);line-height:1.7">This knowledge graph overview was generated by querying the <a href="https://linkeddata.uriburner.com/sparql" target="_blank" rel="noopener noreferrer" style="color:var(--accent)">URIBurner SPARQL endpoint</a> for the named graph <code>{graph-iri}</code>. The original document was transformed into RDF using {skills-used}, then uploaded to the Virtuoso-based URIBurner server. The SPARQL query retrieved {entity-types} from the knowledge graph. The HTML infographic was then rendered using {skills-used} powered by {model-id} and running on Virtuoso.</p>
<p style="margin-top:16px;font-size:0.85rem;color:var(--ink)"><strong>Technology Stack:</strong></p>
<ul style="margin-top:8px;font-size:0.85rem;color:var(--ink);list-style:disc;padding-left:20px">
<li>AI Agent: <a href="https://opencode.ai" target="_blank" rel="noopener noreferrer" style="color:var(--accent)">OpenCode</a></li>
<li>Skills: <a href="https://github.com/anomalyco/opencode/tree/main/skill-name" target="_blank" rel="noopener noreferrer" style="color:var(--accent)">skill-name</a></li>
<li>Language Model: <a href="https://opencode.ai/models/{model-id}" target="_blank" rel="noopener noreferrer" style="color:var(--accent)">{model-id}</a></li>
<li>Server Platform: <a href="https://virtuoso.openlinksw.com/" target="_blank" rel="noopener noreferrer" style="color:var(--accent)">Virtuoso</a></li>
<li>Knowledge Graph: <a href="https://linkeddata.uriburner.com/sparql" target="_blank" rel="noopener noreferrer" style="color:var(--accent)">URIBurner</a></li>
</ul>
</section>
```

Substitute: `{graph-iri}`, `{skills-used}`, `{entity-types}`, `{skill-links}`, and `{model-id}` with actual values.

### Navigation, Theme, and Validation

- Collapse-to-header-bar floating navigation: always-visible compact header, toggle, draggable, resizable.
- Never persist collapsed dimensions in `localStorage`. Recover from stale state. Page-specific keys.
- Dark mode: `html[data-theme="dark"]` and `@media (prefers-color-scheme: dark)` produce equivalent rendering. All colors via CSS variables.
- **Responsive head-to-head comparisons** — when the HTML companion includes a multi-entity comparison matrix (≥2 named products/platforms/systems as columns), dual-present per `rdf-infographic-skill`: table for viewports ≥901px, product cards for ≤900px (CSS-only). Every comparison aspect MUST be a TTL **instance** (name+description) typed via ontology class reuse first (shared vocab or corpus-canonical e.g. `cdx:ComparisonDimension`); mint a new class only under a distinct `owl:Ontology` when no shared/corpus term fits. First column of each table row (and card labels) MUST resolver-link to the aspect **instance** IRI. Do not ship phone-only horizontal-scroll matrices. Canonical template: `rdf-infographic-skill/assets/templates/competitive-analysis-head-to-head-claude_sonnet_4_6.html`. Prefs fallback: `agent-rdf-memory/preferences.ttl#step-responsiveComparisonPresentation`.
- **GATE: 0 failures required.** Validate: HTML parse, JS syntax, RDF parse + compliance audit, resolver links, local RDF link, nav behavior, skills attribution, dark mode consistency, and responsive dual comparison presentation when a multi-column matrix is present.

---

## MD Document Companion Requirements

When generating a Markdown document alongside RDF and HTML outputs, the MD **MUST** follow these requirements:

⛔ **PRE-BUILD CHECK**: Before writing MD, re-read the "Checklist" at the end of this section. Confirm: all entity names/property names in relationships section resolver-hyperlinked, FAQ questions resolver-hyperlinked, glossary terms resolver-hyperlinked, HowTo step titles resolver-hyperlinked, Related Resources includes relative links to companion RDF and HTML, no plain-text code blocks for relationships. Build to pass every item.

### Structure

- **Title + metadata block** — author, date, source URL, reading time (if available).
- **Overview** — 2–3 sentence summary of what the document covers.
- **Core content sections** — entities, concepts, principles, relationships, statistics — organized with H2/H3 headings.
- **How-To guide** — when the RDF includes `schema:HowTo`, render all steps as a numbered list with step titles and descriptions.
- **FAQ** — when the RDF includes `schema:FAQPage`, render all Q&A pairs. Each question hyperlinks to its KG entity IRI via the URIBurner resolver.
- **Glossary** — when the RDF includes `schema:DefinedTermSet`, render all terms with definitions. Each term name hyperlinks to its KG entity IRI via the resolver.
- **Related Resources** — links to the original source, companion RDF file, and companion HTML file (all relative paths).

### Entity Hyperlinks

Every entity reference in the MD (classes, properties, instances, concepts, persons, organizations) **MUST** be hyperlinked using the URIBurner resolver pattern:

```
[Entity Label](https://linkeddata.uriburner.com/describe/?url={URL-encoded-IRI})
```

This applies to:
- **Relationships section** — every entity and property name in relationship descriptions must be a resolver link.
- **Entity tables** — entity names in table cells must be resolver links.
- **Glossary** — each term name must be a resolver link.
- **FAQ** — each question must be a resolver link.
- **How-To steps** — each step title must be a resolver link.

### Relationships Section

The MD **MUST** include a relationships section that:
- Names every relationship (object property) linking domain entities.
- Hyperlinks both the source entity, the property, and the target entity using resolver links.
- Organizes relationships from the central/coordinating entity outward (e.g., Trip as the dispatch hub).
- Uses bulleted or indented lists for visual hierarchy — not plain-text code blocks.

### Checklist

- [ ] All entity names in the relationships section are resolver-hyperlinked.
- [ ] All property names in the relationships section are resolver-hyperlinked.
- [ ] FAQ questions are resolver-hyperlinked.
- [ ] Glossary terms are resolver-hyperlinked.
- [ ] How-To step titles are resolver-hyperlinked.
- [ ] Related Resources section includes relative links to companion RDF and HTML files.
- [ ] No plain-text code blocks used for relationship descriptions that should be hyperlinked.
- [ ] **"Explore Knowledge Graph using SPARQL" CTA link** present at the top of the Related Resources section, using a SPARQL query with an explicit `FROM <{graph-iri}>` clause scoped to the named graph IRI derived from the DAV upload location (`https://linkeddata.uriburner.com/DAV/demos/daas/{filename}.ttl`). The query must use `SELECT DISTINCT ?subject ?type (SAMPLE(?label) AS ?name) … GROUP BY ?subject ?type ORDER BY ?type LIMIT 50` — no `default-graph-uri=` URL parameter, no `FILTER(STRSTARTS(...))` workaround.

---

## Saving Output Files

- **Turtle**: `{descriptive-slug}-{model-id}.ttl` (increment if file exists)
- **JSON-LD**: `{descriptive-slug}-{model-id}.jsonld` (increment if file exists)
- **Default save location**: `{output-directory}` — ask the user if not specified, or infer from context
- Override if user specifies a path
- Replace `-` with `_` in `{model-id}` for filesystem safety (e.g., `minimax_m2.5free`)

### Ontology Identifier Selection Rules

When generating RDF from documents, use these priority rules for entity types:

1. **Use schema.org first** — If `schema.org/{Type}` exists (e.g., `schema:Person`, `schema:Organization`), use it.
2. **Check shared ontologies** — Use well-known RDF vocabularies (e.g., `Dublin Core (dc:)`, `SKOS`, `FOAF`, `PROV`, `schema.org/` alternate terms). Do NOT assume a term exists without verification.
3. **Create on-the-fly** — If neither schema.org nor a shared ontology has the needed type:
   - Create a namespace IRI using the document base (e.g., `https://linkeddata.uriburner.com/DAV/docs-for-knowledge-graph-and-embeddings-generation/UB-PDFs/ontology#`)
   - Define the new class/property in the output with proper `rdfs:comment` for documentation.
   - Include the ontology IRI in the generated RDF's `@prefix` declarations.

**Example:**
```turtle
@prefix somt: <https://linkeddata.uriburner.com/DAV/docs-for-knowledge-graph-and-embeddings-generation/UB-PDFs/ontology#> .

somt:Interview a rdfs:Class ;
    rdfs:label "Interview" ;
    rdfs:comment "An interview or conversation with a person, typically in a professional context." ;
    rdfs:isDefinedBy somt: .
```

Do NOT use non-existent schema.org terms like `schema:Interview` — this causes errors and breaks SPARQL queries.

The output filenames SHOULD include a lowercase, filesystem-safe version of the underlying LLM model identifier to enable provenance tracking. Extract the model ID from the environment or task context:

| Model Source | Example ID |
|---|---|
| minimax | `minimax_m2.5free` |
| openai | `openai_gpt4o` |
| anthropic | `anthropic_sonnet4` |
| google | `google_gemini2` |
| claudeCode | `claude_code` |
| Other | `{provider}_{model}` (lowercase, underscores, no spaces) |

Example output:
- `anthropic-platform-strategy-minimax_m2.5free-1.ttl`
- `azure-accelerate-databases-minimax_m2.5free-1.html`
- `substack-deep-dive-openai_gpt4o-1.jsonld`

---

## Dual-Format RDF Generation (TTL + JSON-LD)

When generating a Knowledge Graph collection, produce **both** RDF Turtle and JSON-LD formats by default. This enables the HTML infographic companion to provide a format toggle in the footer SPARQL button.

### Generation Workflow

1. **Generate Turtle first** — Use the selected template (Generic or Business & Market Analysis) to produce the primary `.ttl` file.
2. **Convert to JSON-LD** — Use `rdflib` to parse the Turtle and serialize as JSON-LD:
   ```python
   import rdflib
   g = rdflib.Graph()
   g.parse('output.ttl', format='turtle')
   g.serialize('output.jsonld', format='json-ld', indent=2)
   ```
3. **Verify both files** — Ensure syntactic validity for each format before delivering.

### Output Files

Both formats use the same slug and version:

| Format | Filename | Purpose |
|--------|----------|---------|
| Turtle | `{slug}-{model-id}-{n}.ttl` | Primary RDF (schema.org-friendly) |
| JSON-LD | `{slug}-{model-id}-{n}.jsonld` | Alternate RDF (JSON-native) |

Both files share the same base namespace (`@prefix : <{source-url}#>`) and entity IRIs.

---

## HTML Infographic Footer — SPARQL Button with Format Toggle

The footer of every HTML infographic **MUST** include a SPARQL button that lets users query the knowledge graph via URIBurner. Include format toggle tabs so users can select which RDF document to query.

⛔ **PRE-BUILD CHECK**: Before writing the footer HTML/JS, re-read this section's "Required HTML Structure," "Required CSS," and "Required JavaScript." Confirm: format toggle tabs (Turtle/JSON-LD), `setSparqlFormat()` function, GRAPH IRI uses `DAV/demos/daas/{filename}` (not source URL), query URL uses `encodeURIComponent`, `#sparqlBtn` href updates on toggle.

### Required HTML Structure

```html
<footer>
    <div class="kg-format-tabs">
        <button class="active" id="fmtTtl" onclick="setSparqlFormat('ttl')">RDF Turtle</button>
        <button id="fmtJsonld" onclick="setSparqlFormat('jsonld')">JSON-LD</button>
    </div>
    <p style="margin-bottom:20px">
        <a id="sparqlBtn" href="..." target="_blank" rel="noopener noreferrer">Explore Knowledge Graph using SPARQL</a>
    </p>
</footer>
```

### Required CSS

```css
.kg-format-tabs { display: flex; gap: 8px; margin-bottom: 12px; }
.kg-format-tabs button { background: var(--bg); border: 1px solid var(--line); border-radius: 6px; padding: 6px 14px; cursor: pointer; font-size: 0.8rem; font-weight: 500; }
.kg-format-tabs button.active { background: var(--accent); color: white; border-color: var(--accent); }
```

### Required JavaScript

```javascript
function setSparqlFormat(fmt) {
    document.getElementById('fmtTtl').classList.toggle('active', fmt === 'ttl');
    document.getElementById('fmtJsonld').classList.toggle('active', fmt === 'jsonld');
    const ext = fmt === 'jsonld' ? 'jsonld' : 'ttl';
    const slug = '{descriptive-slug}-{model-id}-{n}';
    const graphIri = 'https://linkeddata.uriburner.com/DAV/demos/daas/' + slug + '.' + ext;
    const query = 'PREFIX+rdf%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23%3E%0APREFIX+rdfs%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F2000%2F01%2Frdf-schema%23%3E%0A%0ASELECT%0A++++%3Ftype%0A++++%28SAMPLE%28%3Fs%29+AS+%3FsampleEntity%29%0A++++%28SAMPLE%28%3Flabel%29+AS+%3FsampleLabel%29%0A++++%28COUNT%28%3Fs%29+AS+%3FentityCount%29%0AWHERE+%7B%0A++++GRAPH+%3C' + encodeURIComponent(graphIri) + '%3E+%7B%0A++++++++%3Fs+rdf%3Atype+%3Ftype+.%0A%0A++++++++OPTIONAL+%7B%0A++++++++++++%3Fs+rdfs%3Alabel+%3Flabel%0A++++++++%7D%0A++++%7D%0A%7D%0AGROUP+BY+%3Ftype%0AORDER+BY+DESC%28%3FentityCount%29';
    document.getElementById('sparqlBtn').href = 'https://linkeddata.uriburner.com/sparql?query=' + query;
}
```

Substitute `{descriptive-slug}-{model-id}-{n}` with the actual output filename (without extension).

---

## Document IRI vs SPARQL GRAPH IRI

**Critical distinction:**

| IRI Type | Used For | Pattern |
|----------|----------|---------|
| **Document IRI** | Entity references in RDF, HTML, MD | `{source-url}#{entity}` |
| **SPARQL GRAPH IRI** | Querying the named graph in URIBurner | `https://linkeddata.uriburner.com/DAV/demos/daas/{filename}` |

### Document IRI (Entity References)

Use the source URL with `#` suffix as the `@prefix :` base in Turtle files:

```turtle
@prefix : <https://pluralistic.net/2026/05/13/vibe-governance#> .
```

Entities become `:q1`, `:step1`, `:billionaireSolipsism`, etc., resolving to:
- `https://pluralistic.net/2026/05/13/vibe-governance#q1`
- `https://pluralistic.net/2026/05/13/vibe-governance#step1`

HTML/MD resolver links use: `https://linkeddata.uriburner.com/describe/?url={entity-iri}`

### SPARQL GRAPH IRI (Query Target)

The GRAPH clause in SPARQL queries uses the **DAV path** to the generated RDF file:

```
GRAPH <https://linkeddata.uriburner.com/DAV/demos/daas/vibe-governance-minimax_m2.5free-1.ttl>
```

This is **different from** the document IRI. The GRAPH IRI points to the uploaded RDF file in URIBurner's DAV repository, not the original source URL.

### Why the Distinction?

- **Document IRIs** maintain the provenance of the original source — useful for linking back to original content.
- **SPARQL GRAPH IRIs** reference the actual RDF quad store location in URIBurner, enabling queries against the uploaded graph.

**Never confuse the two.** The HTML footer SPARQL button uses GRAPH IRIs; entity resolver links in HTML/MD use Document IRIs.

---

## IRI Patterns Quick Reference

| Context | IRI Pattern | Example |
|---------|------------|---------|
| TTL `@prefix :` | `{source-url}#` | `https://pluralistic.net/2026/05/13/vibe-governance#` |
| TTL entity | `:{name}` → `{source-url}#{name}` | `:q1` → `https://pluralistic.net/2026/05/13/vibe-governance#q1` |
| HTML/MD resolver link | `https://linkeddata.uriburner.com/describe/?url={entity-iri}` | `https://linkeddata.uriburner.com/describe/?url=https://pluralistic.net/2026/05/13/vibe-governance#q1` |
| SPARQL GRAPH clause | `https://linkeddata.uriburner.com/DAV/demos/daas/{filename}` | `https://linkeddata.uriburner.com/DAV/demos/daas/vibe-governance-minimax_m2.5free-1.ttl` |
| JSON-LD `@base` | `{source-url}/` | `https://pluralistic.net/2026/05/13/vibe-governance/` |

This convention allows tracking which AI model generated each artifact without requiring external metadata.
