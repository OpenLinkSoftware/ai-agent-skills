---
name: ucp-client
description: Purchase an HTTP-protected resource by discovering an RDF schema:Offer, authenticating an identity (WebID-TLS/mTLS, OAuth Bearer/DPoP, Digest, or headers), mapping the offer to UCP checkout, handing payment to Machine Payments Protocol (MPP) with Stripe support, verifying the receipt, and retrieving the resource. Use when a user supplies a resource URL and wants flexible identity-first ACL handling, UCP checkout, HTTP 402 payment, or an auditable RDF-to-commerce purchase flow.
---

# UCP Client

Use the resource URL as the primary identifier. Keep RDF as the authoritative offer description, UCP as the commerce/checkout protocol, MPP as the HTTP 402 payment protocol, and Stripe as a payment processor. Do not collapse these layers.

## Core workflow

1. Accept a protected `resource_url` and establish the request identity without putting secrets on the command line. For the selected ODS-QA direct-execution profile, use the [`mtls-curl`](/Users/kidehen/Documents/Management/Development/ai-agent-skills/mtls-curl/SKILL.md) skill with a PKCS#12 or PEM client certificate and `curl`. The client also accepts an OAuth access token (Bearer or DPoP), Digest credentials, environment-backed headers, or an already-established ambient identity session. Discover OAuth metadata from the resource origin's [OAuth 2.0 Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414) endpoint when using OAuth; the server OAuth backend is assumed to already exist and is not implemented by this skill.
2. Probe the resource before commerce. Interpret the server response as an identity-first state machine: `401` means authentication is missing or failed and may advertise one or more authentication schemes; `200` means the authenticated identity passes the resource ACL; `402` means the authenticated identity failed the ACL and payment can grant access; `403` is a terminal policy denial without a payable challenge. A `401` may therefore trigger Digest, WebID-TLS/mTLS, or OAuth token acquisition; it is never itself a payment challenge.
3. Accept `402` only when identity was established and the response includes at least one `WWW-Authenticate: Payment` challenge. Parse repeated `WWW-Authenticate` and `Link` fields, preserving Payment challenge parameters, `Payment-Receipt`, `Location`, content type, and links such as `rel=offer`, `describedby`, `alternate`, or `payment`. A naked `402`, or `402` before identity, is a protocol error.
4. Query the merchant RDF knowledge graph for a `schema:Offer` associated with the resource IRI. Accept both Schema.org namespace forms (`http://schema.org/` and `https://schema.org/`). Match direct `schema:itemOffered`, `schema:url`, `schema:contentUrl`, or `schema:identifier` links and item-mediated links such as Offer → License/Product → resource. Use `--resource-predicate IRI` for additional explicit merchant relations. Use `--sparql-endpoint` when known; otherwise try `<merchant-origin>/sparql`; then use response-linked or explicit RDF metadata. Quad stores commonly keep offer data in a named graph outside the SPARQL protocol default graph: an unscoped query that returns no rows is automatically retried once, scanned across all named graphs (`GRAPH ?g { ... }`), before falling back to RDF dereference; pass `--sparql-default-graph IRI` (repeatable) to scope explicitly instead of relying on the automatic scan. If the resource's public/RDF-published IRI differs from the URL actually used to access it (see the ODS-QA case below), pass `--match-url` with the RDF-published IRI so offer matching succeeds independently of the access URL.
5. Extract offer identity, item identity, price, currency, availability, seller, and UCP item identifier. Read price/currency either directly or through `schema:priceSpecification`. Prefer `schema:sku`, then `schema:productID`, then literal `schema:identifier`; known explicit merchant identifiers such as `oplofr:offerNumber` may follow. For another merchant vocabulary use repeatable `--item-id-predicate IRI`, or supply a verified `--item-id VALUE`. Never infer an ID from a URL path. `schema:potentialAction` query parameters remain opt-in via `--allow-action-item-id`.
6. Discover the merchant UCP profile at `/.well-known/ucp` and read the advertised `dev.ucp.shopping` REST checkout capability/version.
7. Create a UCP checkout session using the mapped item ID and quantity. Treat the checkout response as authoritative for final price, totals, eligibility, and status. Before spending money, surface the checkout amount/currency and payment boundary unless the user explicitly authorized the purchase and any required spending limit is satisfied.
8. Fulfill one server-advertised Payment challenge using an MPP implementation such as `mppx`. Preserve identity independently through WebID-TLS/mTLS, an authenticated session cookie, or a server-side challenge binding; Basic/Digest/Bearer/DPoP and Payment cannot both occupy the single `Authorization` field. After entitlement binding, retry the resource with the original identity context and capture `Payment-Receipt` plus the final status.
9. Reconcile the MPP receipt with the UCP checkout only through a merchant-supported binding. Return the resource plus provenance: identity-gate state, resource URL, offer IRI, checkout ID/status, amount/currency, Payment method/intent, receipt, and final HTTP status.

### Response-driven authentication selection

Treat `401 Unauthorized` as an authentication-protocol negotiation point. Inspect every `WWW-Authenticate` challenge and authentication `Link` metadata before choosing a retry. Select Digest when Digest is advertised; select OAuth when Bearer/DPoP or OAuth metadata is advertised; or negotiate WebID-TLS/mTLS at the TLS layer when a certificate listener is available. Do not infer that Digest is the only possible method merely because it is the only challenge in one response. A successful identity retry proceeds to ACL evaluation; only an authenticated ACL miss can become `402 Payment Required`.

When running interactively, stop at the first `401` and prompt the user: “Authentication is required. Choose Digest, OAuth Bearer/DPoP, WebID-TLS/mTLS, or cancel.” Show the advertised schemes and metadata links, explain the required credential or browser step, and wait for the user's choice before retrying. Never silently fall back between protocols. In non-interactive mode, return the choices as `authentication_schemes` and authentication links and stop without guessing.

## RDF offer rules

Prefer Schema.org IRIs (`https://schema.org/`), while accepting the historically equivalent `http://schema.org/` vocabulary in merchant data. A minimal offer should expose:

```turtle
@prefix schema: <https://schema.org/> .

<https://merchant.example/offers/report-123>
    a schema:Offer ;
    schema:itemOffered <https://merchant.example/DAV/report-123.pdf> ;
    schema:sku "report-123" ;
    schema:price "5.00" ;
    schema:priceCurrency "USD" ;
    schema:availability schema:InStock .
```

Treat IRIs as first-class identifiers. Preserve the offer IRI and resource IRI even when UCP requires a compact merchant item ID.

If multiple offers match, rank exact `schema:itemOffered == resource_url` first, then an explicit relation from the offered item, then a direct offer-to-resource relation; prefer offers with explicit price/currency. If ambiguity remains, do not purchase until a single offer is selected.

## UCP rules

Use the UCP profile rather than hard-coded checkout paths. For REST, discover the service endpoint from `/.well-known/ucp` and issue standard checkout operations relative to it. Read `references/protocol-notes.md` for version and payment-boundary cautions.

Use `scripts/ucp_resource_client.py` for deterministic RDF discovery, UCP profile discovery, checkout creation, MPP handoff orchestration, and provenance output.

For the identity-first response contract and secure CLI identity options, read `references/protocol-notes.md` and `references/api_reference.md`.

Typical dry run:

```bash
python scripts/ucp_resource_client.py \
  --resource-url https://merchant.example/DAV/report.pdf \
  --rdf-url https://merchant.example/offers/report.ttl \
  --sparql-endpoint https://merchant.example/sparql \
  --dry-run
```

SPARQL offer discovery is attempted before `--rdf-url`; the endpoint is optional because the default is the merchant origin plus `/sparql`. The result records whether the offer came from SPARQL or RDF dereferencing, including the fallback reason when applicable. UCP discovery accepts both list-based profiles (`transport: rest`) and current nested profiles (`dev.ucp.shopping.rest.endpoint`), plus dictionary- or array-shaped capability manifests.

For live MPP payment, install an MPP-aware client such as `mppx` and provide an executable command template with `--mpp-command`. The script substitutes `{url}` with the protected resource URL. Example:

```bash
python scripts/ucp_resource_client.py \
  --resource-url https://merchant.example/DAV/report.pdf \
  --rdf-url https://merchant.example/offers/report.ttl \
  --mpp-command 'npx mppx {url}'
```

Never place Stripe secret keys, card numbers, private keys, bearer tokens, or MPP secrets in skill files or logs. Use environment variables, OS keychain facilities, or the payment SDK's secure configuration.

## Safety and spending controls

Require explicit purchase authorization before executing a non-test payment. Respect user-specified price/currency constraints. If the UCP checkout total differs materially from the RDF offer, stop and report the discrepancy. Do not auto-pay a different origin than the resource/merchant origins without explicit authorization.

Prefer Stripe test mode/sandbox credentials for testing. Treat MPP Payment authentication as an emerging Internet-Draft protocol and preserve the exact challenge/receipt data for debugging and provenance.

## Output

Return a compact machine-readable result where possible, plus a human summary. Include:

- `resource_url`
- `offer_iri`
- `ucp_item_id`
- `rdf_price` / `rdf_currency`
- `checkout_id` / `checkout_status`
- authoritative checkout total when available
- `mpp_method` / `mpp_intent`
- payment receipt identifier/header when available
- final resource HTTP status and content location
- warnings or unresolved protocol-state differences

For protocol details and mapping conventions, read `references/protocol-notes.md`.

### Direct WebID-TLS/mTLS execution (ODS-QA)

Use [`mtls-curl`](/Users/kidehen/Documents/Management/Development/ai-agent-skills/mtls-curl/SKILL.md) for the certificate transport, including PKCS#12 bundles. Keep the password in an environment variable and carry the same certificate context through RDF/UCP discovery and the post-payment retry. A live ODS-QA request without a certificate may return only `WWW-Authenticate: Digest`; that is one available authentication challenge, not a statement that OAuth or WebID-TLS is unsupported and not an MPP `402`. The observed pattern is public port `443` → `401`/Digest, while the mTLS listener on `5443` accepts the certificate and returns `302` followed by an identity-qualified `402` Payment challenge.

The RDF offer's `schema:itemOffered`/license `uriParameter` is published against the port-less canonical URL (`https://ods-qa.openlinksw.com/DAV/...`), which is a *different IRI string* from the `:5443` URL actually used for the mTLS-authenticated GET — SPARQL/RDF matching on the `:5443` form will find nothing even with a correctly-scoped named graph. Pass `--resource-url` as the `:5443` URL (for the real access probe and MPP handoff) and `--match-url` as the port-less canonical URL (for offer discovery), e.g.:

```bash
python scripts/ucp_resource_client.py \
  --resource-url  "https://ods-qa.openlinksw.com:5443/DAV/home/.../file.pdf" \
  --match-url     "https://ods-qa.openlinksw.com/DAV/home/.../file.pdf" \
  --sparql-endpoint "https://ods-qa.openlinksw.com/sparql" \
  --merchant-origin "https://ods-qa.openlinksw.com" \
  --client-cert "$WEBID_CERT_PEM" --client-key "$WEBID_KEY_PEM" \
  --bearer-token-env UCP_BEARER --accept-payment "stripe/charge" --dry-run
```

### OAuth browser handoff (alternate)

When direct TLS is unavailable, discover the resource origin's [OAuth 2.0 Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414), use Authorization Code + [PKCE](https://www.rfc-editor.org/rfc/rfc7636) in a browser, and pass the resulting access token via `--bearer-token-env`. Use `Authorization: Bearer` or `DPoP` plus a per-request `DPoP` proof. Tokens never appear in arguments, logs, checkout metadata, or provenance output; the token issuer must match the protected resource origin.
