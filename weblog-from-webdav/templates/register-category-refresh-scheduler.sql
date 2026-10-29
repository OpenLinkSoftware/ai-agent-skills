-- Register scheduled schema:category refresh for WebDAV weblog posts.
-- Default scheduler interval: 5 minutes.
--
-- Purpose:
--   Backfill/repair category metadata for files copied into a WebDAV weblog
--   collection by tools that do not run the WebDAV publish-with-metadata helper.
--
-- Usage examples are at the end of this file.

USE DB;

CREATE PROCEDURE DB.DBA.TMP_WEBLOG_CATEGORY_REFRESH_DROP ()
{
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_DAV_UNSCHEDULE_CATEGORY_REFRESH'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_DAV_SCHEDULE_CATEGORY_REFRESH'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_DAV_REFRESH_CATEGORIES'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_DAV_INFER_CATEGORIES'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_DAV_CATEGORY_APPEND'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_DAV_CATEGORY_NORM'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_DAV_CATEGORY_TERM_COUNT'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_DAV_CATEGORY_STRIP_BLOCKS'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_DAV_GENERIC_SIGNALS'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_DAV_CATEGORY_ALIASES'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_DAV_CATEGORY_RENAMES'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_DAV_ACTIVE_CATEGORY_ALIASES'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_DAV_APPLY_CATEGORY_ALIASES'); }
  { DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; }; exec ('DROP PROCEDURE DB.DBA.WEBLOG_DAV_IS_AUTO_CATEGORIES'); }
}
;
DB.DBA.TMP_WEBLOG_CATEGORY_REFRESH_DROP ();
DROP PROCEDURE DB.DBA.TMP_WEBLOG_CATEGORY_REFRESH_DROP;

CREATE PROCEDURE DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (IN cats VARCHAR, IN label VARCHAR)
{
  IF (label IS NULL OR trim (label) = '')
    RETURN cats;
  IF (cats IS NULL OR cats = '')
    RETURN label;
  IF (strstr (cats, label) IS NOT NULL)
    RETURN cats;
  RETURN concat (cats, '; ', label);
}
;

-- Lower-case; drop tags and entities; and collapse everything that is not
-- a-z/0-9 to single spaces, padded with a space at each end -- so a term
-- matches only as whole words: ' api ' never matches 'rapid', ' rest '
-- never matches 'interest'.
CREATE PROCEDURE DB.DBA.WEBLOG_DAV_CATEGORY_NORM (IN s LONG VARCHAR)
{
  IF (s IS NULL) RETURN ' ';
  s := regexp_replace (s, '<[^>]*>', ' ', 1, null);
  s := regexp_replace (s, '&[A-Za-z#0-9]+;', ' ', 1, null);
  RETURN concat (' ', regexp_replace (lower (s), '[^a-z0-9]+', ' ', 1, null), ' ');
}
;

-- Cut every <tag ...>...</tag> block out of already lower-cased HTML. A
-- plain locate() loop, not regexp_replace: a lazy '<script\b.*?</script>'
-- silently replaces nothing once a block passes the regex engine's match
-- limit (a ~160 KB inline script on a generated infographic page), which
-- left all of that page's script text in the category counts.
CREATE PROCEDURE DB.DBA.WEBLOG_DAV_CATEGORY_STRIP_BLOCKS (IN lower_html LONG VARCHAR, IN tag VARCHAR)
{
  DECLARE out_ses ANY;
  DECLARE open_pat, close_pat VARCHAR;
  DECLARE pos, start_pos, end_pos, next_char INTEGER;
  open_pat := concat ('<', tag);
  close_pat := concat ('</', tag, '>');
  out_ses := string_output ();
  pos := 1;
  WHILE (1)
  {
    start_pos := locate (open_pat, lower_html, pos);
    -- '<head' must not match '<header': the next character has to end the
    -- tag name.
    WHILE (start_pos > 0)
    {
      next_char := case when start_pos + length (open_pat) <= length (lower_html)
                        then lower_html[start_pos - 1 + length (open_pat)] else 62 end;
      IF (next_char = 62 OR next_char = 32 OR next_char = 9 OR next_char = 10 OR next_char = 13 OR next_char = 47)
        GOTO open_found;
      start_pos := locate (open_pat, lower_html, start_pos + 1);
    }
    open_found:
    IF (start_pos = 0)
    {
      http (subseq (lower_html, pos - 1), out_ses);
      RETURN string_output_string (out_ses);
    }
    http (subseq (lower_html, pos - 1, start_pos - 1), out_ses);
    http (' ', out_ses);
    end_pos := locate (close_pat, lower_html, start_pos);
    IF (end_pos = 0)
      RETURN string_output_string (out_ses);
    pos := end_pos + length (close_pat);
  }
}
;

-- Whole-word occurrences of term in a WEBLOG_DAV_CATEGORY_NORM text,
-- counted up to cap (counting further changes nothing).
CREATE PROCEDURE DB.DBA.WEBLOG_DAV_CATEGORY_TERM_COUNT (IN norm_text LONG VARCHAR, IN term VARCHAR, IN cap INTEGER)
{
  DECLARE pat VARCHAR;
  DECLARE n, pos INTEGER;
  pat := concat (' ', term, ' ');
  n := 0;
  pos := locate (pat, norm_text, 1);
  WHILE (pos > 0 AND n < cap)
  {
    n := n + 1;
    pos := locate (pat, norm_text, pos + length (pat) - 1);
  }
  RETURN n;
}
;

-- The generic profile's labels and their whole-word terms. Kept in step
-- with detect_generic_categories in scripts/publish_with_metadata.py.
CREATE PROCEDURE DB.DBA.WEBLOG_DAV_GENERIC_SIGNALS ()
{
  RETURN vector (
    vector ('Semantic Web, RDF, & Linked Data', vector ('linked data', 'semantic web', 'rdf', 'ontology', 'ontologies')),
    vector ('Knowledge Graphs', vector ('knowledge graph', 'knowledge graphs')),
    vector ('AI Agents & LLMs', vector ('ai', 'agent', 'agents', 'ai agent', 'ai agents', 'agentic', 'llm', 'llms', 'chatgpt', 'gpt', 'claude', 'anthropic', 'openai', 'gemini')),
    vector ('APIs, Protocols, & Agent Skills', vector ('api', 'apis', 'rest api', 'oauth', 'mcp', 'a2a', 'agent skill', 'agent skills')),
    vector ('Virtuoso Platform', vector ('virtuoso', 'webdav', 'vsp', 'sparql', 'spasql', 'sql', 'uriburner')),
    vector ('Analytics & Data Engineering', vector ('analytics', 'data engineering', 'etl', 'elt', 'lakehouse', 'data warehouse')),
    vector ('Identity, Security, & Privacy', vector ('security', 'privacy', 'webid', 'identity', 'certificate', 'authentication')),
    vector ('Cloud Storage & S3', vector ('s3', 'bucket', 'object storage', 'cloud storage')),
    vector ('FIFA World Cup & Football', vector ('fifa', 'world cup', 'football', 'soccer')));
}
;

-- Earlier spellings of a label -> the current one, applied to every post's
-- existing tags on each refresh. Labels with three or more items take the
-- Oxford comma (2026-10-15); posts tagged before that keep the old
-- spelling until renamed, which would otherwise show each such label as
-- two facets.
CREATE PROCEDURE DB.DBA.WEBLOG_DAV_CATEGORY_RENAMES ()
{
  RETURN vector (
    'Semantic Web, RDF & Linked Data', 'Semantic Web, RDF, & Linked Data',
    'APIs, Protocols & Agent Skills', 'APIs, Protocols, & Agent Skills',
    'Identity, Security & Privacy', 'Identity, Security, & Privacy',
    'Semantic Web, RDF & Ontologies', 'Semantic Web, RDF, & Ontologies',
    'Analytics, Data Engineering & ERA', 'Analytics, Data Engineering, & ERA',
    'Database, SQL & PostgreSQL', 'Database, SQL, & PostgreSQL',
    'WebDAV, ODS & Collaboration', 'WebDAV, ODS, & Collaboration',
    'Presentation, Infographic & Visual Explanation', 'Presentation, Infographic, & Visual Explanation');
}
;

-- Generic label -> an established equivalent. Used only in a collection
-- where the equivalent is already in use (i.e. it was curated with its own
-- vocabulary, like the openlinksw.com weblog), so automatic tags join the
-- existing facets instead of creating near-duplicates beside them.
CREATE PROCEDURE DB.DBA.WEBLOG_DAV_CATEGORY_ALIASES ()
{
  RETURN vector (
    'Semantic Web, RDF, & Linked Data', 'Semantic Web, RDF, & Ontologies',
    'Knowledge Graphs', 'Knowledge Graphs & Linked Data',
    'AI Agents & LLMs', 'AI Engineering & LLMs',
    'Analytics & Data Engineering', 'Analytics, Data Engineering, & ERA',
    'APIs, Protocols, & Agent Skills', 'OPAL & Agentic AI',
    'WebDAV Published Documents', 'OpenLink Technical Content');
}
;

-- The aliases whose target label some post in coll already carries.
CREATE PROCEDURE DB.DBA.WEBLOG_DAV_ACTIVE_CATEGORY_ALIASES (IN coll VARCHAR)
{
  DECLARE aliases, active, seen ANY;
  DECLARE i INTEGER;
  aliases := DB.DBA.WEBLOG_DAV_CATEGORY_ALIASES ();
  seen := dict_new (31);
  FOR SELECT P.PROP_VALUE AS _v
        FROM WS.WS.SYS_DAV_RES R, WS.WS.SYS_DAV_PROP P
       WHERE R.RES_FULL_PATH LIKE coll || '%'
         AND P.PROP_PARENT_ID = R.RES_ID
         AND P.PROP_TYPE = 'R'
         AND P.PROP_NAME = 'schema:category' DO
  {
    DECLARE parts ANY;
    DECLARE j INTEGER;
    IF (isstring (_v))
    {
      -- Through the renames first: on the run that renames a collection's
      -- tags, its curated labels still carry the old spelling.
      parts := split_and_decode (DB.DBA.WEBLOG_DAV_APPLY_CATEGORY_ALIASES (
        trim (cast (_v AS VARCHAR)), DB.DBA.WEBLOG_DAV_CATEGORY_RENAMES ()), 0, '\0\0;');
      FOR (j := 0; j < length (parts); j := j + 1)
        dict_put (seen, trim (parts[j]), 1);
    }
  }
  active := vector ();
  FOR (i := 0; i < length (aliases); i := i + 2)
    IF (dict_get (seen, aliases[i + 1], 0))
      active := vector_concat (active, vector (aliases[i], aliases[i + 1]));
  RETURN active;
}
;

-- Map each label in a '; '-joined list through active aliases, dropping
-- duplicates (exact match, not substring: 'Knowledge Graphs' is a
-- substring of 'Knowledge Graphs & Linked Data').
CREATE PROCEDURE DB.DBA.WEBLOG_DAV_APPLY_CATEGORY_ALIASES (IN cats VARCHAR, IN active ANY)
{
  DECLARE parts, seen ANY;
  DECLARE out_cats, lab VARCHAR;
  DECLARE i, j INTEGER;
  IF (cats IS NULL OR cats = '' OR length (active) = 0) RETURN cats;
  parts := split_and_decode (cats, 0, '\0\0;');
  seen := dict_new (17);
  out_cats := '';
  FOR (i := 0; i < length (parts); i := i + 1)
  {
    lab := trim (parts[i]);
    FOR (j := 0; j < length (active); j := j + 2)
      IF (lab = active[j]) lab := active[j + 1];
    IF (lab <> '' AND dict_get (seen, lab, 0) = 0)
    {
      dict_put (seen, lab, 1);
      out_cats := case when out_cats = '' then lab else concat (out_cats, '; ', lab) end;
    }
  }
  RETURN out_cats;
}
;

-- 1 when every label in cats is one the generic profile produces, i.e., the
-- tags were assigned automatically rather than curated by hand.
CREATE PROCEDURE DB.DBA.WEBLOG_DAV_IS_AUTO_CATEGORIES (IN cats VARCHAR)
{
  DECLARE parts, signals ANY;
  DECLARE i, j, is_known INTEGER;
  IF (cats IS NULL OR trim (cats) = '') RETURN 0;
  signals := DB.DBA.WEBLOG_DAV_GENERIC_SIGNALS ();
  parts := split_and_decode (cats, 0, '\0\0;');
  FOR (i := 0; i < length (parts); i := i + 1)
  {
    IF (trim (parts[i]) <> '')
    {
      is_known := case when trim (parts[i]) = 'WebDAV Published Documents' then 1 else 0 end;
      FOR (j := 0; j < length (signals); j := j + 1)
        IF (trim (parts[i]) = signals[j][0]) is_known := 1;
      IF (is_known = 0) RETURN 0;
    }
  }
  RETURN 1;
}
;

CREATE PROCEDURE DB.DBA.WEBLOG_DAV_INFER_CATEGORIES
  (
    IN content LONG VARCHAR,
    IN profile VARCHAR := 'generic'
  )
{
  DECLARE lower_text LONG VARCHAR;
  DECLARE cats VARCHAR;

  lower_text := lower (content);
  cats := '';
  IF (profile IS NULL OR profile = '') profile := 'generic';

  IF (profile = 'fifa-player-reports' OR (strstr (lower_text, 'player intelligence report') IS NOT NULL AND strstr (lower_text, 'fifa world cup') IS NOT NULL))
  {
    cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'FIFA Player Intelligence Reports');
    cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'FIFA World Cup 2026');

    IF (lower_text LIKE '%(spain,%')
      cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'National Team: Spain');
    ELSE IF (lower_text LIKE '%(france,%')
      cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'National Team: France');
    ELSE IF (lower_text LIKE '%(argentina,%')
      cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'National Team: Argentina');
    ELSE IF (lower_text LIKE '%(egypt,%')
      cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'National Team: Egypt');
    ELSE IF (lower_text LIKE '%(colombia,%')
      cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'National Team: Colombia');
    ELSE IF (lower_text LIKE '%(england,%')
      cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'National Team: England');
    ELSE IF (lower_text LIKE '%(norway,%')
      cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'National Team: Norway');
    ELSE IF (lower_text LIKE '%(morocco,%')
      cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'National Team: Morocco');

    IF (lower_text LIKE '% forward %')
      cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'Position: Forward');
    ELSE IF (lower_text LIKE '% midfielder %')
      cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'Position: Midfielder');
    ELSE IF (lower_text LIKE '% defender %')
      cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'Position: Defender');
    ELSE IF (lower_text LIKE '% goalkeeper %')
      cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'Position: Goalkeeper');

    IF (strstr (lower_text, 'shot map') IS NOT NULL OR strstr (lower_text, 'creation map') IS NOT NULL OR strstr (lower_text, 'temporal analytics') IS NOT NULL)
      cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'Player Analytics');

    RETURN cats;
  }

  -- Generic profile: whole-word terms, and a label only when the post is
  -- ABOUT it -- a term in its title, meta description, or first <h1>, or
  -- repeated at least 20 times in the visible body. Plain substring tests
  -- over the whole page ('api' in 'rapid', 'rest' in 'interest', 'rdf' in
  -- every generated page's boilerplate) put the top labels on 287-289 of
  -- the URIBurner weblog's 291 posts, so the facets filtered nothing;
  -- tuned against those 291 posts (about 2 labels per post, none on more
  -- than two thirds of them).
  {
    DECLARE about_text, body_text LONG VARCHAR;
    DECLARE signals, terms ANY;
    DECLARE i, j, hits INTEGER;

    about_text := DB.DBA.WEBLOG_DAV_CATEGORY_NORM (concat (
      coalesce (regexp_substr ('(?is)<title[^>]*>(.*?)</title>', content, 1), ''), ' ',
      coalesce (regexp_substr ('(?is)<meta[^>]+name=["'']description["''][^>]*content=["'']([^"'']*)', content, 1), ''), ' ',
      coalesce (regexp_substr ('(?is)<h1[^>]*>(.*?)</h1>', content, 1), '')));

    body_text := lower_text;
    FOR (i := 0; i < 6; i := i + 1)
      body_text := DB.DBA.WEBLOG_DAV_CATEGORY_STRIP_BLOCKS (body_text,
        aref (vector ('head', 'script', 'style', 'footer', 'pre', 'code'), i));
    body_text := DB.DBA.WEBLOG_DAV_CATEGORY_NORM (body_text);

    signals := DB.DBA.WEBLOG_DAV_GENERIC_SIGNALS ();
    FOR (i := 0; i < length (signals); i := i + 1)
    {
      terms := signals[i][1];
      hits := 0;
      FOR (j := 0; j < length (terms); j := j + 1)
      {
        IF (locate (concat (' ', terms[j], ' '), about_text, 1) > 0)
          hits := 20;
        IF (hits < 20)
          hits := hits + DB.DBA.WEBLOG_DAV_CATEGORY_TERM_COUNT (body_text, terms[j], 20 - hits);
      }
      IF (hits >= 20)
        cats := case when cats = '' then signals[i][0] else concat (cats, '; ', signals[i][0]) end;
    }
  }

  IF (cats = '') cats := 'WebDAV Published Documents';
  RETURN cats;
}
;

CREATE PROCEDURE DB.DBA.WEBLOG_DAV_REFRESH_CATEGORIES
  (
    IN dav_collection VARCHAR,
    IN profile VARCHAR := 'generic',
    IN dav_user VARCHAR := 'dba',
    IN update_all INTEGER := 0
  )
{
  DECLARE coll, pwd VARCHAR;
  DECLARE scanned, updated, skipped, failed, renamed INTEGER;
  DECLARE active_aliases, renames ANY;

  coll := trim (dav_collection);
  IF (coll IS NULL OR coll = '')
    SIGNAL ('22023', 'dav_collection is required');

  IF (coll LIKE 'http://%' OR coll LIKE 'https://%')
  {
    DECLARE pos INTEGER;
    pos := strstr (coll, '/DAV/');
    IF (pos IS NULL)
      SIGNAL ('22023', 'dav_collection URL must contain /DAV/');
    coll := subseq (coll, pos);
  }

  IF (subseq (coll, length (coll) - 1) <> '/')
    coll := coll || '/';

  -- dav_user is kept for call compatibility (scheduled events pass it) but
  -- no longer used: reads go straight to WS.WS.SYS_DAV_PROP and writes use
  -- DAV_PROP_SET_INT. DAV_PROP_SET (path, ..., dav_user, pwd_magic_calc (...))
  -- silently fails whenever that account's password hash does not resolve,
  -- and the failure was only counted, never raised -- so the scheduled job
  -- "completed" every 5 minutes while writing nothing (found 2026-10-10 on
  -- the URIBurner weblog: 289 posts, 0 categories, SE_LAST_ERROR null).
  pwd := null;

  scanned := 0;
  updated := 0;
  skipped := 0;
  failed := 0;
  renamed := 0;
  renames := DB.DBA.WEBLOG_DAV_CATEGORY_RENAMES ();

  -- update_all: 0 = untagged posts only (the scheduled default);
  -- 1 = every post; 2 = untagged posts plus posts whose labels all came
  -- from the generic profile (re-tags automatic labels with the current
  -- rules and never touches a curated tag). In every mode, automatic
  -- labels on posts that are otherwise skipped are renamed to an
  -- established equivalent when the collection already uses one.
  active_aliases := vector ();
  IF (profile = 'generic')
    active_aliases := DB.DBA.WEBLOG_DAV_ACTIVE_CATEGORY_ALIASES (coll);

  FOR
    SELECT RES_FULL_PATH AS _path,
           RES_ID AS _rid,
           RES_NAME AS _name,
           RES_CONTENT AS _content
      FROM WS.WS.SYS_DAV_RES
     WHERE (RES_FULL_PATH LIKE coll || '%.html'
         OR RES_FULL_PATH LIKE coll || '%.htm'
         OR RES_FULL_PATH LIKE coll || '%.md')
       AND RES_NAME NOT LIKE '._%'
       AND RES_NAME <> '.DS_Store'
       AND RES_NAME <> 'index.vsp'
     ORDER BY RES_MOD_TIME DESC, RES_NAME DESC
  DO
  {
    DECLARE existing ANY;
    DECLARE existing_text, categories VARCHAR;
    DECLARE rc ANY;

    scanned := scanned + 1;
    existing := null;
    FOR SELECT PROP_VALUE AS _v FROM WS.WS.SYS_DAV_PROP
         WHERE PROP_PARENT_ID = _rid AND PROP_TYPE = 'R' AND PROP_NAME = 'schema:category' DO
      existing := _v;
    existing_text := '';
    IF (existing IS NOT NULL AND isstring (existing))
      existing_text := trim (cast (existing AS VARCHAR));

    -- Bring any earlier spelling of a label up to date, curated tags
    -- included: it is the same label, spelled the current way.
    IF (existing_text <> '' AND existing_text <> '0')
    {
      categories := DB.DBA.WEBLOG_DAV_APPLY_CATEGORY_ALIASES (existing_text, renames);
      IF (categories <> existing_text)
      {
        rc := DB.DBA.DAV_PROP_SET_INT (_path, 'schema:category', categories, null, null, 0, 0, 1);
        IF (not isinteger (rc) OR rc < 0)
          failed := failed + 1;
        ELSE
        {
          renamed := renamed + 1;
          existing_text := categories;
        }
      }
    }

    IF (existing_text <> '' AND existing_text <> '0'
        AND (update_all = 0 OR (update_all = 2 AND DB.DBA.WEBLOG_DAV_IS_AUTO_CATEGORIES (existing_text) = 0)))
    {
      categories := existing_text;
      IF (DB.DBA.WEBLOG_DAV_IS_AUTO_CATEGORIES (existing_text))
        categories := DB.DBA.WEBLOG_DAV_APPLY_CATEGORY_ALIASES (existing_text, active_aliases);
      IF (categories = existing_text)
      {
        skipped := skipped + 1;
        GOTO next_resource;
      }
    }
    ELSE
    {
      categories := DB.DBA.WEBLOG_DAV_INFER_CATEGORIES (blob_to_string (_content), profile);
      categories := DB.DBA.WEBLOG_DAV_APPLY_CATEGORY_ALIASES (categories, active_aliases);
      IF (categories = existing_text)
      {
        skipped := skipped + 1;
        GOTO next_resource;
      }
    }

    rc := DB.DBA.DAV_PROP_SET_INT (_path, 'schema:category', categories, null, null, 0, 0, 1);
    IF (not isinteger (rc) OR rc < 0)
      failed := failed + 1;
    ELSE
      updated := updated + 1;

    next_resource: ;
  }

  RETURN sprintf ('{"ok":true,"collection":"%V","profile":"%V","scanned":%d,"renamed":%d,"updated":%d,"skipped":%d,"failed":%d}', coll, profile, scanned, renamed, updated, skipped, failed);
}
;

CREATE PROCEDURE DB.DBA.WEBLOG_DAV_SCHEDULE_CATEGORY_REFRESH
  (
    IN event_name VARCHAR,
    IN dav_collection VARCHAR,
    IN profile VARCHAR := 'generic',
    IN interval_minutes INTEGER := 5,
    IN dav_user VARCHAR := 'dba',
    IN update_all INTEGER := 0
  )
{
  DECLARE sql_text VARCHAR;

  IF (event_name IS NULL OR trim (event_name) = '')
    SIGNAL ('22023', 'event_name is required');
  IF (interval_minutes IS NULL OR interval_minutes < 1)
    interval_minutes := 5;

  -- Keep scheduler SQL construction parser-safe for isql-loaded scripts.
  -- These values are identifiers/paths, not free-form text; reject embedded quotes
  -- instead of trying fragile nested quote replacement in the deploy script.
  IF (strstr (dav_collection, chr(39)) IS NOT NULL)
    SIGNAL ('22023', 'dav_collection must not contain single quote');
  IF (strstr (profile, chr(39)) IS NOT NULL)
    SIGNAL ('22023', 'profile must not contain single quote');
  IF (strstr (dav_user, chr(39)) IS NOT NULL)
    SIGNAL ('22023', 'dav_user must not contain single quote');

  sql_text := sprintf (
    'DB.DBA.WEBLOG_DAV_REFRESH_CATEGORIES (''%s'', ''%s'', ''%s'', %d)',
    dav_collection,
    profile,
    dav_user,
    update_all);

  INSERT REPLACING DB.DBA.SYS_SCHEDULED_EVENT (SE_NAME, SE_START, SE_INTERVAL, SE_SQL)
  VALUES (event_name, now (), interval_minutes, sql_text);

  RETURN sprintf ('{"ok":true,"event":"%V","interval_minutes":%d,"sql":"%V"}', event_name, interval_minutes, sql_text);
}
;

CREATE PROCEDURE DB.DBA.WEBLOG_DAV_UNSCHEDULE_CATEGORY_REFRESH (IN event_name VARCHAR)
{
  DELETE FROM DB.DBA.SYS_SCHEDULED_EVENT
   WHERE SE_NAME = event_name;
  RETURN sprintf ('{"ok":true,"event":"%V","removed":true}', event_name);
}
;

-- Run every category-refresh job already scheduled on this server once,
-- right now, with the procedures just installed above. Makes this file
-- self-applying on any server (each job carries its own collection and
-- profile). A missing-only job (last argument 0) runs here as mode 2, so
-- posts tagged automatically by an earlier version are re-tagged with the
-- current rules; curated tags are never touched. The schedule itself is
-- not changed. Returns one line per job with its counts.
CREATE PROCEDURE DB.DBA.TMP_WEBLOG_RUN_CATEGORY_JOBS ()
{
  DECLARE report, st, msg, job_sql VARCHAR;
  DECLARE rows ANY;
  report := '';
  FOR (SELECT SE_NAME AS _n, SE_SQL AS _s FROM DB.DBA.SYS_SCHEDULED_EVENT
        WHERE SE_SQL LIKE 'DB.DBA.WEBLOG_DAV_REFRESH_CATEGORIES (%') DO
  {
    st := '00000';
    msg := '';
    rows := null;
    job_sql := trim (_s);
    IF (job_sql LIKE '%, 0)')
      job_sql := concat (subseq (job_sql, 0, length (job_sql) - 2), '2)');
    exec (concat ('SELECT ', job_sql), st, msg, vector (), 1, null, rows);
    IF (st = '00000' AND rows IS NOT NULL AND length (rows) > 0)
      report := concat (report, _n, ': ', cast (rows[0][0] AS VARCHAR), '\n');
    ELSE
      report := concat (report, _n, ': ERROR ', st, ' ', msg, '\n');
  }
  IF (report = '')
    report := 'No scheduled category-refresh jobs on this server -- nothing run.';
  RETURN report;
}
;
SELECT DB.DBA.TMP_WEBLOG_RUN_CATEGORY_JOBS ();
DROP PROCEDURE DB.DBA.TMP_WEBLOG_RUN_CATEGORY_JOBS;

-- Usage: run once immediately for missing categories only.
-- SELECT DB.DBA.WEBLOG_DAV_REFRESH_CATEGORIES ('/DAV/home/demo/Public/fifa-kg-player-reports/', 'fifa-player-reports', 'dba', 0);
--
-- Usage: schedule every 5 minutes, the default interval.
-- SELECT DB.DBA.WEBLOG_DAV_SCHEDULE_CATEGORY_REFRESH ('FIFA player reports category refresh', '/DAV/home/demo/Public/fifa-kg-player-reports/', 'fifa-player-reports');
--
-- Usage: schedule every 15 minutes and recompute all categories.
-- SELECT DB.DBA.WEBLOG_DAV_SCHEDULE_CATEGORY_REFRESH ('FIFA player reports category refresh', '/DAV/home/demo/Public/fifa-kg-player-reports/', 'fifa-player-reports', 15, 'dba', 1);
--
-- Usage: unschedule.
-- SELECT DB.DBA.WEBLOG_DAV_UNSCHEDULE_CATEGORY_REFRESH ('FIFA player reports category refresh');
--
-- Inspect scheduled jobs.
-- SELECT SE_NAME, SE_START, SE_INTERVAL, SE_SQL, SE_LAST_COMPLETED, SE_LAST_ERROR
--   FROM DB.DBA.SYS_SCHEDULED_EVENT
--  WHERE SE_NAME LIKE '%category refresh%';
