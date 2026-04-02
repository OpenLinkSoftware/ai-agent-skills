# Linked Data Skills — Workflow Details

Detailed tool call signatures, script templates, and procedures for Steps 3–5.
Load this file via `getSkillResource` at the start of Step 3.

---

## Step 3 — Generate TBox and ABox Views

All three generation tools use `iri_path_segment` as the primary IRI driver.
Nothing is written to the database during this step.

### 3a — Generate TBox Ontology

**Tool:** `OAI.DBA.RDFVIEW_ONTOLOGY_FROM_TABLES`

```javascript
OAI.DBA.RDFVIEW_ONTOLOGY_FROM_TABLES({
  tables: [
    "{qualifier}.{schema}.{TableA}",
    "{qualifier}.{schema}.{TableB}"
  ],
  iri_path_segment: "{confirmed-iri-path-segment}",
  graphql_annotations: 1
})
```

**Output:** OWL ontology in Turtle format — classes, datatype properties, object properties.
Retain in full. Do not load here.

### 3b — Generate ABox RDF View Script

**Tool:** `OAI.DBA.RDFVIEW_FROM_TABLES`

```javascript
OAI.DBA.RDFVIEW_FROM_TABLES({
  tables: [
    "{qualifier}.{schema}.{TableA}",
    "{qualifier}.{schema}.{TableB}"
  ],
  iri_path_segment: "{confirmed-iri-path-segment}",
  generate_void: 1
})
```

**Output:** SQL script defining quad map storage and IRI class templates.
Retain in full. Do not load here.

### 3c — Generate Linked Data Rewrite Rules

**Tool:** `OAI.DBA.RDFVIEW_GENERATE_DATA_RULES`

```javascript
OAI.DBA.RDFVIEW_GENERATE_DATA_RULES({
  iri_path_segment: "{confirmed-iri-path-segment}",
  include_ontology_rules: 1
})
```

**Output:** SQL script with `DB.DBA.URLREWRITE_CREATE_RULELIST` and `DB.DBA.VHOST_DEFINE`
calls for both TBox and ABox IRIs. Does not take a `tables` parameter — generates rules
for all quad maps created by Step 3b.
Retain in full. Do not load here.

### On Generation Error

Call `OAI.DBA.RDF_AUDIT_METADATA` with `audit_level: 1`:

```javascript
OAI.DBA.RDF_AUDIT_METADATA({
  audit_level: 1,
  format: "json"
})
```

Report findings and offer:
- Repair: re-run with `audit_level: 2`
- Abort

---

## Step 4 — Deploy Linked Data via Rewrite Rules

Execute the generated scripts in sequence. All steps must succeed.

### 4a — Script Validation (mandatory before any execution)

Before passing any script to `OAI.DBA.EXECUTE_SQL_SCRIPT`, verify:

1. **No unresolved placeholders** — no `{host}`, `^{URIQADefaultHost}^`, `{base-iri}`, or any `{...}` token
2. **No empty arguments** — no `''` where a value is expected, no back-to-back commas `, ,`
3. **All parameters present** — every `URLREWRITE_CREATE_RULELIST` and `VHOST_DEFINE` call has all required non-null parameters

Fail loudly if any check fails — present the problematic lines to the user for correction.

### 4b — Load TBox Ontology

```javascript
OAI.DBA.EXECUTE_SQL_SCRIPT({
  sql_script: "DB.DBA.TTLP('{ontology-turtle}', '', '{protocol}://{host}/ontology/{confirmed-iri-path-segment}', 0);"
})
```

The target graph IRI must exactly match the Ontology (TBox) Graph IRI confirmed at Step 2.

### 4c — Execute ABox RDF View Script

```javascript
OAI.DBA.EXECUTE_SQL_SCRIPT({
  sql_script: "{exact-rdfview-script-from-step-3b}"
})
```

Never modify the generated script — execute exactly as returned.

### 4d — Apply Rewrite Rules

```javascript
OAI.DBA.EXECUTE_SQL_SCRIPT({
  sql_script: "{exact-data-rules-script-from-step-3c}"
})
```

Never modify the generated script — execute exactly as returned.

### 4e — Sync to Physical Store

```javascript
OAI.DBA.RDFVIEW_SYNC_TO_PHYSICAL_STORE({})
```

### On Deployment Error

1. Call `OAI.DBA.RDF_AUDIT_METADATA` with `audit_level: 1` to identify integrity issues
2. Report error and audit findings to the user
3. Offer options:
   - **Repair:** re-run audit with `audit_level: 2`
   - **Rollback:** call `OAI.DBA.RDFVIEW_DROP_SCRIPT` for the affected graph IRI, then execute the drop script via `OAI.DBA.EXECUTE_SQL_SCRIPT`
   - **Abort**

To drop a conflicting quad map before rollback:
```sql
SPARQL DROP QUAD MAP <{quad-map-iri}>;
```

### Post-Deployment Sanity Check

After successful completion of 4a–4e:

```javascript
OAI.DBA.RDF_AUDIT_METADATA({
  audit_level: 1,
  format: "json"
})
```

Report result to the user. If issues found, offer `audit_level: 2` repair before proceeding to Step 5.

---

## Step 5 — Verify: Linked Data Compliance

Use IRIs confirmed at Step 2 — do not re-derive from templates.

| Variable | Value |
|----------|-------|
| `{confirmed-abox-graph-iri}` | `{protocol}://{host}/data/{confirmed-iri-path-segment}` |
| `{confirmed-tbox-namespace}` | `{protocol}://{host}/schema/{confirmed-iri-path-segment}#` |
| `{describe-base}` | `{protocol}://{host}/describe/?uri=` |

**Entity sampling query** — execute via `Demo.demo.execute_spasql_query`:

```sparql
SPARQL
SELECT ?type
  (SAMPLE(?entity) AS ?sampleEntity)
  (CONCAT('{describe-base}', STR(SAMPLE(?entity))) AS ?sampleEntityDescUrl)
  (COUNT(?entity) AS ?entityCount)
FROM <{confirmed-abox-graph-iri}>
WHERE {
  ?entity a ?type .
  FILTER (STRSTARTS(STR(?type), '{confirmed-tbox-namespace}'))
}
GROUP BY ?type
ORDER BY DESC(?entityCount)
```

Present as a formatted table with every IRI hyperlinked:

| Entity Type | Sample Entity | Description URL | Count |
|-------------|---------------|-----------------|-------|
| [`{tbox}TableA`]({describe-base}{tbox}TableA) | [`…/TableA/1#this`]({abox}TableA/1#this) | [`describe`]({describe-base}{abox}TableA/1#this) | N |

- **Entity Type** → hyperlinked to TBox class IRI (dereferences to ontology)
- **Sample Entity** → hyperlinked to ABox entity IRI (dereferences to entity RDF description)
- **Description URL** → hyperlinked to `/describe/?uri=` endpoint

If any IRI fails to dereference, report as a Linked Data compliance gap and investigate the rewrite rule registered in Step 4d.

---

## UQ1 — List Existing Quad Maps

Use at Step 2b (collision detection) and post-deployment verification.

```sparql
SPARQL
DEFINE input:storage ""

SELECT ?qm
FROM <http://www.openlinksw.com/schemas/virtrdf#>
WHERE {
  [] virtrdf:qsUserMaps ?maps .
  ?maps ?p ?qm .
  ?qm a virtrdf:QuadMap .
}
```

Execute via `Demo.demo.execute_spasql_query`. Present results as a numbered list.
