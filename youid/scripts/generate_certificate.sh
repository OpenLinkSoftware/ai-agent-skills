#!/bin/bash
#
# YouID Certificate Generator
# Generates an X.509 certificate bound to a WebID URI (Subject Alternative Name).
# Supports self-signed, Let's Encrypt, and ZeroSSL certificate types.
# Outputs .pem, .crt (DER), .p12 files and cert_data.json with extracted fields.
#
# Usage (self-signed, positional args — backward compatible):
#   ./generate_certificate.sh <common_name> <webid_uri> [email] [org] [country] [state] [password] [output_dir] [validity_days]
#
# Usage (named args, all modes):
#   ./generate_certificate.sh --mode self-signed|letsencrypt|zerossl \
#       --common-name <name> --webid <uri> \
#       [--email <email>] [--org <org>] [--country <country>] [--state <state>] \
#       [--password <password>] [--output-dir <dir>] [--validity-days <days>] \
#       [--acme-domain <domain>] [--acme-email <email>] [--zerossl-api-key <key>] \
#       [--acme-staging]
#
# Output:
#   {output_dir}/cert.pem        — PEM-encoded X.509 certificate
#   {output_dir}/cert.crt        — DER-encoded X.509 certificate
#   {output_dir}/cert.p12        — PKCS#12 bundle (cert + key, password-protected)
#   {output_dir}/cert_data.json  — Extracted fields for template filling
#   {output_dir}/ca.cer          — CA certificate (ACME modes only)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Source acme helper for ACME modes
source "$SCRIPT_DIR/acme_helper.sh"

# ---- Defaults ----
MODE="self-signed"
CN=""
WEBID=""
EMAIL=""
ORG=""
COUNTRY=""
STATE=""
PASSWORD="youid"
OUT_DIR="./youid-output"
VALIDITY_DAYS="365"
ACME_DOMAIN=""
ACME_EMAIL=""
ZEROSSL_API_KEY=""
ACME_STAGING=0

# ---- Parse arguments ----
if [ $# -eq 0 ]; then
    echo "Usage: $0 <common_name> <webid_uri> [options]"
    echo "       $0 --mode <type> --common-name <name> --webid <uri> [options]"
    exit 1
fi

# Check if first arg is a flag (named-arg mode)
if [[ "$1" == --* ]]; then
    # Named argument mode
    while [ $# -gt 0 ]; do
        case "$1" in
            --mode) MODE="$2"; shift 2 ;;
            --common-name) CN="$2"; shift 2 ;;
            --webid) WEBID="$2"; shift 2 ;;
            --email) EMAIL="$2"; shift 2 ;;
            --org) ORG="$2"; shift 2 ;;
            --country) COUNTRY="$2"; shift 2 ;;
            --state) STATE="$2"; shift 2 ;;
            --password) PASSWORD="$2"; shift 2 ;;
            --output-dir) OUT_DIR="$2"; shift 2 ;;
            --validity-days) VALIDITY_DAYS="$2"; shift 2 ;;
            --acme-domain) ACME_DOMAIN="$2"; shift 2 ;;
            --acme-email) ACME_EMAIL="$2"; shift 2 ;;
            --zerossl-api-key) ZEROSSL_API_KEY="$2"; shift 2 ;;
            --acme-staging) ACME_STAGING=1; shift ;;
            --help|-h) echo "Usage: ..."; exit 0 ;;
            *) echo "Unknown option: $1"; exit 1 ;;
        esac
    done
else
    # Positional argument mode (backward compatible, self-signed only)
    CN="$1"
    WEBID="$2"
    EMAIL="${3:-}"
    ORG="${4:-}"
    COUNTRY="${5:-}"
    STATE="${6:-}"
    PASSWORD="${7:-youid}"
    OUT_DIR="${8:-./youid-output}"
    VALIDITY_DAYS="${9:-365}"
    MODE="self-signed"
fi

# ---- Validation ----
if [ -z "$CN" ] || [ -z "$WEBID" ]; then
    echo "Error: --common-name and --webid are required"
    exit 1
fi

if [ "$MODE" != "self-signed" ]; then
    if [ -z "$ACME_DOMAIN" ]; then
        ACME_DOMAIN=$(echo "$WEBID" | python3 -c "
import sys, urllib.parse
uri = sys.stdin.read().strip()
parsed = urllib.parse.urlparse(uri)
host = parsed.hostname or ''
print(host)
" 2>/dev/null || echo "")
        if [ -z "$ACME_DOMAIN" ]; then
            echo "Error: --acme-domain is required for ACME modes (could not parse from WebID)"
            exit 1
        fi
        echo "  ACME domain inferred from WebID: $ACME_DOMAIN"
    fi
    if [ "$MODE" = "zerossl" ] && [ -z "$ZEROSSL_API_KEY" ]; then
        echo "Error: --zerossl-api-key is required for ZeroSSL mode"
        exit 1
    fi
    if [ -z "$ACME_EMAIL" ]; then
        ACME_EMAIL="${EMAIL:-contact@${ACME_DOMAIN}}"
        echo "  ACME email inferred: $ACME_EMAIL"
    fi
fi

mkdir -p "$OUT_DIR"

# Build subject string
SUBJ="/CN=${CN}"
if [ -n "$EMAIL" ]; then
    SUBJ="${SUBJ}/emailAddress=${EMAIL}"
fi
if [ -n "$ORG" ]; then
    SUBJ="${SUBJ}/O=${ORG}"
fi
if [ -n "$COUNTRY" ]; then
    SUBJ="${SUBJ}/C=${COUNTRY}"
fi
if [ -n "$STATE" ]; then
    SUBJ="${SUBJ}/ST=${STATE}"
fi

echo "Generating X.509 certificate (mode: ${MODE})..."
echo "  Subject: ${SUBJ}"
echo "  WebID SAN: ${WEBID}"
echo "  Valid for: ${VALIDITY_DAYS} days ($((VALIDITY_DAYS / 365)) years)"

CA_CERT_URL=""

case "$MODE" in
    self-signed)
        # ---- Self-signed certificate (original behavior) ----
        echo "  Mode: self-signed"

        openssl genrsa -out "${OUT_DIR}/key.pem" 2048 2>/dev/null

        openssl req -new -x509 -key "${OUT_DIR}/key.pem" -out "${OUT_DIR}/cert.pem" \
            -days "${VALIDITY_DAYS}" \
            -subj "${SUBJ}" \
            -addext "subjectAltName=URI:${WEBID//#/\\#}" \
            -addext "basicConstraints=critical,CA:FALSE" \
            -addext "keyUsage=critical,digitalSignature,keyEncipherment" \
            -addext "nsComment=YouID Self-Signed Identity Certificate"

        ISSUER="${SUBJ}"
        ;;

    letsencrypt|zerossl)
        # ---- CA-signed certificate via ACME ----
        echo "  Mode: ${MODE}"

        local acme_server
        acme_server=$(get_acme_server "$MODE" "$ACME_STAGING")

        if [ "$ACME_STAGING" = "1" ]; then
            echo "  Using LET'S ENCRYPT STAGING server (test certificates)"
        fi

        # Ensure acme.sh is installed
        ensure_acme_sh "$ACME_EMAIL"

        # Generate RSA key and CSR with DNS + URI SANs
        generate_csr \
            "${OUT_DIR}/key.pem" \
            "${OUT_DIR}/csr.pem" \
            "$SUBJ" \
            "$ACME_DOMAIN" \
            "$WEBID"

        # Handle ZeroSSL EAB
        local eab_kid=""
        local eab_hmac=""
        if [ "$MODE" = "zerossl" ] && [ -n "$ZEROSSL_API_KEY" ]; then
            local eab_response
            eab_response=$(zerossl_fetch_eab "$ZEROSSL_API_KEY")
            eab_kid=$(echo "$eab_response" | cut -d: -f1)
            eab_hmac=$(echo "$eab_response" | cut -d: -f2-)
            echo "  ZeroSSL EAB credentials obtained"
        fi

        # Sign CSR via ACME
        run_acme_sign "$ACME_DOMAIN" "${OUT_DIR}/csr.pem" \
            "$eab_kid" "$eab_hmac" "$acme_server"

        # Download signed certificates
        download_signed_cert "$ACME_DOMAIN" "$OUT_DIR"

        # Clean up acme.sh domain data
        acme_cleanup "$ACME_DOMAIN"

        # Remove CSR (intermediate artifact)
        rm -f "${OUT_DIR}/csr.pem"

        # Extract issuer from CA-signed cert
        ISSUER=$(openssl x509 -in "${OUT_DIR}/cert.pem" -issuer -noout | sed 's/issuer=//' | sed 's/^ *//')

        # Set CA cert URL based on issuer
        if echo "$ISSUER" | grep -qi "Let's Encrypt"; then
            CA_CERT_URL="https://letsencrypt.org/certs/2024/"
        elif echo "$ISSUER" | grep -qi "ZeroSSL"; then
            CA_CERT_URL="https://zerossl.com/resources/"
        fi

        # NOTE: key.pem is kept (not deleted) for PKCS#12 generation below
        ;;

    *)
        echo "Error: unknown mode '$MODE'. Use: self-signed, letsencrypt, or zerossl"
        exit 1
        ;;
esac

# ---- Post-generation: DER, PKCS#12, and cert data extraction ----
# (shared by all modes)

# Export DER format
openssl x509 -in "${OUT_DIR}/cert.pem" -outform DER -out "${OUT_DIR}/cert.crt"

# Export PKCS#12 (key.pem exists for self-signed; kept for ACME modes)
if [ -f "${OUT_DIR}/key.pem" ]; then
    openssl pkcs12 -export \
        -in "${OUT_DIR}/cert.pem" \
        -inkey "${OUT_DIR}/key.pem" \
        -out "${OUT_DIR}/cert.p12" \
        -passout "pass:${PASSWORD}" \
        -name "${CN}"
    # Clean up private key after PKCS#12 bundle
    rm -f "${OUT_DIR}/key.pem"
fi

echo "Extracting certificate data..."

# Extract fingerprints
FINGERPRINT_HEX=$(openssl x509 -in "${OUT_DIR}/cert.pem" -fingerprint -sha1 -noout | cut -d= -f2 | tr '[:upper:]' '[:upper:]')
FINGERPRINT_256_HEX=$(openssl x509 -in "${OUT_DIR}/cert.pem" -fingerprint -sha256 -noout | cut -d= -f2 | tr '[:upper:]' '[:upper:]')
FINGERPRINT_COLON="$FINGERPRINT_HEX"

# Fingerprint without colons
FP_NOCOLON=$(echo "$FINGERPRINT_HEX" | tr -d ':')
FP_256_NOCOLON=$(echo "$FINGERPRINT_256_HEX" | tr -d ':')

# Compute NI URI (base64url-encoded SHA-256 of DER)
DER_SHA256_B64=$(openssl x509 -in "${OUT_DIR}/cert.pem" -outform DER | openssl dgst -sha256 -binary | base64 | tr '+/' '-_' | tr -d '=')
NI_URI="ni:///sha-256;${DER_SHA256_B64}"

# Compute DI URI
DI_URI="urn:di:sha-256;${FP_256_NOCOLON}"

# vCard digest URI
VCARD_DIGEST_URI="data:text/plain;sha-256;${FP_256_NOCOLON}"

# Modulus (hex)
MODULUS=$(openssl x509 -in "${OUT_DIR}/cert.pem" -modulus -noout | sed 's/Modulus=//')

# Exponent (extract from cert, default 65537 for RSA)
EXPONENT=$(openssl x509 -in "${OUT_DIR}/cert.pem" -text -noout | awk '/Exponent:/ {print $2}' || echo "65537")

# Serial number
SERIAL=$(openssl x509 -in "${OUT_DIR}/cert.pem" -serial -noout | cut -d= -f2 | tr '[:upper:]' '[:upper:]')

# Dates (ISO 8601)
NOT_BEFORE=$(openssl x509 -in "${OUT_DIR}/cert.pem" -dates -noout | grep notBefore | cut -d= -f2)
NOT_AFTER=$(openssl x509 -in "${OUT_DIR}/cert.pem" -dates -noout | grep notAfter | cut -d= -f2)

# Convert dates to ISO 8601
if [[ "$OSTYPE" == "darwin"* ]]; then
    DATE_BEFORE=$(date -j -f "%b %d %T %Y %Z" "${NOT_BEFORE}" "+%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "${NOT_BEFORE}")
    DATE_AFTER=$(date -j -f "%b %d %T %Y %Z" "${NOT_AFTER}" "+%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "${NOT_AFTER}")
else
    DATE_BEFORE=$(date -d "${NOT_BEFORE}" "+%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "${NOT_BEFORE}")
    DATE_AFTER=$(date -d "${NOT_AFTER}" "+%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "${NOT_AFTER}")
fi

# Email hash
if [ -n "$EMAIL" ]; then
    PDP_MAIL_SHA1=$(printf "%s" "$EMAIL" | openssl dgst -sha1 | cut -d' ' -f2)
else
    PDP_MAIL_SHA1=""
fi

cat > "${OUT_DIR}/cert_data.json" << EOF
{
  "subj_name": $(echo "$CN" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read().strip()))'),
  "subj_email": $(echo "$EMAIL" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read().strip()))'),
  "subj_email_mailto": "mailto:${EMAIL}",
  "subj_email_mailto_href": "<a href=\"mailto:${EMAIL}\">${EMAIL}</a>",
  "subj_org": $(echo "$ORG" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read().strip()))'),
  "subj_country": $(echo "$COUNTRY" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read().strip()))'),
  "subj_state": $(echo "$STATE" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read().strip()))'),
  "webid": $(echo "$WEBID" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read().strip()))'),
  "modulus": "${MODULUS}",
  "exponent": "${EXPONENT}",
  "serial": "${SERIAL}",
  "subject": "${SUBJ}",
  "issuer": "${ISSUER}",
  "date_before": "${DATE_BEFORE}",
  "date_after": "${DATE_AFTER}",
  "fingerprint_hex": "${FINGERPRINT_HEX}",
  "fingerprint_256_hex": "${FINGERPRINT_256_HEX}",
  "fingerprint_ni": "${NI_URI}",
  "fingerprint_di": "${DI_URI}",
  "fingerprint_colon": "${FINGERPRINT_COLON}",
  "vcard_digest_uri": "${VCARD_DIGEST_URI}",
  "pdp_mail_sha1": "${PDP_MAIL_SHA1}",
  "ca_cert_url": "${CA_CERT_URL}",
  "cert_type": "${MODE}"
}
EOF

echo ""
echo "=== Certificate Generated Successfully ==="
echo "  Mode:    ${MODE}"
echo "  cert.pem:  ${OUT_DIR}/cert.pem"
echo "  cert.crt:  ${OUT_DIR}/cert.crt"
echo "  cert.p12:  ${OUT_DIR}/cert.p12 (password: ${PASSWORD})"
echo "  cert_data: ${OUT_DIR}/cert_data.json"
if [ "$MODE" != "self-signed" ] && [ -f "${OUT_DIR}/ca.cer" ]; then
    echo "  ca.cer:    ${OUT_DIR}/ca.cer"
fi
echo ""
echo "Fingerprint (SHA-1):   ${FINGERPRINT_HEX}"
echo "Fingerprint (SHA-256): ${FINGERPRINT_256_HEX}"
echo "NI URI:               ${NI_URI}"
echo "DI URI:               ${DI_URI}"
if [ -n "$CA_CERT_URL" ]; then
    echo "CA Cert URL:          ${CA_CERT_URL}"
fi
