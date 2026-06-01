---
name: linked-data-skills
title: Linked Data Skills
description: >
  Generates Knowledge Graphs from two source types: (A) relational database objects via Virtuoso
  RDF Views, or (B) documents/text transformed to RDF using schema.org terms. PATH RDBMS — STRICT
  5-step workflow: ask local-vs-DSN, enumerate tables, resolve hostname, confirm IRI patterns,
  generate TBox+ABox+rewrite rules, verify with entity samples. PATH D — 4-step workflow: collect
  document + {page_url} + format (JSON-LD or Turtle), generate RDF via prompt template, post-
  generation review (syntax fix, additional Q&A/entity types), save to user-designated folder.
  TOOL HIERARCHY: read queries use Demo.demo.execute_spasql_query; writes use EXECUTE_SQL_SCRIPT;
  RDF generation uses chatPromptComplete.
version: 3.2.0
type: skill
created: 2026-03-26T18:30:49.078Z
updated: 2026-04-06T00:00:00.000Z
tools:
  - OAI.DBA.getSkillResource
  - ADM.DBA.database_schema_objects
  - Demo.demo.execute_spasql_query
  - OAI.DBA.RDFVIEW_ONTOLOGY_FROM_TABLES
  - OAI.DBA.RDFVIEW_FROM_TABLES
  - OAI.DBA.RDFVIEW_GENERATE_DATA_RULES
  - OAI.DBA.RDFVIEW_SYNC_TO_PHYSICAL_STORE
  - OAI.DBA.RDFVIEW_DROP_SCRIPT
  - OAI.DBA.RDF_AUDIT_METADATA
  - OAI.DBA.sparql_list_ontologies
  - OAI.DBA.sparqlRemoteQuery
  - OAI.DBA.sparql_list_entity_types_samples
  - OAI.DBA.sparql_list_entity_types_detailed
  - OAI.DBA.sparql_list_entity_types
  - OAI.DBA.R2RML_FROM_TABLES
  - OAI.DBA.R2RML_GENERATE_RDFVIEW
  - DB.DBA.graphqlQuery
  - OAI.DBA.graphqlEndpointQuery
  - OAI.DBA.SPONGE_URL
  - OAI.DBA.getAssistantConfiguration
  - ADM.DBA.database_remote_datasources
  - OAI.DBA.EXECUTE_SQL_SCRIPT
  - OAI.DBA.chatPromptComplete
---

# Linked Data Skills — Specification (v3.2.0)

---

## MANDATORY PRE-TOOL SEQUENCE — READ BEFORE CALLING ANY TOOL

This section overrides all default tool-calling behavior. The five steps below must be followed in order. No step may be skipped or reordered.

### Gate 1 — Send announcement and establish scope (NO TOOL CALL YET)

`getSkillResource` may be called once to load this skill's content. After it returns, the **next action must be text only** — send the Opening Announcement and ask the pathway question. Do not call any other tool. Wait for the user's reply.

- If the user says "Document", provides a URL (HTTP, HTTPS, or `file:`), or pastes text → **Path D**, proceed to Step 1D.
- If the user's message already contains an explicit `qualifier.schema` pattern (e.g., `postgres.postgres_jdbc_mt`) → record the qualifier and schema, send the announcement, then proceed to Gate 2.
- If the user says "local" or names a local qualifier → Path B, proceed to Gate 2.
- If the user says "DSN: X" → Path A, attach DSN, then proceed to Gate 2.
- If ambiguous → send the Opening Announcement question. Wait. Do not call any tool.

### Gate 2 — Enumerate tables (ADM.DBA.database_schema_objects ONLY)

Call `ADM.DBA.database_schema_objects` with the confirmed qualifier to enumerate catalogs (a.k.a qualifiers or databases), schemas, then call again with each schema to enumerate tables. Present the full numbered list. Wait for the user's table selection. Typically, you want to list tables for the designated catalog.schema.

**The only tool permitted at this gate is `ADM.DBA.database_schema_objects`.** Do not call `ADM.DBA.database_remote_datasources`, `RDFVIEW_FROM_TABLES`, `EXECUTE_SQL_SCRIPT`, or any other tool.

### Gate 3 — Resolve hostname and protocol (BEFORE any IRI is written)

After the user selects tables, call `Demo.demo.execute_spasql_query` for `DefaultHost` and `SSLPort`. Derive `{protocol}` and `{host}`. These must be known before any IRI string is constructed.

**Do not proceed to Gate 4 without concrete `{protocol}` and `{host}` values.**

### Gate 4 — Present IRI patterns and await CONFIRM (NO GENERATION TOOL YET)

Present the IRI pattern table (Knowledge Graph IRI, Ontology Namespace, Entity IRI template, rewrite paths) derived from `{protocol}`, `{host}`, and `iri_path_segment`. Wait for the user to reply **CONFIRM** or **OVERRIDE**.

**This gate is mandatory. It cannot be skipped unless the user has explicitly or implicitly indicated acceptance of defaults. Selecting tables is NOT authorization to generate scripts. The ONLY authorization to call `RDFVIEW_FROM_TABLES`, `RDFVIEW_ONTOLOGY_FROM_TABLES`, or `RDFVIEW_GENERATE_DATA_RULES` is a CONFIRM at this gate.**

### Gate 5 — Generate, deploy, verify

Only after Gate 4 CONFIRM: generate Ontology and Knowledge Graph views, deploy rewrite rules, audit, verify with entity samples.

---

## Skill Identity

| Field | Value |
|-------|-------|
| **Name** | linked-data-skills |
| **Version** | 3.2.0 |
| **Purpose** | Generate Knowledge Graphs from relational database objects (via Virtuoso RDF Views) or from documents/text (via schema.org RDF generation). |
| **Scope** | **Path RDBMS:** determine DB objects → confirm IRI templates → generate TBox+ABox views → deploy via rewrite rules → verify with entity samples. **Path D:** collect document + page_url + format → generate RDF → post-generation review → save to folder. |

---

## Tools Reference

### Tool Usage Hierarchy

| Tier | When to use | Tools |
|------|-------------|-------|
| **1 — Read queries** | Hostname resolution, SPARQL queries, ontology listing, quad map listing, entity sampling | `Demo.demo.execute_spasql_query`, `OAI.DBA.sparql_list_ontologies`, `OAI.DBA.sparqlRemoteQuery` |
| **2 — Discovery** | Schema and table enumeration | `ADM.DBA.database_schema_objects` |
| **3 — Generation** | Producing TBox/ABox scripts — no writes | `OAI.DBA.RDFVIEW_ONTOLOGY_FROM_TABLES`, `OAI.DBA.RDFVIEW_FROM_TABLES`, `OAI.DBA.RDFVIEW_GENERATE_DATA_RULES` |
| **4 — Write operations** | Loading TBox/ABox, applying rewrite rules, DSN attachment (Path A only), dropping quad maps | `OAI.DBA.EXECUTE_SQL_SCRIPT` |
| **5 — Audit** | Integrity check on generation/deployment error; sanity check after successful deployment | `OAI.DBA.RDF_AUDIT_METADATA` |
| **6 — Last resort** | LLM-mediated fallback when all other tools fail | `OAI.DBA.chatPromptComplete` |

### Execution Routing Order

When tool execution requires protocol selection, use this precedence:

1. **Native OAI.DBA tool execution** — call `OAI.DBA.*` tools directly via the agent tool layer
2. **URIBurner / Demo REST function execution** — call via the REST API endpoint
3. **Terminal-owned OAuth flow** — when the endpoint requires OAuth 2.0 authentication, execute the OAuth flow from the terminal (authorization code, client credentials, or device flow), capture the Bearer token, and inject via `Authorization: Bearer {token}` header into subsequent REST/OpenAPI calls
4. **MCP** — via streamable HTTP or SSE
5. **Authenticated `chatPromptComplete`** — LLM-mediated fallback
6. **OPAL Agent routing** — via canonical OPAL-recognizable function names

If the user explicitly names a protocol, honor that preference. See `references/protocol-routing.md` for detailed guidance.

`OAI.DBA.EXECUTE_SQL_SCRIPT` must never be used for read queries or table enumeration. Use `Demo.demo.execute_spasql_query` for those.

### Tool Inventory

| Tool | Role |
|------|------|
| `ADM.DBA.database_schema_objects` | **Primary discovery tool.** Enumerate schemas and tables by qualifier. |
| `Demo.demo.execute_spasql_query` | **Primary read/query tool.** Hostname resolution, SPARQL SELECT, SPASQL, UQ1 quad map listing. |
| `ADM.DBA.database_remote_datasources` | ⛔ **Path A (DSN) ONLY.** Do not call for local objects. |
| `OAI.DBA.RDFVIEW_ONTOLOGY_FROM_TABLES` | Generate TBox ontology (OWL/Turtle) — no writes. |
| `OAI.DBA.RDFVIEW_FROM_TABLES` | Generate RDF View (ABox) script — no writes. |
| `OAI.DBA.RDFVIEW_GENERATE_DATA_RULES` | Generate Linked Data rewrite rules script — no writes. |
| `OAI.DBA.R2RML_FROM_TABLES` | Generate R2RML mappings — no writes. |
| `OAI.DBA.R2RML_GENERATE_RDFVIEW` | Generate RDF View from R2RML — no writes. |
| `OAI.DBA.RDF_AUDIT_METADATA` | Integrity check on error; sanity check after deployment. |
| `OAI.DBA.RDFVIEW_DROP_SCRIPT` | Drop existing RDF View — collision resolution and rollback. |
| `OAI.DBA.RDFVIEW_SYNC_TO_PHYSICAL_STORE` | Sync RDF View to physical quad store. |
| `OAI.DBA.sparql_list_ontologies` | Verify loaded ontologies in the quad store. |
| `OAI.DBA.sparqlRemoteQuery` | Execute SPARQL against remote endpoints. |
| `OAI.DBA.sparql_list_entity_types_samples` | Sample data from discovered entity types. |
| `OAI.DBA.sparql_list_entity_types_detailed` | Detailed entity type discovery with column metadata. |
| `OAI.DBA.sparql_list_entity_types` | Discover entity types in scope. |
| `DB.DBA.graphqlQuery` | Execute GraphQL queries against Virtuoso. |
| `OAI.DBA.graphqlEndpointQuery` | Execute GraphQL against a specific endpoint. |
| `OAI.DBA.SPONGE_URL` | Fetch and ingest external URLs into the quad store. |
| `OAI.DBA.getAssistantConfiguration` | Retrieve assistant/session configuration. |
| `OAI.DBA.getSkillResource` | Retrieve skill resource files. |
| `OAI.DBA.EXECUTE_SQL_SCRIPT` | ⚠️ **WRITE OPERATIONS ONLY.** DSN attachment, loading TBox via `DB.DBA.TTLP()`, loading ABox, applying rewrite rules, dropping quad maps. Never for queries. |
| `OAI.DBA.chatPromptComplete` | LLM-mediated fallback — only when all other tools fail. |

---

## Session Workflow

⛔ **PRE-BUILD CHECK**: Before producing output, re-read the relevant workflow section above and re-read any checklists or verification gates defined in this skill. Confirm each checklist item before writing output. Build to pass — do not retro-fit. Apply the CLAUDE.md Anti-Drift Protocol: re-read spec section before build, gate-first validation, section-by-section delivery.

### Opening Announcement

⛔ **The very first action after `getSkillResource` loads this skill is to send the following announcement. Do not call any tool before this message is sent and the user has replied.**

---

> **Linked Data Skills activated.** I support two Knowledge Graph generation pathways:
>
> **Path RDBMS — Database Tables** (5-step workflow)
> **Step 1** — Determine the database objects to use
> **Step 2** — Confirm IRI templates before any script is generated
> **Step 3** — Generate Ontology and Knowledge Graph views
> **Step 4** — Deploy Linked Data via rewrite rules
> **Step 5** — Verify with hyperlinked entity samples
>
> **Path D — Document** (4-step workflow)
> **Step 1D** — Collect document source, confirm `{page_url}`, output format, and destination folder
> **Step 2D** — Generate RDF (JSON-LD or Turtle) using schema.org terms
> **Step 3D** — Post-generation review: syntax fixes, additional Q&A / entity types
> **Step 4D** — Save approved RDF to designated folder
>
> Are you working with **Database Tables** or a **Document**?
> - Reply **Database Tables** (then: local qualifier or DSN)
> - Reply **Document** (then: provide a URL or paste your text)

---

Wait for the user's reply. **→ NEXT: Step 1.**

---

### Step 1 — Determine DB Objects

⛔ **CHECKPOINT 1 — Do not call any tool until scope is established.**

Database objects use three-part naming: `qualifier.schema.object_name`.

- `qualifier` = database/catalog (e.g. `postgres`, `Demo`)
- `schema` = schema/owner (e.g. `postgres_jdbc_mt`, `demo`)
- `object_name` = table or view name

Only these prompt patterns resolve scope without asking:
- `"using DSN X"` / `"connect via DSN X"` → **Path A** (DSN attachment)
- `"local"` / a bare qualifier name / `qualifier.schema` pattern → **Path B** (local)
- Ambiguous → send the Opening Announcement question and wait

#### Path A — External (DSN attachment)
Attach the external database via `OAI.DBA.EXECUTE_SQL_SCRIPT`. Confirm the qualifier is enumerable before proceeding.

#### Path B — Local
Qualifier is already accessible. Proceed directly to enumeration.

#### Enumeration

**Call 1 — Get schemas under qualifier:**

```javascript
ADM.DBA.database_schema_objects({
  type: "TABLES",
  qualifier: "{qualifier}",
  format: "markdown"
})
```

**Call 2 — Get tables under each schema:**

```javascript
ADM.DBA.database_schema_objects({
  type: "TABLES",
  qualifier: "{qualifier}",
  schema_filter: "{schema}",
  format: "markdown"
})
```

Collect all results. Present as a numbered table grouped by schema:

```
#    Type    Object
───  ──────  ──────────────────────────────────────
1    TABLE   qualifier.schema.table_name_1
2    TABLE   qualifier.schema.table_name_2
3    VIEW    qualifier.schema.view_name_1
…
```

**Halt and wait for the user to select which objects to include.**

> "Please select the tables and views to include in the Knowledge Graph (by number, name, or 'all')."

Record the selected set as the **working set**.

⛔ **After recording the working set, the ONLY permitted next action is to resolve the hostname. Do NOT call `RDFVIEW_FROM_TABLES`, `RDFVIEW_ONTOLOGY_FROM_TABLES`, `RDFVIEW_GENERATE_DATA_RULES`, or any generation tool. Selecting tables is NOT authorization to generate scripts.**

**Scripted response on table selection — output this text exactly, then call the hostname query:**

> "Working set confirmed: [list the selected fully-qualified table names].
> Resolving hostname and protocol from Virtuoso configuration."

Then immediately call `Demo.demo.execute_spasql_query` with:

```sql
SELECT cfg_item_value(virtuoso_ini_path(), 'URIQA', 'DefaultHost')
```

**→ NEXT: Step 2.**

---

### Step 2 — Confirm IRI Templates

⛔ **CHECKPOINT 2 — Do not call any generation tool until the user has replied CONFIRM.**

#### 2a — Resolve hostname and protocol

Execute via `Demo.demo.execute_spasql_query`:

**Hostname:**
```sql
SELECT cfg_item_value(virtuoso_ini_path(), 'URIQA', 'DefaultHost')
```

- Bare hostname: `demo.openlinksw.com` → `{host}` = `demo.openlinksw.com`
- Host with port: `localhost:8890` → `{host}` = `localhost:8890`
- Full URI with protocol: extract host and protocol separately

**Protocol:**
```sql
SELECT cfg_item_value(virtuoso_ini_path(), 'HTTPServer', 'SSLPort')
```

- `SSLPort` returns a value → `{protocol}` = `https`
- `SSLPort` null/empty → `{protocol}` = `http`
- If `DefaultHost` already contains a protocol prefix, use that and skip this query.

Store `{protocol}` and `{host}`. All IRIs from this point must use `{protocol}://{host}`.

#### 2b — Collision checks (silent — run before presenting to user)

1. Run **UQ1** — if any proposed quad map IRI exists, offer: drop / rename / abort.
2. Call `OAI.DBA.sparql_list_ontologies` — if proposed TBox graph IRI exists, offer: drop / rename / abort.

Resolve all conflicts before presenting to the user.

#### 2c — Present IRI patterns and await CONFIRM

⛔ **This step is mandatory and must not be skipped. Do not proceed to Step 3 unless the user has explicitly replied CONFIRM, or has explicitly or implicitly indicated acceptance of the defaults (e.g., "use defaults", "proceed", "looks good").**

Default `iri_path_segment` = `{qualifier}` (single path component, no `/` characters).

Using the concrete `{protocol}` and `{host}` values resolved in 2a, present the following table — substituting actual values, no unresolved placeholders:

| Artifact | IRI |
|----------|-----|
| `iri_path_segment` | `{iri_path_segment}` |
| Knowledge Graph IRI | `{protocol}://{host}/{iri_path_segment}#` |
| Ontology Namespace | `{protocol}://{host}/schemas/{iri_path_segment}/` |
| Entity IRI template | `{protocol}://{host}/{iri_path_segment}/{table}/{pk_col}/{value}#this` |
| Knowledge Graph rewrite path | `/{iri_path_segment}` |
| Ontology rewrite path | `/schemas/{iri_path_segment}` |

> ⚠️ **No scripts will be generated until you reply.**
> - Reply **CONFIRM** to proceed with these IRIs
> - Reply **OVERRIDE: iri_path_segment = {value}** to use a different path segment

**Wait for the user's reply. Do not call any tool.**

Record the confirmed `iri_path_segment`. All actual IRIs are extracted from Step 3 tool output — the table above shows the expected patterns for pre-approval.

**→ NEXT: Step 3.**

---

### Step 3 — Generate Ontology and Knowledge Graph Views

⚠️ **Load `references/workflow-details.md` via `getSkillResource` before executing this step.** It contains the exact tool call signatures for Steps 3, 4, and 5.

Generate all three artifacts using the confirmed `iri_path_segment` and working set:

- **3a** — Call `OAI.DBA.RDFVIEW_ONTOLOGY_FROM_TABLES` → Ontology (OWL/Turtle)
- **3b** — Call `OAI.DBA.RDFVIEW_FROM_TABLES` → Knowledge Graph RDF View script
- **3c** — Call `OAI.DBA.RDFVIEW_GENERATE_DATA_RULES` → Linked Data rewrite rules script

**Nothing is written to the database during this step.**

On any generation error: call `OAI.DBA.RDF_AUDIT_METADATA` (`audit_level: 1`) for an integrity check. See `references/workflow-details.md` for details.

Present all three generated artifacts to the user for review before proceeding.

**→ NEXT: Step 4.**

---

### Step 4 — Deploy Linked Data via Rewrite Rules

See `references/workflow-details.md` for exact execution signatures and rollback procedures.

Execute in sequence via `OAI.DBA.EXECUTE_SQL_SCRIPT`:

- **4a** — Validate all scripts (no unresolved placeholders, no empty arguments)
- **4b** — Load TBox ontology via `DB.DBA.TTLP()` into the confirmed ontology graph IRI
- **4c** — Execute ABox RDF View script
- **4d** — Apply Linked Data rewrite rules script
- **4e** — Call `OAI.DBA.RDFVIEW_SYNC_TO_PHYSICAL_STORE`

On error at any point: call `OAI.DBA.RDF_AUDIT_METADATA` (`audit_level: 1`), report findings, offer repair / rollback / abort.

After successful completion: call `OAI.DBA.RDF_AUDIT_METADATA` (`audit_level: 1`) as a post-deployment sanity check. Report result before proceeding.

**→ NEXT: Step 5.**

---

### Step 5 — Verify: Linked Data Compliance

⛔ **Execute the query below immediately after the post-deployment audit. Do not ask the user, do not display a success message first. This call is mandatory.**

Use `{actual-abox-graph-iri}` extracted from the Step 3b output — from the `graph iri(...)` clause, substituting `demo.openlinksw.com` for `^{URIQADefaultHost}^` and stripping the trailing `#`.

**Call `Demo.demo.execute_spasql_query` with this exact query** (substitute the actual graph IRI before calling):

```sparql
SPARQL
SELECT ?type
  (SAMPLE(?entity) AS ?sampleEntity)
  (COUNT(?entity) AS ?entityCount)
FROM <{actual-abox-graph-iri}>
WHERE {
  ?entity a ?type .
}
GROUP BY ?type
ORDER BY DESC(?entityCount)
```

If the query returns SR324 (transaction timeout), retry with `LIMIT 100` added inside the `WHERE` clause.

**Present results as a formatted table. Every IRI must be a clickable markdown hyperlink:**

| Entity Type | Sample Entity | Count |
|-------------|---------------|-------|
| [`{?type}`](`{?type}`) | [`{?sampleEntity}`](`{?sampleEntity}`) | `{?entityCount}` |

⛔ **Every IRI in this table must come from query results. Never invent, guess, or construct entity IRIs. If all query attempts fail, report the error — do not fabricate links.**

If any IRI fails to dereference, report as a Linked Data compliance gap and investigate the rewrite rule from Step 4d.

---

---

## Path D — Document → RDF → Storage

Path D is aligned with `document-to-kg-skill` **Document-to-KG Harness Mode**. Use this path only for document/source-to-RDF work, keep RDF as the source of truth, apply the SoftwareApplication IRI denotation rule, and validate RDF before saving. If the user requests HTML, Markdown, an infographic, or KG Explorer output, hand off to `rdf-infographic-skill` **RDF Infographic Harness Mode** after RDF generation.

### Step 1D — Collect source, format, and destination

⛔ **No tool call until all four items are confirmed.**

Collect from the user:
1. **Document source** — pasted text, an `http:`/`https:` URL to fetch, or a `file:` URL to read from local disk
2. **`{page_url}`** — used as `@base` in the generated RDF. Rules by source type:
   - HTTP/HTTPS URL: default `{page_url}` to the source URL and confirm
   - `file:` URL: ask the user whether to use the `file:` URL as-is or supply a canonical HTTP URL as `@base`. Inform the user that `file:` IRIs produce non-dereferenceable hash IRIs.
   - Pasted text: ask the user to provide `{page_url}` explicitly
3. **Output format** — default options: **JSON-LD** or **Turtle**. Honor any other format if explicitly stated.
4. **Destination folder path** — where the output file will be saved.

Record all four as session variables before proceeding.

**→ NEXT: Step 2D.**

---

### Step 2D — Generate RDF

Load `references/document-to-knowledge-graph-prompt.md` via `getSkillResource`. Substitute `{page_url}` and `{selected_text}` into the template, adjusting the opening line for the chosen format. Call `OAI.DBA.chatPromptComplete` with the fully substituted prompt.

Present the generated RDF as a code block.

**→ NEXT: Step 3D.**

---

### Step 3D — Post-generation review (mandatory)

Execute all four sub-tasks before presenting results to the user:

1. **Syntax check** — identify and fix all syntax errors in the generated RDF.
2. **Additional Q&A / defined terms / howtos** — present a list for user approval. Do not add until approved.
3. **Additional entity types** — present a list for user approval. Do not add until approved.
4. **Revised final output** — if any additions are approved, return the complete revised RDF incorporating originals plus approved additions.

Wait for user approval at each sub-task before proceeding.

**→ NEXT: Step 4D.**

---

### Step 4D — Save to folder

Write the approved RDF to the user-designated folder. Derive the filename from `{page_url}` by slugifying the path component and appending the appropriate extension:

| Format | Extension |
|--------|-----------|
| JSON-LD | `.jsonld` |
| Turtle | `.ttl` |
| N-Triples | `.nt` |
| RDF/XML | `.rdf` |

Confirm the full saved file path to the user.

---

### Optional HTML Infographic Companion For Path D

When the user asks for an HTML infographic companion to Path D RDF output, apply `rdf-infographic-skill` **RDF Infographic Harness Mode**. For the complete HTML/RDF/Markdown pairing specification, resolver configuration, KG Explorer behavior, navigation panel behavior, attribution, dark mode, and validation checklist, see the `rdf-infographic-skill` SKILL.md.

- Save RDF documents to `{rdf-output-directory}` and HTML infographics to `{html-output-directory}`. Confirm paths before saving.
- Use `{page_url}` as the source-grounded namespace. Never use `file:` scheme IRIs when a canonical HTTPS URL exists.
- Resolver priority: URIBurner (`https://linkeddata.uriburner.com/describe/?url={entity-iri}`) by default; user-designated resolver if specified; or none if opted out.
- Encode `#` as `%23` exactly once in resolver `url` parameters. `%2523` is invalid. Every generated HTML anchor whose `href` is not a same-page fragment (`#section`) must open a new tab or view using `target="_blank" rel="noopener noreferrer"`; same-page navigation fragment links remain same-tab.
- FAQ questions, FAQ answers, glossary terms, glossary definitions, HowTo section title, and every HowTo step heading are ALL hyperlinked to their KG entity IRIs.
- Visible semantic entities route through the configured resolver using their selected RDF IRIs, including DBpedia/Wikidata IRIs selected under the SoftwareApplication denotation rule.
- POSH link: `<link rel="related" href="../rdf/{rdf-file}" type="text/turtle">`
- JSON-LD `relatedLink`: `{"@id": "../rdf/{rdf-file}"}` — IRI form, never a plain string literal.
- Skills attribution in footer: `Generated using <a target="_blank" rel="noopener noreferrer" href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/{skill-name}">skill-name</a>`. Link attributed labels directly; do not use generic `Visit`/`Learn more` anchor text.
- Collapse-to-header-bar floating navigation, draggable, resizable. Never persist collapsed dimensions. Recover from stale localStorage. Page-specific keys.
- Dark mode: `html[data-theme="dark"]` and `@media (prefers-color-scheme: dark)` equivalent. All colors via CSS variables.
- **GATE: 0 failures.** Validate: HTML parse, JS syntax, RDF parse + compliance audit, resolver links, open-tab behavior for non-fragment links, local RDF link, nav behavior, skills attribution, dark mode consistency.

---

## Execution Routing

Default order: native OAI.DBA tools → REST → MCP → authenticated `chatPromptComplete` → OPAL Agent.

If the user specifies a protocol preference, honor it. See `references/protocol-routing.md` for full routing guidance, MCP endpoints, REST API specs, and canonical OPAL function names.

---

## Utility Queries

See `references/workflow-details.md` for the UQ1 quad map listing query and drop procedure.

---

## Operational Rules

1. **Send the opening announcement before any tool call.** After `getSkillResource`, the next action is the announcement text — no tool call.
2. **`ADM.DBA.database_schema_objects` is the only enumeration tool.** Never use `ADM.DBA.database_remote_datasources` for local objects or `OAI.DBA.EXECUTE_SQL_SCRIPT` for table enumeration.
3. **Three-part naming throughout.** Every object is `qualifier.schema.object_name` in all tool calls and user-facing output.
4. **Table selection is not script authorization.** A reply of "all" or a table list selects the working set only. Script generation requires a separate "CONFIRM" at Step 2.
5. **Never write an IRI before hostname is resolved.** `{protocol}` and `{host}` must be concrete values before any IRI string is constructed.
6. **No unresolved placeholders ever.** No script, IRI, or rewrite rule passed to `OAI.DBA.EXECUTE_SQL_SCRIPT` may contain `{host}`, `{base-iri}`, or any `{...}` placeholder token. **Exception: `^{URIQADefaultHost}^` is a Virtuoso server-side macro** — it MUST remain in generated scripts exactly as produced by the generation tools and is NOT a placeholder to be substituted or blocked.
7. **Rewrite rules are not optional.** Linked Data without dereferenceable IRIs is incomplete. TBox and ABox rewrite rules must both be applied in Step 4.
8. **`OAI.DBA.RDF_AUDIT_METADATA` is an integrity tool, not a pre-flight step.** Call it only on generation/deployment error and as a post-deployment sanity check.
9. **`OAI.DBA.EXECUTE_SQL_SCRIPT` is for write operations only.** Use `Demo.demo.execute_spasql_query` for all read queries.
10. **Entity sampling is mandatory.** Step 5 must be executed and results presented as a hyperlinked table. A session is not complete until Linked Data compliance is demonstrated.
11. **Scope re-use.** If the working set and path (A or B) are already established in the session, do not re-ask.
12. **Tool fallback.** If a primary tool fails, report the error before attempting `OAI.DBA.chatPromptComplete` as fallback.
13. **Path D is self-contained.** No RDBMS tools, no IRI template gates, no Virtuoso deployment steps. The pathway ends when the approved RDF is saved to the designated folder.
14. **Path D format defaults.** Always offer JSON-LD and Turtle as the two default choices. Never assume a format — confirm with the user at Step 1D.
15. **Path D: never invent entity IRIs.** All IRIs in the generated RDF must be derived from `{page_url}` as `@base`, from the source document's existing hyperlinks, or from confident external sources (DBpedia, Wikidata, Wikipedia). Do not fabricate IRIs.

---

## Preferences

| Setting | Value |
|---------|-------|
| **Style** | Precise and professional |
| **Object naming** | Always fully qualified as `qualifier.schema.object_name` |
| **IRI confirmation** | Formatted table with concrete hostname — no unresolved placeholders |
| **Error reporting** | Name the tool, the error, and the step |
| **Response scope** | Strictly scoped to this 5-step KG/Linked Data pipeline |
