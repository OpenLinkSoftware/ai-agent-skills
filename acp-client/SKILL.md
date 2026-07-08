---
name: acp-client
description: >
  Intent-driven ACP (Adaptive Commerce Platform) client. Handles natural-language
  purchase requests by executing checkout, cart, and order flows against OpenLink's
  ACP API. Integrates Stripe test SPT generation for checkout completion. Supports
  product resolution from OpenLink offer catalog, checkout updates, cancellation,
  and subscription payment link detection.
version: 1.1.0
type: skill
---

# ACP Client Skill

Execute checkout, cart, and order operations against the OpenLink Adaptive
Commerce Platform (ACP) API using composable `curl` recipes. Triggered by
natural-language purchase intents.

## When to Use

- "I want to purchase `{product}`" / "Buy `{product}`" / "Get me a license for `{product}`"
- "Checkout `{product}`" / "Create a checkout for `{offer-id}`"
- "Update checkout `{id}`" / "Change quantity for checkout `{id}`"
- "Cancel checkout `{id}`" / "Cancel my order"
- "Complete checkout `{id}`" / "Pay for checkout `{id}`"
- "Add `{product}` to cart" / "Create a cart for `{product}`"
- "Get order `{order-id}`" / "Check status of order `{order-id}`"
- "Get a Stripe test token" / "Generate SPT for `{amount}`"
- "Use balance" / "Pay with balance"
- Any request referencing the ACP API, checkout sessions, carts, or OpenLink
  software license purchases.

## Prerequisites

- `curl` installed
- `jq` recommended (fallback `awk` JSON parsers provided)
- `ACP_AUTH_TOKEN` environment variable set, or user must obtain one manually
- `STRIPE_API_KEY` required for `complete` and `spt` flows

## ACP Instances

Known ACP API endpoints. The default is `shop.openlinksw.com`; override via `ACP_BASE_URL`:

| Instance | URL |
|---|---|
| **Shop (default)** | `https://shop.openlinksw.com/acp` |
| QA / Staging | `https://ods-qa.openlinksw.com/acp` |

To use a non-default instance, set `ACP_BASE_URL` before invoking the skill:
```bash
export ACP_BASE_URL="https://ods-qa.openlinksw.com/acp"
```

## Environment Variables

| Variable | Required | Default |
|---|---|---|
| `ACP_BASE_URL` | No | `https://shop.openlinksw.com/acp` |
| `ACP_API_VERSION` | No | `2026-01-30` |
| `ACP_AUTH_TOKEN` | **Yes** | Prompted if missing |
| `ACP_ITEM_ID` | No | Resolved from product catalog or user input |
| `STRIPE_API_KEY` | Yes (for complete/spt) | Prompted if missing |
| `STRIPE_PAYMENT_METHOD` | No | `pm_card_visa` |
| `STRIPE_SPT_CURRENCY` | No | `usd` |
| `STRIPE_SPT_MAX_AMOUNT` | No | `1000` |
| `STRIPE_SPT_EXPIRES_AT` | No | `now + 1 hour` (auto-computed) |

## Intent-to-Flow Mapping

When the user expresses a natural-language intent, map it to the corresponding
ACP flow:

| User Intent | Skill Flow |
|---|---|
| "I want to purchase `{product}`" | **Full purchase**: `create_checkout` → `get_checkout_total` → (`balance` or `spt`) → `complete_checkout` |
| "Checkout `{product}`" | `create_checkout` → return checkout session ID and total |
| "Update checkout `{id}`" | `update_checkout` — change items/quantity |
| "Cancel checkout `{id}`" | `cancel_checkout` — cancel with `reason_code: buyer_cancelled` |
| "Complete checkout `{id}`" | `complete_checkout` — fetch total, get SPT, complete |
| "Add `{product}` to cart" | `create_cart` → return cart ID |
| "Get order `{order-id}`" | `get_order` |
| "Get Stripe SPT" | `get_test_spt` |
| "Use balance" / "Pay with balance" | `complete_checkout` with `handler_id: "balance"` |

## Product Resolution

When the user names a product (e.g., "JDBC to ODBC bridge driver"), resolve it
to an offer IRI using the catalog in `references/product-catalog.md`. Match
against:

- `schema:name`
- `skos:prefLabel`
- `skos:altLabel`
- `schema:description`

If no match is found, ask the user for the full offer IRI or product URL.

## Bearer Token Acquisition (Manual)

If `ACP_AUTH_TOKEN` is missing or invalid:

1. **Prompt the user**: "ACP bearer token not found. Please obtain one from the
   OAuth applications page."
2. **Provide URLs**:
   - Primary: `https://ods-qa.openlinksw.com/oauth/applications.vsp`
   - Alternative: `https://shop.openlinksw.com/oauth/applications.vsp`
   - Additional: any other Virtuoso instance the user specifies
3. **Instructions**:
   - Navigate to the URL
   - Log in via the authentication form (Digest, WebID-TLS, or social login)
   - Register a new OAuth application
   - Copy the generated bearer token
   - Export as `ACP_AUTH_TOKEN` or paste when prompted

## Browser Automation

The skill uses [Playwright](https://playwright.dev) (`playwright-cli`) for
browser automation. PinchTab is a fallback if Playwright is unavailable.

Set the wrapper script path before use:
```bash
export PWCLI="{REPO_ROOT}/.opencode/skills/playwright/scripts/playwright_cli.sh"
```

### Prerequisites

- `npx` (comes with Node.js/npm)
- Playwright browsers installed (first use): `npx playwright install chromium`

### Workflow

1. Open page in headed mode: `"$PWCLI" open <url> --headed`
2. Snapshot for element refs: `"$PWCLI" snapshot`
3. Interact with elements by ref (e.g., `"$PWCLI" click e79`)
4. Capture screenshots or PDFs as needed

## Subscription Payment Detection

After `complete_checkout`, the response may contain a `links` array with a
`subscription_payment` entry. When present:

1. Extract the `href` value from the link with `rel: "subscription_payment"`
2. Open the link with Playwright:
   ```bash
   "$PWCLI" open <href> --headed
   "$PWCLI" snapshot
   ```
3. Present the snapshot to the user showing the payment form.
4. Ask the user if they want to proceed with payment.

## Checkout Body Format

The `create_checkout` and `update_checkout` operations use `items` (not
`line_items`) and `capabilities` as an empty object:

```json
{
  "items": [
    { "id": "http://data.openlinksw.com/oplweb/offer/Offer-2020-10-virtuoso-8-app-developer-development-WKS-ANY#this", "quantity": 1 }
  ],
  "currency": "usd",
  "capabilities": {}
}
```

## Output Format

- **Default**: Human-readable summary (checkout ID, order ID, status, total,
  receipt, subscription payment link if present)
- **`--json` flag**: Raw JSON from the API response, stable machine-readable
  output for agent consumption

## Post-Purchase File Access Verification

After a checkout is completed and the subscription payment is processed, verify
that the purchased file/resource is accessible:

1. **Resolve the resource URL** from the offer IRI — typically the offer's
   `schema:subjectOf` or the resource's canonical DAV/WebDAV path on the
   ACP instance.

2. **Fetch with On-Behalf-Of delegation** using the ACP bearer token:
   ```bash
   curl -sI -H "Authorization: Bearer ${ACP_AUTH_TOKEN}" \
     -H "On-Behalf-Of: {resource-iri}" \
     "{resource-url}"
   ```
   > **IMPORTANT**: The `On-Behalf-Of` header value must be a **bare WebID URI — no angle brackets**. Correct: `-H "On-Behalf-Of: https://example.com/path#fragment"`. Angle brackets cause delegation resolution failure (402/401). The `{resource-iri}` placeholder uses curly braces conventionally — the actual value is a bare IRI.

   - `200 OK` → access granted, file is available
   - `401 Unauthorized` → provisioning may be async; retry after a short delay
   - `403 Forbidden` → access not granted; check order/subscription status
   - `404 Not Found` → wrong resource URL; verify path

3. **Report result** to the user: confirmed accessible, or explain the issue.

## Error Handling

- `401 Unauthorized` → Bearer token missing or invalid; direct user to OAuth
  applications page
- `404 Not Found` → Checkout/cart/order ID does not exist
- `409 Conflict` → Idempotency key collision; retry with new UUID
- Stripe errors → Report Stripe error message and raw response
- Missing `jq` → Fall back to bundled `awk` JSON parsers (`_json_str`,
  `_json_total`, `_json_sub_payment_url`)

## JSON Helper Functions

The skill bundles three portable JSON extraction functions that work with or
without `jq`:

- `_json_str FIELD` — extract a top-level string field from stdin JSON
- `_json_total` — extract `amount` where `type=="total"` from the `totals` array
- `_json_sub_payment_url` — extract `subscription_payment` href from `links[]`

See `references/acp-api-operations.md` for implementation details.

## References

- `references/acp-api-operations.md` — Full curl recipes for every endpoint
- `references/oauth-token-setup.md` — Step-by-step manual token guide
- `references/product-catalog.md` — Offer IRI mappings from TTL sources

## Anti-Drift Protocol

⛔ **PRE-BUILD CHECK**: Before producing any curl command or output, re-read the
relevant operation section in `references/acp-api-operations.md`. Confirm headers,
body shape, and placeholder substitution. Build to pass — do not retro-fit.

## Examples

See `examples/checkout-flow.sh` and `examples/cart-flow.sh` for complete
executable workflows.

## Attribution

Derived from `acp_curl.sh` — reworked into composable curl recipes for agent use.