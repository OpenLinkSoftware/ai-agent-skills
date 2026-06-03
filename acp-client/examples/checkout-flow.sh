#!/usr/bin/env bash
# ACP Client — Full Checkout Flow Example
# Usage: ACP_AUTH_TOKEN=... STRIPE_API_KEY=... ACP_ITEM_ID=... ./checkout-flow.sh

set -euo pipefail

BASE_URL="${ACP_BASE_URL:-https://ods-qa.openlinksw.com/acp}"
API_VERSION="${ACP_API_VERSION:-2026-01-30}"
AUTH_TOKEN="${ACP_AUTH_TOKEN:?ACP_AUTH_TOKEN required}"
ACP_ITEM_ID="${ACP_ITEM_ID:?ACP_ITEM_ID required}"
STRIPE_API_KEY="${STRIPE_API_KEY:?STRIPE_API_KEY required}"
STRIPE_PAYMENT_METHOD="${STRIPE_PAYMENT_METHOD:-pm_card_visa}"
STRIPE_SPT_CURRENCY="${STRIPE_SPT_CURRENCY:-usd}"
REQ_ID="req_$(date +%s)"

# JSON helpers (awk fallback when jq is unavailable)
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

_json_sub_payment_url() {
  if command -v jq &>/dev/null; then
    jq -r '(.links // [])[] | select(.rel == "subscription_payment") | .href' 2>/dev/null | head -1
  else
    awk -F'"' '
      {
        for (i=1; i<=NF; i++) {
          if ($i == "subscription_payment") { found=1 }
          if (found && $i == "href") { print $(i+2); exit }
        }
      }
    '
  fi
}

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

checkout_id=$(printf '%s' "$resp" | _json_str id)
echo "Checkout ID: ${checkout_id}" >&2

echo "=== Step 2: Get checkout total ===" >&2
total=$(printf '%s' "$resp" | _json_total) || {
  total=$(curl -sS -X GET "${BASE_URL}/checkout_sessions/${checkout_id}" \
    -H "Authorization: Bearer ${AUTH_TOKEN}" \
    -H "API-Version: ${API_VERSION}" \
    -H "Request-Id: ${REQ_ID}" | _json_total)
}
echo "Total: ${total} minor units" >&2

echo "=== Step 3: Fetch Stripe SPT ===" >&2
if date -v+1H +%s 2>/dev/null; then
  expires_at=$(date -v+1H +%s)
else
  expires_at=$(date -d '+1 hour' +%s)
fi
spt=$(curl -sS -X POST "https://api.stripe.com/v1/test_helpers/shared_payment/granted_tokens" \
  -u "${STRIPE_API_KEY}" \
  -d "payment_method=${STRIPE_PAYMENT_METHOD}" \
  -d "usage_limits[currency]=${STRIPE_SPT_CURRENCY}" \
  -d "usage_limits[max_amount]=${total}" \
  -d "usage_limits[expires_at]=${expires_at}" | _json_str id)
echo "SPT: ${spt}" >&2

echo "=== Step 4: Complete checkout ===" >&2
resp=$(curl -sS -X POST "${BASE_URL}/checkout_sessions/${checkout_id}/complete" \
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
)
printf '%s\n' "$resp"

# Check for subscription payment link
sub_url=$(printf '%s' "$resp" | _json_sub_payment_url)
if [ -n "$sub_url" ]; then
  echo >&2
  echo "============================================================" >&2
  echo "  SUBSCRIPTION PAYMENT REQUIRED" >&2
  echo "  Open the link below to complete payment and activate:" >&2
  echo "  ${sub_url}" >&2
  echo "============================================================" >&2
fi

echo "=== Done ===" >&2