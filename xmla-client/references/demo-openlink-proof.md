# Live proof: OpenLink demo XMLA endpoint

Validated on 2026-08-29 against `https://demo.openlinksw.com/XMLA`.

The proof was an XMLA SOAP 1.1 `Discover` request with `RequestType` set to `DISCOVER_DATASOURCES`, not an HTTP `GET`. The service returned:

- HTTP status: `200 OK`
- Content type: `text/xml; charset=utf-8`
- Response size: 12,772 bytes
- XMLA operation: `DiscoverResponse`
- Provider name: `Virtuoso XML for Analysis`
- Advertised endpoint URL: `https://demo.openlinksw.com/XMLA`
- Local data-source selector: `DSN=Local_Instance`
- Authentication mode: `Authenticated`
- Data-source rows normalized by the packaged client: 22

The rowset also advertised data sources backed by Databricks, Informix, Oracle, MySQL, PostgreSQL, Presto, SQL Server, Neo4j, Snowflake, and other configured DSNs. This establishes that a generic XMLA client can bootstrap from the endpoint without prior catalog knowledge.

Two further read-only requests used the advertised `DSN=Local_Instance` selector:

- `DISCOVER_SCHEMA_ROWSETS` returned 13 supported rowsets: `DBSCHEMA_CATALOGS`, `DBSCHEMA_TABLES`, `DBSCHEMA_TABLES_INFO`, `DBSCHEMA_COLUMNS`, `DBSCHEMA_PRIMARY_KEYS`, `DBSCHEMA_FOREIGN_KEYS`, `DBSCHEMA_PROVIDER_TYPES`, `DISCOVER_DATASOURCES`, `DISCOVER_PROPERTIES`, `DISCOVER_SCHEMA_ROWSETS`, `DISCOVER_ENUMERATORS`, `DISCOVER_KEYWORDS`, and `DISCOVER_LITERALS`.
- `DBSCHEMA_CATALOGS` returned 92 catalog rows, including `DB`, `Demo`, `TPCH`, `School`, `stores_demo`, `postgres12`, and `mysql5`.

Final packaged-client smoke run:

| Request type | Rows | Response bytes | SHA-256 |
|---|---:|---:|---|
| `DISCOVER_DATASOURCES` | 22 | 12,772 | `99e7a6c663d680ef8478956b69120a8e1339f45e292e43ea25dc39f342f94206` |
| `DISCOVER_SCHEMA_ROWSETS` | 13 | 6,259 | `4950a2ade2d5bd960eb5470ca2e3626928de897499a034e1d1404aa9164ea2b7` |
| `DBSCHEMA_CATALOGS` | 92 | 13,208 | `5f8652a8d4641bda2eb4bb1b75ab3e09395f4dd761afca1e2abfd60c086fef6c` |

Important observed behavior: a browser-style `GET /XMLA` returned 404 while the XMLA SOAP `POST /XMLA` returned the valid XMLA rowset. Client validation must therefore speak XMLA rather than use GET availability as the protocol test.
