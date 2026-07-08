# ActivityPub Operations Reference

## Content Negotiation

Fetch Actor or ActivityStreams objects with the correct Accept header:

```bash
curl -sL -H "Accept: application/activity+json" "{uri}"
```

Virtuoso servers return a **303 redirect** to a `.jsonld` representation. Always use `-L` to follow it.

Fallback Accept header:
```bash
-H "Accept: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\""
```

## WebFinger Discovery

Discover an actor URI from a handle (`user@host`):

```bash
# Step 1: Discover WebFinger endpoint from host-meta.json
META=$(curl -sk "https://{host}/.well-known/host-meta.json")
LRDD_TEMPLATE=$(echo "$META" | jq -r '.links[] | select(.rel=="lrdd") | .template')

# Step 2: Query WebFinger
WF_URL=$(echo "$LRDD_TEMPLATE" | sed "s/{uri}/acct:$(urlencode "$HANDLE")/")
WF=$(curl -sk -H "Accept: application/jrd+json" "$WF_URL")

# Step 3: Extract actor URI with activity+json link
ACTOR_URI=$(echo "$WF" | jq -r '.links[] | select(.type=="application/activity+json") | .href')
```

The `host-meta.json` endpoint is at:
- `https://{host}/.well-known/host-meta.json`
- `https://{host}/.well-known/host-meta` (XRD XML format)

## OAuth Authorization Code Flow

Use the existing flow documented at `agent-rdf-memory/howto/uriburner-oauth-authcode-flow.ttl` or invoke `oa2.py`:

1. **Discover OIDC**: `GET {host}/.well-known/openid-configuration`
2. **Register client**: `POST {registration_endpoint}` with `redirect_uris: ["http://127.0.0.1:12345/callback"]`
3. **Start local listener**: Python HTTP server on `127.0.0.1:12345`
4. **Open browser**: `{authorization_endpoint}?response_type=code&client_id={id}&redirect_uri=http://127.0.0.1:12345/callback&scope={scopes}`
5. **Exchange code**: `POST {token_endpoint}` with `code={code}&grant_type=authorization_code&redirect_uri=...`
6. **Store token**: Bearer token for subsequent requests

### Scopes (elicit from user)

| Scope | Access |
|-------|--------|
| `read` | GET inbox, outbox, actor, object |
| `write` | POST to outbox (create activities) |
| `follow` | Follow/unfollow actors |
| `push` | Receive push notifications |

## OAuth 2.0 Scopes Elicitation

Prompt the user to specify required scopes based on intended operations.

- Read-only operations: `read`
- Posting content: `read write`
- Follow/unfollow: `read follow`
- Full access: `read write follow push`

## Activity Constructor

Populate the JSON-LD template from `assets/templates/{type}.jsonld` using `sed` or `jq`:

```bash
# Using envsubst-like sed
sed -e "s|{ACTOR_URI}|$ACTOR_URI|g" \
    -e "s|{OBJECT_URI}|$OBJECT_URI|g" \
    -e "s|{CONTENT}|$CONTENT|g" \
    -e "s|{TO}|$TO|g" \
    -e "s|{CC}|$CC|g" \
    -e "s|{PUBLISHED}|$(date -u +%Y-%m-%dT%H:%M:%SZ)|g" \
    assets/templates/note.jsonld > /tmp/payload.json
```

## Activity Types

### Note
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Note",
  "attributedTo": "{actor_uri}",
  "content": "<p>Hello from the Fediverse!</p>",
  "to": ["https://www.w3.org/ns/activitystreams#Public"],
  "cc": ["{actor_uri}/followers"],
  "published": "{timestamp}"
}
```

### Like
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Like",
  "actor": "{actor_uri}",
  "object": "{target_note_uri}",
  "to": ["{target_actor_uri}"],
  "published": "{timestamp}"
}
```

### Announce (Boost)
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Announce",
  "actor": "{actor_uri}",
  "object": "{target_note_uri}",
  "to": ["{actor_uri}/followers"],
  "published": "{timestamp}"
}
```

### Follow
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Follow",
  "actor": "{actor_uri}",
  "object": "{target_actor_uri}"
}
```

### Delete
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Delete",
  "actor": "{actor_uri}",
  "object": "{note_uri}",
  "to": ["{actor_uri}/followers"]
}
```

### Undo (Like)
```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Undo",
  "actor": "{actor_uri}",
  "object": {
    "type": "Like",
    "object": "{original_note_uri}"
  },
  "to": ["{target_actor_uri}"],
  "published": "{timestamp}"
}
```

## Write Operations (POST to Outbox)

```bash
PAYLOAD=$(cat /tmp/payload.json)
RESPONSE=$(curl -sk -X POST "$OUTBOX" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d "$PAYLOAD")
ACTIVITY_ID=$(echo "$RESPONSE" | jq -r '.id')
```

## Read Operations

### Inbox
```bash
curl -sk -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/activity+json" \
  "$INBOX" | jq '.'
```

### Outbox
```bash
curl -sk -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/activity+json" \
  "$OUTBOX" | jq '.'
```

### Pagination

ActivityStreams collections use `first`/`next` pagination:

```bash
# Get first page
PAGE=$(curl -sk -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/activity+json" \
  "$OUTBOX" | jq -r '.first')

# Iterate through pages
while [ "$PAGE" != "null" ]; do
  RESULT=$(curl -sk -H "Authorization: Bearer $TOKEN" \
    -H "Accept: application/activity+json" \
    "$PAGE")
  echo "$RESULT" | jq '.orderedItems[]'
  PAGE=$(echo "$RESULT" | jq -r '.next // "null"')
done
```

## Remote Delivery

ActivityPub servers handle remote delivery automatically:

1. You **POST** an activity to your **outbox**
2. Your server looks up the `inbox` URIs of all recipients (`to`, `cc`, `tag`)
3. Your server sends HTTP Signatures-signed POSTs to each remote inbox
4. The remote server validates the signature and delivers to the recipient's inbox

The `sharedInbox` endpoint is used for server-scoped delivery — multiple recipients on the same server receive via a single delivery. This is more efficient than per-user inbox delivery.

**Verification**: POST a Follow activity to your outbox targeting another user, then check the target user's inbox via `GET {target_inbox}` with that user's own Bearer token.

### Endpoints from the Actor document

```json
{
  "inbox": "https://{host}/DAV/home/{user}/inbox/",
  "outbox": "https://{host}:8890/DAV/home/{user}/outbox/",
  "endpoints": {
    "sharedInbox": "https://{host}/DAV/sharedInbox/",
    "oauthAuthorizationEndpoint": "https://{host}/OAuth2/authorize",
    "oauthTokenEndpoint": "https://{host}/OAuth2/token"
  }
}
```

## Troubleshooting

| HTTP | Meaning | Action |
|------|---------|--------|
| 200 | Success | Parse response body |
| 303 | Redirect | Follow with `-L` — expected for ActivityPub content negotiation |
| 401 | Unauthorized | Token expired or invalid — re-run OAuth flow |
| 403 | Forbidden | Token lacks required scope — re-auth with correct scopes |
| 404 | Not Found | Wrong URI — check actor/activity ID |
| 406 | Not Acceptable | Missing or wrong `Accept` header for content type |
| 410 | Gone | Resource was deleted |

## Content Types

| Content | Media Type |
|---------|-----------|
| ActivityPub actor/object | `application/activity+json` |
| ActivityPub (alt) | `application/ld+json; profile="https://www.w3.org/ns/activitystreams"` |
| WebFinger | `application/jrd+json` |
| JSON-LD | `application/ld+json` |
