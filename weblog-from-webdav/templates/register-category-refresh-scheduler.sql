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

  IF (strstr (lower_text, 'linked data') IS NOT NULL OR strstr (lower_text, 'semantic web') IS NOT NULL OR strstr (lower_text, 'rdf') IS NOT NULL OR strstr (lower_text, 'ontology') IS NOT NULL)
    cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'Semantic Web, RDF & Linked Data');
  IF (strstr (lower_text, 'knowledge graph') IS NOT NULL OR strstr (lower_text, 'entity') IS NOT NULL OR strstr (lower_text, 'relationship') IS NOT NULL)
    cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'Knowledge Graphs');
  IF (strstr (lower_text, 'ai agent') IS NOT NULL OR strstr (lower_text, 'agentic') IS NOT NULL OR strstr (lower_text, 'llm') IS NOT NULL OR strstr (lower_text, 'chatgpt') IS NOT NULL OR strstr (lower_text, 'gpt') IS NOT NULL)
    cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'AI Agents & LLMs');
  IF (strstr (lower_text, 'api') IS NOT NULL OR strstr (lower_text, 'rest') IS NOT NULL OR strstr (lower_text, 'oauth') IS NOT NULL OR strstr (lower_text, 'mcp') IS NOT NULL OR strstr (lower_text, 'a2a') IS NOT NULL OR strstr (lower_text, 'skill') IS NOT NULL)
    cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'APIs, Protocols & Agent Skills');
  IF (strstr (lower_text, 'virtuoso') IS NOT NULL OR strstr (lower_text, 'webdav') IS NOT NULL OR strstr (lower_text, 'vsp') IS NOT NULL OR strstr (lower_text, 'sparql') IS NOT NULL OR strstr (lower_text, 'spasql') IS NOT NULL OR strstr (lower_text, 'sql') IS NOT NULL)
    cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'Virtuoso Platform');
  IF (strstr (lower_text, 'analytics') IS NOT NULL OR strstr (lower_text, 'data engineering') IS NOT NULL OR strstr (lower_text, 'etl') IS NOT NULL OR strstr (lower_text, 'elt') IS NOT NULL OR strstr (lower_text, 'lakehouse') IS NOT NULL)
    cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'Analytics & Data Engineering');
  IF (strstr (lower_text, 'security') IS NOT NULL OR strstr (lower_text, 'privacy') IS NOT NULL OR strstr (lower_text, 'webid') IS NOT NULL OR strstr (lower_text, 'identity') IS NOT NULL OR strstr (lower_text, 'certificate') IS NOT NULL)
    cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'Identity, Security & Privacy');
  IF (strstr (lower_text, 's3') IS NOT NULL OR strstr (lower_text, 'bucket') IS NOT NULL OR strstr (lower_text, 'object storage') IS NOT NULL OR strstr (lower_text, 'cloud storage') IS NOT NULL)
    cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'Cloud Storage & S3');
  IF (strstr (lower_text, 'fifa') IS NOT NULL OR strstr (lower_text, 'world cup') IS NOT NULL OR strstr (lower_text, 'football') IS NOT NULL OR strstr (lower_text, 'soccer') IS NOT NULL)
    cats := DB.DBA.WEBLOG_DAV_CATEGORY_APPEND (cats, 'FIFA World Cup & Football');

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
  DECLARE scanned, updated, skipped, failed INTEGER;

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

  SELECT pwd_magic_calc (U_NAME, U_PASSWORD, 1) INTO pwd
    FROM DB.DBA.SYS_USERS
   WHERE U_NAME = dav_user;

  IF (pwd IS NULL)
    SIGNAL ('22023', sprintf ('DAV user not found: %s', dav_user));

  scanned := 0;
  updated := 0;
  skipped := 0;
  failed := 0;

  FOR
    SELECT RES_FULL_PATH AS _path,
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
    existing := DB.DBA.DAV_PROP_GET (_path, 'schema:category', dav_user, pwd);
    existing_text := '';
    IF (existing IS NOT NULL)
      existing_text := trim (cast (existing AS VARCHAR));

    IF (update_all = 0 AND existing_text <> '' AND existing_text <> '0')
    {
      skipped := skipped + 1;
      GOTO next_resource;
    }

    categories := DB.DBA.WEBLOG_DAV_INFER_CATEGORIES (blob_to_string (_content), profile);
    rc := DB.DBA.DAV_PROP_SET (_path, 'schema:category', categories, dav_user, pwd, 1);
    IF (DB.DBA.DAV_HIDE_ERROR (rc) IS NULL)
      failed := failed + 1;
    ELSE
      updated := updated + 1;

    next_resource: ;
  }

  RETURN sprintf ('{"ok":true,"collection":"%V","profile":"%V","scanned":%d,"updated":%d,"skipped":%d,"failed":%d}', coll, profile, scanned, updated, skipped, failed);
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
