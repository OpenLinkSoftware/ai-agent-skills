#!/usr/bin/env python3
"""Check that the app will work when served from another Virtuoso instance, before and after deploying it there.

    vap_deploy_check.py --profile NAME --origin https://host [--app URL]

Before upload (no --app): for every service the profile uses, request it with an Origin header for the target site
and report the HTTP status and whether the response allows that origin (CORS). The app runs in the browser, so a
service that does not allow the origin will not work from that site.

After upload (--app URL): also confirm the URL serves this app with deep-link support (check-app), that the Turtle
complement is served next to it with a Turtle content type, and that the profile's app URL matches.

Exit status 0 when every required check passes.
"""
import os
import subprocess
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vap_link as L  # noqa: E402


def probe(url, origin, preflight_headers=None):
    cmd = ['curl', '-sS', '-L', '--max-time', '25', '-o', '/dev/null', '-D', '-', '-w', '\n%{http_code}', '-H', 'Origin: ' + origin]
    if preflight_headers:
        cmd += ['-X', 'OPTIONS', '-H', 'Access-Control-Request-Method: GET', '-H', 'Access-Control-Request-Headers: ' + preflight_headers]
    p = subprocess.run(cmd + [url], capture_output=True)
    out = p.stdout.decode('utf-8', 'replace')
    head, _, code = out.rpartition('\n')
    acao, ctype = None, None
    for line in head.splitlines():
        k, _, v = line.partition(':')
        if k.strip().lower() == 'access-control-allow-origin':
            acao = v.strip()
        if k.strip().lower() == 'content-type':
            ctype = v.strip()
    return (int(code) if code.isdigit() else 0), acao, ctype


def main(argv):
    argv = L.take_profile_arg(argv)
    o, _ = L.parse(argv, ('--origin', '--app'))
    if 'origin' not in o:
        print(__doc__)
        return 2
    origin = o['origin'].rstrip('/')
    pr = L.profile()
    q = lambda base: base + '?query=' + urllib.parse.quote('ASK {}', safe='')
    checks = [
        # (label, url, needs CORS from the browser, preflight headers)
        ('RDF Views SPARQL', q(pr['rdfViews']['sparql']), True, None),
        ('Linked-data / Sponger SPARQL', q(pr['linkedData']['sparql']), True, None),
        ('OPAL Agent Card', pr['opal']['agentCard'], True, None),
        ('OPAL chat API (preflight)', 'https://%s/chat/api/getTopic' % pr['opal']['host'], True, 'authorization,x-opal-version'),
        ('OPAL widget script', pr['opal']['widgetBase'] + '/opal.js', False, None),
        ('Linked-data describe', pr['linkedData']['describe'].replace('{IRI}', urllib.parse.quote('http://dbpedia.org/resource/Virtuoso_Universal_Server', safe='')), False, None),
        ('Faceted browser app', pr['facetedBrowser'], False, None),
    ]
    print('Profile %s, target origin %s' % (L.profile_name(), origin))
    ok_all = True
    for label, url, cors, pre in checks:
        code, acao, _ = probe(url, origin, pre)
        good = code == 200 and (not cors or acao in (origin, '*'))
        ok_all &= good
        print('  %-30s HTTP %-3s %-28s %s' % (label, code or '—', ('CORS ' + (acao or 'none')) if cors else '(link or script; no CORS needed)',
                                               'ok' if good else 'FAIL'))
    if 'app' in o:
        app = o['app']
        okapp, msg = L.check_app(app)
        ok_all &= okapp
        print('  %-30s %s' % ('App', msg))
        ttl = app.rsplit('/', 1)[0] + '/virtuoso-ai-value-prop.ttl'
        code, _, ctype = probe(ttl, origin)
        good = code == 200 and ctype and 'turtle' in ctype
        ok_all &= bool(good)
        print('  %-30s HTTP %-3s %s  %s' % ('Turtle complement', code or '—', ctype or '', 'ok' if good else 'FAIL'))
        if pr.get('app') and pr['app'] != app:
            print('  Note: the profile\'s app URL is %s; update it in the app\'s vap-config block (then rebuild the catalog).' % pr['app'])
        elif not pr.get('app'):
            print('  Note: profile "%s" has no app URL yet; set "app" to %s in the app\'s vap-config block, rebuild the catalog, redeploy.' % (L.profile_name(), app))
    print('All checks passed.' if ok_all else 'Some checks failed; see references/deployment.md.')
    return 0 if ok_all else 1


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except L.UsageError as e:
        print('Error: %s' % e, file=sys.stderr)
        sys.exit(2)
