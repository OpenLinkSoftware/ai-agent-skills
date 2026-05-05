---
name: rdf-infographic-skill
description: Generate sophisticated, interactive HTML infographics from RDF data in any format (Turtle, RDF/XML, N-Triples, JSON-LD). Transform knowledge graphs into visually stunning, data-driven narratives with advanced CSS effects, dynamic interactions, floating navigation, smooth animations, and comprehensive metadata. Use when converting RDF datasets or SPARQL results into engaging, responsive infographic pages for marketing, documentation, or knowledge exploration.
license: MIT
---

# RDF-based HTML Infographic Generation Skill

Transform raw RDF knowledge graphs into visually compelling, interactive HTML infographics. This skill provides everything needed to convert semantic data into high-fidelity, modern web presentations.

## Overview

This skill enables you to:

1. **Ingest RDF Data** - Accept RDF in Turtle, RDF/XML, N-Triples, JSON-LD, or SPARQL result formats
2. **Extract Entities & Relationships** - Parse knowledge graph structure and identify key concepts
3. **Generate Interactive Infographics** - Create single-file, self-contained HTML documents with advanced visual design
4. **Implement Advanced Interactions** - Floating draggable navigation, scroll-triggered animations, smooth transitions
5. **Apply Professional Styling** - Glassmorphism effects, gradient backgrounds, responsive layouts, modern typography
6. **Ensure Accessibility & SEO** - Comprehensive metadata (JSON-LD, microdata, Open Graph), proper heading hierarchy, entity linking

## When to Use This Skill

- Converting SPARQL query results into data visualizations
- Creating knowledge graph exploration interfaces
- Building marketing infographics from semantic web data
- Generating interactive documentation from RDF datasets
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
- Format: `https://linkeddata.uriburner.com/describe/?uri={URL-encoded-IRI}`
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

Every generated HTML infographic **MUST** declare its connection to its associated RDF source document using two mechanisms:

**POSH (Plain Old Semantic HTML):**
```html
<link rel="related" href="filename.jsonld" type="application/ld+json">
```
Use relative paths. Support `.jsonld`, `.ttl`, `.rdf`, and `.nt` extensions depending on the RDF serialization produced.

**Embedded JSON-LD:**
```json
"relatedLink": {"@id": "filename.jsonld"}
```
Include `schema:relatedLink` in the JSON-LD structured-data island inside the HTML. Value must be a relative path expressed as an IRI using `@id` — not a plain string literal.

Both links must be relative — never use `file://` or absolute paths — so the relationship holds when the directory is moved or shared.

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

---

## HTML/RDF Pairing Requirements

Every generated HTML infographic **MUST** satisfy these requirements to ensure correct entity-level linkage between the visible HTML and the associated RDF knowledge graph.

### Resolver Link Configuration

Entities that have defined IRIs in the RDF knowledge graph (persons, concepts, organizations, FAQ questions, glossary terms, HowTo steps) **SHOULD** be hyperlinked through a designated Linked Data resolver rather than pointing directly to external source URLs. This preserves the human-readable ↔ machine-readable loop: following a resolver link exposes the entity's full structured description with provenance, cross-references, and property sets.

**Resolver selection (in priority order):**
1. **URIBurner** (default) — `https://linkeddata.uriburner.com/describe/?uri={URL-encoded-IRI}`
2. **User-designated resolver** — any alternative resolver explicitly specified by the user
3. **None** — if the user explicitly opts out, entity text is not hyperlinked and plain entity IRIs may be shown instead

```html
<!-- DEFAULT: URIBurner resolver link to KG entity -->
<a class="entity-link"
   href="https://linkeddata.uriburner.com/describe/?uri=https%3A%2F%2Fwww.lassila.org%2Fpublications%2F2001%2FSciAm.pdf%23timBernersLee"
   target="_blank" rel="noopener noreferrer">Tim Berners-Lee</a>

<!-- WITH USER RESOLVER (e.g., custom describe endpoint) -->
<a class="entity-link"
   href="https://my-company.com/describe/?uri=https%3A%2F%2Fwww.lassila.org%2Fpublications%2F2001%2FSciAm.pdf%23timBernersLee"
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
- [ ] Every resolver entity hyperlink in the HTML resolves to a valid `describe/?uri=` URL (no double-encoding: `%2523` is invalid; `#` must encode to `%23` exactly once).
- [ ] FAQ questions, FAQ answers, glossary terms, and HowTo section + steps are ALL hyperlinked to their KG entity IRIs via the resolver pattern.
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
