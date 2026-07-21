# OPAL Tool Mode

Use OPAL tool mode when a weblog operation should be callable by an AI agent, MCP client, or REST/OpenAPI client instead of only by a local script.

## Stored Procedure Surface

Pinning is exposed by:

```sql
DB.DBA.WEBLOG_DAV_SET_PIN (
  dav_collection VARCHAR,
  post_name VARCHAR,
  pinned INTEGER := 1,
  dav_user VARCHAR := 'dav'
)
```

The procedure sets the resource-level WebDAV property:

```text
schema:position
```

The weblog VSP treats any non-empty, non-zero `schema:position` value as pinned. A value of `0` means unpinned.

## Registration

Deploy `templates/register-weblog-pinning-tool.sql` through `isql`. The script always creates the SQL procedure first. OPAL registration is best-effort and is skipped silently when the target Virtuoso instance does not have OPAL installed.

When OPAL is installed, the script registers the function with:

```sql
OAI.DBA.REGISTER_CHAT_FUNCTION(
  'DB.DBA.WEBLOG_DAV_SET_PIN',
  'Pin or unpin a WebDAV weblog post'
);
```

When updating the procedure, unregister before recreating and registering:

```sql
OAI.DBA.UNREGISTER_CHAT_FUNCTION('DB.DBA.WEBLOG_DAV_SET_PIN');
```

## Verification

Run:

```sql
OAI.DBA.LIST_CHAT_FUNCTIONS();
```

Then check the generated OpenAPI description:

```text
https://{server-cname}/chat/functions/openapi.yaml
```

An MCP-capable agent can use the registered function through the server's OPAL/MCP bridge when that bridge is enabled for the target instance.

## Prompt Action Contract

For a prompt such as:

```text
Pin databricks-virtuoso-kg-deepseek_v4pro-1.html on the UB DaaS weblog
```

the skill should:

1. Resolve the designated weblog to a public route and DAV collection.
2. Verify the target post exists and is not a macOS sidecar file.
3. Prefer the registered OPAL tool when available.
4. Fall back to `isql` execution of `DB.DBA.WEBLOG_DAV_SET_PIN`.
5. Fall back to WebDAV `PROPPATCH` only when server-side tool access is unavailable.
6. Verify the post appears ahead of ordinary recency ordering.
