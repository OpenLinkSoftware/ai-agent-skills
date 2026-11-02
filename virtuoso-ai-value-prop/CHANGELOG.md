# Changelog

## 1.3.3 — 2026-10-20

- **Oracle HR tab removed for now**, with its query constants, Explore dataset, faceted-browser links, Sources entry
  and JSON-LD `isBasedOn` link; Oracle is no longer named among the showcased databases (it stays in the logo strip of
  connectable technologies).

## 1.3.2 — 2026-10-19

- **OPAL chat uses the live widget's authentication.** As on virtuoso.openlinksw.com and www.openlinksw.com, `auth.js`'s
  `AuthClient` carries the site's public widget key and is handed to `new Opal(...)` with the same options. Removed the
  URIBurner OpenID Connect sign-in bar, the sign-in and LLM-key cards, the redirect handler, the Solid OIDC bundle and
  the `signInIssuer` / `signInBundle` profile keys (and their deploy checks).
- **Chat agents are the live widgets' agents, each with its own key.** Each site's key in `apikey.js` is scoped to its
  own agent: Virtuoso Support Agent with `virtuosoApiKey` (virtuoso.openlinksw.com) and ODBC & JDBC Support Agent with
  `udaApiKey` (uda.openlinksw.com), both with `Demo.demo.execute_spasql_query`. Data Twingler and the OPML/RSS reader
  answered "Authentication required" with those keys and were removed from the chat; www.openlinksw.com's agent
  (`www-support-assistant-config`) does not exist on URIBurner and is not offered. The profile `widgetKey` key is gone.
- Chat replies render the `<sub>` and other attribute-free formatting tags the live widget shows (it uses `html:true`).
- **Snowflake tab → ScaleKG.** The Snowflake TPC-H examples are replaced by the ScaleKG demo from the Neo4j Scale AI
  meshup post: eleven native Virtuoso tables of synthetic rows standing in for a Snowflake-style system of record. One
  SQL card (Snowflake-sourced warehouse tables), the post's two SPASQL queries (databases-per-GB rule; graph walk joined
  to `analytics_job`) and five of its SPARQL queries (three hops, databases per cluster, replication, entailment, TBox
  property hierarchy), all returning rows. Explore and faceted-browser links follow; the tab id stays `snowflake`.
  Explore datasets can set `noLabel` (catalog `exploreQueryTemplateNoLabel`), needed for ScaleKG.

## 1.3.1 — 2026-10-19

- Removed server-status and diagnostic text from the page: the status banners on the SQL Server, PostgreSQL, Snowflake
  and Oracle tabs, the Explore notes, the FAQ entry about tabs showing errors, the SQ142 remark on the SQL Server
  sales card and the check date in Sources. Data-source states stay in `references/datasets.md` for the skill.
- PostgreSQL tab: the SQL card that read the system catalog (`DB.DBA.SYS_REMOTE_TABLE`) is replaced by
  `pg-sql-clients`, a plain query against the attached table `"postgres"."postgres_jdbc_mt"."clients"`.

## 1.3.0 — 2026-10-19

- **Databricks, Snowflake and Oracle RDF Views.** Three new tabs in the RDF Views playground, with SQL over XMLA,
  SPASQL and SPARQL cards, deep links (`#/rdf-views?src=databricks|snowflake|oracle`), Explore datasets and faceted
  browser starting points for their classes.
  - **Databricks Bakehouse** (R2RML view, graph `databricks-bakehouse-r2rml#`), from the URIBurner weblog post and the
    OpenLink Community walkthrough: franchises and revenue by city in SQL, the same revenue in SPASQL and SPARQL (the
    numbers agree), entity types, top customers and the post's franchise DESCRIBE. All seven run live.
  - **Snowflake TPC-H** (graph `snowflake_with_keys#`), built from the view's quad maps on demo.openlinksw.com; no
    weblog post covers it yet. Status note: the Snowflake JDBC driver is not loaded on the server (`VD052`).
  - **Oracle HR** (graph `urn:oracle:hr:kg-demo-3#`), from the openlinksw.com weblog post; the post's employee,
    salary and type queries. Status note: the Oracle account behind DSN `mt_ora18` has expired (`ORA-28001`). The
    post's department query fails with `SQ142` and is left out.
- Prose, FAQ, the logo strip, Sources and JSON-LD `isBasedOn` name the new DBMSs and posts; one new agent prompt
  (R2RML over Databricks).
- Catalog (46 examples, 7 datasets) and Turtle (1,348 triples) rebuilt. The new datasets have no DBpedia link yet:
  dbpedia.org was down for maintenance, so the IRIs could not be confirmed.

## 1.2.0 — 2026-10-18

- **Ontology generation, with section emphasis.** New **Ontologies** page (nav, `#/ontologies`, deep links
  `#/ontologies?ex=ID&run=1`) and a home section "Your schema becomes an ontology. Shared ontologies make it travel."
  Six live examples: classes generated from the Northwind tables (8 classes, 94 properties), the generated Products
  properties and foreign-key links, the classes generated from SQL Server (9), generated classes aligned with shared
  ontologies (FOAF, schema.org, DBpedia), a FOAF question answered by the employees table, and one `foaf:Person`
  question answered by CSV files (18) and Virtuoso SQL tables (9) through the alignment. New FAQ entry, talking-point
  claim 11, Turtle capability `ontology-generation` and dataset of generated ontologies.
- Describe links: `&graph=` only when a query names exactly one graph.
- Menu: collapses to the menu button below 1100 px; "Try a live query" hides below 1320 px (six nav links).
- Deployed to URIBurner DAV (1.1.0 build; this build to be re-uploaded).

## 1.1.0 — 2026-10-18

- **Instance profiles.** The app reads every host from a `vap-config` block (`uriburner` default, `www`), selected with
  `?profile=NAME`; widget scripts, the widget key name and the sign-in bundle load per profile. The scripts take
  `--profile` / `VAP_PROFILE`; `vap_link.py list profiles` and `profile`; a profile without an app URL stops link
  building with a clear message.
- **RDF complement.** `assets/virtuoso-ai-value-prop.ttl` (generated by `scripts/build_ttl.py`): capabilities,
  `schema:Claim`s with the examples that prove them, datasets as `sd:NamedGraph`s with state, showcase queries as
  `schema:SoftwareSourceCode` with deep links and `schema:conditionsOfAccess`, agents and prompts, FAQ, sections,
  and the profiles as `schema:EntryPoint` URL templates; relative IRIs, no blank nodes, every literal tagged `@en`.
  The page links to it (`rel="alternate"` and a footer link).
- **Deployment.** `scripts/vap_deploy_check.py` tests every service a profile uses from the target site's origin, and
  after upload the app and its Turtle. `references/deployment.md` covers roles, the www worked case (pre-deployment
  check passed on 2026-10-18), any other instance, and common failures.

## 1.0.0 — 2026-10-18

First release.

- **App (`assets/virtuoso-ai-value-prop.html`):** the Virtuoso Data Spaces single-page app, styled after
  chat-data.com.
  - RDF Views playground: Virtuoso Northwind, SQL Server Northwind, PostgreSQL and CSV Northwind, each with SQL over
    XMLA and SPASQL cards (SPASQL Query Builder links with the demo account preset, sign-in notice, XMLA request) and
    editable SPARQL cards that run in the page. Result links go to `describe/?uri=…&graph=…` with the query's graph.
  - Sponger: Techmeme's RSS feed (headlines, DBpedia-linked entities, companies and people, type profile) and the
    ai-agent-skills GitHub repository; anonymous reads of held graphs, re-sponge links via `/sparql-auth/`, and a
    sponge-any-URL form.
  - Faceted Browse: the standard explore query scoped to the selected dataset's named graph, with faceted-browser
    links per type.
  - OPAL Agents: live A2A Agent Card catalog, chat panel on virtuoso.openlinksw.com's widget scripts, guest mode on the
    public widget key, **Sign in with URIBurner** (Solid OpenID Connect, DPoP) that returns to the same view and
    resends the question, a sign-in notice for "Authentication required" replies, and an LLM API-key field when the
    server asks for one (kept in sessionStorage).
  - Every section has a fragment id with a copy-link anchor and an "On this page" strip.
  - **Deep links** for the skill: `#/rdf-views?ex=ID&run=1`, `#/sponger?ex=ID&run=1`, `#/sponger?url=URL`,
    `#/explore?ds=ID`, `#/agents?agent=KEY&ask=TEXT&send=1`, and `#{section-id}`.
- **Scripts:**
  - `vap_query.py`: runs catalog examples, the explore query, Sponger profiles and ad hoc SPARQL; prints Markdown or
    JSON with describe links (with `&graph=` for demo.openlinksw.com), the app link, endpoint links, Query Builder
    links and the sign-in notice; retries a Virtuoso `SR172` deadlock once.
  - `vap_link.py`: build, decode, describe, qb, endpoint, list, check-app, check-catalog.
  - `build_catalog.mjs`: exports `references/catalog.json` from the app (Node 18+).
- **References:** catalog, datasets and their state, link format, talking points; **examples:** one per interaction
  mode.
- Known states at release: the SQL Server view intermittently fails with `SR172: Transaction deadlocked`; the
  PostgreSQL view fails with `VD052 … driver could not be loaded`.
