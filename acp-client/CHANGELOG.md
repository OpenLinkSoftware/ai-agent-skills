# Changelog

## 1.7.0 — 2026-08-19

### Changed

- **WebID-TLS/NetID-TLS now defaults to port 5443 automatically, as an
  upfront RULE in Auth Protocol Selection, not as prose buried in
  Protocol-Specific Notes discovered after a misleading `401` on 443.**
  Verified live against `ods-qa.openlinksw.com`: port 443 never issues a
  `CertificateRequest` in the TLS handshake at all (falls straight to `401
  Digest` regardless of certificate availability); port 5443 does, and the
  resulting `302 ?k=...` redirect is what actually leads to the `402`
  challenge. Frontmatter, "When to Use", and the WebID-TLS Protocol-Specific
  Notes bullet updated to match, plus the NetID-TLS alias throughout (same
  mechanism, different name).

## 1.6.0 — 2026-08-02

### Changed

- **Mermaids rewritten to match the authoritative two-flow diagram.** Route A is now the **Agent-Centric MPP Flow** (`Software Agent → Resource Server → Stripe (SPT)`): access → `402` challenge → SPT → retry → validate challenge + SPT + ACL → `200 OK` + receipt; no shop/ACP participant. Route B is now the **Human-Centric Shop Flow** (`Human User → Shop Server → Stripe (Subscriptions) → Resource Server`): login & select offer → create subscription → subscription active → shop replicates purchase subset to resource server → user accesses resource authenticated → check ACL + purchase + subscription → `200 OK`. Elicitation table, elicitation prompt, Route A/B notes, and Access Verification updated to match. Both diagrams validated `PARSE OK` via mermaid-cli.

## 1.5.0 — 2026-08-01

### Added

- **Auth Protocol Selection (Elicitation)**: The MPP purchase flow is now protocol-agnostic. WebID-TLS (mTLS) is one option among several — OAuth (Bearer) and Digest are documented, with a signal table and elicitation prompt so the agent selects the authentication protocol before acting when not clearly discernible from the prompt. Frontmatter description and "When to Use" triggers updated to cover MPP 402 flows across protocols.

### Changed

- Renamed the section to "MPP Purchase Flow for Protected Resources (Protocol-Agnostic)". Both Route A and Route B sequence diagrams now use a generic `Resource Server (DAV_MPP_CALLBACK)` participant and a `{protocol}` placeholder for the authentication step, so the same 6-step MPP machinery applies regardless of protocol.
- Added **Protocol-Specific Notes**: WebID-TLS (`:5443`, client cert → principal WebID = service_id), OAuth (Bearer token; `On-Behalf-Of` delegation with bare WebID URI — no angle brackets), Digest (username/password against WebDAV ACL).
- Route B note generalized: buyer is bound to the principal identity (WebID for WebID-TLS, or OAuth/Digest-bound identity).

## 1.4.0 — 2026-08-01

### Added

- **Route selection (elicitation)**: The WebID-TLS purchase flow now documents both settlement routes — **Route A** (direct MPP settlement via `DAV_MPP_CALLBACK`, non-UI/headless agent) and **Route B** (ACP checkout session, interactive/UI agent) — with a signal table and elicitation prompt so the agent selects the route before acting. ACP is described as merchant of record in both routes (owns the Stripe account and offer catalog; only the settlement party differs).

### Changed

- Restructured the WebID-TLS section into: Route Selection (elicitation) → Route A (corrected DAV_MPP_CALLBACK mermaid + notes) → Route B (ACP checkout mermaid incl. step 5b purchases-graph write + notes) → Shared Implementation Notes (`agent: false`, timeouts) → Access Verification (route-specific success criteria).

## 1.3.0 — 2026-08-01

### Changed

- **Corrected WebID-TLS Resource Access Purchase Flow**: Replaced the mermaid sequence diagram with the authoritative flow where the resource server's `DAV_MPP_CALLBACK` is the MPP participant that settles directly with Stripe's Payment Intents API (Basic auth = shop's own Stripe secret key), rather than an ACP checkout session. The 402 is a structured `WWW-Authenticate: Payment` challenge (`id`, `method=stripe`, `intent=charge`, base64 `request`, `Link: offer_iri; rel=schema.org/offers`); the SPT is obtained out of band from Stripe granted_tokens and presented by echoing the challenge (`Authorization: Payment base64({payload:{spt}, challenge})`). Server writes `Purchase(PurchasePending)` → `PurchaseCompleted` to the purchase graph and returns `200 OK` + `Payment-Receipt: receipt` (base64url receipt). Same `k` replays idempotently on re-access.
- **Critical Implementation Notes rewritten** around the corrected flow: `k` = session/idempotency key, `:5443` not `:443`, TLS-session-reuse trap (`agent: false`), ACP-only notes (Content-Length, `buyer.webid`) retained as optional path guidance, ~90-170 s timeouts.

## 1.2.0 — 2026-08-01

### Added

- **WebID-TLS Resource Access Purchase Flow**: Added the validated mermaid sequence diagram documenting the full 6-step flow for paid URIBurner resources (401 → WebID-TLS on `:5443` → 402 → ACP checkout → Stripe MPP settlement → shop writes entitlement to the purchases graph on the resource server → WebID-TLS access test).
- **Critical implementation notes**: WebID-TLS hop on `:5443` (not `:443`); `agent: false` to disable TLS session reuse on redirect hops (otherwise 401 instead of 402); explicit `Content-Length` on ACP POST bodies (otherwise 422 "Request body is required"); `buyer.webid` binding; ~90-170s per-hop timeouts; `subscription_payment_required` hosted-invoice handling.
- **Access verification guidance** for the post-payment WebID-TLS probe (200 vs 402/401 diagnosis).

## 1.0.2 — 2026-05-30

### Added

- **Balance payment method**: Added `handler_id: "balance"` as an alternative to Stripe SPT for completing checkouts when the user has sufficient ACP account credit.

## 1.0.1 — 2026-05-30

### Added

- **Product catalog**: Added Special Price and Retail Price columns for all catalogued offers.
- **Price validation note**: Documented the $0 checkout issue and the `2024-01` vs `2024-02` version discrepancy.

### Fixed

- **Product catalog**: Corrected JDBC to ODBC bridge driver offer IRI from `2024-02` (zero-priced, causes payment decline) to `2024-01` ($49.99, validated working).

## 1.0.0 — 2026-05-29

### Initial Release

- Intent-driven ACP client skill derived from `acp_curl.sh`
- Natural language purchase intent mapping ("I want to purchase X")
- Product catalog resolution from OpenLink TTL sources:
  - Virtuoso Enterprise Offers
  - OPAL Knowledge Graph Access Offers
  - UDA Lite Edition Offers
- Full checkout flow: create → get total → Stripe SPT → complete
- Cart lifecycle: create → get → update → cancel
- Order retrieval
- Manual OAuth bearer token acquisition via `applications.vsp`
- Composable `curl` recipes with `jq`/`awk` JSON helpers
- Human-readable and `--json` output modes
