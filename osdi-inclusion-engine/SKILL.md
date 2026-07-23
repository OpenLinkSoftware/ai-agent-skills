---
name: osdi-inclusion-engine
description: Operate the OpenLink OSDI Inclusion Engine — the Virtuoso index.vsp + XSLT-skin system that renders openlinksw.com sub-sites (www, virtuoso, uda, ps, ode, shop) from WebDAV content. Use for site registration, config-graph inspection and edits, skin selection or per-URL skin overrides, homepage or page replacement deployment from DAV-hosted mockups, double-chrome conflict detection, cache flushing, and post-deploy verification. Trigger on phrases like "integrate this homepage replacement", "swap the skin for", "register a new OSDI site", "Inclusion Engine config", "flush the incleng cache", or any request to deploy content into an OSDI-based website.
---

# OSDI Inclusion Engine

Use this skill to inspect, configure, and deploy content into websites run by the OpenLink Inclusion Engine (OSDI): a Virtuoso-hosted system where a single `index.vsp` per site resolves `/{page}` requests to `content/{page}.html` in WebDAV, passes the document through HTML Tidy (unless its DOCTYPE is XHTML+RDFa), wraps it with a skin's XSLT (`PostProcess.xslt`), merges RDF data-islands, caches the rendered result in `incleng..cache`, and serves it.

All configuration lives in the RDF quadstore graph `<urn:com.openlinksw.virtuoso.incleng>`, accessed via the `incleng..config_*` SQL API — **never** the legacy `incleng..sites` table. Read `references/config-api.md` before issuing any config SQL.

## Blocking Gate — Chrome Conflict Check Before Any Page Deployment

Every chrome-bearing skin — legacy `openlink`/`responsive` in the inclusion-engine VAD, and modern `matrix`/`bootstrap-2022` in the **opl-skins VAD** — **unconditionally injects** the corporate masthead and footer around whatever is in the source document's `<body>`. If a replacement page carries its own `<nav>`, `<header>`, or `<footer>` markup, deploying it under those skins stacks two sets of chrome — and when the replacement's CSS deliberately mirrors the live site's design, the duplication is visually subtle and easy to miss in review.

Therefore, before deploying ANY page into an OSDI site:

1. Read the **live** `xslt_sheet` for the target URL (`config_get`) to learn which skin/VAD is actually active — never assume.
2. Fetch the replacement document and run `scripts/check_chrome_conflict.py <file-or-url>`.
3. If it reports self-contained chrome, elicit which remediation the user wants (see Path A/B below); never deploy a chrome-carrying page under a chrome-injecting skin without the user's explicit, informed choice.

**Path A — passthrough override (page keeps its own chrome).** Per-URL `xslt_sheet` override to `/DAV/VAD/inclusion-engine/skin/passthrough/xslt/PostProcess.xslt`, which copies `/html/head/*` and `/html/body` through essentially verbatim while still merging RDFa/SPARQL data-islands and Markdown blocks. Fastest and page-atomic, but the page loses engine-supplied extras: feeds links, canonical, JSON-LD SearchAction, analytics, OPAL widget, and site-wide nav consistency.

**Path B — chrome-strip under the live skin (recommended when the replacement's CSS derives from the live site).** Remove the replacement's own masthead/nav/footer and any head includes the live skin already injects (under `matrix`: Bootstrap 5.3.3 CSS/JS, Inter font, jQuery, `/skin/matrix/css/style.css` — `tidyups.xslt` dedupes many of these automatically); keep its `<style>` blocks and content sections. No config change at all — a pure WebDAV PUT. Matrix copies body children as-is when a `.container` structure exists, so wrap stripped content accordingly. Preserves site-wide chrome, feeds, search, analytics, and OPAL integration.

## Elicitations — Establish Before Acting

Ask (or confirm from context) each of the following before running SQL or WebDAV operations. Do not guess any of them; example values in documentation are illustrative, not live values.

1. **Target Virtuoso instance**: hostname, SQL port (isql) and HTTP/HTTPS port; whether the SQL listener is TLS-enabled.
2. **Identity mode**: SQL username/password; isql over TLS with `-X` PKCS#12 / `-T` CA bundle / `-W` WebID; WebDAV username/password; WebDAV mTLS; WebDAV mTLS + `On-Behalf-Of` delegation.
3. **Site shortname(s)**: as registered in the config graph (e.g. `virtuoso`, `uda`, `ps`). Verify with the site-enumeration query in `references/config-api.md`; register missing sites with `incleng..config_add_site` only after user confirmation.
4. **Actual `webdav_base` per site**: always read it live via `incleng..config_get(null, '<site>', 'webdav_base')` — never assume the path.
5. **Source document(s)**: URL or local path of each replacement page, and which target page each one replaces (homepage → `content/index.html`; other pages → `content/{name}.html`).
6. **Override scope**: per-URL (recommended for homepage swaps — leaves all other pages on the site's normal skin), per-site, or global.
7. **Chrome remediation & skin choice**: Path A (passthrough override, page keeps own chrome) vs Path B (strip page chrome, deploy under live skin). Available skins span two VADs: `/DAV/VAD/inclusion-engine/skin/` (legacy: `openlink`, `responsive`, `passthrough`, …) and `/DAV/VAD/opl-skins/` (modern: `matrix`, `bootstrap-2022`, `docs-v3`, …). Read the live `xslt_sheet` first to know the active skin.
8. **Backup/rollback policy**: whether to preserve the current `content/index.html` (default: yes — copy to `content/index.html.pre-<YYYYMMDD>` or a user-designated location before overwriting).
9. **Go-live confirmation**: deploying to a public site requires explicit user go-ahead per site. Preparing a validated bundle without deploying is a valid stopping point when credentials or approval are absent.

## Workflow — Homepage / Page Replacement

1. **Elicit** the values above. Fetch each source document; verify HTTP 200 and non-trivial size.
2. **Classify** each document with `scripts/check_chrome_conflict.py`: fragment vs full document; self-contained chrome or not; external asset references (CDN fonts, stylesheets) that must resolve from the live origin.
3. **Read live config**: enumerate sites, read each target site's `webdav_base` and current `xslt_sheet` resolution for the target URL (`references/config-api.md` has the queries).
4. **Back up** the current target file via WebDAV GET before overwriting, unless the user declines.
5. **Apply skin override** (config change) when the gate requires it, scoped per the elicited choice — see `templates/skin-override.sql`.
6. **Deploy content**: WebDAV PUT the replacement as `content/index.html` (or the elicited target path) under the site's `webdav_base`. Use curl per the standing curl-first rule; MCP tools only when no CLI path exists.
7. **Flush cache once** after any config change: `select incleng..config_flush_cache();`. Content-only changes self-invalidate on mtime and need no flush. If skin XSLT files themselves were edited, run `select incleng..staleall();` instead (Virtuoso caches compiled XSLT).
8. **Verify**: fetch each live homepage; confirm single chrome (exactly one masthead/nav/footer), title correctness, resolvable external assets, and that at least one *other* page on the site still renders with the normal skin (proves the override stayed scoped).
9. **Report** per site: config statements executed, files PUT (with backup locations), verification results. Never claim success without step 8.

## Other Supported Operations

- **Site registration/removal**: `incleng..config_add_site('<shortname>', '<baseURL>', '<webdavbase>')` / `incleng..config_remove_site('<shortname>')`, plus vhost/vdir notes in `references/engine-architecture.md`.
- **Config parameter management**: get/set/unset of `debug_level`, `notfoundurl`, `inline_ttl`, `inline_jsonld`, `search_graphs`, `search_requrl`, `search_site_graphs`, `xslt_sheet`, `allow_edit` at URL, site, or global scope.
- **Cache and XSLT maintenance**: `config_flush_cache()` vs `staleall()` — see step 7 for which applies.
- **index.vsp propagation**: after `common/index.vsp` changes, `incleng..config_propagate_index_vsp(user, password)` copies it to every registered site's base collection.
- **Troubleshooting**: double chrome (skin/content conflict), stale pages (cache/XSLT), 404 handling (`notfoundurl`, `incleng..rewrite`), missing images (`/images` vdir opt-out), raw VSP served (vdir default-page misconfig) — see `references/engine-architecture.md`.

## References

- `references/engine-architecture.md` — how index.vsp, skins, tidy, caching, vhosts/vdirs, and opt-outs fit together; skin inventory and per-skin chrome behavior.
- `references/config-api.md` — config graph structure, all `incleng..config_*` signatures, resolution order (URL → site → global), ready-to-run inspection queries.
- `references/homepage-replacement-playbook.md` — the worked virtuoso/uda/ps homepage-swap scenario end to end, including the chrome-conflict findings that motivated the gate.
- `templates/skin-override.sql` — parameterized SQL for per-URL/per-site skin overrides and rollback.
- `scripts/check_chrome_conflict.py` — classifies a replacement document and emits a deploy recommendation.
