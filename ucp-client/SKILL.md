---
name: ucp-client
description: Purchase an HTTP-protected resource by discovering an RDF schema:Offer, authenticating an identity (WebID-TLS/mTLS, OAuth Bearer/DPoP, Digest, or headers), mapping the offer to UCP checkout, handing payment to Machine Payments Protocol (MPP) with Stripe support, verifying the receipt, and retrieving the resource. Use when a user supplies a resource URL and wants flexible identity-first ACL handling, UCP checkout, HTTP 402 payment, or an auditable RDF-to-commerce purchase flow.
---

# UCP Client

Use the resource URL as the primary identifier. Keep RDF as the authoritative offer description, UCP as the commerce/checkout protocol, MPP as the HTTP 402 payment protocol, and Stripe as a payment processor. Do not collapse these layers.

## Two entry points

Everything below (steps 1-9) is the `--resource-url`-driven path: start from a protected resource, work backward through identity/402/RDF discovery to find its offer. When the merchant instead publishes a **product feed** (RSS 2.0 + Google Merchant `g:` namespace, e.g. `https://<shop>/shop/feed?rss`), skip all of that: `--product-feed URL` fetches the feed directly — it is already a complete, typically-public, pre-authenticated list of every purchasable offer with its own IRI (`link`/`guid`), price, and currency. With no `--feed-item-id`/`--feed-search` selector the client lists every item and stops so a human or calling agent can pick one; with a selector matching exactly one item, it goes straight to UCP discovery and checkout (steps 6-9 below), skipping the identity-probe/401/402/RDF/SPARQL steps (1-5) entirely — there is no resource ACL to probe and no offer to discover, the feed already answered both.

```bash
# List every offer in the shop's feed
python scripts/ucp_resource_client.py --product-feed "https://ods-qa.openlinksw.com/shop/feed?rss"

# Pick one by title search, preview the checkout without creating it
python scripts/ucp_resource_client.py \
  --product-feed "https://ods-qa.openlinksw.com/shop/feed?rss" \
  --feed-search "Hotpot" --bearer-token-env UCP_BEARER --dry-run

# Same, but actually create + complete the checkout via a Stripe test SPT
python scripts/ucp_resource_client.py \
  --product-feed "https://ods-qa.openlinksw.com/shop/feed?rss" \
  --feed-item-id "ODSQA-FA-PROPERLANCASHIREHOTPOTRECIPE-0001" \
  --bearer-token-env UCP_BEARER --complete-with-stripe-spt
```

## Core workflow (--resource-url path)

1. Accept a protected `resource_url` and establish the request identity without putting secrets on the command line. `scripts/ucp_resource_client.py` accepts a WebID-TLS/NetID client certificate directly, either as PKCS#12 (`--client-p12 PATH --client-p12-password-env ENV_VAR` — the bundle is decrypted with `cryptography` and staged as temporary `0600` PEM files, cleaned up on exit; confirmed live against ODS-QA) or PEM (`--client-cert`/`--client-key`); for the selected ODS-QA direct-execution profile with `curl` itself rather than this script, the [`mtls-curl`](/Users/kidehen/Documents/Management/Development/ai-agent-skills/mtls-curl/SKILL.md) skill is the alternative. The client also accepts an OAuth access token (Bearer or DPoP), Digest credentials, environment-backed headers, or an already-established ambient identity session. Discover OAuth metadata from the resource origin's [OAuth 2.0 Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414) endpoint when using OAuth; the server OAuth backend is assumed to already exist and is not implemented by this skill.
2. Probe the resource before commerce. Interpret the server response as an identity-first state machine: `401` means authentication is missing or failed and may advertise one or more authentication schemes; `200` means the authenticated identity passes the resource ACL; `402` means the authenticated identity failed the ACL and payment can grant access; `403` is a terminal policy denial without a payable challenge. A `401` may therefore trigger Digest, WebID-TLS/mTLS, or OAuth token acquisition; it is never itself a payment challenge.
3. Accept `402` only when identity was established and the response includes at least one `WWW-Authenticate: Payment` challenge. Parse repeated `WWW-Authenticate` and `Link` fields, preserving Payment challenge parameters, `Payment-Receipt`, `Location`, content type, and links such as `rel=offer`, `describedby`, `alternate`, or `payment`. A naked `402`, or `402` before identity, is a protocol error.
4. Query the merchant RDF knowledge graph for a `schema:Offer` associated with the resource IRI. Accept both Schema.org namespace forms (`http://schema.org/` and `https://schema.org/`). Match direct `schema:itemOffered`, `schema:url`, `schema:contentUrl`, or `schema:identifier` links and item-mediated links such as Offer → License/Product → resource. Use `--resource-predicate IRI` for additional explicit merchant relations. Use `--sparql-endpoint` when known; otherwise try `<merchant-origin>/sparql`; then use response-linked or explicit RDF metadata. Quad stores commonly keep offer data in a named graph outside the SPARQL protocol default graph: an unscoped query that returns no rows is automatically retried once, scanned across all named graphs (`GRAPH ?g { ... }`), before falling back to RDF dereference; pass `--sparql-default-graph IRI` (repeatable) to scope explicitly instead of relying on the automatic scan. If the resource's public/RDF-published IRI differs from the URL actually used to access it (see the ODS-QA case below), pass `--match-url` with the RDF-published IRI so offer matching succeeds independently of the access URL. If discovery still finds no offer at all (some MPP/x402-gated resources publish no RDF description whatsoever), fall back to decoding the offer identity directly out of the resource's own `WWW-Authenticate: Payment request=<base64url JSON>` challenge parameter, when present, rather than failing outright.
5. Extract offer identity, item identity, price, currency, availability, seller, and UCP item identifier. Read price/currency either directly or through `schema:priceSpecification`. Prefer `schema:sku`, then `schema:productID`, then literal `schema:identifier`; known explicit merchant identifiers such as `oplofr:offerNumber` may follow. For another merchant vocabulary use repeatable `--item-id-predicate IRI`, or supply a verified `--item-id VALUE`. Never infer an ID from a URL path. `schema:potentialAction` query parameters remain opt-in via `--allow-action-item-id`.
6. Discover the merchant UCP profile at `/.well-known/ucp` and read the advertised `dev.ucp.shopping` REST checkout capability/version.
7. Create a UCP checkout session using the mapped item ID and quantity. Treat the checkout response as authoritative for final price, totals, eligibility, and status. Before spending money, surface the checkout amount/currency and payment boundary unless the user explicitly authorized the purchase and any required spending limit is satisfied.
8. Pay for the checkout through whichever surface the merchant actually settles it on — these are two distinct targets, not interchangeable:
   - **UCP checkout completion**: when the merchant advertises a payment handler compatible with a Shared Payment Token (e.g. `opl_shop_stripe_spt`, following the Link Agent Wallet shape from [Stripe's UCP payments handler](https://docs.stripe.com/agentic-commerce/ucp/stripe-payments-handler)), pass `--complete-with-stripe-spt` to fetch a Stripe test-mode SPT capped at the checkout's authoritative total and `POST .../complete` directly — this finishes the *UCP checkout itself* and returns the resulting order.
   - **Resource-level MPP payment**: fulfill one server-advertised Payment challenge on the *protected resource* using an MPP implementation such as `mppx` (`--mpp-command`). Preserve identity independently through WebID-TLS/mTLS, an authenticated session cookie, or a server-side challenge binding; Basic/Digest/Bearer/DPoP and Payment cannot both occupy the single `Authorization` field. After entitlement binding, retry the resource with the original identity context and capture `Payment-Receipt` plus the final status.
9. Reconcile an MPP receipt with the UCP checkout only through a merchant-supported binding — the two are not automatically the same transaction. Return the resource plus provenance: identity-gate state, resource URL, offer IRI, checkout ID/status, amount/currency, payment method/intent, receipt or order, and final HTTP status.

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

`scripts/ucp_resource_client.py` carries a PKCS#12 or PEM certificate through the whole session itself (`--client-p12 PATH --client-p12-password-env ENV_VAR`, or `--client-cert`/`--client-key`) -- no separate `curl` transport needed, and the same identity automatically covers RDF/UCP discovery, checkout, and the post-payment retry. [`mtls-curl`](/Users/kidehen/Documents/Management/Development/ai-agent-skills/mtls-curl/SKILL.md) remains the option when driving raw `curl` directly instead of this script; keep the password in an environment variable either way. A live ODS-QA request without a certificate may return only `WWW-Authenticate: Digest`; that is one available authentication challenge, not a statement that OAuth or WebID-TLS is unsupported and not an MPP `402`. The observed pattern is public port `443` → `401`/Digest, while the mTLS listener on `5443` accepts the certificate and returns `302` followed by an identity-qualified `402` Payment challenge -- confirmed live with `--client-p12`.

**ODS-QA runs two independent UCP deployments, not one shared across ports.** `:443`'s `/ucp` is one-way TLS only (no `CertificateRequest` in the handshake -- verified with `curl -v`); a client certificate presented there is silently never negotiated, and `POST /ucp/checkout-sessions` there 401s regardless of `--client-p12`/`--client-cert` -- only `--bearer-token-env` authenticates against it. `:5443` runs its *own* complete UCP deployment with its *own* `/.well-known/ucp` (self-consistently advertising `endpoint: https://ods-qa.openlinksw.com:5443/ucp`), and mutual TLS there is accepted for checkout creation too, not just the DAV resource probe -- confirmed live (`POST .../checkout-sessions` → `201`, `status: ready_for_complete`). Do **not** pass `--merchant-origin` pinned to the plain-`443` host when using `--client-p12`/`--client-cert` against a `:5443` resource URL; leaving `--merchant-origin` unset lets discovery correctly default to the resource's own origin (`:5443`), which is what actually works. One more thing worth checking before trusting a p12 identity's purchases: the resolved `buyer.email` on a real checkout is not guaranteed to match the certificate's own Subject CN -- verify it in the checkout response rather than assuming.

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
