#!/usr/bin/env python3
"""Run the app's showcase queries live and print the answer for chat, plus the links that go with it.

    vap_query.py --ex ID [--limit N] [--format md|json]
        SPARQL example (RDF Views or Sponger): runs it and prints the rows. Entity IRIs become describe links
        (demo.openlinksw.com IRIs carry &graph= with the query's named graph). Then: the app link that opens the
        same example and runs it, and the SPARQL endpoint link.
        SQL / SPASQL example: does not run it (it needs a signed-in session); prints the query, the SPASQL Query
        Builder link with the demo account preset, the sign-in notice, and the app link.
    vap_query.py --explore DS [--limit N] [--format md|json]
        The standard explore query (types, sample entity, sample label, count) scoped to one dataset's named graph.
    vap_query.py --sponge URL [--format md|json]
        The type profile of the graph the Sponger built from URL, read from URIBurner's cache, plus the
        describe link and the authenticated re-sponge link (DEFINE get:soft "replace").
    vap_query.py --sparql QUERY [--ep demo|ub] [--graph G] [--limit N] [--format md|json]
        Any SELECT on demo.openlinksw.com (default) or URIBurner.

Options: --profile NAME (or VAP_PROFILE) picks the instance profile (hosts for each role; default uriburner);
--app URL (or VAP_APP_URL) picks the app instance for the printed app link.
Requires Python 3.8+ and curl. A transient Virtuoso deadlock (SR172) is retried once.
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vap_link as L  # noqa: E402

SIGNIN = ('Sign in first: the Query Builder opens a sign-in page. Under "Using SQL login" use user name **demo** and '
          'password **demo** (or vdb / vdb). The link already presets the demo account for the query itself. The '
          'instance is protected by ABAC ACLs.')


def http_sparql(endpoint, query, wait=60):
    """GET a SPARQL query as JSON. curl handles the endpoints' certificates the way a browser would."""
    url = endpoint + '?query=' + urllib.parse.quote(query, safe='')
    for attempt in (1, 2):
        t0 = time.time()
        p = subprocess.run(['curl', '-sS', '-L', '--max-time', str(wait), '-H', 'Accept: application/sparql-results+json',
                            '-w', '\n%{http_code}', url], capture_output=True)
        out = p.stdout.decode('utf-8', 'replace')
        body, _, code = out.rpartition('\n')
        ms = int((time.time() - t0) * 1000)
        if p.returncode != 0:
            return {'ok': False, 'status': 0, 'error': p.stderr.decode('utf-8', 'replace').strip() or 'curl failed', 'ms': ms}
        status = int(code) if code.isdigit() else 0
        if status >= 400 and 'SR172' in body and attempt == 1:
            time.sleep(1.5)
            continue
        if status == 401:
            return {'ok': False, 'status': 401, 'error': "Authentication required: the endpoint's ABAC ACLs do not allow "
                                                          'anonymous access to this data.', 'ms': ms}
        if status >= 400:
            text = re.sub(r'<[^>]+>', ' ', body) if body.lstrip().startswith('<') else body
            return {'ok': False, 'status': status, 'error': re.sub(r'\s+', ' ', text).strip()[:600], 'ms': ms}
        try:
            j = json.loads(body)
        except ValueError:
            return {'ok': False, 'status': status, 'error': 'The response was not SPARQL JSON: ' + body[:300], 'ms': ms}
        return {'ok': True, 'vars': j.get('head', {}).get('vars', []), 'rows': j.get('results', {}).get('bindings', []), 'ms': ms}
    return {'ok': False, 'status': 0, 'error': 'unreachable', 'ms': 0}


def short(iri):
    s = re.sub(r'^https?://', '', iri)
    return s if len(s) <= 70 else '…' + s[-64:]


def cell(b, graph):
    if not b:
        return ''
    v = b.get('value', '')
    if b.get('type') == 'uri':
        return '[%s](%s)' % (short(v).replace('|', '\\|'), L.describe_link(v, graph))
    dt = b.get('datatype', '')
    if re.search(r'#(decimal|double|float)$', dt):
        try:
            v = ('{:,.2f}'.format(float(v))).rstrip('0').rstrip('.')
        except ValueError:
            pass
    elif dt.endswith('#integer'):
        try:
            v = '{:,}'.format(int(v))
        except ValueError:
            pass
    return v.replace('|', '\\|').replace('\n', ' ')


def table(res, graph, limit):
    rows = res['rows'][:limit] if limit else res['rows']
    out = ['| ' + ' | '.join(res['vars']) + ' |', '|' + '---|' * len(res['vars'])]
    for r in rows:
        out.append('| ' + ' | '.join(cell(r.get(v), graph) for v in res['vars']) + ' |')
    more = len(res['rows']) - len(rows)
    if more > 0:
        out.append('\n…and %s more row%s.' % ('{:,}'.format(more), 's' if more > 1 else ''))
    return '\n'.join(out)


def emit(fmt, title, res, graph, links, limit, query=None, notice=None):
    if res and res.get('ok'):
        # drop rows with no bound value at all (an aggregate over a NULL group yields one)
        res = dict(res, rows=[r for r in res['rows'] if any(r.get(v, {}).get('value') for v in res['vars'])])
    if fmt == 'json':
        print(json.dumps({'title': title, 'graph': graph, 'query': query, 'result': res, 'links': links,
                          'notice': notice}, indent=2, ensure_ascii=False))
        return
    print('**%s**' % title)
    if graph:
        print('Named graph: `%s`' % graph)
    print()
    if res is None:
        print('```sql\n%s\n```' % query)
    elif res['ok']:
        n = len(res['rows'])
        print('%s row%s · %s ms\n' % ('{:,}'.format(n), '' if n == 1 else 's', '{:,}'.format(res['ms'])))
        print(table(res, graph, limit) if n else '(no rows)')
    else:
        print('Live query failed (HTTP %s, %s ms): %s' % (res['status'] or '—', res['ms'], res['error']))
    if notice:
        print('\n' + notice)
    print()
    for label, url in links:
        print('%s: %s' % (label, url))


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    argv = L.take_profile_arg(argv)
    o, rest = L.parse(argv, ('--ex', '--explore', '--sponge', '--sparql', '--ep', '--graph', '--limit', '--format', '--app'))
    cat = L.load_catalog()
    fmt = o.get('format', 'md')
    limit = int(o.get('limit', 25))
    app = o.get('app')
    if 'ex' in o:
        view, e = L.find_example(cat, o['ex'])
        if view == 'rdf-views' and e['lang'] in ('sql', 'spasql'):
            links = [('Open in SPASQL Query Builder', e['verbatimUrl'] if e.get('abridged') and e.get('verbatimUrl') else L.qb_link(cat, e['query'])),
                     ('Open this example in the app', L.build_link(cat, app=app, ex=e['id']))]
            if e.get('postUrl'):
                links.append(('Original link from the post', e['postUrl']))
            emit(fmt, e['title'], None, L.query_graph(e['query']), links, limit, query=e['query'], notice=SIGNIN)
            return 0
        ep = e['ep']
        graph = L.query_graph(e['query']) or (e.get('source') if view == 'sponger' else None)
        res = http_sparql(L.endpoints()[ep], e['query'])
        links = [('Open this example in the app', L.build_link(cat, app=app, ex=e['id'], run=True)),
                 ('Open in the SPARQL endpoint', L.endpoint_link(cat, ep, e['query']))]
        if view == 'sponger':
            links.append(('Re-sponge the source (sign-in)', L.endpoint_link(cat, 'ubAuth', e['respongeQuery'])))
            links.append(('Describe the source', L.describe_link(e['source'])))
        if e.get('facetedBrowser'):
            links.append((e['facetedBrowser']['label'], L.fct_href(e['facetedBrowser']['href'])))
        emit(fmt, e['title'], res, graph, links, limit, query=e['query'])
    elif 'explore' in o:
        d = L.find_dataset(cat, o['explore'], explore=True)
        q = L.explore_query(cat, d['graph'], d.get('noLabel'))
        res = http_sparql(L.endpoints()[d['ep']], q)
        links = [('Open this dataset in the app', L.build_link(cat, app=app, ds=d['id'])),
                 ('Open in the SPARQL endpoint', L.endpoint_link(cat, d['ep'], q))]
        if res['ok']:
            for r in res['rows'][:8]:
                t = r.get('type', {}).get('value')
                dflt = cat['config']['profiles'][cat['config']['default']]
                key_ep = dflt['rdfViews']['sparql'] if d['ep'] == 'demo' else dflt['linkedData']['sparql']
                href = L.fct_href(cat['facetedTypeLinks'].get(key_ep + ' ' + t)) if t else None
                if href:
                    links.append(('Browse %s in the faceted browser' % re.split(r'[#/]', t)[-1], href))
        emit(fmt, 'Explore: ' + d['label'], res, d['graph'], links, limit, query=q,
             notice=('Note: ' + d['note']) if d.get('note') else None)
    elif 'sponge' in o:
        u = o['sponge']
        if not re.match(r'^https?://', u):
            raise L.UsageError('--sponge needs an http(s) URL')
        iri = re.sub(r'[<>"{}|\\^`\s]', lambda m: urllib.parse.quote(m.group(0)), u)
        q = L.explore_query(cat, iri)
        res = http_sparql(L.endpoints()['ub'], q)
        if res['ok'] and not res['rows']:
            res = dict(res, ok=False, status=200, error='URIBurner holds no graph for this URL yet; use the re-sponge link (sign-in) to fetch it.')
        links = [('Open in the app (Sponger)', L.build_link(cat, app=app, url=u)),
                 ('Describe the source', L.describe_link(u)),
                 ('Sponge it now (sign-in)', L.endpoint_link(cat, 'ubAuth', 'DEFINE get:soft "replace"\n' + q))]
        emit(fmt, 'Sponger graph: ' + u, res, u, links, limit, query=q)
    elif 'sparql' in o:
        ep = o.get('ep', 'demo')
        if ep not in ('demo', 'ub'):
            raise L.UsageError('--ep must be demo or ub')
        q = o['sparql']
        res = http_sparql(L.endpoints()[ep], q)
        emit(fmt, 'SPARQL on ' + L.endpoints()[ep], res, o.get('graph') or L.query_graph(q),
             [('Open in the SPARQL endpoint', L.endpoint_link(cat, ep, q))], limit, query=q)
    else:
        raise L.UsageError('Give --ex, --explore, --sponge or --sparql (see --help)')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except L.UsageError as e:
        print('Error: %s' % e, file=sys.stderr)
        sys.exit(2)
