#!/usr/bin/env python3
"""Build, edit and decode SPARQL Faceted Browser links.

The app keeps its whole view in the URL hash:
    {app}#s=<base64url(JSON {ep, nav})>[&cfg=<base64url(JSON {lang})>]
This script is the only sanctioned way for the skill to produce such links: never hand-write one.

App instance resolution (first match wins):
    1. --app URL on the command line
    2. FCT_APP_URL environment variable
    3. the default URIBurner instance (DEFAULT_APP)

Subcommands
    build  [--app URL] [--ep ENDPOINT] [--lang xx] [--json] OPS...
    edit   LINK [--app URL] [--ep ENDPOINT] [--lang xx|--lang ''] [--json] OPS...
    decode LINK [--json]
    check-app [URL]
    app            print the app URL that would be used

OPS are applied left to right, so filters always attach to the most recent set:
    --text "words"           text match on labels (start a set, or add text to the current one)
    --any-literal            make the current set's text match any literal, not just labels
    --type IRI|CURIE         member must have this type          (--not-type to exclude)
    --pv P=V                 property P has value V              (--not-pv to exclude)
                             V: IRI, CURIE, <IRI>, "literal", "literal"@en, "5"^^xsd:integer, or a bare number
    --pv-in P=V              V points at the member through P (incoming)
    --pv-or P=V              or: widen the last --pv on P to also allow V (P = A or B …)
    --has P                  member has any value for P          (--has-in P for incoming)
    --range P LO HI          numeric/date range on P (use '' for an open end)
    --entity IRI             the set is exactly this entity
    --pivot P | --pivot-in P new set: the values of P (or the things pointing at the set through P)
    --focus N                focus set N (1-based)
    --view entities|values|map|describe|sparql
    --values-of P[:in]       open the values view of P for the focused set
    --describe IRI           open the description of IRI (with no trail, just that entity)
    --map-by P               Map view: colour members by property P (default: their type)
    --map-limit N            Map view: show up to N features (1000, 3000 or 10000)
    --map-in-view            Map view: re-query for the visible area as the viewer pans and zooms
"""
import base64
import json
import os
import re
import sys
import urllib.parse

DEFAULT_APP = 'https://linkeddata.uriburner.com/DAV/demos/daas/sparql-faceted-browser-claude_opus_5_5.html'
DEFAULT_EP = 'https://dbpedia.org/sparql'

# Same core prefixes as the app (it also loads prefix.cc); a CURIE outside this list must be given as a full IRI.
NS = {
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'owl': 'http://www.w3.org/2002/07/owl#', 'xsd': 'http://www.w3.org/2001/XMLSchema#',
    'skos': 'http://www.w3.org/2004/02/skos/core#', 'foaf': 'http://xmlns.com/foaf/0.1/',
    'schema': 'http://schema.org/', 'dcterms': 'http://purl.org/dc/terms/', 'dc': 'http://purl.org/dc/elements/1.1/',
    'prov': 'http://www.w3.org/ns/prov#', 'geo': 'http://www.w3.org/2003/01/geo/wgs84_pos#',
    'era': 'http://data.europa.eu/949/', 'jolux': 'http://data.legilux.public.lu/resource/ontology/jolux#',
    'dbo': 'http://dbpedia.org/ontology/', 'dbp': 'http://dbpedia.org/property/', 'dbr': 'http://dbpedia.org/resource/',
    'dbc': 'http://dbpedia.org/resource/Category:', 'yago': 'http://dbpedia.org/class/yago/',
    'wd': 'http://www.wikidata.org/entity/', 'wdt': 'http://www.wikidata.org/prop/direct/',
    'void': 'http://rdfs.org/ns/void#', 'sioc': 'http://rdfs.org/sioc/ns#', 'dcat': 'http://www.w3.org/ns/dcat#',
    'vcard': 'http://www.w3.org/2006/vcard/ns#', 'gr': 'http://purl.org/goodrelations/v1#',
    'up': 'http://purl.uniprot.org/core/',
}
LANG_RE = re.compile(r'^[a-z]{2,3}(-[a-z0-9]{1,8})*$', re.I)
VIEWS = ('entities', 'values', 'map', 'describe', 'sparql')


class UsageError(Exception):
    pass


# ---------- encoding (identical to the app's b64e / b64d) ----------
def b64e(obj):
    raw = json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')


def b64d(s):
    s = s + '=' * (-len(s) % 4)
    return json.loads(base64.urlsafe_b64decode(s.encode('ascii')).decode('utf-8'))


def app_url(explicit=None):
    url = explicit or os.environ.get('FCT_APP_URL') or DEFAULT_APP
    url = url.split('#', 1)[0]
    if not re.match(r'^https?://', url):
        raise UsageError('App URL must be http(s): ' + url)
    return url


def make_link(state, lang=None, app=None):
    link = app_url(app) + '#s=' + b64e(state)
    if lang:
        if not LANG_RE.match(lang):
            raise UsageError('Not a language tag: ' + lang)
        link += '&cfg=' + b64e({'lang': lang.lower()})
    return link


def parse_link(link):
    base, _, frag = link.partition('#')
    params = dict(re.findall(r'(?:^|&)(s|cfg)=([\w-]+)', frag))
    if 's' not in params and 'cfg' not in params:
        raise UsageError('No #s= state in that link.')
    state = b64d(params['s']) if 's' in params else None
    cfg = b64d(params['cfg']) if 'cfg' in params else {}
    return base, state, cfg


# ---------- terms ----------
def expand(t):
    t = t.strip()
    if t.startswith('<') and t.endswith('>'):
        return t[1:-1]
    if re.match(r'^(https?|urn|mailto|ftp):', t):
        return t
    m = re.match(r'^([A-Za-z][\w-]*):(.*)$', t)
    if m and m.group(1) in NS:
        return NS[m.group(1)] + m.group(2)
    raise UsageError('Unknown prefix or not an IRI: %s (use a full IRI)' % t)


def term(v):
    """Parse a value given on the command line into a SPARQL-JSON-style term, as the app stores it."""
    v = v.strip()
    m = re.match(r'^"(.*)"(?:@([A-Za-z][\w-]*)|\^\^(\S+))?$', v, re.S)
    if m:
        t = {'type': 'literal', 'value': m.group(1)}
        if m.group(2):
            t['xml:lang'] = m.group(2)
        elif m.group(3):
            t['datatype'] = expand(m.group(3))
        return t
    if re.match(r'^-?\d+$', v):
        return {'type': 'literal', 'value': v, 'datatype': NS['xsd'] + 'integer'}
    if re.match(r'^-?\d*\.\d+$', v):
        return {'type': 'literal', 'value': v, 'datatype': NS['xsd'] + 'decimal'}
    try:
        return {'type': 'uri', 'value': expand(v)}
    except UsageError:
        return {'type': 'literal', 'value': v}


def split_pv(arg):
    if '=' not in arg:
        raise UsageError('Expected P=V, got: ' + arg)
    p, v = arg.split('=', 1)
    return expand(p), term(v)


# ---------- state ----------
def empty_nav():
    return {'nodes': [], 'focus': -1, 'view': 'entities', 'off': 0, 'vp': None, 'ent': None, 'pg': {}}


def new_node(via=None):
    return {'via': via, 'text': '', 'scope': 'label', 'conds': []}


def cur(nav):
    if not nav['nodes']:
        nav['nodes'].append(new_node())
        nav['focus'] = 0
    return nav['nodes'][nav['focus']]


FILTER_OPS = {'--text', '--any-literal', '--type', '--not-type', '--pv', '--not-pv', '--pv-in', '--pv-or', '--has', '--has-in', '--range', '--entity'}


def apply_ops(nav, ops):
    """Apply OPS left to right. As in the app, adding a filter returns the view to the entity list unless a later
    --view, --values-of or --describe chooses another view."""
    i = 0
    map_opts = dict(((nav.get('pg') or {}).get('map')) or {})   # Map-view options survive an edit

    def arg():
        nonlocal i
        if i >= len(ops):
            raise UsageError('Missing value after ' + ops[i - 1])
        i += 1
        return ops[i - 1]

    while i < len(ops):
        op = ops[i]; i += 1
        if op in FILTER_OPS and nav['view'] not in ('describe', 'map'):
            nav['view'], nav['vp'] = 'entities', None
        if op == '--text':
            cur(nav)['text'] = arg()
        elif op == '--any-literal':
            cur(nav)['scope'] = 'any'
        elif op in ('--type', '--not-type'):
            cur(nav)['conds'].append({'t': 'class', 'iri': expand(arg()), 'neg': 1 if op == '--not-type' else 0})
        elif op in ('--pv', '--not-pv', '--pv-in'):
            p, v = split_pv(arg())
            cur(nav)['conds'].append({'t': 'pv', 'p': p, 'dir': 'in' if op == '--pv-in' else 'out', 'v': v, 'neg': 1 if op == '--not-pv' else 0})
        elif op == '--pv-or':
            p, v = split_pv(arg())
            node = cur(nav)
            c = next((x for x in reversed(node['conds']) if x['t'] == 'pv' and not x.get('neg') and x['p'] == p and x['dir'] == 'out' and (x.get('v') or x.get('vs'))), None)
            if c is None:
                node['conds'].append({'t': 'pv', 'p': p, 'dir': 'out', 'v': v, 'neg': 0})
            else:
                vs = c.get('vs') or [c['v']]
                if v not in vs:
                    vs.append(v)
                c['vs'], c['v'] = vs, None
        elif op == '--map-by':
            map_opts['by'] = expand(arg())
        elif op == '--map-limit':
            n = int(arg())
            if n not in (1000, 3000, 10000):
                raise UsageError('--map-limit must be 1000, 3000 or 10000')
            map_opts['lim'] = n
        elif op == '--map-in-view':
            map_opts['view'] = True
        elif op in ('--has', '--has-in'):
            cur(nav)['conds'].append({'t': 'pv', 'p': expand(arg()), 'dir': 'in' if op == '--has-in' else 'out', 'v': None, 'neg': 0})
        elif op == '--range':
            p = expand(arg()); lo = arg(); hi = arg()
            c = {'t': 'pv', 'p': p, 'dir': 'out', 'v': None, 'neg': 0, 'lo': lo, 'hi': hi}
            if re.match(r'^\d{4}-\d{2}-\d{2}', lo or hi or ''):
                c['dt'] = NS['xsd'] + 'date'
            cur(nav)['conds'].append(c)
        elif op == '--entity':
            node = cur(nav)
            node['conds'] = [c for c in node['conds'] if not (c['t'] == 'is' and not c.get('neg'))]
            node['conds'].insert(0, {'t': 'is', 'v': {'type': 'uri', 'value': expand(arg())}})
        elif op in ('--pivot', '--pivot-in'):
            if not nav['nodes']:
                raise UsageError(op + ' needs a set to pivot from (add --text, --type or --entity first)')
            nav['nodes'] = nav['nodes'][:nav['focus'] + 1]
            nav['nodes'].append(new_node({'p': expand(arg()), 'dir': 'in' if op == '--pivot-in' else 'out'}))
            nav['focus'] = len(nav['nodes']) - 1
            nav['view'], nav['vp'] = 'entities', None
        elif op == '--focus':
            n = int(arg())
            if not 1 <= n <= len(nav['nodes']):
                raise UsageError('--focus out of range (1..%d)' % len(nav['nodes']))
            nav['focus'] = n - 1
            if nav['view'] == 'values':
                nav['vp'] = None
        elif op == '--view':
            v = arg()
            if v not in VIEWS:
                raise UsageError('--view must be one of ' + ', '.join(VIEWS))
            if v == 'describe' and not nav.get('ent'):
                raise UsageError('--view describe needs --describe IRI')
            nav['view'] = v
            if v != 'values':
                nav['vp'] = None
        elif op == '--values-of':
            spec = arg()
            d = 'out'
            if spec.endswith(':in'):
                spec, d = spec[:-3], 'in'
            cur(nav)
            nav['vp'] = {'p': expand(spec), 'dir': d}
            nav['view'] = 'values'
        elif op == '--describe':
            nav['ent'] = expand(arg()); nav['view'] = 'describe'; nav['allLangs'] = False
        else:
            raise UsageError('Unknown option: ' + op)
    nav['off'] = 0
    nav['pg'] = {'map': map_opts} if map_opts else {}
    return nav


# ---------- human summary ----------
def short(iri):
    for p, ns in NS.items():
        if iri.startswith(ns) and re.match(r'^[\w.-]+$', iri[len(ns):]):
            return p + ':' + iri[len(ns):]
    return '<' + iri + '>'


def term_text(t):
    if t is None:
        return 'any value'
    if t['type'] == 'uri':
        return short(t['value'])
    s = '"%s"' % t['value']
    if t.get('xml:lang'):
        s += '@' + t['xml:lang']
    elif t.get('datatype'):
        s += '^^' + short(t['datatype'])
    return s


def summarize(state, cfg=None, base=None):
    nav = state.get('nav') or empty_nav()
    out = []
    if base:
        out.append('App:       ' + base + ('' if base == DEFAULT_APP else '  (not the default instance)'))
    out.append('Endpoint:  ' + state.get('ep', '?'))
    if cfg and cfg.get('lang'):
        out.append('Language:  ' + cfg['lang'] + ' (from the link)')
    for i, n in enumerate(nav.get('nodes', [])):
        head = 'Set %d%s' % (i + 1, '  ← focus' if i == nav.get('focus') else '')
        bits = []
        if n.get('via'):
            v = n['via']
            bits.append(('things whose %s points at set %d' if v['dir'] == 'in' else 'values of %s from set %d') % (short(v['p']), i))
        if n.get('text'):
            bits.append('text "%s" in %s' % (n['text'], 'any literal' if n.get('scope') == 'any' else 'labels'))
        for c in n.get('conds', []):
            neg = 'NOT ' if c.get('neg') else ''
            if c['t'] == 'is':
                bits.append(neg + 'is ' + term_text(c['v']))
            elif c['t'] == 'class':
                bits.append(neg + 'a ' + short(c['iri']))
            elif c['t'] == 'pv':
                if c.get('lo') not in (None, '') or c.get('hi') not in (None, ''):
                    bits.append('%s between %s and %s' % (short(c['p']), c.get('lo') or '−∞', c.get('hi') or '+∞'))
                elif c.get('vs'):
                    bits.append(neg + '%s = %s' % (short(c['p']), ' or '.join(term_text(x) for x in c['vs'])))
                elif c['dir'] == 'in':
                    bits.append(neg + '%s %s this' % (term_text(c['v']), short(c['p'])))
                else:
                    bits.append(neg + '%s = %s' % (short(c['p']), term_text(c['v'])))
        out.append(head + ': ' + ('; '.join(bits) or 'everything'))
    view = nav.get('view', 'entities')
    if view == 'values' and nav.get('vp'):
        view = 'values of %s%s' % (short(nav['vp']['p']), ' (incoming)' if nav['vp']['dir'] == 'in' else '')
    elif view == 'values':
        view = 'distinct members with counts'
    elif view == 'describe':
        view = 'description of ' + short(nav.get('ent') or '?')
    out.append('View:      ' + view)
    return '\n'.join(out)


# ---------- check-app ----------
def check_app(url):
    """Fetch an app URL and confirm it is a SPARQL Faceted Browser that understands #s= and &cfg=."""
    import subprocess
    url = app_url(url)
    try:
        body = subprocess.run(['curl', '-sL', '--max-time', '30', url], capture_output=True, check=True).stdout.decode('utf-8', 'replace')
    except Exception as e:
        return False, 'Could not fetch %s: %s' % (url, e)
    checks = {
        'title': '<title>SPARQL Faceted Browser</title>' in body,
        'state (#s=)': 'function readHash' in body and '#s=' in body,
        'language (&cfg=)': 'function readCfg' in body,
    }
    missing = [k for k, ok in checks.items() if not ok]
    if not checks['title'] or not checks['state (#s=)']:
        return False, '%s is not a SPARQL Faceted Browser instance (missing: %s).' % (url, ', '.join(missing))
    if missing:
        return True, '%s is a SPARQL Faceted Browser, but an older build: %s not supported, so links will open in the viewer\'s own language.' % (url, ', '.join(missing))
    return True, '%s is a SPARQL Faceted Browser instance with #s= state and &cfg= language support.' % url


# ---------- CLI ----------
def take(argv, flag, default=None):
    if flag in argv:
        i = argv.index(flag)
        if i + 1 >= len(argv):
            raise UsageError('Missing value after ' + flag)
        v = argv[i + 1]
        del argv[i:i + 2]
        return v
    return default


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__); return 0
    cmd, argv = argv[0], argv[1:]
    as_json = '--json' in argv
    argv = [a for a in argv if a != '--json']
    if cmd == 'app':
        print(app_url(take(argv, '--app'))); return 0
    if cmd == 'check-app':
        ok, msg = check_app(argv[0] if argv else None)
        print(msg); return 0 if ok else 1
    if cmd == 'decode':
        if not argv:
            raise UsageError('decode needs a link')
        base, state, cfg = parse_link(argv[0])
        if as_json:
            print(json.dumps({'app': base, 'state': state, 'cfg': cfg}, indent=2, ensure_ascii=False))
        else:
            print(summarize(state or {'ep': '?', 'nav': None}, cfg, base))
        return 0
    if cmd in ('build', 'edit'):
        app = take(argv, '--app')
        lang = take(argv, '--lang')
        ep = take(argv, '--ep')
        if cmd == 'edit':
            if not argv or argv[0].startswith('--'):
                raise UsageError('edit needs the link first')
            base, state, cfg = parse_link(argv.pop(0))
            app = app or base
            lang = cfg.get('lang') if lang is None else lang
            state = state or {'ep': ep or DEFAULT_EP, 'nav': None}
            if ep:
                state['ep'] = ep
            nav = state.get('nav') or empty_nav()
        else:
            state = {'ep': ep or DEFAULT_EP}
            nav = empty_nav()
        nav = apply_ops(nav, argv)
        state['nav'] = nav
        link = make_link(state, lang or None, app)
        if as_json:
            print(json.dumps({'link': link, 'state': state, 'cfg': {'lang': lang} if lang else {}}, indent=2, ensure_ascii=False))
        else:
            print(link)
        return 0
    raise UsageError('Unknown command: ' + cmd)


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except UsageError as e:
        print('error: ' + str(e), file=sys.stderr)
        sys.exit(2)
