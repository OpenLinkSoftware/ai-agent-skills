---
name: linked-data-skills
title: Linked Data Skills
description: Generate and manage RDF Views, Knowledge Graphs, and Linked Data from relational database tables using Virtuoso stored procedures. Covers the full pipeline from scope detection and ontology generation through IRI template confirmation, ABox data rules, rewrite rule assignment, and physical store synchronization.
version: 2.0.0
type: skill
created: 2026-03-26T18:30:49.078Z
updated: 2026-04-01T00:00:00.000Z
tools:
  - OAI.DBA.chatPromptComplete
  - OAI.DBA.sparql_list_entity_types_detailed
  - OAI.DBA.EXECUTE_SQL_SCRIPT
  - DB.DBA.graphqlQuery
  - DB.DBA.graphqlEndpointQuery
  - OAI.DBA.sparql_list_ontologies
  - OAI.DBA.sparql_list_entity_types
  - OAI.DBA.sparql_list_entity_types_samples
  - OAI.DBA.R2RML_FROM_TABLES
  - OAI.DBA.R2RML_GENERATE_RDFVIEW
  - OAI.DBA.RDF_BACKUP_METADATA
  - OAI.DBA.RDF_AUDIT_METADATA
  - OAI.DBA.SPONGE_URL
  - OAI.DBA.RDFVIEW_ONTOLOGY_FROM_TABLES
  - OAI.DBA.RDFVIEW_DROP_SCRIPT
  - OAI.DBA.RDFVIEW_FROM_TABLES
  - OAI.DBA.RDFVIEW_GENERATE_DATA_RULES
  - OAI.DBA.RDFVIEW_SYNC_TO_PHYSICAL_STORE
  - OAI.DBA.sparqlRemoteQuery
  - OAI.DBA.getAssistantConfiguration
  - Demo.demo.execute_spasql_query
  - OAI.DBA.getSkillResource
---

# Linked Data Skills — Specification (v2.0.0)

## Skill Identity

| Field | Value |
|-------|-------|
| **Name** | linked-data-skills |
| **Version** | 2.0.0 |
| **Purpose** | Generate and manage RDF Views, Knowledge Graphs, and Linked Data from relational database tables using Virtuoso stored procedures. |
| **Scope** | Full KG generation pipeline: scope detection → discovery → TBox generation → ontology loading → IRI template confirmation → RDF View scripting → ABox data rules + rewrite rule assignment → physical store sync → audit. |

---

## Tools Reference

| Tool | Role | Workflow Step |
|------|------|---------------|
| `OAI.DBA.sparql_list_entity_types` | Discover entity types (tables/views) in scope | Step 1 |
| `OAI.DBA.sparql_list_entity_types_detailed` | Detailed entity type discovery with column metadata | Step 1 |
| `OAI.DBA.sparql_list_entity_types_samples` | Sample data from discovered entity types | Step 1 |
| `OAI.DBA.RDFVIEW_ONTOLOGY_FROM_TABLES` | Generate TBox ontology (OWL/Turtle) from relational tables | Step 2 |
| `OAI.DBA.EXECUTE_SQL_SCRIPT` | Execute SQL/Virtuoso scripts — used to load ontology (`DB.DBA.TTLP()`), apply rewrite rules, and run generated view scripts | Steps 3, 7, 8 |
| `OAI.DBA.sparql_list_ontologies` | Verify loaded ontologies in the quad store | Step 4 |
| `OAI.DBA.R2RML_FROM_TABLES` | Generate R2RML mappings and IRI templates from tables | Step 5 |
| `OAI.DBA.RDFVIEW_FROM_TABLES` | Generate RDF View script from tables | Step 6 |
| `OAI.DBA.R2RML_GENERATE_RDFVIEW` | Generate RDF View from R2RML mappings | Step 6 |
| `OAI.DBA.RDFVIEW_GENERATE_DATA_RULES` | Generate ABox data rules (instance/fact mappings) | Step 7 |
| `OAI.DBA.RDFVIEW_SYNC_TO_PHYSICAL_STORE` | Synchronize RDF View to physical quad store | Step 8 |
| `OAI.DBA.RDF_AUDIT_METADATA` | Audit RDF metadata integrity post-sync | Step 9 |
| `OAI.DBA.RDF_BACKUP_METADATA` | Back up RDF metadata | Step 9 |
| `OAI.DBA.RDFVIEW_DROP_SCRIPT` | Drop/clean up existing RDF View scripts | Maintenance |
| `OAI.DBA.sparqlRemoteQuery` | Execute SPARQL against remote endpoints | Query / Verification |
| `Demo.demo.execute_spasql_query` | Execute SPASQL (SQL + SPARQL hybrid) queries | Query / Verification |
| `DB.DBA.graphqlQuery` | Execute GraphQL queries against Virtuoso | Query / Verification |
| `DB.DBA.graphqlEndpointQuery` | Execute GraphQL against a specific endpoint | Query / Verification |
| `OAI.DBA.SPONGE_URL` | Fetch and ingest external URLs into the quad store | Data ingestion |
| `OAI.DBA.chatPromptComplete` | LLM-mediated fallback for complex reasoning tasks | Fallback |
| `OAI.DBA.getAssistantConfiguration` | Retrieve assistant/session configuration | Session |
| `OAI.DBA.getSkillResource` | Retrieve skill resource files | Session |

---

## Session Workflow

### Step 0 — Scope Detection Gate

**Before any generation work begins**, determine whether the starting scope is established.

**Scope is considered established if the user prompt contains any of:**
- A named database qualifier (e.g., `"using qualifier Northwind"`, `"from database HR"`)
- A named DSN (e.g., `"using DSN sales_db"`, `"connect to MyDSN"`)
- A specific table reference (e.g., `"from table Demo.demo.Orders"`)
- A named graph or IRI base already active in the session
- Prior session context in which tables or a database have already been identified

**If scope is established:** proceed directly to Step 1.

**If scope is NOT established:** ask the user:

> "To begin generating the Knowledge Graph, I need to know the starting point:
> - Are we working with database tables **already attached to this session**? If so, which qualifier or schema should I use?
> - Or do you need to **attach a new data source via a DSN**? If so, please provide the DSN name and connection details."

Do not proceed until the user's response resolves the scope to either an existing qualifier/schema or a confirmed DSN attachment.

---

### Step 1 — Discovery

Use `sparql_list_entity_types` and `sparql_list_entity_types_detailed` to enumerate tables and views within the established scope. Use `sparql_list_entity_types_samples` to retrieve representative row samples where needed to inform IRI template decisions.

Present a summary of discovered entities to the user before proceeding.

---

### Step 2 — TBox Generation

Call `RDFVIEW_ONTOLOGY_FROM_TABLES` against the discovered tables to generate the TBox ontology (OWL classes, datatype properties, object properties) in Turtle or RDF/XML.

Retain the generated ontology document and its intended named graph IRI for Step 3.

---

### Step 3 — Ontology Loading

Load the generated ontology into the Virtuoso quad store using `EXECUTE_SQL_SCRIPT` with `DB.DBA.TTLP()` (or `DB.DBA.RDF_LOAD_RDFXML()` for RDF/XML output) into a session-scoped named graph derived from the IRI base, e.g.:

```
DB.DBA.TTLP('<ontology-turtle>', '', '<{base-iri}/ontology>', 0);
```

**This step is mandatory.** Do not proceed to Step 4 until the load call returns without error.

---

### Step 4 — Ontology Load Verification

Call `sparql_list_ontologies` and confirm the ontology IRI from Step 2 appears in the result. If it does not appear, re-attempt the load or report the error to the user before continuing.

---

### Step 5 — IRI Template Confirmation (Hard Gate)

**This is a mandatory confirmation gate. The workflow cannot advance without explicit user approval.**

From the R2RML mappings produced by `R2RML_FROM_TABLES`, extract and present the proposed IRI templates as a formatted table:

| Entity / Table | Subject IRI Template | Example IRI |
|----------------|----------------------|-------------|
| `Demo.demo.Orders` | `{base-iri}/Orders/{OrderID}` | `https://example.org/Orders/1001` |
| `Demo.demo.Customers` | `{base-iri}/Customers/{CustomerID}` | `https://example.org/Customers/ALFKI` |
| … | … | … |

Then ask:

> "These are the proposed IRI templates derived from the table structure. Please confirm:
> 1. **Proceed with these templates as shown**, or
> 2. **Specify overrides** for any row (provide the table name and your preferred template pattern)."

Accept partial overrides — only the rows the user modifies are changed; the rest proceed as proposed. Record the confirmed (and any overridden) templates as the canonical IRI scheme for all subsequent steps.

---

### Step 6 — RDF View Script Generation

Using the confirmed IRI templates from Step 5, call `RDFVIEW_FROM_TABLES` (or `R2RML_GENERATE_RDFVIEW` when working from the R2RML mappings directly) to produce the RDF View script.

Present the generated script to the user for review before execution.

---

### Step 7 — ABox Data Rules + Rewrite Rule Assignment

Call `RDFVIEW_GENERATE_DATA_RULES` to produce the ABox instance/fact mappings.

**In the same session step**, generate and apply URL rewrite rules via `EXECUTE_SQL_SCRIPT` covering two namespaces:

- **TBox rewrite rules** — map ontology IRIs (e.g., `{base-iri}/ontology#ClassName`) to the ontology document loaded in Step 3
- **ABox rewrite rules** — map instance IRIs (e.g., `{base-iri}/Orders/{OrderID}`) to a SPARQL DESCRIBE endpoint so each IRI dereferences to its RDF description

Both rule sets must be applied before Step 8. Confirm with the user that rewrite rules have been registered successfully.

---

### Step 8 — Sync to Physical Store

Call `RDFVIEW_SYNC_TO_PHYSICAL_STORE` to materialize the RDF View into the physical quad store, making triples queryable via SPARQL.

---

### Step 9 — Audit

Call `RDF_AUDIT_METADATA` to verify integrity of the generated metadata. Optionally call `RDF_BACKUP_METADATA` to persist a backup of the session state.

Report a summary to the user:
- Named graph IRI
- Triple count
- Ontology IRI
- Active rewrite rules (TBox + ABox)
- Any warnings from the audit

---

## Hard Gate Summary

| Gate | Step | Condition to advance |
|------|------|----------------------|
| Scope Gate | 0 | Database/qualifier/DSN is established — from prompt or user response |
| Ontology Load | 3–4 | Ontology confirmed present in `sparql_list_ontologies` output |
| IRI Template Confirmation | 5 | User has explicitly confirmed or overridden all proposed templates |
| Rewrite Rules | 7 | Both TBox and ABox rewrite rules confirmed applied before sync |

---

## Operational Rules

1. **Scope first.** Never call any discovery or generation tool before Step 0 scope is resolved.
2. **No silent defaults.** Do not assume an IRI base, qualifier, or template — always surface the proposed value and wait for confirmation at the designated gate.
3. **Ontology before ABox.** Never generate data rules (Step 7) if the ontology load (Step 3–4) has not been verified.
4. **Rewrite rules are not optional.** Linked Data without dereferenceable IRIs is incomplete. Rewrite rules must be applied in the same session step as ABox generation.
5. **Partial overrides are valid.** At the IRI template gate, a user who changes two out of ten templates has confirmed the other eight implicitly — proceed accordingly.
6. **Scope re-use.** If a database/qualifier is already established earlier in the session, do not re-ask in Step 0.
7. **Tool fallback.** If a primary tool call fails, report the error clearly before attempting `chatPromptComplete` as a fallback. Do not silently substitute.

---

## Preferences

| Setting | Value |
|---------|-------|
| **Style** | Precise and professional |
| **Confirmation prompts** | Formatted tables with example IRIs |
| **Error reporting** | Explicit — name the tool, the error, and the step |
| **Response scope** | Strictly scoped to the KG/Linked Data generation pipeline and the tools listed above |
