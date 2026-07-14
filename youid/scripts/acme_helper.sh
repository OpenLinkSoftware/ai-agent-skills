#!/bin/bash
#
# ACME.sh Helper for YouID Certificate Generator
# Provides ACME.sh installation, CSR generation, and certificate signing
# for Let's Encrypt and ZeroSSL CA-signed certificates.
#
# This script is meant to be sourced by generate_certificate.sh:
#   source "$(dirname "$0")/acme_helper.sh"
#
# Functions exported:
#   ensure_acme_sh <email>
#   generate_csr <key_file> <csr_file> <subj> <domain> <webid_uri>
#   run_acme_sign <domain> <csr_file> [eab_kid] [eab_hmac_key] [acme_server]
#   download_signed_cert <domain> <output_dir>
#   zerossl_fetch_eab <api_key>
#   acme_cleanup <domain>
#
set -euo pipefail

# Default ACME directory URLs
ACME_LE_PRODUCTION="https://acme-v02.api.letsencrypt.org/directory"
ACME_LE_STAGING="https://acme-staging-v02.api.letsencrypt.org/directory"
ACME_ZEROSSL="https://acme.zerossl.com/v2/DV90"

# Install acme.sh if not present
# Usage: ensure_acme_sh <email>
ensure_acme_sh() {
    local email="${1:-}"
    if [ -z "$email" ]; then
        echo "Error: email is required for acme.sh installation" >&2
        return 1
    fi

    if command -v acme.sh &>/dev/null; then
        echo "  acme.sh already installed at $(command -v acme.sh)"
        return 0
    fi

    if [ -f "$HOME/.acme.sh/acme.sh" ]; then
        echo "  Found acme.sh at $HOME/.acme.sh/acme.sh"
        export PATH="$HOME/.acme.sh:$PATH"
        return 0
    fi

    echo "  Installing acme.sh (Let's Encrypt ACME client)..."
    echo "  Using email: $email"
    curl -fsSL https://get.acme.sh | sh -s "email=${email}" 2>/dev/null
    if [ -f "$HOME/.acme.sh/acme.sh" ]; then
        export PATH="$HOME/.acme.sh:$PATH"
        echo "  acme.sh installed successfully"
        return 0
    else
        echo "Error: acme.sh installation failed" >&2
        return 1
    fi
}

# Generate RSA key and CSR with DNS + URI SANs
# Usage: generate_csr <key_file> <csr_file> <subj> <domain> <webid_uri>
generate_csr() {
    local key_file="$1"
    local csr_file="$2"
    local subj="$3"
    local domain="$4"
    local webid_uri="$5"

    if [ -z "$key_file" ] || [ -z "$csr_file" ] || [ -z "$subj" ] || [ -z "$domain" ] || [ -z "$webid_uri" ]; then
        echo "Error: generate_csr requires <key_file> <csr_file> <subj> <domain> <webid_uri>" >&2
        return 1
    fi

    echo "  Generating RSA 2048 key: $key_file"
    openssl genrsa -out "$key_file" 2048 2>/dev/null

    local san="DNS:${domain},URI:${webid_uri//#/\\#}"
    echo "  Generating CSR: $csr_file"
    echo "  SAN: $san"
    openssl req -new -key "$key_file" -out "$csr_file" \
        -subj "$subj" \
        -addext "subjectAltName=${san}"

    echo "  CSR generated successfully"
    return 0
}

# Sign CSR via acme.sh
# Usage: run_acme_sign <domain> <csr_file> [eab_kid] [eab_hmac_key] [acme_server]
run_acme_sign() {
    local domain="$1"
    local csr_file="$2"
    local eab_kid="${3:-}"
    local eab_hmac_key="${4:-}"
    local acme_server="${5:-$ACME_LE_PRODUCTION}"

    if [ -z "$domain" ] || [ -z "$csr_file" ]; then
        echo "Error: run_acme_sign requires <domain> <csr_file>" >&2
        return 1
    fi

    if [ ! -f "$csr_file" ]; then
        echo "Error: CSR file not found: $csr_file" >&2
        return 1
    fi

    local acme_cmd="acme.sh --sign-csr --csr \"$csr_file\" -d \"$domain\" --server \"$acme_server\""

    if [ -n "$eab_kid" ] && [ -n "$eab_hmac_key" ]; then
        acme_cmd="$acme_cmd --eab-kid \"$eab_kid\" --eab-hmac-key \"$eab_hmac_key\""
    fi

    echo "  Signing CSR with acme.sh..."
    echo "  Server: $acme_server"
    echo "  Domain: $domain"
    echo "  CSR:    $csr_file"
    eval "$acme_cmd"
    local rc=$?
    if [ $rc -ne 0 ]; then
        echo "Error: acme.sh signing failed (exit code $rc)" >&2
        return 1
    fi
    echo "  CSR signed successfully"
    return 0
}

# Download signed certificate from acme.sh output directory
# Usage: download_signed_cert <domain> <output_dir>
download_signed_cert() {
    local domain="$1"
    local output_dir="$2"

    if [ -z "$domain" ] || [ -z "$output_dir" ]; then
        echo "Error: download_signed_cert requires <domain> <output_dir>" >&2
        return 1
    fi

    local acme_domain_dir="$HOME/.acme.sh/${domain}_ecc"
    if [ ! -d "$acme_domain_dir" ]; then
        acme_domain_dir="$HOME/.acme.sh/${domain}"
    fi

    if [ ! -d "$acme_domain_dir" ]; then
        echo "Error: acme.sh output directory not found: $acme_domain_dir" >&2
        return 1
    fi

    mkdir -p "$output_dir"

    echo "  Copying certificates from $acme_domain_dir"

    # Copy the full certificate chain
    if [ -f "$acme_domain_dir/fullchain.cer" ]; then
        cp "$acme_domain_dir/fullchain.cer" "$output_dir/cert.pem"
        echo "  cert.pem (fullchain): $acme_domain_dir/fullchain.cer"
    elif [ -f "$acme_domain_dir/fullchain.pem" ]; then
        cp "$acme_domain_dir/fullchain.pem" "$output_dir/cert.pem"
        echo "  cert.pem (fullchain): $acme_domain_dir/fullchain.pem"
    else
        echo "Warning: fullchain not found, trying ca + cert" >&2
        if [ -f "$acme_domain_dir/ca.cer" ] && [ -f "$acme_domain_dir/$domain.cer" ]; then
            cat "$acme_domain_dir/$domain.cer" "$acme_domain_dir/ca.cer" > "$output_dir/cert.pem"
        else
            echo "Error: no certificate files found in $acme_domain_dir" >&2
            return 1
        fi
    fi

    # Copy CA certificate for ca_cert_url
    if [ -f "$acme_domain_dir/ca.cer" ]; then
        cp "$acme_domain_dir/ca.cer" "$output_dir/ca.cer"
        echo "  ca.cer: $acme_domain_dir/ca.cer"
    fi

    echo "  Certificates downloaded to $output_dir"
    return 0
}

# Fetch ZeroSSL EAB credentials
# Usage: zerossl_fetch_eab <api_key>
# Returns: "eab_kid:eab_hmac_key"
zerossl_fetch_eab() {
    local api_key="$1"

    if [ -z "$api_key" ]; then
        echo "Error: ZeroSSL API key is required" >&2
        return 1
    fi

    echo "  Fetching ZeroSSL EAB credentials..."
    local response
    response=$(curl -fsSL -X POST "https://api.zerossl.com/acme/eab-credentials?access_key=${api_key}" 2>/dev/null)

    if [ -z "$response" ]; then
        echo "Error: failed to fetch ZeroSSL EAB credentials" >&2
        return 1
    fi

    local eab_kid eab_hmac
    eab_kid=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin)['eab_kid'])" 2>/dev/null)
    eab_hmac=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin)['eab_hmac_key'])" 2>/dev/null)

    if [ -z "$eab_kid" ] || [ -z "$eab_hmac" ]; then
        echo "Error: invalid ZeroSSL EAB response" >&2
        return 1
    fi

    echo "${eab_kid}:${eab_hmac}"
    return 0
}

# Clean up acme.sh domain directory
# Usage: acme_cleanup <domain>
acme_cleanup() {
    local domain="$1"
    if [ -z "$domain" ]; then
        return 0
    fi
    local acme_dir="$HOME/.acme.sh/${domain}"
    local acme_dir_ecc="$HOME/.acme.sh/${domain}_ecc"
    if [ -d "$acme_dir" ]; then
        rm -rf "$acme_dir"
    fi
    if [ -d "$acme_dir_ecc" ]; then
        rm -rf "$acme_dir_ecc"
    fi
}

# Get ACME server URL for a given cert type
# Usage: get_acme_server <cert_type> [use_staging]
#   cert_type: "letsencrypt" or "zerossl"
#   use_staging: "1" for staging, "0" or empty for production
get_acme_server() {
    local cert_type="$1"
    local use_staging="${2:-0}"
    case "$cert_type" in
        zerossl) echo "$ACME_ZEROSSL" ;;
        letsencrypt)
            if [ "$use_staging" = "1" ]; then
                echo "$ACME_LE_STAGING"
            else
                echo "$ACME_LE_PRODUCTION"
            fi
            ;;
        *) echo "$ACME_LE_PRODUCTION" ;;
    esac
}
