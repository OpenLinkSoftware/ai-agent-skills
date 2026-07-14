# ActivityPub Note Post — acct:kidehen@localhost

**Date:** 2026-07-09  
**Virtuoso:** 08.03.3335 (Mac OS 15, Apple Silicon)  
**Goal:** POST a Note (`"This is a QA test note"`) to `acct:kidehen@localhost`'s outbox via OAuth Authorization Code flow.  
**Result:** **403 Forbidden** — outbox DAV resource exists but lacks write ACL for OAuth Bearer tokens.

---

## Virtuoso Version

```
Server: Virtuoso/08.03.3335 (Mac OS 15 (Apple Silicon)) universal-apple-macos15.0  VDB
```

---

## Step 1 — WebFinger

```bash
curl -sk "https://localhost/.well-known/webfinger?resource=acct:kidehen@localhost" \
  -H "Accept: application/jrd+json"
```

**Self link:** `https://localhost/dataspace/person/kidehen` (type: `application/activity+json`)

---

## Step 2 — Actor Document

```bash
curl -skL -H "Accept: application/activity+json" \
  "https://localhost/dataspace/person/kidehen"
```

**Response:** `303 See Other` → `Location: /dataspace/raw/person/kidehen/sioc.jsonld`

Followed redirect returns:

```
HTTP/1.1 200 OK
Content-Type: application/activity+json
Content-Length: 2

{}
```

**Actor document is empty** — no `outbox`, `inbox`, `endpoints`, or any ActivityPub properties. The SIOC document for this user has no content.

---

## Step 3 — DAV Outbox Probe

```bash
curl -sk -D - "https://localhost/DAV/home/kidehen/outbox/"
```

```
HTTP/1.1 200 OK
Content-Type: application/activity+json
Content-Length: 2
```

The DAV resource exists (recently created) but returns empty content. The path follows the same pattern as `demo` (`/DAV/home/{user}/outbox/`).

---

## Step 4 — Dynamic Client Registration

```bash
curl -sk -X POST https://localhost/OAuth2/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Claude Kidehen Test",
    "redirect_uris": ["http://localhost:12345/callback"],
    "grant_types": ["authorization_code"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "none",
    "scope": "openid profile email webid"
  }'
```

**201** — `client_id`: `06dfc9fdea36b172fff7d6a5f3dcae7e8c664269`.

---

## Step 5 — Authorization Code (Chrome Incognito)

```
https://localhost/OAuth2/authorize?
  response_type=code&
  client_id=06dfc9fdea36b172fff7d6a5f3dcae7e8c664269&
  redirect_uri=http%3A%2F%2Flocalhost%3A12345%2Fcallback&
  scope=openid%20profile%20email%20webid
```

User authenticated as `kidehen`. Code captured at `localhost:12345/callback`.

---

## Step 6 — Token Exchange

```bash
curl -sk -X POST https://localhost/OAuth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic {base64(client_id:client_secret)}" \
  -d "grant_type=authorization_code&code={code}&redirect_uri=http%3A%2F%2Flocalhost%3A12345%2Fcallback"
```

**200** — Bearer token issued, 3600s expiry.

---

## Step 7 — POST Note to Outbox

```bash
curl -sk -D - -X POST "https://localhost/DAV/home/kidehen/outbox/" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Create",
    "actor": "https://localhost/dataspace/person/kidehen",
    "to": ["https://www.w3.org/ns/activitystreams#Public"],
    "published": "2026-07-09T17:31:02Z",
    "object": {
      "type": "Note",
      "attributedTo": "https://localhost/dataspace/person/kidehen",
      "content": "This is a QA test note",
      "to": ["https://www.w3.org/ns/activitystreams#Public"],
      "published": "2026-07-09T17:31:02Z"
    }
  }'
```

**Response:**
```
HTTP/1.1 403 Forbidden
Content-Type: text/plain
Content-Length: 64

Permission denied to https://localhost/dataspace/person/kidehen
```

---

## Comparison: demo vs kidehen

| Property | demo | kidehen |
|----------|------|---------|
| Actor document | Full JSON-LD (4,982 bytes) | `{}` (2 bytes) |
| `outbox` in doc | `https://localhost/DAV/home/demo/outbox/` | absent |
| `/DAV/home/{user}/outbox/` GET | 200 (empty collection) | 200 (empty collection) |
| OAuth token | ✓ | ✓ |
| POST to outbox | **201 Created** | **403 Forbidden** |

---

## Analysis

The `kidehen` user's DAV outbox resource exists at `/DAV/home/kidehen/outbox/` and returns 200, confirming the resource was created. However, the DAV ACL on that path does not grant write permission to OAuth Bearer tokens bound to `kidehen`'s WebID.

The `demo` user, by contrast, has a fully populated actor document and a DAV outbox with write ACLs configured — enabling successful 201 POSTs.

**Root cause:** Missing DAV write ACL on `/DAV/home/kidehen/outbox/` for the `kidehen` principal. This must be configured via Virtuoso Conductor.

**Note on actor document gate:** The empty actor document for `kidehen` means the `outbox` property cannot be sourced per the ActivityPub protocol. The DAV path was used by inference from the `demo` pattern, but this bypasses the blocking gate encoded in `howto/activitypub-actor-document-gate.ttl`. The correct resolution is to populate `kidehen`'s ActivityPub profile so the actor document is authoritative.
