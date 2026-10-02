# Virtuoso × Atlan — Bottom-Up Ontology Showcase

**Thesis article:** [AI Ontology: Bottom-Up Doesn't Mean Starting From Scratch](https://atlan.com/context-and-chaos/issue/ai-ontology-bottom-up-doesnt-mean-starting-from-scratch/) (Emily Winks / Atlan Context & Chaos, 2026-09-04)

**Local Virtuoso:** SQL `localhost:1111` · HTTP `http://localhost:8890/` · spasqlqb `http://localhost:8890/spasqlqb/` · uid `kidehen` · DSN `Local_Instance`

**Schema:** `DB.kidehen` (tables `cc_*`) — do **not** use `Demo.demo`.

**IRIs:**
| Role | IRI |
|------|-----|
| Instance base | `http://localhost:8890/atlan-cc/` |
| Ontology / T-Box | `http://localhost:8890/schemas/atlan-cc/` |
| Named graph | `http://localhost:8890/atlan-cc#` |
| Claim example | `http://localhost:8890/atlan-cc/claim/101#this` |

---

## Article concepts → Virtuoso artifacts

| Article concept | Virtuoso artifact |
|-----------------|-------------------|
| Bottom-up mining from warehouse/CRM/BI/catalog | `DB.kidehen.cc_source` + claims / entities / metrics |
| Competing win-rate definitions (surface disagreement) | Three `cc_claim` rows on `metric:win_rate` + `cc_opportunity` formulas |
| Source + confidence | `cc_claim.source_id`, `cc_claim.confidence` |
| **Missing validity interval** (closed in demo) | `cc_claim.valid_from`, `cc_claim.valid_to` |
| SKOS preferred / alt labels | `cc_entity` + `cc_entity_alt_label` → `skos:prefLabel` / `skos:altLabel` |
| Reification / RDF-star spirit | `:Claim` class with provenance properties |
| Named graphs / partitioning | Graph `http://localhost:8890/atlan-cc#` |
| OWL / SHACL inheritance lesson | `ontology/atlan-cc.ttl` (OWL/RDFS + SKOS + PROV) |
| Bridge tables ↔ ontology | RDF Views QuadMap (`rdfviews/`) |
| Query the same truth | SQL · SPASQL · SPARQL (`queries/`) |

---

## Collection layout

```
atlan-bottom-up-ontology/
├── index.html                 # Landing (<1 screen story)
├── README.md                  # This runbook
├── article/
│   ├── article-source.md      # Cleaned extract + canonical URL
│   ├── article.ttl            # schema.org KG of the article
│   ├── article.html           # Interactive RDF infographic
│   └── article.md             # Markdown companion with entity IRIs
├── sql/
│   ├── 01_ddl.sql             # DB.kidehen.cc_* DDL + indexes
│   └── 02_sample_data.sql     # 4 sources, 3 win-rate claims, opportunities
├── ontology/
│   └── atlan-cc.ttl           # Inherited form (OWL/RDFS/SKOS/PROV)
├── rdfviews/
│   ├── 03_ontology_from_tables.sql  # IRI classes + T-Box graph
│   ├── 03_rdfview_install.sql       # Compact alternate QuadMap install
│   ├── 04_rdfview_data_rules.sql    # Full QuadMap data rules
│   └── 04_alt_labels_and_ontology_load.sql  # TTLP ontology + altLabel materialize
└── queries/
    ├── 05_sql_samples.sql
    ├── 06_spasql_samples.sql
    ├── 07_sparql_samples.rq
    └── spasqlqb-links.md      # Permalink templates (pwd empty)
```

---

## Runbook (local Virtuoso)

1. **DDL** — in isql (`localhost:1111`) or spasqlqb:
   ```
   LOAD .../sql/01_ddl.sql;
   LOAD .../sql/02_sample_data.sql;
   ```
   Or paste/execute the files. Confirm:
   ```sql
   SELECT COUNT(*) FROM DB.kidehen.cc_claim;
   SELECT COUNT(*) FROM DB.kidehen.cc_opportunity;
   ```

2. **Ontology** — load T-Box:
   ```
   SPARQL LOAD <file:///.../ontology/atlan-cc.ttl> INTO GRAPH <http://localhost:8890/schemas/atlan-cc/> ;
   ```
   (or run the inline INSERT in `03_ontology_from_tables.sql`)

3. **RDF Views** — execute in order:
   - `rdfviews/03_ontology_from_tables.sql` (IRI classes / functions)
   - `rdfviews/04_rdfview_data_rules.sql` (QuadMap)
   - If needed: `DB.DBA.RDF_VIEW_SYNC_TO_PHYSICAL ('http://localhost:8890/atlan-cc#', 1, 0);`

4. **Query**
   - SQL: `queries/05_sql_samples.sql`
   - SPASQL: `queries/06_spasql_samples.sql` or open [spasqlqb-links.md](queries/spasqlqb-links.md)
   - SPARQL: `queries/07_sparql_samples.rq` against `http://localhost:8890/sparql`

5. **Narrative UI** — open `index.html` then `article/article.html` in a browser.

---

## Punchline

Bottom-up **claims in SQL tables** + **inherited ontology / RDF Views** + **validity intervals** + **SQL / SPASQL / SPARQL** all query the **same truth** — so agents see disagreement (and time), instead of one silently reconciled win rate.

---

## Notes

- No live DB access is required to author this collection; scripts are runnable against a local Virtuoso with schema `DB.kidehen`.
- UTF-8 throughout; no secrets in permalinks (`pwd=` empty).
- Article rights remain with Atlan / Emily Winks; this is a Virtuoso educational showcase.

---

## Live status (2026-09-04)

- **SQL DDL + sample data:** loaded on local Virtuoso (`DB.kidehen`) as `kidehen`.
- **Measured win rates:** 0.429 / 0.600 / 0.500 — disagreement preserved.
- **Validity as-of queries:** work (Mar 2025 → claims 1+3; Sep 2025 → claims 2+3).
- **RDF Views / SPARQL LOAD:** require DBA on this instance — scripts ready in `rdfviews/`; materialized ABox in `rdf/abox-from-sql.ttl`.
- **Details:** [LIVE_RESULTS.md](LIVE_RESULTS.md)

