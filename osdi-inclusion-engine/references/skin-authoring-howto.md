# Authoring a New OSDI Skin

Canonical community reference (as supplied by the user — do not substitute or fabricate a different URL): https://community.openlinksw.com/t/osdi-howto-2-skins-appearance/5999

This is the process for turning a self-styled mockup into a real skin, either as a **new per-site skin** or as the **shared/per-site-layout half of a `zion`-style shared skin** (see `references/skin-commonality-assessment.md` for which to choose).

## Per-Skin Process

For each new skin (site-specific, or the shared skin plus its per-site layout include):

1. **Paste the mockup HTML into a new `PostProcess.xslt`.** Start from a copy of an existing skin's `PostProcess.xslt` (e.g. `matrix/xslt/PostProcess.xslt` in opl-skins) as the XSLT scaffold — output method, standard `<xsl:param>` list, `<xsl:include>` mechanics — and drop the mockup's markup into the `<body>` template in place of the existing masthead/content/footer structure.
2. **Strip out all the content bits.** Delete everything in the mockup that is actual homepage *content* (headline copy, feature text, testimonial text, specific links) — keep only the structural/appearance shell: the outer containers, the CSS (`<style>` blocks become the skin's own stylesheet or move to a dedicated `.css` file referenced from `<head>`), the nav/masthead markup, the footer markup.
3. **Insert the content hook at the right place.** Where the mockup's actual page content was, insert:
   ```xslt
   <xsl:apply-templates select="/something/appropriate" mode="copy"/>
   ```
   `/something/appropriate` is whatever XPath correctly targets the source document's content region once Tidy has normalized it — typically `/html/body` or `/html/body/*` (see how `matrix/xslt/PostProcess.xslt` targets `/html/body/*` mode="copy" inside its `<main>`). Get this insertion point right before moving on — it's the seam between "site chrome" (now skin-owned) and "page content" (still DAV-owned).
4. **Integrate OSDI components.** A new skin is not done until it wires in the standing engine and skin infrastructure — do not reimplement any of this:
   - From inclusion-engine `common/`: feeds (`feeds.vsp` output → `<link rel="alternate">` in `<head>`), search (`search.vsp`), sitemap, 404 handling.
   - From opl-skins `common/`: `<xsl:include href="../../common/xslt/data-islands.xslt"/>` (RDFa/SPARQL merge), `embedding.xslt` (embedded queries), `urchin*.xslt` (analytics), `opal.xslt` (OPAL widget), and the `auth/` VSP scripts if the skin exposes login/profile/cart UI.
   - Canonical link, JSON-LD `WebSite`/`SearchAction` block, and any icons/keywords templates the site currently relies on (check the currently-live skin's `PostProcess.xslt` for what it emits in `<head>` — replicate the ones still wanted, drop the ones the new design supersedes).
5. **Replace `content/index.html` (or `content/{page}.html`) in DAV with just the content bits.** Once appearance has moved into the skin, the DAV source document shrinks back down to a plain content fragment — no more inline nav/header/footer, no more duplicated Bootstrap/font/framework `<link>`/`<script>` tags the skin now supplies itself. This is the opposite direction of a passthrough deployment: the page gets *simpler*, not the skin looser.
6. **Install and switch.** Package the new skin under the appropriate VAD path (or a new one), install/copy it into DAV, then point `xslt_sheet` at it — per-site scope for a per-site skin, or global/shared for the `zion` variant plus per-site `<xsl:include href="{site}/xslt/layout.xslt"/>` for the varying parts. Run `incleng..staleall()` after installing or changing any skin XSLT.
7. **Verify** the same way as any skin change: single chrome, correct title/canonical/feeds, resolvable assets, and — critically for a new skin — check the non-homepage page types identified during elicitation (Contact form, Customer Snapshot, etc.) still render sensibly under the new appearance, since the mockup had no opinion on them.

## `zion` Shared-Skin Variant

If the commonality assessment favors one shared skin:

- `zion/xslt/PostProcess.xslt` holds everything common: OSDI component integration (step 4 above), the content-hook insertion (step 3), shared CSS/JS libraries, and structural includes.
- Each site gets its own `zion/{site}/xslt/layout.xslt`, included from the shared `PostProcess.xslt`:
  ```xslt
  <xsl:include href="uda/xslt/layout.xslt"/>
  ```
  or resolved dynamically by `$site` if the include target is parameterized — prefer a static include per deployed instance over a runtime `<xsl:choose>` over `$site`, per the low-conditionality principle.
- `layout.xslt` carries only what's genuinely site-specific: masthead branding, color tokens, nav copy/links, footer columns. Anything identical across sites stays in the shared `PostProcess.xslt`, not duplicated into every `layout.xslt`.
