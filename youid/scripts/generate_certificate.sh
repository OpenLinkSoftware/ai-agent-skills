#!/bin/bash
#
# YouID Certificate Generator
# Generates a self-signed X.509 certificate bound to a WebID URI (SAN).
# Outputs .pem, .crt (DER), .p12 files and cert_data.json with extracted fields.
#
# Usage:
#   ./generate_certificate.sh <common_name> <webid_uri> [email] [org] [country] [state] [password] [output_dir] [validity_days]
#
# Output:
#   {output_dir}/cert.pem        — PEM-encoded X.509 certificate
#   {output_dir}/cert.crt        — DER-encoded X.509 certificate
#   {output_dir}/cert.p12        — PKCS#12 bundle (cert + key, password-protected)
#   {output_dir}/cert_data.json  — Extracted fields for template filling
#
set -euo pipefail

if [ $# -lt 2 ]; then
    echo "Usage: $0 <common_name> <webid_uri> [email] [org] [country] [state] [password] [output_dir] [validity_days]"
    exit 1
fi

CN="$1"
WEBID="$2"
EMAIL="${3:-}"
ORG="${4:-}"
COUNTRY="${5:-}"
STATE="${6:-}"
PASSWORD="${7:-youid}"
OUT_DIR="${8:-./youid-output}"
VALIDITY_DAYS="${9:-365}"

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

echo "Generating RSA 2048 key and X.509 certificate..."
echo "  Subject: ${SUBJ}"
echo "  WebID SAN: ${WEBID}"
echo "  Valid for: ${VALIDITY_DAYS} days ($((VALIDITY_DAYS / 365)) years)"

# Generate RSA private key
openssl genrsa -out "${OUT_DIR}/key.pem" 2048 2>/dev/null

# Create self-signed certificate with WebID as SAN
openssl req -new -x509 -key "${OUT_DIR}/key.pem" -out "${OUT_DIR}/cert.pem" \
    -days "${VALIDITY_DAYS}" \
    -subj "${SUBJ}" \
    -addext "subjectAltName=URI:${WEBID//#/\\#}" \
    -addext "basicConstraints=critical,CA:FALSE" \
    -addext "keyUsage=critical,digitalSignature,keyEncipherment" \
    -addext "nsComment=YouID Self-Signed Identity Certificate"

# Export DER format
openssl x509 -in "${OUT_DIR}/cert.pem" -outform DER -out "${OUT_DIR}/cert.crt"

# Export PKCS#12
openssl pkcs12 -export \
    -in "${OUT_DIR}/cert.pem" \
    -inkey "${OUT_DIR}/key.pem" \
    -out "${OUT_DIR}/cert.p12" \
    -passout "pass:${PASSWORD}" \
    -name "${CN}"

# Clean up intermediate key
rm -f "${OUT_DIR}/key.pem"

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
# openssl dates are like "Jun  9 00:00:00 2026 GMT" — parse with date on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    DATE_BEFORE=$(date -j -f "%b %d %T %Y %Z" "${NOT_BEFORE}" "+%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "${NOT_BEFORE}")
    DATE_AFTER=$(date -j -f "%b %d %T %Y %Z" "${NOT_AFTER}" "+%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "${NOT_AFTER}")
else
    DATE_BEFORE=$(date -d "${NOT_BEFORE}" "+%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "${NOT_BEFORE}")
    DATE_AFTER=$(date -d "${NOT_AFTER}" "+%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "${NOT_AFTER}")
fi

# Issuer and subject are the same for self-signed
ISSUER="${SUBJ}"

# Email hash (SHA-1 of email for foaf:mbox_sha1sum)
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
  "pdp_mail_sha1": "${PDP_MAIL_SHA1}"
}
EOF

echo ""
echo "=== Certificate Generated Successfully ==="
echo "  cert.pem:  ${OUT_DIR}/cert.pem"
echo "  cert.crt:  ${OUT_DIR}/cert.crt"
echo "  cert.p12:  ${OUT_DIR}/cert.p12 (password: ${PASSWORD})"
echo "  cert_data: ${OUT_DIR}/cert_data.json"
echo ""
echo "Fingerprint (SHA-1):   ${FINGERPRINT_HEX}"
echo "Fingerprint (SHA-256): ${FINGERPRINT_256_HEX}"
echo "NI URI:               ${NI_URI}"
echo "DI URI:               ${DI_URI}"
