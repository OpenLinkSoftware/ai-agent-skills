# OSDI Inclusion Engine — Architecture

## Request Lifecycle ("full-fat" mode)

1. A vhost maps `/` to a WebDAV collection with `index.vsp` as the default page, handling all requests.
2. `index.vsp` identifies the site (from the incoming URL or DAV base collection) via `incleng..config_url_to_site()`.
3. It resolves the request path to a source document: `{webdav_base}/content/{request}.html` — the engine appends `.html`. `/` → `content/index.html`; `/news` → `content/news.html`; `/news/foo.html` → `content/news/foo.html`.
4. The document is passed through HTML Tidy **unless** its DOCTYPE is XHTML+RDFa. Tidy accepts anything from a bare line of text to a full HTML document and normalizes it into valid XHTML.
5. Optional SPARQL queries pull page metadata from configured graphs (`search_graphs`, `search_requrl`, `search_site_graphs`); Turtle/JSON-LD script-tag data islands are merged per `inline_ttl` / `inline_jsonld`.
6. The result is transformed by a skin. **If `skin_manifest` is set** for this URL/site/global scope, the engine resolves that composite skin's manifest — building `<skintheme>`, `<skintemplate>` and `<skindata>` (the last by running the manifest's SPARQL against `site_graph`) — and hands all three to the single generic composer at `skin/composite/xslt/PostProcess.xslt`. **Otherwise** it uses the legacy skin XSLT named in `xslt_sheet` (a `virt://WS.WS.SYS_DAV_RES...` path into DAV).
7. The fully rendered page is stored in `incleng..cache` and emitted. Only found pages are cached (caching 404s would be a DoS vector).
8. If the page is not found, `incleng..rewrite` rules are consulted; failing that, redirect to `notfoundurl`.

## Caching Rules

- Content change (`content/*.html` mtime newer than cache row) → automatic re-render; no action needed.
- Config change (skin override, search graphs, etc.) → run `select incleng..config_flush_cache();`.
- Skin XSLT file edited → Virtuoso caches compiled XSLT internally; run `select incleng..staleall();` (also empties the cache table).

## Composite Skins

A second kind of skin, selected by `skin_manifest` rather than `xslt_sheet`. A composite skin bundle contains **no XSLT of its own** — only `skin.ttl`, plain-XHTML templates carrying `data-osdi-*` binding attributes, and the theme. One shared composer (`skin/composite/xslt/PostProcess.xslt` + `skin/common/xslt/osdi-compose.xslt`) serves all of them.

The practical difference is that its chrome is a set of **independently suppressible regions** (`regions_off`) rather than an unconditional wrap, so a page can supply its own masthead and still receive canonical, feed autodiscovery, data islands, analytics and the OPAL widget — the trade-off the passthrough skin forces. Navigation is data in the site graph, and the stylesheet is a manifest string, so restructuring the nav or reskinning does not touch a template, and re-laying-out a page does not touch a query.

Full detail in `references/composite-skins.md`.

## Skin Inventory and Chrome Behavior

Skins live in **two VADs**, each skin with an `xslt/PostProcess.xslt` entry point:

- `/DAV/VAD/inclusion-engine/skin/` — legacy skins bundled with the engine (source repo: `inclusion-engine/skin/`).
- `/DAV/VAD/opl-skins/` — modern skins extracted into their own VAD for maintenance (source repo: `opl-skins/`): `matrix`, `bootstrap-2022`, `docs`, `docs-v3`, `openlink`, `wiki`, `vos-ods-v3`, plus shared `common/`. Switch globally with `incleng..config_set(null, null, 'xslt_sheet', 'virt://WS.WS.SYS_DAV_RES.RES_FULL_PATH.RES_CONTENT:/DAV/VAD/opl-skins/{skin}/xslt/PostProcess.xslt')` followed by `incleng..staleall()` (a sheet switch changes compiled XSLT — `config_flush_cache()` alone is not sufficient).

Always read the **live** global/site `xslt_sheet` value before reasoning about chrome; do not assume which VAD or skin is active.

| Skin | Injects chrome? | Notes |
|---|---|---|
| `openlink` | **Yes** — masthead, breadcrumbs, horiznav, navbar2, footer, social bar, unconditionally around `<body>` content | Classic corporate skin; grid layout (`twentythree columns` etc.) |
| `responsive` | **Yes** — masthead, navbar-left, footer | Responsive variant of the corporate chrome |
| `passthrough` | **No** — copies `/html/head/*` and `/html/body` through verbatim | Still merges RDFa/SPARQL data islands and Markdown; correct choice for fully self-styled pages |
| `public` | Partial — masthead, footer, links | Lighter public skin |
| `clean` | Minimal | Near-passthrough with basic framing |
| `docs` | Yes (docs-specific margins) | Elides internal `navheader` divs |
| `bootstrap-2018-frozen` | Yes | Frozen Bootstrap-era chrome with live menus |
| `iODBC` | Yes | iODBC-branded |

opl-skins VAD:

| Skin | Injects chrome? | Notes |
|---|---|---|
| `matrix` | **Yes** — masthead, prefooter, footer, unconditionally | Current-generation corporate skin (Bootstrap 5.3.3 + Inter + `/skin/matrix/css/style.css`). Content-aware body handling: if body already contains a `.container` (div/main/section), body children are copied as-is; otherwise wrapped in `<div class="container py-5">`. `tidyups.xslt` dedupes known libraries the content may carry (bootstrap JS bundle, jQuery, flickity, markdown-it, gsap, papaparse, plausible…) and rewrites relative links. Head auto-injects: Bootstrap CSS/JS, Inter font, jQuery + jquery-xpath, matrix style.css, feeds links (RSS/Atom/JSON), canonical, JSON-LD SearchAction, OPAL widget CSS/JS, ods-auth.js. |
| `bootstrap-2022` | **Yes** — masthead/menus, footer | Predecessor of matrix; menus.xslt, newsanimation, OPAL widget |
| `docs`, `docs-v3`, `wiki`, `vos-ods-v3`, `openlink` | Yes (variant-specific) | Documentation/wiki/site variants |

Key fact driving the chrome-conflict gate: neither the legacy `openlink` skin nor the modern `matrix`/`bootstrap-2022` skins have any conditional that suppresses engine chrome when content supplies its own. A page's own `<nav>/<header>/<footer>` is simply copied inside the engine's `<main>`/`#thecontent`, yielding doubled chrome. However, matrix's head/library dedupe plus its "existing `.container` structure" detection make **chrome-stripping** a first-class alternative to the passthrough override: remove the page's own masthead/nav/footer and redundant head includes, keep its `<style>` and content sections, and the engine supplies consistent site-wide chrome around it.

## Opt-Outs

Anything that must bypass `index.vsp` gets its own vdir: `/skin`, `/images`, `/js`, `/webmaster` (favicon.ico, robots.txt via rewrite), `/vsp` (executable scripts), ODS app dirs like `/dataspace`. Images referenced by content should use `/images/...` paths.

## Alternate Invocation Modes

- **Just the Skin**: any VSP/PHP page emitting valid XHTML can end with `<?vsp incleng..xslt(); ?>` (or `http_xslt(...)`) to gain the skin without index.vsp.
- **ODS Wiki skin**: point the cluster's skin URL at the DAV `xslt/` collection; `PostProcess.xslt` is assumed.

## Troubleshooting Map

| Symptom | Likely cause | Fix |
|---|---|---|
| Two mastheads/navs/footers on a page | Chrome-carrying content deployed under chrome-injecting skin | Composite site: `regions_off` at URL scope. Legacy site: per-URL `xslt_sheet` override to `passthrough`, or strip the page's chrome. Then `config_flush_cache()` |
| Manifest edit has no effect | Manifest is parsed into its own graph at deploy time | `incleng..osdi_skin_load('<manifest>')` **and** `staleall()` |
| `401` on a skin stylesheet or script | Files PUT over WebDAV are owned by the uploading account and are not world-readable | Set `RES_PERMS`/`COL_PERMS` to `111101101NN` across the bundle |
| Every request 302s to a trailing slash | `url_trailing_slash` defaults to 1 | `config_set` `url_trailing_slash` 0 for a site presenting `.html` URLs |
| "This document is empty and basically useless…" as visible page text | `inline_html5md` / `inline_rdfa` placeholder bodies | Set both 0 unless the site graph describes its pages |
| Debug trailer rendered as visible text | `debug_level` left set | `config_set` `debug_level` 0 |
| Edits to content not appearing | Should self-invalidate; if not, clock skew or config-level cache staleness | `config_flush_cache()` |
| Skin edits not appearing | Compiled-XSLT cache | `staleall()` |
| 404s on moved pages | No rewrite rule | Insert into `incleng..rewrite(site, old_url, new_url)`; note a rule never fires if `content/{old}.html` exists |
| Broken images | Content references non-`/images` paths intercepted by index.vsp | Move to `/images` vdir or add opt-out vdir |
| Raw VSP source served | vdir missing VSP user (`dba`) or default page misconfig | Fix vdir definition in Conductor |
| Debug output needed | — | `config_set` `debug_level` > 0 (console logging), remember to unset |
