# Query templates

`fct_query.py` generates these queries. They match the app's generator, so the rows in chat are the rows the app
shows (parity was checked on 2026-10-15 for members, labels and values against the app itself). Run any command with
`--show-query` to see the exact text it sent.

## The WHERE body (`whereBody`)

Each set *i* of the trail binds `?s{i+1}`. Its patterns are added in this order, most selective first:

1. **Identity:** `VALUES ?sN { <iri> }`
2. **Text:** depends on the engine (see below)
3. **Pivot join from the previous set:**
   - `?s{N-1} <p> ?sN .` for `out`
   - `?sN <p> ?s{N-1} .` for `in`
4. **Positive filters:**
   - type: `?sN <typeProp> <C> .`
   - value: `?sN <p> <v> .` for `out`, or `<v> <p> ?sN .` for `in`
   - has a value or a range: `?sN <p> ?vK . FILTER (?vK >= lo && ?vK <= hi)`
5. **Filler:** `?sN ?anyp ?anyo .`, only when a set has no other pattern
6. **Negations:** `FILTER NOT EXISTS { … }`

### Text matching by engine

| Engine | Pattern |
|---|---|
| Virtuoso | `?sN ?txtpN ?txtN . ?txtN bif:contains '"word*" AND "word*"' . FILTER (?txtpN IN (<label props>))`. The IN-list stands in for a property-path alternation because URIBurner's SPARQL-FED proxy rewrites paths. Words of 4+ letters get a `*` prefix wildcard; at most 12 words are used |
| Generic SPARQL 1.1 | `?sN (<label props>) ?txtN . FILTER (isLiteral (?txtN) && CONTAINS (LCASE (STR (?txtN)), "text"))` |
| Wikidata | `SERVICE wikibase:mwapi { … "EntitySearch" … mwapi:search "text" ; mwapi:language "<lang>" . ?sN wikibase:apiOutputItem mwapi:item . }` |

## The views

| `--what` | Query shape |
|---|---|
| `members` | Virtuoso: `SELECT ?sF WHERE {…} GROUP BY ?sF ORDER BY DESC (<LONG::IRI_RANK> (?sF)) LIMIT n`. Others: `SELECT DISTINCT ?sF … LIMIT n` |
| `count` | `SELECT (COUNT (DISTINCT ?sF) AS ?n)` |
| `types` | `SELECT ?c (COUNT (DISTINCT ?sF) AS ?n) WHERE {… ?sF <typeProp> ?c .} GROUP BY ?c ORDER BY DESC (?n)` |
| `props` / `props-in` | The same, over `?sF ?p ?o` / `?o ?p ?sF` |
| `values` | `SELECT ?v (COUNT (DISTINCT ?sF) AS ?n) WHERE {… ?sF <p> ?v .} GROUP BY ?v ORDER BY DESC (?n)` |
| `distinct` | FCT "Distinct (Count)": `SELECT ?sF (COUNT (*) AS ?n) WHERE { { SELECT DISTINCT ?s1 … ?sN WHERE {…} } } GROUP BY ?sF ORDER BY DESC (?n)` |
| `overview` | `SELECT ?type (SAMPLE (?s1) AS ?sample) (COUNT (?s1) AS ?n) WHERE { ?s1 <typeProp> ?type . FILTER (!isBlank (?s1) && !isBlank (?type)) } GROUP BY ?type ORDER BY DESC (?n)` |
| `describe` | Outgoing then incoming statements, ordered by predicate (see below) |

Here `F` is the focused set and `typeProp` is `rdf:type`, or `wdt:P31` on Wikidata (override with `--type-prop`).

### Describe

**Plain form**, used when de-duplication is off:

```
{ <e> ?p ?o . BIND ("out" AS ?dir) } UNION { ?o ?p <e> . BIND ("in" AS ?dir) }
```

**Folded form**, used when de-duplication is on (by default on Virtuoso only; set it with `--dedupe auto|on|off`):
- **Annotation-property literals** are folded to one `SAMPLE()` value per property, with a count. Annotation
  properties are the rdfs/skos/dc/dcterms/schema/foaf label, comment, name and description terms, plus any property
  the data declares `owl:AnnotationProperty`.
- **Other literals** keep every value.
- **Language:** both kinds keep only values in the preferred language or untagged.

## Engine behaviour and fallbacks

| Situation | What happens |
|---|---|
| Engine detection | A host matching `wikidata.org` is treated as Wikidata. Otherwise a `bif:length` probe identifies Virtuoso; anything else is generic |
| Virtuoso Anytime | The request sends `timeout=<ms>` (capped at 30 s). An `X-SQL-State: S1TAT` reply is flagged PARTIAL |
| `IRI_RANK` missing (SR185) | `members` re-runs unranked |
| Sorted-results cap (SR353) | Re-runs without the final ORDER BY, so the endpoint's own order is used |
| Cost-estimate refusal (42000, "estimated execution time") on `types`/`props` | Re-runs as a count-free `DISTINCT` list |
| Folded describe rejected | Re-runs as the plain describe |
| HTTP 502 / 503 / 504 | One retry after 3 s |
| SPARQL XML instead of JSON | Parsed (Wikidata does this) |

## Labels

Entity labels come from the same label properties, filtered to the preferred language or untagged. The best
candidate is picked in this order:
1. an exact language match;
2. a language-prefix match;
3. an untagged label;
4. otherwise the first candidate.

Wikidata property IRIs take their label from `wd:P…`. Display follows the label → CURIE → raw IRI rule.
