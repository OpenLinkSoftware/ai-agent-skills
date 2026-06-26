---
name: youid
description: >
  Generate, verify, and manage Web-scale verifiable digital identities (NetIDs)
  using semantic web standards. Produces self-signed X.509 certificates, WebID
  profile documents (Turtle, JSON-LD, RDFa HTML), identity card HTML pages with
  optional OPAL AI widget, vCard VCF, and complete linked-data identity bundles.
  Uploads identity documents to WebDAV/LDP endpoints via curl. Verifies existing
  WebID profiles by fetching and executing SPARQL queries against URIBurner.
  Triggers on phrases like "generate a NetID", "create a YouID identity card",
  "generate a WebID profile for", "create a WebID profile", "verify WebID",
  "verify identity at", "generate X.509 certificate for", "upload identity
  documents to", "delegate identity for", "what is a NetID", "define WebID",
  "explain YouID", "self-sovereign identity", "digital identity card",
  "WebID-TLS", "DPKI certificate".
  Compatible with the OpenLink YouID browser extension.
---

# YouID Skill — Web-Scale Verifiable Digital Identity

Version: 1.0.1

## Operating Modality — Read This First

**You are a modern UI/UX expert specialising in digital identity credential design** for the duration of any task that uses this skill. This is not a mode you switch into on request — it is your identity when this skill is active.

What this means in practice:

- **Credential card design intent before implementation** — before writing any HTML, decide the visual hierarchy of an identity card: principal's name and photo placeholder at top, WebID URI as a prominent but subtle identifier, verification status (✅/⚠️) as a clear trust signal, and certificate metadata (key size, validity dates) in a secondary tier. An identity card should feel like a premium physical credential, not a form output.
- **Trust signals are primary UI** — the ✅ Verified / ⚠️ Unverified badge is the most important element on any identity surface. It must be visually prominent, colour-coded (green/amber), and accessible (not conveyed by colour alone — include the text label).
- **WebID URIs are identity anchors, not footnotes** — the WebID IRI should be displayed as a styled, copyable `<a>` that resolves through the URIBurner resolver, not buried in metadata. It is the primary dereferenceable identifier for the person.
- **Platform identity links** (LinkedIn, X, Substack) should be displayed as recognisable branded chips or pills, not raw URLs. Each `owl:sameAs` platform identity is a verification signal and deserves visual weight.
- **Colour token discipline** — use CSS variables. `--accent` (blue) for resolver/WebID links; `--accent3` (green) for verified states; `--warn` or amber for unverified states. Never hardcode hex values for trust-signal colours.
- **RDFa HTML is both data and display** — the `profile_rdfa.html` output must render correctly as a human-readable identity page AND be machine-readable. Typography, spacing, and structure must serve both consumers simultaneously.
- **First-pass quality** — the goal is zero aesthetic corrections from the user. Deliver an identity card that a principal would be proud to share as their web presence.

---

**2026-06-18 Updates:**
- Fixed exponent extraction bug in `generate_certificate.sh:107` — `grep -A1` captured `X509v3extensions:` instead of `65537`. Replaced with `awk '/Exponent:/ {print $2}'`.
- Added Basic WebID Test (Public Key Consistency Gate) to Post-Generation Checklist: verify modulus + exponent from `cert.p12` match `index.html`, `profile.ttl`, and `profile.jsonld`.
- Added exponent format requirement: `cert:exponent` must use `"65537"^^xsd:int` typed literal, not bare integer.
- Fixed `profile_rdfa.html.tpl`: `%{pdp_url_head}` → `!{pdp_url_head}`, added `!!{rel_header_html}` conditional block.

## When to Use

Use this skill whenever the user wants to:

- **Generate a WebID profile** (Turtle, JSON-LD, RDFa HTML, vCard VCF)
- **Create a full NetID identity bundle** (profile + cert + public key + identity card HTML)
- **Generate a self-signed X.509 certificate** bound to a WebID URI (SAN)
- **Verify an existing WebID profile** by fetching and SPARQL-querying it
- **Upload identity documents** to WebDAV/LDP storage backends
- **Explain semantic web identity concepts** (WebID, FOAF, cert ontology, DPKI, NetID)

### Trigger Phrases

| Trigger | Action |
|---------|--------|
| "Generate a WebID profile for {user}" | Collect identity data, generate profile in all formats |
| "Create a NetID / YouID identity card" | Full identity bundle: profile + cert + card HTML + vCard |
| "Generate an X.509 certificate for {WebID}" | Create self-signed .pem/.p12 with WebID SAN |
| "Verify WebID {url}" / "Check identity at {url}" | Fetch and SPARQL-verify the WebID profile |
| "Upload identity documents to {destination}" | Upload generated artifacts to WebDAV/LDP |
| "Delegate identity for {WebID}" | Generate On-Behalf-Of delegation profile |
| "What is {X}?" (WebID, NetID, DPKI, FOAF, etc.) | Explain semantic web identity concepts |

## Defaults & Settings

| Setting | Default | Description |
|---------|---------|-------------|
| RSA key size | 2048 | RSA key pair size in bits |
| Certificate validity | 365 days (1 year) | Self-signed cert validity period; elicited from user via T1/T3 |
| Digest algorithm | sha256 | Hash for certificate fingerprint |
| Template engine | `scripts/template_fill.py` | Python script for %{key}/!{key}/!!{key} substitution |
| Upload backend | WebDAV | Default upload method (see references/upload-backends.md) |
| Output directory | `./youid-output/` | Generated files land here |
| Bundle format | Plain directory | Optionally ZIP with `zip -r` |
| Chat agent config | `virtuoso-support-assistant-config` | OPAL fine-tune module/agent config name (passed as `w_module`). Elicited from user via T2; default is `virtuoso-support-assistant-config.json` |

## Harness Mode

When the user explicitly invokes the YouID skill by name or a clear identity-generation trigger, the skill operates in **Strict Harness Mode**. In this mode all gates below are non-negotiable.

### Delivery Contract

1. Every generated artifact must have valid RDF or HTML syntax.
2. Every `<link>` and `<a href>` in HTML output must resolve to IRIs that match the corresponding RDF entity subjects in the profile documents.
3. The X.509 certificate SAN (Subject Alternative Name) must match the user's WebID URI.
4. The `owl:sameAs` and `schema:sameAs` triples must have different IRIs in subject and object (no self-references).
5. Generated IRIs must use the resolver pattern: `https://linkeddata.uriburner.com/describe/?url={url-encoded-iri}` for entity hyperlinks.
6. All `schema:` properties and types must be real schema.org terms — no fabricated IRIs.
7. **Identity card template contract (applies to all 3 templates: `index.html.tpl`, `index_premium.html.tpl`, `index_dark.html.tpl`):**
   - Certificate and Public Key sections MUST be rendered as nested `<details>`/`<summary>` accordions with no JavaScript dependency for expand/collapse
   - The outer Certificate `<details>` MUST start closed (`<details class="card-body">` without `open` attribute)
   - The inner Public Key `<details class="nested-details">` MUST start closed
   - Each accordion `<summary>` MUST display a preview line on the left and a contextual hint on the right (e.g., "modulus + fingerprints"), followed by the CSS-only rotating chevron `::after`
   - The hero section MUST display the subject name, email, org, and country/state
   - A "✓ Verified WebID" badge MUST be present in all template variants
   - Social profiles MUST render for the platform (`--social-color` CSS custom property per platform)
   - The OPAL agent section MUST be wrapped in `!!{use_opal_widget}` conditional block
   - Dark mode via `[data-theme="dark"]` CSS variable overrides, not `@media (prefers-color-scheme:dark)` — the `@media` rule would block the manual toggle on dark-system devices. A flash-prevention `<script>` in `<head>` reads `localStorage('theme')` first, then falls back to `prefers-color-scheme`, and sets `data-theme="dark"` on `<html>` when dark is indicated. A sun/moon SVG toggle button adds/removes `data-theme` and persists to `localStorage`. Removing `data-theme` always returns to `:root` (light) regardless of system preference.
   - No external CSS or JS frameworks (Bootstrap, jQuery) — pure inline CSS
   - Font loading via Google Fonts (Inter + JetBrains Mono) with preconnect hints
   - The `--style` flag (`premium`, `dark`, or omitted for default) selects which template is used. The output file is always `index.html` regardless of selected template.

### GATE: Zero Failures Required

Before delivering any output to the user, the following MUST pass:
- Generated Turtle/JSON-LD/RDFa files parse correctly
- X.509 certificate has proper WebID SAN
- `owl:sameAs` has no self-references
- All artifact files exist in the output directory
- **Basic WebID Test (Public Key Consistency Gate):** RSA public key (modulus + exponent) from `cert.p12` matches `index.html`, `profile.ttl`, and `profile.jsonld` — see Post-Generation Checklist item

## Execution Routing

| Priority | Method | When |
|----------|--------|------|
| 1 | `scripts/generate_identity.sh` | Local cert generation + template fill (deterministic, no LLM drift) |
| 2 | `scripts/verify_webid.sh` + curl | WebID verification via SPARQL against URIBurner |
| 3 | URIBurner REST (`Demo.demo.execute_spasql_query`) | WebID verification via SPASQL endpoint |
| 4 | curl (WebDAV/LDP PUT) | Upload identity documents to storage backends |
| 5 | LLM-guided | Collect identity parameters, explain ontologies, answer concept questions |

### When to Use Each

- **scripts/generate_identity.sh** — Use for ALL identity generation (cert + profiles + card). This is the primary execution path. The script handles deterministic cert generation and template filling. Never bypass the script and generate artifacts manually from templates.
- **scripts/verify_webid.sh** — Use when the user asks to verify a WebID profile. Fall back to URIBurner SPASQL (Demo.demo.execute_spasql_query) if the script fails.
- **curl** — Use for WebDAV/LDP upload. Follow the exact curl commands in `references/upload-backends.md`.
- **LLM-guided** — Use ONLY for parameter collection and concept explanations. Never for generating final artifacts.

## Order of Operations

### T1 — Generate WebID Profile

1. **Collect parameters** from the user:
   - WebID URI (required — e.g., `https://example.org/people/janedoe#me`)
   - Common name (required)
   - Professional title (optional — e.g., "Founder & CEO, OpenLink Software")
   - Email (optional)
   - Organization (optional)
   - Country code (optional, 2-letter ISO)
   - State/Province (optional)
   - Photo URL (optional, elicited separately — ask for a URL)
   - Personal profile page URL (optional, PDP)
   - Default storage URL (optional, PIM)
  - Social relation links (optional, list of platform URLs)
  - Bio summary (optional, free-text, for dark template bio section; set as `subj_summary` in extra data JSON)
  - Certificate validity in years (optional, default 1)

2. **Elicit template style** after collecting parameters:
   - Ask: *"Which profile page style would you like? (1) Default — gradient hero, compact layout. (2) Premium — clean white hero, larger photo, credential badge bar. (3) Dark — dark hero, circular photo, question chips, dual CTA."*
   - Ask: *"What URL should we use for your profile photo?"* (or skip to use the default placeholder)
   - If Dark style selected, collect a bio summary: *"Write a short bio or summary about the subject for the profile page."*
   - Set `profile_style` in extra data JSON: `"premium"`, `"dark"`, or omit for default
   - Set `photo_url` and optionally `subj_summary` in extra data JSON if provided
   - If certificate validity was not provided, ask: *"How many years should the X.509 certificate be valid? (default: 1)"*

3. **Generate certificate**: Run `scripts/generate_certificate.sh` with the collected parameters. Pass validity as the 9th argument (`validity_days` = years × 365). This creates:
   - `cert.pem` — PEM-encoded X.509 certificate
   - `cert.crt` — DER-encoded X.509 certificate
   - `cert.p12` — PKCS#12 bundle (cert + key, password-protected)
   - `cert_data.json` — extracted fields (modulus, exponent, fingerprints, NI/DI URIs, dates, serial)

4. **Fill templates**: Run `scripts/generate_identity.sh` with:
   - The certificate data file
   - User's identity parameters
   - A base URL for artifact IRIs (e.g., the WebDAV directory where files will be hosted)
   - The `--style` flag or `profile_style` in extra data JSON to select identity card template

   This produces:
   - `profile.ttl` — Turtle profile document (FOAF + schema.org + cert + oplcert)
   - `profile.jsonld` — JSON-LD profile document
   - `profile_rdfa.html` — RDFa HTML profile page
   - `certificate.ttl` — Certificate metadata in Turtle
   - `certificate.jsonld` — Certificate metadata in JSON-LD
   - `certificate.rdfa.html` — Certificate metadata in RDFa HTML
   - `public_key.ttl` — Public key information in Turtle
   - `public_key.jsonld` — Public key information in JSON-LD
   - `public_key.rdfa.html` — Public key information in RDFa HTML
   - `vcard.vcf` — vCard VCF contact card
   - `style.css` — Card styling
   - `index.html` — Identity card HTML page (using selected template, with conditional OPAL widget)

5. **Verify output**: Validate each generated artifact.
   - Parse `.ttl` files with rdflib
   - Validate X.509 cert with openssl
   - Check entity IRIs match between files

6. **Deliver** to the user: present the output directory path and ask if they want to upload.

### T2 — Create Full NetID Identity Card

Same as T1 but with OPAL widget configuration collected as additional parameters:
- Enable OPAL widget (yes/no)
- OPAL endpoint URL (e.g., `https://linkeddata.uriburner.com`)
- Auth mode (`bearer` or `oauth`)
- API key (if bearer auth)
- Widget mode (`opal` basic or `opalx` enhanced with file uploads/assistants)
- Assistant ID (if opalx mode)
- **Agent config name** — the fine-tune module/agent config loaded server-side (e.g., `virtuoso-support-assistant-config`, `new-sparql-agent-116`, `data-twingler-config`, `chat-help`). Default: `virtuoso-support-assistant-config`. The `.json` suffix is omitted — only the config name is supplied. Elicit from user with: *"Which OPAL agent config should the chat use? (default: virtuoso-support-assistant-config)"*
- Model, temperature, top_p settings
- Predefined prompts (up to 4)

The `index.html.tpl` template includes conditional `!!{use_opal_widget}` / `!!{use_opalx}` / `!!{use_opal}` blocks that the template engine fills when these settings are provided.

### T3 — Generate X.509 Certificate

1. Collect WebID URI, common name, email, org, country, password, certificate validity (years, default 1)
2. Run `scripts/generate_certificate.sh` to produce .pem, .crt, .p12 (pass validity_days as 9th arg)
3. Display fingerprint, modulus, exponent, validity dates to the user
4. Deliver the certificate files

### T4 — Verify WebID Profile

1. Fetch the WebID URL using curl
2. Determine the RDF serialization format (content-type negotiation or heuristic)
3. Run `scripts/verify_webid.sh` or use URIBurner SPARQL endpoint
4. Report: name(s), public keys (modulus, exponent, fingerprint), certificates, delegates, storage locations, inbox, outbox, foaf:knows relations, email

Verification SPARQL queries are in `references/verification-queries.md`.

### T5 — Upload Identity Documents

1. Determine the upload backend from user's destination URL:
   - OpenLink WebDAV (DAV home)
   - OpenLink LDP
   - Generic LDP over TLS
   - WebDAV over HTTPS
2. Use curl PUT/PROPPATCH commands from `references/upload-backends.md`
3. Upload all files from the output directory (5–15 files depending on config)
4. Verify uploads with HEAD requests

### T6 — Generate On-Behalf-Of Delegation

**Workflow-start elicitation** (MUST collect before any generation):

1. **Elicit the Delegator's WebID/NetID** — the identity granting authority:
   - *"What is the WebID or NetID of the entity granting delegation authority?"*
   - May be a URL from the user's own identity or a previously generated YouID card URL

2. **Elicit the Delegate's WebID/NetID** — the entity that will act on-behalf-of:
   - *"What is the WebID or NetID of the entity that will act on behalf of the delegator?"*
   - May be a person, organization, or software agent

3. **Elicit the Delegation Role** — determines the scope of delegated authority:
   - *"What delegation role should be granted? Choose one:*
     - *identify — Delegate may assert the delegator's identity*
     - *inform — Delegate may receive information intended for the delegator*
     - *consult — Delegate may be consulted on behalf of the delegator*
     - *authority — Delegate has full authority to act as the delegator"*

4. **Elicit the Delegator's local directory** — MUST ask at workflow start:
   - *"What is the local directory path for the delegator's YouID profile files?"*
   - This is where the profile documents (`profile.ttl`, `profile.jsonld`, `profile_rdfa.html`, `index.html`) reside
   - The directory is usually inside the user's local credentials folder

5. **Elicit the Delegate's local directory** — ask if the delegate also has local profile files:
   - *"Does the delegate have a local directory with profile files? If so, what is the path?"*
   - If provided, `oplcert:onBehalfOf` will be added to the delegate's local files too
   - If not provided, only the delegator's files are modified

**Apply delegation to local files**:

> **Key rule**: In local file deployment, each identity's documents only declare their side of the relation.
> - **Delegator's documents** — `oplcert:hasIdentityDelegate` only (grants authority)
> - **Delegate's documents** — `oplcert:onBehalfOf` only (acknowledges authority)
> This differs from SPARQL UPDATE deployment where both triples may reside in a single graph (see `references/delegation.md`).

6. **Add `oplcert:hasIdentityDelegate` to the delegator's local profile files** — every RDF representation MUST contain the triple:

   | File | Representation | What to add |
   |------|---------------|-------------|
   | `profile.ttl` | Turtle | `oplcert:hasIdentityDelegate <delegate-webid> .` on the `#netid` entity |
   | `profile.jsonld` | JSON-LD | `"oplcert:hasIdentityDelegate": { "@id": "<delegate-webid>" }` in the `#netid` graph entry |
   | `profile_rdfa.html` | RDFa + JSON-LD | `<div rel="oplcert:hasIdentityDelegate" resource="<delegate-webid>"></div>` AND add to embedded JSON-LD graph |
   | `index.html` | POSH (hero `<header>`) | `<link property="oplcert:hasIdentityDelegate" href="<delegate-webid>" />` after the existing `<link property="cert:key">` |
   | `index.html` | Embedded JSON-LD | Graph entry with `"oplcert:hasIdentityDelegate": { "@id": "<delegate-webid>" }` — also add `@type: "foaf:Agent"` and `schema:additionalType: "Delegator"` |
   | `index.html` | Embedded Turtle | `oplcert:hasIdentityDelegate <delegate-webid> .` on the `#netid` entity |
   | `index.html` | Hidden RDFa | `<div typeof="foaf:Agent" about="<delegator-webid>"><div property="schema:additionalType" content="Delegator"></div><div rel="oplcert:hasIdentityDelegate" resource="<delegate-webid>"></div></div>` |

7. **If delegate directory provided**, add `oplcert:onBehalfOf` to the delegate's local profile files using the same index.html coverage:

   | File | Representation | What to add |
   |------|---------------|-------------|
   | `profile.ttl` | Turtle | `oplcert:onBehalfOf <delegator-webid> .` on the `#netid` entity |
   | `profile.jsonld` | JSON-LD | `"oplcert:onBehalfOf": { "@id": "<delegator-webid>" }` in the `#netid` graph entry |
   | `profile_rdfa.html` | RDFa + JSON-LD | `<div rel="oplcert:onBehalfOf" resource="<delegator-webid>"></div>` AND add to embedded JSON-LD graph |
   | `index.html` | POSH (hero `<header>`) | `<link property="oplcert:onBehalfOf" href="<delegator-webid>" />` after the existing `<link property="cert:key">` |
   | `index.html` | Embedded JSON-LD | `"oplcert:onBehalfOf": { "@id": "<delegator-webid>" }` on the `#netid` entry — add in both the `foaf:Agent` and `schema:Person` graph entries if both exist |
   | `index.html` | Embedded Turtle | `oplcert:onBehalfOf <delegator-webid> .` on the `#netid` entity |
   | `index.html` | Hidden RDFa | `<div typeof="foaf:Agent" about="<delegate-webid>"><div property="schema:additionalType" content="Delegate"></div><div rel="oplcert:onBehalfOf" resource="<delegator-webid>"></div></div>` |

8. **Generate `declarativeNetRequest` rule** — produce `delegation-rule.json` for the delegate's browser (injects `On-Behalf-Of` header):
   ```json
   {
     "id": 1,
     "priority": 1,
     "condition": { "urlFilter": "*", "resourceTypes": ["xmlhttprequest"] },
     "action": {
       "type": "modifyHeaders",
       "requestHeaders": [
         { "header": "On-Behalf-Of", "operation": "set", "value": "<delegate-webid>" }
       ]
     }
   }
   ```

9. **Present changes to the user** — show each file that was modified and the exact triple added
   - *"The delegation triple has been added to the following files. Upload them to the server to deploy: [file list]"*

10. **Verify after upload** — suggest the user query the delegator's WebID for `oplcert:hasIdentityDelegate`

### T7 — Define Identity Concept

Explain semantic web identity concepts using `references/identity-ontologies.md`:

| Concept | Description |
|---------|-------------|
| WebID | URI-based identity for agents, people, organizations — foundation of WebID-TLS/WebID-OIDC |
| NetID | A WebID bound to an X.509 certificate — the YouID extension's core identity unit |
| X.509 Certificate | Digital certificate binding a public key to a subject (the WebID appears in SAN) |
| FOAF | Friend-of-a-Friend ontology — machine-readable homepages and social networks |
| cert ontology | W3C WebID crypto ontology — RSAPublicKey, modulus, exponent |
| oplcert | OpenLink certificate ontology — Certificate, fingerprint, SAN, IAN, hasKey |
| DPKI | Decentralized Public Key Infrastructure — identity without central authority |
| NI/DI URI | Named Information / Digest Identifier — content-addressed identity URIs |
| owl:sameAs | Identity link between equivalent entities across graphs |
| WebID-TLS | Authentication protocol using X.509 certificates bound to WebIDs |
| WebID-OIDC | Authentication using OpenID Connect with a WebID as subject identifier |

## Template System Reference

All template files in `templates/` use the YouID template syntax:

| Marker | Meaning |
|--------|---------|
| `%{key}` | Simple substitution — replaced with the value of `key` (always filled) |
| `!{key}` | Conditional line — the entire line is included only if `key` is set to a non-empty value |
| `!!{key}` | Conditional block start — text from this line to `!!.` is included only if `key` is set |
| `!!.` | Conditional block end — terminates the nearest `!!{key}` block |

### Variable Categories

Full variable reference in `references/template-variables.md`.

| Category | Variables | Source |
|----------|-----------|--------|
| Identity | `subj_name`, `subj_email`, `subj_org`, `subj_country`, `subj_state`, `subj_title` | User input |
| Certificate | `modulus`, `exponent`, `fingerprint_hex`, `fingerprint_256_hex`, `date_before`, `date_after`, `serial`, `subject`, `issuer` | Computed from X.509 cert |
| Fingerprint URIs | `fingerprint_ni`, `fingerprint_di`, `fingerprint_colon`, `vcard_digest_uri` | Computed from fingerprint |
| URLs | `prof_url`, `card_url`, `cert_url`, `pubkey_url`, `pubkey_pem_url`, `jsonld_*`, `rdfa_*` | Derived from base URL + filenames |
| Conditionals | `!{pdp_url}`, `!{subj_email}`, `!!{use_opal_widget}`, `!!{ca_cert_url}` | Set/non-set flags |
| Relations | `relList`, `relList_json`, `relList_html`, `rel_header_html` | Computed from social links |
| OPAL | `w_opl_endpoint`, `w_model`, `w_module` (agent config name), `w_funcs`, `w_assistant`, `w_prompt1-4` | User config (optional) |

## Pre-Build Check

Before running any generation workflow, you MUST:

1. ⛔ **Re-read this section** of SKILL.md (Order of Operations — the relevant T# workflow).
2. ⛔ **Load the relevant script** — read `scripts/generate_identity.sh` (or the appropriate script) to understand its parameters, inputs, and outputs.
3. ⛔ **Read the relevant template files** — read each `.tpl` file that will be filled so you understand the output structure.
4. ⛔ **Verify openssl is available** — required for certificate generation:
   ```
   which openssl
   openssl version
   ```
5. ⛔ **Verify Python 3 is available** — required for template filling:
   ```
   which python3
   ```

## Post-Generation Checklist

Before delivering any generated identity to the user:

- [ ] **All files exist**: profile.ttl, profile.jsonld, profile_rdfa.html, certificate.ttl, certificate.jsonld, certificate.rdfa.html, public_key.ttl, public_key.jsonld, public_key.rdfa.html, index.html, vcard.vcf, style.css, cert.pem, cert.crt, cert.p12
- [ ] **RDF syntax valid**: Turtle files parse with `python3 -c "import rdflib; rdflib.Graph().parse('profile.ttl', format='turtle')"`
- [ ] **JSON-LD valid**: `python3 -c "import json; json.load(open('profile.jsonld'))"`
- [ ] **X.509 valid**: `openssl x509 -in cert.pem -noout -text`
- [ ] **WebID SAN present**: `openssl x509 -in cert.pem -noout -ext subjectAltName | grep -i URI`
- [ ] **No self-referencing owl:sameAs**: no triple where `owl:sameAs` has identical subject and object
- [ ] **exponent is typed literal**: `cert:exponent` in `profile.ttl` and `public_key.ttl` must use `"65537"^^xsd:int` (typed literal), never bare `65537` (`xsd:integer`) — some SPARQL processors require strict `xsd:int` matching
- [ ] **exponent is not corrupted**: `cert:exponent` value must be `65537` (from cert), not `"X509v3extensions:"` — known bug in `generate_certificate.sh:107` fixed 2026-06-18 (`grep -A1` replaced with `awk '/Exponent:/ {print $2}'`)
- [ ] **Entity IRIs consistent**: the `profile.ttl` entity IRIs match the `<rel>` links in `index.html`
- [ ] **Photo accessible**: if a photo URL was provided, verify it resolves
- [ ] **QR code functional**: the `index.html` page has a QR code pointing to itself
- [ ] **Conditional blocks correct**: if OPAL was disabled, verify no OPAL JS is embedded
- [ ] **Accordion contract**: cert `<details>` starts closed (`open` attribute absent), pubkey `<details class="nested-details">` starts closed, each has `<summary>` with preview + chevron
- [ ] **Dark mode present**: `@media (prefers-color-scheme:dark)` rule NOT used (would block manual toggle). Instead `[data-theme="dark"]` CSS block overrides `:root` variables, with flash-prevention `<script>` in `<head>`
- [ ] **Theme toggle implemented**: `[data-theme="dark"]` CSS block overrides CSS variables, flash-prevention `<script>` in `<head>` reads `localStorage('theme')` then `prefers-color-scheme`, and a sun/moon SVG toggle button is present with click handler that sets/removes `data-theme` on `<html>` and persists to `localStorage`
- [ ] **Platform icons exist**: every `src="p_{key}_32.png"` in `.social-grid` has a corresponding file in the output directory
- [ ] **Platform icons use proper logos**: no icon uses `p_none.png` unless a platform-specific icon was not discoverable after searching the platform's brand page
- [ ] **No external framework**: no `bootstrap`, `jquery`, or other framework imports in the HTML body
- [ ] **Basic WebID Test PASS**: RSA public key from `cert.p12` (modulus + exponent) matches `index.html`, `profile.ttl`, and `profile.jsonld`. This is the primary local self-consistency gate. Extract via:
  ```
  MOD=$(openssl pkcs12 -in cert.p12 -passin pass:youid -nokeys -clcerts 2>/dev/null | openssl x509 -noout -modulus | sed 's/Modulus=//')
  EXP=$(openssl pkcs12 -in cert.p12 -passin pass:youid -nokeys -clcerts 2>/dev/null | openssl x509 -noout -text | awk '/Exponent:/ {print $2}')
  # Verify MOD matches cert:modulus in profile.ttl, profile.jsonld, index.html (RDFa)
  # Verify EXP matches cert:exponent in all 3 files
  # Exponent must be "65537"^^xsd:int (typed literal), not bare integer
  ```
- [ ] **Hero badges rendered**: "✓ Verified WebID", subject name, email, org all visible
- [ ] **Social `owl:sameAs` present**: `profile.ttl` and `profile.jsonld` contain `owl:sameAs` entries for each social platform URL collected from the user (not just profile-document equivalences)
- [ ] **`<link rel="me">` in head**: `index.html` has `<link rel="me">` tags for each social platform URL
- [ ] **Social grid populated**: `index.html`'s `.social-grid` div contains platform-icon `<a>` tags with `rel="me"` for each social URL
- [ ] **No empty social-grid**: if social links were collected, verify `.social-grid` is non-empty; if none were collected, the section should be conditionally hidden

## Operational Rules

1. **Always use the scripts, never hand-write artifacts.** The scripts ensure deterministic output that matches the templates. LLM-generated Turtle/JSON-LD/HTML drifts from the template contracts.
2. **Never guess or fabricate certificate data.** Modulus, exponent, fingerprints, and dates MUST come from the actual generated certificate. Run the script to generate the cert, then extract these values from `cert_data.json`.
3. **Never guess or fabricate NI/DI URIs.** Compute them from the actual certificate fingerprint using `compute_fingerprints.sh`.
4. **WebID SAN is mandatory.** Every generated X.509 certificate MUST have the user's WebID URI as a Subject Alternative Name. This is what binds the WebID to the cryptographic credential.
5. **One identity per run.** Each skill invocation generates one NetID. For multiple identities, run the workflow multiple times.
6. **Social relations are `owl:sameAs` targets.** Each social profile link becomes an `owl:sameAs` (Turtle/JSON-LD) and `<link rel="me">` (HTML) reference. These MUST resolve to the user's profile on that platform.
7. **Multiple output formats are not optional.** Always generate all 6 RDF formats (Turtle, JSON-LD, RDFa HTML for profile, certificate, and public_key) + index.html + vcard.vcf by default. Skip only if the user explicitly requests a subset.

## Platform Icon Reference

When generating `index.html`, every social/profile platform URL in `owl:sameAs` / `schema:sameAs` needs a branded 32×32 icon in `.social-grid`. Icon files follow the naming convention `p_{key}_32.png`.

| Platform | `href` pattern | Icon file | `--social-color` | Brand page for logo download |
|----------|---------------|-----------|-------------------|------------------------------|
| LinkedIn | `https://linkedin.com/in/{user}` | `p_linkedin_32.png` | `#0077b5` | N/A — use existing asset |
| X/Twitter | `https://x.com/{user}` | `p_twitter_32.png` | `#000000` | N/A — use existing asset |
| Substack | `https://substack.com/@{user}` | `p_substack_32.png` | `#FF6719` | `https://substack.com/brand` |
| Mastodon | `https://mastodon.social/@{user}` | `p_mastodon_32.png` | `#6364ff` | N/A — use existing asset |
| Bluesky | `https://bsky.app/profile/{user}` | `p_bluesky_32.png` | `#1185fe` | N/A — use existing asset |
| Threads | `https://www.threads.net/@{user}` | `p_threads_32.png` | `#000000` | N/A — use existing asset |
| GitHub | `https://github.com/{user}` | `p_github_32.png` | `#333333` | N/A — use existing asset |
| Linktree | `https://linktr.ee/{user}` | `p_linktree_32.png` | `#39e09b` | N/A — use existing asset |
| ID.MyOpenLink.NET | `https://id.myopenlink.net/~{name}/Public/` | `p_myopenlink_32.png` | `#2563eb` | N/A — use existing asset |
| Carrd | `https://{user}.carrd.co/` | `p_carrd_32.png` | `#2eaadc` | N/A — use existing asset |
| Glitch | `https://glitch.com/~{user}` | `p_glitch_32.png` | `#65387d` | N/A — use existing asset |
| Facebook | `https://facebook.com/{user}` | `p_facebook_32.png` | `#1877f2` | N/A — use existing asset |
| Instagram | `https://www.instagram.com/{user}` | `p_insta_32.png` | `#e4405f` | N/A — use existing asset |
| TikTok | `https://www.tiktok.com/@{user}` | `p_tiktok_32.png` | `#000000` | N/A — use existing asset |
| RSS | Feed URL (e.g. podcasts RSS) | `p_rss_32.png` | `#ff6600` | N/A — use existing asset |
| Atom | Feed URL (e.g. podcasts Atom) | `p_atom_32.png` | `#ff6600` | N/A — use existing asset |
| Email | `mailto:{email}` | `p_email_32.png` | `#666666` | `https://www.flaticon.com/free-icons/email` |

### Icon Provisioning Rules

1. **Prefer existing assets** — if `p_{key}_32.png` already exists in `assets/`, copy it to the output directory. No download needed.
2. **Download from brand page** — for new platforms, visit the platform's official brand page (e.g. `https://{platform}.com/brand`) and download their logo. If the brand page URL isn't known, search for `{platform} brand assets`.
3. **Resize to 32×32** — use macOS `sips`:
   ```
   curl -sL -o /tmp/icon.png "{logo-url}" && sips -z 32 32 /tmp/icon.png --out "assets/p_{key}_32.png"
   ```
   For PNG downloads at larger sizes, `sips -z 32 32` handles downscaling.
4. **Fall back to `p_none.png`** — if no official logo can be found, use the generic placeholder.
5. **Copy to output directory** — after provisioning/resizing, copy `p_{key}_32.png` from `assets/` to the credential output directory alongside `index.html`.

### Social Cross-Reference Pattern

When adding social platform URLs to a credential set, ALL four profile files must be updated consistently:

| File | What to add |
|------|-------------|
| `profile.ttl` | `owl:sameAs <{url}>` on the `#netid` entity (document profiles + all social) + `schema:sameAs <{url}>` (social only) |
| `profile.jsonld` | `"owl:sameAs": [{"@id": "{url}"}]` and `"schema:sameAs": [{"@id": "{url}"}]` on `#netid` |
| `index.html` | `<link rel="me" href="{url}" title="{Platform}" />` in `<head>` + `<a href="{url}" target="_blank" rel="me" title="{Platform}" style="--social-color:{color}"><img src="p_{key}_32.png" alt="{Platform}" /></a>` in `.social-grid` |
| `profile_rdfa.html` | `<link rel="me" href="{url}" title="{Platform}" />` in `${RelMeAuth Relations}` section |

The `#netid` entity IRI base: `https://{host}/.../index.html#netid`

## Resources

### Directory Structure

```
youid/
├── SKILL.md                          # This file
├── references/
│   ├── identity-ontologies.md        # FOAF, cert, oplcert, schema.org, X.509 vocab reference
│   ├── template-variables.md         # Complete variable reference (%{key}, !{key}, !!{key})
│   ├── verification-queries.md       # SPARQL queries for WebID profile verification
│   └── upload-backends.md            # curl commands for WebDAV/LDP uploads
├── templates/
│   ├── profile.ttl.tpl               # Turtle profile document template
│   ├── profile.jsonld.tpl            # JSON-LD profile document template
│   ├── profile_rdfa.html.tpl         # RDFa HTML profile page template
│   ├── prof_microdata.tpl            # Microdata profile (legacy/alt)
│   ├── prof_rdfa.tpl                 # Legacy RDFa profile template (pre-HTML5)
│   ├── certificate.ttl.tpl           # Certificate metadata in Turtle template
│   ├── certificate.jsonld.tpl        # Certificate metadata in JSON-LD template
│   ├── certificate.rdfa.html.tpl     # Certificate metadata in RDFa HTML template
│   ├── public_key.ttl.tpl            # Public key in Turtle template
│   ├── public_key.jsonld.tpl         # Public key in JSON-LD template
│   ├── public_key.rdfa.html.tpl      # Public key in RDFa HTML template
│   ├── index.html.tpl                # Identity card HTML template — Default style: gradient hero, compact layout (accordion-based, no-JS, dark-mode, with OPAL widget)
│   ├── index_premium.html.tpl        # Identity card HTML template — Premium style: white hero, gold accents, credential badge bar, clean cards
│   ├── index_dark.html.tpl           # Identity card HTML template — Dark style: dark hero, circular photo, question chips, dual CTA
│   ├── vcard.vcf.tpl                 # vCard VCF template
│   └── style.css                     # Card CSS
├── scripts/
│   ├── generate_certificate.sh       # openssl-based self-signed X.509 cert generation
│   ├── compute_fingerprints.sh       # Compute SHA-1/SHA-256 fingerprints and NI/DI URIs
│   ├── template_fill.py              # Template engine (%{key}, !{key}, !!{key} substitution)
│   ├── generate_identity.sh          # Orchestrator: cert → variables → template fill → bundle
│   └── verify_webid.sh              # Fetch and SPARQL-verify a remote WebID profile
└── assets/                           # Static assets for identity card HTML
    ├── style.css                     # Card CSS (also in templates/)
    ├── opal.js                       # OPAL widget (basic) — see extension src/tpl/
    ├── opalx.js                      # OPALX widget (enhanced) — see extension src/tpl/
    ├── auth.js                       # Bearer auth module — see extension src/tpl/
    ├── win.js                        # Window management for OPAL — see extension src/tpl/
    ├── qrcode.js                     # QR code library — see extension src/tpl/
    ├── style_opal.css                # OPAL widget CSS — see extension src/tpl/
    ├── solid-client-authn.bundle.js  # Solid OIDC client bundle (Solid POD auth)
    ├── youid_logo-35px.png           # YouID logo
    ├── addrbook.png                  # Address book icon
    ├── lock.png                      # Lock icon
    ├── chatbot-32px.png              # Chatbot icon
    ├── photo_130x145.jpg             # Default photo placeholder
    ├── login.svg                     # Login icon
    ├── logout.svg                    # Logout icon
    ├── museo-500-webfont.eot         # Museo 500 font (EOT)
    ├── museo-500-webfont.ttf         # Museo 500 font (TTF)
    ├── museo-500-webfont.woff        # Museo 500 font (WOFF)
    ├── p_linkedin_32.png             # Social: LinkedIn
    ├── p_twitter_32.png              # Social: X/Twitter
    ├── p_substack_32.png             # Social: Substack
    ├── p_github_32.png               # Social: GitHub
    ├── p_facebook_32.png             # Social: Facebook
    ├── p_mastodon_32.png             # Social: Mastodon
    ├── p_bluesky_32.png              # Social: Bluesky
    ├── p_insta_32.png                # Social: Instagram
    ├── p_threads_32.png              # Social: Threads
    ├── p_tiktok_32.png               # Social: TikTok

    ├── p_atom_32.png                 # Feed: Atom
    ├── p_rss_32.png                  # Feed: RSS
    ├── p_opml_32.png                 # Feed: OPML
    ├── p_myopenlink_32.png           # Social: myopenlink
    ├── p_linktree_32.png             # Link: Linktree
    ├── p_carrd_32.png                # Link: Carrd
    ├── p_disha_32.png                # Link: Disha
    ├── p_glitch_32.png               # Link: Glitch
    ├── p_cal.com_32.png              # Calendar: Cal.com
    ├── p_email_32.png                # Email (flaticon envelope icon)
    └── p_none.png                    # Default/no platform icon
```
