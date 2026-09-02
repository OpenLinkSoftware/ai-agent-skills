# Protocol notes

## UCP

Current UCP REST discovery uses `/.well-known/ucp`. The business profile advertises a `dev.ucp.shopping` REST service endpoint and capabilities such as `dev.ucp.shopping.checkout`. Checkout operations are relative to the discovered endpoint and include create/get/update/complete/cancel session operations.

Profiles in the wild have at least two relevant shapes. Accept a list of transport records containing `transport: rest` and `endpoint`, or a service object containing `rest.endpoint`. Capabilities may be keyed dictionaries or arrays of objects with a `name`. Preserve the advertised service/capability version rather than normalizing it to a hard-coded release.

UCP checkout line items use merchant commerce item identifiers. RDF resource IRIs and offer IRIs must therefore be preserved separately from the merchant item ID. This skill maps the UCP item ID from Schema.org in this order:

1. `schema:sku`
2. `schema:productID`
3. literal `schema:identifier`
4. configured explicit merchant identifier predicates such as `oplofr:offerNumber`
5. an explicit operator-supplied item ID
6. a `schema:potentialAction` item parameter only when the operator opts in

Never infer an opaque UCP item ID from a URL path.

UCP checkout and MPP are separate protocols. Do not mark a checkout completed merely because MPP returned a payment receipt. Completion requires a merchant-supported binding between the external/MPP payment proof and the checkout session.

## RDF / Schema.org offer matching

Accept both `http://schema.org/` and `https://schema.org/`. An offer matches a resource when the resource IRI appears as:

- `schema:itemOffered` (strongest)
- `schema:url`
- `schema:contentUrl`
- a URI-valued `schema:identifier` (only if explicitly modeled as such)
- an explicit relation from the offered Product/License to the resource, including a merchant predicate supplied with `--resource-predicate`

Extract `schema:price`, `schema:priceCurrency`, `schema:availability`, `schema:seller`, and item identifiers. Price and currency may occur directly on the Offer or on its `schema:priceSpecification`. Numeric price comparison must use decimal arithmetic.

## MPP / HTTP Payment authentication

MPP uses the HTTP `402 Payment Required` response with `WWW-Authenticate: Payment` challenges. The client fulfills one challenge and retries using `Authorization: Payment`; success may include a `Payment-Receipt` response header. `401 Unauthorized` is an authentication discovery/challenge response, not a Digest-only response: it can advertise Digest, WebID-TLS/mTLS-related metadata, Bearer, or DPoP. The client may use a `401` to begin OAuth authorization and obtain a token, but must not rewrite that `401` as `402` until authentication has succeeded and the authenticated identity has failed the ACL.

### Identity discovery and execution modes

The client treats server response headers as the REST discovery surface. A `401` may contain multiple `WWW-Authenticate` schemes (including Digest) and a `Link: rel="service-desc"` pointing to authentication metadata. If OAuth is selected, fetch the resource origin's [OAuth 2.0 Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414), use browser Authorization Code + [PKCE](https://www.rfc-editor.org/rfc/rfc7636), and return the resulting access token through an environment variable. Bearer uses `Authorization: Bearer`; DPoP uses `Authorization: DPoP` plus a `DPoP` proof header. The issuer must match the protected resource origin.

For direct WebID-TLS, use [`mtls-curl`](/Users/kidehen/Documents/Management/Development/ai-agent-skills/mtls-curl/SKILL.md) with a PEM or PKCS#12 certificate. This is the preferred ODS-QA execution profile. The server OAuth backend is assumed to be implemented already; this skill only discovers metadata and consumes tokens. Preserve the certificate context across redirects and post-payment retries.

An interactive client must turn this discovery into a user choice at the first `401`: list the advertised schemes, linked metadata, and the credential or browser action each requires, then wait for confirmation. If no choice is made, stop. This prevents an unadvertised Digest or OAuth fallback from changing the user's intended identity.

### Identity-first ACL state machine

The protected resource is ACL-gated and payment is evaluated for an authenticated identity. Use this response sequence:

1. Authenticate the request identity.
2. Evaluate that identity against the resource ACL.
3. Return `200` when the ACL grants access.
4. Return `401` with the applicable non-payment authentication challenge when identity authentication is missing or fails.
5. When authentication succeeds but the ACL does not grant access, return `402` with at least one `WWW-Authenticate: Payment` challenge that is explicitly correlated with that identity and resource.
6. After payment, bind the receipt/entitlement to the authenticated identity, repeat the ACL decision, and return `200` plus `Payment-Receipt` when access is granted. Use `403` only for a terminal policy denial that payment cannot resolve.

Required payment response shape:

```http
HTTP/1.1 402 Payment Required
Cache-Control: no-store
WWW-Authenticate: Payment id="...", realm="...", method="stripe", intent="charge", request="..."
Link: <https://merchant.example/offers/report.ttl>; rel="describedby"; type="text/turtle"
Link: <https://merchant.example/.well-known/ucp>; rel="service-desc"; type="application/json"
Content-Type: application/problem+json
```

The status code alone is not sufficient. The client parses repeated `WWW-Authenticate` and `Link` fields and treats these as protocol errors:

- `402` before the client has established identity;
- `402` without a `Payment` challenge;
- a Payment challenge that cannot be correlated with the resource and authenticated identity;
- `401` presented as though it were a payment response.

The MPP retry must reuse the same authenticated identity context. A Payment credential does not replace the identity credential; it supplies payment proof for that identity's missing ACL entitlement.

Basic, Digest, Bearer, and DPoP identity credentials compete with Payment for the HTTP `Authorization` field, so do not design the retry as two simultaneous Authorization credentials. Preserve identity continuity using one of these patterns:

- authenticate independently at the transport layer, such as WebID-TLS/mTLS, while `Authorization: Payment` carries payment proof;
- establish a secure authenticated session cookie during the identity exchange, then send that cookie with `Authorization: Payment`;
- bind the Payment challenge ID server-side to the authenticated identity, resource IRI, ACL decision, amount, currency, and expiry, then update the identity's entitlement after verification and require a fresh resource GET using the original identity authentication.

The third pattern is especially suitable when UCP checkout and MPP settlement occur at separate REST resources. The original protected-resource endpoint remains stateless from the client's perspective: its `402` response provides links and challenge metadata, payment updates the entitlement resource, and the client retries the protected GET with the same identity.

The Payment authentication framework is payment-method agnostic. Stripe can be offered as a method such as `stripe/charge`. Use an MPP implementation (for example `mppx`) to handle method-specific challenge parsing, payment credential creation, Stripe Shared Payment Token/card flows, retry, and receipt verification.

Do not implement Stripe card handling directly in this skill. Delegate payment-sensitive operations to the MPP SDK/client so PCI-sensitive details do not enter the agent workflow.

## Versioning

UCP is evolving. Always obey the version and endpoint advertised by the merchant profile instead of assuming a fixed dated schema. MPP Payment authentication is also evolving; preserve raw challenge and receipt headers for reproducibility.
