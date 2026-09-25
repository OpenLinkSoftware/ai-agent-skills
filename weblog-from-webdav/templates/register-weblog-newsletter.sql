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

-- Shared template renderer for every editable outbound-email subject/body.
-- Reads a weblog:* property (falling back to default_text when unset --
-- every email keeps working exactly as before until an admin explicitly
-- customizes it), then substitutes each {{TOKEN}} in replacements
-- (a flat vector: token, value, token, value, ...) via plain string
-- replace(). No markdown/HTML interpretation -- a template used in a
-- text/plain body stays plain text, one used in an HTML body can contain
-- real HTML exactly as the surrounding code already does.
CREATE PROCEDURE DB.DBA.WEBLOG_RENDER_EMAIL_TEMPLATE (IN dav_collection VARCHAR, IN prop_name VARCHAR, IN default_text VARCHAR, IN replacements ANY)
{
  declare coll, text_out VARCHAR;
  declare i INTEGER;
  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';
  text_out := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, prop_name, default_text);
  if (text_out is null or text_out = '') text_out := default_text;
  for (i := 0; i < length (replacements); i := i + 2)
    text_out := replace (text_out, replacements[i], cast (replacements[i + 1] as varchar));
  return text_out;
}
;

-- Every template that references a placeholder marked required below must
-- actually contain it, or the resulting email would be missing something
-- essential (a confirm link with no link is not a confirmation email).
-- Returns '' when valid, else a message naming the missing token(s) --
-- checked before ANY weblog:emailSubject*/emailBody* property is written.
CREATE PROCEDURE DB.DBA.WEBLOG_CHECK_EMAIL_TEMPLATE_TOKENS (IN text_in VARCHAR, IN required_tokens ANY)
{
  declare i INTEGER;
  declare missing VARCHAR;
  missing := '';
  for (i := 0; i < length (required_tokens); i := i + 1)
    if (strstr (text_in, required_tokens[i]) is null)
      missing := missing || required_tokens[i] || ' ';
  if (missing = '') return '';
  return sprintf ('missing required placeholder(s): %s', trim (missing));
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

  subj := DB.DBA.WEBLOG_RENDER_EMAIL_TEMPLATE (coll, 'weblog:emailSubjectAdminAlert',
    '{{WEBLOG_TITLE}} admin: {{SUBJECT_SUFFIX}}', vector ('{{WEBLOG_TITLE}}', from_name, '{{SUBJECT_SUFFIX}}', subject_suffix));
  msg := sprintf ('Date: %s\r\nSubject: %s\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n%s\r\n', date_rfc1123 (now ()), subj, body_text);

  smtp_send (smtp_server, sprintf ('%s <%s>', from_name, from_addr), admin_email, msg);
  return 1;
}
;

-- Best-effort dashboard refresh: subscribe/confirm/unsubscribe all change
-- what the admin dashboard shows, but happen from the PUBLIC route with no
-- admin present to trigger one -- unlike every admin_action, which already
-- refreshes the dashboard on its way back. Without this, a real confirmed
-- subscriber can sit invisible on a dashboard.html snapshot from whenever
-- it was last regenerated (confirmed live: a subscriber confirmed hours
-- earlier, with no scheduled auto-refresh configured, still showed as 0
-- subscribers on the dashboard). Never blocks the subscriber-facing action
-- itself if the refresh fails or the dashboard proc isn't installed.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_TRY_DASHBOARD_REFRESH (IN dav_collection VARCHAR)
{
  declare exit handler for sqlstate '*' { ; };
  if ((select count (*) from DB.DBA.SYS_PROCEDURES where P_NAME = 'DB.DBA.WEBLOG_DASHBOARD_REFRESH') > 0)
    DB.DBA.WEBLOG_DASHBOARD_REFRESH (dav_collection);
}
;

-- ==========================================================================
-- Country list for the subscribe form and for normalizing stored/imported
-- countries. WS_COUNTRY holds an ISO 3166-1 alpha-2 code (the value
-- schema:addressCountry expects), never free text. Generated from the tz
-- database's iso3166.tab (249 entries), with a few names changed to
-- their more familiar form (GB, BQ, KP, KR, UM). Names are HTML-escaped and
-- ASCII-only (&#244; etc.), so they can be emitted with %s from any context
-- -- see WEBLOG_HTML_ESC_BYTES for why %V is avoided for non-ASCII here.
-- ==========================================================================

-- vector (code, name_html, code, name_html, ...), sorted by name.
CREATE PROCEDURE DB.DBA.WEBLOG_COUNTRY_LIST ()
{
  return vector (
    'AF', 'Afghanistan',
    'AX', '&#197;land Islands',
    'AL', 'Albania',
    'DZ', 'Algeria',
    'AD', 'Andorra',
    'AO', 'Angola',
    'AI', 'Anguilla',
    'AQ', 'Antarctica',
    'AG', 'Antigua &amp; Barbuda',
    'AR', 'Argentina',
    'AM', 'Armenia',
    'AW', 'Aruba',
    'AU', 'Australia',
    'AT', 'Austria',
    'AZ', 'Azerbaijan',
    'BS', 'Bahamas',
    'BH', 'Bahrain',
    'BD', 'Bangladesh',
    'BB', 'Barbados',
    'BY', 'Belarus',
    'BE', 'Belgium',
    'BZ', 'Belize',
    'BJ', 'Benin',
    'BM', 'Bermuda',
    'BT', 'Bhutan',
    'BO', 'Bolivia',
    'BA', 'Bosnia &amp; Herzegovina',
    'BW', 'Botswana',
    'BV', 'Bouvet Island',
    'BR', 'Brazil',
    'IO', 'British Indian Ocean Territory',
    'BN', 'Brunei',
    'BG', 'Bulgaria',
    'BF', 'Burkina Faso',
    'BI', 'Burundi',
    'KH', 'Cambodia',
    'CM', 'Cameroon',
    'CA', 'Canada',
    'CV', 'Cape Verde',
    'BQ', 'Caribbean Netherlands',
    'KY', 'Cayman Islands',
    'CF', 'Central African Rep.',
    'TD', 'Chad',
    'CL', 'Chile',
    'CN', 'China',
    'CX', 'Christmas Island',
    'CC', 'Cocos (Keeling) Islands',
    'CO', 'Colombia',
    'KM', 'Comoros',
    'CD', 'Congo (Dem. Rep.)',
    'CG', 'Congo (Rep.)',
    'CK', 'Cook Islands',
    'CR', 'Costa Rica',
    'CI', 'C&#244;te d&#8217;Ivoire',
    'HR', 'Croatia',
    'CU', 'Cuba',
    'CW', 'Cura&#231;ao',
    'CY', 'Cyprus',
    'CZ', 'Czech Republic',
    'DK', 'Denmark',
    'DJ', 'Djibouti',
    'DM', 'Dominica',
    'DO', 'Dominican Republic',
    'TL', 'East Timor',
    'EC', 'Ecuador',
    'EG', 'Egypt',
    'SV', 'El Salvador',
    'GQ', 'Equatorial Guinea',
    'ER', 'Eritrea',
    'EE', 'Estonia',
    'SZ', 'Eswatini (Swaziland)',
    'ET', 'Ethiopia',
    'FK', 'Falkland Islands',
    'FO', 'Faroe Islands',
    'FJ', 'Fiji',
    'FI', 'Finland',
    'FR', 'France',
    'GF', 'French Guiana',
    'PF', 'French Polynesia',
    'TF', 'French S. Terr.',
    'GA', 'Gabon',
    'GM', 'Gambia',
    'GE', 'Georgia',
    'DE', 'Germany',
    'GH', 'Ghana',
    'GI', 'Gibraltar',
    'GR', 'Greece',
    'GL', 'Greenland',
    'GD', 'Grenada',
    'GP', 'Guadeloupe',
    'GU', 'Guam',
    'GT', 'Guatemala',
    'GG', 'Guernsey',
    'GN', 'Guinea',
    'GW', 'Guinea-Bissau',
    'GY', 'Guyana',
    'HT', 'Haiti',
    'HM', 'Heard Island &amp; McDonald Islands',
    'HN', 'Honduras',
    'HK', 'Hong Kong',
    'HU', 'Hungary',
    'IS', 'Iceland',
    'IN', 'India',
    'ID', 'Indonesia',
    'IR', 'Iran',
    'IQ', 'Iraq',
    'IE', 'Ireland',
    'IM', 'Isle of Man',
    'IL', 'Israel',
    'IT', 'Italy',
    'JM', 'Jamaica',
    'JP', 'Japan',
    'JE', 'Jersey',
    'JO', 'Jordan',
    'KZ', 'Kazakhstan',
    'KE', 'Kenya',
    'KI', 'Kiribati',
    'KW', 'Kuwait',
    'KG', 'Kyrgyzstan',
    'LA', 'Laos',
    'LV', 'Latvia',
    'LB', 'Lebanon',
    'LS', 'Lesotho',
    'LR', 'Liberia',
    'LY', 'Libya',
    'LI', 'Liechtenstein',
    'LT', 'Lithuania',
    'LU', 'Luxembourg',
    'MO', 'Macau',
    'MG', 'Madagascar',
    'MW', 'Malawi',
    'MY', 'Malaysia',
    'MV', 'Maldives',
    'ML', 'Mali',
    'MT', 'Malta',
    'MH', 'Marshall Islands',
    'MQ', 'Martinique',
    'MR', 'Mauritania',
    'MU', 'Mauritius',
    'YT', 'Mayotte',
    'MX', 'Mexico',
    'FM', 'Micronesia',
    'MD', 'Moldova',
    'MC', 'Monaco',
    'MN', 'Mongolia',
    'ME', 'Montenegro',
    'MS', 'Montserrat',
    'MA', 'Morocco',
    'MZ', 'Mozambique',
    'MM', 'Myanmar (Burma)',
    'NA', 'Namibia',
    'NR', 'Nauru',
    'NP', 'Nepal',
    'NL', 'Netherlands',
    'NC', 'New Caledonia',
    'NZ', 'New Zealand',
    'NI', 'Nicaragua',
    'NE', 'Niger',
    'NG', 'Nigeria',
    'NU', 'Niue',
    'NF', 'Norfolk Island',
    'KP', 'North Korea',
    'MK', 'North Macedonia',
    'MP', 'Northern Mariana Islands',
    'NO', 'Norway',
    'OM', 'Oman',
    'PK', 'Pakistan',
    'PW', 'Palau',
    'PS', 'Palestine',
    'PA', 'Panama',
    'PG', 'Papua New Guinea',
    'PY', 'Paraguay',
    'PE', 'Peru',
    'PH', 'Philippines',
    'PN', 'Pitcairn',
    'PL', 'Poland',
    'PT', 'Portugal',
    'PR', 'Puerto Rico',
    'QA', 'Qatar',
    'RE', 'R&#233;union',
    'RO', 'Romania',
    'RU', 'Russia',
    'RW', 'Rwanda',
    'AS', 'Samoa (American)',
    'WS', 'Samoa (western)',
    'SM', 'San Marino',
    'ST', 'Sao Tome &amp; Principe',
    'SA', 'Saudi Arabia',
    'SN', 'Senegal',
    'RS', 'Serbia',
    'SC', 'Seychelles',
    'SL', 'Sierra Leone',
    'SG', 'Singapore',
    'SK', 'Slovakia',
    'SI', 'Slovenia',
    'SB', 'Solomon Islands',
    'SO', 'Somalia',
    'ZA', 'South Africa',
    'GS', 'South Georgia &amp; the South Sandwich Islands',
    'KR', 'South Korea',
    'SS', 'South Sudan',
    'ES', 'Spain',
    'LK', 'Sri Lanka',
    'BL', 'St Barthelemy',
    'SH', 'St Helena',
    'KN', 'St Kitts &amp; Nevis',
    'LC', 'St Lucia',
    'SX', 'St Maarten (Dutch)',
    'MF', 'St Martin (French)',
    'PM', 'St Pierre &amp; Miquelon',
    'VC', 'St Vincent',
    'SD', 'Sudan',
    'SR', 'Suriname',
    'SJ', 'Svalbard &amp; Jan Mayen',
    'SE', 'Sweden',
    'CH', 'Switzerland',
    'SY', 'Syria',
    'TW', 'Taiwan',
    'TJ', 'Tajikistan',
    'TZ', 'Tanzania',
    'TH', 'Thailand',
    'TG', 'Togo',
    'TK', 'Tokelau',
    'TO', 'Tonga',
    'TT', 'Trinidad &amp; Tobago',
    'TN', 'Tunisia',
    'TR', 'Turkey',
    'TM', 'Turkmenistan',
    'TC', 'Turks &amp; Caicos Is',
    'TV', 'Tuvalu',
    'UM', 'U.S. Minor Outlying Islands',
    'UG', 'Uganda',
    'UA', 'Ukraine',
    'AE', 'United Arab Emirates',
    'GB', 'United Kingdom',
    'US', 'United States',
    'UY', 'Uruguay',
    'UZ', 'Uzbekistan',
    'VU', 'Vanuatu',
    'VA', 'Vatican City',
    'VE', 'Venezuela',
    'VN', 'Vietnam',
    'VG', 'Virgin Islands (UK)',
    'VI', 'Virgin Islands (US)',
    'WF', 'Wallis &amp; Futuna',
    'EH', 'Western Sahara',
    'YE', 'Yemen',
    'ZM', 'Zambia',
    'ZW', 'Zimbabwe');
}
;

-- Display name (HTML-escaped) for a code, or null if it isn't one.
CREATE PROCEDURE DB.DBA.WEBLOG_COUNTRY_NAME_HTML (IN code ANY)
{
  declare cl any;
  declare i int;
  if (code is null or not isstring (code) or length (code) <> 2) return null;
  code := upper (code);
  cl := DB.DBA.WEBLOG_COUNTRY_LIST ();
  for (i := 0; i < length (cl); i := i + 2)
    if (cl[i] = code) return cl[i + 1];
  return null;
}
;

-- Map a submitted or imported country value to its ISO code: accepts the
-- code itself (any case), the listed name, or a common alternative
-- ("UK", "USA", "Ivory Coast", accent-free spellings, ...). Returns null
-- for blank or unrecognized input, so free text is never stored.
CREATE PROCEDURE DB.DBA.WEBLOG_COUNTRY_NORMALIZE (IN val ANY)
{
  declare cl, aliases any;
  declare lkey VARCHAR;
  declare i int;
  if (val is null) return null;
  if (iswidestring (val)) val := charset_recode (val, '_WIDE_', 'UTF-8');
  if (not isstring (val)) return null;
  -- Typographic and straight apostrophes compare equal ("Cote d'Ivoire").
  lkey := replace (lower (trim (val)), concat (chr (226), chr (128), chr (153)), chr (39));
  if (lkey = '') return null;
  cl := DB.DBA.WEBLOG_COUNTRY_LIST ();
  -- Codes first: the cheap, common case (every value once normalized).
  if (length (lkey) = 2)
    for (i := 0; i < length (cl); i := i + 2)
      if (lower (cl[i]) = lkey) return cl[i];
  for (i := 0; i < length (cl); i := i + 2)
    if (replace (lower (DB.DBA.WEBLOG_HTML_UNESCAPE (cl[i + 1])), concat (chr (226), chr (128), chr (153)), chr (39)) = lkey)
      return cl[i];
  aliases := vector (
    'aland islands', 'AX',
    'america', 'US',
    'antigua and barbuda', 'AG',
    'bosnia and herzegovina', 'BA',
    'britain', 'GB',
    'britain (uk)', 'GB',
    'burma', 'MM',
    'cabo verde', 'CV',
    'caribbean nl', 'BQ',
    'cote d''ivoire', 'CI',
    'curacao', 'CW',
    'czechia', 'CZ',
    'democratic republic of the congo', 'CD',
    'dprk', 'KP',
    'dr congo', 'CD',
    'drc', 'CD',
    'eire', 'IE',
    'england', 'GB',
    'great britain', 'GB',
    'heard island and mcdonald islands', 'HM',
    'holland', 'NL',
    'holy see', 'VA',
    'hong kong sar', 'HK',
    'ivory coast', 'CI',
    'korea', 'KR',
    'korea (north)', 'KP',
    'korea (south)', 'KR',
    'macao', 'MO',
    'macau sar', 'MO',
    'mainland china', 'CN',
    'northern ireland', 'GB',
    'palestinian territories', 'PS',
    'prc', 'CN',
    'republic of china', 'TW',
    'republic of ireland', 'IE',
    'republic of korea', 'KR',
    'republic of the congo', 'CG',
    'reunion', 'RE',
    'russian federation', 'RU',
    'saint barthelemy', 'BL',
    'saint helena', 'SH',
    'saint kitts & nevis', 'KN',
    'saint lucia', 'LC',
    'saint maarten (dutch)', 'SX',
    'saint martin (french)', 'MF',
    'saint pierre & miquelon', 'PM',
    'saint vincent', 'VC',
    'sao tome and principe', 'ST',
    'scotland', 'GB',
    'south georgia and the south sandwich islands', 'GS',
    'st kitts and nevis', 'KN',
    'st pierre and miquelon', 'PM',
    'svalbard and jan mayen', 'SJ',
    'swaziland', 'SZ',
    'the netherlands', 'NL',
    'timor-leste', 'TL',
    'trinidad and tobago', 'TT',
    'turkiye', 'TR',
    'turks and caicos is', 'TC',
    'u.k.', 'GB',
    'u.s.', 'US',
    'u.s.a.', 'US',
    'uae', 'AE',
    'uk', 'GB',
    'united states of america', 'US',
    'us minor outlying islands', 'UM',
    'usa', 'US',
    'viet nam', 'VN',
    'wales', 'GB',
    'wallis and futuna', 'WF');
  for (i := 0; i < length (aliases); i := i + 2)
    if (aliases[i] = lkey) return aliases[i + 1];
  return null;
}
;

-- One-time cleanup of free-text countries stored before the drop-down:
-- rewrites every value WEBLOG_COUNTRY_NORMALIZE recognizes to its code,
-- clears blanks, and leaves anything unrecognized untouched (the dashboard
-- shows it as-is) rather than discarding it. Idempotent.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_NORMALIZE_COUNTRIES (IN dav_collection VARCHAR)
{
  declare coll, code VARCHAR;
  declare changed, unrecognized int;
  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';
  changed := 0;
  unrecognized := 0;
  for (select WS_ID as _id, WS_COUNTRY as _c from DB.DBA.WEBLOG_SUBSCRIBER
        where WS_DAV_COLLECTION = coll and WS_COUNTRY is not null) do
  {
    code := DB.DBA.WEBLOG_COUNTRY_NORMALIZE (_c);
    if (code is null)
    {
      if (trim (cast (_c as varchar)) = '')
      {
        update DB.DBA.WEBLOG_SUBSCRIBER set WS_COUNTRY = null where WS_ID = _id;
        changed := changed + 1;
      }
      else
        unrecognized := unrecognized + 1;
    }
    else if (code <> cast (_c as varchar))
    {
      update DB.DBA.WEBLOG_SUBSCRIBER set WS_COUNTRY = code where WS_ID = _id;
      changed := changed + 1;
    }
  }
  return sprintf ('{"changed":%d,"unrecognized":%d}', changed, unrecognized);
}
;

CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_SUBSCRIBE (IN dav_collection VARCHAR, IN email VARCHAR, IN country VARCHAR, IN confirm_base_url VARCHAR)
{
  declare coll, tok, from_addr, from_name, confirm_base, public_route, smtp_server, subj, body, existing_status VARCHAR;
  declare existing_count INTEGER;

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';
  if (email is null) email := '';
  -- ISO code or null: the form posts a code, but this is also the
  -- boundary for any hand-crafted POST, so free text is never stored.
  country := DB.DBA.WEBLOG_COUNTRY_NORMALIZE (country);
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
  DB.DBA.WEBLOG_NEWSLETTER_TRY_DASHBOARD_REFRESH (coll);

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

  {
    declare confirm_url VARCHAR;
    confirm_url := sprintf ('%s%s?nl_action=confirm&token=%s', confirm_base, public_route, tok);
    subj := DB.DBA.WEBLOG_RENDER_EMAIL_TEMPLATE (coll, 'weblog:emailSubjectConfirm',
      '{{WEBLOG_TITLE}}: confirm your subscription', vector ('{{WEBLOG_TITLE}}', from_name));
    body := DB.DBA.WEBLOG_RENDER_EMAIL_TEMPLATE (coll, 'weblog:emailBodyConfirm',
      'Please confirm your subscription by opening this link:\r\n\r\n{{CONFIRM_URL}}\r\n\r\nIf you did not request this, ignore this message -- you will not be subscribed unless you click the link above.\r\n',
      vector ('{{WEBLOG_TITLE}}', from_name, '{{CONFIRM_URL}}', confirm_url));
  }

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
      DB.DBA.WEBLOG_NEWSLETTER_MIME_MESSAGE (subj, bulk_hdrs, body,
        DB.DBA.WEBLOG_NEWSLETTER_HTML_SHELL (subj,
          DB.DBA.WEBLOG_NEWSLETTER_TEXT_TO_HTML ('Confirm your subscription', body,
            sprintf ('%s%s?nl_action=confirm&token=%s', confirm_base, public_route, tok), 'Confirm subscription'),
          from_name, unsub_url, '', sprintf ('One click to confirm your subscription to %s.', from_name),
          concat (confirm_base, public_route),
          DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterPostalAddress', ''))));
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
  DB.DBA.WEBLOG_NEWSLETTER_TRY_DASHBOARD_REFRESH (coll);

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
  DB.DBA.WEBLOG_NEWSLETTER_TRY_DASHBOARD_REFRESH (coll);
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
  subj := DB.DBA.WEBLOG_RENDER_EMAIL_TEMPLATE (coll, 'weblog:emailSubjectUnsubscribeNotice',
    '{{WEBLOG_TITLE}}: you have been unsubscribed', vector ('{{WEBLOG_TITLE}}', from_name));
  body := DB.DBA.WEBLOG_RENDER_EMAIL_TEMPLATE (coll, 'weblog:emailBodyUnsubscribeNotice',
    '{{GREETING}}You have been removed from the {{WEBLOG_TITLE}} mailing list by the site administrator. You will not receive any further digest emails at this address.\r\n\r\nIf this was a mistake, you can subscribe again at any time:\r\n\r\n{{RESUBSCRIBE_URL}}\r\n',
    vector ('{{WEBLOG_TITLE}}', from_name, '{{GREETING}}', greeting, '{{RESUBSCRIBE_URL}}', public_route));
  bulk_hdrs := DB.DBA.WEBLOG_NEWSLETTER_BULK_HEADERS (coll, from_addr, from_name, email, unsub_url);
  msg := DB.DBA.WEBLOG_NEWSLETTER_MIME_MESSAGE (subj, bulk_hdrs, body,
    DB.DBA.WEBLOG_NEWSLETTER_HTML_SHELL (subj,
      DB.DBA.WEBLOG_NEWSLETTER_TEXT_TO_HTML ('You have been unsubscribed', body, null, null),
      from_name, null, '', sprintf ('You will not receive further emails from %s.', from_name),
      null, DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterPostalAddress', '')));

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
  unsub_url := sprintf ('%s%s?nl_action=unsubscribe&token=%s', base_url, public_route, token);
  subj := DB.DBA.WEBLOG_RENDER_EMAIL_TEMPLATE (coll, 'weblog:emailSubjectActivation',
    '{{WEBLOG_TITLE}}: you have been added to our mailing list', vector ('{{WEBLOG_TITLE}}', from_name));
  body := DB.DBA.WEBLOG_RENDER_EMAIL_TEMPLATE (coll, 'weblog:emailBodyActivation',
    '{{GREETING}}You have been added to the {{WEBLOG_TITLE}} mailing list by the site administrator.\r\n\r\nIf you would rather not receive it, you can unsubscribe at any time:\r\n\r\n{{UNSUBSCRIBE_URL}}\r\n\r\nNo action is needed if you would like to stay on the list.\r\n',
    vector ('{{WEBLOG_TITLE}}', from_name, '{{GREETING}}', greeting, '{{UNSUBSCRIBE_URL}}', unsub_url));
  bulk_hdrs := DB.DBA.WEBLOG_NEWSLETTER_BULK_HEADERS (coll, from_addr, from_name, email, unsub_url);
  msg := DB.DBA.WEBLOG_NEWSLETTER_MIME_MESSAGE (subj, bulk_hdrs, body,
    DB.DBA.WEBLOG_NEWSLETTER_HTML_SHELL (subj,
      DB.DBA.WEBLOG_NEWSLETTER_TEXT_TO_HTML (concat ('Welcome to ', from_name), body,
        concat (base_url, public_route), 'Visit the weblog'),
      from_name, unsub_url, '', sprintf ('You have been added to the %s mailing list.', from_name),
      concat (base_url, public_route),
      DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterPostalAddress', '')));

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
  -- CSV/RDF imports may carry a code or a name; store the ISO code or null.
  country := DB.DBA.WEBLOG_COUNTRY_NORMALIZE (country);
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
  -- Plain text, every character reference decoded (&#x27; included):
  -- the card HTML-escapes it and the Subject header RFC 2047-encodes it.
  t := DB.DBA.WEBLOG_HTML_UNESCAPE (t);
  -- Same stored-title repair the weblog itself applies (deploy-weblog-skinned.sql).
  t := DB.DBA.WEBLOG_FIX_MOJIBAKE (t);
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
    frag := DB.DBA.WEBLOG_NEWSLETTER_CLOSE_OPEN_TAGS (frag);
  }

  return vector (frag, extra_css);
}
;

-- ==========================================================================
-- Email rendering: a newsletter layout in the style Substack sends, built
-- for mail clients rather than browsers -- a centered 600px table layout,
-- inline styles on every element (the post's own stylesheet can't
-- override them), a hidden preview line (preheader), a masthead, title /
-- subtitle / byline, table-based buttons that render in Outlook, and a
-- footer with unsubscribe + optional postal address.
--
-- Every message is multipart/alternative (plain text + HTML), with each
-- part base64-encoded: SMTP limits lines to 998 bytes, and an inlined post
-- body easily exceeds that on a single line.
-- ==========================================================================

-- RFC 2047 encoded-word for a header value containing non-ASCII bytes
-- (e.g. an em dash or accented letter in a post title used as Subject).
CREATE PROCEDURE DB.DBA.WEBLOG_MIME_HEADER_TEXT (IN s VARCHAR)
{
  declare i int;
  if (s is null) return '';
  for (i := 0; i < length (s); i := i + 1)
    if (s[i] > 127)
      return sprintf ('=?UTF-8?B?%s?=', replace (replace (encode_base64 (s), '\r', ''), '\n', ''));
  return s;
}
;

-- Base64 body with CRLF line breaks every 76 characters (RFC 2045).
CREATE PROCEDURE DB.DBA.WEBLOG_MIME_BASE64 (IN s VARCHAR)
{
  declare b64 VARCHAR;
  declare ses any;
  declare i, n int;
  b64 := replace (replace (encode_base64 (coalesce (s, '')), '\r', ''), '\n', '');
  ses := string_output ();
  n := length (b64);
  for (i := 0; i < n; i := i + 76)
  {
    http (subseq (b64, i, case when i + 76 < n then i + 76 else n end), ses);
    http ('\r\n', ses);
  }
  return string_output_string (ses);
}
;

-- A complete message: Date, Subject, the caller's bulk headers
-- (Message-ID, List-*, Reply-To ...), then a multipart/alternative body.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_MIME_MESSAGE (IN subj VARCHAR, IN bulk_hdrs VARCHAR, IN text_body VARCHAR, IN html_body VARCHAR)
{
  declare boundary VARCHAR;
  boundary := sprintf ('=_weblog_%s', md5 (concat (cast (now () as varchar), cast (rnd (1000000000) as varchar))));
  return concat (
    sprintf ('Date: %s\r\nSubject: %s\r\n', date_rfc1123 (now ()), DB.DBA.WEBLOG_MIME_HEADER_TEXT (subj)),
    coalesce (bulk_hdrs, ''),
    'MIME-Version: 1.0\r\n',
    sprintf ('Content-Type: multipart/alternative; boundary="%s"\r\n\r\n', boundary),
    'This is a multi-part message in MIME format.\r\n\r\n',
    sprintf ('--%s\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n', boundary),
    DB.DBA.WEBLOG_MIME_BASE64 (text_body),
    sprintf ('\r\n--%s\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n', boundary),
    DB.DBA.WEBLOG_MIME_BASE64 (html_body),
    sprintf ('\r\n--%s--\r\n', boundary));
}
;

-- Table-based ("bulletproof") button: renders as a filled button in
-- Outlook, Gmail and Apple Mail alike. url and label are escaped here.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_BUTTON (IN url VARCHAR, IN label VARCHAR)
{
  return concat (
    '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:28px auto 8px auto"><tr>',
    '<td align="center" bgcolor="#1f4e79" style="border-radius:6px;background:#1f4e79">',
    '<a href="', DB.DBA.WEBLOG_HTML_ESC_BYTES (url), '" target="_blank" style="display:inline-block;padding:13px 28px;font-family:Helvetica,Arial,sans-serif;font-size:15px;font-weight:bold;line-height:1.2;color:#ffffff;text-decoration:none;border-radius:6px">',
    DB.DBA.WEBLOG_HTML_ESC_BYTES (label), '</a></td></tr></table>');
}
;

-- HTML body for a short transactional message (confirm / activation /
-- unsubscribe notice) from its admin-editable plain-text template: the
-- text is escaped, blank lines become paragraphs, and the line holding the
-- primary link becomes a button (the link stays visible below it as text,
-- for clients that block buttons or readers who want to copy it).
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_TEXT_TO_HTML (IN heading VARCHAR, IN txt VARCHAR, IN button_url VARCHAR, IN button_label VARCHAR)
{
  declare paras any;
  declare out_html, p, esc_url VARCHAR;
  declare i, button_done int;
  button_done := 0;
  txt := replace (coalesce (txt, ''), '\r\n', '\n');
  paras := split_and_decode (txt, 0, '\0\0\n');
  out_html := concat ('<h1 style="margin:0 0 18px 0;font-family:Georgia,''Times New Roman'',serif;font-size:26px;line-height:1.25;font-weight:bold;color:#111111">',
    DB.DBA.WEBLOG_HTML_ESC_BYTES (heading), '</h1>');
  esc_url := case when button_url is null then null else DB.DBA.WEBLOG_HTML_ESC_BYTES (button_url) end;
  p := '';
  -- Group consecutive non-blank lines into one paragraph.
  for (i := 0; i <= length (paras); i := i + 1)
  {
    declare line VARCHAR;
    line := case when i < length (paras) then trim (paras[i]) else '' end;
    if (line <> '')
    {
      if (button_url is not null and line = button_url)
      {
        if (p <> '')
          out_html := concat (out_html, '<p style="margin:0 0 16px 0;font-family:Helvetica,Arial,sans-serif;font-size:16px;line-height:1.6;color:#333333">', p, '</p>');
        p := '';
        out_html := concat (out_html, DB.DBA.WEBLOG_NEWSLETTER_BUTTON (button_url, button_label),
          '<p style="margin:0 0 20px 0;text-align:center;font-family:Helvetica,Arial,sans-serif;font-size:12px;line-height:1.5;color:#8a8a8a;word-break:break-all">',
          'Or open this link: <a href="', esc_url, '" style="color:#8a8a8a">', esc_url, '</a></p>');
        button_done := 1;
      }
      else if ((line like 'http://%' or line like 'https://%') and strchr (line, ' ') is null)
        -- Any other bare URL line (e.g. an unsubscribe link) becomes a link.
        p := concat (p, case when p = '' then '' else '<br>' end, '<a href="', DB.DBA.WEBLOG_HTML_ESC_BYTES (line),
          '" style="color:#1f4e79;word-break:break-all">', DB.DBA.WEBLOG_HTML_ESC_BYTES (line), '</a>');
      else
        p := concat (p, case when p = '' then '' else '<br>' end, DB.DBA.WEBLOG_HTML_ESC_BYTES (line));
    }
    else if (p <> '')
    {
      out_html := concat (out_html, '<p style="margin:0 0 16px 0;font-family:Helvetica,Arial,sans-serif;font-size:16px;line-height:1.6;color:#333333">', p, '</p>');
      p := '';
    }
  }
  -- An admin-edited template may not put the link on a line of its own;
  -- the button still goes at the end so the action is never missing.
  if (button_url is not null and button_done = 0)
    out_html := concat (out_html, DB.DBA.WEBLOG_NEWSLETTER_BUTTON (button_url, button_label));
  return out_html;
}
;

-- Close every element a truncated HTML fragment leaves open. The digest
-- cuts each post body at a length limit (on a tag boundary), which can
-- leave e.g. a display:none container open -- and then everything after
-- it in the email (later posts, the footer with Unsubscribe) is hidden
-- too (caught locally 2026-09-25 with a comparison-table view). Also
-- terminates an unclosed comment and drops a trailing partial tag.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_CLOSE_OPEN_TAGS (IN frag VARCHAR)
{
  declare lc, tag, tname, closing VARCHAR;
  declare stack, voids any;
  declare i, p, gt, e, k, guard int;
  if (frag is null or frag = '') return frag;
  voids := vector ('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr');
  stack := vector ();
  lc := lower (frag);
  i := 0;
  guard := 0;
  while (guard < 100000)
  {
    guard := guard + 1;
    p := strstr (subseq (lc, i), '<');
    if (p is null) goto done;
    p := p + i;
    if (subseq (lc, p, case when p + 4 < length (lc) then p + 4 else length (lc) end) = '<!--')
    {
      e := strstr (subseq (lc, p + 4), '-->');
      if (e is null)
      {
        frag := concat (frag, '-->');
        goto done;
      }
      i := p + 4 + e + 3;
    }
    else
    {
      gt := strstr (subseq (lc, p), '>');
      if (gt is null)
      {
        -- A tag cut in half: drop it.
        frag := subseq (frag, 0, p);
        goto done;
      }
      tag := subseq (lc, p + 1, p + gt);
      if (subseq (tag, 0, 1) = '/')
      {
        tname := regexp_substr ('^[a-z0-9]+', subseq (tag, 1), 0);
        -- Pop back to the matching open element, if there is one.
        for (k := length (stack) - 1; k >= 0; k := k - 1)
          if (stack[k] = tname)
          {
            stack := subseq (stack, 0, k);
            k := -1;
          }
      }
      else if (subseq (tag, 0, 1) <> '!' and subseq (tag, 0, 1) <> '?')
      {
        tname := regexp_substr ('^[a-z0-9]+', tag, 0);
        if (tname is not null and position (tname, voids) = 0 and subseq (trim (tag), length (trim (tag)) - 1) <> '/')
          stack := vector_concat (stack, vector (tname));
      }
      i := p + gt + 1;
    }
  }
done:
  closing := '';
  for (k := length (stack) - 1; k >= 0; k := k - 1)
    closing := concat (closing, '</', stack[k], '>');
  return concat (frag, closing);
}
;

-- Subtitle and reading time for one post. The subtitle is the page's own
-- <meta name="description"> (or og:description), returned both as safe
-- HTML and as plain text; reading time is visible words / 230, min 1.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_POST_META (IN dav_collection VARCHAR, IN filename VARCHAR)
{
  declare coll, content, lc, head, tag, val, txt VARCHAR;
  declare p, s, e, c, words int;
  declare exit handler for sqlstate '*' { return vector ('', '', 0); };
  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';
  content := '';
  for (select blob_to_string (RES_CONTENT) as _c from WS.WS.SYS_DAV_RES where RES_FULL_PATH = coll || filename) do
  {
    content := _c;
  }
  if (content is null or content = '') return vector ('', '', 0);
  lc := lower (content);
  val := '';
  p := strstr (lc, 'name="description"');
  if (p is null) p := strstr (lc, 'property="og:description"');
  if (p is not null)
  {
    s := strrchr (subseq (lc, 0, p), '<');
    e := strstr (subseq (lc, p), '>');
    if (s is not null and e is not null)
    {
      tag := subseq (content, s, p + e);
      c := strstr (lower (tag), 'content="');
      if (c is not null)
      {
        e := strstr (subseq (tag, c + 9), '"');
        if (e is not null) val := DB.DBA.WEBLOG_HTML_UNESCAPE (trim (subseq (tag, c + 9, c + 9 + e)));
      }
    }
  }
  -- Reading time from the visible text only.
  txt := content;
  p := strstr (lc, '<body');
  if (p is not null) txt := subseq (content, p);
  txt := DB.DBA.WEBLOG_NEWSLETTER_STRIP_BLOCK (txt, '<script', '</script>');
  txt := DB.DBA.WEBLOG_NEWSLETTER_STRIP_BLOCK (txt, '<style', '</style>');
  txt := regexp_replace (txt, '<[^>]*>', ' ', 1, null);
  txt := regexp_replace (txt, '[ \t\r\n]+', ' ', 1, null);
  words := length (txt) - length (replace (txt, ' ', ''));
  return vector (DB.DBA.WEBLOG_HTML_ESC_BYTES (val), val, case when words < 230 then 1 else words / 230 end);
}
;

-- One post, laid out like a Substack issue: linked title, subtitle, a
-- byline row (publication, date, reading time) between hairlines, a
-- "Read online" link, the post body, then a button to the full post.
-- title_html / subtitle_html must already be HTML-safe; byline is plain
-- text and is escaped here.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_POST_CARD (IN title_html VARCHAR, IN url VARCHAR, IN excerpt_html VARCHAR, IN subtitle_html VARCHAR := '', IN byline VARCHAR := '')
{
  declare esc_url VARCHAR;
  esc_url := DB.DBA.WEBLOG_HTML_ESC_BYTES (url);
  return concat (
    '<div style="margin:0 0 8px 0">',
    '<h1 class="wl-title" style="margin:0 0 10px 0;font-family:Georgia,''Times New Roman'',serif;font-size:32px;line-height:1.2;font-weight:bold;color:#111111">',
    '<a href="', esc_url, '" target="_blank" style="color:#111111;text-decoration:none">', title_html, '</a></h1>',
    case when coalesce (subtitle_html, '') = '' then '' else concat (
      '<p style="margin:0 0 20px 0;font-family:Helvetica,Arial,sans-serif;font-size:18px;line-height:1.45;color:#6b6b6b">', subtitle_html, '</p>') end,
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-top:1px solid #e6e6e6;border-bottom:1px solid #e6e6e6;margin:0 0 26px 0"><tr>',
    '<td style="padding:11px 0;font-family:Helvetica,Arial,sans-serif;font-size:13px;line-height:1.4;color:#6b6b6b">', DB.DBA.WEBLOG_HTML_ESC_BYTES (coalesce (byline, '')), '</td>',
    '<td align="right" style="padding:11px 0;font-family:Helvetica,Arial,sans-serif;font-size:13px;line-height:1.4;white-space:nowrap">',
    '<a href="', esc_url, '" target="_blank" style="color:#1f4e79;text-decoration:none;font-weight:bold">Read online</a></td>',
    '</tr></table>',
    '<div class="wl-body" style="font-family:Georgia,''Times New Roman'',serif;font-size:17px;line-height:1.7;color:#222222">',
    -- In full-content mode the post body starts with its own <h1>, which
    -- would repeat the title directly above it.
    DB.DBA.WEBLOG_NEWSLETTER_STRIP_ELEMENT (coalesce (excerpt_html, ''), '<h1', 'h1'), '</div>',
    DB.DBA.WEBLOG_NEWSLETTER_BUTTON (url, 'Read the full post'),
    '</div>');
}
;

-- Divider between posts in a digest.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_POST_DIVIDER ()
{
  return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:30px 0 34px 0"><tr><td style="border-top:1px solid #e6e6e6;font-size:0;line-height:0">&nbsp;</td></tr></table>';
}
;

-- The outer email document. kicker is the <title> and the preview-line
-- fallback; from_name is the masthead (linked to site_url when given);
-- extra_css is a post's own stylesheet (full-content mode), which inline
-- styles here always outrank. unsub_url / postal_address are optional.
CREATE PROCEDURE DB.DBA.WEBLOG_NEWSLETTER_HTML_SHELL (IN kicker VARCHAR, IN body_html VARCHAR, IN from_name VARCHAR, IN unsub_url VARCHAR, IN extra_css VARCHAR := '', IN preheader VARCHAR := '', IN site_url VARCHAR := null, IN postal_address VARCHAR := null)
{
  declare pub, masthead, footer_links VARCHAR;
  pub := DB.DBA.WEBLOG_HTML_ESC_BYTES (coalesce (from_name, ''));
  if (site_url is not null and trim (site_url) <> '')
    masthead := concat ('<a href="', DB.DBA.WEBLOG_HTML_ESC_BYTES (site_url), '" target="_blank" style="color:#111111;text-decoration:none">', pub, '</a>');
  else
    masthead := pub;
  footer_links := '';
  if (unsub_url is not null and trim (unsub_url) <> '')
    footer_links := concat ('<a href="', DB.DBA.WEBLOG_HTML_ESC_BYTES (unsub_url), '" target="_blank" style="color:#8a8a8a;text-decoration:underline">Unsubscribe</a>');
  if (site_url is not null and trim (site_url) <> '')
    footer_links := concat (footer_links, case when footer_links = '' then '' else ' &nbsp;&middot;&nbsp; ' end,
      '<a href="', DB.DBA.WEBLOG_HTML_ESC_BYTES (site_url), '" target="_blank" style="color:#8a8a8a;text-decoration:underline">Visit the weblog</a>');
  if (coalesce (preheader, '') = '') preheader := coalesce (kicker, '');
  return concat (
    '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">',
    '<meta name="viewport" content="width=device-width,initial-scale=1">',
    '<meta name="x-apple-disable-message-reformatting">',
    '<meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light">',
    '<title>', DB.DBA.WEBLOG_HTML_ESC_BYTES (coalesce (kicker, '')), '</title>',
    '<style>', coalesce (extra_css, ''), '</style>',
    -- This generator family uses a scroll-triggered reveal-on-scroll
    -- pattern (an IntersectionObserver flips a "visible" class) for the
    -- synopsis deck, HowTo steps, FAQ items, and some whole sections --
    -- CSS classes like .anim-fade / .fade-in start at opacity:0 and rely
    -- on that JS to ever reach opacity:1. Email has no JS, so carrying the
    -- stylesheet along verbatim left entire sections permanently invisible
    -- (caught live 2026-09-22). This forces the post-reveal end state.
    '<style>.anim-fade,.fade-in{opacity:1 !important;transform:none !important}</style>',
    -- Bare <code> gets no styling from the generator's own stylesheets,
    -- so a dense technical sentence reads as one wall of text (flagged
    -- live 2026-09-23); a small monospace chip makes identifiers scannable.
    '<style>code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:0.88em;background:#f4f4f4;border:1px solid #e2e2e2;border-radius:4px;padding:1px 5px}',
    '.wl-body{overflow-wrap:anywhere;word-break:break-word}.wl-body img,.wl-body svg,.wl-body table,.wl-body video{max-width:100% !important;height:auto !important}.wl-body pre{white-space:pre-wrap !important}',
    '@media (max-width:620px){.wl-card{padding:28px 20px !important}.wl-title{font-size:26px !important}.wl-body{font-size:16px !important}}</style>',
    '</head>',
    '<body style="margin:0;padding:0;background:#f5f5f3;-webkit-text-size-adjust:100%">',
    -- Preview line shown next to the subject in the inbox; the trailing
    -- zero-width filler keeps body text from spilling into the preview.
    '<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;font-size:1px;line-height:1px;color:#f5f5f3;opacity:0">',
    DB.DBA.WEBLOG_HTML_ESC_BYTES (preheader), repeat ('&#8199;&#65279;&#847; ', 60), '</div>',
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#f5f5f3" style="background:#f5f5f3"><tr><td align="center" style="padding:28px 12px 36px 12px">',
    '<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;table-layout:fixed">',
    '<tr><td align="center" style="padding:0 0 18px 0;font-family:Georgia,''Times New Roman'',serif;font-size:19px;line-height:1.3;font-weight:bold;color:#111111">', masthead, '</td></tr>',
    '<tr><td class="wl-card" bgcolor="#ffffff" style="background:#ffffff;border:1px solid #e8e8e4;border-radius:8px;padding:40px 44px">', coalesce (body_html, ''), '</td></tr>',
    '<tr><td align="center" style="padding:26px 24px 0 24px;font-family:Helvetica,Arial,sans-serif;font-size:12px;line-height:1.6;color:#8a8a8a">',
    'You&#39;re receiving this because you subscribed to ', pub, '.',
    case when footer_links = '' then '' else concat ('<br>', footer_links) end,
    case when coalesce (trim (postal_address), '') = '' then '' else concat ('<br>', DB.DBA.WEBLOG_HTML_ESC_BYTES (trim (postal_address))) end,
    '</td></tr>',
    '</table></td></tr></table></body></html>');
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
  declare digest_text, digest_preheader, site_url, postal_address, sep VARCHAR;
  declare months any;

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
  site_url := concat (base_url, public_route);
  postal_address := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, 'weblog:newsletterPostalAddress', '');
  months := vector ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec');
  sep := concat (' ', chr (194), chr (183), ' ');
  post_cards := vector ();
  -- Optional intro paragraph before the post cards -- empty by default
  -- (weblog:emailIntroDigest unset), so an un-customized digest looks
  -- exactly as it always has. The per-post cards themselves are generated
  -- code, not template-editable -- too complex/fragile to safely expose as
  -- admin-editable text without risking a malformed digest.
  digest_body_html := DB.DBA.WEBLOG_RENDER_EMAIL_TEMPLATE (coll, 'weblog:emailIntroDigest', '',
    vector ('{{WEBLOG_TITLE}}', from_name, '{{POST_COUNT}}', cast (item_count as varchar)));
  digest_extra_css := '';
  digest_text := trim (regexp_replace (digest_body_html, '<[^>]*>', '', 1, null));
  if (digest_text <> '') digest_text := concat (digest_text, '\r\n\r\n');
  digest_preheader := '';
  for (i := 0; i < length (posts); i := i + 1)
  {
    declare pname, title, url, excerpt, card, post_css, byline, txt_part VARCHAR;
    declare excerpt_result, meta, pmod any;
    pname := aref (aref (posts, i), 0);
    pmod := aref (aref (posts, i), 1);
    title := DB.DBA.WEBLOG_NEWSLETTER_POST_TITLE (coll, pname);
    url := sprintf ('%s%s?post=%U', base_url, public_route, pname);
    -- Immediate mode sends one post per email, so it can afford a longer
    -- inlined excerpt than a digest bundling several posts in one message.
    excerpt_result := DB.DBA.WEBLOG_NEWSLETTER_POST_EXCERPT (coll, pname, case when mode = 'immediate' then 20000 else 8000 end, content_mode);
    excerpt := aref (excerpt_result, 0);
    post_css := aref (excerpt_result, 1);
    -- Subtitle (the page's meta description) and reading time.
    meta := DB.DBA.WEBLOG_NEWSLETTER_POST_META (coll, pname);
    byline := concat (from_name, sep, sprintf ('%s %d, %d', months[month (pmod) - 1], dayofmonth (pmod), year (pmod)),
      sep, sprintf ('%d min read', meta[2]));
    card := DB.DBA.WEBLOG_NEWSLETTER_POST_CARD (DB.DBA.WEBLOG_HTML_ESC_BYTES (title), url, excerpt, meta[0], byline);
    -- Plain-text alternative for this post.
    txt_part := concat (title, '\r\n', case when meta[1] <> '' then concat (meta[1], '\r\n') else '' end,
      byline, '\r\n\r\nRead it online: ', url, '\r\n');
    post_cards := vector_concat (post_cards, vector (vector (title, card, post_css, txt_part, meta[1])));
    if (i > 0)
    {
      digest_body_html := concat (digest_body_html, DB.DBA.WEBLOG_NEWSLETTER_POST_DIVIDER ());
      digest_text := concat (digest_text, '\r\n----------\r\n\r\n');
      digest_preheader := concat (digest_preheader, sep);
    }
    digest_body_html := concat (digest_body_html, card);
    digest_text := concat (digest_text, txt_part);
    digest_preheader := concat (digest_preheader, title);
    digest_extra_css := concat (digest_extra_css, post_css);
  }

  sent_count := 0;
  failed_count := 0;
  for (select WS_TOKEN as _tok, WS_EMAIL as _email from DB.DBA.WEBLOG_SUBSCRIBER
        where WS_DAV_COLLECTION = coll and WS_STATUS = 'confirmed') do
  {
    declare subscriber_ok int;
    declare unsub_url, text_footer VARCHAR;
    unsub_url := sprintf ('%s%s?nl_action=unsubscribe&token=%s', base_url, public_route, _tok);
    text_footer := concat ('\r\n--\r\nYou''re receiving this because you subscribed to ', from_name, '.\r\n',
      'Unsubscribe: ', unsub_url, '\r\n',
      case when trim (postal_address) = '' then '' else concat (trim (postal_address), '\r\n') end);
    subscriber_ok := 1;

    if (mode = 'immediate')
    {
      for (i := 0; i < length (post_cards) and subscriber_ok = 1; i := i + 1)
      {
        declare title, card, post_css, body_html, subj, msg, bulk_hdrs, preheader VARCHAR;
        title := aref (aref (post_cards, i), 0);
        card := aref (aref (post_cards, i), 1);
        post_css := aref (aref (post_cards, i), 2);
        preheader := aref (aref (post_cards, i), 4);
        if (preheader = '') preheader := title;
        body_html := DB.DBA.WEBLOG_NEWSLETTER_HTML_SHELL (title, card, from_name, unsub_url, post_css, preheader, site_url, postal_address);
        subj := DB.DBA.WEBLOG_RENDER_EMAIL_TEMPLATE (coll, 'weblog:emailSubjectImmediate',
          '{{WEBLOG_TITLE}}: {{POST_TITLE}}', vector ('{{WEBLOG_TITLE}}', from_name, '{{POST_TITLE}}', title));
        bulk_hdrs := DB.DBA.WEBLOG_NEWSLETTER_BULK_HEADERS (coll, from_addr, from_name, _email, unsub_url);
        msg := DB.DBA.WEBLOG_NEWSLETTER_MIME_MESSAGE (subj, bulk_hdrs,
          concat (aref (aref (post_cards, i), 3), text_footer), body_html);
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
      subj := DB.DBA.WEBLOG_RENDER_EMAIL_TEMPLATE (coll, 'weblog:emailSubjectDigest',
        '{{WEBLOG_TITLE}}: new posts this week', vector ('{{WEBLOG_TITLE}}', from_name, '{{POST_COUNT}}', cast (item_count as varchar)));
      body_html := DB.DBA.WEBLOG_NEWSLETTER_HTML_SHELL (subj, digest_body_html, from_name, unsub_url, digest_extra_css, digest_preheader, site_url, postal_address);
      bulk_hdrs := DB.DBA.WEBLOG_NEWSLETTER_BULK_HEADERS (coll, from_addr, from_name, _email, unsub_url);
      msg := DB.DBA.WEBLOG_NEWSLETTER_MIME_MESSAGE (subj, bulk_hdrs, concat (digest_text, text_footer), body_html);
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
-- ==========================================================================
-- Dashboard "Trends & Analytics" panel (step 1: data already on hand).
-- Everything here is derived from WEBLOG_SUBSCRIBER timestamps and the
-- collection's posts (RES_MOD_TIME + schema:category) -- no new tables, no
-- view/open/click tracking. Charts are inline SVG styled by the dashboard's
-- own theme tokens (--accent, --border, --muted), so light/dark and the
-- manual theme switch apply to them with no extra code; each chart has
-- one series on one axis, a per-week hover tooltip (<title>), and the same
-- numbers are available as a table under "Weekly data".
-- ==========================================================================

-- HTML-escape a string while keeping its raw UTF-8 bytes. Used instead
-- of sprintf('%V', ...) here because %V's handling of non-ASCII depends on
-- the calling context (verified 2026-09-25): outside an HTTP request it
-- passes narrow UTF-8 through but writes a WIDE string's U+0080-U+00FF as
-- single Latin-1 bytes; inside one (the admin action route) it does the
-- reverse and re-encodes narrow bytes. The dashboard is refreshed from
-- both, so its labels are escaped here and emitted with %s.
CREATE PROCEDURE DB.DBA.WEBLOG_HTML_ESC_BYTES (IN s ANY)
{
  if (s is null) return '';
  if (iswidestring (s)) s := charset_recode (s, '_WIDE_', 'UTF-8');
  if (not isstring (s)) s := cast (s as varchar);
  s := replace (s, '&', '&amp;');
  s := replace (s, '<', '&lt;');
  s := replace (s, '>', '&gt;');
  s := replace (s, '"', '&quot;');
  s := replace (s, '''', '&#39;');
  return s;
}
;

-- One bar with 4px rounded top corners and a flat baseline end.
CREATE PROCEDURE DB.DBA.WEBLOG_SVG_BAR_PATH (IN x DOUBLE PRECISION, IN y DOUBLE PRECISION, IN w DOUBLE PRECISION, IN h DOUBLE PRECISION)
{
  declare r DOUBLE PRECISION;
  r := 4.0;
  if (r > w / 2) r := w / 2;
  if (r > h) r := h;
  return sprintf ('M%.1f,%.1f V%.1f Q%.1f,%.1f %.1f,%.1f H%.1f Q%.1f,%.1f %.1f,%.1f V%.1f Z',
    x, y + h, y + r, x, y, x + r, y, x + w - r, x + w, y, x + w, y + r, y + h);
}
;

-- A single-series weekly chart: kind = 'bar' or 'line'. vals and
-- week_starts are equal-length vectors; unit is the tooltip noun.
CREATE PROCEDURE DB.DBA.WEBLOG_DASHBOARD_CHART (IN kind VARCHAR, IN vals ANY, IN week_starts ANY, IN title VARCHAR, IN unit VARCHAR)
{
  declare n, i, v, maxv, ymax, g int;
  declare x0, y0, ph, pw, slot, bw, x, y, h, cx, cy DOUBLE PRECISION;
  declare svg, pts, months, ws any;
  months := vector ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec');
  n := length (vals);
  maxv := 0;
  for (i := 0; i < n; i := i + 1)
    if (vals[i] > maxv) maxv := vals[i];
  -- Even ceiling so the midline tick is a whole number.
  ymax := maxv;
  if (ymax < 2) ymax := 2;
  if (mod (ymax, 2) = 1) ymax := ymax + 1;
  x0 := 34.0;
  y0 := 170.0;
  ph := 150.0;
  pw := 598.0;
  slot := pw / n;

  svg := sprintf ('<svg class="chart" viewBox="0 0 640 196" role="img" aria-label="%V">', title);
  for (g := 0; g <= 2; g := g + 1)
  {
    y := y0 - ph * g / 2;
    svg := concat (svg, sprintf ('<line class="grid" x1="%.1f" x2="632" y1="%.1f" y2="%.1f"/><text class="tick" x="%.1f" y="%.1f" text-anchor="end">%d</text>',
      x0, y, y, x0 - 6, y + 4, ymax * g / 2));
  }

  if (kind = 'line')
  {
    pts := '';
    for (i := 0; i < n; i := i + 1)
    {
      cx := x0 + slot * i + slot / 2;
      cy := y0 - ph * vals[i] / ymax;
      pts := concat (pts, sprintf ('%.1f,%.1f ', cx, cy));
    }
    svg := concat (svg, sprintf ('<polyline class="line" points="%s"/>', trim (pts)));
  }

  for (i := 0; i < n; i := i + 1)
  {
    v := vals[i];
    ws := week_starts[i];
    svg := concat (svg, sprintf ('<g class="m"><title>Week of %s %d, %d: %d %s</title><rect class="hit" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>',
      months[month (ws) - 1], dayofmonth (ws), year (ws), v, unit, x0 + slot * i, y0 - ph, slot, ph));
    if (kind = 'bar')
    {
      bw := slot - 2;
      if (bw > 28) bw := 28;
      if (bw < 1) bw := 1;
      h := ph * v / ymax;
      if (v > 0)
        svg := concat (svg, sprintf ('<path class="bar" d="%s"/>',
          DB.DBA.WEBLOG_SVG_BAR_PATH (x0 + slot * i + (slot - bw) / 2, y0 - h, bw, h)));
    }
    else
    {
      svg := concat (svg, sprintf ('<circle class="hover-dot" cx="%.1f" cy="%.1f" r="4"/>',
        x0 + slot * i + slot / 2, y0 - ph * v / ymax));
    }
    svg := concat (svg, '</g>');
    -- Every 4th week gets an x label, counted back from the latest week.
    if (mod (n - 1 - i, 4) = 0)
      svg := concat (svg, sprintf ('<text class="xl" x="%.1f" y="188" text-anchor="middle">%s %d</text>',
        x0 + slot * i + slot / 2, months[month (ws) - 1], dayofmonth (ws)));
  }

  -- Selective direct label: only the latest value, on the line chart.
  if (kind = 'line' and n > 0)
  {
    cx := x0 + slot * (n - 1) + slot / 2;
    cy := y0 - ph * vals[n - 1] / ymax;
    svg := concat (svg, sprintf ('<circle class="dot" cx="%.1f" cy="%.1f" r="4"/><text class="val" x="%.1f" y="%.1f" text-anchor="end">%d</text>',
      cx, cy, cx - 7, cy - 8, vals[n - 1]));
  }
  return concat (svg, '</svg>');
}
;

-- Top-N rows of a {label -> count} dictionary, as <tr> HTML, highest first.
CREATE PROCEDURE DB.DBA.WEBLOG_DASHBOARD_TOP_ROWS (IN counts ANY, IN top_n INTEGER, IN is_country INTEGER := 0)
{
  declare kv, used any;
  declare i, j, best_i, best_v, total int;
  declare rows_html VARCHAR;
  kv := dict_to_vector (counts, 0);
  used := make_array (length (kv) / 2, 'any');
  for (i := 0; i < length (kv) / 2; i := i + 1)
    aset (used, i, 0);
  rows_html := '';
  total := 0;
  for (j := 0; j < top_n; j := j + 1)
  {
    best_i := -1;
    best_v := -1;
    for (i := 0; i < length (kv) / 2; i := i + 1)
      if (used[i] = 0 and kv[2 * i + 1] > best_v)
      {
        best_i := i;
        best_v := kv[2 * i + 1];
      }
    if (best_i < 0)
      goto done;
    aset (used, best_i, 1);
    rows_html := concat (rows_html, sprintf ('<tr><td>%s</td><td class="num">%d</td></tr>',
      coalesce (case when is_country = 1 then DB.DBA.WEBLOG_COUNTRY_NAME_HTML (kv[2 * best_i]) else null end,
        DB.DBA.WEBLOG_HTML_ESC_BYTES (kv[2 * best_i])), best_v));
  }
done:
  if (rows_html = '')
    rows_html := '<tr><td colspan="2" class="hint">No data yet</td></tr>';
  return rows_html;
}
;

CREATE PROCEDURE DB.DBA.WEBLOG_DASHBOARD_ANALYTICS_HTML (IN dav_collection VARCHAR)
{
  declare coll, kpis, charts, tables, weekly_rows, rate_txt, confirm_txt VARCHAR;
  declare n, i, d, total_sub, total_conf, total_unsub, conf_n, signups_30, confirmed_30, posts_30, total_posts, base_confirmed int;
  declare conf_minutes integer;
  declare today, start_d any;
  declare signups, confirms, cumul, posts, week_starts, countries, categories, html_stems, post_rows, months any;

  coll := trim (dav_collection);
  if (subseq (coll, length (coll) - 1) <> '/') coll := coll || '/';
  months := vector ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec');

  -- 26 whole weeks, Monday-based, ending with the current week.
  n := 26;
  today := cast (now () as date);
  start_d := dateadd ('day', - mod (dayofweek (today) + 5, 7) - 7 * (n - 1), today);
  signups := make_array (n, 'any');
  confirms := make_array (n, 'any');
  cumul := make_array (n, 'any');
  posts := make_array (n, 'any');
  week_starts := make_array (n, 'any');
  for (i := 0; i < n; i := i + 1)
  {
    aset (signups, i, 0);
    aset (confirms, i, 0);
    aset (cumul, i, 0);
    aset (posts, i, 0);
    aset (week_starts, i, dateadd ('day', 7 * i, start_d));
  }

  total_sub := 0; total_conf := 0; total_unsub := 0; conf_n := 0; conf_minutes := 0;
  signups_30 := 0; confirmed_30 := 0; base_confirmed := 0;
  countries := dict_new (31);
  for (select WS_SUBSCRIBED_AT as _sub, WS_CONFIRMED_AT as _conf, WS_STATUS as _s, WS_COUNTRY as _c
         from DB.DBA.WEBLOG_SUBSCRIBER
        where WS_DAV_COLLECTION = coll) do
  {
    total_sub := total_sub + 1;
    if (_s = 'unsubscribed') total_unsub := total_unsub + 1;
    if (_sub is not null)
    {
      d := datediff ('day', start_d, _sub);
      if (d >= 0 and d / 7 < n) aset (signups, d / 7, signups[d / 7] + 1);
      if (datediff ('day', _sub, now ()) < 30) signups_30 := signups_30 + 1;
    }
    if (_conf is not null)
    {
      total_conf := total_conf + 1;
      if (_sub is not null and _conf >= _sub)
      {
        conf_minutes := conf_minutes + datediff ('minute', _sub, _conf);
        conf_n := conf_n + 1;
      }
      d := datediff ('day', start_d, _conf);
      if (d < 0)
        base_confirmed := base_confirmed + 1;
      else if (d / 7 < n)
        aset (confirms, d / 7, confirms[d / 7] + 1);
      if (datediff ('day', _conf, now ()) < 30) confirmed_30 := confirmed_30 + 1;
    }
    if (_s = 'confirmed')
    {
      declare ckey VARCHAR;
      -- Legacy free-text values merge with their ISO code where recognized.
      ckey := DB.DBA.WEBLOG_COUNTRY_NORMALIZE (_c);
      if (ckey is null) ckey := trim (coalesce (cast (_c as varchar), ''));
      if (ckey = '') ckey := 'Unknown';
      dict_put (countries, ckey, coalesce (dict_get (countries, ckey, 0), 0) + 1);
    }
  }
  d := base_confirmed;
  for (i := 0; i < n; i := i + 1)
  {
    d := d + confirms[i];
    aset (cumul, i, d);
  }

  -- Posts: same selection rule as the public index.vsp -- every .html, and
  -- a .md only when no .html shares its stem. RES_MOD_TIME is the date the
  -- weblog itself shows for a post.
  html_stems := dict_new (61);
  post_rows := vector ();
  for (select RES_NAME as _name, RES_MOD_TIME as _mod, RES_ID as _id
         from WS.WS.SYS_DAV_RES
        where (RES_FULL_PATH like coll || '%.html' or RES_FULL_PATH like coll || '%.md')
          and RES_NAME not like '._%'
          and RES_NAME not in ('index.vsp', 'newsletter.vsp', 'dashboard.html')) do
  {
    declare dpos int;
    declare stem, ext VARCHAR;
    dpos := strrchr (_name, '.');
    stem := subseq (_name, 0, dpos);
    ext := lower (subseq (_name, dpos + 1));
    if (ext = 'html') dict_put (html_stems, stem, 1);
    post_rows := vector_concat (post_rows, vector (vector (_mod, _id, ext, stem)));
  }
  categories := dict_new (61);
  total_posts := 0;
  posts_30 := 0;
  for (i := 0; i < length (post_rows); i := i + 1)
  {
    declare r, parts any;
    declare j int;
    r := post_rows[i];
    if (r[2] = 'md' and dict_get (html_stems, r[3], null) is not null)
      goto next_post;
    total_posts := total_posts + 1;
    d := datediff ('day', start_d, r[0]);
    if (d >= 0 and d / 7 < n) aset (posts, d / 7, posts[d / 7] + 1);
    if (datediff ('day', r[0], now ()) < 30) posts_30 := posts_30 + 1;
    for (select P.PROP_VALUE as _cat from WS.WS.SYS_DAV_PROP P
          where P.PROP_PARENT_ID = r[1] and P.PROP_TYPE = 'R' and P.PROP_NAME = 'schema:category') do
    {
      if (_cat is not null and isstring (_cat))
      {
        parts := split_and_decode (cast (_cat as varchar), 0, '\0\0;');
        for (j := 0; j < length (parts); j := j + 1)
        {
          declare one VARCHAR;
          one := trim (parts[j]);
          if (one <> '')
            dict_put (categories, one, coalesce (dict_get (categories, one, 0), 0) + 1);
        }
      }
    }
  next_post: ;
  }

  if (total_sub = 0)
    rate_txt := '--';
  else
    rate_txt := sprintf ('%d%%', (total_conf * 100) / total_sub);
  if (conf_n = 0)
    confirm_txt := '--';
  else if (conf_minutes / conf_n < 120)
    confirm_txt := sprintf ('%d min', conf_minutes / conf_n);
  else
    confirm_txt := sprintf ('%d h', conf_minutes / conf_n / 60);

  kpis := sprintf (
    '<div class="stats">' ||
    '<div class="stat"><div class="n">%d</div><div class="l">Sign-ups, 30 days</div></div>' ||
    '<div class="stat confirmed"><div class="n">%d</div><div class="l">Confirmed, 30 days</div></div>' ||
    '<div class="stat"><div class="n">%s</div><div class="l">Confirmation rate</div></div>' ||
    '<div class="stat"><div class="n">%s</div><div class="l">Avg. time to confirm</div></div>' ||
    '<div class="stat"><div class="n">%d</div><div class="l">Posts, 30 days</div></div>' ||
    '</div>',
    signups_30, confirmed_30, rate_txt, confirm_txt, posts_30);

  charts := concat (
    '<div class="chart-grid">',
    '<figure class="chart-card"><figcaption><h3>Confirmed subscribers</h3><p class="hint">',
    sprintf ('Running total of confirmations. Unsubscribes aren&#39;t dated yet, so the %d who later unsubscribed are still counted here.', total_unsub),
    '</p></figcaption>',
    DB.DBA.WEBLOG_DASHBOARD_CHART ('line', cumul, week_starts, 'Confirmed subscribers, running total, last 26 weeks', 'confirmed in total'),
    '</figure>',
    '<figure class="chart-card"><figcaption><h3>New sign-ups per week</h3><p class="hint">Every sign-up, confirmed or not.</p></figcaption>',
    DB.DBA.WEBLOG_DASHBOARD_CHART ('bar', signups, week_starts, 'New sign-ups per week, last 26 weeks', 'sign-ups'),
    '</figure>',
    '<figure class="chart-card"><figcaption><h3>Posts published per week</h3><p class="hint">By each post&#39;s date on the weblog.</p></figcaption>',
    DB.DBA.WEBLOG_DASHBOARD_CHART ('bar', posts, week_starts, 'Posts published per week, last 26 weeks', 'posts'),
    '</figure>',
    '</div>');

  tables := concat (
    '<div class="import-grid">',
    '<div class="import-card"><h3>Confirmed subscribers by country</h3><table class="subscribers compact"><thead><tr><th>Country</th><th class="num">Subscribers</th></tr></thead><tbody>',
    DB.DBA.WEBLOG_DASHBOARD_TOP_ROWS (countries, 10, 1),
    '</tbody></table></div>',
    sprintf ('<div class="import-card"><h3>Posts by category</h3><p class="hint">Top 10 across all %d posts. A post can carry several categories.</p><table class="subscribers compact"><thead><tr><th>Category</th><th class="num">Posts</th></tr></thead><tbody>', total_posts),
    DB.DBA.WEBLOG_DASHBOARD_TOP_ROWS (categories, 10),
    '</tbody></table></div>',
    '</div>');

  weekly_rows := '';
  for (i := n - 1; i >= 0; i := i - 1)
    weekly_rows := concat (weekly_rows, sprintf ('<tr><td>%s %d, %d</td><td class="num">%d</td><td class="num">%d</td><td class="num">%d</td></tr>',
      months[month (week_starts[i]) - 1], dayofmonth (week_starts[i]), year (week_starts[i]), signups[i], cumul[i], posts[i]));

  return concat (
    '<section class="panel"><details class="collapsible" open><summary class="panel-h2">Trends &amp; Analytics</summary>',
    '<p class="panel-desc">The last 26 weeks, from subscriber sign-up/confirmation times and post dates. Post views, email opens and clicks aren&#39;t recorded yet.</p>',
    kpis, charts, tables,
    '<details class="collapsible"><summary class="panel-h3">Weekly data</summary><table class="subscribers compact"><thead><tr><th>Week of</th><th class="num">Sign-ups</th><th class="num">Confirmed (total)</th><th class="num">Posts</th></tr></thead><tbody>',
    weekly_rows,
    '</tbody></table></details>',
    '</details></section>');
}
;

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
  declare email_templates_html VARCHAR;
  declare analytics_html VARCHAR;

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

  -- Trends & Analytics panel. Isolated so a failure in it (e.g. an odd
  -- property value) degrades to a note instead of breaking the whole
  -- dashboard refresh.
  analytics_html := '<section class="panel"><p class="admin-note">Trends &amp; Analytics could not be generated on this refresh.</p></section>';
  {
    declare exit handler for sqlstate '*' { ; };
    analytics_html := DB.DBA.WEBLOG_DASHBOARD_ANALYTICS_HTML (coll);
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
      '<section class="panel"><details class="collapsible"><summary class="panel-h2">Delivery Settings</summary><p class="panel-desc">Configure when and how new-post notifications go out.</p>' ||
      '<div class="setting-row"><div class="setting-label">Send new-post notifications now</div><div class="setting-control"><form method="post" action="%s"><input type="hidden" name="admin_action" value="send_digest_now"/><input type="hidden" name="admin_token" value="%s"/><button type="submit" class="secondary">Send now</button></form></div></div>' ||
      '<div class="setting-row"><div class="setting-label">Delivery mode <span class="badge">%V</span></div><div class="setting-control"><form method="post" action="%s"><input type="hidden" name="admin_action" value="set_digest_mode"/><input type="hidden" name="admin_token" value="%s"/><select name="mode"><option value="digest"%s>Digest (bundle new posts)</option><option value="immediate"%s>Immediate (one email per post)</option></select><button type="submit">Save</button></form></div></div>' ||
      '<div class="setting-row"><div class="setting-label">Email content <span class="badge">%V</span></div><div class="setting-control"><form method="post" action="%s"><input type="hidden" name="admin_action" value="set_content_mode"/><input type="hidden" name="admin_token" value="%s"/><select name="content_mode"><option value="auto"%s>Auto</option><option value="snippet"%s>Always snippet</option><option value="full"%s>Always full post</option></select><button type="submit">Save</button></form></div></div>' ||
      '<div class="setting-row"><div class="setting-label">Skin <span class="badge">%V</span></div><div class="setting-control"><form method="post" action="%s"><input type="hidden" name="admin_action" value="set_skin"/><input type="hidden" name="admin_token" value="%s"/><select name="skin_choice"><option value="classic"%s>Classic</option><option value="editorial"%s>Editorial</option></select><button type="submit">Save</button></form><span class="hint">Preview: ?skin=classic or ?skin=editorial</span></div></div>' ||
      '</details></section>',
      action_route, admin_token,
      current_mode, action_route, admin_token, case when current_mode = 'digest' then ' selected="selected"' else '' end, case when current_mode = 'immediate' then ' selected="selected"' else '' end,
      current_content_mode, action_route, admin_token, case when current_content_mode = 'auto' then ' selected="selected"' else '' end, case when current_content_mode = 'snippet' then ' selected="selected"' else '' end, case when current_content_mode = 'full' then ' selected="selected"' else '' end,
      current_skin, action_route, admin_token, case when current_skin = 'classic' then ' selected="selected"' else '' end, case when current_skin = 'editorial' then ' selected="selected"' else '' end);
  }

  -- Every outbound email''s subject (and, for the ones with genuinely
  -- free-text bodies rather than generated content like the digest''s post
  -- cards) body, editable from one uniform loop instead of six near-
  -- identical hand-written blocks. Each entry: [type key, display label,
  -- subject property, subject default, body property ('''' = no editable
  -- body for this type), body default, placeholder-token hint]. Defaults
  -- here MUST match the defaults each WEBLOG_NEWSLETTER_* send procedure
  -- passes to WEBLOG_RENDER_EMAIL_TEMPLATE, so an unset property shows the
  -- admin exactly what is actually being sent.
  email_templates_html := '';
  if (action_route <> '')
  {
    declare et_types any;
    declare et_i INTEGER;
    et_types := vector (
      vector ('confirm', 'Confirmation Email', 'weblog:emailSubjectConfirm', '{{WEBLOG_TITLE}}: confirm your subscription',
        'weblog:emailBodyConfirm', 'Please confirm your subscription by opening this link:\r\n\r\n{{CONFIRM_URL}}\r\n\r\nIf you did not request this, ignore this message -- you will not be subscribed unless you click the link above.\r\n',
        'Tokens: {{WEBLOG_TITLE}}, {{CONFIRM_URL}} (required).'),
      vector ('digest', 'Digest Email', 'weblog:emailSubjectDigest', '{{WEBLOG_TITLE}}: new posts this week',
        'weblog:emailIntroDigest', '',
        'Subject tokens: {{WEBLOG_TITLE}}, {{POST_COUNT}}. Body is an optional intro paragraph shown above the post cards -- leave blank for none.'),
      vector ('immediate', 'Immediate-Mode Email', 'weblog:emailSubjectImmediate', '{{WEBLOG_TITLE}}: {{POST_TITLE}}',
        '', '',
        'Tokens: {{WEBLOG_TITLE}}, {{POST_TITLE}}. Subject only -- the body is the post itself (immediate mode sends one email per post).'),
      vector ('activation', 'Admin-Import Activation Notice', 'weblog:emailSubjectActivation', '{{WEBLOG_TITLE}}: you have been added to our mailing list',
        'weblog:emailBodyActivation', '{{GREETING}}You have been added to the {{WEBLOG_TITLE}} mailing list by the site administrator.\r\n\r\nIf you would rather not receive it, you can unsubscribe at any time:\r\n\r\n{{UNSUBSCRIBE_URL}}\r\n\r\nNo action is needed if you would like to stay on the list.\r\n',
        'Tokens: {{WEBLOG_TITLE}}, {{GREETING}} (blank, or "Hi Name," when a name was given), {{UNSUBSCRIBE_URL}} (required).'),
      vector ('unsubscribe_notice', 'Admin-Unsubscribe Notice', 'weblog:emailSubjectUnsubscribeNotice', '{{WEBLOG_TITLE}}: you have been unsubscribed',
        'weblog:emailBodyUnsubscribeNotice', '{{GREETING}}You have been removed from the {{WEBLOG_TITLE}} mailing list by the site administrator. You will not receive any further digest emails at this address.\r\n\r\nIf this was a mistake, you can subscribe again at any time:\r\n\r\n{{RESUBSCRIBE_URL}}\r\n',
        'Tokens: {{WEBLOG_TITLE}}, {{GREETING}}, {{RESUBSCRIBE_URL}} (required).'),
      vector ('admin_alert', 'Admin Operational Alerts', 'weblog:emailSubjectAdminAlert', '{{WEBLOG_TITLE}} admin: {{SUBJECT_SUFFIX}}',
        '', '',
        'Tokens: {{WEBLOG_TITLE}}, {{SUBJECT_SUFFIX}}. Subject only -- sent to weblog:adminEmail for a new confirmed subscriber or a failed digest batch; body content is generated per alert.')
    );
    email_templates_html := '<section class="panel"><details class="collapsible"><summary class="panel-h2">Email Templates</summary><p class="panel-desc">Customize the subject (and, where shown, body) of every outbound email. Unmodified fields show exactly what is sent today.</p>';
    for (et_i := 0; et_i < length (et_types); et_i := et_i + 1)
    {
      declare et_key, et_label, et_subj_prop, et_subj_default, et_body_prop, et_body_default, et_hint VARCHAR;
      declare et_cur_subj, et_cur_body VARCHAR;
      et_key := et_types[et_i][0]; et_label := et_types[et_i][1];
      et_subj_prop := et_types[et_i][2]; et_subj_default := et_types[et_i][3];
      et_body_prop := et_types[et_i][4]; et_body_default := et_types[et_i][5];
      et_hint := et_types[et_i][6];
      et_cur_subj := DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, et_subj_prop, et_subj_default);
      et_cur_body := case when et_body_prop = '' then null else DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP (coll, et_body_prop, et_body_default) end;
      email_templates_html := concat (email_templates_html, sprintf (
        '<details class="collapsible"><summary class="panel-h3">%V</summary><form method="post" action="%s"><input type="hidden" name="admin_action" value="set_email_template"/><input type="hidden" name="admin_token" value="%s"/><input type="hidden" name="template_type" value="%s"/><div class="nl-field"><label>Subject</label><input type="text" name="subject" value="%V"/></div>',
        et_label, action_route, admin_token, et_key, et_cur_subj));
      if (et_cur_body is not null)
        email_templates_html := concat (email_templates_html, sprintf ('<div class="nl-field"><label>Body</label><textarea name="body" rows="5" style="width:100%%;">%V</textarea></div>', et_cur_body));
      email_templates_html := concat (email_templates_html, sprintf (
        '<p class="hint">%V</p><button type="submit">Save</button></form>' ||
        '<form method="post" action="%s"><input type="hidden" name="admin_action" value="set_email_template"/><input type="hidden" name="admin_token" value="%s"/><input type="hidden" name="template_type" value="%s"/><input type="hidden" name="reset" value="1"/><button type="submit" class="secondary">Reset to Default</button></form></details>',
        et_hint, action_route, admin_token, et_key));
    }
    email_templates_html := concat (email_templates_html, '</details></section>');
  }

  -- Sender identity, SMTP relay override, and the base URL used to build
  -- every absolute link in an email -- previously only settable via a raw
  -- DAV_PROP_SET call. resolved_smtp shows what WEBLOG_NEWSLETTER_RESOLVE_SMTP
  -- actually picks when the override is blank, so the admin isn't guessing.
  email_config_html := '';
  if (action_route <> '')
  {
    email_config_html := sprintf (
      '<section class="panel"><details class="collapsible"><summary class="panel-h2">Email Server Config</summary><p class="panel-desc">Sender identity, SMTP relay override, and the base URL used to build absolute links in every email.</p>' ||
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
      '</form></details></section>',
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
      '<section class="panel"><details class="collapsible"><summary class="panel-h2">Import Subscribers</summary><p class="panel-desc">Admin-only onboarding: added subscribers are marked confirmed immediately and sent an activation notice with an unsubscribe link -- no confirm-click required, but they can opt out.</p>' ||
      '<div class="import-grid">' ||
      '<div class="import-card"><h3>CSV Upload</h3><p class="hint">Header row with "email" (required) and optional "name" / "country" columns. Country may be an ISO code ("US") or a name; anything unrecognized is left blank.</p><form method="post" action="%s" enctype="multipart/form-data"><input type="hidden" name="admin_action" value="import_subscribers_csv"/><input type="hidden" name="admin_token" value="%s"/><input type="file" name="importfile" accept=".csv,text/csv" required/><button type="submit">Import CSV</button></form></div>' ||
      '<div class="import-card"><h3>RDF Upload</h3><p class="hint">Looks for schema:Person / schema:email (+ optional schema:name / schema:addressCountry; name and country not extracted for JSON-LD).</p><form method="post" action="%s" enctype="multipart/form-data"><select name="rdf_format"><option value="turtle">Turtle</option><option value="jsonld">JSON-LD</option><option value="ntriples">N-Triples</option><option value="nquads">N-Quads</option><option value="trig">TriG</option></select><input type="hidden" name="admin_action" value="import_subscribers_rdf"/><input type="hidden" name="admin_token" value="%s"/><input type="file" name="importfile" accept=".ttl,.jsonld,.json,.nt,.nq,.trig,.n3" required/><button type="submit">Import RDF</button></form></div>' ||
      '<div class="import-card"><h3>Manual Entry</h3><p class="hint">Fill in one or more rows -- blank email rows are ignored.</p><form method="post" action="%s"><input type="hidden" name="admin_action" value="import_subscribers_manual"/><input type="hidden" name="admin_token" value="%s"/><table class="manual-add"><thead><tr><th>Name</th><th>Email</th></tr></thead><tbody>%s</tbody></table><button type="submit">Add Subscribers</button></form></div>' ||
      '</div></details></section>',
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
      '<section class="panel"><details class="collapsible"><summary class="panel-h2">Tagging &amp; Scheduling</summary><p class="panel-desc">Per-post category/pin metadata, and this collection''s background jobs.</p>' ||
      '<datalist id="category-options">%s</datalist>' ||
      '<details class="collapsible"><summary class="panel-h3">Post Tags &amp; Pinning</summary><table class="subscribers"><thead><tr><th>Post</th><th>Category</th><th>Pinned</th></tr></thead><tbody>%s</tbody></table></details>' ||
      '<details class="collapsible"><summary class="panel-h3">Scheduled Jobs</summary>' ||
      '<div class="setting-row"><div class="setting-label">Newsletter digest check <span class="badge %s">%V</span></div><div class="setting-control"><form method="post" action="%s"><input type="hidden" name="admin_action" value="set_digest_schedule"/><input type="hidden" name="admin_token" value="%s"/><select name="digest_enabled"><option value="1"%s>On</option><option value="0"%s>Off</option></select><input type="number" name="minutes" min="1" value="%d"/><button type="submit">Save</button></form></div></div>' ||
      '<div class="setting-row"><div class="setting-label">Dashboard auto-refresh <span class="badge %s">%V</span></div><div class="setting-control"><form method="post" action="%s"><input type="hidden" name="admin_action" value="set_dashboard_schedule"/><input type="hidden" name="admin_token" value="%s"/><select name="dash_enabled"><option value="1"%s>On</option><option value="0"%s>Off</option></select><input type="number" name="dash_minutes" min="1" value="%d"/><button type="submit">Save</button></form></div></div>' ||
      '</details>' ||
      '</details></section>',
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
    -- Collapsed by default (no open attribute) -- Subscribers, Post Tags &
    -- Pinning, and Scheduled Jobs can all get long, and a freshly opened
    -- dashboard shouldn''t force scrolling past all of them to reach
    -- Delivery Settings/Email Server Config. Native <details>, no JS.
    'details.collapsible{margin:1rem 0;}details.collapsible:first-of-type{margin-top:0;}' ||
    'details.collapsible>summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:.45rem;}' ||
    'details.collapsible>summary::-webkit-details-marker{display:none;}' ||
    'details.collapsible>summary::before{content:"\\25B6";font-size:.65rem;color:var(--muted);transition:transform .15s ease;display:inline-block;}' ||
    'details.collapsible[open]>summary::before{transform:rotate(90deg);}' ||
    'summary.panel-h2{font-size:1rem;font-weight:700;margin:0 0 .2rem;}summary.panel-h3{font-size:.88rem;font-weight:600;margin:0 0 .3rem;}' ||
    'details.collapsible>summary .count-badge{color:var(--muted);font-weight:500;font-size:.82rem;}' ||
    'details.collapsible[open]>summary{margin-bottom:.9rem;}' ||
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
    '.chart-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(18rem,1fr));gap:1rem;margin:0 0 1.25rem;}' ||
    'figure.chart-card{margin:0;border:1px solid var(--border);border-radius:8px;padding:.9rem 1rem;min-width:0;}figure.chart-card h3{margin:0;font-size:.88rem;}figure.chart-card .hint{margin:.15rem 0 .6rem;}' ||
    'svg.chart{display:block;width:100%%;height:auto;}svg.chart .grid{stroke:var(--border);stroke-width:1;}svg.chart .tick,svg.chart .xl{fill:var(--muted);font-size:11px;}svg.chart .val{fill:var(--text);font-size:11px;font-weight:600;}' ||
    'svg.chart .bar{fill:var(--accent);}svg.chart .line{fill:none;stroke:var(--accent);stroke-width:2;stroke-linejoin:round;stroke-linecap:round;}svg.chart .dot{fill:var(--accent);stroke:var(--surface);stroke-width:2;}' ||
    'svg.chart .hit{fill:var(--accent-soft);fill-opacity:0;}svg.chart g.m:hover .hit{fill-opacity:.7;}svg.chart .hover-dot{fill:var(--accent);stroke:var(--surface);stroke-width:2;opacity:0;}svg.chart g.m:hover .hover-dot{opacity:1;}' ||
    'table.compact th,table.compact td{padding:.4rem .6rem;}table.subscribers .num{text-align:right;font-variant-numeric:tabular-nums;}' ||
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
    '%s%s%s%s%s%s' ||
    '<section class="panel"><details class="collapsible"><summary class="panel-h2">Subscribers <span class="count-badge">(%d)</span></summary><table class="subscribers"><thead><tr><th>Name</th><th>Email</th><th>Status</th><th>Subscribed</th><th>Confirmed</th><th>Last Digest Sent</th><th>Actions</th></tr></thead><tbody>%s</tbody></table></details></section>' ||
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
    dash_total, dash_pending, dash_confirmed, dash_unsubscribed, analytics_html, controls_html, email_config_html, email_templates_html, import_html, tag_schedule_html, dash_total, dash_rows, cast (now () as varchar));

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
