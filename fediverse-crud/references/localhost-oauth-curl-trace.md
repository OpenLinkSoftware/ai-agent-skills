# OAuth Authorization Code Flow — localhost: curl Trace

**Date:** 2026-07-08  
**Goal:** Obtain an OAuth Bearer token for `acct:kidehen@localhost` and POST a Note to the ActivityPub outbox.  
**Result:** Token obtained successfully; outbox POST blocked by Virtuoso DAV ACL (`Permission denied`).

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
| UserInfo | `https://localhost/OAuth2/userinfo` |

**Supported scopes:** `openid`, `profile`, `email`, `address`, `phone`, `webid`, `offline_access`  
**Supported grant types:** `authorization_code`, `client_credentials`  
**Supported token auth methods:** `client_secret_basic`, `client_secret_post`, `client_secret_jwt`, `tls_client_auth`, `self_signed_tls_client_auth`

No `write` or ActivityPub-specific scope is advertised.

---

## Step 2 — Dynamic Client Registration

```bash
curl -sk -X POST https://localhost/OAuth2/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Claude Code Fediverse CRUD",
    "redirect_uris": ["http://localhost:12345/callback"],
    "grant_types": ["authorization_code"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "client_secret_post"
  }'
```

**Response (201):**
```json
{
  "client_id": "ff7d961299f33a0c82cacfc3557526a233405e1b",
  "client_secret": "4b992ce843a120de108fcecd048092a6",
  "issuer": "https://localhost",
  "authorization_endpoint": "https://localhost/OAuth2/authorize",
  "token_endpoint": "https://localhost/OAuth2/token",
  "token_endpoint_auth_method": "client_secret_post"
}
```

Dynamic registration succeeds — no admin pre-approval required.

---

## Step 3 — WebFinger Actor Resolution

```bash
curl -sk "https://localhost/.well-known/webfinger?resource=acct:kidehen@localhost" \
  -H "Accept: application/jrd+json"
```

**Key links returned:**

| Rel | Type | Href |
|-----|------|------|
| `self` | `application/activity+json` | `https://localhost/dataspace/person/kidehen` |
| `http://webfinger.net/rel/profile-page` | `text/html` | `https://localhost/dataspace/person/kidehen` |
| `describedby` | `text/turtle` | `https://localhost/dataspace/person/kidehen/foaf.ttl` |
| `salmon` | — | `https://localhost/ods/salmon` |

Actor URI resolved: `https://localhost/dataspace/person/kidehen`  
Outbox (by ActivityPub convention): `https://localhost/dataspace/person/kidehen/outbox`

---

## Step 4 — GET Actor Document (unauthenticated)

```bash
curl -sk -H "Accept: application/activity+json" \
  "https://localhost/dataspace/person/kidehen"
```

**Response:** `303 See Other` → `Location: https://localhost/dataspace/raw/person/kidehen/sioc.jsonld`

Following redirect returns `{}` (empty JSON object) — the actor document is not populated, or requires authentication.

---

## Step 5 — Authorization Code Flow (Browser)

Authorization URL constructed and opened in browser:

```
https://localhost/OAuth2/authorize?
  response_type=code&
  client_id=ff7d961299f33a0c82cacfc3557526a233405e1b&
  redirect_uri=http%3A%2F%2Flocalhost%3A12345%2Fcallback&
  scope=openid%20webid
```

User authenticates via Digest prompt, grants OAuth consent. Browser redirects to `http://localhost:12345/callback?code={auth_code}`. Local Python HTTP server captures the code.

---

## Step 6 — Token Exchange

```bash
curl -sk -X POST https://localhost/OAuth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code={auth_code}" \
  -d "redirect_uri=http://localhost:12345/callback" \
  -d "client_id=ff7d961299f33a0c82cacfc3557526a233405e1b" \
  -d "client_secret=4b992ce843a120de108fcecd048092a6"
```

**Response (200):**
```json
{
  "access_token": "0446105dba213fea6e311056ee24596ba0c00ffe",
  "refresh_token": "0eb324ed08abdd91576aa317f4181e12",
  "token_type": "Bearer",
  "expires_in": 3600,
  "id_token": "eyJ..."
}
```

**ID token claims (decoded JWT payload):**
- `sub`: `https://localhost/dataspace/person/kidehen#this`
- `iss`: `https://localhost`

Token obtained successfully. The `sub` claim correctly identifies the actor.

---

## Step 7 — POST Note to Outbox (FAILS)

```bash
curl -sk -D - -X POST "https://localhost/dataspace/person/kidehen/outbox" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
  -d '{
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Create",
    "actor": "https://localhost/dataspace/person/kidehen",
    "to": ["https://www.w3.org/ns/activitystreams#Public"],
    "object": {
      "type": "Note",
      "attributedTo": "https://localhost/dataspace/person/kidehen",
      "content": "This is a test QA note.",
      "to": ["https://www.w3.org/ns/activitystreams#Public"]
    }
  }'
```

**Response (200 OK):**
```
Permission denied to https://localhost/dataspace/person/kidehen
```

### Variations attempted — all returned the same error:

| Variation | Result |
|-----------|--------|
| Scope `openid` only | Permission denied |
| Scope `openid webid` | Permission denied |
| Scope `openid profile email webid` | Permission denied |
| `token_endpoint_auth_method: "client_secret_post"` | Permission denied |
| `token_endpoint_auth_method: "none"` + Basic auth exchange | Permission denied |
| Bare `Note` payload (no `Create` wrapper) | Permission denied |
| `Create` wrapping `Note` payload | Permission denied |
| With `On-Behalf-Of` header | Permission denied |
| POST to `/dataspace/kidehen/outbox` (alternate URI) | (empty response) |
| POST to `/dataspace/person/kidehen/inbox` | Permission denied |
| POST to `/activitypub/kidehen/outbox` | 404 Not Found |
| `client_credentials` grant | `access_denied` |

---

## Step 8 — GET Inbox (Authenticated)

```bash
curl -sk -H "Authorization: Bearer {access_token}" \
  -H "Accept: application/activity+json" \
  "https://localhost/dataspace/person/kidehen/inbox"
```

**Response:** `303 See Other` → redirects to `/dataspace/raw/person/kidehen/inbox/sioc.jsonld`

Same pattern as actor document — content negotiation via 303 redirect.

---

## Analysis

The OAuth Authorization Code flow works correctly end-to-end:
1. OIDC discovery succeeds
2. Dynamic client registration succeeds (no admin approval needed)
3. User authentication + consent succeeds
4. Token exchange succeeds — Bearer token with correct `sub` claim is issued

The failure is at the **Virtuoso WebDAV ACL layer**: the dynamically registered OAuth client, even when presenting a valid Bearer token bound to `kidehen`'s WebID, is not authorized to write to `https://localhost/dataspace/person/kidehen` (the DAV resource backing the outbox).

### Likely root causes:

1. **Dynamic clients lack write ACLs by default.** The Virtuoso ODS instance may require the OAuth client to be explicitly granted write permission via the DAV ACL system or Conductor admin UI before it can POST to protected dataspace paths.
2. **No ActivityPub-specific OAuth scope.** The OIDC provider advertises only identity scopes (`openid`, `profile`, `webid`). There is no `write`, `activitypub`, or `feed` scope to signal intent for write operations. The server may require a scope that isn't listed in the discovery document.
3. **WebID-TLS may be required for writes.** The OIDC provider supports `tls_client_auth` and `self_signed_tls_client_auth`. Write operations may be gated on certificate-based authentication (WebID-TLS) rather than Bearer tokens from dynamically registered clients.

### Next steps (not attempted):

- Grant the dynamic OAuth client write ACLs via Virtuoso Conductor (`/conductor/` → WebDAV ACL management)
- Try `tls_client_auth` token endpoint auth method with a client certificate bound to the WebID
- Register the OAuth client as a pre-authorized/trusted client via Conductor rather than dynamic registration
- Check whether the Virtuoso ODS ActivityPub module requires a specific OAuth scope mapped via `OAUTH2..SCOPE` configuration
