---
name: document-to-kg-skill
title: Document to Knowledge Graph Skill
description: >
  Transforms documents or text into RDF-based Knowledge Graphs using schema.org terms.
  4-step workflow: (1) Collect document source, {page_url} as @base, output format (JSON-LD
  or Turtle by default; others if explicitly stated), and destination folder. (2) Generate
  RDF via schema.org prompt template using chatPromptComplete. (3) Post-generation review:
  fix syntax errors, present additional Q&A/defined terms/howtos and entity types for
  approval, return revised final output if approved. (4) Save approved RDF to designated
  folder and confirm saved path.
version: 1.0.0
type: skill
created: 2026-04-06T00:00:00.000Z
updated: 2026-04-06T00:00:00.000Z
tools:
  - OAI.DBA.getSkillResource
  - OAI.DBA.chatPromptComplete
---

# Document to Knowledge Graph Skill — Specification (v1.0.0)

---

## MANDATORY PRE-TOOL SEQUENCE — READ BEFORE CALLING ANY TOOL

After `getSkillResource` loads this skill, the **next action must be text only** — send the Opening Announcement and wait for the user's reply. Do not call any other tool first.

---

## Skill Identity

| Field | Value |
|-------|-------|
| **Name** | document-to-kg-skill |
| **Version** | 1.0.0 |
| **Purpose** | Transform documents or text into RDF Knowledge Graphs using schema.org terms. |
| **Scope** | Four-step pipeline: collect source + page_url + format + destination → generate RDF → post-generation review → save to folder. |

---

## Strict Harness Mode

Use **Document-to-KG Harness Mode** whenever the user asks to transform a document, URL, pasted text, PDF, thread, article, or source mesh into RDF, JSON-LD, Turtle, a Knowledge Graph, or an RDF-backed HTML/MD artifact set.

Harness mode constrains interpretation to this skill's document-to-RDF contract. Do not drift into a generic summary, article rewrite, standalone HTML page, or manually invented graph.

### Harness Contract

When active:

1. **Collect or derive required inputs** — document source, canonical `{page_url}`, output RDF format, destination path, and whether HTML/Markdown companions are required.
2. **Use `{page_url}` as entity namespace** for generated document-local IRIs, never `file:` IRIs when a canonical HTTP/HTTPS URL exists.
3. **Generate RDF first** using schema.org and approved vocabularies; RDF is the source of truth for any companion HTML/Markdown.
4. **Apply authority denotation rules** — `schema:SoftwareApplication`, `schema:Organization`, `schema:Country`, and `schema:DefinedTerm`/`skos:Concept` entities must use DBpedia/Wikidata-centered IRIs as described below, with `owl:sameAs` for confirmed cross references.
5. **Inspect collection sources as collections** — when the source is a manual, documentation site, sitemap-backed site, MkDocs/Docusaurus/VitePress collection, GitBook, docs portal, or other multi-page source, inspect sitemap/search index/navigation for high-signal child pages before finalizing RDF. Always review child pages about APIs, SPARQL, endpoints, query examples, services, reporting workflows, data models, server/runtime platforms, and integration instructions when present.
6. **Preserve SPARQL-bearing content** — when source content includes SPARQL queries, query examples, endpoint demos, or reporting/query recipes, do not summarize the query body away. Model each material query as a named `schema:SoftwareSourceCode` resource with `schema:programmingLanguage "SPARQL"`, `schema:text`, `schema:codeSampleType`, `schema:target` pointing to the endpoint/service, and `schema:potentialAction` pointing to a correctly URL-encoded live query URL when the endpoint accepts GET query parameters. Preserve documented placeholders visibly.
7. **Validate before save** — RDF syntax, expanded DBpedia/Wikidata IRIs, no fabricated IRIs, no double-encoded resolver IRIs, no `file:` IRIs, and required prefix declarations.
8. **If HTML/Markdown companions are requested**, hand off to the `rdf-infographic-skill` **RDF Infographic Harness Mode** and satisfy its full HTML/MD/RDF pairing, resolver, KG Explorer, navigation, attribution, and validation contract.
9. **Fail closed on missing requirements** — if a required source, page URL, destination, resolver, or artifact scope is ambiguous and cannot be safely inferred, ask before generating.

This harness is the default for requests such as "generate RDF and associated HTML and MD docs", "redo for this URL", "mesh these sources into RDF/HTML/MD", and "reproduce the HTML infographic from RDF".

---

## Opening Announcement

⛔ **Send this text immediately after `getSkillResource` loads. Do not call any tool before this message is sent and the user has replied.**

---

> **Document to Knowledge Graph Skill activated.** I follow a 4-step workflow:
>
> **Step 1** — Collect your document source, page URL, output format, and destination folder
> **Step 2** — Generate RDF using schema.org terms
> **Step 3** — Review: fix syntax, approve additional Q&A / entity types
> **Step 4** — Save the approved RDF to your designated folder
>
> To begin, please provide:
> 1. **Document source** — paste your text, provide an `http:`/`https:` URL to fetch, or provide a `file:` URL to read from local disk
> 2. **Page URL (`{page_url}`)** — used as `@base` for all relative IRIs (defaults to the source URL for HTTP/HTTPS; for `file:` URLs you will be asked whether to use it as-is or supply a canonical HTTP URL)
> 3. **Output format** — **JSON-LD** or **Turtle** (default choices; any other format accepted if stated)
> 4. **Destination folder** — where to save the output file

---

Wait for the user's reply. **→ NEXT: Step 1.**

⛔ **PRE-BUILD CHECK**: Before producing output, re-read the relevant workflow section above and re-read any checklists or verification gates defined in this skill. Confirm each checklist item before writing output. Build to pass — do not retro-fit. Apply the CLAUDE.md Anti-Drift Protocol: re-read spec section before build, gate-first validation, section-by-section delivery.

---

## Step 1 — Collect Source, Format, and Destination

⛔ **No tool call until all four session variables are confirmed.**

Record the following from the user's reply:

| Variable | Description |
|----------|-------------|
| `{selected_text}` | Document content — pasted text, text read from a `file:` URL, or text fetched from an HTTP/HTTPS URL |
| `{page_url}` | Used as `@base` in the generated RDF — see source-type rules below |
| `{format}` | `JSON-LD` (default), `Turtle` (default), or any other format if explicitly stated |
| `{destination}` | Folder path where the output file will be saved |

If any item is missing, ask for it before proceeding. Do not assume defaults without confirmation.

### Source-type handling

| Source type | How to obtain `{selected_text}` | `{page_url}` default |
|-------------|----------------------------------|----------------------|
| Pasted text | Use directly | Ask user to provide |
| `http:` / `https:` URL | Fetch via web fetch tool | The source URL |
| `file:` URL | Read from local filesystem | Ask user: use the `file:` URL as-is, or provide an HTTP URL as the canonical `@base`? |

**`file:` URL guidance:** `file:` IRIs as `@base` produce non-dereferenceable hash IRIs. If the document has a canonical web URL (e.g., the page it was downloaded from), that is the better `@base`. If no canonical URL exists, the `file:` URL is acceptable and the user should be informed the resulting IRIs will not be dereferenceable from the web.

**→ NEXT: Step 2.**

---

## Step 2 — Generate RDF

Load `references/document-to-knowledge-graph-prompt.md` via `getSkillResource`. Substitute `{page_url}` and `{selected_text}` into the prompt template. Adjust the opening line for `{format}` if not JSON-LD.

Call `OAI.DBA.chatPromptComplete` with the fully substituted prompt.

Present the generated RDF as a code block.

**→ NEXT: Step 3.**

---

## Step 3 — Post-generation Review (mandatory)

Execute all five sub-tasks. Do not skip any. Do not proceed to Step 4 until all are resolved.

1. **Syntax check** — identify and fix all syntax errors in the generated RDF. Report fixes made.
2. **Compliance check** — verify the output against the Post-Generation Checklist below. Fix all violations before proceeding.
3. **Additional Q&A / defined terms / howtos** — present a candidate list for user approval. Do not add to the output until explicitly approved.
4. **Additional entity types** — present a candidate list for user approval. Do not add until explicitly approved.
5. **Revised final output** — if any additions from sub-tasks 3 or 4 are approved, return the complete revised RDF incorporating originals plus all approved additions.

### Post-Generation Checklist

- [ ] `@base` set to `{page_url}`
- [ ] `schema:` namespace uses `http://schema.org/` (HTTP, not HTTPS)
- [ ] All subject/object IRIs are hash-based relative IRIs (except known authority entities)
- [ ] FAQ questions wrapped in `schema:FAQPage` with `schema:mainEntity`
- [ ] Glossary terms wrapped in `schema:DefinedTermSet` with `schema:hasDefinedTerm`
- [ ] Main article has `schema:hasPart` linking FAQPage, DefinedTermSet, HowTo, and all entity group sections
- [ ] At least 10 `schema:Question` + `schema:Answer` pairs present
- [ ] Every entity's rdf:type matches its semantic role: HowToStep → schema:HowToStep, Question → schema:Question, Answer → schema:Answer, DefinedTerm → schema:DefinedTerm, ArticleSection → schema:CreativeWork. No entity typed as schema:Thing when a specific type exists.
- [ ] No blank nodes for `schema:Answer` — every answer is a named entity
- [ ] Inverse relationships explicit: every `schema:isPartOf` has corresponding `schema:hasPart`
- [ ] `owl:sameAs` used (not `schema:sameAs`) for DBpedia/Wikidata cross-references
- [ ] All DBpedia/Wikidata/Wikipedia IRIs fully expanded (not CURIEs)
- [ ] Every `schema:Organization` subject IRI follows the organization denotation priority rule: DBpedia resource IRI (1st) → Wikidata entity IRI (2nd) → LinkedIn company page `#this` (3rd) → X/Twitter org account `#this` (4th) → official homepage `#this` (5th) → document-local hash IRI (last). The highest-priority available IRI is the primary subject — never a document-local IRI with `owl:sameAs` pointing to the canonical one. `owl:sameAs` links all remaining discovered platform identities.
- [ ] Every `schema:DefinedTerm` or `skos:Concept` subject IRI follows the concept denotation priority rule: standards-body/platform IRI (1st) → DBpedia resource IRI (2nd) → Wikidata entity IRI (3rd) → document-local hash IRI (last). **When a confirmed DBpedia IRI exists, use it as the primary subject directly — do NOT create a document-local IRI and add `owl:sameAs dbr:X`.** The entity IS `dbr:X`; the alias is redundant and bloats the graph. `owl:sameAs` is reserved for genuine cross-vocabulary alignment (e.g., `dbr:SPARQL owl:sameAs wd:Q54871`) and platform identity equivalences — not for local-alias→canonical redirects. Document-local is correct only when no confirmed DBpedia or Wikidata IRI exists.
- [ ] Every `schema:SoftwareApplication` subject IRI follows the software denotation priority rule: DBpedia IRI if confirmed, else Wikidata IRI if confirmed, else official application home page URL with `#this`
- [ ] Any non-DBpedia/non-Wikidata `schema:SoftwareApplication` IRI has `owl:sameAs` links to confirmed DBpedia/Wikidata identities when such identities exist, and `owl:` is declared as `http://www.w3.org/2002/07/owl#`
- [ ] Every `schema:Country` subject IRI follows the country denotation priority rule: DBpedia IRI if confirmed, else Wikidata IRI if confirmed, else a source-grounded document IRI; add `owl:sameAs` links to confirmed DBpedia/Wikidata equivalents.
- [ ] For multi-page documentation/manual sources, sitemap/search index/navigation has been reviewed for high-signal service/API/SPARQL/query/model/platform child pages, and those pages are represented or explicitly ruled out
- [ ] SPARQL query examples, query recipes, or endpoint demos from the source are preserved as `schema:SoftwareSourceCode` with `schema:programmingLanguage "SPARQL"`, `schema:text`, target endpoint/service, and correctly URL-encoded `schema:potentialAction` live-query links where available
- [ ] No `file:` scheme IRIs anywhere
- [ ] All IRI-valued attributes use `@id` — no plain string literals for IRI-only properties
- [ ] Inline double quotes within literals converted to single quotes
- [ ] Smart/curly quotes replaced with straight single quotes
- [ ] `relatedLink` includes up to 20 relevant inline URLs
- [ ] Language tags applied to annotation literals where applicable
- [ ] No guessed media URLs (thumbnailUrl, contentUrl, embedUrl)
- [ ] Images from source content described using `schema:image` with `schema:ImageObject` where distinct
- [ ] Person IRIs derived from LinkedIn/X profile URLs where found; all platform identities linked via `owl:sameAs`
- [ ] If ontology present: `schema:name` + `schema:description`, `schema:identifier`, all classes/properties have `rdfs:isDefinedBy :`
- [ ] `prov:wasGeneratedBy` links article to a skill entity with `schema:name`, `schema:url` (GitHub), `schema:description`

**→ NEXT: Step 4.**

### SoftwareApplication IRI Denotation Rule

When the generated RDF names a software product, application, SaaS product, developer tool, LLM interface, browser extension, server platform, or app connector as a `schema:SoftwareApplication`, choose its subject IRI using this priority order:

1. **DBpedia first** — if a confident DBpedia resource exists, use the fully expanded DBpedia IRI as the primary denotation IRI, for example `http://dbpedia.org/resource/Google_Docs`.
2. **Wikidata second** — if no confident DBpedia resource exists but a confident Wikidata entity exists, use the fully expanded Wikidata IRI, for example `http://www.wikidata.org/entity/Q...`.
3. **Homepage fallback** — if neither DBpedia nor Wikidata can be confirmed, use the official application/product home page URL with `#this` appended, for example `https://example.com/product/#this`.

When the primary IRI is not DBpedia- or Wikidata-based, add `owl:sameAs` relations to any confirmed DBpedia or Wikidata IRIs for that application. Declare `owl:` as `http://www.w3.org/2002/07/owl#` whenever `owl:sameAs` appears. Do not use a local document hash IRI for a known software application when one of the three denotation options above is available.

Do not fabricate DBpedia or Wikidata IRIs. If lookup or source evidence does not provide a confident match, use the homepage `#this` fallback and omit `owl:sameAs` until a confident DBpedia/Wikidata identity is established.

---

### Country IRI Denotation Rule

When the generated RDF names a country as a `schema:Country`, choose its subject IRI using this priority order:

1. **DBpedia first** — if a confident DBpedia country resource exists, use the fully expanded DBpedia IRI as the primary denotation IRI, for example `http://dbpedia.org/resource/South_Africa`.
2. **Wikidata second** — if no confident DBpedia resource exists but a confident Wikidata country entity exists, use the fully expanded Wikidata IRI, for example `http://www.wikidata.org/entity/Q258`.
3. **Document-local fallback** — only if neither authority IRI can be confirmed, use a source-grounded document hash IRI derived from `{page_url}`.

When a primary country IRI is DBpedia-based and a confident Wikidata equivalent exists, add `owl:sameAs` to the Wikidata entity. When a primary country IRI is Wikidata-based and a confident DBpedia equivalent later becomes available, normalize to DBpedia or add `owl:sameAs` to the DBpedia entity if normalization would disrupt an existing artifact. Do not use local document hash IRIs for known countries when DBpedia or Wikidata authority IRIs are available.

Visible country names in HTML, Markdown, and KG Explorer nodes must link through the configured resolver using the selected country RDF IRI. Country rows that carry source-specific measurements may attach those measurements directly to the selected country entity or to a named observation node connected to the country, but the country identity itself must remain DBpedia/Wikidata-centered.

Do not fabricate DBpedia or Wikidata IRIs. If lookup or source evidence does not provide a confident match, use the document-local fallback and omit `owl:sameAs` until a confident identity is established.

---

### Organization IRI Denotation Rule

When the generated RDF names an organization, company, institution, or other corporate/collective entity as a `schema:Organization`, choose its subject IRI using this priority order:

1. **DBpedia first** — if a confident DBpedia resource exists, use the fully expanded DBpedia IRI as the primary denotation IRI, e.g., `http://dbpedia.org/resource/Microsoft`.
2. **Wikidata second** — if no confident DBpedia resource exists but a confident Wikidata entity exists, use the fully expanded Wikidata IRI, e.g., `http://www.wikidata.org/entity/Q2283`.
3. **LinkedIn `#this` third** — if no confident DBpedia or Wikidata identity can be confirmed but a LinkedIn company page URL is available, use the company page URL with `#this` appended, e.g., `https://www.linkedin.com/company/microsoft/#this`.
4. **X/Twitter `#this` fourth** — if no LinkedIn page is found, use the organization's X/Twitter account URL with `#this` appended.
5. **Homepage `#this` fifth** — if no platform identity is available, use the organization's official homepage URL with `#this` appended.
6. **Document-local last resort** — only if no platform identity can be established, use a source-grounded document hash IRI derived from `{page_url}`.

**CRITICAL:** The highest-priority available IRI becomes the PRIMARY SUBJECT — never use a document-local IRI when a canonical platform IRI (DBpedia, Wikidata, LinkedIn, X, homepage) is available. `owl:sameAs` links all remaining discovered platform identities.

When the primary IRI is DBpedia-based and a confident Wikidata equivalent exists, add `owl:sameAs` to the Wikidata entity. When primary IRI is Wikidata-based and a confident DBpedia equivalent exists, normalize to DBpedia or add `owl:sameAs` if normalization would disrupt an existing artifact. Do not use document-local hash IRIs for known organizations when authority IRIs are available.

Organization names must match the source document exactly — no fabricated legal names or suffixes. If the source says "Google", use "Google" — not "Google LLC" or "Alphabet Inc." unless the source explicitly states the full legal name.

Do not fabricate DBpedia or Wikidata IRIs. If lookup or source evidence does not provide a confident match, use the next priority tier and omit `owl:sameAs` until a confident identity is established.

---

### DefinedTerm/Concept IRI Denotation Rule

When the generated RDF names an abstract concept, term, idea, framework, methodology, or ontological class as a `schema:DefinedTerm` or `skos:Concept`, choose its subject IRI using this priority order:

1. **Standards-body or platform IRI first** — if the concept has a well-known W3C, schema.org, IANA, or other standards-body IRI, use that as the primary IRI, e.g., `https://www.w3.org/2001/sw/#this` for Semantic Web.
2. **DBpedia second** — if no standards-body IRI exists but a confident DBpedia resource exists for the term, use the fully expanded DBpedia IRI, e.g., `http://dbpedia.org/resource/Semantic_Web`.
3. **Wikidata third** — if no confident DBpedia resource exists but a confident Wikidata entity exists, use the fully expanded Wikidata IRI, e.g., `http://www.wikidata.org/entity/Q...`.
4. **Document-local last resort** — most common case: use a source-grounded document hash IRI derived from `{page_url}` with a mnemonic fragment, e.g., `#{conceptName}`.

Most concept entities will use the **document-local hash IRI** (tier 4) because abstract concepts rarely have standards-body, DBpedia, or Wikidata IRIs. When a confirmed DBpedia IRI (tier 2) or Wikidata IRI (tier 3) exists, that IRI MUST become the primary subject — `owl:sameAs` must NOT be used to link a document-local alias to the canonical IRI. Use `owl:sameAs` only for cross-vocabulary alignment between the two canonical forms (e.g., `dbr:SPARQL owl:sameAs wd:Q54871`).

Declare `owl:` as `http://www.w3.org/2002/07/owl#` whenever `owl:sameAs` appears.

Do not fabricate DBpedia or Wikidata IRIs. If lookup or source evidence does not provide a confident match, use the document-local fallback and omit `owl:sameAs` until a confident identity is established.

## Step 4 — Save to Folder

Write the approved RDF to `{destination}`. Derive the filename from `{page_url}` by slugifying the path component and appending the appropriate extension:

| Format | Extension |
|--------|-----------|
| JSON-LD | `.jsonld` |
| Turtle | `.ttl` |
| N-Triples | `.nt` |
| RDF/XML | `.rdf` |

Confirm the full saved file path to the user. The session is complete.

---

## Optional HTML Infographic Companion

When the user asks for an HTML infographic in addition to the RDF Knowledge Graph, apply these requirements. For the complete HTML/RDF pairing specification including resolver configuration, navigation panel behavior, localStorage correctness, and validation checklist, see the `rdf-infographic-skill` SKILL.md.

### Output Paths

- Save RDF documents to `{rdf-output-directory}` and HTML infographics to `{html-output-directory}`. Resolve these placeholders from explicit user instructions, current session preferences, or skill defaults; do not hard-code a personal filesystem path into the reusable skill guidance.
- When no destination has been provided, ask for the output directories or use an already-established session default, then confirm the resolved full file paths.

### Entity IRIs and Resolver Links

- Use `{page_url}` as the source-grounded namespace for generated entity IRIs. Do not use `file:` scheme IRIs when a canonical HTTP/HTTPS page URL exists.
- Resolver priority: URIBurner (`https://linkeddata.uriburner.com/describe/?url={entity-iri}`) by default; user-designated resolver if specified; or none if user explicitly opts out.
- Encode `#` as `%23` in resolver `url` parameter values exactly once. `%2523` (double-encoded) is invalid.
- Every generated HTML anchor whose `href` is not a same-page fragment (`#section`) must open a new tab or view using `target="_blank" rel="noopener noreferrer"`. Same-page navigation fragment links remain same-tab and must not carry `target="_blank"`.
- FAQ questions, FAQ answers, glossary terms, glossary definitions, HowTo section title, and every HowTo step heading are ALL hyperlinked to their KG entity IRIs via the resolver pattern.
- Every hyperlinked entity must have a correct rdf:type matching its semantic role: HowToStep headings link to schema:HowToStep entities, FAQ questions link to schema:Question entities, glossary terms link to their declared type (schema:DefinedTerm or appropriate type). Do not link a HowToStep heading to a schema:Question or other mismatched type — content-match alone is insufficient.
- Visible semantic entities route through the configured resolver using their selected RDF IRIs, including DBpedia/Wikidata IRIs selected under the software denotation rule. The visible link target is the resolver URL; the resolver `url` parameter value is the entity IRI.

### POSH and JSON-LD Metadata

- Indicate the associated RDF document using `<link rel="related" href="../rdf/{rdf-file}" type="text/turtle">`.
- Embed a JSON-LD structured-data island with a `WebPage` node. `schema:relatedLink` must use IRI form: `{"@id": "../rdf/{rdf-file}"}` — not a plain string literal.
- `prov:wasGeneratedBy` must reference a `schema:SoftwareApplication` entity for each skill used, with `schema:name`, `schema:url` (GitHub), and `schema:description`.
- Skills attribution line in the HTML footer: `Generated using <a target="_blank" rel="noopener noreferrer" href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/{skill-name}">skill-name</a>`. Link attributed labels directly; do not use generic `Visit`/`Learn more` anchor text.

### Navigation, Theme, and Validation

- Collapse-to-header-bar floating navigation: always-visible compact header, toggle button (− / +), draggable, resizable, closed by default.
- Never persist collapsed dimensions as open dimensions in `localStorage`. Recover from stale or corrupt values. Use page-specific keys.
- Dark mode: `html[data-theme="dark"]` and `@media (prefers-color-scheme: dark)` must produce equivalent rendering. All colors via CSS variables — no hardcoded hex/rgba values outside `:root`.
- **GATE: 0 failures required before delivery.** Validate: HTML parse, JS syntax, RDF parse + compliance audit, resolver-link validity, entity type correctness (each hyperlinked entity's rdf:type matches its HTML role), open-tab behavior for non-fragment links, local RDF link existence, nav behavior, skills attribution, dark mode consistency.

---

## Tools Reference

| Tool | Role |
|------|------|
| `OAI.DBA.getSkillResource` | Load this skill's content and the prompt template |
| `OAI.DBA.chatPromptComplete` | Apply the prompt template to generate RDF |
| *(file-writing tool)* | Write the approved RDF to the designated folder |

### Execution Routing

1. **Native OAI.DBA tool execution** — call `OAI.DBA.*` tools directly
2. **URIBurner / Demo REST function execution** — via REST API endpoint
3. **Terminal-owned OAuth flow** — when the endpoint requires OAuth 2.0 authentication, execute the flow from the terminal (authorization code, client credentials, or device flow), capture the Bearer token, and inject via `Authorization: Bearer {token}` into subsequent REST/OpenAPI calls
4. **MCP** — via streamable HTTP or SSE
5. **OPAL Agent routing** — via canonical OPAL-recognizable function names

If the user explicitly names a protocol, honor that preference.

---

## Operational Rules

1. **Send the opening announcement before any tool call.** After `getSkillResource`, the next action is the announcement text — no tool call.
2. **All four session variables must be confirmed before Step 2.** Never assume `{page_url}` or `{destination}` without explicit user confirmation. For `file:` source URLs, always ask whether to use the `file:` URL or a canonical HTTP URL as `@base`.
3. **Format defaults are JSON-LD and Turtle.** Always offer these two. Honor any other format if explicitly stated by the user.
4. **Post-generation review is mandatory.** Step 3 cannot be skipped. All four sub-tasks must be executed before saving.
5. **Never add unapproved content.** Additional Q&A, defined terms, howtos, and entity types must be presented for approval before being included in the output.
6. **Never fabricate IRIs.** All IRIs must be derived from `{page_url}` as `@base`, from existing hyperlinks in the source document, or from confident external sources (DBpedia, Wikidata, Wikipedia). Do not invent IRIs.
7. **External IRIs must be fully expanded.** DBpedia (`http://dbpedia.org/resource/...`), Wikidata (`http://www.wikidata.org/entity/...`), and Wikipedia (`https://en.wikipedia.org/wiki/...`) references must use their full IRI form — never CURIEs or prefixed names. Only schema.org terms may use the `schema:` prefix.
8. **Smart quotes must be replaced with single quotes.** Enforce this in Step 3 syntax check.
9. **Inline double quotes in annotation values must become single quotes.** Enforce this in Step 3 syntax check.
10. **Filename is derived from `{page_url}`.** Never use a generic or invented filename.
11. **Scope is strictly document → RDF.** This skill does not interact with Virtuoso RDF Views, quad maps, or relational database tables.

---

## Preferences

| Setting | Value |
|---------|-------|
| **Style** | Clear and concise |
| **IRI construction** | Strictly derived from `{page_url}` or known external sources |
| **Format confirmation** | Always confirm with user — never assume |
| **Error reporting** | Name the step, the issue, and the fix applied |
| **Response scope** | Strictly scoped to this 4-step document → RDF pipeline |

---

## Index Page Generation

After saving generated files (RDF, JSON-LD, or companion HTML infographics) into a directory, **always offer** to generate or update `index.html`, `index.css`, and `index.js` for that directory. These provide a dynamic, searchable index with grid, timeline, and table views.

**Generator**: `scripts/index.js`
**Templates**: `templates/corpus-index.css`, `templates/corpus-index.js`

```
node scripts/index.js <target-directory>
```

The index page scans all `.html` files, extracts metadata (`<title>`, `<meta>`, JSON-LD), auto-derives themes from keywords, and renders filterable cards. All links are local `file://` references. Confirm the directory with the user before running.
