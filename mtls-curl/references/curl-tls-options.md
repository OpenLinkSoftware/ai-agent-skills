# curl TLS / mTLS Option Reference

## Client Certificate Options

| Flag | Description |
|------|-------------|
| `--cert-type P12` | Declare certificate format as PKCS#12 |
| `--cert-type PEM` | Declare certificate format as PEM |
| `--cert-type DER` | Declare certificate format as DER |
| `--cert {file}:{password}` | Supply client certificate and password (password may be omitted for PEM with no passphrase) |
| `--key {file}` | Separate private key file (PEM/DER only; not needed for PKCS#12 which bundles the key) |
| `--key-type PEM\|DER\|ENG` | Private key file type |

## Server Certificate Verification

| Flag | Description |
|------|-------------|
| `-k` / `--insecure` | Skip server certificate verification (test/internal use only) |
| `--cacert {file}` | Verify server against specific CA bundle (preferred over `-k`) |
| `--capath {dir}` | Directory of hashed CA certs (OpenSSL c_rehash format) |
| `--pinnedpubkey {hash}` | Pin server to an exact public key SHA-256 hash |

## TLS Version Control

| Flag | Description |
|------|-------------|
| `--tlsv1.0` | Minimum TLS 1.0 |
| `--tlsv1.2` | Minimum TLS 1.2 |
| `--tlsv1.3` | Minimum TLS 1.3 |
| `--tls-max 1.2` | Maximum TLS 1.2 (cap version) |
| `--tls-max 1.3` | Maximum TLS 1.3 |

## Cipher and Protocol Suites

| Flag | Description |
|------|-------------|
| `--ciphers {list}` | Restrict cipher list (OpenSSL cipher string format) |
| `--tls13-ciphers {list}` | Restrict TLS 1.3 cipher suites |
| `--curves {list}` | Restrict elliptic curves for ECDHE |

## Diagnostic and Debug Flags

| Flag | Description |
|------|-------------|
| `-v` | Verbose: full TLS handshake + request/response trace |
| `--trace {file}` | Write full hex trace to file |
| `--trace-ascii {file}` | Write ASCII trace to file |
| `-w "%{ssl_verify_result}"` | Print SSL verify result code |
| `-w "%{http_code}"` | Print HTTP response code only |

## Response Handling

| Flag | Description |
|------|-------------|
| `-i` | Include response headers in output |
| `-I` | HEAD request only (headers, no body) |
| `-L` | Follow redirects |
| `-o {file}` | Write response body to file |
| `-O` | Write response body to file named by URL |
| `-s` | Silent mode (suppress progress meter) |
| `--compressed` | Request gzip compression; decompress automatically |

## Common Compound Commands

```bash
# Minimal mTLS test — show status code only
curl -sk --cert-type P12 --cert "{file}:${MTLS_PWD}" \
  -o /dev/null -w "%{http_code}\n" "{url}"

# Full verbose handshake trace
curl -iLkv --cert-type P12 --cert "{file}:${MTLS_PWD}" "{url}" 2>&1

# mTLS SPARQL GET
curl -iLk --cert-type P12 --cert "{file}:${MTLS_PWD}" \
  -H "Accept: application/sparql-results+json" \
  "{sparql-endpoint}?query={encoded-query}"

# mTLS POST with JSON body
curl -iLk --cert-type P12 --cert "{file}:${MTLS_PWD}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d @{request-body.json} \
  "{url}"

# Use trusted CA bundle instead of -k
curl -iL --cert-type P12 --cert "{file}:${MTLS_PWD}" \
  --cacert /etc/ssl/certs/ca-certificates.crt \
  "{url}"
```
