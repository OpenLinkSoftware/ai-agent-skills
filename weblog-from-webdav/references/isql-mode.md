# isql Mode

Use `isql` mode for weblog engine checks and engine bootstrap. WebDAV publication depends on this engine being present. This mode covers both ordinary SQL login and Virtuoso SQL over TLS/WebID.

## Inputs

- Virtuoso `isql` executable and connection details if running outside an existing session.
- SQL listener mode: plain SQL port or TLS SQL port from `SSLServerPort`.
- Optional PKCS#12 client certificate, certificate password, CA bundle, and delegated WebID IRI.
- Target DAV collection path.
- Public weblog URL.
- Template SQL file from `templates/`.
- Optional category staging SQL or TSV-derived SQL.

## Engine check pattern

Before relying on WebDAV publication, confirm the engine exists:

1. Confirm the target DAV collection exists.
2. Confirm the VSP entry point exists as a DAV resource, normally `index.vsp`.
3. Confirm the entry point is executable VSP, not raw `<?vsp` text.
4. Confirm feed modes are implemented and resolvable.
5. Confirm scoped search is available if the selected variant requires it.
6. Confirm date filtering and optional `schema:category` facet metadata access are implemented.
7. Confirm the public route maps to the target collection or companion weblog resource.

## Bootstrap pattern

If any engine check fails:

1. Patch the SQL template variables and embedded VSP for the target collection and route.
2. Load the SQL with `isql`.
3. Confirm the target resource exists in `WS.WS.SYS_DAV_RES`.
4. Confirm the VSP is served as executable VSP, not raw `<?vsp` text.
5. Open the public route and check:
   - RSS and Atom links return feeds.
   - Search is scoped to the DAV collection.
   - Date range filtering uses the sidebar calendar controls.
   - Category facets appear only when `schema:category` metadata exists.
   - Recent posts remain in recency order.

Only after this succeeds should WebDAV be treated as the primary day-to-day publication channel.

## SQL notes

- Upload VSP text with a `string_output()` content stream.
- Use server-side metadata functions only with the authenticated or owner UID/GID expected by the target DAV collection.
- For free-text search, build a valid expression from user input before calling `contains`.
- Keep text search predicates at top-level `AND` positions.
- Avoid macro-like placeholders in SQL files loaded by `isql`.
- WebDAV cannot create the engine if VSP execution, route mapping, SQL helper logic, ACL scope, or full-text support is absent. Use `isql` for those setup tasks.

## TLS/WebID SQL channel

When the Virtuoso SQL listener is configured with `SSLServerPort`, `SSLCertificate`, and `SSLPrivateKey`, connect to that TLS SQL port with `isql`.

Direct WebID-TLS session:

```bash
read -s -p "PKCS#12 password: " P12_PASSWORD
echo

isql linkeddata.uriburner.com:1113 "" "$P12_PASSWORD" \
  -X VirtuosoLODConnectivity.p12 \
  -T ca_list_shop_2016.pem
```

Delegated WebID-TLS session:

```bash
read -s -p "PKCS#12 password: " P12_PASSWORD
echo

isql linkeddata.uriburner.com:1113 "" "$P12_PASSWORD" \
  -X my_software_agent_id.p12 \
  -T ca_list_shop_2016.pem \
  -W 'http://kingsley.idehen.net/public_home/kidehen/profile.ttl#i'
```

Flag meanings:

- `""`: empty SQL username; authentication is certificate/WebID based.
- `"$P12_PASSWORD"`: PKCS#12 passphrase. Keep it in a shell variable, not shell history.
- `-X`: client PKCS#12 certificate bundle, identifying the calling user or software agent.
- `-T`: CA certificate bundle used to verify the server certificate.
- `-W`: delegated WebID principal. Use when a software agent acts on behalf of a person or another principal.

For batch deployment, append the script path after the TLS/WebID arguments:

```bash
isql linkeddata.uriburner.com:1113 "" "$P12_PASSWORD" \
  -X my_software_agent_id.p12 \
  -T ca_list_shop_2016.pem \
  -W 'http://kingsley.idehen.net/public_home/kidehen/profile.ttl#i' \
  deploy-weblog.sql
```

After private-graph or WebDAV ACL edits, clear the relevant VAL ACL cache before testing access.
