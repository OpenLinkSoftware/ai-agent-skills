#!/usr/bin/env bash
# ACP Client — Full Checkout Flow Example
# Usage: ACP_AUTH_TOKEN=... STRIPE_API_KEY=... ACP_ITEM_ID=... ./checkout-flow.sh

set -euo pipefail

BASE_URL="${ACP_BASE_URL:-https://ods-qa.openlinksw.com/acp}"
API_VERSION="${ACP_API_VERSION:-2026-01-30}"
AUTH_TOKEN="${ACP_AUTH_TOKEN:?ACP_AUTH_TOKEN required}"
ACP_ITEM_ID="${ACP_ITEM_ID:?ACP_ITEM_ID required}"
STRIPE_API_KEY="${STRIPE_API_KEY:?STRIPE_API_KEY required}"
REQ_ID="req_$(date +%s)"

echo "=== Step 1: Create checkout ===" >&2
resp=$(curl -sS -X POST "${BASE_URL}/checkout_sessions" \
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
)

checkout_id=$(printf '%s' "$resp" | jq -r '.id')
echo "Checkout ID: ${checkout_id}" >&2

echo "=== Step 2: Get checkout total ===" >&2
total=$(curl -sS -X GET "${BASE_URL}/checkout_sessions/${checkout_id}" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}" \
  -H "Request-Id: ${REQ_ID}" | jq -r '[.totals[] | select(.type == "total") | .amount] | first')
echo "Total: ${total} minor units" >&2

echo "=== Step 3: Fetch Stripe SPT ===" >&2
expires_at=$(date -v+1H +%s 2>/dev/null || date -d '+1 hour' +%s)
spt=$(curl -sS -X POST "https://api.stripe.com/v1/test_helpers/shared_payment/granted_tokens" \
  -u "${STRIPE_API_KEY}" \
  -d "payment_method=pm_card_visa" \
  -d "usage_limits[currency]=usd" \
  -d "usage_limits[max_amount]=${total}" \
  -d "usage_limits[expires_at]=${expires_at}" | jq -r '.id')
echo "SPT: ${spt}" >&2

echo "=== Step 4: Complete checkout ===" >&2
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
      "credential": {
        "type": "spt",
        "token": "${spt}"
      }
    }
  }
}
JSON

echo "=== Done ===" >&2
