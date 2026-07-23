-- Deploy facet-enabled OpenLink-site themed weblog index.vsp for /DAV/www2.openlinksw.com/data/html/
-- Variant: opl-site color/texture treatment inspired by https://www.openlinksw.com/
-- Run as: isql 1111 dba <password> deploy-weblog-opl-site-facet.sql
CREATE PROCEDURE DB.DBA.TMP_DEPLOY_WEBLOG_VHOST_REMOVE (IN _lh varchar, IN _vh varchar, IN _lp varchar)
{
  declare exit handler for sqlstate '*' { ; };
  DB.DBA.VHOST_REMOVE (lhost=>_lh, vhost=>_vh, lpath=>_lp);
}
;

CREATE PROCEDURE DB.DBA.TMP_DEPLOY_WEBLOG_DEFAULT_PIN (IN _coll varchar, IN _dav_user varchar)
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
     and R.RES_NAME <> 'index.vsp'
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
          and RES_NAME <> 'index.vsp'
        order by RES_MOD_TIME desc, RES_NAME desc) do
  {
    _target := _path;
  }

  if (_target is null) return 0;

  select pwd_magic_calc (U_NAME, U_PASSWORD, 1) into _pwd
    from DB.DBA.SYS_USERS
   where U_NAME = _dav_user;

  if (_pwd is null) return 0;

  _rc := DB.DBA.DAV_PROP_SET (_target, 'schema:position', '1', _dav_user, _pwd, 1);
  return _rc;
}
;

CREATE PROCEDURE DB.DBA.TMP_DEPLOY_WEBLOG ()
{
  declare rc any;
  declare vsp_content varchar;
  declare vsp_stream any;

  vsp_content := '<?vsp
  -- Weblog-style index of /DAV/www2.openlinksw.com/data/html/
  -- Most recent resource is presented as the current post; the rest form the archive.

  declare all_rows, pinned_posts, posts, html_stems, category_seen, category_keys, facet_key, facet_value any;
  declare n, idx, i, has_categories, filter_active, post_selected, all_count, ck, facet_count int;
  declare sel, q, ft_q, from_date, to_date, selected_category, category_cloud, facet_category, facet_active varchar;
  declare q_param, from_param, to_param, category_param any;
  declare months any;
  declare feed_param any;
  declare feed_type varchar;

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

  -- Pass 1: collect .html and .md resources; note stems that have an HTML rendition
  all_rows := vector ();
  html_stems := dict_new (61);
  if (q = '''')
  {
    for (select RES_NAME as _name, RES_MOD_TIME as _mod, RES_CONTENT as _cont
           from WS.WS.SYS_DAV_RES
          where (RES_FULL_PATH like ''/DAV/www2.openlinksw.com/data/html/%.html''
              or RES_FULL_PATH like ''/DAV/www2.openlinksw.com/data/html/%.md'')
            and RES_NAME not like ''._%''
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
          where (RES_FULL_PATH like ''/DAV/www2.openlinksw.com/data/html/%.html''
              or RES_FULL_PATH like ''/DAV/www2.openlinksw.com/data/html/%.md'')
            and RES_NAME not like ''._%''
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
    declare category_match, scan_pos, semi_pos, cat_count, pin_val int;
    declare one_category, active_tag, rest_category, display_category varchar;
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
        -- Normalize common HTML title entities and UTF-8 punctuation bytes from blob_to_string.
        -- Keep emitted titles ASCII-safe so Virtuoso cannot re-mojibake smart punctuation.
        t := replace (t, ''&amp;'', ''&'');
        t := replace (t, ''&quot;'', chr(34));
        t := replace (t, ''&#39;'', chr(39));
        t := replace (t, ''&apos;'', chr(39));
        t := replace (t, ''&ndash;'', ''-'');
        t := replace (t, ''&mdash;'', ''-'');
        t := replace (t, ''&middot;'', ''-'');
        t := replace (t, ''&rarr;'', ''->'');
        t := replace (t, chr(226) || chr(134) || chr(146), ''->'');
        t := replace (t, chr(226) || chr(128) || chr(148), ''-'');
        t := replace (t, chr(226) || chr(128) || chr(147), ''-'');
        t := replace (t, chr(226) || chr(128) || chr(153), chr(39));
        t := replace (t, chr(194) || chr(183), ''-'');
        t := replace (t, chr(195) || chr(162) || chr(194) || chr(128) || chr(194) || chr(148), ''-'');
        t := replace (t, chr(195) || chr(162) || chr(194) || chr(128) || chr(194) || chr(147), ''-'');
        t := replace (t, chr(195) || chr(162) || chr(194) || chr(128) || chr(194) || chr(153), chr(39));
        t := replace (t, chr(195) || chr(162) || chr(194) || chr(134) || chr(194) || chr(146), ''->'');
        t := replace (t, chr(195) || chr(130) || chr(194) || chr(183), ''-'');
      }
    }
    else
    {
      -- Markdown title fallback: avoid escape-heavy line splitting in VSP compile path.
      t := stem;
    }
    if (t is null or t = '''')
      t := aref (r, 0);
    item_date := sprintf (''%04d-%02d-%02d'', year (aref (r, 1)), month (aref (r, 1)), dayofmonth (aref (r, 1)));
    if (from_date <> '''' and item_date < from_date)
      goto next_row;
    if (to_date <> '''' and item_date > to_date)
      goto next_row;
    dav_path := sprintf (''/DAV/www2.openlinksw.com/data/html/%s'', aref (r, 0));
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
    if (raw_category is null)
    {
      for (select CATEGORY as _stage_cat
             from DB.DBA.OPENLINK_HTML_DAV_CATEGORY_STAGE
            where PATH = dav_path) do
      {
        raw_category := _stage_cat;
      }
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
      category_cloud := concat (category_cloud, sprintf (''<a class="facet-option%V" href="/weblog/?category=%U&amp;q=%U&amp;from=%U&amp;to=%U"><span class="facet-name">%V</span><span class="facet-count">%d</span></a>'', facet_active, facet_category, q, from_date, to_date, facet_category, facet_count));
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
    http (''<title>OpenLink Software Weblog</title>
'');
    http (''<link>https://www.openlinksw.com/weblog/</link>
'');
    http (''<description>Linked Data, AI agents, knowledge graphs, and data spaces from a WebDAV folder.</description>
'');
    http (''<generator>Virtuoso Server Pages over WebDAV</generator>
'');
    for (i := 0; i < n; i := i + 1)
    {
      declare fname, ftitle varchar;
      declare fmod datetime;
      fname := aref (aref (posts, i), 0);
      fmod := aref (aref (posts, i), 1);
      ftitle := aref (aref (posts, i), 2);
      http (''<item>
'');
      http (sprintf (''<title>%V</title>
'', ftitle));
      http (sprintf (''<link>https://www.openlinksw.com/weblog/?post=%U</link>
'', fname));
      http (sprintf (''<guid isPermaLink="true">https://www.openlinksw.com/weblog/?post=%U</guid>
'', fname));
      http (sprintf (''<description>%V</description>
'', ftitle));
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
    http (''<title>OpenLink Software Weblog</title>
'');
    http (''<id>https://www.openlinksw.com/weblog/</id>
'');
    http (''<link href="https://www.openlinksw.com/weblog/"/>
'');
    http (''<link rel="self" type="application/atom+xml" href="https://www.openlinksw.com/weblog/?feed=atom"/>
'');
    if (n > 0)
    {
      declare umod datetime;
      umod := aref (aref (posts, 0), 1);
      http (sprintf (''<updated>%04d-%02d-%02dT00:00:00Z</updated>
'', year (umod), month (umod), dayofmonth (umod)));
    }
    else
      http (''<updated>2026-07-17T00:00:00Z</updated>
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
'', ftitle));
      http (sprintf (''<id>https://www.openlinksw.com/weblog/?post=%U</id>
'', fname));
      http (sprintf (''<link href="https://www.openlinksw.com/weblog/?post=%U"/>
'', fname));
      http (sprintf (''<updated>%04d-%02d-%02dT00:00:00Z</updated>
'', year (fmod), month (fmod), dayofmonth (fmod)));
      http (sprintf (''<summary>%V</summary>
'', ftitle));
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
    http (''<service xmlns="http://www.w3.org/2007/app" xmlns:atom="http://www.w3.org/2005/Atom"><workspace><atom:title>OpenLink Software Weblog</atom:title><collection href="https://www.openlinksw.com/data/html/"><atom:title>WebDAV Folder</atom:title></collection></workspace></service>
'');
    return;
  }

?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>OpenLink Software Weblog</title>
  <meta name="description" content="Weblog rendition of OpenLink Software published web pages: Linked Data, AI agents, knowledge graphs, and data spaces." />
  <link rel="alternate" type="application/rss+xml"  title="OpenLink Software Weblog (RSS 2.0)"  href="/weblog/?feed=rss" />
  <link rel="alternate" type="application/atom+xml" title="OpenLink Software Weblog (Atom 1.0)" href="/weblog/?feed=atom" />
  <link rel="service"   type="application/atomsvc+xml" title="AtomPub Service" href="/weblog/?feed=atomPub" />
  <style>
    :root {
      --openlink-navy: #07131d;
      --openlink-navy-2: #0d2233;
      --openlink-blue: #1599d3;
      --openlink-cyan: #5cc9e8;
      --openlink-teal: #2a9bb0;
      --openlink-silver: #d7e3ec;
      --accent: var(--openlink-blue);
      --accent-soft: rgba(21, 153, 211, 0.13);
      --accent-quiet: rgba(92, 201, 232, 0.28);
      --bg: #f5f8fb;
      --panel: rgba(255, 255, 255, 0.94);
      --text: #172838;
      --muted: #637486;
      --border: #d5e3ec;
      --rss: #f26522;
      --shadow: 0 14px 34px rgba(7, 19, 29, 0.10);
    }
    html[data-theme="light"] {
      --accent: var(--openlink-blue);
      --accent-soft: rgba(21, 153, 211, 0.13);
      --accent-quiet: rgba(92, 201, 232, 0.28);
      --bg: #f5f8fb;
      --panel: rgba(255, 255, 255, 0.94);
      --text: #172838;
      --muted: #637486;
      --border: #d5e3ec;
      --shadow: 0 14px 34px rgba(7, 19, 29, 0.10);
    }
    html[data-theme="dark"] {
      --accent: var(--openlink-cyan);
      --accent-soft: rgba(92, 201, 232, 0.13);
      --accent-quiet: rgba(92, 201, 232, 0.25);
      --bg: #07131d;
      --panel: rgba(12, 29, 43, 0.92);
      --text: #f1f7fb;
      --muted: #a8bac8;
      --border: rgba(92, 201, 232, 0.18);
      --shadow: 0 18px 42px rgba(0, 0, 0, 0.36);
    }
    @media (prefers-color-scheme: dark) {
      :root:not([data-theme="light"]) {
        --accent: var(--openlink-cyan);
        --accent-soft: rgba(92, 201, 232, 0.13);
        --accent-quiet: rgba(92, 201, 232, 0.25);
        --bg: #07131d;
        --panel: rgba(12, 29, 43, 0.92);
        --text: #f1f7fb;
        --muted: #a8bac8;
        --border: rgba(92, 201, 232, 0.18);
        --shadow: 0 18px 42px rgba(0, 0, 0, 0.36);
      }
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background:
        radial-gradient(circle at 9% 12%, rgba(92, 201, 232, 0.18), transparent 28rem),
        radial-gradient(circle at 88% 8%, rgba(21, 153, 211, 0.16), transparent 24rem),
        linear-gradient(135deg, var(--openlink-navy) 0%, #0a1722 45%, #111f2b 100%);
      color: var(--text);
      line-height: 1.5;
      min-height: 100vh;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      opacity: 0.26;
      background-image:
        linear-gradient(rgba(92, 201, 232, 0.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(92, 201, 232, 0.08) 1px, transparent 1px),
        radial-gradient(ellipse at 18% 18%, transparent 0 38%, rgba(92, 201, 232, 0.16) 39%, transparent 40%);
      background-size: 42px 42px, 42px 42px, 360px 220px;
      mix-blend-mode: screen;
    }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
    header.masthead {
      position: sticky;
      top: 0;
      z-index: 20;
      background: linear-gradient(135deg, rgba(7, 19, 29, 0.98), rgba(13, 34, 51, 0.96));
      border-bottom: 1px solid rgba(92, 201, 232, 0.24);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);
      padding: 1rem max(1.25rem, calc((100vw - 1380px) / 2));
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.75rem 1rem;
    }
    header.masthead h1 { margin: 0; font-size: 1.35rem; line-height: 1.15; }
    header.masthead h1 a { color: #f5fbff; }
    header.masthead .tagline { color: #b8c9d8; font-size: 0.9rem; flex: 1 1 420px; }
    .feed-buttons { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
    .theme-toggle {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 2rem;
      height: 2rem;
      border: 1px solid rgba(92, 201, 232, 0.34);
      border-radius: 4px;
      background: rgba(255, 255, 255, 0.08);
      color: #f5fbff;
      cursor: pointer;
    }
    .theme-toggle:hover { background: rgba(92, 201, 232, 0.18); }
    .theme-toggle svg { width: 14px; height: 14px; fill: none; stroke: currentColor; stroke-width: 2; }
    .theme-toggle .sun { display: none; }
    html[data-theme="light"] .theme-toggle .moon { display: none; }
    html[data-theme="light"] .theme-toggle .sun { display: block; }
    .feed-btn {
      display: inline-flex; align-items: center; justify-content: center; gap: 0.35rem;
      min-height: 2rem;
      font-size: 0.78rem; font-weight: 700;
      padding: 0.38rem 0.72rem; border-radius: 4px;
      color: #fff !important; text-decoration: none !important;
      white-space: nowrap;
    }
    .feed-btn.rss  { background: var(--rss); }
    .feed-btn.atom { background: linear-gradient(135deg, var(--openlink-blue), var(--openlink-cyan)); }
    .feed-btn svg { width: 12px; height: 12px; fill: currentColor; flex: 0 0 auto; }
    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(280px, 340px);
      gap: 1.25rem;
      max-width: 1380px;
      margin: 1.5rem auto 1.25rem;
      padding: 0 1.25rem;
      align-items: start;
    }
    @media (max-width: 900px) {
      header.masthead { align-items: flex-start; }
      .layout { grid-template-columns: 1fr; margin-top: 1rem; }
      .feed-buttons { width: 100%; }
      aside.sidebar {
        position: static;
        max-height: none;
      }
      aside.sidebar .panel {
        max-height: 55vh;
      }
    }
    article.post {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 6px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      box-shadow: var(--shadow);
    }
    article.post.embedded {
      background: transparent;
    }
    .post-head { padding: 1.2rem 1.4rem 1rem; border-bottom: 1px solid var(--border); }
    .post-kicker {
      display: inline-flex;
      align-items: center;
      min-height: 1.45rem;
      font-size: 0.68rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase;
      color: var(--accent);
      background: var(--accent-soft);
      border: 1px solid var(--accent-quiet);
      border-radius: 3px;
      padding: 0.18rem 0.5rem;
      margin-bottom: 0.6rem;
    }
    .post-head h2 { margin: 0 0 0.45rem; font-size: clamp(1.25rem, 1.1rem + 0.6vw, 1.7rem); line-height: 1.25; }

    .pin-badge {
      position: relative;
      display: inline-block;
      width: 0.66rem;
      height: 0.66rem;
      margin-right: 0.34rem;
      transform: rotate(-22deg);
      vertical-align: -0.06rem;
      flex: 0 0 auto;
    }
    .pin-badge::before {
      content: "";
      position: absolute;
      width: 0.42rem;
      height: 0.42rem;
      left: 0.12rem;
      top: 0.02rem;
      border-radius: 50%;
      background: #ef4444;
      border: 1px solid rgba(255, 255, 255, 0.92);
      box-shadow: 0 1px 4px rgba(239, 68, 68, 0.38);
    }
    .pin-badge::after {
      content: "";
      position: absolute;
      width: 0.1rem;
      height: 0.48rem;
      left: 0.31rem;
      top: 0.35rem;
      border-radius: 999px;
      background: linear-gradient(180deg, #f7d7c4, #805139);
      box-shadow: 0 1px 1px rgba(0, 0, 0, 0.26);
    }
    article.post { position: relative; }
    .post-status {
      display: flex;
      align-items: center;
      gap: 0.08rem;
      min-height: 2.15rem;
      padding: 0.46rem 0.72rem;
      border-bottom: 1px solid var(--border);
      background: linear-gradient(90deg, rgba(239, 68, 68, 0.11), rgba(92, 201, 232, 0.06) 62%, transparent);
      color: var(--muted);
      font-size: 0.68rem;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    article.post.embedded.pinned { background: var(--panel); }
    .post-kicker .pin-badge, .post-status .pin-badge { margin-right: 0.28rem; }
    .post-meta { color: var(--muted); font-size: 0.86rem; }
    .post-meta a { font-weight: 650; }
    .md-body {
      padding: 1.6rem 2rem 2rem;
      max-width: 900px;
      line-height: 1.68;
      font-size: 1rem;
    }
    .md-body h1 { font-size: 1.6rem; line-height: 1.2; }
    .md-body h2 { font-size: 1.28rem; border-bottom: 1px solid var(--border); padding-bottom: 0.35rem; }
    .md-body h3 { font-size: 1.1rem; }
    .md-body pre {
      background: var(--accent-soft);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.85rem 1rem;
      overflow-x: auto;
      font-size: 0.86rem;
    }
    .md-body code { background: var(--accent-soft); border-radius: 3px; padding: 0.1em 0.35em; font-size: 0.88em; }
    .md-body pre code { background: none; padding: 0; }
    .md-body blockquote {
      margin: 1em 0;
      padding: 0.25em 1em;
      border-left: 4px solid var(--accent);
      color: var(--muted);
    }
    .md-body table { border-collapse: collapse; margin: 1em 0; width: 100%; }
    .md-body th, .md-body td { border: 1px solid var(--border); padding: 0.4em 0.7em; }
    .post-body {
      background: #fff;
    }
    .post-frame {
      display: block;
      width: 100%;
      height: calc(100vh - 7.5rem);
      min-height: 420px;
      border: 0;
      background: #fff;
    }
    aside.sidebar {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      position: sticky;
      top: 5.25rem;
      max-height: calc(100vh - 6.5rem);
      min-height: 0;
    }
    .panel {
      background: linear-gradient(180deg, rgba(12, 29, 43, 0.94), rgba(8, 20, 31, 0.94));
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 1rem;
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.20);
      min-height: 0;
    }
    aside.sidebar .panel {
      overflow: auto;
      scrollbar-width: thin;
    }
    .panel h3 {
      margin: 0 0 0.75rem;
      font-size: 0.74rem; font-weight: 800;
      letter-spacing: 0.08em; text-transform: uppercase;
      color: var(--muted);
      border-bottom: 1px solid var(--border);
      padding-bottom: 0.55rem;
    }
    ul.archive { list-style: none; margin: 0; padding: 0; }
    ul.archive li {
      padding: 0.62rem 0;
      border-bottom: 1px solid var(--border);
    }
    ul.archive li:last-child { border-bottom: 0; }
    ul.archive .a-date { display: block; font-size: 0.72rem; color: var(--muted); margin-bottom: 0.16rem; }
    ul.archive a { line-height: 1.35; }
    ul.archive li.current { border-left: 3px solid var(--accent); padding-left: 0.65rem; margin-left: -0.65rem; background: linear-gradient(90deg, var(--accent-soft), transparent 70%); }
    ul.archive li.current a { font-weight: 700; }
    ul.archive li.pinned { background: linear-gradient(90deg, rgba(239, 68, 68, 0.08), transparent 72%); }
    ul.archive li.pinned:not(.current) { border-left: 3px solid rgba(239, 68, 68, 0.46); padding-left: 0.65rem; margin-left: -0.65rem; }
    .filter-form { display: grid; gap: 0.55rem; margin-bottom: 0.95rem; }
    .filter-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.45rem; }
    .filter-label { display: grid; gap: 0.18rem; color: var(--muted); font-size: 0.72rem; }
    .filter-input, .filter-select {
      width: 100%; min-height: 2.1rem; border: 1px solid var(--border); border-radius: 4px;
      background: rgba(255, 255, 255, 0.92); color: #172838; padding: 0.42rem 0.55rem; font: inherit; font-size: 0.84rem;
    }
    html[data-theme="dark"] .filter-input, html[data-theme="dark"] .filter-select { background: rgba(7, 19, 29, 0.92); color: #f1f7fb; }
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
    .facet-option {
      display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 0.55rem;
      min-height: 2rem; border: 1px solid rgba(92, 201, 232, 0.18); border-radius: 4px;
      background: rgba(92, 201, 232, 0.045); color: var(--text);
      padding: 0.34rem 0.45rem 0.34rem 0.55rem; text-decoration: none;
    }
    .facet-option:hover { border-color: var(--accent-quiet); background: var(--accent-soft); text-decoration: none; }
    .facet-option.is-active { border-color: var(--accent); background: linear-gradient(90deg, var(--accent-soft), rgba(92, 201, 232, 0.04)); box-shadow: inset 3px 0 0 var(--accent); }
    .facet-name { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.76rem; font-weight: 700; }
    .facet-count { min-width: 1.8rem; border-radius: 999px; background: rgba(92, 201, 232, 0.12); color: var(--accent); font-size: 0.68rem; font-weight: 850; text-align: center; padding: 0.12rem 0.34rem; }
    .facet-option.is-active .facet-count { background: var(--accent); color: #fff; }
    .a-category { display: none; }
    .results-panel { padding: 1.2rem 1.4rem 1.35rem; }
    .results-list { list-style: none; margin: 0; padding: 0; }
    .results-list li { padding: 0.8rem 0; border-bottom: 1px solid var(--border); }
    .results-list li:last-child { border-bottom: 0; }
    .results-list a { font-weight: 750; }
    .results-meta { color: var(--muted); font-size: 0.78rem; margin-top: 0.2rem; }
    footer.colophon {
      max-width: 1380px;
      margin: 0 auto 1.75rem;
      padding: 0 1.25rem;
      color: var(--muted);
      font-size: 0.8rem;
    }
    .footer-inner {
      border-top: 1px solid rgba(92, 201, 232, 0.22);
      padding-top: 1rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.6rem 1rem;
      justify-content: space-between;
      align-items: center;
    }
    .footer-copy {
      display: grid;
      gap: 0.28rem;
      max-width: 880px;
      line-height: 1.45;
    }
    .footer-primary { color: var(--fg); font-weight: 650; }
    .footer-provenance { color: var(--muted); }
    .footer-links {
      display: flex;
      flex-wrap: wrap;
      gap: 0.45rem 0.75rem;
      align-items: center;
    }
    .footer-links a { font-weight: 650; }
    .virtuoso-badge {
      display: inline-flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0.06rem;
      padding: 0.55rem 1.35rem;
      border: 2px solid var(--accent);
      border-radius: 50%;
      background: var(--panel);
      box-shadow: 0 4px 14px rgba(21, 153, 211, 0.22);
      text-decoration: none !important;
      line-height: 1.05;
      white-space: nowrap;
    }
    .virtuoso-badge:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(21, 153, 211, 0.30); text-decoration: none; }
    .virtuoso-badge .vb-powered { font-size: 0.56rem; font-weight: 650; letter-spacing: 0.14em; text-transform: lowercase; color: var(--muted); }
    .virtuoso-badge .vb-name { font-size: 0.95rem; font-weight: 850; letter-spacing: 0.02em; color: var(--accent); }
    /* Sidebar panel is always dark; pin its text to light ink so both themes stay readable. */
    .panel { color: #d9e6f0; }
    .panel h3, .facet-title, .filter-label, .filter-note, ul.archive .a-date { color: #9fb4c4; }
    .panel h3 { border-bottom-color: rgba(92, 201, 232, 0.22); }
    ul.archive li { border-bottom-color: rgba(92, 201, 232, 0.14); }
    ul.archive a, .facet-clear { color: var(--openlink-cyan); }
    .facet-box { border-top-color: rgba(92, 201, 232, 0.22); }
    .facet-option { color: #e8f2fa; border-color: rgba(92, 201, 232, 0.26); background: rgba(92, 201, 232, 0.07); }
    .facet-name { color: #e8f2fa; }
    .facet-option:hover { border-color: rgba(92, 201, 232, 0.5); background: rgba(92, 201, 232, 0.16); }
    .facet-count { color: var(--openlink-cyan); background: rgba(92, 201, 232, 0.16); }
    .facet-option.is-active { border-color: var(--openlink-cyan); background: linear-gradient(90deg, rgba(92, 201, 232, 0.20), rgba(92, 201, 232, 0.05)); box-shadow: inset 3px 0 0 var(--openlink-cyan); }
    .facet-option.is-active .facet-count { background: var(--openlink-cyan); color: #07131d; }
    .filter-submit { background: var(--openlink-blue); border-color: rgba(92, 201, 232, 0.5); }
    .filter-reset { background: rgba(92, 201, 232, 0.14); color: var(--openlink-cyan); border-color: rgba(92, 201, 232, 0.35); }
  </style>
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
  <header class="masthead">
    <h1><a href="/weblog/">OpenLink Software Weblog</a></h1>
    <span class="tagline">Showcasing the power of loosely coupling Linked Data, AI Agents, Skills, and <span class="term-help" title="databases, knowledge bases, filesystems, and APIs">Data Spaces</span> &mdash; a Weblog view of <a href="/data/html/" target="_top" rel="noopener noreferrer">WebDAV Folder</a></span>
    <nav class="feed-buttons">
      <a class="feed-btn rss" href="/weblog/?feed=rss" type="application/rss+xml" title="Subscribe via RSS 2.0">
        <svg viewBox="0 0 24 24"><path d="M6.18 17.82a2.18 2.18 0 1 1-4.36 0 2.18 2.18 0 0 1 4.36 0zM1.82 8.73v3.27c5.02 0 9.09 4.07 9.09 9.09h3.27c0-6.83-5.53-12.36-12.36-12.36zM1.82 2.18v3.27c8.03 0 14.55 6.52 14.55 14.55h3.27C19.64 10.16 11.66 2.18 1.82 2.18z"/></svg>
        RSS
      </a>
      <a class="feed-btn atom" href="/weblog/?feed=atom" type="application/atom+xml" title="Subscribe via Atom 1.0">
        <svg viewBox="0 0 24 24"><path d="M6.18 17.82a2.18 2.18 0 1 1-4.36 0 2.18 2.18 0 0 1 4.36 0zM1.82 8.73v3.27c5.02 0 9.09 4.07 9.09 9.09h3.27c0-6.83-5.53-12.36-12.36-12.36zM1.82 2.18v3.27c8.03 0 14.55 6.52 14.55 14.55h3.27C19.64 10.16 11.66 2.18 1.82 2.18z"/></svg>
        Atom
      </a>
      <button class="theme-toggle" type="button" aria-label="Toggle light and dark theme" title="Toggle theme" data-theme-toggle>
        <svg class="moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12.8A8.8 8.8 0 1 1 11.2 3 6.8 6.8 0 0 0 21 12.8z"/></svg>
        <svg class="sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/></svg>
      </button>
    </nav>
  </header>

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
      http (sprintf (''<a href="/weblog/?post=%U">%V</a>'', rname, rtitle));
      if (rcat <> '''') http (sprintf (''<span class="a-category">%V</span>'', rcat));
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

    if (cext = ''html'')
    {
      if (cpin)
        http (''<article class="post embedded pinned"><div class="post-status" aria-label="Pinned post"><span class="pin-badge" aria-hidden="true"></span><span>Pinned post</span></div>'');
      else
        http (''<article class="post embedded">'');
      http (sprintf (''<div class="post-body"><iframe class="post-frame" src="/data/html/%U" title="%V" loading="lazy" sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox allow-top-navigation-by-user-activation"></iframe></div>'', cname, ctitle));
      http (''</article>'');
    }
    else
    {
      if (cpin)
        http (''<article class="post pinned">'');
      else
        http (''<article class="post">'');
      http (''<div class="post-head">'');
      if (cpin)
        http (sprintf (''<span class="post-kicker"><span class="pin-badge" aria-hidden="true"></span>Pinned &mdash; %V</span>'', cdate));
      else if (idx = 0)
        http (sprintf (''<span class="post-kicker">Latest Post &mdash; %V</span>'', cdate));
      else
        http (sprintf (''<span class="post-kicker">From the Archive &mdash; %V</span>'', cdate));
      http (sprintf (''<h2>%V</h2>'', ctitle));
      http (sprintf (''<div class="post-meta">Published %V &middot; <a href="/data/html/%U" target="_blank">Open standalone page &rarr;</a></div>'', cdate, cname));
      http (''</div>'');
      http (sprintf (''<div class="post-body"><iframe class="post-frame" src="/data/html/%U" title="%V" loading="lazy" sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox allow-top-navigation-by-user-activation"></iframe></div>'', cname, ctitle));
      http (''</article>'');
    }
  }
?>
    <aside class="sidebar">
      <div class="panel">
        <h3>Recent Posts (<?= n ?> posts)</h3>
        <form class="filter-form" method="get" action="/weblog/" aria-label="Search and filter posts">
          <input class="filter-input" type="search" name="q" value="<?= q ?>" placeholder="Search this DAV collection" aria-label="Search this DAV collection" />
          <div class="filter-row">
            <label class="filter-label">From <input class="filter-input" type="date" name="from" value="<?= from_date ?>" /></label>
            <label class="filter-label">To <input class="filter-input" type="date" name="to" value="<?= to_date ?>" /></label>
          </div>
<?vsp if (has_categories) { ?>
          <div class="facet-box" aria-label="Filter posts by category">
            <div class="facet-head">
              <span class="facet-title">Categories</span>
              <a class="facet-clear" href="/weblog/?q=<?= q ?>&amp;from=<?= from_date ?>&amp;to=<?= to_date ?>">All <?= all_count ?></a>
            </div>
            <div class="facet-list">
<?vsp http (category_cloud); ?>
            </div>
          </div>
<?vsp } ?>
          <div class="filter-actions">
            <button class="filter-submit" type="submit">Apply</button>
            <a class="filter-reset" href="/weblog/">Reset</a>
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
    aname  := aref (aref (posts, i), 0);
    amod   := aref (aref (posts, i), 1);
    atitle := aref (aref (posts, i), 2);
    acategory := aref (aref (posts, i), 4);
    apin := cast (aref (aref (posts, i), 6) as int);
    adate  := sprintf (''%s %d, %d'', aref (months, month (amod) - 1), dayofmonth (amod), year (amod));
    declare cls varchar;
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
    http (sprintf (''<a href="/weblog/?post=%U">%V</a>'', aname, atitle));
    if (acategory <> '''')
      http (sprintf (''<span class="a-category">%V</span>'', acategory));
    http (''</li>'');
  }
?>
        </ul>
      </div>
    </aside>
  </div>

  <footer class="colophon" aria-label="Weblog metadata">
    <div class="footer-inner">
      <div class="footer-copy">
        <span class="footer-primary">Published from <a href="/data/html/" target="_top" rel="noopener noreferrer">WebDAV Folder</a> using <a href="https://virtuoso.openlinksw.com/" target="_blank" rel="noopener noreferrer">OpenLink Virtuoso</a> Server Pages over Virtuoso WebDAV.</span>
        <span class="footer-provenance">Weblog engine by <a href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/weblog-from-webdav" target="_blank" rel="noopener noreferrer">weblog-from-webdav</a> and GPT-5 Chat Codex on behalf of <a href="https://linkeddata.uriburner.com/describe/?url=https%3A%2F%2Fwww.linkedin.com%2Fin%2Fkidehen%23this" target="_blank" rel="noopener noreferrer">Kingsley Idehen</a>, operated by <a href="https://www.openlinksw.com/" target="_blank" rel="noopener noreferrer">OpenLink Software</a>.</span>
      </div>
      <a class="virtuoso-badge" href="https://virtuoso.openlinksw.com/" target="_blank" rel="noopener noreferrer" title="Powered by OpenLink Virtuoso" aria-label="Powered by OpenLink Virtuoso">
        <span class="vb-powered">powered by</span>
        <span class="vb-name">Virtuoso</span>
      </a>
      <nav class="footer-links" aria-label="Subscription links">
        <a href="/weblog/?feed=rss">RSS</a>
        <a href="/weblog/?feed=atom">Atom</a>
        <a href="/weblog/?feed=atomPub">AtomPub</a>
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
    function readableFrameDocument (frame) {
      try {
        if (frame && frame.getAttribute && frame.getAttribute(''data-weblog-opaque-frame'') === ''1'') return null;
        var win = frame.contentWindow;
        if (!win) return null;
        var doc = frame.contentDocument || win.document;
        if (!doc || !doc.documentElement) return null;
        return doc;
      } catch (e) {
        try { frame.setAttribute(''data-weblog-opaque-frame'', ''1''); } catch (ignore) {}
        return null;
      }
    }
    function routeFrameCollectionLinks (frame, doc) {
      if (!doc || !doc.documentElement || doc.documentElement.getAttribute(''data-weblog-link-routing'') === ''1'') return;
      doc.documentElement.setAttribute(''data-weblog-link-routing'', ''1'');
      doc.addEventListener(''click'', function (event) {
        var node = event.target;
        var link = null;
        while (node && node !== doc) {
          if (node.tagName && node.tagName.toLowerCase() === ''a'' && node.getAttribute(''href'')) { link = node; break; }
          node = node.parentNode;
        }
        if (!link) return;
        var raw = link.getAttribute(''href'');
        if (!raw || raw.charAt(0) === ''#'') return;
        var url = null;
        try { url = new URL(raw, frame.src || window.location.href); } catch (e) { return; }
        if (url.origin !== window.location.origin) return;
        var path = url.pathname;
        var isCollection = path.charAt(path.length - 1) === ''/'' && (path.indexOf(''/DAV/'') === 0 || path.indexOf(''/data/'') === 0);
        if (!isCollection) return;
        event.preventDefault();
        window.top.location.href = url.href;
      }, true);
    }
    window.weblogReadableFrameDocument = readableFrameDocument;
    window.weblogRouteFrameCollectionLinks = routeFrameCollectionLinks;
    function applyThemeToFrame (frame, theme) {
      try {
        var doc = readableFrameDocument(frame);
        if (!doc || !doc.documentElement) return;
        doc.documentElement.setAttribute(''data-theme'', theme);
        doc.documentElement.setAttribute(''data-weblog-frame-theme'', theme);
        doc.documentElement.style.colorScheme = theme;
        if (doc.body) {
          doc.body.setAttribute(''data-theme'', theme);
          doc.body.setAttribute(''data-weblog-frame-theme'', theme);
          doc.body.classList.toggle(''dark'', theme === ''dark'');
          doc.body.classList.toggle(''light'', theme === ''light'');
          doc.body.classList.toggle(''dark-mode'', theme === ''dark'');
          doc.body.classList.toggle(''light-mode'', theme === ''light'');
        }
        if (!doc.getElementById(''weblog-frame-theme-style'')) {
          var style = doc.createElement(''style'');
          style.id = ''weblog-frame-theme-style'';
          style.textContent = ''html[data-weblog-frame-theme="dark"]{color-scheme:dark;background:#07131d!important;--ink:#f1f7fb;--text:#f1f7fb;--muted:#a8bac8;--line:rgba(92,201,232,.24);--soft:#0d2233;--paper:#07131d;--panel:#0d2233;--card:#10283a;--bg:#07131d;--background:#07131d;--accent:#5cc9e8;--accent-2:#f28a55;--accent2:#5cc9e8;--code:#e8f3fa;--mark:#27313f}html[data-weblog-frame-theme="dark"] body{background:var(--paper)!important;color:var(--ink)!important}html[data-weblog-frame-theme="dark"] .topbar{background:rgba(7,19,29,.94)!important}html[data-weblog-frame-theme="dark"] section,html[data-weblog-frame-theme="dark"] main,html[data-weblog-frame-theme="dark"] article{border-color:rgba(92,201,232,.22)}html[data-weblog-frame-theme="dark"] a{color:#5cc9e8}html[data-weblog-frame-theme="light"]{color-scheme:light}'';
          (doc.head || doc.documentElement).appendChild(style);
        }
        try { frame.contentWindow.localStorage.setItem(''theme'', theme); } catch (e) {}
        try { frame.contentWindow.localStorage.setItem(''weblog-theme'', theme); } catch (e) {}
        try { frame.contentWindow.localStorage.setItem(''color-theme'', theme); } catch (e) {}
      } catch (e) {}
    }
    window.weblogApplyThemeToFrames = function () {
      var theme = currentTheme();
      var frames = document.querySelectorAll(''.post-frame'');
      for (var i = 0; i < frames.length; i++) applyThemeToFrame(frames[i], theme);
    };
    function labelTheme () {
      var next = currentTheme() === ''dark'' ? ''light'' : ''dark'';
      button.setAttribute(''aria-label'', ''Switch frame and weblog chrome to '' + next + '' theme'');
      button.setAttribute(''title'', ''Switch frame and weblog chrome to '' + next + '' theme'');
    }
    button.addEventListener(''click'', function () {
      var next = currentTheme() === ''dark'' ? ''light'' : ''dark'';
      document.documentElement.setAttribute(''data-theme'', next);
      try { window.localStorage.setItem(''weblog-theme'', next); } catch (e) {}
      window.weblogApplyThemeToFrames();
      labelTheme();
    });
    labelTheme();
    window.weblogApplyThemeToFrames();
  })();
  </script>

  <script>
  (function () {
    if (window.location.pathname === ''/data/html/index.vsp'') {
      window.location.replace(''/weblog/'' + window.location.search + window.location.hash);
    }
  })();
  </script>

  <script>
  (function () {
    var idleDelay = 180000;
    function frameViewportHeight () {
      return Math.max(420, window.innerHeight - 120);
    }
    function fitFrameWithoutBlankTail (frame) {
      try {
        var doc = window.weblogReadableFrameDocument ? window.weblogReadableFrameDocument(frame) : null;
        if (!doc || !doc.body) return;
        var html = doc.documentElement;
        var body = doc.body;
        var contentHeight = Math.max(
          body.scrollHeight, body.offsetHeight,
          html.clientHeight, html.scrollHeight, html.offsetHeight
        );
        if (contentHeight > 0) {
          frame.style.height = Math.min(contentHeight + 2, frameViewportHeight()) + ''px'';
        }
      } catch (e) {}
    }
    function installFrameControlBehavior (frame) {
      try {
        var win = frame.contentWindow;
        var doc = window.weblogReadableFrameDocument ? window.weblogReadableFrameDocument(frame) : null;
        if (!win || !doc || !doc.head) return;
        if (window.weblogRouteFrameCollectionLinks) window.weblogRouteFrameCollectionLinks(frame, doc);
        fitFrameWithoutBlankTail(frame);
        if (!doc.getElementById(''weblog-nav-idle-style'')) {
          var style = doc.createElement(''style'');
          style.id = ''weblog-nav-idle-style'';
          style.textContent = ''#float-nav.weblog-controls-idle,[aria-label="Section navigation"].weblog-controls-idle{opacity:0;pointer-events:none;transform:translateY(-8px);transition:opacity 220ms ease,transform 220ms ease}#float-nav,[aria-label="Section navigation"]{transition:opacity 220ms ease,transform 220ms ease}'';
          doc.head.appendChild(style);
        }
        var controls = doc.querySelectorAll(''#float-nav,[aria-label="Section navigation"]'');
        if (!controls.length) return;
        var timer = null;
        function setIdle () {
          for (var i = 0; i < controls.length; i++) controls[i].classList.add(''weblog-controls-idle'');
        }
        function wake () {
          for (var i = 0; i < controls.length; i++) controls[i].classList.remove(''weblog-controls-idle'');
          if (timer) win.clearTimeout(timer);
          timer = win.setTimeout(setIdle, idleDelay);
        }
        [''mousemove'',''mousedown'',''keydown'',''touchstart'',''wheel'',''scroll'',''pointermove''].forEach(function (evt) {
          doc.addEventListener(evt, wake, {passive:true});
        });
        wake();
      } catch (e) {}
    }
    var frames = document.querySelectorAll(''.post-frame'');
    for (var i = 0; i < frames.length; i++) {
      frames[i].addEventListener(''load'', function () { installFrameControlBehavior(this); });
    }
    window.addEventListener(''resize'', function () {
      for (var i = 0; i < frames.length; i++) fitFrameWithoutBlankTail(frames[i]);
    });
  })();
  </script>
</body>
</html>
';

  vsp_stream := string_output ();
  http (vsp_content, vsp_stream);

  -- 1. Upload the VSP page into the DAV collection (internal call, no DAV auth needed)
  DB.DBA.DAV_DELETE_INT ('/DAV/www2.openlinksw.com/data/html/index.vsp', 1, null, null, 0);
  rc := DB.DBA.DAV_RES_UPLOAD_STRSES_INT (
          '/DAV/www2.openlinksw.com/data/html/index.vsp',
          vsp_stream,
          'text/html',
          '111101101R',
          'dav',
          null,
          null,
          null,
          0);
  if (rc < 0)
    signal ('42000', sprintf ('DAV upload failed, rc=%d', rc));

  -- Seed the default pin when no explicit schema:position pin exists yet.
  DB.DBA.TMP_DEPLOY_WEBLOG_DEFAULT_PIN ('/DAV/www2.openlinksw.com/data/html/', 'dav');

  -- 2. Map /weblog/ as a VSP-enabled DAV directory for the exact entry point
  for (select distinct HP_LISTEN_HOST as _lh, HP_HOST as _vh
         from DB.DBA.HTTP_PATH where HP_LPATH in ('/DAV', '/public_home')) do
  {
    DB.DBA.TMP_DEPLOY_WEBLOG_VHOST_REMOVE (_lh, _vh, '/weblog');
    DB.DBA.TMP_DEPLOY_WEBLOG_VHOST_REMOVE (_lh, _vh, '/weblog/');
    DB.DBA.VHOST_DEFINE (lhost=>_lh, vhost=>_vh, lpath=>'/weblog/',
                         ppath=>'/DAV/www2.openlinksw.com/data/html/',
                         is_dav=>1,
                         is_brws=>0,
                         def_page=>'index.vsp',
                         vsp_user=>'dba',
                         ses_vars=>0,
                         opts=>vector ('browse_sheet', '', 'noinherit', 'yes'),
                         is_default_host=>0);
  }
}
;

DB.DBA.TMP_DEPLOY_WEBLOG ();
DROP PROCEDURE DB.DBA.TMP_DEPLOY_WEBLOG;
DROP PROCEDURE DB.DBA.TMP_DEPLOY_WEBLOG_DEFAULT_PIN;
DROP PROCEDURE DB.DBA.TMP_DEPLOY_WEBLOG_VHOST_REMOVE;

-- Verification
SELECT HP_LISTEN_HOST, HP_HOST, HP_LPATH, HP_PPATH, HP_RUN_VSP_AS, HP_OPTIONS FROM DB.DBA.HTTP_PATH WHERE HP_LPATH like '/weblog%';
SELECT R.RES_FULL_PATH, R.RES_PERMS, U.U_NAME AS RES_OWNER, G.G_NAME AS RES_GROUP, length (R.RES_CONTENT) AS CONTENT_LENGTH FROM WS.WS.SYS_DAV_RES R LEFT JOIN WS.WS.SYS_DAV_USER U ON R.RES_OWNER = U.U_ID LEFT JOIN WS.WS.SYS_DAV_GROUP G ON R.RES_GROUP = G.G_ID WHERE R.RES_FULL_PATH = '/DAV/www2.openlinksw.com/data/html/index.vsp';
