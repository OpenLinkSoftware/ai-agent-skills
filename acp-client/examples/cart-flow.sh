#!/usr/bin/env bash
# ACP Client — Full Cart Lifecycle Example
# Usage: ACP_AUTH_TOKEN=... ACP_ITEM_ID=... ./cart-flow.sh

set -euo pipefail

BASE_URL="${ACP_BASE_URL:-https://ods-qa.openlinksw.com/acp}"
API_VERSION="${ACP_API_VERSION:-2026-01-30}"
AUTH_TOKEN="${ACP_AUTH_TOKEN:?ACP_AUTH_TOKEN required}"
ACP_ITEM_ID="${ACP_ITEM_ID:?ACP_ITEM_ID required}"

# JSON helper (awk fallback when jq is unavailable)
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

echo "=== Step 1: Create cart ===" >&2
resp=$(curl -sS -X POST "${BASE_URL}/carts" \
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
)

cart_id=$(printf '%s' "$resp" | _json_str id)
echo "Cart ID: ${cart_id}" >&2

echo "=== Step 2: Get cart ===" >&2
curl -sS -X GET "${BASE_URL}/carts/${cart_id}" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}"
echo

echo "=== Step 3: Update cart (qty 1 -> 3) ===" >&2
curl -sS -X PUT "${BASE_URL}/carts/${cart_id}" \
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
echo

echo "=== Step 4: Cancel cart ===" >&2
curl -sS -X POST "${BASE_URL}/carts/${cart_id}/cancel" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "API-Version: ${API_VERSION}" \
  -H "Idempotency-Key: $(uuidgen | tr '[:upper:]' '[:lower:]')" \
  -H "Content-Type: application/json" \
  -d '{}'
echo

echo "=== Done ===" >&2