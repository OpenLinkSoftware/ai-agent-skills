# Sample URLs — demo.openlinksw.com (tested)

Permalink JSON: DataTwingler `exec.sql` + `tab=exec` (not `squery`).

**Graph:** `http://demo.openlinksw.com/DB#`  
**Ontology:** `http://demo.openlinksw.com/schemas/DB/`  
**ABox mode:** materialized Turtle via TTLP (RDF View `create iri class` is currently locked on demo; virtual quad maps pending DBA unlock).  
**SPARQL UI links:** use `qtxt` (not `query`) so the form shows the query text.  
**DESCRIBE format:** `text/x-html-nice-turtle` (UI label: Turtle (beautified - browsing oriented)).  
**Rewrite / entity HTTP:** `/DB` VHOST needs DBA — use SPARQL DESCRIBE until then.

## Entry points
| Approach | URL |
|---|---|
| spasqlqb | https://demo.openlinksw.com/spasqlqb/ |
| SPARQL | https://demo.openlinksw.com/sparql |
| XMLA | https://demo.openlinksw.com/XMLA |

## Verified sample entities
- Claim (CRM Win Rate): `http://demo.openlinksw.com/DB/cc_claim/claim_id/2#this`
- [DESCRIBE Pretty Turtle · claim 2](https://demo.openlinksw.com/sparql?default-graph-uri=&query=DESCRIBE+%3Chttp%3A%2F%2Fdemo.openlinksw.com%2FDB%2Fcc_claim%2Fclaim_id%2F2%23this%3E+FROM+%3Chttp%3A%2F%2Fdemo.openlinksw.com%2FDB%23%3E&should-sponge=&format=text%2Fx-html-nice-turtle&timeout=0)
- Metric: `http://demo.openlinksw.com/DB/cc_metric/metric_id/1#this`
- Source CRM: `http://demo.openlinksw.com/DB/cc_source/source_id/2#this`

## SQL via spasqlqb (live-tested)
### [SQL1 · Competing Win Rate claims](https://demo.openlinksw.com/spasqlqb/?permlink_e=%7B%22v%22%3A1%2C%22url%22%3A%22%2FXMLA%22%2C%22dsn%22%3A%22DSN%3DLocal_Instance%22%2C%22uid%22%3A%22kidehen%22%2C%22pwd%22%3A%22%22%2C%22path%22%3Anull%2C%22tab%22%3A%22exec%22%2C%22idx%22%3Anull%2C%22fkey%22%3Anull%2C%22ref%22%3Anull%2C%22exec%22%3A%7B%22sql%22%3A%22SELECT%20c.claim_id%2C%20c.definition_text%2C%20s.name%20AS%20source_name%2C%20c.confidence%2C%20c.valid_from%2C%20c.valid_to%2C%20c.status%5CnFROM%20DB.kidehen.cc_claim%20c%5CnJOIN%20DB.kidehen.cc_source%20s%20ON%20s.source_id%20%3D%20c.source_id%5CnWHERE%20c.subject_ref%20%3D%20%27metric%3A1%27%5CnORDER%20BY%20c.confidence%20DESC%22%7D%7D)

```sql
SELECT c.claim_id, c.definition_text, s.name AS source_name, c.confidence, c.valid_from, c.valid_to, c.status
FROM DB.kidehen.cc_claim c
JOIN DB.kidehen.cc_source s ON s.source_id = c.source_id
WHERE c.subject_ref = 'metric:1'
ORDER BY c.confidence DESC
```

### [SQL2 · Claims valid as-of 2025-03-15](https://demo.openlinksw.com/spasqlqb/?permlink_e=%7B%22v%22%3A1%2C%22url%22%3A%22%2FXMLA%22%2C%22dsn%22%3A%22DSN%3DLocal_Instance%22%2C%22uid%22%3A%22kidehen%22%2C%22pwd%22%3A%22%22%2C%22path%22%3Anull%2C%22tab%22%3A%22exec%22%2C%22idx%22%3Anull%2C%22fkey%22%3Anull%2C%22ref%22%3Anull%2C%22exec%22%3A%7B%22sql%22%3A%22SELECT%20c.claim_id%2C%20c.definition_text%2C%20c.valid_from%2C%20c.valid_to%2C%20c.status%5CnFROM%20DB.kidehen.cc_claim%20c%5CnWHERE%20c.subject_ref%20%3D%20%27metric%3A1%27%5Cn%20%20AND%20c.valid_from%20%3C%3D%20cast%28%272025-03-15%27%20as%20date%29%5Cn%20%20AND%20%28c.valid_to%20IS%20NULL%20OR%20c.valid_to%20%3E%3D%20cast%28%272025-03-15%27%20as%20date%29%29%22%7D%7D)

```sql
SELECT c.claim_id, c.definition_text, c.valid_from, c.valid_to, c.status
FROM DB.kidehen.cc_claim c
WHERE c.subject_ref = 'metric:1'
  AND c.valid_from <= cast('2025-03-15' as date)
  AND (c.valid_to IS NULL OR c.valid_to >= cast('2025-03-15' as date))
```

### [SQL3 · Claims valid as-of 2025-09-01](https://demo.openlinksw.com/spasqlqb/?permlink_e=%7B%22v%22%3A1%2C%22url%22%3A%22%2FXMLA%22%2C%22dsn%22%3A%22DSN%3DLocal_Instance%22%2C%22uid%22%3A%22kidehen%22%2C%22pwd%22%3A%22%22%2C%22path%22%3Anull%2C%22tab%22%3A%22exec%22%2C%22idx%22%3Anull%2C%22fkey%22%3Anull%2C%22ref%22%3Anull%2C%22exec%22%3A%7B%22sql%22%3A%22SELECT%20c.claim_id%2C%20c.definition_text%2C%20c.valid_from%2C%20c.valid_to%2C%20c.status%5CnFROM%20DB.kidehen.cc_claim%20c%5CnWHERE%20c.subject_ref%20%3D%20%27metric%3A1%27%5Cn%20%20AND%20c.valid_from%20%3C%3D%20cast%28%272025-09-01%27%20as%20date%29%5Cn%20%20AND%20%28c.valid_to%20IS%20NULL%20OR%20c.valid_to%20%3E%3D%20cast%28%272025-09-01%27%20as%20date%29%29%22%7D%7D)

```sql
SELECT c.claim_id, c.definition_text, c.valid_from, c.valid_to, c.status
FROM DB.kidehen.cc_claim c
WHERE c.subject_ref = 'metric:1'
  AND c.valid_from <= cast('2025-09-01' as date)
  AND (c.valid_to IS NULL OR c.valid_to >= cast('2025-09-01' as date))
```

### [SQL4a · Win rate all closed](https://demo.openlinksw.com/spasqlqb/?permlink_e=%7B%22v%22%3A1%2C%22url%22%3A%22%2FXMLA%22%2C%22dsn%22%3A%22DSN%3DLocal_Instance%22%2C%22uid%22%3A%22kidehen%22%2C%22pwd%22%3A%22%22%2C%22path%22%3Anull%2C%22tab%22%3A%22exec%22%2C%22idx%22%3Anull%2C%22fkey%22%3Anull%2C%22ref%22%3Anull%2C%22exec%22%3A%7B%22sql%22%3A%22SELECT%20a.n%2A1.0%2FNULLIF%28b.n%2C0%29%20AS%20win_rate_all_closed%5CnFROM%20%28SELECT%20count%28%2A%29%20AS%20n%20FROM%20DB.kidehen.cc_opportunity%20WHERE%20stage%3D%27closed_won%27%29%20a%2C%5Cn%20%20%20%20%20%28SELECT%20count%28%2A%29%20AS%20n%20FROM%20DB.kidehen.cc_opportunity%20WHERE%20stage%20LIKE%20%27closed%25%27%29%20b%22%7D%7D)

```sql
SELECT a.n*1.0/NULLIF(b.n,0) AS win_rate_all_closed
FROM (SELECT count(*) AS n FROM DB.kidehen.cc_opportunity WHERE stage='closed_won') a,
     (SELECT count(*) AS n FROM DB.kidehen.cc_opportunity WHERE stage LIKE 'closed%') b
```

### [SQL4b · Win rate qualified only](https://demo.openlinksw.com/spasqlqb/?permlink_e=%7B%22v%22%3A1%2C%22url%22%3A%22%2FXMLA%22%2C%22dsn%22%3A%22DSN%3DLocal_Instance%22%2C%22uid%22%3A%22kidehen%22%2C%22pwd%22%3A%22%22%2C%22path%22%3Anull%2C%22tab%22%3A%22exec%22%2C%22idx%22%3Anull%2C%22fkey%22%3Anull%2C%22ref%22%3Anull%2C%22exec%22%3A%7B%22sql%22%3A%22SELECT%20a.n%2A1.0%2FNULLIF%28b.n%2C0%29%20AS%20win_rate_qualified_only%5CnFROM%20%28SELECT%20count%28%2A%29%20AS%20n%20FROM%20DB.kidehen.cc_opportunity%20WHERE%20stage%3D%27closed_won%27%29%20a%2C%5Cn%20%20%20%20%20%28SELECT%20count%28%2A%29%20AS%20n%20FROM%20DB.kidehen.cc_opportunity%20WHERE%20stage%20LIKE%20%27closed%25%27%20AND%20reached_qualification%3D1%29%20b%22%7D%7D)

```sql
SELECT a.n*1.0/NULLIF(b.n,0) AS win_rate_qualified_only
FROM (SELECT count(*) AS n FROM DB.kidehen.cc_opportunity WHERE stage='closed_won') a,
     (SELECT count(*) AS n FROM DB.kidehen.cc_opportunity WHERE stage LIKE 'closed%' AND reached_qualification=1) b
```

### [SQL4c · Win rate new business](https://demo.openlinksw.com/spasqlqb/?permlink_e=%7B%22v%22%3A1%2C%22url%22%3A%22%2FXMLA%22%2C%22dsn%22%3A%22DSN%3DLocal_Instance%22%2C%22uid%22%3A%22kidehen%22%2C%22pwd%22%3A%22%22%2C%22path%22%3Anull%2C%22tab%22%3A%22exec%22%2C%22idx%22%3Anull%2C%22fkey%22%3Anull%2C%22ref%22%3Anull%2C%22exec%22%3A%7B%22sql%22%3A%22SELECT%20a.n%2A1.0%2FNULLIF%28b.n%2C0%29%20AS%20win_rate_new_business%5CnFROM%20%28SELECT%20count%28%2A%29%20AS%20n%20FROM%20DB.kidehen.cc_opportunity%20WHERE%20stage%3D%27closed_won%27%20AND%20is_new_business%3D1%29%20a%2C%5Cn%20%20%20%20%20%28SELECT%20count%28%2A%29%20AS%20n%20FROM%20DB.kidehen.cc_opportunity%20WHERE%20stage%20LIKE%20%27closed%25%27%20AND%20is_new_business%3D1%29%20b%22%7D%7D)

```sql
SELECT a.n*1.0/NULLIF(b.n,0) AS win_rate_new_business
FROM (SELECT count(*) AS n FROM DB.kidehen.cc_opportunity WHERE stage='closed_won' AND is_new_business=1) a,
     (SELECT count(*) AS n FROM DB.kidehen.cc_opportunity WHERE stage LIKE 'closed%' AND is_new_business=1) b
```

## SPASQL via spasqlqb (live against materialized DB#)
### [SPASQL1 · Competing claims](https://demo.openlinksw.com/spasqlqb/?permlink_e=%7B%22v%22%3A1%2C%22url%22%3A%22%2FXMLA%22%2C%22dsn%22%3A%22DSN%3DLocal_Instance%22%2C%22uid%22%3A%22kidehen%22%2C%22pwd%22%3A%22%22%2C%22path%22%3Anull%2C%22tab%22%3A%22exec%22%2C%22idx%22%3Anull%2C%22fkey%22%3Anull%2C%22ref%22%3Anull%2C%22exec%22%3A%7B%22sql%22%3A%22SELECT%20claim%2C%20definition%2C%20confidence%2C%20validFrom%2C%20validTo%2C%20status%5CnFROM%20%28%5CnSPARQL%5CnPREFIX%20DB%3A%20%3Chttp%3A%2F%2Fdemo.openlinksw.com%2Fschemas%2FDB%2F%3E%5CnSELECT%20%3Fclaim%20%3Fdefinition%20%3Fconfidence%20%3FvalidFrom%20%3FvalidTo%20%3Fstatus%5CnFROM%20%3Chttp%3A%2F%2Fdemo.openlinksw.com%2FDB%23%3E%5CnWHERE%20%7B%5Cn%20%20%3Fclaim%20a%20DB%3Acc_claim%20%3B%5Cn%20%20%20%20%20%20%20%20%20DB%3Asubject_ref%20%5C%22metric%3A1%5C%22%20%3B%5Cn%20%20%20%20%20%20%20%20%20DB%3Adefinition_text%20%3Fdefinition%20%3B%5Cn%20%20%20%20%20%20%20%20%20DB%3Aconfidence%20%3Fconfidence%20%3B%5Cn%20%20%20%20%20%20%20%20%20DB%3Avalid_from%20%3FvalidFrom%20%3B%5Cn%20%20%20%20%20%20%20%20%20DB%3Astatus%20%3Fstatus%20.%5Cn%20%20OPTIONAL%20%7B%20%3Fclaim%20DB%3Avalid_to%20%3FvalidTo%20%7D%5Cn%7D%5CnORDER%20BY%20DESC%28%3Fconfidence%29%5Cn%29%20AS%20x%22%7D%7D)

```sql
SELECT claim, definition, confidence, validFrom, validTo, status
FROM (
SPARQL
PREFIX DB: <http://demo.openlinksw.com/schemas/DB/>
SELECT ?claim ?definition ?confidence ?validFrom ?validTo ?status
FROM <http://demo.openlinksw.com/DB#>
WHERE {
  ?claim a DB:cc_claim ;
         DB:subject_ref "metric:1" ;
         DB:definition_text ?definition ;
         DB:confidence ?confidence ;
         DB:valid_from ?validFrom ;
         DB:status ?status .
  OPTIONAL { ?claim DB:valid_to ?validTo }
}
ORDER BY DESC(?confidence)
) AS x
```

### [SPASQL2 · Claim 2 properties](https://demo.openlinksw.com/spasqlqb/?permlink_e=%7B%22v%22%3A1%2C%22url%22%3A%22%2FXMLA%22%2C%22dsn%22%3A%22DSN%3DLocal_Instance%22%2C%22uid%22%3A%22kidehen%22%2C%22pwd%22%3A%22%22%2C%22path%22%3Anull%2C%22tab%22%3A%22exec%22%2C%22idx%22%3Anull%2C%22fkey%22%3Anull%2C%22ref%22%3Anull%2C%22exec%22%3A%7B%22sql%22%3A%22SELECT%20p%2C%20o%5CnFROM%20%28%5CnSPARQL%5CnPREFIX%20DB%3A%20%3Chttp%3A%2F%2Fdemo.openlinksw.com%2Fschemas%2FDB%2F%3E%5CnSELECT%20%3Fp%20%3Fo%5CnFROM%20%3Chttp%3A%2F%2Fdemo.openlinksw.com%2FDB%23%3E%5CnWHERE%20%7B%5Cn%20%20%3Chttp%3A%2F%2Fdemo.openlinksw.com%2FDB%2Fcc_claim%2Fclaim_id%2F2%23this%3E%20%3Fp%20%3Fo%20.%5Cn%7D%5Cn%29%20AS%20x%22%7D%7D)

```sql
SELECT p, o
FROM (
SPARQL
PREFIX DB: <http://demo.openlinksw.com/schemas/DB/>
SELECT ?p ?o
FROM <http://demo.openlinksw.com/DB#>
WHERE {
  <http://demo.openlinksw.com/DB/cc_claim/claim_id/2#this> ?p ?o .
}
) AS x
```

## SPARQL via spasqlqb
### [SPARQL1 · Competing claims (pure SPARQL)](https://demo.openlinksw.com/sparql?query=PREFIX+DB%3A+%3Chttp%3A%2F%2Fdemo.openlinksw.com%2Fschemas%2FDB%2F%3E%0ASELECT+%3Fclaim+%3Fdefinition+%3Fconfidence+%3FvalidFrom+%3FvalidTo+%3Fstatus%0AFROM+%3Chttp%3A%2F%2Fdemo.openlinksw.com%2FDB%23%3E%0AWHERE+%7B%0A++%3Fclaim+a+DB%3Acc_claim+%3B%0A+++++++++DB%3Asubject_ref+%22metric%3A1%22+%3B%0A+++++++++DB%3Adefinition_text+%3Fdefinition+%3B%0A+++++++++DB%3Aconfidence+%3Fconfidence+%3B%0A+++++++++DB%3Avalid_from+%3FvalidFrom+%3B%0A+++++++++DB%3Astatus+%3Fstatus+.%0A++OPTIONAL+%7B+%3Fclaim+DB%3Avalid_to+%3FvalidTo+%7D%0A%7D%0AORDER+BY+DESC%28%3Fconfidence%29&format=text%2Fx-html%2Btr)

Pure `/sparql` endpoint (not spasqlqb). Format: `text/x-html+tr`.

Optional spasqlqb twin: [SPARQL1 via spasqlqb](https://demo.openlinksw.com/spasqlqb/?permlink_e=%7B%22v%22%3A1%2C%22url%22%3A%22%2FXMLA%22%2C%22dsn%22%3A%22DSN%3DLocal_Instance%22%2C%22uid%22%3A%22kidehen%22%2C%22pwd%22%3A%22%22%2C%22path%22%3Anull%2C%22tab%22%3A%22exec%22%2C%22idx%22%3Anull%2C%22fkey%22%3Anull%2C%22ref%22%3Anull%2C%22exec%22%3A%7B%22sql%22%3A%22SPARQL%5CnPREFIX%20DB%3A%20%3Chttp%3A%2F%2Fdemo.openlinksw.com%2Fschemas%2FDB%2F%3E%5CnSELECT%20%3Fclaim%20%3Fdefinition%20%3Fconfidence%20%3FvalidFrom%20%3FvalidTo%20%3Fstatus%5CnFROM%20%3Chttp%3A%2F%2Fdemo.openlinksw.com%2FDB%23%3E%5CnWHERE%20%7B%5Cn%20%20%3Fclaim%20a%20DB%3Acc_claim%20%3B%5Cn%20%20%20%20%20%20%20%20%20DB%3Asubject_ref%20%5C%22metric%3A1%5C%22%20%3B%5Cn%20%20%20%20%20%20%20%20%20DB%3Adefinition_text%20%3Fdefinition%20%3B%5Cn%20%20%20%20%20%20%20%20%20DB%3Aconfidence%20%3Fconfidence%20%3B%5Cn%20%20%20%20%20%20%20%20%20DB%3Avalid_from%20%3FvalidFrom%20%3B%5Cn%20%20%20%20%20%20%20%20%20DB%3Astatus%20%3Fstatus%20.%5Cn%20%20OPTIONAL%20%7B%20%3Fclaim%20DB%3Avalid_to%20%3FvalidTo%20%7D%5Cn%7D%5CnORDER%20BY%20DESC%28%3Fconfidence%29%22%7D%7D)


```sparql
SPARQL
PREFIX DB: <http://demo.openlinksw.com/schemas/DB/>
SELECT ?claim ?definition ?confidence ?validFrom ?validTo ?status
FROM <http://demo.openlinksw.com/DB#>
WHERE {
  ?claim a DB:cc_claim ;
         DB:subject_ref "metric:1" ;
         DB:definition_text ?definition ;
         DB:confidence ?confidence ;
         DB:valid_from ?validFrom ;
         DB:status ?status .
  OPTIONAL { ?claim DB:valid_to ?validTo }
}
ORDER BY DESC(?confidence)
```

## Live test notes
- `SQL1`: 200 [[2,"closed_won / closed opportunities that reached qualification (exclude never-qualified)","CRM",0.91,"2025-07-01",null,"approved"],[1,"closed_won / all closed opportunities","Cl
- `SQL4a`: 200 [[0.428571428571429]]
- `SPASQL1`: 200 [["http://demo.openlinksw.com/DB/cc_claim/claim_id/2#this","closed_won / closed opportunities that reached qualification (exclude never-qualified)",0.91,"2025-07-01",null,"approved"],["http://demo.openlinksw.com/DB/cc_cl
- `SPARQL1_as_sql`: 200 [["http://demo.openlinksw.com/DB/cc_claim/claim_id/2#this","closed_won / closed opportunities that reached qualification (exclude never-qualified)",0.91,"2025-07-01",null,"approved"],["http://demo.openlinksw.com/DB/cc_cl
- `SPASQL1_ui`: 200 len=5000
