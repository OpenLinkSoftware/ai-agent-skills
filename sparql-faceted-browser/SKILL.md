---
name: sparql-faceted-browser
description: Natural-language faceted search and browsing over any SPARQL endpoint, with the SPARQL Faceted Browser web app (an FCT-style single-page app) summoned on demand at the exact view the conversation reached. Answers in chat with live SPARQL, and opens or links the app when exploring, narrowing, pivoting or scanning large sets is better done visually; reads pasted app links back into the conversation. Trigger on "browse", "explore", "facet", "drill down", "narrow to", "pivot to", "show me all", "what types/properties", "describe <entity>", "open this in the faceted browser", a pasted faceted-browser link, or any natural-language question over DBpedia, Wikidata, URIBurner, UniProt or another SPARQL endpoint where the answer may need a browsable view. Default app instance is URIBurner's; another instance is used when the user names its URL.
---

# SPARQL Faceted Browser Skill

Natural language is the interface. The SPARQL Faceted Browser app is a view the conversation calls up when a
picture beats a paragraph: a big set to scan, facets to narrow by, a pivot to follow. Everything the app can show is
addressable by a link, so the skill can open it on the exact view, and read a pasted link back into the conversation.

Two scripts carry the contract. Use them; never hand-write an app link or improvise the query shapes.

| Script | Does |
|---|---|
| `scripts/fct_state.py` | Builds, edits and decodes app links (`build`, `edit`, `decode`), resolves the app instance (`app`, `check-app`) |
| `scripts/fct_query.py` | Runs the same SPARQL the app runs for a view and prints rows (Markdown by default) **plus the link to that view** |

Both accept the same left-to-right trail options (`--text`, `--type`, `--pv`, `--pivot`, `--values-of`, `--describe`,
…; see `python3 scripts/fct_state.py --help`). Worked examples for every interaction mode are in
`examples/interaction-modalities.md`; read it the first time the skill is used in a session.

---

## 1. Which app instance

The app can live at any URL. Resolution order (first match wins):

1. **The user names one** in the conversation: "use the browser at https://…", "open it on my instance https://…",
   "my faceted browser is at https://…". Pass it as `--app URL` on every call for the rest of the session.
2. **`FCT_APP_URL`** environment variable, when set.
3. **Default:** URIBurner's instance,
   `https://linkeddata.uriburner.com/DAV/demos/daas/sparql-faceted-browser-claude_opus_5_5.html`.

The first time a non-default instance is named, verify it before linking to it:

```bash
python3 scripts/fct_state.py check-app https://host/path/app.html
```

`check-app` confirms the page is a SPARQL Faceted Browser that understands `#s=` (view state) and `&cfg=` (link
language). If it is not, say so and offer the default instance; if it is an older build without `&cfg=`, links still
open but in the viewer's own language — mention it when a language was requested. A pasted link already names its
instance: `edit` and `--link` keep it unless `--app` overrides.

## 2. Interaction modes — stay in chat or bring in the app

Decide per turn. The goal is the least effort for the user: a sentence when a sentence answers it, the app when the
user needs to look around.

| The user… | Mode | What to do |
|---|---|---|
| asks a factual question with a short answer | **Answer** | `fct_query.py` → answer in prose; link the entity labels; offer the view link in one line |
| asks for a list that fits in chat (≲ 25 rows) | **List + link** | `fct_query.py` → Markdown table, then "Open this view" link |
| wants to explore, browse, scan "all", compare or narrow a large set; or the count is large | **Summon the app** | `fct_query.py --what count` to size it, short summary in chat, then open the view (§3) |
| refines: "only the ones…", "narrow to…", "exclude…", "now their birthplaces" | **Refine** | `fct_state.py edit <last link> …` (or rebuild) → answer + new link; same trail, one more step |
| asks what kinds of things / which properties a set has | **Facets** | `fct_query.py --what types` / `props` → table; link opens the same set so the facet panel is live |
| asks to map a set, or where things are ("show on a map", "with the lines", "plus the tunnels") | **Map** | build the trail, then `--view map`; `--map-layer C` per extra class, `--map-by P` to colour; large sets open grouped by area and fill in as the viewer zooms |
| asks about one entity | **Describe** | `fct_query.py --describe IRI` → summarize the key facts; link opens the description |
| pastes an app link | **Read back** | `fct_state.py decode LINK` → say what the view holds; `fct_query.py --link LINK` → answer from it; continue refining with `edit` |
| asks for another language | **Language** | add `--lang xx` (labels and the link's `&cfg=` language) |
| names another app instance | **Instance** | `check-app`, then `--app URL` from then on (§1) |

Escalate to the app, even unasked, when any of these hold: the set has more than ~50 members; the user's next step is
likely to be several narrowing moves; the answer is a distribution (types, values with counts) the user will want to
click through. Do not open the app for a one-line fact.

## 3. Bringing in the app

- **A host with a built-in browser** (for example the Claude desktop app's browser pane): open the link there so the
  view appears beside the conversation, then keep talking about what it shows.
- **Anywhere else:** give the link as a Markdown link with a short label — `[Open in SPARQL Faceted Browser](…)` —
  never as raw text in the middle of prose.
- The link is printed by the script (`Open this view: …`, or `link` in `--format json`). Copy it verbatim; never edit,
  shorten or reconstruct it. A link that has to change gets regenerated with `fct_state.py edit`.

## 4. From a request to a trail

The app's model is FCT's query tree, flattened into a chain of sets joined by pivots. Map the request onto it:

| Request fragment | Option |
|---|---|
| a name or phrase ("Einstein", "machine learning") | `--text "…"` (labels; add `--any-literal` for any text, or `--vector` to match by meaning on a Virtuoso with a vector index) |
| a kind of thing ("films", "cities", "proteins") | `--type CURIE/IRI` (`dbo:Film`, `wd:Q11424` via `--type wd:Q11424` on Wikidata, …) |
| "directed by Nolan", "in Nigeria" | `--pv P=V` (`--pv dbo:director=dbr:Christopher_Nolan`) |
| "not …" | `--not-type`, `--not-pv` |
| "that have a …" | `--has P` |
| "between 1 and 5 million", "after 1990" | `--range P LO HI` (`''` for an open end) |
| "their birthplaces", "the actors in them" | `--pivot P` (values of P); "things that cite them" → `--pivot-in P` |
| "how are they distributed by country" | `--values-of P` |
| "tell me about X" | `--describe IRI` |

Resolve names to IRIs before filtering on them: find the entity with `fct_query.py --text "name" --limit 5` (and
`--type` when ambiguous), confirm the right one, then use its IRI. Property and class IRIs come from the facets
(`--what props` / `--what types`) when the vocabulary is unfamiliar — never guess an IRI. More mappings, per endpoint,
are in `references/nl-to-trail.md`.

## 5. Endpoints and engines

Default endpoint: URIBurner (https://linkeddata.uriburner.com/sparql), in the app and the scripts. Use `--ep URL`
for any other (the DBpedia examples pass `--ep https://dbpedia.org/sparql`); the presets the app ships with are listed in
`references/endpoints.md`. The engine is detected the way the app does it, and the queries follow:

- **Virtuoso** — `bif:contains` text search, members ranked by `IRI_RANK`, **Anytime** queries (partial results at
  the time budget: say so when the output is flagged PARTIAL), annotation literals folded with `SAMPLE()` in
  descriptions.
- **Generic SPARQL 1.1** — `CONTAINS()` text search over label properties, plain `DISTINCT`, no Anytime, no folding
  (descriptions are still limited to the preferred language; `--all-langs` lifts that on any engine).
- **Wikidata** — EntitySearch for text, `wdt:P31` as the type property.

The fallbacks the app uses are built in (no `IRI_RANK` → unranked; sorted-results cap → unsorted; cost-estimate
refusal on a facet → list without counts; gateway 502/503/504 → one retry). On a timeout, offer to retry rather than
dumping the error.

## 6. Answer style

- Entity labels are the hyperlinks, pointing at the entity IRIs; when there is no label show a CURIE, and only then
  the raw IRI (the scripts' Markdown output already does this).
- Literal language: the user's language when known (`--lang`), else English; the same `--lang` goes into the link.
- Give counts with thousands separators; state partial (Anytime) results as partial.
- End an answer that has a browsable view with one link line, not a paragraph about the app.

## 7. Rules

1. Every app link comes from `fct_state.py` or `fct_query.py`. Never type, edit or truncate one by hand.
2. Every IRI in a filter comes from a query result, a pasted link, or the user. Never guess an IRI.
3. Default to URIBurner's app instance; switch only when the user names another (or `FCT_APP_URL` is set), and
   verify a newly named instance with `check-app` first.
4. Bring in the app when exploring beats reading (§2); otherwise answer in chat.
5. Run the scripts with Python 3 and `curl` available; they need network access to the endpoint (and, for
   `check-app`, to the app URL).

## Files

- `scripts/fct_state.py`, `scripts/fct_query.py` — the two tools above.
- `examples/interaction-modalities.md` — one worked example per interaction mode.
- `references/state-schema.md` — the `#s=` / `&cfg=` link format.
- `references/query-templates.md` — the SPARQL each view runs, per engine.
- `references/nl-to-trail.md` — more request-to-trail mappings, per endpoint.
- `references/endpoints.md` — preset endpoints and their engines.
- `assets/sparql-faceted-browser.html` — the app itself, for self-hosting (serve it anywhere, then use `--app`).
