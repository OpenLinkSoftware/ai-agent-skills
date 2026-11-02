#!/usr/bin/env python3
"""Build, decode and check links for the Virtuoso AI value-proposition app, and the other links its answers use.

The app keeps its view in the URL hash:
    {app}#/                                     home
    {app}#{section-id}                          any section, on any page (for example #how-it-works)
    {app}#/rdf-views?src=ID&lang=L&ex=ID&run=1  RDF Views: dataset tab, language filter, focus (and run) an example
    {app}#/ontologies?ex=ID&run=1               Ontologies: generated ontologies and their reuse with shared ones
    {app}#/sponger?ex=ID&run=1 | ?url=URL       Sponger: focus (and run) an example, or sponge a URL
    {app}#/explore?ds=ID                        Faceted Browse: run the explore query on one dataset
    {app}#/agents?agent=KEY&ask=TEXT&send=1     OPAL chat on an agent, with a question filled in (and sent)
    {app}#/sources                              where every example comes from

This script is the only sanctioned way for the skill to produce such links: never hand-write one.

Instance profile (which hosts serve each role; profiles live in the app's vap-config block and the catalog):
    --profile NAME on the command line, else VAP_PROFILE, else the catalog default (uriburner).
    `list profiles` shows them; `profile` prints the active one.

App instance resolution (first match wins):
    1. --app URL on the command line
    2. VAP_APP_URL environment variable
    3. the active profile's "app" URL (an error if the profile has none yet, for example before a deployment)

Subcommands
    build    [--app URL] [--view V] [--section ID] [--src ID] [--lang L] [--ex ID] [--run] [--ds ID] [--url URL]
             [--agent KEY] [--ask TEXT] [--send]
    decode   LINK
    describe IRI [--graph G]           entity description link (demo.openlinksw.com IRIs get uri= and graph=)
    qb       (--ex ID | --sql SQL)     SPASQL Query Builder link, demo account preset (sign-in still required)
    endpoint (--ex ID | --explore DS | --sparql Q --ep demo|ub)   SPARQL endpoint link (HTML table or Turtle)
    list     [datasets|examples|sponger|explore|agents|prompts|sections|profiles]
    profile                            print the active profile as JSON
    check-app [URL]                    confirm a URL serves this app with deep-link support
    check-catalog                      confirm references/catalog.json matches the app in assets/
    app                                print the app URL that would be used
"""
import json
import os
import re
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CATALOG_PATH = os.path.join(ROOT, 'references', 'catalog.json')
ASSET_PATH = os.path.join(ROOT, 'assets', 'virtuoso-ai-value-prop.html')
LANGS = ('all', 'sql', 'spasql', 'sparql')


class UsageError(Exception):
    pass


_CAT = None
PROFILE_NAME = None  # set by take_profile_arg() or VAP_PROFILE


def load_catalog():
    global _CAT
    if _CAT is None:
        with open(CATALOG_PATH, encoding='utf-8') as f:
            _CAT = json.load(f)
    return _CAT


def take_profile_arg(argv):
    """Remove --profile NAME from argv (anywhere) and remember it."""
    global PROFILE_NAME
    out, i = [], 0
    while i < len(argv):
        if argv[i] == '--profile':
            if i + 1 >= len(argv):
                raise UsageError('--profile needs a name')
            PROFILE_NAME = argv[i + 1]
            i += 2
        else:
            out.append(argv[i])
            i += 1
    return out


def profile_name():
    cfg = load_catalog()['config']
    name = PROFILE_NAME or os.environ.get('VAP_PROFILE') or cfg['default']
    if name not in cfg['profiles']:
        raise UsageError('Unknown profile: %s (known: %s)' % (name, ', '.join(cfg['profiles'])))
    return name


def profile():
    return load_catalog()['config']['profiles'][profile_name()]


def endpoints():
    p = profile()
    return {'demo': p['rdfViews']['sparql'], 'ub': p['linkedData']['sparql'], 'ubAuth': p['linkedData']['sparqlAuth']}


def app_url(explicit=None):
    url = explicit or os.environ.get('VAP_APP_URL') or profile().get('app')
    if not url:
        raise UsageError('Profile "%s" has no app URL yet (the app has not been deployed there). Pass --app URL or set '
                         'VAP_APP_URL; see references/deployment.md.' % profile_name())
    return url


def fct_href(href):
    """Faceted-browser links in the catalog use the default profile's browser; follow the active profile's."""
    cat = load_catalog()
    return href.replace(cat['facetedBrowserDefaultApp'], profile()['facetedBrowser']) if href else href


# ---------- lookups ----------
def find_example(cat, ex_id):
    for e in cat['examples']:
        if e['id'] == ex_id:
            return e.get('view', 'rdf-views'), e
    for e in cat['sponger']:
        if e['id'] == ex_id:
            return 'sponger', e
    raise UsageError('Unknown example id: %s (see: vap_link.py list examples / list sponger)' % ex_id)


def find_dataset(cat, ds_id, explore=False):
    pool = cat['exploreDatasets'] if explore else cat['datasets']
    for d in pool:
        if d['id'] == ds_id:
            return d
    raise UsageError('Unknown dataset id: %s (known: %s)' % (ds_id, ', '.join(d['id'] for d in pool)))


def find_agent(cat, key):
    for a in cat['agents']:
        if key in (a['key'], a['module']):
            return a
    raise UsageError('Unknown agent: %s (known: %s)' % (key, ', '.join(a['key'] for a in cat['agents'])))


def query_graph(q):
    """The single named graph a query is scoped to; None when it names none or several."""
    gs = list(dict.fromkeys(re.findall(r'\b(?:FROM|GRAPH)\s*<([^>]+)>', q, re.I)))
    return gs[0] if len(gs) == 1 else None


# ---------- link builders ----------
def build_link(cat, app=None, view=None, section=None, src=None, lang=None, ex=None, run=False, ds=None, url=None,
               agent=None, ask=None, send=False):
    base = app_url(app)
    if section:
        if not any(s['id'] == section for s in cat['sections']):
            raise UsageError('Unknown section id: %s (see: vap_link.py list sections)' % section)
        if any([view, src, lang, ex, ds, url, agent, ask]):
            raise UsageError('--section cannot be combined with view options')
        return base + '#' + section
    params = []
    if ex:
        v, _ = find_example(cat, ex)
        if view and view != v:
            raise UsageError('Example %s belongs to the %s view, not %s' % (ex, v, view))
        view = v
    if ds:
        find_dataset(cat, ds, explore=True)
        view = view or 'explore'
    if url:
        if not re.match(r'^https?://', url):
            raise UsageError('--url must be an http(s) URL')
        view = view or 'sponger'
    if agent or ask:
        view = view or 'agents'
    if src or lang:
        view = view or 'rdf-views'
    view = view or 'home'
    if view not in cat['views']:
        raise UsageError('Unknown view: %s (known: %s)' % (view, ', '.join(cat['views'])))
    if view == 'rdf-views':
        if src:
            find_dataset(cat, src)
            params.append(('src', src))
        if lang:
            if lang not in LANGS:
                raise UsageError('--lang must be one of: ' + ', '.join(LANGS))
            params.append(('lang', lang))
    if ex:
        params.append(('ex', ex))
        if run:
            _, e = find_example(cat, ex)
            if e.get('lang') in ('sql', 'spasql'):
                raise UsageError('%s is a %s example: it runs in the SPASQL Query Builder after sign-in, so --run does not apply (use: vap_link.py qb --ex %s)' % (ex, e['lang'].upper(), ex))
            params.append(('run', '1'))
    elif run:
        raise UsageError('--run needs --ex')
    if view == 'explore' and ds:
        params.append(('ds', ds))
    if view == 'sponger' and url:
        params.append(('url', url))
    if view == 'agents':
        if agent:
            params.append(('agent', find_agent(cat, agent)['key']))
        if ask:
            params.append(('ask', ask))
            if send:
                params.append(('send', '1'))
    elif send:
        raise UsageError('--send needs --ask')
    if view == 'home' and not params:
        return base + '#/'
    q = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return base + '#/' + (view if view != 'home' else '') + ('?' + q if q else '')


def decode_link(cat, link):
    if '#' not in link:
        return {'app': link, 'view': 'home'}
    app, frag = link.split('#', 1)
    frag = urllib.parse.unquote(frag) if not frag.startswith('/') else frag
    if not frag.startswith('/'):
        sec = next((s for s in cat['sections'] if s['id'] == frag), None)
        return {'app': app, 'section': frag, 'view': sec['view'] if sec else None, 'title': sec['title'] if sec else None}
    path, _, qs = frag[1:].partition('?')
    out = {'app': app, 'view': path or 'home'}
    for k, v in urllib.parse.parse_qsl(qs, keep_blank_values=True):
        out[k] = v
    if 'ex' in out:
        try:
            _, e = find_example(cat, out['ex'])
            out['example'] = e['title']
        except UsageError:
            out['example'] = '(unknown id)'
    return out


def fill(pattern, iri, graph=None):
    q = lambda s: urllib.parse.quote(s, safe='')
    out = pattern.replace('{IRI}', q(iri))
    if '&graph={GRAPH}' in out and not graph:
        return out.replace('&graph={GRAPH}', '')
    return out.replace('{GRAPH}', q(graph) if graph else '')


def describe_link(iri, graph=None):
    p = profile()
    if '//%s/' % p['rdfViews']['host'] in iri:
        return fill(p['rdfViews']['describe'], iri, graph)
    return fill(p['linkedData']['describe'], iri)


def qb_link(cat, sql):
    p = dict(cat['spasqlQueryBuilder']['permalink'])
    p['exec'] = {'sql': sql}
    return profile()['rdfViews']['spasqlqb'] + urllib.parse.quote(json.dumps(p, separators=(',', ':')), safe='')


def endpoint_link(cat, ep, q):
    url = endpoints()[ep]
    graph_form = re.match(r'^\s*(?:(?:PREFIX|DEFINE)[^\n]*\n\s*)*(DESCRIBE|CONSTRUCT)\b', q, re.I)
    fmt = 'text/x-html-nice-turtle' if graph_form else 'text/x-html+tr'
    return url + '?query=' + urllib.parse.quote(q, safe='') + '&format=' + urllib.parse.quote(fmt, safe='')


def explore_query(cat, graph, no_label=False):
    t = cat.get('exploreQueryTemplateNoLabel') if no_label else None
    return (t or cat['exploreQueryTemplate']).replace('{GRAPH}', graph)


# ---------- checks ----------
def check_app(url):
    try:
        out = subprocess.run(['curl', '-sL', '--max-time', '30', '-w', '\n%{http_code}', url], capture_output=True, check=True).stdout.decode('utf-8', 'replace')
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        return False, '%s could not be fetched (%s).' % (url, e)
    body, _, code = out.rpartition('\n')
    if code != '200':
        return False, '%s answered HTTP %s. If this is the default instance, the app has not been uploaded there yet; use --app with a URL that serves assets/virtuoso-ai-value-prop.html.' % (url, code)
    if 'name="generator" content="virtuoso-ai-value-prop"' not in body:
        return False, '%s is not the Virtuoso AI value-proposition app (no generator marker).' % url
    if 'function findExample' not in body:
        return False, '%s is an older build of the app without deep links (#/…?ex=, ds=, agent=).' % url
    return True, '%s is the Virtuoso AI value-proposition app, with deep-link support.' % url


def check_catalog(cat):
    with open(ASSET_PATH, encoding='utf-8') as f:
        html = f.read()
    problems = []
    for e in cat['examples'] + cat['sponger']:
        if "id:'%s'" % e['id'] not in html:
            problems.append('example %s is in the catalog but not in the app' % e['id'])
    app_ids = set(re.findall(r"\{id:'([a-z0-9-]+)', (?:lang|title|url):", html))
    cat_ids = {e['id'] for e in cat['examples'] + cat['sponger']}
    for i in sorted(app_ids - cat_ids):
        problems.append('example %s is in the app but not in the catalog' % i)
    for s in cat['sections']:
        if 'id="%s"' % s['id'] not in html:
            problems.append('section %s is in the catalog but not in the app' % s['id'])
    return problems


# ---------- CLI ----------
def parse(argv, flags, switches=()):
    opts, rest, i = {}, [], 0
    while i < len(argv):
        a = argv[i]
        if a in switches:
            opts[a.lstrip('-')] = True
            i += 1
        elif a in flags:
            if i + 1 >= len(argv):
                raise UsageError('%s needs a value' % a)
            opts[a.lstrip('-')] = argv[i + 1]
            i += 2
        elif a.startswith('--'):
            raise UsageError('Unknown option: %s' % a)
        else:
            rest.append(a)
            i += 1
    return opts, rest


def main(argv):
    if not argv or argv[0] in ('-h', '--help', 'help'):
        print(__doc__)
        return 0
    argv = take_profile_arg(argv)
    cmd, args = argv[0], argv[1:]
    cat = load_catalog()
    if cmd == 'build':
        o, _ = parse(args, ('--app', '--view', '--section', '--src', '--lang', '--ex', '--ds', '--url', '--agent', '--ask'),
                     ('--run', '--send'))
        print(build_link(cat, app=o.get('app'), view=o.get('view'), section=o.get('section'), src=o.get('src'),
                         lang=o.get('lang'), ex=o.get('ex'), run=o.get('run', False), ds=o.get('ds'), url=o.get('url'),
                         agent=o.get('agent'), ask=o.get('ask'), send=o.get('send', False)))
    elif cmd == 'decode':
        o, rest = parse(args, ())
        if not rest:
            raise UsageError('decode needs a link')
        print(json.dumps(decode_link(cat, rest[0]), indent=2, ensure_ascii=False))
    elif cmd == 'describe':
        o, rest = parse(args, ('--graph',))
        if not rest:
            raise UsageError('describe needs an IRI')
        print(describe_link(rest[0], o.get('graph')))
    elif cmd == 'qb':
        o, _ = parse(args, ('--ex', '--sql'))
        if 'ex' in o:
            _, e = find_example(cat, o['ex'])
            if e.get('lang') not in ('sql', 'spasql'):
                raise UsageError('%s is a %s example; qb is for SQL and SPASQL' % (o['ex'], e.get('lang', 'Sponger')))
            print(e.get('verbatimUrl') if e.get('abridged') and e.get('verbatimUrl') else qb_link(cat, e['query']))
        elif 'sql' in o:
            print(qb_link(cat, o['sql']))
        else:
            raise UsageError('qb needs --ex ID or --sql SQL')
    elif cmd == 'endpoint':
        o, _ = parse(args, ('--ex', '--explore', '--sparql', '--ep'))
        if 'ex' in o:
            v, e = find_example(cat, o['ex'])
            if v in ('rdf-views', 'ontologies') and e['lang'] != 'sparql':
                raise UsageError('%s is a %s example; use qb for it' % (o['ex'], e['lang']))
            print(endpoint_link(cat, e['ep'], e['query']))
        elif 'explore' in o:
            d = find_dataset(cat, o['explore'], explore=True)
            print(endpoint_link(cat, d['ep'], explore_query(cat, d['graph'], d.get('noLabel'))))
        elif 'sparql' in o:
            print(endpoint_link(cat, o.get('ep', 'demo'), o['sparql']))
        else:
            raise UsageError('endpoint needs --ex, --explore or --sparql')
    elif cmd == 'list':
        what = args[0] if args else 'examples'
        if what == 'examples':
            for e in cat['examples']:
                print('%-28s %-9s %-7s %s' % (e['id'], e['dataset'], e['lang'], e['title']))
        elif what == 'sponger':
            for e in cat['sponger']:
                print('%-28s %s  (%s)' % (e['id'], e['title'], e['source']))
        elif what == 'datasets':
            for d in cat['datasets']:
                print('%-10s %-26s %s%s' % (d['id'], d['label'], d['meta'].get('Graph') or d['meta'].get('Graphs', ''),
                                            '  [status: see datasets.md]' if d.get('status') else ''))
        elif what == 'explore':
            for d in cat['exploreDatasets']:
                print('%-10s %-4s %s' % (d['id'], d['ep'], d['graph']))
        elif what == 'agents':
            for a in cat['agents']:
                print('%-17s %s  (module %s)' % (a['key'], a['label'], a['module']))
        elif what == 'prompts':
            for p in cat['prompts']:
                print('%-17s %s' % (p['agent'], p['text']))
        elif what == 'profiles':
            cfg = cat['config']
            for n, pr in cfg['profiles'].items():
                print('%-10s %-26s app=%s%s' % (n, pr['label'], pr.get('app') or '(not deployed yet)',
                                               '  [default]' if n == cfg['default'] else ''))
        elif what == 'sections':
            for s in cat['sections']:
                print('%-22s %-10s %s' % (s['id'], s['view'], s['title']))
        else:
            raise UsageError('list what? datasets|examples|sponger|explore|agents|prompts|sections')
    elif cmd == 'check-app':
        ok, msg = check_app(args[0] if args else app_url())
        print(msg)
        return 0 if ok else 1
    elif cmd == 'check-catalog':
        problems = check_catalog(cat)
        if problems:
            print('\n'.join(problems))
            print('Run: node scripts/build_catalog.mjs')
            return 1
        print('Catalog matches the app: %d examples, %d Sponger examples, %d sections.' % (
            len(cat['examples']), len(cat['sponger']), len(cat['sections'])))
    elif cmd == 'app':
        print(app_url())
    elif cmd == 'profile':
        print(json.dumps(dict(profile(), name=profile_name()), indent=2))
    else:
        raise UsageError('Unknown subcommand: %s' % cmd)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except UsageError as e:
        print('Error: %s' % e, file=sys.stderr)
        sys.exit(2)
