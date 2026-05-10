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
- Do not use raw source URLs for semantic entity links unless the entity is a Linked Open Data cross-reference intended to resolve directly.
- Include media references when they exist in the RDF:
  - Images: embed with Markdown image syntax using the image content URL, and wrap or caption with a resolver link to the image object's RDF IRI.
  - Video: embed with an HTML `<video controls>` block because portable Markdown has no native video syntax. Use the video `contentUrl` as `<source src="..." type="video/mp4">` when available, include `poster="..."` from `schema:thumbnailUrl` when available, and provide a resolver link to the `schema:VideoObject` IRI.
  - Audio: embed with an HTML `<audio controls>` block when `schema:contentUrl` exists, and provide a resolver link to the `schema:AudioObject` IRI.
- Markdown does not need interactive navigation, JavaScript, dark mode, or visual effects, but it must remain structurally parallel to the HTML companion: title, overview, core entities, document links, FAQ, glossary, HowTo, sources, and provenance where applicable.

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

When generating an RDF infographic that includes a knowledge graph visualization, you MUST first elicit the visualization mode preference from the user:

> "Would you like a **Basic** (simple, lightweight) or **Advanced** (full-featured, with settings panel) graph visualization?"

#### Basic Mode (Default)

Basic mode provides a lightweight, functional D3.js force-directed graph:
- Filter buttons: toggle visibility by node type (Classes, Properties, Instances)
- Search input: filter nodes by name
- Simple legend with color-coded dots
- Click any node to open its IRI in the configured resolver (URIBurner describe service)
- Drag nodes to reposition
- Mouse wheel zoom and drag-to-pan
- Hover tooltip showing entity description
- Edge labels that are clickable hyperlinks to property/type IRIs

**Implementation requirements:**
- Include D3.js via CDN: `<script src="https://d3js.org/d3.v7.min.js"></script>`
- Use URIBurner resolver pattern: `https://linkeddata.uriburner.com/describe/?uri={encodedIRI}`
- Node colors: Classes (orange #ea580c), Properties (blue #0ea5e9), Instances (green #059669)
- Edge label click behavior:
  - "a" (rdf:type) → rdf:type predicate IRI
  - "domain" (rdfs:domain) → rdfs:domain predicate IRI
  - "range" (rdfs:range) → rdfs:range predicate IRI
  - Property labels → the property's own IRI

#### Advanced Mode

Advanced mode provides a full-featured visualization with settings panel, inspired by OSDS_extension/graph_gen.js:

**Visual features:**
- Dark/light theme toggle with gradient backgrounds and vignette effect
- Arrow markers on edges indicating relationship direction
- Node type icons: 👤 person, 🏢 organization, 📍 place, 💭 concept, 📅 event, 📝 literal, 🔗 resource
- Color-coded node sizes based on connectivity/importance
- Backdrop blur tooltip styling

**Control toolbar (top-right):**
- Fullscreen toggle button
- Center graph button  
- Settings gear button (opens settings panel)

> **Note:** Do NOT include a theme toggle in the graph toolbar. The page already has a theme toggle in the navigation panel (top-left). Duplicate theme controls are redundant.

**Settings panel (slides from right):**
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
- Double-click to pin/unpin node
- Local storage for preferences (theme, physics settings, resolver preference, arrow style)

**Implementation reference**: See `/Users/kidehen/Documents/Management/Development/OSDS_extension/src/graph_gen.js` for complete implementation details.

#### Mode Elicitation (CRITICAL)

When the user requests an RDF infographic with graph visualization:

**STOP - Do not generate any HTML until you complete this step:**

1. Ask the user explicitly: "Would you like a **Basic** (lightweight, no settings panel) or **Advanced** (full-featured, with settings panel) graph visualization?"
2. **Wait for the user's response** before proceeding
3. If the user does not specify within 2 exchanges, default to Basic mode
4. Once confirmed, proceed with the appropriate mode:
   - **Basic** → implement Basic mode only (no Advanced features)
   - **Advanced** → implement Advanced mode with toggle to switch to Basic at runtime

> **Why this matters:** Including Advanced features (settings panel, physics controls, theme toggle, etc.) adds complexity and potential bugs. Only include them when the user explicitly requests them.

The infographic should include a mode toggle (Basic/Advanced) in the visualization controls if Advanced is selected, allowing users to switch between modes at runtime.

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

- The inferred LLM or LLM interface used for generation, matching the `{llm-id}` in the filename stem, for example `gpt5-chat`, linked to its RDF provenance entity through the configured resolver.
- The generation client/environment when known, for example `Codex desktop`, linked to its RDF provenance entity through the configured resolver.
- The source delivery host/server when it is known from the source URL or HTTP headers, for example `content.martechday.com via Amazon S3/CloudFront`, linked to its source host URL and/or RDF provenance entity.
- The Linked Data resolver/server platform used for entity hyperlinks. When URIBurner is used, identify and hyperlink it as `URIBurner`, and state that it is a Virtuoso-backed Linked Data resolver/server platform.

The RDF and embedded JSON-LD provenance SHOULD mirror this visible attribution using named entities such as `:gpt5ChatInterface`, `:codexDesktopEnvironment`, `:sourceDeliveryServer`, `:uriBurnerResolver`, and `:virtuosoServer` where applicable. These entities MUST NOT use `file:` IRIs. If the server/provider cannot be determined, state `source delivery server not determined` in the human-visible attribution instead of omitting the field.

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

**Encoding rule:** `#` in entity IRIs must be encoded as `%23` exactly once in resolver `uri` parameter values. `%2523` (double-encoded) is invalid.

The resolver is for entities defined **within the document's own knowledge graph** (hash-based IRIs under the document namespace) that need a describe service to expose their structured descriptions. Entities that already have dereferenceable RDF IRIs in the Linked Open Data Cloud — such as DBpedia (`http://dbpedia.org/resource/...`), Wikidata (`http://www.wikidata.org/entity/...`), and other LOD sources — are cross-reference links. They resolve natively and should be linked directly, not routed through a resolver.

### Navigation Panel Behavior

Every infographic **MUST** include a floating section navigation control that:

- **Is movable** — draggable by pointer on desktop.
- **Is resizable** — resizable by pointer drag on desktop.
- **Is collapsible** — a toggle button collapses/expands the link list (collapse-to-header-bar pattern). The header bar remains always visible. Collapsed state shows a `+` / "Expand" control; expanded state shows `−` / "Collapse".
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
- [ ] Every resolver entity hyperlink in the HTML resolves to a valid `describe/?url=` URL (no double-encoding: `%2523` is invalid; `#` must encode to `%23` exactly once).
- [ ] FAQ questions, FAQ answers, glossary terms, glossary definitions, HowTo section + steps, and other visible semantic entities are ALL hyperlinked to their KG entity IRIs via the resolver pattern.
- [ ] If a Markdown companion was requested, it is saved in the same folder as the HTML file, uses the same filename stem with `.md`, links to the HTML file, links to the RDF file with a relative path, and has no non-resolver external semantic links.
- [ ] If a Markdown companion was requested, the HTML POSH metadata includes `<link rel="alternate" type="text/markdown" href="{markdown-file}">`, and the embedded JSON-LD declares the Markdown file as an alternate encoding/representation using a relative `@id`.
- [ ] If a Markdown companion was requested and RDF media entities exist, it embeds or references them: images with Markdown image syntax, videos with HTML `<video controls>`, audio with HTML `<audio controls>`, and captions/labels linked to the RDF media entity IRIs through the resolver.
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
