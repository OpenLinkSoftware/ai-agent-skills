# OAuth Authorization Code Flow — acct:demo@localhost: curl Trace

**Date:** 2026-07-09  
**Goal:** Obtain an OAuth Bearer token for `acct:demo@localhost` and POST a Note (`"This is a QA test note"`) to the ActivityPub outbox.  
**Result:** Token obtained successfully; outbox POST blocked with **403 Forbidden: insufficient user permissions** + `WWW-Authenticate: Digest` challenge.

---

## Step 1 — OIDC Discovery

```bash
curl -sk https://localhost/.well-known/openid-configuration
```

**Key endpoints returned:**

| Endpoint | URL |
|----------|-----|
| Issuer | `https://localhost` |
| Authorization | `https://localhost/OAuth2/authorize` |
| Token | `https://localhost/OAuth2/token` |
| Registration | `https://localhost/OAuth2/register` |

**Supported scopes:** `openid`, `profile`, `email`, `address`, `phone`, `webid`, `offline_access`  
**Supported grant types:** `authorization_code`, `client_credentials`  
**Supported token auth methods:** `client_secret_basic`, `client_secret_post`, `client_secret_jwt`, `tls_client_auth`, `self_signed_tls_client_auth`

No `write` or ActivityPub-specific scope advertised.

---

## Step 2 — WebFinger: acct:demo@localhost

```bash
curl -sk "https://localhost/.well-known/webfinger?resource=acct:demo@localhost" \
  -H "Accept: application/jrd+json"
```

**Key links extracted:**

| Rel | Type | Href |
|-----|------|------|
| `self` | `application/activity+json` | `https://localhost/dataspace/person/demo` |
| `http://webfinger.net/rel/profile-page` | `text/html` | `https://localhost/dataspace/person/demo` |
| `describedby` | `text/turtle` | `https://localhost/dataspace/person/demo/foaf.ttl` |
| `describedby` | `application/ld+json` | `https://localhost/dataspace/person/demo/foaf.jsonld` |
| `salmon` | — | `https://localhost/ods/salmon` |

**Actor URI:** `https://localhost/dataspace/person/demo`  
**Outbox (by convention):** `https://localhost/dataspace/person/demo/outbox`

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
  "client_id": "903a252545ea055b940ad6f357f435e8573d4fc1",
  "client_secret": "...",
  "issuer": "https://localhost",
  "token_endpoint_auth_method": "none"
}
```

Dynamic registration succeeds — no admin pre-approval required.

---

## Step 4 — Authorization Code Flow (Browser)

Authorization URL opened in browser:

```
https://localhost/OAuth2/authorize?
  response_type=code&
  client_id=903a252545ea055b940ad6f357f435e8573d4fc1&
  redirect_uri=http%3A%2F%2Flocalhost%3A12345%2Fcallback&
  scope=openid%20profile%20email%20webid
```

User authenticates as `demo` via Digest prompt, grants OAuth consent. Browser redirects to `http://localhost:12345/callback?code={auth_code}`. Local Python HTTP server captures the code.

---

## Step 5 — Token Exchange

```bash
curl -sk -X POST https://localhost/OAuth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic {base64(client_id:client_secret)}" \
  -d "grant_type=authorization_code&code={auth_code}&redirect_uri=http%3A%2F%2Flocalhost%3A12345%2Fcallback"
```

**Response (200):**
```json
{
  "access_token": "65db72aa1f569f6ab99ecff5ab195bb3868...",
  "refresh_token": "3839cdec4598123fcc4cae4505b2945d...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "id_token": "eyJ..."
}
```

**ID token claims (decoded JWT payload):**
- `sub`: `https://localhost/dataspace/person/demo#this`
- `iss`: `https://localhost`

Token obtained successfully. The `sub` claim correctly identifies the `demo` actor.

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
    "published": "2026-07-09T13:44:57Z",
    "object": {
      "type": "Note",
      "attributedTo": "https://localhost/dataspace/person/demo",
      "content": "This is a QA test note",
      "to": ["https://www.w3.org/ns/activitystreams#Public"],
      "published": "2026-07-09T13:44:57Z"
    }
  }'
```

**Response:**
```
HTTP/1.1 403 Forbidden: insufficient user permissions
Server: Virtuoso/08.03.3335 (macOS 11 (Apple Silicon)) universal-apple-macos11  VDB
Content-Type: text/html; charset=UTF-8
WWW-Authenticate: Digest realm="DAV", domain="/DAV",
  nonce="90b52e8d917564ecc4fd8fb23cb5ea02",
  opaque="be46c4911088fb075550624a721bdedd",
  stale="false", qop="auth", algorithm="MD5"
Content-Length: 0
```

---

## Analysis

| Step | Result |
|------|--------|
| OIDC Discovery | ✓ All endpoints resolved |
| WebFinger | ✓ Actor URI resolved correctly |
| Dynamic Client Registration | ✓ Client registered (201) |
| Authorization Code (Browser) | ✓ User authenticated as `demo` |
| Token Exchange | ✓ Bearer token issued; `sub` = `demo#this` |
| **POST to Outbox** | **✗ 403 Forbidden** |

The OAuth flow is correct end-to-end. The Bearer token is valid and correctly bound to the `demo` actor's WebID. The failure is at the Virtuoso DAV ACL layer.

### Key observations

1. **403 (not 200 or 401).** The server actively rejects the write — a proper HTTP semantics response indicating the authenticated identity lacks sufficient permissions.
2. **Digest challenge in `WWW-Authenticate`.** The server offers Digest authentication as an alternative credential path. This suggests DAV Digest auth may be the expected mechanism for write operations to this dataspace path, and that OAuth Bearer tokens from dynamically registered clients do not carry write ACLs.
3. **No write/ActivityPub scope.** The OIDC provider only advertises identity scopes. There is no mechanism in the OAuth flow to signal intent for ActivityPub write operations.
4. **Dynamic vs pre-registered client.** The client is dynamically registered (`token_endpoint_auth_method: "none"`). A pre-registered/trusted client configured via Virtuoso Conductor may have different ACL characteristics.

### Potential resolution paths (not attempted)

- Use **Digest authentication** (from the `WWW-Authenticate` challenge) instead of OAuth Bearer for the outbox POST
- Grant the dynamic OAuth client write ACLs via Virtuoso Conductor (`/conductor/` → WebDAV ACL)
- Register the OAuth client as a pre-authorized/trusted client via Conductor
- Use `tls_client_auth` with a WebID-bound X.509 certificate
- Check `OAUTH2..SCOPE` configuration in Virtuoso for ActivityPub-specific scope/claim mapping
