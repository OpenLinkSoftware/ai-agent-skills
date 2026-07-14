# ACME Certificate Workflows for YouID

## Overview

The YouID skill supports three certificate types for WebID identity certificates:

| Type | Trust Chain | CA | Uses | Best For |
|------|-------------|-----|-------|----------|
| **Self-signed** | None (root is own key) | None | WebID-TLS, NetID identity | Quick dev, testing, internal use |
| **Let's Encrypt** | ISRG Root X1 → R3 → Your cert | Let's Encrypt | Public WebID, DPKI | Production WebIDs on public domains |
| **ZeroSSL** | ZeroSSL Root → Intermediate → Your cert | ZeroSSL (SSL.com) | Public WebID, DPKI | Alternative to LE, longer validity |

## How ACME Certificates Work for WebID

ACME (Automatic Certificate Management Environment) issues Domain-Validated (DV) certificates. The ACME CA verifies that you control the domain, then signs your certificate.

### SAN Strategy

For WebID certificates, the CSR contains two Subject Alternative Names:

```
DNS:example.org          ← Validated by ACME (domain ownership)
URI:https://example.org/people/jane#me  ← Pass-through (not validated, but included in cert)
```

The ACME CA validates only the DNS name. The URI SAN is included in the resulting certificate but is not checked by the CA — this is standard ACME behavior. Both SANs appear in the signed certificate, making it usable for WebID-TLS.

### ACME Challenge Types

| Challenge | What's Needed | When to Use |
|-----------|--------------|-------------|
| **HTTP-01** | Port 80/443 accessible, `/.well-known/acme-challenge/` reachable | Default. Domain points to a server you control |
| **DNS-01** | DNS provider API key (Cloudflare, Route53, etc.) | Domain is behind a proxy or not directly accessible on port 80 |
| **TLS-ALPN-01** | Port 443 with ALPN support | Minimal, but requires modifying server TLS config |

Default for YouID ACME modes: **HTTP-01** (via `acme.sh --standalone` on port 80).

## Cert Type Comparison

### Self-Signed

```
openssl genrsa -out key.pem 2048
openssl req -new -x509 -key key.pem -out cert.pem \
    -days 365 \
    -subj "/CN=Jane Doe" \
    -addext "subjectAltName=URI:https://example.org/people/jane#me"
```

- Quick, no external dependency
- No domain validation needed
- Not trusted by browsers/OS trust stores
- Can be used for WebID-TLS with explicit trust configuration

### Let's Encrypt (via ACME)

```
1. Generate key + CSR with DNS:example.org + URI:https://... (created by acme_helper.sh)
2. acme.sh --sign-csr --csr csr.pem -d example.org --server letsencrypt
3. ACME validates domain ownership (HTTP-01 or DNS-01)
4. CA signs the certificate (includes both DNS and URI SANs)
5. Download fullchain.cer → cert.pem
```

- Widely trusted (in most browser/OS trust stores)
- 90-day validity (auto-renewable)
- Domain validation required
- Rate limits: 50 certificates/week/domain (production), 30/week (staging)

### ZeroSSL (via ACME)

```
1. Obtain ZeroSSL API key from https://app.zerossl.com/developers
2. Generate key + CSR with DNS + URI SANs (created by acme_helper.sh)
3. Fetch EAB credentials via ZeroSSL API: POST /acme/eab-credentials
4. acme.sh --sign-csr --csr csr.pem -d example.org \
     --server zerossl \
     --eab-kid <kid> --eab-hmac-key <key>
5. ACME validates domain ownership
6. Download signed certificate
```

- Alternative trust chain (SSL.com root)
- Up to 90-day validity
- Requires API key for External Account Binding (EAB)
- 3 free certificates per month (no rate limits on paid plans)

## Directory URLs

| CA | Production | Staging |
|------|-----------|---------|
| Let's Encrypt | `https://acme-v02.api.letsencrypt.org/directory` | `https://acme-staging-v02.api.letsencrypt.org/directory` |
| ZeroSSL | `https://acme.zerossl.com/v2/DV90` | Same (no staging, use LE staging for dev) |

## ZeroSSL External Account Binding

ZeroSSL requires EAB for all ACME accounts. The flow:

1. User creates an API key at `https://app.zerossl.com/developers`
2. `zerossl_fetch_eab()` calls `POST https://api.zerossl.com/acme/eab-credentials?access_key=<key>`
3. Response returns `eab_kid` and `eab_hmac_key`
4. These are passed to `acme.sh --eab-kid <kid> --eab-hmac-key <key>`
5. `acme.sh` includes the EAB JWS in the newAccount request

## acme.sh Auto-Install

The YouID skill auto-installs acme.sh when needed:

```bash
ensure_acme_sh "admin@example.org"
# Installs via: curl -fsSL https://get.acme.sh | sh -s email=admin@example.org
```

Install location: `~/.acme.sh/acme.sh`

## Output Files

After ACME signing, the following files are in `~/.acme.sh/<domain>/`:

| File | Description | Copied To |
|------|-------------|-----------|
| `fullchain.cer` | Full certificate chain (leaf + intermediates) | `cert.pem` |
| `ca.cer` | CA/issuer certificate | `ca.cer` |
| `<domain>.cer` | Leaf certificate only | (merged into fullchain) |
| `<domain>.key` | Private key (from acme.sh) | Not used; we use our own key |

> Note: `acme.sh` also creates `_ecc` suffixed directories when ECDSA keys are used. The YouID skill uses RSA 2048 exclusively, so the non-ECC path is used.

## CA Certificate URLs for Templates

When `ca_cert_url` is set in `cert_data.json`, the template conditionals (`!!{ca_cert_url}`) activate CA-certificate blocks in profile documents.

| CA | ca_cert_url |
|----|-------------|
| Let's Encrypt | `https://letsencrypt.org/certs/2024/` |
| ZeroSSL | `https://zerossl.com/resources/` |

The `ca_cert_url` is inserted into generated documents as:
- `oplcert:IAN <%{ca_cert_url}>` (certificate ontology — Issuer Alternate Name)
- `xhv:alternate <%{ca_cert_url}>` (alternate representation link)
- HTML link to download CA certificate

## Staging vs Production

### Let's Encrypt Staging

Use `--acme-staging` flag for testing:

```bash
./generate_certificate.sh --mode letsencrypt \
    --common-name "Test User" \
    --webid "https://example.org/people/test#me" \
    --acme-domain example.org \
    --acme-staging
```

Staging certificates:
- Are NOT trusted by browsers
- Have no rate limits (95% of production rate limits)
- Have relaxed validation (still requires domain control)
- Issued by "Fake LE Intermediate X1"

### Production (default)

```bash
./generate_certificate.sh --mode letsencrypt \
    --common-name "Jane Doe" \
    --webid "https://example.org/people/jane#me" \
    --acme-domain example.org
```

Production certificates:
- Are publicly trusted
- Subject to rate limits: 50 certs/week/domain
- 90-day validity

## Rate Limit Information

### Let's Encrypt
| Limit | Value |
|-------|-------|
| Certificates per domain per week | 50 (production), unlimited (staging) |
| Failed validations per domain per hour | 5 |
| Authorizations per account per hour | 300 |
| Duplicate certificate per week | 5 |

### ZeroSSL
| Limit | Value |
|-------|-------|
| Free certificates per month | 3 |
| Paid plans | 100+ per month |

## Troubleshooting

### acme.sh fails with "No authorization found"
- Check that port 80 is accessible (for HTTP-01)
- Check DNS resolution: `dig <domain> A`
- Try staging server first (more lenient)

### Certificate issued but doesn't contain URI SAN
- Rare, but verify with: `openssl x509 -in cert.pem -noout -ext subjectAltName`
- The CSR must have `URI:...` in subjectAltName
- Check CSR before signing: `openssl req -in csr.pem -noout -text`

### ZeroSSL EAB fails
- Verify API key is valid
- Check API key permissions in ZeroSSL dashboard
- Try fetching EAB manually: `curl -s -X POST "https://api.zerossl.com/acme/eab-credentials?access_key=YOUR_KEY"`

### Port 80 not available
- Use DNS-01 challenge instead: `acme.sh --sign-csr --csr csr.pem -d example.org --dns dns_cf` (Cloudflare)
- Or use `--standalone --httpport 8080` with port forwarding

## Virtuoso ACME Note

Virtuoso includes a native ACME protocol implementation (`ACME.DBA` schema in `acme.sql`) supporting Let's Encrypt and ZeroSSL. However, Virtuoso's CSR generation (`ACME.DBA.make_csr`) only generates DNS Subject Alternative Names (`DNS:` prefix), not URI SANs. This makes it unsuitable for WebID identity certificates directly.

Virtuoso ACME is recommended for:
- Server TLS certificates (HTTPS hosting)
- Internal PKI automation
- Testing ACME workflows in a Virtuoso-hosted environment

For WebID certificates with URI SANs, the `acme.sh` route is required.
