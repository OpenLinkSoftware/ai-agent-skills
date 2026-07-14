#!/bin/bash
#
# bulk-load-rdf.sh — Load RDF archives into Virtuoso via isql,
# using ld_dir + rdf_loader_run.  Supports all RDF formats:
#   N-Triples, Turtle, RDF/XML, N-Quads, TriG, JSON-LD, Notation3
#   (gzip-compressed or raw).  No extraction needed — Virtuoso reads .gz natively.
#
# Usage:
#   ./bulk-load-rdf.sh                                    \
#       --host      localhost                             \
#       --port      1111                                  \
#       --user      dba                                   \
#       --pass      dba                                   \
#       --graph     https://example.com/my-graph          \
#       --dir       /data/rdf/incoming                    \
#       --pattern   "*.nt.gz"                             \
#       dataset.nt.gz
#
#   --dir      Server-side directory containing (or receiving) the file(s).
#              The script copies the archive there unless --no-copy is given.
#   --pattern  File pattern for ld_dir (default: *.nt.gz).
#              Use *.ttl.gz, *.rdf.gz, *.nq.gz, *.trig.gz, *.jsonld.gz, or * for all.
#   --graph    Target named-graph IRI (required).
#   --host / --port   Virtuoso SQL listener (default: localhost:1111).
#
# Prerequisites:
#   isql — Virtuoso command-line SQL tool (on PATH)
#
# Environment variables (fallback when flags omitted):
#   VIRTUOSO_HOST  — SQL listener hostname (overridden by --host)
#   VIRTUOSO_PORT  — SQL listener port    (overridden by --port)
#   VIRTUOSO_USER  — isql username        (overridden by --user)
#   VIRTUOSO_PASS  — isql password        (overridden by --pass)
#   VIRTUOSO_GRAPH — default graph IRI    (overridden by --graph)
#   VIRTUOSO_DIR   — server-side staging  (overridden by --dir)
#
#   Set them for GUI apps on macOS (they don't read shell dotfiles):
#     launchctl setenv VIRTUOSO_HOST  linkeddata.uriburner.com
#     launchctl setenv VIRTUOSO_PORT  1116
#     launchctl setenv VIRTUOSO_USER  dba
#     launchctl setenv VIRTUOSO_PASS  <password>

set -euo pipefail

# ---------------------------------------------------------------------------
# defaults
# ---------------------------------------------------------------------------
HOST="${VIRTUOSO_HOST:-localhost}"
PORT="${VIRTUOSO_PORT:-1111}"
USER="${VIRTUOSO_USER:-dba}"
PASS="${VIRTUOSO_PASS:-dba}"
GRAPH="${VIRTUOSO_GRAPH:-}"
STAGE_DIR="${VIRTUOSO_DIR:-}"
ARCHIVE=""
NO_COPY=false
PATTERN="*.nt.gz"

usage() {
  sed -n '/^#/{/^#!/d;s/^# //;p}' "$0"
  exit 1
}

# ---------------------------------------------------------------------------
# arg parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)     HOST="$2";      shift 2 ;;
    --port)     PORT="$2";      shift 2 ;;
    --user)     USER="$2";      shift 2 ;;
    --pass)     PASS="$2";      shift 2 ;;
    --graph)    GRAPH="$2";     shift 2 ;;
    --dir)      STAGE_DIR="$2"; shift 2 ;;
    --pattern)  PATTERN="$2";   shift 2 ;;
    --no-copy)  NO_COPY=true;   shift   ;;
    -h|--help)  usage ;;
    *)          ARCHIVE="$1";   shift   ;;
  esac
done

# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------
if [[ -z "$ARCHIVE" ]]; then
  echo "ERROR: no archive specified" >&2
  usage
fi
if [[ ! -f "$ARCHIVE" ]]; then
  echo "ERROR: archive not found: $ARCHIVE" >&2
  exit 1
fi
if [[ -z "$GRAPH" ]]; then
  echo "ERROR: --graph is required" >&2
  usage
fi

ARCHIVE_ABS="$(cd "$(dirname "$ARCHIVE")" && pwd)/$(basename "$ARCHIVE")"
ARCHIVE_NAME="$(basename "$ARCHIVE_ABS")"

# staging directory
if [[ -z "$STAGE_DIR" ]]; then
  STAGE_DIR="$(mktemp -d "/tmp/rdf-load-$(date +%Y%m%d-%H%M%S)-XXXX")"
  echo "Staging directory: $STAGE_DIR"
else
  mkdir -p "$STAGE_DIR"
fi

ISQL="isql ${HOST}:${PORT} ${USER} ${PASS}"

# ---------------------------------------------------------------------------
# stage the archive
# ---------------------------------------------------------------------------
if $NO_COPY; then
  LOAD_DIR="$STAGE_DIR"
  echo "Using existing server-side directory: ${LOAD_DIR}"
else
  cp "$ARCHIVE_ABS" "$STAGE_DIR/"
  LOAD_DIR="$STAGE_DIR"
  echo "Copied ${ARCHIVE_NAME} → ${LOAD_DIR}"
fi

# When a single file was staged, use its exact name as the pattern
if [[ -f "${LOAD_DIR}/${ARCHIVE_NAME}" ]]; then
  PATTERN="${ARCHIVE_NAME}"
fi

# ---------------------------------------------------------------------------
# register & load
# ---------------------------------------------------------------------------
echo "Registering: ld_dir('${LOAD_DIR}', '${PATTERN}', '${GRAPH}')"

$ISQL <<EOF
ld_dir ('${LOAD_DIR}', '${PATTERN}', '${GRAPH}');
rdf_loader_run ();
CHECKPOINT;
EOF

echo "Load started. Monitoring DB.DBA.LOAD_LIST ..."
sleep 2

# ---------------------------------------------------------------------------
# monitor until done
# ---------------------------------------------------------------------------
while true; do
  STATUS=$($ISQL <<'EOSQL' 2>/dev/null | grep -v '^Rows\|^$'
SELECT ll_file, ll_state, ll_started, ll_done, ll_error
FROM DB.DBA.LOAD_LIST
WHERE ll_file IN (
  SELECT ll_file FROM DB.DBA.LOAD_LIST
  WHERE ll_state <> 2
);
EOSQL
)
  echo "$STATUS"

  if echo "$STATUS" | grep -q 'No\. of rows\|0 rows'; then
    echo "Loader finished — no rows in progress."
    break
  fi
  if echo "$STATUS" | grep -qi 'error'; then
    echo "Errors detected — review the output above."
    break
  fi

  sleep 5
done

echo ""
echo "Final load summary:"
$ISQL <<EOF
SELECT ll_file, ll_state, ll_started, ll_done, ll_error
FROM DB.DBA.LOAD_LIST;
EOF
