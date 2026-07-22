---
name: weblog-from-webdav
description: Build, deploy, update, or troubleshoot a Virtuoso Server Pages weblog generated from a Virtuoso WebDAV collection of HTML or Markdown documents. Use for VSP weblog engine setup checks, SQL bootstrap via Virtuoso isql or isql over TLS/WebID, VSP weblog templates, RSS/Atom feed discovery, AtomPub links, scoped full-text search, calendar date filtering, schema:category facets, category metadata application, and post publication via WebDAV copying of HTML, Markdown, and asset folders including mTLS and On-Behalf-Of delegation.
---

# Weblog From WebDAV

Use this skill to turn a Virtuoso WebDAV folder into a live weblog whose posts remain ordinary files. The skill always starts by determining whether the Virtuoso-side weblog engine is already in place. If it is not, bootstrap it with `isql`; WebDAV is then used for the post-publication workflow.

## Blocking Gate — WebDAV URL Means VSP/isql Weblog

When the user asks to generate a weblog from a WebDAV URL, a static HTML index is **not** a valid completion unless the user explicitly asks for a static-only page or preview. The default deliverable is either:

- a live verified VSP weblog deployed on the target Virtuoso/WebDAV server, or
- a complete deployable VSP/isql bundle: `index.vsp`, `deploy-*.sql`, optional route SQL, optional facet/category SQL when requested, README/run notes outside the skill package, and verification queries.

Before writing or claiming completion, read `references/webdav-weblog-engine-gate.md` and run `scripts/validate_generated_weblog_bundle.py` against the generated bundle. If deployment credentials are unavailable, stop at the deployable bundle and state that live deployment is blocked by missing authenticated `isql`/WebDAV access. Do not substitute a static HTML lens as the answer.

The skill supports two interaction modalities, each with plain credential and TLS/WebID variants:

- **isql engine mode**: inspect or create the server-side weblog engine: VSP resource deployment, DAV path mapping assumptions, route/friendly URL setup, SQL helpers, full-text/search support, feed handling, metadata access, ACL/cache maintenance, and category staging. If the SQL listener is TLS-enabled, use `isql` with `-X` for the client PKCS#12 bundle, `-T` for the CA bundle, and `-W` for delegated WebID identity.
- **WebDAV post mode**: publish posts and assets only, by copying HTML files, Markdown files, and associated asset folders into the configured DAV collection. WebDAV can also read or set custom resource properties when the engine already supports them. If acting as a software agent for a principal, pass the principal WebID via the `On-Behalf-Of` HTTP header.
- **OPAL tool mode**: expose server-side weblog operations, such as post pinning, as Virtuoso stored procedures registered with `OAI.DBA.REGISTER_CHAT_FUNCTION`. Registered functions are available to OPAL/MCP-capable agents and are described through `/chat/functions/openapi.yaml`.

## First decisions

Establish these before editing or deploying:

- Target DAV collection, for example `/DAV/www2.openlinksw.com/data/html/`.
- Public route, for example `https://www.openlinksw.com/weblog/`.
- Deployment mode: `isql-engine`, `webdav-posts`, or `hybrid` where SQL bootstraps the engine and WebDAV publishes posts.
- Identity mode: SQL username/password, WebID-TLS client certificate, WebID-TLS plus delegation, WebDAV username/password, WebDAV mTLS, or WebDAV mTLS plus `On-Behalf-Of`.
- Variant: base weblog, OpenLink-site themed, or facet-enabled.
- Whether search, calendar date filtering, RSS/Atom/AtomPub links, `schema:category` facets, and scheduled category refresh are required.
- Metadata source for categories: existing WebDAV custom properties, an analysis TSV, SQL staging rows, or generated suggestions requiring user approval.
- Pinning policy: pinning is part of the core engine. On deployment, if no non-zero `schema:position` exists in the weblog collection, the current first post by recency is seeded as the default pinned item. The pinning tool maintains one pinned post per collection by clearing sibling `schema:position` values before setting the requested post. Manual metadata can still create multiple pinned posts, but the skill should treat that as drift to clean up.

## Workflow

1. Inspect the target collection or supplied SQL/VSP artifact before making assumptions. Exclude `._*`, `.DS_Store`, hidden macOS sidecar files, and non-post assets from post enumeration.
2. Before authoring VSP or SQL, search prior memory/work for `DAV_RES_UPLOAD_STRSES_INT`, `string_output`, `HTTP_PATH`, `index.vsp`, `raw <?vsp`, `vsp_user`, and `weblog-from-webdav`; reuse proven patterns and failure fixes.
3. Determine whether the weblog engine is already in place. Check that the target collection has an executable VSP entry point, working feed modes, collection-scoped search, date filtering, optional metadata facets, and the expected public route.
4. If the engine is missing or incomplete, switch to `isql-engine` setup. Start from the templates in `templates/`, patch paths, public URLs, title, and theme labels explicitly, then produce and, when credentials are available, deploy the complete VSP/isql bundle.
5. Validate the generated bundle with `scripts/validate_generated_weblog_bundle.py`. This gate is blocking for WebDAV weblog generation.
6. Use WebDAV only for post publication after the engine check passes: copy HTML files, Markdown files, and associated asset folders. For normal post uploads, use `scripts/publish_with_metadata.py` so each uploaded document also receives verified `schema:category` metadata through `PROPPATCH`. For out-of-band DAV uploads through mounted folders or third-party clients, install `templates/register-category-refresh-scheduler.sql` and schedule `DB.DBA.WEBLOG_DAV_REFRESH_CATEGORIES` with a default five-minute interval.
7. Use scoped search. In Virtuoso SQL, keep `contains` / `xcontains` as a top-level `AND` predicate and escape multi-word user input into a valid free-text expression.
8. Use calendar controls for date ranges in the sidebar, with `from` and `to` parameters preserved in filtered links.
9. Show category facets only when `schema:category` metadata exists. Facet counts must be computed from the filtered candidate set, not from all resources after a later display filter.
10. Support core and prompt-driven post pinning for a designated weblog. The engine deploy SQL seeds the newest valid post as the default pinned item only when no explicit pin exists. For user-requested changes, resolve the weblog target, verify the post resource exists, set `schema:position` to `1` for the designated post while clearing sibling pins, or reset it to `0` for unpinning, then verify the weblog order.
11. For agent-facing pinning, deploy `templates/register-weblog-pinning-tool.sql` through `isql`, register `DB.DBA.WEBLOG_DAV_SET_PIN`, and verify it appears in `OAI.DBA.LIST_CHAT_FUNCTIONS()` and the generated OpenAPI description at `/chat/functions/openapi.yaml`.
12. Preserve the recency-ordered post list in the sidebar, with pinned posts promoted ahead of ordinary recency and the first pinned post selected as the default current post. Pinned posts must have an obvious but restrained visual indicator: a compact red-headed pin badge in the sidebar and a non-overlapping status strip above embedded posts or a compact kicker for non-embedded posts. Facets, explicit post selection, and search refine that list; they do not replace it with monthly buckets.
13. Validate locally when possible, then verify the served route, feeds, search, date filters, facets, pinned ordering, registered OPAL tools, and a newly copied post.

## Mode references

- For engine checks and SQL bootstrap, read `references/isql-mode.md`.
- For post publication by WebDAV copy, read `references/webdav-mode.md`.
- For template behavior and known VSP pitfalls, read `references/vsp-template-contract.md`.
- For custom metadata and category facets, read `references/facet-metadata-contract.md`.
- For OPAL/OpenAPI/MCP tool exposure, read `references/opal-tool-mode.md`.

## Practical guardrails

- `DAV_RES_UPLOAD_STRSES_INT` needs a string session object such as `string_output()`, not a string literal passed to a reference parameter.
- Avoid `$1`, `$2`, and similar tokens in SQL loaded by `isql`; they can trigger macro substitution. Use named variables instead.
- Do not rely on `SET MACRO_SUBSTITUTION OFF` unless the target Virtuoso build accepts it; write scripts that avoid macro-looking text.
- Cast WebDAV property values before `trim`; Virtuoso can return integers for absent or encoded property states.
- Use `dict_iter_next` for category aggregate dictionaries; fragile key-list plus second lookup patterns can produce all-zero counts.
- Keep feed links resolvable. POSH discovery and visible RSS/Atom buttons should point at actual feed variants handled by the VSP route.
- In the weblog masthead/footer, use the positioning line `Showcasing the power of loosely coupling Linked Data, AI Agents, Skills, and Data Spaces - a Weblog view of WebDAV Folder`, with `WebDAV Folder` as the linked destination-generic anchor text. Wrap `Data Spaces` in a help affordance whose help text reads `databases, knowledge bases, filesystems, and APIs`.
- Treat the certificate-bearing identity and the delegated principal as separate facts: `-X` or `--cert` identifies the calling agent, while `-W` or `On-Behalf-Of` identifies the WebID principal whose ACL rights should be evaluated.
- Weblog post iframes must tolerate opaque or sandboxed embedded content: frame helpers should catch access denial, skip unreadable frames, and route same-origin WebDAV collection links to top-level navigation when readable.
- Never write credentials into the skill, generated SQL, VSP, logs, or committed files.
