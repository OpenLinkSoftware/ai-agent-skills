# OAuth Authorization Code Flow — localhost: curl Trace (Session 2)

**Date:** 2026-07-09  
**Goal:** Obtain OAuth Bearer tokens for three localhost users and POST Notes to their ActivityPub outboxes.  
**Result:** Tokens obtained successfully for all three users; all outbox POSTs blocked — two with `Permission denied`, one with `403 Forbidden`.

---

## Users Tested

| User | Actor URI | Outbox | Token | POST Result |
|------|-----------|--------|-------|-------------|
| `kidehen` | `https://localhost/dataspace/person/kidehen` | `.../outbox` | ✓ | 200 + "Permission denied" |
| `vdb` | `https://localhost/dataspace/person/vdb` | `.../outbox` | ✓ | 200 + "Permission denied" |
| `demo` | `https://localhost/dataspace/person/demo` | `.../outbox` | ✓ | **403** + "insufficient user permissions" |

---

## Step 1 — OIDC Discovery (shared)

```bash
curl -sk https://localhost/.well-known/openid-configuration
```

**Key endpoints:**

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

## Step 2 — Dynamic Client Registrations

Each run registered a fresh dynamic client:

```
POST https://localhost/OAuth2/register
Content-Type: application/json

{
  "client_name": "Claude Code Fediverse CRUD",
  "redirect_uris": ["http://localhost:12345/callback"],
  "grant_types": ["authorization_code"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "none",
  "scope": "openid profile email webid"
}
```

All three registrations succeeded (201) with `client_id` + `client_secret` returned. No admin pre-approval required.

---

## Step 3 — WebFinger Actor Resolution

### acct:kidehen@localhost

```bash
curl -sk "https://localhost/.well-known/webfinger?resource=acct:kidehen@localhost" \
  -H "Accept: application/jrd+json"
```

Self link: `https://localhost/dataspace/person/kidehen` (type: `application/activity+json`)

### acct:vdb@localhost

```bash
curl -sk "https://localhost/.well-known/webfinger?resource=acct:vdb@localhost" \
  -H "Accept: application/jrd+json"
```

Self link: `https://localhost/dataspace/person/vdb` (type: `application/activity+json`)

### acct:demo@localhost

```bash
curl -sk "https://localhost/.well-known/webfinger?resource=acct:demo@localhost" \
  -H "Accept: application/jrd+json"
```

Self link: `https://localhost/dataspace/person/demo` (type: `application/activity+json`)

All three users resolved via WebFinger successfully. All three also exposed a `salmon` endpoint at `https://localhost/ods/salmon`.

---

## Step 4 — GET Actor Documents

All three returned `303 See Other` → `Location: https://localhost/dataspace/raw/person/{user}/sioc.jsonld`. Following the redirect (with or without auth) returned `{}` (empty JSON object).

---

## Step 5 — Authorization Code Flow (Browser)

Each flow followed the same pattern:

```
https://localhost/OAuth2/authorize?
  response_type=code&
  client_id={client_id}&
  redirect_uri=http%3A%2F%2Flocalhost%3A12345%2Fcallback&
  scope=openid%20profile%20email%20webid
```

User authenticated as the target user in the browser. Browser redirected to `http://localhost:12345/callback?code={auth_code}`. Local Python HTTP server captured the code.

---

## Step 6 — Token Exchanges

```
POST https://localhost/OAuth2/token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {base64(client_id:client_secret)}

grant_type=authorization_code&code={auth_code}&redirect_uri=http%3A%2F%2Flocalhost%3A12345%2Fcallback
```

All three exchanges succeeded (200) with Bearer token, refresh token, and 3600s expiry. ID token `sub` claim confirmed correct actor WebID for each user.

---

## Step 7 — POST Notes to Outbox

### Payload (identical structure for all three):

```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Create",
  "actor": "https://localhost/dataspace/person/{user}",
  "to": ["https://www.w3.org/ns/activitystreams#Public"],
  "published": "2026-07-09T{timestamp}",
  "object": {
    "type": "Note",
    "attributedTo": "https://localhost/dataspace/person/{user}",
    "content": "This is a test QA note.",
    "to": ["https://www.w3.org/ns/activitystreams#Public"],
    "published": "2026-07-09T{timestamp}"
  }
}
```

### Command:

```bash
curl -sk -D - -X POST "https://localhost/dataspace/person/{user}/outbox" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{...}'
```

### Results:

**kidehen (Session 1):**
```
HTTP/1.1 200 OK
Content-Type: text/plain

Permission denied to https://localhost/dataspace/person/kidehen
```

**vdb:**
```
HTTP/1.1 200 OK
Content-Type: text/plain

Permission denied to https://localhost/dataspace/person/vdb
```

**demo:**
```
HTTP/1.1 403 Forbidden: insufficient user permissions
Content-Type: text/html; charset=UTF-8
WWW-Authenticate: Digest realm="DAV", domain="/DAV", nonce="ee0625e3b4b858fc96213e8e15b9cecc", opaque="be46c4911088fb075550624a721bdedd", stale="false", qop="auth", algorithm="MD5"
```

---

## Variations Attempted (all three users)

| Variation | kidehen | vdb | demo |
|-----------|---------|-----|------|
| Scope `openid` only | Permission denied | — | — |
| Scope `openid webid` | Permission denied | — | — |
| Scope `openid profile email webid` | Permission denied | Permission denied | 403 Forbidden |
| `token_endpoint_auth_method: "client_secret_post"` | Permission denied | — | — |
| `token_endpoint_auth_method: "none"` + Basic auth exchange | Permission denied | Permission denied | 403 Forbidden |
| Bare `Note` payload (no `Create` wrapper) | Permission denied | — | — |
| `Create` wrapping `Note` payload | Permission denied | Permission denied | 403 Forbidden |
| With `On-Behalf-Of` header | Permission denied | Permission denied | — |
| POST to `/dataspace/{user}/outbox` (alternate URI) | (empty) | — | — |
| POST to `/dataspace/person/{user}/inbox` | Permission denied | — | — |
| POST to `/activitypub/{user}/outbox` | 404 | — | — |
| `client_credentials` grant | `access_denied` | — | — |

---

## Analysis

### What works
1. OIDC discovery — all endpoints correctly advertised
2. Dynamic client registration — no admin approval needed
3. WebFinger resolution — all three users resolve correctly
4. Authorization Code flow — browser auth + consent works
5. Token exchange — Bearer tokens issued with correct `sub` claims
6. Token validity — tokens are accepted by the server (no 401)

### What fails
The outbox POST is blocked at the Virtuoso DAV ACL layer for all three users.

### Key difference: kidehen/vdb vs demo

| Aspect | kidehen / vdb | demo |
|--------|:------------:|:----:|
| HTTP status | 200 OK | **403 Forbidden** |
| Response body | "Permission denied to ..." | "insufficient user permissions" |
| Content-Type | text/plain | text/html |
| WWW-Authenticate | absent | **Digest challenge** |

The `demo` user's 403 + Digest challenge is more conventional HTTP semantics — the server rejects the OAuth Bearer token as insufficient for the write operation and offers Digest authentication as an alternative path. The `kidehen`/`vdb` 200 + "Permission denied" is non-standard (should be 401/403) and may indicate a different ACL configuration path.

### Likely root causes

1. **Dynamic OAuth clients lack write ACLs.** The Virtuoso ODS instance does not grant write permission to dataspace paths for dynamically registered OAuth clients, regardless of which user authenticated.
2. **No write/ActivityPub scope.** The OIDC provider only advertises identity scopes. No `write`, `feed`, or `activitypub` scope exists to signal intent for write operations.
3. **Digest auth may be required for writes.** The `demo` response explicitly offers Digest as an alternative — suggesting the outbox write path may be gated on DAV Digest authentication rather than OAuth Bearer tokens.
4. **WebID-TLS may be required.** The OIDC provider supports `tls_client_auth` — write operations may require certificate-based authentication bound to the actor's WebID.

### Next steps (not attempted)

- Grant the dynamic OAuth client write ACLs via Virtuoso Conductor (`/conductor/` → WebDAV ACL)
- Use Digest authentication (with the `demo` user's DAV credentials) for the outbox POST
- Use `tls_client_auth` token endpoint auth with a WebID-bound client certificate
- Register the OAuth client as a pre-authorized/trusted client via Conductor rather than dynamic registration
- Check `OAUTH2..SCOPE` configuration in Virtuoso for ActivityPub-specific scope mapping
