# ActivityPub Operations Reference

## Content Negotiation

Per W3C ActivityPub §3.2 (Retrieving objects):

> Servers MUST present the ActivityStreams object representation in response to
> `application/ld+json; profile="https://www.w3.org/ns/activitystreams"`, and SHOULD
> also present the ActivityStreams representation in response to
> `application/activity+json` as well.

Fetch Actor or ActivityStreams objects with `application/ld+json` first (MUST), then fall back to `application/activity+json` (SHOULD):

```bash
# Primary (W3C MUST)
curl -sL -H "Accept: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" "{uri}"

# Fallback (W3C SHOULD)
curl -sL -H "Accept: application/activity+json" "{uri}"
```

Virtuoso servers return a **303 redirect** to a `.jsonld` representation. Always use `-L` to follow it.

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

## Outbox Setup (Collection Initialization)

Per W3C ActivityPub §5.1, the outbox MUST be an OrderedCollection. Some servers
require the outbox to be created as an LDP container first.

Check if the outbox exists as a collection:

```bash
# PROPFIND the outbox to check its resourcetype
PROPFIND_RESP=$(curl -sk -X PROPFIND "$OUTBOX" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Depth: 0")
# Look for <D:resourcetype><D:collection/></D:resourcetype>
```

If the outbox is a plain resource or missing:

```bash
# Delete old outbox resource (if it exists)
curl -sk -X DELETE "$OUTBOX" -H "Authorization: Bearer $TOKEN"

# Create as a collection (LDP BasicContainer)
curl -sk -X MKCOL "$OUTBOX" -H "Authorization: Bearer $TOKEN"

# Verify
curl -sk -X PROPFIND "$OUTBOX" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Depth: 0" | grep resourcetype
```

Once the outbox is a proper collection, POST will create child resources with
unique IDs returned in the Location header.

## Create Activity Wrapping

Per W3C ActivityPub §6.2.1, when a bare object (not a subtype of Activity) is
POSTed to the outbox, the server MUST wrap it in a Create activity:

```json
// Client POSTs a bare Note
{
  "type": "Note",
  "content": "Hello",
  "to": ["https://www.w3.org/ns/activitystreams#Public"]
}

// Server converts to:
{
  "type": "Create",
  "id": "https://server/outbox/uuid",    // ← Location header
  "actor": "{actor}",
  "object": {
    "type": "Note",
    "id": "https://server/note/uuid",     // ← server-assigned ID
    "attributedTo": "{actor}",
    "content": "Hello",
    "to": ["https://www.w3.org/ns/activitystreams#Public"]
  },
  "published": "{timestamp}",
  "to": ["https://www.w3.org/ns/activitystreams#Public"]
}
```

To verify the wrapping:
```bash
curl -skL -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  "$LOCATION_URL" | jq '.type'
# Expected: "Create"
# If "Note": server stored raw without wrapping
```

## Write Operations (POST to Outbox)

```bash
PAYLOAD=$(cat /tmp/payload.json)
LOCATION=$(curl -sk -D - -X POST "$OUTBOX" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d "$PAYLOAD" 2>&1 | grep -i "^location:" | sed 's/[Ll]ocation: //;s/\r//')
# Location is the new Activity's URL per §6
```

## Read Operations

Per W3C §3.2, try Accept headers in priority order:
1. `application/ld+json; profile="https://www.w3.org/ns/activitystreams"` (MUST)
2. `application/activity+json` (SHOULD)

### Inbox
```bash
curl -skL -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  "$INBOX" | jq '.'
```

### Outbox
```bash
curl -skL -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  "$OUTBOX" | jq '.'
```

If the server returns 406, retry with `application/activity+json`:

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
| ActivityPub actor/object | `application/ld+json; profile="https://www.w3.org/ns/activitystreams"` (W3C MUST) |
| ActivityPub (alt) | `application/activity+json` (W3C SHOULD) |
| WebFinger | `application/jrd+json` |
| JSON-LD | `application/ld+json` |

## W3C Spec Conformance Tests

Reference: https://test.activitypub.rocks/

Run these checks to verify server compliance:

### Test 1: Actor Document (§4.1)
```bash
ACTOR=$(curl -skL -H "Accept: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  "$ACTOR_URI")
echo "$ACTOR" | jq -e '.type' || echo "FAIL: no type"
echo "$ACTOR" | jq -e '.id' || echo "FAIL: no id"
echo "$ACTOR" | jq -e '.inbox' || echo "FAIL: no inbox"
echo "$ACTOR" | jq -e '.outbox' || echo "FAIL: no outbox"
echo "$ACTOR" | jq -e '.preferredUsername' || echo "FAIL: no preferredUsername"
```

### Test 2: Content Negotiation (§3.2)
```bash
# MUST support application/ld+json
S1=$(curl -skL -o /dev/null -w "%{http_code}" "$ACTOR_URI" \
  -H "Accept: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"")
[ "$S1" = "200" ] && echo "PASS: ld+json" || echo "FAIL: ld+json → $S1"

# SHOULD support application/activity+json
S2=$(curl -skL -o /dev/null -w "%{http_code}" "$ACTOR_URI" \
  -H "Accept: application/activity+json")
[ "$S2" = "200" ] && echo "PASS: activity+json" || echo "SHOULD: activity+json → $S2"
```

### Test 3: Outbox as OrderedCollection (§5.1)
```bash
OUTBOX_DATA=$(curl -skL -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  "$OUTBOX")
echo "$OUTBOX_DATA" | jq -e '.type == "OrderedCollection"' || echo "FAIL: not OrderedCollection"
```

### Test 4: POST to Outbox returns Location (§6)
```bash
LOCATION=$(curl -sk -D - -X POST "$OUTBOX" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{"@context":"https://www.w3.org/ns/activitystreams","type":"Note","content":"<p>test</p>","to":["https://www.w3.org/ns/activitystreams#Public"]}' \
  2>&1 | grep -i "^location:")
[ -n "$LOCATION" ] && echo "PASS: Location returned" || echo "FAIL: no Location"
```

### Test 5: Create Activity Wrapping (§6.2.1)
```bash
CREATED=$(curl -skL -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  "$LOCATION_URL")
TYPE=$(echo "$CREATED" | jq -r '.type')
[ "$TYPE" = "Create" ] && echo "PASS: wrapped in Create" || echo "NOTE: stored as $TYPE"
```

### Test 6: Object ID Assignment (§3.1, §6)
```bash
OBJ_ID=$(echo "$CREATED" | jq -r '.object.id // .id')
HTTP_CODE=$(curl -skL -o /dev/null -w "%{http_code}" "$OBJ_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"")
[ "$HTTP_CODE" = "200" ] && echo "PASS: object dereferenceable" || echo "FAIL: object → $HTTP_CODE"
```
