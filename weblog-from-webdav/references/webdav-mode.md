# WebDAV Mode

Use WebDAV mode for day-to-day post publication after the Virtuoso-side weblog engine is already in place. WebDAV is for copying HTML files, Markdown files, and associated asset folders into the configured collection. It is not the engine setup channel.

This mode covers password-based WebDAV, mTLS-authenticated WebDAV, and mTLS plus WebID delegation.

## Inputs

- Base WebDAV URL for the collection.
- Public weblog URL.
- Authentication mechanism: `.netrc`, environment variables, mTLS, OAuth bearer token, or an existing curl config.
- Optional delegated principal WebID for `On-Behalf-Of`.
- Local HTML files, Markdown files, and associated asset folders to publish as posts.
- Optional TSV with resource filename and category values.

## Post publication pattern

1. Use `PROPFIND` to inspect the collection and confirm writable target paths.
2. Verify the weblog engine exists before publishing posts. If the engine is missing, stop WebDAV publication and switch to `isql` engine bootstrap.
3. Copy post documents with `PUT`: `.html`, `.htm`, `.md`, and related media/assets.
4. Copy associated asset folders recursively where the HTML documents expect relative links.
5. Apply `schema:category` metadata with `PROPPATCH` if requested and if the engine supports category facets.
6. Read back metadata with `PROPFIND` before claiming facets are available.
7. Verify the public weblog route, feed URLs, and the newly copied post.

## Out of scope for WebDAV

Do not use WebDAV mode to claim these tasks are complete:

- Creating the VSP weblog engine.
- Enabling VSP execution for a DAV collection.
- Installing or replacing SQL procedures.
- Configuring route mapping or friendly URLs.
- Enabling full-text index behavior.
- Changing VAL ACL graph scopes or clearing ACL caches.
- Fixing server-side DAV ownership, UID/GID, or metadata-table problems.

Use `isql` mode for those setup tasks, then return to WebDAV mode for posts.

## curl guidance

- Prefer `curl --anyauth` when the server supports multiple authentication schemes.
- Keep credentials in environment variables, `.netrc`, a curl config, or certificate files; do not print them.
- Use `--cert-type P12 --cert "$P12_FILE:$P12_PASSWORD" --cacert "$CA_BUNDLE"` for WebDAV over mTLS.
- Use `-H "On-Behalf-Of: {principal-webid}"` when the certificate-bearing software agent is acting for a delegated principal.
- A successful `PROPFIND` or `GET` does not prove `PROPPATCH` rights. Stop and report authorization failure after repeated `401` or `403` responses.
- Use XML namespaces for custom properties. For `schema:category`, the namespace is `https://schema.org/`.

## Delegated WebDAV examples

Inspect a collection:

```bash
curl -iL --anyauth \
  --cert-type P12 \
  --cert "$P12_FILE:$P12_PASSWORD" \
  --cacert "$CA_BUNDLE" \
  -H "On-Behalf-Of: http://kingsley.idehen.net/public_home/kidehen/profile.ttl#i" \
  -X PROPFIND \
  -H "Depth: 1" \
  "https://www.openlinksw.com/DAV/www2.openlinksw.com/data/html/"
```

Upload a post document:

```bash
curl -iL --anyauth \
  --cert-type P12 \
  --cert "$P12_FILE:$P12_PASSWORD" \
  --cacert "$CA_BUNDLE" \
  -H "On-Behalf-Of: http://kingsley.idehen.net/public_home/kidehen/profile.ttl#i" \
  -T 2026-07-19-example-post.html \
  "https://www.openlinksw.com/DAV/www2.openlinksw.com/data/html/2026-07-19-example-post.html"
```

Apply category metadata through the bundled helper:

```bash
python3 scripts/proppatch_categories.py \
  --base-url "https://www.openlinksw.com/DAV/www2.openlinksw.com/data/html/" \
  --tsv categories.tsv \
  --cert-type P12 \
  --cert "$P12_FILE:$P12_PASSWORD" \
  --cacert "$CA_BUNDLE" \
  --on-behalf-of "http://kingsley.idehen.net/public_home/kidehen/profile.ttl#i"
```
