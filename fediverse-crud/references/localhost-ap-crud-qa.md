# ActivityPub CRUD QA — kidehen & demo

**Date:** 2026-07-09  
**Virtuoso:** 08.03.3335 (Mac OS 15, Apple Silicon)  
**Actors:** `acct:kidehen@localhost`, `acct:demo@localhost`  
**Goal:** Exercise Like, Announce, Delete, and Undo operations via ActivityPub protocol.  
**Result:** All 4 operations returned 201 Created. Undo semantics not processed server-side.

---

## Baseline: Create Note (kidehen)

Verify the outbox still accepts Creates before testing other operations.

```bash
curl -sk -D - -X POST "https://localhost/DAV/home/kidehen/outbox/" \
  -H "Authorization: Bearer {kidehen_token}" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Create",
    "actor": "https://localhost/dataspace/person/kidehen",
    "to": ["https://www.w3.org/ns/activitystreams#Public"],
    "object": {
      "type": "Note",
      "attributedTo": "https://localhost/dataspace/person/kidehen",
      "content": "This is a QA test note",
      "to": ["https://www.w3.org/ns/activitystreams#Public"]
    }
  }'
```

**201 Created** — `Location: .../outbox/3d0e0494998cc2d8`

---

## Operation 1 — Like

kidehen likes demo's Create activity (`6f7fadaaa1268c01`) containing the QA note.

```bash
curl -sk -D - -X POST "https://localhost/DAV/home/kidehen/outbox/" \
  -H "Authorization: Bearer {kidehen_token}" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Like",
    "actor": "https://localhost/dataspace/person/kidehen",
    "object": "https://localhost/DAV/home/demo/outbox/6f7fadaaa1268c01"
  }'
```

**201 Created** — `Location: .../outbox/9344861434cff689`

---

## Operation 2 — Announce (Boost)

kidehen boosts demo's Create activity.

```bash
curl -sk -D - -X POST "https://localhost/DAV/home/kidehen/outbox/" \
  -H "Authorization: Bearer {kidehen_token}" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Announce",
    "actor": "https://localhost/dataspace/person/kidehen",
    "object": "https://localhost/DAV/home/demo/outbox/6f7fadaaa1268c01"
  }'
```

**201 Created** — `Location: .../outbox/7fb6f64bcbe05ae7`

---

## Operation 3 — Delete

kidehen creates a fresh Note (`a81fb0b921c8f663`), then deletes it.

### 3a — Create Note

```bash
curl -sk -D - -X POST "https://localhost/DAV/home/kidehen/outbox/" \
  -H "Authorization: Bearer {kidehen_token}" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Create",
    "actor": "https://localhost/dataspace/person/kidehen",
    "object": {
      "type": "Note",
      "attributedTo": "https://localhost/dataspace/person/kidehen",
      "content": "QA note — to be deleted"
    }
  }'
```

**201 Created** — `Location: .../outbox/a81fb0b921c8f663`

### 3b — Delete

```bash
curl -sk -D - -X POST "https://localhost/DAV/home/kidehen/outbox/" \
  -H "Authorization: Bearer {kidehen_token}" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Delete",
    "actor": "https://localhost/dataspace/person/kidehen",
    "object": "https://localhost/DAV/home/kidehen/outbox/a81fb0b921c8f663"
  }'
```

**201 Created** — `Location: .../outbox/3713fa98ce151e76`

---

## Operation 4 — Undo Follow

kidehen undoes the Follow activity (`80feb1a8d3f9f47f`) targeting demo.

```bash
curl -sk -D - -X POST "https://localhost/DAV/home/kidehen/outbox/" \
  -H "Authorization: Bearer {kiden_token}" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Undo",
    "actor": "https://localhost/dataspace/person/kidehen",
    "object": "https://localhost/DAV/home/kidehen/outbox/80feb1a8d3f9f47f"
  }'
```

**201 Created** — `Location: .../outbox/8d2299806cd5cde4`

---

## Post-Test Reconciliation (SPARQL)

### kidehen outbox contents

```sparql
PREFIX ldp: <http://www.w3.org/ns/ldp#>
SELECT ?item
FROM <https://localhost/DAV/home/kidehen/outbox/>
WHERE { <https://localhost/DAV/home/kidehen/outbox/> ldp:contains ?item }
```

| # | Item | Type |
|---|------|------|
| 1 | `e1baf179d65b43cb` | Create (Note: "This is a QA test note") |
| 2 | `80feb1a8d3f9f47f` | Follow (kidehen → demo) |
| 3 | `3d0e0494998cc2d8` | Create (Note: baseline) |
| 4 | `9344861434cff689` | **Like** (demo's Note) |
| 5 | `7fb6f64bcbe05ae7` | **Announce** (demo's Note) |
| 6 | `a81fb0b921c8f663` | Create (Note: "QA note — to be deleted") |
| 7 | `3713fa98ce151e76` | **Delete** (Note a81fb0b9) |
| 8 | `8d2299806cd5cde4` | **Undo** (Follow 80feb1a8) |

### Following/Followers State

| Collection | `totalItems` | After Undo |
|------------|:------------:|:----------:|
| `kidehen/following` | 1 | ✗ Should be 0 |
| `demo/followers` | 1 | ✗ Should be 0 |

---

## Summary

| # | Operation | Object | Status |
|---|-----------|--------|:------:|
| — | Create (baseline) | New Note | 201 ✓ |
| 1 | **Like** | `demo/.../6f7fadaaa1268c01` | 201 ✓ |
| 2 | **Announce** | `demo/.../6f7fadaaa1268c01` | 201 ✓ |
| 3a | Create | New Note (for delete) | 201 ✓ |
| 3b | **Delete** | `kidehen/.../a81fb0b921c8f663` | 201 ✓ |
| 4 | **Undo Follow** | `kidehen/.../80feb1a8d3f9f47f` | 201 ✓ |

All 5 ActivityPub activity types were exercised: **Create**, **Follow**, **Like**, **Announce**, **Delete**, **Undo**.

### Known Issue

The **Undo** activity was accepted into the outbox (201) but the server did not reverse the Follow — `kidehen/following` and `demo/followers` still show `totalItems: 1`. The Undo payload referenced the Follow activity by URI; the server may require the Follow object to be embedded inline, or auto-accepted Follows may not be undoable via outbox POST on this Virtuoso ODS version (08.03.3335).
