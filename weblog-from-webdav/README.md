# Weblog From WebDAV

Turn a Virtuoso WebDAV collection of HTML or Markdown documents into a working weblog — feeds, search, categories, pinning, a password-protected admin dashboard, and an optional email newsletter — with no separate CMS or database.

## Overview

Point this skill at a WebDAV collection full of posts and it generates a self-contained `index.vsp` (the public weblog) plus a separate, non-public admin dashboard. Everything else — look and feel, the newsletter, email messages, category tags, pinned posts — is a **configuration modality**: a property you set on the collection, read at request time, changeable without a redeploy.

For the full technical reference (deploy modes, identity/auth options, VSP internals, gotchas found in production), see `SKILL.md`. This file covers the user-facing features.

## Quick Start: one file installs and upgrades

`templates/upgrade.sql` is the single file for a **fresh install** and for **every upgrade**. Edit its TARGET block at the top, then run it as `dba`:

```sql
create procedure DB.DBA.TMP_WEBLOG_UPGRADE_TARGET ()
{
  return vector (
    '/DAV/home/dba/my-weblog/',   -- DAV collection of posts (created if it doesn't exist)
    'example.org',                -- public host
    '/weblog/',                   -- public path
    0,                            -- allow_template_overwrite (see below)
    0,                            -- dry_run: 1 = print the plan, change nothing
    '',                           -- admin collection ('' = default)
    'My Weblog',                  -- title          } masthead: fill in for a fresh
    'A weblog powered by WebDAV.',-- tagline        } install; leave blank on an
    '', '', '', '');              -- tagline link / help tooltip } upgrade to keep it
}
;
```

```bash
isql <host>:<port> dba <password> upgrade.sql
```

It works the same from Conductor's Interactive SQL, which reports one harmless `SR077: Bad option for SET` near the end.

The run ends with a JSON report of every value it used and where each came from: `given` (the TARGET block), `recorded` (saved by an earlier deploy), `current index.vsp` (read from the live page), or `default`. Set `dry_run` to 1 first to see that plan without changing anything.

## Modalities

### Skins

Two built-in looks, switchable per request (`?skin=editorial`) or per collection (`weblog:skin`, the admin dashboard's Skin setting) — no redeploy needed:

- **classic** — sidebar archive + search/filter, a single embedded post.
- **editorial** — a large single-column hero post with a card-grid archive below.

Adding a new skin is a template change; see `references/skin-authoring-contract.md`.

### Admin dashboard

A separate, non-public collection (never inside the public blog folder, so it never inherits whatever makes the blog itself public) serves a password-protected dashboard at `{public path}-admin/` (e.g. `/weblog-admin/`), over HTTPS. It covers:

- **Trends & Analytics** — sign-ups and confirmations over the last 30 days, confirmation rate, 26-week charts (subscribers, sign-ups, posts), top countries and categories.
- **Subscribers** — the list, manual unsubscribe, and import (CSV, RDF, manual entry).
- **Delivery settings, Email Server Config, Email Templates** — see **Email messages** below.
- **Tagging & Scheduling** — per-post category and pin, digest and dashboard-refresh schedules.

Access is native HTTP Digest authentication against real Virtuoso accounts — the weblog's recorded admin user, members of the `WEBLOG_OPERATOR` role, and `dba` (which `upgrade.sql` adds to that role) — no shared secrets, no tokens embedded in a page.

### Newsletter

Double opt-in email subscription, sent through the operator's own SMTP relay:

1. Enable it: `weblog:newsletterEnabled = 'true'`.
2. A **Subscribe** button appears next to RSS/Atom, opening an in-page dialog — visitors never leave the article they're reading. The dialog asks for an email and, optionally, a country from an ISO 3166-1 drop-down (stored as the 2-letter code, never free text).
3. New subscribers confirm by email before being added; digests (or immediate per-post sends) go out on a schedule you control from the dashboard.
4. Manual entry, CSV import, and RDF (`schema:Person`) import are available from the dashboard for bringing in an existing list; imported subscribers get a welcome email.

Set the sender (From name and address), the SMTP relay, and the base URL for email links in the dashboard's **Email Server Config**. The newsletter's tables and procedures are installed by `upgrade.sql`.

### Email messages

Every email — confirmation, welcome (for imported subscribers), unsubscribe notice, digest, and immediate per-post — uses one newsletter layout: a logo, the weblog's name once in the masthead, then the message or posts (serif title, subtitle, date and reading time, a "Read the full post" button), and a footer with an unsubscribe link. Each is sent as plain text plus HTML, built to render in Gmail, Outlook and Apple Mail.

- **Templates.** The dashboard's **Email Templates** panel edits every email's subject, and the body of the confirmation, welcome and unsubscribe-notice emails (plus an optional digest intro). **Reset to Default** restores the built-in text. Separate paragraphs with a blank line; a line containing only a URL becomes a link.
- **Placeholders** in the welcome email: `{{NAME}}` and `{{FIRST_NAME}}` ("Subscriber" when no name was imported), `{{EMAIL}}`, `{{ADMIN_NAME}}` (the **Admin name** setting, else the sender name), `{{WEBLOG_TITLE}}`, `{{WEBLOG_URL}}`. `{{UNSUBSCRIBE_URL}}` is optional — every email carries an unsubscribe link anyway.
- **Per-import message.** Each import form (CSV, RDF, manual entry) has an optional "Welcome email for this import" subject and message, used for that batch only.
- **Logo.** **Logo image URL** in Email Server Config: blank shows OpenLink's logo, `none` shows no logo, anything else is your own image (PNG/JPEG/GIF — email clients don't show SVG).

### WebDAV Permalink

Every post view shows a **WebDAV Permalink** — the post's real, absolute URL on the underlying WebDAV collection — separate from the weblog's own `?post=` view URL. Useful for citing or bookmarking the actual resource rather than a query-string view of it.

### Feeds

RSS 2.0, Atom 1.0, and AtomPub are generated automatically from the same post list the weblog itself renders — no separate feed file to keep in sync.

### Category tags and pinning

Posts can carry a `schema:category` tag (shown as a filterable facet in the sidebar) and a pin (`schema:position`) to feature a post ahead of normal recency — both editable from the admin dashboard, or via `templates/register-weblog-pinning-tool.sql` for agent-driven pinning.

Categories can also be **derived from each post's content**: `scripts/publish_with_metadata.py` tags posts as it uploads them, and `templates/register-category-refresh-scheduler.sql` installs `WEBLOG_DAV_REFRESH_CATEGORIES`, which tags any post that has no category yet (run once, or on a schedule for posts copied in by other means). Existing categories are never overwritten.

## Upgrades are never destructive

Running `upgrade.sql` against an already-deployed weblog is always safe:

- **Settings are kept.** Every `weblog:*` setting — skin, newsletter and email configuration, templates, masthead, admin location — is preserved; only the page and dashboard are regenerated.
- **Backups first.** The current `index.vsp` and `dashboard.html` are copied into `DB.DBA.WEBLOG_UPGRADE_BACKUP`, and the subscriber table into a timestamped `WEBLOG_SUBSCRIBER_BACKUP_*` table, before anything is replaced. Restore steps are in the file's comments.
- **Hand-built pages are protected.** If the collection's `index.vsp` was not generated by this skill (for example, an older hand-authored template), the upgrade refuses to replace it. To migrate such a site, review the plan with `dry_run`, then set `allow_template_overwrite` to 1 for that one run: posts, categories, pins and existing `?post=`/`?q=`/`?category=`/`?feed=` URLs carry over, and the old masthead is read from the old page.
- **Dry run.** `dry_run = 1` shows exactly what would be deployed, and where each value came from, without changing anything.

## File Structure

```
weblog-from-webdav/
├── SKILL.md                              # Full technical reference
├── README.md                             # This file
├── templates/
│   ├── upgrade.sql                       # THE install/upgrade file (both templates below + backups)
│   ├── deploy-weblog-skinned.sql         # Engine: page, dashboard routes, WEBLOG_UPGRADE
│   ├── register-weblog-newsletter.sql    # Newsletter, email messages, dashboard
│   ├── register-weblog-pinning-tool.sql  # Agent-facing post pinning
│   ├── register-category-refresh-scheduler.sql  # Content-derived categories
│   ├── deploy-weblog-opl-site.sql        # Legacy fixed, single-site OpenLink-themed deploy
│   └── deploy-weblog-opl-site-facet.sql  # ...same, with facet support
├── references/                           # Deep-dive contracts (skins, facets, VSP internals)
└── scripts/
    ├── publish_with_metadata.py          # Post upload + content-derived schema:category
    └── validate_weblog_bundle.py         # Bundle marker checks
```

## Requirements

- A Virtuoso Server instance with WebDAV enabled and `isql` (or Conductor) access as `dba` — plain SQL, or WebID-TLS/mTLS.
- A WebDAV collection for the posts (HTML or Markdown); `upgrade.sql` creates it if its parent exists.
- For the newsletter: an SMTP relay reachable from the Virtuoso instance (set in Email Server Config, or the server's own default mail configuration), a From address, and the base URL for email links.

## Limitations

- One admin identity model per collection: the account in `weblog:adminDavUser`, plus members of the `WEBLOG_OPERATOR` role, plus `dba`.
- The newsletter's "immediate" and "digest" send modes cover most cases, but there is no per-subscriber send-time customization.
- Unsubscribes aren't timestamped, so the dashboard's subscriber trend can't subtract them.
- Feed and search results are scoped to the single WebDAV collection being served — this is not a multi-collection aggregator.

## Version

See `CHANGELOG.md` if present, or `SKILL.md` for the most recent verified-live changes.
