# Datasets

The showcases run against these graphs. Ids are the ones `vap_query.py --explore` and `vap_link.py build --ds/--src`
take. States were checked on 2026-10-17, 2026-10-18 and 2026-10-19; run a query to see the state now.

## RDF Views on demo.openlinksw.com

RDF Views work over any ODBC- or JDBC-accessible DBMS. These are the examples the showcases use.

| Id | Source DBMS | Named graph | Ontology | Anonymous SPARQL | State |
|---|---|---|---|---|---|
| `northwind` | native Virtuoso SQL tables (`Demo.demo`) | `http://demo.openlinksw.com/Northwind#` (also `http://demo.openlinksw.com/demo#`) | `http://demo.openlinksw.com/schemas/Northwind/` | yes | working; the Customers quad map returns no rows |
| `sqlserver` | Microsoft SQL Server, attached as `"sqlserver"."northwind".*` | `http://demo.openlinksw.com/northwind-sqlserver#` | `http://demo.openlinksw.com/schemas/northwind-sqlserver/` | yes | intermittent `SR172: Transaction deadlocked`, mostly on aggregates; a retry usually answers |
| `postgres` | PostgreSQL, through the JDBC data source `postgres_jdbc_mt` (OpenLink Multi-Tier) | `http://demo.openlinksw.com/postgres_postgres_jdbc_mt_codex_20260403#` | `http://demo.openlinksw.com/schemas/postgres_postgres_jdbc_mt_codex_20260403/` | yes (2026-10-19) | working (2026-10-19): SQL on `\"postgres\".\"postgres_jdbc_mt\".\"clients\"`, SPASQL and SPARQL answer (18 entity types); on 2026-10-17 it failed with `VD052 … Specified driver could not be loaded` |
| `databricks` | Databricks (bakehouse sample), attached over ODBC as `databricks.bakehouse.*`; mapped with R2RML (`urn:databricks:bakehouse:r2rml`) | `http://demo.openlinksw.com/databricks-bakehouse-r2rml#` | `http://www.databricks.com/bakehouse#` | yes | working (2026-10-19): 3,333 transactions, 300 customers, 204 reviews, 48 franchises, 27 suppliers; SQL and SPARQL revenue by city agree |
| `snowflake` | ScaleKG: eleven native Virtuoso SQL tables (`ScaleKG.kidehen.*`, 76 synthetic rows) modelling a graph-database estate fed by warehouse sources (Snowflake, Databricks, BigQuery), from the Neo4j Scale AI meshup post; it stands in for the Snowflake system of record Neo4j Virtual Graph reads, and is not a Snowflake connection | `http://demo.openlinksw.com/ScaleKG#` | `http://demo.openlinksw.com/schemas/ScaleKG/` | yes | working (2026-10-19): SQL 3, SPASQL 4 and 5, SPARQL 9/4/3/3/19 rows; the explore query must omit the `rdfs:label` OPTIONAL (`noLabel`), which otherwise returns no rows. The earlier Snowflake TPC-H view (`snowflake_with_keys#`, DSN `snowflake_jdbc`) failed with a missing JDBC driver and was replaced |
| `csv` | CSV files attached as tables | `urn:demo.csv:northwind:data` | `http://demo.openlinksw.com/schemas/csv_northwind/` | yes | working |

Notes:

- The RDF Views have no `rdfs:label`, so the explore query's `sampleLabel` is empty for them. Widening the label to
  `schema:name` or `foaf:name` on `Northwind#` fails with `SQ070` (no SELECT on the helper view
  `Demo.demo.northwind__Total`), so the explore query keeps `rdfs:label` only.
- SQL and SPASQL against these databases need a signed-in session (demo / demo or vdb / vdb).
- The published SQL Server dashboard query (seven-column GROUP BY) fails with `SQ142`; the catalog's
  `ss-sparql-top-customers` is the working variant.
- On `databricks`, the explore query's `rdfs:label` OPTIONAL drops `CustomerReview` (204 rows, no label) and the
  server returns an empty last row; `db-sparql-entity-types` counts all five classes.
- The Oracle HR view (`urn:oracle:hr:kg-demo-3#`, DSN `mt_ora18`, failing with `ORA-28001` on 2026-10-19) was
  dropped from the app on 2026-10-20 at the user's request. Other Oracle and Databricks views on demo (`http://demo.openlinksw.com/OracleHR#`, `oracle_hr_kg#`,
  `databricks-schemaorg#`, `databricks-wanderbricks-r2rml#` and others) are not in the catalog.

## Generated ontologies on demo.openlinksw.com

Generating an RDF View also generates its ontology. Checked on 2026-10-18:

| Ontology | Generated from | What is in it |
|---|---|---|
| `http://demo.openlinksw.com/schemas/Northwind/` | native Virtuoso SQL tables (`Demo.demo`) | 8 classes labelled with their tables (`Demo.demo.Orders` …), 94 properties with domain and range; foreign keys as object properties (`has_categories`, labelled "Relation to Demo.demo.Categories"); `Customers` ⊑ `foaf:Organization`, `Employees` ⊑ `foaf:Person` |
| `http://demo.openlinksw.com/schemas/northwind-sqlserver/` | Microsoft SQL Server | 9 classes labelled `sqlserver.northwind.*` |
| `http://demo.openlinksw.com/schemas/csv_northwind/` | CSV files | `customers` ⊑ `foaf:Organization`, `employees` ⊑ `foaf:Person` |

Other ontologies on the server align locally minted classes with DBpedia (`MovieKG/Movie` ⊑ `dbo:Film`) and
schema.org (`CustomerKG/Campaign` ⊑ `schema:Action`). Queries over these must not use `GRAPH ?g` with patterns that
touch the RDF Views (it fails with `SQ070` on a helper view); name the graphs, or leave the graph out. The
`urn:rdfs:subclass:subproperty:inference:rules` rule set does not cover the CSV alignment on demo, so the
cross-source example applies `rdfs:subClassOf` in the query itself.

## Sponger graphs on URIBurner

The Sponger stores what it reads in a graph named by the source URL. Anonymous queries read the graph it already
holds; fetching or refreshing (`DEFINE get:soft "replace"`) needs a URIBurner sign-in.

| Id | Source | What the graph holds |
|---|---|---|
| `techmeme` | `https://www.techmeme.com/feed.xml` | 15 `schema:DataFeedItem` stories with titles, dates and links; named entities linked to DBpedia with relevance scores and abstracts (about 2,300 triples) |
| `github` | `https://github.com/OpenLinkSoftware/ai-agent-skills` | page metadata, extracted entity mentions and annotations, load provenance (23 types) |

`vap_query.py --sponge URL` works for any URL: it shows the type profile when URIBurner holds the graph, otherwise it
says so and gives the sign-in re-sponge link.

## Endpoints

| Name | URL | Notes |
|---|---|---|
| demo | `https://demo.openlinksw.com/sparql` | anonymous SPARQL; CORS reflects the origin |
| ub | `https://linkeddata.uriburner.com/sparql` | anonymous SPARQL over held graphs; `get:soft "replace"` is refused anonymously |
| ubAuth | `https://linkeddata.uriburner.com/sparql-auth/` | signed in; for sponging |
| XMLA | `https://demo.openlinksw.com/XMLA` | SOAP; reached through the SPASQL Query Builder; anonymous Execute is refused |
| OPAL | `https://linkeddata.uriburner.com/chat/`, `wss://linkeddata.uriburner.com/ws/chat` | agent catalog at `/.well-known/agent.json`; MCP at `/chat/mcp/messages` and `/chat/mcp/sse` |
