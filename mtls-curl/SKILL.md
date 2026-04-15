---
name: mtls-curl
description: "Execute mTLS (Mutual TLS) sessions using a PKCS#12 certificate bundle — either HTTP/HTTPS requests via curl (Mode A) or Virtuoso SQL sessions via iSQL with WebID authentication (Mode B). Interactively elicits the PKCS#12 file path, access password, CA bundle, and WebID URI when not already supplied. Use whenever the user wants to make an authenticated HTTP/HTTPS request using a client certificate, open a Virtuoso iSQL session with mTLS + WebID, test an mTLS-protected endpoint, or mentions PKCS#12, .p12, .pfx, mTLS, mutual TLS, iSQL, WebID, or -X/-T/-W flags."
---

# mTLS Session Skill (v1.1.0)

Executes mTLS-authenticated sessions using a PKCS#12 certificate bundle,
covering two modes:

- **Mode A — HTTP/HTTPS via `curl`** — one-shot or repeated HTTP requests
  against any mTLS-protected endpoint
- **Mode B — Virtuoso SQL via `isql`** — interactive SQL session authenticated
  by client certificate + WebID identity

Both modes guide the user through supplying (or locating) their `.p12` / `.pfx`
file and password before executing. Never logs, echoes, or stores the
certificate password.

---

## Execution Routing

1. **Local `curl`** (Mode A) — one-shot HTTP/HTTPS requests with client cert
2. **Local `isql`** (Mode B) — interactive Virtuoso SQL session with WebID auth
3. **Shell password elicitation** — `read -s` to collect the password without echo
4. **Environment variables** — accept `MTLS_PKCS12_FILE`, `MTLS_PKCS12_PWD`,
   `MTLS_CA_BUNDLE`, and `MTLS_WEBID` as pre-supplied inputs; skip elicitation
   when set

**Mode selection:** default to Mode A (curl) for HTTP endpoints; switch to
Mode B (iSQL) when the user mentions Virtuoso, iSQL, SQL session, port 1111,
or uses the `-X`/`-T`/`-W` flag syntax.

If the user explicitly specifies a different client (e.g., HTTPie, Python
`requests`, `openssl s_client`), follow that preference and adapt accordingly.

---

## Step 0 — Resolve Inputs

Collect all required inputs before constructing any command. Which inputs are
needed depends on the mode:

| # | Input | Mode A (curl) | Mode B (iSQL) | Source priority |
|---|-------|:---:|:---:|-----------------|
| 1 | **PKCS#12 file path** | required | required | Explicit arg → `$MTLS_PKCS12_FILE` → elicit |
| 2 | **PKCS#12 password** | required | required | `$MTLS_PKCS12_PWD` → elicit (masked) |
| 3 | **Target URL** | required | — | Explicit arg → elicit |
| 4 | **Host:port** | — | required | Explicit arg → elicit |
| 5 | **CA bundle path** | optional | required | Explicit arg → `$MTLS_CA_BUNDLE` → auto-detect → elicit |
| 6 | **WebID URI** | — | required | Explicit arg → `$MTLS_WEBID` → elicit |

### 0a — Locate PKCS#12 File

If the user has not supplied a path and `$MTLS_PKCS12_FILE` is unset:

```bash
# 1. Check environment
echo "${MTLS_PKCS12_FILE:-not set}"

# 2. Scan common locations for .p12 / .pfx files
find "$HOME" -maxdepth 5 \( -name "*.p12" -o -name "*.pfx" \) 2>/dev/null | head -20
```

Present any matches and ask the user to confirm which file to use:

> "I found the following PKCS#12 files. Which one should I use, or would you
> like to provide a different path?"

If no files are found, prompt:

> "Please provide the full path to your PKCS#12 (.p12 or .pfx) file."

### 0b — Elicit Password (Masked)

**Never** display, echo, or log the certificate password. Use shell masked
input so it does not appear in the terminal or in shell history:

```bash
# Collect password without echo — assign to shell variable only
read -s -p "PKCS#12 password: " MTLS_PWD
echo   # newline after silent input
```

If `$MTLS_PKCS12_PWD` is already set in the environment, skip this step and
inform the user:

> "Using password from \$MTLS_PKCS12_PWD environment variable."

### 0c — Elicit Target URL (Mode A)

If no URL was given, prompt:

> "Please provide the target URL for the mTLS request."

### 0d — Elicit Host:Port (Mode B)

If no host:port was given, prompt:

> "Please provide the Virtuoso host and port (e.g., `localhost:1111` or
> `data.example.org:1111`)."

Default Virtuoso iSQL port is **1111**.

### 0e — Locate CA Bundle (Mode B)

Required for iSQL's `-T` flag. Resolve in this order:

| Priority | Source |
|----------|--------|
| 1 | Explicit user argument |
| 2 | `$MTLS_CA_BUNDLE` environment variable |
| 3 | OS default bundle (see table below) |
| 4 | Interactive elicitation |

**OS default CA bundle locations:**

| OS | Default Path |
|----|-------------|
| macOS (Homebrew) | `/opt/homebrew/etc/openssl@3/cert.pem` |
| macOS (system) | `/etc/ssl/cert.pem` |
| Ubuntu / Debian | `/etc/ssl/certs/ca-certificates.crt` |
| RHEL / CentOS | `/etc/pki/tls/certs/ca-bundle.crt` |
| Alpine | `/etc/ssl/certs/ca-certificates.crt` |

```bash
# Auto-detect: try each path in order
for f in \
  "$MTLS_CA_BUNDLE" \
  /opt/homebrew/etc/openssl@3/cert.pem \
  /etc/ssl/cert.pem \
  /etc/ssl/certs/ca-certificates.crt \
  /etc/pki/tls/certs/ca-bundle.crt; do
  [ -f "$f" ] && echo "Found CA bundle: $f" && break
done
```

If none found, prompt:

> "Please provide the path to your CA certificate bundle (e.g., `ca-bundle.crt`)."

### 0f — Elicit WebID URI (Mode B)

The WebID URI identifies the user/agent in the server's access control policy.
It is the `rdfs:seeAlso` link in the TLS client certificate's Subject
Alternative Name (SAN) extension, pointing to an RDF profile document that
asserts the public key.

Resolve in this order:

| Priority | Source |
|----------|--------|
| 1 | Explicit user argument |
| 2 | `$MTLS_WEBID` environment variable |
| 3 | Extract from client cert SAN |
| 4 | Interactive elicitation |

```bash
# Attempt to extract WebID URI from PKCS#12 SAN extension
openssl pkcs12 -in "{pkcs12-file}" -clcerts -nokeys \
  -passin "pass:${MTLS_PWD}" 2>/dev/null \
  | openssl x509 -noout -text 2>/dev/null \
  | grep -A2 "Subject Alternative Name" \
  | grep -oE "URI:[^\s,]+" | sed 's/URI://'
```

If found, confirm with the user:

> "Found WebID URI in your certificate: `{webid-uri}`. Use this?"

If not found or not confirmed, prompt:

> "Please provide your WebID URI (e.g.,
> `https://id.example.org/dataspace/person/alice#this`)."

---

---

## Mode A — HTTP/HTTPS via `curl`

---

## Step 1 — Validate the Certificate Bundle

Before making a live request, verify the PKCS#12 file is readable and the
password is correct:

```bash
openssl pkcs12 \
  -in "{pkcs12-file}" \
  -noout \
  -passin "pass:${MTLS_PWD}" 2>&1
```

| Result | Action |
|--------|--------|
| `MAC verified OK` or no error output | Proceed to Step 2 |
| `Mac verify error` | Report bad password; return to Step 0b |
| `No such file or directory` | Report bad path; return to Step 0a |
| `openssl: command not found` | Instruct user to install openssl; skip validation |

---

## Step 2 — Execute the mTLS Request

Construct and run the canonical `curl` command:

```bash
curl -iLk \
  --cert-type P12 \
  --cert "{pkcs12-file}:${MTLS_PWD}" \
  "{target-url}"
```

### Curl Flag Reference

| Flag | Meaning |
|------|---------|
| `-i` | Include HTTP response headers in output |
| `-L` | Follow HTTP redirects (3xx) |
| `-k` | Allow insecure server certificates (self-signed / internal CAs) |
| `--cert-type P12` | Tell curl the certificate is PKCS#12 format |
| `--cert file:pwd` | Supply client certificate and password together |

### Optional Flag Extensions

Append any of these when the user requests more detail or control:

| Flag | Effect |
|------|--------|
| `-v` | Verbose: show TLS handshake, request/response headers |
| `--tls-max 1.2` | Cap TLS version (e.g., force TLS 1.2) |
| `--tlsv1.3` | Require TLS 1.3 minimum |
| `-H "Accept: application/json"` | Set Accept header |
| `-H "Authorization: Bearer {token}"` | Add Bearer token alongside mTLS |
| `-o /dev/null -w "%{http_code}"` | Return only the HTTP status code |
| `--cacert {ca-bundle}` | Verify server against a specific CA bundle (replaces `-k`) |
| `-X POST --data @{file}` | POST a request body from a file |
| `--compressed` | Request gzip-compressed response |
| `-s` | Silent: suppress progress meter (use with `-o` or piping) |

> **Security note:** Replace `-k` with `--cacert {ca-bundle}` whenever a
> trusted CA bundle is available. `-k` disables server certificate verification
> and should only be used on internal or test endpoints.

---

## Step 3 — Present and Interpret the Response

Display the full response (headers + body). Then annotate key fields:

### HTTP Status Codes

| Range | Meaning |
|-------|---------|
| 2xx | Success — request accepted |
| 401 | Unauthorized — client cert rejected or credentials mismatch |
| 403 | Forbidden — cert valid but insufficient permissions |
| 495 | SSL Certificate Error — cert presented but invalid |
| 496 | SSL Certificate Required — no client cert presented |
| 526 | Invalid SSL Certificate — server-side issue |

### TLS Handshake Failures (visible with `-v`)

| Error string | Likely cause |
|---|---|
| `SSL_ERROR_HANDSHAKE_FAILURE_ALERT` | Server rejected the client cert |
| `certificate verify failed` | CA chain mismatch (add `--cacert`) |
| `no certificate or key found` | Wrong password or corrupted P12 |
| `NSS error -8023` | PKCS#12 passphrase incorrect (NSS backend) |

---

## Step 4 — Session Reuse (Optional)

After a successful request, offer:

> "Would you like to reuse this certificate for additional requests in this
> session? I can remember the file path (but not the password — you will be
> prompted again for each new shell invocation)."

If yes, set the path in the current shell environment:

```bash
export MTLS_PKCS12_FILE="{pkcs12-file}"
```

Never persist the password to environment, shell history, or any file.

---

---

## Mode B — Virtuoso SQL via `isql`

---

## Step 5 — Validate Inputs (Mode B)

Run the same PKCS#12 bundle validation as Step 1, then additionally confirm
the CA bundle is readable:

```bash
# PKCS#12 validation (same as Step 1)
openssl pkcs12 -in "{pkcs12-file}" -noout -passin "pass:${MTLS_PWD}" 2>&1

# CA bundle readable?
openssl verify -CAfile "{ca-bundle}" "{ca-bundle}" 2>&1 | head -3
```

---

## Step 6 — Construct and Execute the iSQL Command

The canonical Virtuoso mTLS + WebID iSQL invocation:

```
isql {host}:{port} "" {pkcs12-pwd} -X {pkcs12-file} -T {ca-bundle} -W {user-webid}
```

### Argument breakdown

| Position / Flag | Value | Notes |
|-----------------|-------|-------|
| `{host}:{port}` | e.g., `localhost:1111` | First positional — connection target |
| `""` | empty string | Second positional — **username must be empty**; signals cert-based auth |
| `{pkcs12-pwd}` | password string | Third positional — PKCS#12 passphrase |
| `-X {pkcs12-file}` | path to `.p12` / `.pfx` | Client certificate bundle |
| `-T {ca-bundle}` | path to CA cert file | Server certificate verification; required for TLS |
| `-W {user-webid}` | WebID URI | Identity assertion — must match a key in the server's ACL graph |

### The empty-username convention

The `""` (empty string) in the username position is the signal to Virtuoso's
iSQL that no SQL-layer username/password auth should occur. Authentication is
delegated entirely to:
1. The TLS handshake (client cert presented via `-X`)
2. The WebID profile lookup (identity asserted via `-W`)

Passing any non-empty username here would attempt SQL password authentication
in parallel and likely fail or shadow the WebID flow.

### Preview before execution

Always show the sanitized form (password as `****`) before running:

```
isql {host}:{port} "" **** -X {pkcs12-file} -T {ca-bundle} -W {user-webid}
```

Confirm with the user, then execute:

```bash
isql "{host}:{port}" "" "${MTLS_PWD}" \
  -X "{pkcs12-file}" \
  -T "{ca-bundle}" \
  -W "{user-webid}"
```

> **Security note:** Unlike curl's `--cert file:pwd`, the iSQL password is a
> plain positional argument and will be briefly visible in `ps` output for the
> duration of the process start. Mitigate by:
> - Using a shell variable (not a literal string) so the value isn't in
>   `.bash_history` / `.zsh_history`
> - Running in a dedicated terminal session with restricted `ps` visibility
> - Preferring certificate-only auth flows where Virtuoso supports it

---

## Step 7 — Interactive SQL Session (Mode B)

On successful connection, `isql` presents a prompt:

```
Connected to OpenLink Virtuoso
Driver: 08.03.3337 OpenLink Virtuoso ODBC Driver
OpenLink Interactive SQL (Virtuoso), version 0.9849b.
Type HELP; for help and EXIT; to exit.
SQL>
```

The session runs under the identity of the WebID — access control is governed
by Virtuoso's VAL (Virtuoso Access Layer) ACL graph for that WebID.

### Useful session commands

| Command | Effect |
|---------|--------|
| `SELECT USER;` | Confirm the authenticated user identity |
| `SPARQL SELECT * WHERE { ?s ?p ?o } LIMIT 5;` | Run a SPARQL query inline |
| `SELECT TOP 10 * FROM Demo.Demo.Customers;` | SQL query |
| `GRANT EXECUTE ON ...` | Grant privileges (if WebID has DBA role) |
| `HELP;` | List available commands |
| `EXIT;` | Close the session |

### Non-interactive (batch) mode

To run a single statement without entering the interactive prompt:

```bash
echo "SELECT USER;" \
  | isql "{host}:{port}" "" "${MTLS_PWD}" \
      -X "{pkcs12-file}" \
      -T "{ca-bundle}" \
      -W "{user-webid}"
```

Or pass a script file:

```bash
isql "{host}:{port}" "" "${MTLS_PWD}" \
  -X "{pkcs12-file}" \
  -T "{ca-bundle}" \
  -W "{user-webid}" \
  < my-script.sql
```

---

## Step 8 — Session Reuse (Mode B)

After a successful iSQL session, offer to export the non-secret inputs:

```bash
export MTLS_PKCS12_FILE="{pkcs12-file}"
export MTLS_CA_BUNDLE="{ca-bundle}"
export MTLS_WEBID="{user-webid}"
# Note: MTLS_PKCS12_PWD intentionally NOT exported — re-elicit each session
```

---

## Mode B Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `Cannot login` | WebID not in server ACL | Check VAL ACL graph; confirm WebID has `SELECT` access |
| `SSL handshake failed` | CA bundle mismatch or cert not trusted | Verify `-T` points to the correct CA that signed the server cert |
| `Invalid certificate` | Wrong P12 or wrong password | Re-validate with `openssl pkcs12 -noout` |
| `no such user` error after connect | Username field not empty | Ensure second positional arg is `""` (empty string) |
| `WebID verification failed` | WebID profile document unreachable or key mismatch | Confirm WebID URI resolves and its RDF profile contains the cert's public key |
| `Connection refused` | Wrong host:port | Verify Virtuoso is running on the target port (`telnet {host} {port}`) |
| `isql: command not found` | Virtuoso client tools not in PATH | Locate with `find /opt /usr -name isql 2>/dev/null`; add to PATH |

---

## Security Guidelines

1. **Password never logged** — always use `read -s`; never interpolate the
   password into a visible command string displayed to the user.
2. **Prefer `--cacert` over `-k`** — only use `-k` when the server uses a
   self-signed or internal CA that cannot be trusted via bundle.
3. **Scope the certificate** — use purpose-specific `.p12` files (agent
   certificates) rather than personal identity certificates where possible.
4. **Short-lived sessions** — do not cache passwords across shell sessions;
   re-elicit on each invocation.
5. **Audit curl flags** — always show the user the exact `curl` command that
   will run (with password replaced by `****`) before executing:

```
curl -iLk --cert-type P12 --cert "{pkcs12-file}:****" "{target-url}"
```

---

## Common Usage Patterns — Mode A (curl)

### Pattern A — Quick endpoint test

User says: *"Test mTLS against https://api.example.com/health"*

1. Elicit PKCS#12 file and password
2. Validate bundle
3. Run: `curl -iLk --cert-type P12 --cert "{file}:${MTLS_PWD}" https://api.example.com/health`
4. Display response + HTTP status interpretation

### Pattern B — SPARQL endpoint with client cert

User says: *"Query https://data.example.org/sparql with my agent cert"*

1. Elicit PKCS#12 file and password
2. Run SPARQL GET:
   ```bash
   curl -iLk \
     --cert-type P12 \
     --cert "{file}:${MTLS_PWD}" \
     -H "Accept: application/sparql-results+json" \
     "https://data.example.org/sparql?query=SELECT+*+WHERE+%7B%3Fs+%3Fp+%3Fo%7D+LIMIT+10"
   ```

### Pattern C — Verbose TLS debug

User says: *"Show me the TLS handshake details"*

```bash
curl -iLkv \
  --cert-type P12 \
  --cert "{file}:${MTLS_PWD}" \
  "{target-url}" 2>&1
```

### Pattern D — POST with JSON body

```bash
curl -iLk \
  --cert-type P12 \
  --cert "{file}:${MTLS_PWD}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"key":"value"}' \
  "{target-url}"
```

---

## Common Usage Patterns — Mode B (iSQL)

### Pattern E — Standard Virtuoso mTLS + WebID session

User says: *"Open an iSQL session on localhost:1111 with my agent cert"*

1. Elicit (or confirm) PKCS#12 file, password, CA bundle, WebID URI
2. Validate bundle
3. Show sanitized preview:
   ```
   isql localhost:1111 "" **** -X agent.p12 -T ca-bundle.crt -W https://id.example.org/me#this
   ```
4. Execute:
   ```bash
   isql "localhost:1111" "" "${MTLS_PWD}" \
     -X agent.p12 \
     -T ca-bundle.crt \
     -W "https://id.example.org/me#this"
   ```
5. At `SQL>` prompt, run `SELECT USER;` to confirm authenticated identity

### Pattern F — Batch SPARQL via iSQL

User says: *"Run a SPARQL query over iSQL with my cert"*

```bash
echo 'SPARQL SELECT DISTINCT ?type WHERE { ?s a ?type } LIMIT 10;' \
  | isql "{host}:{port}" "" "${MTLS_PWD}" \
      -X "{pkcs12-file}" \
      -T "{ca-bundle}" \
      -W "{user-webid}"
```

### Pattern G — Verify WebID identity on connection

```bash
echo "SELECT USER, SYS_STAT('st_dbms_name');" \
  | isql "{host}:{port}" "" "${MTLS_PWD}" \
      -X "{pkcs12-file}" \
      -T "{ca-bundle}" \
      -W "{user-webid}"
```

Expected output confirms the WebID URI as the session identity.

---

## Initialization Sequence

When invoked:
1. Determine mode: **A** (curl / HTTP) or **B** (iSQL / Virtuoso SQL)
2. Run Step 0 — resolve all required inputs for the selected mode
3. Run Step 1 / Step 5 — validate PKCS#12 bundle (skip only if openssl unavailable)
4. Show the user the sanitized command (password as `****`)
5. Confirm before executing, or execute immediately if the user said "go ahead"

**Mode A continues:**
6. Run Step 2 — execute curl request
7. Run Step 3 — present and annotate response
8. Offer Step 4 — export PKCS#12 path for session reuse

**Mode B continues:**
6. Run Step 6 — execute iSQL session
7. Run Step 7 — assist with interactive or batch SQL
8. Offer Step 8 — export non-secret inputs for session reuse

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `curl: (58) unable to set private key file` | Wrong password | Re-elicit password; re-validate with openssl |
| `curl: (35) OpenSSL SSL_connect` | TLS version mismatch | Add `--tlsv1.2` or `--tls-max 1.3` |
| `curl: (6) Could not resolve host` | DNS failure | Check URL spelling and network |
| `curl: (60) SSL certificate problem` | Server cert untrusted | Add `--cacert {bundle}` or use `-k` for testing |
| `curl: (77) Problem with the SSL CA cert` | Bad `--cacert` path | Verify CA bundle path |
| `HTTP 401` after cert presented | Cert not authorized on server | Confirm correct cert is enrolled on target |
| `HTTP 403` | Cert valid, insufficient scope | Check server-side ACL/role for this cert's CN/SAN |
| openssl `Mac verify error` | Wrong P12 password | Re-elicit password |

---

## Reference Files

| File | Contents |
|------|----------|
| `references/curl-tls-options.md` | Complete curl TLS flag reference with examples |
| `references/pkcs12-openssl-guide.md` | Working with PKCS#12 files: inspect, extract, convert |
| `references/virtuoso-isql-mtls.md` | Virtuoso iSQL mTLS + WebID flag reference and session guide |

---

## Version

**1.1.0** — Added Mode B: Virtuoso iSQL mTLS + WebID authentication. Interactive
elicitation for CA bundle and WebID URI. Auto-detect WebID from certificate SAN.
OS CA bundle auto-detection. Empty-username convention documented. iSQL batch
mode. Session export for non-secret inputs.
