# Interaction modes: worked examples

Each example shows what the user says, what the skill decides, the command it runs, and what the user gets back. The
commands run from the skill folder. Rows and timings come from real runs on 2026-10-18; live data changes. Long links
are shortened here with `…`; in a real answer, paste the full link the script printed.

| # | Mode | User says |
|---|---|---|
| 1 | Pitch | "Why would I use Virtuoso for AI?" |
| 2 | Explain + prove | "What is SPASQL?" |
| 3 | Showcase (and a failed live query) | "Show me SQL Server as a graph." |
| 4 | Explore | "What's in the CSV Northwind data?" |
| 5 | Sponge | "What can the Sponger do with Techmeme's feed?" |
| 6 | Agent | "Let me ask an agent what an RDF View is." |
| 7 | Summon the app / a section | "I need to show this to my team." |
| 8 | Read a pasted link back | "What does this link show? <link>" |
| 9 | Another app instance | "Use the copy at https://example-host/vap.html" |

---

## 1. Pitch

> **User:** Why would I use Virtuoso for AI?

**Skill decides:** a pitch. Three claims from `references/talking-points.md` (1, 4, 8), each backed by a live result.
It runs one example to show the tables answering as a graph.

```bash
python3 scripts/vap_query.py --ex nw-sparql-category-sales
```
```
**Sales by category**
Named graph: `http://demo.openlinksw.com/Northwind#`

8 rows · 865 ms

| categoryName | totalSales | units |
|---|---|---|
| Beverages | 267,868 | 9,532 |
| Dairy Products | 234,507 | 9,149 |
| Confections | 167,357 | 7,906 |
…
Open this example in the app: https://linkeddata.uriburner.com/DAV/demos/daas/virtuoso-ai-value-prop.html#/rdf-views?ex=nw-sparql-category-sales&run=1
Open in the SPARQL endpoint: https://demo.openlinksw.com/sparql?query=…&format=text%2Fx-html%2Btr
```

> **Answer:** Virtuoso gives every row in any ODBC- or JDBC-accessible DBMS its own hyperlink, which works as a
> cross-platform super-key. The same tables then answer SQL, SPARQL, or both at once, without being copied. Here is
> the Northwind order data, grouped by category through links rather than foreign-key columns, read live in under a
> second: Beverages 267,868, Dairy Products 234,507, Confections 167,357 … And an
> [OPAL](https://opal.openlinksw.com/) agent can answer questions about the same data by running queries you can
> inspect.
> [Open this example in the app](https://linkeddata.uriburner.com/DAV/demos/daas/virtuoso-ai-value-prop.html#/rdf-views?ex=nw-sparql-category-sales&run=1)

## 2. Explain + prove

> **User:** What is SPASQL?

**Skill decides:** two sentences of explanation, then the SPASQL twin of example 1. SPASQL runs in the Query Builder
after sign-in, so the skill does not run it; it gives the link and the sign-in notice.

```bash
python3 scripts/vap_query.py --ex nw-spasql-category-sales
```
```
**Sales by category, SPARQL inside SQL**
Named graph: `http://demo.openlinksw.com/Northwind#`

```sql
SELECT categoryName, totalSales, units
FROM (
  SPARQL
  PREFIX nw: <http://demo.openlinksw.com/schemas/Northwind/>
  SELECT ?categoryName … FROM <http://demo.openlinksw.com/Northwind#> WHERE { … }
  GROUP BY ?categoryName
  ORDER BY DESC(?totalSales)
) AS x
```

Sign in first: the Query Builder opens a sign-in page. Under "Using SQL login" use user name **demo** and password **demo** (or vdb / vdb). The link already presets the demo account for the query itself. The instance is protected by ABAC ACLs.

Open in SPASQL Query Builder: https://demo.openlinksw.com/spasqlqb/?permlink_e=…
Open this example in the app: https://linkeddata.uriburner.com/DAV/demos/daas/virtuoso-ai-value-prop.html#/rdf-views?ex=nw-spasql-category-sales
```

> **Answer:** SPASQL is SPARQL inside SQL: a SPARQL query sits in a SQL `FROM` clause and its result behaves like a
> derived table, so any SQL tool can use graph data. This one returns the same eight categories as the SPARQL query
> above. [Open in SPASQL Query Builder](https://demo.openlinksw.com/spasqlqb/?permlink_e=…). Sign in first with user
> name **demo** and password **demo** (or vdb / vdb); the instance is protected by ABAC ACLs.

## 3. Showcase, and a failed live query

> **User:** Show me SQL Server as a graph.

```bash
python3 scripts/vap_query.py --ex ss-sparql-customers --limit 5
```
```
**Customers as entities**
Named graph: `http://demo.openlinksw.com/northwind-sqlserver#`

Live query failed (HTTP 400, 798 ms): Virtuoso 40001 Error SR172: Transaction deadlocked …

Open this example in the app: https://linkeddata.uriburner.com/DAV/demos/daas/virtuoso-ai-value-prop.html#/rdf-views?ex=ss-sparql-customers&run=1
Browse SQL Server customers: https://linkeddata.uriburner.com/DAV/demos/daas/sparql-faceted-browser-claude_opus_5_5.html#s=…
```

**Skill decides:** the script already retried once. The skill says so plainly, does not reuse old numbers, and offers
the app link (which retries again when opened) and the faceted browser. When the query answers, each customer row
links to `https://demo.openlinksw.com/describe/?uri=…ALFKI%23this&graph=http%3A%2F%2Fdemo.openlinksw.com%2Fnorthwind-sqlserver%23`.

> **Answer:** The SQL Server view is answering with a transient deadlock right now (`SR172`), so I can't show live rows
> this moment; it usually answers on another try. The same view as a browsable list:
> [Browse SQL Server customers](…). [Open this example in the app](…) to run it again. Meanwhile, the federated join
> of SQL Server customers with MySQL orders is here: [Open in SPASQL Query Builder](…) (sign in as demo / demo).

## 4. Explore

> **User:** What's in the CSV Northwind data?

```bash
python3 scripts/vap_query.py --explore csv --limit 6
```
```
**Explore: CSV Northwind (RDF View over CSV files)**
Named graph: `urn:demo.csv:northwind:data`

11 rows · 433 ms

| type | sampleEntity | sampleLabel | entityCount |
|---|---|---|---|
| [demo.openlinksw.com/schemas/csv_northwind/orders](https://demo.openlinksw.com/describe/?uri=…&graph=urn%3Ademo.csv%3Anorthwind%3Adata) | […/orders/orderID/10248#this](…) |  | 1,660 |
…
Open this dataset in the app: https://linkeddata.uriburner.com/DAV/demos/daas/virtuoso-ai-value-prop.html#/explore?ds=csv
Browse orders in the faceted browser: https://linkeddata.uriburner.com/DAV/demos/daas/sparql-faceted-browser-claude_opus_5_5.html#s=…
```

> **Answer:** Eleven entity types, led by orders (1,660), order details (830), customers (182) and products (154).
> [Open this dataset in the app](…#/explore?ds=csv) · [Browse orders](…) · [Browse customers](…)

## 5. Sponge

> **User:** What can the Sponger do with Techmeme's feed?

```bash
python3 scripts/vap_query.py --ex tm-entities --limit 6
```
```
**Entities in the news, linked to DBpedia**
Named graph: `https://www.techmeme.com/feed.xml`

15 rows · 532 ms

| label | entity | relevance |
|---|---|---|
| Apple Watch | [dbpedia.org/resource/Apple_Watch](https://linkeddata.uriburner.com/describe/?url=http%3A%2F%2Fdbpedia.org%2Fresource%2FApple_Watch) | 0.91 |
| Kioxia | [dbpedia.org/resource/Kioxia](…) | 0.9 |
…
Open this example in the app: https://linkeddata.uriburner.com/DAV/demos/daas/virtuoso-ai-value-prop.html#/sponger?ex=tm-entities&run=1
Re-sponge the source (URIBurner sign-in): https://linkeddata.uriburner.com/sparql-auth/?query=DEFINE%20get%3Asoft%20%22replace%22…
```

> **Answer:** The Sponger read the feed into a graph named by its URL, turned each story into a feed item, and linked
> the companies and products it mentions to DBpedia: [Apple Watch](…), [Kioxia](…), [The Wall Street Journal](…) …
> [Open this example in the app](…). For a fresh copy, [re-sponge it](…) (needs a URIBurner sign-in).

For any other URL: `python3 scripts/vap_query.py --sponge URL` (type profile if URIBurner holds the graph, otherwise
the sign-in link).

## 6. Agent

> **User:** Let me ask an agent what an RDF View is.

```bash
python3 scripts/vap_link.py build --agent virtuoso-support --ask "What is a Virtuoso RDF View, and how does it differ from loading data into the quad store?"
```
```
https://linkeddata.uriburner.com/DAV/demos/daas/virtuoso-ai-value-prop.html#/agents?agent=virtuoso-support&ask=What%20is%20a%20Virtuoso%20RDF%20View%2C…
```

> **Answer:** [Ask the Virtuoso Support Agent](…): the chat opens with your question typed in; press Send. The panel
> connects with the live widget's key, as on virtuoso.openlinksw.com.

Add `--send` only when the user asked for the question to be sent straight away.

## 7. Summon the app, or one section

> **User:** I need to show this to my team.

```bash
python3 scripts/vap_link.py build
python3 scripts/vap_link.py build --section why-virtuoso
```
```
https://linkeddata.uriburner.com/DAV/demos/daas/virtuoso-ai-value-prop.html#/
https://linkeddata.uriburner.com/DAV/demos/daas/virtuoso-ai-value-prop.html#why-virtuoso
```

> **Answer:** [Virtuoso Data Spaces](…#/) runs every example live, so the numbers your team sees are current. Start
> with [Three facts worth knowing before you choose](…#why-virtuoso).

## 8. Read a pasted link back

> **User:** What does this link show? `…virtuoso-ai-value-prop.html#/rdf-views?ex=ss-sparql-top-customers&run=1`

```bash
python3 scripts/vap_link.py decode "<link>"
```
```
{
  "app": "https://linkeddata.uriburner.com/DAV/demos/daas/virtuoso-ai-value-prop.html",
  "view": "rdf-views",
  "ex": "ss-sparql-top-customers",
  "run": "1",
  "example": "Top customers by sales"
}
```

Then `python3 scripts/vap_query.py --ex ss-sparql-top-customers` to answer from it.

## 9. Another app instance

> **User:** Use the copy at https://example-host/vap.html

```bash
python3 scripts/vap_link.py check-app https://example-host/vap.html
```

If it passes, add `--app https://example-host/vap.html` (or set `VAP_APP_URL`) for the rest of the session. If it
fails, say why (not found, not this app, or an older build without deep links) and keep the instance that works.
