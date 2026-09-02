# UCP resource client command reference

`scripts/ucp_resource_client.py` performs RDF offer discovery, UCP profile discovery, optional checkout creation, and optional MPP handoff.

## Discovery and mapping options

- `--resource-url URL` — protected resource IRI; required.
- `--rdf-url URL` — explicit RDF offer document used after SPARQL fallback.
- `--sparql-endpoint URL` — merchant SPARQL endpoint; defaults to `/sparql` on the merchant origin.
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
- `--mpp-command TEMPLATE` — external MPP client command; `{url}` is replaced with the protected resource URL.

## Compatibility behavior

The client accepts both Schema.org namespace variants, direct and item-mediated resource relations, direct and `schema:priceSpecification` pricing, legacy and nested UCP REST-service declarations, and dictionary- or array-shaped capability manifests. Every selected UCP item ID includes `ucp_item_id_source` in the result.

The client never converts an HTTP path into a merchant item ID. When the RDF does not contain an accepted identifier, supply a verified predicate or explicit value rather than guessing.
