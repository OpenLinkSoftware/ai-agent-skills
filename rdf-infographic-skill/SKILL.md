---
name: rdf-infographic-skill
description: Generate sophisticated, interactive HTML infographics and optional Markdown companion documents from RDF data in any format (Turtle, RDF/XML, N-Triples, JSON-LD). Transform knowledge graphs into visually stunning, data-driven narratives with advanced CSS effects, dynamic interactions, floating navigation, smooth animations, comprehensive metadata, and Markdown variants when requested. Use when converting RDF datasets or SPARQL results into engaging, responsive infographic pages, Markdown companions, marketing assets, documentation, or knowledge exploration artifacts.
license: MIT
---

# RDF-based HTML and Markdown Infographic Generation Skill

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

1. **RDF source of truth** — parse or generate the companion RDF first; derive semantic entities, links, and KG Explorer graph data from that RDF.
2. **Shared artifact stem** — save HTML, Markdown, and RDF with the same `{descriptive-slug}-{llm-id}-{n}` stem.
3. **Resolver-backed entity links** — visible semantic entities in HTML, Markdown, KG nodes, and KG edge predicates route through `https://linkeddata.uriburner.com/describe/?url={encodedIRI}` unless the user explicitly supplies another resolver.
4. **POSH and JSON-LD pairing** — HTML declares the companion RDF and Markdown files through `<link rel="related">`, `<link rel="alternate">`, and embedded JSON-LD.
5. **Floating navigation control** — movable, resizable, collapsible, visible in a closed compact header-bar state by default, and recoverable after stale localStorage.
6. **Page theme control** — one page-level light/dark toggle in the navigation panel, with equivalent `html[data-theme="dark"]` and `prefers-color-scheme: dark` variable values.
7. **Knowledge Graph Explorer** — Basic and Advanced modes, resolver-backed node/edge links, directed subject-to-object arrowheads, Core/Full density, multi-select Classes/Properties/Instances filters, visible selected states, node/link counts, sticky drag, double-click unpin, and no resolver launchpad/card grid unless explicitly requested.
8. **Advanced KG settings panel** — fullscreen, center, settings button, visible close (`X`), wired physics controls, predicate display, predicate filters, node filters, literal filter, resolver preference, arrow style, and clear state feedback.
9. **Attribution footer** — source material, companion files, skills used, generation environment, server/platform items where known, resolver pattern, and hyperlinked generation-environment entities.
10. **Markdown companion parity** — Markdown mirrors the HTML narrative structure and preserves resolver-backed links for FAQ, glossary, HowTo, People, Organizations, SoftwareApplication, source/document, and media entities.
11. **Authority denotation rules** — SoftwareApplication and Country entities use DBpedia/Wikidata-centered IRIs where confidently available; add `owl:sameAs` for confirmed DBpedia/Wikidata equivalents.
12. **Zero-failure delivery gate** — do not deliver until RDF parse, HTML/JS parse, resolver link audit, KG Explorer behavior checklist, nav behavior, dark mode, output path checks, and programmatic KG orphan-node checks all pass.
13. **SPARQL query presentation** — when the RDF or source content contains `schema:SoftwareSourceCode` SPARQL examples, endpoint demos, or query recipes, render them as readable accordions with resolver-backed query-entity links, fenced/preformatted query text, a visible endpoint/service link, and a correctly URL-encoded live query link when an endpoint is known. Markdown companions must include the same query headings, resolver links, live links, and fenced `sparql` code blocks.

If an input is insufficient to satisfy the harness contract, ask for the missing source, RDF, resolver, output folder, or artifact scope before generating. If an existing artifact is being repaired, preserve its RDF/HTML/MD pairing and retrofit the missing contract items rather than creating a separate one-off patch.

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

### 3. Generate the HTML Infographic

Pass the RDF data and parameters to generate a complete, single-file HTML document with:

- Modern, responsive design with glassmorphism effects
- Floating, draggable, resizable navigation panel
- Scroll-triggered animations using Intersection Observer API
- Interactive FAQ accordion with smooth transitions
- Section anchors with copy-to-clipboard functionality
- Entity linking to external URIs
- Comprehensive metadata (JSON-LD, microdata, Open Graph)
- Professional typography and color schemes

### 4. Generate a Markdown Companion (Optional)

When the user asks for Markdown, a Markdown variant, a `.md` companion, or a text-first companion output:

- Save the Markdown file in the **same folder as the HTML file**.
- Use the same slug/model/version stem as the HTML file, changing only the extension to `.md`.
  - Stem pattern: `{descriptive-slug}-{llm-id}-{n}`.
  - Example HTML: `x-kidehen-knowledge-base-update-thread-gpt5-chat-1.html`
  - Markdown companion: `x-kidehen-knowledge-base-update-thread-gpt5-chat-1.md`
- Link back to the HTML file with a relative link.
- Link to the associated RDF file with the same relative path used by the HTML `rel="related"` link.
- Preserve the RDF entity-linking contract: FAQ questions/answers, glossary terms/definitions, HowTo section and step headings, article/person/organization/media entities, and other key entities must link through the configured resolver using their RDF IRIs.
- Treat every visible HowTo step label exactly like a visible FAQ question: if the RDF contains `schema:HowToStep` entities, the step heading/label in HTML and Markdown MUST be an anchor to that step entity's RDF IRI through the configured resolver.
- Treat every visible SPARQL query heading exactly like a visible FAQ question: if the RDF contains `schema:SoftwareSourceCode` with `schema:programmingLanguage "SPARQL"`, the heading/title in HTML and Markdown MUST be an anchor to that query entity's RDF IRI through the configured resolver.
- Do not use raw source URLs for semantic entity links. Visible semantic entity links, including DBpedia/Wikidata IRIs selected as RDF entity identifiers, should route through the configured resolver unless the user explicitly asks for direct LOD links.
- Include media references when they exist in the RDF:
  - Images: embed with Markdown image syntax using the image content URL, and wrap or caption with a resolver link to the image object's RDF IRI.
  - Video: embed with an HTML `<video controls>` block because portable Markdown has no native video syntax. Use the video `contentUrl` as `<source src="..." type="video/mp4">` when available, include `poster="..."` from `schema:thumbnailUrl` when available, and provide a resolver link to the `schema:VideoObject` IRI.
  - Audio: embed with an HTML `<audio controls>` block when `schema:contentUrl` exists, and provide a resolver link to the `schema:AudioObject` IRI.
- Markdown does not need interactive navigation, JavaScript, dark mode, or visual effects, but it must remain structurally parallel to the HTML companion: title, overview, core entities, document links, FAQ, glossary, HowTo, sources, and provenance where applicable.

### SPARQL Query Sections

When RDF or source content includes SPARQL examples, query families, endpoint demos, or reporting recipes:

- Preserve the query body verbatim apart from safe HTML escaping. Do not replace it with a summary.
- Render each query in HTML as a `<details>`/`<summary>` accordion so long queries do not dominate the page.
- The summary title MUST link to the query entity through the configured resolver pattern.
- Include a visible "Run live query" link when the endpoint supports GET query URLs. Construct the URL with `encodeURIComponent(query)` and endpoint-specific parameters, defaulting to `?query={encoded}&format=text%2Fhtml` when no endpoint-specific pattern is known.
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

**Pattern**: Collapse-to-header-bar — the panel is always visible as a compact header. A toggle button collapses/expands the link list. No pin marker, no inactivity fade, no separate close/restore buttons.

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

**JavaScript**: Use the minimal collapse IIFE — a single script block with draggable header and toggle behavior. No timers, no localStorage, no separate close/restore/pin elements.

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
- No pin marker, no inactivity timer, no separate close/restore buttons
- JavaScript: single IIFE with drag + toggle behavior

#### Scroll-Triggered Animations
- Sections fade in and slide up as they enter viewport
- Implemented via Intersection Observer API for performance
- Staggered animation timing for visual flow

#### Section Anchors
- Heading hover shows visible 🔗 icon
- Click copies direct link to clipboard
- Enables shareable section references

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
- [ ] Section anchors have copy functionality
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
- **No Pin Marker**: Pin marker and inactivity fade removed — simpler, always-visible control
- **No Close Button**: Toggle replaces close/restore — a single button handles both states
- **Minimal JavaScript**: Single IIFE with drag + toggle behavior, no timers or localStorage
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

Basic mode provides a lightweight, functional D3.js force-directed graph:
- Multi-select filter buttons: toggle visibility by node type (Classes, Properties, Instances) with visually obvious selected/unselected states and matching `aria-pressed` values
- Density buttons: Core and Full graph views. Default to Core + Instances when the full graph is visually busy; keep Full available for complete RDF inspection
- Search input: filter nodes by name
- Status readout showing active mode, active filters, and visible node/link counts
- Simple legend with color-coded dots
- Click any node to open its IRI in the configured resolver (URIBurner describe service)
- Drag nodes to reposition; dragged nodes MUST pin/stick at the drop destination. Double-click unpins
- Mouse wheel zoom and drag-to-pan
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

> **Note:** Do NOT include a theme toggle in the graph toolbar. The page already has a theme toggle in the navigation panel (top-left). Duplicate theme controls are redundant.

**Settings panel (slides from right):**
- Must include an obvious close control (`X`) in the panel header that hides the settings panel, updates the settings button `aria-expanded` state, and returns focus to the settings button.
- **Physics Simulation**: Charge strength slider (-1200 to -50), Link distance slider (40-320px), Enable/disable physics toggle
  > **Critical:** These controls MUST be wired to update the D3 force simulation in real-time. Use event listeners on the input elements to call `simulation.force("charge").strength(value)` and `simulation.force("link").distance(value)`, then `simulation.alpha(0.3).restart()` to apply changes.
- **Predicate Display**: Radio option for "Icons" vs "Labels"
- **Edge Filtering**: Checkbox list of all predicates, Select All/Deselect All buttons
- **Node Filtering**: Chips for each node type (person, organization, place, concept, event, literal, resource), Select All/Deselect All
- **Literal Text Filtering**: Text input to show only literal relationships containing specified text
- **Resolver Preference**: Options for "None", "URIBurner" (https://linkeddata.uriburner.com/describe/?url={uri}), or "Custom" with pattern input
- **Arrow Style**: "Dual arrows" (render every triple) vs "Single arrow" (merge mutual predicates)
- **Color-coded Legend**: Dynamic legend showing node type colors with toggle chips

**Interaction:**
- Mouse wheel zoom (0.2x to 4x scale extent)
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

## Constructing kgData from RDF (CRITICAL)

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

Correspondingly, the embedded JSON-LD `WebPage` node MUST include a `prov:wasGeneratedBy` reference to a `schema:SoftwareApplication` entity for each skill, with `schema:name`, `schema:url` (GitHub), and `schema:description`. Declare the `prov:` context prefix as `http://www.w3.org/ns/prov#`.

### Generation Environment Attribution

Every generated HTML infographic footer sources/attribution section MUST also include a concise, human-visible generation environment line with each generation environment item hyperlinked when it has a known IRI or URL. This line states:

- The inferred LLM or LLM interface used for generation, matching the `{llm-id}` in the filename stem, for example `gpt5-chat`, linked to its canonical product URL (see canonical URL table below).
- The generation client/environment when known, for example `Cowork Desktop`, linked to its canonical product URL.
- The source delivery host/server when it is known from the source URL or HTTP headers, for example `content.martechday.com via Amazon S3/CloudFront`, linked to its source host URL.
- The Linked Data resolver/server platform used for entity hyperlinks. When URIBurner is used, identify and hyperlink it as `URIBurner` using its canonical URL `https://linkeddata.uriburner.com/`, and state that it is a Virtuoso-backed Linked Data resolver/server platform.

The RDF and embedded JSON-LD provenance SHOULD mirror this visible attribution using named entities such as `:gpt5ChatInterface`, `:codexDesktopEnvironment`, `:sourceDeliveryServer`, `:uriBurnerResolver`, and `:virtuosoServer` where applicable. These entities MUST NOT use `file:` IRIs. If the server/provider cannot be determined, state `source delivery server not determined` in the human-visible attribution instead of omitting the field.

#### Provenance Card Canonical Link Rule

**CRITICAL**: The provenance/attribution section exists to credit real products and tools. Items in provenance cards that represent known products, platforms, or tools with stable URLs MUST link to their **canonical homepage or repository URL** — NOT to session-generated URIBurner resolver URLs built from document-local fragment IRIs. Use `🔗 Visit` as the link label for canonical product links (vs `🔗 Explore` for resolver-based entity links elsewhere in the document).

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

### SoftwareApplication IRI Denotation Rule

For every `schema:SoftwareApplication` entity introduced or normalized during RDF/HTML/Markdown generation, select the subject IRI using this priority order:

1. **DBpedia first** — if a confident DBpedia resource exists, use the fully expanded DBpedia IRI as the software application's primary denotation IRI, for example `http://dbpedia.org/resource/Google_Docs`.
2. **Wikidata second** — if no confident DBpedia resource exists but a confident Wikidata entity exists, use the fully expanded Wikidata IRI, for example `http://www.wikidata.org/entity/Q...`.
3. **Homepage fallback** — if neither DBpedia nor Wikidata can be confirmed, use the official product/application home page URL with `#this` appended, for example `https://example.com/product/#this`.

When the primary IRI is not DBpedia- or Wikidata-based, add `owl:sameAs` relations to any confirmed DBpedia or Wikidata IRIs for that application. Declare `owl:` as `http://www.w3.org/2002/07/owl#` whenever `owl:sameAs` appears. Do not use a local document hash IRI for a known software application when one of the three denotation options above is available.

Visible software application names in HTML and Markdown MUST link through the configured resolver using the selected RDF IRI. The KG Explorer node for the software application MUST use the same selected IRI.

Before delivery, record or verify the chosen denotation basis for every `schema:SoftwareApplication`: DBpedia, Wikidata, or homepage `#this`. Do not fabricate DBpedia or Wikidata IRIs; if no confident match is found, use the homepage fallback and omit `owl:sameAs` unless a confident external identity is later established.

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
- [ ] FAQ questions, FAQ answers, glossary terms, glossary definitions, the HowTo section entity, every individual HowToStep heading/label, and other visible semantic entities are ALL hyperlinked to their KG entity IRIs via the resolver pattern.
- [ ] If a KG Explorer is present, its graph data is derived from the companion RDF artifact; if embedded, it is explicitly derived at generation time and not manually invented.
- [ ] KG Explorer includes resolver-backed node links and resolver-backed edge predicate links using `describe/?url=`.
- [ ] KG Explorer renders RDF triple direction explicitly: every visible predicate edge has an arrowhead from subject to object, with the path endpoint offset so the arrowhead is visible outside the target node.
- [ ] KG Explorer Advanced mode includes its required control surface: fullscreen button, center button, settings button, and a settings panel with wired physics sliders/toggle, predicate display, predicate filtering, node filtering, literal filtering, resolver preference, arrow style, and legend/filter state feedback.
- [ ] KG Explorer settings panel includes a visible close (`X`) control that hides the panel and restores focus predictably.
- [ ] KG Explorer includes Basic/Advanced modes by default, Core/Full density controls, multi-select Classes/Properties/Instances filters, clear selected/unselected filter states, visible node/link count feedback, and no blank graph when filters are enabled.
- [ ] KG Explorer node dragging pins/sticks nodes at their drop destinations, and double-click unpins.
- [ ] KG Explorer is visually readable: type-aware layout, collision spacing, curved or otherwise legible edges, restrained edge opacity, readable labels, and no unnecessary resolver launchpad/card grid below it.
- [ ] KG Explorer render validation: the SVG/canvas fills the full graph pane width, the plotted nodes are not clipped into a narrow left strip, and the graph has visible nodes/edges distributed across the pane in the default view.
- [ ] Programmatic KG orphan-node gate has passed: global embedded graph has zero orphan nodes and default rendered graph has zero orphan nodes.
- [ ] If a Markdown companion was requested, it is saved in the same folder as the HTML file, uses the same filename stem with `.md`, links to the HTML file, links to the RDF file with a relative path, and has no non-resolver external semantic links.
- [ ] If a Markdown companion was requested, the HTML POSH metadata includes `<link rel="alternate" type="text/markdown" href="{markdown-file}">`, and the embedded JSON-LD declares the Markdown file as an alternate encoding/representation using a relative `@id`.
- [ ] If a Markdown companion was requested and RDF media entities exist, it embeds or references them: images with Markdown image syntax, videos with HTML `<video controls>`, audio with HTML `<audio controls>`, and captions/labels linked to the RDF media entity IRIs through the resolver.
- [ ] If RDF contains SPARQL `schema:SoftwareSourceCode` examples, HTML renders them as accordions with resolver-backed query headings, escaped preformatted query text, endpoint/service links, and correctly URL-encoded live query links where an endpoint is known; Markdown mirrors them with fenced `sparql` code blocks.
- [ ] The local RDF link (`rel="related"`) uses a relative path and the target file exists.
- [ ] Navigation panel: drag works, resize works, collapse/expand toggles correctly, localStorage read/write does not throw, stale values are recovered from gracefully.
- [ ] Skills attribution line present in footer with correct GitHub URL(s).
- [ ] Dark mode: both `html[data-theme="dark"]` and `@media (prefers-color-scheme: dark)` produce equivalent rendering; no hardcoded colors outside CSS variables.

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
