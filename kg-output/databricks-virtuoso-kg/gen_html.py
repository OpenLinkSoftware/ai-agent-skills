"""Generate HTML infographic from Databricks-Virtuoso KG RDF."""
import rdflib, json, urllib.parse, sys, html as _html
from rdflib import RDF, RDFS, OWL

TTL_PATH = os.environ.get("TTL_PATH", os.path.join(
    os.environ.get("LLM_ROOT", os.path.join(os.path.expanduser("~"), "Documents", "LLMs")),
    "DeepSeek/rdf/databricks-virtuoso-kg-deepseek_v4pro-1.ttl"))
OUT_PATH = os.environ.get("OUT_PATH", os.path.join(
    os.environ.get("LLM_ROOT", os.path.join(os.path.expanduser("~"), "Documents", "LLMs")),
    "DeepSeek/webpages/databricks-virtuoso-kg-deepseek_v4pro-1.html"))
RESOLVER = 'https://linkeddata.uriburner.com/describe/?url='
SOURCE = 'https://community.openlinksw.com/t/from-databricks-tables-to-a-virtual-knowledge-graph-with-virtuoso/6293'
STEM = 'databricks-virtuoso-kg-deepseek_v4pro-1'
DEMO_GRAPH = 'http://demo.openlinksw.com/databricks-bakehouse-r2rml#'
GRAPH_TTL = f'https://linkeddata.uriburner.com/DAV/demos/daas/{STEM}.ttl'
GRAPH_JSONLD = f'https://linkeddata.uriburner.com/DAV/demos/daas/{STEM}.jsonld'

def enc(iri): return urllib.parse.quote(str(iri), safe='')
def rlink(iri, label, cls=''):
    c = f' class="{cls}"' if cls else ''
    return f'<a href="{RESOLVER}{enc(iri)}" target="_blank" rel="noopener noreferrer"{c}>{label}</a>'

# ── Load RDF ──────────────────────────────────────────────────────────────────
g = rdflib.Graph()
g.parse(TTL_PATH, format='turtle')
SCHEMA = rdflib.Namespace('http://schema.org/')
SKOS = rdflib.Namespace('http://www.w3.org/2004/02/skos/core#')
PROV = rdflib.Namespace('http://www.w3.org/ns/prov#')
NS = rdflib.Namespace(SOURCE + '#')

def val(s, p):
    o = g.value(s, p)
    return str(o) if o else ''

def vals(s, p):
    return [str(o) for o in g.objects(s, p)]

# ── Extract Entities ──────────────────────────────────────────────────────────
concepts = []
for s in g.subjects(RDF.type, SKOS.Concept):
    n = val(s, SCHEMA.name); d = val(s, SCHEMA.description)
    if n: concepts.append({'iri': str(s), 'name': n, 'desc': d[:200]})

faq_items = []
for q in g.subjects(RDF.type, SCHEMA.Question):
    a_s = g.value(q, SCHEMA.acceptedAnswer)
    faq_items.append({'q_iri': str(q), 'a_iri': str(a_s) if a_s else '',
        'q': val(q, SCHEMA.name), 'a': val(a_s, SCHEMA.text) if a_s else ''})

glossary_terms = []
for t in g.subjects(RDF.type, SCHEMA.DefinedTerm):
    if not g.value(t, RDFS.seeAlso):
        glossary_terms.append({'iri': str(t), 'name': val(t, SCHEMA.name), 'defn': val(t, SCHEMA.description)})

steps = []
for s_iri in g.objects(NS.howtoSection, SCHEMA.step):
    steps.append({'iri': str(s_iri), 'pos': int(val(s_iri, SCHEMA.position)),
        'name': val(s_iri, SCHEMA.name), 'text': val(s_iri, SCHEMA.text)})
steps.sort(key=lambda x: x['pos'])

sparql_queries = []
for s in g.subjects(RDF.type, SCHEMA.SoftwareSourceCode):
    if 'SPARQL' in (val(s, SCHEMA.programmingLanguage) or ''):
        act = g.value(s, SCHEMA.potentialAction)
        sparql_queries.append({'iri': str(s), 'name': val(s, SCHEMA.name),
            'desc': val(s, SCHEMA.description), 'text': val(s, SCHEMA.text),
            'fmt': val(s, SCHEMA.codeSampleType) or 'text/x-html+tr',
            'live': val(act, SCHEMA.target) if act else ''})

caps = []
for s in g.subjects(RDF.type, SCHEMA.ActionAccessSpecification):
    n = val(s, SCHEMA.name); d = val(s, SCHEMA.description)
    if n: caps.append({'iri': str(s), 'name': n, 'desc': d})

software = []
for s in g.subjects(RDF.type, SCHEMA.SoftwareApplication):
    if not str(s).endswith('#this'): continue
    n = val(s, SCHEMA.name)
    if n and 'skill' not in n.lower():
        software.append({'iri': str(s), 'name': n, 'desc': val(s, SCHEMA.description), 'url': val(s, SCHEMA.url)})

# ── Build kgData for KG Explorer ──────────────────────────────────────────────
TYPE_MAP = {
    str(SCHEMA.CreativeWork): 'CreativeWork', str(SCHEMA.TechArticle): 'CreativeWork',
    str(SCHEMA.Person): 'Person', str(SCHEMA.Organization): 'Organization',
    str(SCHEMA.SoftwareApplication): 'Software', str(SCHEMA.WebAPI): 'WebAPI',
    str(SCHEMA.DataFeed): 'DataFeed', str(SCHEMA.Dataset): 'Dataset',
    str(SCHEMA.FAQPage): 'CreativeWork', str(SCHEMA.DefinedTermSet): 'CreativeWork',
    str(SCHEMA.HowTo): 'CreativeWork', str(SCHEMA.Question): 'CreativeWork',
    str(SCHEMA.Answer): 'CreativeWork', str(SCHEMA.DefinedTerm): 'Concept',
    str(SCHEMA.SoftwareSourceCode): 'Software', str(SKOS.Concept): 'Concept',
    str(OWL.Ontology): 'Ontology', str(RDFS.Class): 'Class', str(RDF.Property): 'Property',
    str(SCHEMA.ActionAccessSpecification): 'Concept',
}
PRED_LABELS = {
    str(SCHEMA.hasPart): 'hasPart', str(SCHEMA.isPartOf): 'isPartOf',
    str(SCHEMA.about): 'about', str(SCHEMA.mentions): 'mentions',
    str(SCHEMA.author): 'author', str(SCHEMA.manufacturer): 'manufacturer',
    str(SCHEMA.step): 'step', str(SCHEMA.mainEntity): 'mainEntity',
    str(SCHEMA.hasDefinedTerm): 'hasDefinedTerm', str(SCHEMA.acceptedAnswer): 'acceptedAnswer',
    str(SCHEMA.potentialAction): 'potentialAction', str(SCHEMA.target): 'target',
    str(RDF.type): 'type', str(RDFS.isDefinedBy): 'isDefinedBy', str(RDFS.seeAlso): 'seeAlso',
    str(OWL.sameAs): 'sameAs', str(PROV.wasGeneratedBy): 'wasGeneratedBy',
    str(RDFS.domain): 'domain', str(RDFS.range): 'range',
}

nodes_d, links = {}, []
for s_ in g.subjects():
    if isinstance(s_, rdflib.BNode): continue
    sid = str(s_)
    types_ = [str(t) for t in g.objects(s_, RDF.type)]
    gtype = 'instance'
    for t in types_:
        if t in TYPE_MAP: gtype = TYPE_MAP[t]; break
    display = val(s_, SCHEMA.name) or val(s_, RDFS.label) or sid.split('#')[-1].split('/')[-1]
    nodes_d[sid] = {'id': sid, 'label': display, 'type': gtype, 'core': False, 'desc': val(s_, SCHEMA.description)[:120]}

for o_ in g.objects():
    if isinstance(o_, rdflib.BNode) or isinstance(o_, rdflib.Literal): continue
    oid = str(o_)
    if oid not in nodes_d:
        nodes_d[oid] = {'id': oid, 'label': oid.split('#')[-1].split('/')[-1], 'type': 'instance', 'core': False, 'desc': ''}

deg = {}
for s_, p, o_ in g:
    if isinstance(s_, rdflib.BNode) or isinstance(o_, rdflib.Literal): continue
    sid, oid, pid = str(s_), str(o_), str(p)
    if sid in nodes_d and oid in nodes_d:
        pl = PRED_LABELS.get(pid, pid.split('#')[-1].split('/')[-1])
        links.append({'source': sid, 'target': oid, 'label': pl, 'iri': pid})
        deg[sid] = deg.get(sid, 0) + 1; deg[oid] = deg.get(oid, 0) + 1

nodes = list(nodes_d.values())
for n in nodes:
    if deg.get(n['id'], 0) >= 3: n['core'] = True

kgdata_json = json.dumps({'nodes': nodes, 'links': links})

# ── HTML Sections ─────────────────────────────────────────────────────────────
def faq_html():
    rows = []
    for i, f in enumerate(faq_items):
        rows.append(f'''<div class="accordion-item" id="faq{i}">
<div class="accordion-header" onclick="toggleAccordion('faq{i}')" style="display:flex;align-items:center;justify-content:space-between">
<span><span class="accordion-num">{i+1}</span>{rlink(f['q_iri'], f['q'])}</span>
<span class="accordion-toggle">▼</span></div>
<div class="accordion-body"><p>{f['a']}</p></div></div>''')
    return '\n'.join(rows)

def glossary_html():
    rows = []
    for t in glossary_terms:
        rows.append(f'''<div class="glossary-card">
<div class="term">{rlink(t['iri'], t['name'])}</div>
<div class="def">{t['defn']}</div></div>''')
    return '\n'.join(rows)

def steps_html():
    rows = []
    for i, s in enumerate(steps):
        rows.append(f'''<div class="howto-step">
<div class="step-num">Step {s['pos']}</div>
<h4>{rlink(s['iri'], s['name'])}</h4>
<p>{s['text']}</p></div>''')
    return '\n'.join(rows)

def sparql_accordion_html():
    rows = []
    for i, sq in enumerate(sparql_queries):
        fenc = 'text/x-html-nice-turtle' if 'CONSTRUCT' in sq['text'] else 'text/x-html+tr'
        lf = urllib.parse.quote(fenc, safe='')
        lq = f'https://linkeddata.uriburner.com/sparql?default-graph-uri=&query={urllib.parse.quote(sq["text"], safe="")}&format={urllib.parse.quote(sq["fmt"], safe="")}&timeout=0&debug=on&run=+Run+Query+'
        rows.append(f'''<div class="accordion-item" id="sq{i}">
<div class="accordion-header" onclick="toggleAccordion('sq{i}')" style="display:flex;align-items:center;justify-content:space-between">
<span><span class="accordion-num">{i+1}</span>{rlink(sq['iri'], sq['name'])}</span>
<button class="sparql-run-btn" onclick="event.stopPropagation();window.open('{lq}','_blank','noopener,noreferrer')" title="Run live query">▶ Run</button></div>
<div class="accordion-body"><pre class="sparql-code">{_html.escape(sq['text'])}</pre>
<a class="sparql-live-link" href="{lq}" target="_blank" rel="noopener noreferrer">▶ Open at linkeddata.uriburner.com/sparql</a>
<p style="font-size:0.78rem;color:var(--muted);margin-top:6px">{'CONSTRUCT' if 'CONSTRUCT' in sq['text'] else 'SELECT'} uses <code>{sq['fmt']}</code> result format.</p></div></div>''')
    return '\n'.join(rows)

# ── Assemble HTML ─────────────────────────────────────────────────────────────
html = f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Databricks → Virtual Knowledge Graph with Virtuoso — RDF Infographic</title>
<link rel="related" href="../rdf/{STEM}.ttl" type="text/turtle" title="RDF Turtle companion">
<link rel="related" href="../rdf/{STEM}.jsonld" type="application/ld+json" title="JSON-LD companion">
<style>
:root {{
  --bg: #0f1117; --surface: #1a1d27; --surface2: #22263a; --border: #2e3350;
  --accent: #4f8ef7; --accent2: #7c5cfc; --accent3: #36c990; --accent4: #f7a140; --accent5: #e85c5c;
  --text: #e8ecf5; --muted: #7a82a6; --code-bg: #12151f; --sparql: #1a2840;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 15px; line-height: 1.65; }}
a {{ color: var(--accent); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.container {{ max-width: 960px; margin: 0 auto; padding: 0 24px; }}

/* Hero */
.hero {{ background: linear-gradient(135deg, #1a1d27 0%, #1a2840 50%, #1e1a30 100%); padding: 60px 24px 50px; text-align: center; border-bottom: 1px solid var(--border); }}
.hero h1 {{ font-size: 2rem; font-weight: 700; color: white; margin-bottom: 16px; line-height: 1.3; }}
.hero p {{ color: var(--muted); font-size: 1.05rem; max-width: 720px; margin: 0 auto; line-height: 1.7; }}
.hero .meta {{ margin-top: 18px; font-size: 0.82rem; color: var(--muted); }}

/* Sections */
.section {{ padding: 48px 24px; border-bottom: 1px solid var(--border); }}
.section-title {{ margin-bottom: 24px; }}
.section-title h2 {{ font-size: 1.5rem; font-weight: 700; color: var(--text); }}
.section-title p {{ color: var(--muted); margin-top: 6px; font-size: 0.92rem; }}
.eyebrow {{ font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent); margin-bottom: 6px; }}

/* Cards */
.card-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }}
.card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 20px; }}
.card h4 {{ font-size: 1rem; margin-bottom: 8px; color: var(--accent); }}
.card p {{ font-size: 0.88rem; color: var(--muted); line-height: 1.6; }}

/* Capabilities */
.cap-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }}
.cap-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 20px; display: flex; gap: 14px; align-items: flex-start; }}
.cap-icon {{ font-size: 1.5rem; flex-shrink: 0; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background: var(--surface2); border-radius: 8px; }}
.cap-text h4 {{ font-size: 0.95rem; color: var(--text); margin-bottom: 4px; }}
.cap-text p {{ font-size: 0.84rem; color: var(--muted); }}

/* HowTo */
.howto-step {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 20px 24px; margin-bottom: 14px; }}
.howto-step .step-num {{ font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--accent); margin-bottom: 4px; }}
.howto-step h4 {{ font-size: 1.05rem; margin-bottom: 8px; }}
.howto-step h4 a {{ color: var(--text); }}
.howto-step p {{ font-size: 0.88rem; color: var(--muted); line-height: 1.7; }}

/* Accordion */
.accordion-item {{ border: 1px solid var(--border); border-radius: 8px; margin-bottom: 10px; overflow: hidden; }}
.accordion-header {{ padding: 14px 18px; background: var(--surface); cursor: pointer; font-weight: 600; font-size: 0.92rem; user-select: none; }}
.accordion-header:hover {{ background: var(--surface2); }}
.accordion-num {{ display: inline-block; width: 24px; height: 24px; line-height: 24px; text-align: center; background: var(--accent2); color: white; border-radius: 50%; font-size: 0.72rem; margin-right: 10px; font-weight: 700; }}
.accordion-toggle {{ transition: transform 0.2s; font-size: 0.7rem; color: var(--muted); }}
.accordion-item .accordion-header.open .accordion-toggle {{ transform: rotate(180deg); }}
.accordion-body {{ display: none; padding: 16px 18px 20px; background: var(--code-bg); font-size: 0.9rem; color: var(--text); line-height: 1.7; }}
.accordion-body.open {{ display: block; }}

/* Glossary */
.glossary-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; }}
.glossary-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 18px 20px; }}
.glossary-card .term {{ font-weight: 700; font-size: 0.95rem; margin-bottom: 6px; }}
.glossary-card .term a {{ color: var(--accent); }}
.glossary-card .def {{ font-size: 0.85rem; color: var(--muted); line-height: 1.6; }}

/* SPARQL */
pre.sparql-code {{ background: var(--code-bg); border: 1px solid var(--border); border-radius: 6px; padding: 16px; font-family: "JetBrains Mono","SF Mono",monospace; font-size: 0.78rem; line-height: 1.6; color: var(--text); overflow-x: auto; white-space: pre; tab-size: 2; margin: 8px 0; }}
.sparql-run-btn {{ background: var(--accent); color: white; border: none; border-radius: 4px; padding: 4px 12px; cursor: pointer; font-size: 0.72rem; font-weight: 600; }}
.sparql-live-link {{ display: inline-block; margin-top: 8px; font-size: 0.8rem; color: var(--accent); }}

/* Nav */
#fnav {{ position: fixed; top: 20px; right: 20px; z-index: 1000; font-family: -apple-system, sans-serif; min-width: 180px; max-width: 340px; }}
#fnav-header {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 8px 12px; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; cursor: move; user-select: none; }}
#fnav-header span {{ font-weight: 600; font-size: 0.82rem; color: var(--text); }}
#fnav-header button {{ background: none; border: none; color: var(--muted); cursor: pointer; font-size: 1.1rem; padding: 0 4px; }}
#fnav-links {{ max-height: 0; overflow: hidden; transition: max-height 0.25s ease; }}
#fnav-links.open {{ max-height: 600px; overflow-y: auto; }}
#fnav-links div {{ padding: 8px 12px; border-bottom: 1px solid var(--border); background: var(--surface); font-size: 0.78rem; }}
#fnav-links div:last-child {{ border-bottom: none; border-radius: 0 0 8px 8px; }}
#fnav-links div a {{ color: var(--muted); display: block; padding: 3px 0; }}
#fnav-links div a:hover {{ color: var(--accent); }}
#themeToggle {{ background: none; border: 1px solid var(--border); border-radius: 4px; color: var(--muted); cursor: pointer; font-size: 0.85rem; padding: 2px 6px; }}

/* KG Explorer */
#kg-section {{ padding: 36px 24px; }}
#kg-explorer {{ position: relative; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; background: var(--surface); }}
#kg-explorer.kg-active {{ border-color: var(--accent); box-shadow: 0 0 12px rgba(79,142,247,0.25); }}
#kg-svg {{ width: 100%; height: 450px; display: block; cursor: grab; }}
#kg-explorer.kg-active #kg-svg {{ cursor: grabbing; }}
#kg-toolbar {{ padding: 12px 16px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; border-bottom: 1px solid var(--border); }}
#kg-toolbar button {{ padding: 5px 12px; border: 1px solid var(--border); border-radius: 6px; background: var(--surface); color: var(--text); cursor: pointer; font-size: 0.75rem; }}
#kg-toolbar button.active {{ background: var(--accent); color: white; border-color: var(--accent); }}
#kg-controls {{ display: none; padding: 12px 16px; border-bottom: 1px solid var(--border); background: var(--surface2); }}
#kg-controls.open {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }}
#kg-counts {{ font-size: 0.7rem; color: var(--muted); padding: 4px 10px; }}
#kg-filter-chips {{ display: flex; flex-wrap: wrap; gap: 6px; padding: 8px 16px; border-bottom: 1px solid var(--border); }}
.filter-chip {{ padding: 3px 10px; border-radius: 12px; font-size: 0.68rem; cursor: pointer; border: 1px solid var(--border); background: var(--surface); color: var(--muted); }}
.filter-chip.active {{ background: var(--accent); color: white; border-color: var(--accent); }}

/* SPARQL Workbench */
.sparql-launch {{ background: var(--surface2); border: 1px solid var(--border); border-radius: 10px; padding: 24px; margin-top: 24px; }}
.sparql-head {{ display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; }}
.sparql-head h3 {{ font-size: 1rem; font-weight: 600; color: var(--text); }}
.sparql-grid {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }}
.sparql-field {{ display: flex; flex-direction: column; gap: 3px; font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }}
.sparql-field select, .sparql-field input {{ padding: 5px 8px; border: 1px solid var(--border); border-radius: 6px; font-size: 0.78rem; background: var(--surface); color: var(--text); }}
.sparql-editor {{ width: 100%; height: 160px; font-family: "JetBrains Mono","SF Mono",monospace; font-size: 0.8rem; padding: 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--code-bg); color: var(--text); resize: vertical; margin-bottom: 12px; tab-size: 2; }}
.sparql-actions {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
.sparql-actions button {{ padding: 7px 14px; border: 1px solid var(--border); border-radius: 6px; background: var(--surface); color: var(--text); cursor: pointer; font-size: 0.78rem; }}
.sparql-actions button:hover {{ background: var(--surface2); }}
.sparql-link-preview {{ font-size: 0.7rem; color: var(--muted); word-break: break-all; font-family: "JetBrains Mono","SF Mono",monospace; }}
.sparql-note {{ font-size: 0.72rem; color: var(--muted); margin-top: 10px; }}
#sparqlBtn {{ display: inline-block; background: var(--accent); color: white; padding: 10px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; }}
#sparqlBtn:hover {{ opacity: 0.88; text-decoration: none; }}

/* Footer */
footer {{ padding: 36px 24px; text-align: center; border-top: 1px solid var(--border); color: var(--muted); font-size: 0.84rem; line-height: 1.8; }}
footer a {{ color: var(--accent); }}
.attribution-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; margin-top: 20px; text-align: left; }}
.attribution-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; }}
.attribution-label {{ font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--accent); margin-bottom: 4px; }}
.attribution-card p {{ font-size: 0.78rem; }}
.attribution-card code {{ font-size: 0.7rem; word-break: break-all; }}

@media (max-width: 768px) {{
  .hero h1 {{ font-size: 1.5rem; }}
  .card-grid, .glossary-grid, .cap-grid {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>

<!-- Floating Nav -->
<div id="fnav">
  <div id="fnav-header">
    <span>☰ Navigate</span>
    <div style="display:flex;gap:4px;align-items:center">
      <button id="themeToggle" onclick="toggleTheme()" title="Toggle light/dark" aria-label="Toggle theme">🌓</button>
      <button id="nav-toggle" title="Expand navigation" aria-label="Toggle navigation" onclick="
        var l=document.getElementById('fnav-links');
        l.classList.toggle('open');
        this.textContent=l.classList.contains('open')?'−':'+';
      ">+</button>
    </div>
  </div>
  <div id="fnav-links">
    <div><a href="#concepts" style="font-weight:600;color:var(--accent)">Key Concepts</a></div>
    <div><a href="#capabilities">Capabilities</a></div>
    <div><a href="#standards">W3C Standards</a></div>
    <div><a href="#software">Software Stack</a></div>
    <div><a href="#howto">How-To Guide</a></div>
    <div><a href="#sparql-queries">SPARQL Queries</a></div>
    <div><a href="#dataset">Bakehouse Dataset</a></div>
    <div><a href="#faq">FAQ</a></div>
    <div><a href="#glossary">Glossary</a></div>
    <div><a href="#kg-section">KG Explorer</a></div>
  </div>
</div>

<!-- Hero -->
<section class="hero">
  <div class="container">
    <h1>From Databricks Tables<br>to a Virtual Knowledge Graph with Virtuoso</h1>
    <p>{g.value(NS.analysis, SCHEMA.abstract)}</p>
    <p class="meta">Source: <a href="{SOURCE}" target="_blank" rel="noopener noreferrer">OpenLink Community</a> · {g.value(NS.analysis, SCHEMA.datePublished)} · Author: {rlink('https://github.com/danielhmills#this', 'danielhm')}</p>
  </div>
</section>

<!-- Key Concepts -->
<section class="section" id="concepts">
  <div class="container">
    <div class="eyebrow">Core Concepts</div>
    <div class="section-title"><h2>{rlink(NS.conceptsSection, 'Key Concepts')}</h2></div>
    <div class="card-grid">
''' + '\n'.join(f'''<div class="card"><h4>{rlink(c['iri'], c['name'])}</h4><p>{c['desc']}</p></div>''' for c in concepts) + f'''
    </div>
  </div>
</section>

<!-- Capabilities -->
<section class="section" id="capabilities">
  <div class="container">
    <div class="eyebrow">Value Proposition</div>
    <div class="section-title"><h2>{rlink(NS.capabilitiesSection, 'Capabilities Enabled')}</h2></div>
    <div class="cap-grid">
''' + '\n'.join(f'''<div class="cap-card"><div class="cap-icon">{'🔗' if 'Linked' in c['name'] else '🧠' if 'reasoning' in c['name'].lower() else '📡' if 'interop' in c['name'].lower() else '⚡' if 'Zero' in c['name'] else '🏷️' if 'enrichment' in c['name'].lower() else '🏭' if 'Production' in c['name'] else '🔗'}</div><div class="cap-text"><h4>{rlink(c['iri'], c['name'])}</h4><p>{c['desc']}</p></div></div>''' for c in caps) + f'''
    </div>
  </div>
</section>

<!-- W3C Standards -->
<section class="section" id="standards">
  <div class="container">
    <div class="eyebrow">Open Standards</div>
    <div class="section-title"><h2>{rlink(NS.standardsSection, 'W3C Standards & Technologies')}</h2></div>
    <div class="card-grid">
''' + '\n'.join(f'''<div class="card"><h4>{rlink(c['iri'], c['name'])}</h4><p>{c['desc']}</p></div>''' for c in concepts if 'zero' not in c['name'].lower() and 'loosely' not in c['name'].lower() and 'agent' not in c['name'].lower() and 'hyperlink' not in c['name'].lower() and 'content' not in c['name'].lower()) + f'''
    </div>
  </div>
</section>

<!-- HowTo -->
<section class="section" id="howto">
  <div class="container">
    <div class="eyebrow">Step-by-Step Guide</div>
    <div class="section-title"><h2>{rlink(NS.howtoSection, 'How to Build a Virtual Knowledge Graph from Databricks')}</h2></div>
    {steps_html()}
  </div>
</section>

<!-- SPARQL Queries -->
<section class="section" id="sparql-queries">
  <div class="container">
    <div class="section-title"><h2>SPARQL Query Examples</h2></div>
    <p style="color:var(--muted);margin-bottom:16px">Ready-to-run queries against the {rlink('http://demo.openlinksw.com/databricks-bakehouse-r2rml#', 'bakehouse virtual knowledge graph')}. SELECT uses <code>text/x-html+tr</code>; CONSTRUCT uses <code>text/x-html-nice-turtle</code>.</p>
    {sparql_accordion_html()}
  </div>
</section>

<!-- FAQ -->
<section class="section" id="faq">
  <div class="container">
    <div class="eyebrow">FAQ</div>
    <div class="section-title"><h2>{rlink(NS.faqSection, 'Frequently Asked Questions')}</h2></div>
    {faq_html()}
  </div>
</section>

<!-- Glossary -->
<section class="section" id="glossary">
  <div class="container">
    <div class="section-title"><h2>{rlink(NS.glossarySection, 'Glossary')}</h2></div>
    <div class="glossary-grid">
      {glossary_html()}
    </div>
  </div>
</section>

<!-- KG Explorer -->
<section class="section" id="kg-section">
  <div class="container">
    <div class="section-title"><h2>Knowledge Graph Explorer</h2></div>
    <div id="kg-explorer">
      <div id="kg-toolbar">
        <button id="kg-controls-btn" onclick="var c=document.getElementById('kg-controls');c.classList.toggle('open');this.textContent=c.classList.contains('open')?'Hide Controls':'Controls'">Controls</button>
        <button id="mode-basic" class="active" onclick="setMode('Basic')">Basic</button>
        <button id="mode-advanced" onclick="setMode('Advanced')">Advanced</button>
        <button id="density-core" class="active" onclick="setDensity('Core')">Core</button>
        <button id="density-full" onclick="setDensity('Full')">Full</button>
        <span id="kg-counts" style="margin-left:auto">157 nodes / 273 links</span>
      </div>
      <div id="kg-filter-chips">
        <span class="filter-chip active" onclick="toggleNodeType('Concept')" data-type="Concept">Concepts</span>
        <span class="filter-chip active" onclick="toggleNodeType('CreativeWork')" data-type="CreativeWork">Creative Works</span>
        <span class="filter-chip active" onclick="toggleNodeType('Organization')" data-type="Organization">Organizations</span>
        <span class="filter-chip active" onclick="toggleNodeType('Software')" data-type="Software">Software</span>
        <span class="filter-chip active" onclick="toggleNodeType('WebAPI')" data-type="WebAPI">Web APIs</span>
        <span class="filter-chip" onclick="toggleNodeType('Class')" data-type="Class">Classes</span>
        <span class="filter-chip" onclick="toggleNodeType('Property')" data-type="Property">Properties</span>
        <span class="filter-chip" onclick="toggleNodeType('instance')" data-type="instance">Instances</span>
        <span class="filter-chip" style="border-color:var(--accent);color:var(--accent)" onclick="setAllTypes(true)">All</span>
        <span class="filter-chip" style="border-color:var(--muted);color:var(--muted)" onclick="setAllTypes(false)">None</span>
      </div>
      <div id="kg-controls">
        <label style="font-size:0.7rem">Search: <input id="kg-search" style="width:120px;padding:3px 6px;border:1px solid var(--border);border-radius:4px;background:var(--surface);color:var(--text);font-size:0.72rem" placeholder="node name..." oninput="renderKG()"></label>
        <label style="font-size:0.7rem">Charge: <input type="range" id="kg-charge" min="-1200" max="-50" value="-400" oninput="updatePhysics()" style="width:80px"></label>
        <label style="font-size:0.7rem">Link: <input type="range" id="kg-linkdist" min="40" max="320" value="100" oninput="updatePhysics()" style="width:80px"></label>
        <button onclick="renderKG()" style="padding:3px 8px;font-size:0.7rem;border:1px solid var(--border);border-radius:4px;background:var(--surface);color:var(--text);cursor:pointer">Refresh</button>
      </div>
      <svg id="kg-svg"></svg>
    </div>
    <p style="margin-top:8px;font-size:0.7rem;color:var(--muted);text-align:center">Click inside graph to activate zoom · Click outside to release · Drag nodes to pin · Double-click to unpin</p>
  </div>
</section>

<!-- SPARQL Workbench -->
<div class="container">
  <div class="sparql-launch" id="sparql-explorer">
    <div class="sparql-head"><div><h3>Explore Knowledge Graph using SPARQL</h3></div><a id="sparqlBtn" class="run-query" href="https://linkeddata.uriburner.com/sparql" target="_blank" rel="noopener noreferrer">Run live query</a></div>
    <div class="sparql-grid">
      <label class="sparql-field">Named graph<select id="sparqlGraph"><option value="{DEMO_GRAPH}" selected>Bakehouse Demo Graph (live)</option><option value="{GRAPH_TTL}">Companion TTL graph</option><option value="{GRAPH_JSONLD}">Companion JSON-LD graph</option></select></label>
      <label class="sparql-field">Query recipe<select id="sparqlRecipe"><option value="select" selected>SELECT triples</option><option value="describe">DESCRIBE source article</option><option value="construct">CONSTRUCT compact graph</option></select></label>
      <label class="sparql-field">Result format<input id="sparqlFormat" value="text/x-html+tr" readonly></label>
    </div>
    <textarea id="sparqlText" class="sparql-editor" spellcheck="false" aria-label="Editable SPARQL query"></textarea>
    <div class="sparql-actions"><button id="sparqlRefresh" type="button">Refresh live link</button><button id="sparqlCopy" type="button">Copy query</button><span id="sparqlLinkPreview" class="sparql-link-preview"></span></div>
    <p class="sparql-note">SELECT uses <code>text/x-html+tr</code>. DESCRIBE and CONSTRUCT use <code>text/x-html-nice-turtle</code>.</p>
  </div>
</div>

<!-- Footer -->
<footer>
  <div class="container">
    <p style="margin-bottom:14px">
      Generated using
      <a href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator" target="_blank" rel="noopener noreferrer">kg-generator</a>,
      <a href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/rdf-infographic-skill" target="_blank" rel="noopener noreferrer">rdf-infographic-skill</a>
      via <a href="https://www.deepseek.com/" target="_blank" rel="noopener noreferrer">DeepSeek V4 Pro</a>.
      Linked Data resolved via <a href="https://linkeddata.uriburner.com/" target="_blank" rel="noopener noreferrer">URIBurner</a>
      (<a href="https://virtuoso.openlinksw.com/" target="_blank" rel="noopener noreferrer">Virtuoso</a>-backed).
    </p>
    <div class="attribution-grid">
      <div class="attribution-card"><span class="attribution-label">Source</span><p><a href="{SOURCE}" target="_blank" rel="noopener noreferrer">OpenLink Community — Databricks + Virtuoso</a></p></div>
      <div class="attribution-card"><span class="attribution-label">Companion RDF</span><p><a href="../rdf/{STEM}.ttl" target="_blank" rel="noopener noreferrer">{STEM}.ttl</a> · <a href="../rdf/{STEM}.jsonld" target="_blank" rel="noopener noreferrer">JSON-LD</a></p></div>
      <div class="attribution-card"><span class="attribution-label">Named Graph</span><p><code>{GRAPH_TTL}</code></p></div>
      <div class="attribution-card"><span class="attribution-label">Resolver</span><p><code>linkeddata.uriburner.com/describe/?url={{IRI}}</code></p></div>
    </div>
  </div>
</footer>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
// ── Accordion ─────────────────────────────────────────────────────────────
function toggleAccordion(id) {{
  var el = document.getElementById(id);
  var hdr = el.querySelector('.accordion-header');
  var body = el.querySelector('.accordion-body');
  hdr.classList.toggle('open');
  body.classList.toggle('open');
}}

// ── Navigation ────────────────────────────────────────────────────────────
(function() {{
  var panel = document.getElementById('fnav'), header = document.getElementById('fnav-header');
  var dragging = false, startX, startY, origLeft, origTop;
  header.addEventListener('mousedown', function(e) {{
    if (e.target.tagName === 'BUTTON') return;
    dragging = true; panel.classList.add('dragging');
    startX = e.clientX; startY = e.clientY;
    var rect = panel.getBoundingClientRect();
    origLeft = rect.left; origTop = rect.top;
    panel.style.right = 'auto'; panel.style.left = origLeft + 'px'; panel.style.top = origTop + 'px';
    e.preventDefault();
  }});
  document.addEventListener('mousemove', function(e) {{
    if (!dragging) return;
    panel.style.left = (origLeft + e.clientX - startX) + 'px';
    panel.style.top = (origTop + e.clientY - startY) + 'px';
  }});
  document.addEventListener('mouseup', function() {{ dragging = false; panel.classList.remove('dragging'); }});

  // Restore position
  var k = 'fnav-pos-' + window.location.pathname.split('/').pop();
  var saved = localStorage.getItem(k);
  if (saved) {{
    try {{
      var p = JSON.parse(saved);
      if (p.l > -100 && p.t > -100 && p.l < window.innerWidth + 200) {{
        panel.style.right = 'auto'; panel.style.left = p.l + 'px'; panel.style.top = p.t + 'px';
      }}
    }} catch(e) {{}}
  }}
  window.addEventListener('beforeunload', function() {{
    var rect = panel.getBoundingClientRect();
    if (rect.left > -100 && rect.top > -100) {{
      localStorage.setItem(k, JSON.stringify({{l: rect.left, t: rect.top}}));
    }}
  }});
}})();

// ── Theme ─────────────────────────────────────────────────────────────────
function toggleTheme() {{
  var html = document.documentElement;
  var cur = html.getAttribute('data-theme');
  var next = cur === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  document.getElementById('themeToggle').textContent = next === 'dark' ? '🌓' : '☀️';
}}

// ── KG Explorer ───────────────────────────────────────────────────────────
var kgData = {kgdata_json};
var kgMode = 'Basic', kgDensity = 'Core';
var activeTypes = new Set(['Concept','CreativeWork','Organization','Software','WebAPI']);
var kgSim = null, kgZoomActive = false;

function getFiltered() {{
  var nodes = kgData.nodes.filter(function(n) {{
    if (kgDensity === 'Core' && !n.core) return false;
    return activeTypes.has(n.type);
  }});
  var nids = new Set(nodes.map(function(n) {{ return n.id; }}));
  var links = kgData.links.filter(function(l) {{
    return nids.has(l.source) && nids.has(l.target);
  }});
  if (kgMode === 'Basic') links = links.slice(0, 50);
  var search = (document.getElementById('kg-search') || {{}}).value;
  if (search) {{
    var q = search.toLowerCase();
    nodes = nodes.filter(function(n) {{ return n.label.toLowerCase().indexOf(q) >= 0; }});
    var snids = new Set(nodes.map(function(n) {{ return n.id; }}));
    links = links.filter(function(l) {{ return snids.has(l.source) && snids.has(l.target); }});
  }}
  return {{nodes: nodes, links: links}};
}}

function setMode(m) {{
  kgMode = m;
  document.getElementById('mode-basic').classList.toggle('active', m === 'Basic');
  document.getElementById('mode-advanced').classList.toggle('active', m === 'Advanced');
  renderKG();
}}

function setDensity(d) {{
  kgDensity = d;
  document.getElementById('density-core').classList.toggle('active', d === 'Core');
  document.getElementById('density-full').classList.toggle('active', d === 'Full');
  renderKG();
}}

function toggleNodeType(t) {{
  if (activeTypes.has(t)) activeTypes.delete(t); else activeTypes.add(t);
  document.querySelectorAll('#kg-filter-chips .filter-chip[data-type="' + t + '"]').forEach(function(c) {{
    c.classList.toggle('active', activeTypes.has(t));
  }});
  renderKG();
}}

function setAllTypes(on) {{
  var allTypes = new Set(kgData.nodes.map(function(n) {{ return n.type; }}));
  document.querySelectorAll('#kg-filter-chips .filter-chip[data-type]').forEach(function(c) {{
    if (on) activeTypes.add(c.getAttribute('data-type'));
    else activeTypes.delete(c.getAttribute('data-type'));
    c.classList.toggle('active', on);
  }});
  renderKG();
}}

function updatePhysics() {{
  if (!kgSim) return;
  var charge = document.getElementById('kg-charge').value;
  var linkdist = document.getElementById('kg-linkdist').value;
  kgSim.force('charge').strength(Number(charge));
  kgSim.force('link').distance(Number(linkdist));
  kgSim.alpha(0.3).restart();
}}

var nodeColor = {{'Organization':'#f7a140','Software':'#4f8ef7','Concept':'#36c990','CreativeWork':'#7c5cfc','WebAPI':'#e85c5c','Class':'#ea580c','Property':'#0ea5e9','Ontology':'#c084fc','instance':'#7a82a6','Dataset':'#059669','DataFeed':'#06b6d4','Person':'#f59e0b'}};

function renderKG() {{
  if (kgSim) {{ kgSim.stop(); kgSim = null; }}
  var svg = d3.select('#kg-svg');
  svg.selectAll('*').remove();
  var fd = getFiltered(), nodes = fd.nodes, links = fd.links;
  document.getElementById('kg-counts').textContent = nodes.length + ' nodes / ' + links.length + ' links';
  var W = document.getElementById('kg-explorer').clientWidth || 900, H = 450;
  svg.attr('viewBox', [0, 0, W, H]);
  var g = svg.append('g');

  svg.append('defs').append('marker').attr('id','arrowhead').attr('viewBox','0 -6 12 12').attr('refX',14).attr('refY',0).attr('markerWidth',6).attr('markerHeight',6).attr('orient','auto').append('path').attr('d','M0,-6L12,0L0,6').attr('fill','#7a82a6');

  kgSim = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(function(d) {{ return d.id; }}).distance(100))
    .force('charge', d3.forceManyBody().strength(-400))
    .force('center', d3.forceCenter(W/2, H/2))
    .force('collision', d3.forceCollide(30))
    .on('tick', function() {{
      lk.attr('x1',function(d){{return d.source.x}}).attr('y1',function(d){{return d.source.y}})
        .attr('x2',function(d){{return d.target.x}}).attr('y2',function(d){{return d.target.y}});
      ln.attr('transform',function(d){{return'translate('+d.x+','+d.y+')'}});
      lb.attr('x',function(d){{return(d.source.x+d.target.x)/2}}).attr('y',function(d){{return(d.source.y+d.target.y)/2}});
    }});

  var lk = g.append('g').selectAll('line').data(links).join('line')
    .attr('stroke','#4a5078').attr('stroke-width',1).attr('marker-end','url(#arrowhead)');

  var ln = g.append('g').selectAll('g').data(nodes).join('g')
    .attr('cursor','pointer')
    .call(d3.drag().on('start',function(e,d){{if(!e.sourceEvent||e.sourceEvent.detail<2){{d.fx=d.x;d.fy=d.y;kgSim.alphaTarget(0.3).restart()}}}}).on('drag',function(e,d){{d.fx=e.x;d.fy=e.y}}).on('end',function(e,d){{kgSim.alphaTarget(0)}}))
    .on('dblclick',function(e,d){{d.fx=null;d.fy=null;kgSim.alpha(0.3).restart()}})
    .on('click',function(e,d){{if(d3.event&&d3.event.defaultPrevented)return;window.open('{RESOLVER}'+encodeURIComponent(d.id),'_blank','noopener,noreferrer')}});

  ln.append('circle').attr('r',function(d){{return d.core?8:5}})
    .attr('fill',function(d){{return nodeColor[d.type]||'#7a82a6'}});

  ln.append('a')
    .attr('href',function(d){{return'{RESOLVER}'+encodeURIComponent(d.id)}})
    .attr('target','_blank').attr('rel','noopener noreferrer')
    .attr('data-iri',function(d){{return d.id}})
    .attr('data-resolver-href',function(d){{return'{RESOLVER}'+encodeURIComponent(d.id)}})
    .append('text').text(function(d){{return d.label.length>25?d.label.slice(0,23)+'…':d.label}})
    .attr('dy',-10).attr('text-anchor','middle').attr('font-size','8px').attr('fill','var(--muted)');

  var lb = g.append('g').selectAll('a').data(links).join('a')
    .attr('href',function(d){{return'{RESOLVER}'+encodeURIComponent(d.iri)}})
    .attr('target','_blank').attr('rel','noopener noreferrer')
    .attr('xlink:href',function(d){{return'{RESOLVER}'+encodeURIComponent(d.iri)}})
    .attr('data-iri',function(d){{return d.iri}})
    .attr('data-resolver-href',function(d){{return'{RESOLVER}'+encodeURIComponent(d.iri)}})
    .attr('aria-label',function(d){{return d.label+' — open predicate IRI in resolver'}})
    .append('text').text(function(d){{return d.label}})
    .attr('text-anchor','middle').attr('font-size','7px').attr('fill','var(--accent)').attr('dy',-4)
    .style('cursor','pointer');

  window._kgSvg = svg; window._kgG = g; window._kgSim = kgSim;
  if (kgZoomActive) svg.call(window._kgZoom);
}}

// Zoom isolation
(function() {{
  var explorer = document.getElementById('kg-explorer');
  var svgEl = document.getElementById('kg-svg');
  window._kgZoom = d3.zoom().scaleExtent([0.15,6]).on('zoom', function(e) {{
    if (window._kgG) window._kgG.attr('transform', e.transform);
  }});

  svgEl.addEventListener('click', function(e) {{
    if (kgZoomActive) return;
    kgZoomActive = true;
    explorer.classList.add('kg-active');
    d3.select('#kg-svg').call(window._kgZoom);
  }});

  document.addEventListener('click', function(e) {{
    if (!kgZoomActive) return;
    if (!explorer.contains(e.target)) {{
      kgZoomActive = false;
      explorer.classList.remove('kg-active');
      d3.select('#kg-svg').on('.zoom', null);
    }}
  }});
}})();

// Initial render
renderKG();

// ── SPARQL Workbench ──────────────────────────────────────────────────────
(function() {{
  var SPARQL='https://linkeddata.uriburner.com/sparql';
  var SOURCE='{SOURCE}';
  var g=document.getElementById('sparqlGraph'),r=document.getElementById('sparqlRecipe'),
      t=document.getElementById('sparqlText'),f=document.getElementById('sparqlFormat'),
      b=document.getElementById('sparqlBtn'),p=document.getElementById('sparqlLinkPreview');
  function qf(k,gr) {{
    if(k==='describe')return 'DESCRIBE <'+SOURCE+'>\\nFROM <'+gr+'>';
    if(k==='construct')return 'CONSTRUCT {{ ?s ?p ?o }}\\nWHERE {{\\n  GRAPH <'+gr+'> {{\\n    ?s ?p ?o .\\n    FILTER(?p IN (<http://schema.org/about>, <http://schema.org/name>, <http://schema.org/hasPart>, <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>))\\n  }}\\n}}\\nLIMIT 100';
    return 'PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\\n\\nSELECT ?type (SAMPLE(?s) AS ?sampleEntity) (SAMPLE(?label) AS ?sampleLabel) (COUNT(?s) AS ?entityCount)\\nWHERE {{\\n  GRAPH <'+gr+'> {{\\n    ?s rdf:type ?type .\\n    OPTIONAL {{ ?s rdfs:label ?label }}\\n  }}\\n}}\\nGROUP BY ?type\\nORDER BY DESC(?entityCount)';
  }}
  function fmt(q){{var f_=q.trim().split(/\\s+/,1)[0].toUpperCase();return f_==='DESCRIBE'||f_==='CONSTRUCT'?'text/x-html-nice-turtle':'text/x-html+tr';}}
  function st(){{t.value=qf(r.value,g.value);upd();}}
  function upd(){{var q=t.value.trim(),fm=fmt(q);f.value=fm;b.href=SPARQL+'?default-graph-uri=&query='+encodeURIComponent(q)+'&format='+encodeURIComponent(fm)+'&timeout=0&debug=on&run=+Run+Query+';p.textContent='🔗 Live query link ready';}}
  g.addEventListener('change',st);r.addEventListener('change',st);t.addEventListener('input',upd);
  document.getElementById('sparqlRefresh').addEventListener('click',upd);
  document.getElementById('sparqlCopy').addEventListener('click',function(){{navigator.clipboard?.writeText(t.value);this.textContent='Copied!';setTimeout(function(){{document.getElementById('sparqlCopy').textContent='Copy query'}},1200)}});
  st();
}})();
</script>

<script type="application/ld+json">
{{
  "@context": {{"@vocab": "http://schema.org/", "@language": "en", "prov": "http://www.w3.org/ns/prov#"}},
  "@type": "WebPage",
  "name": "Databricks → Virtual Knowledge Graph with Virtuoso — RDF Infographic",
  "description": "{g.value(NS.analysis, SCHEMA.abstract)}",
  "dateCreated": "2026-06-16",
  "dateModified": "2026-06-16",
  "author": {{"@id": "https://www.linkedin.com/in/kidehen#this", "@type": "Person", "name": "Kingsley Uyi Idehen"}},
  "accountablePerson": {{"@id": "https://www.linkedin.com/in/kidehen#this"}},
  "isBasedOn": "{SOURCE}",
  "relatedLink": [{{"@id": "../rdf/{STEM}.ttl"}}, {{"@id": "../rdf/{STEM}.jsonld"}}],
  "prov:wasGeneratedBy": [
    {{"@type": ["SoftwareApplication", "prov:SoftwareAgent"], "@id": "https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator#this", "name": "kg-generator", "url": "https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator", "description": "Knowledge graph generation skill for AI agents", "prov:actedOnBehalfOf": {{"@id": "https://www.linkedin.com/in/kidehen#this"}}}},
    {{"@type": ["SoftwareApplication", "prov:SoftwareAgent"], "@id": "https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/rdf-infographic-skill#this", "name": "rdf-infographic-skill", "url": "https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/rdf-infographic-skill", "description": "HTML infographic generation skill from RDF knowledge graphs", "prov:actedOnBehalfOf": {{"@id": "https://www.linkedin.com/in/kidehen#this"}}}}
  ]
}}
</script>
</body>
</html>'''

with open(OUT_PATH, 'w') as f:
    f.write(html)
print(f'✓ HTML written: {OUT_PATH}')
print(f'Size: {len(html):,} bytes')
print(f'Sections: concepts({len(concepts)}), capabilities({len(caps)}), steps({len(steps)}), faq({len(faq_items)}), glossary({len(glossary_terms)}), sparql({len(sparql_queries)})')
