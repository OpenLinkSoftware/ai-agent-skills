---
name: fediverse-crud
description: Perform ActivityPub read/write operations against Fediverse instances (Note, Like, Announce, Follow, Delete, Undo). Handles OAuth Authorization Code flow, WebFinger resolution, ActivityPub content negotiation, and server-to-server delivery verification.
---

# Fediverse CRUD

Create, read, and manage ActivityPub activities on any Fediverse server.

## Triggers

- "post a note/toot/status" — create a Note
- "like/boost/favourite" — Like or Announce an object
- "follow/unfollow @user" — Follow or Undo-Follow
- "delete my post/activity" — Delete your own activity
- "read/show my inbox/outbox" — GET and paginate collections
- "send an ActivityPub activity" — any of the above
- "test the fediverse" — run the test harness
- "show me an example of fediverse/activitypub" — run the W3C spec-based demo suite
- "remote delivery" — verify server-to-server fan-out

## Workflow

### Step 1: Elicit server and identity

Prompt the user for:

| Variable | Prompt | Example |
|----------|--------|---------|
| `INSTANCE` | "Fediverse instance hostname" | `localhost` or `fediverse.demo.openlinksw.com` |
| `USER_HANDLE` | "Your handle" | `demo` |
| `SECOND_USER` | "Target handle (for Follow/delivery)" | `kidehen` |
| `SCOPES` | "OAuth scopes" | `openid webid` |

### Step 2: Resolve actor

1. **WebFinger**: Discover the WebFinger endpoint from `https://{instance}/.well-known/host-meta.json` (lrdd link template)
2. **Query**: WebFinger `acct:{handle}@{instance}` with `Accept: application/jrd+json`
3. **Extract**: Pull the actor URI from the `self` link with `type: application/activity+json`

### Step 3: Fetch actor document

```bash
curl -sL -H "Accept: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" "{actor_uri}"
```

Parse the response to extract:
- `inbox`
- `outbox`
- `followers`
- `following`
- `endpoints.sharedInbox`
- `endpoints.oauthAuthorizationEndpoint`
- `endpoints.oauthTokenEndpoint`

Note: Per W3C ActivityPub §3.2, servers MUST serve `application/ld+json` and SHOULD serve `application/activity+json`. Try `application/ld+json` first; fall back to `application/activity+json` if the server returns 406.

### Step 4: Authenticate

Delegated to the existing OAuth Authorization Code flow:

- Reference: `agent-rdf-memory/howto/uriburner-oauth-authcode-flow.ttl`
- Implementation: `oa2.py` (in this repo's root) or equivalent
- OIDC discovery: `{instance}/.well-known/openid-configuration`
- Scopes at runtime: elicit from user (`openid webid`)

**Do not create new auth scripts.** Use the existing pattern.

### Step 5: Ensure outbox is a proper collection

Some servers need the outbox initialized as an LDP container before it can hold child resources. Check via PROPFIND:

```bash
# Check if outbox exists as a collection
PROPFIND_RESP=$(curl -sk -X PROPFIND "$OUTBOX" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Depth: 0")
```

If the outbox is missing or is a plain resource (not a collection):
1. DELETE the old outbox resource
2. Create it as a collection via MKCOL
3. Re-fetch the outbox to confirm it's a container

This is needed for spec compliance — per W3C ActivityPub §5.1, the outbox MUST be an OrderedCollection.

### Step 6: Elicit operation parameters from the user

Before building any payload, capture the user's input for the operation:

| Operation | What to elicit | Example |
|-----------|---------------|---------|
| **Note** | "What content for the note?" | `Hello from the Fediverse!` |
| **Like** | "What object URI to like?" | `https://.../note/123` |
| **Announce** | "What object URI to boost?" | `https://.../note/123` |
| **Follow** | "What actor URI to follow?" | `https://.../person/other` |
| **Delete** | "What activity URI to delete?" | `https://.../activity/456` |
| **Undo** | "What type and object URI to undo?" | `Like` / `https://.../note/123` |

Present the user's input back for confirmation before proceeding.

### Step 7: Execute ActivityPub operation

**Write operations**: Populate the template from `assets/templates/{type}.jsonld` with the user's captured input and `POST` to the actor's `outbox`:

```bash
sed -e "s|{ACTOR_URI}|$ACTOR|g" \
    -e "s|{OBJECT_URI}|$OBJECT|g" \
    -e "s|{CONTENT}|$CONTENT|g" \
    -e "s|{TO}|$TO|g" \
    -e "s|{PUBLISHED}|$(date -u +%Y-%m-%dT%H:%M:%SZ)|g" \
    assets/templates/{type}.jsonld > /tmp/payload.json

LOCATION=$(curl -sk -D - -X POST "$OUTBOX" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d @/tmp/payload.json 2>&1 | grep -i "^location:" | sed 's/[Ll]ocation: //;s/\r//')
```

**Always capture the `Location` header** from the 201 response — this is the canonical ActivityPub resource URL. Per W3C ActivityPub §6, the server MUST generate a new id and return it in the Location header.

**Verify the created resource**: Fetch the resource at the Location URL. Per §6.2.1, bare objects submitted to the outbox SHOULD be wrapped in a Create activity by the server. Check `type` in the response:
- If `type` is `Create` → server wrapped the object correctly
- If `type` is the original type (e.g. `Note`) → server stored it raw

**Read operations**: Bearer GET on inbox/outbox/object URIs. Try Accept headers in this order per W3C §3.2:
1. `application/ld+json; profile="https://www.w3.org/ns/activitystreams"` (MUST)
2. `application/activity+json` (SHOULD)

Walk pagination via `first`/`next`.

### Step 8: Verify delivery (for Follow)

1. POST a Follow activity to User A's outbox targeting User B's actor URI
2. GET User B's inbox (with User B's token) to confirm the Follow arrived
3. Server-to-server delivery via `sharedInbox` happens automatically

## Test Harness

Run the end-to-end test script:

```bash
fediverse-crud/scripts/test-fediverse.sh
```

The script elicits the server, handles, and scopes at runtime. It does not hardcode any accounts.

## W3C Spec Demo Suite

Invoke with: "show me an example of fediverse" or "run the w3c test suite"

The demo performs these spec-verifying steps against the user's chosen server:

1. **§4.1 Actor resolution**: WebFinger acct:user@host → GET actor document → verify inbox, outbox, preferredUsername exist
2. **§5.1 Outbox as OrderedCollection**: PROPFIND outbox → if not a collection, MKCOL to create it
3. **§6 Client-to-server POST**: POST bare Note to outbox → expect 201 with Location header
4. **§6.2.1 Create wrapping**: GET the Location URL → verify the server wrapped the Note in a Create activity
5. **§6.11 Delivery**: Verify the created activity appears in the outbox collection
6. **§3.2 Content negotiation**: Verify both `application/ld+json` and `application/activity+json` Accept headers

## Template Variables

| Variable | Description |
|----------|-------------|
| `{ACTOR_URI}` | Actor performing the activity |
| `{OBJECT_URI}` | Activity target (Note, actor, etc.) |
| `{TARGET_ACTOR_URI}` | Target actor for Follow |
| `{CONTENT}` | Note body content (HTML) |
| `{TO}` | Primary audience URI |
| `{CC}` | Secondary audience URI |
| `{PUBLISHED}` | ISO 8601 timestamp |
| `{UNDO_TYPE}` | Type being undone (e.g. "Like") |

## Auth Reference

See `agent-rdf-memory/howto/uriburner-oauth-authcode-flow.ttl` for the complete OAuth Authorization Code flow with dynamic client registration and local callback server.
