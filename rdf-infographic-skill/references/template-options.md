# RDF Infographic Template Options

Use templates as visual and interaction references, not as hard dependencies. The strict harness contract defines required behavior; templates are selectable shells that must be adapted to pass validation.

## Selection Rule

- If the user names or supplies a template, use that as the visual reference and retrofit the contract features into it.
- If the user asks for the "usual" collection and gives no preference, infer the best template from the source content, audience, and nearby prior artifacts.
- **For Thesis & Framework Article content specifically (a named framework, a workload/tier/category mapping, sample instance data meant to be queried) — default to the Editorial Data-Viz / Intelligence-Threshold template below** (recorded 2026-08-19, preferences.ttl Step 236 / howto/editorial-data-viz-aesthetic.ttl), which supersedes the OpenLink Brand shell for this content class; use the OpenLink Brand template only when the user names it or the OpenLink brand palette is required. This is a standing preference, not just one more option in the list.
- If an existing artifact is being repaired, preserve its visual language unless the user asks for a redesign.
- If a helper script is convenient, use it; if the template calls for a different implementation, implement directly and run the validator.

## Available References

### Harness Reference

Asset: `scripts/rdf_infographic_harness.py`

Best for:

- New article collections where consistency matters more than a bespoke layout.
- Cases where previous KG Explorer regressions are the main risk.
- Fast generation using known IDs and validation-friendly controls.

Characteristics:

- Floating compact navigation.
- Single KG Explorer SVG with controls tray closed by default.
- Advanced-only settings panel.
- Footer SPARQL workbench with named graph and query recipe selectors.
- Full attribution card set.

### Competitive / Head-to-Head Analysis

Asset: `assets/templates/competitive-analysis-head-to-head-claude_sonnet_4_6.html`

Best for:

- Sources that compare **two or more** named platforms, products, systems, harnesses, or vendors.
- Feature matrices, capability scoreboards, and tabulated peer comparisons (including Grok/X share tables).

Characteristics worth preserving:

- Premium dark aesthetic, hero dual-badges, horizontal timeline.
- **Responsive dual comparison presentation (skill contract item 15):**
  - `.comparison-table-view` — semantic multi-column matrix for viewports **≥901px**
  - `.comparison-cards-view` — one product card per entity for viewports **≤900px**
  - Identical facts in both views; CSS-only switch at 900px; no JS required for the switch
  - Resolver-linked entity names in table headers **and** card headers
  - **Each aspect/dimension described in companion TTL** and **resolver-linked in the first column** of every comparison table row (and matching card row labels)
  - Overflow-safe cells (`min-width:0`, `overflow-wrap:anywhere`)
- Two-column capability panels that collapse to one column on narrow screens.
- Glossary/FAQ/HowTo patterns consistent with the harness contract.

Required adaptations before reuse:

- Substitute compared entities and matrix cells from the companion RDF (do not invent competitors).
- Keep dual markup when the matrix has ≥2 entity columns — do **not** ship a phone-only horizontal-scroll table.
- Retrofit full harness features (nav collapsed default, theme toggle, KG Explorer, SPARQL workbench, attribution cards) if the shell is used as a visual reference rather than a complete page.
- Verify both viewports before delivery (table visible at desktop; cards visible at ~390px).

### Claude Sonnet 4 Gartner Dashboard

Asset: `assets/templates/gartner-da-london-2026-claude-sonnet4-dashboard.html`

Best for:

- Dense conference reports, field notes, strategy analysis, or operational dashboards.
- Documents with many sections, metrics, tables, chips, archetypes, and quick SPARQL recipes.
- User preference for a compact top navigation bar and work-focused dashboard feel.

Characteristics worth preserving:

- Fixed top horizontal navigation with compact menu expansion.
- Dense metric/stat pills and dashboard cards.
- Top-level theme button.
- Two-pane Basic/Advanced KG Explorer pattern.
- Advanced settings drawer rather than large card controls.
- Footer quick-explore SPARQL links.

Required adaptations before reuse:

- Keep navigation collapsed by default and include the required page-level theme control.
- Ensure KG controls are closed by default. If using a two-pane Basic/Advanced layout, Advanced settings must still be hidden until Advanced mode and Settings are explicitly selected.
- Build KG data from companion RDF, not hand-authored subsets unless the RDF itself is the source of those subsets.
- Make SVG node labels and edge labels resolver-backed anchors using RDF IRIs.
- Use sticky node drag with double-click unpin.
- Replace `format=text/html` SPARQL links with query-type-specific formats: `text/x-html+tr` for SELECT and `text/x-html-nice-turtle` for DESCRIBE/CONSTRUCT.
- Add or preserve full attribution: source material, companion files, skills, generation environment, Linked Data runtime, named graph IRIs, resolver pattern, and extraction provenance.
- Ensure every non-fragment HTML link opens in a new tab with `target="_blank" rel="noopener noreferrer"`.

### Semantic Medallion Editorial Technical Template

Asset: `assets/templates/semantic-medallion-editorial-technical.html`

Best for:

- Technical explainers, architecture patterns, ontology/SPARQL tutorials, and documentation-style artifacts.
- Articles where the main story is a layered architecture, implementation path, vocabulary mapping, or executable query examples.
- Outputs that need a polished editorial feel with dense technical sections rather than a dashboard/briefing feel.

Characteristics worth preserving:

- Compact movable/resizable navigation panel that starts as a small header control.
- Separate page-level theme button.
- Narrow reading column with technical cards, architecture layers, capability cards, FAQ, glossary, and downloads.
- Strong medallion/layer visual language suitable for Bronze/Silver/Gold/Platinum or other staged architectures.
- SPARQL query accordions with syntax-styled query blocks and live-run buttons.
- Single-canvas D3 KG Explorer with legend and toolbar.
- Footer with source, companion artifact, skill, resolver, and server/platform references.

Required adaptations before reuse:

- Keep or retrofit POSH links for the companion HTML/MD/RDF set, including Markdown parity when a Markdown output is requested.
- Ensure every external link has `target="_blank" rel="noopener noreferrer"`; this template has some same-folder artifact links and source links that may need updating.
- Replace static or hand-authored KG nodes/links with graph data derived from the companion RDF, unless the static subset is programmatically derived from that RDF.
- Make KG node labels and edge labels resolver-backed anchors using RDF IRIs, not just click handlers or plain text.
- Keep controls closed by default; if the toolbar is visible, wrap it in a compact Controls tray or otherwise preserve the first visible KG state required by the contract.
- Scope settings to Advanced mode if settings are present.
- Add predicate Select All/Deselect All when predicate filtering is available.
- Preserve sticky drag and double-click unpin.
- Replace `format=text/html` SPARQL links with query-type-specific formats: `text/x-html+tr` for SELECT and `text/x-html-nice-turtle` for DESCRIBE/CONSTRUCT.
- If the footer uses a single quick SPARQL link, upgrade it to either the full workbench or an equivalent set of quick links plus editable/query recipe capability, depending on user preference.
- Include named graph IRIs and extraction/generation provenance in the attribution block.

### Spec-Sheet Editorial Essay

Asset: `assets/templates/spec-sheet-editorial-essay-claude_sonnet_5.html`

Best for:

- Long-form argumentative essays, thesis pieces, and framework commentary where the point is a sustained read, not a data-exploration surface — narrative prose is the primary artifact, not a KG.
- Content organized as a numbered sequence of short chapters (§1, §2, …) rather than a dashboard of independent cards.
- Pieces that cite or visually reproduce a named external framework (e.g. a tetrad, a quadrant model, a maturity ladder) as part of the argument.
- Pieces that credit third-party source images (charts, cartoons, diagrams) inline, with per-image creator attribution.

Characteristics worth preserving:

- Quiet limestone/ink editorial palette (serif body + monospace structural labels — eyebrows, step numbers, quadrant tags) instead of a dashboard or gradient-hero look; both light and dark themes fully tokenized.
- Numbered chapter sections (`<section class="chapter" id="{slug}">`), each with a self-linking `§N` badge (`<a href="#{slug}">`) so every section is a stable, clickable anchor and cross-references between sections use real `<a href="#slug">` links, not bare "§N" prose.
- A hub-and-quadrant diagram pattern (`.tetrad`/`.tetrad-hub`/`.tetrad-cell`) for any four-part reciprocal framework — center circle absolutely positioned over a 2×2 grid on wide viewports, falling back to a static stacked header block under 620px. Asymmetric per-quadrant padding on the corner facing the hub keeps prose clear of the circle at any content length — do not rely on a fixed hub size alone.
- `.figure-block` figures for credited third-party images: image, `<figcaption>` description/quote, and a monospace `.figure-credit` line crediting the named creator via a resolver-wrapped link plus a "view full size ↗" out to the original hosted asset.
- Hero delegation line (`.hero-attrib`) directly under the dek, short and singular — model + delegation only, not a full tool enumeration (that belongs in the footer per the single-canonical-surface rule).
- Footer `.tech-grid` carries the full stack as separate cards: language model, agent platform (the harness, e.g. Claude Code — distinct from the model per the model-vs-environment rule), any named framework cited, the RDF companion link, and — when the piece is deployed to a Virtuoso/URIBurner endpoint rather than kept client-side only — server platform and linked-data-resolver cards alongside them.

Required adaptations before reuse:

- This template intentionally omits the KG Explorer and SPARQL workbench (contract items 7, 8, 13) — it is not a graph-exploration surface. Do not add them; a narrative essay with an embedded force-directed graph is a contract mismatch, not an enhancement. Full harness mode should select a different template when a KG Explorer is actually wanted.
- Every `schema:DefinedTerm`, `schema:HowToStep`, and `schema:ItemList` item minted in the companion RDF MUST still get a resolver-backed hyperlink (`https://linkeddata.uriburner.com/describe/?url={encoded fragment IRI}`) on its first visible mention in the HTML body prose — section headings, quadrant/stack-layer/debt labels, and list items, not just person names. This is the harness contract's resolver-link requirement (item 3) applied to concept entities instead of KG nodes; verify no minted RDF entity is left unlinked in either the HTML or the Markdown companion.
- Embedded third-party images MUST be inlined as `data:` URIs, never `<img src="https://…">` — a strict artifact CSP blocks remote image loads. Keep the Markdown companion's images as ordinary remote `![]()` links instead, since Markdown has no such CSP.
- Confirm the person/creator credited per image resolves to a real, user-supplied profile URL — never invent or guess one.
- If the piece will be deployed to a Virtuoso/URIBurner endpoint, add the Server platform + Linked data resolver footer cards; omit them only when the artifact is genuinely staying client-side (e.g. Claude Artifacts only, no DAV deployment planned).

### Editorial Data-Viz / Intelligence-Threshold Template — PREFERRED DEFAULT for Thesis & Framework + data-rich content (2026-08-19)

Canonical implementation: `{LLM_ROOT}/DeepSeek/webpages/right-sizing-intelligence-spend-deepseek_v4flash-1.html` (the Right-Sizing Your Intelligence Spend collection) and its generator suite `{LLM_ROOT}/DeepSeek/_build/right-sizing/html_{css,visuals,body,js}.py`.

**This is the current standing preferred default for Thesis & Framework Article content and data-rich collections** (a named framework, workload/tier/category mapping, sample instance data meant to be queried) — select it before the OpenLink Brand shell below unless the user names a different template or an existing artifact's visual language should be preserved. Recorded 2026-08-19 (preferences.ttl Step 236 / howto/editorial-data-viz-aesthetic.ttl) after the user asked for this page's look to become the going-forward default. The OpenLink Brand entry below remains a valid alternative shell; the Editorial Data-Viz aesthetic extends it with the inline-SVG data-visualization signature.

Best for:

- Thesis/opinion pieces proposing a named framework (pillars, tiers, predictions) that maps onto categorized sample data meant to be queried.
- Any collection whose argument is quantitative or ordinal — thresholds, tiers, trends, trade-offs — where the visuals carry the argument.

Characteristics worth preserving:

- **CSS-variable theming** — `:root` light tokens overridden in `html[data-theme="dark"]` and `@media (prefers-color-scheme: dark)` as two entirely separate blocks; no hardcoded colors; SVG visuals use `var()` via style attributes (var() does not resolve in SVG presentation attributes).
- **Editorial typography** — uppercase letter-spaced eyebrows (`eyebrow`/`eyebrow-dark`), clamp()-scaled display headings, muted `section-sub` lines, lede/body synopsis deck, `Author`/`Contributors` hero labels.
- **Inline-SVG data visualizations as the signature** (see `howto/editorial-data-viz-aesthetic.ttl`):
  - Hero threshold/capability curve — rising gradient line, shaded `frontier band`, workload dots positioned by threshold, annotation 'below the line: context & execution / above: frontier intelligence pays';
  - Workload threshold spectrum — gradient None→Extreme bar with threshold ticks and a dashed rising capability line;
  - Workload intelligence map — scatter of sample instances (intelligence-threshold × token-sensitivity), colored by value class (discovery/application/hybrid), dot radius encoding a third dimension (e.g. overqualification risk), shaded frontier-reserve region;
  - Descending trend line for metrics that fall toward zero (e.g. intelligence consumed per successful outcome).
  - Animated line draws via stroke-dashoffset, disabled under `prefers-reduced-motion`.
- **Stat cards with mini magnitude bars** under each key figure.
- **Every visual entity resolver-linked** — dots/markers/labels are SVG `<a>` with `href` + `xlink:href` + `data-iri` + `target="_blank" rel="noopener noreferrer"` pointing at `describe/?url={iri}`, each with a `<title>` tooltip.
- **SPARQL workbench with a visible demo-instance-data panel** — the sample instances the source covers, resolver-linked, plus demo recipes (one `<details class="sparql-card">` per query, `FROM <DAV graph>` clause) that actually exercise them.
- **Responsive dual-presentation matrices** for multi-entity comparisons (harness item 15: table ≥901px, cards ≤900px).
- **Full harness contract retained** — floating collapsed nav, theme toggle in the nav header, KG Explorer Basic/Advanced with settings panel, 8-item attribution footer, open-tab links.

Required adaptations before reuse:

- Generate the visuals from the companion RDF (the canonical `html_visuals.py` builds dots from the instance list) — do not hand-author coordinates that drift from the graph.
- Keep the standing section order `kg-explorer < sparql-workbench < howto < faq < glossary` and the validator's SPARQL-accordion/escape gates.
- Re-run `scripts/validate-harness-contract.py` (0 failures) plus the anchor audit, `node --check`, orphan-node check, and the headless-browser DOM check (0 JS errors, KG renders) before delivery.

### Editorial Data-Viz / Intelligence-Threshold Template — PREFERRED DEFAULT for Thesis & Framework + data-rich content (2026-08-19)

Canonical implementation: `{LLM_ROOT}/DeepSeek/webpages/right-sizing-intelligence-spend-deepseek_v4flash-1.html` (the Right-Sizing Your Intelligence Spend collection) and its generator suite `{LLM_ROOT}/DeepSeek/_build/right-sizing/html_{css,visuals,body,js}.py`.

**This is the current standing preferred default for Thesis & Framework Article content and data-rich collections** (a named framework, workload/tier/category mapping, sample instance data meant to be queried) — select it before the OpenLink Brand shell below unless the user names a different template or an existing artifact's visual language should be preserved. Recorded 2026-08-19 (preferences.ttl Step 236 / howto/editorial-data-viz-aesthetic.ttl) after the user asked for this page's look to become the going-forward default. The OpenLink Brand entry below remains a valid alternative shell; the Editorial Data-Viz aesthetic extends it with the inline-SVG data-visualization signature.

Best for:

- Thesis/opinion pieces proposing a named framework (pillars, tiers, predictions) that maps onto categorized sample data meant to be queried.
- Any collection whose argument is quantitative or ordinal — thresholds, tiers, trends, trade-offs — where the visuals carry the argument.

Characteristics worth preserving:

- **CSS-variable theming** — `:root` light tokens overridden in `html[data-theme="dark"]` and `@media (prefers-color-scheme: dark)` as two entirely separate blocks; no hardcoded colors; SVG visuals use `var()` via style attributes (var() does not resolve in SVG presentation attributes).
- **Editorial typography** — uppercase letter-spaced eyebrows (`eyebrow`/`eyebrow-dark`), clamp()-scaled display headings, muted `section-sub` lines, lede/body synopsis deck, `Author`/`Contributors` hero labels.
- **Inline-SVG data visualizations as the signature** (see `howto/editorial-data-viz-aesthetic.ttl`):
  - Hero threshold/capability curve — rising gradient line, shaded `frontier band`, workload dots positioned by threshold, annotation 'below the line: context & execution / above: frontier intelligence pays';
  - Workload threshold spectrum — gradient None→Extreme bar with threshold ticks and a dashed rising capability line;
  - Workload intelligence map — scatter of sample instances (intelligence-threshold × token-sensitivity), colored by value class (discovery/application/hybrid), dot radius encoding a third dimension (e.g. overqualification risk), shaded frontier-reserve region;
  - Descending trend line for metrics that fall toward zero (e.g. intelligence consumed per successful outcome).
  - Animated line draws via stroke-dashoffset, disabled under `prefers-reduced-motion`.
- **Stat cards with mini magnitude bars** under each key figure.
- **Every visual entity resolver-linked** — dots/markers/labels are SVG `<a>` with `href` + `xlink:href` + `data-iri` + `target="_blank" rel="noopener noreferrer"` pointing at `describe/?url={iri}`, each with a `<title>` tooltip.
- **SPARQL workbench with a visible demo-instance-data panel** — the sample instances the source covers, resolver-linked, plus demo recipes (one `<details class="sparql-card">` per query, `FROM <DAV graph>` clause) that actually exercise them.
- **Responsive dual-presentation matrices** for multi-entity comparisons (harness item 15: table ≥901px, cards ≤900px).
- **Full harness contract retained** — floating collapsed nav, theme toggle in the nav header, KG Explorer Basic/Advanced with settings panel, 8-item attribution footer, open-tab links.

Required adaptations before reuse:

- Generate the visuals from the companion RDF (the canonical `html_visuals.py` builds dots from the instance list) — do not hand-author coordinates that drift from the graph.
- Keep the standing section order `kg-explorer < sparql-workbench < howto < faq < glossary` and the validator's SPARQL-accordion/escape gates.
- Re-run `scripts/validate-harness-contract.py` (0 failures) plus the anchor audit, `node --check`, orphan-node check, and the headless-browser DOM check (0 JS errors, KG renders) before delivery.

### Thesis & Framework / OpenLink Brand Template — PREFERRED DEFAULT for Thesis & Framework Article content

Asset: `assets/templates/thesis-framework-openlink-brand-claude_opus_5.html`

**This is the standing preferred default for the kg-generator Thesis & Framework Article template** (a named framework, a workload/tier/category mapping, sample instance data meant to be queried) — select it before reaching for another template, unless the user names a different one or an existing artifact's visual language should be preserved. Recorded 2026-08-19 (preferences.ttl Step 232 / howto/thesis-framework-openlink-brand-template.ttl) after the user asked for this page's look and the demo-data discipline behind it to become the going-forward default rather than a one-off.

Best for:

- Thesis/opinion pieces proposing a named framework (pillars, tiers, predictions) where the framework maps onto categorized sample data — not just prose describing the categories.
- Any source with quantitative examples worth surfacing as typed, queryable evidence rather than leaving them in prose.
- Content with a comment thread worth including (the principal's own comment plus a sampling of others).

Characteristics worth preserving:

- **OpenLink brand palette** (`agent-rdf-memory/howto/openlink-brand-color-scheme.ttl`, preferences.ttl Step 125) as the `:root`/`html[data-theme="dark"]`/`@media(prefers-color-scheme:dark)` token set — navy `#1f4e79` accent in light, vivid cyan `#00b4ff` in dark. A `--on-accent` token (white in light, near-black in dark) keeps text legible on saturated tier/badge fills in both themes — do not hardcode `#fff` on a colored chip; both theme's accent brightness differs too much for one literal to work in both.
- Hero built from the article's own load-bearing figures as resolver-linked stat chips (`.hstat`), not generic decoration — pull 3-5 of the source's strongest numbers and link each to the KG section entity that states it.
- **Tier/category map as the visual centerpiece** (`.tier-map`/`.tier-panel`/`.tier-workload-row`) when the source has a multi-tier or multi-category structure: a `.tier-legend` spectrum bar above the panels (counts per tier, resolver-linked), color-railed panels per tier, and per-item rows carrying whatever typed attributes the RDF actually has for that item — not just a name and description. **Generate this section directly from the RDF** (walk the graph, don't hand-author HTML that can drift from it) — see the required-adaptation note below on why.
- Comment-thread cards (`.comment-card`) with a monogram avatar, the principal's own comment visually distinguished (`.is-principal`, accent rail + tint), and a resolver link per comment to its RDF entity.
- SPARQL demo-query set (`.demo-query-set`) *in addition to* the standard workbench editor: one closed-by-default `<details class="sparql-card" data-demo-query>` accordion per query that actually exercises the sample data, each with a "Load into editor" button wired to the shared `#sparqlText` textarea, sourced from `schema:SoftwareSourceCode` entities in the companion TTL — not the generic entity-summary/all-triples/named-graph-triples recipes alone. See the required-adaptation note below on demo-data completeness.

Required adaptations before reuse:

- **Regenerate the tier/category map section from the RDF at build time, not by hand.** A hand-written tier map silently drifts out of sync the moment a workload/category instance is added or a count changes — this happened once already (Step 233) and was caught only because the user asked a direct question about tier counts. Walk `?w rs:hasIntelligenceThreshold ?tier` (or the source's equivalent typed relation) and emit panels/rows/counts/legend from the query result.
- **Before shipping the demo-query set, verify every category/tier the source discusses actually has instance data and a query, not just the tier the source gives the richest numbers for.** The original build only modeled numeric detail (employment counts) for one of three tiers, using name+description+tier-link for the other two — even though the source article was, if anything, *more* specific about those tiers (named context inputs, definitions of done, failure modes). Read each source section for the concrete specifics it gives per category before deciding a category "has no data to model."
- **Every quantitative example the source cites is evidence data, not prose decoration.** Scan for numeric claims (percentages, multipliers, counts, ranges) the source uses to support its argument and model each as a typed value (`schema:value`/`schema:minValue`/`schema:maxValue`/`schema:unitText`) linked to what it measures and which argument it supports — verified via `grep`/regex for numeric literals in the companion TTL, not by eye. A number that exists only inside a `schema:description` string is unqueryable and will be missed by exactly this kind of "did you actually include X" follow-up.
- Run every demo query against the graph with `rdflib` before shipping (`g.query(text)` after stripping the `FROM <...>` line for a local run) and confirm each returns rows — a query that returns zero rows is worse than no query, since it looks demonstrated but silently isn't.
- Sync new entities into the embedded `kgData` graph payload and re-check the orphan-node gate whenever the TTL gains new instances after the KG Explorer was first built from it.
- Split `schema:author` (the source's actual bylined author only) from `schema:contributor` (co-writers named in body text, commenters) — do not default multiple named bylines into a joint `schema:author` list without checking which byline the source's own platform metadata actually asserts.
- Re-run `scripts/validate-harness-contract.py` after every structural change (tier map regeneration, demo-query additions, byline correction) — several of the fixes above were only caught because the validator's SPARQL-accordion and KG-orphan gates fired on a change that looked cosmetic.
- CSS comment hygiene: never write a literal `*/` sequence inside a CSS comment documenting a property-name glob (e.g. `--opal-*/--ols-*`) — it silently truncates the comment and drops the following rule block. Run the brace/comment-balance scan in `howto/css-comment-star-slash-trap.ttl` after any hand-edit to the `<style>` block.

### Thesis & Framework / Harness-Styled — use when hand-assembling from `rdf_infographic_harness`

Asset: `assets/templates/thesis-framework-harness-styled-claude_sonnet_5.html`

The OpenLink-brand thesis chassis above, carrying the **first complete style layer for the harness helper surfaces** — the attribution footer and the SPARQL workbench. Select it whenever a page is hand-assembled from `attribution_footer()` / `footer_sparql_workbench()` / `kg_explorer_shell()` rather than driven through `html_assembler.py`.

Why it exists: until 2026-08-20 **no template in this collection defined a single rule for any harness-emitted class** (`.attribution-*`, `.sparql-*`, `.entity-link`). Pages built from the helpers therefore shipped a full-bleed unstyled footer and a SPARQL workbench of bare form controls with the percent-encoded live-query URL wrapping across the page — while remaining valid HTML with correct content and a full validator PASS. The CSS now ships from `rdf_infographic_harness.harness_styles()`, and `validate-harness-contract.py` fails any page that uses the markup without it.

Characteristics worth preserving:

- **Footer as a card grid**, not a text stack: uppercase micro-labels (`.attribution-label`), tinted companion-file/skill pills (`.attribution-pill`), equal-height rows, `.wide` cards spanning two columns only above 720px, and a `--bg-alt` band with a top hairline so the footer reads as a distinct region.
- **SPARQL workbench as a real panel** (`.sparql-launch`): a `--primary → --accent` gradient hairline on the top edge, a solid primary "Run live query" CTA, a three-field control row, and a 210px monospace editor with `resize:vertical` and `tab-size:2`.
- **`#sparqlLinkPreview` constrained to one truncating chip.** It is filled with the full percent-encoded query URL; unconstrained it wraps across a dozen lines and bleeds past the panel. The href still carries the whole query.
- **One shared measure.** Footer, SPARQL panel, KG panel and body sections all resolve to the same 1036px content width (1100px box − 2rem padding), so nothing sits visibly wider than the column above it.
- Every colour in the supplement is a `var()` fallback chain ending in a literal, so the rules survive being dropped into a template using a different token vocabulary instead of failing silently at computed-value time.

Required adaptations before reuse:

- **This is a chassis, not a blank.** Its `kgData`, prose, entity IRIs and title belong to the x402/Circle meshup. Replace all of them and re-check against the companion TTL — the semantic-fidelity gate exists because carried-forward prior-task content is the recurring failure here.
- **Check for stale ids and titles inherited from the chassis you copy.** This page was itself built by copying a chassis, and shipped with the *source* template's KG panel title ("Right-Sizing Your Intelligence Spend") plus a duplicate `id="kg-explorer"` on both the outer `<section>` and the inner panel — the duplicate made `#kg-explorer`'s card styling paint the whole section and made `getElementById('kg-explorer')` return the section instead of the panel. Outer is now `#kg-explorer-section`.
- When extracting a `<style>` block from a template, **strip the source file's own `<style>`/`</style>` boundary lines** before re-wrapping. A nested `<style><style>` corrupts parsing of the first rule through error recovery and has silently eaten an entire `:root` custom-property definition.
- Pass `include_markdown=False` to `attribution_footer()` on runs that produce RDF + HTML only, or the footer advertises a Markdown companion that was never written.

## Validation

Run:

```bash
python3 scripts/validate-harness-contract.py path/to/page.html --ttl path/to/page.ttl --jsonld path/to/page.jsonld
```

The validator is a contract gate, not a template selector. A page may use any visual template if it passes the contract checks.
