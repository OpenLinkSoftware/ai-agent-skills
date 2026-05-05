# Verification Queries

Collection mount:

```sql
select COL_ID, COL_FULL_PATH, COL_DET
from WS.WS.SYS_DAV_COL
where COL_FULL_PATH = '/your/csv-det/path/';
```

Stored CSV resources:

```sql
select RES_ID, RES_COL, RES_NAME, RES_FULL_PATH, RES_TYPE
from WS.WS.SYS_DAV_RES
where RES_COL = <collection_id>;
```

Listing:

```sql
select WEBDAV.DBA.DAV_DIR_LIST('/your/csv-det/path/', 0, null, null);
```

Graph verification:

```sparql
select *
from <{graph-iri}>
where { ?s ?p ?o }
```

Mapping verification:

- query a small sample of generated triples for one known CSV row
- verify datatypes and subject IRIs explicitly

