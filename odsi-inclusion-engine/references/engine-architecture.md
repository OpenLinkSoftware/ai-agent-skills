# ODSI Inclusion Engine — Architecture

## Request Lifecycle ("full-fat" mode)

1. A vhost maps `/` to a WebDAV collection with `index.vsp` as the default page, handling all requests.
2. `index.vsp` identifies the site (from the incoming URL or DAV base collection) via `incleng..config_url_to_site()`.
3. It resolves the request path to a source document: `{webdav_base}/content/{request}.html` — the engine appends `.html`. `/` → `content/index.html`; `/news` → `content/news.html`; `/news/foo.html` → `content/news/foo.html`.
4. The document is passed through HTML Tidy **unless** its DOCTYPE is XHTML+RDFa. Tidy accepts anything from a bare line of text to a full HTML document and normalizes it into valid XHTML.
5. Optional SPARQL queries pull page metadata from configured graphs (`search_graphs`, `search_requrl`, `search_site_graphs`); Turtle/JSON-LD script-tag data islands are merged per `inline_ttl` / `inline_jsonld`.
6. The result is transformed by the skin XSLT named in `xslt_sheet` (a `virt://WS.WS.SYS_DAV_RES...` path into DAV).
7. The fully rendered page is stored in `incleng..cache` and emitted. Only found pages are cached (caching 404s would be a DoS vector).
8. If the page is not found, `incleng..rewrite` rules are consulted; failing that, redirect to `notfoundurl`.

## Caching Rules

- Content change (`content/*.html` mtime newer than cache row) → automatic re-render; no action needed.
- Config change (skin override, search graphs, etc.) → run `select incleng..config_flush_cache();`.
- Skin XSLT file edited → Virtuoso caches compiled XSLT internally; run `select incleng..staleall();` (also empties the cache table).

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
| Two mastheads/navs/footers on a page | Chrome-carrying content deployed under chrome-injecting skin | Per-URL `xslt_sheet` override to `passthrough`, then `config_flush_cache()` |
| Edits to content not appearing | Should self-invalidate; if not, clock skew or config-level cache staleness | `config_flush_cache()` |
| Skin edits not appearing | Compiled-XSLT cache | `staleall()` |
| 404s on moved pages | No rewrite rule | Insert into `incleng..rewrite(site, old_url, new_url)`; note a rule never fires if `content/{old}.html` exists |
| Broken images | Content references non-`/images` paths intercepted by index.vsp | Move to `/images` vdir or add opt-out vdir |
| Raw VSP source served | vdir missing VSP user (`dba`) or default page misconfig | Fix vdir definition in Conductor |
| Debug output needed | — | `config_set` `debug_level` > 0 (console logging), remember to unset |
