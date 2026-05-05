# Verification Queries

Collection mount:

```sql
select COL_ID, COL_FULL_PATH, COL_DET
from WS.WS.SYS_DAV_COL
where COL_FULL_PATH = '/your/det/path/';
```

Stored resources:

```sql
select RES_ID, RES_COL, RES_NAME, RES_FULL_PATH, RES_TYPE
from WS.WS.SYS_DAV_RES
where RES_COL = <collection_id>;
```

Path lookup:

```sql
select DB.DBA.DAV_SEARCH_ID('/your/det/path/file.ext', 'R');
```

Single-row materialization:

```sql
select DB.DBA.DAV_DIR_SINGLE_INT(<resource_id>, 'R', '', null, null, 0);
```

Listing:

```sql
select WEBDAV.DBA.DAV_DIR_LIST('/your/det/path/', 0, null, null);
```

Graph verification:

```sparql
select *
from <{graph-iri}>
where { ?s ?p ?o }
```

