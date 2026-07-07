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
- "remote delivery" — verify server-to-server fan-out

## Workflow

### Step 1: Elicit server and identity

Prompt the user for:

| Variable | Prompt | Example |
|----------|--------|---------|
| `INSTANCE` | "Fediverse instance hostname" | `localhost` or `fediverse.demo.openlinksw.com` |
| `USER_HANDLE` | "Your handle" | `demo` |
| `SECOND_USER` | "Target handle (for Follow/delivery)" | `kidehen` |
| `SCOPES` | "OAuth scopes" | `read write follow push` |

### Step 2: Resolve actor

1. **WebFinger**: Discover the WebFinger endpoint from `https://{instance}/.well-known/host-meta.json` (lrdd link template)
2. **Query**: WebFinger `acct:{handle}@{instance}` with `Accept: application/jrd+json`
3. **Extract**: Pull the actor URI from the `self` link with `type: application/activity+json`

### Step 3: Fetch actor document

```bash
curl -sL -H "Accept: application/activity+json" "{actor_uri}"
```

Parse the response to extract:
- `inbox`
- `outbox`
- `followers`
- `following`
- `endpoints.sharedInbox`
- `endpoints.oauthAuthorizationEndpoint`
- `endpoints.oauthTokenEndpoint`

### Step 4: Authenticate

Delegated to the existing OAuth Authorization Code flow:

- Reference: `agent-rdf-memory/howto/uriburner-oauth-authcode-flow.ttl`
- Implementation: `oa2.py` (in this repo's root) or equivalent
- OIDC discovery: `{instance}/.well-known/openid-configuration`
- Scopes at runtime: elicit from user (`read write follow push`)

**Do not create new auth scripts.** Use the existing pattern.

### Step 5: Elicit operation parameters from the user

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

### Step 6: Execute ActivityPub operation

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

**Always capture the `Location` header** from the 201 response — this is the canonical ActivityPub resource URL. The response body HTML may contain a different internal ID.

**Read operations**: Bearer GET on inbox/outbox/object URIs with `Accept: application/activity+json`. Walk pagination via `first`/`next`.

### Step 7: Verify delivery (for Follow)

1. POST a Follow activity to User A's outbox targeting User B's actor URI
2. GET User B's inbox (with User B's token) to confirm the Follow arrived
3. Server-to-server delivery via `sharedInbox` happens automatically

## Test Harness

Run the end-to-end test script:

```bash
.opencode/skills/fediverse-crud/scripts/test-fediverse.sh
```

The script elicits the server, handles, and scopes at runtime. It does not hardcode any accounts.

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
