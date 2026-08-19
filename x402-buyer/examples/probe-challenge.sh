#!/usr/bin/env bash
# Probe a URL for an x402 challenge WITHOUT paying, and decode it.
#
# Moves no money. Run this before every payment so the user sees the price,
# the network, and the pay-to address before agreeing to spend.
#
# Plain probe:
#   ./probe-challenge.sh "https://localhost:8443/DAV/data/paid.txt"
#
# WebID-TLS probe (port auto-rewritten to 5443, redirect followed, cert
# presented on every hop) -- pass a PKCS#12 cert as the second argument:
#   ./probe-challenge.sh "https://ods-qa.openlinksw.com/DAV/home/USER/file.pdf" /path/to/cert.p12

set -euo pipefail

URL="${1:?usage: probe-challenge.sh <url> [cert.p12]}"
P12="${2:-}"

CURL_CERT_ARGS=()
if [ -n "$P12" ]; then
  # WebID-TLS: the handshake lives on :5443, not :443 -- rewrite unless the
  # URL already names some other explicit port (a deliberate override).
  # See references/protocol.md's WebID-TLS section for why 443 is a dead end.
  if [[ "$URL" =~ ^(https://[^/:]+)(:([0-9]+))?(/.*)?$ ]]; then
    HOST_PART="${BASH_REMATCH[1]}"
    PORT_PART="${BASH_REMATCH[3]}"
    PATH_PART="${BASH_REMATCH[4]}"
    if [ -z "$PORT_PART" ] || [ "$PORT_PART" = "443" ]; then
      URL="${HOST_PART}:5443${PATH_PART}"
      echo "WebID-TLS: rewrote target port to 5443 -> $URL"
    fi
  fi

  : "${MTLS_PKCS12_PW:?export MTLS_PKCS12_PW with the PKCS#12 passphrase first}"
  CURL_CERT_ARGS=(--cert-type P12 --cert "$P12" --pass "$MTLS_PKCS12_PW")
fi

echo "== Response headers =="
# -L follows the WebID-TLS 302 -> ?k=... redirect; curl re-sends --cert on
# every hop of a -L follow, satisfying the "cert on every hop" requirement.
curl -sS -o /dev/null -D - -k -L "${CURL_CERT_ARGS[@]+"${CURL_CERT_ARGS[@]}"}" "$URL" || true

echo
echo "== Decoded PAYMENT-REQUIRED challenge =="
curl -sS -o /dev/null -D - -k -L "${CURL_CERT_ARGS[@]+"${CURL_CERT_ARGS[@]}"}" "$URL" \
  | grep -i '^payment-required:' \
  | cut -d: -f2- \
  | tr -d ' \r' \
  | base64 -d \
  || echo "(no PAYMENT-REQUIRED header -- not an x402 endpoint, or auth is required first)"
echo
