# Deploying the app to another Virtuoso instance

The app is two static files that travel together: `assets/virtuoso-ai-value-prop.html` and its RDF complement
`assets/virtuoso-ai-value-prop.ttl` (the page links to the Turtle by relative URL). Serve both from the same folder on
any web server; a Virtuoso instance's WebDAV is the usual choice. URIBurner is the default deployment, not a
requirement.

## 1. Roles and profiles

The app never hard-codes a host. It reads an **instance profile** from the `vap-config` block in its `<head>`:

| Role | Profile keys | What uses it |
|---|---|---|
| RDF Views data | `rdfViews.sparql`, `rdfViews.describe` (`{IRI}`, `{GRAPH}`), `rdfViews.spasqlqb`, `rdfViews.xmla`, `rdfViews.host` | RDF Views SPARQL cards, explore query, describe links with `&graph=`, SQL/SPASQL Query Builder links |
| Linked data and Sponger | `linkedData.sparql`, `linkedData.sparqlAuth`, `linkedData.describe` (`{IRI}`) | Sponger cards, sponge-any-URL, re-sponge links, describe links for non-RDF-View entities |
| OPAL | `opal.host`, `opal.agentCard`, `opal.widgetBase`, `opal.chatUi` | agent catalog, chat panel (widget scripts; each chat agent names its own key from `apikey.js`, as on the live sites) |
| Faceted browser | `facetedBrowser` | "Browse … in the faceted browser" links |
| The app itself | `app` | links the skill prints (`null` until deployed) |

Selection: `?profile=NAME` on the page URL picks a profile for that visit; otherwise `"default"` applies. The skill's
scripts take `--profile NAME` or `VAP_PROFILE`. `python3 scripts/vap_link.py list profiles` shows them.

Shipped profiles:

- **`uriburner`** (default): data on demo.openlinksw.com; linked data, Sponger and OPAL on linkeddata.uriburner.com;
  widget scripts and key from virtuoso.openlinksw.com (`virtuosoApiKey`); app at
  `https://linkeddata.uriburner.com/DAV/demos/daas/virtuoso-ai-value-prop.html`.
- **`www`**: the app served by www.openlinksw.com. Widget scripts and key come from www (`wwwApiKey`, the key the www
  site itself uses with the OPAL host) and describe links for non-RDF-View entities use www's `/describe`. The
  Sponger, sponging, the Agent Card, sign-in and OPAL stay on URIBurner, because on 2026-10-18 www held none of the
  Sponger graphs, and had no `/sparql-auth/`, no Agent Card and no OpenID Connect discovery document. `app` is `null`
  until a location on www is chosen.

## 2. Worked case: www.openlinksw.com

### 2a. Pre-deployment test (runs now, no upload)

```bash
python3 scripts/vap_deploy_check.py --profile www --origin https://www.openlinksw.com
```

Result on 2026-10-18: all nine checks passed. RDF Views SPARQL, Sponger SPARQL, the Agent Card and the OPAL chat API
all answer requests from `https://www.openlinksw.com` with that origin allowed; the widget script, describe page and faceted browser all answer 200. The app was also exercised in a browser with
`?profile=www` (served locally): widget scripts and `wwwApiKey` loaded from www, Sponger rows came from URIBurner,
describe links went to www, and a guest question to the Data Twingler agent was answered.

### 2b. Choose the location

www is managed by the OSDI Inclusion Engine, which renders site pages through skins. The app is a complete page with
its own styling, so serve it as a **plain file** from a WebDAV collection that www serves as-is, not as an OSDI page
(a skin would wrap it in a second header). The site owner picks the collection; nothing in this skill assumes a path.
Check that a test file put there comes back unchanged and with the right content type before uploading the app.

### 2c. Set the profile's app URL

In `assets/virtuoso-ai-value-prop.html`, set `"app"` in the `www` profile to the final URL. Optionally make `www` the
`"default"` in that copy, so visitors need no `?profile=www`. Then regenerate:

```bash
node scripts/build_catalog.mjs
python3 scripts/build_ttl.py
python3 scripts/vap_link.py check-catalog
```

### 2d. Upload both files

Every PUT needs an explicit `Content-Type` (curl's `--data-binary` otherwise sends `application/x-www-form-urlencoded`),
and every upload is checked with HEAD afterwards:

```bash
curl -sS -X PUT -H 'Content-Type: text/html; charset=utf-8' --data-binary @assets/virtuoso-ai-value-prop.html "<collection-url>/virtuoso-ai-value-prop.html" <credentials>
curl -sS -X PUT -H 'Content-Type: text/turtle; charset=utf-8' --data-binary @assets/virtuoso-ai-value-prop.ttl "<collection-url>/virtuoso-ai-value-prop.ttl" <credentials>
curl -sSI "<collection-url>/virtuoso-ai-value-prop.html"
curl -sSI "<collection-url>/virtuoso-ai-value-prop.ttl"
```

Use the credential method the target requires (WebID-TLS client certificate, Digest, or OAuth); never embed a password
in a URL or a file.

### 2e. Post-deployment test

```bash
python3 scripts/vap_deploy_check.py --profile www --origin https://www.openlinksw.com --app "<app-url>"
```

This repeats the service checks and adds: the URL serves this app with deep-link support, the Turtle is served next
to it with a Turtle content type, and the profile's `app` matches. Then open a few deep links in a browser
(`vap_link.py --profile www build --ex nw-sparql-stock --run`, `--ds csv`, `--agent virtuoso-support --ask "…"`) and send
one chat question to confirm the widget key works from the www origin.

## 3. Any other instance

1. Copy a profile in `vap-config`, give it a name, and point each role at the host that serves it. Keep a role on an
   existing host when the new host lacks the service (for example the Sponger graphs, `/sparql-auth/`, or an Agent
   Card); the deploy check shows which ones answer.
2. The RDF Views datasets are bound to their named graphs on demo.openlinksw.com. Pointing `rdfViews` at another host
   only makes sense if that host has the same RDF Views (same graph IRIs); otherwise keep demo.openlinksw.com.
3. Run `vap_deploy_check.py --profile NAME --origin https://new-host`; fix any FAIL by keeping that role elsewhere
   or enabling the service (CORS on SPARQL and the chat API is required, because the page calls them from the browser).
4. Set `app`, regenerate the catalog and Turtle, upload both files with explicit content types, run the deploy check
   with `--app`, and add the profile to the skill's own copy so its links can use it.

## 4. Things that commonly go wrong

| Symptom | Cause | Fix |
|---|---|---|
| Every SPARQL card says "Could not reach …" | the endpoint is down (a 502 page carries no CORS header) or does not allow the site's origin | check the endpoint; run the deploy check |
| Chat says the widget scripts did not load | `opal.widgetBase` wrong, or the site's `apikey.js` does not define the agent's key (`virtuosoApiKey`, `udaApiKey`) | open `{widgetBase}/apikey.js` and use the constant it declares |
| Page shows two headers | the file was deployed as an OSDI page and wrapped by a skin | serve it as a plain file |
| `.ttl` downloads as `application/octet-stream` or the page is served as text | PUT without `Content-Type` | re-PUT with the explicit type and check with HEAD |
| Sign-in returns to the wrong page | the page URL changed after login started | sign in from the final URL; `redirectUrl` is the page URL without the hash |
