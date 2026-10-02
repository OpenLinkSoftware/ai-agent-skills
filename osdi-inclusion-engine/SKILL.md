---
name: osdi-inclusion-engine
description: Operate the OpenLink OSDI Inclusion Engine — the Virtuoso index.vsp + skin system that renders openlinksw.com sub-sites (www, virtuoso, uda, ps, ode, shop) from WebDAV content. Use for site registration, config-graph inspection and edits, skin selection or per-URL skin overrides, composite-skin authoring and deployment (manifest + XHTML templates + SPARQL bindings), region suppression, homepage or page replacement deployment from DAV-hosted mockups, double-chrome conflict detection, cache flushing, and post-deploy verification. Trigger on phrases like "integrate this homepage replacement", "swap the skin for", "register a new OSDI site", "Inclusion Engine config", "build a composite skin", "flush the incleng cache", or any request to deploy content into an OSDI-based website.
---

# OSDI Inclusion Engine

Use this skill to inspect, configure, and deploy content into websites run by the OpenLink Inclusion Engine (OSDI): a Virtuoso-hosted system where a single `index.vsp` per site resolves `/{page}` requests to `content/{page}.html` in WebDAV, passes the document through HTML Tidy (unless its DOCTYPE is XHTML+RDFa), wraps it with a skin, merges RDF data-islands, caches the rendered result in `incleng..cache`, and serves it.

All configuration lives in the RDF quadstore graph `<urn:com.openlinksw.virtuoso.incleng>`, accessed via the `incleng..config_*` SQL API — **never** the legacy `incleng..sites` table. Read `references/config-api.md` before issuing any config SQL.

<<<<<<< HEAD
## Two Kinds of Skin

Which kind is in play determines almost everything else, so establish it first.

**Legacy skins** (`openlink`, `responsive`, `matrix`, `bootstrap-2022`, `docs-v3`, …) are single hand-written `PostProcess.xslt` files with the site's navigation markup, asset paths and layout fused inside them. They **unconditionally inject** masthead and footer around whatever is in the source document's `<body>`. They are selected by the `xslt_sheet` config parameter.

**Composite skins** are manifest-declared bundles — a `skin.ttl` naming a theme, a set of plain-XHTML templates carrying `data-osdi-*` binding attributes, and SPARQL bindings resolved against a named graph at render time. Navigation is data, the stylesheet is a manifest string, and chrome is a set of independently suppressible regions. They are selected by the `skin_manifest` config parameter, which overrides `xslt_sheet`. See `references/composite-skins.md`.

**Check the target engine before promising a composite deployment.** `skin_manifest` is only read by an engine whose `transform` carries the composite block; on a stock instance it is an unread config value. Confirm with `select count(*) from DB.DBA.SYS_PROCEDURES where P_NAME like '%osdi_skin%'` before planning. If it returns 0, either install the engine code — which redefines `incleng..transform` for **every** site on that instance, so treat it as a change needing explicit approval and a before/after regression on the other sites — or use the `composite-doc` front end, which needs no stored procedure and is selected with `xslt_sheet`. See the deployment section in `references/composite-skins.md`.

Read the live config for the target URL before reasoning about either — never assume.

## Blocking Gate — Chrome Conflict Check Before Any Page Deployment

Every **legacy** chrome-bearing skin injects the corporate masthead and footer unconditionally. If a replacement page carries its own `<nav>`, `<header>`, or `<footer>`, deploying it under such a skin stacks two sets of chrome — and when the replacement's CSS deliberately mirrors the live site's design, the duplication is visually subtle and easy to miss in review.
=======
## Blocking Gate — This Is a Skin-Authoring Decision, Not a Deploy-Path Choice

Every chrome-bearing skin — legacy `openlink`/`responsive` in the inclusion-engine VAD, and modern `matrix`/`bootstrap-2022` in the **opl-skins VAD** — **unconditionally injects** the corporate masthead and footer around whatever is in the source document's `<body>`. A page carrying its own `<nav>`/`<header>`/`<footer>` deployed under one of these skins stacks two sets of chrome.
>>>>>>> origin/main

The **passthrough override** (per-URL `xslt_sheet` → `/DAV/VAD/inclusion-engine/skin/passthrough/xslt/PostProcess.xslt`) avoids the stack, but its cost is too great to be a default: it freezes one page as a permanent one-off outside the skin system, forfeiting engine-supplied feeds links, canonical, JSON-LD SearchAction, analytics, OPAL widget, and site-wide nav consistency — forever, since nothing about the override is a stepping stone to anything better. Only use it as an explicit, time-boxed stopgap the user has chosen with that cost stated.

<<<<<<< HEAD
1. Read the **live** skin for the target URL (`config_get` for `skin_manifest`, then `xslt_sheet`) to learn what is actually active.
2. Fetch the replacement document and run `scripts/check_chrome_conflict.py <file-or-url>`. It reports which chrome the page carries and recommends a path; it is a **recommender, not a blocker** — the choice below is the user's.
3. If it reports self-contained chrome, elicit which remediation the user wants. Never deploy a chrome-carrying page under a chrome-injecting legacy skin without the user's explicit, informed choice.

**Path C — region suppression (preferred whenever the site is on a composite skin).** Set `regions_off` at URL scope to the regions the page supplies itself (e.g. `nav,footer`). Pure config, page-atomic, and the page keeps every engine service: canonical, feed autodiscovery, JSON-LD SearchAction, data islands, analytics, OPAL widget. This is the option legacy skins cannot offer, and it is the reason to consider migrating a site to a composite skin rather than repeatedly working around the all-or-nothing wrap.

**Path A — passthrough override (legacy sites; page keeps its own chrome).** Per-URL `xslt_sheet` override to `/DAV/VAD/inclusion-engine/skin/passthrough/xslt/PostProcess.xslt`, which copies `/html/head/*` and `/html/body` through essentially verbatim while still merging RDFa/SPARQL data-islands and Markdown blocks. Fast and page-atomic, but the page forfeits the engine-supplied extras listed above and loses site-wide nav consistency.

**Path B — chrome-strip under the live skin (legacy sites; recommended when the replacement's CSS derives from the live site).** Remove the replacement's own masthead/nav/footer and any head includes the live skin already injects (under `matrix`: Bootstrap 5.3.3 CSS/JS, Inter font, jQuery, `/skin/matrix/css/style.css` — `tidyups.xslt` dedupes many automatically); keep its `<style>` blocks and content sections. No config change at all — a pure WebDAV PUT. Matrix copies body children as-is when a `.container` structure exists, so wrap stripped content accordingly.
=======
**The real question is never "strip this one page to fit the current skin" — it's "does this new appearance become the site's skin?"** A homepage mockup only has opinions about the homepage; every site has a multiplicity of other page types (contact forms, customer-snapshot/testimonial layouts, pricing, docs, etc.) that the mockup says nothing about. Treat every self-styled replacement as a candidate **new skin**, and resolve these design questions before writing any XSLT or touching DAV content:

1. **How many appearances do you actually want?** One shared look across all affected sites, or a distinct one per site?
2. **Relationship to the current skin (`matrix` or whichever is live)**: same CSS framework (Bootstrap) across all of them? Same dynamic-menu/nav-toggle JS?
3. **Coverage beyond the homepage**: what do Contact forms, Customer Snapshots, and other recurring page/component types need to look like under the new appearance? A homepage-only mockup is silent on this — it must be extended or the gap flagged before go-live.
4. **Common features across the candidate mockups** — literal overlap in fonts, color tokens, nav markup, CSS frameworks — is the input to the decision below. Run `scripts/check_chrome_conflict.py` on each candidate first for a fast per-file signal, then compare across candidates by eye (font-family, `--custom-property` names, Bootstrap usage, nav/toggle markup) — see `references/skin-commonality-assessment.md` for the method and a worked example.
5. **Minimize conditionality in the skin.** Every `<xsl:if>`/`<xsl:choose>` branching on site or content shape is a maintenance liability — prefer factoring differences into includes or separate skins over branching logic in one shared `PostProcess.xslt`.

Both the inclusion-engine and opl-skins VADs already carry a `common/` directory — any new skin must integrate with these, not reimplement them:

- **inclusion-engine `common/`** — engine functionality: feeds (`feeds.vsp`), search (`search.vsp`), sitemap (`sitemap.vsp`), 404 handling, `osdi.vsp`.
- **opl-skins `common/`** — skin-level integration: authentication (`auth/login.vsp`, `logout.vsp`, `register.vsp`, `profile.vsp`, cart), `data-islands.xslt` (RDFa/SPARQL merge), `embedding.xslt` (embedded queries), analytics (`urchin*.xslt`), feed transforms (`feed2atom/json/rss/sitemap.xslt`), `opal.xslt`.

**Decide, then act** (full process in `references/skin-commonality-assessment.md` and `references/skin-authoring-howto.md`):

- **Enough commonality across the candidates** → author **one new shared skin** (e.g. `zion` — deliberately the inverse of `matrix`: per-site layout supplies the variation, not per-page content-stripping) with per-site includes, e.g. `<xsl:include href="uda/xslt/layout.xslt"/>`.
- **Not enough commonality** → author **one new skin per site**, following the community-documented process in `references/skin-authoring-howto.md`: paste the mockup HTML into a new `PostProcess.xslt`, strip content down to appearance-only markup plus an `<xsl:apply-templates select="/something/appropriate" mode="copy"/>` at the correct insertion point, integrate the two `common/` directories above, then replace DAV `content/index.html` with just the content fragment (the appearance now lives in the skin, not the page).

Passthrough remains available for a genuine one-off with no skin ambition — but it is the exception, not step one.
>>>>>>> origin/main

## Elicitations — Establish Before Acting

Ask (or confirm from context) each of the following before running SQL or WebDAV operations. Do not guess any of them; example values in documentation are illustrative, not live values.

1. **Target Virtuoso instance**: hostname, SQL port (isql) and HTTP/HTTPS port; whether the SQL listener is TLS-enabled.
2. **Identity mode**: SQL username/password; isql over TLS with `-X` PKCS#12 / `-T` CA bundle / `-W` WebID; WebDAV username/password; WebDAV mTLS; WebDAV mTLS + `On-Behalf-Of` delegation.
3. **Site shortname(s)**: as registered in the config graph (e.g. `virtuoso`, `uda`, `ps`). Verify with the site-enumeration query in `references/config-api.md`; register missing sites with `incleng..config_add_site` only after user confirmation.
4. **Actual `webdav_base` per site**: always read it live via `incleng..config_get(null, '<site>', 'webdav_base')` — never assume the path.
5. **Source document(s)**: URL or local path of each replacement page, and which target page each one replaces (homepage → `content/index.html`; other pages → `content/{name}.html`).
6. **Override scope**: per-URL (recommended for homepage swaps — leaves all other pages on the site's normal skin), per-site, or global.
<<<<<<< HEAD
7. **Chrome remediation & skin choice**: Path C (region suppression, composite sites), Path A (passthrough override), or Path B (strip page chrome). Read the live skin first to know which are available.
8. **For composite-skin work**: the manifest's DAV path (`skin_manifest`), the site's named graph (`site_graph`), and whether the site graph already exists or must be built.
9. **Backup/rollback policy**: whether to preserve the current `content/index.html` (default: yes — copy to `content/index.html.pre-<YYYYMMDD>` or a user-designated location before overwriting).
10. **Go-live confirmation**: deploying to a public site requires explicit user go-ahead per site. Preparing a validated bundle without deploying is a valid stopping point when credentials or approval are absent.

## Workflow — Homepage / Page Replacement

1. **Elicit** the values above. Fetch each source document; verify HTTP 200 and non-trivial size.
2. **Classify** each document with `scripts/check_chrome_conflict.py`: fragment vs full document; which chrome regions it carries; external asset references that must resolve from the live origin.
3. **Read live config**: enumerate sites, read each target site's `webdav_base`, and resolve the target URL's `skin_manifest` / `xslt_sheet` (`references/config-api.md` has the queries).
4. **Back up** the current target file via WebDAV GET before overwriting, unless the user declines.
5. **Apply the elicited remediation**: `regions_off` (Path C), `xslt_sheet` override (Path A), or nothing (Path B) — see `templates/skin-override.sql`.
6. **Deploy content**: WebDAV PUT the replacement as `content/index.html` (or the elicited target path) under the site's `webdav_base`. Use curl per the standing curl-first rule; MCP tools only when no CLI path exists.
7. **Flush once** after any config change: `select incleng..config_flush_cache();`. Content-only changes self-invalidate on mtime. If skin XSLT or a composite manifest changed, run `select incleng..staleall();` instead — and re-run `incleng..osdi_skin_load()` after any manifest edit.
8. **Verify in a browser**, not only by diffing markup. Confirm single chrome, correct title, resolvable stylesheet (a `401` from a freshly PUT asset is the common one), and that at least one *other* page still renders normally, proving the override stayed scoped.
9. **Report** per site: config statements executed, files PUT (with backup locations), verification results. Never claim success without step 8.
=======
7. **Skin strategy**: one shared new skin (e.g. `zion`) vs one new skin per site vs a one-off passthrough override — resolved via the commonality assessment above and `references/skin-commonality-assessment.md`. Available skins span two VADs: `/DAV/VAD/inclusion-engine/skin/` (legacy: `openlink`, `responsive`, `passthrough`, …) and `/DAV/VAD/opl-skins/` (modern: `matrix`, `bootstrap-2022`, `docs-v3`, …). Read the live `xslt_sheet` first to know the active skin.
7a. **Non-homepage page/component coverage**: which additional page types (Contact, Customer Snapshot, pricing, docs, …) must be styled under the new skin before go-live, and who is supplying those designs if the mockup doesn't cover them.
8. **Backup/rollback policy**: whether to preserve the current `content/index.html` (default: yes — copy to `content/index.html.pre-<YYYYMMDD>` or a user-designated location before overwriting).
9. **Go-live confirmation**: deploying to a public site requires explicit user go-ahead per site. Preparing a validated bundle without deploying is a valid stopping point when credentials or approval are absent.

## Workflow — Homepage / Page Replacement

1. **Elicit** the values above, including the skin-strategy questions (how many appearances, relationship to the live skin, non-homepage coverage). Fetch each source document; verify HTTP 200 and non-trivial size.
2. **Classify** each document with `scripts/check_chrome_conflict.py`: fragment vs full document; self-contained chrome or not; external asset references (CDN fonts, stylesheets); fonts, CSS custom-property names, CSS framework, and nav/toggle markup for the cross-candidate commonality comparison.
3. **Assess commonality** across all candidate mockups per `references/skin-commonality-assessment.md`; decide with the user: shared `zion`-style skin, per-site skins, or (exceptionally) passthrough for a single page.
4. **Read live config**: enumerate sites, read each target site's `webdav_base` and current `xslt_sheet` resolution for the target URL (`references/config-api.md` has the queries).
5. **Author the skin(s)** per `references/skin-authoring-howto.md`: paste mockup HTML into a new `PostProcess.xslt`, strip to appearance-only markup plus the correct `apply-templates mode="copy"` insertion point, integrate both `common/` directories (feeds/search/sitemap from inclusion-engine; auth/data-islands/embedding/analytics from opl-skins), install under the target VAD.
6. **Back up** the current target file(s) via WebDAV GET before overwriting, unless the user declines.
7. **Switch the skin**: `xslt_sheet` config to the new skin, scoped per the elicited choice (per-URL for a single-page passthrough stopgap; per-site or global for a real new skin) — see `templates/skin-override.sql`.
8. **Deploy content**: WebDAV PUT each page's stripped content fragment as `content/{name}.html` under the site's `webdav_base`. Use curl per the standing curl-first rule; MCP tools only when no CLI path exists.
9. **Flush**: `select incleng..staleall();` after any new/changed skin XSLT (compiled-XSLT cache); `select incleng..config_flush_cache();` after any other config change. Content-only changes self-invalidate on mtime.
10. **Verify**: fetch each live page; confirm single chrome (exactly one masthead/nav/footer), title correctness, resolvable external assets, and — if the skin change was scoped — that at least one *other* page still renders correctly (proves scope was respected). Spot-check any non-homepage page types elicited in step 1.
11. **Report** per site: skin strategy chosen and why, XSLT/config statements executed, files PUT (with backup locations), verification results. Never claim success without step 10.
>>>>>>> origin/main

## Workflow — Composite Skin

Full detail, including the manifest and directive vocabularies, is in `references/composite-skins.md`. The shape:

1. Author or upload the bundle (`skin.ttl`, `template/`, `css/`, `js/`) to its DAV collection.
2. Make the bundle world-readable and give it a vdir matching its `osdi:assetBase`.
3. Load the site's RDF into the named graph; set `site_graph`.
4. `select incleng..osdi_skin_load('<manifest>');` — the manifest deployment step, re-run after **every** manifest edit.
5. `config_set` `skin_manifest` at the chosen scope; set `url_trailing_slash 0` if the site presents `.html` URLs.
6. `select incleng..staleall();`
7. Verify in a browser.

`templates/composite-skin-register.sql` is a parameterised version of steps 2–6.

## Other Supported Operations

- **Site registration/removal**: `incleng..config_add_site('<shortname>', '<baseURL>', '<webdavbase>')` / `incleng..config_remove_site('<shortname>')`. `baseURL` must be the **absolute** public prefix — `config_url_to_site` matches it with `fn:starts-with` against the request URL, and `url_davfile` strips it. Note `config_add_site` swallows errors and will not update an existing site's `foaf:homepage`; delete the old triple first.
- **Config parameter management**: get/set/unset of `debug_level`, `notfoundurl`, `inline_ttl`, `inline_jsonld`, `search_graphs`, `search_requrl`, `search_site_graphs`, `xslt_sheet`, `skin_manifest`, `site_graph`, `regions_off`, `url_trailing_slash`, `allow_edit` at URL, site, or global scope.
- **Cache and XSLT maintenance**: `config_flush_cache()` vs `staleall()` — see step 7 above.
- **index.vsp propagation**: after `common/index.vsp` changes, `incleng..config_propagate_index_vsp(user, password)` copies it to every registered site's base collection.
- **Troubleshooting**: double chrome, stale pages, 404 handling, missing images, raw VSP served, `401` on skin assets — see `references/engine-architecture.md`.

## References

- `references/composite-skins.md` — the manifest and directive vocabularies, config parameters, SQL API, deployment checklist, and the authoring gotchas that only a browser load catches.
- `references/engine-architecture.md` — how index.vsp, skins, tidy, caching, vhosts/vdirs, and opt-outs fit together; skin inventory and per-skin chrome behavior.
<<<<<<< HEAD
- `references/config-api.md` — config graph structure, all `incleng..config_*` and `incleng..osdi_*` signatures, resolution order (URL → site → global), ready-to-run inspection queries.
- `references/homepage-replacement-playbook.md` — the worked virtuoso/uda/ps homepage-swap scenario end to end, including the chrome-conflict findings that motivated the gate.
- `templates/skin-override.sql` — parameterized SQL for per-URL/per-site skin overrides, region suppression, and rollback.
- `templates/composite-skin-register.sql` — parameterized composite-skin registration and teardown.
- `scripts/check_chrome_conflict.py` — classifies a replacement document, names the regions it carries, and recommends Path A/B/C.
=======
- `references/config-api.md` — config graph structure, all `incleng..config_*` signatures, resolution order (URL → site → global), ready-to-run inspection queries.
- `references/skin-commonality-assessment.md` — the method for deciding shared-skin vs per-site-skins vs passthrough, with a worked commonality scan across the virtuoso/uda/ps mockups (fonts, CSS custom properties, framework usage, nav markup all diverged — recorded as a real example of "not enough commonality").
- `references/skin-authoring-howto.md` — the community-documented new-skin authoring process (PostProcess.xslt content-stripping, `common/` integration, DAV content replacement), plus the `zion` shared-skin variant with per-site `xsl:include` layouts.
- `references/homepage-replacement-playbook.md` — the worked virtuoso/uda/ps scenario end to end, revised to the skin-authoring decision framework.
- `templates/skin-override.sql` — parameterized SQL for `xslt_sheet` switches (per-URL, per-site, or global) and rollback.
- `scripts/check_chrome_conflict.py` — classifies a candidate document (structure, chrome, assets, fonts, CSS custom properties, framework, nav markup) as input to the commonality assessment.
>>>>>>> origin/main
