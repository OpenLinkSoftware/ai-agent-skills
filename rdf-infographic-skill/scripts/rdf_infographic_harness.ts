/**
 * Reusable RDF infographic harness helpers — TypeScript edition (no npm deps).
 * Identical behavior to rdf_infographic_harness.py.
 *
 * Importable module — no CLI entry point.
 * Usage: import { resolverUrl, kgExplorerShell, … } from "./rdf_infographic_harness.ts";
 */

export const RESOLVER = "https://linkeddata.uriburner.com/describe/?url=";
export const SPARQL_ENDPOINT = "https://linkeddata.uriburner.com/sparql";

export interface HarnessContext {
  stem: string;
  baseIri: string;
  sourceLabel: string;
  sourceEntityIri: string;
  authorLabel: string;
  authorEntityIri: string;
  platformLabel: string;
  platformEntityIri: string;
  ttlGraphIri: string;
  jsonldGraphIri: string;
  markdownFile: string;
  turtleRel: string;
  jsonldRel: string;
}

function escape(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function resolverUrl(iri: string): string {
  return RESOLVER + encodeURIComponent(iri);
}

export function sparqlResultFormat(query: string): string {
  const first = query.trim().split(/\s+/, 1)[0].toUpperCase();
  return first === "DESCRIBE" || first === "CONSTRUCT"
    ? "text/x-html-nice-turtle"
    : "text/x-html+tr";
}

export function sparqlLiveUrl(
  query: string,
  endpoint: string = SPARQL_ENDPOINT,
): string {
  return (
    endpoint +
    "?default-graph-uri=&query=" +
    encodeURIComponent(query) +
    "&format=" +
    encodeURIComponent(sparqlResultFormat(query)) +
    "&timeout=0&debug=on&run=+Run+Query+"
  );
}

export function kgExplorerShell(stem: string, ttlGraphIri: string): string {
  return `<section id="kg">
  <div class="section-head">
    <h2>Knowledge Graph Explorer</h2>
    <p>Graph data is derived from the generated RDF entity and relationship model. Node and edge clicks use URIBurner resolver-backed IRIs.</p>
  </div>
  <div class="panel" id="kg-explorer" data-rdf-source="../rdf/${escape(stem)}.ttl" data-graph-iri="${escape(ttlGraphIri)}">
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
</section>`;
}

export function footerSparqlWorkbench(ctx: HarnessContext): string {
  const selectQuery = `PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?type (SAMPLE(?s) AS ?sampleEntity) (SAMPLE(?label) AS ?sampleLabel) (COUNT(?s) AS ?entityCount)
WHERE {
  GRAPH <${ctx.ttlGraphIri}> {
    ?s rdf:type ?type .
    OPTIONAL { ?s rdfs:label ?label }
  }
}
GROUP BY ?type
ORDER BY DESC(?entityCount)`;

  return `<div class="sparql-launch" id="sparql-explorer">
  <div class="sparql-head">
    <div>
      <h3>Explore Knowledge Graph using SPARQL</h3>
      <p>Choose a named graph and query recipe, edit the SPARQL if needed, then open the encoded URIBurner query.</p>
    </div>
    <a id="sparqlBtn" class="run-query" href="${sparqlLiveUrl(selectQuery)}" target="_blank" rel="noopener noreferrer">Run live query</a>
  </div>
  <div class="sparql-grid">
    <label class="sparql-field">Named graph<select id="sparqlGraph"><option value="${escape(ctx.ttlGraphIri)}" selected>RDF Turtle graph</option><option value="${escape(ctx.jsonldGraphIri)}">JSON-LD graph</option></select></label>
    <label class="sparql-field">Query recipe<select id="sparqlRecipe"><option value="select" selected>SELECT triples</option><option value="describe">DESCRIBE source article</option><option value="construct">CONSTRUCT compact graph</option></select></label>
    <label class="sparql-field">Result format<input id="sparqlFormat" value="text/x-html+tr" readonly></label>
  </div>
  <textarea id="sparqlText" class="sparql-editor" spellcheck="false" aria-label="Editable SPARQL query">${escape(selectQuery)}</textarea>
  <div class="sparql-actions"><button id="sparqlRefresh" type="button">Refresh live link</button><button id="sparqlCopy" type="button">Copy query</button><span id="sparqlLinkPreview" class="sparql-link-preview"></span></div>
  <p class="sparql-note">SELECT uses <code>text/x-html+tr</code>. DESCRIBE and CONSTRUCT use <code>text/x-html-nice-turtle</code>, matching the SPARQL format guidance in the skill contract.</p>
</div>`;
}

export function footerSparqlScript(
  sourceArticleIri: string,
  endpoint: string = SPARQL_ENDPOINT,
): string {
  return `(() => {
  const endpoint = ${JSON.stringify(endpoint)};
  const graph = document.getElementById('sparqlGraph');
  const recipe = document.getElementById('sparqlRecipe');
  const text = document.getElementById('sparqlText');
  const format = document.getElementById('sparqlFormat');
  const btn = document.getElementById('sparqlBtn');
  const preview = document.getElementById('sparqlLinkPreview');
  const refresh = document.getElementById('sparqlRefresh');
  const copy = document.getElementById('sparqlCopy');
  const source = ${JSON.stringify(sourceArticleIri)};
  function queryFor(kind, g) {
    if (kind === 'describe') return 'DESCRIBE <' + source + '>\\nFROM <' + g + '>';
    if (kind === 'construct') return 'CONSTRUCT { ?s ?p ?o }\\nWHERE {\\n  GRAPH <' + g + '> {\\n    ?s ?p ?o .\\n    FILTER(?p IN (<http://schema.org/about>, <http://schema.org/mentions>, <http://schema.org/hasPart>, <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>))\\n  }\\n}\\nLIMIT 100';
    return 'PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\\n\\nSELECT ?type (SAMPLE(?s) AS ?sampleEntity) (SAMPLE(?label) AS ?sampleLabel) (COUNT(?s) AS ?entityCount)\\nWHERE {\\n  GRAPH <' + g + '> {\\n    ?s rdf:type ?type .\\n    OPTIONAL { ?s rdfs:label ?label }\\n  }\\n}\\nGROUP BY ?type\\nORDER BY DESC(?entityCount)';
  }
  function fmtFor(q) {
    const first = q.trim().split(/\\s+/, 1)[0].toUpperCase();
    return first === 'DESCRIBE' || first === 'CONSTRUCT' ? 'text/x-html-nice-turtle' : 'text/x-html+tr';
  }
  function syncText() { text.value = queryFor(recipe.value, graph.value); update(); }
  function update() {
    const q = text.value.trim(), fmt = fmtFor(q);
    format.value = fmt;
    btn.href = endpoint + '?default-graph-uri=&query=' + encodeURIComponent(q) + '&format=' + encodeURIComponent(fmt) + '&timeout=0&debug=on&run=+Run+Query+';
    preview.textContent = btn.href;
  }
  graph.addEventListener('change', syncText);
  recipe.addEventListener('change', syncText);
  text.addEventListener('input', update);
  refresh.addEventListener('click', update);
  copy.addEventListener('click', async () => {
    await navigator.clipboard?.writeText(text.value);
    copy.textContent = 'Copied';
    setTimeout(() => copy.textContent = 'Copy query', 1200);
  });
  syncText();
})();`;
}

export function attributionFooter(
  ctx: HarnessContext,
  skillsHtml: string,
  environmentHtml: string,
): string {
  return `<footer id="sources">
  <section class="attribution-panel">
    <div class="attribution-inner">
      <div class="section-head"><h2>Sources And Attribution</h2><p>This collection is derived from source material, generated RDF, and the RDF infographic harness contract.</p></div>
      <div class="attribution-grid">
        <article class="attribution-card wide"><span class="attribution-label">Source material</span><p><a class="entity-link" href="${resolverUrl(ctx.sourceEntityIri)}" target="_blank" rel="noopener noreferrer">${escape(ctx.sourceLabel)}</a> by <a class="entity-link" href="${resolverUrl(ctx.authorEntityIri)}" target="_blank" rel="noopener noreferrer">${escape(ctx.authorLabel)}</a>, published on <a class="entity-link" href="${resolverUrl(ctx.platformEntityIri)}" target="_blank" rel="noopener noreferrer">${escape(ctx.platformLabel)}</a>. Entity IRIs use the canonical article URL as the document base.</p></article>
        <article class="attribution-card"><span class="attribution-label">Companion files</span><div class="attribution-links"><a class="attribution-pill" href="${escape(ctx.turtleRel)}" target="_blank" rel="noopener noreferrer">RDF Turtle</a><a class="attribution-pill" href="${escape(ctx.jsonldRel)}" target="_blank" rel="noopener noreferrer">JSON-LD</a><a class="attribution-pill" href="${escape(ctx.markdownFile)}" target="_blank" rel="noopener noreferrer">Markdown</a></div><p>All files share the <code>${escape(ctx.stem)}</code> artifact stem.</p></article>
        <article class="attribution-card"><span class="attribution-label">Skills used</span>${skillsHtml}</article>
        <article class="attribution-card wide"><span class="attribution-label">Generation environment</span>${environmentHtml}</article>
        <article class="attribution-card"><span class="attribution-label">Linked Data runtime</span><p>Semantic links use <a href="https://linkeddata.uriburner.com/fct" target="_blank" rel="noopener noreferrer">URIBurner describe</a>; live queries target <a href="${SPARQL_ENDPOINT}" target="_blank" rel="noopener noreferrer">URIBurner SPARQL</a> over <a href="https://virtuoso.openlinksw.com/" target="_blank" rel="noopener noreferrer">OpenLink Virtuoso</a>. The KG Explorer uses <a href="https://d3js.org/" target="_blank" rel="noopener noreferrer">D3.js</a>.</p></article>
        <article class="attribution-card"><span class="attribution-label">Named graphs</span><p><code>${escape(ctx.ttlGraphIri)}</code><br><code>${escape(ctx.jsonldGraphIri)}</code></p></article>
        <article class="attribution-card"><span class="attribution-label">Resolver pattern</span><p>Visible semantic links route through <code>https://linkeddata.uriburner.com/describe/?url={encodedIRI}</code>.</p></article>
        <article class="attribution-card"><span class="attribution-label">Extraction provenance</span><p>RDF, Markdown, HTML, SPARQL examples, and KG Explorer data are generated from the companion graph.</p></article>
      </div>
      ${footerSparqlWorkbench(ctx)}
    </div>
  </section>
</footer>`;
}
