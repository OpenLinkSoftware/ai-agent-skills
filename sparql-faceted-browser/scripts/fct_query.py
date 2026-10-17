#!/usr/bin/env python3
"""Answer in chat with the same SPARQL the SPARQL Faceted Browser runs for a view.

Give the view either as a link (--link, e.g. one the user pasted) or as fct_state.py build options, then say what
to fetch. The query text matches the app's generator (sql/facet.sql-style FCT query tree), so the rows here are the
rows the app shows, and every answer comes with the app link for the same view.

    fct_query.py [--link LINK | --ep EP OPS...] [--what WHAT] [--limit N] [--offset N] [--lang xx]
                 [--profile auto|virtuoso|generic|wikidata] [--timeout MS] [--no-anytime] [--dedupe auto|on|off]
                 [--format md|table|json] [--show-query] [--all-langs] [--app URL]

WHAT (default: from the view in the link/options)
    members    entities of the focused set (ranked by IRI_RANK on Virtuoso)
    count      how many members
    types      type facet with counts          props / props-in   property facets with counts
    values     values of --prop P (or the view's property), with counts  (--incoming for P pointing at members)
    distinct   members with the number of trail solutions reaching each (FCT 'Distinct (Count)')
    describe   statements about --entity IRI (or the view's entity)
    overview   entity types of the whole endpoint with a SAMPLE() member each (Explore)

Engine behaviour mirrors the app: Virtuoso gets bif:contains text search, IRI_RANK ordering and Anytime (partial
results at the timeout, flagged in the output); other engines get CONTAINS() and plain DISTINCT; Wikidata uses
EntitySearch and wdt:P31. Fallbacks: no IRI_RANK (SR185) → unranked; sorted-TOP cap (SR353) → unsorted;
cost-estimate refusal (42000) on a facet → the count-free list; a rejected SAMPLE() describe → the plain list.
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fct_state as st  # noqa: E402

NS = st.NS
LABEL_PROPS = ['rdfs:label', 'skos:prefLabel', 'schema:name', 'foaf:name', 'dcterms:title', 'dc:title']
ANNOT_PROPS = ['rdfs:label', 'rdfs:comment', 'skos:prefLabel', 'skos:altLabel', 'skos:hiddenLabel', 'skos:definition', 'skos:note',
               'skos:scopeNote', 'dc:title', 'dc:description', 'dcterms:title', 'dcterms:description', 'dcterms:abstract', 'dbo:abstract', 'schema:name',
               'schema:alternateName', 'schema:description', 'foaf:name']
ANNOT_IRIS = [NS[c.split(':')[0]] + c.split(':')[1] for c in ANNOT_PROPS] + ['https://schema.org/name', 'https://schema.org/alternateName', 'https://schema.org/description']
ANYTIME_MAX_MS = 30000


class QueryError(Exception):
    def __init__(self, msg, status=None, body=''):
        super().__init__(msg)
        self.status, self.body = status, body


# ---------- transport ----------
def http_sparql(ep, query, timeout_ms=20000, anytime=False):
    """GET a SPARQL query; returns (json, partial). curl is used because it handles the certificates of the endpoints
    this app targets more reliably than Python's bundled store."""
    params = {'query': query, 'format': 'application/sparql-results+json'}
    if anytime:
        params['timeout'] = str(min(timeout_ms, ANYTIME_MAX_MS))
    url = ep + ('&' if '?' in ep else '?') + urllib.parse.urlencode(params)
    wait = max(timeout_ms / 1000 + 15, 30)
    cmd = ['curl', '-sS', '-L', '--max-time', str(int(wait)), '-H', 'Accept: application/sparql-results+json',
           '-D', '-', '-o', '-', url]
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=wait + 5).stdout.decode('utf-8', 'replace')
    except subprocess.TimeoutExpired:
        raise QueryError('No response after %d s' % wait)
    # split the (possibly repeated, on redirects) header blocks from the body
    head, body = '', out
    while body.startswith('HTTP/'):
        h, _, body = body.partition('\r\n\r\n')
        head = h
    m = re.match(r'HTTP/\S+ (\d+)', head)
    status = int(m.group(1)) if m else 0
    headers = {k.strip().lower(): v.strip() for k, _, v in (ln.partition(':') for ln in head.split('\r\n')[1:])}
    if not body.strip() and status < 400:
        raise QueryError('Empty reply from %s (network blocked or unreachable, or the endpoint closed the connection)' % ep, status, body)
    if status >= 400 or status == 0:
        text = re.sub(r'<[^>]+>', ' ', body)
        raise QueryError('HTTP %d: %s' % (status, re.sub(r'\s+', ' ', text).strip()[:400]), status, body)
    try:
        j = json.loads(body)
    except ValueError:
        j = parse_xml_results(body)   # some endpoints (Wikidata among them) answer in SPARQL XML whatever was asked
        if j is None:
            raise QueryError('Not SPARQL results: ' + body[:160], status, body)
    partial = headers.get('x-sql-state') == 'S1TAT' or status == 206
    return j, partial


def parse_xml_results(body):
    """SPARQL Query Results XML → the JSON shape (results.bindings / boolean); None if it is not that format."""
    import xml.etree.ElementTree as ET
    ns = '{http://www.w3.org/2005/sparql-results#}'
    try:
        root = ET.fromstring(body.encode('utf-8'))
    except ET.ParseError:
        return None
    if root.tag != ns + 'sparql':
        return None
    boolean = root.find(ns + 'boolean')
    if boolean is not None:
        return {'boolean': boolean.text.strip() == 'true'}
    out = []
    for res in root.iter(ns + 'result'):
        b = {}
        for bd in res.findall(ns + 'binding'):
            node = list(bd)[0]
            kind = node.tag[len(ns):]
            if kind == 'uri':
                b[bd.get('name')] = {'type': 'uri', 'value': node.text or ''}
            elif kind == 'bnode':
                b[bd.get('name')] = {'type': 'bnode', 'value': node.text or ''}
            else:
                t = {'type': 'literal', 'value': node.text or ''}
                lang = node.get('{http://www.w3.org/XML/1998/namespace}lang')
                if lang:
                    t['xml:lang'] = lang
                elif node.get('datatype'):
                    t['datatype'] = node.get('datatype')
                b[bd.get('name')] = t
        out.append(b)
    return {'results': {'bindings': out}}


def rows(j):
    return (j.get('results') or {}).get('bindings') or []


# ---------- context (what the app keeps in settings) ----------
class Ctx:
    def __init__(self, ep, lang, profile='auto', timeout=20000, anytime=True, dedupe='auto', type_prop=None):
        self.ep, self.lang, self.timeout, self.anytime_pref, self.dedupe = ep, lang, timeout, anytime, dedupe
        self.profile = profile if profile != 'auto' else detect_profile(ep)
        self.type_prop = st.expand(type_prop) if type_prop else (NS['wdt'] + 'P31' if self.profile == 'wikidata' or 'wikidata' in ep else NS['rdf'] + 'type')
        self.ranked = True
        self.partial = False
        self.queries = []

    @property
    def anytime(self):
        return self.anytime_pref and self.profile == 'virtuoso'

    def dedupe_on(self):
        return self.dedupe == 'on' or (self.dedupe != 'off' and self.profile == 'virtuoso')

    def run(self, q, name):
        self.queries.append((name, q))
        try:
            j, partial = http_sparql(self.ep, q, self.timeout, self.anytime)
        except QueryError as e:
            if e.status not in (502, 503, 504) and not str(e).startswith('Empty reply'):
                raise
            time.sleep(3)   # gateway hiccup or dropped connection in front of the endpoint: one retry
            j, partial = http_sparql(self.ep, q, self.timeout, self.anytime)
        self.partial = self.partial or partial
        return rows(j)


def detect_profile(ep):
    if 'wikidata.org' in ep:
        return 'wikidata'
    try:
        r = rows(http_sparql(ep, 'SELECT ?x WHERE { BIND (bif:length ("ab") AS ?x) }', 15000)[0])
        return 'virtuoso' if r else 'generic'
    except QueryError:
        return 'generic'


# ---------- SPARQL terms (as the app writes them) ----------
def iri_ref(i):
    return '<' + re.sub(r'[<>"{}|^`\\\s]', lambda m: urllib.parse.quote(m.group(0)), str(i)) + '>'


def P(c):
    return iri_ref(st.expand(c))


def lit_str(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r') + '"'


def term_sparql(t):
    if t['type'] == 'uri':
        return iri_ref(t['value'])
    s = lit_str(t['value'])
    if t.get('xml:lang'):
        s += '@' + t['xml:lang']
    elif t.get('datatype'):
        s += '^^' + iri_ref(t['datatype'])
    return s


NUM_DT = re.compile(r'#(integer|decimal|double|float|int|long|short|byte|nonNegativeInteger|positiveInteger|unsignedInt|unsignedLong)$')


def bound_literal(raw, dt):
    raw = str(raw).strip()
    if (not dt or NUM_DT.search(dt)) and re.match(r'^-?\d+(\.\d+)?(e[-+]?\d+)?$', raw, re.I):
        return raw
    if dt:
        return lit_str(raw) + '^^' + iri_ref(dt)
    if re.match(r'^\d{4}-\d{2}-\d{2}$', raw):
        return lit_str(raw) + '^^' + iri_ref(NS['xsd'] + 'date')
    return lit_str(raw)


# ---------- query builder (port of the app's FCT query tree → SPARQL) ----------
def sv(i):
    return '?s%d' % (i + 1)


class Builder:
    def __init__(self, ctx, nav):
        self.c, self.nav = ctx, nav

    def prologue(self):
        if self.c.profile == 'wikidata':
            return 'PREFIX wikibase: <http://wikiba.se/ontology#>\nPREFIX bd: <http://www.bigdata.com/rdf#>\nPREFIX mwapi: <https://www.mediawiki.org/ontology#API/>\n'
        return ''

    def ft_expr(self, text):
        words = [w for w in re.sub(r'["\'\\()*&|!~^]', ' ', text).split() if w][:12]
        return ' AND '.join('"%s*"' % w if len(w) >= 4 else '"%s"' % w for w in words)

    def text_pattern(self, s, node, i):
        t = node.get('text', '').strip()
        if not t:
            return ''
        o = '?txt%d' % (i + 1)
        if self.c.profile == 'wikidata':
            return ('SERVICE wikibase:mwapi { bd:serviceParam wikibase:api "EntitySearch" ; wikibase:endpoint "www.wikidata.org" ; mwapi:search '
                    + lit_str(t) + ' ; mwapi:language ' + lit_str(self.c.lang) + ' . ' + s + ' wikibase:apiOutputItem mwapi:item . }')
        if self.c.profile == 'virtuoso':
            tp = '?txtp%d' % (i + 1)
            return (s + ' ' + tp + ' ' + o + ' . ' + o + " bif:contains '" + self.ft_expr(t) + "' ." +
                    ('' if node.get('scope') == 'any' else ' FILTER (' + tp + ' IN (' + ', '.join(P(x) for x in LABEL_PROPS) + '))'))
        pred = '?txtp%d' % (i + 1) if node.get('scope') == 'any' else '(' + '|'.join(P(x) for x in LABEL_PROPS) + ')'
        return s + ' ' + pred + ' ' + o + ' . FILTER (isLiteral (' + o + ') && CONTAINS (LCASE (STR (' + o + ')), ' + lit_str(t.lower()) + '))'

    def cond_pattern(self, s, c, aux):
        if c['t'] == 'is':
            return ('FILTER (!sameTerm (' + s + ', ' + term_sparql(c['v']) + '))') if c.get('neg') else 'VALUES ' + s + ' { ' + term_sparql(c['v']) + ' }'
        if c['t'] == 'class':
            tp = s + ' ' + iri_ref(self.c.type_prop) + ' ' + iri_ref(c['iri']) + ' .'
            return 'FILTER NOT EXISTS { ' + tp + ' }' if c.get('neg') else tp
        if c['t'] == 'pv':
            if c.get('vs'):
                x = aux()
                inner = 'VALUES ' + x + ' { ' + ' '.join(term_sparql(t) for t in c['vs']) + ' } ' + ((x + ' ' + iri_ref(c['p']) + ' ' + s + ' .') if c['dir'] == 'in' else (s + ' ' + iri_ref(c['p']) + ' ' + x + ' .'))
            elif c.get('v'):
                t = term_sparql(c['v'])
                inner = (t + ' ' + iri_ref(c['p']) + ' ' + s + ' .') if c['dir'] == 'in' else (s + ' ' + iri_ref(c['p']) + ' ' + t + ' .')
            else:
                x = aux()
                inner = (x + ' ' + iri_ref(c['p']) + ' ' + s + ' .') if c['dir'] == 'in' else (s + ' ' + iri_ref(c['p']) + ' ' + x + ' .')
                f = []
                if c.get('lo') not in (None, ''):
                    f.append(x + ' >= ' + bound_literal(c['lo'], c.get('dt')))
                if c.get('hi') not in (None, ''):
                    f.append(x + ' <= ' + bound_literal(c['hi'], c.get('dt')))
                if f:
                    inner += ' FILTER (' + ' && '.join(f) + ')'
            return 'FILTER NOT EXISTS { ' + inner + ' }' if c.get('neg') else inner
        return ''

    def where(self, bound=None, skip=None):
        """skip=(i, p, dir): leave out set i's positive value filters on that property, as the app does for value lists
        (multi-select facets: with FRA picked, the country list still shows DEU and ITA)."""
        lines, k = [], [0]

        def skipped(i, c):
            return (skip is not None and skip[0] == i and c['t'] == 'pv' and not c.get('neg') and c['p'] == skip[1]
                    and c['dir'] == skip[2] and (c.get('v') or c.get('vs')))

        def aux():
            k[0] += 1
            return '?v%d' % k[0]
        for i, node in enumerate(self.nav['nodes']):
            s = sv(i)
            conds = node.get('conds', [])
            lines += [self.cond_pattern(s, c, aux) for c in conds if c['t'] == 'is' and not c.get('neg')]
            if node.get('text'):
                lines.append(self.text_pattern(s, node, i))
            if i > 0:
                via, prev = node['via'], sv(i - 1)
                lines.append((s + ' ' + iri_ref(via['p']) + ' ' + prev + ' .') if via['dir'] == 'in' else (prev + ' ' + iri_ref(via['p']) + ' ' + s + ' .'))
            lines += [self.cond_pattern(s, c, aux) for c in conds if c['t'] != 'is' and not c.get('neg') and not skipped(i, c)]
            if not (i > 0 or node.get('text') or any(not c.get('neg') for c in conds)) and i != bound:
                lines.append(s + ' ?anyp ?anyo .')
            lines += [self.cond_pattern(s, c, aux) for c in conds if c.get('neg')]
        return '\n'.join('  ' + ln for ln in lines if ln)

    def sel(self, proj, body, tail=''):
        return self.prologue() + 'SELECT ' + proj + '\nWHERE {\n' + body + '\n}' + ('\n' + tail if tail else '')

    @staticmethod
    def page(lim, off):
        return 'LIMIT %d' % lim + (' OFFSET %d' % off if off else '')

    # views
    def members(self, f, off, lim, ranked=True):
        if self.c.profile == 'virtuoso' and ranked:
            return self.sel(sv(f), self.where(), 'GROUP BY ' + sv(f) + ' ORDER BY DESC (<LONG::IRI_RANK> (' + sv(f) + ')) ' + self.page(lim, off))
        return self.sel('DISTINCT ' + sv(f), self.where(), self.page(lim, off))

    def count(self, f):
        return self.sel('(COUNT (DISTINCT ' + sv(f) + ') AS ?n)', self.where())

    def types(self, f, off, lim, plain=False):
        body = self.where(f) + '\n  ' + sv(f) + ' ' + iri_ref(self.c.type_prop) + ' ?c .'
        return self.sel('DISTINCT ?c', body, self.page(lim, off)) if plain else self.sel('?c (COUNT (DISTINCT ' + sv(f) + ') AS ?n)', body, 'GROUP BY ?c ORDER BY DESC (?n) ' + self.page(lim, off))

    def props(self, f, d, off, lim, plain=False):
        body = self.where(f) + '\n  ' + ('?o ?p ' + sv(f) if d == 'in' else sv(f) + ' ?p ?o') + ' .'
        return self.sel('DISTINCT ?p', body, self.page(lim, off)) if plain else self.sel('?p (COUNT (DISTINCT ' + sv(f) + ') AS ?n)', body, 'GROUP BY ?p ORDER BY DESC (?n) ' + self.page(lim, off))

    def values(self, f, p, d, off, lim):
        body = self.where(f, (f, p, d)) + '\n  ' + ('?v ' + iri_ref(p) + ' ' + sv(f) if d == 'in' else sv(f) + ' ' + iri_ref(p) + ' ?v') + ' .'
        return self.sel('?v (COUNT (DISTINCT ' + sv(f) + ') AS ?n)', body, 'GROUP BY ?v ORDER BY DESC (?n) ' + self.page(lim, off))

    def distinct(self, f, off, lim):
        allv = ' '.join(sv(i) for i in range(len(self.nav['nodes'])))
        return self.sel(sv(f) + ' (COUNT (*) AS ?n)', '  { SELECT DISTINCT ' + allv + ' WHERE {\n' + self.where() + '\n  } }', 'GROUP BY ' + sv(f) + ' ORDER BY DESC (?n) ' + self.page(lim, off))

    def overview(self, off, lim):
        body = '  ?s1 ' + iri_ref(self.c.type_prop) + ' ?type .\n  FILTER (!isBlank (?s1) && !isBlank (?type))'
        return self.sel('?type (SAMPLE (?s1) AS ?sample) (COUNT (?s1) AS ?n)', body, 'GROUP BY ?type ORDER BY DESC (?n) ' + self.page(lim, off))

    def describe(self, e, mode, off, lim):
        """mode 'sample': fold annotation literals with SAMPLE(); 'lang': keep every value; both limited to the preferred
        language or untagged. mode 'all': no language filter (the app's 'All values & languages')."""
        E = iri_ref(e)
        lang = lit_str(self.c.lang)
        sampled = mode == 'sample'
        ok = lambda v: '(LANG (' + v + ') = "" || LANGMATCHES (LANG (' + v + '), ' + lang + '))'  # noqa: E731
        if sampled:
            annot = '(?p IN (' + ', '.join(iri_ref(i) for i in ANNOT_IRIS) + ') || EXISTS { ?p a <http://www.w3.org/2002/07/owl#AnnotationProperty> })'
            union = ('  { { SELECT ?p (SAMPLE (?lo) AS ?o) (COUNT (?lo) AS ?n) WHERE {\n      ' + E + ' ?p ?lo .\n      FILTER (isLiteral (?lo) && ' + annot + ' && ' + ok('?lo') + ')\n    } GROUP BY ?p } BIND ("out" AS ?dir) }\n'
                     '  UNION { ' + E + ' ?p ?o . FILTER (!isLiteral (?o) || (!' + annot + ' && ' + ok('?o') + ')) BIND ("out" AS ?dir) }\n'
                     '  UNION { ?o ?p ' + E + ' . BIND ("in" AS ?dir) }')
        elif mode == 'lang':
            union = '  { ' + E + ' ?p ?o . FILTER (!isLiteral (?o) || ' + ok('?o') + ') BIND ("out" AS ?dir) }\n  UNION { ?o ?p ' + E + ' . BIND ("in" AS ?dir) }'
        else:
            union = '  { ' + E + ' ?p ?o . BIND ("out" AS ?dir) }\n  UNION { ?o ?p ' + E + ' . BIND ("in" AS ?dir) }'
        return self.sel('?dir ?p ?o' + (' ?n' if sampled else ''), union, 'ORDER BY DESC (?dir) ?p ' + self.page(lim, off))


def strip_order(q):
    return re.sub(r'\n(GROUP BY \S+ )?ORDER BY [^\n]*?(LIMIT \d+( OFFSET \d+)?)$', lambda m: '\n' + (m.group(1) or '') + m.group(2), q)


# ---------- labels: label → CURIE → raw IRI ----------
def label_key(iri):
    """Wikidata property IRIs in every form (wdt:, p:, ps:, pq:, …) take their label from the entity wd:P123."""
    m = re.match(r'^http://www\.wikidata\.org/prop/(?:[a-z-]+/)*(P\d+)$', iri)
    return NS['wd'] + m.group(1) if m else iri


def pick_lang(cands, want):
    """Same preference as the app: exact language, then a language-prefix match, then untagged, then the first."""
    for test in (lambda c: c[1] == want, lambda c: c[1] and c[1].startswith(want), lambda c: not c[1], lambda c: True):
        for c in cands:
            if test(c):
                return c[0]
    return None


def fetch_labels(ctx, iris):
    iris = [i for i in dict.fromkeys(iris) if i]
    out = {}
    path = '(' + '|'.join(P(x) for x in LABEL_PROPS) + ')'
    for k in range(0, len(iris), 60):
        chunk = iris[k:k + 60]
        keyed = {label_key(x): x for x in chunk}
        q = ('SELECT ?x ?l\nWHERE {\n  VALUES ?x { ' + ' '.join(iri_ref(i) for i in keyed) + ' }\n  ?x ' + path + ' ?l .\n'
             '  FILTER (isLiteral (?l) && (LANG (?l) = "" || LANGMATCHES (LANG (?l), ' + lit_str(ctx.lang) + ')))\n}\nLIMIT %d' % (len(chunk) * 8))
        try:
            j, _ = http_sparql(ctx.ep, q, 15000, False)
        except QueryError:
            continue
        by = {}
        for r in rows(j):
            x = keyed.get(r['x']['value'], r['x']['value'])
            by.setdefault(x, []).append((r['l']['value'], (r['l'].get('xml:lang') or '').lower()))
        for x, cands in by.items():
            out[x] = pick_lang(cands, ctx.lang)
    return out


def display(iri, labels):
    if iri in labels:
        return labels[iri], 'label'
    sh = st.short(iri)
    if not sh.startswith('<'):
        return sh, 'curie'
    return iri, 'raw'


def md_link(iri, labels):
    text, _ = display(iri, labels)
    return '[%s](%s)' % (text.replace('[', '\\[').replace(']', '\\]').replace('|', '\\|'), iri)


def cell(t, labels, fmt):
    if t is None:
        return ''
    if t['type'] == 'uri':
        return md_link(t['value'], labels) if fmt == 'md' else display(t['value'], labels)[0]
    v = t['value']
    v = v if len(v) <= 160 else v[:160] + '…'
    if t.get('xml:lang'):
        v += ' @' + t['xml:lang']
    return v.replace('|', '\\|').replace('\n', ' ') if fmt == 'md' else v


# ---------- running a request ----------
def run(ctx, nav, what, off, lim, prop=None, incoming=False, entity=None, all_langs=False):
    b = Builder(ctx, nav)
    f = nav.get('focus', len(nav['nodes']) - 1)
    if what in ('members', 'count', 'types', 'props', 'props-in', 'values', 'distinct') and not nav['nodes']:
        raise QueryError('This view has no set yet: add --text, --type or --entity (or use --what describe/overview).')
    cols, data = [], []
    if what == 'members':
        q = b.members(f, off, lim)
        try:
            data = ctx.run(q, 'members')
        except QueryError as e:
            if 'SR185' in str(e) or 'IRI_RANK' in str(e):
                q = b.members(f, off, lim, ranked=False); data = ctx.run(q, 'members (unranked)')
            elif 'SR353' in str(e) or 'Sorted TOP' in str(e):
                q = strip_order(q); data = ctx.run(q, 'members (unsorted)')
            else:
                raise
        cols = [('entity', sv(f)[1:])]
    elif what == 'count':
        data = ctx.run(b.count(f), 'count'); cols = [('count', 'n')]
    elif what in ('types', 'props', 'props-in'):
        def q_(plain):
            return b.types(f, off, lim, plain) if what == 'types' else b.props(f, 'in' if what == 'props-in' else 'out', off, lim, plain)
        try:
            data = ctx.run(q_(False), what)
            cols = [('type' if what == 'types' else 'property', 'c' if what == 'types' else 'p'), ('members', 'n')]
        except QueryError as e:
            if 'estimated execution time' not in str(e):
                raise
            data = ctx.run(q_(True), what + ' (without counts)')
            cols = [('type' if what == 'types' else 'property', 'c' if what == 'types' else 'p')]
    elif what == 'values':
        vp = nav.get('vp') or {}
        p = st.expand(prop) if prop else vp.get('p')
        if not p:
            raise QueryError('values needs --prop P (or a link opened on a property\'s values)')
        d = 'in' if incoming else (vp.get('dir', 'out') if not prop else 'out')
        data = ctx.run(b.values(f, p, d, off, lim), 'values'); cols = [('value', 'v'), ('members', 'n')]
    elif what == 'distinct':
        data = ctx.run(b.distinct(f, off, lim), 'distinct'); cols = [('member', sv(f)[1:]), ('solutions', 'n')]
    elif what == 'overview':
        data = ctx.run(b.overview(off, lim), 'overview'); cols = [('type', 'type'), ('sample', 'sample'), ('entities', 'n')]
    elif what == 'describe':
        e = st.expand(entity) if entity else nav.get('ent')
        if not e:
            raise QueryError('describe needs --entity IRI (or a link opened on a description)')
        mode = 'all' if all_langs else ('sample' if ctx.dedupe_on() else 'lang')
        sampled = mode == 'sample'
        try:
            data = ctx.run(b.describe(e, mode, off, lim), 'describe')
        except QueryError:
            if not sampled:
                raise
            sampled = False
            data = ctx.run(b.describe(e, 'lang', off, lim), 'describe (language-filtered, unfolded)')
        cols = [('direction', 'dir'), ('property', 'p'), ('value', 'o')] + ([('values folded', 'n')] if sampled else [])
    else:
        raise QueryError('Unknown --what ' + what)
    return cols, data


def default_what(nav):
    v = nav.get('view', 'entities')
    if v == 'describe' and nav.get('ent'):
        return 'describe'
    if v == 'values':
        return 'values' if nav.get('vp') else 'distinct'
    return 'members' if nav.get('nodes') else 'overview'


def render(cols, data, labels, fmt):
    if fmt == 'json':
        return [{name: (r.get(var) or {}) | ({'label': labels[r[var]['value']]} if r.get(var, {}).get('type') == 'uri' and r[var]['value'] in labels else {})
                 for name, var in cols} for r in data]
    lines = []
    if fmt == 'md':
        lines.append('| ' + ' | '.join(c for c, _ in cols) + ' |')
        lines.append('|' + '---|' * len(cols))
    for r in data:
        vals = []
        for name, var in cols:
            t = r.get(var)
            if name in ('count', 'members', 'entities', 'solutions', 'values folded') and t:
                vals.append('{:,}'.format(int(float(t['value']))))
            else:
                vals.append(cell(t, labels, fmt))
        lines.append(('| ' + ' | '.join(vals) + ' |') if fmt == 'md' else '  '.join(vals))
    return '\n'.join(lines)


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__); return 0
    take = st.take
    link = take(argv, '--link')
    what = take(argv, '--what')
    lim = int(take(argv, '--limit', '25')); off = int(take(argv, '--offset', '0'))
    lang = take(argv, '--lang')
    profile = take(argv, '--profile', 'auto')
    timeout = int(take(argv, '--timeout', '20000'))
    dedupe = take(argv, '--dedupe', 'auto')
    fmt = take(argv, '--format', 'md')
    prop = take(argv, '--prop'); entity = take(argv, '--entity-iri') or take(argv, '--about')
    app = take(argv, '--app'); ep_opt = take(argv, '--ep'); type_prop = take(argv, '--type-prop')
    flags = {f: (f in argv) for f in ('--show-query', '--no-anytime', '--incoming', '--all-langs')}
    argv = [a for a in argv if a not in flags]
    if link:
        base, state, cfg = st.parse_link(link)
        app = app or base
        lang = lang or cfg.get('lang')
        state = state or {'ep': ep_opt or st.DEFAULT_EP, 'nav': None}
        nav = state.get('nav') or st.empty_nav()
        if argv:
            nav = st.apply_ops(nav, argv)
        ep = ep_opt or state['ep']
    else:
        ep = ep_opt or st.DEFAULT_EP
        nav = st.apply_ops(st.empty_nav(), argv)
    link_lang = lang   # only an explicitly requested language travels in the app link (&cfg=)
    lang = (lang or os.environ.get('FCT_LANG') or 'en').lower()
    ctx = Ctx(ep, lang, profile, timeout, not flags['--no-anytime'], dedupe, type_prop)
    what = what or default_what(nav)
    if what == 'describe' and entity and not nav.get('ent'):
        nav['ent'] = st.expand(entity); nav['view'] = 'describe'
    try:
        cols, data = run(ctx, nav, what, off, lim, prop, flags['--incoming'], entity, flags['--all-langs'] or bool(nav.get('allLangs')))
    except QueryError as e:
        out = {'error': str(e), 'endpoint': ep, 'profile': ctx.profile, 'queries': [q for _, q in ctx.queries]}
        print(json.dumps(out, indent=2) if fmt == 'json' else 'error: ' + str(e), file=sys.stdout if fmt == 'json' else sys.stderr)
        return 1
    iris = [r[v]['value'] for r in data for _, v in cols if r.get(v, {}).get('type') == 'uri']
    labels = fetch_labels(ctx, iris) if iris else {}
    view_link = st.make_link({'ep': ep, 'nav': nav}, link_lang, app)
    if fmt == 'json':
        print(json.dumps({'endpoint': ep, 'profile': ctx.profile, 'what': what, 'partial': ctx.partial, 'rows': render(cols, data, labels, fmt),
                          'link': view_link, 'queries': [q for _, q in ctx.queries] if flags['--show-query'] else None}, indent=2, ensure_ascii=False))
        return 0
    print(render(cols, data, labels, fmt))
    meta = '%d row%s · %s · %s' % (len(data), '' if len(data) == 1 else 's', ctx.profile, ep)
    if ctx.partial:
        meta += ' · PARTIAL (Virtuoso Anytime: the endpoint stopped at its time budget)'
    print('\n' + meta)
    print('Open this view: ' + view_link)
    if flags['--show-query']:
        for name, q in ctx.queries:
            print('\n# ' + name + '\n' + q)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except (st.UsageError, QueryError) as e:
        print('error: ' + str(e), file=sys.stderr)
        sys.exit(2)
