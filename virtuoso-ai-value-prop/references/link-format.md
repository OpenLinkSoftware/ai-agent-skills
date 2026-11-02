# Link format

All links below are produced by `scripts/vap_link.py` (or printed by `scripts/vap_query.py`). This page documents
what they mean so a pasted link can be read back; it is not a licence to write them by hand.

## The app

The app is a single HTML file with hash routing. `{app}` is the instance URL (§1 of `SKILL.md`).

| Link | Opens | Built with |
|---|---|---|
| `{app}#/` | home | `build` |
| `{app}#{section-id}` | one section, on whichever page holds it, scrolled under the header | `build --section how-it-works` |
| `{app}#/rdf-views?src={dataset}&lang={all\|sql\|spasql\|sparql}` | RDF Views on one dataset tab, filtered by language | `build --src sqlserver --lang sparql` |
| `{app}#/rdf-views?ex={id}&run=1` | the example's card, focused; `run=1` runs a SPARQL example on arrival | `build --ex nw-sparql-stock --run` |
| `{app}#/ontologies?ex={id}&run=1` | an ontology example (generated classes, alignments, shared-vocabulary queries), focused and run | `build --ex onto-cross-source-people --run` |
| `{app}#/sponger?ex={id}&run=1` | a Sponger example, focused and run | `build --ex tm-headlines --run` |
| `{app}#/sponger?url={URL}` | the "Sponge any URL" form, filled in and submitted | `build --url https://…` |
| `{app}#/explore?ds={dataset}` | Faceted Browse with the explore query run on that dataset's named graph | `build --ds csv` |
| `{app}#/agents?agent={key}&ask={text}` | the OPAL chat on that agent with the question typed in | `build --agent virtuoso-support --ask "…"` |
| `…&send=1` | as above, and the question is sent | `build --agent … --ask "…" --send` |
| `{app}#/sources` | where every example comes from | `build --view sources` |
| `{app}?profile={name}#…` | any of the above, with another instance profile for this visit | (add `?profile=` to the app URL) |
| `{app-folder}/virtuoso-ai-value-prop.ttl` | the app's RDF complement (Turtle) | deployed next to the app |

Rules the builder enforces: `--run` only with a SPARQL or Sponger `--ex` (SQL and SPASQL run in the Query Builder after
sign-in); `--send` only with `--ask`; `--section` alone. Ids come from `vap_link.py list …`.

Section ids (from `list sections`): `overview`, `four-ways`, `how-it-works`, `why-virtuoso`, `access-control`,
`questions`, `get-started`, `ontologies` (home); `rdf-views-playground`, `datasets`; `ontology-overview`,
`ontology-how`, `ontology-examples`, `ontology-make-your-own`; `sponger-overview`, `sponger-examples`,
`sponge-any-url`; `faceted-overview`, `explore-query`, `starting-points`; `opal-overview`, `how-opal-answers`,
`agent-catalog`, `questions-to-try`, `widget-usage`, `protocols`; `sources-list`.

Hosts in the links below are those of the `uriburner` profile; another profile substitutes its own (`vap_link.py
--profile NAME …` prints them).

## Entity descriptions

- demo.openlinksw.com RDF View entities:
  `https://demo.openlinksw.com/describe/?uri={IRI}&graph={GRAPH}` (both percent-encoded; the graph is the query's
  `FROM`/`GRAPH` IRI; omitted when the query names several graphs). Example, built by `vap_link.py describe … --graph …`:
  `https://demo.openlinksw.com/describe/?uri=http%3A%2F%2Fdemo.openlinksw.com%2FNorthwind%2Femployees%2FEmployeeID%2F3%23this&graph=http%3A%2F%2Fdemo.openlinksw.com%2FNorthwind%23`
- Other IRIs: `https://linkeddata.uriburner.com/describe/?url={IRI}`.

## SPASQL Query Builder (SQL over XMLA, and SPASQL)

`https://demo.openlinksw.com/spasqlqb/?permlink_e={percent-encoded JSON}` with
`{"v":1,"url":"/XMLA","dsn":"DSN=Local_Instance","uid":"demo","pwd":"demo","path":null,"tab":"exec","idx":null,"fkey":null,"ref":null,"exec":{"sql":"…"}}`.
`uid`/`pwd` preset the public demo account for the XMLA connection. The Query Builder still opens a VAL sign-in
page first: user name `demo`, password `demo` (or `vdb` / `vdb`). The abridged SalesPerformance example keeps its
post's own short link.

## SPARQL endpoint

`{endpoint}?query={percent-encoded query}&format=text%2Fx-html%2Btr` for SELECT, `text%2Fx-html-nice-turtle` for
DESCRIBE and CONSTRUCT. Endpoints: `https://demo.openlinksw.com/sparql`, `https://linkeddata.uriburner.com/sparql`,
and `https://linkeddata.uriburner.com/sparql-auth/` (signed in; used for `DEFINE get:soft "replace"`).

## Faceted browser

Links into the SPARQL Faceted Browser (`…/sparql-faceted-browser-claude_opus_5_5.html#s=…`) in the catalog were built
with the `sparql-faceted-browser` skill's `fct_state.py`. For browsing beyond these starting points, hand off to that
skill.
