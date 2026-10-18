# App link format

A SPARQL Faceted Browser link is the app URL followed by a fragment:

```
{app-url}#s={base64url(JSON state)}[&cfg={base64url(JSON cfg)}]
```

- **base64url** is base64 of the UTF-8 JSON with `+` → `-` and `/` → `_`, and no `=` padding. It matches the app's
  `b64e` / `b64d`.
- The fragment never reaches a server. The whole view lives in the browser, so any static host can serve the app.
- `fct_state.py` is the only supported way to write these links. This file describes them so that a decoded link can
  be read and reasoned about.

## `s`: the view

```json
{
  "ep": "https://dbpedia.org/sparql",
  "nav": {
    "nodes": [ NODE, ... ],
    "focus": 0,
    "view": "entities",
    "off": 0,
    "vp": null,
    "ent": null,
    "pg": {}
  }
}
```

| Field | Meaning |
|---|---|
| `ep` | The SPARQL endpoint the app connects to |
| `nodes` | The trail: a chain of sets. Each set after the first is reached by a pivot from the one before it |
| `focus` | Index of the set the view shows (0-based; −1 when there is no set, e.g. a describe-only link) |
| `view` | Which tab is open: `entities` (members), `values` (values of `vp`, or "Distinct (Count)" when `vp` is null), `map` (members of the focused set that have a location, coloured by type), `describe` (the entity `ent`), or `sparql` (the generated queries) |
| `pg.map` | Map-tab options: `lim` (1000, 3000, 10000 or 25000 features; beyond it members are grouped by area and the map follows the view), `by` (property IRI to colour by; empty = type), `view` (true = re-query for the visible area), `layers` (class IRIs drawn as extra layers), `lf` (false = do not apply the focused set's value filters to the layers; default true), `shape` (`lines` or `points` for members that join two located things; default auto) |
| `vp` | `{ "p": IRI, "dir": "out" \| "in" }`: the property whose values the values tab lists |
| `ent` | The IRI shown on the describe tab |
| `off`, `pg` | Paging state. Links built by the skill start at the first page |
| `allLangs`, `raw`, `liveCounts` | App-internal toggles that may appear in links the app itself writes. Leave them as they are |

### NODE: one set

```json
{ "via": null | { "p": IRI, "dir": "out" | "in" }, "text": "", "scope": "label" | "any", "conds": [ COND, ... ] }
```

- `via`: how this set is reached from the previous one.
  - `out`: the values of `p` on the previous set's members.
  - `in`: the things whose `p` points at the previous set's members.
- `text`: free-text match.
  - `scope: "label"` searches the label properties: rdfs:label, skos:prefLabel, schema:name, foaf:name, dcterms:title and dc:title.
  - `scope: "any"` searches any literal.

### COND: one filter on a set

| Shape | Meaning |
|---|---|
| `{ "t": "class", "iri": IRI, "neg": 0\|1 }` | Has (or lacks) this type. The type property is `rdf:type`, or `wdt:P31` on Wikidata |
| `{ "t": "pv", "p": IRI, "dir": "out"\|"in", "v": TERM, "neg": 0\|1 }` | Has (or lacks) this property value. With `dir: "in"`, `v` points at the member |
| `{ "t": "pv", "p": IRI, "dir": "out"\|"in", "v": null, "vs": [TERM, …], "neg": 0\|1 }` | Has any of these values (OR). With `neg: 1`, has none of them. A value list for `p` ignores this filter, so the other values stay available to add |
| `{ "t": "pv", "p": IRI, "dir": "out", "v": null, "neg": 0 }` | Has any value for `p` |
| `{ "t": "pv", "p": IRI, "dir": "out", "v": null, "lo": "...", "hi": "...", "dt": IRI? }` | Value of `p` lies in the range; `""` leaves an end open |
| `{ "t": "is", "v": TERM }` | The set is exactly this entity |

**TERM** follows the SPARQL 1.1 JSON results shape:
- an IRI: `{ "type": "uri", "value": IRI }`;
- a literal: `{ "type": "literal", "value": "...", "xml:lang"?: "en", "datatype"?: IRI }`.

## `cfg`: link-scoped settings (optional)

```json
{ "lang": "de" }
```

`lang` is the literal language the view should use: for labels, for describe values, and for Wikidata text search.

- **Precedence:** it overrides the viewer's Settings and browser language for that tab only.
- **Persistence:** it is never saved, and it is dropped when the viewer applies Settings.
- **Validation:** the tag must look like a language tag (`^[a-z]{2,3}(-[a-z0-9]{1,8})*$`); otherwise it is ignored.
- **Other keys:** these are ignored.
- **Older builds:** an app build without `&cfg=` support opens the view in the viewer's own language
  (`fct_state.py check-app` reports this).

## Examples

```bash
python3 scripts/fct_state.py build --ep https://dbpedia.org/sparql --type dbo:Film --pv dbo:director=dbr:Christopher_Nolan --json
python3 scripts/fct_state.py decode "<link>" --json
```
