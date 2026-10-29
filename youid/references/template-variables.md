# YouID Template Variable Reference

All templates in `templates/` use the YouID template syntax:

- `%{key}` — Simple substitution, replaced with the value of `key` (always filled, error if empty)
- `!{key}` — Conditional line: the entire line is included only if `key` is set to a non-empty value
- `!!{key}` — Conditional block start: text from this line to the matching `!!.` is included only if `key` is set
- `!!.` — Conditional block end
- `!!{key}` at line start (no `%`/`!`) — Same as `!{key}`, a conditional line prefix

## Identity Variables

| Variable | Example | Source | Required |
|----------|---------|--------|----------|
| `subj_name` | `Jane Doe` | Certificate common name (CN) | Yes |
| `subj_email` | `jane@example.org` | Certificate email address | No |
| `subj_org` | `Acme Corp` | Certificate organization (O) | No |
| `subj_country` | `US` | Certificate country (C), 2-letter ISO | No |
| `subj_state` | `California` | Certificate state (ST) | No |
| `subj_summary` | `A short biography or summary about the subject.` | Free-text bio/summary (used by dark template bio section) | No (provided via extra data JSON `-f`) |
| `subj_email_mailto` | `mailto:jane@example.org` | Derived from email | If email set |
| `subj_email_mailto_href` | `<a href="mailto:jane@example.org">jane@example.org</a>` | HTML mailto link | If email set |
| `photo_url` | `photo_130x145.jpg` | Photo filename or URL | No |
| `webid` | `https://example.org/people/jane#me` | User's WebID URI | Yes |

## Certificate Variables

| Variable | Example | Description |
|----------|---------|-------------|
| `modulus` | `00A3B2C1...` | RSA public key modulus, hex-encoded |
| `exponent` | `65537` | RSA public key exponent |
| `subject` | `/CN=Jane Doe/O=Acme/C=US` | X.509 subject Distinguished Name |
| `issuer` | `/CN=Jane Doe/O=Acme/C=US` | X.509 issuer DN (self-signed = same as subject) |
| `date_before` | `2026-06-09T00:00:00Z` | Certificate notBefore (ISO 8601) |
| `date_after` | `2036-06-06T00:00:00Z` | Certificate notAfter (ISO 8601) |
| `serial` | `01A2B3...` | Certificate serial number (hex) |
| `fingerprint_hex` | `A1B2C3D4...` | SHA-1 fingerprint of DER (hex) |
| `fingerprint_256_hex` | `E5F6A7B8...` | SHA-256 fingerprint of DER (hex) |
| `fingerprint_ni` | `ni:///sha-256;...` | Named Information URI (NI) |
| `fingerprint_di` | `urn:di:sha-256;...` | Digest Identifier URI (DI) |
| `fingerprint_colon` | `A1:B2:C3:D4...` | Fingerprint with colon separators |
| `vcard_digest_uri` | `data:text/plain;sha-256;...` | vCard digest URI |

## URL Variables (Derived from Base URL + Filenames)

All URL variables are derived from a user-provided base URL (the directory where files will be hosted). The base URL MUST end with `/`.

| Variable | Default (relative to base URL) | Description |
|----------|-------------------------------|-------------|
| `prof_url` | `{base}profile.ttl` | Turtle profile URL |
| `pubkey_url` | `{base}public_key.ttl` | Public key Turtle URL |
| `cert_url` | `{base}certificate.ttl` | Certificate Turtle URL |
| `card_url` | `{base}index.html` | Identity card HTML URL |
| `card_ident_url` | `{card_url}#netid` | Card identity fragment IRI |
| `jsonld_prof_url` | `{base}profile.jsonld` | JSON-LD profile URL |
| `jsonld_cert_url` | `{base}certificate.jsonld` | JSON-LD cert URL |
| `jsonld_pubkey_url` | `{base}public_key.jsonld` | JSON-LD pubkey URL |
| `rdfa_prof_url` | `{base}profile_rdfa.html` | RDFa profile URL |
| `rdfa_cert_url` | `{base}certificate.rdfa.html` | RDFa cert URL |
| `rdfa_pubkey_url` | `{base}public_key.rdfa.html` | RDFa pubkey URL |
| `vcard_url` | `{base}vcard.vcf` | vCard URL |
| `pubkey_pem_url` | `{base}cert.pem` | PEM certificate URL |
| `pubkey_der_url` | `{base}cert.crt` | DER certificate URL |

## Conditional Flags (Enable/Disable Template Sections)

| Flag | Set to | Effect |
|------|--------|--------|
| `pdp_url` | URL string | Include personal profile page links/owl:sameAs |
| `pdp_mail` | email string | Include foaf:Agent declarations with foaf:mbox |
| `ca_cert_url` | URL string | Include CA certificate alternate links |
| `pim_storage` | URL string | Include pim:storage link |
| `use_opal_widget` | `1` | Enable OPAL widget section in identity card |
| `use_opalx` | `1` | Use OPALX mode (enhanced, with file uploads) |
| `use_opal` | `1` | Use basic OPAL mode |
| `use_oauth` | `1` | Use OIDC/OAuth authentication for OPAL |
| `use_bearer` | `1` | Use bearer token authentication for OPAL |
| `em_indie_idp` | URL string | Include IndieAuth authorization/token endpoints |
| `em_microdata` | `1` | Embed microdata in identity card HTML |
| `em_ttl` | `1` | Embed Turtle in `<script type="text/turtle">` |
| `em_jsonld` | `1` | Embed JSON-LD in `<script type="application/ld+json">` |

## Social Relation Variables

| Variable | Format | Description |
|----------|--------|-------------|
| `relList` | `<url> ,\n\t<url> ,` | Turtle owl:sameAs/schema:sameAs relation list |
| `relList_json` | `{"@id":"url"},\n` | JSON-LD owl:sameAs array entries |
| `relList_rdfa` | `<div rel="owl:sameAs"...>` HTML | RDFa sameAs markup |
| `relList_rdf` | `<owl:sameAs rdf:resource="url"/>` | RDF/XML sameAs |
| `relList_html` | `<a href="url"><img src="icon.png" ...></a>` | HTML social icon links |
| `rel_header_html` | `<link rel="me" href="url" />` | HTML `<head>` relation links |
| `relList_rdfa_schema` | `<div rel="schema:sameAs"...>` | RDFa schema:sameAs markup |
| `relList_rdf_schema` | `<schema:sameAs rdf:resource="url"/>` | RDF/XML schema:sameAs |
| `relList_micro` | `<link itemprop="owl:sameAs"...>` | Microdata sameAs |
| `relList_micro_schema` | `<link itemprop="schema:sameAs"...>` | Microdata schema:sameAs |

## did:nostr Variables (set by `generate_identity.sh -N <id> -R same|agent`)

| Variable | Example | Description |
|----------|---------|-------------|
| `nostr_did` | `did:nostr:124c0f…fdd2` | Conditional-block flag + DID IRI (enables the Multikey block and the card section) |
| `nostr_npub` | `npub1zfxql2…` | NIP-19 display form; `schema:identifier` of the DID; vCard `nostr:` URI |
| `nostr_hex` | `124c0f…fdd2` | Canonical 64-hex x-only public key |
| `nostr_multibase` | `fe70102124c0f…` | `sec:publicKeyMultibase` value |
| `nostr_same` | `1` | Mode `same` → `<webid> owl:sameAs <nostr_did>` lines |
| `nostr_agent` | `1` | Mode `agent` → `<webid> oplcert:hasIdentityDelegate <nostr_did>` lines |
| `nostr_relation_label` | `Same agent as this WebID (owl:sameAs)` | Human label on the card |

## OPAL Widget Variables

| Variable | Example | Description |
|----------|---------|-------------|
| `w_opl_endpoint` | `https://linkeddata.uriburner.com` | OPAL backend endpoint URL |
| `w_opl_api_key` | `sk-...` | Bearer API key (if bearer auth) |
| `w_mode` | `w_opal` or `w_opalx` | Widget mode selector |
| `w_model` | `gpt-4o` | OpenAI-compatible model name |
| `w_funcs` | `'func1','func2'` | OPAL backend functions |
| `w_top_p` | `1.0` | Nucleus sampling parameter |
| `w_temperature` | `0.7` | Temperature parameter |
| `w_assistant` | `asst_xxx` | Assistant ID (OPALX) |
| `w_module` | `data-twingler-config` | OPAL session module |
| `w_prompt1` | `Explore this knowledge graph` | Predefined prompt 1 |
| `w_prompt2` | `Define the term...` | Predefined prompt 2 |
| `w_prompt3` | `How to...` | Predefined prompt 3 |
| `w_prompt4` | `What is...` | Predefined prompt 4 |
