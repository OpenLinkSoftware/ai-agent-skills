-- Register OPAL/OpenAPI tool for pinning WebDAV weblog posts.
-- Patch the optional VHOST host/port for the target Virtuoso instance before running.
-- Registered functions are exposed through OPAL chat functions and documented at:
--   https://{server-cname}/chat/functions/openapi.yaml
-- OPAL registration is best-effort: if OPAL is not installed, the SQL pinning
-- procedure is still created and can be invoked directly through isql.

-- Optional HTTP endpoint for SQL/SOAP execution, when not already configured.
-- DB.DBA.VHOST_DEFINE (
--      lhost => ':8443',
--      vhost => 'localhost',
--      lpath => '/sqlexec',
--      ppath => '/SOAP/Http',
--      soap_user => 'demo',
--      opts => vector('cors', '*', 'cors_allow_headers', '*', 'cors_restricted', 0)
-- );

CREATE PROCEDURE DB.DBA.TMP_WEBLOG_PIN_DROP ()
{
  DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; };
  exec ('DROP PROCEDURE DB.DBA.WEBLOG_DAV_SET_PIN');
}
;

DB.DBA.TMP_WEBLOG_PIN_DROP ();
DROP PROCEDURE DB.DBA.TMP_WEBLOG_PIN_DROP;

CREATE PROCEDURE DB.DBA.WEBLOG_DAV_SET_PIN
  (
    IN dav_collection VARCHAR,
    IN post_name VARCHAR,
    IN pinned INTEGER := 1,
    IN dav_user VARCHAR := 'dav'
  )
{
  --## Pin or unpin a post in a Virtuoso WebDAV-backed weblog by setting schema:position metadata. Provide the DAV collection path or URL, post filename or DAV path, and pinned=1 to make it the single pinned post for the collection or pinned=0 to unpin it.
  DECLARE coll, post, dav_path, pin_value, pwd VARCHAR;
  DECLARE rc, clear_rc, exists_count INTEGER;

  coll := trim(dav_collection);
  post := trim(post_name);

  IF (coll IS NULL OR coll = '')
    SIGNAL ('22023', 'dav_collection is required');
  IF (post IS NULL OR post = '')
    SIGNAL ('22023', 'post_name is required');
  IF (post LIKE '._%')
    SIGNAL ('22023', 'Refusing to pin macOS sidecar resource');

  IF (coll LIKE 'http://%' OR coll LIKE 'https://%')
  {
    DECLARE pos INTEGER;
    pos := strstr(coll, '/DAV/');
    IF (pos IS NULL)
      SIGNAL ('22023', 'dav_collection URL must contain /DAV/');
    coll := subseq(coll, pos);
  }

  IF (post LIKE 'http://%' OR post LIKE 'https://%')
  {
    DECLARE pos2 INTEGER;
    pos2 := strstr(post, '/DAV/');
    IF (pos2 IS NULL)
      SIGNAL ('22023', 'post URL must contain /DAV/');
    dav_path := subseq(post, pos2);
  }
  ELSE IF (post LIKE '/DAV/%')
  {
    dav_path := post;
  }
  ELSE
  {
    IF (subseq(coll, length(coll) - 1) <> '/')
      coll := coll || '/';
    dav_path := coll || post;
  }

  SELECT count(*) INTO exists_count
    FROM WS.WS.SYS_DAV_RES
   WHERE RES_FULL_PATH = dav_path
     AND RES_NAME NOT LIKE '._%';

  IF (exists_count = 0)
    SIGNAL ('22023', sprintf('No DAV resource found for %s', dav_path));

  pin_value := '0';
  IF (pinned <> 0)
    pin_value := '1';

  SELECT pwd_magic_calc(U_NAME, U_PASSWORD, 1) INTO pwd
    FROM DB.DBA.SYS_USERS
   WHERE U_NAME = dav_user;

  IF (pwd IS NULL)
    SIGNAL ('22023', sprintf('DAV user not found: %s', dav_user));

  IF (pinned <> 0)
  {
    for (select RES_FULL_PATH as _other_path
           from WS.WS.SYS_DAV_RES
          where (RES_FULL_PATH like coll || '%.html'
              or RES_FULL_PATH like coll || '%.md')
            and RES_NAME not like '._%'
            and RES_NAME <> 'index.vsp') do
    {
      IF (_other_path <> dav_path)
        clear_rc := DB.DBA.DAV_PROP_SET(_other_path, 'schema:position', '0', dav_user, pwd, 1);
    }
  }

  rc := DB.DBA.DAV_PROP_SET(dav_path, 'schema:position', pin_value, dav_user, pwd, 1);
  IF (rc < 0)
    SIGNAL ('42000', sprintf('DAV_PROP_SET failed for %s, rc=%d', dav_path, rc));

  RETURN sprintf(
    '{"ok":true,"dav_path":"%V","schema_position":"%V","pinned":%d}',
    dav_path,
    pin_value,
    CASE WHEN pinned <> 0 THEN 1 ELSE 0 END
  );
}
;

CREATE PROCEDURE DB.DBA.TMP_WEBLOG_PIN_UNREGISTER ()
{
  DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; };
  exec ('OAI.DBA.UNREGISTER_CHAT_FUNCTION (''DB.DBA.WEBLOG_DAV_SET_PIN'')');
}
;

DB.DBA.TMP_WEBLOG_PIN_UNREGISTER ();
DROP PROCEDURE DB.DBA.TMP_WEBLOG_PIN_UNREGISTER;

CREATE PROCEDURE DB.DBA.TMP_WEBLOG_PIN_REGISTER ()
{
  DECLARE EXIT HANDLER FOR SQLSTATE '*' { ; };
  exec ('OAI.DBA.REGISTER_CHAT_FUNCTION (''DB.DBA.WEBLOG_DAV_SET_PIN'', ''Pin or unpin a WebDAV weblog post'')');
}
;

DB.DBA.TMP_WEBLOG_PIN_REGISTER ();
DROP PROCEDURE DB.DBA.TMP_WEBLOG_PIN_REGISTER;

-- Optional verification when OPAL is installed:
-- OAI.DBA.LIST_CHAT_FUNCTIONS();
