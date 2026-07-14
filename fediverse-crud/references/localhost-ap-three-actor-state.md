# ActivityPub Three-Actor State — localhost

**Date:** 2026-07-09  
**Virtuoso:** 08.03.3335 (Mac OS 15, Apple Silicon)  
**Goal:** Verify ActivityPub outbox write readiness for `demo`, `kidehen`, and `vdb` on localhost.  
**Result:** Only `demo` writable. `kidehen` ACL lost since earlier session. `vdb` never configured.

---

## Outbox State

| Actor | Outbox URL | GET | POST (Create Note) | Earlier |
|-------|-----------|:---:|:---:|:---:|
| `demo` | `https://localhost/DAV/home/demo/outbox/` | 401 | **201** ✓ | ✓ |
| `kidehen` | `https://localhost/DAV/home/kidehen/outbox/` | 200 | **403** ✗ | was 201 |
| `vdb` | `https://localhost/DAV/home/vdb/outbox/` | 200 | **403** ✗ | was 403 |

---

## kidehen — Regressed from 201 to 403

### Outbox GET

```bash
curl -sk -D - "https://localhost/DAV/home/kidehen/outbox/"
```

```
HTTP/1.1 200 OK
Content-Type: application/json
```

Outbox DAV resource exists and is browseable.

### Actor Document

```bash
curl -skL -H "Accept: application/activity+json" \
  "https://localhost/dataspace/person/kidehen"
```

Returns `{}` (2 bytes). SIOC profile not populated.

### WebFinger

```bash
curl -sk "https://localhost/.well-known/webfinger?resource=acct:kidehen@localhost" \
  -H "Accept: application/jrd+json"
```

Self link resolves correctly: `https://localhost/dataspace/person/kidehen`.

### OAuth Token

Dynamic client registered, Authorization Code flow completed as `kidehen`. Bearer token issued (3600s).

### POST Note

```bash
curl -sk -D - -X POST "https://localhost/DAV/home/kidehen/outbox/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{ "@context": "https://www.w3.org/ns/activitystreams", "type": "Create", ... }'
```

```
HTTP/1.1 403 Forbidden
Content-Type: text/plain

Permission denied to https://localhost/dataspace/person/kidehen
```

---

## demo — Still Working

### Outbox GET

```bash
curl -sk -D - "https://localhost/DAV/home/demo/outbox/"
```

```
HTTP/1.1 401 Unauthorized
```

Requires authentication to browse (DAV ACL restricts listing).

### POST Note

OAuth flow as `demo` → Bearer token → POST to outbox.

```
HTTP/1.1 201 Created
Location: https://localhost/DAV/home/demo/outbox/297fd88ec635dbcc
```

---

## vdb — Never Configured

### Outbox GET

```bash
curl -sk -D - "https://localhost/DAV/home/vdb/outbox/"
```

```
HTTP/1.1 200 OK
Content-Type: text/html
```

Returns DAV browser HTML — outbox exists as a DAV collection but not configured for ActivityPub writes.

### POST Note

OAuth flow as `vdb` → Bearer token → POST to outbox.

```
HTTP/1.1 403 Forbidden
Permission denied to https://localhost/dataspace/person/vdb
```

---

## Session Activity Summary

| Timestamp (approx) | Actor | Operation | Result |
|---|---|---|---|
| 16:56 | `demo` | Create Note | 201 ✓ |
| 17:28 | `kidehen` | Create Note | 403 (before ACL config) |
| 17:31 | `kidehen` | Create Note | 403 |
| 18:02 | `kidehen` | Create Note | 201 ✓ (after ACL config) |
| 18:06 | `kidehen` | Follow demo | 201 ✓ |
| 18:19 | `kidehen` | Create Note | 201 ✓ |
| 18:23 | `kidehen` | Like demo | 201 ✓ |
| 18:24 | `kidehen` | Announce demo | 201 ✓ |
| 18:24 | `kidehen` | Create + Delete | 201 + 201 ✓ |
| 18:24 | `kidehen` | Undo Follow | 201 (not processed) |
| 21:20 | `demo` | Create Note | 201 ✓ |
| 21:23 | `vdb` | Create Note | 403 (never configured) |
| 21:25 | `kidehen` | Create Note | **403 (regression)** |

---

## Analysis

`kidehen`'s DAV write ACL was functional during the 18:02–18:24 window (6 successful operations across Create, Follow, Like, Announce, Delete, Undo) but has since reverted to 403. Likely causes:

1. Server restart cleared dynamically granted ACLs
2. The ACL grant was session-scoped
3. Conductor-side ACL changes require persistence configuration

`vdb` has never had write ACLs configured. Only `demo` has a persistent, working outbox configuration on this Virtuoso 08.03.3335 instance.
