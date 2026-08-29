# XMLA protocol notes

XML for Analysis (XMLA) uses SOAP operations in the namespace `urn:schemas-microsoft-com:xml-analysis`.

## Operations

- `Discover` requests a named metadata rowset. Its body contains `RequestType`, `Restrictions/RestrictionList`, and `Properties/PropertyList`.
- `Execute` submits `Command/Statement` plus `Properties/PropertyList`. Providers commonly interpret the statement as MDX, but some expose SQL or another dialect.

The SOAP 1.1 action is `urn:schemas-microsoft-com:xml-analysis:Discover` or `urn:schemas-microsoft-com:xml-analysis:Execute`. Use `Content-Type: text/xml; charset=utf-8`.

## Discovery progression

1. `DISCOVER_DATASOURCES` identifies service bindings, data-source information strings, provider types, and authentication modes.
2. `DISCOVER_SCHEMA_ROWSETS` lists the metadata rowsets supported by the selected provider.
3. Relational providers often expose `DBSCHEMA_CATALOGS`, `DBSCHEMA_SCHEMATA`, `DBSCHEMA_TABLES`, and `DBSCHEMA_COLUMNS`.
4. Multidimensional providers often expose `MDSCHEMA_CUBES`, `MDSCHEMA_DIMENSIONS`, `MDSCHEMA_HIERARCHIES`, `MDSCHEMA_LEVELS`, `MDSCHEMA_MEASURES`, and `MDSCHEMA_MEMBERS`.

Do not assume every provider supports every rowset. Ask `DISCOVER_SCHEMA_ROWSETS` and use its restriction metadata.

## Properties and restrictions

Common properties include:

- `DataSourceInfo`: provider connection selector returned by `DISCOVER_DATASOURCES`.
- `Catalog`: selected relational or multidimensional catalog.
- `Content`: response detail, commonly `SchemaData`.
- `Format`: provider-supported rowset or multidimensional response format.

Restrictions are rowset-specific. Common examples include `CATALOG_NAME`, `SCHEMA_NAME`, `TABLE_NAME`, `TABLE_TYPE`, `CUBE_NAME`, and `MEASURE_NAME`. Preserve case and spelling advertised by the service.

## Response handling

Discovery usually returns an inline XML Schema followed by `<row>` elements in `urn:schemas-microsoft-com:xml-analysis:rowset`. Execute may return a rowset or a multidimensional dataset. A successful HTTP status can still carry a SOAP Fault, so inspect both transport and envelope.

## Authentication

XMLA authentication may be an HTTP concern or may use provider properties. This client supports HTTP Basic, bearer tokens, mutual TLS, private certificate authorities, normal anonymous access, and the `UserName`/`Password` XMLA properties through environment variables. Inspect `DISCOVER_PROPERTIES` and SOAP Faults before selecting the mode. Keep secrets in environment variables and never embed them in command arguments or saved SOAP request files.
