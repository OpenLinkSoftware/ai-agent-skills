#!/usr/bin/env bash
# Pay for OPL Shop's local DAV test file over x402.
#
# WebDAV requires Digest auth independently of the payment layer, and the local
# server uses a self-signed cert, so --secure is omitted.
#
# No key handling here: the script resolves it from the OS credential store
# (x402-buyer-evm-key / default) and prompts, without echoing, if it's absent.
# Store one first with:
#   security add-generic-password -s x402-buyer-evm-key -a default \
#       -T /usr/bin/security -w
#
#   ./local-dav.sh demo '<password>'

set -euo pipefail

DIGEST_USER="${1:?usage: local-dav.sh <digest-user> <digest-pass> [url] [key-account]}"
DIGEST_PASS="${2:?usage: local-dav.sh <digest-user> <digest-pass> [url] [key-account]}"
URL="${3:-https://localhost:8443/DAV/data/paid.txt}"
KEY_ACCOUNT="${4:-default}"

python3 "$(dirname "$0")/../scripts/x402_get.py" "$URL" \
    --key-account "$KEY_ACCOUNT" \
    --max-amount '$20' \
    --digest-user "$DIGEST_USER" \
    --digest-pass "$DIGEST_PASS"
