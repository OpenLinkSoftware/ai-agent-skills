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

# Step 5: Basic WebID Test (Public Key Consistency Gate)
echo "=== Step 5: Basic WebID Test (Public Key Consistency Gate) ==="
GATE_FAILED=0

# Extract from cert.p12
MOD=$(openssl pkcs12 -in "$OUT_DIR/cert.p12" -passin pass:"$PASSWORD" -nokeys -clcerts 2>/dev/null \
    | openssl x509 -noout -modulus | sed 's/Modulus=//')
EXP=$(openssl pkcs12 -in "$OUT_DIR/cert.p12" -passin pass:"$PASSWORD" -nokeys -clcerts 2>/dev/null \
    | openssl x509 -noout -text | awk '/Exponent:/ {print $2}')

if [ -z "$MOD" ] || [ -z "$EXP" ]; then
    echo "  ✗ FAILED: Could not extract public key from cert.p12"
    GATE_FAILED=1
fi

mod_lc=$(echo "$MOD" | tr 'A-Z' 'a-z')
exp_lc=$(echo "$EXP" | tr 'A-Z' 'a-z')

# Define a small Python script for value extraction that won't pollute the output
read -r -d '' PY_GATE << 'PYEOF' || true
import json, sys, re, os

out_dir = os.environ.get('OUT_DIR', '')
mod_ref = os.environ.get('MOD_REF', '')
exp_ref = os.environ.get('EXP_REF', '')
mod_lc = mod_ref.lower()
exp_lc = exp_ref.lower()
fail = 0

def check(label, actual_mod, actual_exp):
    global fail
    mod_ok = actual_mod.lower().strip() == mod_lc.strip()
    exp_ok = actual_exp.strip() == exp_lc.strip()
    print(f"  {'✓' if mod_ok else '✗'} {label} modulus")
    print(f"  {'✓' if exp_ok else '✗'} {label} exponent")
    if not mod_ok or not exp_ok:
        fail = 1

# profile.ttl
import rdflib
g = rdflib.Graph()
g.parse(os.path.join(out_dir, 'profile.ttl'), format='turtle')
ttl_mod = ''
ttl_exp = ''
for s, p, o in g.triples((None, rdflib.URIRef('http://www.w3.org/ns/auth/cert#modulus'), None)):
    ttl_mod = str(o)
    break
for s, p, o in g.triples((None, rdflib.URIRef('http://www.w3.org/ns/auth/cert#exponent'), None)):
    ttl_exp = str(o)
    break
check('profile.ttl', ttl_mod, ttl_exp)

# profile.jsonld
with open(os.path.join(out_dir, 'profile.jsonld')) as f:
    jld = json.load(f)
jld_mod = ''
jld_exp = ''
for item in jld.get('@graph', []):
    if 'cert:modulus' in item:
        jld_mod = item['cert:modulus']['@value']
    if 'cert:exponent' in item:
        jld_exp = item['cert:exponent']['@value']
check('profile.jsonld', jld_mod, jld_exp)

# index.html (RDFa property)
from html.parser import HTMLParser
class ModParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.mod = ''
        self.in_mod = False
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if d.get('property') == 'cert:modulus':
            self.in_mod = True
    def handle_data(self, data):
        if self.in_mod and data.strip():
            self.mod = data.strip()
            self.in_mod = False
p = ModParser()
with open(os.path.join(out_dir, 'index.html')) as f:
    p.feed(f.read())
check('index.html (RDFa)', p.mod, '65537')

sys.exit(fail)
PYEOF

export OUT_DIR MOD_REF="$MOD" EXP_REF="$EXP"
if python3 -c "$PY_GATE"; then
    echo "  Basic WebID Test: PASS"
else
    echo "  Basic WebID Test: FAIL — Public key mismatch detected!"
    GATE_FAILED=1
fi
unset OUT_DIR MOD_REF EXP_REF

# Step 6: WebID Delegation Consistency Gate
echo "=== Step 6: WebID Delegation Consistency Gate ==="
read -r -d '' PY_DEL_GATE << 'PYEOF' || true
import json, sys, os
from html.parser import HTMLParser

out_dir = os.environ.get('OUT_DIR', '')
fail = 0

OPLHAS = 'http://www.openlinksw.com/schemas/cert#hasIdentityDelegate'
OPLON = 'http://www.openlinksw.com/schemas/cert#onBehalfOf'

# Collect delegation triples from each file
results = {}

# --- profile.ttl ---
import rdflib
ttl_delegates = set()
ttl_behalfof = set()
if os.path.exists(os.path.join(out_dir, 'profile.ttl')):
    g = rdflib.Graph()
    g.parse(os.path.join(out_dir, 'profile.ttl'), format='turtle')
    for s, p, o in g.triples((None, rdflib.URIRef(OPLHAS), None)):
        ttl_delegates.add(str(o))
    for s, p, o in g.triples((None, rdflib.URIRef(OPLON), None)):
        ttl_behalfof.add(str(o))
results['profile.ttl'] = (ttl_delegates, ttl_behalfof)

# --- profile.jsonld ---
jld_delegates = set()
jld_behalfof = set()
jsonld_path = os.path.join(out_dir, 'profile.jsonld')
if os.path.exists(jsonld_path):
    with open(jsonld_path) as f:
        jld = json.load(f)
    for item in jld.get('@graph', []):
        if 'oplcert:hasIdentityDelegate' in item:
            v = item['oplcert:hasIdentityDelegate']
            jld_delegates.add(v['@id'] if isinstance(v, dict) else v)
        if 'oplcert:onBehalfOf' in item:
            v = item['oplcert:onBehalfOf']
            jld_behalfof.add(v['@id'] if isinstance(v, dict) else v)
results['profile.jsonld'] = (jld_delegates, jld_behalfof)

# --- profile_rdfa.html ---
rdfa_delegates = set()
rdfa_behalfof = set()
rdfa_path = os.path.join(out_dir, 'profile_rdfa.html')
if os.path.exists(rdfa_path):
    # Parse embedded JSON-LD first
    with open(rdfa_path) as f:
        content = f.read()
    # Extract JSON-LD blocks
    import re as _re
    for match in _re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, _re.DOTALL):
        try:
            block = json.loads(match.group(1))
            for item in block.get('@graph', []):
                if 'oplcert:hasIdentityDelegate' in item:
                    v = item['oplcert:hasIdentityDelegate']
                    rdfa_delegates.add(v['@id'] if isinstance(v, dict) else v)
                if 'oplcert:onBehalfOf' in item:
                    v = item['oplcert:onBehalfOf']
                    rdfa_behalfof.add(v['@id'] if isinstance(v, dict) else v)
        except json.JSONDecodeError:
            pass
    # Also check RDFa rel attributes
    class DelegationParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.delegates = set()
            self.behalfof = set()
        def handle_starttag(self, tag, attrs):
            d = dict(attrs)
            rel = d.get('rel', '')
            href = d.get('resource', '') or d.get('href', '')
            if rel == 'oplcert:hasIdentityDelegate' and href:
                self.delegates.add(href)
            if rel == 'oplcert:onBehalfOf' and href:
                self.behalfof.add(href)
    dp = DelegationParser()
    dp.feed(content)
    rdfa_delegates.update(dp.delegates)
    rdfa_behalfof.update(dp.behalfof)
results['profile_rdfa.html'] = (rdfa_delegates, rdfa_behalfof)

# --- index.html ---
idx_delegates = set()
idx_behalfof = set()
idx_path = os.path.join(out_dir, 'index.html')
if os.path.exists(idx_path):
    with open(idx_path) as f:
        content = f.read()
    # Embedded JSON-LD
    import re as _re
    for match in _re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, _re.DOTALL):
        try:
            block = json.loads(match.group(1))
            for item in block.get('@graph', []):
                if 'oplcert:hasIdentityDelegate' in item:
                    v = item['oplcert:hasIdentityDelegate']
                    idx_delegates.add(v['@id'] if isinstance(v, dict) else v)
                if 'oplcert:onBehalfOf' in item:
                    v = item['oplcert:onBehalfOf']
                    idx_behalfof.add(v['@id'] if isinstance(v, dict) else v)
        except json.JSONDecodeError:
            pass
    # RDFa property attrs (<link property="oplcert:hasIdentityDelegate" href="...">)
    class IndexPropParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.delegates = set()
            self.behalfof = set()
        def handle_starttag(self, tag, attrs):
            d = dict(attrs)
            prop = d.get('property', '')
            href = d.get('href', '') or d.get('resource', '') or d.get('content', '')
            if prop == 'oplcert:hasIdentityDelegate' and href:
                self.delegates.add(href)
            if prop == 'oplcert:onBehalfOf' and href:
                self.behalfof.add(href)
            if d.get('rel') == 'oplcert:hasIdentityDelegate':
                self.delegates.add(d.get('resource', '') or d.get('href', ''))
            if d.get('rel') == 'oplcert:onBehalfOf':
                self.behalfof.add(d.get('resource', '') or d.get('href', ''))
    ip = IndexPropParser()
    ip.feed(content)
    idx_delegates.update(ip.delegates)
    idx_behalfof.update(ip.behalfof)
results['index.html'] = (idx_delegates, idx_behalfof)

# Check if delegation is present at all
all_delegates = set()
all_behalfof = set()
for fname, (dels, bofs) in results.items():
    all_delegates.update(dels)
    all_behalfof.update(bofs)

if not all_delegates and not all_behalfof:
    print("  No delegation triples found — skipping consistency check")
    sys.exit(0)

# Report per file
print("  Checking delegation consistency across all representations...")
for fname, (dels, bofs) in results.items():
    dels_str = ', '.join(sorted(dels)) if dels else '(none)'
    bofs_str = ', '.join(sorted(bofs)) if bofs else '(none)'
    print(f"    {fname}:")
    print(f"      hasIdentityDelegate → {dels_str}")
    print(f"      onBehalfOf         → {bofs_str}")

# hasIdentityDelegate consistency
if all_delegates:
    for fname, (dels, bofs) in results.items():
        if dels != all_delegates:
            print(f"  ✗ {fname}: hasIdentityDelegate mismatch")
            print(f"    expected: {', '.join(sorted(all_delegates))}")
            print(f"    got:      {', '.join(sorted(dels))}")
            fail = 1
    if not fail:
        print(f"  ✓ hasIdentityDelegate consistent across all files → {', '.join(sorted(all_delegates))}")

# onBehalfOf consistency
if all_behalfof:
    for fname, (dels, bofs) in results.items():
        if bofs != all_behalfof:
            print(f"  ✗ {fname}: onBehalfOf mismatch")
            print(f"    expected: {', '.join(sorted(all_behalfof))}")
            print(f"    got:      {', '.join(sorted(bofs))}")
            fail = 1
    if not fail:
        print(f"  ✓ onBehalfOf consistent across all files → {', '.join(sorted(all_behalfof))}")

sys.exit(fail)
PYEOF

export OUT_DIR
if python3 -c "$PY_DEL_GATE"; then
    echo "  Delegation Consistency Test: PASS"
else
    echo "  Delegation Consistency Test: FAIL — Delegation triples inconsistent across files!"
    GATE_FAILED=1
fi

if [ "$GATE_FAILED" -ne 0 ]; then
    echo ""
    echo "=== GATE BLOCKED: Identity generation aborted due to consistency failure ==="
    echo "  One or more consistency gates failed. Review errors above before delivery."
    exit 1
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
