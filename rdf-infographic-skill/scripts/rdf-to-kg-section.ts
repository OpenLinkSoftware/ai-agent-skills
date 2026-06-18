/**
 * rdf-to-kg-section.ts — Generate a self-contained D3 v7 KG Explorer HTML section from RDF/TTL input.
 * TypeScript edition (Node.js ≥ 18, requires n3). Identical behavior to rdf-to-kg-section.py.
 *
 * Install: npm install (from rdf-infographic-skill/scripts/)
 *
 * Usage:
 *   npx tsx rdf-to-kg-section.ts <input.ttl> [options]
 *
 * Options:
 *   --base-iri <IRI>    Override base IRI for resolver links
 *   --core-max <N>      Max nodes in 'core' density view (default: 30)
 *   --output <file>     Write output to file instead of stdout
 *   --format <fmt>      n3 parse format: Turtle, N-Triples, N3 (default: auto-detect)
 *   --resolver <url>    URIBurner describe URL prefix
 *   --title <text>      Section heading (default: 'Knowledge Graph Explorer')
 *   --json-only         Output kgData JSON only (no HTML wrapper)
 */

import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { DataFactory, Parser, Store } from "n3";

const { namedNode } = DataFactory;

// ── Namespaces ────────────────────────────────────────────────────────────────

const RDF_TYPE   = namedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type");
const RDFS_LABEL = namedNode("http://www.w3.org/2000/01/rdf-schema#label");
const RDFS_COMMENT = namedNode("http://www.w3.org/2000/01/rdf-schema#comment");

const SCHEMA_NAME        = namedNode("http://schema.org/name");
const SCHEMAS_NAME       = namedNode("https://schema.org/name");
const SCHEMA_DESCRIPTION = namedNode("http://schema.org/description");
const SCHEMAS_DESCRIPTION = namedNode("https://schema.org/description");
const SCHEMA_ABSTRACT    = namedNode("http://schema.org/abstract");
const DCTERMS_TITLE      = namedNode("http://purl.org/dc/terms/title");
const DC_TITLE           = namedNode("http://purl.org/dc/elements/1.1/title");
const FOAF_NAME          = namedNode("http://xmlns.com/foaf/0.1/name");
const SKOS_PREF_LABEL    = namedNode("http://www.w3.org/2004/02/skos/core#prefLabel");
const DC_DESCRIPTION     = namedNode("http://purl.org/dc/elements/1.1/description");
const DCTERMS_DESCRIPTION = namedNode("http://purl.org/dc/terms/description");

const PROP_TYPES = new Set([
  "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property",
  "http://www.w3.org/2002/07/owl#ObjectProperty",
  "http://www.w3.org/2002/07/owl#DatatypeProperty",
  "http://www.w3.org/2002/07/owl#AnnotationProperty",
  "http://www.w3.org/2002/07/owl#TransitiveProperty",
  "http://www.w3.org/2002/07/owl#SymmetricProperty",
  "http://www.w3.org/2002/07/owl#FunctionalProperty",
  "http://www.w3.org/2002/07/owl#InverseFunctionalProperty",
]);
const CLASS_TYPES = new Set([
  "http://www.w3.org/2000/01/rdf-schema#Class",
  "http://www.w3.org/2002/07/owl#Class",
]);
const PERSON_TYPES = new Set([
  "http://schema.org/Person", "https://schema.org/Person",
  "http://xmlns.com/foaf/0.1/Person",
]);
const ORG_TYPES = new Set([
  "http://schema.org/Organization", "https://schema.org/Organization",
  "http://schema.org/Corporation",  "https://schema.org/Corporation",
  "http://xmlns.com/foaf/0.1/Organization",
]);

const SKIP_PREDS = new Set([
  "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
  "http://www.w3.org/2000/01/rdf-schema#domain",
  "http://www.w3.org/2000/01/rdf-schema#range",
  "http://www.w3.org/2002/07/owl#sameAs",
  "http://www.w3.org/2002/07/owl#equivalentClass",
  "http://www.w3.org/2002/07/owl#equivalentProperty",
  "http://www.w3.org/2000/01/rdf-schema#subClassOf",
  "http://www.w3.org/2000/01/rdf-schema#subPropertyOf",
  "http://www.w3.org/2000/01/rdf-schema#isDefinedBy",
  "http://www.w3.org/2000/01/rdf-schema#seeAlso",
]);

// ── Format detection ──────────────────────────────────────────────────────────

function autoFormat(path: string): string {
  const ext = path.toLowerCase().split(".").pop() ?? "";
  return ({ ttl: "Turtle", n3: "N3", nt: "N-Triples", rdf: "application/rdf+xml", xml: "application/rdf+xml" } as Record<string, string>)[ext] ?? "Turtle";
}

// ── Label / description helpers ───────────────────────────────────────────────

function shortName(uri: string): string {
  if (uri.includes("#")) {
    const frag = uri.split("#").pop();
    if (frag) return frag;
  }
  const parts = uri.replace(/\/$/, "").split("/");
  return parts[parts.length - 1] ?? uri;
}

function camelSplit(s: string): string {
  s = s.replace(/([A-Z]+)([A-Z][a-z])/g, "$1 $2");
  s = s.replace(/([a-z\d])([A-Z])/g, "$1 $2");
  return s.replace(/_/g, " ").replace(/-/g, " ").trim();
}

function firstLiteral(store: Store, subject: ReturnType<typeof namedNode>, ...preds: ReturnType<typeof namedNode>[]): string {
  for (const pred of preds) {
    for (const obj of store.getObjects(subject, pred, null)) {
      if (obj.termType === "Literal") {
        const v = obj.value.trim();
        if (v) return v;
      }
    }
  }
  return "";
}

function getLabel(store: Store, uri: string): string {
  const node = namedNode(uri);
  return (
    firstLiteral(store, node, RDFS_LABEL, SCHEMA_NAME, SCHEMAS_NAME, DCTERMS_TITLE, DC_TITLE, FOAF_NAME, SKOS_PREF_LABEL) ||
    camelSplit(shortName(uri))
  );
}

function getDesc(store: Store, uri: string): string {
  const node = namedNode(uri);
  const d = firstLiteral(store, node, RDFS_COMMENT, SCHEMA_DESCRIPTION, SCHEMAS_DESCRIPTION, SCHEMA_ABSTRACT, DC_DESCRIPTION, DCTERMS_DESCRIPTION);
  return d.slice(0, 200);
}

function classifyType(store: Store, uri: string): string {
  const types = new Set(store.getObjects(namedNode(uri), RDF_TYPE, null).map(t => t.value));
  if ([...types].some(t => PROP_TYPES.has(t)))   return "prop";
  if ([...types].some(t => CLASS_TYPES.has(t)))  return "class";
  if ([...types].some(t => PERSON_TYPES.has(t))) return "person";
  if ([...types].some(t => ORG_TYPES.has(t)))    return "org";
  return "inst";
}

// ── Graph extraction ──────────────────────────────────────────────────────────

interface UriNode {
  id: string; label: string; type: string; desc: string; radius: number; _deg: number;
}

function extractGraphData(store: Store): { uriNodes: Map<string, UriNode>; links: Array<{ source: string; target: string; label: string }> } {
  const uriNodes = new Map<string, UriNode>();

  function ensure(uri: string): UriNode {
    if (!uriNodes.has(uri)) {
      uriNodes.set(uri, { id: uri, label: getLabel(store, uri), type: classifyType(store, uri), desc: getDesc(store, uri), radius: 18, _deg: 0 });
    }
    return uriNodes.get(uri)!;
  }

  const links: Array<{ source: string; target: string; label: string }> = [];

  for (const quad of store) {
    const { subject: s, predicate: p, object: o } = quad;
    if (s.termType !== "NamedNode" || o.termType !== "NamedNode") continue;
    if (SKIP_PREDS.has(p.value)) continue;
    const predLabel = camelSplit(shortName(p.value));
    ensure(s.value)._deg++;
    ensure(o.value)._deg++;
    links.push({ source: s.value, target: o.value, label: predLabel });
  }

  // Ensure isolated subject nodes appear
  for (const quad of store) {
    if (quad.subject.termType === "NamedNode") ensure(quad.subject.value);
  }

  return { uriNodes, links };
}

// ── kgData builder ────────────────────────────────────────────────────────────

interface KgDensityData { nodes: Omit<UriNode, "_deg">[]; links: Array<{ source: string; target: string; label: string }> }

function buildKgdata(uriNodes: Map<string, UriNode>, links: Array<{ source: string; target: string; label: string }>, coreMax = 30): { core: KgDensityData; full: KgDensityData } {
  const linkedIds = new Set(links.flatMap(l => [l.source, l.target]));
  const connected = [...uriNodes.values()].filter(n => linkedIds.has(n.id));
  const clean = (n: UriNode): Omit<UriNode, "_deg"> => { const { _deg, ...rest } = n; return rest; };

  const fullNodes = connected.map(clean);
  const fullLinks = [...links];

  const sortedByDeg = [...connected].sort((a, b) => b._deg - a._deg);
  const coreIds = new Set(sortedByDeg.slice(0, coreMax).map(n => n.id));
  const coreNodes = sortedByDeg.slice(0, coreMax).map(clean);
  const coreLinks = links.filter(l => coreIds.has(l.source) && coreIds.has(l.target));

  return { core: { nodes: coreNodes, links: coreLinks }, full: { nodes: fullNodes, links: fullLinks } };
}

// ── Base IRI derivation ───────────────────────────────────────────────────────

function deriveBaseIri(uriNodes: Map<string, UriNode>): string {
  if (!uriNodes.size) return "https://example.org/";
  const ns: string[] = [];
  for (const uri of uriNodes.keys()) {
    if (uri.includes("#")) ns.push(uri.split("#")[0] + "#");
    else {
      const parts = uri.replace(/\/$/, "").split("/");
      parts.pop();
      if (parts.length) ns.push(parts.join("/") + "/");
    }
  }
  if (!ns.length) return "https://example.org/";
  const counts = new Map<string, number>();
  for (const n of ns) counts.set(n, (counts.get(n) ?? 0) + 1);
  return [...counts.entries()].sort((a, b) => b[1] - a[1])[0][0];
}

// ── Embedded CSS ──────────────────────────────────────────────────────────────

const CSS = `<style id="kg-section-styles">
/* KG Explorer — self-contained (CSS vars fall back gracefully outside a harness page) */
#kg-explorer{background:var(--panel,#111827);border:1px solid var(--line-strong,#334155);border-radius:var(--radius,12px);overflow:hidden;margin-bottom:1rem;position:relative}
#kg-explorer.kg-active{border-color:var(--accent,#00b2c2);box-shadow:0 0 0 3px rgba(0,178,194,0.2)}
.kg-toolbar,#kgToolbar{display:flex;flex-wrap:wrap;gap:6px;padding:10px 14px;background:var(--panel-strong,#1e293b);border-bottom:1px solid var(--line,#1e293b);align-items:center}
.kg-toolbar button,.kg-btn{background:var(--panel,#111827);border:1px solid var(--line,#1e293b);border-radius:8px;padding:5px 11px;font-size:.75rem;cursor:pointer;color:var(--ink,#e2e8f0);font-weight:500;transition:all .2s}
.kg-toolbar button:hover,.kg-btn:hover{border-color:var(--accent,#00b2c2);background:rgba(0,178,194,.07)}
.kg-toolbar button.active,.kg-btn.active{background:var(--accent,#00b2c2);color:#fff;border-color:var(--accent,#00b2c2)}
.kg-toolbar .sep,.kg-sep{width:1px;height:20px;background:var(--line,#1e293b);margin:0 4px}
.kg-toolbar input[type="search"],#kg-search{background:var(--panel,#111827);border:1px solid var(--line,#1e293b);border-radius:8px;padding:5px 12px;font-size:.75rem;color:var(--ink,#e2e8f0);width:150px}
.kg-toolbar input[type="search"]:focus,#kg-search:focus{outline:none;border-color:var(--accent,#00b2c2)}
.kg-toolbar .ml-auto{margin-left:auto;display:flex;gap:3px}
.kg-toolbar .ml-auto button{background:transparent;border:1px solid transparent;padding:5px 8px;font-size:.95rem;color:var(--muted,#64748b)}
.kg-toolbar .ml-auto button:hover{color:var(--accent,#00b2c2);background:rgba(0,178,194,.08);border-color:transparent}
.kg-stats,#kg-stats{font-size:.68rem;color:var(--muted,#64748b);background:var(--panel-strong,#1e293b);padding:3px 10px;border-radius:20px;border:1px solid var(--line,#1e293b);white-space:nowrap}
#kg-svg-container{width:100%;height:480px;position:relative;cursor:grab;overflow:hidden}
#kg-svg,#kg-svg-container svg{width:100%;height:100%;display:block}
.kg-zoom-hint{position:absolute;top:12px;left:50%;transform:translateX(-50%);background:rgba(0,178,194,.9);color:#fff;padding:5px 16px;border-radius:24px;font-size:.68rem;font-weight:600;opacity:0;pointer-events:none;transition:opacity .3s;z-index:10}
#kg-explorer.kg-active .kg-zoom-hint{opacity:1}
#kg-legend{display:flex;flex-wrap:wrap;gap:.4rem;padding:.5rem .75rem;border-top:1px solid var(--line,#1e293b);background:var(--panel-strong,#1e293b);align-items:center}
.legend-item{display:flex;align-items:center;gap:.25rem;font-size:.72rem;color:var(--muted,#64748b);cursor:pointer}
.legend-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.legend-item.dimmed{opacity:.35}
#kg-settings{position:absolute;top:0;right:-390px;width:380px;height:100%;background:var(--panel,#111827);border-left:1px solid var(--line,#1e293b);box-shadow:-8px 0 40px rgba(0,0,0,.3);z-index:50;padding:18px;overflow-y:auto;transition:right .35s cubic-bezier(.16,1,.3,1)}
#kg-settings.open{right:0}
#kg-settings-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid var(--line,#1e293b)}
#kg-settings-header h4{font-size:.9rem;font-weight:700;color:var(--ink,#e2e8f0);margin:0}
#kg-settings-close{background:none;border:1px solid var(--line,#1e293b);border-radius:8px;cursor:pointer;font-size:.9rem;color:var(--muted,#64748b);padding:4px 10px;transition:all .2s}
.kg-sg{margin-bottom:14px}
.kg-sg>label:first-child{display:block;font-size:.68rem;font-weight:700;color:var(--muted,#64748b);text-transform:uppercase;letter-spacing:.07em;margin-bottom:5px}
.kg-sg input[type="range"]{width:100%;accent-color:var(--accent,#00b2c2);margin:2px 0}
.kg-sg .rval{font-size:.67rem;color:var(--muted,#64748b)}
.kg-sg select{background:var(--panel-strong,#1e293b);border:1px solid var(--line,#1e293b);border-radius:6px;padding:5px 8px;font-size:.75rem;color:var(--ink,#e2e8f0);width:100%}
#pred-filters{display:flex;flex-direction:column;gap:3px;max-height:140px;overflow-y:auto;font-size:.73rem;color:var(--ink,#e2e8f0);padding:4px 0}
#pred-filters label{display:flex;align-items:center;gap:6px;padding:2px 0;cursor:pointer}
#pred-filters input{accent-color:var(--accent,#00b2c2)}
#node-type-chips{display:flex;flex-wrap:wrap;gap:5px}
#node-type-chips button{border-radius:20px;padding:4px 12px;font-size:.7rem;font-weight:600;cursor:pointer;border:1px solid;transition:all .2s}
.literal-row{display:flex;gap:6px;align-items:center}
#literal-filter{flex:1;background:var(--panel-strong,#1e293b);border:1px solid var(--line,#1e293b);border-radius:6px;padding:5px 8px;font-size:.73rem;color:var(--ink,#e2e8f0)}
select.kg-select{background:var(--panel,#111827);border:1px solid var(--line-strong,#334155);color:var(--ink,#e2e8f0);border-radius:4px;padding:.2rem .5rem;font-size:.78rem}
</style>`;

// ── Embedded HTML template ────────────────────────────────────────────────────

function buildHtml(title: string): string {
  return `<span id="settings-panel" style="display:none"></span>
<section id="kg-section">
  <h2 style="font-size:1.1rem;font-weight:700;margin:0 0 .5rem;color:var(--ink,#e2e8f0)">${title}</h2>
  <div id="kg-explorer">
    <div class="kg-toolbar" id="kgToolbar">
      <button id="btn-basic"   class="active" onclick="setMode('basic')">Basic</button>
      <button id="btn-advanced"              onclick="setMode('advanced')">Advanced</button>
      <div class="sep"></div>
      <button id="btn-core" class="active" onclick="setDensity('core')">Core</button>
      <button id="btn-full"               onclick="setDensity('full')">Full</button>
      <div class="sep"></div>
      <input type="search" id="kg-search" placeholder="Search nodes…" oninput="render()">
      <span class="kg-stats" id="kg-stats">— nodes / — links</span>
      <div class="ml-auto">
        <button onclick="centerGraph()" title="Center graph">⊙</button>
        <button onclick="toggleFullscreen()" title="Fullscreen">⛶</button>
        <button id="btn-settings" aria-expanded="false" onclick="toggleSettings()" title="Settings">⚙</button>
      </div>
    </div>
    <div id="kg-svg-container">
      <svg id="kg-svg"></svg>
      <div class="kg-zoom-hint">Click outside to release zoom</div>
    </div>
    <div id="kg-legend"></div>
    <div id="kg-settings">
      <div id="kg-settings-header">
        <h4>Graph Settings</h4>
        <button id="kg-settings-close" onclick="toggleSettings()">✕ Close</button>
      </div>
      <div class="kg-sg">
        <label>Charge strength</label>
        <input type="range" id="charge-slider" min="-800" max="-50" value="-400"
               oninput="document.getElementById('charge-val').textContent=this.value;updatePhysics()">
        <span class="rval">Value: <span id="charge-val">-400</span></span>
      </div>
      <div class="kg-sg">
        <label>Link distance</label>
        <input type="range" id="dist-slider" min="30" max="300" value="90"
               oninput="document.getElementById('dist-val').textContent=this.value+'px';updatePhysics()">
        <span class="rval">Value: <span id="dist-val">90px</span></span>
      </div>
      <div class="kg-sg">
        <label style="display:flex;align-items:center;gap:6px;text-transform:none;font-size:.78rem">
          <input type="checkbox" id="physics-enabled" checked onchange="updatePhysics()"> Enable physics
        </label>
      </div>
      <div class="kg-sg" data-advanced-control style="display:none">
        <label>Predicate display</label>
        <select id="pred-display" onchange="render()">
          <option value="labels">Labels</option>
          <option value="icons">Icons only</option>
        </select>
      </div>
      <div class="kg-sg">
        <label>Resolver</label>
        <select id="kg-resolver" onchange="render()">
          <option value="uriburner">URIBurner Describe</option>
          <option value="none">Raw IRI</option>
        </select>
      </div>
      <div class="kg-sg">
        <label>Arrow style</label>
        <select id="arrow-style" onchange="render()">
          <option value="directed">Directed</option>
          <option value="single">Dedup single</option>
          <option value="line">Lines only</option>
        </select>
      </div>
      <div class="kg-sg">
        <label>Node types</label>
        <div id="node-type-chips"></div>
        <div style="display:flex;gap:6px;margin-top:5px">
          <button class="kg-btn" onclick="setNodeTypeAll(true)"  style="font-size:.68rem;padding:3px 8px">All</button>
          <button class="kg-btn" onclick="setNodeTypeAll(false)" style="font-size:.68rem;padding:3px 8px">None</button>
        </div>
      </div>
      <div class="kg-sg" data-advanced-control style="display:none">
        <label>Predicates</label>
        <div id="pred-filters"></div>
        <div style="display:flex;gap:6px;margin-top:5px">
          <button class="kg-btn" onclick="setPredAll(true)"  style="font-size:.68rem;padding:3px 8px">All</button>
          <button class="kg-btn" onclick="setPredAll(false)" style="font-size:.68rem;padding:3px 8px">None</button>
        </div>
      </div>
      <div class="kg-sg" data-advanced-control style="display:none">
        <label>Literal / label filter</label>
        <div class="literal-row">
          <input type="text" id="literal-filter" placeholder="Filter by label…" oninput="render()">
        </div>
      </div>
    </div>
  </div>
</section>`;
}

// ── Embedded JS ───────────────────────────────────────────────────────────────

function buildJs(baseIri: string, resolverUrl: string, kgdataJson: string): string {
  return `<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
<script>
/* KG data (generated by rdf-to-kg-section.ts) */
const B        = ${JSON.stringify(baseIri)};
const RESOLVER = ${JSON.stringify(resolverUrl)};
function res(iri){ return RESOLVER + encodeURIComponent(iri); }

const kgData = ${kgdataJson};
const KGDATA = kgData;

let kgMode        = 'basic';
let kgDensity     = 'core';
let simulation    = null;
let kgZoom        = null;
let kgSvg         = null;
let kgG           = null;
let settingsOpen  = false;
let activePreds   = null;
let allPredicates = [];
const typeColors = {
  class:  'var(--class-color,  #ea580c)',
  prop:   'var(--prop-color,   #0ea5e9)',
  inst:   'var(--inst-color,   #059669)',
  person: 'var(--person-color, #7c3aed)',
  org:    'var(--org-color,    #1d4ed8)'
};
let activeNodeTypes = new Set(['class','prop','inst','person','org']);

function openInResolver(iri){
  const m = (document.getElementById('kg-resolver')||{}).value || 'uriburner';
  window.open(m === 'none' ? iri : res(iri), '_blank', 'noopener,noreferrer');
}

function getFiltered(){
  const src = kgDensity === 'core' ? KGDATA.core : KGDATA.full;
  let nodes = [...src.nodes];
  let links = src.links.map(l => ({
    source: typeof l.source === 'object' ? l.source.id : l.source,
    target: typeof l.target === 'object' ? l.target.id : l.target,
    label:  l.label
  }));
  const arrowEl = document.getElementById('arrow-style');
  if(arrowEl && arrowEl.value === 'single'){
    const seen = new Set();
    links = links.filter(l => {
      const key = [l.source, l.target, l.label].sort().join('|||');
      if(seen.has(key)) return false;
      seen.add(key); return true;
    });
  }
  if(activePreds !== null) links = links.filter(l => activePreds.has(l.label));
  const litTerm    = (document.getElementById('literal-filter') || {}).value?.trim().toLowerCase() || '';
  const searchTerm = (document.getElementById('kg-search')      || {}).value?.trim().toLowerCase() || '';
  nodes = nodes.filter(n => activeNodeTypes.has(n.type));
  if(searchTerm) nodes = nodes.filter(n =>
    n.label.toLowerCase().includes(searchTerm) || (n.desc||'').toLowerCase().includes(searchTerm));
  if(litTerm)    nodes = nodes.filter(n =>
    n.label.toLowerCase().includes(litTerm)    || (n.desc||'').toLowerCase().includes(litTerm));
  const nodeIds = new Set(nodes.map(n => n.id));
  links = links.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target));
  const conn = new Set();
  links.forEach(l => { conn.add(l.source); conn.add(l.target); });
  nodes = nodes.filter(n => conn.has(n.id));
  return { nodes, links };
}

function render(){
  const { nodes, links } = getFiltered();
  document.getElementById('kg-stats').textContent =
    nodes.length + ' nodes / ' + links.length + ' links';
  const explorer  = document.getElementById('kg-explorer');
  const container = document.getElementById('kg-svg-container');
  kgSvg = d3.select('#kg-svg');
  kgSvg.selectAll('*').remove();
  if(simulation){ simulation.stop(); simulation = null; }
  const W = container.clientWidth  || 700;
  const H = container.clientHeight || 480;
  kgSvg.attr('viewBox', '0 0 ' + W + ' ' + H);
  kgG = kgSvg.append('g');
  kgSvg.append('defs').append('marker')
    .attr('id','arr').attr('markerWidth',8).attr('markerHeight',8)
    .attr('refX',20).attr('refY',3).attr('orient','auto')
    .append('polygon').attr('points','0 0, 6 3, 0 6').attr('fill','#475569');
  const chargeVal    = parseInt((document.getElementById('charge-slider') || {value:'-400'}).value);
  const distVal      = parseInt((document.getElementById('dist-slider')   || {value:'90' }).value);
  const resolverEl   = document.getElementById('kg-resolver');
  const resolverMode = resolverEl ? resolverEl.value : 'uriburner';
  const arrowStyleEl = document.getElementById('arrow-style');
  const useArrow     = !arrowStyleEl || arrowStyleEl.value !== 'line';
  const linkGs    = kgG.append('g').selectAll('g').data(links).join('g');
  const linkLines = linkGs.append('line')
    .attr('stroke','#2d3f5a').attr('stroke-width',1.5).attr('stroke-opacity',0.6)
    .attr('marker-end', useArrow ? 'url(#arr)' : null).attr('style','cursor:pointer');
  linkLines
    .on('mouseenter', function(e,d){ d3.select(this).attr('stroke','#00b2c2').attr('stroke-width',2).attr('stroke-opacity',1); })
    .on('mouseleave', function(e,d){ d3.select(this).attr('stroke','#2d3f5a').attr('stroke-width',1.5).attr('stroke-opacity',0.6); })
    .on('click', (e,d) => { openInResolver(resolvePredicateIRI(d.label)); });
  const predDisplayEl = document.getElementById('pred-display');
  const dispMode      = predDisplayEl ? predDisplayEl.value : 'labels';
  if(dispMode === 'labels'){
    const predAnchor = linkGs.append('a')
      .attr('data-resolver-href', d => res(d.label))
      .on('click', (e,d) => { e.preventDefault(); openInResolver(d.label); });
    predAnchor.append('text')
      .text(d => { const l=d.label.replace('schema:','').replace('rdfs:','').replace('prov:','').replace(':',''); return l.length>16?l.slice(0,14)+'…':l; })
      .attr('data-from', d => typeof d.source === 'object' ? d.source.id : d.source)
      .attr('data-to',   d => typeof d.target === 'object' ? d.target.id : d.target)
      .attr('font-size','8px').attr('fill','var(--muted,#64748b)')
      .attr('font-family',"'JetBrains Mono',monospace")
      .attr('text-anchor','middle').attr('dy','0.32em').style('cursor','pointer');
  }
  const nodesG = kgG.append('g').selectAll('g').data(nodes).join('g')
    .attr('style','cursor:pointer')
    .call(d3.drag()
      .clickDistance(6)
      .on('start', (e,d) => { if(!e.active) simulation.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; })
      .on('drag',  (e,d) => { d.fx=e.x; d.fy=e.y; })
      .on('end',   (e,d) => { if(!e.active) simulation.alphaTarget(0); d.fx=null; d.fy=null; }));
  nodesG.append('circle')
    .attr('r',            d => d.radius || 18)
    .attr('fill',         d => typeColors[d.type] || '#475569')
    .attr('stroke','#1e2d45').attr('stroke-width',1.5).attr('fill-opacity', 0.85);
  nodesG.append('text')
    .text(d => { const l=d.label||''; return l.length>16?l.slice(0,14)+'…':l; })
    .attr('font-size','0.65rem').attr('fill','#e2e8f0')
    .attr('text-anchor','middle').attr('dy','0.35em').attr('pointer-events','none');
  nodesG.on('click', (e,d) => { openInResolver(d.id); });
  nodesG.on('dblclick', (e,d) => { delete d.fx; delete d.fy; simulation.alpha(0.3).restart(); });
  nodesG.append('title').text(d => d.label + (d.desc ? '\\n'+d.desc : ''));
  const physEnabled = (document.getElementById('physics-enabled') || {checked:true}).checked;
  simulation = d3.forceSimulation(nodes)
    .force('link',      d3.forceLink(links).id(d=>d.id).distance(distVal))
    .force('charge',    d3.forceManyBody().strength(chargeVal))
    .force('center',    d3.forceCenter(W/2, H/2))
    .force('collision', d3.forceCollide().radius(d => (d.radius||18)+8));
  if(!physEnabled) simulation.stop();
  simulation.on('tick', () => {
    linkLines
      .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => { const dx=d.target.x-d.source.x,dy=d.target.y-d.source.y,r=Math.hypot(dx,dy)||1,rad=d.target.radius||18; return d.target.x-dx/r*rad; })
      .attr('y2', d => { const dx=d.target.x-d.source.x,dy=d.target.y-d.source.y,r=Math.hypot(dx,dy)||1,rad=d.target.radius||18; return d.target.y-dy/r*rad; });
    if(dispMode === 'labels'){
      linkGs.select('text').attr('x', d => (d.source.x+d.target.x)/2).attr('y', d => (d.source.y+d.target.y)/2);
    }
    nodesG.attr('transform', d => 'translate('+d.x+','+d.y+')');
  });
  kgZoom = d3.zoom().scaleExtent([0.2,4]).on('zoom', e => { kgG.attr('transform', e.transform); });
  kgSvg.on('click.zoomActivate', () => { kgSvg.call(kgZoom); explorer.classList.add('kg-active'); });
  document.addEventListener('click', function outsideClick(e) {
    if(!explorer.contains(e.target)){
      kgSvg.on('.zoom', null); explorer.classList.remove('kg-active');
      document.removeEventListener('click', outsideClick);
    }
  });
  allPredicates = [...new Set(links.map(l => l.label))].sort();
  populatePredFilters(links); populateNodeTypeChips(); updateLegend();
}

function populatePredFilters(links){
  const container = document.getElementById('pred-filters');
  if(!container) return;
  const preds = [...new Set(links.map(l => l.label))].sort();
  container.innerHTML = '';
  preds.forEach(p => {
    const active = activePreds === null || activePreds.has(p);
    const lbl = document.createElement('label');
    lbl.innerHTML = '<input type="checkbox"' + (active?' checked':'') + ' data-pred="' + p + '"> ' + p;
    lbl.querySelector('input').onchange = e => {
      if(activePreds === null) activePreds = new Set(allPredicates);
      if(e.target.checked) activePreds.add(p); else activePreds.delete(p);
      render();
    };
    container.appendChild(lbl);
  });
}

function populateNodeTypeChips(){
  const container = document.getElementById('node-type-chips');
  if(!container) return;
  const types = [
    {k:'class',  color:'#ea580c', label:'Classes'},
    {k:'prop',   color:'#0ea5e9', label:'Properties'},
    {k:'inst',   color:'#059669', label:'Instances'},
    {k:'person', color:'#7c3aed', label:'Persons'},
    {k:'org',    color:'#1d4ed8', label:'Organizations'}
  ];
  container.innerHTML = '';
  types.forEach(t => {
    const active = activeNodeTypes.has(t.k);
    const btn = document.createElement('button');
    btn.textContent = t.label;
    btn.setAttribute('aria-pressed', active ? 'true' : 'false');
    btn.style.cssText = 'color:' + t.color + ';border-color:' + t.color + ';' + (active ? 'background:' + t.color + ';color:#fff;' : 'background:transparent;');
    btn.onclick = () => { toggleNodeType(t.k); };
    container.appendChild(btn);
  });
}

function toggleNodeType(k){ if(activeNodeTypes.has(k)) activeNodeTypes.delete(k); else activeNodeTypes.add(k); populateNodeTypeChips(); updateLegend(); render(); }
function setNodeTypeAll(val){ activeNodeTypes = val ? new Set(['class','prop','inst','person','org']) : new Set(); populateNodeTypeChips(); updateLegend(); render(); }
function setPredAll(val){ activePreds = val ? null : new Set(); populatePredFilters(getFiltered().links); render(); }

function setMode(m){
  kgMode = m;
  document.getElementById('btn-basic').classList.toggle('active',    m==='basic');
  document.getElementById('btn-advanced').classList.toggle('active', m==='advanced');
  document.querySelectorAll('[data-advanced-control]').forEach(el => { el.style.display = m === 'advanced' ? '' : 'none'; });
  if(m === 'basic' && settingsOpen) toggleSettings();
  render();
}

function setDensity(d){ kgDensity = d; activePreds = null; document.getElementById('btn-core').classList.toggle('active', d==='core'); document.getElementById('btn-full').classList.toggle('active', d==='full'); render(); }

function toggleSettings(){
  const panel = document.getElementById('kg-settings');
  const btn   = document.getElementById('btn-settings');
  settingsOpen = !settingsOpen;
  panel.classList.toggle('open', settingsOpen);
  if(btn) btn.setAttribute('aria-expanded', settingsOpen ? 'true' : 'false');
}

function updatePhysics(){
  const chargeEl  = document.getElementById('charge-slider');
  const distEl    = document.getElementById('dist-slider');
  const physicsEl = document.getElementById('physics-enabled');
  if(chargeEl) document.getElementById('charge-val').textContent = chargeEl.value;
  if(distEl)   document.getElementById('dist-val').textContent   = distEl.value + 'px';
  if(!simulation) return;
  if(physicsEl && !physicsEl.checked){ simulation.stop(); return; }
  if(chargeEl) simulation.force('charge').strength(parseInt(chargeEl.value));
  if(distEl)   simulation.force('link').distance(parseInt(distEl.value));
  simulation.alpha(0.3).restart();
}

function centerGraph(){ if(!kgSvg||!kgZoom) return; kgSvg.transition().duration(400).call(kgZoom.transform, d3.zoomIdentity); }
function toggleFullscreen(){ const el=document.getElementById('kg-explorer'); if(!document.fullscreenElement) el.requestFullscreen&&el.requestFullscreen(); else document.exitFullscreen&&document.exitFullscreen(); }

function updateLegend(){
  const legend = document.getElementById('kg-legend');
  legend.innerHTML = '';
  [{key:'class',label:'Class',color:'#ea580c'},{key:'person',label:'Person',color:'#7c3aed'},{key:'org',label:'Organization',color:'#1d4ed8'},{key:'inst',label:'Instance',color:'#059669'},{key:'prop',label:'Property',color:'#0ea5e9'}].forEach(t => {
    const el = document.createElement('div');
    el.className = 'legend-item' + (activeNodeTypes.has(t.key) ? '' : ' dimmed');
    el.innerHTML = '<div class="legend-dot" style="background:' + t.color + '"></div><span>' + t.label + '</span>';
    el.onclick = () => { toggleNodeType(t.key); };
    legend.appendChild(el);
  });
}

function resolvePredicateIRI(label){ return label; }

if(document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', () => { render(); setMode('basic'); });
} else {
  render(); setMode('basic');
}
window.addEventListener('resize', () => { if(simulation) render(); });
</script>`;
}

// ── Section renderer ──────────────────────────────────────────────────────────

export function renderSection(kgdata: ReturnType<typeof buildKgdata>, baseIri: string, resolverUrl: string, title: string): string {
  const kgdataJson = JSON.stringify(kgdata, null, 2);
  return CSS + "\n" + buildHtml(title) + "\n" + buildJs(baseIri, resolverUrl, kgdataJson);
}

// ── CLI ───────────────────────────────────────────────────────────────────────

function parseArgs(argv: string[]) {
  const args: Record<string, string | boolean> = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith("--")) {
      const key = argv[i].slice(2);
      if (argv[i + 1] && !argv[i + 1].startsWith("--")) { args[key] = argv[++i]; }
      else args[key] = true;
    } else if (!args["input"]) {
      args["input"] = argv[i];
    }
  }
  return args;
}

if (
  process.argv[1] &&
  (process.argv[1].endsWith("rdf-to-kg-section.ts") || process.argv[1].endsWith("rdf-to-kg-section.js"))
) {
  const args = parseArgs(process.argv.slice(2));
  const inputPath = args["input"] as string;

  if (!inputPath) {
    process.stderr.write("Usage: npx tsx rdf-to-kg-section.ts <input.ttl> [--title ...] [--output ...] [--core-max N] [--resolver ...] [--base-iri ...] [--json-only]\n");
    process.exit(1);
  }
  if (!existsSync(inputPath)) { process.stderr.write(`Error: file not found: ${inputPath}\n`); process.exit(1); }

  const fmt = (args["format"] as string) ?? autoFormat(inputPath);
  process.stderr.write(`Parsing ${inputPath} (format=${fmt})…\n`);

  const { store } = (() => {
    const content = readFileSync(inputPath, "utf-8");
    const store = new Store();
    const parser = new Parser({ format: fmt as Parameters<typeof Parser>[0]["format"] });
    store.addQuads(parser.parse(content));
    return { store };
  })();

  process.stderr.write(`  ${store.size} triples loaded.\n`);

  const { uriNodes, links } = extractGraphData(store);
  process.stderr.write(`  ${uriNodes.size} nodes, ${links.length} URI-URI links extracted.\n`);

  const coreMax = args["core-max"] ? parseInt(args["core-max"] as string) : 30;
  const kgdata = buildKgdata(uriNodes, links, coreMax);
  process.stderr.write(`  Core: ${kgdata.core.nodes.length} nodes / ${kgdata.core.links.length} links\n`);
  process.stderr.write(`  Full: ${kgdata.full.nodes.length} nodes / ${kgdata.full.links.length} links\n`);

  const baseIri = (args["base-iri"] as string) ?? deriveBaseIri(uriNodes);
  process.stderr.write(`  Base IRI: ${baseIri}\n`);

  const resolverUrl = (args["resolver"] as string) ?? "https://linkeddata.uriburner.com/describe/?url=";
  const title = (args["title"] as string) ?? "Knowledge Graph Explorer";

  const output = args["json-only"]
    ? JSON.stringify(kgdata, null, 2)
    : renderSection(kgdata, baseIri, resolverUrl, title);

  const outputPath = args["output"] as string | undefined;
  if (outputPath) {
    writeFileSync(outputPath, output, "utf-8");
    process.stderr.write(`  Written to ${outputPath}\n`);
  } else {
    process.stdout.write(output + "\n");
  }
}
