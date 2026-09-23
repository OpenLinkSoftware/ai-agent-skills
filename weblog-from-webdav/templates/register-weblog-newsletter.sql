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
  email := trim (email);
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
  email := trim (email);
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
  declare coll, admin_user, dash_rows, html VARCHAR;
  declare dash_total, dash_pending, dash_confirmed, dash_unsubscribed INTEGER;
  declare stream any;
  declare rc any;
  declare admin_token, public_route, current_mode, current_content_mode, current_skin, controls_html, import_html VARCHAR;
  declare current_interval INTEGER;
  declare current_from_name, current_from_addr, current_smtp_override, current_base_url, current_admin_email, resolved_smtp, email_config_html VARCHAR;
  declare digest_scheduled, dash_scheduled INTEGER;
  declare dash_interval INTEGER;
  declare tag_schedule_html VARCHAR;

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';
  admin_user := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:adminDavUser', 'dba');
  admin_token := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:adminActionToken', '');
  public_route := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:publicRoute', coll);
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
    if (_s = 'unsubscribed' or admin_token = '')
      action_cell := '--';
    else
      action_cell := sprintf (
        '<form method="post" action="%s" class="row-action"><input type="hidden" name="admin_action" value="admin_unsubscribe"/><input type="hidden" name="admin_token" value="%s"/><input type="hidden" name="sub_token" value="%s"/><button type="submit" class="secondary">Unsubscribe</button></form>',
        public_route, admin_token, _tok);
    dash_rows := concat (dash_rows, sprintf (
      '<tr><td>%V</td><td>%V</td><td><span class="badge %s">%V</span></td><td>%V</td><td>%V</td><td>%V</td><td>%s</td></tr>',
      coalesce (_n, '--'), _e, _s, _s, cast (_sub as varchar), coalesce (cast (_conf as varchar), '--'), coalesce (cast (_sent as varchar), '--'), action_cell));
  }

  -- Action forms post to the PUBLIC route's ?admin_action= dispatcher (the
  -- one thing on this static, Digest-gated page that is NOT static): the
  -- token embedded here is only ever visible to someone who already passed
  -- native Digest auth to load this very page.
  if (admin_token = '')
  {
    controls_html := '<section class="panel"><p class="admin-note">Admin actions are unavailable: weblog:adminActionToken is not set on this collection yet (it should be generated automatically on the next deploy).</p></section>';
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
      public_route, admin_token,
      current_mode, public_route, admin_token, case when current_mode = 'digest' then ' selected="selected"' else '' end, case when current_mode = 'immediate' then ' selected="selected"' else '' end,
      current_content_mode, public_route, admin_token, case when current_content_mode = 'auto' then ' selected="selected"' else '' end, case when current_content_mode = 'snippet' then ' selected="selected"' else '' end, case when current_content_mode = 'full' then ' selected="selected"' else '' end,
      current_skin, public_route, admin_token, case when current_skin = 'classic' then ' selected="selected"' else '' end, case when current_skin = 'editorial' then ' selected="selected"' else '' end);
  }

  -- Sender identity, SMTP relay override, and the base URL used to build
  -- every absolute link in an email -- previously only settable via a raw
  -- DAV_PROP_SET call. resolved_smtp shows what WEBLOG_NEWSLETTER_RESOLVE_SMTP
  -- actually picks when the override is blank, so the admin isn't guessing.
  email_config_html := '';
  if (admin_token <> '')
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
      public_route, admin_token, current_from_name, current_from_addr, current_admin_email, current_smtp_override, current_base_url, resolved_smtp);
  }

  -- Admin-only bulk onboarding: imported rows land 'confirmed' immediately
  -- (the admin is vouching for the list) and each gets an activation-notice
  -- email with an unsubscribe link -- see WEBLOG_NEWSLETTER_IMPORT_ONE.
  -- Two separate forms (CSV vs RDF) since they need different fields
  -- (a format selector for RDF) and mixing file inputs of different
  -- purposes into one multipart form invites uploading the wrong kind.
  import_html := '';
  if (admin_token <> '')
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
      public_route, admin_token,
      public_route, admin_token,
      public_route, admin_token, manual_rows_html);
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
  if (admin_token <> '')
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
        public_route, admin_token, _rname, coalesce (_cat, ''),
        public_route, admin_token, _rname, _pin_target, _pin_label));
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
      digest_status_class, digest_status_text, public_route, admin_token, case when digest_scheduled = 1 then ' selected="selected"' else '' end, case when digest_scheduled = 0 then ' selected="selected"' else '' end, current_interval,
      dash_status_class, dash_status_text, public_route, admin_token, case when dash_scheduled = 1 then ' selected="selected"' else '' end, case when dash_scheduled = 0 then ' selected="selected"' else '' end, dash_interval);
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
  -- Owner stays 'dav' for consistency with every other upload in this skill;
  -- group is the admin account itself, verified live to resolve RES_GROUP
  -- to that account's own U_GROUP -- this is what the 401/200 Digest gate
  -- actually checks against, not RES_OWNER.
  rc := DB.DBA.DAV_RES_UPLOAD_STRSES_INT (coll || 'dashboard.html', stream, 'text/html', '111100000R', 'dav', admin_user, null, null, 0);
  if (rc < 0)
    signal ('42000', sprintf ('DAV upload failed for dashboard.html, rc=%d', rc));
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
-- (default 'dba'); only requests that Digest-authenticate as this account
-- can read the admin route.
-- SELECT DB.DBA.DAV_PROP_SET ('/DAV/home/dba/weblog-test/', 'weblog:adminDavUser', 'dba', 'dba', (SELECT pwd_magic_calc (U_NAME, U_PASSWORD, 1) FROM DB.DBA.SYS_USERS WHERE U_NAME = 'dba'), 1);
