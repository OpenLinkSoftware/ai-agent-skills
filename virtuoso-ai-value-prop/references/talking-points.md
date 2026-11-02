# Talking points

The value proposition, claim by claim. Each claim names the example that proves it; run the example
(`vap_query.py --ex …`) before quoting its numbers, and link it in the app.

## Wording rules

- RDF Views work over **any ODBC- or JDBC-accessible DBMS**. SQL Server, PostgreSQL, Databricks and native Virtuoso SQL tables (plus the synthetic Snowflake-style ScaleKG estate) are
  **the examples the showcases use**.
- Say the key idea once: *Virtuoso gives every row in any ODBC- or JDBC-accessible DBMS its own hyperlink, which works
  as a cross-platform super-key.* In reader-facing prose call it a hyperlink; keep "IRI" for queries and labels.
- Plain, specific sentences with facts from live runs. No superlatives, no "seamless", no "revolutionary".
- For AI systems use operational verbs (decipher, interpret, process); never understand, think, know or believe.
- Write "a Semantic Web", never "the Semantic Web".

## The claims

| # | Claim | One-sentence version | Proof (catalog id) |
|---|---|---|---|
| 1 | Every row gets a hyperlink | Each customer, order and product gets a hyperlink that opens a page describing it, and the link keeps its meaning outside its own database. | `nw-sparql-stock`, `ss-sparql-customers` (click a row's link) |
| 2 | Any ODBC or JDBC database | Attach a DBMS over ODBC or JDBC and its tables appear inside Virtuoso, queryable in place. | `ss-sql-customers`, `ss-sql-federated-join` |
| 3 | Nothing is copied | SPARQL over an RDF View is translated to SQL and run against the source tables at that moment, so a change in the source shows in the next answer. | `ss-sparql-top-customers`, `csv-sparql-quad-maps` (the SQL table behind each predicate) |
| 4 | Three languages, one set of tables | The same rows answer SQL over XMLA, SPASQL (SPARQL inside a SQL `FROM`) and SPARQL. | `nw-sql-customers`, `nw-spasql-category-sales`, `nw-sparql-category-sales` |
| 5 | Joins by reference across systems | One SQL statement joins customers in SQL Server, orders in MySQL and employees in Virtuoso. | `ss-sql-federated-join` |
| 6 | Web pages become graphs | The Sponger reads a page or feed and stores a graph named by its URL, with entities linked to DBpedia. | `tm-headlines`, `tm-entities`, `gh-ai-agent-skills-types` |
| 7 | See before you query | The explore query lists every type in a dataset with a sample and a count, and each type opens in a faceted browser. | `--explore northwind`, `--explore csv` |
| 8 | Agents answer from queries | An OPAL agent answers by running a predefined SQL, SPARQL or SPASQL query you can inspect, so a number can be traced to its source. | `--agent virtuoso-support`, `--agent data-twingler` |
| 9 | Loose coupling | Agents hold instructions and a list of query functions, not a copy of the data, so the model, the agent or the Data Space can change independently. | the `how-opal-answers` section |
| 10 | Access stays with the data | ABAC ACLs on the server decide who may run what: anonymous SPARQL, signed-in SQL and SPASQL, signed-in sponging. | the `access-control` section |
| 11 | Ontologies are generated, then shared | Generating an RDF View also generates its ontology (a class per table, a typed property per column, a link per foreign key); aligned with FOAF, schema.org or DBpedia, it lets one question reach every source. | `onto-nw-classes`, `onto-shared-alignments`, `onto-cross-source-people` |

## A 30-second version

> Virtuoso gives every row in any ODBC- or JDBC-accessible DBMS its own hyperlink, which works as a cross-platform
> super-key. The same tables then answer SQL, SPARQL, or both at once, without being copied, and an OPAL agent can
> answer questions about them by running queries you can inspect. Here are 10 products from the Northwind tables,
> read live a moment ago: [table]. [Open this example in the app](…)
