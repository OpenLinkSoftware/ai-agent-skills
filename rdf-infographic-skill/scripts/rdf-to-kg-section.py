#!/usr/bin/env python3
"""
rdf-to-kg-section.py — Generate a self-contained D3 v7 KG Explorer HTML section from RDF/TTL input.

The emitted HTML block can be dropped verbatim into any rdf-infographic-skill
harness-compliant page. It includes embedded <style> and <script> tags; all
CSS custom-property references use var(--prop, fallback) so the section renders
correctly both inside a themed harness page and standalone.

Usage:
    python3 rdf-to-kg-section.py <input.ttl> [options]

Options:
    --base-iri <IRI>        Override base IRI for resolver links
                            (default: derived from most common node namespace)
    --core-max <N>          Max nodes in 'core' density view (default: 30)
    --output <file>         Write output to file instead of stdout
    --format <fmt>          rdflib parse format: turtle, xml, json-ld, n3, nt
                            (default: auto-detect from file extension)
    --resolver <url>        URIBurner describe URL prefix
                            (default: https://linkeddata.uriburner.com/describe/?url=)
    --title <text>          Section heading (default: 'Knowledge Graph Explorer')
    --json-only             Output kgData JSON only (no HTML wrapper)

Examples:
    # Full HTML section to stdout
    python3 rdf-to-kg-section.py article.ttl

    # Write to file with custom heading and base IRI
    python3 rdf-to-kg-section.py article.ttl \\
        --title "Super-App vs Super-Agent Knowledge Graph" \\
        --base-iri "https://example.com/article#" \\
        --output kg-section.html

    # Just the kgData JSON (for manual embedding)
    python3 rdf-to-kg-section.py article.ttl --json-only
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    from rdflib import Graph, URIRef, Literal, BNode, Namespace, RDF, RDFS, OWL
    from rdflib.namespace import SKOS, FOAF, DC, DCTERMS
except ImportError:
    sys.exit("rdflib not found. Install with: pip install rdflib")

# ── Namespaces ────────────────────────────────────────────────────────────────

SCHEMA   = Namespace("http://schema.org/")
SCHEMAH  = Namespace("https://schema.org/")  # https variant

# ── Format detection ──────────────────────────────────────────────────────────

def auto_format(path: str) -> str:
    return {
        '.ttl':    'turtle',
        '.n3':     'n3',
        '.nt':     'nt',
        '.rdf':    'xml',
        '.xml':    'xml',
        '.jsonld': 'json-ld',
        '.json':   'json-ld',
    }.get(Path(path).suffix.lower(), 'turtle')

# ── Label / description helpers ───────────────────────────────────────────────

def short_name(uri: str) -> str:
    """Extract the local name (fragment or last path segment) from a URI."""
    if '#' in uri:
        frag = uri.split('#')[-1]
        if frag:
            return frag
    parts = uri.rstrip('/').split('/')
    return parts[-1] if parts else uri


def camel_split(s: str) -> str:
    """Convert camelCase / PascalCase / snake_case to spaced words."""
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', s)
    s = re.sub(r'([a-z\d])([A-Z])', r'\1 \2', s)
    return s.replace('_', ' ').replace('-', ' ').strip()


def get_label(g: Graph, uri: URIRef) -> str:
    """Return the best human-readable label for a URI node."""
    for pred in (RDFS.label, SCHEMA.name, SCHEMAH.name,
                 DCTERMS.title, DC.title, FOAF.name, SKOS.prefLabel):
        for obj in g.objects(uri, pred):
            if isinstance(obj, Literal):
                s = str(obj).strip()
                if s:
                    return s
    return camel_split(short_name(str(uri)))


def get_desc(g: Graph, uri: URIRef) -> str:
    """Return a short description for a URI node (max 200 chars)."""
    for pred in (RDFS.comment, SCHEMA.description, SCHEMAH.description,
                 SCHEMA.abstract, SCHEMAH.abstract, DC.description, DCTERMS.description):
        for obj in g.objects(uri, pred):
            if isinstance(obj, Literal):
                s = str(obj).strip()
                if s:
                    return s[:200]
    return ''

# ── Node type classification ──────────────────────────────────────────────────

_PROP_TYPES = frozenset({
    RDF.Property, OWL.ObjectProperty, OWL.DatatypeProperty,
    OWL.AnnotationProperty, OWL.TransitiveProperty,
    OWL.SymmetricProperty, OWL.FunctionalProperty,
    OWL.InverseFunctionalProperty,
})
_CLASS_TYPES = frozenset({RDFS.Class, OWL.Class})
_PERSON_TYPES = frozenset({SCHEMA.Person, SCHEMAH.Person, FOAF.Person})
_ORG_TYPES = frozenset({
    SCHEMA.Organization, SCHEMAH.Organization,
    SCHEMA.Corporation,  SCHEMAH.Corporation,
    FOAF.Organization,
})


def classify_type(g: Graph, uri: URIRef) -> str:
    """Return one of: class | prop | person | org | inst."""
    types = set(g.objects(uri, RDF.type))
    if types & _PROP_TYPES:   return 'prop'
    if types & _CLASS_TYPES:  return 'class'
    if types & _PERSON_TYPES: return 'person'
    if types & _ORG_TYPES:    return 'org'
    return 'inst'

# ── Predicates to suppress as graph edges ────────────────────────────────────

_SKIP_PREDS = frozenset({
    str(RDF.type),
    str(RDFS.domain), str(RDFS.range),
    str(OWL.sameAs), str(OWL.equivalentClass), str(OWL.equivalentProperty),
    str(RDFS.subClassOf), str(RDFS.subPropertyOf),
    str(RDFS.isDefinedBy), str(RDFS.seeAlso),
})

# ── Graph extraction ──────────────────────────────────────────────────────────

def extract_graph_data(g: Graph):
    """
    Walk the rdflib Graph and collect node dicts + link dicts.

    Returns:
        uri_nodes : dict[str, dict]  — keyed by IRI string
        links     : list[dict]       — {source, target, label}
    """
    uri_nodes: dict = {}

    def ensure(uri_ref: URIRef):
        uri = str(uri_ref)
        if uri not in uri_nodes:
            uri_nodes[uri] = {
                'id':     uri,
                'label':  get_label(g, uri_ref),
                'type':   classify_type(g, uri_ref),
                'desc':   get_desc(g, uri_ref),
                'radius': 18,
                '_deg':   0,   # scratch field removed before output
            }
        return uri_nodes[uri]

    links = []

    for s, p, o in g:
        # Skip blank nodes and literals on either end
        if isinstance(s, (BNode, Literal)) or isinstance(o, (BNode, Literal)):
            continue
        if not isinstance(s, URIRef) or not isinstance(o, URIRef):
            continue
        if str(p) in _SKIP_PREDS:
            continue

        ensure(s)
        ensure(o)
        pred_label = camel_split(short_name(str(p)))
        links.append({'source': str(s), 'target': str(o), 'label': pred_label})
        uri_nodes[str(s)]['_deg'] += 1
        uri_nodes[str(o)]['_deg'] += 1

    # Ensure isolated subjects still get a node entry (for --json-only auditing)
    for s in g.subjects():
        if isinstance(s, URIRef):
            ensure(s)

    return uri_nodes, links

# ── kgData builder ────────────────────────────────────────────────────────────

def build_kgdata(uri_nodes: dict, links: list, core_max: int = 30) -> dict:
    """
    Build the kgData structure expected by the D3 KG Explorer:
        { "core": { "nodes": [...], "links": [...] },
          "full": { "nodes": [...], "links": [...] } }

    'core'  = top core_max nodes by degree (most connected)
    'full'  = all nodes that participate in at least one link
    """
    # Only keep nodes that are actually connected
    linked_ids = set()
    for lnk in links:
        linked_ids.add(lnk['source'])
        linked_ids.add(lnk['target'])

    connected = [n for n in uri_nodes.values() if n['id'] in linked_ids]

    def clean(n):
        return {k: v for k, v in n.items() if k != '_deg'}

    # Full density
    full_nodes = [clean(n) for n in connected]
    full_links = links[:]

    # Core density — top N by degree
    sorted_by_deg = sorted(connected, key=lambda n: n['_deg'], reverse=True)
    core_ids = {n['id'] for n in sorted_by_deg[:core_max]}
    core_nodes = [clean(n) for n in sorted_by_deg[:core_max]]
    core_links = [lnk for lnk in links
                  if lnk['source'] in core_ids and lnk['target'] in core_ids]

    return {
        'core': {'nodes': core_nodes, 'links': core_links},
        'full': {'nodes': full_nodes, 'links': full_links},
    }

# ── Base IRI derivation ───────────────────────────────────────────────────────

def derive_base_iri(uri_nodes: dict) -> str:
    """Heuristically derive the dominant namespace from the node URIs."""
    if not uri_nodes:
        return 'https://example.org/'
    namespaces = []
    for uri in uri_nodes:
        if '#' in uri:
            namespaces.append(uri.rsplit('#', 1)[0] + '#')
        else:
            parts = uri.rstrip('/').rsplit('/', 1)
            if len(parts) == 2:
                namespaces.append(parts[0] + '/')
    if namespaces:
        return Counter(namespaces).most_common(1)[0][0]
    return 'https://example.org/'

# ── HTML / JS templates ───────────────────────────────────────────────────────

_CSS = """\
<style id="kg-section-styles">
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
</style>"""

_HTML = """\
<span id="settings-panel" style="display:none"></span>
<section id="kg-section">
  <h2 style="font-size:1.1rem;font-weight:700;margin:0 0 .5rem;color:var(--ink,#e2e8f0)">{title}</h2>
  <div id="kg-explorer">
    <div class="kg-toolbar" id="kgToolbar">
      <button id="btn-basic"   class="active" onclick="setMode('basic')">Basic</button>
      <button id="btn-advanced"              onclick="setMode('advanced')">Advanced</button>
      <div class="sep"></div>
      <button id="btn-core" class="active" onclick="setDensity('core')">Core</button>
      <button id="btn-full"               onclick="setDensity('full')">Full</button>
      <div class="sep"></div>
      <input type="search" id="kg-search" placeholder="Search nodes…" oninput="render()" />
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
               oninput="document.getElementById('charge-val').textContent=this.value;updatePhysics()" />
        <span class="rval">Value: <span id="charge-val">-400</span></span>
      </div>
      <div class="kg-sg">
        <label>Link distance</label>
        <input type="range" id="dist-slider" min="30" max="300" value="90"
               oninput="document.getElementById('dist-val').textContent=this.value+'px';updatePhysics()" />
        <span class="rval">Value: <span id="dist-val">90px</span></span>
      </div>
      <div class="kg-sg">
        <label style="display:flex;align-items:center;gap:6px;text-transform:none;font-size:.78rem">
          <input type="checkbox" id="physics-enabled" checked="checked" onchange="updatePhysics()" /> Enable physics
        </label>
      </div>
      <div class="kg-sg" data-advanced-control="true" style="display:none">
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
      <div class="kg-sg" data-advanced-control="true" style="display:none">
        <label>Predicates</label>
        <div id="pred-filters"></div>
        <div style="display:flex;gap:6px;margin-top:5px">
          <button class="kg-btn" onclick="setPredAll(true)"  style="font-size:.68rem;padding:3px 8px">All</button>
          <button class="kg-btn" onclick="setPredAll(false)" style="font-size:.68rem;padding:3px 8px">None</button>
        </div>
      </div>
      <div class="kg-sg" data-advanced-control="true" style="display:none">
        <label>Literal / label filter</label>
        <div class="literal-row">
          <input type="text" id="literal-filter" placeholder="Filter by label…" oninput="render()" />
        </div>
      </div>
    </div>
  </div>
</section>"""

# Note: double-brace {{ }} escapes literal braces in Python .format()
_JS = """\
<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
<script>
/* ── KG data (generated by rdf-to-kg-section.py) ─── */
const B        = '{base_iri}';
const DBR      = 'http://dbpedia.org/resource/';
const RESOLVER = '{resolver_url}';
function res(iri){{ return RESOLVER + encodeURIComponent(iri); }}

const kgData = {kgdata_json};
const KGDATA = kgData;

/* ── KG State ────────────────────────────────────── */
let kgMode         = 'basic';
let kgDensity      = 'core';
let simulation     = null;
let kgZoom         = null;
let kgSvg          = null;
let kgG            = null;
let settingsOpen   = false;
let activePreds    = null;
let allPredicates  = [];
const typeColors = {{
  class:  'var(--class-color,  #ea580c)',
  prop:   'var(--prop-color,   #0ea5e9)',
  inst:   'var(--inst-color,   #059669)',
  person: 'var(--person-color, #7c3aed)',
  org:    'var(--org-color,    #1d4ed8)'
}};
let activeNodeTypes = new Set(['class','prop','inst','person','org']);

/* ── Helpers ─────────────────────────────────────── */
function openInResolver(iri){{
  const m = (document.getElementById('kg-resolver')||{{}}).value || 'uriburner';
  window.open(m === 'none' ? iri : res(iri), '_blank', 'noopener,noreferrer');
}}

/* ── Filter pipeline ─────────────────────────────── */
function getFiltered(){{
  const src = kgDensity === 'core' ? KGDATA.core : KGDATA.full;
  let nodes = [...src.nodes];
  let links = src.links.map(l => ({{
    source: typeof l.source === 'object' ? l.source.id : l.source,
    target: typeof l.target === 'object' ? l.target.id : l.target,
    label:  l.label
  }}));

  /* Arrow-style dedup */
  const arrowEl = document.getElementById('arrow-style');
  if(arrowEl && arrowEl.value === 'single'){{
    const seen = new Set();
    links = links.filter(l => {{
      const key = [l.source, l.target, l.label].sort().join('|||');
      if(seen.has(key)) return false;
      seen.add(key); return true;
    }});
  }}

  /* Predicate filter */
  if(activePreds !== null) links = links.filter(l => activePreds.has(l.label));

  /* Text filters */
  const litTerm    = (document.getElementById('literal-filter') || {{}}).value?.trim().toLowerCase() || '';
  const searchTerm = (document.getElementById('kg-search')      || {{}}).value?.trim().toLowerCase() || '';

  nodes = nodes.filter(n => activeNodeTypes.has(n.type));
  if(searchTerm) nodes = nodes.filter(n =>
    n.label.toLowerCase().includes(searchTerm) || (n.desc||'').toLowerCase().includes(searchTerm));
  if(litTerm)    nodes = nodes.filter(n =>
    n.label.toLowerCase().includes(litTerm)    || (n.desc||'').toLowerCase().includes(litTerm));

  const nodeIds = new Set(nodes.map(n => n.id));
  links = links.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target));
  const conn = new Set();
  links.forEach(l => {{ conn.add(l.source); conn.add(l.target); }});
  nodes = nodes.filter(n => conn.has(n.id));
  return {{ nodes, links }};
}}

/* ── Render ──────────────────────────────────────── */
function render(){{
  const {{ nodes, links }} = getFiltered();
  document.getElementById('kg-stats').textContent =
    nodes.length + ' nodes / ' + links.length + ' links';

  const explorer  = document.getElementById('kg-explorer');
  const container = document.getElementById('kg-svg-container');
  kgSvg = d3.select('#kg-svg');
  kgSvg.selectAll('*').remove();
  if(simulation){{ simulation.stop(); simulation = null; }}

  const W = container.clientWidth  || 700;
  const H = container.clientHeight || 480;
  kgSvg.attr('viewBox', '0 0 ' + W + ' ' + H);
  kgG = kgSvg.append('g');

  /* Arrow marker */
  kgSvg.append('defs').append('marker')
    .attr('id','arr').attr('markerWidth',8).attr('markerHeight',8)
    .attr('refX',20).attr('refY',3).attr('orient','auto')
    .append('polygon').attr('points','0 0, 6 3, 0 6').attr('fill','#475569');

  const chargeVal   = parseInt((document.getElementById('charge-slider') || {{value:'-400'}}).value);
  const distVal     = parseInt((document.getElementById('dist-slider')   || {{value:'90' }}).value);
  const resolverEl  = document.getElementById('kg-resolver');
  const resolverMode = resolverEl ? resolverEl.value : 'uriburner';
  const arrowStyleEl = document.getElementById('arrow-style');
  const useArrow    = !arrowStyleEl || arrowStyleEl.value !== 'line';

  /* Edges — G-wrapped so labels can be repositioned on tick */
  const linkGs    = kgG.append('g').selectAll('g').data(links).join('g');
  const linkLines = linkGs.append('line')
    .attr('stroke','#2d3f5a').attr('stroke-width',1.5)
    .attr('stroke-opacity',0.6)
    .attr('marker-end', useArrow ? 'url(#arr)' : null)
    .attr('style','cursor:pointer');

  linkLines
    .on('mouseenter', function(e,d){{ d3.select(this).attr('stroke','#00b2c2').attr('stroke-width',2).attr('stroke-opacity',1); }})
    .on('mouseleave', function(e,d){{ d3.select(this).attr('stroke','#2d3f5a').attr('stroke-width',1.5).attr('stroke-opacity',0.6); }})
    .on('click', (e,d) => {{ openInResolver(resolvePredicateIRI(d.label)); }});

  /* Predicate labels — always shown unless pred-display === 'icons' */
  const predDisplayEl = document.getElementById('pred-display');
  const dispMode      = predDisplayEl ? predDisplayEl.value : 'labels';
  if(dispMode === 'labels'){{
    linkGs.append('text')
      .text(d => {{ const l=d.label.replace('schema:','').replace('rdfs:','').replace('prov:','').replace(':',''); return l.length>16?l.slice(0,14)+'…':l; }})
      .attr('data-from', d => typeof d.source === 'object' ? d.source.id : d.source)
      .attr('data-to',   d => typeof d.target === 'object' ? d.target.id : d.target)
      .attr('font-size','8px').attr('fill','var(--muted,#64748b)')
      .attr('font-family',"'JetBrains Mono',monospace")
      .attr('text-anchor','middle').attr('dy','0.32em')
      .style('cursor','pointer')
      .on('click', (e,d) => {{ openInResolver(resolvePredicateIRI(d.label)); }});
  }}

  /* Nodes */
  const nodesG = kgG.append('g').selectAll('g').data(nodes).join('g')
    .attr('style','cursor:pointer')
    .call(d3.drag()
      .clickDistance(6)
      .on('start', (e,d) => {{ if(!e.active) simulation.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; }})
      .on('drag',  (e,d) => {{ d.fx=e.x; d.fy=e.y; }})
      .on('end',   (e,d) => {{ if(!e.active) simulation.alphaTarget(0); }}));

  nodesG.append('circle')
    .attr('r',            d => d.radius || 18)
    .attr('fill',         d => typeColors[d.type] || '#475569')
    .attr('stroke','#1e2d45').attr('stroke-width',1.5)
    .attr('fill-opacity', 0.85);

  nodesG.append('text')
    .text(d => {{ const l=d.label||''; return l.length>16?l.slice(0,14)+'…':l; }})
    .attr('font-size','0.65rem').attr('fill','#e2e8f0')
    .attr('text-anchor','middle').attr('dy','0.35em')
    .attr('pointer-events','none');

  nodesG.on('click', (e,d) => {{ window.open(d.id, '_blank', 'noopener,noreferrer'); }});
  nodesG.on('dblclick', (e,d) => {{ delete d.fx; delete d.fy; simulation.alpha(0.3).restart(); }});
  nodesG.append('title').text(d => d.label + (d.desc ? '\\n'+d.desc : ''));

  /* Physics */
  const physEnabled = (document.getElementById('physics-enabled') || {{checked:true}}).checked;
  simulation = d3.forceSimulation(nodes)
    .force('link',      d3.forceLink(links).id(d=>d.id).distance(distVal))
    .force('charge',    d3.forceManyBody().strength(chargeVal))
    .force('center',    d3.forceCenter(W/2, H/2))
    .force('collision', d3.forceCollide().radius(d => (d.radius||18)+8));
  if(!physEnabled) simulation.stop();

  simulation.on('tick', () => {{
    /* Offset x2/y2 so arrowhead sits at node circumference, not centre */
    linkLines
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => {{
        const dx=d.target.x-d.source.x, dy=d.target.y-d.source.y;
        const r = Math.hypot(dx,dy)||1, rad = d.target.radius||18;
        return d.target.x - dx/r*rad;
      }})
      .attr('y2', d => {{
        const dx=d.target.x-d.source.x, dy=d.target.y-d.source.y;
        const r = Math.hypot(dx,dy)||1, rad = d.target.radius||18;
        return d.target.y - dy/r*rad;
      }});
    if(dispMode === 'labels'){{
      linkGs.select('text')
        .attr('x', d => (d.source.x + d.target.x)/2)
        .attr('y', d => (d.source.y + d.target.y)/2);
    }}
    nodesG.attr('transform', d => 'translate(' + d.x + ',' + d.y + ')');
  }});

  /* Zoom — armed on click-inside, disarmed on click-outside */
  kgZoom = d3.zoom().scaleExtent([0.2,4]).on('zoom', e => {{ kgG.attr('transform', e.transform); }});
  kgSvg.on('click.zoomActivate', () => {{ kgSvg.call(kgZoom); explorer.classList.add('kg-active'); }});
  document.addEventListener('click', function outsideClick(e) {{
    if(!explorer.contains(e.target)) {{
      kgSvg.on('.zoom', null);
      explorer.classList.remove('kg-active');
      document.removeEventListener('click', outsideClick);
    }}
  }});

  /* Populate settings widgets after render */
  allPredicates = [...new Set(links.map(l => l.label))].sort();
  populatePredFilters(links);
  populateNodeTypeChips();
  updateLegend();
}}

/* ── Settings widgets ────────────────────────────── */
function populatePredFilters(links){{
  const container = document.getElementById('pred-filters');
  if(!container) return;
  const preds = [...new Set(links.map(l => l.label))].sort();
  container.innerHTML = '';
  preds.forEach(p => {{
    const active = activePreds === null || activePreds.has(p);
    const lbl = document.createElement('label');
    lbl.innerHTML = '<input type="checkbox"' + (active?' checked':'') + ' data-pred="' + p + '"> ' + p;
    lbl.querySelector('input').onchange = e => {{
      if(activePreds === null) activePreds = new Set(allPredicates);
      if(e.target.checked) activePreds.add(p); else activePreds.delete(p);
      render();
    }};
    container.appendChild(lbl);
  }});
}}

function populateNodeTypeChips(){{
  const container = document.getElementById('node-type-chips');
  if(!container) return;
  const types = [
    {{k:'class',  color:'#ea580c', label:'Classes'}},
    {{k:'prop',   color:'#0ea5e9', label:'Properties'}},
    {{k:'inst',   color:'#059669', label:'Instances'}},
    {{k:'person', color:'#7c3aed', label:'Persons'}},
    {{k:'org',    color:'#1d4ed8', label:'Organizations'}}
  ];
  container.innerHTML = '';
  types.forEach(t => {{
    const active = activeNodeTypes.has(t.k);
    const btn = document.createElement('button');
    btn.textContent = t.label;
    btn.setAttribute('aria-pressed', active ? 'true' : 'false');
    btn.style.cssText = 'color:' + t.color + ';border-color:' + t.color + ';'
      + (active ? 'background:' + t.color + ';color:#fff;' : 'background:transparent;');
    btn.onclick = () => {{ toggleNodeType(t.k); }};
    container.appendChild(btn);
  }});
}}

function toggleNodeType(k){{
  if(activeNodeTypes.has(k)) activeNodeTypes.delete(k); else activeNodeTypes.add(k);
  populateNodeTypeChips(); updateLegend(); render();
}}

function setNodeTypeAll(val){{
  activeNodeTypes = val ? new Set(['class','prop','inst','person','org']) : new Set();
  populateNodeTypeChips(); updateLegend(); render();
}}

function setPredAll(val){{
  activePreds = val ? null : new Set();
  populatePredFilters(getFiltered().links); render();
}}

/* ── Mode / density ──────────────────────────────── */
function setMode(m){{
  kgMode = m;
  document.getElementById('btn-basic').classList.toggle('active',    m==='basic');
  document.getElementById('btn-advanced').classList.toggle('active', m==='advanced');
  document.querySelectorAll('[data-advanced-control]').forEach(el => {{
    el.style.display = m === 'advanced' ? '' : 'none';
  }});
  if(m === 'basic' && settingsOpen) toggleSettings();
  render();
}}

function setDensity(d){{
  kgDensity = d;
  activePreds = null;
  document.getElementById('btn-core').classList.toggle('active', d==='core');
  document.getElementById('btn-full').classList.toggle('active', d==='full');
  render();
}}

/* ── Settings panel ──────────────────────────────── */
function toggleSettings(){{
  const panel = document.getElementById('kg-settings');
  const btn   = document.getElementById('btn-settings');
  settingsOpen = !settingsOpen;
  panel.classList.toggle('open', settingsOpen);
  if(btn) btn.setAttribute('aria-expanded', settingsOpen ? 'true' : 'false');
}}

/* ── Physics controls ────────────────────────────── */
function updatePhysics(){{
  const chargeEl  = document.getElementById('charge-slider');
  const distEl    = document.getElementById('dist-slider');
  const physicsEl = document.getElementById('physics-enabled');
  if(chargeEl) document.getElementById('charge-val').textContent = chargeEl.value;
  if(distEl)   document.getElementById('dist-val').textContent   = distEl.value + 'px';
  if(!simulation) return;
  if(physicsEl && !physicsEl.checked) {{ simulation.stop(); return; }}
  if(chargeEl) simulation.force('charge').strength(parseInt(chargeEl.value));
  if(distEl)   simulation.force('link').distance(parseInt(distEl.value));
  simulation.alpha(0.3).restart();
}}

/* ── View controls ───────────────────────────────── */
function centerGraph(){{
  if(!kgSvg || !kgZoom) return;
  kgSvg.transition().duration(400).call(kgZoom.transform, d3.zoomIdentity);
}}

function toggleFullscreen(){{
  const el = document.getElementById('kg-explorer');
  if(!document.fullscreenElement) el.requestFullscreen && el.requestFullscreen();
  else document.exitFullscreen && document.exitFullscreen();
}}

/* ── Legend ──────────────────────────────────────── */
function updateLegend(){{
  const legend = document.getElementById('kg-legend');
  legend.innerHTML = '';
  [
    {{key:'class',  label:'Class',        color:'#ea580c'}},
    {{key:'person', label:'Person',        color:'#7c3aed'}},
    {{key:'org',    label:'Organization',  color:'#1d4ed8'}},
    {{key:'inst',   label:'Instance',      color:'#059669'}},
    {{key:'prop',   label:'Property',      color:'#0ea5e9'}}
  ].forEach(t => {{
    const el = document.createElement('div');
    el.className = 'legend-item' + (activeNodeTypes.has(t.key) ? '' : ' dimmed');
    el.innerHTML = '<div class="legend-dot" style="background:' + t.color + '"></div><span>' + t.label + '</span>';
    el.onclick = () => {{ toggleNodeType(t.key); }};
    legend.appendChild(el);
  }});
}}

/* ── Init ────────────────────────────────────────── */
if(document.readyState === 'loading'){{
  document.addEventListener('DOMContentLoaded', () => {{ render(); setMode('basic'); }});
}} else {{
  render(); setMode('basic');
}}
window.addEventListener('resize', () => {{ if(simulation) render(); }});
</script>"""


def render_section(kgdata: dict, base_iri: str, resolver_url: str, title: str) -> str:
    kgdata_json = json.dumps(kgdata, indent=2, ensure_ascii=False)
    return (
        _CSS + '\n'
        + _HTML.format(title=title) + '\n'
        + _JS.format(
            base_iri=base_iri,
            resolver_url=resolver_url,
            kgdata_json=kgdata_json,
        )
    )

# ── CLI entry point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Generate a self-contained D3 v7 KG Explorer HTML section from RDF/TTL input.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split('\n\nUsage')[0].split('\n\n', 1)[1] if '\n\n' in __doc__ else '',
    )
    parser.add_argument('input',
                        help='Path to RDF/TTL input file')
    parser.add_argument('--base-iri', default=None,
                        help='Override base IRI for resolver links')
    parser.add_argument('--core-max', type=int, default=30,
                        help='Max nodes in core density view (default: 30)')
    parser.add_argument('--output', default=None,
                        help='Output file path (default: stdout)')
    parser.add_argument('--format', default=None, dest='fmt',
                        help='rdflib parse format: turtle, xml, json-ld, n3, nt')
    parser.add_argument('--resolver',
                        default='https://linkeddata.uriburner.com/describe/?url=',
                        help='URIBurner describe URL prefix')
    parser.add_argument('--title', default='Knowledge Graph Explorer',
                        help='Section heading text')
    parser.add_argument('--json-only', action='store_true',
                        help='Output kgData JSON only (no HTML wrapper)')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        sys.exit(f'Error: file not found: {args.input}')

    fmt = args.fmt or auto_format(args.input)
    print(f'Parsing {args.input} (format={fmt})…', file=sys.stderr)

    g = Graph()
    try:
        g.parse(args.input, format=fmt)
    except Exception as e:
        sys.exit(f'Parse error: {e}')

    print(f'  {len(g)} triples loaded.', file=sys.stderr)

    uri_nodes, links = extract_graph_data(g)
    print(f'  {len(uri_nodes)} nodes, {len(links)} URI-URI links extracted.', file=sys.stderr)

    kgdata = build_kgdata(uri_nodes, links, core_max=args.core_max)
    print(f'  Core : {len(kgdata["core"]["nodes"])} nodes / {len(kgdata["core"]["links"])} links',
          file=sys.stderr)
    print(f'  Full : {len(kgdata["full"]["nodes"])} nodes / {len(kgdata["full"]["links"])} links',
          file=sys.stderr)

    base_iri = args.base_iri or derive_base_iri(uri_nodes)
    print(f'  Base IRI: {base_iri}', file=sys.stderr)

    if args.json_only:
        output = json.dumps(kgdata, indent=2, ensure_ascii=False)
    else:
        output = render_section(kgdata, base_iri, args.resolver, args.title)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as fh:
            fh.write(output)
        print(f'  Written to {args.output}', file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
