#!/usr/bin/env python3
"""
Reusable RDF infographic harness helpers.

These helpers are a reference implementation, not a mandatory visual template.
Use them directly when they fit the artifact, or mirror their contract behavior
inside another selected template. They encode the contract pieces that have
regressed in prior runs: KG Explorer shell conventions, footer attribution, and
the footer SPARQL workbench with query-type-specific URIBurner result formats.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from urllib.parse import quote


RESOLVER = "https://linkeddata.uriburner.com/describe/?url="
SPARQL_ENDPOINT = "https://linkeddata.uriburner.com/sparql"


def resolver_url(iri: str) -> str:
    return RESOLVER + quote(iri, safe="")


# ── Styles for the markup these helpers emit ────────────────────────────────
#
# WHY THIS EXISTS. kg_explorer_shell(), footer_sparql_workbench() and
# attribution_footer() emit .attribution-* / .sparql-* / .entity-link markup.
# Until 2026-08-20 NO template in this skill -- not assets/templates/*.html,
# not assets/html-template.html, not scripts/templates/styles.css -- carried a
# single rule for any of those classes. Every page hand-assembled from these
# helpers therefore rendered its footer as full-bleed unstyled text and its
# SPARQL workbench as bare form controls with the percent-encoded live-query
# URL wrapping across the page. The failure is silent: no console error, no
# validator failure, valid HTML, correct content -- it just looks broken.
#
# Emitting markup whose styling lives somewhere else is what allowed the drift.
# Markup and CSS now ship from the same module, so they cannot separate.
# Pages that already style these classes can pass include_styles=False.
#
# PORTABILITY. Templates in this skill use different custom-property
# vocabularies (--card-bg/--border/--text vs --panel/--line/--ink vs --card).
# Hard-coding one vocabulary is how this class of bug recurs: an unresolvable
# var() makes the whole declaration invalid at computed-value time and the rule
# silently does nothing. Every colour below is therefore a fallback chain
# ending in a literal, so these rules degrade to something readable under any
# template rather than to nothing.
_SURFACE = "var(--card-bg, var(--panel, var(--card, #ffffff)))"
_PAGE_BG = "var(--bg, #ffffff)"
_BAND_BG = "var(--bg-alt, var(--bg-soft, #f9fafb))"
_LINE = "var(--border, var(--line, #e5e7eb))"
_LINE_STRONG = "var(--primary-light, var(--accent, #2d6a9f))"
_INK = "var(--text, var(--ink, #111827))"
_MUTED = "var(--text-secondary, var(--muted, #6b7280))"
# Entity/link colour is --primary where the palette separates it from --accent
# (--accent is reserved for rules, counters and icon fills, never entity links
# -- see agent-rdf-memory/howto/ui-ux-expert-persona.ttl). Templates that only
# define --accent fall through to it.
_LINK = "var(--primary, var(--accent, #1f4e79))"
_LINK_HOVER = "var(--secondary, var(--primary-light, #163a5c))"
_TINT = "var(--accent-soft, var(--chip, rgba(127,127,127,.14)))"
_ON_LINK = "var(--on-accent, #ffffff)"
_FOCUS = "var(--focus-ring, rgba(0,180,255,.55))"
_SHADOW = "var(--card-shadow, 0 1px 2px rgba(16,32,52,.06), 0 4px 16px rgba(31,78,121,.06))"
_SHADOW_HOVER = "var(--card-hover-shadow, 0 2px 4px rgba(16,32,52,.07), 0 18px 40px rgba(31,78,121,.14))"
_MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def harness_styles() -> str:
    """CSS for every class the harness helpers emit.

    Returned without <style> tags so callers can concatenate it into an
    existing stylesheet. Never wrap the result in <style> if you are appending
    it to a block that already has them -- a nested <style><style> corrupts
    parsing of the FIRST rule in the block through the parser's error recovery,
    which has previously eaten an entire :root token definition and silently
    dropped every custom property with it.
    """
    return f"""
/* ── rdf-infographic harness helper styles ──────────────────────────────── */
.entity-link{{color:{_LINK};text-decoration:none;border-bottom:1px solid transparent;transition:border-color .2s,color .2s}}
.entity-link:hover{{border-bottom-color:{_LINK};text-decoration:none}}

/* Footer attribution surface (attribution_footer) */
footer#sources{{background:{_BAND_BG};border-top:1px solid {_LINE};margin-top:3rem;padding:4rem 0 3.25rem}}
.attribution-panel{{max-width:1100px;margin:0 auto;padding:0 2rem;min-width:0}}
.attribution-inner{{min-width:0}}
.attribution-panel .section-head{{display:block;margin:0 0 1.6rem}}
.attribution-panel .section-head h2{{font-size:1.45rem;letter-spacing:-.02em;margin:0 0 .5rem;color:{_INK}}}
.attribution-panel .section-head p{{font-size:.92rem;line-height:1.55;color:{_MUTED};max-width:62ch;margin:0}}
.attribution-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,250px),1fr));gap:1rem;align-items:stretch}}
.attribution-card{{background:{_SURFACE};border:1px solid {_LINE};border-radius:12px;padding:1.05rem 1.15rem 1.15rem;min-width:0;overflow-wrap:anywhere;box-shadow:{_SHADOW};transition:border-color .2s,box-shadow .2s,transform .2s}}
.attribution-card:hover{{border-color:{_LINE_STRONG};box-shadow:{_SHADOW_HOVER};transform:translateY(-2px)}}
/* span 2 only where 2 columns can exist, else the card overflows its grid */
@media(min-width:720px){{.attribution-card.wide{{grid-column:span 2}}}}
.attribution-label{{display:block;font-size:.68rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:{_MUTED};margin:0 0 .6rem}}
.attribution-card p{{font-size:.86rem;line-height:1.6;color:{_INK};margin:0 0 .45rem;overflow-wrap:anywhere}}
.attribution-card p:last-child{{margin-bottom:0}}
.attribution-card code{{font-family:{_MONO};font-size:.78rem;background:{_TINT};border-radius:4px;padding:.1em .35em;overflow-wrap:anywhere}}
/* The named-graphs card stacks long DAV IRIs in <code> chips separated only by
   <br>. Left inline, each chip's tinted background wraps mid-IRI and the two
   graphs read as one run-on block. Scoped to <br>-separated paragraphs so
   prose paragraphs keep their trailing punctuation on the same line. */
.attribution-card p:has(br) > code{{display:inline-block;max-width:100%;padding:.3em .55em;margin-bottom:.3rem;line-height:1.5}}
.attribution-card a:not(.attribution-pill){{color:{_LINK};font-weight:500;text-decoration:none;overflow-wrap:anywhere}}
.attribution-card a:not(.attribution-pill):hover{{text-decoration:underline}}
.attribution-links{{display:flex;flex-wrap:wrap;gap:.45rem;margin:0 0 .65rem}}
.attribution-links:last-child{{margin-bottom:0}}
.attribution-pill{{display:inline-flex;align-items:center;background:{_TINT};border:1px solid transparent;border-radius:999px;padding:.32rem .8rem;font-size:.76rem;font-weight:600;color:{_LINK};text-decoration:none;white-space:nowrap;transition:border-color .2s,transform .2s}}
.attribution-pill:hover{{border-color:{_LINE_STRONG};transform:translateY(-1px);text-decoration:none}}

/* SPARQL workbench (footer_sparql_workbench) */
.sparql-launch{{position:relative;background:{_SURFACE};border:1px solid {_LINE};border-radius:14px;padding:1.6rem 1.5rem 1.4rem;box-shadow:{_SHADOW};overflow:hidden;min-width:0}}
.sparql-launch::before{{content:"";position:absolute;inset:0 0 auto 0;height:3px;background:linear-gradient(90deg,{_LINK},var(--accent, {_LINK}))}}
.sparql-head{{display:flex;justify-content:space-between;align-items:flex-start;gap:1.25rem;flex-wrap:wrap}}
.sparql-head h3{{font-size:1.15rem;letter-spacing:-.01em;margin:0 0 .35rem;color:{_INK}}}
.sparql-head p{{font-size:.86rem;line-height:1.55;color:{_MUTED};margin:0;max-width:62ch}}
.run-query{{background:{_LINK};color:{_ON_LINK};border:1px solid {_LINK};border-radius:10px;padding:.6rem 1.15rem;font-size:.86rem;font-weight:600;text-decoration:none;white-space:nowrap;flex:0 0 auto;transition:background .2s,transform .2s}}
.run-query:hover{{background:{_LINK_HOVER};border-color:{_LINK_HOVER};color:{_ON_LINK};text-decoration:none;transform:translateY(-1px)}}
.run-query:focus-visible{{outline:2px solid {_FOCUS};outline-offset:2px}}
.sparql-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,190px),1fr));gap:.75rem;margin:1.35rem 0 .9rem}}
.sparql-field{{display:flex;flex-direction:column;gap:.32rem;min-width:0;font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:{_MUTED}}}
.sparql-field select,.sparql-field input{{font:inherit;font-size:.82rem;font-weight:400;letter-spacing:normal;text-transform:none;color:{_INK};background:{_PAGE_BG};border:1px solid {_LINE};border-radius:8px;padding:.5rem .6rem;width:100%;min-width:0}}
.sparql-field select:focus-visible,.sparql-field input:focus-visible,.sparql-editor:focus-visible{{outline:2px solid {_FOCUS};outline-offset:1px;border-color:{_LINE_STRONG}}}
.sparql-field input[readonly]{{color:{_MUTED};background:{_BAND_BG};cursor:default}}
.sparql-editor{{display:block;width:100%;min-height:210px;resize:vertical;font-family:{_MONO};font-size:.8rem;line-height:1.65;tab-size:2;color:{_INK};background:{_PAGE_BG};border:1px solid {_LINE};border-radius:10px;padding:.9rem 1rem}}
.sparql-actions{{display:flex;flex-wrap:wrap;align-items:center;gap:.5rem;margin-top:.9rem;min-width:0}}
.sparql-actions button{{font:inherit;font-size:.78rem;font-weight:500;color:{_INK};background:{_SURFACE};border:1px solid {_LINE};border-radius:8px;padding:.42rem .9rem;cursor:pointer;transition:border-color .2s,background .2s}}
.sparql-actions button:hover{{background:{_BAND_BG};border-color:{_LINE_STRONG}}}
.sparql-actions button:focus-visible{{outline:2px solid {_FOCUS};outline-offset:2px}}
/* display on a class always beats the `hidden` attribute's UA rule, so a
   toggled-off control stays visible unless this guard is present. Has bitten
   this workbench before (footer-sparql-explorer-gate.ttl). */
.sparql-actions [hidden],.sparql-link-preview[hidden]{{display:none !important}}
/* #sparqlLinkPreview is filled with the full percent-encoded query URL.
   Unconstrained it wraps across a dozen lines and bleeds past the panel; keep
   it one truncating chip -- the href still carries the whole query. */
.sparql-link-preview{{display:inline-flex;align-items:center;max-width:100%;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:{_MONO};font-size:.74rem;font-weight:500;color:{_LINK};background:{_TINT};border:1px solid transparent;border-radius:999px;padding:.35rem .85rem;text-decoration:none}}
.sparql-link-preview:hover{{border-color:{_LINE_STRONG};text-decoration:none}}
.sparql-note{{font-size:.78rem;line-height:1.6;color:{_MUTED};margin-top:.9rem}}
.sparql-note code{{font-family:{_MONO};font-size:.74rem;background:{_TINT};border-radius:4px;padding:.1em .35em}}
@media(max-width:768px){{
  footer#sources{{padding:2.5rem 0 2rem}}
  .attribution-panel{{padding:0 1rem}}
  .sparql-launch{{padding:1.25rem 1rem 1.1rem;border-radius:12px}}
  .run-query{{width:100%;text-align:center}}
}}
""".strip()


def sparql_result_format(query: str) -> str:
    first = query.strip().split(None, 1)[0].upper()
    if first in {"DESCRIBE", "CONSTRUCT"}:
        return "text/x-html-nice-turtle"
    return "text/x-html+tr"


def sparql_live_url(query: str, endpoint: str = SPARQL_ENDPOINT) -> str:
    return (
        endpoint
        + "?default-graph-uri=&query="
        + quote(query, safe="")
        + "&format="
        + quote(sparql_result_format(query), safe="")
        + "&timeout=0&debug=on&run=+Run+Query+"
    )


@dataclass(frozen=True)
class HarnessContext:
    stem: str
    base_iri: str
    source_label: str
    source_entity_iri: str
    author_label: str
    author_entity_iri: str
    platform_label: str
    platform_entity_iri: str
    ttl_graph_iri: str
    jsonld_graph_iri: str
    markdown_file: str
    turtle_rel: str
    jsonld_rel: str


def kg_explorer_shell(stem: str, ttl_graph_iri: str) -> str:
    """Return the canonical KG Explorer shell.

    The companion generator must pair this shell with RDF-derived `kgData` and
    D3 behavior that creates resolver-backed SVG anchors for node labels and
    edge labels, uses sticky drag, and keeps the controls tray closed by
    default.
    """

    return f"""
<section id="kg">
  <div class="section-head">
    <h2>Knowledge Graph Explorer</h2>
    <p>Graph data is derived from the generated RDF entity and relationship model. Node and edge clicks use URIBurner resolver-backed IRIs.</p>
  </div>
  <div class="panel" id="kg-explorer" data-rdf-source="../rdf/{escape(stem)}.ttl" data-graph-iri="{escape(ttl_graph_iri)}">
    <div class="kg-shell">
      <div class="kg-header">
        <div>
          <h3>RDF Graph Workbench</h3>
          <p>Explore ontology terms, representative instances, query examples, provenance, and source entities.</p>
        </div>
        <div class="kg-header-actions">
          <button class="kg-control-toggle" id="kgControlsToggle" type="button" aria-expanded="false" aria-controls="kgToolbar">Controls</button>
          <span class="kg-count-badge" id="counts">0 nodes / 0 links</span>
        </div>
      </div>
      <div class="kg-toolbar" id="kgToolbar" hidden>
        <div class="kg-toolbar-main">
          <div class="kg-segment" role="group" aria-label="Mode"><button class="active" type="button" data-mode="Basic" aria-pressed="true">Basic</button><button type="button" data-mode="Advanced" aria-pressed="false">Advanced</button></div>
          <div class="kg-segment" role="group" aria-label="Density"><button class="active" type="button" data-density="Core" aria-pressed="true">Core</button><button type="button" data-density="Full" aria-pressed="false">Full</button></div>
          <div class="kg-segment" role="group" aria-label="Node type filters"><button class="kg-modality active" type="button" data-modality="instances" aria-pressed="true">Instances</button><button class="kg-modality" type="button" data-modality="classes" aria-pressed="false">Classes</button><button class="kg-modality" type="button" data-modality="properties" aria-pressed="false">Properties</button></div>
          <input id="nodeFilter" class="kg-search" placeholder="Search nodes" aria-label="Search graph nodes">
          <button class="kg-tool-button" id="kgCenter" type="button" data-advanced-control hidden>Center</button>
          <button id="kgFullscreen" type="button" data-advanced-control hidden>Fullscreen</button>
          <button id="kgSettings" type="button" data-advanced-control hidden aria-expanded="false" aria-controls="settingsPanel">Settings</button>
          <span class="kg-meta" id="kgState" role="status" aria-live="polite">Basic / Core</span>
        </div>
        <div class="settings" id="settingsPanel" hidden>
          <label class="settings-field">Charge <input id="charge" type="range" min="-600" max="-20" value="-180"></label>
          <label class="settings-field">Distance <input id="distance" type="range" min="20" max="220" value="72"></label>
          <label class="settings-wide">Predicate search <input id="predicateFilter" placeholder="hasPart, type, target"></label>
          <label class="settings-field">Predicate labels <select id="labelMode"><option selected>Predicates</option><option>Hidden</option></select></label>
          <label class="settings-wide">Resolver <select id="resolverPreference"><option value="describe">URIBurner describe</option><option value="direct">Direct IRI</option></select></label>
          <label class="settings-field">Arrows <select id="arrowStyle"><option value="directed">Directed</option><option value="none">Hidden</option></select></label>
          <label class="literal-control settings-field"><input id="literalToggle" type="checkbox" checked> Literals</label>
          <div class="settings-card predicate-card"><div class="settings-heading"><span class="settings-title">Predicate filter</span><div class="settings-actions-inline"><button id="predicateSelectAll" type="button">All</button><button id="predicateDeselectAll" type="button">None</button></div></div><div class="filter-list" id="edgeFilterList" role="group" aria-label="Predicate filters"></div></div>
          <div class="settings-card node-card"><span class="settings-title">Node filters</span><div class="chip-list" id="nodeFilterList" role="group" aria-label="Node filters"></div></div>
          <div class="settings-actions"><button id="clearGraphFilters" type="button">Clear filters</button><button id="closeSettings" type="button" aria-label="Close advanced settings">X</button></div>
        </div>
      </div>
      <div class="kg-stage"><svg id="kg-svg" role="img" aria-label="Knowledge graph visualization"></svg><p class="kg-note">Graph data embedded from companion RDF at generation time. The controls tray is closed by default; Advanced exposes settings and predicate filters.</p></div>
    </div>
  </div>
</section>""".strip()


def footer_sparql_workbench(ctx: HarnessContext) -> str:
    select_query = f"""PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?type (SAMPLE(?s) AS ?sampleEntity) (SAMPLE(?label) AS ?sampleLabel) (COUNT(?s) AS ?entityCount)
WHERE {{
  GRAPH <{ctx.ttl_graph_iri}> {{
    ?s rdf:type ?type .
    OPTIONAL {{ ?s rdfs:label ?label }}
  }}
}}
GROUP BY ?type
ORDER BY DESC(?entityCount)"""
    return f"""
<div class="sparql-launch" id="sparql-explorer">
  <div class="sparql-head">
    <div>
      <h3>Explore Knowledge Graph using SPARQL</h3>
      <p>Choose a named graph and query recipe, edit the SPARQL if needed, then open the encoded URIBurner query.</p>
    </div>
    <a id="sparqlBtn" class="run-query" href="{sparql_live_url(select_query)}" target="_blank" rel="noopener noreferrer">Run live query</a>
  </div>
  <div class="sparql-grid">
    <label class="sparql-field">Named graph<select id="sparqlGraph"><option value="{escape(ctx.ttl_graph_iri)}" selected>RDF Turtle graph</option><option value="{escape(ctx.jsonld_graph_iri)}">JSON-LD graph</option></select></label>
    <label class="sparql-field">Query recipe<select id="sparqlRecipe"><option value="select" selected>SELECT triples</option><option value="describe">DESCRIBE source article</option><option value="construct">CONSTRUCT compact graph</option></select></label>
    <label class="sparql-field">Result format<input id="sparqlFormat" value="text/x-html+tr" readonly></label>
  </div>
  <textarea id="sparqlText" class="sparql-editor" spellcheck="false" aria-label="Editable SPARQL query">{escape(select_query)}</textarea>
  <div class="sparql-actions"><button id="sparqlRefresh" type="button">Refresh live link</button><button id="sparqlCopy" type="button">Copy query</button><span id="sparqlLinkPreview" class="sparql-link-preview"></span></div>
  <p class="sparql-note">SELECT uses <code>text/x-html+tr</code>. DESCRIBE and CONSTRUCT use <code>text/x-html-nice-turtle</code>, matching the SPARQL format guidance in the skill contract.</p>
</div>""".strip()


def footer_sparql_script(source_article_iri: str, endpoint: str = SPARQL_ENDPOINT) -> str:
    return f"""
(() => {{
  const endpoint = {endpoint!r};
  const graph = document.getElementById('sparqlGraph');
  const recipe = document.getElementById('sparqlRecipe');
  const text = document.getElementById('sparqlText');
  const format = document.getElementById('sparqlFormat');
  const btn = document.getElementById('sparqlBtn');
  const preview = document.getElementById('sparqlLinkPreview');
  const refresh = document.getElementById('sparqlRefresh');
  const copy = document.getElementById('sparqlCopy');
  const source = {source_article_iri!r};
  function queryFor(kind, g) {{
    if (kind === 'describe') return 'DESCRIBE <' + source + '>\\nFROM <' + g + '>';
    if (kind === 'construct') return 'CONSTRUCT {{ ?s ?p ?o }}\\nWHERE {{\\n  GRAPH <' + g + '> {{\\n    ?s ?p ?o .\\n    FILTER(?p IN (<http://schema.org/about>, <http://schema.org/mentions>, <http://schema.org/hasPart>, <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>))\\n  }}\\n}}\\nLIMIT 100';
    return 'PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\\n\\nSELECT ?type (SAMPLE(?s) AS ?sampleEntity) (SAMPLE(?label) AS ?sampleLabel) (COUNT(?s) AS ?entityCount)\\nWHERE {{\\n  GRAPH <' + g + '> {{\\n    ?s rdf:type ?type .\\n    OPTIONAL {{ ?s rdfs:label ?label }}\\n  }}\\n}}\\nGROUP BY ?type\\nORDER BY DESC(?entityCount)';
  }}
  function fmtFor(q) {{
    const first = q.trim().split(/\\s+/, 1)[0].toUpperCase();
    return first === 'DESCRIBE' || first === 'CONSTRUCT' ? 'text/x-html-nice-turtle' : 'text/x-html+tr';
  }}
  function syncText() {{ text.value = queryFor(recipe.value, graph.value); update(); }}
  function update() {{
    const q = text.value.trim(), fmt = fmtFor(q);
    format.value = fmt;
    btn.href = endpoint + '?default-graph-uri=&query=' + encodeURIComponent(q) + '&format=' + encodeURIComponent(fmt) + '&timeout=0&debug=on&run=+Run+Query+';
    preview.textContent = btn.href;
  }}
  graph.addEventListener('change', syncText);
  recipe.addEventListener('change', syncText);
  text.addEventListener('input', update);
  refresh.addEventListener('click', update);
  copy.addEventListener('click', async () => {{
    await navigator.clipboard?.writeText(text.value);
    copy.textContent = 'Copied';
    setTimeout(() => copy.textContent = 'Copy query', 1200);
  }});
  syncText();
}})();""".strip()


def attribution_footer(
    ctx: HarnessContext,
    skills_html: str,
    environment_html: str,
    include_markdown: bool = True,
) -> str:
    """Render the single canonical attribution surface.

    include_markdown=False for runs that produce RDF + HTML only. The footer
    previously advertised a Markdown companion unconditionally, so any such run
    shipped a dead pill link to a .md that was never written, plus a provenance
    card claiming Markdown had been generated. Both are factual claims about
    the artifact, so they track what was actually produced.
    """
    md_pill = (
        f'<a class="attribution-pill" href="{escape(ctx.markdown_file)}" target="_blank" rel="noopener noreferrer">Markdown</a>'
        if include_markdown
        else ""
    )
    provenance = (
        "RDF, Markdown, HTML, SPARQL examples, and KG Explorer data are generated from the companion graph."
        if include_markdown
        else "RDF, HTML, SPARQL examples, and KG Explorer data are generated from the companion graph. No Markdown companion was generated for this artifact."
    )
    return f"""
<footer id="sources">
  <section class="attribution-panel">
    <div class="attribution-inner">
      <div class="section-head"><h2>Sources And Attribution</h2><p>This collection is derived from source material, generated RDF, and the RDF infographic harness contract.</p></div>
      <div class="attribution-grid">
        <article class="attribution-card wide"><span class="attribution-label">Source material</span><p><a class="entity-link" href="{resolver_url(ctx.source_entity_iri)}" target="_blank" rel="noopener noreferrer">{escape(ctx.source_label)}</a> by <a class="entity-link" href="{resolver_url(ctx.author_entity_iri)}" target="_blank" rel="noopener noreferrer">{escape(ctx.author_label)}</a>, published on <a class="entity-link" href="{resolver_url(ctx.platform_entity_iri)}" target="_blank" rel="noopener noreferrer">{escape(ctx.platform_label)}</a>. Entity IRIs use the canonical article URL as the document base.</p></article>
        <article class="attribution-card"><span class="attribution-label">Companion files</span><div class="attribution-links"><a class="attribution-pill" href="{escape(ctx.turtle_rel)}" target="_blank" rel="noopener noreferrer">RDF Turtle</a><a class="attribution-pill" href="{escape(ctx.jsonld_rel)}" target="_blank" rel="noopener noreferrer">JSON-LD</a>{md_pill}</div><p>All files share the <code>{escape(ctx.stem)}</code> artifact stem.</p></article>
        <article class="attribution-card"><span class="attribution-label">Skills used</span>{skills_html}</article>
        <article class="attribution-card wide"><span class="attribution-label">Generation environment</span>{environment_html}</article>
        <article class="attribution-card"><span class="attribution-label">Linked Data runtime</span><p>Semantic links use <a href="https://linkeddata.uriburner.com/fct" target="_blank" rel="noopener noreferrer">URIBurner describe</a>; live queries target <a href="{SPARQL_ENDPOINT}" target="_blank" rel="noopener noreferrer">URIBurner SPARQL</a> over <a href="https://virtuoso.openlinksw.com/" target="_blank" rel="noopener noreferrer">OpenLink Virtuoso</a>. The KG Explorer uses <a href="https://d3js.org/" target="_blank" rel="noopener noreferrer">D3.js</a>.</p></article>
        <article class="attribution-card"><span class="attribution-label">Named graphs</span><p><code>{escape(ctx.ttl_graph_iri)}</code><br><code>{escape(ctx.jsonld_graph_iri)}</code></p></article>
        <article class="attribution-card"><span class="attribution-label">Resolver pattern</span><p>Visible semantic links route through <code>https://linkeddata.uriburner.com/describe/?url={{encodedIRI}}</code>.</p></article>
        <article class="attribution-card"><span class="attribution-label">Extraction provenance</span><p>{provenance}</p></article>
      </div>
      {footer_sparql_workbench(ctx)}
    </div>
  </section>
</footer>""".strip()
