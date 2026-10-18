# Changelog

## 1.0.6 — 2026-10-18

- **Map tab, after the production RINF Atlas:**
  - **Grouped by area.** When more members are located than the limit, they are counted per grid cell in SPARQL
    (`GROUP BY` on the rounded coordinates) and drawn as numbered circles. All 62,352 RINF operational points open on one
    map; zooming in regroups at finer cells until the view holds no more than the limit, then draws each member.
  - **Layers.** Other classes can be added as layers from the dataset's classes (VoID or live counts) or by IRI. Each
    is located like the set, drawn under it in its own colour and grouped by area when large. The focused set's value
    filters apply to the layers by default (for example a country), as Atlas filters do.
  - **Lines between linked places.** A member with no line geometry of its own is drawn as a line when a sample of
    the set shows two links to located things on nearly every member, for example a section of line's `era:opStart`
    and `era:opEnd`; "Draw as" switches between lines and points.
  - Lines are placed by their first coordinate when the view is limited (areas still pass), so line sets fill in as
    the viewer zooms. New limit: 25,000 features.
- **Scripts:** `fct_state.py` adds `--map-layer`, `--map-layer-filters on|off`, `--map-shape` and `--map-limit 25000`.

## 1.0.5 — 2026-10-18

- **Default endpoint:** URIBurner (`linkeddata.uriburner.com/sparql`) replaces DBpedia.
  - The app opens on it unless a link names another endpoint, and lists it first in the Featured group.
  - `fct_state.py` and `fct_query.py` default to it when no `--ep` is given.
  - The DBpedia worked examples (README, `examples/`, `references/`) pass `--ep https://dbpedia.org/sparql`.
- **EU data portal preset:** new starter samples.
  - Types: Dataset, Catalog and Data Service.
  - Searches that return datasets: "air quality", "renewable energy", "Horizon 2020".
  - Entities: the CORDIS coronavirus dataset, and the Eurostat and Open Maps for Europe catalogues.
- **Unranked fallback:** when the ranked member query is refused without CORS headers, the app lists the members
  unranked instead of failing. data.europa.eu has no `IRI_RANK` and sends its error without those headers.

## 1.0.4 — 2026-10-17

- **Bundled app (`assets/`):**
  - New preset: ERA RINF (`graph.data.era.europa.eu/repositories/rinf-plus`, GraphDB), with operational points,
    sections of line and tunnels as starter types.
  - New presets on the same ERA GraphDB server: ERA vocabulary & requirements (`ERA-Onto`) and the ERA
    Organisation Code Register (`OCR-KG`), plus ERA-Lex, the EU railway legislation corpus (`era-lex`).
  - New preset: OpenLink demo server (`demo.openlinksw.com/sparql`), with Transfermarkt players, TCRD genes and NFL
    plays as starter types.
  - Labels: the batched label lookup uses `SELECT DISTINCT`. When a batch still reaches its LIMIT, the missing IRIs
    are asked again instead of being cached as unlabelled. Before this, labels copied across many graphs (the demo
    server's `rdf:type`) left entity headings showing raw IRIs.
  - Thumbnails also accept image URLs stored as plain literals.
  - DBpedia is the pinned default: opening the app without a view link always starts on DBpedia, not on the last
    endpoint used. Links still open on their own endpoint, and other Settings are still remembered.
  - Descriptions show a **Location** map (Leaflet with OpenStreetMap tiles, loaded only when needed) when the entity
    has `geo:lat`/`geo:long`, GeoSPARQL `asWKT` (directly or through `hasGeometry`; points, lines and polygons),
    Wikidata P625, `georss:point` or `schema:geo`. This follows fct-dev's map for `geosparql:asWKT`.
    The map zooms with the mouse wheel, and opens outside the app: full screen, as a standalone map page in a new
    tab, as a GeoJSON download, or in OpenStreetMap.
  - **Map tab** for the focused set, in the manner of RINF Atlas. It draws the members that have a location (points
    and lines, on a canvas), coloured by their type in the dataset's own vocabulary, with a legend. It follows the
    trail, so facets narrow it, and changing a facet keeps the map open. Members without their own geometry are
    located one link away (RINF operational points through `era:netReference`). The map shows up to 1,000, 3,000 or
    10,000 features, and offers full screen and a GeoJSON download. Descriptions use the same one-link fallback.
  - `fct_state.py --view map` builds a link that opens the Map tab.
  - **Multi-select facets (OR):** the ∨ button in a value list adds an alternative, giving for example
    "any of In country France or Germany or Italy". A property's value list ignores its own value filter, so the
    other values stay listed (selected ones are ticked) and the list stays open while you add more. Condition JSON:
    `vs: [TERM, …]`. Skill: `fct_state.py --pv-or P=V`, and `fct_query.py` uses the same semantics.
  - **Map: Colour by** a property of the set with 2–15 distinct values (for example RINF's type of operational point)
    instead of type, with a legend.
  - **Map: Limit to map view** re-queries as you pan and zoom. It reuses what the first load found (the link and the
    lat/long or WKT branch), and boxes points numerically: 2 s instead of over 45 s on RINF. Map options travel in the
    link (`pg.map`; skill: `--map-by`, `--map-limit`, `--map-in-view`).
  - New presets: Fedlex (Swiss federal law) and Legilux (Luxembourg legislation), both at `/sparqlendpoint`.
  - JOLux labelling: `jolux:title` is a label property. Works and acts take their title from
    `jolux:isRealizedBy/jolux:title`, in the preferred language when `jolux:language` names it.
  - Text search falls back to `CONTAINS` on a Virtuoso without a free-text index (checked at connect).
  - Endpoints whose gateway rejects FOAF IRIs (checked at connect) get queries without FOAF terms.
  - Header: the app's mark is now the OpenLink logo used on openlinksw.com (the minimal blue mark), embedded at 2x.
  - Footer redesign: a main tier (logo behind a hairline divider, the tagline with an accent rule, chips linking the
    sparql-faceted-browser skill and the OpenLink AI Agent Skills collection on GitHub, and a one-line note), above a
    base bar for the rights notice and copyright. On phones it stacks.
  - SPARQL tab: each query is editable and has a **Run** button (or ⌘/Ctrl+Enter) that shows results in place
    (table, ASK true/false, or the error). The endpoint's own result page is still one click away.
  - Presets: Datao (`sparql.datao.net`) removed after failing the `ASK { ?s ?p ?o }` probe (HTTP 503, re-checked on
    2026-10-17). The Italian Chamber of Deputies (`dati.camera.it`) stays: an earlier run of this release removed it
    after HTTP 502s, but it answers again (HTTP 200 on two probes).
  - The location map also reads WGS84 `geo:geometry` and direct schema.org `latitude`/`longitude`, uses plain
    triples rather than property paths (so the query survives the URIBurner proxy), and dims tiles in dark mode.
    This folds in a parallel 1.0.4 map from another working session.
- **Scripts:** `fct_state.py` adds `--pv-or`, `--view map`, `--map-by`, `--map-limit` and `--map-in-view`, plus the
  `era:` and `jolux:` prefixes. `fct_query.py` understands OR conditions (`vs`), and a property's value list ignores
  that property's own filter, as in the app.

## 1.0.3 — 2026-10-16

- **Bundled app (`assets/`):**
  - Settings gains a **Virtuoso reasoning & sponging** section, replacing the free-text rule field and the sameAs
    checkbox (old values migrate):
    - inference rule set (`DEFINE input:inference`), checked on the endpoint with one ASK per candidate; the default
      is `urn:rdfs:subclass:subproperty:inference:rules` on URIBurner and none elsewhere;
    - fct-dev's "Same As" (`input:same-as`) and IFP (`input:ifp`) modes;
    - Sponger modes (`get:soft`, `input:grab-*`), applied to entity descriptions by default.
  - A pragma the endpoint refuses is dropped for that endpoint and the query re-runs. For example, DBpedia refuses the
    Sponger with SR186.
  - `schema:jobTitle` literals are folded with `SAMPLE()` like the other annotation properties.
  - Also: a Stop control for running queries, an image viewer for thumbnails, and a top bar that never reflows.
  - DBpedia's starter samples lead with Benin City.
- **Examples:** the Describe and Language examples use `dbr:Benin_City` instead of `dbr:Lagos`, with output re-run
  from `fct_query.py`.

## 1.0.2 — 2026-10-15

- **New presets:** 11, each with start samples (types, entities, search words) checked with the app's own query
  shapes. They are listed in `references/endpoints.md`.
  - **Direct, with CORS:** Italian Chamber of Deputies, dati.gov.it, datos.gob.es, LIBRIS, Data for Humanities
    (ABES), WikiPathways, OMA, OrthoDB and 3LGM². Aragon Open Data's samples are refreshed.
  - **Through the URIBurner proxy only:** datos.bcn.cl and SIOP (Brazil). Neither sends CORS headers on https.
  - **Left out:** datos.infolobby.cl. Its certificate names `*.cplt.cl`, plain http is blocked on an https page, and
    it refuses the proxy with 403.
- **Removed preset:** Protein Ontology (`sparql.proconsortium.org`).
- **Bundled app (`assets/`):**
  - adds the new presets;
  - proxied endpoints skip the engine check, which URIBurner refuses inside `SERVICE` after 45–90 s, and use the
    generic SPARQL 1.1 profile.

## 1.0.1 — 2026-10-15

- **Describe language filter:** it no longer depends on `SAMPLE()` de-duplication.
  - Modes are now `sample` (Virtuoso default), `lang` (any other engine) and `all` (`--all-langs`).
  - The bug: on a non-Virtuoso endpoint such as QLever, `dbo:abstract` showed in 11 languages despite the English
    default.
- **Annotation properties:** `dbo:abstract` now counts as one.
- **Bundled app (`assets/`):**
  - the language filter applies on every engine, and "All values & languages" is always offered;
  - the facet column is sticky and scrolls inside itself, as in fct-dev;
  - the results pane scrolls into view when a query starts while it is off-screen;
  - the connect status names each handshake step.

## 1.0.0 — 2026-10-15

First release.

### Scripts
- `scripts/fct_state.py` builds, edits and decodes SPARQL Faceted Browser links (`#s=` view state, `&cfg=` link
  language).
  - **App instance:** `--app`, then `FCT_APP_URL`, then the URIBurner default. `check-app` verifies a named instance.
- `scripts/fct_query.py` runs the app's own query shapes for a view and prints the rows with the matching link.
  - **Queries:** members, count, type and property facets, values, Distinct (Count), overview and describe.
  - **Engines:** Virtuoso (bif:contains, IRI_RANK, Anytime, annotation `SAMPLE()` folding), generic SPARQL 1.1, and
    Wikidata (EntitySearch, wdt:P31).
  - **Fallbacks:** SR185, SR353, cost-estimate refusals, gateway errors, and SPARQL XML replies.
  - **Labels:** chosen the same way as the app (exact language, then prefix, then untagged); shown as label, then
    CURIE, then raw IRI.

### Documentation
- `SKILL.md` covers the interaction modes (answer, list + link, summon the app, refine, facets, pivot, describe,
  read back, language, another instance) and the rules for links and IRIs.
- `examples/interaction-modalities.md` has one worked example per mode, from live DBpedia runs.
- `references/` describes the link format, query templates, preset endpoints and request-to-trail mappings.

### App
- `assets/sparql-faceted-browser.html` is the app (1.0, built 2026-10-15) for self-hosting.
  - **New in this build:** `&cfg=` language links.

### Verified
- **App parity**, checked in a real browser: the same 10 members in the same order with the same labels (DBpedia,
  "Einstein" + dbo:Person, German), and the same 8 values with the same counts (actors in Nolan's films).
- **Links:** links made by the app decode and answer correctly.
- **Language:** `&cfg=` sets the app's language ("de (from this link)").
- **Instances:** `check-app` accepts the URIBurner instance and rejects a non-app URL.
