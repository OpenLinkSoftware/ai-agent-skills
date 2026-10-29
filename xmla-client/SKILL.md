---
name: xmla-client
description: Interrogate XML for Analysis (XMLA) SOAP endpoints, discover data sources and schema rowsets, and execute MDX or other provider-supported statements. Use for XMLA endpoint inspection, OLAP metadata discovery, connectivity diagnosis, or structured query execution; do not use for unrelated SOAP services.
---

# XMLA Client

Use `scripts/xmla_client.py` to speak XMLA directly over SOAP 1.1. It uses only the Python standard library.

## Workflow

1. Start with `DISCOVER_DATASOURCES`. Do not reject an endpoint because HTTP `GET` returns 404; XMLA is exercised by a SOAP `POST` and a service may accept only that method.
2. Inspect the returned `DataSourceInfo`, provider name, provider type, URL, and authentication mode.
3. Continue with `DISCOVER_SCHEMA_ROWSETS` for the selected data source. Then use an advertised schema rowset such as `DBSCHEMA_CATALOGS`, `MDSCHEMA_CUBES`, or `MDSCHEMA_MEASURES` with appropriate restrictions.
4. Use `execute` only when the user wants a statement run. XMLA providers may accept MDX, SQL, or another command dialect. Treat data-changing statements as mutations and require explicit authorization before sending them.
5. On failure, preserve the HTTP status and SOAP Fault. Retry only when a changed binding, credential, property, or restriction is supported by evidence.

Read [references/xmla-protocol.md](references/xmla-protocol.md) when choosing discovery rowsets, properties, output handling, or authentication. Read [references/demo-openlink-proof.md](references/demo-openlink-proof.md) for the live OpenLink proof that motivated this client.

Read [README.md](README.md) when the user wants runnable, verified SQL or SPASQL/SPARQL-FED examples.

## Commands

Discover data sources:

```bash
python3 scripts/xmla_client.py \
  --endpoint https://example.com/XMLA \
  discover --request-type DISCOVER_DATASOURCES
```

Discover catalogs for one advertised data source:

```bash
python3 scripts/xmla_client.py \
  --endpoint https://example.com/XMLA \
  --data-source-info 'DSN=Local_Instance' \
  discover --request-type DBSCHEMA_CATALOGS
```

Execute a statement from a file:

```bash
python3 scripts/xmla_client.py \
  --endpoint https://example.com/XMLA \
  --data-source-info 'DSN=Local_Instance' \
  --catalog Demo \
  execute --statement-file query.mdx --output-format pretty-xml
```

Use repeated `--restriction NAME=VALUE` and `--property NAME=VALUE` arguments for provider-specific discovery. Use `--dry-run --output-format pretty-xml` to inspect the SOAP envelope without sending it.

## Credentials and TLS

- Basic authentication: set `XMLA_USERNAME` and `XMLA_PASSWORD`. The environment variable names can be changed with `--username-env` and `--password-env`.
- Bearer authentication: set `XMLA_BEARER_TOKEN` or select another variable with `--bearer-token-env`.
- XMLA `PropertyList` authentication: set `XMLA_PROPERTY_USERNAME` and `XMLA_PROPERTY_PASSWORD`. Change the variable names with `--xmla-username-env` and `--xmla-password-env`. Use this when `DISCOVER_PROPERTIES` advertises `UserName` and `Password` properties or a SOAP Fault explicitly requests them.
- Never place passwords or bearer tokens in command arguments, generated XML, logs, or skill files.
- Prefer normal certificate validation. Use `--ca-cert` for a private CA. Use `--insecure` only for an explicitly approved diagnostic against a known endpoint.
- For mutual TLS, use `--client-cert` and, when separate, `--client-key`.

## Result discipline

Default JSON output contains normalized rowset rows and a row count. Use `--output-format xml` when exact server bytes matter and `pretty-xml` for inspection. `--response-out` preserves the unmodified response independently of formatted stdout. Do not claim a query succeeded unless the response is HTTP-successful and contains no SOAP Fault.
