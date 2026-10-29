# Live SQL results (2026-09-04) — local Virtuoso shop-database
Loaded into `DB.kidehen` as user `kidehen` on `localhost:1111` / HTTP `8890`.
## Punchline
| Formula (article disagreement) | Result |
|---|---|
| closed_won / all closed | **0.429** (3/7) |
| closed_won / qualified closed | **0.600** (3/5) |
| closed_won new-business / closed new-business | **0.500** (2/4) |

Three defensible Win Rate claims (source + confidence + **validity**):

| claim | source | confidence | status | valid_from | valid_to | definition |
|---|---|---|---|---|---|---|
| 1 | Cloud Warehouse | 0.82 | superseded | 2024-01-01 | 2025-06-30 | closed_won / all closed |
| 2 | CRM | 0.91 | approved | 2025-07-01 | NULL | exclude never-qualified |
| 3 | BI Tool | 0.74 | candidate | 2025-01-01 | NULL | new-business only |

As-of **2025-03-15**: claims 1 + 3. As-of **2025-09-01**: claims 2 + 3.

## Open in spasqlqb (SQL — works now)

### [SQL1 Competing Win Rate claims](http://localhost:8890/spasqlqb/?q=SELECT%20c.claim_id%2C%20c.definition_text%2C%20s.name%20AS%20source_name%2C%20c.confidence%2C%20c.valid_from%2C%20c.valid_to%2C%20c.status%0AFROM%20DB.kidehen.cc_claim%20c%0AJOIN%20DB.kidehen.cc_source%20s%20ON%20s.source_id%20%3D%20c.source_id%0AWHERE%20c.subject_ref%20%3D%20%27metric%3A1%27%0AORDER%20BY%20c.confidence%20DESC&uid=kidehen&pwd=&dsn=DSN%3DLocal_Instance)

```sql
SELECT c.claim_id, c.definition_text, s.name AS source_name, c.confidence, c.valid_from, c.valid_to, c.status
FROM DB.kidehen.cc_claim c
JOIN DB.kidehen.cc_source s ON s.source_id = c.source_id
WHERE c.subject_ref = 'metric:1'
ORDER BY c.confidence DESC
```

### [SQL2 Claims valid as-of 2025-03-15](http://localhost:8890/spasqlqb/?q=SELECT%20c.claim_id%2C%20c.definition_text%2C%20c.valid_from%2C%20c.valid_to%2C%20c.status%0AFROM%20DB.kidehen.cc_claim%20c%0AWHERE%20c.subject_ref%20%3D%20%27metric%3A1%27%0A%20%20AND%20c.valid_from%20%3C%3D%20cast%28%272025-03-15%27%20as%20date%29%0A%20%20AND%20%28c.valid_to%20IS%20NULL%20OR%20c.valid_to%20%3E%3D%20cast%28%272025-03-15%27%20as%20date%29%29&uid=kidehen&pwd=&dsn=DSN%3DLocal_Instance)

```sql
SELECT c.claim_id, c.definition_text, c.valid_from, c.valid_to, c.status
FROM DB.kidehen.cc_claim c
WHERE c.subject_ref = 'metric:1'
  AND c.valid_from <= cast('2025-03-15' as date)
  AND (c.valid_to IS NULL OR c.valid_to >= cast('2025-03-15' as date))
```

### [SQL3 Claims valid as-of 2025-09-01](http://localhost:8890/spasqlqb/?q=SELECT%20c.claim_id%2C%20c.definition_text%2C%20c.valid_from%2C%20c.valid_to%2C%20c.status%0AFROM%20DB.kidehen.cc_claim%20c%0AWHERE%20c.subject_ref%20%3D%20%27metric%3A1%27%0A%20%20AND%20c.valid_from%20%3C%3D%20cast%28%272025-09-01%27%20as%20date%29%0A%20%20AND%20%28c.valid_to%20IS%20NULL%20OR%20c.valid_to%20%3E%3D%20cast%28%272025-09-01%27%20as%20date%29%29&uid=kidehen&pwd=&dsn=DSN%3DLocal_Instance)

```sql
SELECT c.claim_id, c.definition_text, c.valid_from, c.valid_to, c.status
FROM DB.kidehen.cc_claim c
WHERE c.subject_ref = 'metric:1'
  AND c.valid_from <= cast('2025-09-01' as date)
  AND (c.valid_to IS NULL OR c.valid_to >= cast('2025-09-01' as date))
```

### [SQL4a Win rate — all closed](http://localhost:8890/spasqlqb/?q=SELECT%20a.n%2A1.0/NULLIF%28b.n%2C0%29%20AS%20win_rate_all_closed%0AFROM%20%28SELECT%20count%28%2A%29%20AS%20n%20FROM%20DB.kidehen.cc_opportunity%20WHERE%20stage%3D%27closed_won%27%29%20a%2C%0A%20%20%20%20%20%28SELECT%20count%28%2A%29%20AS%20n%20FROM%20DB.kidehen.cc_opportunity%20WHERE%20stage%20LIKE%20%27closed%25%27%29%20b&uid=kidehen&pwd=&dsn=DSN%3DLocal_Instance)

```sql
SELECT a.n*1.0/NULLIF(b.n,0) AS win_rate_all_closed
FROM (SELECT count(*) AS n FROM DB.kidehen.cc_opportunity WHERE stage='closed_won') a,
     (SELECT count(*) AS n FROM DB.kidehen.cc_opportunity WHERE stage LIKE 'closed%') b
```

### [SQL4b Win rate — qualified only](http://localhost:8890/spasqlqb/?q=SELECT%20a.n%2A1.0/NULLIF%28b.n%2C0%29%20AS%20win_rate_qualified_only%0AFROM%20%28SELECT%20count%28%2A%29%20AS%20n%20FROM%20DB.kidehen.cc_opportunity%20WHERE%20stage%3D%27closed_won%27%29%20a%2C%0A%20%20%20%20%20%28SELECT%20count%28%2A%29%20AS%20n%20FROM%20DB.kidehen.cc_opportunity%20WHERE%20stage%20LIKE%20%27closed%25%27%20AND%20reached_qualification%3D1%29%20b&uid=kidehen&pwd=&dsn=DSN%3DLocal_Instance)

```sql
SELECT a.n*1.0/NULLIF(b.n,0) AS win_rate_qualified_only
FROM (SELECT count(*) AS n FROM DB.kidehen.cc_opportunity WHERE stage='closed_won') a,
     (SELECT count(*) AS n FROM DB.kidehen.cc_opportunity WHERE stage LIKE 'closed%' AND reached_qualification=1) b
```

### [SQL4c Win rate — new business](http://localhost:8890/spasqlqb/?q=SELECT%20a.n%2A1.0/NULLIF%28b.n%2C0%29%20AS%20win_rate_new_business%0AFROM%20%28SELECT%20count%28%2A%29%20AS%20n%20FROM%20DB.kidehen.cc_opportunity%20WHERE%20stage%3D%27closed_won%27%20AND%20is_new_business%3D1%29%20a%2C%0A%20%20%20%20%20%28SELECT%20count%28%2A%29%20AS%20n%20FROM%20DB.kidehen.cc_opportunity%20WHERE%20stage%20LIKE%20%27closed%25%27%20AND%20is_new_business%3D1%29%20b&uid=kidehen&pwd=&dsn=DSN%3DLocal_Instance)

```sql
SELECT a.n*1.0/NULLIF(b.n,0) AS win_rate_new_business
FROM (SELECT count(*) AS n FROM DB.kidehen.cc_opportunity WHERE stage='closed_won' AND is_new_business=1) a,
     (SELECT count(*) AS n FROM DB.kidehen.cc_opportunity WHERE stage LIKE 'closed%' AND is_new_business=1) b
```

## RDF / SPARQL status
`kidehen` can CREATE/SELECT on `DB.kidehen.*` but **cannot** install QuadMaps or `SPARQL LOAD` without DBA / `SPARQL_UPDATE` (errors on `SYS_IDONLY_ONE` / `RDF_QUAD`).

**One DBA step to unlock SPASQL/SPARQL over the same tables:**
1. As `dba`, run `rdfviews/03_rdfview_install.sql` (or `04_rdfview_data_rules.sql`).
2. Optionally `GRANT SPARQL_UPDATE TO "kidehen"` and load `ontology/atlan-cc.ttl` + `rdf/abox-from-sql.ttl`.
3. Then open SPARQL links in `queries/spasqlqb-links.md`.

Until then, the Virtuoso story is already proven on the SQL path: bottom-up claims with validity intervals, competing definitions, and three disagreeing metrics from one opportunity table.
