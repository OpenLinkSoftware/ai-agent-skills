# Playbook — Homepage Replacement into OSDI Sites

Worked scenario (2026-07): replacing the homepages of virtuoso.openlinksw.com, uda.openlinksw.com, and ps.openlinksw.com with three self-styled mockups hosted on an intranet DAV server. Generalizes to any "drop this finished HTML design in as page X" request.

## Why this scenario needs the gate

Analysis of the three replacement documents (`scripts/check_chrome_conflict.py`) showed:

| Document | Structure | Own chrome |
|---|---|---|
| Virtuoso revamp | Fragment (no `<html>/<body>`; `<meta>/<title>/<style>/<script>` + body markup) | `<nav class="navbar navbar-expand-lg bg-dark">`, `<footer class="bg-dark ...">` |
| UDA replacement | Fragment | `<header class="hdr"><nav>`, `<footer class="ftr">` |
| PS Ogilvy revamp | Full document (`<!doctype html>...<body>...</body>`) | `<header class="masthead">` |

All three reuse CSS from the live pages they replace, so their inline chrome **visually matches** the engine-injected chrome. Deployed unmodified under any chrome-bearing skin (legacy `openlink` or live `matrix` from the opl-skins VAD), each page would render doubled masthead/nav/footer — and because both copies look "correct", the duplication reads as a subtle glitch rather than an obvious clash.

Fragments are fine as source content — Tidy normalizes them into full documents before XSLT. Full documents with XHTML+RDFa DOCTYPEs skip Tidy entirely.

## Choose the Integration Path (elicit)

The live sites render under the `matrix` skin (`/DAV/VAD/opl-skins/matrix/`), and the replacements' CSS was derived from matrix-rendered pages — the Virtuoso mockup even links `/skin/matrix/css/style.css` and Bootstrap 5.3.3, which matrix injects into `<head>` anyway.

- **Path A — passthrough override**: deploy each file verbatim; per-URL `xslt_sheet` override to the inclusion-engine VAD's `passthrough` skin. Fastest; page is fully self-contained; but loses engine-supplied feeds links, canonical, JSON-LD SearchAction, analytics, OPAL widget, and shared masthead/footer.
- **Path B — chrome-strip under matrix (recommended for lasting integration)**: delete each mockup's own `<nav>/<header>/<footer>` and the head includes matrix already injects (Bootstrap CSS, Inter font, matrix style.css; `tidyups.xslt` auto-dedupes bootstrap JS/jQuery/etc.); keep the mockup's `<style>` and content sections, ensuring a top-level `.container` element so matrix copies the body as-is. **No config change** — pure WebDAV PUT of the edited file. Site-wide chrome, search, feeds, and OPAL stay consistent.

The procedure below is Path A; for Path B, skip steps 4 and 6 (no config change → no flush needed; content mtime self-invalidates) and instead verify the stripped file renders correctly under matrix.

## Per-Site Procedure (Path A)

For each site (shortname `S`, homepage URL `U`, replacement source `SRC`):

1. **Confirm live values** — never trust documentation examples:
   ```sql
   select incleng..config_get(null, 'S', 'webdav_base');
   select incleng..config_get('U', 'S', 'xslt_sheet');
   ```
2. **Classify the source**: `python3 scripts/check_chrome_conflict.py SRC` (accepts URL or file; use `--insecure` for intranet self-signed TLS).
3. **Back up** current homepage:
   ```
   curl -k -u user:pass -o index.html.pre-YYYYMMDD "https://host{webdav_base}content/index.html"
   ```
4. **Scope the skin override to U only** (see `templates/skin-override.sql`):
   ```sql
   select incleng..config_set('U', 'S', 'xslt_sheet',
     'virt://WS.WS.SYS_DAV_RES.RES_FULL_PATH.RES_CONTENT:/DAV/VAD/inclusion-engine/skin/passthrough/xslt/PostProcess.xslt');
   ```
5. **Deploy** the replacement:
   ```
   curl -k -u user:pass -T replacement.html "https://host{webdav_base}content/index.html"
   ```
   (mTLS variant: `--cert bundle.p12:pass --cert-type P12`; delegation: add `-H "On-Behalf-Of: <webid>"`.)
6. **Flush once** (config changed in step 4): `select incleng..config_flush_cache();`
7. **Verify**:
   - `U` renders with exactly one masthead/nav/footer;
   - `<title>` is the replacement's, not the old page's (proves cache refreshed);
   - external assets (Google Fonts, Bootstrap CDN, `https://www.openlinksw.com/skin/matrix/css/style.css`, etc.) return 200 from the live origin;
   - one other page on the site (e.g. `/download` or any `content/*.html`) still renders with the normal site skin — proves the override stayed URL-scoped.

## Rollback

```sql
select incleng..config_unset('U', 'S', 'xslt_sheet');
select incleng..config_flush_cache();
```
plus WebDAV PUT of the backed-up `index.html.pre-YYYYMMDD` back to `content/index.html`.

## Stopping Points

- No isql/WebDAV credentials → deliver the validated bundle: classified sources, per-site SQL, curl commands, verification checklist. State plainly that live deployment is blocked on access.
- Public-site go-live → requires explicit per-site user confirmation even when credentials are available.
