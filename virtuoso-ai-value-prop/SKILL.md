---
name: virtuoso-ai-value-prop
description: Make the case for Virtuoso in conversation, with proof that runs live. Answers questions about what Virtuoso does for data and AI (RDF Views over any ODBC- or JDBC-accessible DBMS, each row's hyperlink as a cross-platform super-key, SQL over XMLA, SPASQL and SPARQL over the same tables, the Sponger turning web pages into graphs, faceted browsing, OPAL agents loosely coupled with Data Spaces) by running the matching showcase query against demo.openlinksw.com or URIBurner, hyperlinking every entity in the answer, and summoning the Virtuoso Data Spaces app at the exact view when a picture beats a paragraph. Trigger on "why Virtuoso", "Virtuoso value proposition", "show me RDF Views", "query SQL Server / PostgreSQL as a graph", "what is SPASQL", "SQL over XMLA", "super-key", "data virtualization without copying", "sponge this page", "explore the Northwind graph", "ask an OPAL agent", "Virtuoso for AI agents", "Data Spaces", or a pasted Virtuoso Data Spaces app link.
---

# Virtuoso AI Value Proposition Skill

The conversation is the interface. The **Virtuoso Data Spaces** app is the proof the conversation calls up: a page of
live showcases (RDF Views, Sponger, faceted browsing, OPAL agents) that opens on the exact example, dataset or agent
the conversation reached. Every claim the skill makes should come with something the user can click and see run.

Two scripts carry the contract. Use them; never hand-write an app link or retype a showcase query.

| Script | Does |
|---|---|
| `scripts/vap_query.py` | Runs a showcase query live (`--ex`, `--explore`, `--sponge`, `--sparql`) and prints rows for chat, with entity links, **plus the app link to that view** and the endpoint / Query Builder links |
| `scripts/vap_link.py` | Builds and decodes app links (`build`, `decode`), entity describe links (`describe`), SPASQL Query Builder links (`qb`), endpoint links (`endpoint`), lists the catalog and profiles (`list`), checks an app instance (`check-app`) and the catalog (`check-catalog`) |
| `scripts/vap_deploy_check.py` | Tests, from a target site's origin, every service a profile uses, and after upload the app and its Turtle |

Both read `references/catalog.json`, which is exported from the app itself (`node scripts/build_catalog.mjs`), so the
skill and the app always show the same queries. Worked examples for every interaction mode are in
`examples/interaction-modalities.md`; read it the first time the skill is used in a session.

---

## 1. Which instance profile, and which app instance

**Profile.** Every host the app and the scripts use comes from an instance profile (the `vap-config` block in the
app; `references/deployment.md` explains the roles). `uriburner` is the default; `www` serves the app from
www.openlinksw.com. Pick one with `--profile NAME` or `VAP_PROFILE` (the app takes `?profile=NAME`). Switch only when
the user names an instance or a profile; `vap_link.py list profiles` shows them.

**App URL** (first match wins):

1. **The user names one** ("use the copy at https://…"): pass `--app URL` for the rest of the session, after
   `python3 scripts/vap_link.py check-app URL` confirms it is this app with deep-link support.
2. **`VAP_APP_URL`** environment variable, when set.
3. **The profile's `app` URL.** For `uriburner`: `https://linkeddata.uriburner.com/DAV/demos/daas/virtuoso-ai-value-prop.html`.
   A profile with no `app` yet (for example `www` before deployment) makes the scripts stop and ask for `--app`.

Run `check-app` on the default once per session before linking to it. If it fails (for example HTTP 404 because the
app has not been uploaded there), say so, offer to serve `assets/virtuoso-ai-value-prop.html` from another location,
and use `--app` with that URL. Never link to an instance that failed `check-app`.

## 2. Interaction modes

Decide per turn. Lead with the claim, then the evidence, then one link.

| The user… | Mode | What to do |
|---|---|---|
| asks why Virtuoso, or what it does for data and AI | **Pitch** | 3–5 sentences from `references/talking-points.md`, each claim backed by one live example (`vap_query.py --ex …`) and its app link |
| asks how a capability works ("what is SPASQL?", "what is an RDF View?") | **Explain + prove** | two or three sentences, then run the matching example and show a few rows; link the example in the app |
| asks to see a database as a graph ("query SQL Server as a graph") | **Showcase** | `vap_query.py --ex <sparql example>`, table in chat, then the app link with `run=1`; mention the SQL and SPASQL twins with their Query Builder links |
| asks about ontologies, schemas or vocabularies ("does Virtuoso generate an ontology?", "can I use schema.org/FOAF?") | **Ontology** | run `onto-nw-classes` or `onto-ss-classes` to show the generated ontology, then `onto-shared-alignments` and `onto-cross-source-people` to show reuse with shared ontologies; link the Ontologies page (`--ex … --run` or `--section ontology-overview`) |
| asks about SQL or SPASQL specifically | **Signed-in showcase** | `vap_query.py --ex <sql/spasql example>`; give the Query Builder link **and** the sign-in notice; never claim you ran it |
| asks what is in a dataset | **Explore** | `vap_query.py --explore <ds>`; types table, then the app link and two or three faceted-browser links for the main types |
| gives a web page or feed | **Sponge** | `vap_query.py --sponge URL`; if URIBurner already holds the graph show its type profile, else give the sign-in re-sponge link |
| wants to talk to an agent | **Agent** | `vap_link.py build --agent KEY --ask "…"` (add `--send` only when the user asked to send it); explain guest vs sign-in (§6) |
| wants the whole picture, or to present it | **Summon the app** | the home link, or `--section` for one part (`how-it-works`, `why-virtuoso`, `access-control`, …) |
| pastes an app link | **Read back** | `vap_link.py decode LINK`; say what it shows, run the matching query, continue from there |

Escalate to the app, even unasked, when: the answer is a table the user will want to sort or rerun; the user is
evaluating Virtuoso for a team (the app is shareable); or the next step is the OPAL chat. Do not open the app for a
one-line fact.

## 3. Bringing in the app

- **A host with a built-in browser** (for example the Claude desktop app's browser pane): open the link there so the
  view appears beside the conversation.
- **Anywhere else:** a Markdown link with a short label, `[Open this example in the app](…)`, never raw text mid-prose.
- Copy links verbatim from the script output. A link that must change is regenerated with `vap_link.py build`.

## 4. Entity hyperlinks in answers

Every entity in a reply is a hyperlink, using the link the scripts print:

- **demo.openlinksw.com RDF View entities:** `https://demo.openlinksw.com/describe/?uri={IRI}&graph={named graph}`,
  both percent-encoded, with the graph of the query that produced the row (`vap_link.py describe IRI --graph G`).
  Without `&graph=` the description is not scoped to the RDF View. When a query names several graphs, the scripts
  leave `&graph=` off rather than attach the wrong one.
- **Everything else** (Sponger graphs, DBpedia): `https://linkeddata.uriburner.com/describe/?url={IRI}`.
- Products and tools named in prose link to their home pages (Virtuoso, OPAL, URIBurner), not to describe pages.

## 5. How to say it

The narrative rules from `references/talking-points.md`, in short:

- **Scope:** RDF Views work over **any ODBC- or JDBC-accessible DBMS**. Microsoft SQL Server, PostgreSQL,
  Databricks and native Virtuoso SQL tables (plus a synthetic Snowflake-style estate, ScaleKG) are the **examples the showcases use**, never the limits of the capability.
- **The key idea, said once:** Virtuoso gives every row its own **hyperlink, which works as a cross-platform
  super-key** (a key that keeps its meaning outside its own database). Do not restate it in a second sentence.
- **No copying:** SPARQL over an RDF View is translated to SQL against the source tables at query time.
- **Ontologies:** generating an RDF View also generates its ontology (a class per table, a typed property per column,
  a link per foreign key), on the fly, for any ODBC- or JDBC-accessible DBMS; aligning those classes with shared
  ontologies (FOAF, schema.org, DBpedia) is what lets one question reach every source. Say "generated", not
  "hand-written"; show the alignment, do not assert it.
- **Agents:** an OPAL agent answers from a query you can inspect. Use operational verbs for AI systems (decipher,
  interpret, process), never understand, think, know or believe.
- Plain, specific, factual sentences; numbers from live runs, with the date when it matters; no superlatives.

## 6. Access, sign-in and status

- **Anonymous:** SPARQL on demo.openlinksw.com and on graphs URIBurner already holds.
- **Signed in on demo.openlinksw.com:** SQL over XMLA and SPASQL, through the SPASQL Query Builder. Every SQL or
  SPASQL answer carries the notice printed by `vap_query.py`: user name **demo**, password **demo** (or vdb / vdb);
  the link presets the demo account for the query; the instance is protected by ABAC ACLs.
- **Signed in on URIBurner:** sponging a new or stale URL (`DEFINE get:soft "replace"` via `/sparql-auth/`), and
  OPAL answers in URIBurner's own chat UI. The app's chat panel behaves like the live widget on
  virtuoso.openlinksw.com and www.openlinksw.com: `auth.js`'s `AuthClient` carries that site's public widget key and is
  handed to `new Opal(...)`; there is no separate sign-in in the panel.
- **Known states** (`references/datasets.md`): the SQL Server view intermittently fails with `SR172: Transaction
  deadlocked` (retry once; the scripts do); the PostgreSQL view answered again on 2026-10-19
  (it had failed with `VD052 … driver could not be loaded`). The Databricks view (R2RML) answers.
  When a live query fails, show the error the script printed and keep going with another example; never present
  stale numbers as live. A `502 Bad Gateway` (or the app's "Could not reach …") means the endpoint itself is down:
  say so, offer the app link to try later, and switch to the other endpoint's examples (URIBurner Sponger graphs when
  demo.openlinksw.com is down, and the reverse).

## 7. Deploying to another instance, and the RDF complement

- The app ships with `assets/virtuoso-ai-value-prop.ttl`, generated from the same catalog: capabilities, the claims
  and the live example behind each (`schema:Claim` → `schema:isBasedOn`), datasets as named graphs with their state,
  every showcase query (`schema:SoftwareSourceCode`, with `schema:conditionsOfAccess` for SQL and SPASQL) and its deep
  link, agents and prompts, FAQ, sections, and the instance profiles as `schema:EntryPoint` URL templates. Deploy it
  next to the HTML; its IRIs are relative, so it resolves wherever it is served. When the user asks what the app
  claims or demonstrates, the Turtle is the machine-readable answer: query it rather than paraphrasing.
- When the user wants the app on another instance (for example www), follow `references/deployment.md`: run
  `vap_deploy_check.py --profile NAME --origin https://host` first, set the profile's `app`, regenerate, upload both
  files with explicit content types (after the user approves the upload and supplies credentials), then run the check
  again with `--app`.

## 8. Rules

1. Every app link comes from `vap_link.py` or `vap_query.py`. Never type, edit or truncate one by hand.
2. Every query comes from the catalog (`--ex`, `--explore`, `--sponge`) or is written for the user and run with
   `--sparql`; numbers in an answer come from a run in this conversation.
3. SQL and SPASQL are never run by the skill and never reported as run: give the Query Builder link and the notice.
4. Default to URIBurner's app instance only after `check-app` passes; otherwise use an instance the user names.
5. Entity links follow §4; the describe link for demo.openlinksw.com always carries `&graph=`.
6. After changing the app in `assets/` or the talking points, run `node scripts/build_catalog.mjs`,
   `python3 scripts/build_ttl.py` and `python3 scripts/vap_link.py check-catalog`, then repackage the ZIP.
7. Never upload to an instance without the user's approval; never put credentials in a URL or a file.
8. Run the scripts with Python 3.8+ and `curl`; they need network access to demo.openlinksw.com and
   linkeddata.uriburner.com.

## Files

- `scripts/vap_query.py`, `scripts/vap_link.py`, `scripts/vap_deploy_check.py`: the tools above.
  `scripts/build_catalog.mjs` (Node 18+) and `scripts/build_ttl.py`: regenerate the catalog and the Turtle from the
  app (maintainers).
- `references/catalog.json`: datasets, examples, Sponger examples, explore datasets, agents, prompts, sections.
- `references/datasets.md`: what each dataset is, its graph, its access and its known state.
- `references/link-format.md`: the app's deep-link format and the describe, Query Builder and endpoint links.
- `references/deployment.md`: roles and profiles, the www worked case, any other instance, common failures.
- `references/talking-points.md`: the value proposition, claim by claim, with the example that proves each one.
- `examples/interaction-modalities.md`: one worked example per interaction mode.
- `assets/virtuoso-ai-value-prop.html`: the app itself; `assets/virtuoso-ai-value-prop.ttl`: its RDF complement.
  Deploy both together (see `references/deployment.md`).
