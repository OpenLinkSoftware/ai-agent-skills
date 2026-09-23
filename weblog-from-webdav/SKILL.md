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
- Variant: base weblog, OpenLink-site themed, facet-enabled, or the general-purpose, parameterized `templates/deploy-weblog-skinned.sql` (any DAV collection/route, not fixed to one site).
- Whether search, calendar date filtering, RSS/Atom/AtomPub links, `schema:category` facets, and scheduled category refresh are required.
- Look-and-feel is itself a configuration modality when using `deploy-weblog-skinned.sql`: `weblog:skin` (`classic` default, or `editorial`) resolves at request time from a `?skin=` override, then a `weblog:skin` collection property, then the deploy-time default — no redeploy needed to switch. See `references/skin-authoring-contract.md`.
- Whether the newsletter feature (double opt-in subscribe, batched digest via the operator's own SMTP relay) is wanted: `weblog:newsletterEnabled` plus `templates/register-weblog-newsletter.sql`.
- Every outbound newsletter message (confirm, admin-import activation notice, admin-unsubscribe notice, and both digest sends) carries `Message-ID`, `List-Id`, `Precedence: bulk`, and — when a per-recipient unsubscribe link exists — `List-Unsubscribe` / `List-Unsubscribe-Post` (RFC 8058 one-click), built by `WEBLOG_NEWSLETTER_BULK_HEADERS`. These headers reduce spam-tagging risk but are not sufficient on their own: actual inbox placement is dominated by **SPF/DKIM/DMARC alignment on the sending domain and the SMTP relay** (`weblog:newsletterSmtpServer` / the server's default mail server), which this skill has no way to configure from VSP/SQL — that is the operator's mail infrastructure to set up.
- `weblog:adminEmail` (settable from the Email Server Config panel) is the site operator's own contact address, distinct from `weblog:newsletterFromAddress` (the subscriber-facing sender identity): it is used as `Reply-To` on every outbound newsletter message, and as the destination for operational alerts (a new confirmed subscriber, a digest batch with failed sends) via `WEBLOG_NEWSLETTER_NOTIFY_ADMIN`. Leaving it blank disables both, matching this skill's soft-fail-on-missing-config convention.
- **Blocking correctness requirement**: the `nl_action=confirm` and `nl_action=unsubscribe` links emailed to subscribers must never change subscription state on a plain GET request — only on POST. Mail-security gateways routinely prefetch every link found in an email with a GET to scan for phishing; if GET executed the action, that prefetch silently confirms or unsubscribes the real subscriber before they ever open the message (this happened live during development: adding `List-Unsubscribe` caused exactly this). `index.vsp`'s newsletter dispatcher checks the raw request line from `http_request_header()[0]` (`... like 'POST %'`) and, on GET, renders a confirmation page with a same-URL POST form instead of acting — a real POST (the human's click-through, or a mail client's `List-Unsubscribe-Post` one-click) is what actually performs the change. Do not "simplify" this back to a single GET-triggered action.
- Metadata source for categories: existing WebDAV custom properties, an analysis TSV, SQL staging rows, or generated suggestions requiring user approval.
- Pinning policy: pinning is part of the core engine. On deployment, if no non-zero `schema:position` exists in the weblog collection, the current first post by recency is seeded as the default pinned item. The pinning tool maintains one pinned post per collection by clearing sibling `schema:position` values before setting the requested post. Manual metadata can still create multiple pinned posts, but the skill should treat that as drift to clean up.

## Initial setup and upgrading an existing deployment

For `deploy-weblog-skinned.sql` deployments (the general-purpose, parameterized variant), both the FIRST deploy of a collection and an UPGRADE of one already running an older version of this skill's templates go through the same two files:

- `templates/register-weblog-newsletter.sql` — newsletter tables/procedures.
- `templates/deploy-weblog-skinned.sql` — the engine procedures, including `DB.DBA.WEBLOG_DAV_DEPLOY_SKINNED`, the actual deploy/redeploy call.

Both are idempotent installers: each `DROP`s then recreates its own procedures, so reinstalling either one is always safe to repeat. `WEBLOG_DAV_DEPLOY_SKINNED` itself is also safe to re-run against an already-deployed collection — it reads and preserves existing `weblog:*` collection properties (skin choice, newsletter config, admin email, etc.) and only refreshes `index.vsp`/`dashboard.html`, so redeploying an existing site picks up every template change (new admin panels, header/deliverability fixes, UI redesigns) with zero configuration loss. The one non-idempotent part is `register-weblog-newsletter.sql`'s `WEBLOG_SUBSCRIBER` table (`DROP`+`CREATE`, wiping subscribers on every reinstall) — `templates/upgrade.sql` (below) backs this up automatically; running `register-weblog-newsletter.sql` directly, on its own, does not.

`templates/upgrade.sql` is a single-file convenience wrapper — a concatenation of both templates above, automatic pre-flight backups, and an auto-detecting redeploy call — for handing to an operator who wants to apply the upgrade via their own working `isql` session, without needing to locate and run three separate files in order, remember to back anything up first, or hand-edit connection parameters per site. Before Section 1 drops `WEBLOG_SUBSCRIBER`, its current contents (if any) are copied into a fresh, timestamped `WEBLOG_SUBSCRIBER_BACKUP_<timestamp>` table; before the REDEPLOY block overwrites `index.vsp`/`dashboard.html`, their current content (if any) is copied into `DB.DBA.WEBLOG_UPGRADE_BACKUP`. Neither backup table is ever dropped by a later run, and restore steps are documented in-line as comments right above each backup block. This makes "can I revert if it fails" true by default for what this file changes — it is not a substitute for backing up anything else on the target instance.

Before the REDEPLOY block, `TMP_WEBLOG_UPGRADE_GRANT_ROLE` sets up a `WEBLOG_OPERATOR` SQL role and grants it `EXECUTE` on every `DB.DBA.WEBLOG_*` procedure this skill installs, then grants that role to `kidehen`. This exists because Virtuoso does not auto-grant execute on a new object to anyone but its owner/`dba` — verified live 2026-09-23 that a non-`dba`, non-owner session (a WebID-TLS connection mapped to a restricted account) gets `SR186:SECURITY: No permission to execute procedure` calling any of these by default. Idempotent and safe to re-run: the role is created once and reused, every matching procedure is re-granted on each run (so a procedure a future template change adds gets covered automatically), and `GRANT <role> TO <user>` — unlike `GRANT EXECUTE ON <object>` — is **not** idempotent on its own (a second grant to an existing member errors with `U0013`), so the script checks `__SQL_MESSAGE` for that specific case rather than treating any grant failure as fatal. Add another designated user with `grant WEBLOG_OPERATOR to <username>;`, run once as `dba`.

The REDEPLOY block ends with `TMP_WEBLOG_UPGRADE_AUTODETECT`, which figures out WHICH known site the connected instance is by checking which of the registered `DAV_COLLECTION`s already has an `index.vsp` (each Virtuoso instance has its own siloed DAV tree, so a match is unambiguous) — no manual host/collection editing needed for a site already registered in it. It never guesses: an instance matching none of the registered sites (a genuinely new site, or a first-ever install with nothing deployed yet to detect from) gets a clear `{"ok":false,"reason":...}` diagnostic instead of a deploy. Register a new site by adding an `else if` branch to that procedure's detection logic; a first-ever install (nothing to auto-detect) needs `DB.DBA.WEBLOG_DAV_DEPLOY_SKINNED` called directly with explicit parameters instead.

This file is a dated snapshot, not a maintained source of truth: regenerate it (concatenate the two source templates plus fresh backup/redeploy/auto-detect blocks) whenever either source template changes materially, rather than trusting a stale copy indefinitely.

CAUTION when writing `CREATE TABLE ... AS SELECT` in Virtuoso SQL: verified live 2026-09-23 that it copies structure ONLY, not rows — a bare CTAS silently produces an empty "backup". Always follow it with an explicit `INSERT ... SELECT` to actually copy data, as `templates/upgrade.sql`'s subscriber-backup step does. Also, a stored procedure body cannot directly `INSERT`/`SELECT` against a table that does not exist yet at compile time (Virtuoso resolves table references at procedure-compile time, not deferred to call time) — a table a procedure will write to must already exist before that `CREATE PROCEDURE` statement runs, even behind a runtime existence check.

When this skill is used to check or upgrade a **remote, already-deployed** collection, first fetch the public route read-only (HTTP GET, no credentials needed) to identify which template generation it's running — the presence/absence of `class="theme-switch"` vs the older `class="theme-toggle"`, a `/weblog-admin/` dashboard route, `Subscribe`/newsletter markup, `facet` support — before assuming credentials or a redeploy are needed.

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
- For the config-driven skin mechanism and how to add a new skin, read `references/skin-authoring-contract.md`.
- For initial setup or upgrading an existing `deploy-weblog-skinned.sql` deployment, see "Initial setup and upgrading an existing deployment" above and `templates/upgrade.sql`.

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
- A `.vsp` resource only executes when `WS.WS.SYS_DAV_RES.RES_OWNER` is the `dav` user (uid 2); any other owner serves it as raw static source with no error. Always upload with `DB.DBA.DAV_RES_UPLOAD_STRSES_INT(path, stream, mime, perms, 'dav', 'dav', ...)` regardless of which account is deploying. See `agent-rdf-memory/howto/osdi-vsp-execution-registration.ttl`.
- A VHOST route with `is_brws=>0` and `def_page` dispatches **every** path under it to that default page, including a post's own filename — there is no way to reach an individual DAV resource directly through that route. Serve raw post content through a query param on the same route (`?raw=<filename>`, validated against an enumerated resource) instead of assuming a nested path or a second VHOST mapping will reach the file; a sibling `is_brws=>1` VHOST hit a 401 in testing and a nested path is captured by the parent route's own catch-all.
- A POST to a nested `.vsp` path under an `is_brws=>0` VHOST route gets redirected (trailing slash appended), which silently downgrades the request to GET and drops the form body. Route form submissions through the collection's existing `index.vsp` via a query param instead of a dedicated endpoint file.
- **Remote uploads and removals** use HTTP first, then WebDAV, then iSQL, with the principal PKCS#12 path plus `/tmp/uyi` (`howto/remote-webdav-upload.ttl`, `howto/remote-resource-removal.ttl`, prefs Steps 215–216). URIBurner operations use port 5443. Verify PUT and DELETE against the public URL and `:5443` before claiming success.
