#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES="$SKILL_DIR/assets/templates"
TMPDIR=$(mktemp -d)
PASS=0
FAIL=0
RESULTS=()

cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT

echo "=== Fediverse CRUD Test Harness ==="
echo ""

# --- Dependencies ---
for cmd in curl jq python3; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "ERROR: $cmd is required but not found." >&2
    exit 1
  fi
done

# --- Elicit ---
read -r -p "Fediverse instance hostname: " INSTANCE
read -r -p "Your handle: " USER_HANDLE
read -r -p "Second handle (for Follow/delivery test): " SECOND_USER
read -r -p "OAuth scopes (e.g., read write follow push): " SCOPES
read -r -p "Note content to post: " NOTE_CONTENT
read -r -p "Object URI to like (Enter to skip): " LIKE_OBJECT
read -r -p "Object URI to boost (Enter to skip): " ANN_OBJECT
read -r -p "Actor URI to follow (Enter to skip, defaults to second user): " FOLLOW_TARGET
FOLLOW_TARGET="${FOLLOW_TARGET:-}"
echo ""

BASE="https://$INSTANCE"
ACTOR_URI=""
ACTOR2_URI=""
INBOX=""
OUTBOX=""
INBOX2=""
SHARED_INBOX=""
TOKEN=""
ACCEPT_LD='Accept: application/ld+json; profile="https://www.w3.org/ns/activitystreams"'
ACCEPT_AP='Accept: application/activity+json'

# --- Phase 1: Resolve actors via WebFinger ---
resolve_actor() {
  local handle="$1"
  local meta wf_url wf actor

  echo ">> Resolving $handle@$INSTANCE"

  meta=$(curl -sk "$BASE/.well-known/host-meta.json" 2>/dev/null) || {
    echo "ERROR: Cannot fetch host-meta.json from $BASE" >&2
    return 1
  }

  lrdd_template=$(echo "$meta" | jq -r '.links[] | select(.rel=="lrdd") | .template' 2>/dev/null) || {
    echo "ERROR: No lrdd template in host-meta.json" >&2
    return 1
  }

  resource="acct:${handle}@${INSTANCE}"
  wf_url=$(echo "$lrdd_template" | sed "s|{uri}|$resource|g")
  wf=$(curl -sk -H "Accept: application/jrd+json" "$wf_url" 2>/dev/null) || {
    echo "ERROR: WebFinger query failed for $resource" >&2
    return 1
  }

  actor=$(echo "$wf" | jq -r '.links[] | select(.type=="application/activity+json") | .href' 2>/dev/null)
  if [ -z "$actor" ] || [ "$actor" = "null" ]; then
    echo "ERROR: No activity+json link in WebFinger response for $resource" >&2
    return 1
  fi

  echo "$actor"
  return 0
}

echo "--- Phase 1: WebFinger Resolution ---"
ACTOR_URI=$(resolve_actor "$USER_HANDLE") || exit 1
echo "  Actor 1: $ACTOR_URI"
ACTOR2_URI=$(resolve_actor "$SECOND_USER") || exit 1
echo "  Actor 2: $ACTOR2_URI"
echo ""

# --- Phase 2: Fetch actor documents ---
echo "--- Phase 2: Actor Documents ---"
actor_doc=$(curl -skL -H "$ACCEPT_LD" "$ACTOR_URI" 2>/dev/null)
if [ -z "$actor_doc" ]; then
  actor_doc=$(curl -skL -H "$ACCEPT_AP" "$ACTOR_URI" 2>/dev/null)
fi
OUTBOX=$(echo "$actor_doc" | jq -r '.outbox // empty')
INBOX=$(echo "$actor_doc" | jq -r '.inbox // empty')
SHARED_INBOX=$(echo "$actor_doc" | jq -r '.endpoints.sharedInbox // empty')
echo "  Outbox: $OUTBOX"
echo "  Inbox: $INBOX"
echo "  SharedInbox: $SHARED_INBOX"

actor2_doc=$(curl -skL -H "$ACCEPT_LD" "$ACTOR2_URI" 2>/dev/null)
if [ -z "$actor2_doc" ]; then
  actor2_doc=$(curl -skL -H "$ACCEPT_AP" "$ACTOR2_URI" 2>/dev/null)
fi
INBOX2=$(echo "$actor2_doc" | jq -r '.inbox // empty')
echo "  Actor2 Inbox: $INBOX2"
echo ""

# --- Phase 3: OAuth Authorization Code flow ---
echo "--- Phase 3: OAuth Authorization Code Flow ---"

oidc=$(curl -sk "$BASE/.well-known/openid-configuration" 2>/dev/null) || {
  echo "ERROR: Cannot fetch OIDC configuration" >&2
  exit 1
}
REG_EP=$(echo "$oidc" | jq -r '.registration_endpoint // empty')
AUTH_EP=$(echo "$oidc" | jq -r '.authorization_endpoint // empty')
TOKEN_EP=$(echo "$oidc" | jq -r '.token_endpoint // empty')
echo "  Registration: $REG_EP"
echo "  Authorize: $AUTH_EP"
echo "  Token: $TOKEN_EP"

# Register dynamic client
REDIRECT_URI="http://127.0.0.1:12345/callback"
reg_resp=$(curl -sk -X POST "$REG_EP" \
  -H "Content-Type: application/json" \
  -d "$(cat <<EOF
{
  "client_name": "fediverse-test-harness",
  "redirect_uris": ["$REDIRECT_URI"],
  "grant_types": ["authorization_code"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "client_secret_basic",
  "scope": "$SCOPES"
}
EOF
)" 2>/dev/null)
CID=$(echo "$reg_resp" | jq -r '.client_id // empty')
SECRET=$(echo "$reg_resp" | jq -r '.client_secret // ""')
if [ -z "$CID" ] || [ "$CID" = "null" ]; then
  echo "ERROR: Dynamic client registration failed" >&2
  echo "  Response: $reg_resp" >&2
  exit 1
fi
echo "  Client ID: $CID"
echo ""

# Build authorize URL
STATE=$(uuidgen 2>/dev/null || echo "fediverse-test-$$")
AUTH_URL="${AUTH_EP}?response_type=code&client_id=${CID}&redirect_uri=${REDIRECT_URI}&scope=${SCOPES}&state=${STATE}"

# Start callback server and open browser
echo "  Starting callback server on http://127.0.0.1:12345 ..."
echo "  Open this URL in your browser:"
echo ""
echo "    $AUTH_URL"
echo ""
echo "  (Login via Digest prompt, grant consent, wait for 'Authentication complete')"
echo ""

PYTHON_SCRIPT=$(cat <<'PYEOF'
import http.server, urllib.parse, json, sys, os, base64, uuid

ISSUER = os.environ.get("FEDIVERSE_ISSUER", "")
CID = os.environ.get("FEDIVERSE_CID", "")
SECRET = os.environ.get("FEDIVERSE_SECRET", "")
REDIRECT_URI = "http://127.0.0.1:12345/callback"
OUTPUT = "/tmp/fediverse_test_token.sh"

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(p.query)
        if 'code' not in params:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "waiting"}).encode())
            return
        code = params['code'][0]
        print(f"\n  Code captured. Exchanging for token ...", flush=True)
        creds_b64 = base64.b64encode(f"{CID}:{SECRET}".encode()).decode()
        body = f"grant_type=authorization_code&code={code}&redirect_uri={REDIRECT_URI}"
        try:
            import urllib.request
            req = urllib.request.Request(f"{ISSUER}/OAuth2/token", data=body.encode(),
                headers={"Content-Type": "application/x-www-form-urlencoded",
                         "Authorization": f"Basic {creds_b64}"})
            resp = urllib.request.urlopen(req).read()
            token_data = json.loads(resp)
            access_token = token_data["access_token"]
            refresh_token = token_data.get("refresh_token", "")
            with open(OUTPUT, 'w') as f:
                f.write(f"TOKEN={access_token}\n")
                f.write(f"CLIENT_ID={CID}\n")
                f.write(f"CLIENT_SECRET={SECRET}\n")
                f.write(f"REFRESH={refresh_token}\n")
                f.write(f"EXPIRES_AT=$(( $(date +%s) + {token_data['expires_in']} ))\n")
            print(f"  Bearer token obtained! Saved to {OUTPUT}", flush=True)
        except Exception as e:
            print(f"  Token exchange failed: {e}", flush=True)
            sys.exit(1)
        resp_body = ("<html><body style='font-family:sans-serif;text-align:center;padding:60px'>"
                     "<h1>Authentication complete</h1>"
                     "<p>You can close this tab and return to the terminal.</p></body></html>")
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(resp_body.encode())
        os._exit(0)
    def log_message(self, *a): pass

server = http.server.HTTPServer(('127.0.0.1', 12345), Handler)
server.handle_request()
PYEOF
)

export FEDIVERSE_ISSUER="$BASE"
export FEDIVERSE_CID="$CID"
export FEDIVERSE_SECRET="$SECRET"

python3 -c "$PYTHON_SCRIPT" 2>&1 || true

if [ ! -f /tmp/fediverse_test_token.sh ]; then
  echo "ERROR: OAuth flow did not complete" >&2
  exit 1
fi
source /tmp/fediverse_test_token.sh
echo "  Token: ${TOKEN:0:20}... (${#TOKEN} chars)"
echo ""

# --- Helper functions ---
record() {
  local op="$1" status="$2" detail="$3"
  if [ "$status" = "PASS" ]; then
    PASS=$((PASS + 1))
  else
    FAIL=$((FAIL + 1))
  fi
  RESULTS+=("$op|$status|$detail")
}

ap_post() {
  local outbox_uri="$1" payload_file="$2"
  local tmpfile="$TMPDIR/ap_headers_$$.txt"
  curl -sk -D "$tmpfile" -X POST "$outbox_uri" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"" \
    -d @"$payload_file" -o /dev/null 2>/dev/null
  grep -i "^location:" "$tmpfile" | sed 's/[Ll]ocation: //;s/\r//' | head -1
}

ap_get() {
  local uri="$1"
  local resp
  resp=$(curl -sk -w "%{http_code}" -H "Authorization: Bearer $TOKEN" \
    -H "$ACCEPT_LD" "$uri" 2>/dev/null)
  local code="${resp: -3}"
  if [ "$code" = "406" ]; then
    curl -sk -H "Authorization: Bearer $TOKEN" \
      -H "$ACCEPT_AP" "$uri" 2>/dev/null
  else
    echo "${resp:0:-3}"
  fi
}

now_iso() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

TIMESTAMP=$(now_iso)
CREATED_NOTE_ID=""

# --- Phase 3b: Ensure outbox is a proper collection (W3C §5.1) ---
echo "--- Phase 3b: Outbox Collection Setup (W3C §5.1) ---"
echo "  Checking outbox: $OUTBOX"
IS_COL=$(curl -sk -X PROPFIND "${OUTBOX%/}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Depth: 0" 2>/dev/null | grep -c 'resourcetype.*collection')
if [ "$IS_COL" -eq 0 ]; then
  echo "  Outbox is not a collection. Recreating as MKCOL..."
  curl -sk -X DELETE "${OUTBOX%/}" -H "Authorization: Bearer $TOKEN" -o /dev/null 2>/dev/null || true
  MKCOL_CODE=$(curl -sk -w "%{http_code}" -X MKCOL "${OUTBOX%/}" \
    -H "Authorization: Bearer $TOKEN" 2>/dev/null)
  if [ "$MKCOL_CODE" = "201" ]; then
    record "Outbox MKCOL" "PASS" "created as collection"
  else
    record "Outbox MKCOL" "FAIL" "HTTP $MKCOL_CODE"
  fi
else
  record "Outbox MKCOL" "PASS" "already a collection"
fi
echo ""

# --- Phase 4: Write operations ---
echo "--- Phase 4: Write Operations ---"

# 4a. Note
if [ -n "$NOTE_CONTENT" ]; then
  echo "  Posting Note ..."
  sed -e "s|{ACTOR_URI}|$ACTOR_URI|g" \
      -e "s|{CONTENT}|<p>$NOTE_CONTENT</p>|g" \
      -e "s|{TO}|https://www.w3.org/ns/activitystreams#Public|g" \
      -e "s|{CC}|${ACTOR_URI}/followers|g" \
      -e "s|{PUBLISHED}|$TIMESTAMP|g" \
      "$TEMPLATES/note.jsonld" > "$TMPDIR/note.json"
  NOTE_ID=$(ap_post "$OUTBOX" "$TMPDIR/note.json")
  if [ -n "$NOTE_ID" ]; then
    record "Note" "PASS" "$NOTE_ID"
    CREATED_NOTE_ID="$NOTE_ID"
  else
    record "Note" "FAIL" "no Location header in response"
  fi
else
  echo "  Skipping Note (no content provided)"
fi

# 4b. Like
if [ -n "$LIKE_OBJECT" ]; then
  echo "  Posting Like on $LIKE_OBJECT ..."
  sed -e "s|{ACTOR_URI}|$ACTOR_URI|g" \
      -e "s|{OBJECT_URI}|$LIKE_OBJECT|g" \
      -e "s|{TO}|$ACTOR2_URI|g" \
      -e "s|{PUBLISHED}|$(now_iso)|g" \
      "$TEMPLATES/like.jsonld" > "$TMPDIR/like.json"
  LIKE_ID=$(ap_post "$OUTBOX" "$TMPDIR/like.json")
  if [ -n "$LIKE_ID" ]; then
    record "Like" "PASS" "$LIKE_ID"
    LIKE_ACTIVITY_ID="$LIKE_ID"
  else
    record "Like" "FAIL" "no Location header in response"
  fi
else
  echo "  Skipping Like (no object provided)"
fi

# 4c. Announce (Boost)
if [ -n "$ANN_OBJECT" ]; then
  echo "  Posting Announce on $ANN_OBJECT ..."
  sed -e "s|{ACTOR_URI}|$ACTOR_URI|g" \
      -e "s|{OBJECT_URI}|$ANN_OBJECT|g" \
      -e "s|{TO}|${ACTOR_URI}/followers|g" \
      -e "s|{PUBLISHED}|$(now_iso)|g" \
      "$TEMPLATES/announce.jsonld" > "$TMPDIR/announce.json"
  ANN_ID=$(ap_post "$OUTBOX" "$TMPDIR/announce.json")
  if [ -n "$ANN_ID" ]; then
    record "Announce" "PASS" "$ANN_ID"
  else
    record "Announce" "FAIL" "no Location header in response"
  fi
else
  echo "  Skipping Announce (no object provided)"
fi

# 4d. Follow
if [ -z "$FOLLOW_TARGET" ]; then
  FOLLOW_TARGET="$ACTOR2_URI"
fi
echo "  Posting Follow on $FOLLOW_TARGET ..."
sed -e "s|{ACTOR_URI}|$ACTOR_URI|g" \
    -e "s|{TARGET_ACTOR_URI}|$FOLLOW_TARGET|g" \
    "$TEMPLATES/follow.jsonld" > "$TMPDIR/follow.json"
FOL_ID=$(ap_post "$OUTBOX" "$TMPDIR/follow.json")
if [ -n "$FOL_ID" ]; then
  record "Follow" "PASS" "$FOL_ID"
else
  record "Follow" "FAIL" "no Location header in response"
fi

# 4e. Undo the Like (if one was posted)
if [ -n "${LIKE_ACTIVITY_ID:-}" ]; then
  read -r -p "Undo type (Enter for default: Like): " UNDO_TYPE
  UNDO_TYPE="${UNDO_TYPE:-Like}"
  echo "  Posting Undo ($UNDO_TYPE) ..."
  sed -e "s|{ACTOR_URI}|$ACTOR_URI|g" \
      -e "s|{UNDO_TYPE}|$UNDO_TYPE|g" \
      -e "s|{OBJECT_URI}|$LIKE_OBJECT|g" \
      -e "s|{TO}|$ACTOR2_URI|g" \
      -e "s|{PUBLISHED}|$(now_iso)|g" \
      "$TEMPLATES/undo.jsonld" > "$TMPDIR/undo.json"
  UNDO_ID=$(ap_post "$OUTBOX" "$TMPDIR/undo.json")
  if [ -n "$UNDO_ID" ]; then
    record "Undo" "PASS" "$UNDO_ID"
  else
    record "Undo" "FAIL" "no Location header in response"
  fi
fi

# 4f. Delete the Note (if one was posted)
if [ -n "$CREATED_NOTE_ID" ]; then
  read -r -p "Delete which activity URI (Enter for default: the posted Note): " DEL_OBJECT
  DEL_OBJECT="${DEL_OBJECT:-$CREATED_NOTE_ID}"
  echo "  Posting Delete on $DEL_OBJECT ..."
  sed -e "s|{ACTOR_URI}|$ACTOR_URI|g" \
      -e "s|{OBJECT_URI}|$DEL_OBJECT|g" \
      -e "s|{TO}|${ACTOR_URI}/followers|g" \
      "$TEMPLATES/delete.jsonld" > "$TMPDIR/delete.json"
  DEL_ID=$(ap_post "$OUTBOX" "$TMPDIR/delete.json")
  if [ -n "$DEL_ID" ]; then
    record "Delete" "PASS" "$DEL_ID"
  else
    record "Delete" "FAIL" "no Location header in response"
  fi
fi

echo ""

# --- Phase 5: Read Operations ---
echo "--- Phase 5: Read Operations ---"

# 5a. Outbox
echo "  Reading outbox ..."
OUTBOX_DATA=$(ap_get "$OUTBOX")
OUTBOX_COUNT=$(echo "$OUTBOX_DATA" | jq '.totalItems // (.first | .orderedItems | length) // 0' 2>/dev/null)
if [ -n "$OUTBOX_COUNT" ] && [ "$OUTBOX_COUNT" != "null" ]; then
  record "Read outbox" "PASS" "$OUTBOX_COUNT items (or more)"
else
  record "Read outbox" "FAIL" "Could not parse outbox"
fi

# 5b. Deleted object (expect 410)
if [ -n "$CREATED_NOTE_ID" ]; then
  echo "  Verifying deletion (expect 410) ..."
  DEL_CHECK=$(curl -sk -o /dev/null -w "%{http_code}" \
    -H "$ACCEPT_LD" \
    "$CREATED_NOTE_ID" 2>/dev/null)
  if [ "$DEL_CHECK" = "410" ]; then
    record "Delete verify (410)" "PASS" "$DEL_CHECK"
  else
    record "Delete verify (410)" "FAIL" "Expected 410, got $DEL_CHECK"
  fi
fi

echo ""

# --- Phase 6: Delivery check ---
echo "--- Phase 6: Remote Delivery Check ---"
echo "  NOTE: To verify delivery, re-run with the second user's token."
echo "  The Follow activity was sent to the outbox. Server-side delivery"
echo "  via sharedInbox handles relaying to $SECOND_USER's inbox."
echo ""

# --- Report ---
echo "============================================"
echo "            TEST RESULTS"
echo "============================================"
for r in "${RESULTS[@]}"; do
  IFS='|' read -r op status detail <<< "$r"
  if [ "$status" = "PASS" ]; then
    printf "  ✓ %-20s %s\n" "$op" "$detail"
  else
    printf "  ✗ %-20s %s\n" "$op" "$detail"
  fi
done
echo ""
printf "  Passed: %d, Failed: %d\n" "$PASS" "$FAIL"
echo "============================================"
[ "$FAIL" -eq 0 ] && echo "  All tests passed!" || echo "  Some tests failed."
exit $FAIL
