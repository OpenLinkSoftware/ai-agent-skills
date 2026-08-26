---
name: osdi-inclusion-engine
description: Operate the OpenLink OSDI Inclusion Engine — the Virtuoso index.vsp + skin system that renders openlinksw.com sub-sites (www, virtuoso, uda, ps, ode, shop) from WebDAV content. Use for site registration, config-graph inspection and edits, skin selection or per-URL skin overrides, composite-skin authoring and deployment (manifest + XHTML templates + SPARQL bindings), region suppression, homepage or page replacement deployment from DAV-hosted mockups, double-chrome conflict detection, cache flushing, and post-deploy verification. Trigger on phrases like "integrate this homepage replacement", "swap the skin for", "register a new OSDI site", "Inclusion Engine config", "build a composite skin", "flush the incleng cache", or any request to deploy content into an OSDI-based website.
---

# OSDI Inclusion Engine

Use this skill to inspect, configure, and deploy content into websites run by the OpenLink Inclusion Engine (OSDI): a Virtuoso-hosted system where a single `index.vsp` per site resolves `/{page}` requests to `content/{page}.html` in WebDAV, passes the document through HTML Tidy (unless its DOCTYPE is XHTML+RDFa), wraps it with a skin, merges RDF data-islands, caches the rendered result in `incleng..cache`, and serves it.

All configuration lives in the RDF quadstore graph `<urn:com.openlinksw.virtuoso.incleng>`, accessed via the `incleng..config_*` SQL API — **never** the legacy `incleng..sites` table. Read `references/config-api.md` before issuing any config SQL.

## Two Kinds of Skin

Which kind is in play determines almost everything else, so establish it first.

**Legacy skins** (`openlink`, `responsive`, `matrix`, `bootstrap-2022`, `docs-v3`, …) are single hand-written `PostProcess.xslt` files with the site's navigation markup, asset paths and layout fused inside them. They **unconditionally inject** masthead and footer around whatever is in the source document's `<body>`. They are selected by the `xslt_sheet` config parameter.

**Composite skins** are manifest-declared bundles — a `skin.ttl` naming a theme, a set of plain-XHTML templates carrying `data-osdi-*` binding attributes, and SPARQL bindings resolved against a named graph at render time. Navigation is data, the stylesheet is a manifest string, and chrome is a set of independently suppressible regions. They are selected by the `skin_manifest` config parameter, which overrides `xslt_sheet`. See `references/composite-skins.md`.

Read the live config for the target URL before reasoning about either — never assume.

## Blocking Gate — Chrome Conflict Check Before Any Page Deployment

Every **legacy** chrome-bearing skin injects the corporate masthead and footer unconditionally. If a replacement page carries its own `<nav>`, `<header>`, or `<footer>`, deploying it under such a skin stacks two sets of chrome — and when the replacement's CSS deliberately mirrors the live site's design, the duplication is visually subtle and easy to miss in review.

Therefore, before deploying ANY page into an OSDI site:

1. Read the **live** skin for the target URL (`config_get` for `skin_manifest`, then `xslt_sheet`) to learn what is actually active.
2. Fetch the replacement document and run `scripts/check_chrome_conflict.py <file-or-url>`. It reports which chrome the page carries and recommends a path; it is a **recommender, not a blocker** — the choice below is the user's.
3. If it reports self-contained chrome, elicit which remediation the user wants. Never deploy a chrome-carrying page under a chrome-injecting legacy skin without the user's explicit, informed choice.

**Path C — region suppression (preferred whenever the site is on a composite skin).** Set `regions_off` at URL scope to the regions the page supplies itself (e.g. `nav,footer`). Pure config, page-atomic, and the page keeps every engine service: canonical, feed autodiscovery, JSON-LD SearchAction, data islands, analytics, OPAL widget. This is the option legacy skins cannot offer, and it is the reason to consider migrating a site to a composite skin rather than repeatedly working around the all-or-nothing wrap.

**Path A — passthrough override (legacy sites; page keeps its own chrome).** Per-URL `xslt_sheet` override to `/DAV/VAD/inclusion-engine/skin/passthrough/xslt/PostProcess.xslt`, which copies `/html/head/*` and `/html/body` through essentially verbatim while still merging RDFa/SPARQL data-islands and Markdown blocks. Fast and page-atomic, but the page forfeits the engine-supplied extras listed above and loses site-wide nav consistency.

**Path B — chrome-strip under the live skin (legacy sites; recommended when the replacement's CSS derives from the live site).** Remove the replacement's own masthead/nav/footer and any head includes the live skin already injects (under `matrix`: Bootstrap 5.3.3 CSS/JS, Inter font, jQuery, `/skin/matrix/css/style.css` — `tidyups.xslt` dedupes many automatically); keep its `<style>` blocks and content sections. No config change at all — a pure WebDAV PUT. Matrix copies body children as-is when a `.container` structure exists, so wrap stripped content accordingly.

## Elicitations — Establish Before Acting

Ask (or confirm from context) each of the following before running SQL or WebDAV operations. Do not guess any of them; example values in documentation are illustrative, not live values.

1. **Target Virtuoso instance**: hostname, SQL port (isql) and HTTP/HTTPS port; whether the SQL listener is TLS-enabled.
2. **Identity mode**: SQL username/password; isql over TLS with `-X` PKCS#12 / `-T` CA bundle / `-W` WebID; WebDAV username/password; WebDAV mTLS; WebDAV mTLS + `On-Behalf-Of` delegation.
3. **Site shortname(s)**: as registered in the config graph (e.g. `virtuoso`, `uda`, `ps`). Verify with the site-enumeration query in `references/config-api.md`; register missing sites with `incleng..config_add_site` only after user confirmation.
4. **Actual `webdav_base` per site**: always read it live via `incleng..config_get(null, '<site>', 'webdav_base')` — never assume the path.
5. **Source document(s)**: URL or local path of each replacement page, and which target page each one replaces (homepage → `content/index.html`; other pages → `content/{name}.html`).
6. **Override scope**: per-URL (recommended for homepage swaps — leaves all other pages on the site's normal skin), per-site, or global.
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
- `references/config-api.md` — config graph structure, all `incleng..config_*` and `incleng..osdi_*` signatures, resolution order (URL → site → global), ready-to-run inspection queries.
- `references/homepage-replacement-playbook.md` — the worked virtuoso/uda/ps homepage-swap scenario end to end, including the chrome-conflict findings that motivated the gate.
- `templates/skin-override.sql` — parameterized SQL for per-URL/per-site skin overrides, region suppression, and rollback.
- `templates/composite-skin-register.sql` — parameterized composite-skin registration and teardown.
- `scripts/check_chrome_conflict.py` — classifies a replacement document, names the regions it carries, and recommends Path A/B/C.
