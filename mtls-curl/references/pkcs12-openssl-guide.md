# PKCS#12 / OpenSSL Quick Reference

## Validate a PKCS#12 File

```bash
# Check password and list contents (no extraction)
openssl pkcs12 -in cert.p12 -noout -passin "pass:${MTLS_PWD}"
```

Output `MAC verified OK` = password correct and bundle intact.

---

## Inspect Bundle Contents

```bash
# List all objects in the bundle
openssl pkcs12 -in cert.p12 -info -nokeys -passin "pass:${MTLS_PWD}"
```

Shows: Subject DN, Issuer DN, serial, validity dates, and any CA chain certs.

---

## Extract Components (PEM)

```bash
# Extract certificate only
openssl pkcs12 -in cert.p12 -clcerts -nokeys -out cert.pem \
  -passin "pass:${MTLS_PWD}"

# Extract private key (adds new passphrase)
openssl pkcs12 -in cert.p12 -nocerts -out key.pem \
  -passin "pass:${MTLS_PWD}" -passout "pass:${NEW_PWD}"

# Extract private key unencrypted (use with care)
openssl pkcs12 -in cert.p12 -nocerts -nodes -out key.pem \
  -passin "pass:${MTLS_PWD}"

# Extract CA chain only
openssl pkcs12 -in cert.p12 -cacerts -nokeys -out chain.pem \
  -passin "pass:${MTLS_PWD}"
```

---

## Convert Formats

```bash
# PEM cert + key → PKCS#12
openssl pkcs12 -export \
  -in cert.pem -inkey key.pem \
  -out bundle.p12 \
  -passout "pass:${NEW_PWD}"

# PKCS#12 → PEM (cert + key combined, unencrypted)
openssl pkcs12 -in cert.p12 -nodes -out bundle.pem \
  -passin "pass:${MTLS_PWD}"

# DER cert → PEM
openssl x509 -in cert.der -inform der -out cert.pem
```

---

## Inspect Certificate Details

```bash
# Subject, issuer, validity, SANs
openssl x509 -in cert.pem -noout -text | grep -E \
  "Subject:|Issuer:|Not Before:|Not After:|DNS:|IP Address:"

# Fingerprint (SHA-256)
openssl x509 -in cert.pem -noout -fingerprint -sha256
```

---

## Common Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| `Mac verify error` | Wrong password | Re-elicit password |
| `Could not read PKCS12 file` | File not found or not a valid P12 | Check path; verify file with `file cert.p12` |
| `no objects loaded` | Empty or mis-formed file | Re-export from original source |
| `invalid password` | OpenSSL 3.x stricter MAC | Try adding `-legacy` flag |
| `unable to load private key` | Key protected with different password than cert | Confirm P12 was exported with a single passphrase |

### OpenSSL 3.x Compatibility Note

Some legacy PKCS#12 files (exported by older Java keystores or Windows) use
RC2/3DES encryption that OpenSSL 3.x rejects by default. If you see
`unsupported` or `unknown` cipher errors:

```bash
# Attempt with legacy provider
openssl pkcs12 -legacy -in cert.p12 -noout -passin "pass:${MTLS_PWD}"
```

Or re-export the P12 using a modern cipher:

```bash
openssl pkcs12 -export -legacy \
  -in cert.pem -inkey key.pem \
  -out bundle_modern.p12 -passout "pass:${NEW_PWD}"
```
