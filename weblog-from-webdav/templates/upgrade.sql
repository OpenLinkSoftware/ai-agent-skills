-- ============================================================================
-- upgrade.sql -- single-file setup/upgrade for a weblog-from-webdav
-- deployment (templates/deploy-weblog-skinned.sql), for manual application
-- via your own working isql session.
--
-- WHAT THIS IS
--   A concatenation, as of the date below, of:
--     1. templates/register-weblog-newsletter.sql
--     2. templates/deploy-weblog-skinned.sql
--   plus automatic pre-flight backups and one final call to (re)deploy the
--   target collection's index.vsp and admin dashboard. Both source files
--   are idempotent installers (each DROPs then recreates its own
--   procedures). Running this file end to end is equivalent to reinstalling
--   both templates by hand and then (re)deploying -- and covers a FIRST-EVER
--   deploy just as well as an upgrade of an existing one; there is no
--   separate "initial setup" script.
--
-- WHEN TO REGENERATE INSTEAD OF REUSING THIS COPY
--   This file is a SNAPSHOT, not a maintained source of truth. If
--   templates/register-weblog-newsletter.sql or templates/deploy-weblog-skinned.sql
--   change after the date below, regenerate this file rather than trusting
--   a stale copy.
--
-- AUTOMATIC PRE-FLIGHT BACKUPS (added 2026-09-23 -- see each backup block's
-- own comments below for exact restore steps)
--   1. Before Section 1 DROPs and recreates WEBLOG_SUBSCRIBER, its current
--      contents (if any) are copied into a fresh, timestamped
--      WEBLOG_SUBSCRIBER_BACKUP_<timestamp> table -- never overwritten by a
--      later run.
--   2. Before the REDEPLOY block overwrites index.vsp/dashboard.html, their
--      current content (if any) is copied into DB.DBA.WEBLOG_UPGRADE_BACKUP
--      (created on first use, never dropped by a reinstall).
--   These make "can I revert if this fails" true by default -- but they
--   only cover what THIS file changes. They are not a substitute for your
--   own backup of anything else on the target instance.
--
-- HOW TO RUN
--   isql <host>:<port> <user> <password> upgrade.sql
--   (plain SQL login, or WebID-TLS with -X <cert.p12> -T <CA bundle> --
--    whatever already works for isql against this target)
--
-- AFTER RUNNING SECTIONS 1-2
--   Edit the DB.DBA.WEBLOG_DAV_DEPLOY_SKINNED call arguments in the
--   REDEPLOY block at the very end of this file for your target
--   collection/route before running it (or run that block on its own,
--   separately, any time afterward -- it is safe and idempotent to re-run).
--
-- Generated from weblog-from-webdav templates as of 2026-09-23.
-- ============================================================================

-- ============================================================================
-- PRE-FLIGHT BACKUP 1 of 2 -- WEBLOG_SUBSCRIBER, before Section 1 drops and
-- recreates it. Runs automatically, every time this file is run. Best-effort
-- (a missing table on a first-ever install is not an error -- there is
-- nothing to back up yet).
--
-- Each run creates its OWN timestamped table, e.g.
-- WEBLOG_SUBSCRIBER_BACKUP_20260923_143012 -- never overwritten by a later
-- run, so every prior upgrade's subscriber snapshot stays available.
--
-- TO RESTORE from a backup table (only if Section 1 below actually ran and
-- lost data you need back -- check first, most reinstalls need no restore):
--   insert into DB.DBA.WEBLOG_SUBSCRIBER
--     (WS_DAV_COLLECTION, WS_EMAIL, WS_NAME, WS_COUNTRY, WS_STATUS, WS_TOKEN,
--      WS_SUBSCRIBED_AT, WS_CONFIRMED_AT, WS_LAST_SENT_AT)
--   select WS_DAV_COLLECTION, WS_EMAIL, WS_NAME, WS_COUNTRY, WS_STATUS, WS_TOKEN,
--          WS_SUBSCRIBED_AT, WS_CONFIRMED_AT, WS_LAST_SENT_AT
--   from DB.DBA.WEBLOG_SUBSCRIBER_BACKUP_<timestamp-of-the-run-you-want>;
-- (the unique index on (WS_DAV_COLLECTION, WS_EMAIL) means a restore after
-- new signups already landed will skip/conflict on overlapping rows -- check
-- for conflicts first if the table is not empty.)
-- ============================================================================

create procedure DB.DBA.TMP_WEBLOG_UPGRADE_BACKUP_SUBSCRIBERS ()
{
  declare ts, backup_table_name varchar;
  declare dot_pos int;
  declare exit handler for sqlstate '*' { return 'Pre-flight subscriber backup skipped (no existing WEBLOG_SUBSCRIBER table to back up -- fine on a first-ever install).'; };
  if ((select count (*) from SYS_COLS where "TABLE" = 'DB.DBA.WEBLOG_SUBSCRIBER') = 0)
    return 'No existing WEBLOG_SUBSCRIBER table -- nothing to back up (first-ever install).';
  ts := replace (replace (replace (cast (now () as varchar), '-', ''), ':', ''), ' ', '_');
  dot_pos := strchr (ts, '.');
  if (dot_pos is not null) ts := subseq (ts, 0, dot_pos);
  backup_table_name := sprintf ('DB.DBA.WEBLOG_SUBSCRIBER_BACKUP_%s', ts);
  -- CREATE TABLE ... AS SELECT copies STRUCTURE ONLY in this Virtuoso build
  -- (verified live 2026-09-23) -- the data must be copied with a separate
  -- INSERT ... SELECT, never assume CTAS alone backs up rows.
  exec (sprintf ('create table %s as select * from DB.DBA.WEBLOG_SUBSCRIBER', backup_table_name));
  exec (sprintf ('insert into %s select * from DB.DBA.WEBLOG_SUBSCRIBER', backup_table_name));
  return sprintf ('Backed up WEBLOG_SUBSCRIBER to %s before reinstalling.', backup_table_name);
}
;
select DB.DBA.TMP_WEBLOG_UPGRADE_BACKUP_SUBSCRIBERS ();
drop procedure DB.DBA.TMP_WEBLOG_UPGRADE_BACKUP_SUBSCRIBERS;


-- ============================================================================
-- SECTION 1 of 2: templates/register-weblog-newsletter.sql
-- ============================================================================

-- Register the double-opt-in, batch-digest newsletter feature for a
-- weblog-from-webdav collection deployed by deploy-weblog-skinned.sql.
-- Run as: isql 1111 dba <password> register-weblog-newsletter.sql
--
-- Requires deploy-weblog-skinned.sql to already be installed (it defines
-- DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP, the shared collection-level config
-- property reader both index.vsp and the procedures below use).
--
-- Mail is sent through the operator's own SMTP relay: weblog:newsletterSmtpServer
-- if set on the collection, else the same relay DB.DBA.WA_SEND_MAIL already
-- uses (WA_SETTINGS.WS_SMTP, or virtuoso.ini [HTTPServer] DefaultMailServer
-- when WA_SETTINGS.WS_USE_DEFAULT_SMTP=1) -- no external ESP involved.
--
-- Config properties (set with DB.DBA.DAV_PROP_SET on the collection path):
--   weblog:newsletterEnabled           'true' | 'false' (default false; read by index.vsp)
--   weblog:newsletterFromAddress       e.g. 'news@example.org'
--   weblog:newsletterFromName          e.g. 'My Weblog'
--   weblog:newsletterConfirmBaseUrl    absolute scheme+host, e.g. 'http://localhost:8890'
--                                      (index.vsp's ?nl_action=subscribe handler
--                                      derives this from the request when possible;
--                                      this is the fallback, used by the digest
--                                      scheduler which has no request context)
--   weblog:newsletterDigestIntervalMinutes  integer minutes (default 10080 = weekly)
--   weblog:newsletterMirrorRdf         'true' | 'false' (default true)
--   weblog:newsletterSmtpServer        optional SMTP relay override
--   weblog:newsletterContentMode       'auto' (default) | 'snippet' | 'full' --
--                                      what goes in the email body per post.
--                                      'auto' sends a short lede/tagline
--                                      snippet for this skill's own detected
--                                      interactive infographics (floating
--                                      nav present) and the full post body
--                                      for a plain prose post -- mirrors how
--                                      Substack sends full content inline
--                                      for an ordinary post but falls back
--                                      to "read in app" for anything more
--                                      elaborate. 'snippet' or 'full' forces
--                                      that choice for every post. See
--                                      WEBLOG_NEWSLETTER_POST_EXCERPT.
--
-- weblog:publicRoute is set automatically by deploy-weblog-skinned.sql --
-- it is how these procedures build web-facing confirm/unsubscribe links
-- that point at the public route rather than the internal DAV collection
-- path, which need not match.

CREATE PROCEDURE DB.DBA.TMP_WEBLOG_NEWSLETTER_DROP ()
{
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_UNSCHEDULE_DIGEST'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_SCHEDULE_DIGEST'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_SEND_DIGEST'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_HTML_SHELL'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_POST_CARD'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_POST_EXCERPT'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_IS_INFOGRAPHIC'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_FIND_TAGGED_TEXT'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_EXTRACT_STYLE_BLOCKS'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_STRIP_ELEMENT'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_STRIP_BLOCK'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_POST_TITLE'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_MIRROR_RDF'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_IMPORT_RDF'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_IMPORT_CSV'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_IMPORT_ONE'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_SEND_ACTIVATION'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_SEND_UNSUBSCRIBE_NOTICE'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_UNSUBSCRIBE'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_CONFIRM'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_SUBSCRIBE'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_NOTIFY_ADMIN'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_BULK_HEADERS'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_RESOLVE_SMTP'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP TABLE DB.DBA.WEBLOG_SUBSCRIBER'); }
}
;
DB.DBA.TMP_WEBLOG_NEWSLETTER_DROP ();
DROP PROCEDURE DB.DBA.TMP_WEBLOG_NEWSLETTER_DROP;

CREATE TABLE DB.DBA.WEBLOG_SUBSCRIBER
(
  WS_ID INTEGER IDENTITY,
  WS_DAV_COLLECTION VARCHAR,
  WS_EMAIL VARCHAR,
  WS_NAME VARCHAR,
  WS_COUNTRY VARCHAR,
  WS_STATUS VARCHAR,
  WS_TOKEN VARCHAR,
  WS_SUBSCRIBED_AT DATETIME,
  WS_CONFIRMED_AT DATETIME,
  WS_LAST_SENT_AT DATETIME,
  PRIMARY KEY (WS_ID)
)
;

CREATE UNIQUE INDEX WEBLOG_SUBSCRIBER_UQ ON DB.DBA.WEBLOG_SUBSCRIBER (WS_DAV_COLLECTION, WS_EMAIL);

-- Resolve the SMTP relay the same way DB.DBA.WA_SEND_MAIL does, honoring a
-- per-collection override first.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_RESOLVE_SMTP (IN dav_collection VARCHAR)
{
  declare smtp_server VARCHAR;
  smtp_server := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (dav_collection, 'weblog:newsletterSmtpServer', '');
  if (smtp_server is not null and trim (smtp_server) <> '')
    return trim (smtp_server);
  if ((select max (WS_USE_DEFAULT_SMTP) from WA_SETTINGS) = 1 or (select max (WS_SMTP) from WA_SETTINGS) is null)
    return cfg_item_value (virtuoso_ini_path (), 'HTTPServer', 'DefaultMailServer');
  return (select max (WS_SMTP) from WA_SETTINGS);
}
;

-- Shared bulk-mail headers (Message-ID, List-Id, Precedence, and -- when a
-- per-recipient unsubscribe link is available -- List-Unsubscribe /
-- List-Unsubscribe-Post) for every outbound newsletter message. Returns an
-- \r\n-terminated header block ready to splice between the existing
-- Date/Subject/Content-Type headers and the blank line that starts the body.
-- These headers reduce spam-tagging risk (missing Message-ID is itself a
-- negative signal; List-Unsubscribe/-Post is what lets Gmail/Yahoo/Outlook
-- show a native one-click Unsubscribe control) but do NOT substitute for
-- SPF/DKIM/DMARC alignment on the sending domain and relay, which this VSP
-- code has no way to configure -- see SKILL.md.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_BULK_HEADERS (IN dav_collection VARCHAR, IN from_addr VARCHAR, IN from_name VARCHAR, IN recipient_email VARCHAR, IN unsub_url VARCHAR := null)
{
  declare coll, domain, list_slug, list_id, msg_id, hdrs, admin_email VARCHAR;
  declare at_pos, i INTEGER;

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';

  domain := 'localhost';
  at_pos := strchr (coalesce (from_addr, ''), '@');
  if (at_pos is not null and at_pos >= 0 and at_pos < length (from_addr) - 1)
    domain := trim (subseq (from_addr, at_pos + 1, length (from_addr)));
  if (domain = '') domain := 'localhost';

  -- List-Id (RFC 2919) identifies the list itself, not the message -- one
  -- stable slug per collection, sanitized to lowercase alnum + '-' since the
  -- public route is a URL path, not a valid header-safe token as-is.
  list_slug := lower (trim (DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:publicRoute', coll)));
  {
    declare out_s, ch VARCHAR;
    out_s := '';
    for (i := 0; i < length (list_slug); i := i + 1)
    {
      ch := subseq (list_slug, i, i + 1);
      if ((ch >= 'a' and ch <= 'z') or (ch >= '0' and ch <= '9'))
        out_s := out_s || ch;
      else if (out_s <> '' and subseq (out_s, length (out_s) - 1, length (out_s)) <> '-')
        out_s := out_s || '-';
    }
    while (length (out_s) > 0 and subseq (out_s, length (out_s) - 1, length (out_s)) = '-')
      out_s := subseq (out_s, 0, length (out_s) - 1);
    if (out_s = '') out_s := 'weblog';
    list_slug := out_s;
  }
  list_id := sprintf ('%s <%s.%s>', coalesce (from_name, 'Weblog Newsletter'), list_slug, domain);

  msg_id := sprintf ('<%s@%s>', md5 (concat (coalesce (recipient_email, ''), cast (now () as varchar), cast (rnd (1000000000) as varchar), cast (rnd (1000000000) as varchar))), domain);

  hdrs := sprintf ('Message-ID: %s\r\nList-Id: %s\r\nPrecedence: bulk\r\nAuto-Submitted: auto-generated\r\n', msg_id, list_id);
  if (unsub_url is not null and trim (unsub_url) <> '')
    hdrs := hdrs || sprintf ('List-Unsubscribe: <%s>\r\nList-Unsubscribe-Post: List-Unsubscribe=One-Click\r\n', trim (unsub_url));

  -- Reply-To the operator's own address (weblog:adminEmail) rather than the
  -- From address -- From often stays a stable noreply-style identity for
  -- SPF/DKIM alignment, while replies should land somewhere a human reads.
  admin_email := trim (DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:adminEmail', ''));
  if (admin_email <> '')
    hdrs := hdrs || sprintf ('Reply-To: %s\r\n', admin_email);

  return hdrs;
}
;

-- Operational alert to the site operator (weblog:adminEmail) -- NOT
-- subscriber-facing mail, so no bulk-mail headers here. Silent no-op
-- (returns 0) if no admin email or no mail server is configured, matching
-- this file's soft-fail-on-missing-config convention throughout.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_NOTIFY_ADMIN (IN dav_collection VARCHAR, IN subject_suffix VARCHAR, IN body_text VARCHAR)
{
  declare coll, admin_email, from_addr, from_name, smtp_server, subj, msg VARCHAR;
  declare exit handler for sqlstate '*' { return 0; };

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';

  admin_email := trim (DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:adminEmail', ''));
  if (admin_email = '') return 0;

  from_name := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterFromName', 'Weblog Newsletter');
  from_addr := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterFromAddress', 'noreply@localhost');

  smtp_server := DB.DBA.WEBLOG_NEWSLETTER_RESOLVE_SMTP (coll);
  if (smtp_server is null or trim (smtp_server) = '') return 0;

  subj := sprintf ('%s admin: %s', from_name, subject_suffix);
  msg := sprintf ('Date: %s\r\nSubject: %s\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n%s\r\n', date_rfc1123 (now ()), subj, body_text);

  smtp_send (smtp_server, sprintf ('%s <%s>', from_name, from_addr), admin_email, msg);
  return 1;
}
;

CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_SUBSCRIBE (IN dav_collection VARCHAR, IN email VARCHAR, IN country VARCHAR, IN confirm_base_url VARCHAR)
{
  declare coll, tok, from_addr, from_name, confirm_base, public_route, smtp_server, subj, body, existing_status VARCHAR;
  declare existing_count INTEGER;

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';
  if (email is null) email := '';
  -- Lowercased, not just trimmed: WEBLOG_SUBSCRIBER_UQ's unique index is on
  -- the literal (WS_DAV_COLLECTION, WS_EMAIL) VARCHAR pair, so without this
  -- "John@x.com" and "john@x.com" would pass it as two distinct rows for
  -- what is the same real address -- duplicate prevention belongs in the
  -- key structure, not a runtime check, so every write path canonicalizes
  -- to the same case the index actually compares.
  email := lower (trim (email));
  if (email = '' or strchr (email, '@') is null or strchr (email, '.') is null)
    return 'Please provide a valid email address.';

  existing_count := 0;
  existing_status := null;
  for (select WS_STATUS as _s from DB.DBA.WEBLOG_SUBSCRIBER
        where WS_DAV_COLLECTION = coll and WS_EMAIL = email) do
  {
    existing_count := existing_count + 1;
    existing_status := _s;
  }

  if (existing_count > 0 and existing_status = 'confirmed')
    return 'You are already subscribed.';

  tok := md5 (concat (email, cast (now () as varchar), cast (rnd (1000000000) as varchar), cast (rnd (1000000000) as varchar)));

  if (existing_count > 0)
  {
    update DB.DBA.WEBLOG_SUBSCRIBER
       set WS_TOKEN = tok, WS_STATUS = 'pending', WS_COUNTRY = country, WS_SUBSCRIBED_AT = now ()
     where WS_DAV_COLLECTION = coll and WS_EMAIL = email;
  }
  else
  {
    insert into DB.DBA.WEBLOG_SUBSCRIBER (WS_DAV_COLLECTION, WS_EMAIL, WS_COUNTRY, WS_STATUS, WS_TOKEN, WS_SUBSCRIBED_AT)
      values (coll, email, country, 'pending', tok, now ());
  }

  from_name := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterFromName', 'Weblog Newsletter');
  from_addr := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterFromAddress', 'noreply@localhost');
  confirm_base := trim (coalesce (confirm_base_url, ''));
  if (confirm_base = '')
    confirm_base := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterConfirmBaseUrl', '');
  -- Links must point at the PUBLIC route, not the internal DAV path -- the
  -- deploy proc records this as a collection property since it's the only
  -- place that ever tells us the two need not match.
  public_route := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:publicRoute', coll);

  smtp_server := DB.DBA.WEBLOG_NEWSLETTER_RESOLVE_SMTP (coll);
  if (smtp_server is null or trim (smtp_server) = '')
    return 'Subscribed -- but no mail server is configured yet. Ask the site operator to set weblog:newsletterSmtpServer or the server DefaultMailServer, then subscribe again to get a confirmation link.';

  subj := concat (from_name, ': confirm your subscription');
  body := sprintf (
    'Please confirm your subscription by opening this link:\r\n\r\n%s%s?nl_action=confirm&token=%s\r\n\r\nIf you did not request this, ignore this message -- you will not be subscribed unless you click the link above.\r\n',
    confirm_base, public_route, tok);

  {
    declare unsub_url, bulk_hdrs VARCHAR;
    declare exit handler for sqlstate '*'
    {
      return 'Subscribed -- but the confirmation email could not be sent right now (the mail server is unreachable). Ask the site operator to check weblog:newsletterSmtpServer / the server mail configuration, then request the confirmation link again.';
    };
    -- The token already resolves against WEBLOG_NEWSLETTER_UNSUBSCRIBE even
    -- while still 'pending', so this is a real, working escape hatch, not
    -- just a header placeholder.
    unsub_url := sprintf ('%s%s?nl_action=unsubscribe&token=%s', confirm_base, public_route, tok);
    bulk_hdrs := DB.DBA.WEBLOG_NEWSLETTER_BULK_HEADERS (coll, from_addr, from_name, email, unsub_url);
    smtp_send (smtp_server, sprintf ('%s <%s>', from_name, from_addr), email,
      sprintf ('Date: %s\r\nSubject: %s\r\n%sContent-Type: text/plain; charset=UTF-8\r\n\r\n%s', date_rfc1123 (now ()), subj, bulk_hdrs, body));
  }

  return 'Almost there -- check your inbox and click the confirmation link.';
}
;

-- Assert or retract schema:Person/schema:email triples for a confirmed
-- subscriber. assert_flag: 1 = assert, 0 = retract. Uses the standard
-- Virtuoso idiom of executing a SPARQL statement string via exec() for
-- writes (inline `(sparql ...)` subquery syntax only covers SELECT).
-- name is optional (default null, meaning "no schema:name triple") --
-- WEBLOG_NEWSLETTER_UNSUBSCRIBE must pass the SAME name value that was
-- asserted at confirm/import time, since "delete from graph {...}" removes
-- exactly the listed triples (SPARQL Update's DELETE DATA semantics, not a
-- pattern match) -- a retract missing the name triple would silently leave
-- a stale schema:name behind in the mirror graph after unsubscribe.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_MIRROR_RDF (IN dav_collection VARCHAR, IN email VARCHAR, IN assert_flag INTEGER, IN name VARCHAR := null)
{
  declare coll, graph_iri, subject_iri, verb, stmt, name_triple VARCHAR;
  declare exit handler for sqlstate '*' { return; };

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';
  -- A stable, collection-scoped URN rather than an HTTP IRI, since this
  -- procedure has no request context (host/scheme) to build one from.
  graph_iri := concat ('urn:weblog:newsletter-subscribers:', coll);
  subject_iri := concat (graph_iri, ':', md5 (email));

  name_triple := '';
  if (name is not null and trim (name) <> '')
    name_triple := concat (' ; schema:name ', concat ('"""', replace (replace (trim (name), '\\', '\\\\'), '"', '\\"'), '"""'));

  -- INSERT and DELETE take different graph-clause keywords in SPARQL Update
  -- (INTO GRAPH vs FROM GRAPH) -- they are not interchangeable via one verb
  -- substituted into an "%s into graph" template.
  verb := case when assert_flag = 1 then 'insert into graph' else 'delete from graph' end;
  stmt := sprintf (
    'sparql prefix schema: <https://schema.org/> %s <%s> { <%s> a schema:Person ; schema:email %s%s }',
    verb, graph_iri, subject_iri, concat ('"""', replace (replace (email, '\\', '\\\\'), '"', '\\"'), '"""'), name_triple);
  exec (stmt);
}
;

CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_CONFIRM (IN token VARCHAR)
{
  declare coll, email, mirror_rdf VARCHAR;
  declare found_count INTEGER;

  found_count := 0;
  coll := null;
  email := null;
  for (select WS_DAV_COLLECTION as _c, WS_EMAIL as _e from DB.DBA.WEBLOG_SUBSCRIBER where WS_TOKEN = trim (token)) do
  {
    found_count := found_count + 1;
    coll := _c;
    email := _e;
  }
  if (found_count = 0)
    return 'This confirmation link is invalid or has already been used.';

  update DB.DBA.WEBLOG_SUBSCRIBER set WS_STATUS = 'confirmed', WS_CONFIRMED_AT = now () where WS_TOKEN = trim (token);

  mirror_rdf := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterMirrorRdf', 'true');
  if (lower (mirror_rdf) = 'true')
    DB.DBA.WEBLOG_NEWSLETTER_MIRROR_RDF (coll, email, 1);

  DB.DBA.WEBLOG_NEWSLETTER_NOTIFY_ADMIN (coll, 'new subscriber confirmed',
    sprintf ('%s just confirmed their subscription.', email));

  return 'Subscription confirmed -- thank you! You will receive the weblog digest at this address.';
}
;

-- notify: 0 (default) = the person unsubscribing IS the one who clicked the
-- link, so the on-page confirmation text below is all they need. 1 = an
-- admin unsubscribed them on the dashboard's behalf -- they have no other
-- visibility into that, so send a final email confirming the new state of
-- affairs (mirrors the activation-notice email sent on admin import, just
-- the reverse). Soft-fails like every other send in this file: a missing or
-- unreachable mail server never blocks the unsubscribe itself.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_UNSUBSCRIBE (IN token VARCHAR, IN notify INTEGER := 0)
{
  declare coll, email, uname VARCHAR;
  declare found_count INTEGER;

  found_count := 0;
  coll := null;
  email := null;
  uname := null;
  for (select WS_DAV_COLLECTION as _c, WS_EMAIL as _e, WS_NAME as _n from DB.DBA.WEBLOG_SUBSCRIBER where WS_TOKEN = trim (token)) do
  {
    found_count := found_count + 1;
    coll := _c;
    email := _e;
    uname := _n;
  }
  if (found_count = 0)
    return 'This unsubscribe link is invalid or has already been used.';

  update DB.DBA.WEBLOG_SUBSCRIBER set WS_STATUS = 'unsubscribed' where WS_TOKEN = trim (token);
  DB.DBA.WEBLOG_NEWSLETTER_MIRROR_RDF (coll, email, 0, uname);

  if (notify = 1)
    DB.DBA.WEBLOG_NEWSLETTER_SEND_UNSUBSCRIBE_NOTICE (coll, email, uname, trim (token));

  return 'You have been unsubscribed. Sorry to see you go.';
}
;

-- Final message to a subscriber removed via the admin dashboard, confirming
-- the new state of affairs (no longer subscribed) and how to resubscribe if
-- it was a mistake. Silent no-op (returns 0) if no mail server is
-- configured -- matches WEBLOG_NEWSLETTER_SEND_ACTIVATION's convention.
-- token is optional -- import paths that predate this parameter, or any
-- other future caller without a token handy, still get a working notice
-- email, just without a redundant (they're already off the list) but
-- conventional List-Unsubscribe header pointing back at the same link.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_SEND_UNSUBSCRIBE_NOTICE (IN dav_collection VARCHAR, IN email VARCHAR, IN name VARCHAR := null, IN token VARCHAR := null)
{
  declare coll, from_addr, from_name, public_route, smtp_server, subj, greeting, body, msg, unsub_url, bulk_hdrs VARCHAR;
  declare exit handler for sqlstate '*' { return 0; };

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';

  from_name := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterFromName', 'Weblog Newsletter');
  from_addr := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterFromAddress', 'noreply@localhost');
  public_route := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:publicRoute', coll);

  smtp_server := DB.DBA.WEBLOG_NEWSLETTER_RESOLVE_SMTP (coll);
  if (smtp_server is null or trim (smtp_server) = '') return 0;

  unsub_url := null;
  if (token is not null and trim (token) <> '')
    unsub_url := sprintf ('%s?nl_action=unsubscribe&token=%s', public_route, trim (token));

  greeting := case when name is not null and trim (name) <> '' then sprintf ('Hi %s,\r\n\r\n', trim (name)) else '' end;
  subj := concat (from_name, ': you have been unsubscribed');
  body := sprintf (
    '%sYou have been removed from the %s mailing list by the site administrator. You will not receive any further digest emails at this address.\r\n\r\nIf this was a mistake, you can subscribe again at any time:\r\n\r\n%s\r\n',
    greeting, from_name, public_route);
  bulk_hdrs := DB.DBA.WEBLOG_NEWSLETTER_BULK_HEADERS (coll, from_addr, from_name, email, unsub_url);
  msg := sprintf ('Date: %s\r\nSubject: %s\r\n%sContent-Type: text/plain; charset=UTF-8\r\n\r\n%s', date_rfc1123 (now ()), subj, bulk_hdrs, body);

  smtp_send (smtp_server, sprintf ('%s <%s>', from_name, from_addr), email, msg);
  return 1;
}
;

-- ==========================================================================
-- Admin bulk onboarding (CSV / RDF import) -- NOT the public double-opt-in
-- subscribe form. This is an admin-only dashboard action: the admin is
-- vouching for the list (e.g. migrating an existing mailing list), so
-- imported rows land as 'confirmed' immediately rather than 'pending'.
-- Every imported subscriber still gets an activation-notice email with an
-- unsubscribe link -- ignoring it leaves them subscribed, clicking
-- unsubscribe removes them -- so nobody is silently enrolled with no way
-- out even though there is no confirm-click step.
-- ==========================================================================

-- Notify one newly-imported subscriber that they were added, with an
-- unsubscribe escape hatch. Distinct copy from the double-opt-in confirm
-- email (there is nothing to click to "activate" -- they already are).
-- Silent no-op (returns 0) if no mail server is configured, matching the
-- rest of this file's soft-fail-on-missing-SMTP convention.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_SEND_ACTIVATION (IN dav_collection VARCHAR, IN email VARCHAR, IN token VARCHAR, IN name VARCHAR := null)
{
  declare coll, from_addr, from_name, base_url, public_route, smtp_server, subj, greeting, body, msg, unsub_url, bulk_hdrs VARCHAR;
  declare exit handler for sqlstate '*' { return 0; };

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';

  from_name := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterFromName', 'Weblog Newsletter');
  from_addr := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterFromAddress', 'noreply@localhost');
  public_route := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:publicRoute', coll);
  base_url := trim (DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterConfirmBaseUrl', ''));
  if (base_url = '') return 0;
  if (subseq (base_url, length (base_url) - 1) = '/') base_url := subseq (base_url, 0, length (base_url) - 1);

  smtp_server := DB.DBA.WEBLOG_NEWSLETTER_RESOLVE_SMTP (coll);
  if (smtp_server is null or trim (smtp_server) = '') return 0;

  greeting := case when name is not null and trim (name) <> '' then sprintf ('Hi %s,\r\n\r\n', trim (name)) else '' end;
  subj := concat (from_name, ': you have been added to our mailing list');
  unsub_url := sprintf ('%s%s?nl_action=unsubscribe&token=%s', base_url, public_route, token);
  body := sprintf (
    '%sYou have been added to the %s mailing list by the site administrator.\r\n\r\nIf you would rather not receive it, you can unsubscribe at any time:\r\n\r\n%s\r\n\r\nNo action is needed if you would like to stay on the list.\r\n',
    greeting, from_name, unsub_url);
  bulk_hdrs := DB.DBA.WEBLOG_NEWSLETTER_BULK_HEADERS (coll, from_addr, from_name, email, unsub_url);
  msg := sprintf ('Date: %s\r\nSubject: %s\r\n%sContent-Type: text/plain; charset=UTF-8\r\n\r\n%s', date_rfc1123 (now ()), subj, bulk_hdrs, body);

  smtp_send (smtp_server, sprintf ('%s <%s>', from_name, from_addr), email, msg);
  return 1;
}
;

-- Add ONE subscriber as already-confirmed. Shared by the CSV, RDF, and
-- manual-entry import paths below. name is optional (default null).
-- Returns 1 if a row was inserted/reactivated, 0 if skipped (blank/invalid
-- email, or already 'confirmed' -- re-importing an existing confirmed
-- subscriber is a harmless no-op, not a re-notify).
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_IMPORT_ONE (IN dav_collection VARCHAR, IN email VARCHAR, IN country VARCHAR, IN name VARCHAR := null)
{
  declare coll, tok, mirror_rdf VARCHAR;
  declare existing_count INTEGER;
  declare existing_status VARCHAR;
  declare exit handler for sqlstate '*' { return 0; };

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';
  if (email is null) return 0;
  -- Lowercased -- see WEBLOG_NEWSLETTER_SUBSCRIBE's comment on the same
  -- line for why.
  email := lower (trim (email));
  if (email = '' or strchr (email, '@') is null or strchr (email, '.') is null)
    return 0;
  if (name is not null and trim (name) = '') name := null;

  existing_count := 0;
  existing_status := null;
  for (select WS_STATUS as _s from DB.DBA.WEBLOG_SUBSCRIBER where WS_DAV_COLLECTION = coll and WS_EMAIL = email) do
  {
    existing_count := existing_count + 1;
    existing_status := _s;
  }
  if (existing_count > 0 and existing_status = 'confirmed')
    return 0;

  tok := md5 (concat (email, cast (now () as varchar), cast (rnd (1000000000) as varchar), cast (rnd (1000000000) as varchar)));

  if (existing_count > 0)
  {
    update DB.DBA.WEBLOG_SUBSCRIBER
       set WS_TOKEN = tok, WS_STATUS = 'confirmed', WS_COUNTRY = country, WS_NAME = name, WS_SUBSCRIBED_AT = now (), WS_CONFIRMED_AT = now ()
     where WS_DAV_COLLECTION = coll and WS_EMAIL = email;
  }
  else
  {
    insert into DB.DBA.WEBLOG_SUBSCRIBER (WS_DAV_COLLECTION, WS_EMAIL, WS_COUNTRY, WS_NAME, WS_STATUS, WS_TOKEN, WS_SUBSCRIBED_AT, WS_CONFIRMED_AT)
      values (coll, email, country, name, 'confirmed', tok, now (), now ());
  }

  mirror_rdf := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterMirrorRdf', 'true');
  if (lower (mirror_rdf) = 'true')
    DB.DBA.WEBLOG_NEWSLETTER_MIRROR_RDF (coll, email, 1, name);

  DB.DBA.WEBLOG_NEWSLETTER_SEND_ACTIVATION (coll, email, tok, name);
  return 1;
}
;

-- Bulk-onboard subscribers from a CSV file's raw text: a header row naming
-- "email" (required) and optionally "country", one subscriber per
-- following row. Header matching is case-insensitive and order-independent;
-- unrecognized columns are ignored. Naive comma-split (no quoted-field
-- support) -- adequate for a two-column email/country export, not a
-- general CSV parser.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_IMPORT_CSV (IN dav_collection VARCHAR, IN csv_text VARCHAR)
{
  declare coll VARCHAR;
  declare lines, cols any;
  declare i, email_col, country_col, name_col, imported, skipped, total_rows INTEGER;
  declare exit handler for sqlstate '*' { return 'Could not parse the uploaded CSV file.'; };

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';
  if (csv_text is null or trim (csv_text) = '')
    return 'The uploaded CSV file is empty.';

  csv_text := replace (csv_text, '\r\n', '\n');
  csv_text := replace (csv_text, '\r', '\n');
  lines := split_and_decode (csv_text, 0, '\0\0\n');
  if (length (lines) < 2)
    return 'The CSV file needs a header row plus at least one subscriber row.';

  cols := split_and_decode (lower (trim (aref (lines, 0))), 0, '\0\0,');
  email_col := -1;
  country_col := -1;
  name_col := -1;
  for (i := 0; i < length (cols); i := i + 1)
  {
    declare c VARCHAR;
    c := trim (aref (cols, i));
    if (c = 'email') email_col := i;
    else if (c = 'country') country_col := i;
    else if (c = 'name') name_col := i;
  }
  if (email_col = -1)
    return 'The CSV header row must include an "email" column.';

  imported := 0;
  skipped := 0;
  total_rows := 0;
  for (i := 1; i < length (lines); i := i + 1)
  {
    declare row_text VARCHAR;
    declare row_cols any;
    declare row_email, row_country, row_name VARCHAR;
    row_text := trim (aref (lines, i));
    if (row_text <> '')
    {
      total_rows := total_rows + 1;
      row_cols := split_and_decode (row_text, 0, '\0\0,');
      row_email := case when email_col < length (row_cols) then trim (aref (row_cols, email_col)) else '' end;
      row_country := case when country_col >= 0 and country_col < length (row_cols) then trim (aref (row_cols, country_col)) else null end;
      row_name := case when name_col >= 0 and name_col < length (row_cols) then trim (aref (row_cols, name_col)) else null end;
      if (DB.DBA.WEBLOG_NEWSLETTER_IMPORT_ONE (coll, row_email, row_country, row_name) = 1)
        imported := imported + 1;
      else
        skipped := skipped + 1;
    }
  }

  return sprintf ('CSV import: %d row(s) processed, %d imported, %d skipped (already confirmed or invalid).', total_rows, imported, skipped);
}
;

-- Bulk-onboard subscribers from an RDF document, looking for schema:Person
-- entities with a schema:email (and optional schema:addressCountry).
-- rdf_format dispatch:
--   'turtle' | 'ntriples' | 'nquads' | 'trig' -- loaded via DB.DBA.TTLP (the
--     same Turtle-family parser handles all four; confirmed live for
--     turtle and ntriples 2026-09-22 -- trig/nquads share the same parser
--     but were not individually re-verified) into a throwaway scratch
--     graph, queried via a dynamically-built SPARQL SELECT run through
--     exec()'s extended result-set form, then the scratch graph is
--     dropped. Matches both http:// and https:// schema.org, since real
--     documents in this skill's own corpus use both.
--   'jsonld' -- this Virtuoso instance has no lightweight raw-string
--     JSON-LD-to-RDF loader (JSONLD_TREE_TO_XML produced ~200KB of output
--     for a single trivial Person object -- not viable here, confirmed
--     live 2026-09-22), so JSON-LD is instead scanned as text for
--     "email"-style keys (bare "email", "schema:email", or the full
--     schema.org IRI as the key) and their quoted string value -- covers a
--     flat schema:Person JSON-LD export, the realistic shape for a
--     subscriber list, but does not do general JSON-LD context expansion.
--     Country is intentionally NOT extracted for JSON-LD imports (out of
--     scope rather than guessing at a nearby-key heuristic).
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_IMPORT_RDF (IN dav_collection VARCHAR, IN rdf_text VARCHAR, IN rdf_format VARCHAR)
{
  declare coll, fmt, graph_iri VARCHAR;
  declare imported, skipped, total_rows INTEGER;
  declare exit handler for sqlstate '*' { return 'Could not parse the uploaded RDF file -- check it is valid for the selected format.'; };

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';
  if (rdf_text is null or trim (rdf_text) = '')
    return 'The uploaded RDF file is empty.';

  fmt := lower (trim (coalesce (rdf_format, 'turtle')));
  imported := 0;
  skipped := 0;
  total_rows := 0;

  if (fmt = 'jsonld')
  {
    declare lc VARCHAR;
    declare needles any;
    declare ni, search_pos, guard INTEGER;

    lc := lower (rdf_text);
    needles := vector ('"email"', '"schema:email"', '"http://schema.org/email"', '"https://schema.org/email"');
    for (ni := 0; ni < length (needles); ni := ni + 1)
    {
      declare needle VARCHAR;
      declare kpos INTEGER;
      needle := aref (needles, ni);
      search_pos := 0;
      guard := 0;
      kpos := strstr (subseq (lc, search_pos), needle);
      while (kpos is not null and guard < 5000)
      {
        declare abs_kpos, after_key, colon_pos, qstart, val_start, qend INTEGER;
        declare found_email VARCHAR;
        abs_kpos := search_pos + kpos;
        after_key := abs_kpos + length (needle);
        colon_pos := strstr (subseq (lc, after_key), ':');
        if (colon_pos is not null)
        {
          qstart := strstr (subseq (lc, after_key + colon_pos + 1), '"');
          if (qstart is not null)
          {
            val_start := after_key + colon_pos + 1 + qstart + 1;
            qend := strstr (subseq (lc, val_start), '"');
            if (qend is not null)
            {
              found_email := trim (subseq (rdf_text, val_start, val_start + qend));
              total_rows := total_rows + 1;
              if (DB.DBA.WEBLOG_NEWSLETTER_IMPORT_ONE (coll, found_email, null) = 1)
                imported := imported + 1;
              else
                skipped := skipped + 1;
            }
          }
        }
        search_pos := after_key;
        guard := guard + 1;
        if (search_pos >= length (lc))
          kpos := null;
        else
          kpos := strstr (subseq (lc, search_pos), needle);
      }
    }
  }
  else
  {
    declare state, msg, q VARCHAR;
    declare meta, rows any;
    declare ri INTEGER;

    graph_iri := sprintf ('urn:weblog:newsletter-import-scratch:%s', md5 (concat (coll, cast (now () as varchar), cast (rnd (1000000000) as varchar))));
    DB.DBA.TTLP (rdf_text, coll, graph_iri, 0);

    q := sprintf (
      'sparql prefix schemaS: <https://schema.org/> prefix schemaH: <http://schema.org/> select ?email ?country ?name from <%s> where { { ?p schemaS:email ?email } union { ?p schemaH:email ?email } optional { { ?p schemaS:addressCountry ?country } union { ?p schemaH:addressCountry ?country } } optional { { ?p schemaS:name ?name } union { ?p schemaH:name ?name } } }',
      graph_iri);
    state := '00000';
    exec (q, state, msg, vector (), 0, meta, rows);

    if (state = '00000')
    {
      for (ri := 0; ri < length (rows); ri := ri + 1)
      {
        declare row_email, row_country, row_name VARCHAR;
        row_email := cast (aref (aref (rows, ri), 0) as varchar);
        row_country := case when aref (aref (rows, ri), 1) is null then null else cast (aref (aref (rows, ri), 1) as varchar) end;
        row_name := case when aref (aref (rows, ri), 2) is null then null else cast (aref (aref (rows, ri), 2) as varchar) end;
        total_rows := total_rows + 1;
        if (DB.DBA.WEBLOG_NEWSLETTER_IMPORT_ONE (coll, row_email, row_country, row_name) = 1)
          imported := imported + 1;
        else
          skipped := skipped + 1;
      }
    }

    delete from DB.DBA.RDF_QUAD where G = iri_to_id (graph_iri, 0);
  }

  if (total_rows = 0)
    return sprintf ('No schema:Person / schema:email entries were found in the uploaded %s file.', fmt);
  return sprintf ('%s import: %d entrie(s) found, %d imported, %d skipped (already confirmed or invalid).', fmt, total_rows, imported, skipped);
}
;

-- Remove every occurrence of a tag block (e.g. <script>...</script>) from
-- txt. Case-insensitive tag matching via a lower-cased scan, but the
-- returned text keeps the original casing (ASCII tag names only, so the
-- positions line up). Bounded by a 200-iteration guard so a malformed
-- unclosed tag can't loop forever -- it truncates the remainder instead.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_STRIP_BLOCK (IN txt VARCHAR, IN open_tag VARCHAR, IN close_tag VARCHAR)
{
  declare result VARCHAR;
  declare op, cp, guard INTEGER;
  declare exit handler for sqlstate '*' { return txt; };

  -- NOTE: strchr/strrchr in this Virtuoso version match against a SET of
  -- characters (strpbrk-style), not a literal substring -- confirmed live
  -- 2026-09-22 (strchr against a real '<body' tag returned 0, matching on
  -- the leading '<' alone). strstr is the actual literal-substring search,
  -- returning a 0-based position or NULL, and is what every multi-character
  -- tag lookup in this file must use.
  result := txt;
  guard := 0;
  op := strstr (lower (result), open_tag);
  while (op is not null and guard < 200)
  {
    cp := strstr (subseq (lower (result), op), close_tag);
    if (cp is null)
    {
      result := subseq (result, 0, op);
      op := null;
    }
    else
    {
      result := concat (subseq (result, 0, op), subseq (result, op + cp + length (close_tag)));
      op := strstr (lower (result), open_tag);
    }
    guard := guard + 1;
  }
  return result;
}
;

-- Remove ONE specific element (the first one starting with open_needle,
-- e.g. '<div id="fnav"') by NESTING-DEPTH, not by nearest closing tag --
-- WEBLOG_NEWSLETTER_STRIP_BLOCK's nearest-close approach is wrong here
-- because a floating-nav widget contains its own nested <div>s (a header
-- row, a links list): stopping at the first </div> would truncate mid-
-- structure and leave the rest of the widget's markup dangling in the
-- output. This walks forward counting <tag_name ...> opens and </tag_name>
-- closes to find the TRUE matching close. Bounded by a 5000-iteration guard;
-- on anything unexpected (tag never closes, guard exceeded) it returns txt
-- unchanged rather than risk corrupting real content.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_STRIP_ELEMENT (IN txt VARCHAR, IN open_needle VARCHAR, IN tag_name VARCHAR)
{
  declare lc, open_tag, close_tag VARCHAR;
  declare spos, gtpos, scan_pos, depth, next_open, next_close, elem_end, guard INTEGER;
  declare exit handler for sqlstate '*' { return txt; };

  lc := lower (txt);
  spos := strstr (lc, lower (open_needle));
  if (spos is null) return txt;
  gtpos := strstr (subseq (lc, spos), '>');
  if (gtpos is null) return txt;

  open_tag := concat ('<', lower (tag_name));
  close_tag := concat ('</', lower (tag_name));
  scan_pos := spos + gtpos + 1;
  depth := 1;
  elem_end := null;
  guard := 0;
  while (depth > 0 and guard < 5000)
  {
    next_open := strstr (subseq (lc, scan_pos), open_tag);
    next_close := strstr (subseq (lc, scan_pos), close_tag);
    if (next_close is null) return txt;
    if (next_open is not null and next_open < next_close)
    {
      depth := depth + 1;
      scan_pos := scan_pos + next_open + length (open_tag);
    }
    else
    {
      declare close_tag_end, close_gt INTEGER;
      depth := depth - 1;
      -- close_tag is '</div' etc, WITHOUT the trailing '>' -- close_tag_end
      -- lands right AT that '>', not past it, so it must be advanced one
      -- more step to the real tag boundary (confirmed live 2026-09-22: the
      -- off-by-one left a stray '>' character behind after removal).
      close_tag_end := scan_pos + next_close + length (close_tag);
      if (depth = 0)
      {
        close_gt := strstr (subseq (lc, close_tag_end), '>');
        elem_end := case when close_gt is not null then close_tag_end + close_gt + 1 else close_tag_end end;
      }
      scan_pos := close_tag_end;
    }
    guard := guard + 1;
  }
  if (elem_end is null) return txt;
  return concat (subseq (txt, 0, spos), subseq (txt, elem_end));
}
;

-- Collect the inner content of every <style>...</style> block in txt,
-- concatenated with a newline between blocks. Used by 'full' content mode
-- to carry a post's OWN stylesheet into its email instead of the earlier
-- approach of stripping all <style> and hand-authoring substitute CSS for
-- each widget class this generator family happens to use -- the source
-- stylesheet already defines every one of them correctly, including the
-- :root custom properties (var(--accent), ...) those rules depend on,
-- which a hand-authored substitute could never fully keep up with (this
-- skill hit that wall three separate times: comparison matrix, then the
-- synopsis "Layer concept" panel, then the Sources chips -- all the same
-- root cause). Bounded by a 200-iteration guard, matching
-- WEBLOG_NEWSLETTER_STRIP_BLOCK's.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_EXTRACT_STYLE_BLOCKS (IN txt VARCHAR)
{
  declare lc, result VARCHAR;
  declare op, gtpos, bstart, cpos, guard INTEGER;
  declare exit handler for sqlstate '*' { return coalesce (result, ''); };

  if (txt is null) return '';
  result := '';
  lc := lower (txt);
  guard := 0;
  op := strstr (lc, '<style');
  while (op is not null and guard < 200)
  {
    gtpos := strstr (subseq (lc, op), '>');
    if (gtpos is null)
    {
      op := null;
    }
    else
    {
      bstart := op + gtpos + 1;
      cpos := strstr (subseq (lc, bstart), '</style');
      if (cpos is null)
      {
        op := null;
      }
      else
      {
        result := concat (result, subseq (txt, bstart, bstart + cpos), '\n');
        op := strstr (subseq (lc, bstart + cpos), '<style');
        if (op is not null) op := op + bstart + cpos;
      }
    }
    guard := guard + 1;
  }
  return result;
}
;

-- Extract a post's real <title> (same regex + entity-cleanup approach
-- index.vsp uses for its archive list), falling back to the bare filename
-- when extraction fails -- used to make newsletter emails read as "New
-- post: <em>Actual Title</em>" rather than a raw filename.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_POST_TITLE (IN dav_collection VARCHAR, IN filename VARCHAR)
{
  declare coll, content, t VARCHAR;
  declare exit handler for sqlstate '*' { return filename; };

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';
  content := '';
  for (select subseq (blob_to_string (RES_CONTENT), 0, 8000) as _c from WS.WS.SYS_DAV_RES where RES_FULL_PATH = coll || filename) do
  {
    content := _c;
  }
  t := regexp_match ('<title>[^<]+</title>', content);
  if (t is null) return filename;
  t := replace (t, '<title>', '');
  t := replace (t, '</title>', '');
  t := trim (t);
  t := replace (t, '&amp;', '&');
  t := replace (t, '&quot;', chr (34));
  t := replace (t, '&#39;', chr (39));
  t := replace (t, '&apos;', chr (39));
  t := replace (t, '&ndash;', '-');
  t := replace (t, '&mdash;', '-');
  if (t = '') return filename;
  return t;
}
;

-- Return the inner HTML of the first tag in content whose start matches
-- open_needle literally (e.g. '<p class="lede"'), up to close_tag, or NULL
-- if open_needle isn't found or its closing tag never appears. Matching is
-- case-insensitive (content is assumed already lower-cased by the caller
-- for the purpose of locating positions; the returned slice is taken from
-- the ORIGINAL-case text passed in as orig).
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_FIND_TAGGED_TEXT (IN orig VARCHAR, IN lc VARCHAR, IN open_needle VARCHAR, IN close_tag VARCHAR)
{
  declare pos, gtpos, bstart, epos INTEGER;
  declare exit handler for sqlstate '*' { return null; };

  pos := strstr (lc, lower (open_needle));
  if (pos is null) return null;
  gtpos := strstr (subseq (lc, pos), '>');
  if (gtpos is null) return null;
  bstart := pos + gtpos + 1;
  epos := strstr (subseq (lc, bstart), lower (close_tag));
  if (epos is null) return null;
  return subseq (orig, bstart, bstart + epos);
}
;

-- Detect this skill's own interactive-infographic markup (kg-generator /
-- rdf-infographic-skill output): a floating navigation panel. Same marker
-- family validate-harness-contract.py itself checks for ('id="fnav"',
-- 'class="section-nav"', 'id="nav-panel"', an aria-label naming section
-- navigation) -- reused here, not guessed, because it's the one signal this
-- repo's own generators already treat as "this page has chrome/widgets", as
-- opposed to a plain prose post that has none of it.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_IS_INFOGRAPHIC (IN lc VARCHAR)
{
  declare exit handler for sqlstate '*' { return 0; };
  if (strstr (lc, 'id="fnav"') is not null) return 1;
  if (strstr (lc, 'class="section-nav"') is not null) return 1;
  if (strstr (lc, 'id="nav-panel"') is not null) return 1;
  if (strstr (lc, 'aria-label="section navigation"') is not null) return 1;
  return 0;
}
;

-- Extract this post's email excerpt for a Substack-style inline email, in
-- one of two shapes selected by content_mode ('auto' | 'snippet' | 'full'):
--
--   snippet -- ONE short, genuinely-authored excerpt, never the whole
--     document. This skill's HTML posts are often full interactive
--     infographics (floating nav, hero badges/stat tiles, KG attribution
--     line, comparison matrices, in-body <style> blocks for section-scoped
--     CSS, accordions) -- inlining the raw <body> pulled all of that UI
--     chrome, and in one case even raw CSS text, into real subscriber
--     emails (caught live 2026-09-22). Only these, in priority order, are
--     ever used as the snippet:
--       1. <p class="lede">    -- this skill's own synopsis/dek convention
--       2. <p class="tagline"> -- the shorter one-line hero tagline some
--          pages use instead of a synopsis section
--       3. the first <p> immediately after the page's <h1> -- covers
--          simpler posts with neither class
--     An empty snippet (title + "Read the full post" link only) is always
--     safer than guessing at body content when none of the three match.
--
--   full -- the inner HTML of <body>...</body>, <script> blocks stripped.
--     Only safe for posts that AREN'T one of this skill's own infographics
--     (Substack's own model: full content inline for a plain article,
--     "read in app" for anything more elaborate) -- 'auto' never chooses
--     this for a page WEBLOG_NEWSLETTER_IS_INFOGRAPHIC flags. The post's
--     OWN <style> block(s) -- both in <head> and any embedded in <body> --
--     are carried along rather than stripped (comments removed, size
--     capped at 65000 chars): a hand-authored substitute stylesheet can
--     never keep up with every widget class this generator family invents,
--     and the real stylesheet already gets it right, :root custom
--     properties included. See WEBLOG_NEWSLETTER_HTML_SHELL for where this
--     gets embedded.
--
--   auto (the default) -- 'snippet' for a detected infographic, 'full'
--     otherwise.
--
-- Either shape's HTML is truncated to max_len characters (0 = no limit) at
-- the last safe tag boundary, with an ellipsis appended. A .md/.txt post
-- has none of this markup and is always escaped and wrapped as
-- preformatted text, regardless of content_mode.
--
-- Returns vector(excerpt_html, extra_css) -- extra_css is '' outside
-- 'full' mode (a snippet or a plain-text post never carries a stylesheet).
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_POST_EXCERPT (IN dav_collection VARCHAR, IN filename VARCHAR, IN max_len INTEGER, IN content_mode VARCHAR)
{
  declare coll, content, lc, frag, effective_mode, extra_css VARCHAR;
  declare h1_close, cutpos, bpos, gtpos, bstart, epos INTEGER;
  declare is_html INTEGER;
  declare exit handler for sqlstate '*' { return vector ('', ''); };

  extra_css := '';
  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';
  content := '';
  for (select blob_to_string (RES_CONTENT) as _c from WS.WS.SYS_DAV_RES where RES_FULL_PATH = coll || filename) do
  {
    content := _c;
  }
  if (content is null or content = '') return vector ('', '');

  is_html := case when lower (filename) like '%.html' or lower (filename) like '%.htm' then 1 else 0 end;

  if (is_html = 0)
  {
    frag := replace (replace (replace (content, '&', '&amp;'), '<', '&lt;'), '>', '&gt;');
    frag := concat ('<div style="white-space:pre-wrap;font-family:Georgia,serif;line-height:1.6">', frag, '</div>');
  }
  else
  {
    lc := lower (content);
    effective_mode := lower (trim (coalesce (content_mode, 'auto')));
    if (effective_mode <> 'snippet' and effective_mode <> 'full') effective_mode := 'auto';
    if (effective_mode = 'auto')
      effective_mode := case when DB.DBA.WEBLOG_NEWSLETTER_IS_INFOGRAPHIC (lc) = 1 then 'snippet' else 'full' end;

    if (effective_mode = 'full')
    {
      declare head_close, scan_from INTEGER;
      frag := content;
      -- Search for <body only AFTER </head>, not from the start of the
      -- document -- a plain strstr(lc, '<body') can match prose INSIDE
      -- <head> that merely talks about the body element (e.g. a CSS-comment
      -- note reading "...is a direct <body> child..."), landing bstart deep
      -- inside <style> content instead of the real tag (caught live
      -- 2026-09-22 via a raw CSS-comment leak into a real email). </head>
      -- always precedes the real <body> tag in a well-formed document, so
      -- anchoring the search there is far less ambiguous.
      head_close := strstr (lc, '</head>');
      -- Carry the <head>-level stylesheet along BEFORE narrowing frag down
      -- to the <body> region -- this is the post's own design system
      -- (:root custom properties included), not chrome to be discarded.
      extra_css := DB.DBA.WEBLOG_NEWSLETTER_EXTRACT_STYLE_BLOCKS (
        case when head_close is not null then subseq (content, 0, head_close) else content end);
      scan_from := case when head_close is not null then head_close + 7 else 0 end;
      bpos := strstr (subseq (lc, scan_from), '<body');
      if (bpos is not null)
      {
        bpos := bpos + scan_from;
        gtpos := strstr (subseq (lc, bpos), '>');
        if (gtpos is not null)
        {
          bstart := bpos + gtpos + 1;
          epos := strstr (subseq (lc, bstart), '</body');
          if (epos is not null)
            frag := subseq (content, bstart, bstart + epos);
          else
            frag := subseq (content, bstart);
        }
      }
      -- A page can also embed a <style> block directly in <body> (scoped,
      -- section-local CSS) -- capture those too before stripping them out
      -- of the visible fragment.
      extra_css := concat (extra_css, DB.DBA.WEBLOG_NEWSLETTER_EXTRACT_STYLE_BLOCKS (frag));
      extra_css := DB.DBA.WEBLOG_NEWSLETTER_STRIP_BLOCK (extra_css, '/*', '*/');
      if (length (extra_css) > 65000)
        extra_css := concat (subseq (extra_css, 0, 65000), '\n/* truncated */\n');
      frag := DB.DBA.WEBLOG_NEWSLETTER_STRIP_BLOCK (frag, '<script', '</script>');
      frag := DB.DBA.WEBLOG_NEWSLETTER_STRIP_BLOCK (frag, '<style', '</style>');
      -- Trim the floating-nav widget itself (both markup shapes seen in
      -- this skill's own generated infographics) -- it's page-navigation
      -- chrome (jump links, theme/hide/expand buttons) with no meaning
      -- once lifted out of the live page into an email (caught live
      -- 2026-09-22: raw nav links and inert buttons in a real "full" email).
      frag := DB.DBA.WEBLOG_NEWSLETTER_STRIP_ELEMENT (frag, '<div id="fnav"', 'div');
      frag := DB.DBA.WEBLOG_NEWSLETTER_STRIP_ELEMENT (frag, '<nav id="floating-nav"', 'nav');
    }
    else
    {
      frag := DB.DBA.WEBLOG_NEWSLETTER_FIND_TAGGED_TEXT (content, lc, '<p class="lede"', '</p>');
      if (frag is null)
        frag := DB.DBA.WEBLOG_NEWSLETTER_FIND_TAGGED_TEXT (content, lc, '<p class="tagline"', '</p>');
      if (frag is null)
      {
        h1_close := strstr (lc, '</h1>');
        if (h1_close is not null)
          frag := DB.DBA.WEBLOG_NEWSLETTER_FIND_TAGGED_TEXT (subseq (content, h1_close + 5), subseq (lc, h1_close + 5), '<p', '</p>');
      }
      if (frag is null)
        frag := '';
      else
      {
        -- Defense in depth only -- none of the three lookups above should
        -- ever land on a <script>/<style> block, but a single short
        -- paragraph is cheap to run through the same stripper regardless.
        frag := DB.DBA.WEBLOG_NEWSLETTER_STRIP_BLOCK (frag, '<script', '</script>');
        frag := DB.DBA.WEBLOG_NEWSLETTER_STRIP_BLOCK (frag, '<style', '</style>');
        frag := concat ('<p>', frag, '</p>');
      }
    }
  }

  if (max_len > 0 and length (frag) > max_len)
  {
    cutpos := strrchr (subseq (frag, 0, max_len), '<');
    if (cutpos is not null and cutpos > 0)
      frag := subseq (frag, 0, cutpos);
    else
      frag := subseq (frag, 0, max_len);
    frag := concat (frag, '&hellip;');
  }

  return vector (frag, extra_css);
}
;

-- Render one post as a Substack-style card: the title IS the hyperlink to
-- the post (grounded in the blog's own public domain, never a relative
-- path -- relative links don't resolve inside a mail client), the post's
-- own content inlined below it, then a plain-text-style "read more" link
-- for the (possibly truncated) rest.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_POST_CARD (IN title_html VARCHAR, IN url VARCHAR, IN excerpt_html VARCHAR)
{
  return sprintf (
    '<div style="margin:0 0 36px 0">' ||
    '<h2 style="margin:0 0 14px 0;font-size:24px;line-height:1.3;font-family:Georgia,serif"><a href="%s" style="color:#1f4e79;text-decoration:none">%s</a></h2>' ||
    '<div style="font-size:16px;line-height:1.7;color:#222">%s</div>' ||
    '<p style="margin:14px 0 0 0"><a href="%s" style="color:#1f4e79;font-family:Helvetica,Arial,sans-serif;font-size:14px;font-weight:bold">Read the full post &rarr;</a></p>' ||
    '</div>',
    url, title_html, excerpt_html, url);
}
;

-- Wrap one or more post cards in the shared email chrome (kicker line,
-- white card on a light background, unsubscribe footer). Shared by both
-- digest modalities so a single visual identity covers "one post now" and
-- "several posts this week".
-- extra_css (default '') is the carried-along stylesheet from one or more
-- posts' own <head> -- see WEBLOG_NEWSLETTER_POST_EXCERPT's 'full' mode.
-- It is embedded AFTER this shell's own <style> so that, on any selector
-- collision (unlikely: every element this shell itself renders carries an
-- inline style="...", which always wins over an embedded stylesheet
-- regardless of order or specificity), the source CSS -- not this shell's
-- chrome -- is what loses. This replaces an earlier approach of stripping
-- every post's <style> and hand-authoring substitute CSS one widget class
-- at a time (comparison matrix, then a synopsis panel, then a chip row --
-- the same root cause resurfacing three separate times): the post's own
-- stylesheet already gets every one of its own widgets right, including
-- the :root custom properties those rules depend on, which no
-- hand-authored substitute could keep pace with as this generator grows
-- new components.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_HTML_SHELL (IN kicker VARCHAR, IN body_html VARCHAR, IN from_name VARCHAR, IN unsub_url VARCHAR, IN extra_css VARCHAR := '')
{
  return sprintf (
    '<!DOCTYPE html><html><head><meta charset="UTF-8">' ||
    '<style>%s</style>' ||
    -- This generator family uses a scroll-triggered reveal-on-scroll
    -- pattern (an IntersectionObserver flips a "visible" class) for the
    -- synopsis deck, HowTo steps, FAQ items, and some whole sections --
    -- CSS classes like .anim-fade / .fade-in start at opacity:0 and rely
    -- on that JS to ever reach opacity:1. Email has no JS, so carrying the
    -- stylesheet along verbatim left entire sections permanently invisible
    -- (caught live 2026-09-22: the whole synopsis section rendered as a
    -- blank white gap, confirmed via getComputedStyle -- correct DOM,
    -- correct colors, opacity:0). This unconditionally forces the
    -- post-reveal end state; !important since a scoped source selector
    -- could otherwise out-specificity a same-name override.
    '<style>.anim-fade,.fade-in{opacity:1 !important;transform:none !important}</style>' ||
    -- This generator marks up inline technical identifiers (table names,
    -- graph URIs, IRIs) with plain <code>, but none of its own stylesheets
    -- give bare <code> any visual treatment at all (confirmed across this
    -- whole corpus, not just one post) -- so a dense technical sentence
    -- renders as an undifferentiated wall of text, code and prose blurred
    -- together (flagged live 2026-09-23). A small monospace chip is enough
    -- to make each identifier scannable against the surrounding prose.
    '<style>code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:0.9em;background:#f4f4f4;border:1px solid #e2e2e2;border-radius:4px;padding:1px 5px}</style>' ||
    '</head>' ||
    '<body style="margin:0;padding:0;background:#f4f4f4;font-family:Helvetica,Arial,sans-serif;color:#222">' ||
    '<div style="max-width:640px;margin:0 auto;background:#ffffff;padding:32px 28px">' ||
    '<p style="margin:0 0 22px 0;font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:#888">%s</p>' ||
    '%s' ||
    '<hr style="border:none;border-top:1px solid #e2e2e2;margin:8px 0 20px 0">' ||
    '<p style="font-size:12px;color:#999;margin:0">You are receiving this because you subscribed to %s.<br><a href="%s" style="color:#999">Unsubscribe</a></p>' ||
    '</div></body></html>',
    coalesce (extra_css, ''), kicker, body_html, from_name, unsub_url);
}
;

-- Send new-post notifications to confirmed subscribers, in one of two
-- modalities selected by weblog:newsletterMode ('digest', the default, or
-- 'immediate'):
--   digest    -- one email per subscriber, bundling every post published
--               since the newest WS_LAST_SENT_AT across that collection's
--               subscribers. Intended for a long polling interval (the
--               default schedule is weekly).
--   immediate -- one SEPARATE email per subscriber PER new post, so each
--               post goes out the same day it is found rather than waiting
--               to be bundled. This is still schedule-driven (Virtuoso has
--               no native "on WebDAV PUT" hook to fire from), so
--               "immediate" in practice means "as soon as the next
--               scheduled check runs" -- pair it with a short interval
--               (minutes, not days) via WEBLOG_NEWSLETTER_SCHEDULE_DIGEST
--               for same-day delivery.
-- Either mode skips silently (returns a status string, does not signal)
-- when there is nothing new, so the scheduled job can fire on a fixed
-- interval without emailing anything empty.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_SEND_DIGEST (IN dav_collection VARCHAR)
{
  declare coll, mode, content_mode, from_addr, from_name, public_route, base_url, smtp_server VARCHAR;
  declare since_ts DATETIME;
  declare sent_count, failed_count, item_count INTEGER;
  declare posts, post_cards any;
  declare digest_body_html, digest_extra_css VARCHAR;
  declare i INTEGER;

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';
  mode := lower (DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterMode', 'digest'));
  if (mode <> 'immediate') mode := 'digest';
  -- 'auto' (the default) chooses per-post between a short snippet (for this
  -- skill's own interactive infographics) and the full body (for a plain
  -- prose post) -- see WEBLOG_NEWSLETTER_POST_EXCERPT. 'snippet' or 'full'
  -- overrides that per-post detection for every post in this collection.
  content_mode := lower (trim (DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterContentMode', 'auto')));
  if (content_mode <> 'snippet' and content_mode <> 'full') content_mode := 'auto';

  since_ts := (select max (WS_LAST_SENT_AT) from DB.DBA.WEBLOG_SUBSCRIBER where WS_DAV_COLLECTION = coll);
  if (since_ts is null) since_ts := stringdate ('2000-01-01');

  -- Oldest first, so "immediate" mode's separate emails arrive in
  -- publication order rather than newest-first.
  posts := vector ();
  for (select RES_NAME as _name, RES_MOD_TIME as _mod
         from WS.WS.SYS_DAV_RES
        where (RES_FULL_PATH like coll || '%.html' or RES_FULL_PATH like coll || '%.md')
          and RES_NAME not like '._%'
          and RES_NAME <> 'index.vsp'
          and RES_NAME <> 'dashboard.html'
          and RES_MOD_TIME > since_ts
        order by RES_MOD_TIME asc) do
  {
    posts := vector_concat (posts, vector (vector (_name, _mod)));
  }
  item_count := length (posts);

  if (item_count = 0)
    return 'No new posts since the last check -- nothing sent.';

  from_name := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterFromName', 'Weblog Newsletter');
  from_addr := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterFromAddress', 'noreply@localhost');
  public_route := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:publicRoute', coll);

  -- Every link in the email (post title, unsubscribe) must be absolute and
  -- grounded in the blog's real public domain -- a relative link like
  -- "/weblog-test/?post=..." does not resolve inside a mail client. This is
  -- the same property index.vsp's own confirm-link path already relies on;
  -- there is no safe default to fabricate here, so bail out with a clear
  -- reason rather than sending broken links.
  base_url := trim (DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterConfirmBaseUrl', ''));
  if (base_url = '')
    return sprintf ('%d new post(s) to send, but weblog:newsletterConfirmBaseUrl is not set -- cannot build absolute post links for an email, nothing sent.', item_count);
  if (subseq (base_url, length (base_url) - 1) = '/') base_url := subseq (base_url, 0, length (base_url) - 1);

  smtp_server := DB.DBA.WEBLOG_NEWSLETTER_RESOLVE_SMTP (coll);
  if (smtp_server is null or trim (smtp_server) = '')
    return sprintf ('%d new post(s) to send, but no mail server is configured (weblog:newsletterSmtpServer / server DefaultMailServer) -- nothing sent.', item_count);

  -- Render every post's card ONCE (title, absolute URL, inlined content),
  -- outside the subscriber loop -- the post content itself doesn't vary by
  -- subscriber, only the per-subscriber unsubscribe link does.
  post_cards := vector ();
  digest_body_html := '';
  digest_extra_css := '';
  for (i := 0; i < length (posts); i := i + 1)
  {
    declare pname, title, url, excerpt, card, post_css VARCHAR;
    declare excerpt_result any;
    pname := aref (aref (posts, i), 0);
    title := DB.DBA.WEBLOG_NEWSLETTER_POST_TITLE (coll, pname);
    url := sprintf ('%s%s?post=%U', base_url, public_route, pname);
    -- Immediate mode sends one post per email, so it can afford a longer
    -- inlined excerpt than a digest bundling several posts in one message.
    excerpt_result := DB.DBA.WEBLOG_NEWSLETTER_POST_EXCERPT (coll, pname, case when mode = 'immediate' then 20000 else 8000 end, content_mode);
    excerpt := aref (excerpt_result, 0);
    post_css := aref (excerpt_result, 1);
    card := DB.DBA.WEBLOG_NEWSLETTER_POST_CARD (title, url, excerpt);
    post_cards := vector_concat (post_cards, vector (vector (title, card, post_css)));
    digest_body_html := concat (digest_body_html, card);
    digest_extra_css := concat (digest_extra_css, post_css);
  }

  sent_count := 0;
  failed_count := 0;
  for (select WS_TOKEN as _tok, WS_EMAIL as _email from DB.DBA.WEBLOG_SUBSCRIBER
        where WS_DAV_COLLECTION = coll and WS_STATUS = 'confirmed') do
  {
    declare subscriber_ok int;
    declare unsub_url VARCHAR;
    unsub_url := sprintf ('%s%s?nl_action=unsubscribe&token=%s', base_url, public_route, _tok);
    subscriber_ok := 1;

    if (mode = 'immediate')
    {
      for (i := 0; i < length (post_cards) and subscriber_ok = 1; i := i + 1)
      {
        declare title, card, post_css, body_html, subj, msg, bulk_hdrs VARCHAR;
        title := aref (aref (post_cards, i), 0);
        card := aref (aref (post_cards, i), 1);
        post_css := aref (aref (post_cards, i), 2);
        body_html := DB.DBA.WEBLOG_NEWSLETTER_HTML_SHELL ('New post', card, from_name, unsub_url, post_css);
        subj := sprintf ('%s: %s', from_name, title);
        bulk_hdrs := DB.DBA.WEBLOG_NEWSLETTER_BULK_HEADERS (coll, from_addr, from_name, _email, unsub_url);
        msg := sprintf ('Date: %s\r\nSubject: %s\r\n%sMIME-Version: 1.0\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n%s',
          date_rfc1123 (now ()), subj, bulk_hdrs, body_html);
        {
          -- One post''s send failing must not silently mark the others as
          -- delivered -- treat the whole per-subscriber batch as retryable.
          declare exit handler for sqlstate '*' { subscriber_ok := 0; };
          smtp_send (smtp_server, sprintf ('%s <%s>', from_name, from_addr), _email, msg);
        }
      }
    }
    else
    {
      declare body_html, subj, msg, bulk_hdrs VARCHAR;
      subj := concat (from_name, ': new posts this week');
      body_html := DB.DBA.WEBLOG_NEWSLETTER_HTML_SHELL ('New posts', digest_body_html, from_name, unsub_url, digest_extra_css);
      bulk_hdrs := DB.DBA.WEBLOG_NEWSLETTER_BULK_HEADERS (coll, from_addr, from_name, _email, unsub_url);
      msg := sprintf ('Date: %s\r\nSubject: %s\r\n%sMIME-Version: 1.0\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n%s',
        date_rfc1123 (now ()), subj, bulk_hdrs, body_html);
      {
        declare exit handler for sqlstate '*' { subscriber_ok := 0; };
        smtp_send (smtp_server, sprintf ('%s <%s>', from_name, from_addr), _email, msg);
      }
    }

    if (subscriber_ok = 1)
    {
      -- One subscriber's unreachable mailbox/relay hiccup must not abort
      -- the whole batch, and a failed send must not update WS_LAST_SENT_AT
      -- so the next scheduled run retries it.
      update DB.DBA.WEBLOG_SUBSCRIBER set WS_LAST_SENT_AT = now () where WS_TOKEN = _tok;
      sent_count := sent_count + 1;
    }
    else
      failed_count := failed_count + 1;
  }

  if (failed_count > 0)
    DB.DBA.WEBLOG_NEWSLETTER_NOTIFY_ADMIN (coll, 'digest send had failures',
      sprintf ('%d of %d confirmed subscriber(s) could not be sent this batch (covering %d new post(s)); they will be retried on the next scheduled run.', failed_count, sent_count + failed_count, item_count));

  return sprintf ('%s: sent to %d confirmed subscriber(s) (%d failed, will retry next run) covering %d new post(s).', mode, sent_count, failed_count, item_count);
}
;

CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_SCHEDULE_DIGEST
  (
    IN event_name VARCHAR,
    IN dav_collection VARCHAR,
    IN interval_minutes INTEGER := 10080
  )
{
  declare sql_text VARCHAR;

  if (event_name is null or trim (event_name) = '')
    SIGNAL ('22023', 'event_name is required');
  if (interval_minutes is null or interval_minutes < 1)
    interval_minutes := 10080;
  if (strstr (dav_collection, chr (39)) is not null)
    SIGNAL ('22023', 'dav_collection must not contain single quote');

  sql_text := sprintf ('DB.DBA.WEBLOG_NEWSLETTER_SEND_DIGEST (''%s'')', dav_collection);

  INSERT REPLACING DB.DBA.SYS_SCHEDULED_EVENT (SE_NAME, SE_START, SE_INTERVAL, SE_SQL)
  VALUES (event_name, now (), interval_minutes, sql_text);

  return sprintf ('{"ok":true,"event":"%V","interval_minutes":%d,"sql":"%V"}', event_name, interval_minutes, sql_text);
}
;

CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_UNSCHEDULE_DIGEST (IN event_name VARCHAR)
{
  DELETE FROM DB.DBA.SYS_SCHEDULED_EVENT WHERE SE_NAME = event_name;
  return sprintf ('{"ok":true,"event":"%V","removed":true}', event_name);
}
;

-- Regenerate the static dashboard.html a Digest-auth-protected admin route
-- serves (see deploy-weblog-skinned.sql''s admin_route VHOST -- a live .vsp
-- under those same restrictive permissions serves raw source instead of
-- executing, so the dashboard is static content refreshed on a schedule
-- rather than computed per request). weblog:adminDavUser (default 'dba')
-- names the Virtuoso account whose own DAV group is granted read access;
-- only requests that Digest-authenticate as that account (or another
-- account sharing its DAV group) can retrieve the page.
CREATE PROCEDURE DB.DBA.WEBLOG_DASHBOARD_REFRESH (IN dav_collection VARCHAR)
{
  declare coll, admin_user, admin_coll, dash_rows, html VARCHAR;
  declare operator_gid INTEGER;
  declare dash_total, dash_pending, dash_confirmed, dash_unsubscribed INTEGER;
  declare stream any;
  declare rc any;
  declare admin_token, public_route, action_route, current_mode, current_content_mode, current_skin, controls_html, import_html VARCHAR;
  declare current_interval INTEGER;
  declare current_from_name, current_from_addr, current_smtp_override, current_base_url, current_admin_email, resolved_smtp, email_config_html VARCHAR;
  declare digest_scheduled, dash_scheduled INTEGER;
  declare dash_interval INTEGER;
  declare tag_schedule_html VARCHAR;

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';
  admin_user := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:adminDavUser', 'dba');
  -- The dashboard lists subscriber names/emails, so it is only ever written
  -- to the separate, non-public admin collection -- never back into the
  -- public blog collection, even if the location is missing.
  admin_coll := trim (DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:adminCollection', ''));
  if (admin_coll = '')
    signal ('42000', sprintf ('weblog:adminCollection is not set on %s -- redeploy with DB.DBA.WEBLOG_DAV_DEPLOY_SKINNED to create the admin collection.', coll));
  if (subseq (admin_coll, length (admin_coll) - 1) <> '/') admin_coll := admin_coll || '/';
  operator_gid := (select U_ID from DB.DBA.SYS_USERS where U_NAME = 'WEBLOG_OPERATOR' and U_IS_ROLE = 1);
  if (operator_gid is null)
    signal ('42000', 'Role WEBLOG_OPERATOR does not exist -- redeploy with DB.DBA.WEBLOG_DAV_DEPLOY_SKINNED.');
  -- admin_token is now vestigial: it is still read (and still emitted as a
  -- harmless, unused hidden form field below) purely so every existing
  -- sprintf argument list keeps its exact placeholder count -- the actual
  -- security boundary is action_route's real HTTP Digest auth_fn gate, not
  -- this value, which nothing generates or checks anymore. See
  -- DB.DBA.WEBLOG_ADMIN_AUTH_FN in deploy-weblog-skinned.sql for why.
  admin_token := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:adminActionToken', '');
  public_route := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:publicRoute', coll);
  action_route := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:actionRoute', '');
  current_mode := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterMode', 'digest');
  current_content_mode := lower (trim (DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterContentMode', 'auto')));
  if (current_content_mode <> 'snippet' and current_content_mode <> 'full') current_content_mode := 'auto';
  current_skin := lower (trim (DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:skin', 'classic')));
  if (current_skin <> 'editorial') current_skin := 'classic';
  current_interval := 10080;
  digest_scheduled := 0;
  {
    declare exit handler for sqlstate '*' { ; };
    for (select SE_INTERVAL as _i from DB.DBA.SYS_SCHEDULED_EVENT where SE_NAME = sprintf ('weblog-newsletter-digest:%s', coll)) do
    {
      current_interval := _i;
      digest_scheduled := 1;
    }
  }
  dash_interval := 5;
  dash_scheduled := 0;
  {
    declare exit handler for sqlstate '*' { ; };
    for (select SE_INTERVAL as _i from DB.DBA.SYS_SCHEDULED_EVENT where SE_NAME = sprintf ('weblog-dashboard-refresh:%s', coll)) do
    {
      dash_interval := _i;
      dash_scheduled := 1;
    }
  }

  current_from_name := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterFromName', 'Weblog Newsletter');
  current_from_addr := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterFromAddress', 'noreply@localhost');
  current_smtp_override := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterSmtpServer', '');
  current_base_url := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterConfirmBaseUrl', '');
  current_admin_email := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:adminEmail', '');
  resolved_smtp := '(none configured)';
  {
    declare exit handler for sqlstate '*' { ; };
    if ((select count (*) from DB.DBA.SYS_PROCEDURES where P_NAME = 'DB.DBA.WEBLOG_NEWSLETTER_RESOLVE_SMTP') > 0)
    {
      declare _rs VARCHAR;
      _rs := DB.DBA.WEBLOG_NEWSLETTER_RESOLVE_SMTP (coll);
      if (_rs is not null and trim (_rs) <> '') resolved_smtp := _rs;
    }
  }

  dash_total := 0;
  dash_pending := 0;
  dash_confirmed := 0;
  dash_unsubscribed := 0;
  dash_rows := '';
  for (select WS_STATUS as _s from DB.DBA.WEBLOG_SUBSCRIBER where WS_DAV_COLLECTION = coll) do
  {
    dash_total := dash_total + 1;
    if (_s = 'pending') dash_pending := dash_pending + 1;
    else if (_s = 'confirmed') dash_confirmed := dash_confirmed + 1;
    else if (_s = 'unsubscribed') dash_unsubscribed := dash_unsubscribed + 1;
  }
  for (select WS_EMAIL as _e, WS_NAME as _n, WS_STATUS as _s, WS_TOKEN as _tok, WS_SUBSCRIBED_AT as _sub, WS_CONFIRMED_AT as _conf, WS_LAST_SENT_AT as _sent
         from DB.DBA.WEBLOG_SUBSCRIBER
        where WS_DAV_COLLECTION = coll
        order by WS_SUBSCRIBED_AT desc) do
  {
    declare action_cell VARCHAR;
    -- Reuses WEBLOG_NEWSLETTER_UNSUBSCRIBE directly (same code path a
    -- subscriber's own unsubscribe link runs, RDF-mirror retraction
    -- included) -- an admin-triggered manual unsubscribe, not a separate
    -- mechanism to keep in sync with that one.
    if (_s = 'unsubscribed' or action_route = '')
      action_cell := '--';
    else
      action_cell := sprintf (
        '<form method="post" action="%s" class="row-action"><input type="hidden" name="admin_action" value="admin_unsubscribe"/><input type="hidden" name="admin_token" value="%s"/><input type="hidden" name="sub_token" value="%s"/><button type="submit" class="secondary">Unsubscribe</button></form>',
        action_route, admin_token, _tok);
    dash_rows := concat (dash_rows, sprintf (
      '<tr><td>%V</td><td>%V</td><td><span class="badge %s">%V</span></td><td>%V</td><td>%V</td><td>%V</td><td>%s</td></tr>',
      coalesce (_n, '--'), _e, _s, _s, cast (_sub as varchar), coalesce (cast (_conf as varchar), '--'), coalesce (cast (_sent as varchar), '--'), action_cell));
  }

  -- Action forms post to the PUBLIC route's ?admin_action= dispatcher (the
  -- one thing on this static, Digest-gated page that is NOT static): the
  -- token embedded here is only ever visible to someone who already passed
  -- native Digest auth to load this very page.
  if (action_route = '')
  {
    controls_html := '<section class="panel"><p class="admin-note">Admin actions are unavailable: weblog:actionRoute is not set on this collection yet (it should be generated automatically on the next deploy -- redeploy via WEBLOG_DAV_DEPLOY_SKINNED to enable).</p></section>';
  }
  else
  {
    controls_html := sprintf (
      '<section class="panel"><h2>Delivery Settings</h2><p class="panel-desc">Configure when and how new-post notifications go out.</p>' ||
      '<div class="setting-row"><div class="setting-label">Send new-post notifications now</div><div class="setting-control"><form method="post" action="%s"><input type="hidden" name="admin_action" value="send_digest_now"/><input type="hidden" name="admin_token" value="%s"/><button type="submit" class="secondary">Send now</button></form></div></div>' ||
      '<div class="setting-row"><div class="setting-label">Delivery mode <span class="badge">%V</span></div><div class="setting-control"><form method="post" action="%s"><input type="hidden" name="admin_action" value="set_digest_mode"/><input type="hidden" name="admin_token" value="%s"/><select name="mode"><option value="digest"%s>Digest (bundle new posts)</option><option value="immediate"%s>Immediate (one email per post)</option></select><button type="submit">Save</button></form></div></div>' ||
      '<div class="setting-row"><div class="setting-label">Email content <span class="badge">%V</span></div><div class="setting-control"><form method="post" action="%s"><input type="hidden" name="admin_action" value="set_content_mode"/><input type="hidden" name="admin_token" value="%s"/><select name="content_mode"><option value="auto"%s>Auto</option><option value="snippet"%s>Always snippet</option><option value="full"%s>Always full post</option></select><button type="submit">Save</button></form></div></div>' ||
      '<div class="setting-row"><div class="setting-label">Skin <span class="badge">%V</span></div><div class="setting-control"><form method="post" action="%s"><input type="hidden" name="admin_action" value="set_skin"/><input type="hidden" name="admin_token" value="%s"/><select name="skin_choice"><option value="classic"%s>Classic</option><option value="editorial"%s>Editorial</option></select><button type="submit">Save</button></form><span class="hint">Preview: ?skin=classic or ?skin=editorial</span></div></div>' ||
      '</section>',
      action_route, admin_token,
      current_mode, action_route, admin_token, case when current_mode = 'digest' then ' selected="selected"' else '' end, case when current_mode = 'immediate' then ' selected="selected"' else '' end,
      current_content_mode, action_route, admin_token, case when current_content_mode = 'auto' then ' selected="selected"' else '' end, case when current_content_mode = 'snippet' then ' selected="selected"' else '' end, case when current_content_mode = 'full' then ' selected="selected"' else '' end,
      current_skin, action_route, admin_token, case when current_skin = 'classic' then ' selected="selected"' else '' end, case when current_skin = 'editorial' then ' selected="selected"' else '' end);
  }

  -- Sender identity, SMTP relay override, and the base URL used to build
  -- every absolute link in an email -- previously only settable via a raw
  -- DAV_PROP_SET call. resolved_smtp shows what WEBLOG_NEWSLETTER_RESOLVE_SMTP
  -- actually picks when the override is blank, so the admin isn't guessing.
  email_config_html := '';
  if (action_route <> '')
  {
    email_config_html := sprintf (
      '<section class="panel"><h2>Email Server Config</h2><p class="panel-desc">Sender identity, SMTP relay override, and the base URL used to build absolute links in every email.</p>' ||
      '<form method="post" action="%s" class="manual-add-form"><input type="hidden" name="admin_action" value="set_email_config"/><input type="hidden" name="admin_token" value="%s"/>' ||
      '<table class="manual-add"><tbody>' ||
      '<tr><td>From name</td><td><input type="text" name="from_name" value="%V"/></td></tr>' ||
      '<tr><td>From address</td><td><input type="email" name="from_address" value="%V"/></td></tr>' ||
      '<tr><td>Admin email</td><td><input type="email" name="admin_email" value="%V" placeholder="you@example.org"/></td></tr>' ||
      '<tr><td>SMTP server override</td><td><input type="text" name="smtp_server" value="%V" placeholder="blank = use server default"/></td></tr>' ||
      '<tr><td>Base URL</td><td><input type="text" name="confirm_base_url" value="%V" placeholder="https://example.org"/></td></tr>' ||
      '</tbody></table>' ||
      '<button type="submit">Save</button>' ||
      '<p class="hint">Currently resolved SMTP relay: <strong>%V</strong>. Base URL is required for any email link (post, unsubscribe) to work. Admin email is used as Reply-To on outgoing newsletter mail and receives operational alerts (new confirmed subscribers, failed digest sends) -- leave it blank to disable both.</p>' ||
      '</form></section>',
      action_route, admin_token, current_from_name, current_from_addr, current_admin_email, current_smtp_override, current_base_url, resolved_smtp);
  }

  -- Admin-only bulk onboarding: imported rows land 'confirmed' immediately
  -- (the admin is vouching for the list) and each gets an activation-notice
  -- email with an unsubscribe link -- see WEBLOG_NEWSLETTER_IMPORT_ONE.
  -- Two separate forms (CSV vs RDF) since they need different fields
  -- (a format selector for RDF) and mixing file inputs of different
  -- purposes into one multipart form invites uploading the wrong kind.
  import_html := '';
  if (action_route <> '')
  {
    declare manual_rows_html VARCHAR;
    declare mi INTEGER;
    manual_rows_html := '';
    for (mi := 1; mi <= 5; mi := mi + 1)
    {
      manual_rows_html := concat (manual_rows_html, sprintf (
        '<tr><td><input type="text" name="name%d" placeholder="Name (optional)"/></td><td><input type="email" name="email%d" placeholder="email@example.org"/></td></tr>',
        mi, mi));
    }

    import_html := sprintf (
      '<section class="panel"><h2>Import Subscribers</h2><p class="panel-desc">Admin-only onboarding: added subscribers are marked confirmed immediately and sent an activation notice with an unsubscribe link -- no confirm-click required, but they can opt out.</p>' ||
      '<div class="import-grid">' ||
      '<div class="import-card"><h3>CSV Upload</h3><p class="hint">Header row with "email" (required) and optional "name" / "country" columns.</p><form method="post" action="%s" enctype="multipart/form-data"><input type="hidden" name="admin_action" value="import_subscribers_csv"/><input type="hidden" name="admin_token" value="%s"/><input type="file" name="importfile" accept=".csv,text/csv" required/><button type="submit">Import CSV</button></form></div>' ||
      '<div class="import-card"><h3>RDF Upload</h3><p class="hint">Looks for schema:Person / schema:email (+ optional schema:name / schema:addressCountry; name and country not extracted for JSON-LD).</p><form method="post" action="%s" enctype="multipart/form-data"><select name="rdf_format"><option value="turtle">Turtle</option><option value="jsonld">JSON-LD</option><option value="ntriples">N-Triples</option><option value="nquads">N-Quads</option><option value="trig">TriG</option></select><input type="hidden" name="admin_action" value="import_subscribers_rdf"/><input type="hidden" name="admin_token" value="%s"/><input type="file" name="importfile" accept=".ttl,.jsonld,.json,.nt,.nq,.trig,.n3" required/><button type="submit">Import RDF</button></form></div>' ||
      '<div class="import-card"><h3>Manual Entry</h3><p class="hint">Fill in one or more rows -- blank email rows are ignored.</p><form method="post" action="%s"><input type="hidden" name="admin_action" value="import_subscribers_manual"/><input type="hidden" name="admin_token" value="%s"/><table class="manual-add"><thead><tr><th>Name</th><th>Email</th></tr></thead><tbody>%s</tbody></table><button type="submit">Add Subscribers</button></form></div>' ||
      '</div></section>',
      action_route, admin_token,
      action_route, admin_token,
      action_route, admin_token, manual_rows_html);
  }

  -- Per-post schema:category (tag) / schema:position (pin) metadata --
  -- index.vsp already reads and filters on both (category facet, pinned
  -- post) but until now the only way to WRITE either was a raw
  -- DAV_PROP_SET call. Pinning is delegated to WEBLOG_DAV_SET_PIN (from
  -- the separate, optional register-weblog-pinning-tool.sql template,
  -- which already implements the "only one post pinned at a time"
  -- invariant correctly) when installed; category is set directly here
  -- since it has no such invariant to preserve.
  -- Also surfaces the two background jobs this collection can run
  -- (SYS_SCHEDULED_EVENT-backed) with an on/off toggle plus interval,
  -- instead of only the newsletter digest's interval being editable and
  -- the dashboard's own auto-refresh having no admin control at all.
  tag_schedule_html := '';
  if (action_route <> '')
  {
    declare posts_rows, categories_datalist VARCHAR;
    declare digest_status_class, digest_status_text, dash_status_class, dash_status_text VARCHAR;
    declare cat_dict any;
    posts_rows := '';
    categories_datalist := '';
    cat_dict := dict_new (31);
    for (select RES_ID as _rid, RES_NAME as _rname
           from WS.WS.SYS_DAV_RES
          where (RES_FULL_PATH like coll || '%.html' or RES_FULL_PATH like coll || '%.md')
            and RES_NAME not like '._%'
            and RES_NAME <> 'index.vsp'
            and RES_NAME <> 'dashboard.html'
          order by RES_NAME asc) do
    {
      declare _cat, _pos, _pin_target, _pin_label, _pin_badge VARCHAR;
      _cat := null;
      _pos := null;
      for (select PROP_VALUE as _v, PROP_NAME as _n from WS.WS.SYS_DAV_PROP
            where PROP_PARENT_ID = _rid and PROP_TYPE = 'R' and PROP_NAME in ('schema:category', 'schema:position')) do
      {
        if (_n = 'schema:category') _cat := cast (_v as varchar);
        else if (_n = 'schema:position') _pos := cast (_v as varchar);
      }
      -- category-options datalist: existing values become one-click
      -- suggestions (the "auto" side of tagging) while the same input
      -- stays a free-text field for anything new (the "manual" side) --
      -- one field, two ways to fill it in, rather than a separate
      -- dropdown-only vs type-only choice.
      if (_cat is not null and trim (_cat) <> '' and dict_get (cat_dict, trim (_cat), null) is null)
      {
        dict_put (cat_dict, trim (_cat), 1);
        categories_datalist := concat (categories_datalist, sprintf ('<option value="%V"></option>', trim (_cat)));
      }
      if (_pos = '1')
      {
        _pin_target := '0';
        _pin_label := 'Unpin';
        _pin_badge := '<span class="badge confirmed">Pinned</span>';
      }
      else
      {
        _pin_target := '1';
        _pin_label := 'Pin';
        _pin_badge := '';
      }
      -- Per-row forms, not a single shared post-picker + Save at the
      -- bottom: category and pin are independent one-click/one-field
      -- actions right next to the post they act on, and submitting one
      -- never touches the other's value.
      posts_rows := concat (posts_rows, sprintf (
        '<tr><td>%V %s</td>' ||
        '<td><form method="post" action="%s" class="row-action row-tag"><input type="hidden" name="admin_action" value="set_post_category"/><input type="hidden" name="admin_token" value="%s"/><input type="hidden" name="post_name" value="%V"/><input type="text" name="category" list="category-options" value="%V" placeholder="Uncategorized"/><button type="submit" class="secondary">Save</button></form></td>' ||
        '<td><form method="post" action="%s" class="row-action"><input type="hidden" name="admin_action" value="set_post_pin"/><input type="hidden" name="admin_token" value="%s"/><input type="hidden" name="post_name" value="%V"/><input type="hidden" name="pinned" value="%s"/><button type="submit" class="secondary">%s</button></form></td></tr>',
        _rname, _pin_badge,
        action_route, admin_token, _rname, coalesce (_cat, ''),
        action_route, admin_token, _rname, _pin_target, _pin_label));
    }

    digest_status_class := case when digest_scheduled = 1 then 'confirmed' else 'unsubscribed' end;
    digest_status_text := case when digest_scheduled = 1 then 'Scheduled' else 'Off' end;
    dash_status_class := case when dash_scheduled = 1 then 'confirmed' else 'unsubscribed' end;
    dash_status_text := case when dash_scheduled = 1 then 'Scheduled' else 'Off' end;

    tag_schedule_html := sprintf (
      '<section class="panel"><h2>Tagging &amp; Scheduling</h2><p class="panel-desc">Per-post category/pin metadata, and this collection''s background jobs.</p>' ||
      '<datalist id="category-options">%s</datalist>' ||
      '<h3>Post Tags &amp; Pinning</h3><table class="subscribers"><thead><tr><th>Post</th><th>Category</th><th>Pinned</th></tr></thead><tbody>%s</tbody></table>' ||
      '<h3>Scheduled Jobs</h3>' ||
      '<div class="setting-row"><div class="setting-label">Newsletter digest check <span class="badge %s">%V</span></div><div class="setting-control"><form method="post" action="%s"><input type="hidden" name="admin_action" value="set_digest_schedule"/><input type="hidden" name="admin_token" value="%s"/><select name="digest_enabled"><option value="1"%s>On</option><option value="0"%s>Off</option></select><input type="number" name="minutes" min="1" value="%d"/><button type="submit">Save</button></form></div></div>' ||
      '<div class="setting-row"><div class="setting-label">Dashboard auto-refresh <span class="badge %s">%V</span></div><div class="setting-control"><form method="post" action="%s"><input type="hidden" name="admin_action" value="set_dashboard_schedule"/><input type="hidden" name="admin_token" value="%s"/><select name="dash_enabled"><option value="1"%s>On</option><option value="0"%s>Off</option></select><input type="number" name="dash_minutes" min="1" value="%d"/><button type="submit">Save</button></form></div></div>' ||
      '</section>',
      categories_datalist,
      posts_rows,
      digest_status_class, digest_status_text, action_route, admin_token, case when digest_scheduled = 1 then ' selected="selected"' else '' end, case when digest_scheduled = 0 then ' selected="selected"' else '' end, current_interval,
      dash_status_class, dash_status_text, action_route, admin_token, case when dash_scheduled = 1 then ' selected="selected"' else '' end, case when dash_scheduled = 0 then ' selected="selected"' else '' end, dash_interval);
  }

  html := sprintf (
    '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><title>Subscriber Dashboard</title><style>' ||
    ':root{--accent:#1f4e79;--accent-soft:#eaf1f8;--bg:#f5f7fa;--surface:#ffffff;--border:#e1e7ee;--text:#172838;--muted:#64748b;--ok:#1a7f4e;--ok-bg:#e7f6ee;--warn:#b7791f;--warn-bg:#fdf3e2;--danger:#b3261e;--danger-bg:#fbeceb;--radius:10px;--shadow:0 1px 2px rgba(15,23,42,.04),0 1px 8px rgba(15,23,42,.05);}' ||
    -- Manual toggle overrides the OS preference: the media query is guarded
    -- with :not([data-theme="light"]) so an explicit light choice while the
    -- OS is in dark mode isn''t clobbered back to dark by the media query
    -- (this exact gap existed here before the toggle was added -- the
    -- established weblog-skin toggle in deploy-weblog-skinned.sql already
    -- guards it this way, reused verbatim rather than reinvented).
    '@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--accent:#4db8ff;--accent-soft:#12293d;--bg:#0f1620;--surface:#161f2c;--border:#263241;--text:#e7edf5;--muted:#93a2b5;--ok:#3ed08c;--ok-bg:#0f2c20;--warn:#f0b429;--warn-bg:#2e2510;--danger:#ff6b64;--danger-bg:#331416;--shadow:0 1px 2px rgba(0,0,0,.4),0 1px 10px rgba(0,0,0,.35);}}' ||
    'html[data-theme="dark"]{--accent:#4db8ff;--accent-soft:#12293d;--bg:#0f1620;--surface:#161f2c;--border:#263241;--text:#e7edf5;--muted:#93a2b5;--ok:#3ed08c;--ok-bg:#0f2c20;--warn:#f0b429;--warn-bg:#2e2510;--danger:#ff6b64;--danger-bg:#331416;--shadow:0 1px 2px rgba(0,0,0,.4),0 1px 10px rgba(0,0,0,.35);}' ||
    'html[data-theme="light"]{--accent:#1f4e79;--accent-soft:#eaf1f8;--bg:#f5f7fa;--surface:#ffffff;--border:#e1e7ee;--text:#172838;--muted:#64748b;--ok:#1a7f4e;--ok-bg:#e7f6ee;--warn:#b7791f;--warn-bg:#fdf3e2;--danger:#b3261e;--danger-bg:#fbeceb;--shadow:0 1px 2px rgba(15,23,42,.04),0 1px 8px rgba(15,23,42,.05);}' ||
    '*{box-sizing:border-box;}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--text);margin:0;padding:2.5rem 1.5rem;}' ||
    'main{max-width:64rem;margin:0 auto;}' ||
    '.page-head{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;flex-wrap:wrap;margin-bottom:1.75rem;}.page-head h1{font-size:1.55rem;margin:0 0 .3rem;letter-spacing:-.01em;}.page-head p{margin:0;color:var(--muted);font-size:.92rem;}' ||
    -- A sliding switch (track + icons at each end + a moving thumb), not an
    -- icon-only button that swaps glyph on click: the earlier icon button
    -- read as an unlabeled blank square at this size (confirmed live via
    -- its own verification screenshot) -- a switch is self-explanatory by
    -- shape alone (this IS a two-state toggle) even before either icon
    -- registers, and is the conventional pattern for exactly this control
    -- in dashboard/settings UI (GitHub, Stripe, Notion, Linear, etc.).
    '.theme-switch{display:inline-flex;align-items:center;gap:.5rem;background:none;border:none;padding:0;cursor:pointer;flex:0 0 auto;}' ||
    '.theme-switch-label{font-size:.78rem;color:var(--muted);font-weight:600;}' ||
    '.theme-switch-track{position:relative;display:inline-flex;align-items:center;justify-content:space-between;width:3.4rem;height:1.7rem;border-radius:999px;background:var(--border);padding:0 .35rem;box-sizing:border-box;transition:background .2s ease;}' ||
    '.theme-switch-track svg{position:relative;z-index:1;width:.8rem;height:.8rem;fill:none;stroke:var(--muted);stroke-width:2;pointer-events:none;}' ||
    '.theme-switch-thumb{position:absolute;top:.15rem;left:.15rem;width:1.4rem;height:1.4rem;border-radius:50%%;background:var(--surface);box-shadow:0 1px 3px rgba(0,0,0,.3);transition:transform .2s ease;}' ||
    -- Thumb position and track tint track the EFFECTIVE theme, same
    -- explicit-choice-wins-over-OS-preference precedence as the rest of the
    -- page''s own colors, so the switch never shows a state that contradicts
    -- what''s actually on screen.
    '@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .theme-switch-thumb{transform:translateX(1.7rem);}:root:not([data-theme="light"]) .theme-switch-track{background:var(--accent-soft);}}' ||
    'html[data-theme="dark"] .theme-switch-thumb{transform:translateX(1.7rem);}html[data-theme="dark"] .theme-switch-track{background:var(--accent-soft);}' ||
    '.row-action{margin:0;}.row-action button{padding:.25rem .6rem;font-size:.78rem;white-space:nowrap;}' ||
    '.row-tag{display:flex;gap:.4rem;align-items:center;}.row-tag input[type="text"]{width:8rem;padding:.25rem .5rem;font-size:.78rem;}' ||
    '.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(9.5rem,1fr));gap:.85rem;margin-bottom:1.75rem;}' ||
    '.stat{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--accent);border-radius:var(--radius);box-shadow:var(--shadow);padding:1rem 1.15rem;}' ||
    '.stat.pending{border-left-color:var(--warn);}.stat.confirmed{border-left-color:var(--ok);}.stat.unsubscribed{border-left-color:var(--danger);}' ||
    '.stat .n{font-size:1.7rem;font-weight:700;line-height:1.1;}.stat .l{color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;margin-top:.25rem;}' ||
    'section.panel{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);padding:1.4rem 1.5rem;margin-bottom:1.5rem;}' ||
    'section.panel h2{font-size:1rem;margin:0 0 .2rem;}section.panel h3{font-size:.88rem;margin:0 0 .3rem;}section.panel .panel-desc{color:var(--muted);font-size:.82rem;margin:0 0 1.1rem;}' ||
    '.setting-row{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.7rem 0;border-bottom:1px solid var(--border);flex-wrap:wrap;}.setting-row:last-of-type{border-bottom:none;padding-bottom:0;}' ||
    '.setting-label{font-weight:600;font-size:.88rem;white-space:nowrap;}.setting-control{display:flex;align-items:center;gap:.55rem;flex-wrap:wrap;}' ||
    '.setting-control form{display:flex;align-items:center;gap:.55rem;flex-wrap:wrap;}' ||
    '.badge{display:inline-flex;align-items:center;font-size:.72rem;font-weight:600;padding:.15rem .55rem;border-radius:999px;background:var(--accent-soft);color:var(--accent);}' ||
    '.badge.pending{background:var(--warn-bg);color:var(--warn);}.badge.confirmed{background:var(--ok-bg);color:var(--ok);}.badge.unsubscribed{background:var(--danger-bg);color:var(--danger);}' ||
    'select,input[type="number"],input[type="text"],input[type="email"],input[type="file"]{font:inherit;font-size:.86rem;padding:.4rem .6rem;border:1px solid var(--border);border-radius:6px;background:var(--surface);color:var(--text);}' ||
    'input[type="number"]{width:5.5rem;}' ||
    'button{font:inherit;font-size:.86rem;font-weight:600;padding:.45rem 1rem;border-radius:6px;border:1px solid var(--accent);cursor:pointer;background:var(--accent);color:#fff;}' ||
    'button:hover{filter:brightness(1.1);}button.secondary{background:var(--surface);color:var(--accent);}' ||
    '.import-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1rem;}' ||
    '.import-card{border:1px solid var(--border);border-radius:8px;padding:1rem;}.import-card form{display:flex;flex-direction:column;gap:.5rem;align-items:stretch;}' ||
    'table.manual-add{width:100%%;margin-bottom:.2rem;}table.manual-add input{width:100%%;}' ||
    'table.subscribers{width:100%%;border-collapse:collapse;}table.subscribers th,table.subscribers td{text-align:left;padding:.55rem .7rem;border-bottom:1px solid var(--border);font-size:.84rem;}' ||
    'table.subscribers th{text-transform:uppercase;font-size:.68rem;letter-spacing:.06em;color:var(--muted);}table.subscribers tbody tr:hover{background:var(--accent-soft);}' ||
    '.hint{color:var(--muted);font-size:.78rem;}.refreshed{color:var(--muted);font-size:.78rem;margin-top:1.5rem;}.admin-note{color:var(--danger);}' ||
    '.admin-banner{display:flex;justify-content:space-between;align-items:center;gap:1rem;background:var(--accent-soft);border:1px solid var(--accent);color:var(--text);border-radius:8px;padding:.75rem 1rem;margin-bottom:1.25rem;font-size:.86rem;}' ||
    '.admin-banner button{background:none;border:none;color:var(--muted);cursor:pointer;font-size:.8rem;padding:0;text-decoration:underline;}' ||
    '</style>' ||
    -- FOUC guard: applies a stored manual choice before first paint, same
    -- idiom as the public weblog''s own toggle (deploy-weblog-skinned.sql)
    -- -- a distinct localStorage key so the admin''s dashboard theme choice
    -- doesn''t silently also flip their reader-facing site theme, or vice
    -- versa. Double-quoted JS strings throughout: this file is a plain
    -- (non-nested) SQL string literal, so no quote-doubling is needed here
    -- the way the nested deploy-weblog-skinned.sql required.
    '<script>(function(){try{var s=window.localStorage.getItem("weblog-dashboard-theme");if(s==="dark"||s==="light")document.documentElement.setAttribute("data-theme",s);}catch(e){}})();</script>' ||
    '</head><body><main>' ||
    '<div class="page-head"><div><h1>Subscriber Dashboard</h1><p>Newsletter subscribers, delivery settings, and onboarding tools for this weblog.</p></div><button class="theme-switch" type="button" role="switch" aria-checked="false" aria-label="Toggle light and dark theme" title="Toggle theme" data-theme-toggle><span class="theme-switch-track"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/></svg><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12.8A8.8 8.8 0 1 1 11.2 3 6.8 6.8 0 0 0 21 12.8z"/></svg><span class="theme-switch-thumb"></span></span></button></div>' ||
    '<div id="admin-banner-slot"></div>' ||
    '<div class="stats"><div class="stat"><div class="n">%d</div><div class="l">Total</div></div><div class="stat pending"><div class="n">%d</div><div class="l">Pending</div></div><div class="stat confirmed"><div class="n">%d</div><div class="l">Confirmed</div></div><div class="stat unsubscribed"><div class="n">%d</div><div class="l">Unsubscribed</div></div></div>' ||
    '%s%s%s%s' ||
    '<section class="panel"><h2>Subscribers</h2><table class="subscribers"><thead><tr><th>Name</th><th>Email</th><th>Status</th><th>Subscribed</th><th>Confirmed</th><th>Last Digest Sent</th><th>Actions</th></tr></thead><tbody>%s</tbody></table></section>' ||
    '<p class="refreshed">Refreshed %s</p>' ||
    '</main>' ||
    -- Every admin action now redirects back here (HTML/JS-level, not a
    -- real HTTP 3xx -- see the admin_action dispatcher''s own comment for
    -- why) instead of showing a separate "here''s what happened" page.
    -- This is what shows that result on landing: read admin_msg from the
    -- query string once, render it as a dismissible banner, then strip it
    -- from the URL so a reload or bookmark doesn''t keep re-showing it.
    '<script>(function(){var m=new URLSearchParams(location.search).get("admin_msg");if(!m)return;var slot=document.getElementById("admin-banner-slot");if(!slot)return;var b=document.createElement("div");b.className="admin-banner";var t=document.createElement("span");t.textContent=m;var x=document.createElement("button");x.type="button";x.textContent="Dismiss";x.addEventListener("click",function(){b.remove();});b.appendChild(t);b.appendChild(x);slot.appendChild(b);try{history.replaceState(null,"",location.pathname);}catch(e){}})();</script>' ||
    '<script>(function(){var b=document.querySelector("[data-theme-toggle]");if(!b)return;function cur(){var e=document.documentElement.getAttribute("data-theme");if(e==="dark"||e==="light")return e;return window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";}b.setAttribute("aria-checked",cur()==="dark"?"true":"false");b.addEventListener("click",function(){var n=cur()==="dark"?"light":"dark";document.documentElement.setAttribute("data-theme",n);b.setAttribute("aria-checked",n==="dark"?"true":"false");try{window.localStorage.setItem("weblog-dashboard-theme",n);}catch(e){}});})();</script>' ||
    '</body></html>',
    dash_total, dash_pending, dash_confirmed, dash_unsubscribed, controls_html, email_config_html, import_html, tag_schedule_html, dash_rows, cast (now () as varchar));

  stream := string_output ();
  http (html, stream);
  DB.DBA.DAV_DELETE_INT (coll || 'dashboard.html', 1, null, null, 0);
  DB.DBA.DAV_DELETE_INT (admin_coll || 'dashboard.html', 1, null, null, 0);
  -- Owner = the collection's admin, group = WEBLOG_OPERATOR (by numeric
  -- U_ID -- a role NAME here silently stores RES_GROUP = -12), no world
  -- bits: owner and role members can read/write, anonymous gets 401.
  rc := DB.DBA.DAV_RES_UPLOAD_STRSES_INT (admin_coll || 'dashboard.html', stream, 'text/html', '110110000N', admin_user, operator_gid, null, null, 0);
  if (rc < 0)
    signal ('42000', sprintf ('DAV upload failed for dashboard.html, rc=%d', rc));
  -- Re-assert owner/group/perms explicitly: confirmed live on a real
  -- instance that the perms argument above did NOT take effect (RES_PERMS
  -- came back as a plain default '110100100' -- rw-r--r--, WORLD-READABLE --
  -- instead of the requested '110110000' -- no world access at all). Unlike
  -- index.vsp (where the same silent reset broke execution), a reset here
  -- is a direct exposure of subscriber names/emails, so it is re-applied
  -- unconditionally rather than only fixed after the fact.
  {
    declare admin_owner_uid int;
    admin_owner_uid := (select U_ID from DB.DBA.SYS_USERS where U_NAME = admin_user);
    if (admin_owner_uid is not null)
      update WS.WS.SYS_DAV_RES set RES_OWNER = admin_owner_uid, RES_GROUP = operator_gid, RES_PERMS = '110110000N' where RES_FULL_PATH = admin_coll || 'dashboard.html';
  }
  return sprintf ('{"ok":true,"total":%d,"pending":%d,"confirmed":%d,"unsubscribed":%d}', dash_total, dash_pending, dash_confirmed, dash_unsubscribed);
}
;

CREATE PROCEDURE DB.DBA.WEBLOG_DASHBOARD_SCHEDULE_REFRESH
  (
    IN event_name VARCHAR,
    IN dav_collection VARCHAR,
    IN interval_minutes INTEGER := 5
  )
{
  declare sql_text VARCHAR;

  if (event_name is null or trim (event_name) = '')
    SIGNAL ('22023', 'event_name is required');
  if (interval_minutes is null or interval_minutes < 1)
    interval_minutes := 5;
  if (strstr (dav_collection, chr (39)) is not null)
    SIGNAL ('22023', 'dav_collection must not contain single quote');

  sql_text := sprintf ('DB.DBA.WEBLOG_DASHBOARD_REFRESH (''%s'')', dav_collection);

  INSERT REPLACING DB.DBA.SYS_SCHEDULED_EVENT (SE_NAME, SE_START, SE_INTERVAL, SE_SQL)
  VALUES (event_name, now (), interval_minutes, sql_text);

  return sprintf ('{"ok":true,"event":"%V","interval_minutes":%d,"sql":"%V"}', event_name, interval_minutes, sql_text);
}
;

CREATE PROCEDURE DB.DBA.WEBLOG_DASHBOARD_UNSCHEDULE_REFRESH (IN event_name VARCHAR)
{
  DELETE FROM DB.DBA.SYS_SCHEDULED_EVENT WHERE SE_NAME = event_name;
  return sprintf ('{"ok":true,"event":"%V","removed":true}', event_name);
}
;

-- Usage: subscribe/confirm/unsubscribe are normally driven by index.vsp's
-- ?nl_action= dispatcher, but can be invoked directly for testing:
-- SELECT DB.DBA.WEBLOG_NEWSLETTER_SUBSCRIBE ('/DAV/home/dba/weblog-test/', 'someone@example.org', 'GB', 'http://localhost:8890');
-- SELECT DB.DBA.WEBLOG_NEWSLETTER_SEND_DIGEST ('/DAV/home/dba/weblog-test/');
--
-- Usage: schedule the weekly digest (default 10080 minutes).
-- SELECT DB.DBA.WEBLOG_NEWSLETTER_SCHEDULE_DIGEST ('weblog-test newsletter digest', '/DAV/home/dba/weblog-test/');
--
-- Usage: unschedule.
-- SELECT DB.DBA.WEBLOG_NEWSLETTER_UNSCHEDULE_DIGEST ('weblog-test newsletter digest');
--
-- Usage: refresh the admin dashboard immediately, then keep it fresh every 5 minutes.
-- SELECT DB.DBA.WEBLOG_DASHBOARD_REFRESH ('/DAV/home/dba/weblog-test/');
-- SELECT DB.DBA.WEBLOG_DASHBOARD_SCHEDULE_REFRESH ('weblog-test dashboard refresh', '/DAV/home/dba/weblog-test/');
--
-- Usage: unschedule the dashboard refresh.
-- SELECT DB.DBA.WEBLOG_DASHBOARD_UNSCHEDULE_REFRESH ('weblog-test dashboard refresh');
--
-- Usage: designate a different Virtuoso account as the dashboard admin
-- (default 'dba'; redeploys reset it to the deploying dav_user). That
-- account owns the admin collection's dashboard.html; members of the
-- WEBLOG_OPERATOR role can read it too:  grant WEBLOG_OPERATOR to <user>;
-- SELECT DB.DBA.DAV_PROP_SET ('/DAV/home/dba/weblog-test/', 'weblog:adminDavUser', 'dba', 'dba', (SELECT pwd_magic_calc (U_NAME, U_PASSWORD, 1) FROM DB.DBA.SYS_USERS WHERE U_NAME = 'dba'), 1);

-- ============================================================================
-- SECTION 2 of 2: templates/deploy-weblog-skinned.sql
-- ============================================================================

-- Deploy a parameterized, multi-skin weblog index.vsp (with a built-in
-- ?nl_action= newsletter subscribe/confirm/unsubscribe dispatcher) for an
-- arbitrary WebDAV collection.
-- Run as: isql 1111 dba <password> deploy-weblog-skinned.sql
--
-- Unlike deploy-weblog-opl-site.sql / deploy-weblog-opl-site-facet.sql (which
-- are fixed, single-site OpenLink-themed deploys), this template takes the
-- DAV collection, public route, title, tagline and default skin as runtime
-- parameters to DB.DBA.WEBLOG_DAV_DEPLOY_SKINNED, so it can be pointed at any
-- collection without hand-editing the SQL.
--
-- Look-and-feel ("skin") and the newsletter feature are both configuration
-- modalities resolved AT REQUEST TIME by the deployed index.vsp, not baked in
-- at deploy time, so changing either needs no redeploy:
--   weblog:skin               'classic' (default) | 'editorial'
--                              per-request override: ?skin=<name>
--   weblog:newsletterEnabled  'true' | 'false' (default false)
-- Both are read via DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (defined below,
-- persistent -- also used by templates/register-weblog-newsletter.sql),
-- which reads a custom WebDAV property set on the COLLECTION resource itself
-- with DB.DBA.DAV_PROP_SET, the same property mechanism already used for the
-- per-post schema:category / schema:position facet metadata.
--
-- See references/skin-authoring-contract.md for what a skin must supply.

CREATE PROCEDURE DB.DBA.TMP_DEPLOY_WEBLOG_SKINNED_VHOST_REMOVE (IN _lh varchar, IN _vh varchar, IN _lp varchar)
{
  declare exit handler for sqlstate '*' { ; };
  DB.DBA.VHOST_REMOVE (lhost=>_lh, vhost=>_vh, lpath=>_lp);
}
;

CREATE PROCEDURE DB.DBA.TMP_DEPLOY_WEBLOG_SKINNED_DEFAULT_PIN (IN _coll varchar, IN _dav_user varchar)
{
  declare _pwd, _target varchar;
  declare _existing, _rc int;
  declare exit handler for sqlstate '*' { ; };

  if (_coll is null or _coll = '') return 0;
  if (subseq (_coll, length (_coll) - 1) <> '/') _coll := _coll || '/';
  _existing := 0;
  _target := null;

  select count(*) into _existing
    from WS.WS.SYS_DAV_RES R, WS.WS.SYS_DAV_PROP P
   where (R.RES_FULL_PATH like _coll || '%.html'
       or R.RES_FULL_PATH like _coll || '%.md')
     and R.RES_NAME not like '._%'
     and R.RES_NAME not in ('index.vsp', 'newsletter.vsp')
     and P.PROP_PARENT_ID = R.RES_ID
     and P.PROP_TYPE = 'R'
     and P.PROP_NAME = 'schema:position'
     and trim (cast (P.PROP_VALUE as varchar)) <> ''
     and trim (cast (P.PROP_VALUE as varchar)) <> '0';

  if (_existing > 0) return 0;

  for (select top 1 RES_FULL_PATH as _path
         from WS.WS.SYS_DAV_RES
        where (RES_FULL_PATH like _coll || '%.html'
            or RES_FULL_PATH like _coll || '%.md')
          and RES_NAME not like '._%'
          and RES_NAME not in ('index.vsp', 'newsletter.vsp')
        order by RES_MOD_TIME desc, RES_NAME desc) do
  {
    _target := _path;
  }

  if (_target is null) return 0;

  -- DAV_PROP_SET_INT, not DAV_PROP_SET as _dav_user -- see the comment on
  -- the admin_action property writes below for why.
  _rc := DB.DBA.DAV_PROP_SET_INT (_target, 'schema:position', '1', null, null, 0, 0, 1);
  return _rc;
}
;

-- Native HTTP Digest auth_fn for the admin-action VHOST (see admin_route/
-- action_route below) -- verified live 2026-09-23 against a real remote
-- instance and locally: three cases confirmed correct (unauthenticated ->
-- 401; authenticated as the collection's configured weblog:adminDavUser ->
-- allowed; authenticated as a DIFFERENT genuinely-valid SQL account that is
-- NOT this collection's admin -> denied). Wraps the native
-- DB.DBA.HP_AUTH_SQL_USER builtin (which does the real Digest verification
-- against Virtuoso's own SYS_USERS credential store -- no hand-rolled
-- crypto here) with a per-collection authorization check on top, since
-- HP_AUTH_SQL_USER alone would accept ANY valid SQL login on the whole
-- instance, not just the one designated as this collection's admin.
--
-- realm is deploy-time-baked as ''WeblogAdmin:<dav_collection>'' (see
-- action_route setup below) specifically so this ONE shared auth_fn can
-- serve every weblog collection deployed on the same instance, each
-- checking against its own weblog:adminDavUser -- auth_fn''s only
-- documented parameter is realm, so encoding the collection identity into
-- that string is the only way to make it collection-aware.
--
-- This REPLACES the old admin_action_token scheme (a shared secret
-- embedded in every dashboard form and thus only as safe as dashboard.html's
-- own DAV-permission gate, which does not reliably enforce on every
-- instance -- confirmed live on a real remote instance: the token was
-- fully readable by an anonymous request). Real Digest credentials checked
-- at the point of action execution have no equivalent single point of
-- failure.
CREATE PROCEDURE DB.DBA.WEBLOG_ADMIN_AUTH_FN (IN realm VARCHAR)
{
  declare ok int;
  declare lines any;
  declare auth any;
  declare uname, coll, expected_admin varchar;
  declare sep_pos, member_count int;
  declare exit handler for sqlstate '*' { return 0; };

  sep_pos := strchr (realm, ':');
  if (sep_pos is null) return 0;
  coll := subseq (realm, sep_pos + 1, length (realm));

  ok := DB.DBA.HP_AUTH_SQL_USER (realm);
  if (ok = 0) return 0;

  lines := http_request_header ();
  auth := DB.DBA.vsp_auth_vec (lines);
  uname := get_keyword ('username', auth, '');

  -- dba (the Virtuoso superuser) is always authorized, the same way it
  -- already bypasses ordinary DAV/SQL grants everywhere else.
  if (lower (trim (uname)) = 'dba') return 1;

  expected_admin := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:adminDavUser', 'dba');
  if (lower (trim (uname)) = lower (trim (expected_admin))) return 1;

  -- Members of WEBLOG_OPERATOR can read the admin collection's dashboard,
  -- so they must also be able to submit its forms.
  member_count := (select count (*) from DB.DBA.SYS_ROLE_GRANTS G, DB.DBA.SYS_USERS U, DB.DBA.SYS_USERS R
                    where U.U_NAME = trim (uname) and R.U_NAME = 'WEBLOG_OPERATOR' and R.U_IS_ROLE = 1
                      and G.GI_SUPER = U.U_ID and G.GI_SUB = R.U_ID);
  if (member_count > 0) return 1;

  return 0;
}
;

-- Shared, persistent helper: repair "double-encoded UTF-8" corruption in
-- post titles (verified live against a real post: "AI For Creativity —
-- RDF Knowledge Graph" was stored, and served, as "AI For Creativity \xC3
-- \xA2\xC2\x80\xC2\x94 RDF Knowledge Graph" -- the original em dash's UTF-8
-- bytes E2 80 94 had each been read once as Latin-1 and re-encoded as
-- UTF-8). blob_to_string() does not decode UTF-8 at all -- confirmed live
-- it returns raw bytes as a narrow string, one byte per character
-- position, and the browser is what interprets them as UTF-8 given this
-- template's <meta charset="utf-8">. A genuinely correct title's raw bytes
-- therefore look byte-for-byte identical to one "layer" of the corruption
-- wherever it happens to contain a multi-byte UTF-8 character at all --
-- there is no way to tell "raw bytes for one correctly-encoded character"
-- from "raw bytes left over after correctly decoding one layer of double
-- encoding" from the bytes alone. Confirmed live that decoding via
-- charset_recode (s, 'UTF-8', '_WIDE_') -- correct in isolation, verified
-- byte-by-byte -- corrupts an ALREADY-correct title into "?" once the
-- resulting wide string is concatenated into HTML output alongside plain
-- narrow strings and re-serialized; that is not an acceptable trade-off
-- for one known-corrupted title. This instead does a plain byte-sequence
-- replace of specific KNOWN double-encoded "smart punctuation" sequences
-- (the common Word/Google-Docs-paste corruption set: dashes, curly
-- quotes, ellipsis, bullet, trademark, nbsp, copyright, registered) for
-- their correct single-encoded bytes, staying entirely within the same
-- raw-byte narrow-string representation the rest of this template already
-- passes straight through to the browser -- verified live this fixes the
-- corrupted title and leaves an already-correct title's bytes untouched.
CREATE PROCEDURE DB.DBA.WEBLOG_FIX_MOJIBAKE (IN s VARCHAR)
{
  declare pairs any;
  declare i int;
  if (s is null or s = '') return s;
  pairs := vector (
    vector (concat (chr(195),chr(162),chr(194),chr(128),chr(194),chr(148)), concat (chr(226),chr(128),chr(148))), -- em dash —
    vector (concat (chr(195),chr(162),chr(194),chr(128),chr(194),chr(147)), concat (chr(226),chr(128),chr(147))), -- en dash –
    vector (concat (chr(195),chr(162),chr(194),chr(128),chr(194),chr(152)), concat (chr(226),chr(128),chr(152))), -- left single quote '
    vector (concat (chr(195),chr(162),chr(194),chr(128),chr(194),chr(153)), concat (chr(226),chr(128),chr(153))), -- right single quote '
    vector (concat (chr(195),chr(162),chr(194),chr(128),chr(194),chr(156)), concat (chr(226),chr(128),chr(156))), -- left double quote "
    vector (concat (chr(195),chr(162),chr(194),chr(128),chr(194),chr(157)), concat (chr(226),chr(128),chr(157))), -- right double quote "
    vector (concat (chr(195),chr(162),chr(194),chr(128),chr(194),chr(166)), concat (chr(226),chr(128),chr(166))), -- ellipsis …
    vector (concat (chr(195),chr(162),chr(194),chr(128),chr(194),chr(162)), concat (chr(226),chr(128),chr(162))), -- bullet •
    vector (concat (chr(195),chr(162),chr(194),chr(132),chr(194),chr(162)), concat (chr(226),chr(132),chr(162))), -- trademark ™
    vector (concat (chr(195),chr(130),chr(194),chr(160)), concat (chr(194),chr(160))), -- non-breaking space
    vector (concat (chr(195),chr(130),chr(194),chr(169)), concat (chr(194),chr(169))), -- copyright ©
    vector (concat (chr(195),chr(130),chr(194),chr(174)), concat (chr(194),chr(174)))  -- registered ®
  );
  for (i := 0; i < length (pairs); i := i + 1)
    s := replace (s, pairs[i][0], pairs[i][1]);
  return s;
}
;

-- Shared, persistent helper: decode a post title/category/snippet from the
-- raw UTF-8 bytes blob_to_string() returns into a WIDE string, for use as a
-- sprintf('%V', ...) argument. Verified live 2026-09-25: sprintf's %V
-- treats a NARROW string as ISO-8859-1 and re-encodes every byte above 127
-- as UTF-8, so a correct em dash (E2 80 94) was emitted as C3 A2 C2 80 C2 94
-- in every title in the sidebar, post list, hero, and feeds. %V on
-- the decoded WIDE string emits the correct UTF-8 bytes, and sprintf's
-- result is itself a plain narrow string, so nothing downstream ever has to
-- mix wide and narrow values. charset_recode() returns 0 (not a string) on
-- input that is not valid UTF-8 -- in that case fall back to the original
-- string, which %V then correctly treats as Latin-1.
CREATE PROCEDURE DB.DBA.WEBLOG_UTF8_DECODE (IN s ANY)
{
  declare w any;
  if (s is null) return '';
  if (iswidestring (s)) return s;
  if (not isstring (s)) return cast (s as varchar);
  w := charset_recode (s, 'UTF-8', '_WIDE_');
  if (iswidestring (w)) return w;
  return s;
}
;

-- Shared, persistent helper: decode the HTML character references found in
-- a post's <title> so the raw title text can be re-escaped exactly once by
-- sprintf('%V', ...). Handles every numeric reference (&#39; &#x27; &#8212;
-- &#x2014; ...), encoded here as raw UTF-8 bytes to match the rest of the
-- title, plus the common named ones. A malformed or out-of-range numeric
-- reference is left as literal text. &amp; is decoded LAST so that
-- "&amp;#x27;" (literal text "&#x27;") is not decoded twice.
CREATE PROCEDURE DB.DBA.WEBLOG_HTML_UNESCAPE (IN s VARCHAR)
{
  declare ent, digits, enc, alphabet varchar;
  declare cp, i, d, ok, base, guard int;
  if (s is null or not isstring (s) or strchr (s, '&') is null) return s;
  guard := 0;
  ent := regexp_substr ('&#[xX]?[0-9a-fA-F]+;', s, 0);
  while (ent is not null and guard < 500)
  {
    guard := guard + 1;
    digits := lower (subseq (ent, 2, length (ent) - 1));
    base := 10;
    alphabet := '0123456789';
    if (subseq (digits, 0, 1) = 'x')
    {
      base := 16;
      alphabet := '0123456789abcdef';
      digits := subseq (digits, 1);
    }
    ok := 1;
    cp := 0;
    if (length (digits) = 0 or length (digits) > 7)
      ok := 0;
    for (i := 0; ok and i < length (digits); i := i + 1)
    {
      d := locate (subseq (digits, i, i + 1), alphabet) - 1;
      if (d < 0)
        ok := 0;
      else
        cp := cp * base + d;
    }
    if (cp = 0 or cp > 1114111 or (cp >= 55296 and cp <= 57343))
      ok := 0;
    if (ok)
    {
      if (cp < 128)
        enc := chr (cp);
      else if (cp < 2048)
        enc := concat (chr (192 + bit_shift (cp, -6)), chr (128 + bit_and (cp, 63)));
      else if (cp < 65536)
        enc := concat (chr (224 + bit_shift (cp, -12)), chr (128 + bit_and (bit_shift (cp, -6), 63)), chr (128 + bit_and (cp, 63)));
      else
        enc := concat (chr (240 + bit_shift (cp, -18)), chr (128 + bit_and (bit_shift (cp, -12), 63)), chr (128 + bit_and (bit_shift (cp, -6), 63)), chr (128 + bit_and (cp, 63)));
      s := replace (s, ent, enc);
    }
    else
      s := replace (s, ent, concat ('&amp;', subseq (ent, 1)));
    ent := regexp_substr ('&#[xX]?[0-9a-fA-F]+;', s, 0);
  }
  s := replace (s, '&quot;', chr (34));
  s := replace (s, '&apos;', chr (39));
  s := replace (s, '&lt;', '<');
  s := replace (s, '&gt;', '>');
  s := replace (s, '&nbsp;', concat (chr (194), chr (160)));
  s := replace (s, '&middot;', concat (chr (194), chr (183)));
  s := replace (s, '&ndash;', concat (chr (226), chr (128), chr (147)));
  s := replace (s, '&mdash;', concat (chr (226), chr (128), chr (148)));
  s := replace (s, '&lsquo;', concat (chr (226), chr (128), chr (152)));
  s := replace (s, '&rsquo;', concat (chr (226), chr (128), chr (153)));
  s := replace (s, '&ldquo;', concat (chr (226), chr (128), chr (156)));
  s := replace (s, '&rdquo;', concat (chr (226), chr (128), chr (157)));
  s := replace (s, '&hellip;', concat (chr (226), chr (128), chr (166)));
  s := replace (s, '&amp;', '&');
  return s;
}
;

-- Shared, persistent helper: read a custom WebDAV property set on a
-- COLLECTION resource (not a post), the config mechanism for weblog:skin,
-- weblog:newsletterEnabled and friends. Falls back to default_val when the
-- collection resource or the property is missing/blank.
CREATE PROCEDURE DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (IN dav_collection VARCHAR, IN in_prop_name VARCHAR, IN default_val VARCHAR)
{
  declare coll VARCHAR;
  declare v ANY;

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';
  v := null;
  -- A collection is a row in WS.WS.SYS_DAV_COL (COL_ID / PROP_TYPE='C'),
  -- NOT in WS.WS.SYS_DAV_RES (RES_ID / PROP_TYPE='R', which only holds
  -- files) -- do not copy the per-post schema:category/position lookup
  -- pattern here, it silently matches zero rows against a collection path.
  for (select P.PROP_VALUE as _v
         from WS.WS.SYS_DAV_COL C, WS.WS.SYS_DAV_PROP P
        where C.COL_FULL_PATH = coll
          and P.PROP_PARENT_ID = C.COL_ID
          and P.PROP_TYPE = 'C'
          and P.PROP_NAME = in_prop_name) do
  {
    v := _v;
  }
  if (v is null or not isstring (v) or trim (cast (v as varchar)) = '')
    return default_val;
  return trim (cast (v as varchar));
}
;

CREATE PROCEDURE DB.DBA.WEBLOG_DAV_DEPLOY_SKINNED
  (
    IN dav_collection VARCHAR,
    IN public_route VARCHAR,
    IN weblog_title VARCHAR := 'WebDAV Weblog',
    IN weblog_tagline VARCHAR := 'A configurable, skinnable weblog view of a WebDAV folder.',
    IN default_skin VARCHAR := 'classic',
    IN dav_user VARCHAR := 'dba',
    IN admin_collection VARCHAR := null,
    IN admin_host VARCHAR := null,
    IN admin_listener VARCHAR := null,
    IN tagline_link_url VARCHAR := null,
    IN tagline_link_text VARCHAR := null,
    IN allow_template_overwrite INTEGER := 0
  )
{
  declare rc any;
  declare coll, route, index_path, admin_route, action_route, action_realm VARCHAR;
  declare admin_coll, admin_lpath, admin_lhost, uriqa_host, ssl_port VARCHAR;
  declare operator_gid, owner_uid, admin_col_id int;
  declare dashboard_status VARCHAR;
  declare val_present int;
  declare action_opts any;
  declare index_content VARCHAR;
  declare index_stream any;

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';
  route := trim (public_route);
  if (subseq (route, length (route) - 1) <> '/') route := route || '/';
  if (default_skin <> 'editorial') default_skin := 'classic';

  -- Optional real hyperlink appended after the plain tagline in the
  -- VISIBLE masthead span only -- RSS <description> and <meta
  -- name="description"> keep using weblog_tagline as plain text
  -- unchanged. weblog_tagline itself is HTML-escaped at request time via
  -- sprintf('%V', ...), so embedding a raw <a> tag directly in it would
  -- show up as literal escaped text there, not a link (confirmed live);
  -- this builds the link separately and safely instead.
  declare tagline_link_html VARCHAR;
  tagline_link_html := '';
  if (tagline_link_url is not null and trim (tagline_link_url) <> ''
      and tagline_link_text is not null and trim (tagline_link_text) <> '')
    tagline_link_html := sprintf (' <a href="%V" target="_top" rel="noopener noreferrer">%V</a>', trim (tagline_link_url), trim (tagline_link_text));

  index_path := coll || 'index.vsp';
  -- Admin route: serves the STATIC dashboard.html (refreshed by
  -- DB.DBA.WEBLOG_DASHBOARD_REFRESH) from a SEPARATE admin collection, never
  -- from the public blog collection -- anything inside the public
  -- collection inherits whatever makes it public (on UB an ACL on the blog
  -- collection overrode the file's own 000 world bits, leaving subscriber
  -- PII anonymously readable at /DAV/.../dashboard.html). The admin
  -- collection is owned by dav_user, grouped to the WEBLOG_OPERATOR role,
  -- with no world bits, so the raw DAV path and the admin route both
  -- require Digest auth as the owner or a role member.
  admin_route := concat (subseq (route, 0, length (route) - 1), '-admin/');
  admin_lpath := subseq (admin_route, 0, length (admin_route) - 1);

  -- Admin collection resolution: explicit argument, else the location
  -- recorded by a previous deploy, else the suggested default -- an
  -- aunt/uncle of the blog collection (sibling of its parent), so it sits
  -- outside the public parent's subtree too:
  --   /DAV/demos/daas/  ->  /DAV/demos-daas-admin/
  admin_coll := trim (coalesce (admin_collection, ''));
  if (admin_coll = '')
    admin_coll := trim (DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:adminCollection', ''));
  if (admin_coll = '')
  {
    declare trimmed, blog_name, parent_path, parent_name, grand_path VARCHAR;
    declare p1, p2 int;
    trimmed := subseq (coll, 0, length (coll) - 1);
    p1 := strrchr (trimmed, '/');
    parent_path := subseq (trimmed, 0, p1);
    blog_name := subseq (trimmed, p1 + 1);
    p2 := strrchr (parent_path, '/');
    grand_path := subseq (parent_path, 0, p2 + 1);
    parent_name := subseq (parent_path, p2 + 1);
    if (p2 is null or grand_path not like '/DAV/%')
      signal ('22023', sprintf ('Cannot derive a default admin collection for %s (it has no grandparent under /DAV/) -- pass admin_collection explicitly.', coll));
    admin_coll := concat (grand_path, parent_name, '-', blog_name, '-admin/');
  }
  if (subseq (admin_coll, length (admin_coll) - 1) <> '/') admin_coll := admin_coll || '/';
  if (admin_coll not like '/DAV/%')
    signal ('22023', sprintf ('Admin collection %s must be a DAV path under /DAV/.', admin_coll));
  if (admin_coll = coll or admin_coll like concat (coll, '%'))
    signal ('22023', sprintf ('Admin collection %s must be outside the public blog collection %s.', admin_coll, coll));

  -- The admin route is defined only on a TLS listener, with sec=>'SSL' --
  -- never on plain HTTP.
  -- Host: admin_host (the host of the blog's own public URL -- pass it when
  -- deploying from a prompt that names the blog URL), else [URIQA]
  -- DefaultHost. Any :port suffix is dropped.
  uriqa_host := trim (coalesce (admin_host, ''));
  if (uriqa_host = '')
  {
    uriqa_host := cfg_item_value (virtuoso_ini_path (), 'URIQA', 'DefaultHost');
    if (not isstring (uriqa_host)) uriqa_host := '';
    uriqa_host := trim (uriqa_host);
  }
  if (strrchr (uriqa_host, ':') is not null) uriqa_host := subseq (uriqa_host, 0, strrchr (uriqa_host, ':'));
  -- TLS listener: admin_listener (e.g. ':443'), else the ini's
  -- [HTTPServer] SSLPort, else an existing ':443' listener. Instances whose
  -- TLS listener is defined in Conductor rather than in virtuoso.ini (UB)
  -- have no SSLPort, so the ini alone is not enough.
  ssl_port := trim (coalesce (admin_listener, ''));
  if (ssl_port = '')
  {
    ssl_port := cfg_item_value (virtuoso_ini_path (), 'HTTPServer', 'SSLPort');
    if (not isstring (ssl_port)) ssl_port := '';
    ssl_port := trim (ssl_port);
  }
  if (ssl_port = '' and (select count (*) from DB.DBA.HTTP_PATH where HP_LISTEN_HOST = ':443') > 0)
    ssl_port := '443';
  if (strrchr (ssl_port, ':') is not null) ssl_port := subseq (ssl_port, strrchr (ssl_port, ':') + 1);
  if (uriqa_host = '')
    signal ('42000', 'Cannot determine the admin route host: pass admin_host (the blog URL''s host) or set [URIQA] DefaultHost.');
  if (ssl_port = '')
    signal ('42000', 'Cannot find a TLS listener for the admin route: pass admin_listener (e.g. '':443''), set [HTTPServer] SSLPort, or define a :443 listener.');
  admin_lhost := concat (':', ssl_port);

  -- Action route: a SEPARATE VHOST pointing at the SAME collection, SAME
  -- def_page='index.vsp' file as the public route -- multiple VHOSTs can
  -- share one physical DAV resource, so this reuses the existing
  -- admin_action dispatcher code unchanged, just reached through a
  -- DIFFERENT URL with native HTTP Digest required in front of it (see
  -- DB.DBA.WEBLOG_ADMIN_AUTH_FN above). Verified live 2026-09-23: unlike
  -- the admin_route/dashboard.html case, gating index.vsp this way does NOT
  -- hit the "restrictive permissions break VSP execution" problem, because
  -- the gate is VHOST-level auth_fn, not a resource permission bit -- the
  -- underlying index.vsp resource keeps its normal, permissive permissions
  -- (it must stay world-executable for the public route to keep serving
  -- the blog) and executes completely normally once auth_fn allows the
  -- request through.
  action_route := concat (subseq (route, 0, length (route) - 1), '-action/');
  action_realm := concat ('WeblogAdmin:', coll);

  -- VAL (a full ACL/OAuth/session VAD package -- confirmed present on some
  -- but not all target instances) gets an optional, nicer login experience
  -- layered on TOP of the real auth_fn gate above, never instead of it:
  -- when detected, 401/403 responses on the action route redirect to VAL's
  -- own login dialog (/val/authenticate.vsp) instead of a bare browser
  -- Digest popup. auth_fn + sec=''digest'' remains the actual security
  -- boundary either way -- VAL''s own login page was found live 2026-09-23
  -- to not reliably complete an anonymous login flow on every instance, so
  -- it is never relied on as the sole gate.
  val_present := 0;
  {
    declare exit handler for sqlstate '*' { val_present := 0; };
    if ((select count (*) from DB.DBA.HTTP_PATH where HP_LPATH = '/val') > 0)
      val_present := 1;
  }
  if (val_present = 1)
    action_opts := vector ('browse_sheet', '', 'noinherit', 'yes', '401_page', '/val/authenticate.vsp', '403_page', '/val/authenticate.vsp');
  else
    action_opts := vector ('browse_sheet', '', 'noinherit', 'yes');

  index_content := '<?vsp
  -- Weblog-style index of {{DAV_COLLECTION}} -- multi-skin, config-driven.
  declare all_rows, pinned_posts, posts, html_stems, category_seen, category_keys, facet_key, facet_value any;
  declare n, idx, i, has_categories, filter_active, post_selected, all_count, ck, facet_count int;
  declare sel, q, ft_q, from_date, to_date, selected_category, category_cloud, facet_category, facet_active varchar;
  declare q_param, from_param, to_param, category_param, skin_param any;
  declare months any;
  declare feed_param any;
  declare feed_type, skin, newsletter_enabled, site_base varchar;

  months := vector (''January'',''February'',''March'',''April'',''May'',''June'',
                    ''July'',''August'',''September'',''October'',''November'',''December'');
  q := '''';
  ft_q := '''';
  from_date := '''';
  to_date := '''';
  selected_category := '''';
  feed_type := '''';
  q_param := http_param (''q'');
  from_param := http_param (''from'');
  to_param := http_param (''to'');
  category_param := http_param (''category'');
  feed_param := http_param (''feed'');
  skin_param := http_param (''skin'');
  if (not isstring (feed_param)) feed_param := http_param (''a'');
  if (isstring (q_param)) q := trim (q_param);
  if (isstring (from_param)) from_date := trim (from_param);
  if (isstring (to_param)) to_date := trim (to_param);
  if (isstring (category_param)) selected_category := trim (category_param);
  if (isstring (feed_param)) feed_type := lower (trim (feed_param));
  if (q <> '''') ft_q := concat (''"'', replace (q, ''"'', '' ''), ''"'');
  filter_active := 0;
  if (q <> '''' or from_date <> '''' or to_date <> '''' or selected_category <> '''') filter_active := 1;
  category_seen := dict_new (101);
  category_cloud := '''';
  has_categories := 0;
  all_count := 0;

  -- Skin resolution: ?skin= override, else weblog:skin collection property, else the deploy default.
  skin := '''';
  if (isstring (skin_param)) skin := lower (trim (skin_param));
  if (skin <> ''classic'' and skin <> ''editorial'')
    skin := lower (DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (''{{DAV_COLLECTION}}'', ''weblog:skin'', ''{{DEFAULT_SKIN}}''));
  if (skin <> ''classic'' and skin <> ''editorial'')
    skin := ''{{DEFAULT_SKIN}}'';

  -- Newsletter footer band: only rendered when explicitly enabled.
  newsletter_enabled := lower (DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (''{{DAV_COLLECTION}}'', ''weblog:newsletterEnabled'', ''false''));

  -- Best-effort absolute site base (scheme://host) for feed <link>/<guid>
  -- values and the WebDAV permalink. Falls back to the public route alone
  -- (relative) if request headers are unavailable.
  -- Confirmed live this was silently broken: http_request_header(req_lines,
  -- ''Host'', '''', '''') -- a 4-arg keyword-lookup call -- returns empty even
  -- though the Host header genuinely is present at req_lines[1] (verified
  -- with a standalone probe page); scanning the raw lines for a literal
  -- ''Host:'' prefix instead works. Scheme was also always hardcoded to
  -- ''http://'' regardless of the actual request -- is_https_ctx() (the
  -- same native builtin OAUTH2.DBA.check_https_ctx wraps) correctly
  -- reports 0/1 for a real HTTP vs HTTPS request, verified live both ways.
  site_base := '''';
  {
    declare exit handler for sqlstate ''*'' { site_base := ''''; };
    declare req_lines any;
    declare req_host, scheme varchar;
    declare li int;
    req_lines := http_request_header ();
    req_host := '''';
    for (li := 0; li < length (req_lines); li := li + 1)
    {
      declare line varchar;
      line := cast (aref (req_lines, li) as varchar);
      if (line like ''Host:%'')
        -- trim() only strips spaces, not the carriage-return/linefeed each
        -- raw header line ends with (confirmed live: the extracted host
        -- otherwise ends with a literal newline, breaking every URL built
        -- from site_base with a line break between host and path).
        req_host := trim (replace (replace (subseq (line, 5, length (line)), chr (13), ''''), chr (10), ''''));
    }
    scheme := case when is_https_ctx () then ''https://'' else ''http://'' end;
    if (req_host <> '''')
      site_base := concat (scheme, req_host);
  }

  -- Serve a sibling resource''s raw content via ?raw=<filename>. This has to
  -- be a query param, not the request PATH: this VHOST has def_page=index.vsp,
  -- and Virtuoso''s def_page dispatch overrides EVERY path under the route
  -- regardless of is_brws or whether the path names a real file (confirmed
  -- live: http_path() reports ".../<anything>/index.vsp" for every request,
  -- and a sibling VHOST without def_page 401s even world-readable files) --
  -- there is no way to reach an individual DAV resource by its own path
  -- under this route. Binary-safe: passes the BLOB straight to http(), no
  -- blob_to_string(). When the requested file is HTML, its own sibling
  -- asset references (a <video src="clip.mp4">, <img src="pic.jpg">, plain
  -- relative URLs a post author wrote with no knowledge of this routing
  -- constraint) are rewritten to go through this same ?raw= mechanism,
  -- since those requests would otherwise hit the same def_page catch-all.
  {
    declare raw_param any;
    declare raw_name, raw_ext, raw_ctype varchar;
    declare raw_content any;
    declare raw_found int;

    raw_param := http_param (''raw'');
    if (isstring (raw_param) and trim (raw_param) <> '''')
    {
      raw_name := trim (raw_param);
      raw_found := 0;
      raw_content := null;
      if (strchr (raw_name, ''/'') is null and raw_name not like ''._%'' and raw_name <> ''index.vsp'' and raw_name <> ''newsletter.vsp'')
      {
        for (select RES_CONTENT as _c from WS.WS.SYS_DAV_RES where RES_FULL_PATH = concat (''{{DAV_COLLECTION}}'', raw_name)) do
        {
          raw_found := 1;
          raw_content := _c;
        }
      }
      if (raw_found = 0)
      {
        http_header (''Status: 404 Not Found\r\nContent-Type: text/plain; charset=UTF-8\r\n'');
        http (''Not found.'');
        return;
      }
      raw_ext := lower (subseq (raw_name, strrchr (raw_name, ''.'') + 1));
      raw_ctype := case raw_ext
        when ''html'' then ''text/html; charset=UTF-8''
        when ''htm''  then ''text/html; charset=UTF-8''
        when ''md''   then ''text/plain; charset=UTF-8''
        when ''txt''  then ''text/plain; charset=UTF-8''
        when ''css''  then ''text/css''
        when ''js''   then ''application/javascript''
        when ''json'' then ''application/json''
        when ''mp4''  then ''video/mp4''
        when ''webm'' then ''video/webm''
        when ''mov''  then ''video/quicktime''
        when ''mp3''  then ''audio/mpeg''
        when ''wav''  then ''audio/wav''
        when ''jpg''  then ''image/jpeg''
        when ''jpeg'' then ''image/jpeg''
        when ''png''  then ''image/png''
        when ''gif''  then ''image/gif''
        when ''svg''  then ''image/svg+xml''
        when ''webp'' then ''image/webp''
        when ''pdf''  then ''application/pdf''
        else ''application/octet-stream''
      end;
      http_header (sprintf (''Content-Type: %s\r\n'', raw_ctype));
      if (raw_ext = ''html'' or raw_ext = ''htm'')
      {
        declare html_text varchar;
        declare sib_name varchar;
        html_text := blob_to_string (raw_content);
        for (select RES_NAME as _sib
               from WS.WS.SYS_DAV_RES
              where RES_FULL_PATH like ''{{DAV_COLLECTION}}%''
                and RES_NAME <> raw_name
                and RES_NAME <> ''index.vsp''
                and RES_NAME <> ''newsletter.vsp''
                and RES_NAME not like ''._%'') do
        {
          sib_name := _sib;
          html_text := replace (html_text, sprintf (''"%s"'', sib_name), sprintf (''"{{PUBLIC_ROUTE}}?raw=%s"'', sib_name));
        }
        http (html_text);
      }
      else
      {
        http (raw_content);
      }
      return;
    }
  }

  -- Admin actions (send digest now, change the digest interval), gated by
  -- REAL native HTTP Digest authentication -- checked at the ACTION ROUTE''s
  -- VHOST level (is_dav=1, def_page=index.vsp -- the SAME physical file as
  -- the public route, reached through a DIFFERENT, auth_fn-protected URL)
  -- via DB.DBA.WEBLOG_ADMIN_AUTH_FN, which verifies genuine SQL credentials
  -- against Virtuoso''s own credential store AND that the authenticated
  -- account matches this collection''s configured weblog:adminDavUser --
  -- see that procedure''s own comments for the full verification history.
  -- This REPLACES a previous design (a shared admin_action_token embedded
  -- in every dashboard form) that was found live to be readable by an
  -- anonymous request whenever the admin dashboard''s own DAV-permission
  -- gate failed to enforce -- which happened on a real remote instance.
  --
  -- Because the public route and the action route both execute this SAME
  -- index.vsp file, a request MUST be explicitly confirmed to have arrived
  -- via the action route''s URL before any admin_action is processed --
  -- otherwise the public route (which has no auth_fn at all, by design, so
  -- the blog itself stays anonymously readable) would let anyone reach this
  -- same code with no authentication challenge ever having been issued.
  {
    declare admin_action any;
    admin_action := http_param (''admin_action'');
    if (isstring (admin_action) and trim (admin_action) <> '''')
    {
      declare admin_result varchar;
      declare req_lines any;
      declare on_action_route int;
      admin_action := trim (admin_action);

      on_action_route := 0;
      {
        declare exit handler for sqlstate ''*'' { ; };
        req_lines := http_request_header ();
        if (length (req_lines) > 0 and strstr (cast (aref (req_lines, 0) as varchar), ''{{ACTION_ROUTE}}'') is not null)
          on_action_route := 1;
      }

      if (on_action_route = 0)
      {
        http_header (''Status: 403 Forbidden\r\nContent-Type: text/plain; charset=UTF-8\r\n'');
        http (''Forbidden: admin actions must be submitted via the action route, which requires real Digest authentication.'');
        return;
      }

      admin_result := ''Unknown admin action.'';
      {
        declare exit handler for sqlstate ''*''
        {
          admin_result := ''Something went wrong processing that action. Please try again in a moment.'';
        };
        if (admin_action = ''send_digest_now'')
        {
          if ((select count (*) from DB.DBA.SYS_PROCEDURES where P_NAME = ''DB.DBA.WEBLOG_NEWSLETTER_SEND_DIGEST'') > 0)
            admin_result := DB.DBA.WEBLOG_NEWSLETTER_SEND_DIGEST (''{{DAV_COLLECTION}}'');
          else
            admin_result := ''The newsletter feature is not installed yet.'';
        }
        else if (admin_action = ''set_digest_interval'')
        {
          declare minutes_param any;
          declare minutes_val int;
          minutes_param := http_param (''minutes'');
          minutes_val := 0;
          if (isstring (minutes_param)) minutes_val := atoi (trim (minutes_param));
          if (minutes_val < 1)
          {
            admin_result := ''Please provide a positive number of minutes.'';
          }
          else if ((select count (*) from DB.DBA.SYS_PROCEDURES where P_NAME = ''DB.DBA.WEBLOG_NEWSLETTER_SCHEDULE_DIGEST'') > 0)
          {
            admin_result := DB.DBA.WEBLOG_NEWSLETTER_SCHEDULE_DIGEST (sprintf (''weblog-newsletter-digest:%s'', ''{{DAV_COLLECTION}}''), ''{{DAV_COLLECTION}}'', minutes_val);
          }
          else
          {
            admin_result := ''The newsletter feature is not installed yet.'';
          }
        }
        else if (admin_action = ''set_digest_mode'')
        {
          declare mode_param varchar;
          declare deploy_pwd2 any;
          mode_param := http_param (''mode'');
          if (not isstring (mode_param)) mode_param := '''';
          mode_param := lower (trim (mode_param));
          if (mode_param <> ''digest'' and mode_param <> ''immediate'')
          {
            admin_result := ''Mode must be either "digest" or "immediate".'';
          }
          else
          {
            -- DAV_PROP_SET_INT, not DAV_PROP_SET as USER (whichever account
            -- this VSP executes as, the route''s vsp_user) -- the latter
            -- needs USER''s SQL password hash via pwd_magic_calc and
            -- silently writes nothing when that account''s SQL login is
            -- disabled or the hash otherwise fails to resolve (confirmed
            -- live on a real instance where vsp_user was SQL-disabled: every
            -- admin_action save appeared to succeed but changed nothing).
            deploy_pwd2 := DB.DBA.DAV_PROP_SET_INT (''{{DAV_COLLECTION}}'', ''weblog:newsletterMode'', mode_param, null, null, 0, 0, 1);
            if (not isinteger (deploy_pwd2) or deploy_pwd2 < 0)
              admin_result := sprintf (''Could not save the newsletter mode (DAV error %s).'', cast (deploy_pwd2 as varchar));
            else
              admin_result := sprintf (''Newsletter mode set to "%s".'', mode_param);
          }
        }
        else if (admin_action = ''set_content_mode'')
        {
          declare content_mode_param varchar;
          declare deploy_pwd3 any;
          content_mode_param := http_param (''content_mode'');
          if (not isstring (content_mode_param)) content_mode_param := '''';
          content_mode_param := lower (trim (content_mode_param));
          if (content_mode_param <> ''auto'' and content_mode_param <> ''snippet'' and content_mode_param <> ''full'')
          {
            admin_result := ''Content mode must be "auto", "snippet", or "full".'';
          }
          else
          {
            deploy_pwd3 := DB.DBA.DAV_PROP_SET_INT (''{{DAV_COLLECTION}}'', ''weblog:newsletterContentMode'', content_mode_param, null, null, 0, 0, 1);
            if (not isinteger (deploy_pwd3) or deploy_pwd3 < 0)
              admin_result := sprintf (''Could not save the email content mode (DAV error %s).'', cast (deploy_pwd3 as varchar));
            else
              admin_result := sprintf (''Email content mode set to "%s".'', content_mode_param);
          }
        }
        else if (admin_action = ''set_skin'')
        {
          declare skin_param varchar;
          declare deploy_pwd4 any;
          skin_param := http_param (''skin_choice'');
          if (not isstring (skin_param)) skin_param := '''';
          skin_param := lower (trim (skin_param));
          if (skin_param <> ''classic'' and skin_param <> ''editorial'')
          {
            admin_result := ''Skin must be either "classic" or "editorial".'';
          }
          else
          {
            deploy_pwd4 := DB.DBA.DAV_PROP_SET_INT (''{{DAV_COLLECTION}}'', ''weblog:skin'', skin_param, null, null, 0, 0, 1);
            if (not isinteger (deploy_pwd4) or deploy_pwd4 < 0)
              admin_result := sprintf (''Could not save the skin (DAV error %s).'', cast (deploy_pwd4 as varchar));
            else
              admin_result := sprintf (''Skin set to "%s".'', skin_param);
          }
        }
        else if (admin_action = ''set_email_config'')
        {
          declare fn_param, fa_param, smtp_param, base_param, admin_email_param varchar;
          declare deploy_pwd5 any;
          fn_param := http_param (''from_name'');
          fa_param := http_param (''from_address'');
          smtp_param := http_param (''smtp_server'');
          base_param := http_param (''confirm_base_url'');
          admin_email_param := http_param (''admin_email'');
          if (not isstring (fn_param)) fn_param := '''';
          if (not isstring (fa_param)) fa_param := '''';
          if (not isstring (smtp_param)) smtp_param := '''';
          if (not isstring (base_param)) base_param := '''';
          if (not isstring (admin_email_param)) admin_email_param := '''';
          fn_param := trim (fn_param);
          fa_param := trim (fa_param);
          smtp_param := trim (smtp_param);
          base_param := trim (base_param);
          admin_email_param := trim (admin_email_param);
          if (fn_param = '''' or fa_param = '''')
          {
            admin_result := ''From name and from address are required.'';
          }
          else if (admin_email_param <> '''' and (strchr (admin_email_param, ''@'') is null or strchr (admin_email_param, ''.'') is null))
          {
            admin_result := ''Admin email looks invalid -- leave it blank to clear it, or provide a valid address.'';
          }
          else
          {
            declare email_props any;
            declare email_pi int;
            declare email_fail varchar;
            email_fail := '''';
            email_props := vector (''weblog:newsletterFromName'', fn_param,
                                   ''weblog:newsletterFromAddress'', fa_param,
                                   ''weblog:newsletterSmtpServer'', smtp_param,
                                   ''weblog:newsletterConfirmBaseUrl'', base_param,
                                   ''weblog:adminEmail'', admin_email_param);
            for (email_pi := 0; email_pi < length (email_props); email_pi := email_pi + 2)
            {
              deploy_pwd5 := DB.DBA.DAV_PROP_SET_INT (''{{DAV_COLLECTION}}'', email_props[email_pi], email_props[email_pi + 1], null, null, 0, 0, 1);
              if (not isinteger (deploy_pwd5) or deploy_pwd5 < 0)
                email_fail := email_fail || sprintf (''%s (DAV error %s); '', email_props[email_pi], cast (deploy_pwd5 as varchar));
            }
            if (email_fail <> '''')
              admin_result := sprintf (''Could not save: %s'', email_fail);
            else
              admin_result := ''Email server configuration saved.'';
          }
        }
        else if (admin_action = ''set_digest_schedule'')
        {
          declare digest_enabled_param, minutes_param2 varchar;
          declare minutes_val2 int;
          digest_enabled_param := http_param (''digest_enabled'');
          minutes_param2 := http_param (''minutes'');
          if (not isstring (digest_enabled_param)) digest_enabled_param := ''1'';
          minutes_val2 := 0;
          if (isstring (minutes_param2)) minutes_val2 := atoi (trim (minutes_param2));
          if (digest_enabled_param = ''0'')
          {
            if ((select count (*) from DB.DBA.SYS_PROCEDURES where P_NAME = ''DB.DBA.WEBLOG_NEWSLETTER_UNSCHEDULE_DIGEST'') > 0)
            {
              DB.DBA.WEBLOG_NEWSLETTER_UNSCHEDULE_DIGEST (sprintf (''weblog-newsletter-digest:%s'', ''{{DAV_COLLECTION}}''));
              admin_result := ''Newsletter digest schedule turned off.'';
            }
            else
              admin_result := ''The newsletter feature is not installed yet.'';
          }
          else if (minutes_val2 < 1)
          {
            admin_result := ''Please provide a positive number of minutes.'';
          }
          else if ((select count (*) from DB.DBA.SYS_PROCEDURES where P_NAME = ''DB.DBA.WEBLOG_NEWSLETTER_SCHEDULE_DIGEST'') > 0)
          {
            DB.DBA.WEBLOG_NEWSLETTER_SCHEDULE_DIGEST (sprintf (''weblog-newsletter-digest:%s'', ''{{DAV_COLLECTION}}''), ''{{DAV_COLLECTION}}'', minutes_val2);
            admin_result := sprintf (''Newsletter digest schedule set to every %d minutes.'', minutes_val2);
          }
          else
          {
            admin_result := ''The newsletter feature is not installed yet.'';
          }
        }
        else if (admin_action = ''set_dashboard_schedule'')
        {
          declare dash_enabled_param, dash_minutes_param varchar;
          declare dash_minutes_val int;
          dash_enabled_param := http_param (''dash_enabled'');
          dash_minutes_param := http_param (''dash_minutes'');
          if (not isstring (dash_enabled_param)) dash_enabled_param := ''1'';
          dash_minutes_val := 0;
          if (isstring (dash_minutes_param)) dash_minutes_val := atoi (trim (dash_minutes_param));
          if (dash_enabled_param = ''0'')
          {
            if ((select count (*) from DB.DBA.SYS_PROCEDURES where P_NAME = ''DB.DBA.WEBLOG_DASHBOARD_UNSCHEDULE_REFRESH'') > 0)
            {
              DB.DBA.WEBLOG_DASHBOARD_UNSCHEDULE_REFRESH (sprintf (''weblog-dashboard-refresh:%s'', ''{{DAV_COLLECTION}}''));
              admin_result := ''Dashboard auto-refresh turned off.'';
            }
            else
              admin_result := ''The newsletter feature is not installed yet.'';
          }
          else if (dash_minutes_val < 1)
          {
            admin_result := ''Please provide a positive number of minutes.'';
          }
          else if ((select count (*) from DB.DBA.SYS_PROCEDURES where P_NAME = ''DB.DBA.WEBLOG_DASHBOARD_SCHEDULE_REFRESH'') > 0)
          {
            DB.DBA.WEBLOG_DASHBOARD_SCHEDULE_REFRESH (sprintf (''weblog-dashboard-refresh:%s'', ''{{DAV_COLLECTION}}''), ''{{DAV_COLLECTION}}'', dash_minutes_val);
            admin_result := sprintf (''Dashboard auto-refresh set to every %d minutes.'', dash_minutes_val);
          }
          else
          {
            admin_result := ''The newsletter feature is not installed yet.'';
          }
        }
        else if (admin_action = ''set_post_category'')
        {
          -- Dedicated, single-purpose: touches ONLY schema:category, never
          -- schema:position. A blank submission clears the tag -- this form
          -- has no other field competing for "blank means what?", unlike
          -- the earlier combined tag+pin form it replaces.
          declare post_name_param, category_param varchar;
          declare deploy_pwd6 any;
          post_name_param := http_param (''post_name'');
          category_param := http_param (''category'');
          if (not isstring (post_name_param)) post_name_param := '''';
          if (not isstring (category_param)) category_param := '''';
          post_name_param := trim (post_name_param);
          category_param := trim (category_param);
          if (post_name_param = '''')
          {
            admin_result := ''Please choose a post.'';
          }
          else if (post_name_param like ''._%'')
          {
            admin_result := ''Refusing to tag a macOS sidecar resource.'';
          }
          else
          {
            declare post_target varchar;
            post_target := ''{{DAV_COLLECTION}}'' || post_name_param;
            deploy_pwd6 := DB.DBA.DAV_PROP_SET_INT (post_target, ''schema:category'', category_param, null, null, 0, 0, 1);
            if (not isinteger (deploy_pwd6) or deploy_pwd6 < 0)
              admin_result := sprintf (''Could not update the category for "%s" (DAV error %s).'', post_name_param, cast (deploy_pwd6 as varchar));
            else
              admin_result := case when category_param = '''' then sprintf (''Category cleared for "%s".'', post_name_param) else sprintf (''"%s" tagged "%s".'', post_name_param, category_param) end;
          }
        }
        else if (admin_action = ''set_post_pin'')
        {
          -- Dedicated, single-purpose: touches ONLY schema:position, never
          -- schema:category -- a one-click Pin/Unpin button next to a post
          -- can never accidentally wipe that post''s tag as a side effect.
          declare pin_post_param, pin_value_param varchar;
          pin_post_param := http_param (''post_name'');
          pin_value_param := http_param (''pinned'');
          if (not isstring (pin_post_param)) pin_post_param := '''';
          if (not isstring (pin_value_param)) pin_value_param := ''1'';
          pin_post_param := trim (pin_post_param);
          pin_value_param := trim (pin_value_param);
          if (pin_post_param = '''')
          {
            admin_result := ''Please choose a post.'';
          }
          else if (pin_post_param like ''._%'')
          {
            admin_result := ''Refusing to pin a macOS sidecar resource.'';
          }
          else if ((select count (*) from DB.DBA.SYS_PROCEDURES where P_NAME = ''DB.DBA.WEBLOG_DAV_SET_PIN'') > 0)
          {
            DB.DBA.WEBLOG_DAV_SET_PIN (''{{DAV_COLLECTION}}'', pin_post_param, atoi (pin_value_param), USER);
            admin_result := sprintf (''"%s" %s.'', pin_post_param, case when pin_value_param = ''1'' then ''pinned'' else ''unpinned'' end);
          }
          else
          {
            admin_result := ''Pinning needs templates/register-weblog-pinning-tool.sql installed.'';
          }
        }
        else if (admin_action = ''admin_unsubscribe'')
        {
          -- Runs the exact same code path a subscriber''s own unsubscribe
          -- link runs (RDF-mirror retraction included) -- an admin-
          -- triggered manual unsubscribe, not a separate mechanism to keep
          -- in sync with that one.
          declare sub_token_param varchar;
          sub_token_param := http_param (''sub_token'');
          if (not isstring (sub_token_param)) sub_token_param := '''';
          sub_token_param := trim (sub_token_param);
          if (sub_token_param = '''')
          {
            admin_result := ''Missing subscriber token.'';
          }
          else if ((select count (*) from DB.DBA.SYS_PROCEDURES where P_NAME = ''DB.DBA.WEBLOG_NEWSLETTER_UNSUBSCRIBE'') > 0)
          {
            -- notify=1: the subscriber has no on-screen confirmation of
            -- this (the admin is the one looking at the dashboard), so
            -- send them a final email confirming they''ve been removed.
            admin_result := DB.DBA.WEBLOG_NEWSLETTER_UNSUBSCRIBE (sub_token_param, 1);
          }
          else
          {
            admin_result := ''The newsletter feature is not installed yet.'';
          }
        }
        else if (admin_action = ''import_subscribers_csv'')
        {
          declare import_file any;
          import_file := http_param (''importfile'');
          if (import_file is null)
            admin_result := ''Please choose a CSV file to upload.'';
          else if (not isstring (import_file))
            admin_result := sprintf (''Unexpected upload type (not a string): %s'', case when isarray (import_file) then ''ARRAY'' else ''OTHER'' end);
          else if (trim (import_file) = '''')
            admin_result := ''The uploaded CSV file appears to be empty.'';
          else if ((select count (*) from DB.DBA.SYS_PROCEDURES where P_NAME = ''DB.DBA.WEBLOG_NEWSLETTER_IMPORT_CSV'') > 0)
            admin_result := DB.DBA.WEBLOG_NEWSLETTER_IMPORT_CSV (''{{DAV_COLLECTION}}'', import_file);
          else
            admin_result := ''The newsletter feature is not installed yet.'';
        }
        else if (admin_action = ''import_subscribers_rdf'')
        {
          declare import_file any;
          declare rdf_format_param varchar;
          import_file := http_param (''importfile'');
          rdf_format_param := http_param (''rdf_format'');
          if (not isstring (rdf_format_param)) rdf_format_param := ''turtle'';
          if (import_file is null)
            admin_result := ''Please choose an RDF file to upload.'';
          else if (not isstring (import_file))
            admin_result := sprintf (''Unexpected upload type (not a string): %s'', case when isarray (import_file) then ''ARRAY'' else ''OTHER'' end);
          else if (trim (import_file) = '''')
            admin_result := ''The uploaded RDF file appears to be empty.'';
          else if ((select count (*) from DB.DBA.SYS_PROCEDURES where P_NAME = ''DB.DBA.WEBLOG_NEWSLETTER_IMPORT_RDF'') > 0)
            admin_result := DB.DBA.WEBLOG_NEWSLETTER_IMPORT_RDF (''{{DAV_COLLECTION}}'', import_file, rdf_format_param);
          else
            admin_result := ''The newsletter feature is not installed yet.'';
        }
        else if (admin_action = ''import_subscribers_manual'')
        {
          declare mi, total_rows, imported INTEGER;
          declare has_procs INTEGER;
          declare fail_list varchar;
          has_procs := (select count (*) from DB.DBA.SYS_PROCEDURES where P_NAME = ''DB.DBA.WEBLOG_NEWSLETTER_IMPORT_ONE'');
          total_rows := 0;
          imported := 0;
          fail_list := '''';
          if (has_procs > 0)
          {
            for (mi := 1; mi <= 5; mi := mi + 1)
            {
              declare nm, em varchar;
              nm := http_param (sprintf (''name%d'', mi));
              em := http_param (sprintf (''email%d'', mi));
              if (not isstring (nm)) nm := '''';
              if (not isstring (em)) em := '''';
              -- Lowercased, not just trimmed -- WEBLOG_SUBSCRIBER_UQ''s
              -- unique index compares the literal string, so this keeps
              -- "John@x.com" and "john@x.com" from being treated as
              -- different addresses; every other write path (subscribe,
              -- CSV/RDF import) canonicalizes the same way.
              em := lower (trim (em));
              if (em <> '''')
              {
                total_rows := total_rows + 1;
                if (strchr (em, ''@'') is null or strchr (em, ''.'') is null)
                  fail_list := fail_list || sprintf (''%s (invalid address); '', em);
                else
                {
                  declare dup_status varchar;
                  dup_status := null;
                  for (select WS_STATUS as _s from DB.DBA.WEBLOG_SUBSCRIBER
                        where WS_DAV_COLLECTION = ''{{DAV_COLLECTION}}'' and WS_EMAIL = em) do
                    dup_status := _s;
                  if (dup_status = ''confirmed'')
                    fail_list := fail_list || sprintf (''%s (already a confirmed subscriber); '', em);
                  else if (DB.DBA.WEBLOG_NEWSLETTER_IMPORT_ONE (''{{DAV_COLLECTION}}'', em, null, trim (nm)) = 1)
                    imported := imported + 1;
                  else
                    fail_list := fail_list || sprintf (''%s (could not be added); '', em);
                }
              }
            }
          }
          if (has_procs = 0)
            admin_result := ''The newsletter feature is not installed yet.'';
          else if (total_rows = 0)
            admin_result := ''Please fill in at least one email address.'';
          else if (fail_list <> '''' and imported = 0)
            admin_result := sprintf (''Manual entry failed for: %s'', fail_list);
          else if (fail_list <> '''')
            admin_result := sprintf (''Manual entry: %d row(s) processed, %d added. Failed for: %s'', total_rows, imported, fail_list);
          else
            admin_result := sprintf (''Manual entry: %d row(s) processed, %d added.'', total_rows, imported);
        }
      }

      -- Regenerate the dashboard snapshot BEFORE sending the admin back to
      -- it, so the page they land on already reflects this action (the
      -- earlier stale-cache confusion this session -- "still shows
      -- pending" right after confirming -- was exactly this gap). Then
      -- return to the dashboard itself with the result in the query
      -- string, instead of a separate "here''s what happened, click Back"
      -- page: a custom Status: header does not reliably change the actual
      -- wire-level response code on this VHOST route (confirmed live
      -- 2026-09-23 -- a 403 case still came back as a literal 200 OK), so
      -- a real Location-header redirect can''t be relied on either; a
      -- meta-refresh plus an immediate JS location.replace() both act at
      -- the HTML/DOM level and don''t depend on that, so either one alone
      -- is enough, and together they''re a reliable fallback pair. The
      -- dashboard''s own page-load script (WEBLOG_DASHBOARD_REFRESH) reads
      -- admin_msg from the query string and shows it as a dismissible
      -- banner, then strips it from the URL.
      {
        declare exit handler for sqlstate ''*'' { ; };
        if ((select count (*) from DB.DBA.SYS_PROCEDURES where P_NAME = ''DB.DBA.WEBLOG_DASHBOARD_REFRESH'') > 0)
          DB.DBA.WEBLOG_DASHBOARD_REFRESH (''{{DAV_COLLECTION}}'');
      }
      -- Encode the message exactly once via the same %U conversion already
      -- trusted everywhere else in this file for building links, then
      -- reuse that one value verbatim in all three destinations below --
      -- it contains only URL-safe characters, so embedding it inside a JS
      -- string literal needs no separate JS-escaping step (and doing that
      -- escaping ad hoc, e.g. with encodeURIComponent() around the RAW
      -- unencoded message, would have been unsafe: an admin_result
      -- containing a literal double-quote -- plausible, filenames and
      -- category text both flow into it -- breaks out of the JS string).
      {
        declare admin_msg_enc varchar;
        admin_msg_enc := sprintf (''%U'', admin_result);
        http_header (''Content-Type: text/html; charset=UTF-8\r\n'');
        http (sprintf (''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/><meta http-equiv="refresh" content="0;url={{ADMIN_ROUTE}}?admin_msg=%s"/><title>Admin Action</title></head><body><script>location.replace("{{ADMIN_ROUTE}}?admin_msg=%s");</script><noscript><a href="{{ADMIN_ROUTE}}?admin_msg=%s">Continue to the dashboard</a></noscript></body></html>'',
          admin_msg_enc, admin_msg_enc, admin_msg_enc));
      }
      return;
    }
  }

  -- Newsletter subscribe/confirm/unsubscribe dispatch. This has to live in
  -- index.vsp itself (a dedicated newsletter.vsp file does NOT work: the
  -- VSP-only VHOST route redirects any nested path -- including a POST to
  -- newsletter.vsp -- by appending a trailing slash, which turns the POST
  -- into a GET and loses the form body; the query-param approach below
  -- avoids that entirely). Works whether or not register-weblog-newsletter.sql
  -- has been installed yet -- it reports a clear message instead of a raw
  -- VSP fault if the newsletter procedures are missing.
  {
    declare nl_action, nl_email, nl_country, nl_token, nl_result, nl_site_base varchar;
    declare nl_has_procs, nl_is_post, nl_needs_confirm_post int;
    declare nl_confirm_label varchar;
    nl_action := http_param (''nl_action'');
    if (not isstring (nl_action)) nl_action := '''';
    nl_action := lower (trim (nl_action));
    if (nl_action <> '''')
    {
      -- RFC 8058 / basic CSRF hygiene: ''confirm'' and ''unsubscribe'' change
      -- state from a link an unauthenticated party controls (it''s in an
      -- email). Mail-security gateways routinely PREFETCH every link in a
      -- message with a plain GET to scan for phishing -- if a GET here
      -- executed the action, that prefetch silently confirms/unsubscribes
      -- the real subscriber before they ever open the email (confirmed live
      -- 2026-09-23: a List-Unsubscribe header addition caused exactly this).
      -- A GET must only ever render a confirmation page with a same-URL POST
      -- form; only an actual POST (a human''s click-through, or a mail
      -- client''s List-Unsubscribe-Post one-click) performs the change.
      nl_is_post := 0;
      {
        declare exit handler for sqlstate ''*'' { ; };
        declare req_lines any;
        req_lines := http_request_header ();
        if (length (req_lines) > 0 and cast (aref (req_lines, 0) as varchar) like ''POST %'')
          nl_is_post := 1;
      }
      nl_email := http_param (''email'');
      nl_country := http_param (''country'');
      nl_token := http_param (''token'');
      nl_result := ''Unknown or missing action.'';
      nl_needs_confirm_post := 0;
      nl_confirm_label := '''';
      nl_has_procs := 0;
      {
        declare exit handler for sqlstate ''*'' { nl_has_procs := 0; };
        if ((select count (*) from DB.DBA.SYS_PROCEDURES where P_NAME = ''DB.DBA.WEBLOG_NEWSLETTER_SUBSCRIBE'') > 0)
          nl_has_procs := 1;
      }
      if (nl_has_procs = 0)
      {
        nl_result := ''The newsletter feature is not installed on this server yet -- ask the site operator to run templates/register-weblog-newsletter.sql.'';
      }
      else if ((nl_action = ''confirm'' or nl_action = ''unsubscribe'') and nl_is_post = 0 and isstring (nl_token) and trim (nl_token) <> '''')
      {
        nl_needs_confirm_post := 1;
        nl_confirm_label := case when nl_action = ''confirm'' then ''confirm your subscription'' else ''unsubscribe from this newsletter'' end;
      }
      else
      {
        -- Defense in depth for a public, unauthenticated form endpoint: an
        -- unexpected failure in any of these procedures must still render
        -- the friendly result page below, never a raw SQL error page.
        declare exit handler for sqlstate ''*''
        {
          nl_result := ''Something went wrong processing that request. Please try again in a moment.'';
        };
        if (nl_action = ''subscribe'')
        {
          nl_site_base := site_base;
          if (isstring (nl_email) and trim (nl_email) <> '''')
            nl_result := DB.DBA.WEBLOG_NEWSLETTER_SUBSCRIBE (''{{DAV_COLLECTION}}'', trim (nl_email), nl_country, nl_site_base);
          else
            nl_result := ''Please provide a valid email address.'';
        }
        else if (nl_action = ''confirm'' and isstring (nl_token) and trim (nl_token) <> '''')
        {
          nl_result := DB.DBA.WEBLOG_NEWSLETTER_CONFIRM (trim (nl_token));
        }
        else if (nl_action = ''unsubscribe'' and isstring (nl_token) and trim (nl_token) <> '''')
        {
          nl_result := DB.DBA.WEBLOG_NEWSLETTER_UNSUBSCRIBE (trim (nl_token));
        }
      }
      http_header (''Content-Type: text/html; charset=UTF-8\r\n'');
      if (nl_needs_confirm_post = 1)
      {
        http (sprintf (''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><title>%V Newsletter</title><style>body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:#f5f8fb;color:#172838;}main{max-width:30rem;margin:2rem;padding:2rem 2.25rem;border:1px solid #d5e3ec;border-radius:8px;background:#fff;box-shadow:0 14px 34px rgba(7,19,29,0.10);text-align:center;}h1{font-size:1.3rem;margin:0 0 1rem;}p{line-height:1.55;}button{font:inherit;font-size:.92rem;font-weight:600;padding:.6rem 1.3rem;border-radius:6px;border:1px solid #1599d3;cursor:pointer;background:#1599d3;color:#fff;}a{color:#1599d3;}</style></head><body><main><h1>%V Newsletter</h1><p>Click below to %V.</p><form method="post" action="{{PUBLIC_ROUTE}}"><input type="hidden" name="nl_action" value="%V"/><input type="hidden" name="token" value="%V"/><button type="submit">Confirm</button></form><p><a href="{{PUBLIC_ROUTE}}">&larr; Back to the weblog</a></p></main></body></html>'',
          ''{{WEBLOG_TITLE}}'', ''{{WEBLOG_TITLE}}'', nl_confirm_label, nl_action, trim (nl_token)));
      }
      else
      {
        http (sprintf (''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><title>%V Newsletter</title><style>body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:#f5f8fb;color:#172838;}main{max-width:30rem;margin:2rem;padding:2rem 2.25rem;border:1px solid #d5e3ec;border-radius:8px;background:#fff;box-shadow:0 14px 34px rgba(7,19,29,0.10);text-align:center;}h1{font-size:1.3rem;margin:0 0 1rem;}p{line-height:1.55;}a{color:#1599d3;}</style></head><body><main><h1>%V Newsletter</h1><p>%V</p><p><a href="{{PUBLIC_ROUTE}}">&larr; Back to the weblog</a></p></main></body></html>'', ''{{WEBLOG_TITLE}}'', ''{{WEBLOG_TITLE}}'', nl_result));
      }
      return;
    }
  }

  -- Pass 1: collect .html and .md resources; note stems that have an HTML rendition
  all_rows := vector ();
  html_stems := dict_new (61);
  if (q = '''')
  {
    for (select RES_NAME as _name, RES_MOD_TIME as _mod, RES_CONTENT as _cont
           from WS.WS.SYS_DAV_RES
          where (RES_FULL_PATH like ''{{DAV_COLLECTION}}%.html''
              or RES_FULL_PATH like ''{{DAV_COLLECTION}}%.md'')
            and RES_NAME not like ''._%''
            and RES_NAME not in (''index.vsp'', ''newsletter.vsp'')
          order by RES_MOD_TIME desc, RES_NAME desc) do
    {
    declare s, ext, stem varchar;
    declare dpos int;
    dpos := strrchr (_name, ''.'');
    stem := subseq (_name, 0, dpos);
    ext  := lower (subseq (_name, dpos + 1));
    if (ext = ''html'')
      dict_put (html_stems, stem, 1);
    s := subseq (blob_to_string (_cont), 0, 8000);
    all_rows := vector_concat (all_rows, vector (vector (_name, _mod, s, ext, stem)));
    }
  }
  else
  {
    for (select RES_NAME as _name, RES_MOD_TIME as _mod, RES_CONTENT as _cont
           from WS.WS.SYS_DAV_RES
          where (RES_FULL_PATH like ''{{DAV_COLLECTION}}%.html''
              or RES_FULL_PATH like ''{{DAV_COLLECTION}}%.md'')
            and RES_NAME not like ''._%''
            and RES_NAME not in (''index.vsp'', ''newsletter.vsp'')
            and contains (RES_CONTENT, ft_q)
          order by RES_MOD_TIME desc, RES_NAME desc) do
    {
    declare s, ext, stem varchar;
    declare dpos int;
    dpos := strrchr (_name, ''.'');
    stem := subseq (_name, 0, dpos);
    ext  := lower (subseq (_name, dpos + 1));
    if (ext = ''html'')
      dict_put (html_stems, stem, 1);
    s := subseq (blob_to_string (_cont), 0, 8000);
    all_rows := vector_concat (all_rows, vector (vector (_name, _mod, s, ext, stem)));
    }
  }

  -- Pass 2: keep every .html; keep a .md only when no .html counterpart shares its stem
  pinned_posts := vector ();
  posts := vector ();
  for (i := 0; i < length (all_rows); i := i + 1)
  {
    declare r any;
    declare s, t, ext, stem, dav_path, category_val, item_date varchar;
    declare raw_category, raw_pin any;
    declare category_match, semi_pos, cat_count, pin_val int;
    declare one_category, rest_category varchar;
    r    := aref (all_rows, i);
    s    := aref (r, 2);
    ext  := aref (r, 3);
    stem := aref (r, 4);
    if (ext = ''md'' and dict_get (html_stems, stem, null) is not null)
      goto next_row;
    if (ext = ''html'')
    {
      t := regexp_match (''<title>[^<]+</title>'', s);
      if (t is not null)
      {
        t := replace (t, ''<title>'', '''');
        t := replace (t, ''</title>'', '''');
        t := trim (t);
        t := DB.DBA.WEBLOG_HTML_UNESCAPE (t);
        t := DB.DBA.WEBLOG_FIX_MOJIBAKE (t);
      }
    }
    else
    {
      t := stem;
    }
    if (t is null or t = '''')
      t := aref (r, 0);
    item_date := sprintf (''%04d-%02d-%02d'', year (aref (r, 1)), month (aref (r, 1)), dayofmonth (aref (r, 1)));
    if (from_date <> '''' and item_date < from_date)
      goto next_row;
    if (to_date <> '''' and item_date > to_date)
      goto next_row;
    dav_path := sprintf (''{{DAV_COLLECTION}}%s'', aref (r, 0));
    raw_pin := null;
    for (select P.PROP_VALUE as _pin
           from WS.WS.SYS_DAV_RES R, WS.WS.SYS_DAV_PROP P
          where R.RES_FULL_PATH = dav_path
            and P.PROP_PARENT_ID = R.RES_ID
            and P.PROP_TYPE = ''R''
            and P.PROP_NAME = ''schema:position'') do
    {
      raw_pin := _pin;
    }
    pin_val := 0;
    if (raw_pin is not null and isstring (raw_pin) and trim (cast (raw_pin as varchar)) <> '''' and trim (cast (raw_pin as varchar)) <> ''0'')
      pin_val := 1;
    raw_category := null;
    for (select P.PROP_VALUE as _cat
           from WS.WS.SYS_DAV_RES R, WS.WS.SYS_DAV_PROP P
          where R.RES_FULL_PATH = dav_path
            and P.PROP_PARENT_ID = R.RES_ID
            and P.PROP_TYPE = ''R''
            and P.PROP_NAME = ''schema:category'') do
    {
      raw_category := _cat;
    }
    category_val := '''';
    if (raw_category is not null and isstring (raw_category))
      category_val := trim (cast (raw_category as varchar));
    category_match := 0;
    if (selected_category = '''')
      category_match := 1;
    if (category_val <> '''')
    {
      rest_category := category_val;
      while (rest_category <> '''')
      {
        semi_pos := strchr (rest_category, '';'');
        if (semi_pos is null)
        {
          one_category := trim (rest_category);
          rest_category := '''';
        }
        else
        {
          one_category := trim (subseq (rest_category, 0, semi_pos));
          rest_category := trim (subseq (rest_category, semi_pos + 1));
        }
        if (one_category <> '''' and length (one_category) > 2)
        {
          has_categories := 1;
          if (one_category = selected_category)
            category_match := 1;
          cat_count := cast (dict_get (category_seen, one_category, 0) as int) + 1;
          dict_put (category_seen, one_category, cat_count);
        }
      }
    }
    all_count := all_count + 1;
    if (selected_category <> '''' and category_match = 0)
      goto next_row;
    if (pin_val)
      pinned_posts := vector_concat (pinned_posts, vector (vector (aref (r, 0), aref (r, 1), t, ext, category_val, item_date, pin_val)));
    else
      posts := vector_concat (posts, vector (vector (aref (r, 0), aref (r, 1), t, ext, category_val, item_date, pin_val)));
next_row: ;
  }
  posts := vector_concat (pinned_posts, posts);

  if (has_categories)
  {
    dict_iter_rewind (category_seen);
    while (dict_iter_next (category_seen, facet_key, facet_value))
    {
      facet_category := cast (facet_key as varchar);
      facet_count := cast (facet_value as int);
      facet_active := '''';
      if (facet_category = selected_category)
        facet_active := '' is-active'';
      category_cloud := concat (category_cloud, sprintf (''<a class="facet-option%V" href="{{PUBLIC_ROUTE}}?category=%U&amp;q=%U&amp;from=%U&amp;to=%U"><span class="facet-name">%V</span><span class="facet-count">%d</span></a>'', facet_active, facet_category, q, from_date, to_date, DB.DBA.WEBLOG_UTF8_DECODE (facet_category), facet_count));
    }
  }

  n := length (posts);
  idx := 0;
  post_selected := 0;
  sel := http_param (''post'');
  if (isstring (sel))
  {
    for (i := 0; i < n; i := i + 1)
    {
      if (aref (aref (posts, i), 0) = sel)
      {
        idx := i;
        post_selected := 1;
      }
    }
  }

  if (feed_type = ''rss'')
  {
    http_header (''Content-Type: application/rss+xml; charset=UTF-8
'');
    http (''<?xml version="1.0" encoding="UTF-8"?>
'');
    http (''<rss version="2.0"><channel>
'');
    http (sprintf (''<title>%V</title>
'', ''{{WEBLOG_TITLE}}''));
    http (sprintf (''<link>%s{{PUBLIC_ROUTE}}</link>
'', site_base));
    http (''<description>{{WEBLOG_TAGLINE}}</description>
'');
    http (''<generator>Virtuoso Server Pages over WebDAV</generator>
'');
    for (i := 0; i < n; i := i + 1)
    {
      declare fname, ftitle varchar;
      fname := aref (aref (posts, i), 0);
      ftitle := aref (aref (posts, i), 2);
      http (''<item>
'');
      http (sprintf (''<title>%V</title>
'', DB.DBA.WEBLOG_UTF8_DECODE (ftitle)));
      http (sprintf (''<link>%s{{PUBLIC_ROUTE}}?post=%U</link>
'', site_base, fname));
      http (sprintf (''<guid isPermaLink="true">%s{{PUBLIC_ROUTE}}?post=%U</guid>
'', site_base, fname));
      http (sprintf (''<description>%V</description>
'', DB.DBA.WEBLOG_UTF8_DECODE (ftitle)));
      http (''</item>
'');
    }
    http (''</channel></rss>
'');
    return;
  }
  if (feed_type = ''atom'')
  {
    http_header (''Content-Type: application/atom+xml; charset=UTF-8
'');
    http (''<?xml version="1.0" encoding="UTF-8"?>
'');
    http (''<feed xmlns="http://www.w3.org/2005/Atom">
'');
    http (sprintf (''<title>%V</title>
'', ''{{WEBLOG_TITLE}}''));
    http (sprintf (''<id>%s{{PUBLIC_ROUTE}}</id>
'', site_base));
    http (sprintf (''<link href="%s{{PUBLIC_ROUTE}}"/>
'', site_base));
    http (sprintf (''<link rel="self" type="application/atom+xml" href="%s{{PUBLIC_ROUTE}}?feed=atom"/>
'', site_base));
    if (n > 0)
    {
      declare umod datetime;
      umod := aref (aref (posts, 0), 1);
      http (sprintf (''<updated>%04d-%02d-%02dT00:00:00Z</updated>
'', year (umod), month (umod), dayofmonth (umod)));
    }
    else
      http (''<updated>2026-01-01T00:00:00Z</updated>
'');
    for (i := 0; i < n; i := i + 1)
    {
      declare fname, ftitle varchar;
      declare fmod datetime;
      fname := aref (aref (posts, i), 0);
      fmod := aref (aref (posts, i), 1);
      ftitle := aref (aref (posts, i), 2);
      http (''<entry>
'');
      http (sprintf (''<title>%V</title>
'', DB.DBA.WEBLOG_UTF8_DECODE (ftitle)));
      http (sprintf (''<id>%s{{PUBLIC_ROUTE}}?post=%U</id>
'', site_base, fname));
      http (sprintf (''<link href="%s{{PUBLIC_ROUTE}}?post=%U"/>
'', site_base, fname));
      http (sprintf (''<updated>%04d-%02d-%02dT00:00:00Z</updated>
'', year (fmod), month (fmod), dayofmonth (fmod)));
      http (sprintf (''<summary>%V</summary>
'', DB.DBA.WEBLOG_UTF8_DECODE (ftitle)));
      http (''</entry>
'');
    }
    http (''</feed>
'');
    return;
  }
  if (feed_type = ''atompub'' or feed_type = ''atomPub'')
  {
    http_header (''Content-Type: application/atomsvc+xml; charset=UTF-8
'');
    http (''<?xml version="1.0" encoding="UTF-8"?>
'');
    http (sprintf (''<service xmlns="http://www.w3.org/2007/app" xmlns:atom="http://www.w3.org/2005/Atom"><workspace><atom:title>%V</atom:title><collection href="%s{{PUBLIC_ROUTE}}"><atom:title>WebDAV Folder</atom:title></collection></workspace></service>
'', ''{{WEBLOG_TITLE}}'', site_base));
    return;
  }
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title><?= ''{{WEBLOG_TITLE}}'' ?></title>
  <meta name="description" content="{{WEBLOG_TAGLINE}}" />
  <link rel="alternate" type="application/rss+xml"  title="<?= ''{{WEBLOG_TITLE}}'' ?> (RSS 2.0)"  href="{{PUBLIC_ROUTE}}?feed=rss" />
  <link rel="alternate" type="application/atom+xml" title="<?= ''{{WEBLOG_TITLE}}'' ?> (Atom 1.0)" href="{{PUBLIC_ROUTE}}?feed=atom" />
  <link rel="service"   type="application/atomsvc+xml" title="AtomPub Service" href="{{PUBLIC_ROUTE}}?feed=atomPub" />
  <style>
    /* Shared, skin-agnostic base -- reset, theme-toggle chrome, feed buttons, newsletter band, footer. */
    * { box-sizing: border-box; }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .feed-buttons { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
    .theme-toggle {
      display: inline-flex; align-items: center; justify-content: center;
      width: 2rem; height: 2rem; border: 1px solid var(--border); border-radius: 4px;
      background: var(--accent-soft); color: var(--text); cursor: pointer;
    }
    .theme-toggle:hover { background: var(--accent-quiet); }
    .theme-toggle svg { width: 14px; height: 14px; fill: none; stroke: currentColor; stroke-width: 2; }
    .theme-toggle .sun { display: none; }
    html[data-theme="light"] .theme-toggle .moon { display: none; }
    html[data-theme="light"] .theme-toggle .sun { display: block; }
    .feed-btn {
      display: inline-flex; align-items: center; justify-content: center; gap: 0.35rem;
      min-height: 2rem; font-size: 0.78rem; font-weight: 700;
      padding: 0.38rem 0.72rem; border-radius: 4px;
      color: #fff !important; text-decoration: none !important; white-space: nowrap;
    }
    .feed-btn.rss  { background: var(--rss); }
    .feed-btn.atom { background: var(--accent); }
    .feed-btn.subscribe { background: var(--subscribe); }
    button.feed-btn { border: 0; font: inherit; cursor: pointer; }
    .feed-btn svg { width: 12px; height: 12px; fill: currentColor; flex: 0 0 auto; }
    .post-frame { display: block; width: 100%; height: calc(100vh - 7.5rem); min-height: 420px; border: 0; background: #fff; }
    .a-category { display: none; }
    .newsletter-band {
      max-width: 1380px; margin: 2rem auto 0; padding: 1.75rem 1.5rem;
      border: 1px solid var(--border); border-radius: 8px; background: var(--panel);
      text-align: center; box-shadow: var(--shadow);
    }
    dialog.newsletter-band {
      max-width: 26rem; width: calc(100% - 2.5rem); margin: auto; padding: 2rem 1.5rem 1.5rem;
      border-radius: 12px; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.28); color: var(--text);
      position: relative;
    }
    dialog.newsletter-band::backdrop { background: rgba(10, 14, 20, 0.55); }
    .nl-close {
      position: absolute; top: 0.5rem; right: 0.6rem; width: 2rem; height: 2rem;
      border: 0; border-radius: 50%; background: transparent; color: var(--muted);
      font-size: 1.3rem; line-height: 1; cursor: pointer;
    }
    .nl-close:hover { color: var(--text); background: var(--accent-soft); }
    .newsletter-band h2 { margin: 0 0 0.4rem; font-size: 1.35rem; }
    .newsletter-band p.nl-sub { margin: 0 0 1.1rem; color: var(--muted); }
    .nl-form { display: flex; flex-wrap: wrap; gap: 0.6rem; justify-content: center; align-items: flex-end; }
    .nl-field { display: grid; gap: 0.25rem; text-align: left; }
    .nl-field label { font-size: 0.78rem; color: var(--muted); }
    .nl-field input {
      min-height: 2.3rem; min-width: 15rem; border: 1px solid var(--border); border-radius: 4px;
      padding: 0.45rem 0.6rem; font: inherit; font-size: 0.9rem; background: #fff; color: #172838;
    }
    .nl-field.nl-country input { min-width: 9rem; }
    .nl-submit {
      min-height: 2.3rem; padding: 0.45rem 1.1rem; border: 0; border-radius: 4px;
      background: var(--accent); color: #fff; font-weight: 700; cursor: pointer;
    }
    .nl-consent { margin: 0.85rem auto 0; max-width: 34rem; font-size: 0.72rem; color: var(--muted); }
    footer.colophon { max-width: 1380px; margin: 0 auto 1.75rem; padding: 0 1.25rem; color: var(--muted); font-size: 0.8rem; }
    .footer-inner { border-top: 1px solid var(--border); padding-top: 1rem; display: flex; flex-wrap: wrap; gap: 0.6rem 1rem; justify-content: space-between; align-items: center; }
    .footer-copy { display: grid; gap: 0.28rem; max-width: 880px; line-height: 1.45; }
    .footer-primary { color: var(--text); font-weight: 650; }
    .footer-provenance { color: var(--muted); }
    .footer-links { display: flex; flex-wrap: wrap; gap: 0.45rem 0.75rem; align-items: center; }
    .footer-links a { font-weight: 650; }
    .virtuoso-badge {
      display: inline-flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.06rem;
      padding: 0.55rem 1.35rem; border: 2px solid var(--accent); border-radius: 50%;
      background: var(--panel); box-shadow: 0 4px 14px rgba(0,0,0,0.14); text-decoration: none !important;
      line-height: 1.05; white-space: nowrap;
    }
    .virtuoso-badge:hover { transform: translateY(-1px); text-decoration: none; }
    .virtuoso-badge .vb-powered { font-size: 0.56rem; font-weight: 650; letter-spacing: 0.14em; text-transform: lowercase; color: var(--muted); }
    .virtuoso-badge .vb-name { font-size: 0.95rem; font-weight: 850; letter-spacing: 0.02em; color: var(--accent); }
  </style>
<?vsp if (skin = ''editorial'') { ?>
  <style>
    /* editorial skin -- single-column magazine layout, serif headlines. */
    :root {
      --accent: #1f4e79; --accent-soft: rgba(31, 78, 121, 0.10); --accent-quiet: rgba(31, 78, 121, 0.22);
      --paper: #faf7f2; --ink: #1c1c1a; --panel: #ffffff; --text: #1c1c1a; --muted: #6b6b64;
      --border: #e7e1d6; --rss: #f26522; --subscribe: #2e7d32; --shadow: 0 10px 28px rgba(28, 28, 26, 0.07);
      --headline: Charter, "Iowan Old Style", "Palatino Linotype", Georgia, "Times New Roman", serif;
      --body-font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    @media (prefers-color-scheme: dark) {
      :root:not([data-theme="light"]) {
        --accent: #00b4ff; --accent-soft: rgba(0, 180, 255, 0.12); --accent-quiet: rgba(0, 180, 255, 0.28);
        --paper: #0f1720; --ink: #f1f5f9; --panel: #16212c; --text: #f1f5f9; --muted: #92a3b3;
        --border: rgba(0, 180, 255, 0.20); --shadow: 0 14px 34px rgba(0, 0, 0, 0.4);
      }
    }
    html[data-theme="dark"] {
      --accent: #00b4ff; --accent-soft: rgba(0, 180, 255, 0.12); --accent-quiet: rgba(0, 180, 255, 0.28);
      --paper: #0f1720; --ink: #f1f5f9; --panel: #16212c; --text: #f1f5f9; --muted: #92a3b3;
      --border: rgba(0, 180, 255, 0.20); --shadow: 0 14px 34px rgba(0, 0, 0, 0.4);
    }
    html[data-theme="light"] {
      --accent: #1f4e79; --accent-soft: rgba(31, 78, 121, 0.10); --accent-quiet: rgba(31, 78, 121, 0.22);
      --paper: #faf7f2; --ink: #1c1c1a; --panel: #ffffff; --text: #1c1c1a; --muted: #6b6b64;
      --border: #e7e1d6; --shadow: 0 10px 28px rgba(28, 28, 26, 0.07);
    }
    body { margin: 0; font-family: var(--body-font); background: var(--paper); color: var(--text); line-height: 1.55; }
    header.masthead {
      position: sticky; top: 0; z-index: 20; background: var(--paper);
      border-bottom: 1px solid var(--border); padding: 0.9rem max(1.25rem, calc((100vw - 1080px) / 2));
      display: flex; flex-wrap: wrap; align-items: center; gap: 0.6rem 1rem;
    }
    header.masthead h1 { margin: 0; font-family: var(--headline); font-size: 1.3rem; font-weight: 700; }
    header.masthead h1 a { color: var(--ink); }
    .util-row {
      max-width: 1080px; margin: 0 auto; padding: 0.9rem 1.25rem 0; display: flex; flex-wrap: wrap;
      gap: 0.6rem 0.85rem; align-items: center;
    }
    .util-row form { display: flex; gap: 0.5rem; flex: 1 1 260px; }
    .util-row input[type="search"], .util-row input[type="date"] {
      min-height: 2.15rem; border: 1px solid var(--border); border-radius: 999px; padding: 0.4rem 0.9rem;
      font: inherit; font-size: 0.86rem; background: var(--panel); color: var(--text); flex: 1 1 auto;
    }
    .chip-row { display: flex; flex-wrap: wrap; gap: 0.4rem; }
    .chip {
      display: inline-flex; align-items: center; gap: 0.3rem; border: 1px solid var(--border); border-radius: 999px;
      padding: 0.28rem 0.75rem; font-size: 0.76rem; font-weight: 650; color: var(--text); background: var(--panel);
    }
    .chip.is-active { border-color: var(--accent); background: var(--accent-soft); color: var(--accent); }
    .chip .facet-count { color: var(--muted); font-weight: 500; }
    main.editorial-main { max-width: 1080px; margin: 1.75rem auto 0; padding: 0 1.25rem; }
    .hero { border-bottom: 1px solid var(--border); padding-bottom: 2rem; margin-bottom: 2rem; }
    .hero-kicker {
      display: inline-flex; align-items: center; font-size: 0.72rem; font-weight: 800;
      letter-spacing: 0.09em; text-transform: uppercase; color: var(--accent); margin-bottom: 0.6rem;
    }
    .hero h2 { font-family: var(--headline); font-size: clamp(1.8rem, 1.3rem + 2vw, 2.8rem); line-height: 1.15; margin: 0 0 0.6rem; }
    .hero .post-meta { color: var(--muted); font-size: 0.9rem; margin-bottom: 1.1rem; }
    .hero .post-meta a { color: var(--accent); font-weight: 650; }
    .hero .post-frame { border-radius: 6px; box-shadow: var(--shadow); }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 1.1rem; margin-bottom: 2.25rem; }
    .card {
      border: 1px solid var(--border); border-radius: 6px; background: var(--panel); padding: 1.1rem 1.2rem;
      display: flex; flex-direction: column; gap: 0.4rem; box-shadow: var(--shadow);
    }
    .card.current { border-color: var(--accent); box-shadow: inset 0 0 0 1px var(--accent); }
    .card-kicker { font-size: 0.68rem; font-weight: 800; letter-spacing: 0.07em; text-transform: uppercase; color: var(--muted); }
    .card h3 { margin: 0; font-family: var(--headline); font-size: 1.1rem; line-height: 1.3; }
    .card h3 a { color: var(--ink); }
    .results-panel .results-list { list-style: none; margin: 0; padding: 0; }
    .results-panel .results-list li { padding: 0.9rem 0; border-bottom: 1px solid var(--border); }
    .results-panel .results-list a { font-family: var(--headline); font-size: 1.05rem; font-weight: 700; }
    .results-meta { color: var(--muted); font-size: 0.8rem; margin-top: 0.2rem; }
    .newsletter-band { background: var(--panel); }
    .nl-field input { background: var(--paper); color: var(--text); }
  </style>
<?vsp } else { ?>
  <style>
    /* classic skin -- OpenLink-style two-column layout, sans throughout. */
    :root {
      --accent: #1599d3; --accent-soft: rgba(21, 153, 211, 0.13); --accent-quiet: rgba(92, 201, 232, 0.28);
      --bg: #f5f8fb; --panel: rgba(255, 255, 255, 0.94); --text: #172838; --muted: #637486;
      --border: #d5e3ec; --rss: #f26522; --subscribe: #2e7d32; --shadow: 0 14px 34px rgba(7, 19, 29, 0.10);
    }
    html[data-theme="dark"] {
      --accent: #5cc9e8; --accent-soft: rgba(92, 201, 232, 0.13); --accent-quiet: rgba(92, 201, 232, 0.25);
      --bg: #07131d; --panel: rgba(12, 29, 43, 0.92); --text: #f1f7fb; --muted: #a8bac8;
      --border: rgba(92, 201, 232, 0.18); --shadow: 0 18px 42px rgba(0, 0, 0, 0.36);
    }
    @media (prefers-color-scheme: dark) {
      :root:not([data-theme="light"]) {
        --accent: #5cc9e8; --accent-soft: rgba(92, 201, 232, 0.13); --accent-quiet: rgba(92, 201, 232, 0.25);
        --bg: #07131d; --panel: rgba(12, 29, 43, 0.92); --text: #f1f7fb; --muted: #a8bac8;
        --border: rgba(92, 201, 232, 0.18); --shadow: 0 18px 42px rgba(0, 0, 0, 0.36);
      }
    }
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: var(--bg); color: var(--text); line-height: 1.5; min-height: 100vh; }
    header.masthead {
      position: sticky; top: 0; z-index: 20; background: var(--panel); border-bottom: 1px solid var(--border);
      box-shadow: 0 8px 24px rgba(0,0,0,0.08); padding: 1rem max(1.25rem, calc((100vw - 1380px) / 2));
      display: flex; flex-wrap: wrap; align-items: center; gap: 0.75rem 1rem;
    }
    header.masthead h1 { margin: 0; font-size: 1.35rem; line-height: 1.15; }
    header.masthead h1 a { color: var(--text); }
    header.masthead .tagline { color: var(--muted); font-size: 0.9rem; flex: 1 1 420px; }
    .layout { display: grid; grid-template-columns: minmax(0, 1fr) minmax(280px, 340px); gap: 1.25rem; max-width: 1380px; margin: 1.5rem auto 1.25rem; padding: 0 1.25rem; align-items: start; }
    @media (max-width: 900px) {
      header.masthead { align-items: flex-start; }
      .layout { grid-template-columns: 1fr; margin-top: 1rem; }
      .feed-buttons { width: 100%; }
      aside.sidebar { position: static; max-height: none; }
      aside.sidebar .panel { max-height: 55vh; }
    }
    article.post { background: var(--panel); border: 1px solid var(--border); border-radius: 6px; overflow: hidden; display: flex; flex-direction: column; box-shadow: var(--shadow); position: relative; }
    article.post.embedded { background: transparent; }
    .post-head { padding: 1.2rem 1.4rem 1rem; border-bottom: 1px solid var(--border); }
    .post-kicker { display: inline-flex; align-items: center; min-height: 1.45rem; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent); background: var(--accent-soft); border: 1px solid var(--accent-quiet); border-radius: 3px; padding: 0.18rem 0.5rem; margin-bottom: 0.6rem; }
    .post-head h2 { margin: 0 0 0.45rem; font-size: clamp(1.25rem, 1.1rem + 0.6vw, 1.7rem); line-height: 1.25; }
    .pin-badge { position: relative; display: inline-block; width: 0.66rem; height: 0.66rem; margin-right: 0.34rem; transform: rotate(-22deg); vertical-align: -0.06rem; flex: 0 0 auto; }
    .pin-badge::before { content: ""; position: absolute; width: 0.42rem; height: 0.42rem; left: 0.12rem; top: 0.02rem; border-radius: 50%; background: #ef4444; border: 1px solid rgba(255,255,255,0.92); box-shadow: 0 1px 4px rgba(239,68,68,0.38); }
    .pin-badge::after { content: ""; position: absolute; width: 0.1rem; height: 0.48rem; left: 0.31rem; top: 0.35rem; border-radius: 999px; background: linear-gradient(180deg, #f7d7c4, #805139); }
    .post-status { display: flex; align-items: center; gap: 0.08rem; min-height: 2.15rem; padding: 0.46rem 0.72rem; border-bottom: 1px solid var(--border); background: linear-gradient(90deg, rgba(239,68,68,0.11), rgba(92,201,232,0.06) 62%, transparent); color: var(--muted); font-size: 0.68rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
    article.post.embedded.pinned { background: var(--panel); }
    .post-kicker .pin-badge, .post-status .pin-badge { margin-right: 0.28rem; }
    .post-meta { color: var(--muted); font-size: 0.86rem; }
    .post-meta a { font-weight: 650; color: var(--accent); }
    .post-body { background: #fff; }
    aside.sidebar { display: flex; flex-direction: column; gap: 1rem; position: sticky; top: 5.25rem; max-height: calc(100vh - 6.5rem); min-height: 0; }
    .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 6px; padding: 1rem; box-shadow: var(--shadow); min-height: 0; color: var(--text); }
    aside.sidebar .panel { overflow: auto; scrollbar-width: thin; }
    .panel h3 { margin: 0 0 0.75rem; font-size: 0.74rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); border-bottom: 1px solid var(--border); padding-bottom: 0.55rem; }
    ul.archive { list-style: none; margin: 0; padding: 0; }
    ul.archive li { padding: 0.62rem 0; border-bottom: 1px solid var(--border); }
    ul.archive li:last-child { border-bottom: 0; }
    ul.archive .a-date { display: block; font-size: 0.72rem; color: var(--muted); margin-bottom: 0.16rem; }
    ul.archive li.current { border-left: 3px solid var(--accent); padding-left: 0.65rem; margin-left: -0.65rem; background: var(--accent-soft); }
    ul.archive li.current a { font-weight: 700; }
    ul.archive li.pinned:not(.current) { border-left: 3px solid rgba(239,68,68,0.46); padding-left: 0.65rem; margin-left: -0.65rem; }
    .filter-form { display: grid; gap: 0.55rem; margin-bottom: 0.95rem; }
    .filter-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.45rem; }
    .filter-label { display: grid; gap: 0.18rem; color: var(--muted); font-size: 0.72rem; }
    .filter-input, .filter-select { width: 100%; min-height: 2.1rem; border: 1px solid var(--border); border-radius: 4px; background: #fff; color: #172838; padding: 0.42rem 0.55rem; font: inherit; font-size: 0.84rem; }
    html[data-theme="dark"] .filter-input, html[data-theme="dark"] .filter-select { background: rgba(7,19,29,0.92); color: #f1f7fb; }
    .filter-actions { display: flex; flex-wrap: wrap; gap: 0.45rem; align-items: center; }
    .filter-submit, .filter-reset { border: 1px solid var(--accent-quiet); border-radius: 4px; padding: 0.34rem 0.55rem; font-weight: 700; cursor: pointer; }
    .filter-submit { background: var(--accent); color: #fff; }
    .filter-reset { background: var(--accent-soft); color: var(--accent); }
    .filter-note { color: var(--muted); font-size: 0.74rem; }
    .facet-box { display: grid; gap: 0.55rem; border-top: 1px solid var(--border); padding-top: 0.75rem; }
    .facet-head { display: flex; justify-content: space-between; gap: 0.75rem; align-items: baseline; }
    .facet-title { color: var(--muted); font-size: 0.72rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
    .facet-clear { color: var(--accent); font-size: 0.72rem; font-weight: 750; }
    .facet-list { display: grid; gap: 0.34rem; max-height: 13.5rem; overflow: auto; padding-right: 0.15rem; scrollbar-width: thin; }
    .facet-option { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 0.55rem; min-height: 2rem; border: 1px solid var(--border); border-radius: 4px; background: var(--accent-soft); color: var(--text); padding: 0.34rem 0.45rem 0.34rem 0.55rem; text-decoration: none; }
    .facet-option:hover { border-color: var(--accent-quiet); text-decoration: none; }
    .facet-option.is-active { border-color: var(--accent); box-shadow: inset 3px 0 0 var(--accent); }
    .facet-name { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.76rem; font-weight: 700; }
    .facet-count { min-width: 1.8rem; border-radius: 999px; background: var(--accent-soft); color: var(--accent); font-size: 0.68rem; font-weight: 850; text-align: center; padding: 0.12rem 0.34rem; }
    .facet-option.is-active .facet-count { background: var(--accent); color: #fff; }
    .results-panel { padding: 1.2rem 1.4rem 1.35rem; }
    .results-list { list-style: none; margin: 0; padding: 0; }
    .results-list li { padding: 0.8rem 0; border-bottom: 1px solid var(--border); }
    .results-list a { font-weight: 750; }
    .results-meta { color: var(--muted); font-size: 0.78rem; margin-top: 0.2rem; }
  </style>
<?vsp } ?>
  <script>
  (function () {
    try {
      var stored = window.localStorage.getItem(''weblog-theme'');
      if (stored === ''dark'' || stored === ''light'') document.documentElement.setAttribute(''data-theme'', stored);
    } catch (e) {}
  })();
  </script>
</head>
<body>
<?vsp
  http (''<header class="masthead">'');
  http (sprintf (''<h1><a href="{{PUBLIC_ROUTE}}">%V</a></h1>'', ''{{WEBLOG_TITLE}}''));
  if (skin <> ''editorial'')
    http (sprintf (''<span class="tagline">%V{{TAGLINE_LINK_HTML}}</span>'', ''{{WEBLOG_TAGLINE}}''));
  http (''<nav class="feed-buttons">'');
  http (''<a class="feed-btn rss" href="{{PUBLIC_ROUTE}}?feed=rss" type="application/rss+xml" title="Subscribe via RSS 2.0"><svg viewBox="0 0 24 24"><path d="M6.18 17.82a2.18 2.18 0 1 1-4.36 0 2.18 2.18 0 0 1 4.36 0zM1.82 8.73v3.27c5.02 0 9.09 4.07 9.09 9.09h3.27c0-6.83-5.53-12.36-12.36-12.36zM1.82 2.18v3.27c8.03 0 14.55 6.52 14.55 14.55h3.27C19.64 10.16 11.66 2.18 1.82 2.18z"/></svg>RSS</a>'');
  http (''<a class="feed-btn atom" href="{{PUBLIC_ROUTE}}?feed=atom" type="application/atom+xml" title="Subscribe via Atom 1.0"><svg viewBox="0 0 24 24"><path d="M6.18 17.82a2.18 2.18 0 1 1-4.36 0 2.18 2.18 0 0 1 4.36 0zM1.82 8.73v3.27c5.02 0 9.09 4.07 9.09 9.09h3.27c0-6.83-5.53-12.36-12.36-12.36zM1.82 2.18v3.27c8.03 0 14.55 6.52 14.55 14.55h3.27C19.64 10.16 11.66 2.18 1.82 2.18z"/></svg>Atom</a>'');
  if (newsletter_enabled = ''true'')
    http (''<button type="button" class="feed-btn subscribe" onclick="document.getElementById(&apos;newsletter&apos;).showModal()" title="Subscribe by email"><svg viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>Subscribe</button>'');
  http (''<button class="theme-toggle" type="button" aria-label="Toggle light and dark theme" title="Toggle theme" data-theme-toggle><svg class="moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12.8A8.8 8.8 0 1 1 11.2 3 6.8 6.8 0 0 0 21 12.8z"/></svg><svg class="sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/></svg></button>'');
  http (''</nav></header>'');
?>
<?vsp if (skin = ''editorial'') { ?>
  <div class="util-row">
    <form method="get" action="{{PUBLIC_ROUTE}}" aria-label="Search and filter posts">
      <input type="search" name="q" value="<?= q ?>" placeholder="Search this DAV collection" aria-label="Search this DAV collection" />
      <input type="date" name="from" value="<?= from_date ?>" title="From date" />
      <input type="date" name="to" value="<?= to_date ?>" title="To date" />
    </form>
<?vsp if (has_categories) { ?>
    <div class="chip-row" aria-label="Filter posts by category">
<?vsp http (replace (replace (category_cloud, ''facet-option'', ''chip''), ''facet-name'', ''chip-name'')); ?>
      <a class="chip" href="{{PUBLIC_ROUTE}}?q=<?= q ?>&amp;from=<?= from_date ?>&amp;to=<?= to_date ?>">All <?= all_count ?></a>
    </div>
<?vsp } ?>
  </div>
  <main class="editorial-main">
<?vsp
  if (n = 0)
  {
    if (filter_active)
      http (''<div class="hero"><h2>No matching posts</h2><p class="post-meta">Adjust the search terms, date range, or category filter.</p></div>'');
    else
      http (''<div class="hero"><h2>No posts yet</h2></div>'');
  }
  else if (filter_active and post_selected = 0)
  {
    http (''<div class="results-panel"><div class="hero-kicker">Search Results</div>'');
    http (sprintf (''<h2 style="font-family:var(--headline);font-size:1.6rem;">%d matching posts</h2>'', n));
    http (''<ul class="results-list">'');
    for (i := 0; i < n; i := i + 1)
    {
      declare rname, rtitle, rdate varchar;
      declare rmod datetime;
      rname := aref (aref (posts, i), 0);
      rmod := aref (aref (posts, i), 1);
      rtitle := aref (aref (posts, i), 2);
      rdate := sprintf (''%s %d, %d'', aref (months, month (rmod) - 1), dayofmonth (rmod), year (rmod));
      http (sprintf (''<li><a href="{{PUBLIC_ROUTE}}?post=%U">%V</a><div class="results-meta">%V</div></li>'', rname, DB.DBA.WEBLOG_UTF8_DECODE (rtitle), rdate));
    }
    http (''</ul></div>'');
  }
  else
  {
    declare cname, ctitle, cext varchar;
    declare cmod datetime;
    declare cdate varchar;
    declare cpin int;
    cname  := aref (aref (posts, idx), 0);
    cmod   := aref (aref (posts, idx), 1);
    ctitle := aref (aref (posts, idx), 2);
    cext   := aref (aref (posts, idx), 3);
    cdate  := sprintf (''%s %d, %d'', aref (months, month (cmod) - 1), dayofmonth (cmod), year (cmod));
    cpin := cast (aref (aref (posts, idx), 6) as int);
    http (''<div class="hero">'');
    if (cpin)
      http (sprintf (''<div class="hero-kicker">Pinned &mdash; %V</div>'', cdate));
    else if (idx = 0)
      http (sprintf (''<div class="hero-kicker">Latest Post &mdash; %V</div>'', cdate));
    else
      http (sprintf (''<div class="hero-kicker">From the Archive &mdash; %V</div>'', cdate));
    http (sprintf (''<h2>%V</h2>'', DB.DBA.WEBLOG_UTF8_DECODE (ctitle)));
    {
      declare permalink_url varchar;
      permalink_url := sprintf (''%s{{DAV_COLLECTION}}%U'', site_base, cname);
      http (sprintf (''<div class="post-meta">Published %V &middot; <a class="post-permalink" href="%V" target="_top" rel="noopener noreferrer">WebDAV Permalink</a></div>'', cdate, permalink_url));
    }
    if (cext = ''html'')
      http (sprintf (''<iframe class="post-frame" src="{{PUBLIC_ROUTE}}?raw=%U" title="%V" loading="lazy" sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox allow-top-navigation-by-user-activation"></iframe>'', cname, DB.DBA.WEBLOG_UTF8_DECODE (ctitle)));
    else
      http (sprintf (''<iframe class="post-frame" src="{{PUBLIC_ROUTE}}?raw=%U" title="%V" loading="lazy" sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox allow-top-navigation-by-user-activation"></iframe>'', cname, DB.DBA.WEBLOG_UTF8_DECODE (ctitle)));
    http (''</div>'');
  }
  if (n > 0)
  {
    http (''<div class="grid">'');
    for (i := 0; i < n; i := i + 1)
    {
      declare aname, atitle, adate varchar;
      declare amod datetime;
      declare apin int;
      declare cardcls varchar;
      aname  := aref (aref (posts, i), 0);
      amod   := aref (aref (posts, i), 1);
      atitle := aref (aref (posts, i), 2);
      apin := cast (aref (aref (posts, i), 6) as int);
      adate  := sprintf (''%s %d, %d'', aref (months, month (amod) - 1), dayofmonth (amod), year (amod));
      cardcls := ''card'';
      if (i = idx and post_selected) cardcls := ''card current'';
      http (sprintf (''<article class="%s">'', cardcls));
      if (apin)
        http (sprintf (''<span class="card-kicker">Pinned &middot; %V</span>'', adate));
      else
        http (sprintf (''<span class="card-kicker">%V</span>'', adate));
      http (sprintf (''<h3><a href="{{PUBLIC_ROUTE}}?post=%U">%V</a></h3>'', aname, DB.DBA.WEBLOG_UTF8_DECODE (atitle)));
      http (''</article>'');
    }
    http (''</div>'');
  }
?>
  </main>
<?vsp } else { ?>
  <div class="layout">
<?vsp
  if (n = 0)
  {
    if (filter_active)
      http (''<article class="post"><div class="post-head"><h2>No matching posts</h2><div class="post-meta">Adjust the search terms, date range, or category filter.</div></div></article>'');
    else
      http (''<article class="post"><div class="post-head"><h2>No posts yet</h2></div></article>'');
  }
  else if (filter_active and post_selected = 0)
  {
    http (''<article class="post"><div class="post-head"><span class="post-kicker">Search Results</span>'');
    http (sprintf (''<h2>%d matching posts</h2>'', n));
    http (''<div class="post-meta">Results are scoped to this WebDAV collection.</div></div><div class="results-panel"><ul class="results-list">'');
    for (i := 0; i < n; i := i + 1)
    {
      declare rname, rtitle, rdate, rcat varchar;
      declare rmod datetime;
      rname := aref (aref (posts, i), 0);
      rmod := aref (aref (posts, i), 1);
      rtitle := aref (aref (posts, i), 2);
      rcat := aref (aref (posts, i), 4);
      rdate := sprintf (''%s %d, %d'', aref (months, month (rmod) - 1), dayofmonth (rmod), year (rmod));
      http (''<li>'');
      http (sprintf (''<a href="{{PUBLIC_ROUTE}}?post=%U">%V</a>'', rname, DB.DBA.WEBLOG_UTF8_DECODE (rtitle)));
      if (rcat <> '''') http (sprintf (''<span class="a-category">%V</span>'', DB.DBA.WEBLOG_UTF8_DECODE (rcat)));
      http (sprintf (''<div class="results-meta">%V</div>'', rdate));
      http (''</li>'');
    }
    http (''</ul></div></article>'');
  }
  else
  {
    declare cname, ctitle, cext varchar;
    declare cmod datetime;
    declare cdate varchar;
    declare cpin int;
    cname  := aref (aref (posts, idx), 0);
    cmod   := aref (aref (posts, idx), 1);
    ctitle := aref (aref (posts, idx), 2);
    cext   := aref (aref (posts, idx), 3);
    cdate  := sprintf (''%s %d, %d'', aref (months, month (cmod) - 1), dayofmonth (cmod), year (cmod));
    cpin := cast (aref (aref (posts, idx), 6) as int);
    if (cpin)
      http (''<article class="post embedded pinned"><div class="post-status" aria-label="Pinned post"><span class="pin-badge" aria-hidden="true"></span><span>Pinned post</span></div>'');
    else
      http (''<article class="post embedded">'');
    {
      declare permalink_url varchar;
      permalink_url := sprintf (''%s{{DAV_COLLECTION}}%U'', site_base, cname);
      http (sprintf (''<div class="post-meta">Published %V &middot; <a class="post-permalink" href="%V" target="_top" rel="noopener noreferrer">WebDAV Permalink</a></div>'', cdate, permalink_url));
    }
    http (sprintf (''<div class="post-body"><iframe class="post-frame" src="{{PUBLIC_ROUTE}}?raw=%U" title="%V" loading="lazy" sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox allow-top-navigation-by-user-activation"></iframe></div>'', cname, DB.DBA.WEBLOG_UTF8_DECODE (ctitle)));
    http (''</article>'');
  }
?>
    <aside class="sidebar">
      <div class="panel">
        <h3>Recent Posts (<?= n ?> posts)</h3>
        <form class="filter-form" method="get" action="{{PUBLIC_ROUTE}}" aria-label="Search and filter posts">
          <input class="filter-input" type="search" name="q" value="<?= q ?>" placeholder="Search this DAV collection" aria-label="Search this DAV collection" />
          <div class="filter-row">
            <label class="filter-label">From <input class="filter-input" type="date" name="from" value="<?= from_date ?>" /></label>
            <label class="filter-label">To <input class="filter-input" type="date" name="to" value="<?= to_date ?>" /></label>
          </div>
<?vsp if (has_categories) { ?>
          <div class="facet-box" aria-label="Filter posts by category">
            <div class="facet-head">
              <span class="facet-title">Categories</span>
              <a class="facet-clear" href="{{PUBLIC_ROUTE}}?q=<?= q ?>&amp;from=<?= from_date ?>&amp;to=<?= to_date ?>">All <?= all_count ?></a>
            </div>
            <div class="facet-list">
<?vsp http (category_cloud); ?>
            </div>
          </div>
<?vsp } ?>
          <div class="filter-actions">
            <button class="filter-submit" type="submit">Apply</button>
            <a class="filter-reset" href="{{PUBLIC_ROUTE}}">Reset</a>
          </div>
          <div class="filter-note">Search uses Virtuoso full-text search over this DAV collection.</div>
        </form>
        <ul class="archive">
<?vsp
  for (i := 0; i < n; i := i + 1)
  {
    declare aname, atitle, adate, acategory varchar;
    declare amod datetime;
    declare apin int;
    declare cls varchar;
    aname  := aref (aref (posts, i), 0);
    amod   := aref (aref (posts, i), 1);
    atitle := aref (aref (posts, i), 2);
    acategory := aref (aref (posts, i), 4);
    apin := cast (aref (aref (posts, i), 6) as int);
    adate  := sprintf (''%s %d, %d'', aref (months, month (amod) - 1), dayofmonth (amod), year (amod));
    cls := '''';
    if (i = idx and apin)
      cls := '' class="current pinned"'';
    else if (i = idx)
      cls := '' class="current"'';
    else if (apin)
      cls := '' class="pinned"'';
    http (sprintf (''<li%s>'', cls));
    if (apin)
      http (sprintf (''<span class="a-date"><span class="pin-badge" aria-hidden="true"></span>%V</span>'', adate));
    else
      http (sprintf (''<span class="a-date">%V</span>'', adate));
    http (sprintf (''<a href="{{PUBLIC_ROUTE}}?post=%U">%V</a>'', aname, DB.DBA.WEBLOG_UTF8_DECODE (atitle)));
    if (acategory <> '''')
      http (sprintf (''<span class="a-category">%V</span>'', DB.DBA.WEBLOG_UTF8_DECODE (acategory)));
    http (''</li>'');
  }
?>
        </ul>
      </div>
    </aside>
  </div>
<?vsp } ?>
<?vsp if (newsletter_enabled = ''true'') { ?>
  <dialog id="newsletter" class="newsletter-band" aria-label="Newsletter subscription">
    <button type="button" class="nl-close" aria-label="Close" onclick="document.getElementById(''newsletter'').close()">&times;</button>
    <h2>Get the latest posts in your inbox</h2>
    <p class="nl-sub">Subscribe to this weblog and get new posts delivered to your inbox.</p>
    <form class="nl-form" method="post" action="{{PUBLIC_ROUTE}}">
      <input type="hidden" name="nl_action" value="subscribe" />
      <div class="nl-field">
        <label for="nl-email">Email <span aria-hidden="true">*</span></label>
        <input id="nl-email" type="email" name="email" required="required" placeholder="you@example.com" />
      </div>
      <div class="nl-field nl-country">
        <label for="nl-country">Country (optional)</label>
        <input id="nl-country" type="text" name="country" placeholder="Country" />
      </div>
      <button class="nl-submit" type="submit">Subscribe</button>
    </form>
    <p class="nl-consent">By clicking &ldquo;Subscribe&rdquo; you agree to receive email updates about new posts on this weblog. You can unsubscribe at any time via the link in every email.</p>
  </dialog>
<?vsp } ?>

  <footer class="colophon" aria-label="Weblog metadata">
    <div class="footer-inner">
      <div class="footer-copy">
        <span class="footer-primary">Published from <a href="{{PUBLIC_ROUTE}}" target="_top" rel="noopener noreferrer">this WebDAV Folder</a> using <a href="https://virtuoso.openlinksw.com/" target="_blank" rel="noopener noreferrer">OpenLink Virtuoso</a> Server Pages over Virtuoso WebDAV.</span>
        <span class="footer-provenance">Weblog engine by <a href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/weblog-from-webdav" target="_blank" rel="noopener noreferrer">weblog-from-webdav</a>, operated by <a href="https://www.openlinksw.com/" target="_blank" rel="noopener noreferrer">OpenLink Software</a>.</span>
      </div>
      <a class="virtuoso-badge" href="https://virtuoso.openlinksw.com/" target="_blank" rel="noopener noreferrer" title="Powered by OpenLink Virtuoso" aria-label="Powered by OpenLink Virtuoso">
        <span class="vb-powered">powered by</span>
        <span class="vb-name">Virtuoso</span>
      </a>
      <nav class="footer-links" aria-label="Subscription links">
        <a href="{{PUBLIC_ROUTE}}?feed=rss">RSS</a>
        <a href="{{PUBLIC_ROUTE}}?feed=atom">Atom</a>
        <a href="{{PUBLIC_ROUTE}}?feed=atomPub">AtomPub</a>
      </nav>
    </div>
  </footer>

  <script>
  (function () {
    var button = document.querySelector(''[data-theme-toggle]'');
    if (!button) return;
    function currentTheme () {
      var explicitTheme = document.documentElement.getAttribute(''data-theme'');
      if (explicitTheme === ''dark'' || explicitTheme === ''light'') return explicitTheme;
      return window.matchMedia && window.matchMedia(''(prefers-color-scheme: dark)'').matches ? ''dark'' : ''light'';
    }
    button.addEventListener(''click'', function () {
      var next = currentTheme() === ''dark'' ? ''light'' : ''dark'';
      document.documentElement.setAttribute(''data-theme'', next);
      try { window.localStorage.setItem(''weblog-theme'', next); } catch (e) {}
    });
  })();
  </script>
</body>
</html>
';

  index_content := replace (index_content, '{{DAV_COLLECTION}}', coll);
  index_content := replace (index_content, '{{PUBLIC_ROUTE}}', route);
  index_content := replace (index_content, '{{ADMIN_ROUTE}}', admin_route);
  index_content := replace (index_content, '{{ACTION_ROUTE}}', action_route);
  index_content := replace (index_content, '{{WEBLOG_TITLE}}', weblog_title);
  index_content := replace (index_content, '{{WEBLOG_TAGLINE}}', weblog_tagline);
  index_content := replace (index_content, '{{TAGLINE_LINK_HTML}}', tagline_link_html);
  index_content := replace (index_content, '{{DEFAULT_SKIN}}', default_skin);

  index_stream := string_output ();
  http (index_content, index_stream);

  -- Upgrades must not be destructive: an existing index.vsp that was NOT
  -- generated by this template (e.g. the hand-authored, single-site
  -- deploy-weblog-opl-site.sql/deploy-weblog-opl-site-facet.sql templates)
  -- must never be silently overwritten by a redeploy/upgrade call -- that
  -- would replace real, deliberately different site content with the
  -- generic one. Every index.vsp this template has ever generated contains
  -- this exact literal comment (grep-checked, not modified by any
  -- {{TOKEN}} substitution). If existing content doesn't contain it, this
  -- collection is either running a different template or something
  -- unrecognized -- refuse rather than guess, unless the caller explicitly
  -- opts in with allow_template_overwrite=1. Skin changes on an existing,
  -- already-deployed-by-this-template collection never need a redeploy at
  -- all: they go through weblog:skin (the admin dashboard's Skin setting),
  -- resolved at request time.
  {
    declare existing_content varchar;
    declare existing_count int;
    existing_content := null;
    existing_count := 0;
    for (select RES_CONTENT as _c from WS.WS.SYS_DAV_RES where RES_FULL_PATH = index_path) do
    {
      existing_count := existing_count + 1;
      existing_content := blob_to_string (_c);
    }
    if (existing_count > 0 and allow_template_overwrite = 0
        and (existing_content is null or strstr (existing_content, 'multi-skin, config-driven') is null))
      signal ('42000', sprintf ('Refusing to overwrite %s -- its existing content does not look like a deploy-weblog-skinned.sql deployment (no matching signature found), so it is likely a different, hand-authored template. To change the skin on an already-deployed collection, use weblog:skin (the admin dashboard''s Skin setting) instead of redeploying -- no redeploy needed. If you are certain you want to replace this collection''s index.vsp with the generic template, call this procedure again with allow_template_overwrite=>1.', index_path));
  }

  DB.DBA.DAV_DELETE_INT (index_path, 1, null, null, 0);
  -- Owner/group MUST be 'dav' (RES_OWNER=2) for Virtuoso to execute a .vsp
  -- resource rather than serve it as raw static source -- see
  -- agent-rdf-memory/howto/osdi-vsp-execution-registration.ttl. This is
  -- independent of dav_user, which only controls VHOST vsp_user (the SQL
  -- identity the script runs AS) and the pin-seeding DAV_PROP_SET call.
  rc := DB.DBA.DAV_RES_UPLOAD_STRSES_INT (index_path, index_stream, 'text/html', '111101101R', 'dav', 'dav', null, null, 0);
  if (rc < 0)
    signal ('42000', sprintf ('DAV upload failed for %s, rc=%d', index_path, rc));
  -- Re-assert RES_PERMS explicitly: confirmed live on a real instance that
  -- the perms argument above did NOT take effect (RES_OWNER/RES_GROUP were
  -- applied correctly as 'dav', but RES_PERMS came back as a plain default
  -- '110100100' -- rw-r--r--, no world-execute -- instead of the requested
  -- '111101101' -- rwxr-xr-x). World lost execute, so every request that
  -- Digest-authenticated on the action route (falling into the "world"
  -- permission bucket, since it matches neither RES_OWNER nor RES_GROUP)
  -- got served index.vsp's raw, uncompiled source instead of having it
  -- execute -- identical symptom to the documented restrictive-permissions
  -- constraint, but caused by this silent reset rather than a deliberately
  -- restrictive upload. This UPDATE is the actual word on RES_PERMS
  -- regardless of what upload the resource went through.
  update WS.WS.SYS_DAV_RES set RES_PERMS = '111101101R' where RES_FULL_PATH = index_path;

  -- Seed the default pin when no explicit schema:position pin exists yet.
  DB.DBA.TMP_DEPLOY_WEBLOG_SKINNED_DEFAULT_PIN (coll, dav_user);

  -- Record the public route as a collection property so code with no HTTP
  -- request context (the newsletter digest scheduler) can still build
  -- correct public links back into this weblog.
  {
    -- Written with DAV_PROP_SET_INT (no per-user auth) rather than
    -- DAV_PROP_SET as dav_user: the latter needs dav_user's SQL password
    -- hash and silently writes nothing when that doesn't resolve or is
    -- rejected -- on UB weblog:adminCollection was never recorded that way,
    -- so the dashboard refresh then refused to run. Any error code fails
    -- the deploy instead of being ignored.
    -- weblog:adminDavUser is kept in sync with dav_user: WEBLOG_ADMIN_AUTH_FN
    -- reads it to decide who may authenticate as this collection's admin.
    declare props any;
    declare pi, prc int;
    props := vector ('weblog:publicRoute', route,
                     'weblog:actionRoute', action_route,
                     'weblog:adminDavUser', dav_user,
                     'weblog:adminCollection', admin_coll);
    for (pi := 0; pi < length (props); pi := pi + 2)
    {
      prc := DB.DBA.DAV_PROP_SET_INT (coll, props[pi], props[pi + 1], null, null, 0, 0, 1);
      if (not isinteger (prc) or prc < 0)
        signal ('42000', sprintf ('Could not record %s on %s (DAV error %s).', props[pi], coll, cast (prc as varchar)));
    }
  }

  -- Admin collection: owner dav_user, group WEBLOG_OPERATOR, no world bits.
  -- DAV owner/group arguments must be numeric U_IDs for a role: passing the
  -- role NAME silently stores COL_GROUP/RES_GROUP = -12 (verified live).
  -- Permissions are re-applied on every deploy so a hand-loosened
  -- collection is put back.
  {
    declare exit handler for sqlstate '*' { ; };
    exec ('create role WEBLOG_OPERATOR');
  }
  operator_gid := (select U_ID from DB.DBA.SYS_USERS where U_NAME = 'WEBLOG_OPERATOR' and U_IS_ROLE = 1);
  owner_uid := (select U_ID from DB.DBA.SYS_USERS where U_NAME = dav_user);
  if (operator_gid is null or owner_uid is null)
    signal ('42000', sprintf ('Cannot resolve owner %s or role WEBLOG_OPERATOR for the admin collection.', dav_user));
  admin_col_id := DB.DBA.DAV_SEARCH_ID (admin_coll, 'C');
  if (not isinteger (admin_col_id) or admin_col_id < 0)
  {
    admin_col_id := DB.DBA.DAV_COL_CREATE_INT (admin_coll, '111111000N', owner_uid, operator_gid, null, null, 0, 0, 0);
    if (not isinteger (admin_col_id) or admin_col_id < 0)
      signal ('42000', sprintf ('Could not create admin collection %s (rc=%s) -- does its parent collection exist?', admin_coll, cast (admin_col_id as varchar)));
  }
  update WS.WS.SYS_DAV_COL set COL_OWNER = owner_uid, COL_GROUP = operator_gid, COL_PERMS = '111111000N' where COL_ID = admin_col_id;

  -- A dashboard.html left in the public collection by an earlier deploy is
  -- publicly readable (and holds subscriber names/emails) -- remove it.
  DB.DBA.DAV_DELETE_INT (coll || 'dashboard.html', 1, null, null, 0);

  -- Map public_route as a VSP-enabled DAV directory serving this collection.
  for (select distinct HP_LISTEN_HOST as _lh, HP_HOST as _vh
         from DB.DBA.HTTP_PATH where HP_LPATH in ('/DAV', '/public_home') and HP_LISTEN_HOST <> '') do
  -- Listener-less ('' lhost) rows are skipped: VHOST_REMOVE cannot delete a
  -- row with an empty lhost/vhost (verified live), so redefining a route
  -- there on redeploy always fails with SR197 Non unique primary key.
  {
    DB.DBA.TMP_DEPLOY_WEBLOG_SKINNED_VHOST_REMOVE (_lh, _vh, route);
    DB.DBA.TMP_DEPLOY_WEBLOG_SKINNED_VHOST_REMOVE (_lh, _vh, subseq (route, 0, length (route) - 1));
    DB.DBA.VHOST_DEFINE (lhost=>_lh, vhost=>_vh, lpath=>route,
                         ppath=>coll,
                         is_dav=>1,
                         is_brws=>0,
                         def_page=>'index.vsp',
                         vsp_user=>dav_user,
                         ses_vars=>0,
                         opts=>vector ('browse_sheet', '', 'noinherit', 'yes'),
                         is_default_host=>0);

    -- Clear any older admin-route definition on every host pair (earlier
    -- versions defined it everywhere, pointing at the public collection);
    -- it is redefined once, TLS-only, after this loop.
    DB.DBA.TMP_DEPLOY_WEBLOG_SKINNED_VHOST_REMOVE (_lh, _vh, admin_route);
    DB.DBA.TMP_DEPLOY_WEBLOG_SKINNED_VHOST_REMOVE (_lh, _vh, admin_lpath);

    DB.DBA.TMP_DEPLOY_WEBLOG_SKINNED_VHOST_REMOVE (_lh, _vh, action_route);
    DB.DBA.TMP_DEPLOY_WEBLOG_SKINNED_VHOST_REMOVE (_lh, _vh, subseq (action_route, 0, length (action_route) - 1));
    DB.DBA.VHOST_DEFINE (lhost=>_lh, vhost=>_vh, lpath=>action_route,
                         ppath=>coll,
                         is_dav=>1,
                         is_brws=>0,
                         def_page=>'index.vsp',
                         vsp_user=>dav_user,
                         realm=>action_realm,
                         auth_fn=>'DB.DBA.WEBLOG_ADMIN_AUTH_FN',
                         sec=>'digest',
                         ses_vars=>0,
                         opts=>action_opts,
                         is_default_host=>0);
  }

  DB.DBA.TMP_DEPLOY_WEBLOG_SKINNED_VHOST_REMOVE (admin_lhost, uriqa_host, admin_route);
  DB.DBA.TMP_DEPLOY_WEBLOG_SKINNED_VHOST_REMOVE (admin_lhost, uriqa_host, admin_lpath);
  DB.DBA.VHOST_DEFINE (lhost=>admin_lhost,
                       vhost=>uriqa_host,
                       lpath=>admin_lpath,
                       ppath=>admin_coll,
                       is_dav=>1,
                       is_brws=>0,
                       def_page=>'dashboard.html',
                       ses_vars=>0,
                       sec=>'SSL',
                       opts=>vector ('browse_sheet', '', 'noinherit', 'yes'),
                       is_default_host=>0);

  -- Seed dashboard.html immediately so the admin route isn't empty before
  -- the first scheduled refresh, and make sure the digest actually has a
  -- schedule (defaulting to weekly) so it is not silently unscheduled after
  -- a deploy. Both guarded: register-weblog-newsletter.sql is an optional
  -- add-on and may not be installed yet. Only schedules the digest if no
  -- event by this deterministic name exists yet -- never clobbers an
  -- interval the operator already changed from the dashboard.
  -- A failed dashboard refresh is reported in the result, not swallowed --
  -- an empty admin route with a "successful" deploy is what hid the UB
  -- failure.
  dashboard_status := 'newsletter add-on not installed';
  if ((select count (*) from DB.DBA.SYS_PROCEDURES where P_NAME = 'DB.DBA.WEBLOG_DASHBOARD_REFRESH') > 0)
  {
    declare exit handler for sqlstate '*' { dashboard_status := concat ('FAILED: ', __SQL_MESSAGE); };
    DB.DBA.WEBLOG_DASHBOARD_REFRESH (coll);
    dashboard_status := 'refreshed';
  }
  {
    declare exit handler for sqlstate '*' { ; };
    if ((select count (*) from DB.DBA.SYS_PROCEDURES where P_NAME = 'DB.DBA.WEBLOG_NEWSLETTER_SCHEDULE_DIGEST') > 0
        and (select count (*) from DB.DBA.SYS_SCHEDULED_EVENT where SE_NAME = sprintf ('weblog-newsletter-digest:%s', coll)) = 0)
      DB.DBA.WEBLOG_NEWSLETTER_SCHEDULE_DIGEST (sprintf ('weblog-newsletter-digest:%s', coll), coll, 10080);
  }

  return sprintf ('{"ok":true,"dav_collection":"%V","public_route":"%V","skin":"%V","admin_collection":"%V","dashboard_url":"https://%V%V%V","action_route":"%V","admin_dav_user":"%V","dashboard":"%V"}', coll, route, default_skin, admin_coll, uriqa_host, case when ssl_port = '443' then '' else concat (':', ssl_port) end, admin_route, action_route, dav_user, dashboard_status);
}
;

-- Usage: deploy against an arbitrary local collection.
-- SELECT DB.DBA.WEBLOG_DAV_DEPLOY_SKINNED ('/DAV/home/dba/weblog-test/', '/weblog-test/', 'My Test Weblog', 'A configurable, skinnable weblog view of a WebDAV folder.', 'classic', 'dba');
--
-- Switch the live skin without redeploying (per-request override also works via ?skin=editorial):
-- SELECT DB.DBA.DAV_PROP_SET ('/DAV/home/dba/weblog-test/', 'weblog:skin', 'editorial', 'dba', (SELECT pwd_magic_calc (U_NAME, U_PASSWORD, 1) FROM DB.DBA.SYS_USERS WHERE U_NAME = 'dba'), 1);
--
-- Turn on the newsletter footer band:
-- SELECT DB.DBA.DAV_PROP_SET ('/DAV/home/dba/weblog-test/', 'weblog:newsletterEnabled', 'true', 'dba', (SELECT pwd_magic_calc (U_NAME, U_PASSWORD, 1) FROM DB.DBA.SYS_USERS WHERE U_NAME = 'dba'), 1);

-- Verification
SELECT HP_LISTEN_HOST, HP_HOST, HP_LPATH, HP_PPATH, HP_RUN_VSP_AS, HP_OPTIONS FROM DB.DBA.HTTP_PATH WHERE HP_PPATH LIKE '%weblog-test%';

-- ============================================================================
-- OPERATOR ROLE -- lets designated non-dba users (e.g. a WebID-TLS session
-- mapped to a specific SQL account) call the procedures this skill installs,
-- without granting them dba/superuser rights. Verified live 2026-09-23: a
-- WebID-TLS session that isn't dba and isn't the object owner gets
-- "SR186:SECURITY: No permission to execute procedure" calling any DB.DBA.WEBLOG_*
-- procedure by default -- Virtuoso does not auto-grant execute on a new
-- object to anyone but its owner/dba. Fully idempotent and safe to re-run:
-- the role is created once and reused, every DB.DBA.WEBLOG_% procedure
-- (the permanent library this skill installs -- newsletter, dashboard,
-- deploy, etc.) gets (re-)granted every run, so a procedure added by a
-- future template change is automatically covered on the next reinstall,
-- not just the ones that existed when the role was first created. Re-
-- granting membership to an already-member user is a harmless no-op. Runs
-- BEFORE the REDEPLOY block's own TMP_WEBLOG_UPGRADE_* helper procedures are
-- created below on purpose -- those are ephemeral (created, called, and
-- dropped within this same script run by the SAME privileged session that
-- is running this file), never called independently by a different,
-- less-privileged session the way the permanent WEBLOG_* library is, so
-- they have no standing need for a role grant.
--
-- ADDING ANOTHER DESIGNATED USER (besides kidehen): run, once, as dba:
--   grant WEBLOG_OPERATOR to <username>;
-- REMOVING ONE:
--   revoke WEBLOG_OPERATOR from <username>;
create procedure DB.DBA.TMP_WEBLOG_UPGRADE_GRANT_ROLE ()
{
  declare grant_note varchar;
  grant_note := '';
  {
    declare exit handler for sqlstate '*' { ; };
    exec ('create role WEBLOG_OPERATOR');
  }
  {
    declare pname varchar;
    for (select P_NAME as _p from DB.DBA.SYS_PROCEDURES where P_NAME like 'DB.DBA.WEBLOG\_%' escape '\\') do
    {
      pname := _p;
      {
        declare exit handler for sqlstate '*' { ; };
        exec (sprintf ('grant execute on %s to WEBLOG_OPERATOR', pname));
      }
    }
  }
  {
    -- GRANT <role> TO <user> is NOT idempotent (verified live 2026-09-23):
    -- re-granting a role a user already holds errors with U0013 rather than
    -- silently succeeding, unlike GRANT EXECUTE ON <object> above. __SQL_MESSAGE
    -- distinguishes that harmless case from a real failure (most likely
    -- 'kidehen' not existing as a SQL account on this particular instance,
    -- which the role/procedure grants above are unaffected by either way).
    declare exit handler for sqlstate '*'
    {
      if (__SQL_MESSAGE like '%already has role%')
        grant_note := 'WEBLOG_OPERATOR role ready, granted on every WEBLOG_* procedure; kidehen was already a member.';
      else
        grant_note := sprintf ('(WEBLOG_OPERATOR role/procedure grants applied; granting membership to kidehen failed -- %s -- add the right account manually per the comment above)', __SQL_MESSAGE);
    };
    exec ('grant WEBLOG_OPERATOR to kidehen');
  }
  if (grant_note = '') grant_note := 'WEBLOG_OPERATOR role ready, granted on every WEBLOG_* procedure, kidehen added as a member.';
  return grant_note;
}
;
commit work;
select DB.DBA.TMP_WEBLOG_UPGRADE_GRANT_ROLE ();
drop procedure DB.DBA.TMP_WEBLOG_UPGRADE_GRANT_ROLE;

-- ============================================================================
-- PRE-FLIGHT BACKUP 2 of 2 + REDEPLOY -- no editing needed for the three
-- sites already registered below (demo.openlinksw.com, UB, www.openlinksw.com):
-- this block AUTO-DETECTS which one you're connected to and redeploys it,
-- so the file can be run as-is (see TMP_WEBLOG_UPGRADE_AUTODETECT below for
-- how, and DAV_COLLECTION/PUBLIC_ROUTE/etc. for what it deploys with).
-- Before overwriting index.vsp/dashboard.html, this automatically snapshots
-- whatever is currently there (if anything) into DB.DBA.WEBLOG_UPGRADE_BACKUP
-- (created on first use, never dropped by a reinstall -- every prior run's
-- snapshots stay available).
--
-- ADDING A NEW SITE: add an "else if" branch to
-- TMP_WEBLOG_UPGRADE_AUTODETECT's detection logic below, or bypass
-- auto-detection entirely by calling TMP_WEBLOG_UPGRADE_APPLY directly with
-- explicit arguments (DAV_COLLECTION, PUBLIC_ROUTE, WEBLOG_TITLE,
-- WEBLOG_TAGLINE, DEFAULT_SKIN, DAV_USER -- same six DB.DBA.WEBLOG_DAV_DEPLOY_SKINNED
-- takes) before the DROP PROCEDURE statements remove it -- required for a
-- first-ever install, since auto-detection has nothing to find yet on a
-- site with no prior deployment.
--
-- Sites registered as of 2026-09-23:
--   demo.openlinksw.com : '/DAV/home/demo/Public/fifa-kg/', '/weblog/'
--   UB                  : '/DAV/demos/daas/',               '/weblog/'
--   www.openlinksw.com  : '/DAV/www2.openlinksw.com/data/html/', '/weblog/'
--
-- CAUTION -- demo.openlinksw.com and www.openlinksw.com: verified live
-- 2026-09-24 that these two currently serve a DIFFERENT, hand-authored
-- template (deploy-weblog-opl-site.sql / deploy-weblog-opl-site-facet.sql,
-- with their own custom tagline/markup), not this file's generic
-- deploy-weblog-skinned.sql -- their branches below have not been
-- exercised against a real deploy and would silently REPLACE that custom
-- template's index.vsp/dashboard.html with the generic one if their
-- index.vsp happens to be found at the path checked. Only UB has actually
-- been run through this file to date. Confirm which template a site is
-- really running (compare its live tagline/markup against both templates)
-- before running this file against demo or www for the first time.
--
-- ADMIN DASHBOARD LOCATION: each site's admin_coll below is left null, which
-- means "reuse the location a previous deploy recorded in
-- weblog:adminCollection, else the suggested aunt/uncle default" --
--   demo : /DAV/home/demo/Public-fifa-kg-admin/
--   UB   : /DAV/demos-daas-admin/
--   www  : /DAV/www2.openlinksw.com/data-html-admin/
-- Set admin_coll to an explicit /DAV/... path to choose a different one; it
-- must be outside the public blog collection. The admin route is published
-- TLS-only, on each site's own public host (set per site below), at the
-- ini's SSLPort or else an existing :443 listener.
--
-- TO RESTORE index.vsp or dashboard.html from a WEBLOG_UPGRADE_BACKUP row
-- (find the row first -- select WUB_ID, WUB_RES_NAME, WUB_BACKED_UP_AT from
-- DB.DBA.WEBLOG_UPGRADE_BACKUP where WUB_DAV_COLLECTION = '<collection>'
-- order by WUB_BACKED_UP_AT desc):
--   declare content varchar;
--   select WUB_RES_CONTENT into content from DB.DBA.WEBLOG_UPGRADE_BACKUP where WUB_ID = <id>;
--   DB.DBA.DAV_RES_UPLOAD_STRSES_INT ('<collection>index.vsp', string_to_file (content, null, 0), 'text/html', '111101101R', 'dav', 'dav', null, null, 0);
-- ============================================================================

-- Fully self-contained via exec() (dynamic SQL) for every step that touches
-- DB.DBA.WEBLOG_UPGRADE_BACKUP -- deliberately NOT a static INSERT/SELECT
-- against that table. A stored procedure body cannot reference a table that
-- does not exist yet at COMPILE time (Virtuoso resolves table references at
-- procedure-compile time, not deferred to call time) -- an earlier version
-- of this file split table-creation into its own helper procedure, called
-- it, then compiled THIS procedure expecting the table to already be
-- visible; that worked in repeated local testing but failed against a real
-- remote instance 2026-09-23 (SQ096: No table ... on the compile of this
-- very procedure, immediately after the helper reported success) -- most
-- likely a client/transaction-visibility difference in how that instance's
-- SQL tool committed between statements. exec()-only sidesteps the whole
-- class of failure: Virtuoso never needs to statically resolve the table
-- name at compile time, only at the moment each exec() actually runs, by
-- which point the CREATE TABLE exec() just above it has already completed
-- within the SAME statement's execution. Each backup step also gets its own
-- exit handler so a backup failure can never prevent the deploy itself from
-- running -- backups are best-effort, the deploy is not.
create procedure DB.DBA.TMP_WEBLOG_UPGRADE_APPLY
  (
    IN dav_collection VARCHAR,
    IN public_route VARCHAR,
    IN weblog_title VARCHAR,
    IN weblog_tagline VARCHAR,
    IN default_skin VARCHAR,
    IN dav_user VARCHAR,
    IN admin_collection VARCHAR := null,
    IN admin_host VARCHAR := null,
    IN tagline_link_url VARCHAR := null,
    IN tagline_link_text VARCHAR := null
  )
{
  declare coll, index_path, dash_path, backup_note varchar;
  declare deploy_result any;

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';

  backup_note := '';
  index_path := coll || 'index.vsp';
  dash_path := coll || 'dashboard.html';

  {
    -- Harmless no-op on every run after the first ("table already exists");
    -- any OTHER failure here just means backups are skipped, not that the
    -- deploy below is blocked.
    declare exit handler for sqlstate '*' { ; };
    exec ('create table DB.DBA.WEBLOG_UPGRADE_BACKUP (WUB_ID INTEGER IDENTITY, WUB_DAV_COLLECTION VARCHAR, WUB_RES_NAME VARCHAR, WUB_RES_CONTENT LONG VARCHAR, WUB_BACKED_UP_AT DATETIME, PRIMARY KEY (WUB_ID))');
  }
  {
    declare _cc any;
    for (select RES_CONTENT as _c from WS.WS.SYS_DAV_RES where RES_FULL_PATH = index_path) do
    {
      _cc := _c;
      {
        declare exit handler for sqlstate '*' { ; };
        exec ('insert into DB.DBA.WEBLOG_UPGRADE_BACKUP (WUB_DAV_COLLECTION, WUB_RES_NAME, WUB_RES_CONTENT, WUB_BACKED_UP_AT) values (?, ?, ?, now ())',
          null, null, vector (coll, 'index.vsp', _cc));
        backup_note := backup_note || 'index.vsp ';
      }
    }
    for (select RES_CONTENT as _c from WS.WS.SYS_DAV_RES where RES_FULL_PATH = dash_path) do
    {
      _cc := _c;
      {
        declare exit handler for sqlstate '*' { ; };
        exec ('insert into DB.DBA.WEBLOG_UPGRADE_BACKUP (WUB_DAV_COLLECTION, WUB_RES_NAME, WUB_RES_CONTENT, WUB_BACKED_UP_AT) values (?, ?, ?, now ())',
          null, null, vector (coll, 'dashboard.html', _cc));
        backup_note := backup_note || 'dashboard.html ';
      }
    }
  }
  if (backup_note = '') backup_note := '(nothing existed yet to back up, or backup failed -- see comments above; the deploy below still runs)';

  deploy_result := DB.DBA.WEBLOG_DAV_DEPLOY_SKINNED (coll, public_route, weblog_title, weblog_tagline, default_skin, dav_user, admin_collection, admin_host, null, tagline_link_url, tagline_link_text);

  -- WEBLOG_DAV_DEPLOY_SKINNED records weblog:adminDavUser and the other
  -- weblog:* properties itself, refreshes dashboard.html, and reports the
  -- refresh outcome in its "dashboard" field -- nothing to repeat here.
  return sprintf ('{"pre_flight_backup":"%s","deploy":%s}', backup_note, deploy_result);
}
;
-- Force this CREATE PROCEDURE durably visible before the next statement
-- compiles a reference to it -- some SQL client/transaction configurations
-- (verified live 2026-09-23 against a real remote instance) leave a
-- freshly created object showing up in the catalog (SYS_PROCEDURES/SYS_COLS)
-- immediately, but not yet actually resolvable/callable by an immediately
-- following statement without an explicit commit forcing full visibility.
commit work;

-- Auto-detects WHICH known site this connected Virtuoso instance is, so the
-- whole file can be run as-is against any of them without hand-editing
-- placeholders first. Detection signal: which known DAV_COLLECTION already
-- has an index.vsp deployed on THIS instance -- each Virtuoso instance has
-- its own siloed DAV tree, so finding a known path's index.vsp here
-- unambiguously identifies which site this session is connected to (no
-- reliance on any config value like URIQA DefaultHost, which may not be
-- customized per-instance). Never guesses: an instance matching none of the
-- known paths (a genuinely new site, a typo below, or a first-ever install
-- with nothing deployed yet) gets a clear diagnostic instead of a deploy --
-- add a new "else if" branch here for a new site, or call
-- DB.DBA.WEBLOG_DAV_DEPLOY_SKINNED directly with explicit parameters for a
-- first-ever install this can't detect.
create procedure DB.DBA.TMP_WEBLOG_UPGRADE_AUTODETECT ()
{
  declare coll, title, tagline, skin, dav_user, admin_coll, host varchar;
  declare tagline_link_url, tagline_link_text varchar;
  declare site_found int;
  site_found := 0;
  tagline := 'A configurable, skinnable weblog view of a WebDAV folder.';
  skin := 'classic';
  dav_user := 'dba';
  -- null = recorded weblog:adminCollection, else aunt/uncle default (see
  -- ADMIN DASHBOARD LOCATION above); set per site below to override.
  admin_coll := null;
  -- null = no extra link appended to the visible tagline; set per site
  -- below for a site that wants one (see TAGLINE LINK above).
  tagline_link_url := null;
  tagline_link_text := null;

  if ((select count (*) from WS.WS.SYS_DAV_RES where RES_FULL_PATH = '/DAV/home/demo/Public/fifa-kg/index.vsp') > 0)
  {
    site_found := 1;
    coll := '/DAV/home/demo/Public/fifa-kg/';
    title := 'FIFA Knowledge Graph Weblog';
    host := 'demo.openlinksw.com';
  }
  else if ((select count (*) from WS.WS.SYS_DAV_RES where RES_FULL_PATH = '/DAV/demos/daas/index.vsp') > 0)
  {
    site_found := 1;
    coll := '/DAV/demos/daas/';
    title := 'URIBurner DaaS Weblog';
    host := 'linkeddata.uriburner.com';
    -- UB's actual privileged SQL/DAV account is kidehen, not dba (confirmed
    -- live 2026-09-23) -- WEBLOG_DAV_DEPLOY_SKINNED resolves dav_user's
    -- password hash via pwd_magic_calc to record the weblog:* collection
    -- properties (publicRoute, actionRoute, adminCollection, ...); that step
    -- silently no-ops if dav_user doesn't resolve.
    dav_user := 'kidehen';
    tagline_link_url := coll;
    tagline_link_text := 'WebDAV folder';
  }
  else if ((select count (*) from WS.WS.SYS_DAV_RES where RES_FULL_PATH = '/DAV/www2.openlinksw.com/data/html/index.vsp') > 0)
  {
    site_found := 1;
    coll := '/DAV/www2.openlinksw.com/data/html/';
    title := 'OpenLink Software Weblog';
    host := 'www.openlinksw.com';
  }

  if (site_found = 0)
    return '{"ok":false,"reason":"No known site detected on this instance -- checked /DAV/home/demo/Public/fifa-kg/, /DAV/demos/daas/, and /DAV/www2.openlinksw.com/data/html/ for an existing index.vsp and found none. This is either a first-ever install (nothing deployed yet, so there is nothing to auto-detect from) or a site not yet registered in this procedure -- add an else-if branch above for a new site, or call DB.DBA.WEBLOG_DAV_DEPLOY_SKINNED directly with explicit parameters."}';

  return DB.DBA.TMP_WEBLOG_UPGRADE_APPLY (coll, '/weblog/', title, tagline, skin, dav_user, admin_coll, host, tagline_link_url, tagline_link_text);
}
;
-- Same reasoning as the commit work; above this procedure -- force full
-- visibility before the call below.
commit work;
select DB.DBA.TMP_WEBLOG_UPGRADE_AUTODETECT ();
drop procedure DB.DBA.TMP_WEBLOG_UPGRADE_AUTODETECT;
drop procedure DB.DBA.TMP_WEBLOG_UPGRADE_APPLY;
