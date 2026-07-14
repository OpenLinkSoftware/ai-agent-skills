# OAuth Authorization Code Flow — acct:demo@localhost (Incognito Session)

**Date:** 2026-07-09  
**Goal:** Obtain an OAuth Bearer token for `acct:demo@localhost` via a clean Chrome incognito session and POST a Note (`"This is a QA test note"`) to the ActivityPub outbox.  
**Result:** Token obtained; outbox POST blocked — **403 Forbidden**. Digest auth also attempted — same 403.

---

## Step 1 — OIDC Discovery

```bash
curl -sk https://localhost/.well-known/openid-configuration
```

| Endpoint | URL |
|----------|-----|
| Issuer | `https://localhost` |
| Authorization | `https://localhost/OAuth2/authorize` |
| Token | `https://localhost/OAuth2/token` |
| Registration | `https://localhost/OAuth2/register` |

**Scopes:** `openid`, `profile`, `email`, `address`, `phone`, `webid`, `offline_access`  
**Grant types:** `authorization_code`, `client_credentials`  
**Token auth methods:** `client_secret_basic`, `client_secret_post`, `client_secret_jwt`, `tls_client_auth`, `self_signed_tls_client_auth`

No `write` or ActivityPub-specific scope advertised.

---

## Step 2 — WebFinger

```bash
curl -sk "https://localhost/.well-known/webfinger?resource=acct:demo@localhost" \
  -H "Accept: application/jrd+json"
```

| Rel | Href |
|-----|------|
| `self` (activity+json) | `https://localhost/dataspace/person/demo` |
| profile-page | `https://localhost/dataspace/person/demo` |
| describedby (turtle) | `https://localhost/dataspace/person/demo/foaf.ttl` |
| describedby (ld+json) | `https://localhost/dataspace/person/demo/foaf.jsonld` |
| salmon | `https://localhost/ods/salmon` |

**Actor URI:** `https://localhost/dataspace/person/demo`  
**Outbox:** `https://localhost/dataspace/person/demo/outbox`

---

## Step 3 — Dynamic Client Registration

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

**Response (201):**
```json
{
  "client_id": "65a358ef80cc45800527ad3702de8aaeebe16898",
  "client_secret": "...",
  "issuer": "https://localhost"
}
```

---

## Step 4 — Authorization Code (Browser — Incognito)

Chrome launched with `--incognito` flag to prevent cookie contamination from prior sessions:

```
open -na "Google Chrome" --args --incognito "{auth_url}"
```

Authorization URL:
```
https://localhost/OAuth2/authorize?
  response_type=code&
  client_id=65a358ef80cc45800527ad3702de8aaeebe16898&
  redirect_uri=http%3A%2F%2Flocalhost%3A12345%2Fcallback&
  scope=openid%20profile%20email%20webid
```

User authenticated as `demo` via Digest prompt in incognito window, granted OAuth consent. Redirect to `localhost:12345/callback?code={code}` captured by local Python HTTP server.

---

## Step 5 — Token Exchange

```bash
curl -sk -X POST https://localhost/OAuth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic {base64(client_id:client_secret)}" \
  -d "grant_type=authorization_code&code={code}&redirect_uri=http%3A%2F%2Flocalhost%3A12345%2Fcallback"
```

**Response (200):**
```json
{
  "access_token": "be8600289afa4ca9728580d4a549130c47b...",
  "refresh_token": "00ae94547c497f974d2a6127c92c24a2...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

ID token claims: `sub` = `https://localhost/dataspace/person/demo#this`, `iss` = `https://localhost`.

---

## Step 6 — POST Note to Outbox (OAuth Bearer)

```bash
curl -sk -D - -X POST "https://localhost/dataspace/person/demo/outbox" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Create",
    "actor": "https://localhost/dataspace/person/demo",
    "to": ["https://www.w3.org/ns/activitystreams#Public"],
    "published": "2026-07-09T15:36:29Z",
    "object": {
      "type": "Note",
      "attributedTo": "https://localhost/dataspace/person/demo",
      "content": "This is a QA test note",
      "to": ["https://www.w3.org/ns/activitystreams#Public"],
      "published": "2026-07-09T15:36:29Z"
    }
  }'
```

**Response:**
```
HTTP/1.1 403 Forbidden: insufficient user permissions
WWW-Authenticate: Digest realm="DAV", domain="/DAV",
  nonce="2282bb3e7b9c1bceb567094200867db9",
  opaque="be46c4911088fb075550624a721bdedd",
  stale="false", qop="auth", algorithm="MD5"
```

---

## Step 7 — POST Note to Outbox (Digest Auth)

Initial request without auth triggers 401 + challenge:

```bash
curl -sk -D - -X POST "https://localhost/dataspace/person/demo/outbox" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{...}'
```

**Response:** `401 Unauthorized` + `WWW-Authenticate: Digest` (realm=DAV, nonce=..., algorithm=MD5)

Digest response computed (RFC 2617, MD5, qop=auth) and retried:

```bash
curl -sk -D - -X POST "https://localhost/dataspace/person/demo/outbox" \
  -H "Authorization: Digest username=\"demo\", realm=\"DAV\", nonce=\"...\", uri=\"/dataspace/person/demo/outbox\", algorithm=MD5, qop=auth, nc=00000001, cnonce=\"...\", response=\"...\", opaque=\"...\"" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{...}'
```

**Response:** `403 Forbidden: insufficient user permissions`

---

## Summary

| Step | Method | Result |
|------|--------|--------|
| OIDC Discovery | — | ✓ |
| WebFinger | — | ✓ Actor resolved |
| Dynamic Client Registration | — | ✓ Client registered (201) |
| Authorization Code | Incognito Chrome | ✓ Authenticated as `demo` |
| Token Exchange | — | ✓ Bearer token issued |
| POST to Outbox | OAuth Bearer | ✗ **403 Forbidden** |
| POST to Outbox | Digest `demo:demo` | ✗ **403 Forbidden** |

Both OAuth Bearer and Digest auth succeed at the authentication layer — the server accepts the credentials and identifies the caller as `demo`. The 403 comes from the DAV authorization layer: the `demo` user lacks write ACLs on `/dataspace/person/demo/outbox`. Incognito session confirmed the result is not cookie-related.

### Resolution

The `demo` user needs write permission granted on the dataspace path via Virtuoso Conductor → WebDAV ACL management.
