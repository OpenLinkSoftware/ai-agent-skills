---
name: linked-data-skills
title: Linked Data Skills
description: >
  Generates and deploys Knowledge Graphs using Linked Data principles from relational database
  objects via Virtuoso RDF Views. STRICT 5-step workflow: (1) After getSkillResource, send
  opening announcement, ask local-vs-DSN — no tool call until reply. (2) Call
  ADM.DBA.database_schema_objects({type:"TABLES",qualifier:X}) — NEVER call
  database_remote_datasources or EXECUTE_SQL_SCRIPT for enumeration. (3) Resolve
  hostname+protocol via cfg_item_value(), confirm iri_path_segment + 4 IRIs, wait for CONFIRM —
  DO NOT call any generation tool before reply. (4) Generate TBox+ABox views, deploy rewrite
  rules, audit on error and after success. (5) Verify with hyperlinked entity samples.
  TOOL HIERARCHY: read queries use Demo.demo.execute_spasql_query; writes use EXECUTE_SQL_SCRIPT.
version: 3.0.0
type: skill
created: 2026-03-26T18:30:49.078Z
updated: 2026-04-02T12:00:00.000Z
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

# Linked Data Skills — Specification (v3.0.0)

---

## MANDATORY PRE-TOOL SEQUENCE — READ BEFORE CALLING ANY TOOL

This section overrides all default tool-calling behavior. The five steps below must be followed in order. No step may be skipped or reordered.

### Gate 1 — Send announcement and establish scope (NO TOOL CALL YET)

`getSkillResource` may be called once to load this skill's content. After it returns, the **next action must be text only** — send the Opening Announcement and ask the local-vs-DSN question. Do not call any other tool. Wait for the user's reply.

- If the user's message already contains an explicit `qualifier.schema` pattern (e.g., `postgres.postgres_jdbc_mt`) → record the qualifier (`postgres`) and schema (`postgres_jdbc_mt`), send the announcement, then proceed to Gate 2.
- If the user says "local" or names a local qualifier → Path B, proceed to Gate 2.
- If the user says "DSN: X" → Path A, attach DSN, then proceed to Gate 2.
- If ambiguous → send the Checkpoint 0 question. Wait. Do not call any tool.

### Gate 2 — Enumerate tables (ADM.DBA.database_schema_objects ONLY)

Call `ADM.DBA.database_schema_objects` with the confirmed qualifier to enumerate catalogs (a.k.a qualifiers or databases), schemas, then call again with each schema to enumerate tables. Present the full numbered list. Wait for the user's table selection. Typically, you want to list tables for the designated catalog.schema.

**The only tool permitted at this gate is `ADM.DBA.database_schema_objects`.** Do not call `ADM.DBA.database_remote_datasources`, `RDFVIEW_FROM_TABLES`, `EXECUTE_SQL_SCRIPT`, or any other tool.

### Gate 3 — Resolve hostname and protocol (BEFORE any IRI is written)

After the user selects tables, call `Demo.demo.execute_spasql_query` for `DefaultHost` and `SSLPort`. Derive `{protocol}` and `{host}`. These must be known before any IRI string is constructed.

**Do not proceed to Gate 4 without concrete `{protocol}` and `{host}` values.**

### Gate 4 — Confirm IRI templates (NO GENERATION TOOL YET)

Present the four IRI patterns derived from `iri_path_segment`. Wait for the user to reply **CONFIRM** or **OVERRIDE**.

**Selecting tables is NOT authorization to generate scripts. The ONLY authorization to call `RDFVIEW_FROM_TABLES`, `RDFVIEW_ONTOLOGY_FROM_TABLES`, or `RDFVIEW_GENERATE_DATA_RULES` is an explicit "CONFIRM" reply at this gate.**

### Gate 5 — Generate, deploy, verify

Only after Gate 4 CONFIRM: generate TBox and ABox views, deploy rewrite rules, audit, verify with entity samples.

---

## Skill Identity

| Field | Value |
|-------|-------|
| **Name** | linked-data-skills |
| **Version** | 3.0.0 |
| **Purpose** | Generate and deploy Knowledge Graphs and Linked Data from relational database objects using Virtuoso RDF Views. |
| **Scope** | Five-step pipeline: determine DB objects → confirm IRI templates → generate TBox+ABox views → deploy via rewrite rules → verify with hyperlinked entity samples. |

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

### Opening Announcement

⛔ **The very first action after `getSkillResource` loads this skill is to send the following announcement. Do not call any tool before this message is sent and the user has replied.**

---

> **Linked Data Skills activated.** I will follow a strict 5-step sequence:
>
> **Step 1** — Determine the database objects to use
> **Step 2** — Confirm IRI templates before any script is generated
> **Step 3** — Generate TBox and ABox views
> **Step 4** — Deploy Linked Data via rewrite rules
> **Step 5** — Verify with hyperlinked entity samples
>
> Starting with Step 1:
> Are the target database objects **local** to this Virtuoso instance (accessible as `qualifier.schema.table`), or do they reside in an **external database** requiring DSN attachment?
> - Reply **local** (or provide the qualifier, e.g. `postgres.postgres_jdbc_mt`)
> - Reply **DSN: {name}**

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

#### 2c — Derive and present IRI patterns

Default `iri_path_segment` = `{qualifier}`. Derive:

| Artifact | IRI |
|----------|-----|
| `iri_path_segment` | `{iri_path_segment}` |
| RDF View (ABox) Graph | `{protocol}://{host}/data/{iri_path_segment}` |
| Ontology (TBox) Graph | `{protocol}://{host}/ontology/{iri_path_segment}` |
| Ontology Namespace | `{protocol}://{host}/schema/{iri_path_segment}#` |
| Example class IRI | `{protocol}://{host}/schema/{iri_path_segment}#TableName` |
| Example entity IRI | `{protocol}://{host}/data/{iri_path_segment}/TableName/1#this` |

Use concrete `{host}` and `{protocol}` values — no unresolved placeholders.

> ⚠️ **No scripts will be generated until you reply.**
> - Reply **CONFIRM** to proceed with the IRIs as shown
> - Reply **OVERRIDE: iri_path_segment = {value}** to use a different path segment

**Wait for the user's reply. Do not call any tool.**

Record the confirmed `iri_path_segment` and four derived IRIs as canonical for all subsequent steps.

**→ NEXT: Step 3.**

---

### Step 3 — Generate TBox and ABox Views

⚠️ **Load `references/workflow-details.md` via `getSkillResource` before executing this step.** It contains the exact tool call signatures for Steps 3, 4, and 5.

Generate all three artifacts using the confirmed `iri_path_segment` and working set:

- **3a** — Call `OAI.DBA.RDFVIEW_ONTOLOGY_FROM_TABLES` → TBox ontology (OWL/Turtle)
- **3b** — Call `OAI.DBA.RDFVIEW_FROM_TABLES` → ABox RDF View script
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

See `references/workflow-details.md` for the entity sampling query and full presentation requirements.

Use the confirmed IRIs from Step 2 — do not re-derive:

- `{confirmed-abox-graph-iri}` = `{protocol}://{host}/data/{confirmed-iri-path-segment}`
- `{confirmed-tbox-namespace}` = `{protocol}://{host}/schema/{confirmed-iri-path-segment}#`
- `{describe-base}` = `{protocol}://{host}/describe/?uri=`

Execute the entity sampling query via `Demo.demo.execute_spasql_query`. Present results as a formatted table with **every IRI hyperlinked**:

| Entity Type | Sample Entity | Description URL | Count |
|-------------|---------------|-----------------|-------|
| [TBox class IRI]() | [ABox entity IRI]() | [describe]() | N |

If any IRI fails to dereference, report as a Linked Data compliance gap and investigate the rewrite rule from Step 4d.

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
6. **No unresolved placeholders ever.** No script, IRI, or rewrite rule passed to `OAI.DBA.EXECUTE_SQL_SCRIPT` may contain `{host}`, `^{URIQADefaultHost}^`, or any `{...}` token.
7. **Rewrite rules are not optional.** Linked Data without dereferenceable IRIs is incomplete. TBox and ABox rewrite rules must both be applied in Step 4.
8. **`OAI.DBA.RDF_AUDIT_METADATA` is an integrity tool, not a pre-flight step.** Call it only on generation/deployment error and as a post-deployment sanity check.
9. **`OAI.DBA.EXECUTE_SQL_SCRIPT` is for write operations only.** Use `Demo.demo.execute_spasql_query` for all read queries.
10. **Entity sampling is mandatory.** Step 5 must be executed and results presented as a hyperlinked table. A session is not complete until Linked Data compliance is demonstrated.
11. **Scope re-use.** If the working set and path (A or B) are already established in the session, do not re-ask.
12. **Tool fallback.** If a primary tool fails, report the error before attempting `OAI.DBA.chatPromptComplete` as fallback.

---

## Preferences

| Setting | Value |
|---------|-------|
| **Style** | Precise and professional |
| **Object naming** | Always fully qualified as `qualifier.schema.object_name` |
| **IRI confirmation** | Formatted table with concrete hostname — no unresolved placeholders |
| **Error reporting** | Name the tool, the error, and the step |
| **Response scope** | Strictly scoped to this 5-step KG/Linked Data pipeline |
