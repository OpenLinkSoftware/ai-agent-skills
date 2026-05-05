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
- [ ] No blank nodes for `schema:Answer` — every answer is a named entity
- [ ] Inverse relationships explicit: every `schema:isPartOf` has corresponding `schema:hasPart`
- [ ] `owl:sameAs` used (not `schema:sameAs`) for DBpedia cross-references
- [ ] All DBpedia/Wikidata/Wikipedia IRIs fully expanded (not CURIEs)
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

---

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

When the user asks for an HTML infographic in addition to the RDF Knowledge Graph, apply these requirements:

- Save RDF documents to `{rdf-output-directory}` and HTML infographics to `{html-output-directory}`. Resolve these placeholders from explicit user instructions, current session preferences, or skill defaults; do not hard-code a personal filesystem path into the reusable skill guidance.
- When no destination has been provided, ask for the output directories or use an already-established session default, then confirm the resolved full file paths.
- Use `{page_url}` as the source-grounded namespace for generated entity IRIs. Do not use `file:` scheme IRIs when a canonical HTTP/HTTPS page URL exists.
- Hyperlink visible entity mentions using `https://linkeddata.uriburner.com/describe/?uri={entity-iri}` where `{entity-iri}` is an actual entity identifier from the generated Knowledge Graph.
- Encode `#` as `%23` in resolver `uri` parameter values. Do not double encode; `%2523` is invalid.
- Entity links must open a new tab or view using `target="_blank" rel="noopener noreferrer"`.
- Embed a JSON-LD structured-data island. Resolver-backed JSON-LD `@id` values must match the visible HTML entity hyperlinks exactly when they represent the same KG node.
- Indicate the associated RDF document in HTML metadata using a relative POSH link, e.g. `<link rel="xhv:related related" href="../rdf/{rdf-file}" type="text/turtle">`, with `xhv` bound to `http://www.w3.org/1999/xhtml/vocab#`.
- Also indicate the same associated RDF document in the embedded JSON-LD `WebPage` node using `schema:relatedLink` with the same relative href, e.g. `"relatedLink": "../rdf/{rdf-file}"`.
- Hyperlink FAQ questions, FAQ answers, glossary terms, and HowTo steps to their KG entity IRIs through the same resolver pattern.
- Render FAQs with native `<details class="faq-item">` and `<summary>` accordions.
- Include a floating section navigation control in every HTML infographic. It must be closed by default, openable, closable, draggable, and resizable by pointer drag.
- Persist the navigation control's open/closed state, position, and size in `localStorage` using a page-specific key.
- Link the navigation control to stable section IDs. If sections lack IDs, derive stable IDs from their headings.
- Ensure the control and page aesthetics work in both light and dark mode; dark-mode CSS must not make light mode render as dark.
- Include a page-level light/dark mode toggle control in every HTML infographic. The default theme should follow `prefers-color-scheme` only until the user makes an explicit choice.
- Persist the user's theme choice in `localStorage`, apply it at document level with `html[data-theme="light"]` or `html[data-theme="dark"]`, and keep all component styling driven by CSS variables.
- The theme toggle must not conflict spatially or visually with the floating section navigation control.

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
