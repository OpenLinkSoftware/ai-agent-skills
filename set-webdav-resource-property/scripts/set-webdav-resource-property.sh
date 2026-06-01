#!/usr/bin/env bash
# set-webdav-resource-property.sh
# Skill: set-webdav-resource-property
# https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/set-webdav-resource-property
#
# Usage:
#   ./set-webdav-resource-property.sh -u USER [-p PASS] -b BASE [-f PATH_LIST.txt] [-n PROP] [-s NS_URI] [-v]
#
# Purpose:
#   Set a human-readable metadata value for a WebDAV resource via PROPPATCH using curl.
#   The namespace declaration is placed on the root element and the property element
#   contains only the plain text value.
#
# Defaults:
#   PROP defaults to "schema:name".
#   Known default namespaces: schema -> http://schema.org/ , dc -> http://purl.org/dc/elements/1.1/
#
set -euo pipefail

usage(){
  cat <<USAGE
Usage: $0 -u USER [-p PASS] -b BASE [-f FILE] [-n PROP] [-s NS_URI] [-v] [-h]

  -u USER   WebDAV username (required)
  -p PASS   WebDAV password (if omitted you'll be prompted)
  -b BASE   Base URL (required), e.g. https://linkeddata.uriburner.com
  -f FILE   Optional file with resource paths (one per line). If omitted, reads from stdin.
  -n PROP   Property to set (default: schema:name). Use prefix:local (e.g. schema:name or dc:title)
  -s NS_URI Namespace URI to declare for the prefix of PROP (optional). Overrides known defaults.
  -v        Verbose mode (show generated XML and responses)
  -h        Show this help
USAGE
}

# Simple XML escaper
xmlescape() {
  sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g' \
      -e "s/'/\&apos;/g" -e 's/\"/\&quot;/g'
}

# Naive title-case
titlecase() {
  awk '{
    for(i=1;i<=NF;i++){
      $i = toupper(substr($i,1,1)) tolower(substr($i,2))
    }
    print
  }'
}

# Known namespace mapping function (POSIX-safe replacement for associative arrays)
get_known_ns() {
  case "$1" in
    schema) printf '%s' "http://schema.org/" ;;
    dc)     printf '%s' "http://purl.org/dc/elements/1.1/" ;;
    *)      printf '%s' "" ;;
  esac
}

# Defaults
USER=""
PASS=""
BASE=""
FILE=""
PROP="schema:name"
NS_URI=""
VERBOSE=false

# Parse args
while getopts ":u:p:b:f:n:s:vh" opt; do
  case $opt in
    u) USER="$OPTARG" ;;
    p) PASS="$OPTARG" ;;
    b) BASE="$OPTARG" ;;
    f) FILE="$OPTARG" ;;
    n) PROP="$OPTARG" ;;
    s) NS_URI="$OPTARG" ;;
    v) VERBOSE=true ;;
    h) usage; exit 0 ;;
    \?) echo "Invalid option -$OPTARG" >&2; usage; exit 1 ;;
    :) echo "Option -$OPTARG requires an argument." >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$USER" || -z "$BASE" ]]; then
  echo "USER and BASE are required." >&2
  usage
  exit 1
fi

if [[ -z "${PASS:-}" ]]; then
  read -s -p "Password for $USER: " PASS
  echo
fi

# Read resource list either from FILE or stdin
if [[ -n "$FILE" ]]; then
  if [[ ! -f "$FILE" ]]; then
    echo "File not found: $FILE" >&2
    exit 1
  fi
  exec 3<"$FILE"
else
  exec 3<&0
fi

# Normalize base (no trailing slash)
BASE="${BASE%/}"

# Parse PROP into prefix and local name
if [[ "$PROP" == *:* ]]; then
  PREFIX="${PROP%%:*}"
  LOCALNAME="${PROP#*:}"
else
  PREFIX=""
  LOCALNAME="$PROP"
fi

# Determine namespace URI for prefix (if any)
if [[ -n "$PREFIX" ]]; then
  if [[ -n "$NS_URI" ]]; then
    NS_DECL="$NS_URI"
  else
    NS_DECL="$(get_known_ns "$PREFIX")"
  fi

  if [[ -z "$NS_DECL" ]]; then
    if $VERBOSE; then
      echo "Warning: no namespace URI supplied for prefix '$PREFIX' and no known default."
      echo "The generated PROPPATCH will include a prefixed element without an xmlns declaration,"
      echo "which some servers may reject. Consider using -s to provide the namespace URI."
    fi
  fi
else
  NS_DECL=""
fi

# Build root namespace attributes string (only include prefix xmlns if NS_DECL available)
build_ns_attrs() {
  local attrs=""
  if [[ -n "$PREFIX" && -n "$NS_DECL" ]]; then
    attrs=" xmlns:${PREFIX}=\"${NS_DECL}\""
  fi
  printf '%s' "$attrs"
}

# Template for PROPPATCH with placeholders to avoid accidental inline xmlns on the property element
read -r -d '' XML_TEMPLATE <<'EOF' || true
<?xml version="1.0" encoding="utf-8"?>
<D:propertyupdate xmlns:D="DAV:"{NS_ATTRS_PLACEHOLDER}>
  <D:set>
    <D:prop>
      {PROP_OPEN}{TITLE_TEXT}{PROP_CLOSE}
    </D:prop>
  </D:set>
</D:propertyupdate>
EOF

# Main loop: process resource list
while IFS= read -r rawpath <&3 || [[ -n "$rawpath" ]]; do
  # skip empty / commented lines
  [[ -z "$rawpath" ]] && continue
  [[ "$rawpath" =~ ^[[:space:]]*# ]] && continue

  path="$(printf "%s" "$rawpath" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"

  # Build final URL
  if [[ "$path" =~ ^https?:// ]]; then
    url="$path"
    filename="$(basename "$path")"
  else
    if [[ "$path" =~ ^/ ]]; then
      url="${BASE}${path}"
    else
      url="${BASE}/${path}"
    fi
    filename="$(basename "$path")"
  fi

  ext="${filename##*.}"
  basefn="${filename%.*}"

  # Friendly title generation
  friendly="$(printf "%s" "$basefn" | sed -E 's/%20/ /g; s/[_-]+/ /g; s/[[:space:]]+/ /g')"
  friendly="$(printf "%s" "$friendly" | titlecase)"

  # Convert extension to lowercase for case-insensitive comparison (POSIX compatible)
  ext_lower="$(printf "%s" "$ext" | tr '[:upper:]' '[:lower:]')"
  case "$ext_lower" in
    pdf) type_tag="(PDF)" ;;
    mp4|mkv|webm) type_tag="(Video)" ;;
    png|jpg|jpeg|gif|svg) type_tag="(Image)" ;;
    wav|mp3|m4a) type_tag="(Audio)" ;;
    html|htm) type_tag="(WebPage)" ;;
    *) type_tag="" ;;
  esac

  title="$(printf "%s %s" "$friendly" "$type_tag" | sed -E 's/[[:space:]]+$//')"
  title_escaped="$(printf "%s" "$title" | xmlescape)"

  # Prepare namespace attributes and property element tokens
  NS_ATTRS="$(build_ns_attrs)"

  # Construct full property name for display purposes
  if [[ -n "$PREFIX" ]]; then
    PROP_NAME="${PREFIX}:${LOCALNAME}"
  else
    PROP_NAME="${LOCALNAME}"
  fi

  # For the property element, use the fully qualified name with namespace prefix
  PROP_OPEN="<${PREFIX}:${LOCALNAME}>"
  PROP_CLOSE="</${PREFIX}:${LOCALNAME}>"

  # Substitute placeholders in template to create final XML
  xml="${XML_TEMPLATE//\{NS_ATTRS_PLACEHOLDER\}/${NS_ATTRS}}"
  xml="${xml//\{PROP_OPEN\}/${PROP_OPEN}}"
  xml="${xml//\{PROP_CLOSE\}/${PROP_CLOSE}}"
  xml="${xml//\{TITLE_TEXT\}/${title_escaped}}"

  # Verbose output
  if $VERBOSE; then
    echo "------------------------------------------------------------"
    echo "Resource: $path"
    echo "  URL           : $url"
    echo "  Filename      : $filename"
    echo "  Generated title: $title"
    if [[ -n "$NS_DECL" ]]; then
      echo "  Property      : ${NS_DECL}${LOCALNAME}"
      echo "  Property (QName): ${PROP_NAME}"
    else
      echo "  Property      : ${PROP_NAME}"
    fi
    if [[ -n "$NS_DECL" ]]; then
      echo "  Namespace     : ${NS_DECL} (declared on root)"
    else
      [[ -n "$PREFIX" ]] && echo "  Namespace     : (none declared for prefix '$PREFIX')"
    fi
    echo
    echo "PROPPATCH XML to send:"
    printf '%s\n' "$xml"
    echo "Sending PROPPATCH..."
    echo "Note: The property value in the XML is the text content between the property tags."
    echo "      A proper WebDAV server should extract just the text content and store it as the property value."
  else
    printf "Setting title for %s ... " "$url"
  fi

  # Send PROPPATCH via curl
  if $VERBOSE; then
    curl -u "${USER}:${PASS}" -X PROPPATCH "$url" \
      -H "Content-Type: application/xml; charset=utf-8" \
      --data "$xml" -i --http1.1 || {
        rc=$?
        echo "curl failed with exit code $rc" >&2
      }
    echo "Done."
  else
    http_out=$(curl -sS -u "${USER}:${PASS}" -X PROPPATCH "$url" \
      -H "Content-Type: application/xml; charset=utf-8" \
      --data "$xml" -w "HTTP_CODE:%{http_code}" ) || {
        echo "FAILED"
        continue
      }
    http_code="${http_out##*HTTP_CODE:}"
    body="${http_out%HTTP_CODE:*}"
    printf "HTTP %s\n" "$http_code"
    if [[ -n "${body//[[:space:]]/}" ]]; then
      printf "  Response (truncated): %.200s\n" "$(echo "$body" | tr '\n' ' ' )"
    fi
  fi

done

# End of script
