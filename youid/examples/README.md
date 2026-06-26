# YouID Skill — Example Prompts

These example prompts demonstrate how to invoke the youid skill for common identity workflows. Use them as templates — replace placeholder values (e.g. `{name}`, `{webid}`) with the actual identity data.

## Prerequisites

**Credentials are generated locally, then copied to the destination server.** The skill produces all credential files in a local output directory:

```
./youid-output/{webid-label}/
```

The WebID URI (e.g. `https://example.org/people/john-doe#me`) implies the profile document must be deployed at `https://example.org/people/john-doe`. You therefore need **read-write control over the destination folder** on the server (e.g. a WebDAV/LDP directory) to publish the generated files. No placeholder document is required — the skill creates everything from scratch.

After generation, use T5 to upload, or copy the files manually to the destination server. The produced files are suitable for hosting on any static file server, provided the profile document is served with `Content-Type: text/turtle` or `application/ld+json`.

---

## T1 — Generate a Full WebID Profile (NetID)

Collects identity parameters, generates a self-signed X.509 certificate with a WebID SAN, fills all profile templates, and produces an identity card HTML page with a dark/light toggle and social profile cross-references.

```
Generate a WebID profile for John Doe
WebID: https://example.org/people/john-doe#me
Email: john@example.org
Organization: Example Corp
Country: US
State: California
Photo: https://example.org/photos/john.jpg
Social profiles: LinkedIn (https://linkedin.com/in/johndoe), GitHub (https://github.com/johndoe), Mastodon (https://mastodon.social/@johndoe)
Certificate validity: 2 years
Style: premium
```

```
Create a YouID identity card for Jane Smith
WebID: https://id.example.com/jane#me
Email: jane@example.com
Title: Software Engineer
Social: https://x.com/janesmith, https://bsky.app/profile/janesmith.bsky.social, https://substack.com/@janesmith
Style: dark
```

## T2 — Generate Full NetID with OPAL Agent

Same as T1 but includes configuration for the OPAL AI chat widget embedded in the identity card.

```
Create a NetID identity card with OPAL agent for Alice Brown
WebID: https://mydata.example/alice#me
Email: alice@example.org
Agent config: data-twingler-config
Model: gemini-2.5-pro
Temperature: 0.2
Predefined prompts:
  "Who are you?"
  "What certificates do you have?"
  "Verify my identity"
```

## T3 — Generate X.509 Certificate Only

Produces just the certificate bundle (`.pem`, `.crt`, `.p12`) with a WebID SAN, without profile documents.

```
Generate an X.509 certificate for https://example.org/people/bob#me
Name: Bob Smith
Email: bob@example.org
Organization: ACME Inc
Country: US
Valid for: 3 years
```

## T4 — Verify a WebID Profile

Fetches a remote WebID profile, extracts the public key, and verifies consistency between the certificate and profile documents.

```
Verify WebID https://example.org/people/john-doe#me
```

```
Check identity at https://kingsley.idehen.net/DAV/home/kidehen/Public/YouID/link-in-bio-credentials-5/index.html
```

## T5 — Upload Identity Documents

Uploads generated credential files to a WebDAV/LDP storage backend.

```
Upload identity documents to https://kingsley.idehen.net/DAV/home/kidehen/Public/YouID/my-credentials/
```

## T6 — Delegate Identity (On-Behalf-Of)

Adds `oplcert:hasIdentityDelegate` to the delegator's profile files and `oplcert:onBehalfOf` to the delegate's files, plus a browser extension rule.

```
Delegate identity from https://example.org/alice#me to https://example.org/bob-agent#me
Role: authority
Delegator directory: ./youid-output/alice-credentials/
Delegate directory: ./youid-output/bob-agent-credentials/
```

## T7 — Explain Identity Concepts

```
What is a WebID?
Explain DPKI
What is the difference between WebID-TLS and WebID-OIDC?
Define NetID
```

## Post-Generation — Add Social Profiles

Updates generated credential files with social media cross-references (`owl:sameAs`, `schema:sameAs`, `<link rel="me">`, and platform icons in the social grid).

```
Add social profiles to the credentials in ./youid-output/my-creds/
LinkedIn: https://linkedin.com/in/johndoe
GitHub: https://github.com/johndoe
Bluesky: https://bsky.app/profile/johndoe.bsky.social
```

## Post-Generation — Toggle Dark/Light Mode

Adds a manual theme toggle button (sun/moon SVG icons with `localStorage` persistence) to an existing identity card.

```
Add a dark/light toggle to the identity card at ./youid-output/my-creds/index.html
```
