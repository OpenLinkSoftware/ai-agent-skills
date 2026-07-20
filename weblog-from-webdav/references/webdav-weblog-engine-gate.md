# WebDAV Weblog Engine Gate

Use this gate whenever the user asks to generate a weblog from a WebDAV URL.

## Required Interpretation

- A WebDAV weblog is a Virtuoso Server Pages (VSP) weblog over ordinary WebDAV files.
- Static HTML is only an optional preview when the user explicitly asks for static-only output.
- If the target collection lacks a working executable weblog entry point, generate the VSP/isql engine bundle.

## Prior-Work Lookup

Before writing VSP or SQL, search memory or local prior work for:

- `DAV_RES_UPLOAD_STRSES_INT`
- `string_output`
- `HTTP_PATH`
- `index.vsp`
- `raw <?vsp`
- `vsp_user`
- `weblog-from-webdav`

Carry forward these known fixes:

- `DAV_RES_UPLOAD_STRSES_INT` receives a `string_output()` stream populated by `http(vsp_content, vsp_stream)`, not a plain string.
- Avoid `$1`, `$2`, and similar replacement tokens in SQL loaded through `isql`.
- Raw `<?vsp ... ?>` in the browser means the route is static or VSP execution failed; inspect `HTTP_PATH`.
- A VSP-enabled DAV mapping uses `is_dav=>1`, `def_page=>'index.vsp'`, and an explicit `vsp_user`.
- Feed links must point at modes the VSP actually handles.
- `http_param()` can return a non-string sentinel on absent parameters in some Virtuoso builds; check `isstring(...)` before calling `lower`, `lcase`, `trim`, or similar string functions.

## Required Bundle

For a generated, not-yet-deployed weblog bundle, include:

- `index.vsp`
- `deploy-*.sql` that uploads the VSP resource using `string_output()` and `DAV_RES_UPLOAD_STRSES_INT`
- `VHOST_DEFINE` route setup, or a separate route SQL file plus a clear route assumption
- verification queries against `DB.DBA.HTTP_PATH` and `WS.WS.SYS_DAV_RES`
- RSS and Atom handling
- AtomPub service handling
- dynamic post enumeration from `WS.WS.SYS_DAV_RES`
- `._*` and `.DS_Store` exclusion
- README or run notes outside the skill package

When `schema:category` facets are requested, also include:

- category metadata source description
- facet SQL or property-application SQL
- facet count logic using the filtered candidate set
- `dict_iter_next` for category aggregate dictionaries

## Completion Rule

Do not claim a WebDAV weblog request is complete until either:

- the live deployed route and feeds have been verified, or
- the complete deployable bundle passes `scripts/validate_generated_weblog_bundle.py` and the response clearly says live deployment still requires authenticated Virtuoso/WebDAV access.
