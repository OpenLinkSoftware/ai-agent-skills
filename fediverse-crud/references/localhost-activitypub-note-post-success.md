# ActivityPub Note Post — acct:demo@localhost (Protocol-Correct)

**Date:** 2026-07-09  
**Virtuoso:** 08.03.3335 (Mac OS 15, Apple Silicon)  
**Goal:** POST a Note (`"This is a QA test note"`) to `acct:demo@localhost`'s outbox using full ActivityPub + WebFinger protocol.  
**Result:** **201 Created** — Note posted successfully.

---

## Protocol Flow

### 1. WebFinger Resolution

```bash
curl -sk "https://localhost/.well-known/webfinger?resource=acct:demo@localhost" \
  -H "Accept: application/jrd+json"
```

Extracted `self` link with type `application/activity+json`:

**Actor URI:** `https://localhost/dataspace/person/demo`

---

### 2. Actor Document (Content Negotiation)

```bash
curl -skL -H "Accept: application/activity+json" \
  "https://localhost/dataspace/person/demo"
```

Server returned `303 See Other` → `Location: /dataspace/raw/person/demo/sioc.jsonld`. Followed redirect to get the full actor document.

**Key properties extracted:**

| Property | Value |
|----------|-------|
| `id` | `https://localhost/dataspace/person/demo` |
| `type` | `Person` |
| `preferredUsername` | `demo` |
| **`outbox`** | **`https://localhost/DAV/home/demo/outbox/`** |
| `inbox` | `https://localhost/DAV/home/demo/inbox/` |
| `endpoints.sharedInbox` | `https://localhost/DAV/sharedInbox/` |
| `endpoints.oauthAuthorizationEndpoint` | `https://localhost/OAuth2/authorize` |
| `endpoints.oauthTokenEndpoint` | `https://localhost/OAuth2/token` |

> **Critical:** The outbox is at `/DAV/home/demo/outbox/` — **not** `/dataspace/person/demo/outbox`. Prior failed attempts guessed the URL by convention instead of reading it from the actor document. This is the ActivityPub protocol requirement.

---

### 3. OAuth Dynamic Client Registration

```bash
curl -sk -X POST https://localhost/OAuth2/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Claude Demo Test",
    "redirect_uris": ["http://localhost:12345/callback"],
    "grant_types": ["authorization_code"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "none",
    "scope": "openid profile email webid"
  }'
```

**201** — `client_id` issued.

---

### 4. Authorization Code (Chrome Incognito)

```
https://localhost/OAuth2/authorize?
  response_type=code&
  client_id={cid}&
  redirect_uri=http%3A%2F%2Flocalhost%3A12345%2Fcallback&
  scope=openid%20profile%20email%20webid
```

User authenticated as `demo`, granted consent. Code captured at `localhost:12345/callback`.

---

### 5. Token Exchange

```bash
curl -sk -X POST https://localhost/OAuth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic {base64(client_id:client_secret)}" \
  -d "grant_type=authorization_code&code={code}&redirect_uri=http%3A%2F%2Flocalhost%3A12345%2Fcallback"
```

**200** — Bearer token issued. ID token `sub`: `https://localhost/dataspace/person/demo#this`.

---

### 6. POST Create Activity to Outbox

```bash
curl -sk -D - -X POST "https://localhost/DAV/home/demo/outbox/" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Create",
    "actor": "https://localhost/dataspace/person/demo",
    "to": ["https://www.w3.org/ns/activitystreams#Public"],
    "published": "2026-07-09T16:56:43Z",
    "object": {
      "type": "Note",
      "attributedTo": "https://localhost/dataspace/person/demo",
      "content": "This is a QA test note",
      "to": ["https://www.w3.org/ns/activitystreams#Public"],
      "published": "2026-07-09T16:56:43Z"
    }
  }'
```

**Response:**
```
HTTP/1.1 201 Created
Location: https://localhost/DAV/home/demo/outbox/6f7fadaaa1268c01
Content-Type: application/ld+json
User: <https://localhost/dataspace/person/demo>
Link: <http://www.w3.org/ns/ldp#Resource>; rel="type"
Link: <http://www.w3.org/ns/ldp#RDFSource>; rel="type"
```

**Activity URI:** `https://localhost/DAV/home/demo/outbox/6f7fadaaa1268c01`

---

## Root Cause of Prior Failures

All 4 prior attempts (spanning OAuth Bearer and Digest auth, normal and incognito sessions) **used the wrong outbox URL**. The outbox was guessed by convention as:

```
https://localhost/dataspace/person/demo/outbox   ← WRONG (guessed)
```

The correct outbox, discovered by fetching the actor document per the ActivityPub protocol, is:

```
https://localhost/DAV/home/demo/outbox/           ← CORRECT (from actor doc)
```

The ActivityPub specification requires that the outbox URL be read from the actor document's `outbox` property — **never guessed by appending `/outbox` to the actor URI**. The Virtuoso ODS instance places outboxes under `/DAV/home/{user}/outbox/`, not `/dataspace/person/{user}/outbox`.

---

## Summary

| Step | Result |
|------|--------|
| WebFinger | ✓ Actor URI resolved |
| Actor Document | ✓ Outbox, inbox, OAuth endpoints extracted |
| Dynamic Client Registration | ✓ (201) |
| Authorization Code (Incognito) | ✓ |
| Token Exchange | ✓ Bearer token issued |
| **POST to Outbox** | **✓ 201 Created** |

**Lesson:** Always fetch the actor document and read the `outbox` property. Never guess it.
