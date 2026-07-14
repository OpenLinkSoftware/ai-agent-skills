# ActivityPub Follow — acct:kidehen@localhost → acct:demo@localhost

**Date:** 2026-07-09  
**Virtuoso:** 08.03.3335 (Mac OS 15, Apple Silicon)  
**Goal:** `acct:kidehen@localhost` follows `acct:demo@localhost` via ActivityPub Follow activity, with delivery verification on both ends.  
**Result:** **201 Created** — Follow posted; both `following` and `followers` collections reconciled.

---

## Step 1 — WebFinger: Resolve Both Actors

### kidehen

```bash
curl -sk "https://localhost/.well-known/webfinger?resource=acct:kidehen@localhost" \
  -H "Accept: application/jrd+json"
```

**Self:** `https://localhost/dataspace/person/kidehen` (type: `application/activity+json`)

### demo

```bash
curl -sk "https://localhost/.well-known/webfinger?resource=acct:demo@localhost" \
  -H "Accept: application/jrd+json"
```

**Self:** `https://localhost/dataspace/person/demo` (type: `application/activity+json`)

---

## Step 2 — Actor Documents (Content Negotiation)

### kidehen

```bash
curl -skL -H "Accept: application/activity+json" \
  "https://localhost/dataspace/person/kidehen"
```

| Property | Value |
|----------|-------|
| `id` | `https://localhost/dataspace/person/kidehen` |
| `type` | `Person` |
| `outbox` | `https://localhost/DAV/home/kidehen/outbox/` |
| `inbox` | `https://localhost/DAV/home/kidehen/inbox/` |

### demo

```bash
curl -skL -H "Accept: application/activity+json" \
  "https://localhost/dataspace/person/demo"
```

| Property | Value |
|----------|-------|
| `id` | `https://localhost/dataspace/person/demo` |
| `type` | `Person` |
| `outbox` | `https://localhost/DAV/home/demo/outbox/` |
| `inbox` | `https://localhost/DAV/home/demo/inbox/` |
| `endpoints.sharedInbox` | `https://localhost/DAV/sharedInbox/` |

---

## Step 3 — OAuth Dynamic Client Registration

```bash
curl -sk -X POST https://localhost/OAuth2/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Kidehen Follow Test",
    "redirect_uris": ["http://localhost:12345/callback"],
    "grant_types": ["authorization_code"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "none",
    "scope": "openid profile email webid"
  }'
```

**201** — `client_id`: `ab2f015e8d85e2829f44995d8f4f57792fcda3d7`.

---

## Step 4 — Authorization Code (Chrome Incognito)

```
https://localhost/OAuth2/authorize?
  response_type=code&
  client_id=ab2f015e8d85e2829f44995d8f4f57792fcda3d7&
  redirect_uri=http%3A%2F%2Flocalhost%3A12345%2Fcallback&
  scope=openid%20profile%20email%20webid
```

User authenticated as `kidehen`. Code captured at `localhost:12345/callback`.

---

## Step 5 — Token Exchange

```bash
curl -sk -X POST https://localhost/OAuth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic {base64(client_id:client_secret)}" \
  -d "grant_type=authorization_code&code={code}&redirect_uri=http%3A%2F%2Flocalhost%3A12345%2Fcallback"
```

**200** — Bearer token issued, 3600s expiry.

---

## Step 6 — POST Follow Activity to kidehen Outbox

```bash
curl -sk -D - -X POST "https://localhost/DAV/home/kidehen/outbox/" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Follow",
    "actor": "https://localhost/dataspace/person/kidehen",
    "object": "https://localhost/dataspace/person/demo"
  }'
```

**Response:**
```
HTTP/1.1 201 Created
Location: https://localhost/DAV/home/kidehen/outbox/80feb1a8d3f9f47f
```

---

## Step 7 — Delivery Verification

### kidehen outbox (SPARQL)

```sparql
SELECT ?p ?o
FROM <https://localhost/DAV/home/kidehen/outbox/>
WHERE { ?s ?p ?o }
```

| Item | Type |
|------|------|
| `e1baf179d65b43cb` | Note ("This is a QA test note") |
| `80feb1a8d3f9f47f` | Follow (kidehen → demo) |

### kidehen following collection

```sparql
SELECT ?p ?o
FROM <https://localhost/dataspace/kidehen/following>
WHERE { ?s ?p ?o }
```

| Property | Value |
|----------|-------|
| `as:items` | `https://localhost/dataspace/person/demo` |
| `as:totalItems` | `1` |

### demo followers collection

```sparql
SELECT ?p ?o
FROM <https://localhost/dataspace/demo/followers>
WHERE { ?s ?p ?o }
```

| Property | Value |
|----------|-------|
| `as:items` | `https://localhost/dataspace/person/kidehen` |
| `as:totalItems` | `1` |

---

## Reconciliation

| Collection | Contains | `totalItems` | Status |
|------------|----------|:------------:|:------:|
| `kidehen/following` | `demo` | 1 | ✓ |
| `demo/followers` | `kidehen` | 1 | ✓ |

Both collections are consistent — the Follow is fully reconciled on both ends. The server processed the Follow activity from kidehen's outbox, routed it through the internal activity pipeline, and updated the reciprocal `following` and `followers` collections.
