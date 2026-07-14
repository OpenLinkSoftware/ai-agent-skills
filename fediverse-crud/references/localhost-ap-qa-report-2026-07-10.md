# ActivityPub CRUD QA Report — demo & kidehen

**Date:** 2026-07-10  
**Virtuoso:** 08.03.3335 (Mac OS 15, Apple Silicon)  
**Actors:** `acct:kidehen@localhost`, `acct:demo@localhost`  
**Auth:** OAuth Authorization Code flow per actor, Chrome incognito, clear per-actor prompts  

---

## Results

| # | Operation | Actor | Target | Status | Location |
|---|-----------|-------|--------|:---:|------|
| 1 | **Create Note** | kidehen | (new) | 201 ✓ | `.../kidehen/outbox/cb9c91b55374630f` |
| 2 | **Create Note** | demo | (new) | 201 ✓ | `.../demo/outbox/b20ea48d07e5246c` |
| 3 | **Like** | kidehen | demo's Note (`b20ea48d07e5246c`) | 405 ⚠️ | `.../kidehen/outbox/54a7bab4e17f8ed4` |
| 4 | **Announce** | demo | kidehen's Note (`cb9c91b55374630f`) | 201 ✓ | `.../demo/outbox/c5c1745fef623658` |
| 5 | **Follow** | kidehen | demo's actor | 201 ✓ | `.../kidehen/outbox/e9bb8e698e55af87` |
| 6 | **Delete** | kidehen | own Note (`cb9c91b55374630f`) | 201 ✓ | `.../kidehen/outbox/51bee302b108646b` |
| 7 | **Undo Follow** | kidehen | Follow activity (`e9bb8e698e55af87`) | 201 ✓ | `.../kidehen/outbox/e786bdc75408972d` |

**Pass rate:** 6/7 (86%) — all intended operations except Like returned 201.

---

## Anomaly: Like Returns 405 (Reproduced)

### Test 1 (initial QA run, 13:42)

**Request:**

```bash
curl -sk -D - -X POST "https://localhost/DAV/home/kidehen/outbox/" \
  -H "Authorization: Bearer {kidehen_token}" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Like",
    "actor": "https://localhost/dataspace/person/kidehen",
    "object": "https://localhost/DAV/home/demo/outbox/b20ea48d07e5246c"
  }'
```

**Response:**
```
HTTP/1.1 405 Method Not Allowed
Location: https://localhost/DAV/home/kidehen/outbox/54a7bab4e17f8ed4
```

GET on `54a7bab4e17f8ed4` confirmed the Like was persisted (correct `as:Like` type, `actor`, `object`).

### Test 2 (retry with fresh auth, 14:13)

Same target object (`b20ea48d07e5246c`), fresh kidehen OAuth token, fresh dynamic client registration.

**Response:**
```
HTTP/1.1 405 Method Not Allowed
Location: https://localhost/DAV/home/kidehen/outbox/bde261749dc29a99
```

GET on `bde261749dc29a99` confirmed persistence:

```json
{
  "@type": "https://www.w3.org/ns/activitystreams#Like",
  "actor": "https://localhost/dataspace/person/kidehen",
  "object": {
    "@id": "https://localhost/DAV/home/demo/outbox/b20ea48d07e5246c",
    "@type": ["rdfs:Resource", "ldp:Resource"]
  }
}
```

### Conclusion

The Like activity is **always persisted** to the outbox despite the 405 status code. The resource is created correctly with valid `as:Like` type, `actor`, and `object` properties. The HTTP status is incorrect — should be 201 Created.

**Reproducibility:** 2/2 attempts return 405. The behavior is consistent.

**Difference btw local Shop and Actpub database tests:** On 2026-07-09 the identical Like payload (targeting `demo/.../6f7fadaaa1268c01`) returned **201 Created**. This is a server-side regression in Virtuoso 08.03.3335 — the Like activity handler switched from returning 201 to 405 between sessions, while continuing to correctly persist the resource.

---

## Cross-Actor Operations

| Operation | Actor | Target's Actor | Result |
|-----------|-------|:---:|:---:|
| kidehen likes demo's Note | kidehen | demo | 405 (persisted) |
| demo boosts kidehen's Note | demo | kidehen | 201 ✓ |
| kidehen follows demo | kidehen | demo | 201 ✓ |

Cross-actor operations (Announce, Follow) work correctly. The Like anomaly is isolated to that activity type.

---

## SPARQL Endpoint Change

The public SPARQL endpoint (`/sparql`) now requires authentication:

```
Permission denied: authentication required
```

Yesterday (2026-07-09) the same endpoint was open and queryable without auth. This prevents outbox and collection reconciliation via SPARQL for unauthenticated clients.

**Workaround:** Use the authenticated endpoint at `/sparql-auth/` or supply credentials.

---

## OAuth Auth Prompts

Both actors received clear browser prompts identifying which account to authenticate with:

```
── Authenticating as kidehen ──
  Opening browser → log in as kidehen@localhost
  Token: abf72de...

── Authenticating as demo ──
  Opening browser → log in as demo@localhost
  Token: 479d645...
```

The HTML success page also identifies the authenticated actor ("kidehen Authenticated" / "demo Authenticated").

---

## Activity Type Coverage

| Activity Type | Tested | Result |
|---------------|:---:|:---:|
| `Create` | ✓ | 201 |
| `Like` | ✓ | 405 (persisted) |
| `Announce` | ✓ | 201 |
| `Follow` | ✓ | 201 |
| `Delete` | ✓ | 201 |
| `Undo` | ✓ | 201 |

All 6 ActivityPub activity types exercised. 5/6 return correct 201. Like anomaly noted above.
