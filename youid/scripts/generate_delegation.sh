#!/bin/bash
#
# YouID Delegation Generator
# Generates:
#   1. SPARQL UPDATE patch for delegator's profile
#   2. declarativeNetRequest rule JSON for Chrome extension header injection
#   3. Deployment summary with curl examples
#
# Usage:
#   ./generate_delegation.sh -d <delegator-webid> -e <delegate-webid> -r <role> [-k <delegate-cert.pem>] [-o <output-dir>]
#
# Role: identify | inform | consult | authority
#
# IMPORTANT (fixed 2026-09-13): the SPARQL patch below republishes the
# delegate's own cert:key (RSA modulus+exponent) under the delegator's
# profile, not just the hasIdentityDelegate/onBehalfOf relation triples.
# Confirmed live that those relation triples alone are NOT independently
# verified by any tested resource-server authorization path (WAC/ACL, MPP
# entitlement, or a remote WebID-TLS verification service) — a standard
# verifier checks cert:key, so a delegation patch that only asserts the
# relationship silently does nothing for actual delegated access. See
# agent-rdf-memory/howto/webid-tls-on-behalf-of-delegation-no-effect-incident-report
# and generate_identity.sh's Step 6 gate, which now enforces this same
# requirement at identity-generation time.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
YOUID_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

DELEGATOR=""
DELEGATE=""
ROLE=""
DELEGATE_CERT=""
OUT_DIR="$(pwd)/delegation-output"

while getopts "d:e:r:k:o:h" opt; do
    case $opt in
        d) DELEGATOR="$OPTARG" ;;
        e) DELEGATE="$OPTARG" ;;
        r) ROLE="$OPTARG" ;;
        k) DELEGATE_CERT="$OPTARG" ;;
        o) OUT_DIR="$OPTARG" ;;
        h) echo "Usage: $0 -d <delegator-webid> -e <delegate-webid> -r <role> [-k <delegate-cert.pem>] [-o <output-dir>]"
           echo ""
           echo "Required:"
           echo "  -d  Delegator WebID/NetID (the entity granting authority)"
           echo "  -e  Delegate WebID/NetID (the entity acting on-behalf-of)"
           echo "  -r  Delegation role: identify | inform | consult | authority"
           echo ""
           echo "Optional:"
           echo "  -k  Delegate's PEM certificate (or path readable by openssl) — its RSA"
           echo "      public key is extracted and republished under the delegator's profile."
           echo "      Without this, the script attempts to dereference the delegate's own"
           echo "      WebID and reuse its already-published cert:key; if that also fails,"
           echo "      the generated patch omits cert:key and prints a loud warning, since"
           echo "      a delegation patch without it will not actually grant delegated access."
           echo "  -o  Output directory (default: ./delegation-output)"
           echo ""
           echo "Role definitions:"
           echo "  identify   - Delegate may identify as the delegator for identification purposes"
           echo "  inform     - Delegate may be informed on behalf of the delegator"
           echo "  consult    - Delegate may be consulted on behalf of the delegator"
           echo "  authority  - Delegate has full authority to act on behalf of the delegator"
           exit 0 ;;
        *) echo "Unknown option -$opt"; exit 1 ;;
    esac
done

if [ -z "$DELEGATOR" ] || [ -z "$DELEGATE" ] || [ -z "$ROLE" ]; then
    echo "Error: -d (delegator), -e (delegate), and -r (role) are required"
    echo "Usage: $0 -d <delegator> -e <delegate> -r <role>"
    exit 1
fi

case "$ROLE" in
    identify|inform|consult|authority) ;;
    *) echo "Error: role must be one of: identify, inform, consult, authority"; exit 1 ;;
esac

mkdir -p "$OUT_DIR"
ROLE_UPPER="$(echo "$ROLE" | tr '[:lower:]' '[:upper:]')"

echo "=== Generating Delegation Bundle ==="
echo "  Delegator: $DELEGATOR"
echo "  Delegate:  $DELEGATE"
echo "  Role:      $ROLE"

# Step 0: Resolve the delegate's RSA public key (modulus + exponent).
# This is what actually makes delegation work for a standard WebID-TLS
# verifier — the hasIdentityDelegate/onBehalfOf triples alone are not
# independently checked by any tested resource-server authorization path.
echo "=== Step 0: Resolve Delegate's Public Key ==="
KEY_MODULUS=""
KEY_EXPONENT="65537"
if [ -n "$DELEGATE_CERT" ]; then
    if [ -f "$DELEGATE_CERT" ]; then
        KEY_MODULUS="$(openssl x509 -noout -modulus -in "$DELEGATE_CERT" 2>/dev/null | sed 's/Modulus=//')"
        if [ -n "$KEY_MODULUS" ]; then
            echo "  Extracted modulus from -k $DELEGATE_CERT (${KEY_MODULUS:0:24}...)"
        else
            echo "  WARNING: could not extract a modulus from $DELEGATE_CERT — is it a valid PEM cert?"
        fi
    else
        echo "  WARNING: -k $DELEGATE_CERT not found on disk"
    fi
else
    echo "  No -k given — attempting to dereference the delegate's own WebID for its published cert:key..."
    DELEGATE_PROFILE_URL="${DELEGATE%%#*}"
    KEY_MODULUS="$(curl -sS -L "$DELEGATE_PROFILE_URL" 2>/dev/null \
        | grep -o 'cert:modulus[^;.]*' | grep -o '"[A-Fa-f0-9]*"' | head -1 | tr -d '"')"
    if [ -n "$KEY_MODULUS" ]; then
        echo "  Found published cert:modulus at $DELEGATE_PROFILE_URL (${KEY_MODULUS:0:24}...)"
    else
        echo "  Could not resolve a cert:modulus from $DELEGATE_PROFILE_URL either."
    fi
fi
if [ -z "$KEY_MODULUS" ]; then
    echo ""
    echo "  *** WARNING: no delegate public key resolved. The generated SPARQL patch will"
    echo "  *** only assert hasIdentityDelegate/onBehalfOf — confirmed live that this alone"
    echo "  *** does NOT grant delegated resource access on any tested server. Supply -k"
    echo "  *** with the delegate's cert.pem, or publish the delegate's own WebID profile"
    echo "  *** first, then re-run this script."
    echo ""
fi
KEY_MODULUS="$(echo "$KEY_MODULUS" | tr '[:lower:]' '[:upper:]')"

# Step 1: Generate SPARQL UPDATE patch
echo "=== Step 1: SPARQL UPDATE Patch ==="
SPARQL_FILE="$OUT_DIR/delegation.sparql"

if [ -n "$KEY_MODULUS" ]; then
    DELEGATE_KEY_IRI="${DELEGATE%%#*}#DelegateKey-$(date -u +%Y%m%d)"
    KEY_BLOCK="
  # Delegate's public key, republished under the delegator's own profile so a
  # standard WebID-TLS verifier that checks THIS graph recognizes the delegate's cert
  <${DELEGATE}>
      cert:key <${DELEGATE_KEY_IRI}> .
  <${DELEGATE_KEY_IRI}>
      a cert:RSAPublicKey ;
      cert:modulus \"${KEY_MODULUS}\"^^xsd:hexBinary ;
      cert:exponent \"${KEY_EXPONENT}\"^^xsd:int ."
else
    KEY_BLOCK="
  # WARNING: no delegate public key was resolved — see Step 0 output above.
  # Delegation asserted below is relationship-only and will NOT grant
  # delegated resource access until cert:key is added separately."
fi

cat > "$SPARQL_FILE" <<SPARQL
# YouID Delegation — SPARQL UPDATE Patch
# Generated: $(date -u)
# Delegator: <${DELEGATOR}>
# Delegate:  <${DELEGATE}>
# Role:      ${ROLE}
#
# Deploy: curl -X POST <sparql-endpoint> \\
#             -H 'Content-Type: application/sparql-update' \\
#             -u <username>:<password> \\
#             --data-binary @'${SPARQL_FILE}'

PREFIX foaf:     <http://xmlns.com/foaf/0.1/>
PREFIX oplcert:  <http://www.openlinksw.com/schemas/cert#>
PREFIX cert:     <http://www.w3.org/ns/auth/cert#>
PREFIX schema:   <http://schema.org/>
PREFIX xsd:      <http://www.w3.org/2001/XMLSchema#>

INSERT DATA {
  # Delegation role: ${ROLE}
  <${DELEGATOR}>
      a foaf:Agent ;
      a schema:Person ;
      schema:additionalType "Delegator" ;
      schema:description "Delegates ${ROLE_UPPER} role to <${DELEGATE}>"^^xsd:string ;
      oplcert:hasIdentityDelegate <${DELEGATE}> .

  # Delegate acts on behalf of delegator
  <${DELEGATE}>
      a foaf:Agent ;
      schema:additionalType "Delegate" ;
      schema:description "Assigned ${ROLE_UPPER} role for <${DELEGATOR}>"^^xsd:string ;
      oplcert:onBehalfOf <${DELEGATOR}> .
${KEY_BLOCK}
}
SPARQL
echo "  → ${SPARQL_FILE}"

# Step 2: Generate declarativeNetRequest rule JSON
echo "=== Step 2: declarativeNetRequest Rule ==="
RULE_FILE="$OUT_DIR/delegation-rule.json"

cat > "$RULE_FILE" <<JSON
{
  "id": 1,
  "priority": 1,
  "condition": {
    "urlFilter": "*",
    "resourceTypes": ["xmlhttprequest"]
  },
  "action": {
    "type": "modifyHeaders",
    "requestHeaders": [
      {
        "header": "On-Behalf-Of",
        "operation": "set",
        "value": "${DELEGATE}"
      }
    ]
  }
}
JSON
echo "  → ${RULE_FILE}"

# Step 3: Generate deployment summary
echo "=== Step 3: Deployment Summary ==="
SUMMARY_FILE="$OUT_DIR/delegation-summary.json"

cat > "$SUMMARY_FILE" <<JSON
{
  "delegator": "${DELEGATOR}",
  "delegate": "${DELEGATE}",
  "role": "${ROLE}",
  "generated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "files": {
    "sparql_patch": "delegation.sparql",
    "dnr_rule": "delegation-rule.json"
  },
  "deployment": {
    "method": "SPARQL UPDATE via HTTP POST",
    "content_type": "application/sparql-update",
    "auth_options": [
      "Basic (username:password)",
      "Digest",
      "Bearer token",
      "WebID-OIDC DPoP"
    ],
    "curl_example": "curl -X POST <endpoint> -H 'Content-Type: application/sparql-update' -u <user>:<pass> --data-binary @delegation.sparql",
    "endpoint_note": "Use the SPARQL endpoint of the delegator's identity provider (e.g., https://linkeddata.uriburner.com/SPARQL)"
  }
}
JSON
echo "  → ${SUMMARY_FILE}"

echo ""
echo "=== Delegation Bundle Generated ==="
echo "  Output: ${OUT_DIR}/"
ls -la "$OUT_DIR/"
echo ""
echo "=== Next Steps ==="
echo "  1. Review delegation.sparql — verify the triples are correct"
echo "  2. Deploy the SPARQL UPDATE to the delegator's profile store:"
echo "     curl -X POST <sparql-endpoint> \\"
echo "       -H 'Content-Type: application/sparql-update' \\"
echo "       -u <username>:<password> \\"
echo "       --data-binary @'${SPARQL_FILE}'"
echo "  3. Install delegation-rule.json in the delegate's browser"
echo "     (Chrome extension → declarativeNetRequest rules)"
echo "  4. Verify: query the delegator's WebID for oplcert:hasIdentityDelegate triples"
