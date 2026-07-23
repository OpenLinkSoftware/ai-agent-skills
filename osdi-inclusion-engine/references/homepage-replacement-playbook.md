# Playbook — Homepage Replacement into OSDI Sites

Worked scenario (2026-07): replacing the homepages of virtuoso.openlinksw.com, uda.openlinksw.com, and ps.openlinksw.com with three self-styled mockups hosted on an intranet DAV server. Generalizes to any "drop this finished HTML design in as page X" request.

## Why This Is a Skin-Authoring Decision

Analysis of the three replacement documents (`scripts/check_chrome_conflict.py`) showed:

| Document | Structure | Own chrome |
|---|---|---|
| Virtuoso revamp | Fragment (no `<html>/<body>`; `<meta>/<title>/<style>/<script>` + body markup) | `<nav class="navbar navbar-expand-lg bg-dark">`, `<footer class="bg-dark ...">` |
| UDA replacement | Fragment | `<header class="hdr"><nav>`, `<footer class="ftr">` |
| PS Ogilvy revamp | Full document (`<!doctype html>...<body>...</body>`) | `<header class="masthead">` |

All three reuse CSS from the live pages they replace, so their inline chrome **visually matches** the engine-injected chrome. Deployed unmodified under any chrome-bearing skin (legacy `openlink` or live `matrix` from the opl-skins VAD), each page would render doubled masthead/nav/footer — and because both copies look "correct", the duplication reads as a subtle glitch rather than an obvious clash.

The first-pass instinct — strip each mockup's chrome and deploy the bare content under the *current* `matrix` skin — treats this as a one-off deploy-path choice. It isn't. The mockups are homepage-only; they have no opinion on Contact forms, Customer Snapshots, or any other recurring page type these sites carry. Stripping and deploying under the unchanged skin answers "how do I get this one page live" but ducks the real question: **does this new appearance become the site's skin**, so every page benefits and future pages have somewhere to inherit from?

Fragments are fine as source content — Tidy normalizes them into full documents before XSLT. Full documents with XHTML+RDFa DOCTYPEs skip Tidy entirely.

## Commonality Assessment (this batch)

Per `references/skin-commonality-assessment.md`, a structural scan across the three mockups found:

| | Virtuoso | UDA | PS |
|---|---|---|---|
| Font | Inter | Montserrat | Inter |
| CSS custom properties | `--accent-strong`, `--accent`, `--font-body`, `--font-display`, `--font-mono`, `--rule` | `--acc`, `--bd`, `--bg`, `--border-c`, `--cloud`, `--fog`, `--ink`, `--ol-blue-lt` | `--bg-light`, `--ink`, `--muted`, `--ols-blue-dark`, `--ols-blue-medium`, `--ols-button-hover`, `--ols-check`, `--ols-cta` |
| Bootstrap | Yes | No | No |
| Nav markup | Bootstrap navbar | `btn-nav`/`hdr-nav` custom | plain `<header class="masthead">` |

**Result: not enough commonality** for a single shared `zion` skin — fonts, token vocabularies, framework choice, and nav markup all diverge with no consistent pattern. **This batch calls for three separate new skins**, one per site, via the process in `references/skin-authoring-howto.md`. (If a future mockup batch shows real overlap — same font, same token names, same framework, same nav pattern — revisit the shared-skin option.)

## Per-Site Procedure — New Skin (recommended path for this batch)

For each site (shortname `S`, homepage URL `U`, replacement source `SRC`):

1. **Confirm live values** — never trust documentation examples:
   ```sql
   select incleng..config_get(null, 'S', 'webdav_base');
   select incleng..config_get('U', 'S', 'xslt_sheet');
   ```
2. **Classify the source**: `python3 scripts/check_chrome_conflict.py SRC` (accepts URL or file; use `--insecure` for intranet self-signed TLS).
3. **Elicit non-homepage coverage**: which other page types on site `S` (Contact, Customer Snapshot, pricing, docs, …) need this new appearance before go-live, and who supplies those designs — the mockup only covers the homepage.
4. **Author the new skin** per `references/skin-authoring-howto.md`: copy an existing skin's `PostProcess.xslt` as scaffold, paste `SRC`'s markup in, strip content down to appearance + the `apply-templates mode="copy"` hook, wire in both `common/` directories (feeds/search/sitemap; auth/data-islands/embedding/analytics), install under a new VAD path (e.g. `/DAV/VAD/opl-skins/{S}/xslt/PostProcess.xslt`).
5. **Back up** the current homepage source before replacing it:
   ```
   curl -k -u user:pass -o index.html.pre-YYYYMMDD "https://host{webdav_base}content/index.html"
   ```
6. **Switch the skin** for site `S` (site-scoped, not per-URL — the whole site should move to its new skin, not just the homepage):
   ```sql
   select incleng..config_set(null, 'S', 'xslt_sheet',
     'virt://WS.WS.SYS_DAV_RES.RES_FULL_PATH.RES_CONTENT:/DAV/VAD/opl-skins/{S}/xslt/PostProcess.xslt');
   select incleng..staleall();
   ```
7. **Replace `content/index.html`** with just the stripped content fragment (no inline nav/header/footer, no duplicated Bootstrap/font `<link>`/`<script>` tags — the new skin now supplies those):
   ```
   curl -k -u user:pass -T content-only.html "https://host{webdav_base}content/index.html"
   ```
   (mTLS variant: `--cert bundle.p12:pass --cert-type P12`; delegation: add `-H "On-Behalf-Of: <webid>"`.)
8. **Verify**:
   - `U` renders with exactly one masthead/nav/footer, sourced from the new skin;
   - `<title>`, canonical, feeds links, and JSON-LD SearchAction are present (proves `common/` integration, not a bare passthrough);
   - external assets return 200 from the live origin;
   - any other existing page on `S` still renders sensibly under the new skin (a fast smoke test that the skin's content hook — `/something/appropriate` — targets the right XPath for non-homepage content too).

## Rollback

```sql
select incleng..config_set(null, 'S', 'xslt_sheet', '<previous-live-sheet>');
select incleng..staleall();
```
plus WebDAV PUT of the backed-up `index.html.pre-YYYYMMDD` back to `content/index.html`.

## Alternative — Passthrough Stopgap (not recommended as default)

If the user explicitly wants one page live immediately with no skin commitment, Path A remains available: per-URL `xslt_sheet` override to `/DAV/VAD/inclusion-engine/skin/passthrough/xslt/PostProcess.xslt`, deploy the mockup verbatim, `config_flush_cache()`. State the cost plainly before using it: the page is permanently outside the skin system, with no feeds links, canonical, JSON-LD SearchAction, analytics, OPAL widget, or path toward covering the site's other page types.

## Stopping Points

- No isql/WebDAV credentials → deliver the validated bundle: commonality assessment, per-site skin drafts, SQL, curl commands, verification checklist. State plainly that live deployment is blocked on access.
- Public-site go-live → requires explicit per-site user confirmation even when credentials are available.
