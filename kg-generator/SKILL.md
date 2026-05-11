---
name: kg-generator
description: "Generate comprehensive Knowledge Graphs (RDF-Turtle by default, or JSON-LD and other RDF serializations on request) from content at file: or http(s): scheme URLs. Uses curated prompt templates: a Generic template for general web content (producing JSON-LD), and a Business and Market Analysis template for strategy/analysis content (producing RDF-Turtle with NAICS industry code identifiers, lightweight ontology, FAQ, glossary, and HowTo sections). Trigger when users ask to: generate a knowledge graph, generate RDF or RDF-Turtle, generate JSON-LD, convert a URL to structured semantic data, or extract schema.org data from a page or document."
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

## Template Selection

| Content type | Template | Default output |
|---|---|---|
| General articles, blog posts, documentation | Generic | JSON-LD |
| Business strategy, market analysis, industry threads | Business & Market Analysis | RDF-Turtle |
| User requests JSON-LD explicitly | Generic | JSON-LD |
| User requests RDF-Turtle explicitly | Business & Market Analysis | RDF-Turtle |

When uncertain, default to the **Generic** template and ask the user if they want the Business & Market Analysis variant.

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
16. For every person entity (authors, commentators, or explicitly mentioned individuals): (a) if a LinkedIn profile URL is found in the source, use {linkedin-url}#this as the primary person IRI with schema:url pointing to the bare profile URL; (b) if an X/Twitter profile URL is found and no LinkedIn URL exists, use {x-url}#this as the primary person IRI; (c) otherwise derive a hash-based IRI from {page_url}. In every case, ALL discovered platform identities MUST be linked via owl:sameAs — e.g., owl:sameAs <https://www.linkedin.com/in/name/#this>, <https://x.com/handle/#this> — ensuring the person is resolvable from any direction. For JSON-LD, use @id for all owl:sameAs values.
17. Where relevant, include additional entity types when discovered e.g., Product, Offer, and Service etc.
18. Language-tag the values of annotation attributes; apply properly according to JSON-LD syntax rules.
19. Describe article authors and publishers in detail.
20. Use a relatedLink attribute to comprehensively handle all inline URLs. Unless told otherwise, it should be a maximum of 20 relevant links.
21. You MUST ensure smart quotes are replaced with single quotes.
22. You MUST check and fix any JSON-LD usage errors based on its syntax rules e.g., missing @id designation for IRI values of attributes that only accept IRI values (e.g., schema:sameAs, owl:sameAs, etc.).
23. You MUST use http://schema.org/ (HTTP, not HTTPS) as the schema: namespace URI. Never use https://schema.org/.
24. You MUST wrap FAQ questions in a schema:FAQPage with schema:mainEntity listing all question IRIs. The FAQPage MUST be linked from the main article via schema:hasPart.
25. You MUST wrap glossary terms in a schema:DefinedTermSet with schema:hasDefinedTerm listing all term IRIs. The DefinedTermSet MUST be linked from the main article via schema:hasPart.
26. ALL DBpedia, Wikidata, and Wikipedia entity references MUST use fully expanded IRIs (e.g., http://dbpedia.org/resource/Tim_Berners-Lee) — never CURIEs or prefixed names.
27. You MUST NOT use file: scheme IRIs anywhere. The @base or @prefix : MUST use the canonical https: URL of the source document with a # suffix.
28. If the response includes a lightweight ontology (custom classes, properties, or an owl:Ontology declaration), you MUST: (a) name and describe the ontology using schema:name and schema:description alongside rdfs:label and rdfs:comment; (b) add schema:identifier with the canonical source URL; (c) associate every class and property with the ontology using rdfs:isDefinedBy : .
29. You MUST NOT use blank nodes for schema:Answer instances. Every schema:Answer MUST be a named entity with its own hash-based IRI (e.g., :a1, :a2) connected via schema:acceptedAnswer :aN — never schema:acceptedAnswer [ a schema:Answer ; ... ].
30. When you assert a directional relationship (e.g., schema:isPartOf), you MUST also assert its inverse on the target entity (e.g., schema:hasPart) — RDF does not infer inverses automatically, so both directions are needed for completeness.
31. Every logical entity group beyond FAQ/glossary/HowTo (e.g., use cases, technologies, architectural layers, key concepts) MUST be wrapped in a schema:ArticleSection and linked to the main article via schema:hasPart. No entity should be orphaned — every entity must be reachable from the main article through some path.
32. The main article MUST include prov:wasGeneratedBy linking to a schema:SoftwareApplication entity representing the skill that produced it. Declare @prefix prov: <http://www.w3.org/ns/prov#> . The skill entity MUST have schema:name (e.g., "kg-generator skill"), schema:url pointing to its GitHub source (e.g., https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator), and schema:description. If multiple skills were used, use multiple prov:wasGeneratedBy triples.

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
8. @base or @prefix : is the canonical https: source URL with # suffix
9. If an ontology is present: (a) it has schema:name and schema:description, (b) schema:identifier with canonical URL, (c) all classes and properties have rdfs:isDefinedBy :
10. No blank nodes used for schema:Answer — every answer is a named entity (:a1, :a2, ...) with schema:acceptedAnswer :aN
11. Inverse relationships are explicit: for every schema:isPartOf there is a corresponding schema:hasPart, etc.
12. prov:wasGeneratedBy links the main article to a skill entity with schema:name, schema:url (GitHub), and schema:description
Report: "COMPLIANCE SELF-AUDIT: X/12 passed. [list any FAIL items with the specific fix applied]. Final output follows."

GATE: 0 FAIL required before delivery. Every numbered rule in this prompt has a corresponding check in this audit. No rule without verification — unchecked rules are aspirational, not enforceable.```

### Post-Generation Checklist

- [ ] `@base` set to `{page_url}`
- [ ] `schema:` namespace uses `http://schema.org/` (HTTP, not HTTPS)
- [ ] All subject/object IRIs are hash-based relative IRIs (except known authority entities)
- [ ] FAQ questions wrapped in `schema:FAQPage` with `schema:mainEntity`
- [ ] Glossary terms wrapped in `schema:DefinedTermSet` with `schema:hasDefinedTerm`
- [ ] Main article has `schema:hasPart` linking FAQPage, DefinedTermSet, HowTo, the ontology (:), and all entity group sections
- [ ] At least 10 `schema:Question` + `schema:Answer` pairs present
- [ ] `owl:sameAs` used (not `schema:sameAs`) for DBpedia cross-references
- [ ] All DBpedia/Wikidata/Wikipedia IRIs fully expanded (not CURIEs)
- [ ] No `file:` scheme IRIs anywhere
- [ ] All IRI-valued attributes use `@id` — no plain string literals for IRI-only properties
- [ ] Inline double quotes within literals converted to single quotes
- [ ] Smart/curly quotes replaced with straight single quotes
- [ ] `relatedLink` includes up to 20 relevant inline URLs
- [ ] Language tags applied to annotation literals where applicable
- [ ] JSON-LD is syntactically valid
- [ ] No guessed media URLs (thumbnailUrl, contentUrl, embedUrl)
- [ ] Images from source content described using `schema:image` with `schema:ImageObject` where distinct
- [ ] Person IRIs derived from LinkedIn/X profile URLs where found; all platform identities linked via `owl:sameAs`
- [ ] If ontology present: `schema:name` + `schema:description`, `schema:identifier`, all classes/properties have `rdfs:isDefinedBy :`
- [ ] `prov:wasGeneratedBy` links article to a skill entity with `schema:name`, `schema:url` (GitHub), `schema:description`

## Template 2 — Business & Market Analysis (RDF-Turtle)

Use for business strategy posts, X/social threads, market analyses, and industry deep-dives.

### Placeholders

| Placeholder | Value |
|---|---|
| `{url}` | URL of the original post or content being analysed |
| `{post-url}` | Used as the Turtle `@prefix :` base (append `#`) |
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

### Prompt

```
You are an expert in semantic web modeling, RDF/Turtle serialization, and schema.org + lightweight ontology design.
Given the post at {url} and its thread (which discusses AI-driven "autopilots" disrupting services markets by selling outcomes rather than tools, starting with outsourced intelligence-heavy tasks such as NDA drafting, insurance brokerage (~$140–200B labor TAM), and accounting (~$50–80B labor TAM), with structural shortages like the loss of ~340k U.S. accountants, data compounding enabling eventual judgment handling, debates around copilots vs. full autopilots, the innovator's dilemma, and founder collaboration opportunities),
produce a **comprehensive RDF/Turtle document** that represents the full business & strategy analysis.
Follow ALL of these final design requirements exactly:
1. Base URI: Use relative hash URIs grounded in {post-url} as the namespace prefix :
2. Use schema.org as the primary vocabulary — use http://schema.org/ (HTTP, not HTTPS) as the schema: namespace URI — supplemented by:
   - skos: for glossary/concept definitions
   - org: for organizations
   - dbo: for selected DBpedia cross-references (via rdfs:seeAlso)
   - rdfs: for class/property definitions
3. Create a small custom lightweight ontology in the same namespace:
   - Define :Industry as rdfs:Class (base class for verticals)
   - Define two subclass rdfs:Class resources: :InsuranceBrokerageIndustry and :AccountingIndustry
   - Define two custom properties on :Industry:
     - :hasLaborTAM      (range xsd:string)
     - :hasAutomationReadiness (range xsd:string)
   - Create explicit instances of these classes (e.g. :insuranceBrokerageVertical a :InsuranceBrokerageIndustry ; ...) to hold concrete data (TAM values, readiness, NAICS, offers, DBpedia links). Do NOT put instance data directly on the class definitions.
4. Use low-redundancy schema.org identifier modeling (Option 3 style):
   - Use dedicated properties when they exist: schema:naics (on industry instances), schema:isbn (on the book), schema:identifier with plain literal for unambiguous codes (e.g. "US" for ISO 3166-1 alpha-2)
   - For NAICS codes, always pair schema:naics (plain code string) with schema:identifier using the Census Bureau canonical lookup URL: https://www.census.gov/naics/?input={code}&year=2022&details={code}
   - Avoid unnecessary schema:PropertyValue wrappers unless genuinely required for disambiguation or extra metadata
5. Core entities that must be included:
   - The main analysis CreativeWork (:analysis)
   - Author (:grok), original post reference (:originalXPost), Julien Bek
   - :aiAutopilotDisruption (Product), :marketDisruptionAction, :servicesMarketDisruption
   - Example task :ndaExample
   - Concrete vertical instances :insuranceBrokerageVertical and :accountingVertical (with TAM, readiness, naics, offers WithCoverage/Rillet autopilots)
   - Organizations :withCoverage and :rillet + their autopilots
   - :shortageEvent (U.S. accountant shortage)
   - :unitedStates with ISO code
   - :threadReplies, :cursorExample, :scalingChallenges
   - :innovatorsDilemma (CreativeWork with isbn "9780060521998")
6. Mandatory structured sections (all must be present and complete):
   - schema:FAQPage (:faqSection) with **exactly 12** schema:Question items (:q1–:q12)
   - skos:ConceptScheme + schema:DefinedTermSet (:glossarySection) with **exactly 10** terms (:termAutopilot through :termVerticalMapping)
   - schema:HowTo (:howtoSection) with **exactly 7** schema:HowToStep items (:step1–:step7)
7. Include all original details:
   - Labor TAM ranges exactly as stated ($140-200B insurance, $50-80B accounting)
   - Automation readiness "High" for both
   - 340,000 accountant shortage statistic
   - Data compounding explanation
   - Outcome-as-a-Service model
   - Innovator's dilemma application
   - Copilot → autopilot transition challenges
   - Founder collaboration via tagging / datasets
8. Keep descriptions concise yet precise; avoid unnecessary verbosity in literals.
9. Output **only** the complete, valid Turtle document inside a single code block. Do not include explanations, comments outside Turtle, or any other text before/after the code block.
10. The main analysis CreativeWork (:analysis) MUST have schema:hasPart linking to :faqSection, :glossarySection, :howtoSection, and ALL other entity group sections (e.g., industry verticals, use cases, technologies).
11. All DBpedia references MUST use fully expanded IRIs (e.g., http://dbpedia.org/resource/...) — never CURIEs or prefixed names.
12. All Wikidata references MUST use fully expanded IRIs (e.g., http://www.wikidata.org/entity/...) — never CURIEs or prefixed names.
13. For every person entity: (a) if a LinkedIn profile URL is found, use {linkedin-url}#this as the primary person IRI with schema:url pointing to the bare profile URL; (b) if an X/Twitter profile URL is found and no LinkedIn URL exists, use {x-url}#this as the primary person IRI; (c) otherwise derive a hash-based IRI from {post-url}. In every case, ALL discovered platform identities MUST be linked via owl:sameAs — e.g., owl:sameAs <https://www.linkedin.com/in/name/#this>, <https://x.com/handle/#this>.
14. The lightweight ontology MUST be named and described using schema:name and schema:description alongside rdfs:label/rdfs:comment, with schema:identifier carrying the canonical source URL. Every class and property MUST have rdfs:isDefinedBy : linking it to the ontology.
15. You MUST NOT use blank nodes for schema:Answer instances. Every schema:Answer MUST be a named entity with its own hash-based IRI (e.g., :a1, :a2) connected via schema:acceptedAnswer :aN — never schema:acceptedAnswer [ a schema:Answer ; ... ].
16. For every directional relationship you assert (e.g., schema:isPartOf), you MUST also assert its inverse on the target entity (e.g., schema:hasPart) — RDF does not infer inverses, so both directions are necessary.
17. The main analysis (:analysis) MUST include prov:wasGeneratedBy linking to a schema:SoftwareApplication entity representing the kg-generator skill. Declare @prefix prov: <http://www.w3.org/ns/prov#> . The skill entity MUST have schema:name "kg-generator skill", schema:url <https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator>, and schema:description.
Current date for metadata: {current date}.

CRITICAL — Before outputting the Turtle, you MUST perform a compliance self-audit. Verify each item and report PASS or FAIL (with the violation fixed):
1. schema: namespace is http://schema.org/ (not https://schema.org/)
2. :analysis has schema:hasPart linking :faqSection, :glossarySection, :howtoSection
3. :faqSection is a schema:FAQPage with schema:mainEntity listing all :q1–:q12
4. :glossarySection is a schema:DefinedTermSet with schema:hasDefinedTerm listing all 10 terms
5. :howtoSection is a schema:HowTo with schema:step listing all :step1–:step7
6. All DBpedia/Wikidata IRIs are fully expanded (not CURIEs)
7. NAICS codes use ?input=&year=2022&details= pattern (not ?code=)
8. No file: scheme IRIs exist anywhere
9. Ontology has schema:name + schema:description + schema:identifier; all custom classes/properties have rdfs:isDefinedBy :
10. No blank nodes for schema:Answer — every answer is a named entity (:aN) with schema:acceptedAnswer :aN
11. Inverse relationships explicit: every schema:isPartOf has a corresponding schema:hasPart, etc.
12. prov:wasGeneratedBy links :analysis to a skill entity with schema:name, schema:url (GitHub), and schema:description
Report: "COMPLIANCE SELF-AUDIT: X/12 passed. [list any FAIL items, already fixed]. Output follows."

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
- [ ] Lightweight ontology present: `:Industry`, two subclasses, two custom properties
- [ ] Instance data on instances only — not on class definitions
- [ ] Both `schema:naics` and `schema:identifier` (Census URL) on each vertical instance
- [ ] Exactly 12 FAQ questions (`:q1`–`:q12`) wrapped in `schema:FAQPage` with `schema:mainEntity`
- [ ] Exactly 10 glossary terms wrapped in `schema:DefinedTermSet` with `schema:hasDefinedTerm`
- [ ] Exactly 7 HowTo steps (`:step1`–`:step7`) wrapped in `schema:HowTo` with `schema:step`
- [ ] All DBpedia/Wikidata IRIs fully expanded (not CURIEs)
- [ ] TAM values exact: `"$140-200B"` and `"$50-80B"`
- [ ] `schema:isbn "9780060521998"` on `:innovatorsDilemma`
- [ ] `schema:identifier "US"` on `:unitedStates`
- [ ] NAICS URLs use `?input=&year=2022&details=` pattern (not `?code=`)
- [ ] No `file:` scheme IRIs anywhere
- [ ] `prov:wasGeneratedBy` links :analysis to a skill entity with `schema:name`, `schema:url` (GitHub), `schema:description`
- [ ] Ontology has `schema:name` + `schema:description` + `schema:identifier`; all classes/properties have `rdfs:isDefinedBy :`
- [ ] Output is the Turtle code block only — no surrounding text

---

## HTML Infographic Companion Requirements

When the user asks for an HTML infographic companion to a generated Knowledge Graph, apply these requirements. For the complete HTML/RDF pairing specification including resolver configuration, navigation panel behavior, localStorage correctness, and the full validation checklist, see the `rdf-infographic-skill` SKILL.md.

### Output Paths

- Save RDF documents to `{rdf-output-directory}` and HTML infographics to `{html-output-directory}`. Resolve from explicit user instructions or session defaults.
- Confirm resolved full file paths before saving.

### Entity IRIs and Resolver Links

- Use `{page_url}` or `{post-url}` as the source-grounded namespace. Never use `file:` scheme IRIs when a canonical HTTPS URL exists.
- Resolver priority: URIBurner (`https://linkeddata.uriburner.com/describe/?uri={entity-iri}`) by default; user-designated resolver if specified; or none if user explicitly opts out.
- Encode `#` as `%23` exactly once in resolver `uri` parameters. `%2523` (double-encoded) is invalid.
- Entity links open in new tabs: `target="_blank" rel="noopener noreferrer"`.
- FAQ questions, FAQ answers, glossary terms, glossary definitions, HowTo section title, and every HowTo step heading are ALL hyperlinked to their KG entity IRIs.
- Local KG entities (hash-based IRIs) route through resolver. LOD Cloud cross-references (DBpedia, Wikidata) link directly.

### POSH and JSON-LD Metadata

- POSH link: `<link rel="related" href="../rdf/{rdf-file}" type="text/turtle">`
- JSON-LD `relatedLink` must use IRI form: `{"@id": "../rdf/{rdf-file}"}` — never a plain string literal.
- `prov:wasGeneratedBy` must reference a `schema:SoftwareApplication` entity per skill.
- Attributions in footer must include: AI Agent (OpenCode), each Skill used, LLM used, Server Platform (Virtuoso)

```html
<!-- Premium footer with 4-column grid design -->
<footer class="footer">
<p style="margin-bottom:20px"><a href="https://linkeddata.uriburner.com/sparql?query=..." target="_blank" class="cta-btn" style="display:inline-flex;align-items:center;gap:8px;padding:12px 24px;background:var(--accent);color:#fff;border-radius:12px;text-decoration:none;font-weight:600;font-size:0.95rem">Explore Knowledge Graph <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M9.5 3.5a1.5 1.5 0 0 1 0 3h-5l-.5.5 1 1a1 1 0 0 0 1.414 1.414l-2-2a1 1 0 0 0 0-1.414l-2-2a1 1 0 0 0-1.414 1.414l1 1-.5.5h5z"/></svg></a></p>
<div class="tech-grid" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:24px;border-top:1px solid var(--line);padding-top:24px">
<div class="tech-card" style="text-align:center;padding:16px;background:var(--panel);border-radius:12px;border:1px solid var(--line)">
<h4 style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:8px">AI Agent</h4>
<a href="https://opencode.ai" target="_blank" style="color:var(--accent);font-family:'Space Grotesk';font-weight:600;font-size:0.95rem;text-decoration:none">OpenCode</a>
</div>
<div class="tech-card" style="text-align:center;padding:16px;background:var(--panel);border-radius:12px;border:1px solid var(--line)">
<h4 style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:8px">AI Agent Skills</h4>
<div style="font-size:0.8rem"><a href="https://github.com/anomalyco/opencode/tree/main/skill-name" target="_blank" style="color:var(--accent);text-decoration:none">skill-name</a></div>
</div>
<div class="tech-card" style="text-align:center;padding:16px;background:var(--panel);border-radius:12px;border:1px solid var(--line)">
<h4 style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:8px">Language Model</h4>
<a href="https://opencode.ai/models/minimax_m2.5free" target="_blank" style="color:var(--accent);font-family:'Space Grotesk';font-weight:600;font-size:0.95rem;text-decoration:none">minimax_m2.5free</a>
</div>
<div class="tech-card" style="text-align:center;padding:16px;background:var(--panel);border-radius:12px;border:1px solid var(--line)">
<h4 style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:8px">Server Platform</h4>
<a href="https://virtuoso.openlinksw.com/" target="_blank" style="color:var(--accent);font-family:'Space Grotesk';font-weight:600;font-size:0.95rem;text-decoration:none">Virtuoso</a>
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
<p style="color:var(--muted);line-height:1.7">This knowledge graph overview was generated by querying the <a href="https://linkeddata.uriburner.com/sparql" target="_blank" style="color:var(--accent)">URIBurner SPARQL endpoint</a> for the named graph <code>{graph-iri}</code>. The original document was transformed into RDF using {skills-used}, then uploaded to the Virtuoso-based URIBurner server. The SPARQL query retrieved {entity-types} from the knowledge graph. The HTML infographic was then rendered using {skills-used} powered by {model-id} and running on Virtuoso.</p>
<p style="margin-top:16px;font-size:0.85rem;color:var(--ink)"><strong>Technology Stack:</strong></p>
<ul style="margin-top:8px;font-size:0.85rem;color:var(--ink);list-style:disc;padding-left:20px">
<li>AI Agent: <a href="https://opencode.ai" target="_blank" style="color:var(--accent)">OpenCode</a></li>
<li>Skills: <a href="https://github.com/anomalyco/opencode/tree/main/skill-name" target="_blank" style="color:var(--accent)">skill-name</a></li>
<li>Language Model: <a href="https://opencode.ai/models/{model-id}" target="_blank" style="color:var(--accent)">{model-id}</a></li>
<li>Server Platform: <a href="https://virtuoso.openlinksw.com/" target="_blank" style="color:var(--accent)">Virtuoso</a></li>
<li>Knowledge Graph: <a href="https://linkeddata.uriburner.com/sparql" target="_blank" style="color:var(--accent)">URIBurner</a></li>
</ul>
</section>
```

Substitute: `{graph-iri}`, `{skills-used}`, `{entity-types}`, `{skill-links}`, and `{model-id}` with actual values.

### Navigation, Theme, and Validation

- Collapse-to-header-bar floating navigation: always-visible compact header, toggle, draggable, resizable.
- Never persist collapsed dimensions in `localStorage`. Recover from stale state. Page-specific keys.
- Dark mode: `html[data-theme="dark"]` and `@media (prefers-color-scheme: dark)` produce equivalent rendering. All colors via CSS variables.
- **GATE: 0 failures required.** Validate: HTML parse, JS syntax, RDF parse + compliance audit, resolver links, local RDF link, nav behavior, skills attribution, dark mode consistency.

---

## MD Document Companion Requirements

When generating a Markdown document alongside RDF and HTML outputs, the MD **MUST** follow these requirements:

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
[Entity Label](https://linkeddata.uriburner.com/describe/?uri={URL-encoded-IRI})
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

This convention allows tracking which AI model generated each artifact without requiring external metadata.
