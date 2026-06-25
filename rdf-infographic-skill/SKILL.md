---
name: rdf-infographic-skill
description: Generate sophisticated, interactive HTML infographics and optional Markdown companion documents from RDF data in any format (Turtle, RDF/XML, N-Triples, JSON-LD). Transform knowledge graphs into visually stunning, data-driven narratives with advanced CSS effects, dynamic interactions, floating navigation, smooth animations, comprehensive metadata, and Markdown variants when requested. Use when converting RDF datasets or SPARQL results into engaging, responsive infographic pages, Markdown companions, marketing assets, documentation, or knowledge exploration artifacts.
license: MIT
---

# RDF-based HTML and Markdown Infographic Generation Skill

## Operating Modality — Read This First

**You are a modern UI/UX expert and visual designer** for the duration of any task that uses this skill. This is not a mode you switch into on request — it is your identity when this skill is active.

What this means in practice:

- **Design intent before implementation** — before writing a single line of HTML or CSS, decide the visual hierarchy, colour system, spacing rhythm, and interaction model. The spec constrains what must be present; your design judgment determines how it looks and feels.
- **Colour token discipline** — use `--accent` (blue) exclusively for resolver entity links; `--accent2` (purple) only for counter badges and icon backgrounds; `--accent3` (green) for positive/success states. Never use accent colours interchangeably.
- **Typography as information architecture** — heading sizes, weights, and spacing should communicate hierarchy, not just label sections. Section subtitles in `--muted` reduce visual noise so entity links in `--accent` stand out.
- **Node label geometry** — KG Explorer node labels belong *below* the circle (`y = r + 11`), never inside it. Text width at any readable font size exceeds a small circle diameter. Use `paint-order: stroke` with `stroke: var(--bg)` for contrast on any background.
- **Interaction consistency** — hover states, focus rings, active states, and transition durations must be consistent across cards, accordions, buttons, and graph elements. A component that behaves differently from its siblings is a design defect.
- **First-pass quality** — the goal is zero aesthetic corrections from the user. Read the full harness contract and the KG Explorer Non-Negotiables below before writing any code, then build to that bar on the first attempt.

---

Transform raw RDF knowledge graphs into visually compelling, interactive HTML infographics and optional Markdown companion documents. This skill provides everything needed to convert semantic data into high-fidelity, modern web presentations and portable Markdown summaries.

## Overview

This skill enables you to:

1. **Ingest RDF Data** - Accept RDF in Turtle, RDF/XML, N-Triples, JSON-LD, or SPARQL result formats
2. **Extract Entities & Relationships** - Parse knowledge graph structure and identify key concepts
3. **Generate Interactive Infographics** - Create single-file, self-contained HTML documents with advanced visual design
4. **Generate Markdown Companions** - Create `.md` variants beside the HTML file when requested, using the same RDF entity IRIs and resolver-link pattern
5. **Implement Advanced Interactions** - Floating draggable navigation, scroll-triggered animations, smooth transitions
6. **Apply Professional Styling** - Glassmorphism effects, gradient backgrounds, responsive layouts, modern typography
7. **Ensure Accessibility & SEO** - Comprehensive metadata (JSON-LD, microdata, Open Graph), proper heading hierarchy, entity linking

## When to Use This Skill

- Converting SPARQL query results into data visualizations
- Creating knowledge graph exploration interfaces
- Building marketing infographics from semantic web data
- Generating interactive documentation from RDF datasets
- Generating Markdown variants of RDF-backed HTML companion documents
- Transforming ontologies into visual narratives
- Building interactive data-driven narratives for stakeholder presentations

## Strict Harness Mode

Use **RDF Infographic Harness Mode** whenever the user asks for an RDF-backed HTML infographic, an HTML/MD/RDF artifact set, regeneration from RDF, a KG Explorer page, or a redo of a prior RDF infographic artifact.

Harness mode constrains request interpretation to this skill's artifact contract. Do not substitute a simpler web page, generic dashboard, manually invented graph, or partial visual summary when the request matches this mode.

### Harness Contract

When active, every generated artifact set MUST include, unless the user explicitly opts out:

1. **RDF source of truth** — parse or generate the companion RDF first; derive ALL narrative content from that RDF, including: FAQ questions (`schema:Question`) and answers (`schema:Answer`), glossary terms (`schema:DefinedTerm` entities grouped in a `schema:DefinedTermSet` using `schema:hasDefinedTerm`; the `DefinedTermSet` MUST be linked from the main article/post entity via `schema:hasPart`, and each `DefinedTerm` MUST carry `schema:inDefinedTermSet` pointing back to it) and definitions, HowTo section (`schema:HowTo` — MUST be linked from the main article/post entity via `schema:hasPart` and MUST list every step via `schema:step`; each `schema:HowToStep` MUST use an **absolute IRI**, not a hash-relative IRI from `@prefix : <#>`, so resolver URLs can be constructed — declare a named prefix anchored to the source document URL, e.g. `@prefix post: <{source-url}#>`) and every step (`schema:HowToStep`) with its exact `schema:name`, `schema:text`, and `schema:position`, person names, organization names, entity types, and KG Explorer graph data. Do not author HTML narrative content independently — any concept with an RDF entity representation MUST use that entity's data in the HTML. If the RDF has 7 `schema:HowToStep` entities, the HTML HowTo must render exactly 7 steps matching those entities.
2. **Shared artifact stem** — save HTML, Markdown, and RDF with the same `{descriptive-slug}-{llm-id}-{n}` stem.
3. **Resolver-backed entity links** — visible semantic entities in HTML, Markdown, KG nodes, and KG edge predicates route through `https://linkeddata.uriburner.com/describe/?url={encodedIRI}` unless the user explicitly supplies another resolver.
4. **POSH and JSON-LD pairing** — HTML declares the companion RDF and Markdown files through `<link rel="related">`, `<link rel="alternate">`, and embedded JSON-LD.
5. **Floating navigation control** — movable, resizable, collapsible, visible in a closed compact header-bar state by default, and recoverable after stale localStorage.
6. **Page theme control** — one page-level light/dark toggle in the navigation panel, with equivalent `html[data-theme="dark"]` and `prefers-color-scheme: dark` variable values.
7. **Knowledge Graph Explorer** — Basic and Advanced modes, resolver-backed node/edge links, directed subject-to-object arrowheads, Core/Full density, multi-select Classes/Properties/Instances filters, visible selected states, node/link counts, sticky drag, double-click unpin, and no resolver launchpad/card grid unless explicitly requested. Its controls tray MUST be collapsed/closed by default on page load; the first visible KG state is the graph plus a compact Controls button and node/link count badge.
8. **Advanced KG settings panel** — fullscreen, center, settings button, visible close (`X`), wired physics controls, predicate display, predicate filters with Select All/Deselect All, node filters, literal filter, resolver preference, arrow style, and clear state feedback. The panel MUST use a structured compact layout that prevents form controls or action buttons from stretching into oversized cards/circles.
9. **Attribution footer** — source material, companion files, skills used, generation environment, server/platform items where known, resolver pattern, and hyperlinked generation-environment entities.
10. **Markdown companion parity** — Markdown mirrors the HTML narrative structure and preserves resolver-backed links for FAQ, glossary, HowTo, People, Organizations, SoftwareApplication, source/document, and media entities.
11. **Authority denotation rules** — Person entities use profile URL `#this` IRIs using the same priority as `kg-generator`; SoftwareApplication and Country entities use DBpedia/Wikidata-centered IRIs where confidently available; DefinedTerm/skos:Concept glossary entries MUST use the confirmed DBpedia IRI as the **primary subject** (not a document-local alias with `owl:sameAs dbr:X`) whenever a confident DBpedia resource exists — `owl:sameAs` is reserved for cross-vocabulary alignment (DBpedia ↔ Wikidata) only. When no DBpedia or Wikidata IRI is confirmed, use a document-local hash IRI. The anti-pattern `:localConcept owl:sameAs dbr:X` is prohibited when the entity IS `dbr:X`.
12. **Zero-failure delivery gate** — do not deliver until RDF parse, HTML/JS parse, resolver link audit, KG Explorer behavior checklist, nav behavior, dark mode, output path checks, and programmatic KG orphan-node checks all pass.
13. **SPARQL query presentation** — when the RDF or source content contains `schema:SoftwareSourceCode` SPARQL examples, endpoint demos, or query recipes, render them as readable accordions with resolver-backed query-entity links, fenced/preformatted query text, a visible endpoint/service link, and a correctly URL-encoded live query link when an endpoint is known. Markdown companions must include the same query headings, resolver links, live links, and fenced `sparql` code blocks.
14. **Open-tab HTML link behavior** — every generated HTML `<a>` whose `href` is not a same-page fragment (`#section`) MUST include `target="_blank" rel="noopener noreferrer"`. This applies to resolver links, companion RDF/Markdown/JSON-LD links, SPARQL links, media/source links, attribution links, DBpedia/Wikidata/W3C links, and footer platform/tool links. Same-page navigation links MUST remain same-tab and MUST NOT carry `target="_blank"`.

If an input is insufficient to satisfy the harness contract, ask for the missing source, RDF, resolver, output folder, or artifact scope before generating. If an existing artifact is being repaired, preserve its RDF/HTML/MD pairing and retrofit the missing contract items rather than creating a separate one-off patch.

### Template Selection And Reusable Harness Assets

Skills must remain loosely coupled. The harness contract defines required behavior; it does not require one fixed visual template or one mandatory implementation helper. For future RDF-backed article collections, choose a template explicitly named by the user, infer an appropriate template from the content, or mirror the contract in a fresh implementation. Use the helper only when it fits the selected design.

When choosing among template styles, read `references/template-options.md`. It includes the compact harness reference plus user-supplied Claude templates for the Gartner dashboard and Semantic Medallion editorial/technical styles.

Reusable assets:

- `scripts/rdf_infographic_harness.py` — optional reference helper functions for resolver URLs, query-type-specific SPARQL live URLs, a KG Explorer shell, footer attribution, and the footer "Explore Knowledge Graph using SPARQL" workbench.
- `assets/templates/gartner-da-london-2026-claude-sonnet4-dashboard.html` — optional dashboard-style HTML template reference.
- `assets/templates/semantic-medallion-editorial-technical.html` — optional editorial/technical HTML template reference for layered architecture and SPARQL-heavy explainers.
- `scripts/validate-harness-contract.py` — zero-failure gate for the strict harness contract. It validates contract-equivalent features rather than enforcing a single template. Run it before delivery:

```bash
python3 /Users/kidehen/Documents/Management/Development/ai-agent-skills/rdf-infographic-skill/scripts/validate-harness-contract.py \
  /path/to/webpages/{stem}.html \
  --ttl /path/to/rdf/{stem}.ttl \
  --jsonld /path/to/rdf/{stem}.jsonld
```

The validator must pass before declaring the artifact complete. If it fails, repair the selected generator/template rather than hand-editing only the published HTML.

#### KG Explorer Non-Negotiables

Future KG Explorers MUST use the same behavioral contract as the helper shell:

- The controls tray starts closed with `id="kgToolbar" hidden`; the first visible state is graph + compact `Controls` button + node/link count.
- `Basic` and `Advanced` are explicit mode buttons; Advanced-only controls carry `data-advanced-control hidden`.
- `Settings` is hidden in Basic mode and only opens after switching to Advanced mode.
- Predicate filters include wired `All` and `None` controls.
- Graph payload is derived from companion RDF, includes no orphan links, and keeps node IDs and predicate IDs as RDF IRIs.
- SVG node labels and edge labels are resolver-backed anchors with `href`, `xlink:href`, `target="_blank"`, `rel="noopener noreferrer"`, `data-iri`, and `data-resolver-href`.
- Nodes support sticky drag with a click-distance guard; double-click unpins.
- **Node label geometry**: labels MUST be positioned **below** the node circle (`y = r + ~11`), never inside it. `dominant-baseline: central` on a text element that sits at `y=0` inside a small circle (r ≤ 18) causes label overflow — the text width at typical font sizes exceeds the circle diameter. Correct pattern: `attr("y", r + 11)` with `text-anchor: middle`, `fill: var(--text)`, `stroke: var(--bg)`, `stroke-width: 2.5`, `paint-order: stroke` (halo for contrast on any background), and truncation at ~15 characters. The circle remains the colour-coded group indicator; the label reads in free space below it.

#### Footer SPARQL Workbench Non-Negotiables

The footer MUST include a real workbench, not only a static link:

- `id="sparql-explorer"` section with named graph selector, query recipe selector, editable SPARQL textarea, result-format display, live query link, refresh, and copy controls.
- SELECT links use `format=text%2Fx-html%2Btr`.
- DESCRIBE and CONSTRUCT links use `format=text%2Fx-html-nice-turtle`.
- Live query URLs are built with `encodeURIComponent(query)`.
- Attribution cards include source material, companion files, skills used, generation environment, Linked Data runtime, named graphs, resolver pattern, and extraction provenance.
- **SPARQL textarea escape gate** — grep the generated HTML for `\\\\n` (literal backslash-n) inside `queryFor`/`qf` function bodies. A match means the SELECT return was double-escaped and the query will display raw `\n` characters instead of newlines. If found, fix the escaping (JS strings use `\n` for newline, not `\\n`) before delivering.
- **SPARQL HTML escape gate** — grep every `<pre class="sparql-code">` block for raw angle brackets around IRIs (`GRAPH <https?://` or `FROM <https?://`). A match means the GRAPH/FROM IRI will be invisible — the browser consumes `<https://...>` as an HTML tag. The fix is `html.escape()` on query text at generation time. Escaped form MUST read `GRAPH &lt;https://` (with `&lt;` and `&gt;`). Do NOT hand-patch the published HTML; fix the generator. See `preferences.ttl` Step 57 and `howto/sparql-html-escape-gate.ttl`.
- The SELECT recipe in `queryFor`/`qf` MUST use the SAMPLE-based entity type summary query, not bare `SELECT *`.

## Quick Workflow

### 1. Prepare Your RDF Data

You can provide RDF in any of these formats:

- **Turtle (.ttl)** - Preferred for readability
- **RDF/XML (.rdf)** - XML serialization
- **N-Triples (.nt)** - Line-based format
- **JSON-LD (.jsonld)** - JSON serialization
- **SPARQL Results** - JSON or XML results from queries

See `references/rdf-formats.md` for format specifications and examples.

### 2. Define Infographic Parameters

Provide or derive the following from your RDF data:

```
[MAIN_TITLE]           → Primary page title/branding
[TAGLINE]              → Value proposition/main message
[COMPANY_NAME]         → Organization name
[COMPANY_LOGO]         → Company logo URL or data URI
[ENTITY_TYPES]         → Key entity classifications (derived from rdf:type)
[KEY_ACRONYMS]         → Terms to expand on first mention
[PRIMARY_SOLUTIONS]    → Main products/services to highlight
[DOMAIN_KEYWORDS]      → SEO keywords (derived from data)
[COLOR_PALETTE]        → Primary color scheme (optional; defaults provided)
```

### 3. Locate Prior Working Examples

Before generating KG Explorer JavaScript, identify the output folder(s) where prior HTML infographics exist:

- If the user specified an output path, use it.
- If uncertain, ask: "Where are prior HTML infographic outputs saved? Provide the folder path (or a list of folders) so I can find working KG Explorer implementations."
- List the folder contents and grep for files containing `kg-explorer`, `d3.forceSimulation`, or `renderKG` to identify candidates.
- Present a sampling of up to 5 working examples found across the folder(s), showing filename, size, and a brief note on which KG Explorer features each implements (e.g., drag pinning, filter re-render, advanced sliders, zoom isolation).
- Reuse the D3.js patterns from these examples rather than generating from scratch.

### 4. Generate the HTML Infographic

⛔ **PRE-BUILD CHECK**: Before writing HTML, re-read the "Harness Contract" (14-point checklist at the top of this skill) and the "Validation Checklist" in the "Quality Checklist" section. Confirm every clause: RDF source of truth, shared stem, resolver-backed links, POSH + JSON-LD with `"@language": "en"` in `@context`, floating nav (collapsed default), theme toggle, KG Explorer (Basic + Advanced), attribution footer, MD parity, open-tab link behavior, 0-failure delivery gate. Build to pass — do not retro-fit.

Pass the RDF data and parameters to generate a complete, single-file HTML document with:

- Modern, responsive design with glassmorphism effects
- Floating, draggable, resizable navigation panel
- Scroll-triggered animations using Intersection Observer API
- Interactive FAQ accordion with smooth transitions
- Section anchors with stable URL fragment identifiers and copy-to-clipboard functionality
- Entity linking to external URIs
- Comprehensive metadata (JSON-LD, microdata, Open Graph)
- Professional typography and color schemes

### 5. Generate a Markdown Companion (Optional)

⛔ **PRE-BUILD CHECK**: Before writing Markdown, re-read the full MD companion requirements in this section and the "Markdown companion parity" clause in the Harness Contract. Confirm: same filename stem as HTML with `.md` extension, saved in same folder, resolver-backed links for FAQ/glossary/HowTo/People/Organizations/SoftwareApplication entities, related link block pointing to companion RDF and HTML, fenced `sparql` code blocks with live query links, structural parity with HTML narrative.

When the user asks for Markdown, a Markdown variant, a `.md` companion, or a text-first companion output:

- Save the Markdown file in the **same folder as the HTML file**.
- Use the same slug/model/version stem as the HTML file, changing only the extension to `.md`.
  - Stem pattern: `{descriptive-slug}-{llm-id}-{n}`.
  - Example HTML: `x-kidehen-knowledge-base-update-thread-gpt5-chat-1.html`
  - Markdown companion: `x-kidehen-knowledge-base-update-thread-gpt5-chat-1.md`
- Link back to the HTML file with a relative link.
- Link to the associated RDF file with the same relative path used by the HTML `rel="related"` link.
- Preserve the RDF entity-linking contract: FAQ questions/answers, glossary terms/definitions, HowTo section and step headings, article/person/organization/media entities, and other key entities must link through the configured resolver using their RDF IRIs.
- The HTML HowTo section MUST be derived from the RDF's `schema:HowTo` and `schema:HowToStep` entities, not independently authored. The number of steps, step names, step positions, and step body text must match the RDF exactly. Treat every visible HowTo step label exactly like a visible FAQ question: if the RDF contains `schema:HowToStep` entities, the step heading/label in HTML and Markdown MUST be an anchor to that step entity's RDF IRI through the configured resolver.
- Treat every visible SPARQL query heading exactly like a visible FAQ question: if the RDF contains `schema:SoftwareSourceCode` with `schema:programmingLanguage "SPARQL"`, the heading/title in HTML and Markdown MUST be an anchor to that query entity's RDF IRI through the configured resolver.
- Do not use raw source URLs for semantic entity links. Visible semantic entity links, including DBpedia/Wikidata IRIs selected as RDF entity identifiers, should route through the configured resolver unless the user explicitly asks for direct LOD links.
- Include media references when they exist in the RDF:
  - Images: embed with Markdown image syntax using the image content URL, and wrap or caption with a resolver link to the image object's RDF IRI.
  - Video: embed with an HTML `<video controls>` block because portable Markdown has no native video syntax. Use the video `contentUrl` as `<source src="..." type="video/mp4">` when available, include `poster="..."` from `schema:thumbnailUrl` when available, and provide a resolver link to the `schema:VideoObject` IRI.
  - Audio: embed with an HTML `<audio controls>` block when `schema:contentUrl` exists, and provide a resolver link to the `schema:AudioObject` IRI.
- Markdown does not need interactive navigation, JavaScript, dark mode, or visual effects, but it must remain structurally parallel to the HTML companion: title, overview, core entities, document links, FAQ, glossary, HowTo, sources, and provenance where applicable.

### SPARQL Query Sections

⛔ **PRE-BUILD CHECK**: Before writing SPARQL accordions, re-read this section. Confirm: each query rendered as `<details>`/`<summary>` accordion, summary title linked to query entity via resolver, "Run live query" link with URIBurner default endpoint, query body preserved verbatim (no summarization), `encodeURIComponent` for live links, no `http://example.org/` live links. Markdown mirrors with resolver-backed headings, live links, and fenced `sparql` blocks.

When RDF or source content includes SPARQL examples, query families, endpoint demos, or reporting recipes:

- Preserve the query body verbatim apart from safe HTML escaping. Do not replace it with a summary.
- Render each query in HTML as a `<details>`/`<summary>` accordion so long queries do not dominate the page.
- The summary title MUST link to the query entity through the configured resolver pattern.
- Include a visible "Run live query" link for every SPARQL query. **URIBurner (`https://linkeddata.uriburner.com/sparql`) is the default endpoint** when the source document does not specify one. Construct the URL with `encodeURIComponent(query)` using `?default-graph-uri=&query={encoded}&format={format-param}&timeout=0&debug=on&run=+Run+Query+`. The `format` parameter MUST be query-type-specific: `text%2Fx-html%2Btr` (`text/x-html+tr`) for SELECT queries; `text%2Fx-html-nice-turtle` for DESCRIBE and CONSTRUCT queries. If the query uses a placeholder namespace (e.g., `PREFIX ex: <http://example.org/>`), remap it to a resolver-backed namespace in the generated RDF so the query targets the knowledge graph loaded into the URIBurner named graph. Do NOT ship live links with `http://example.org/` — it is a non-resolvable placeholder.
- If the query contains placeholders, preserve them visibly and add nearby copy indicating the live link opens with placeholders retained for editing.
- Link the query card/chips to the endpoint/service entity and the main concept being queried when those IRIs exist in RDF.
- In Markdown, mirror the same structure with a resolver-backed heading, a live query link, and a fenced `sparql` code block.

## Core Architecture

### Document Structure

The generated HTML follows this narrative flow:

1. **Hero Section** - Eye-catching introduction with gradient backgrounds
2. **Problem-Solution Overview** - Cards contrasting the challenge and approach
3. **Core Technology/Features** - Icon-driven grid layout with descriptions
4. **Available Tools/Components** - Entity types presented as interactive cards
5. **Implementation Strategy** - Visual timeline or connected steps
6. **Challenges & Considerations** - Risk management and edge cases
7. **FAQ Accordion** - Common questions with smooth expand/collapse
8. **Glossary/Definitions** - Interactive entity index with external links
9. **Related Resources** - Links to source data and documentation
10. **Footer** - Attribution, copyright, and deployment information

### Visual Design Principles

**Color Scheme**: Professional, harmonious palette with:
- Primary: Indigo/slate gradients for headers
- Accent: Vibrant cyan for CTAs and highlights
- Neutral: White/gray backgrounds for readability
- Soft, layered shadows for depth

**Typography**: 
- Headers: Bold Poppins family (wght 600-800)
- Body: Regular Inter family, 16-18px base size
- Code: Monospace with syntax highlighting

**Layout & Spacing**:
- Generous whitespace between sections
- Card-based layouts with 2rem padding
- Responsive grid (1 column mobile, 2-3 columns desktop)
- Cubic-bezier animations (0.16, 1, 0.3, 1) for smooth transitions

**Advanced Effects**:
- Glassmorphism: Navigation panel with `backdrop-filter: blur(30px)`
- Hover Effects: Smooth `transform: translateY(-8px)` on cards with scale on buttons
- Animations: Fade-in and slide-up on scroll using Intersection Observer
- Text Contrast: Explicit white text on gradient backgrounds with proper opacity
- Nav Toggle: Expand/collapse button in the header bar with draggable behavior

### Navigation Control Best Practices

⛔ **PRE-BUILD CHECK**: Before writing the nav panel HTML/CSS/JS, re-read the full "Navigation Control Best Practices" section and the "Navigation Control" and "localStorage Correctness" items in the Validation Checklist. Confirm: collapse-to-header-bar pattern, always-visible header, toggle button (+/−) with aria-label, links hidden when collapsed (`max-height:0`), draggable by header bar, resizable, starts collapsed by default, no pin marker, no separate close/restore elements, inactivity fade after 2 minutes with reactivation marker. JS: IIFE for drag + toggle + inactivity fade; separate IIFE for fade timer; localStorage write only when expanded, stale-state recovery, page-specific key.

**Pattern**: Collapse-to-header-bar — the panel is always visible as a compact header. A toggle button collapses/expands the link list. No pin marker, no separate close/restore buttons.

**Inactivity fade**: After 2 minutes of user inactivity (no `mousemove`, `keydown`, `scroll`, `click`, or `touchstart`), the nav panel fades out via `opacity: 0` + `pointer-events: none`. A small reactivation marker (☰ button, same `top`/`right` position as the nav, `z-index` one above) becomes visible. Clicking the marker or any user activity resets the 2-minute timer and restores the nav. The marker is created dynamically in JS, styled via an injected `<style>` block, and requires `transition: opacity 0.8s ease` on `#fnav`.

**Header bar**:
- Always visible, positioned fixed (top-left or top-right)
- Contains a title/icon and a toggle button (− / +)
- Draggable by the header bar on desktop
- Default page-load state is collapsed unless the user explicitly requests otherwise. The first visible state should be the compact header bar, with the toggle showing `+` and an "Expand navigation" label.

**Collapsed state**:
- Only the header bar is shown
- Toggle button shows `+` with title "Expand"
- Links are hidden (`display: none` or `max-height: 0`)

**Expanded state**:
- Header bar stays visible
- Toggle button shows `−` with title "Collapse"
- Link list appears below the header

**JavaScript**: Two IIFEs — (1) drag + collapse toggle with localStorage persistence; (2) inactivity fade timer (2-minute `setTimeout`, reset on any user activity) that fades the nav and shows a dynamically created reactivation marker. No separate close/restore/pin elements.

### Hero Section Best Practices

**Text Visibility**:
- Explicit `color: white` for h1 and h2 elements
- Tagline color: `rgba(255, 255, 255, 0.95)` for high contrast
- Highlight elements: Semi-transparent white background with white border-bottom

**Animations**:
- Title: `slideUpFade 1s ease-out`
- Tagline: `slideUpFade 1s ease-out 0.2s backwards`
- Buttons: `slideUpFade 1s ease-out 0.4s backwards`
- Staggered timing for visual flow

### Scrollbar Styling

Styled scrollbars in navigation panel:
- Width: 8px (visible but non-intrusive)
- Track: Gradient background matching theme
- Thumb: Gradient slider with shadow effects
- Hover: Enhanced shadow on interaction

See `references/design-patterns.md` for detailed design system guidelines.

### Interactive Components

#### Floating Navigation Panel
- Draggable by the header bar
- Always-visible header with title and collapse toggle (− / +)
- Collapsed: header bar only. Expanded: header + link list
- Contains navigation to all entity types and main sections
- No pin marker, no separate close/restore buttons
- Inactivity fade: nav fades after 2 minutes; reactivation marker (☰) appears at same position
- JavaScript: single IIFE with drag + toggle behavior

#### Scroll-Triggered Animations
- Sections fade in and slide up as they enter viewport
- Implemented via Intersection Observer API for performance
- Staggered animation timing for visual flow

#### Section Anchors and URL Fragment Identifiers
- **Every section/subsection heading MUST carry a stable, unique HTML `id` attribute** serving as a URL-addressable fragment identifier (e.g., `<h2 id="overview">`, `<h3 id="faq-what-is-opal">`).
- Fragment IDs MUST use lowercase kebab-case: alphanumeric characters and hyphens only (no spaces, underscores, special characters, or leading digits).
- Fragment IDs MUST be stable across regenerations of the same content — derive them from the section heading text (slugified) or the RDF entity IRI local name, never from auto-incrementing counters, timestamps, or random values.
- The URL fragment MUST resolve natively: `<a href="#id">` scrolls to the correct section without JavaScript dependency (`html { scroll-behavior: smooth; }` is sufficient).
- Heading hover shows visible 🔗 icon that copies the full page URL with the fragment to clipboard.
- **Enables shareable section references** — both via the 🔗 copy mechanism and by direct URL fragment navigation (e.g., `page.html#faq-what-is-opal`).

#### Entity Linking
- First occurrence of RDF entities become hyperlinks
- Format: `https://linkeddata.uriburner.com/describe/?url={URL-encoded-IRI}`
- Applies to: FAQs, glossaries, HowTos, Articles, and all instances

#### FAQ Accordion
- Smooth expand/collapse transitions
- Rotating chevron icons
- Click to expand/collapse
- Maintains state across interactions

#### Image Lightbox
- All images are clickable
- Opens full-screen view in modal
- Zoom-in animation on open
- Close via background click or X button

### Technical Implementation

**Self-Contained File**: Single HTML file with:
- Embedded CSS (clean, organized, ~2000 lines typical)
- Embedded JavaScript (modular, well-commented)
- External libraries via CDN: Tailwind CSS, Google Fonts, Heroicons

**Metadata & SEO**:
- JSON-LD structured data for knowledge graphs
- Microdata annotations for semantic markup
- Open Graph / Twitter Cards for social sharing
- Complete `<head>` metadata with descriptions, keywords, canonical URL

**JavaScript Architecture**:
- Modular function organization
- Clear event handling without conflicts
- State management for interactive components
- Efficient DOM manipulation

See `references/technical-guide.md` for implementation details.

## Quality Checklist

Use this checklist to validate generated infographics:

### Navigation Control
- [ ] Header bar is always visible
- [ ] Toggle button collapses/expands link list
- [ ] Collapsed state shows `+`, expanded shows `−`
- [ ] Panel is draggable by the header bar
- [ ] All entity types appear in menu

### Content Structure
- [ ] All RDF entities are represented
- [ ] Acronyms expanded on first use
- [ ] Every section/subsection heading has a unique, stable HTML `id` attribute (lowercase kebab-case)
- [ ] Fragment IDs are directly addressable via URL (e.g., `page.html#section-id` scrolls to the correct section)
- [ ] Section anchors have copy-to-clipboard functionality
- [ ] Entity links point to correct external URIs
- [ ] Problem-solution framing is clear

### Interactive Elements
- [ ] FAQ accordion expands/collapses smoothly
- [ ] Scroll animations trigger at appropriate points
- [ ] Hover effects work on all interactive elements
- [ ] Mobile responsive design functions correctly
- [ ] Lightbox opens/closes smoothly

### Metadata & SEO
- [ ] JSON-LD structured data present and valid
- [ ] Microdata annotations applied to entities
- [ ] Open Graph tags set correctly
- [ ] All meta tags in `<head>`
- [ ] Heading hierarchy is proper (H1, H2, H3...)
- [ ] Alternate format links present

### Visual Design
- [ ] Glassmorphism effect visible on nav panel
- [ ] Color scheme consistent throughout
- [ ] Typography scales properly on mobile
- [ ] Cards have appropriate shadows and hover states
- [ ] Icons render correctly for all browsers
- [ ] Gradient backgrounds display smoothly

## Recent Aesthetic Enhancements (v1.1)

This version of the rdf-infographic-skill includes significant UX and visual improvements based on professional design standards:

### Navigation Panel Redesign
- **Collapse-to-Header-Bar**: Panel always shows a compact header; toggle expands/collapses the link list
- **No Pin Marker**: No pin marker or separate close/restore buttons
- **Inactivity Fade**: Nav fades to 0 opacity after 2 minutes of inactivity; a ☰ reactivation marker appears at the same position; any user activity (mousemove, keydown, scroll, click, touch) resets the timer and restores the nav
- **No Close Button**: Toggle replaces close/restore — a single button handles both states
- **JavaScript**: Two IIFEs — drag + collapse toggle (with localStorage), and inactivity fade timer with reactivation marker
- **Smooth Animations**: Cubic-bezier easing (0.16, 1, 0.3, 1) throughout

### Hero Section Fixes
- **Text Contrast**: Explicit white text on gradient backgrounds
- **Highlight Styling**: Semi-transparent white background with white border-bottom
- **Animation Stagger**: Coordinated fade-in timing for visual flow

### Scrollbar Styling
- **Gradient Scrollbar**: Matches theme colors with shadow effects
- **Better Visibility**: 8px width (visible but non-intrusive)
- **Hover Effects**: Enhanced shadow on interaction

### Typography & Colors
- **Enhanced Color Palette**: Added `--primary-light`, `--accent-warm`, `--success`, `--danger`
- **Better Font Weighting**: Poppins from 400-800 for better hierarchy
- **Improved Contrast**: All text readable on intended backgrounds

### Responsive Design
- **Mobile Optimization**: Navigation panel becomes static on mobile
- **Touch-Friendly**: Larger touch targets (36px buttons minimum)
- **Flexible Grids**: Auto-fit columns with minimum sizes

See `references/design-patterns.md` for detailed implementation guidelines.

### References

- **`references/rdf-formats.md`** - RDF format specifications, parsing examples, and conversion patterns
- **`references/design-patterns.md`** - Visual design system, component specifications, and CSS patterns
- **`references/technical-guide.md`** - JavaScript implementation details, state management, and integration patterns

### Scripts

- **`scripts/rdf-parser.py`** - Python utility for parsing RDF in multiple formats and extracting key information (entities, relationships, acronyms, keywords)
- **`scripts/validate-infographic.js`** - JavaScript validator for checking generated HTML quality against the checklist

### Assets

- **`assets/html-template.html`** - Base HTML template structure with proper semantic markup and metadata
- **`assets/css-framework.css`** - Reusable CSS components (cards, buttons, inputs, animations)
- **`assets/js-utilities.js`** - JavaScript utilities for common interactions (drag, resize, animations)

## Workflow Example

### Input

```turtle
@prefix ex: <http://example.org/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:OPAL a ex:Product ;
  rdfs:label "OPAL" ;
  rdfs:comment "OpenLink AI Layer for semantic integration" ;
  ex:hasFeature ex:RDFViewGeneration, ex:SPARQLSupport .

ex:RDFViewGeneration a ex:Feature ;
  rdfs:label "RDF View Generation" ;
  rdfs:comment "Automatically generate RDF views from relational databases" .
```

### Process

1. Parse RDF to extract entities, types, relationships
2. Derive acronyms from labels (OPAL → "OpenLink AI Layer")
3. Identify problem (manual data integration) and solution (OPAL)
4. Generate sections for each entity type
5. Create navigation from extracted types
6. Apply design system and interactions
7. Validate against quality checklist
8. Output single HTML file

### Output

A sophisticated, single-file HTML infographic with:
- Hero section showcasing OPAL
- Problem-solution overview
- Feature cards for RDF View Generation and SPARQL Support
- Interactive FAQ about configuration
- Floating navigation with all entity types
- Comprehensive metadata for SEO and social sharing

## Getting Started

1. Gather your RDF data in any supported format
2. Define or derive the infographic parameters from the RDF
3. Reference the technical guide for implementation details
4. Use the Python RDF parser script to extract entities and relationships
5. Generate the HTML infographic
6. Validate against the quality checklist
7. Deploy the self-contained HTML file

## Advanced Features

### Custom Color Schemes

Modify the CSS variables at the top of the embedded stylesheet:

```css
:root {
  --primary: #4F46E5;
  --secondary: #7C3AED;
  --accent: #06B6D4;
  --neutral-light: #F8FAFC;
  --neutral-dark: #1E293B;
}
```

### Extending Entity Linking

Modify the entity linking format to point to your own knowledge graph viewer:

```javascript
const entityLinkTemplate = "https://your-graph-viewer.com/entity?iri={encodedIRI}";
```

### Custom Navigation Items

Add domain-specific navigation sections beyond entity types:

```javascript
const customNavItems = [
  { label: "Documentation", href: "#docs" },
  { label: "API Reference", href: "#api" }
];
```

### Knowledge Graph Visualization Modes

When generating an RDF infographic that includes a knowledge graph visualization, the default KG Explorer deliverable is a combined **Basic/Advanced** graph with a runtime mode toggle. Do not make the user choose unless they explicitly ask for a smaller artifact or graph complexity/performance is unclear.

#### Basic Mode (Default)

⛔ **PRE-BUILD CHECK**: Before writing the D3.js KG Explorer code, re-read every bullet in this Basic Mode section and the "Validation Checklist" below. Confirm: multi-select filter buttons with aria-pressed, Core/Full density, search, legend, node click → resolver, drag-pin + dblclick-unpin, zoom isolation (no `svg.call(zoom)` on init, click-to-activate, click-outside-to-release), hover tooltip, edge labels with clickable hyperlinks to predicate IRIs, edge hover highlighting, predicate description mapping. Use the Programmatic Orphan-Node Gate checklist as a pre-build verification script.

**Best practice**: Before generating KG Explorer JavaScript, study prior working HTML documents in the output folder. Reuse their proven D3.js patterns for drag pinning, filter re-rendering, and slider behavior rather than generating from scratch.

Basic mode provides a lightweight, functional D3.js force-directed graph:
- Multi-select filter buttons: toggle visibility by node type (Classes, Properties, Instances) with visually obvious selected/unselected states and matching `aria-pressed` values
- Density buttons: Core and Full graph views. Default to Core + Instances when the full graph is visually busy; keep Full available for complete RDF inspection
- Search input: filter nodes by name
- Status readout showing active mode, active filters, and visible node/link counts
- Simple legend with color-coded dots
- Click any node to open its IRI in the configured resolver (URIBurner describe service)
- Drag nodes to reposition; dragged nodes MUST pin/stick at the drop destination. Double-click unpins
- Mouse wheel zoom and drag-to-pan
- **Zoom isolation (REQUIRED):** D3 zoom MUST NOT be attached to the SVG on init (`svg.call(zoom)` is forbidden at render time). Zoom activates only when the user clicks into the KG Explorer SVG, and deactivates when clicking anywhere outside `#kg-explorer`. This prevents the graph from capturing page scroll events when the user is simply scrolling the document.
  - Store zoom as `window._kgZoom`, SVG as `window._kgSvg`, and group as `window._kgG` in `renderKG`
  - On SVG click: `svg.call(window._kgZoom)` + add CSS class `kg-active` to `#kg-explorer`
  - On document click outside `#kg-explorer`: `svg.on('.zoom', null)` (removes D3 listeners) + remove `kg-active` class
  - Visual indicator: `#kg-explorer.kg-active` gets a colored border glow (accent color + box-shadow) and a brief fading hint "Click outside to release zoom"
  - In `setMode`: re-attach zoom if `kg-active` class is present after re-rendering
  - SVG cursor: `grab` by default, `grabbing` when `.kg-active` and `:active`
- Hover tooltip showing entity description
- Edge/connector labels that are clickable hyperlinks to property/type IRIs
- **Edge hover tooltip** showing predicate description with semantic meaning (e.g., "rdf:type - Indicates that a node is an instance of a class", "rdfs:subClassOf - Node is a subclass of the target class")
- Edge line highlights on hover with increased opacity and width
- Predicate descriptions mapped: `a`/`type` → rdf:type, `subClassOf` → rdfs:subClassOf, `domain` → rdfs:domain, `range` → rdfs:range, `seeAlso` → rdfs:seeAlso, `hasPart` → schema:hasPart, `author` → schema:author, `about` → schema:about

**Implementation requirements:**
- Include D3.js via CDN: `<script src="https://d3js.org/d3.v7.min.js"></script>`
- Use URIBurner resolver pattern: `https://linkeddata.uriburner.com/describe/?url={encodedIRI}`
- Node colors: Classes (orange #ea580c), Properties (blue #0ea5e9), Instances (green #059669)
- Improve graph readability with type-aware layout/positioning, collision spacing, curved edges, pill-backed labels, and lower-priority edge labels suppressed or deemphasized in dense views
- The graph SVG/canvas MUST fill the available graph pane width. For SVG, set `width: 100%`, `display: block`, an explicit height, and update `width`, `height`, and `viewBox` from the rendered container before starting or restarting the D3 simulation. Never rely on the browser's default SVG intrinsic size.
- Edge label click behavior:
  - "a" (rdf:type) → rdf:type predicate IRI
  - "domain" (rdfs:domain) → rdfs:domain predicate IRI
  - "range" (rdfs:range) → rdfs:range predicate IRI
  - Property labels → the property's own IRI
- Do NOT add a separate resolver launchpad/card grid below the KG Explorer unless the user explicitly requests one. The graph itself is the entity resolver surface; the next section should be the next narrative section.

#### Advanced Mode

⛔ **PRE-BUILD CHECK**: Before writing Advanced mode, re-read the full Advanced Mode section. Confirm: KG controls tray closed by default, fullscreen toggle, center graph button, settings gear button (no theme toggle in graph toolbar), settings panel with visible close (X), wired physics sliders (charge, link distance, enable/disable), predicate display (Icons/Labels), edge filtering with Select All/None, node filtering with chips, literal text filter, resolver preference (URIBurner/None/Custom), arrow style (Dual/Single), color-coded legend with toggle chips, and compact settings-panel layout that cannot stretch controls into oversized cards/circles. Every slider and toggle MUST update the D3 simulation via wired event listeners.

Advanced mode provides a full-featured visualization with settings panel, inspired by OSDS_extension/graph_gen.js:

**Visual features:**
- Uses the page-level dark/light theme state from the floating navigation panel. Do not add a second graph-specific theme toggle
- Refined graph surface with soft contrast, type-aware clustering, curved relationships, readable label backing, and restrained edge opacity
- Arrow markers on edges indicating relationship direction
- Node type icons: 👤 person, 🏢 organization, 📍 place, 💭 concept, 📅 event, 📝 literal, 🔗 resource
- Color-coded node sizes based on connectivity/importance
- Backdrop blur tooltip styling for both nodes and edges
- Edge hover tooltips showing predicate semantic descriptions
- Edge highlighting on hover

**Control toolbar (top-right):**
- Fullscreen toggle button
- Center graph button  
- Settings gear button (opens settings panel)
- Controls tray is closed by default on page load. The KG header shows only a compact Controls button and node/link badge until the user opens the tray. Do not render the filter/search/settings toolbar open by default.

> **Note:** Do NOT include a theme toggle in the graph toolbar. The page already has a theme toggle in the navigation panel (top-left). Duplicate theme controls are redundant.

**Settings panel (slides from right):**
- Must include an obvious close control (`X`) in the panel header that hides the settings panel, updates the settings button `aria-expanded` state, and returns focus to the settings button.
- Must use a compact, bounded layout: scalar controls (charge, distance, search, display mode, resolver, arrow style, literal toggle) occupy a dense top control area; predicate and node filters occupy separate lower cards/rows; Clear filters and close actions stay in a compact footer/header action area. Do not use unconstrained `auto-fit` grids that allow buttons, selects, or action controls to stretch into oversized circular or card-like elements.
- **Physics Simulation**: Charge strength slider (-1200 to -50), Link distance slider (40-320px), Enable/disable physics toggle
  > **Critical:** These controls MUST be wired to update the D3 force simulation in real-time. Use event listeners on the input elements to call `simulation.force("charge").strength(value)` and `simulation.force("link").distance(value)`, then `simulation.alpha(0.3).restart()` to apply changes.
- **Predicate Display**: Radio option for "Icons" vs "Labels"
- **Edge Filtering**: Checkbox list of all predicates plus Select All/Deselect All controls. These controls MUST mutate the same active predicate set used by graph rendering, update checkbox state, update count/state feedback, and re-render immediately.
- **Node Filtering**: Chips for each node type (person, organization, place, concept, event, literal, resource), Select All/Deselect All where the node-type set is broad enough to need bulk actions. Chips must have clear selected/unselected visuals and matching `aria-pressed` values.
- **Literal Text Filtering**: Text input to show only literal relationships containing specified text
- **Resolver Preference**: Options for "None", "URIBurner" (https://linkeddata.uriburner.com/describe/?url={uri}), or "Custom" with pattern input
- **Arrow Style**: "Dual arrows" (render every triple) vs "Single arrow" (merge mutual predicates)
- **Color-coded Legend**: Dynamic legend showing node type colors with toggle chips

**Interaction:**
- Mouse wheel zoom (0.2x to 4x scale extent) — follows the same zoom isolation rules as Basic mode: click-to-activate, click-outside-to-release
- Drag background to pan
- Click node to open IRI in resolver
- **Click edge label to open predicate IRI in resolver** — the click handler MUST resolve edge labels using this mapping:
  - `"a"` → `http://www.w3.org/1999/02/22-rdf-syntax-ns#type`
  - `"domain"` → `http://www.w3.org/2000/01/rdf-schema#domain`
  - `"range"` → `http://www.w3.org/2000/01/rdf-schema#range`
  - `"subClassOf"` → `http://www.w3.org/2000/01/rdf-schema#subClassOf`
  - `"seeAlso"` → `http://www.w3.org/2000/01/rdf-schema#seeAlso`
  - Other labels → `{document-baseIRI}{label}` (hash-based relative IRI)
- Drag nodes to reposition
- Dragged nodes MUST pin/stick at their drop destination; double-click to pin/unpin node
- Local storage for preferences where useful (physics settings, resolver preference, arrow style). Page theme belongs to the navigation panel theme toggle, not the graph toolbar

**Implementation reference**: See `/Users/kidehen/Documents/Management/Development/OSDS_extension/src/graph_gen.js` for complete implementation details.

#### Mode Selection

When the user requests an RDF infographic with graph visualization:

1. Default to a Basic/Advanced runtime toggle.
2. If the user explicitly asks for a lightweight graph, implement Basic only.
3. If the user explicitly asks for full controls, make Advanced the default selected mode while preserving the Basic toggle.
4. Do not include a graph-specific theme toggle in any mode.

#### ✅ POST-WRITE VERIFICATION GATE — KG Explorer (BLOCKING)

**After writing the KG Explorer HTML/CSS/JS block and before proceeding to any subsequent section**, grep the generated output for every item in this list. A missing item is a delivery blocker — fix it before continuing.

This gate exists because PRE-BUILD CHECKs operate on intent and are silently skipped under session pressure. This gate operates on evidence: the string either exists in the output or it does not.

**CSS — must exist in `<style>`:**
- `#kg-explorer.kg-active` — box-shadow/border-color rule that fires when zoom is armed

**HTML — must exist in the KG Explorer markup:**
- `id="pred-filters"` — container div that receives dynamic predicate checkboxes
- `id="literal-filter"` — text input for literal/label filtering
- `id="node-type-chips"` (or equivalent) — container for per-group node type toggle chips
- Settings panel close `<button>` containing `✕` or `×`
- `Select All` and `Deselect All` controls for both predicates **and** node types

**JavaScript — must exist as named functions or inline handlers:**
- `setPredAll` (or equivalent) — bulk-checks/unchecks all predicate checkboxes
- `toggleNodeType` (or equivalent) — toggles a single node type chip on/off and re-renders
- `setNodeTypeAll` (or equivalent) — bulk-selects/deselects all node type chips
- `aria-pressed` — every node type chip must carry this attribute and update it on toggle
- `classList.add('kg-active')` — zoom-arm handler adds class to `#kg-explorer`
- `classList.remove('kg-active')` — zoom-release handler removes class from `#kg-explorer`
- Dynamic predicate checkbox population — reads unique predicates from link data and inserts `<input type="checkbox">` elements into `#pred-filters`
- Dynamic node-type chip population — reads unique groups from node data and inserts chips into the node-type container, each styled with the group colour
- `simulation.force` wired to slider inputs — physics sliders must call `simulation.force("charge").strength(...)` or equivalent and `simulation.alpha(0.3).restart()`

**Verification method**: Run the following grep against the generated HTML file; every pattern must return at least one match:
```
grep -c "kg-explorer.kg-active" file.html        # must be ≥ 1
grep -c "pred-filters" file.html                  # must be ≥ 2 (HTML + JS)
grep -c "literal-filter" file.html                # must be ≥ 2 (HTML + JS)
grep -c "setPredAll\|Select All" file.html        # must be ≥ 2
grep -c "node-type-chips\|toggleNodeType" file.html # must be ≥ 2 (HTML + JS)
grep -c "setNodeTypeAll" file.html               # must be ≥ 2 (definition + call)
grep -c "aria-pressed" file.html                  # must be ≥ 2 (initial HTML + JS update)
grep -c "kg-active" file.html                     # must be ≥ 3 (CSS + add + remove)
grep -c "\.force(" file.html                      # must be ≥ 1 (matches _sim.force or simulation.force)
```

**GATE: 0 failures required.** Do not present or link the file if any grep returns 0.

## Constructing kgData from RDF (CRITICAL)

⛔ **PRE-BUILD CHECK**: Before embedding kgData in HTML, re-read the "Validation Checklist" and "Programmatic Orphan-Node Gate" below. Confirm: all RDF entities represented as nodes, all triples as links, 0 orphan nodes in both full and core datasets, 0 orphan nodes in default rendered state. Build the extraction script (Python/rdflib) first, run it, verify 0 orphans, THEN embed in HTML. Never manually type kgData.

When generating an HTML infographic with a D3.js knowledge graph visualization, you MUST derive the `kgData` object from the RDF data - do NOT manually type out nodes and links. This ensures the graph accurately represents the RDF.

For `file://` reliability, it is acceptable to embed a precomputed `kgData` object in the HTML, but it MUST be generated from the companion RDF artifact at generation time. Include a concise graph note such as "Graph data embedded from companion RDF at generation time" when live RDF parsing is not used.

The graph dataset MUST include:
- Instance nodes for document entities and domain entities
- Class nodes from `rdf:type`, schema.org, PROV, RDF, RDFS, or local ontology usage
- Property nodes or predicate metadata for edge labels and filter/legend surfaces
- Resolver-backed IRIs for every node and every edge predicate. Class/property nodes that use vocabulary IRIs such as `schema:Person`, `prov:wasGeneratedBy`, or `rdf:type` still open through the configured resolver unless the user explicitly asks for direct LOD links.

### Option 1: Automatic RDF-to-D3 Parser

Include a JavaScript function that parses the RDF and builds kgData:

```javascript
// RDF data embedded in HTML (from the TTL)
const rdfData = `
:liverpoolFC a :FootballTeam .
:arneSlot a :FootballManager ; :oversaw :liverpoolFC .
:virgilVanDijk a schema:Person ; :playsFor :liverpoolFC .
`;

// Parse RDF to extract nodes and links
function parseRDFToGraph(rdfText, baseIRI) {
    const nodes = new Map();
    const links = [];
    const triples = rdfText.split(' .\n').filter(t => t.trim());
    
    triples.forEach(triple => {
        // Extract subject, predicate, object
        const match = triple.match(/^:(\w+)\s+(\w+):(\w+)\s+/);
        if (!match) return;
        
        const [, subject, predNS, predicate] = match;
        
        // Add subject as node if not exists
        if (!nodes.has(subject)) {
            const isClass = predicate === 'Class' || predicate === 'Property';
            nodes.set(subject, { 
                id: subject, 
                label: subject, 
                type: isClass ? (predicate === 'Class' ? 'class' : 'property') : 'instance',
                desc: `RDF entity: ${subject}`
            });
        }
        
        // Add object as node if not exists
        const obj = `${predNS}:${predicate}`;
        if (!nodes.has(obj)) {
            nodes.set(obj, { 
                id: obj, 
                label: predicate, 
                type: 'instance',
                desc: `RDF entity: ${predicate}`
            });
        }
        
        // Add link
        links.push({ source: subject, target: obj, label: predicate });
    });
    
    return { nodes: Array.from(nodes.values()), links };
}

// Build kgData from the parsed graph
const kgData = parseRDFToGraph(rdfData, BASE_IRI);
```

### Option 2: Embedded Reference Data

Include the key RDF entities as reference data in the HTML that can be used to construct kgData:

```javascript
// Reference data extracted from RDF - include all key entities
const rdfEntities = {
    classes: [
        { id: "FootballTeam", label: "FootballTeam", desc: "Professional football club" },
        { id: "FootballManager", label: "FootballManager", desc: "Manager of a football team" },
        { id: "SeasonAnalysis", label: "SeasonAnalysis", desc: "Analysis of season performance" },
        { id: "PlayerLoad", label: "PlayerLoad", desc: "Analysis of player workload" }
    ],
    instances: [
        { id: "liverpoolFC", label: "Liverpool FC", desc: "Premier League football club", type: "team" },
        { id: "arneSlot", label: "Arne Slot", desc: "Liverpool manager", type: "manager" },
        { id: "seasonAnalysis", label: "Season Analysis", desc: "26-point regression", type: "analysis" },
        { id: "playerLoad", label: "Player Load", desc: "70,166 total mins", type: "data" },
        { id: "virgilVanDijk", label: "Van Dijk", desc: "5592 mins, 50x90s", type: "player" },
        // ... all other entities from RDF
    ],
    relationships: [
        { source: "liverpoolFC", target: "FootballTeam", label: "a" },
        { source: "arneSlot", target: "FootballManager", label: "a" },
        { source: "arneSlot", target: "liverpoolFC", label: "oversaw" },
        { source: "virgilVanDijk", target: "liverpoolFC", label: "playsFor" },
        { source: "virgilVanDijk", target: "playerLoad", label: "hasLoad" },
        // ... all other relationships from RDF
    ]
};

// Build kgData from reference data
const kgData = {
    nodes: [
        ...rdfEntities.classes.map(c => ({ ...c, type: 'class' })),
        ...rdfEntities.instances.map(i => ({ ...i, type: 'instance' }))
    ],
    links: rdfEntities.relationships
};
```

### Key Requirements

1. **All RDF entities MUST be represented** - Every subject/object in the RDF should appear as a node
2. **All RDF triples MUST be links** - Every predicate creates a link between subject and object
3. **No orphaned nodes** - Every node must have at least one incoming or outgoing link
4. **Type classification** - Use `type: 'class'`, `type: 'property'`, or `type: 'instance'`
5. **Bidirectional for relevant relationships** - Players connect to both club (`playsFor`) and load data (`hasLoad`)

### Validation Checklist

Before finalizing the HTML, verify:
- [ ] All classes from RDF appear as class-type nodes
- [ ] All instances from RDF appear as instance-type nodes  
- [ ] All predicates from RDF appear as links
- [ ] No nodes exist that are not in the RDF
- [ ] No links exist that are not in the RDF
- [ ] Every node has at least one connection (no orphans)
- [ ] Player/Person entities connect to their organization AND relevant data entities

### Programmatic Orphan-Node Gate

When the HTML embeds a `kgData` object or equivalent graph payload, the final validation MUST programmatically inspect it before delivery:

1. Parse the embedded graph payload from the saved HTML.
2. Build the set of node IDs.
3. Build the incident set from every link whose `source` and `target` both exist in the node set.
4. Fail delivery if any node is absent from the incident set.
5. Emulate the default KG Explorer render state (default mode, default density, default Classes/Properties/Instances filters, default predicate filters, and default search/literal filters) and fail delivery if any rendered node has no rendered incoming or outgoing link.
6. If the graph renderer prunes nodes after filter/density changes, ensure the pruning occurs after link filtering so no visible orphan nodes remain.

Record the validation result in the work log or final answer, for example: `KG data check: 177 nodes / 312 links, global orphan nodes: 0, default rendered orphan nodes: 0`.

## Performance Considerations

- **Intersection Observer API**: Used instead of scroll events for optimal performance
- **CSS Animations**: Hardware-accelerated transforms for smooth 60fps
- **Lazy Loading**: Images and resources load on demand
- **Minimal JavaScript**: Core functionality uses vanilla JS, no frameworks required
- **CDN Delivery**: Tailwind CSS and Google Fonts loaded from CDN for caching

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari 14+, Chrome Android 90+)

## Next Steps

1. **To generate an infographic**: Provide RDF data and desired title/tagline
2. **To customize design**: See `references/design-patterns.md`
3. **To parse complex RDF**: Use `scripts/rdf-parser.py` utility
4. **To extend functionality**: Reference `references/technical-guide.md`

---

## RDF Document Relationship

### Filename Stem Rule

Every generated HTML/RDF/Markdown set MUST use one shared filename stem:

`{descriptive-slug}-{llm-id}-{n}`

- `{descriptive-slug}` is a concise lowercase hyphenated summary of the source title or topic.
- `{llm-id}` identifies the underlying generating LLM or LLM interface, normalized to lowercase hyphen form, for example `gpt5-chat`, `gpt5-mini`, `claude-sonnet`, or `gemini-pro`.
- Infer `{llm-id}` from the active model or output root when available, e.g., `GPT5-Chat-Generated` -> `gpt5-chat`; if uncertain, ask before saving.
- `{n}` starts at `1` and increments only when the exact target filename already exists.
- HTML, RDF, and Markdown companions must keep the same stem and differ only by extension and directory, for example:
  - HTML: `../webpages/ai-visibility-needs-signal-graph-andrea-volpini-gpt5-chat-1.html`
  - RDF: `../rdf/ai-visibility-needs-signal-graph-andrea-volpini-gpt5-chat-1.ttl`
  - Markdown: `../webpages/ai-visibility-needs-signal-graph-andrea-volpini-gpt5-chat-1.md`

Every generated HTML infographic **MUST** declare its connection to its associated RDF source document using two mechanisms:

**POSH (Plain Old Semantic HTML):**
```html
<link rel="related" href="filename.jsonld" type="application/ld+json">
```
Use relative paths. Support `.jsonld`, `.ttl`, `.rdf`, and `.nt` extensions depending on the RDF serialization produced.

When a Markdown companion exists, the HTML page **MUST** also advertise it as an alternate representation:

```html
<link rel="alternate" href="example.md" type="text/markdown" title="Markdown representation">
```

**Embedded JSON-LD:**
```json
"relatedLink": {"@id": "filename.jsonld"}
```
Include `schema:relatedLink` in the JSON-LD structured-data island inside the HTML. Value must be a relative path expressed as an IRI using `@id` — not a plain string literal.

When a Markdown companion exists, the embedded JSON-LD **MUST** also describe the Markdown file as an alternate encoding/representation of the same `schema:WebPage` or `schema:CreativeWork`:

```json
{
  "@type": "schema:MediaObject",
  "encodingFormat": "text/markdown",
  "contentUrl": {"@id": "example.md"},
  "name": "Markdown representation"
}
```

Attach this object through `schema:encoding` or an equivalent schema.org relationship that clearly denotes the Markdown file as an alternate representation of the HTML document. Use relative `@id` values, never plain string URLs.

Both links must be relative — never use `file://` or absolute paths — so the relationship holds when the directory is moved or shared.

Every generated Markdown companion **MUST** declare its connection to the same associated RDF source document using a relative Markdown link near the top of the file:

```markdown
Associated RDF: [example.ttl](../rdf/example.ttl)
```

If the Markdown was generated as a variant of an HTML companion, also include:

```markdown
Source HTML: [example.html](example.html)
```

---

## Skills Attribution

Every generated HTML infographic **MUST** include a skills attribution line in the footer sources section, linking to the GitHub repository for each skill used to produce the output:

```html
<!-- Single skill -->
<p style="margin-top:14px;color:var(--muted);font-size:0.86rem">
  Generated using <a href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/rdf-infographic-skill">rdf-infographic-skill</a>
</p>

<!-- Multiple skills -->
<p style="margin-top:14px;color:var(--muted);font-size:0.86rem">
  Generated using
  <a href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator">kg-generator</a>,
  <a href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/rdf-infographic-skill">rdf-infographic-skill</a>
</p>
```

The GitHub URL pattern for all skills is: `https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/{skill-name}`. Distinguish singular vs. plural phrasing ("skill" vs. "skills") based on the number of skills used.

Correspondingly, the embedded JSON-LD `WebPage` node MUST include a `prov:wasGeneratedBy` reference to a `schema:SoftwareApplication` entity for each skill, using the canonical skill IRI with `#this` appended (e.g., `<https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator#this>`), with `schema:name`, `schema:url` (GitHub without `#this`), and `schema:description`. Declare the `prov:` context prefix as `http://www.w3.org/ns/prov#`.

### Generation Environment Attribution

Every generated HTML infographic footer sources/attribution section MUST also include a concise, human-visible generation environment line with each generation environment item hyperlinked when it has a known IRI or URL. This line states:

- The inferred LLM or LLM interface used for generation, matching the `{llm-id}` in the filename stem, for example `gpt5-chat`, linked to its canonical product URL (see canonical URL table below).
- The generation client/environment when known, for example `Cowork Desktop`, linked to its canonical product URL.
- The source delivery host/server when it is known from the source URL or HTTP headers, for example `content.martechday.com via Amazon S3/CloudFront`, linked to its source host URL.
- The Linked Data resolver/server platform used for entity hyperlinks. When URIBurner is used, identify and hyperlink it as `URIBurner` using its canonical URL `https://linkeddata.uriburner.com/`, and state that it is a Virtuoso-backed Linked Data resolver/server platform.

The RDF and embedded JSON-LD provenance SHOULD mirror this visible attribution using named entities such as `:gpt5ChatInterface`, `:codexDesktopEnvironment`, `:sourceDeliveryServer`, `:uriBurnerResolver`, and `:virtuosoServer` where applicable. These entities MUST NOT use `file:` IRIs. If the server/provider cannot be determined, state `source delivery server not determined` in the human-visible attribution instead of omitting the field.

#### Provenance Card Canonical Link Rule

**CRITICAL**: The provenance/attribution section exists to credit real products and tools. Items in provenance cards that represent known products, platforms, or tools with stable URLs MUST link the **visible item label itself** to the canonical homepage or repository URL — NOT to session-generated URIBurner resolver URLs built from document-local fragment IRIs. Do not use generic labels such as `Visit`, `Learn more`, or `Explore` for attribution links. For example, link `URIBurner`, `OpenLink Virtuoso`, `D3.js`, `Python`, and skill names directly.

Canonical URLs for standard provenance items:

| Item | Canonical URL |
|------|--------------|
| Claude / Claude Sonnet | `https://www.anthropic.com/claude` |
| Cowork Desktop Environment | `https://claude.ai/download` |
| OpenLink Virtuoso Server | `https://virtuoso.openlinksw.com/` |
| URIBurner | `https://linkeddata.uriburner.com/` |
| KG Generator Skill | `https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator` |
| RDF Infographic Skill | `https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/rdf-infographic-skill` |
| OpenLink Software skills (general) | `https://github.com/OpenLinkSoftware/ai-agent-skills` |

For products or tools not in this table, use their official homepage. If no canonical URL can be determined, omit the link rather than substituting a resolver URL.

The resolver (`https://linkeddata.uriburner.com/describe/?url=...`) is for **semantic entities** defined in the document's knowledge graph (persons, concepts, organizations, FAQ items, glossary terms, etc.) — not for product attribution.

#### Skill SoftwareApplication Denotation

When modeling a skill used to generate the artifact as `schema:SoftwareApplication`, the RDF subject IRI MUST be the canonical skill repository URL with `#this` appended, for example:

- `https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator#this`
- `https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/rdf-infographic-skill#this`

Use `schema:url` for the bare repository page without `#this`. Do not mint document-local hash IRIs such as `{source-url}#rdf-infographic-skill` for these skill software entities.

### SoftwareApplication IRI Denotation Rule

For every `schema:SoftwareApplication` entity introduced or normalized during RDF/HTML/Markdown generation, select the subject IRI using this priority order:

1. **DBpedia first** — if a confident DBpedia resource exists, use the fully expanded DBpedia IRI as the software application's primary denotation IRI, for example `http://dbpedia.org/resource/Google_Docs`.
2. **Wikidata second** — if no confident DBpedia resource exists but a confident Wikidata entity exists, use the fully expanded Wikidata IRI, for example `http://www.wikidata.org/entity/Q...`.
3. **Homepage fallback** — if neither DBpedia nor Wikidata can be confirmed, use the official product/application home page URL with `#this` appended, for example `https://example.com/product/#this`.

When the primary IRI is not DBpedia- or Wikidata-based, add `owl:sameAs` relations to any confirmed DBpedia or Wikidata IRIs for that application. Declare `owl:` as `http://www.w3.org/2002/07/owl#` whenever `owl:sameAs` appears. Do not use a local document hash IRI for a known software application when one of the three denotation options above is available.

Visible software application names in HTML and Markdown MUST link through the configured resolver using the selected RDF IRI. The KG Explorer node for the software application MUST use the same selected IRI.

Before delivery, record or verify the chosen denotation basis for every `schema:SoftwareApplication`: DBpedia, Wikidata, or homepage `#this`. Do not fabricate DBpedia or Wikidata IRIs; if no confident match is found, use the homepage fallback and omit `owl:sameAs` unless a confident external identity is later established.

---

### Person IRI Denotation Rule

For every `schema:Person` entity introduced or normalized during RDF/HTML/Markdown generation, use the person denotation priority rule from `kg-generator`:

1. **LinkedIn profile first** — if a LinkedIn profile URL appears in the source or can be confidently matched, use `{linkedin-profile-url}#this`.
2. **X/Twitter second** — if no LinkedIn profile is found but an X/Twitter profile is confidently matched, use `{x-profile-url}#this`.
3. **Substack third** — if no LinkedIn or X/Twitter profile is found but a Substack author profile is confidently matched, use `{substack-profile-url}#this`.
4. **Other platform profile next** — use another social, author, blog, or professional profile URL with `#this` when confidently matched.
5. **Document-local fallback last** — only when no platform/profile URL can be confirmed, derive a source-grounded document hash IRI.

Add `schema:url` pointing to the bare profile URL and `schema:identifier` with the canonical profile URL. Link all confirmed platform, DBpedia, or Wikidata equivalents via `owl:sameAs`. Visible person names in HTML and Markdown MUST link through the configured resolver using the selected person RDF IRI, and KG Explorer person nodes MUST use the same selected IRI. Do not leave a visible person link on `{source-url}#person-name` when a profile URL is known.

---

### Country IRI Denotation Rule

For every `schema:Country` entity introduced or normalized during RDF/HTML/Markdown generation, select the subject IRI using this priority order:

1. **DBpedia first** — if a confident DBpedia country resource exists, use the fully expanded DBpedia IRI as the primary country denotation IRI, for example `http://dbpedia.org/resource/South_Africa`.
2. **Wikidata second** — if no confident DBpedia resource exists but a confident Wikidata country entity exists, use the fully expanded Wikidata IRI, for example `http://www.wikidata.org/entity/Q258`.
3. **Document-local fallback** — only when neither authority IRI can be confirmed, use a source-grounded document hash IRI.

When the primary country IRI is DBpedia-based and a confirmed Wikidata equivalent exists, add `owl:sameAs` to the Wikidata entity. When a primary country IRI is Wikidata-based and a DBpedia equivalent later becomes available, normalize to DBpedia or add `owl:sameAs` if preserving an existing artifact requires it. Do not use a local document hash IRI for a known country when DBpedia or Wikidata authority IRIs are available.

Visible country names in HTML and Markdown MUST link through the configured resolver using the selected country RDF IRI. The KG Explorer node for the country MUST use the same selected IRI. If the RDF includes source-specific country observations, metrics, or rows, connect those observation nodes to the selected country IRI rather than minting a competing country identity.

Before delivery, record or verify the chosen denotation basis for every `schema:Country`: DBpedia, Wikidata, or document-local fallback. Do not fabricate DBpedia or Wikidata IRIs.

---

## Footer SPARQL Button with Format Toggle

⛔ **PRE-BUILD CHECK**: Before writing the footer SPARQL button, re-read this entire section. Confirm: (a) `<a id="sparqlBtn">` anchor exists with label "Explore Knowledge Graph using SPARQL"; (b) `setSparqlFormat` / `setSparqlFmt` builds `sparqlBtn.href` using the pre-encoded canonical entity-type summary query — `SPARQL_BTN_Q_PRE + encodeURIComponent(graphIri) + SPARQL_BTN_Q_POST` — never a simplified substitute; (c) the canonical query projects `?type`, `SAMPLE(?s) AS ?sampleEntity`, `SAMPLE(?label) AS ?sampleLabel`, `COUNT(?s) AS ?entityCount`, includes `OPTIONAL { ?s rdfs:label ?label }`, uses `rdf:type` (not `a`), and has a `GRAPH <{graphIri}>` clause; (d) format parameter is `text%2Fx-html%2Btr`; (e) `sparqlBtn.href` is initialised on page load; (f) switching format tabs updates `sparqlBtn.href` with the new graph IRI.

Every HTML infographic that has a companion RDF file (Turtle and/or JSON-LD) **MUST** include a SPARQL button in the footer that lets users query the knowledge graph via URIBurner. Include format toggle tabs (RDF Turtle / JSON-LD) so users can select which RDF document to query.

### Required HTML Structure

```html
<footer>
    <div class="kg-format-tabs">
        <button class="active" id="fmtTtl" onclick="setSparqlFormat('ttl')">RDF Turtle</button>
        <button id="fmtJsonld" onclick="setSparqlFormat('jsonld')">JSON-LD</button>
    </div>
    <p style="margin-bottom:20px">
        <a id="sparqlBtn" href="...">Explore Knowledge Graph using SPARQL</a>
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

### Document IRI vs SPARQL GRAPH IRI

**Critical distinction:**

| IRI Type | Used For | Pattern |
|----------|----------|---------|
| **Document IRI** | Entity references in RDF, HTML, MD | `{source-url}#{entity}` |
| **SPARQL GRAPH IRI** | Querying the named graph in URIBurner | `https://linkeddata.uriburner.com/DAV/demos/daas/{filename}` |

- **Document IRIs** use the source URL with `#` suffix (e.g., `https://pluralistic.net/2026/05/13/vibe-governance#q1`)
- **SPARQL GRAPH IRIs** use the DAV path to the generated RDF file (e.g., `https://linkeddata.uriburner.com/DAV/demos/daas/vibe-governance-minimax_m2.5free-1.ttl`)

**Never confuse the two.** HTML entity resolver links use Document IRIs; the SPARQL query GRAPH clause uses the DAV GRAPH IRI.

---

## HTML/Markdown/RDF Pairing Requirements

Every generated HTML infographic and Markdown companion **MUST** satisfy these requirements to ensure correct entity-level linkage between visible human-readable output and the associated RDF knowledge graph.

### Resolver Link Configuration

Entities that have defined IRIs in the RDF knowledge graph (persons, concepts, organizations, FAQ questions, FAQ answers, glossary terms, glossary definitions, HowTo sections, HowTo steps, media objects, and source/document entities) **SHOULD** be hyperlinked through a designated Linked Data resolver rather than pointing directly to external source URLs. This preserves the human-readable ↔ machine-readable loop: following a resolver link exposes the entity's full structured description with provenance, cross-references, and property sets.

**Resolver selection (in priority order):**
1. **URIBurner** (default) — `https://linkeddata.uriburner.com/describe/?url={URL-encoded-IRI}`. In footer prose, describe this as `URIBurner describe links` linked to `https://linkeddata.uriburner.com/fct`, via the `{cname}/{describe}/{query}` pattern, as in `https://linkeddata.uriburner.com/describe/?url={uri}`, over RDF hash IRIs.
2. **User-designated resolver** — any alternative resolver explicitly specified by the user
3. **None** — if the user explicitly opts out, entity text is not hyperlinked and plain entity IRIs may be shown instead

```html
<!-- DEFAULT: URIBurner resolver link to KG entity -->
<a class="entity-link"
   href="https://linkeddata.uriburner.com/describe/?url=https%3A%2F%2Fwww.lassila.org%2Fpublications%2F2001%2FSciAm.pdf%23timBernersLee"
   target="_blank" rel="noopener noreferrer">Tim Berners-Lee</a>

<!-- WITH USER RESOLVER (e.g., custom describe endpoint) -->
<a class="entity-link"
   href="https://my-company.com/describe/?url=https%3A%2F%2Fwww.lassila.org%2Fpublications%2F2001%2FSciAm.pdf%23timBernersLee"
   target="_blank" rel="noopener noreferrer">Tim Berners-Lee</a>

<!-- NO RESOLVER (user opted out): plain entity IRI, no hyperlink, or inline IRI display -->
```

**Encoding rule:** `#` in entity IRIs must be encoded as `%23` exactly once in resolver `url` parameter values. `%2523` (double-encoded) is invalid.

The resolver is for entities defined **within the document's knowledge graph**, including hash-based document IRIs and external RDF IRIs selected as entity identifiers. Entities that already have dereferenceable RDF IRIs in the Linked Open Data Cloud — such as DBpedia (`http://dbpedia.org/resource/...`), Wikidata (`http://www.wikidata.org/entity/...`), and other LOD sources — still route through the configured resolver when they are visible semantic entities in the HTML/Markdown/KG Explorer. The resolver `url` parameter carries the selected RDF IRI.

### Navigation Panel Behavior

Every infographic **MUST** include a floating section navigation control that:

- **Is movable** — draggable by pointer on desktop.
- **Is resizable** — resizable by pointer drag on desktop.
- **Is collapsible** — a toggle button collapses/expands the link list (collapse-to-header-bar pattern). The header bar remains always visible. Collapsed state shows a `+` / "Expand" control; expanded state shows `−` / "Collapse".
- **Starts closed by default** — page load shows the compact collapsed header bar unless the user explicitly requested an expanded default for that artifact.
- **Is visually minimal when closed** — the collapsed panel is a compact header bar only. Do NOT leave an empty link list area or separator lines visible in the collapsed state.
- **Does not waste space** — avoid separate `#` column markers or redundant icon columns. The compact header bar already serves as the anchor affordance.

### localStorage Correctness

Navigation state persistence **MUST** handle these edge cases:

- **Never persist collapsed dimensions as open dimensions.** When saving position/size to `localStorage`, save only when the panel is in the expanded state. If the user collapses the panel and then closes the page, restoring should bring back the last *expanded* position/size — not the collapsed header-bar dimensions.
- **Recover from stale or corrupt localStorage state.** If saved position values are NaN, negative, off-screen, or from a different page version, discard them and fall back to the CSS defaults. Use a page-specific key (derived from the page URL or title) to prevent cross-page contamination.

### Validation Checklist

**GATE: 0 failures required before delivery.** Every generated HTML infographic must pass all checks. No exceptions.

- [ ] HTML parses without errors (no unclosed tags, valid attributes).
- [ ] JavaScript syntax is valid (no missing brackets, undefined references, or silent failures in the nav IIFE).
- [ ] Associated RDF document parses without errors and passes the `validate-kg-compliance.sh` audit.
- [ ] Every `schema:SoftwareApplication` uses the denotation priority rule: DBpedia IRI if confirmed, else Wikidata IRI if confirmed, else official homepage URL with `#this`; non-DBpedia/non-Wikidata software IRIs include `owl:sameAs` to confirmed DBpedia/Wikidata identities when such identities exist.
- [ ] Every `schema:Country` uses the denotation priority rule: DBpedia IRI if confirmed, else Wikidata IRI if confirmed, else source-grounded document IRI; confirmed DBpedia/Wikidata equivalents are connected with `owl:sameAs`.
- [ ] Every resolver entity hyperlink in the HTML resolves to a valid `describe/?url=` URL (no double-encoding: `%2523` is invalid; `#` must encode to `%23` exactly once).
- [ ] Every non-fragment HTML anchor (`href` not starting with `#`) has `target="_blank" rel="noopener noreferrer"`; same-page fragment navigation links do not have `target="_blank"`.
- [ ] FAQ questions, FAQ answers, glossary terms, glossary definitions, the HowTo section entity, every individual HowToStep heading/label, and other visible semantic entities are ALL hyperlinked to their KG entity IRIs via the resolver pattern.
- [ ] Every hyperlinked entity has a correct rdf:type matching its HTML role: HowToStep headings link to schema:HowToStep entities, FAQ questions link to schema:Question entities, glossary terms link to their declared type (schema:DefinedTerm or appropriate type), section titles link to schema:CreativeWork entities. No HowToStep heading links to a schema:Question or other mismatched type.
- [ ] HTML narrative content matches the companion RDF exactly: the number of HowTo steps matches the RDF's schema:HowToStep count, each step heading/label matches schema:name, and each step body matches schema:text. FAQ questions and answers match the RDF's schema:Question and schema:Answer entities. Glossary terms match the RDF's schema:DefinedTerm entities. The HTML is not independently authored — it is a rendering of the RDF data.
- [ ] Glossary terms are wrapped in a `schema:DefinedTermSet` with `schema:hasDefinedTerm` listing all term IRIs; the main article/post entity has `schema:hasPart` linking to the `DefinedTermSet`; and each `schema:DefinedTerm` carries `schema:inDefinedTermSet` pointing back to the set.
- [ ] If a HowTo section is present: a `schema:HowTo` container entity exists in the companion TTL with `schema:step` linking to every step; the main article/post entity links to the `schema:HowTo` via `schema:hasPart`; each `schema:HowToStep` has an **absolute IRI** (not hash-relative from `@prefix : <#>`) using a named prefix anchored to the source document URL (e.g., `@prefix post: <{source-url}#>`); and every HowTo step title/heading in HTML links to its `schema:HowToStep` entity IRI via the resolver pattern — never to a topically-related DBpedia, Wikidata, or other external IRI.
- [ ] If a KG Explorer is present, its graph data is derived from the companion RDF artifact; if embedded, it is explicitly derived at generation time and not manually invented.
- [ ] KG Explorer includes resolver-backed node links and resolver-backed edge predicate links using `describe/?url=`.
- [ ] KG Explorer renders RDF triple direction explicitly: every visible predicate edge has an arrowhead from subject to object, with the path endpoint offset so the arrowhead is visible outside the target node.
- [ ] KG Explorer Advanced mode includes its required control surface: fullscreen button, center button, settings button, and a settings panel with wired physics sliders/toggle, predicate display, predicate filtering, node filtering, literal filtering, resolver preference, arrow style, and legend/filter state feedback.
- [ ] KG Explorer controls tray is closed by default on page load; the default visible state is the graph surface plus compact Controls button and node/link count badge. Opening the tray reveals Basic/Advanced, Core/Full, node-type filters, search, and only Advanced-gated settings controls.
- [ ] KG Explorer settings panel includes a visible close (`X`) control that hides the panel and restores focus predictably.
- [ ] KG Explorer Advanced settings panel passes the compact-layout gate: scalar controls are bounded, predicate/node filters are grouped in separate cards/rows, Select All/Deselect All predicate controls are present and wired, and no button/select/action stretches into an oversized circular or card-like element at desktop, tablet, or mobile widths.
- [ ] KG Explorer includes Basic/Advanced modes by default, Core/Full density controls, multi-select Classes/Properties/Instances filters, clear selected/unselected filter states, visible node/link count feedback, and no blank graph when filters are enabled.
- [ ] KG Explorer node dragging pins/sticks nodes at their drop destinations, and double-click unpins.
- [ ] KG Explorer D3 zoom is focus-activated, not attached on init: no `svg.call(zoom)` at render time; zoom attaches on SVG click and detaches on outside click via `svg.on('.zoom', null)`; `#kg-explorer` shows `kg-active` visual indicator when zoom is armed
- [ ] KG Explorer render validation: the SVG/canvas fills the full graph pane width, the plotted nodes are not clipped into a narrow left strip, and the graph has visible nodes/edges distributed across the pane in the default view.
- [ ] Programmatic KG orphan-node gate has passed: global embedded graph has zero orphan nodes and default rendered graph has zero orphan nodes.
- [ ] If a Markdown companion was requested, it is saved in the same folder as the HTML file, uses the same filename stem with `.md`, links to the HTML file, links to the RDF file with a relative path, and has no non-resolver external semantic links.
- [ ] If a Markdown companion was requested, the HTML POSH metadata includes `<link rel="alternate" type="text/markdown" href="{markdown-file}">`, and the embedded JSON-LD declares the Markdown file as an alternate encoding/representation using a relative `@id`.
- [ ] Embedded JSON-LD `@context` includes `"@language": "en"` so all string literals inherit the English language tag, matching the `@en` tags in the companion Turtle file.
- [ ] If a Markdown companion was requested and RDF media entities exist, it embeds or references them: images with Markdown image syntax, videos with HTML `<video controls>`, audio with HTML `<audio controls>`, and captions/labels linked to the RDF media entity IRIs through the resolver.
- [ ] If RDF contains SPARQL `schema:SoftwareSourceCode` examples, HTML renders them as accordions with resolver-backed query headings, escaped preformatted query text, endpoint/service links, and correctly URL-encoded live query links defaulting to URIBurner; Markdown mirrors them with fenced `sparql` code blocks. No `http://example.org/` live links.
- [ ] The local RDF link (`rel="related"`) uses a relative path and the target file exists.
- [ ] Navigation panel: drag works, resize works, collapse/expand toggles correctly, localStorage read/write does not throw, stale values are recovered from gracefully.
- [ ] Skills attribution line present in footer with correct GitHub URL(s).
- [ ] Provenance/attribution links use the attributed labels themselves as anchors (for example `URIBurner`, `OpenLink Virtuoso`, `D3.js`, `rdf-infographic-skill`); no generic `Visit`/`Learn more` labels.
- [ ] Footer SPARQL button present with Turtle/JSON-LD format toggle; `<a id="sparqlBtn">` uses the canonical entity-type summary query (`SAMPLE(?s) AS ?sampleEntity`, `SAMPLE(?label) AS ?sampleLabel`, `COUNT(?s) AS ?entityCount`, `OPTIONAL { rdfs:label }`, `rdf:type` not `a`, `GRAPH <DAV/demos/daas/{filename}>` clause) — not a simplified substitute; format parameter is `text%2Fx-html%2Btr`; `sparqlBtn.href` initialised on load and updated on format-tab switch.
- [ ] Dark mode: both `html[data-theme="dark"]` and `@media (prefers-color-scheme: dark)` produce equivalent rendering; no hardcoded colors outside CSS variables.
- [ ] Dark mode CSS blocks are **not** comma-combined: `html[data-theme="dark"] { … }` and `@media (prefers-color-scheme:dark) { … }` must be two entirely separate blocks. A trailing comma after a selector followed by an `@media` rule is invalid CSS and silently fails in most browsers.
- [ ] Light/dark theme toggle is present in the **nav panel header bar** (`#fnav-header`) — not inside the collapsible `#fnav-links` section — so it is accessible whether the nav is collapsed or expanded. The button must carry `title` and `aria-label` attributes and update its icon/label to reflect the current theme state on each click.
- [ ] Every section heading (`h1`–`h4`) throughout the document carries a unique HTML `id` attribute in lowercase kebab-case.
- [ ] Fragment IDs are stable (derived from heading text slug or entity IRI local name, not from counters or timestamps).
- [ ] Each fragment ID resolves natively: `<a href="#id">` positions the section correctly without JavaScript dependency.

---

## Index Page Generation

After saving HTML infographic files into a directory, **always offer** to generate or update `index.html`, `index.css`, and `index.js` for that directory. These provide a dynamic, searchable index with grid, timeline, and table views.

**Generator**: `scripts/index.js`
**Templates**: `templates/corpus-index.css`, `templates/corpus-index.js`

```
node scripts/index.js <target-directory>
```

The index page scans all `.html` files, extracts metadata (`<title>`, `<meta>`, JSON-LD), auto-derives theme categories from keywords, and renders filterable cards. All links are local `file://` references. Confirm the directory with the user before running.

---

## Dark Mode CSS Requirements

Every generated HTML infographic MUST support both `prefers-color-scheme: dark` (system-level) and `html[data-theme="dark"]` (explicit toggle). The two must be functionally equivalent:

1. **Single dark-mode strategy** — use ONE consistent approach, not two competing blocks. Use `html[data-theme="dark"]` (explicit toggle) AND `@media (prefers-color-scheme: dark)` (system) with identical variable values. Do NOT generate a separate "dark-mode-retrofit" block with competing `!important` rules
2. **All colors via variables** — every `color`, `background`, `border-color`, and `box-shadow` must use CSS variables. Never hardcode hex values, `rgba()`, or `linear-gradient()` with literal colors. Use `var(--ink)`, `var(--muted)`, `var(--panel)`, `var(--panel-strong)`, `var(--line)`, `var(--accent)`, `var(--accent2)`, `var(--chip)`, `var(--shadow)` — all defined in `:root` for light mode and overridden in `html[data-theme="dark"]` and `@media (prefers-color-scheme: dark)`
3. **Text inherits** — `body { color: var(--ink); }` and paragraph/muted text uses `var(--muted)`. Override only on accent elements (badges, hero text, pills). Never set `color: rgba(255,255,255,...)` or `color: #fff` outside of `.hero` or badge contexts
4. **Every component class gets a dark override** — `.flow-step`, `.stack-card`, `.footer`, `.footer p`, `.source-list a`, and any element with a background must have `html[data-theme="dark"] &` rules
5. **Avoid `!important`** — use specificity, not `!important`, to manage cascading. The only exception is the body background override for dark-mode gradient compatibility
