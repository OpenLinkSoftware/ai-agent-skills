# ACP API Operations Reference

Compositional `curl` recipes for every ACP endpoint. Derived from `acp_curl.sh`.
All recipes use these common headers and environment variables:

```bash
BASE_URL="${ACP_BASE_URL:-https://ods-qa.openlinksw.com/acp}"
API_VERSION="${ACP_API_VERSION:-2026-01-30}"
AUTH_TOKEN="${ACP_AUTH_TOKEN}"
REQ_ID="req_$(date +%s)"
```

**Standard headers for every request:**
```bash
-H "Authorization: Bearer ${AUTH_TOKEN}" \
-H "API-Version: ${API_VERSION}" \
-H "Request-Id: ${REQ_ID}" \
-H "Content-Type: application/json"
```

For `POST`/`PUT` operations that mutate state, also include:
```bash
-H "Idempotency-Key: $(uuidgen | tr '[:upper:]' '[:lower:]')"
```

---

## JSON Helpers

### `_json_str` — extract a top-level string field

```bash
_json_str() {
  local field="$1"
  if command -v jq &>/dev/null; then
    jq -r ".$field"
  else
    awk -F'"' -v f="$field" '
      { for (i=1; i<=NF; i++) if ($i == f) { print $(i+2); exit } }
    '
  fi
}
```

### `_json_total` — extract `amount` where `type=="total"`

```bash
_json_total() {
  if command -v jq &>/dev/null; then
    jq -r '[.totals[] | select(.type == "total") | .amount] | first'
  else
    awk '
      match($0, /"type":"total","amount":[0-9]+/) {
        s = substr($0, RSTART, RLENGTH)
        match(s, /[0-9]+$/)
        print substr(s, RSTART, RLENGTH)
        found = 1; exit
      }
      /"type"[[:space:]]*:[[:space:]]*"total"/ { flag = 1 }
      flag && /"amount"[[:space:]]*:/ {
        match($0, /[0-9]+/)
        print substr($0, RSTART, RLENGTH)
        found = 1; exit
      }
      END { if (!found) exit 1 }
    '
  fi
}
```

---

## Checkout Sessions

### Create Checkout

```bash
curl -sS -X POST "${BASE_URL}/checkout_sessions" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}" \
  -H "Idempotency-Key: $(uuidgen | tr '[:upper:]' '[:lower:]')" \
  -H "Request-Id: ${REQ_ID}" \
  -H "Content-Type: application/json" \
  -d @- <<JSON
{
  "items": [
    { "id": "${ACP_ITEM_ID}", "quantity": 1 }
  ],
  "currency": "usd",
  "capabilities": {}
}
JSON
```

**Response fields to capture:** `id` (checkout session ID), `totals[]`.

### Update Checkout

```bash
curl -sS -X POST "${BASE_URL}/checkout_sessions/${CHECKOUT_ID}" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}" \
  -H "Idempotency-Key: $(uuidgen | tr '[:upper:]' '[:lower:]')" \
  -H "Request-Id: ${REQ_ID}" \
  -H "Content-Type: application/json" \
  -d @- <<JSON
{
  "items": [
    { "id": "${ACP_ITEM_ID}", "quantity": 2 }
  ]
}
JSON
```

### Get Checkout Total

```bash
curl -sS -X GET "${BASE_URL}/checkout_sessions/${CHECKOUT_ID}" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}" \
  -H "Request-Id: ${REQ_ID}"
```

Pipe through `_json_total` to extract the payable amount in minor units.

### Complete Checkout — Stripe SPT

Requires a Stripe Shared Payment Token (SPT):

```bash
# 1. Fetch total
TOTAL=$(curl -sS -X GET "${BASE_URL}/checkout_sessions/${CHECKOUT_ID}" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}" \
  -H "Request-Id: ${REQ_ID}" | _json_total)

# 2. Fetch test SPT scoped to total
SPT=$(curl -sS -X POST "https://api.stripe.com/v1/test_helpers/shared_payment/granted_tokens" \
  -u "${STRIPE_API_KEY}" \
  -d "payment_method=${STRIPE_PAYMENT_METHOD}" \
  -d "usage_limits[currency]=${STRIPE_SPT_CURRENCY:-usd}" \
  -d "usage_limits[max_amount]=${TOTAL}" \
  -d "usage_limits[expires_at]=${STRIPE_SPT_EXPIRES_AT}" | _json_str id)

# 3. Complete checkout
curl -sS -X POST "${BASE_URL}/checkout_sessions/${CHECKOUT_ID}/complete" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}" \
  -H "Idempotency-Key: $(uuidgen | tr '[:upper:]' '[:lower:]')" \
  -H "Request-Id: ${REQ_ID}" \
  -H "Content-Type: application/json" \
  -d @- <<JSON
{
  "payment_data": {
    "handler_id": "card_tokenized",
    "instrument": {
      "type": "card",
      "credential": {
        "type": "spt",
        "token": "${SPT}"
      }
    }
  }
}
JSON
```

### Complete Checkout — Account Balance

If the user has sufficient ACP account balance, complete without Stripe:

```bash
curl -sS -X POST "${BASE_URL}/checkout_sessions/${CHECKOUT_ID}/complete" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}" \
  -H "Idempotency-Key: $(uuidgen | tr '[:upper:]' '[:lower:]')" \
  -H "Request-Id: ${REQ_ID}" \
  -H "Content-Type: application/json" \
  -d @- <<JSON
{
  "payment_data": {
    "handler_id": "balance",
    "instrument": {
      "type": "balance"
    }
  }
}
JSON
```

### Cancel Checkout

```bash
curl -sS -X POST "${BASE_URL}/checkout_sessions/${CHECKOUT_ID}/cancel" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}" \
  -H "Idempotency-Key: $(uuidgen | tr '[:upper:]' '[:lower:]')" \
  -H "Request-Id: ${REQ_ID}" \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "intent_trace": {
    "reason_code": "buyer_cancelled",
    "trace_summary": "Customer decided not to purchase"
  }
}
JSON
```

---

## Orders

### Get Order

```bash
curl -sS -X GET "${BASE_URL}/orders/${ORDER_ID}" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}" \
  -H "Request-Id: ${REQ_ID}"
```

---

## Carts

### Create Cart

```bash
curl -sS -X POST "${BASE_URL}/carts" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}" \
  -H "Idempotency-Key: $(uuidgen | tr '[:upper:]' '[:lower:]')" \
  -H "Content-Type: application/json" \
  -d @- <<JSON
{
  "line_items": [
    { "id": "${ACP_ITEM_ID}", "quantity": 1 }
  ],
  "buyer": {
    "email": "buyer@example.com"
  }
}
JSON
```

### Get Cart

```bash
curl -sS -X GET "${BASE_URL}/carts/${CART_ID}" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}"
```

### Update Cart

```bash
curl -sS -X PUT "${BASE_URL}/carts/${CART_ID}" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}" \
  -H "Content-Type: application/json" \
  -d @- <<JSON
{
  "line_items": [
    { "id": "${ACP_ITEM_ID}", "quantity": 3 }
  ],
  "buyer": {
    "email": "buyer@example.com"
  }
}
JSON
```

### Cancel Cart

```bash
curl -sS -X POST "${BASE_URL}/carts/${CART_ID}/cancel" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}" \
  -H "Idempotency-Key: $(uuidgen | tr '[:upper:]' '[:lower:]')" \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Stripe Test SPT

Generate a test Shared Payment Token directly from Stripe:

```bash
_default_expires_at() {
  if date -v+1H +%s 2>/dev/null; then :; else date -d '+1 hour' +%s; fi
}

STRIPE_SPT_EXPIRES_AT="${STRIPE_SPT_EXPIRES_AT:-$(_default_expires_at)}"

curl -sS -X POST "https://api.stripe.com/v1/test_helpers/shared_payment/granted_tokens" \
  -u "${STRIPE_API_KEY}" \
  -d "payment_method=${STRIPE_PAYMENT_METHOD:-pm_card_visa}" \
  -d "usage_limits[currency]=${STRIPE_SPT_CURRENCY:-usd}" \
  -d "usage_limits[max_amount]=${AMOUNT:-${STRIPE_SPT_MAX_AMOUNT:-1000}}" \
  -d "usage_limits[expires_at]=${STRIPE_SPT_EXPIRES_AT}"
```

Pipe through `_json_str id` to extract the token.

---

## Full Purchase Flow (Intent: "I want to purchase X")

```bash
#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${ACP_BASE_URL:-https://ods-qa.openlinksw.com/acp}"
API_VERSION="${ACP_API_VERSION:-2026-01-30}"
AUTH_TOKEN="${ACP_AUTH_TOKEN}"
ACP_ITEM_ID="${ACP_ITEM_ID}"
STRIPE_API_KEY="${STRIPE_API_KEY}"
REQ_ID="req_$(date +%s)"

# 1. Create checkout
echo "=== Creating checkout ===" >&2
resp=$(curl -sS -X POST "${BASE_URL}/checkout_sessions" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}" \
  -H "Idempotency-Key: $(uuidgen | tr '[:upper:]' '[:lower:]')" \
  -H "Request-Id: ${REQ_ID}" \
  -H "Content-Type: application/json" \
  -d @- <<JSON
{ "items": [{ "id": "${ACP_ITEM_ID}", "quantity": 1 }], "currency": "usd", "capabilities": {} }
JSON
)
checkout_id=$(printf '%s' "$resp" | jq -r '.id')
echo "Checkout ID: ${checkout_id}" >&2

# 2. Get total
echo "=== Fetching total ===" >&2
total=$(curl -sS -X GET "${BASE_URL}/checkout_sessions/${checkout_id}" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}" \
  -H "Request-Id: ${REQ_ID}" | jq -r '[.totals[] | select(.type == "total") | .amount] | first')
echo "Total: ${total} minor units" >&2

# 3. Get Stripe SPT
echo "=== Fetching Stripe SPT ===" >&2
spt=$(curl -sS -X POST "https://api.stripe.com/v1/test_helpers/shared_payment/granted_tokens" \
  -u "${STRIPE_API_KEY}" \
  -d "payment_method=pm_card_visa" \
  -d "usage_limits[currency]=usd" \
  -d "usage_limits[max_amount]=${total}" \
  -d "usage_limits[expires_at]=$(date -v+1H +%s 2>/dev/null || date -d '+1 hour' +%s)" | jq -r '.id')
echo "SPT: ${spt}" >&2

# 4. Complete checkout
echo "=== Completing checkout ===" >&2
curl -sS -X POST "${BASE_URL}/checkout_sessions/${checkout_id}/complete" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}" \
  -H "Idempotency-Key: $(uuidgen | tr '[:upper:]' '[:lower:]')" \
  -H "Request-Id: ${REQ_ID}" \
  -H "Content-Type: application/json" \
  -d @- <<JSON
{
  "payment_data": {
    "handler_id": "card_tokenized",
    "instrument": {
      "type": "card",
      "credential": { "type": "spt", "token": "${spt}" }
    }
  }
}
JSON
```

---

## Error Reference

| HTTP Status | Meaning | Action |
|---|---|---|
| `401 Unauthorized` | Bearer token missing/invalid | Direct user to OAuth applications page |
| `404 Not Found` | Resource ID does not exist | Verify ID spelling |
| `409 Conflict` | Idempotency key collision | Retry with new UUID |
| `422 Unprocessable Entity` | Validation error | Report field-level errors from body |
| Stripe `4xx/5xx` | Payment setup failure | Report Stripe error message |
