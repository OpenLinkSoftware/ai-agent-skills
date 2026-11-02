# virtuoso-ai-value-prop

Make the case for Virtuoso in conversation, with proof that runs live. The skill answers questions about what
Virtuoso does for data and AI by running the matching showcase query against demo.openlinksw.com or URIBurner,
hyperlinking every entity in the answer, and opening the **Virtuoso Data Spaces** app at the exact example, dataset
or agent when a picture beats a paragraph.

The showcases cover RDF Views over any ODBC- or JDBC-accessible DBMS (examples: Microsoft SQL Server, PostgreSQL,
Databricks and native Virtuoso SQL tables, plus a synthetic Snowflake-style estate), queried by SQL over XMLA, SPASQL and SPARQL; the Sponger turning web pages into graphs;
faceted browsing; and OPAL agents loosely coupled with Data Spaces.

## Quick start

```bash
cd virtuoso-ai-value-prop

# Run a showcase query: rows for chat, entity links, and the app link that opens and runs the same example
python3 scripts/vap_query.py --ex nw-sparql-category-sales

# What is in a dataset (explore query on its named graph), with faceted-browser links per type
python3 scripts/vap_query.py --explore northwind

# What the Sponger holds for a URL
python3 scripts/vap_query.py --sponge https://www.techmeme.com/feed.xml

# Links only
python3 scripts/vap_link.py build --ex nw-sparql-stock --run
python3 scripts/vap_link.py build --agent virtuoso-support --ask "Define the term SPASQL"
python3 scripts/vap_link.py build --section how-it-works
python3 scripts/vap_link.py qb --ex ss-sql-federated-join
python3 scripts/vap_link.py list examples
```

The scripts need Python 3.8+ and `curl`, and network access to demo.openlinksw.com and linkeddata.uriburner.com.

## Which app instance

By default, links open `https://linkeddata.uriburner.com/DAV/demos/daas/virtuoso-ai-value-prop.html`. To use another
copy (for example `assets/virtuoso-ai-value-prop.html` served from your own site), name it in the conversation, pass
`--app URL`, or set `VAP_APP_URL`. Check an instance first:

```bash
python3 scripts/vap_link.py check-app https://your-host/path/virtuoso-ai-value-prop.html
```

## Instance profiles and other deployments

Every host the app and scripts use (RDF Views data, linked data and Sponger, OPAL, widget, faceted browser, the app
itself) comes from an instance profile in the app's `vap-config` block. `uriburner` is the default; `www` serves the app
from www.openlinksw.com. Use `--profile www` (or `VAP_PROFILE=www`; in the browser, `?profile=www`).

```bash
python3 scripts/vap_link.py list profiles
python3 scripts/vap_deploy_check.py --profile www --origin https://www.openlinksw.com          # before upload
python3 scripts/vap_deploy_check.py --profile www --origin https://www.openlinksw.com --app URL # after upload
```

`references/deployment.md` walks through deploying to www (the worked case) and to any other instance.

## RDF complement

`assets/virtuoso-ai-value-prop.ttl` describes the app in RDF: capabilities, claims and the live example behind each,
datasets and their state, every showcase query with its deep link, agents, FAQ, sections and the instance profiles.
Deploy it next to the HTML (the page links to it).

## Keeping the skill and the app in step

The app in `assets/` is the source of truth. After changing it:

```bash
node scripts/build_catalog.mjs          # re-export references/catalog.json from the app
python3 scripts/build_ttl.py            # regenerate assets/virtuoso-ai-value-prop.ttl
python3 scripts/vap_link.py check-catalog
```

## Where to read more

- `SKILL.md`: when to stay in chat and when to bring in the app, how to word the value proposition, and the rules.
- `examples/interaction-modalities.md`: one worked example per interaction mode.
- `references/`: the catalog, the datasets and their state, the link format, and the talking points.
