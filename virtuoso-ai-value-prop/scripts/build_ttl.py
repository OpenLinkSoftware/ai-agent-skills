#!/usr/bin/env python3
"""Generate assets/virtuoso-ai-value-prop.ttl, the RDF complement of the app, from the catalog and the talking points.

    python3 scripts/build_ttl.py

The Turtle describes the app's value-proposition functionality: the capabilities, the claims and the live example
that proves each one, the datasets (named graphs) and their state, every showcase query with its app deep link and
access conditions, the OPAL agents and their prompts, the FAQ, the page sections, and the instance profiles (the
hosts that serve each role, as schema:EntryPoint URL templates).

All app-local IRIs are relative (<#…>, <virtuoso-ai-value-prop.html#…>), so the file resolves against wherever it
is deployed next to the app. Inputs: references/catalog.json (exported from the app) and the claims table in
references/talking-points.md. Run it after scripts/build_catalog.mjs.
"""
import datetime
import json
import os
import re
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CATALOG = os.path.join(ROOT, 'references', 'catalog.json')
TALKING = os.path.join(ROOT, 'references', 'talking-points.md')
OUT = os.path.join(ROOT, 'assets', 'virtuoso-ai-value-prop.ttl')
APP = 'virtuoso-ai-value-prop.html'
SKILL = 'https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/virtuoso-ai-value-prop#this'
AUTHOR = 'https://www.linkedin.com/in/kidehen#this'

# DBpedia IRIs, each confirmed by dereferencing (rdfs:label lookup) before being added here.
DBMS = {
    'northwind': 'http://dbpedia.org/resource/Virtuoso_Universal_Server',
    'sqlserver': 'http://dbpedia.org/resource/Microsoft_SQL_Server',
    'postgres': 'http://dbpedia.org/resource/PostgreSQL',
    'csv': 'http://dbpedia.org/resource/Comma-separated_values',
}
# databricks has no entry yet: dbpedia.org was down for maintenance on 2026-10-19, so their
# IRIs could not be confirmed.
VIRTUOSO = 'http://dbpedia.org/resource/Virtuoso_Universal_Server'
# http://dbpedia.org/resource/OpenLink_Software could not be verified (no label, no redirect on 2026-10-18), so the
# publisher is a local entity identified by its home page.

CAPABILITIES = [
    ('rdf-views', 'RDF Views', 'Quad maps that present the tables of any ODBC- or JDBC-accessible DBMS as RDF without copying them; SPARQL is translated to SQL against the source tables at query time.'),
    ('super-key', 'Row hyperlinks as cross-platform super-keys', 'Every row gets its own hyperlink, which works as a cross-platform super-key: a key that keeps its meaning outside its own database and resolves to a description of the row.'),
    ('sql-xmla', 'SQL over XMLA', 'SQL sent to Virtuoso over the XML for Analysis SOAP protocol, from a browser, through the SPASQL Query Builder.'),
    ('spasql', 'SPASQL', 'SPARQL inside a SQL FROM clause, so the result of a SPARQL query behaves like a derived table in SQL.'),
    ('sparql', 'SPARQL over RDF Views', 'SPARQL queries over the same rows that SQL reads, following links instead of foreign-key columns.'),
    ('sponger', 'Sponger', 'Virtuoso Linked Data middleware: cartridges read a web resource and store RDF in a named graph whose IRI is the source URL.'),
    ('faceted-browse', 'Faceted browsing', 'The explore query lists every type in a named graph with a sample and a count; each type opens in a faceted browser.'),
    ('opal-agents', 'OPAL agents loosely coupled with Data Spaces', 'Agents hold instructions and a list of query functions, not a copy of the data; answers come from predefined SQL, SPARQL or SPASQL queries that can be inspected.'),
    ('access-control', 'Access control with the data', 'ABAC ACLs on the server decide who may run what: anonymous SPARQL, signed-in SQL and SPASQL, signed-in sponging and query-backed agent answers.'),
    ('deep-links', 'Conversation deep links', 'Every example, dataset, agent question and section has a link that opens the app on that exact view, so a conversation can hand over to the app.'),
    ('ontology-generation', 'Ontology generation from SQL schemas', 'Generating an RDF View also generates its ontology: a class per table, a typed datatype property per column, an object property per foreign key, each with its own IRI and a label naming the SQL source; the classes are then aligned with shared ontologies (rdfs:subClassOf, owl:equivalentClass) so one query in a shared vocabulary reaches every source.'),
    ('instance-profiles', 'Instance profiles', 'The hosts that serve each role (RDF Views data, linked data and Sponger, OPAL, widget, faceted browser, app) are configuration, with URIBurner as the default profile.'),
]
CLAIM_CAP = {1: 'super-key', 2: 'rdf-views', 3: 'rdf-views', 4: 'spasql', 5: 'sql-xmla', 6: 'sponger', 7: 'faceted-browse',
             8: 'opal-agents', 9: 'opal-agents', 10: 'access-control', 11: 'ontology-generation'}
LANG_NAME = {'sql': 'SQL', 'spasql': 'SPASQL', 'sparql': 'SPARQL'}


def lit(s):
    s = str(s).replace('\\', '\\\\').replace('"', '\\"')
    if '\n' in s:
        return '"""' + s.replace('\\"', '"').replace('"""', '\\"\\"\\"') + '"""@en'
    return '"' + s + '"@en'


def iri(u):
    return '<' + re.sub(r'[<>"{}|\\^`\s]', lambda m: urllib.parse.quote(m.group(0)), u) + '>'


def app_link(fragment):
    return iri(APP + fragment)


def block(subject, types, props):
    lines = ['%s a %s' % (subject, ', '.join(types))]
    for p, objs in props:
        if objs is None or objs == [] or objs == '':
            continue
        if not isinstance(objs, list):
            objs = [objs]
        lines.append('    %s %s' % (p, ' ,\n        '.join(objs)))
    return ' ;\n'.join(lines) + ' .\n'


def parse_claims():
    rows = []
    with open(TALKING, encoding='utf-8') as f:
        for line in f:
            m = re.match(r'^\|\s*(\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*(.+)\|\s*$', line)
            if m:
                rows.append((int(m.group(1)), m.group(2).strip(), m.group(3).strip(), m.group(4).strip()))
    return rows


def proof_refs(proof, cat):
    ex_ids = {e['id'] for e in cat['examples']} | {e['id'] for e in cat['sponger']}
    refs = []
    for tok in re.findall(r'`([^`]+)`', proof):
        tok = tok.strip()
        if tok in ex_ids:
            refs.append('<#ex-%s>' % tok)
        elif tok.startswith('--explore '):
            refs.append('<#explore-%s>' % tok.split()[1])
        elif tok.startswith('--agent '):
            refs.append('<#agent-%s>' % tok.split()[1])
        elif re.match(r'^[a-z-]+$', tok) and any(s['id'] == tok for s in cat['sections']):
            refs.append('<#section-%s>' % tok)
    for sec in re.findall(r'the `?([a-z-]+)`? section', proof):
        r = '<#section-%s>' % sec
        if r not in refs and any(s['id'] == sec for s in cat['sections']):
            refs.append(r)
    return refs


def main():
    with open(CATALOG, encoding='utf-8') as f:
        cat = json.load(f)
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    dflt = cat['config']['profiles'][cat['config']['default']]
    out = ['''@prefix schema: <http://schema.org/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix sd: <http://www.w3.org/ns/sparql-service-description#> .
@prefix void: <http://rdfs.org/ns/void#> .

# Generated by scripts/build_ttl.py from references/catalog.json and references/talking-points.md. Do not edit by
# hand: change the app (then node scripts/build_catalog.mjs) or the talking points, and regenerate.
''']
    out.append(block('<>', ['schema:CreativeWork'], [
        ('schema:about', '<#app>'),
        ('schema:name', lit('Virtuoso Data Spaces: value proposition, showcases and instance profiles')),
        ('schema:description', lit('RDF description of the Virtuoso Data Spaces app: the capabilities it demonstrates, the claims and the live example behind each, the datasets and their state, every showcase query with its deep link, the OPAL agents, and the instance profiles that make the app portable across Virtuoso hosts.')),
        ('schema:encodingFormat', lit('text/turtle')),
        ('schema:dateCreated', '"%s"^^xsd:dateTime' % now),
        ('schema:dateModified', '"%s"^^xsd:dateTime' % now),
        ('schema:author', iri(AUTHOR)),
        ('prov:wasGeneratedBy', iri(SKILL)),
    ]))
    out.append(block(iri(SKILL), ['schema:SoftwareSourceCode'], [
        ('schema:name', lit('virtuoso-ai-value-prop')),
        ('schema:codeRepository', iri('https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/virtuoso-ai-value-prop')),
        ('schema:description', lit('Agent skill that makes the case for Virtuoso in conversation, with live proof, and opens the Virtuoso Data Spaces app at the exact view.')),
    ]))
    out.append(block('<#openlink>', ['schema:Organization'], [
        ('schema:name', lit('OpenLink Software')), ('schema:url', iri('https://www.openlinksw.com/'))]))
    caps = ['<#cap-%s>' % c[0] for c in CAPABILITIES]
    out.append(block('<#app>', ['schema:WebApplication'], [
        ('schema:name', lit('Virtuoso Data Spaces')),
        ('schema:url', iri(APP)),
        ('schema:description', lit('Single-page app of live Virtuoso showcases: RDF Views over any ODBC- or JDBC-accessible DBMS queried by SQL over XMLA, SPASQL and SPARQL; Sponger graphs; faceted browsing; and OPAL agents.')),
        ('schema:applicationCategory', lit('Data and AI showcase')),
        ('schema:operatingSystem', lit('Any modern web browser')),
        ('schema:featureList', [lit(c[1]) for c in CAPABILITIES]),
        ('schema:about', ['<#capabilities>'] + ['<#claim-%d>' % r[0] for r in parse_claims()]),
        ('schema:hasPart', ['<#section-%s>' % s['id'] for s in cat['sections']]),
        ('schema:mentions', [iri(VIRTUOSO)]),
        ('schema:publisher', '<#openlink>'),
        ('schema:isPartOf', iri(SKILL)),
        ('schema:isBasedOn', ['<#source-%d>' % (i + 1) for i in range(len(cat['sources']))]),
    ]))
    out.append(block('<#capabilities>', ['schema:DefinedTermSet'], [
        ('schema:name', lit('Capabilities the app demonstrates')),
        ('schema:hasDefinedTerm', caps),
    ]))
    for cid, name, desc in CAPABILITIES:
        out.append(block('<#cap-%s>' % cid, ['schema:DefinedTerm'], [
            ('schema:name', lit(name)), ('schema:description', lit(desc)), ('schema:inDefinedTermSet', '<#capabilities>')]))
    for n, name, text, proof in parse_claims():
        out.append(block('<#claim-%d>' % n, ['schema:Claim'], [
            ('schema:name', lit(name)), ('schema:text', lit(text)), ('schema:position', '"%d"^^xsd:integer' % n),
            ('schema:about', '<#cap-%s>' % CLAIM_CAP.get(n, 'rdf-views')),
            ('schema:isBasedOn', proof_refs(proof, cat)),
        ]))
    # datasets (RDF Views)
    for d in cat['datasets']:
        graph = d['meta'].get('Graph') or d['meta'].get('Graphs', '').split('·')[0].strip()
        props = [('schema:name', lit(d['label'])), ('schema:description', lit(d['meta'].get('Database', ''))),
                 ('sd:name', iri(graph)), ('void:sparqlEndpoint', iri(dflt['rdfViews']['sparql'])),
                 ('void:vocabulary', iri(d['meta']['Ontology']) if d['meta'].get('Ontology') else None),
                 ('schema:isBasedOn', iri(DBMS[d['id']]) if d['id'] in DBMS else None),
                 ('schema:subjectOf', [iri(u) for u in d['posts']]),
                 ('prov:wasGeneratedBy', '<#cap-rdf-views>')]
        if d.get('status'):
            props.append(('rdfs:comment', lit('State: ' + d['status'])))
        out.append(block('<#dataset-%s>' % d['id'], ['schema:Dataset', 'sd:NamedGraph'], props))
    # generated ontologies
    onto = cat.get('ontologies', {})
    onto_iris = [s.strip() for s in onto.get('meta', {}).get('Ontologies', '').split('·') if s.strip()]
    out.append(block('<#dataset-ontology>', ['schema:Dataset'], [
        ('schema:name', lit(onto.get('label', 'Generated ontologies'))),
        ('schema:description', lit('Ontologies generated from SQL schemas: ' + onto.get('meta', {}).get('Generated from', ''))),
        ('schema:hasPart', [iri(u) for u in onto_iris]),
        ('void:sparqlEndpoint', iri(dflt['rdfViews']['sparql'])),
        ('prov:wasGeneratedBy', '<#cap-ontology-generation>')]))
    for u in onto_iris:
        out.append(block(iri(u), ['schema:DefinedTermSet'], [
            ('schema:name', lit('Ontology generated for ' + u.rstrip('/').rsplit('/', 1)[-1])),
            ('schema:isPartOf', '<#dataset-ontology>')]))
    # Sponger graphs
    for s in {e['source'] for e in cat['sponger']}:
        gid = 'github' if 'github.com' in s else 'techmeme'
        out.append(block('<#dataset-%s>' % gid, ['schema:Dataset', 'sd:NamedGraph'], [
            ('schema:name', lit('Sponger graph of ' + s)), ('sd:name', iri(s)), ('schema:isBasedOn', iri(s)),
            ('void:sparqlEndpoint', iri(dflt['linkedData']['sparql'])), ('prov:wasGeneratedBy', '<#cap-sponger>')]))
    # examples
    for e in cat['examples']:
        frag = '#/%s?ex=%s%s' % (e.get('view', 'rdf-views'), e['id'], '&run=1' if e['lang'] == 'sparql' else '')
        props = [('schema:identifier', lit(e['id'])), ('schema:name', lit(e['title'])),
                 ('schema:description', lit(e['description'])), ('schema:programmingLanguage', lit(LANG_NAME[e['lang']])),
                 ('schema:text', lit(e['query'])), ('schema:about', '<#dataset-%s>' % e['dataset']),
                 ('schema:url', app_link(frag)),
                 ('schema:exampleOfWork', '<#cap-%s>' % ('ontology-generation' if e.get('view') == 'ontologies' else {'sql': 'sql-xmla', 'spasql': 'spasql', 'sparql': 'sparql'}[e['lang']])),
                 ('schema:targetProduct', iri(VIRTUOSO))]
        if e['lang'] in ('sql', 'spasql'):
            props.append(('schema:conditionsOfAccess', lit('Runs in the SPASQL Query Builder on demo.openlinksw.com after sign-in: user name demo, password demo (or vdb / vdb); the instance is protected by ABAC ACLs.')))
        if e.get('verbatimUrl'):
            props.append(('schema:subjectOf', iri(e['verbatimUrl'])))
        out.append(block('<#ex-%s>' % e['id'], ['schema:SoftwareSourceCode'], props))
    for e in cat['sponger']:
        gid = 'github' if 'github.com' in e['source'] else 'techmeme'
        out.append(block('<#ex-%s>' % e['id'], ['schema:SoftwareSourceCode'], [
            ('schema:identifier', lit(e['id'])), ('schema:name', lit(e['title'])), ('schema:description', lit(e['description'])),
            ('schema:programmingLanguage', lit('SPARQL')), ('schema:text', lit(e['query'])),
            ('schema:about', '<#dataset-%s>' % gid), ('schema:url', app_link('#/sponger?ex=%s&run=1' % e['id'])),
            ('schema:exampleOfWork', '<#cap-sponger>'), ('schema:targetProduct', iri(VIRTUOSO)),
            ('schema:conditionsOfAccess', lit('Reads the graph the Sponger already holds anonymously; refreshing it (DEFINE get:soft "replace") needs a signed-in session on the linked-data host.'))]))
    # explore queries
    for x in cat['exploreDatasets']:
        out.append(block('<#explore-%s>' % x['id'], ['schema:SoftwareSourceCode'], [
            ('schema:identifier', lit('explore-' + x['id'])), ('schema:name', lit('Explore: ' + x['label'])),
            ('schema:programmingLanguage', lit('SPARQL')), ('schema:text', lit((cat.get('exploreQueryTemplateNoLabel') if x.get('noLabel') else cat['exploreQueryTemplate']).replace('{GRAPH}', x['graph']))),
            ('schema:about', '<#dataset-%s>' % x['id']), ('schema:url', app_link('#/explore?ds=' + x['id'])),
            ('schema:exampleOfWork', '<#cap-faceted-browse>'),
            ('rdfs:comment', lit(x['note']) if x.get('note') else None)]))
    # agents and prompts
    for a in cat['agents']:
        out.append(block('<#agent-%s>' % a['key'], ['schema:SoftwareApplication'], [
            ('schema:name', lit(a['label'])), ('schema:identifier', lit(a['module'])),
            ('schema:applicationCategory', lit('OPAL agent')), ('schema:url', app_link('#/agents?agent=' + a['key'])),
            ('schema:isPartOf', '<#cap-opal-agents>')]))
    for i, pr in enumerate(cat['prompts'], 1):
        out.append(block('<#prompt-%d>' % i, ['schema:Question'], [
            ('schema:text', lit(pr['text'])), ('schema:about', '<#agent-%s>' % pr['agent']),
            ('schema:url', app_link('#/agents?' + urllib.parse.urlencode({'agent': pr['agent'], 'ask': pr['text']}, quote_via=urllib.parse.quote)))]))
    # FAQ
    for i, q in enumerate(cat['faq'], 1):
        out.append(block('<#faq-%d>' % i, ['schema:Question'], [
            ('schema:name', lit(q['q'])), ('schema:acceptedAnswer', '<#faq-%d-answer>' % i), ('schema:isPartOf', '<#section-questions>')]))
        out.append(block('<#faq-%d-answer>' % i, ['schema:Answer'], [('schema:text', lit(q['a']))]))
    # sections
    for s in cat['sections']:
        out.append(block('<#section-%s>' % s['id'], ['schema:WebPageElement'], [
            ('schema:name', lit(s['title'])), ('schema:url', app_link('#' + s['id'])), ('schema:isPartOf', '<#app>')]))
    # sources
    for i, s in enumerate(cat['sources'], 1):
        out.append(block('<#source-%d>' % i, ['schema:CreativeWork'], [
            ('schema:name', lit(s['title'])), ('schema:url', iri(s['url'])), ('schema:description', lit(s['use']))]))
    # instance profiles
    roles = [('rdfViews', 'sparql', 'RDF Views SPARQL endpoint'), ('rdfViews', 'describe', 'RDF View entity description (uri and graph)'),
             ('rdfViews', 'spasqlqb', 'SPASQL Query Builder (SQL over XMLA and SPASQL)'), ('rdfViews', 'xmla', 'XMLA endpoint'),
             ('linkedData', 'sparql', 'Linked-data and Sponger SPARQL endpoint'), ('linkedData', 'sparqlAuth', 'Signed-in SPARQL endpoint (sponging)'),
             ('linkedData', 'describe', 'Linked-data entity description'), ('opal', 'agentCard', 'OPAL A2A Agent Card'),
             ('opal', 'chatUi', 'OPAL chat UI'),
             ('opal', 'widgetBase', 'OPAL widget scripts')]
    profile_iris = []
    for name, pr in cat['config']['profiles'].items():
        pid = '<#profile-%s>' % name
        profile_iris.append(pid)
        eps, props = [], []
        for grp, key, label in roles:
            v = pr.get(grp, {}).get(key)
            if not v:
                continue
            eid = '<#profile-%s-%s-%s>' % (name, grp.lower(), key.lower())
            eps.append(eid)
            out.append(block(eid, ['schema:EntryPoint'], [('schema:name', lit(label)), ('schema:urlTemplate', lit(v.replace('{IRI}', '{iri}').replace('{GRAPH}', '{graph}')))]))
        fb = '<#profile-%s-facetedbrowser>' % name
        eps.append(fb)
        out.append(block(fb, ['schema:EntryPoint'], [('schema:name', lit('SPARQL Faceted Browser app')), ('schema:urlTemplate', lit(pr['facetedBrowser'] + '#s={state}'))]))
        props = [('schema:name', lit('Instance profile: ' + pr['label'])), ('schema:identifier', lit(name)),
                 ('schema:url', iri(pr['app']) if pr.get('app') else None), ('schema:hasPart', eps),
                 ('schema:isPartOf', '<#cap-instance-profiles>'),
                 ('rdfs:comment', lit('Default profile.' if name == cat['config']['default'] else
                                      'Selected with ?profile=%s on the app URL, or made the default in the app\'s vap-config block when deploying.' % name))]
        if not pr.get('app'):
            props.append(('schema:creativeWorkStatus', lit('Not deployed yet: no app URL.')))
        out.append(block(pid, ['schema:CreativeWork'], props))
    out.append(block('<#cap-instance-profiles>', ['schema:DefinedTerm'], [('schema:hasPart', profile_iris)]))
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    print('Wrote %s' % os.path.relpath(OUT, ROOT))


if __name__ == '__main__':
    main()
