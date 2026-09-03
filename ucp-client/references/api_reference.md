# UCP resource client command reference

`scripts/ucp_resource_client.py` performs RDF offer discovery, UCP profile discovery, optional checkout creation, and optional MPP handoff.

## Entry points

Pass exactly one of `--resource-url` or `--product-feed` — they are alternative ways to identify what to check out, not combinable:

- `--resource-url URL` drives the full identity-first flow: probe the resource, interpret `401`/`402`/`200`, discover the offer via SPARQL/RDF (or, failing that, the resource's own 402 challenge), then check out.
- `--product-feed URL` skips all of that. A merchant product feed (RSS 2.0 + Google Merchant `g:` namespace, e.g. opl-shop's `/shop/feed?rss`) is a complete, typically-public, pre-authenticated catalog — every item already carries its offer IRI, price, and currency. There is nothing to probe and no 401/402 to interpret.

## Product feed options

- `--product-feed URL` — merchant product feed URL. With no selector, the client fetches it, lists every item (`title`, `description`, `link`, `guid`, `feed_item_id` (the feed's `g:id`), `price`, `currency`, `product_type`, `brand`) as `feed_items` in the JSON result, and stops — "ask which product offer to use" for a human or calling agent to pick from. `link`/`guid` is the offer IRI, used directly as the UCP item id (`ucp_item_id_source: "product_feed"`).
- `--feed-item-id VALUE` — select one feed item by its `feed_item_id` (`g:id`), `guid`, or `link`. Must match exactly one item, or the result reports `error` and exits `1` (no match) or `2` (ambiguous).
- `--feed-search TEXT` — select by case-insensitive substring match on `title`; same match-exactly-one-or-report-and-exit behavior as `--feed-item-id`.
- Once exactly one item is selected, the flow continues identically to the `--resource-url` path from UCP discovery onward: `--dry-run` previews the checkout request and stops; otherwise a real checkout is created and handled the same way (`--complete-with-stripe-spt` / `--mpp-command` / `handoff_required`) — see "Checkout and payment options" below. `--mpp-command` doesn't apply here (there is no protected resource URL to retry against) and reports `not_executed` if given without `--complete-with-stripe-spt`.

## Discovery and mapping options (--resource-url path only)

- `--resource-url URL` — protected resource IRI. Used for the identity/ACL probe and the MPP handoff.
- `--match-url URL` — canonical resource IRI to match against RDF/SPARQL offers, if different from `--resource-url`. Defaults to `--resource-url`. Use this when the merchant's RDF-published resource identifier and the actual access endpoint differ in their exact IRI string (e.g. access requires a distinct mTLS port, like ODS-QA's `:5443`, that is absent from the resource's published IRI) — offer matching is exact-IRI, so the two cannot be the same flag when the strings differ.
- `--rdf-url URL` — explicit RDF offer document used after SPARQL fallback.
- `--sparql-endpoint URL` — merchant SPARQL endpoint; defaults to `/sparql` on the merchant origin.
- `--sparql-default-graph IRI` — SPARQL protocol `default-graph-uri` parameter(s) to scope offer discovery to a named graph; repeatable. Quad stores often keep offer data outside the SPARQL default graph; when this is omitted, a first unscoped query that returns zero rows is automatically retried once, scanned across all named graphs (`GRAPH ?g { ... }`), before falling back to RDF dereference. Pass this explicitly to skip the automatic scan or to disambiguate when more than one graph could match.
- `--merchant-origin URL` — origin used for `/.well-known/ucp` discovery.
- `--resource-predicate IRI` — additional predicate that explicitly links an Offer or its offered item to the resource; repeatable.
- `--item-id-predicate IRI` — additional predicate containing a literal UCP item identifier; repeatable.
- `--item-id VALUE` — verified UCP item identifier override.
- `--allow-action-item-id` — opt in to an `item`, `sku`, `product`, or `product_id` query parameter from `schema:potentialAction`.

## Identity and ACL probe options

- `--identity-header-env HEADER=ENV_VAR` — set an identity-bearing request header from an environment variable; repeatable. The secret value is never emitted.
- `--digest-user-env ENV_VAR` and `--digest-password-env ENV_VAR` — perform HTTP Digest authentication using environment-backed values. Supply both.
- `--bearer-token-env ENV_VAR` — send an OAuth access token from an environment variable as `Authorization: Bearer ...` (or `DPoP ...`); the value is never emitted.
- `--oauth-token-type {Bearer,DPoP}` — select the OAuth authorization scheme; defaults to `Bearer`.
- `--dpop-proof-env ENV_VAR` — per-request DPoP proof JWT when `--oauth-token-type DPoP` is selected.
- `--client-cert PATH` and optional `--client-key PATH` — use a PEM client certificate and key.
- `--client-p12 PATH` with required `--client-p12-password-env ENV_VAR` — use a PKCS#12 (`.p12`/`.pfx`) client identity bundle (e.g. a WebID-TLS/NetID certificate) as an alternative to `--client-cert`/`--client-key`. `requests` has no native PKCS#12 support, so the bundle is decrypted with the `cryptography` library and its cert chain + private key are written to a `0700` temp directory as `0600` PEM files, which `requests`/urllib3 requires; the directory is removed via `atexit` when the process exits. The password comes only from the named environment variable, never the command line, and is never logged or re-emitted. Mutually exclusive with `--client-cert`.
- `--identity-established` — assert that an ambient session establishes identity without exposing credentials. This assertion does not itself authenticate the request.
- `--accept-payment VALUE` — send `Accept-Payment`, for example `stripe/charge`.
- `--access-probe-only` — execute the authenticated resource request, classify `200`/`401`/`402`/`403`, parse response metadata, and stop before commerce.

Interactive callers must pause on `401`, present the discovered authentication choices to the user, and obtain an explicit protocol selection before retrying. Non-interactive callers must stop and return the parsed `authentication_schemes` and authentication links; they must not select Digest or OAuth implicitly.

For `402`, the result contains parsed `payment_challenges`, typed `links`, `Payment-Receipt`, `Location`, and protocol errors. A linked `rel=describedby`/`alternate` RDF document and `rel=ucp`/`service-desc` UCP profile are used automatically when present.

For direct WebID-TLS/mTLS with PKCS#12, compose this skill with [`mtls-curl`](/Users/kidehen/Documents/Management/Development/ai-agent-skills/mtls-curl/SKILL.md); the Python client retains PEM support while curl owns PKCS#12 transport and header capture. OAuth browser authorization is external: this skill consumes the resulting token and assumes the server OAuth backend is already deployed.

## Checkout and payment options

- `--quantity N` — positive checkout quantity; defaults to 1.
- `--agent-profile URL` — value advertised in the `UCP-Agent` header.
- `--dry-run` — probe access, discover the offer, and render the checkout request without creating a checkout or invoking payment. It continues discovery after `401` for diagnostics while preserving the failed authentication state.
- `--mpp-command TEMPLATE` — external MPP client command; `{url}` is replaced with the protected resource URL. Pays the protected *resource's* own `402` challenge directly — distinct from `--complete-with-stripe-spt`, which completes the *UCP checkout* itself.
- `--complete-with-stripe-spt` — after creating the checkout, fetch its `totals[type=total]` amount, request a Stripe test-mode Shared Payment Token capped at that amount, and `POST .../checkout-sessions/{id}/complete` with `payment.instruments[0].credential = {type: "stripe_payment_token", token: <spt>}` (the Link Agent Wallet shape from [Stripe's UCP payments handler](https://docs.stripe.com/agentic-commerce/ucp/stripe-payments-handler)). On success, fetches and includes the resulting order. Mutually exclusive in practice with `--mpp-command` — if both are given, `--complete-with-stripe-spt` runs and `--mpp-command` is not reached.
- `--stripe-api-key-env ENV_VAR` — environment variable holding the Stripe secret key (test mode); never emitted. Default: `STRIPE_API_KEY`.
- `--stripe-payment-method VALUE` — Stripe test payment method backing the SPT. Default: `pm_card_visa`.
- `--stripe-payment-handler-id VALUE` — `handler_id` sent in the payment instrument; must match a handler the merchant advertises at `/.well-known/ucp`. Default: `opl_shop_stripe_spt`.

A non-2xx response from `create_checkout` is reported as a `checkout_error` object (`status`, `body`, `endpoint`) in the JSON result rather than an unhandled exception, and the process exits `4`. A failure anywhere in the `--complete-with-stripe-spt` sequence (no total on the checkout, missing Stripe key, Stripe SPT request failure, or checkout completion failure) is reported as `mpp: {status, ...}` and exits `5`.

If offer discovery itself fails (no SPARQL/RDF-discoverable `schema:Offer` at all, even after the named-graph retry and `--match-url`), the client falls back to decoding the offer identity directly out of the resource's own `WWW-Authenticate: Payment request=<base64url JSON>` challenge parameter, when present — some MPP/x402-gated resources carry no RDF description whatsoever, but the challenge itself names the exact offer IRI (and often price/currency) used to price the checkout. The result's `offer_discovery.method` is `payment_challenge` (or `cli_override` when `--item-id` was supplied) in that case, rather than `sparql`/`rdf_dereference`.

## Compatibility behavior

The client accepts both Schema.org namespace variants, direct and item-mediated resource relations, direct and `schema:priceSpecification` pricing, legacy and nested UCP REST-service declarations, and dictionary- or array-shaped capability manifests. Every selected UCP item ID includes `ucp_item_id_source` in the result.

The client never converts an HTTP path into a merchant item ID. When the RDF does not contain an accepted identifier, supply a verified predicate or explicit value rather than guessing.
