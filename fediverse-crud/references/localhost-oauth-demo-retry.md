# OAuth Authorization Code Flow — acct:demo@localhost (Retry #4)

**Date:** 2026-07-09  
**Goal:** OAuth token for `acct:demo@localhost`, incognito session, POST Note to outbox.  
**Virtuoso:** 08.03.3335 (Mac OS 15, Apple Silicon)  
**Result:** Token obtained; outbox POST → **403 Forbidden**.

---

## Step 1 — OIDC Discovery

```bash
curl -sk https://localhost/.well-known/openid-configuration
```

Issuer: `https://localhost`. Supported scopes: `openid profile email address phone webid offline_access`. No `write` scope.

---

## Step 2 — WebFinger

```bash
curl -sk "https://localhost/.well-known/webfinger?resource=acct:demo@localhost" \
  -H "Accept: application/jrd+json"
```

Self link: `https://localhost/dataspace/person/demo` (type: `application/activity+json`).

---

## Step 3 — Dynamic Client Registration

```bash
curl -sk -X POST https://localhost/OAuth2/register \
  -H "Content-Type: application/json" \
  -d '{"client_name":"Claude Demo Test","redirect_uris":["http://localhost:12345/callback"],"grant_types":["authorization_code"],"response_types":["code"],"token_endpoint_auth_method":"none","scope":"openid profile email webid"}'
```

**201** — `client_id`: `f5e076b67150766158bf4d5558b4efe659901237`.

---

## Step 4 — Authorization Code (Chrome Incognito)

```
open -na "Google Chrome" --args --incognito "{auth_url}"
```

User authenticated as `demo`, granted consent. Code captured at `localhost:12345/callback`.

---

## Step 5 — Token Exchange

```bash
curl -sk -X POST https://localhost/OAuth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic {base64(client_id:client_secret)}" \
  -d "grant_type=authorization_code&code={code}&redirect_uri=http%3A%2F%2Flocalhost%3A12345%2Fcallback"
```

**200** — `access_token` issued, expires 3600s. ID token `sub`: `https://localhost/dataspace/person/demo#this`.

---

## Step 6 — POST Note to Outbox

```bash
curl -sk -D - -X POST "https://localhost/dataspace/person/demo/outbox" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Create",
    "actor": "https://localhost/dataspace/person/demo",
    "to": ["https://www.w3.org/ns/activitystreams#Public"],
    "published": "2026-07-09T16:34:45Z",
    "object": {
      "type": "Note",
      "attributedTo": "https://localhost/dataspace/person/demo",
      "content": "This is a QA test note",
      "to": ["https://www.w3.org/ns/activitystreams#Public"],
      "published": "2026-07-09T16:34:45Z"
    }
  }'
```

**Response:**
```
HTTP/1.1 403 Forbidden: insufficient user permissions
Server: Virtuoso/08.03.3335 (Mac OS 15 (Apple Silicon)) universal-apple-macos15.0  VDB
WWW-Authenticate: Digest realm="DAV", domain="/DAV",
  nonce="7f92a1b3aae3247229acaf177a9262e8",
  opaque="be46c4911088fb075550624a721bdedd",
  stale="false", qop="auth", algorithm="MD5"
```

---

## Cumulative Results (All Attempts)

| # | Auth | Session | Response |
|---|------|---------|----------|
| 1 | OAuth Bearer | Normal | 403 Forbidden |
| 2 | Digest `demo:demo` | — | 403 Forbidden |
| 3 | OAuth Bearer | Incognito | 403 Forbidden |
| 4 | OAuth Bearer | Incognito | 403 Forbidden |

## Conclusion

All authentication methods succeed. The Virtuoso 08.03.3335 DAV ACL layer consistently denies write access to `/dataspace/person/demo/outbox` for the `demo` user. This requires a Conductor-side DAV ACL change.
