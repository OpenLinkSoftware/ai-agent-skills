# From requests to trails

A trail is one or more sets. Filters attach to the most recent set, and `--pivot` starts a new set. Resolve every
name to an IRI with a query first, and never guess one.

## The general recipe

1. **Find the anchor:** `fct_query.py --text "name" [--type T] --limit 5`, then pick the right IRI.
2. **Say what kind of thing:** `--type T`. If unsure, run `--what types` on a text match to see the candidates.
3. **Add constraints:** `--pv P=V`, `--range P LO HI`, `--has P`, `--not-…`. If the property is unknown, run
   `--what props` on the current set.
4. **Move along a relation:** `--pivot P` for the values of P, or `--pivot-in P` for the things pointing in through P.
5. **Choose the view:** members (default), `--values-of P` for a distribution, or `--describe IRI` for one entity.

## DBpedia (default endpoint)

| Request | Options |
|---|---|
| films directed by Christopher Nolan | `--type dbo:Film --pv dbo:director=dbr:Christopher_Nolan` |
| …starring Michael Caine | `… --pv dbo:starring=dbr:Michael_Caine` |
| the actors in those films | `… --pivot dbo:starring` |
| …born in London | `… --pivot dbo:starring --pv dbo:birthPlace=dbr:London` |
| settlements in Nigeria | `--type dbo:Settlement --pv dbo:country=dbr:Nigeria` |
| …by state | `… --values-of dbo:subdivision` |
| people named Einstein | `--text Einstein --type dbo:Person` |
| cities with 1–5 million people | `--type dbo:City --range dbo:populationTotal 1000000 5000000` |
| tell me about Benin City | `--describe dbr:Benin_City` |

## Wikidata (`--ep https://query.wikidata.org/sparql`)

Types use `wdt:P31` automatically, so `--type wd:Q…` means "instance of".

| Request | Options |
|---|---|
| Ada Lovelace | `--text "Ada Lovelace"` (EntitySearch; the person is `wd:Q7259`) |
| describe Ada Lovelace | `--describe wd:Q7259` |
| humans (Q5) with a given property value | `--type wd:Q5 --pv wdt:P…=wd:Q…` (look up the P and Q ids with `--what props` / `--text`) |

## URIBurner (`--ep https://linkeddata.uriburner.com/sparql`)

| Request | Options |
|---|---|
| how-to guides | `--type schema:HowTo` |
| FAQ questions | `--type schema:Question` |
| software applications | `--type schema:SoftwareApplication` |
| things mentioning "Glossary" | `--text Glossary` |

URIBurner holds `schema:` types under both `http://schema.org/` (most of the data) and `https://schema.org/`.
`schema:` expands to the http form; to reach the https form, use the full IRI, e.g.
`--type https://schema.org/HowTo`.

## Words → options

| Words | Option |
|---|---|
| "named", "called", "about", "mentioning" | `--text` (`--any-literal` for "anywhere in the text") |
| "that are", "kind of", "type" | `--type` |
| "by", "in", "from", "with", "directed by", "born in" | `--pv` with the matching property |
| "not", "except", "excluding" | `--not-type`, `--not-pv` |
| "that have a…", "with any…" | `--has` |
| "between", "over", "under", "after", "before" | `--range` (`''` for an open end) |
| "their…", "the … of those" | `--pivot` |
| "what links to…", "who cites…" | `--pivot-in` |
| "how many" | `--what count` |
| "what kinds", "which types" | `--what types` |
| "which properties", "what do we know about them" | `--what props` |
| "broken down by", "distribution", "top … by" | `--values-of` |
