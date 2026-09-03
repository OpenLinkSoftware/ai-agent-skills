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

**Directives work in WebDAV-authored pages too, not just skin templates.** A page injected with `data-osdi-content` can mark the places where live data belongs, and everything inside such an element is treated as template markup — so a repeat row uses `data-osdi-text` exactly as it would in the bundle. This is what lets an author keep a hand-written page — its form markup, its page-scoped CSS, its bespoke layout — without either rewriting it as a skin template or restating data the graph already holds.

`data-osdi-content` is the one directive not honoured inside authored content: it means "insert the authored body", and acting on it while already copying that body recurses forever.

Use it to kill duplication rather than to smuggle layout into content. The case that motivated it: a contact page restating the office addresses, phone and fax numbers that `site.ttl` already held as `schema:Place` entities and the footer already rendered from — the company's own details with two sources of truth, in two languages, changed twice or not at all.

Judgement about *what* to move: an address, a price, a phone number, a product list is content and belongs in the graph. A form is UI structure — modelling eight inputs as triples buys nothing, and its page-scoped CSS would have to move into the skin, which is a CSS change and so defeats the reason for moving it.

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

## Verify Against a Static Control

Deploy the hand-written source as plain static files at its own endpoint — no engine, no skin, no SPARQL — and compare the rendered site against it page for page. It costs one collection and one vdir, and it is the only check that answers "does the RDF-driven site actually reproduce the design", as opposed to "does it render without erroring".

Two rules make the comparison mean something:

- **Keep the control current.** If the design source has been revised since it was packaged, run the control through the same copy transformations the generated site gets, reusing the same function rather than restating it. A stale control turns every editorial change into a false positive on the most-looked-at page, which is exactly where a real regression would hide.
- **Expect a short, enumerated difference list, and know each entry.** Regions the design never had (a chat widget added as a composite region) and whitespace between elements the composer emits adjacently will differ legitimately. Anything else is a finding.

Compare *rendered visible text and link targets*, not bytes — and beware your own comparison script. A crude tag-to-space substitution reports `<span>City</span>, <span>Region</span>` as `City , Region` and invents a difference that does not exist on the page.

---

## Deploying to an Engine Without Composite Support

`skin_manifest` is read inside `incleng..transform`. On an instance running a stock engine it is an unread config value, and adding the composite block means redefining a procedure every other site on that instance renders through — not something to do casually on a shared or staging box.

There is a second front end for exactly this case. It is selected with the ordinary **`xslt_sheet`** parameter that every engine build already has, and it sources the three trees itself:

| | Composite engine | Stock engine |
|---|---|---|
| front end | `skin/composite/xslt/PostProcess.xslt` | `skin/composite-doc/xslt/PostProcess.xslt` |
| trees module | `osdi-trees.xslt` (params from `transform`) | `osdi-trees-doc.xslt` (`document()`) |
| selected by | `skin_manifest` | `xslt_sheet` |
| directive expander | `osdi-compose.xslt` | **same file** |
| page scaffold | `osdi-page.xslt` | **same file** |

Only the tree sourcing differs, so a page composed either way comes out of identical code.

**What makes it possible.** Three Virtuoso XPath facilities, each verified before relying on it: `document('virt://WS.WS.SYS_DAV_RES.RES_FULL_PATH.RES_CONTENT:/DAV/…')` reads a DAV resource; `document('http://host/sparql/?query=…&format=application/sparql-results+xml')` returns a result set — **note the trailing slash**, since `/sparql` issues a 301 and `document()` does not follow redirects; and `document-literal(string, cache_uri)` parses an assembled string into a node-set, which is Virtuoso's stand-in for `exsl:node-set` (that one is absent). Give `document-literal` a **per-page** `cache_uri` or every page after the first is composed from the first page's data.

**Compile the bundle first.** The theme and the template bundle do not vary per request, so `infrastructure-tests/composite/build_compiled.py` writes `compiled/skintheme.xml`, `compiled/skintemplate.xml` and `compiled/datasources.xml` into the bundle at deploy time. Queries are stored **already percent-encoded**, with `__SLUG__` and `__URLENC__` left as substitution tokens — XSLT 1.0 has no URL-encode function, and both tokens survive encoding untouched so the stylesheet only ever splices URL-safe text into URL-safe text. `--widget-base` retargets an absolute asset path that differs per host.

**Each site needs a shim.** The five deployment bindings — `skinbase`, `sparqlbase`, `datasetparams`, `sitebase`, `regions_off` — must be `xsl:variable` in the **principal** stylesheet, which then `xsl:include`s the front end. That is forced by the two non-conformances in the Gotchas below, not a style choice.

`datasetparams` is the **already-encoded dataset clause**, not a graph IRI: `default-graph-uri=<encoded>` for a site whose triples are in one graph, or that parameter repeated once per graph for a site whose RDF is one LDP resource per document.

**Cost.** One HTTP round trip to the SPARQL endpoint per declared data source per render. With the page cache broken (below), that is per *request*: a 22-source skin measured ~1.5s against ~0.15s for a legacy page on the same instance.

---

## Where the Site's RDF Lives

`site_graph` names the graph a skin's SPARQL is scoped to. How the triples get there is deployment configuration, and there are two arrangements worth knowing.

**One graph for the site.** Load every Turtle document into one named graph with `TTLP`. Simplest, and a content change is: edit the file, re-upload it, re-run the loader, flush.

**One graph per document, via an LDP Basic Container.** Give the collection holding the Turtle the WebDAV property

```
LDP = ldp:BasicContainer
```

and Virtuoso treats each RDF document in it as an `ldp:RDFSource`: it loads on upload, and **the graph IRI is the document's own HTTP URL**. That is LDP's identity contract, not a naming convention — the resource you `PUT`, the resource you `GET` and the graph you query have to be the same thing, or dereferencing and querying would disagree about what the document denotes.

There is then no loader step. **Uploading is the load.** A content change is one `PUT` of one Turtle document — no HTML, no CSS, no template, no stylesheet recompile, no `TTLP`. Each document is separately addressable, fetchable and replaceable, and the container keeps `ldp:contains`, `posix:size` and `posix:mtime` in a graph named after the collection, so the document list is live queryable data rather than a directory listing.

Set the property with `PROPPATCH` (`<LDP xmlns="">ldp:BasicContainer</LDP>`), before uploading anything — a document already sitting in a plain collection is not retro-imported.

**The one preparation the documents need:** absolute IRIs for any custom ontology terms. LDP resolves relative IRIs against the resource's own URL, which is right for instance data — `<#page>` becomes `…/oracle.ttl#page`, distinct per document, free of charge. But a relative `@prefix : <../ontology.ttl#>` resolves the same way, making your *predicates* hostname- and path-specific: the same content deployed to another host would use different predicates. Keep instance IRIs relative if you like; make the ontology prefix absolute.

**Addressing many graphs at once.** Repeat `default-graph-uri` once per graph. That is SPARQL 1.1 Protocol dataset construction, so the merge is the standard's behaviour, not a server feature. A graph group is the obvious alternative and is **not reliable** — on one 8.3 instance `RDF_GRAPH_GROUP_CREATE`/`_INS` report success, the membership table shows every member, and queries against the group return zero rows over both isql and HTTP, while the identical construction works on another. Cost of the repeated parameter is URL length: 16 graphs plus a 4KB query is a 6.4KB URL, which Virtuoso serves without complaint.

**Not the same as the RDFImport DET**, which also produces per-document graphs and is easy to reach for by mistake. RDFImport names graphs `urn:dav:{path}`, resolves relative IRIs against a malformed `http:/…` base (one slash, silently), and **appends on PUT** rather than replacing — so an edited re-upload leaves old and new values both live. LDP does none of those. Use RDFImport only where LDP is not available.

---

## Page Bodies From a VSP Script

A page body does not have to come from a template or from WebDAV content. It can be generated by a classic Virtuoso Server Page — `<?vsp ?>` code interleaved with markup, running SPARQL itself — which is how OpenLink's own production UDA driver pages work: one script serving many pages, the variable captured from the URL by a rewrite rule and passed as a parameter.

This stays **inside** the engine and the skin, not beside them. End the script with:

```
incleng..vsp_transform(lines, invoked_url, 0);
```

That hands the emitted body to `incleng..transform()`, which applies the site's configured skin. Set the page's route to **`layout "default"`** so the composer injects that body through `data-osdi-content`. Output is then indistinguishable from a template-composed page.

Reach for this when a body genuinely needs *code* rather than *data* — branching, computation, or an existing VSP being carried over. It composes with either RDF arrangement.

**Give each variant its own routing data.** `oplsite:layout` decides which template composes a page: a template-rendered variant needs `"driver"` (or whatever the layout is called), a VSP-bodied one needs `"default"`. One shared `routing.ttl` cannot be both — pointing several sites at one copy silently collapses one variant into another, with no error. Give the VSP site its own `rdf/` collection, its own named graph, and its own `routing.ttl`; copy every other Turtle document verbatim. Content, assets and the skin bundle are safely shared.

**Never scope data on `layout`.** Layout is a rendering choice and changes when you change *how* a page is built. A footer link scoped `onlyOnLayout "driver"` silently selected the wrong variant — dropping an anchor from nine pages — the moment those pages moved to a VSP. Introduce an explicit `oplsite:pageKind` and scope on that: what kind of page it is does not change when the rendering method does.

### Six silent failure modes

None of these produces a useful error; several produce no error at all.

1. **Rewrite-rule list order is not honoured.** A general rule `/site/([^?]*)\.html` also matches `/site/drivers/x.html` and beats a more specific rule placed *first* in the list. Make the patterns **non-overlapping** — `[^/?]*` restricts the general rule to a single path segment. The specific rule appears never to fire; removing the general rule proves it does.
2. **An unanchored root rule swallows everything.** `/site/` matches as a prefix and rewrites every non-`.html` URL to the home page. Anchor it: `/site/$`.
3. **A `.vsp` executes only at the vdir root.** The identical file one directory down is served as *source*, whatever its permissions say.
4. **A `.vsp` executes only when owned by `dav`.** Owned by anyone else it is also served as source. A WebDAV `PUT` resets **both** owner and execute bits, so every redeploy must restore them — a deploy script that omits this works once and then silently regresses.
5. **Never upload a `.vsp` through isql.** isql treats `$` in a string literal as a variable sigil and mangles regex end-anchors, failing to compile several lines later with an error pointing at unrelated markup. Use WebDAV.
6. **`skin_manifest` is inert on an engine without composite support.** The site falls back to a legacy skin — legacy nav, legacy footer — and nothing says why. Select the skin with `xslt_sheet` and a shim (see *Deploying to an Engine Without Composite Support*).

Two more inside the script itself: `exec()` reports success as **integer `0`**, not the SQLSTATE string `'00000'`, so comparing against string literals makes every successful query look like an error; and VSP's `<?=expr?>` **escapes on output**, so pre-escaping in your own code yields `&amp;amp;`.


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

**Virtuoso's XSLT is not conformant on two points that matter for module layout.** Both were found by probe, not by reading:

- **Import precedence does not apply to `xsl:param`.** Where the spec says an importing stylesheet's binding wins, Virtuoso keeps the *imported* one. `xsl:variable` does override correctly.
- **A variable reference resolves against its own module's bindings**, not the highest-precedence binding in the stylesheet. So a variable defined in an imported module and *referenced* there keeps seeing its own definition even when an importing stylesheet rebinds the name.

Together these mean **you cannot override a composer's variable from above by importing it.** `xsl:include` — a flat textual merge — does work, and works through a chain: a name bound in the principal stylesheet is visible to a module two levels down. That is why tree sourcing is a swappable *included* module (`osdi-trees.xslt` / `osdi-trees-doc.xslt`) rather than something an importing front end overrides.

**Entity references in attribute values are expanded twice.** `string-length('&amp;amp;')` returns **1**, not 5 — the parser resolves `&amp;amp;` to `&amp;` and then to `&`. Any escape written as a literal silently becomes a no-op, and a tree assembled from those values fails to parse on the first value containing an ampersand (`Entity reference expected after '&' character`). Build the replacement by concatenation instead — `concat($AMP, 'amp;')` where `$AMP` is `'&amp;'` — because the plain-text tail has no entity syntax for the second expansion to consume.

**`staleall()` only invalidates the skins the engine knows about.** A stylesheet outside the registered skin collections stays compiled in Virtuoso's cache across edits, so a fix appears to have no effect. Call `xslt_stale('virt://…:/DAV/…/your.xslt')` on each file by name, then `config_flush_cache()`.

**The engine's page cache never hits for a WebDAV-backed page.** `incleng..cache.mtime` is timezoneless (`curutcdatetime()`) while `WS.WS.SYS_DAV_RES.RES_MOD_TIME` is timezoned, so the hit predicate `mtime > modtime` in `cached_transform` raises `DT013: Mixed timezoned and timezoneless arguments` — which the enclosing `declare exit handler for sqlstate '*'` swallows into a cache miss. Every such page re-renders on every request; `use_count` stays `0` for every site. Reproduced on two independent 8.3 instances. Legacy skins hide it because they are cheap to render, but a skin doing per-request work pays it in full on every hit. **Do not benchmark a skin assuming the cache is helping you.**

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
