# OSDI Composite Skins

A composite skin is a **loosely coupled bundle of three independently authored artifacts** — a theme (CSS/JS/fonts), a set of plain-XHTML templates, and a set of SPARQL bindings resolved against a named graph at render time. A manifest declares all three, and it is the only place they meet.

This is the alternative to a legacy skin, where navigation markup, asset paths and page layout are all fused inside one hand-written `PostProcess.xslt` per skin — which is why site structure is duplicated across skins (`skin/responsive/xslt/masthead.xslt` is 347 lines of literal menu, restated again in `navbar-left.xslt` and again in `skin/openlink/xslt/navbar.xslt`), why swapping a stylesheet means editing XSLT, and why chrome can only be taken all-or-nothing.

**Legacy skins are unaffected.** A site with no `skin_manifest` set behaves exactly as before.

---

## Bundle Layout

```
/DAV/VAD/opl-skins/{skin}/
  skin.ttl                    the manifest — the entire coupling surface
  template/{layout}.html      whole-page layouts
  template/region/{name}.html reusable fragments (nav, footer, …)
  css/  js/  images/          the theme
```

There is **no XSLT in a composite skin bundle.** One shared, generic composer serves every composite skin:

- `/DAV/VAD/inclusion-engine/skin/composite/xslt/PostProcess.xslt` — entry point
- `/DAV/VAD/inclusion-engine/skin/common/xslt/osdi-compose.xslt` — directive expander

---

## Manifest Vocabulary (`osdi:`)

Namespace `http://www.openlinksw.com/ontology/osdi#`, defined in `inclusion-engine/common/osdi-skin-ontology.ttl`.

| Term | Purpose |
|---|---|
| `osdi:Skin` | The manifest subject, conventionally `<>` |
| `osdi:assetBase` | URL prefix for the bundle's own assets. **Absolute** (`/skin-foo/`) is used as-is; **relative** (`assets/`) resolves against each page's own base, which is what a static export needs |
| `osdi:asset` → `osdi:kind` `osdi:href` `osdi:external` `osdi:crossorigin` `osdi:position` | One stylesheet / script / icon / preconnect. `kind` ∈ {stylesheet, script, icon, preconnect}. `external=true` means do not prefix with `assetBase`. **`osdi:position` is required** — head order is significant and a SPARQL result set is unordered |
| `osdi:template` → `osdi:name` `osdi:file` | A whole-page layout, selected per URL by the route data (below) |
| `osdi:region` → `osdi:name` `osdi:file` | A reusable fragment, referenced by `data-osdi-region`. Regions are the unit of chrome suppression |
| `osdi:dataSource` → `osdi:name` `osdi:sparql` `osdi:scalar` | A named SELECT whose bindings become an addressable result set. `scalar=true` marks a single-row set addressed as `set.field` |
| `osdi:prefixes` | PREFIX preamble prepended to every `osdi:sparql`. Also the skin's declaration of what it expects of a site graph |
| `osdi:markdown` | Enables the engine's client-side Markdown block rendering |
| `osdi:lang` | `<html lang>` |

Two substitution tokens are expanded in every `osdi:sparql` before execution:

- `<{URL}>` — the request URL as an IRI (the engine's existing convention, cf. `search_url`, `fct_url`)
- `{SLUG}` — the page slug, i.e. the request path relative to the site base minus `.html`, empty meaning `index`

---

## Template Directive Vocabulary

Directives are attributes in no namespace, so a template stays a valid, browser-openable HTML document before composition.

| Directive | Effect |
|---|---|
| `data-osdi-region="NAME"` | Replace this element with region template NAME |
| `data-osdi-region-from="REF"` | As above, but the region name comes from the data — a page's RDF chooses its own partial |
| `data-osdi-content` | Replace with the WebDAV source document's `<body>` children |
| `data-osdi-repeat="SET"` | Emit this element once per row of result set SET |
| `data-osdi-repeat-where="F=R"` | Restrict that repeat to rows whose field F equals reference R resolved in the enclosing row — the master/detail primitive (footer columns each iterating their own links) |
| `data-osdi-text="REF"` | Replace element content with REF's value, escaped |
| `data-osdi-html="REF"` | As above, but the value is markup |
| `data-osdi-attr-NAME="REF"` | Set attribute NAME (`data-osdi-attr-aria-label` works) |
| `data-osdi-addclass="REF"` | Append REF's value to the class list |
| `data-osdi-if="REF"` / `data-osdi-ifnot="REF"` | Drop the element when REF is empty / non-empty |
| `data-osdi-unwrap` | Emit only this element's children |

**Reference syntax.** `set.field` always resolves against that named set's first row. A bare `field` resolves against the current `data-osdi-repeat` row. Qualified refs still reach the global sets from inside a repeat, so a row template can mix row data with site-wide data freely.

**Put decisions in the query, not the template.** The current-page nav highlight, a primary-vs-ghost button class, a link's target attribute — compute them as a bound column and render with `data-osdi-addclass`. That is what keeps the template free of page logic and therefore restyleable without touching behaviour.

**Template files must be well-formed XML.** Named HTML entities are not: use numeric (`&#8212;`, not `&mdash;`). Each file may carry a leading comment; the loader strips it.

---

## Config Parameters

| Param | Scope | Meaning |
|---|---|---|
| `skin_manifest` | URL / site / global | DAV path to `skin.ttl`. **Setting this switches the site to composite rendering** and overrides `xslt_sheet` |
| `site_graph` | URL / site / global | Named graph the manifest's SPARQL is scoped to. This is what lets one skin dress several sites off different graphs |
| `regions_off` | URL / site / global | Comma-delimited region names to omit for this scope — per-page chrome suppression |

## SQL API

```sql
incleng..osdi_skin_load(manifest)                  -- parse skin.ttl into its own graph; RE-RUN AFTER EVERY MANIFEST EDIT
incleng..osdi_skin_theme(manifest)                 -- -> <skintheme>
incleng..osdi_skin_templates(manifest)             -- -> <skintemplate>
incleng..osdi_skin_data(manifest, graph, url, slug)-- -> <skindata>
incleng..osdi_skin_layout(skindata [, default])    -- layout named by the route row
incleng..osdi_url_slug(url, sitebase)              -- request path -> slug
```

The manifest is parsed into `urn:osdi:skin:{manifest-path}`, one graph per manifest resource, so two sites can use two skins — or two revisions of one skin — side by side.

---

## Deploying a Composite Skin

1. **Upload the bundle** to its DAV collection (curl per the curl-first rule).
2. **Make it publicly readable.** Files PUT over WebDAV are owned by the uploading account and are **not** world-readable; a browser fetching the stylesheet gets `401`, not `200`. Set `RES_PERMS`/`COL_PERMS` to `111101101NN` across the bundle.
3. **Give the bundle a vdir** whose lpath equals `osdi:assetBase`. Do not assume `/skin` is free — on a stock instance it resolves to *different* collections on the plain and SSL vhosts.
4. **Load the site graph** and set `site_graph`.
5. **`osdi_skin_load(manifest)`** — this is the manifest deployment step.
6. **`config_set` `skin_manifest`** at the chosen scope.
7. **`staleall()`**, not just `config_flush_cache()` — the composer is XSLT and Virtuoso caches compiled XSLT.
8. **Verify in a browser**, not only by diffing markup. See the gotchas below for what only a browser load catches.

---

## Gotchas

Each of these cost real debugging time; all are fixed in the shipped engine code, but they shape how a skin must be authored and verified.

**Virtuoso rejects `EXISTS` inside `BIND`.** rdflib accepts it, so a data source developed against the offline harness can fail outright on the server with `syntax error at EXISTS` — and because the whole data source fails, the page 500s rather than degrading. `FILTER NOT EXISTS` is best avoided for the same reason. Compute structural facts where they are already known (at build time, or when the graph is authored) and record them as triples: a `topLevel`, `hasChildren` or `coversSlug` flag costs one triple and removes the portability question entirely. This is the single most likely way a working offline skin breaks when deployed.

**Serialisation.** The composer emits `method="xml"` and guarantees no non-void element is ever emitted empty. It has to: an XML serialiser writes `<script src="x"/>`, which every browser reads as an unterminated script that swallows the rest of the document — and `<div/>`, `<a/>`, `<span/>` are mis-parsed too. `method="xhtml"` is *not* a portable fix: libxslt builds vary in accepting it, and a rejected output method **silently falls back to xml while still exiting 0**. Never treat a generator's exit code as proof it rendered correctly.

**Entities in RDF literals.** A literal reaches the page either escaped (`xsl:value-of`, for `<title>` and `meta content`) or raw (`disable-output-escaping`, for markup-bearing fields). `&amp;` survives only the second path and appears verbatim in the first. **Store the real character** — it is correct on both paths.

**Virtuoso re-evaluates an OPTIONAL when a FILTER references a variable bound inside it.** A nav query that wrapped its route join in `OPTIONAL` and then filtered on a variable from it had the base-path variable unbind on exactly the row being filtered, so one link lost its `../` prefix while its siblings kept theirs. Keep a join non-optional when every row genuinely has it.

**Trailing slashes.** The engine canonicalises to a trailing slash by default. A site presenting `.html` URLs must set `url_trailing_slash 0` or every request 302s.

**`.vsp` execute bits.** A dispatcher uploaded without execute permission is served as a static resource and redirects in search of a collection — a silent, confusing failure.

**Data-island placeholders.** With no statements about a page, `inline_html5md` and `inline_rdfa` emit visible placeholder prose ("This document is empty and basically useless…"). Set both to `0` unless the site graph actually describes its pages.

**`debug_level`.** Leave it set and a debug trailer renders as visible text on every page. Unset it before declaring done.

---

## Interaction with `?skin=`

`?skin=<name>` is a per-impression override, resolved before any config. Precedence, highest first:

1. **`?skin=` naming an opl-skins bundle with `xslt/PostProcess.xslt`** — an explicit *legacy* skin override wins even on a composite site. Previewing another skin on a page is the point of the parameter, and it would be useless if composite config shadowed it.
2. **`?skin=` naming a bundle with `skin.ttl`** — the same override, for a composite skin.
3. **the configured `skin_manifest`** for that URL / site / global scope.

So a composite site stays previewable under any legacy skin, and a composite skin can be previewed on a site that is not yet configured for it. Note the request URL reaches `incleng..transform` with `skin=` still on it; the parameter is stripped only for content and config resolution, so the page cache keys on it and previews do not poison the cached page.

## When to Use Which

| Situation | Approach |
|---|---|
| New site, or a site whose structure you control | Composite skin |
| One page needs its own layout on an otherwise legacy site | `regions_off` if the site is already composite; otherwise Path A/B from SKILL.md |
| Page's design derives from the live site's | Composite skin with `data-osdi-content`, or Path B |
| Existing legacy site, no appetite for migration | Leave it; nothing changes |

A composite skin does **not** face the passthrough skin's trade-off. Because its chrome is regions rather than an unconditional wrap, a page can keep its own body *and* keep canonical, feed autodiscovery, data islands and the rest.
