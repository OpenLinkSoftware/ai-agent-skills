#!/bin/bash
#
# YouID T8 — did:nostr identity generator (wraps melvincarvalho/create-agent)
#
# Mints a secp256k1 keypair + W3C did:nostr DID document with create-agent
# (nostr-tools under the hood), then optionally:
#   * links it to a WebID (reciprocal side of the link — see -w/-R)
#   * stores the secret in the macOS Keychain            (-K)
#   * exports the secret as an encrypted PKCS#12 bundle  (-X, optional backup)
#   * writes the HTTP-resolution copy of the DID document (-H)
#
# Secret-key custody (never written into the YouID output bundle, never printed):
#   1. git config --local nostr.privkey   (create-agent's convention; read by aam / fund-agent)
#   2. macOS Keychain generic-password item service "youid-nostr", account = npub   (-K)
#   3. PKCS#12 (secp256k1 key + self-signed X.509, SAN = did:nostr + WebID)        (-X)
#      Portable encrypted backup only. It is NOT usable for WebID-TLS: browsers/TLS
#      stacks don't offer secp256k1 client certificates.
#
# Usage:
#   generate_nostr_identity.sh [-d agent_dir] [-w webid -R same|agent] [-r relay]...
#                              [-K] [-X out.p12 -p password [-V days]] [-H wellknown_root] [-E]
#
#   -d <dir>     Agent identity directory (git repo; created if missing). Default ./agent-identity
#   -w <webid>   WebID to link with
#   -R <mode>    same  = the DID and the WebID denote the SAME agent  → DID alsoKnownAs WebID
#                agent = the DID is an agent acting on behalf of the WebID → DID oplcert:onBehalfOf WebID
#   -r <relay>   wss:// relay to advertise as a DID service (repeatable; trailing slash enforced)
#   -K           Also store the secret key in the macOS Keychain
#   -X <file>    Also export an encrypted PKCS#12 (.p12) bundle
#   -p <pass>    PKCS#12 password (required with -X)
#   -V <days>    PKCS#12 certificate validity (default 365)
#   -H <root>    Write <root>/.well-known/did/nostr/<hex>.json (HTTP resolution copy)
#   -E           Use the existing identity in <dir> (skip minting; apply the other options)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CRYPTO="$SCRIPT_DIR/nostr_crypto.py"

AGENT_DIR="$(pwd)/agent-identity"
WEBID=""
MODE=""
RELAYS=()
KEYCHAIN=0
P12_OUT=""
P12_PASS=""
P12_DAYS="365"
WELLKNOWN=""
EXISTING=0

while getopts "d:w:R:r:KX:p:V:H:Eh" opt; do
    case $opt in
        d) AGENT_DIR="$OPTARG" ;;
        w) WEBID="$OPTARG" ;;
        R) MODE="$OPTARG" ;;
        r) RELAYS+=("$OPTARG") ;;
        K) KEYCHAIN=1 ;;
        X) P12_OUT="$OPTARG" ;;
        p) P12_PASS="$OPTARG" ;;
        V) P12_DAYS="$OPTARG" ;;
        H) WELLKNOWN="$OPTARG" ;;
        E) EXISTING=1 ;;
        h) sed -n '2,40p' "$0"; exit 0 ;;
        *) echo "Unknown option"; exit 1 ;;
    esac
done

if [ -n "$WEBID" ] && [ "$MODE" != "same" ] && [ "$MODE" != "agent" ]; then
    echo "Error: -w requires -R same|agent (whose identity is this DID?)"; exit 1
fi
if [ -n "$P12_OUT" ] && [ -z "$P12_PASS" ]; then
    echo "Error: -X requires -p <password>"; exit 1
fi

mkdir -p "$AGENT_DIR"
AGENT_DIR="$(cd "$AGENT_DIR" && pwd)"
DID_FILE="$AGENT_DIR/agent.did.json"

# ── Step 1: mint (or reuse) ─────────────────────────────────────────────────
if [ "$EXISTING" -eq 1 ]; then
    echo "=== Step 1: Reusing existing identity in $AGENT_DIR ==="
    [ -f "$DID_FILE" ] || { echo "Error: $DID_FILE not found"; exit 1; }
else
    echo "=== Step 1: Minting did:nostr identity with create-agent ==="
    ( cd "$AGENT_DIR" && npx -y create-agent > /dev/null )
fi

SECRET=$(git -C "$AGENT_DIR" config --local nostr.privkey || true)
if [ -z "$SECRET" ]; then
    echo "Error: git config --local nostr.privkey is empty in $AGENT_DIR"; exit 1
fi

# ── Step 2: key-consistency gate (secret ⇄ DID document) ────────────────────
echo "=== Step 2: Key Consistency Gate ==="
HEX=$(python3 -c "import json;print(json.load(open('$DID_FILE'))['id'].split(':')[-1])")
DERIVED=$(python3 "$CRYPTO" pubkey "$SECRET")
if [ "$DERIVED" != "$HEX" ]; then
    echo "  ✗ secret key does not derive the DID's public key — aborting"; exit 1
fi
NPUB=$(python3 "$CRYPTO" normalize "$HEX" | python3 -c "import json,sys;print(json.load(sys.stdin)['npub'])")
echo "  ✓ git config nostr.privkey derives did:nostr:$HEX"

# ── Step 3: WebID link + relay services (reciprocal side of the link) ──────
echo "=== Step 3: Updating DID document ==="
python3 "$CRYPTO" patch-did "$DID_FILE" "$WEBID" "$MODE" ${RELAYS[@]+"${RELAYS[@]}"}

# ── Step 4 (optional): macOS Keychain ──────────────────────────────────────
if [ "$KEYCHAIN" -eq 1 ]; then
    echo "=== Step 4: Storing secret in macOS Keychain ==="
    security add-generic-password -U -s youid-nostr -a "$NPUB" -l "YouID did:nostr $NPUB" -w "$SECRET"
    KC=$(security find-generic-password -s youid-nostr -a "$NPUB" -w)
    if [ "$(python3 "$CRYPTO" pubkey "$KC")" = "$HEX" ]; then
        echo "  ✓ Keychain item youid-nostr / $NPUB round-trips to the DID key"
    else
        echo "  ✗ Keychain round-trip mismatch"; exit 1
    fi
    unset KC
fi

# ── Step 5 (optional): PKCS#12 export ──────────────────────────────────────
if [ -n "$P12_OUT" ]; then
    echo "=== Step 5: Exporting encrypted PKCS#12 (secp256k1) ==="
    WORK=$(mktemp -d "${TMPDIR:-/tmp}/youid-nostr-p12.XXXXXX")
    chmod 700 "$WORK"
    trap 'rm -f "$WORK"/key.der "$WORK"/key.pem "$WORK"/cert.pem; rmdir "$WORK" 2>/dev/null || true' EXIT
    python3 "$CRYPTO" sec1der "$SECRET" "$WORK/key.der"
    openssl ec -inform DER -in "$WORK/key.der" -out "$WORK/key.pem" 2>/dev/null
    SAN="URI:did:nostr:$HEX"
    # '#' starts a comment in OpenSSL config syntax — escape it (same as generate_certificate.sh)
    [ -n "$WEBID" ] && SAN="$SAN,URI:${WEBID//#/\\#}"
    openssl req -new -x509 -key "$WORK/key.pem" -sha256 -days "$P12_DAYS" -subj "/CN=$NPUB" \
        -addext "subjectAltName=$SAN" \
        -addext "basicConstraints=critical,CA:FALSE" \
        -addext "keyUsage=critical,digitalSignature" \
        -addext "nsComment=YouID did:nostr key backup (secp256k1; not for WebID-TLS)" \
        -out "$WORK/cert.pem" 2>/dev/null
    openssl pkcs12 -export -inkey "$WORK/key.pem" -in "$WORK/cert.pem" \
        -name "did:nostr:$HEX" -passout pass:"$P12_PASS" -out "$P12_OUT"
    chmod 600 "$P12_OUT"
    # Gate: the x-coordinate inside the .p12 must equal the did:nostr key
    P12_X=$(openssl pkcs12 -in "$P12_OUT" -passin pass:"$P12_PASS" -nokeys -clcerts 2>/dev/null \
        | openssl x509 -noout -pubkey | openssl ec -pubin -outform DER -conv_form compressed 2>/dev/null \
        | tail -c 32 | xxd -p -c 64)
    if [ "$P12_X" = "$HEX" ]; then
        echo "  ✓ $P12_OUT: secp256k1 x-coordinate matches did:nostr key (SAN: $SAN)"
    else
        echo "  ✗ PKCS#12 key mismatch"; exit 1
    fi
fi

# ── Step 6 (optional): HTTP-resolution copy ────────────────────────────────
if [ -n "$WELLKNOWN" ]; then
    echo "=== Step 6: Writing HTTP-resolution DID document ==="
    WK_DIR="$WELLKNOWN/.well-known/did/nostr"
    mkdir -p "$WK_DIR"
    cp "$DID_FILE" "$WK_DIR/$HEX.json"
    echo "  ✓ $WK_DIR/$HEX.json  (serve as application/did+json at https://<domain>/.well-known/did/nostr/$HEX.json)"
fi

unset SECRET
echo ""
echo "=== did:nostr identity ready ==="
echo "  DID:          did:nostr:$HEX"
echo "  npub:         $NPUB"
echo "  DID document: $DID_FILE"
echo "  Secret key:   git -C $AGENT_DIR config nostr.privkey  (never commit / print)"
