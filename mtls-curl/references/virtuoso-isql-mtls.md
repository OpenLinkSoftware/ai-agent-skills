# Virtuoso iSQL — mTLS + WebID Flag Reference

## Full Command Syntax

```
isql {host}:{port} {username} {password} [options]
```

For mTLS + WebID sessions specifically:

```
isql {host}:{port} "" {pkcs12-pwd} -X {pkcs12-file} -T {ca-bundle} -W {user-webid}
```

---

## Positional Arguments

| Position | Value | Notes |
|----------|-------|-------|
| 1 | `{host}:{port}` | Connection endpoint. Default iSQL port: **1111**. Use `{host}/ODBC` for HTTP-tunneled connections. |
| 2 | `""` (empty string) | Username — **must be empty** for WebID/cert auth. Any non-empty value triggers SQL-layer password auth instead. |
| 3 | `{pkcs12-pwd}` | PKCS#12 passphrase as plain string. Process-visible in `ps`; always pass via shell variable, never a literal. |

---

## mTLS / WebID Flags

| Flag | Argument | Description |
|------|----------|-------------|
| `-X` | `{pkcs12-file}` | Client certificate and private key in PKCS#12 format. Presented during TLS handshake to authenticate the client. |
| `-T` | `{ca-bundle}` | CA certificate bundle used to verify the **server's** TLS certificate. Required; iSQL does not fall back to OS trust store. |
| `-W` | `{user-webid}` | WebID URI. Asserted as the session identity after the TLS handshake. Must be resolvable to an RDF profile document that includes the client certificate's public key. |

---

## Other Useful iSQL Flags

| Flag | Argument | Description |
|------|----------|-------------|
| `-b` | — | Batch mode: suppress the interactive banner and prompt; useful for piping queries |
| `-u` | `{key}=val,...` | Set ODBC connection attributes (e.g., `-u CHARSET=UTF-8`) |
| `-d` | `{delimiter}` | Column delimiter in batch output (default: `\|`) |
| `-m` | `{width}` | Max column width in output (useful for long IRIs; try `-m 200`) |
| `-c` | — | Column headers in batch output |
| `-i` | `{file}` | Read SQL statements from a file instead of stdin |
| `-o` | `{file}` | Write output to a file |
| `-v` | — | Verbose: show driver version and connection info |

---

## WebID Authentication Flow

```
Client                          Virtuoso Server
  |                                   |
  |-- TCP connect {host}:{port} ------->|
  |<-- TLS ServerHello + server cert --|
  |  (client verifies with -T bundle)  |
  |-- TLS ClientHello + client cert -->|  (-X PKCS#12)
  |  (server verifies cert chain)      |
  |<-- TLS handshake complete ---------|
  |                                   |
  |-- Login request (-W WebID URI) --->|
  |  Virtuoso fetches WebID profile    |
  |  Verifies public key in profile    |
  |  matches client cert public key    |
  |  Checks VAL ACL graph for WebID   |
  |<-- Session established ------------|
  |                                   |
  SQL>
```

Key verification steps the server performs:
1. Client cert chain validates against its CA store
2. The `-W` WebID URI is fetched and parsed as RDF
3. The public key in the WebID profile matches the public key in the presented cert
4. The WebID URI appears in the VAL ACL graph with the required permissions

---

## Environment Variables

| Variable | Used for |
|----------|---------|
| `MTLS_PKCS12_FILE` | Default path to PKCS#12 file (`-X` value) |
| `MTLS_PKCS12_PWD` | Default PKCS#12 password (3rd positional) |
| `MTLS_CA_BUNDLE` | Default CA bundle path (`-T` value) |
| `MTLS_WEBID` | Default WebID URI (`-W` value) |

Example session setup:

```bash
export MTLS_PKCS12_FILE="$HOME/.certs/agent.p12"
export MTLS_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"
export MTLS_WEBID="https://id.example.org/dataspace/person/alice#this"
# MTLS_PKCS12_PWD intentionally not persisted — elicit at runtime
read -s -p "PKCS#12 password: " MTLS_PWD; echo
isql "localhost:1111" "" "${MTLS_PWD}" \
  -X "${MTLS_PKCS12_FILE}" \
  -T "${MTLS_CA_BUNDLE}" \
  -W "${MTLS_WEBID}"
```

---

## Confirming Session Identity

Immediately after connecting, run:

```sql
SELECT USER;
```

For a WebID-authenticated session, `USER` returns the WebID URI
(e.g., `https://id.example.org/dataspace/person/alice#this`), not a
SQL username. If it returns `nobody` or an unexpected value, the WebID
verification did not complete successfully.

---

## Running SPARQL Within iSQL

Virtuoso iSQL supports inline SPARQL with the `SPARQL` keyword prefix:

```sql
-- Basic triple scan
SPARQL SELECT * WHERE { ?s ?p ?o } LIMIT 10;

-- Count triples in a named graph
SPARQL SELECT COUNT(*) WHERE { GRAPH <{graph-uri}> { ?s ?p ?o } };

-- Subject lookup
SPARQL DESCRIBE <{subject-uri}>;
```

The SPARQL query runs under the same WebID identity as the SQL session, so
named graph access is governed by VAL ACL rules.

---

## Common Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot login` | WebID not in VAL ACL | Add WebID to the server's ACL graph with appropriate permissions |
| `*** Error 42000: [OpenLink]...SSL handshake failed` | TLS failure | Check `-T` CA bundle covers the server cert; check `-X` cert is trusted by server |
| `WebID verification failed` | WebID profile unreachable or key mismatch | Verify WebID URI resolves, check `foaf:maker`/`cert:key` triples in profile |
| `Wrong number of parameters` | Argument order error | Ensure positional order: `host:port "" pwd -X ... -T ... -W ...` |
| `isql: error while loading shared libraries` | Missing iSQL runtime | Verify Virtuoso client install; check `LD_LIBRARY_PATH` on Linux |
| `Connection refused` | Virtuoso not running or wrong port | `telnet {host} {port}` to confirm reachability |
| `certificate verify failed` | Server cert not covered by CA bundle | Point `-T` to the correct CA (often an internal PKI CA, not a public CA) |

---

## Locating the iSQL Binary

Virtuoso ships `isql` (or `isql-v` to avoid clash with unixODBC's `isql`)
in its `bin/` directory. Common locations:

| Platform | Path |
|----------|------|
| macOS (Homebrew) | `/opt/homebrew/opt/virtuoso/bin/isql-v` |
| Linux (package) | `/usr/bin/isql-v` or `/usr/local/virtuoso-opensource/bin/isql` |
| OpenLink bundle | `/opt/openlink/virtuoso/bin/isql` |
| Docker container | `/usr/local/virtuoso-opensource/bin/isql` |

```bash
# Find all isql binaries
which isql isql-v 2>/dev/null
find /opt /usr/local /home -name "isql*" -type f 2>/dev/null | head -10
```

If both Virtuoso's `isql` and unixODBC's `isql` are present, prefer
`isql-v` (Virtuoso) for mTLS sessions — unixODBC's `isql` does not support
the `-X`/`-T`/`-W` flags.
