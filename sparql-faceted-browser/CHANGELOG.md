# Changelog

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
