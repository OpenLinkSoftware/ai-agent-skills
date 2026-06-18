#!/bin/bash
#
# YouID Identity Generator — Orchestrator
# Generates a complete NetID identity bundle:
#   1. Self-signed X.509 certificate
#   2. All RDF profile documents via template filling
#   3. Identity card HTML page
#   4. vCard VCF
#
# Usage:
#   ./generate_identity.sh -n <name> -w <webid> [-t <title>] [-e <email>] [-o <org>] [-c <country>]
#                          [-s <state>] [-p <password>] [-b <base_url>] [-d <output_dir>]
#                          [-P <photo_url>] [-u <pdp_url>] [-S <pim_storage>]
#                          [-T <style>] [-V <validity_days>] [-f <data_json>]
#
# All arguments:
#   -n <name>        Common name (required)
#   -w <webid>       WebID URI (required)
#   -t <title>       Professional title (e.g., "Founder & CEO, OpenLink Software")
#   -e <email>       Email address
#   -o <org>         Organization
#   -c <country>     2-letter ISO country code
#   -s <state>       State/province
#   -p <password>    PKCS#12 password (default: youid)
#   -b <base_url>    Base URL for generated artifact IRIs (default: file:///path/to/output/)
#   -d <output_dir>  Output directory (default: ./youid-output)
#   -P <photo_url>   Photo URL (default: photo_130x145.jpg)
#   -u <pdp_url>     Personal profile page URL
#   -S <pim_storage> Storage URL
#   -T <style>       Identity card template style: default, premium, dark (default: default)
#   -V <days>        Certificate validity in days (default: 365 = 1 year)
#   -f <data_json>   Path to additional JSON data (for social relations, OPAL settings, etc.)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
YOUID_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Defaults
NAME=""
WEBID=""
EMAIL=""
ORG=""
COUNTRY=""
STATE=""
TITLE=""
PASSWORD="youid"
BASE_URL=""
OUT_DIR="$(pwd)/youid-output"
PHOTO_URL="photo_130x145.jpg"
PDP_URL=""
PIM_STORAGE=""
STYLE="default"
VALIDITY_DAYS="365"
EXTRA_DATA=""
CHAT_CONFIG="virtuoso-support-assistant-config"

while getopts "n:w:t:e:o:c:s:p:b:d:P:u:S:T:V:f:C:h" opt; do
    case $opt in
        n) NAME="$OPTARG" ;;
        w) WEBID="$OPTARG" ;;
        t) TITLE="$OPTARG" ;;
        e) EMAIL="$OPTARG" ;;
        o) ORG="$OPTARG" ;;
        c) COUNTRY="$OPTARG" ;;
        s) STATE="$OPTARG" ;;
        p) PASSWORD="$OPTARG" ;;
        b) BASE_URL="$OPTARG" ;;
        d) OUT_DIR="$OPTARG" ;;
        P) PHOTO_URL="$OPTARG" ;;
        u) PDP_URL="$OPTARG" ;;
        S) PIM_STORAGE="$OPTARG" ;;
        T) STYLE="$OPTARG" ;;
        V) VALIDITY_DAYS="$OPTARG" ;;
        f) EXTRA_DATA="$OPTARG" ;;
        C) CHAT_CONFIG="$OPTARG" ;;
        h) echo "Usage: $0 -n <name> -w <webid> [-t title] [-e email] [-o org] [-c country] [-s state] [-p password] [-b base_url] [-d out_dir] [-P photo_url] [-u pdp_url] [-S pim_storage] [-T style] [-V validity_days] [-f extra.json] [-C chat_config]"
           exit 0 ;;
        *) echo "Unknown option -$opt"; exit 1 ;;
    esac
done

if [ -z "$NAME" ] || [ -z "$WEBID" ]; then
    echo "Error: -n (name) and -w (webid) are required"
    exit 1
fi

mkdir -p "$OUT_DIR"

# Step 1: Generate certificate
echo "=== Step 1: Generating X.509 Certificate ==="
"$SCRIPT_DIR/generate_certificate.sh" \
    "$NAME" "$WEBID" "$EMAIL" "$ORG" "$COUNTRY" "$STATE" "$PASSWORD" "$OUT_DIR" "$VALIDITY_DAYS"

# Step 2: Build template data
echo "=== Step 2: Building Template Data ==="
CERT_DATA="$OUT_DIR/cert_data.json"

# Merge extra data if provided
TEMPLATE_DATA="$OUT_DIR/template_data.json"
python3 -c "
import json

with open('$CERT_DATA') as f:
    data = json.load(f)

# Add URL variables
base_url = '${BASE_URL}' if '${BASE_URL}' else 'file://${OUT_DIR}/'
if not base_url.endswith('/'):
    base_url += '/'

data['base_url'] = base_url
data['prof_url'] = base_url + 'profile.ttl'
data['pubkey_url'] = base_url + 'public_key.ttl'
data['cert_url'] = base_url + 'certificate.ttl'
data['card_url'] = base_url + 'index.html'
data['card_ident_url'] = base_url + 'index.html#netid'
data['jsonld_prof_url'] = base_url + 'profile.jsonld'
data['jsonld_cert_url'] = base_url + 'certificate.jsonld'
data['jsonld_pubkey_url'] = base_url + 'public_key.jsonld'
data['rdfa_prof_url'] = base_url + 'profile_rdfa.html'
data['rdfa_cert_url'] = base_url + 'certificate.rdfa.html'
data['rdfa_pubkey_url'] = base_url + 'public_key.rdfa.html'
data['vcard_url'] = base_url + 'vcard.vcf'
data['pubkey_pem_url'] = base_url + 'cert.pem'
data['pubkey_der_url'] = base_url + 'cert.crt'
data['photo_url'] = '${PHOTO_URL}'

# Professional title
title = '${TITLE}'
if title:
    data['subj_title'] = title

# Optional URLs
pdp = '${PDP_URL}'
if pdp:
    data['pdp_url'] = pdp
    data['pdp_url_head'] = f'<link rel=\"related\" href=\"{pdp}\" title=\"Related Document\" type=\"text/html\" />'

pim = '${PIM_STORAGE}'
if pim:
    data['pim_storage'] = pim

# Chat agent config (set from -C, overridable by -f extra data)
data['w_module'] = '${CHAT_CONFIG}'

# Load extra data if provided
extra_path = '${EXTRA_DATA}'
if extra_path:
    with open(extra_path) as ef:
        extra = json.load(ef)
        data.update(extra)

with open('$TEMPLATE_DATA', 'w') as f:
    json.dump(data, f, indent=2)

print(f'Template data written to {len(data)} variables')
"

# Override STYLE from extra data JSON if present (allows profile_style in -f file)
if python3 -c "import json; d=json.load(open('$TEMPLATE_DATA')); print(d.get('profile_style',''))" 2>/dev/null | grep -q '.'; then
    JSON_STYLE=$(python3 -c "import json; print(json.load(open('$TEMPLATE_DATA'))['profile_style'])")
    if [ "$JSON_STYLE" != "default" ]; then
        STYLE="$JSON_STYLE"
        echo "  Using template style from extra data: $STYLE"
    fi
fi

# Step 3a: Render partial/profile templates first for embedding
echo "=== Step 3a: Rendering Partial Templates ==="
TPLDIR="$YOUID_DIR/templates"
OUT="$OUT_DIR"

# Render profile.ttl, profile.jsonld, prof_rdfa first — their output
# gets embedded into index.html and profile_rdfa.html as %{profile_ttl},
# %{json_ld}, and %{rdfa} respectively
for tpl in profile.ttl profile.jsonld prof_rdfa.tpl; do
    TPL_FILE="$TPLDIR/$tpl.tpl"
    if [ ! -f "$TPL_FILE" ]; then
        TPL_FILE="$TPLDIR/$tpl"
    fi
    if [ -f "$TPL_FILE" ]; then
        if [ "$tpl" = "prof_rdfa.tpl" ]; then
            OUT_FILE="$OUT/prof_rdfa.inc"
        else
            OUT_FILE="$OUT/$tpl"
        fi
        echo "  Rendering $tpl → $OUT_FILE..."
        python3 "$SCRIPT_DIR/template_fill.py" \
            "$TPL_FILE" \
            "$TEMPLATE_DATA" \
            "$OUT_FILE"
    fi
done

# Read generated content and inject into template data for embedded rendering
python3 -c "
import json, os

tpl_data_path = '$TEMPLATE_DATA'
out_dir = '$OUT'

with open(tpl_data_path) as f:
    data = json.load(f)

# Read generated partial/profile files
for key, filename in [('rdfa', 'prof_rdfa.inc'),
                       ('json_ld', 'profile.jsonld'),
                       ('profile_ttl', 'profile.ttl')]:
    path = os.path.join(out_dir, filename)
    try:
        with open(path) as f:
            data[key] = f.read()
        print(f'  Embedded {key}: {len(data[key])}B from {filename}')
    except FileNotFoundError:
        print(f'  WARNING: {filename} not found, {key} will be empty')
        data[key] = ''

# Auto-enable conditional flags for embedded content
data['em_rdfa'] = True
data['em_jsonld'] = True
data['em_ttl'] = True

with open(tpl_data_path, 'w') as f:
    json.dump(data, f, indent=2)
print('  Conditional flags enabled: em_rdfa=yes em_jsonld=yes em_ttl=yes')
"

# Step 3b: Render all remaining templates (now with embeddable content)
echo "=== Step 3b: Filling Remaining Templates ==="

for tpl in profile_rdfa.html \
           certificate.ttl certificate.jsonld certificate.rdfa.html \
           public_key.ttl public_key.jsonld public_key.rdfa.html \
           index.html vcard.vcf style.css; do
    # Select identity card template based on style
    if [ "$tpl" = "index.html" ] && [ "$STYLE" != "default" ]; then
        TPL_FILE="$TPLDIR/index_${STYLE}.html.tpl"
    else
        TPL_FILE="$TPLDIR/$tpl.tpl"
    fi

    if [ -f "$TPL_FILE" ]; then
        echo "  Generating $tpl (from $(basename $TPL_FILE))..."
        python3 "$SCRIPT_DIR/template_fill.py" \
            "$TPL_FILE" \
            "$TEMPLATE_DATA" \
            "$OUT/$tpl"
    elif [ -f "$TPLDIR/$tpl.tpl" ]; then
        # Fallback to default template
        echo "  Generating $tpl..."
        python3 "$SCRIPT_DIR/template_fill.py" \
            "$TPLDIR/$tpl.tpl" \
            "$TEMPLATE_DATA" \
            "$OUT/$tpl"
    fi
done

# Clean up: template_data.json is a build artifact, not for deployment
rm -f "$TEMPLATE_DATA" "$OUT/prof_rdfa.inc"

# Step 4: Copy assets
echo "=== Step 4: Copying Assets ==="
if [ -d "$YOUID_DIR/assets" ]; then
    # Always-needed assets
    for asset in youid_logo-35px.png addrbook.png lock.png chatbot-32px.png \
                 qrcode.js opal.js opalx.js auth.js win.js style_opal.css solid-client-authn.bundle.js login.svg logout.svg \
                 photo_130x145.jpg; do
        if [ -f "$YOUID_DIR/assets/$asset" ]; then
            cp "$YOUID_DIR/assets/$asset" "$OUT/$asset"
        fi
    done
    # Social media platform icons (needed by relList_html in the identity card)
    for asset in "$YOUID_DIR/assets"/p_*.png; do
        if [ -f "$asset" ]; then
            cp "$asset" "$OUT/$(basename "$asset")"
        fi
    done
fi

echo ""
echo "=== Identity Bundle Generated Successfully ==="
echo "  Output: $OUT_DIR"
ls -la "$OUT_DIR"/*.ttl "$OUT_DIR"/*.jsonld "$OUT_DIR"/*.html "$OUT_DIR"/*.vcf 2>/dev/null
echo ""
echo "  Certificate:     ${OUT_DIR}/cert.pem"
echo "  PKCS#12:         ${OUT_DIR}/cert.p12 (password: ${PASSWORD})"
echo "  Profile (TTL):   ${OUT_DIR}/profile.ttl"
echo "  Identity Card:   ${OUT_DIR}/index.html (style: ${STYLE})"
echo "  vCard:           ${OUT_DIR}/vcard.vcf"
