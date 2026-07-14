#!/bin/bash
#
# bulk-load-ntriples.sh — Load gzip-compressed N-Triples into Virtuoso via isql,
# using ld_dir + rdf_loader_run.  Virtuoso reads .gz files directly — no extraction needed.
#
# Usage:
#   ./bulk-load-ntriples.sh                              \
#       --host      localhost                             \
#       --port      1111                                  \
#       --user      dba                                   \
#       --pass      dba                                   \
#       --graph     https://example.com/my-graph          \
#       --dir       /data/rdf/incoming                    \
#       dataset.nt.gz
#
#   --dir   Server-side directory containing (or receiving) the file(s).
#           The script copies the archive there unless --no-copy is given.
#
#   --graph Target named-graph IRI (required).
#
#   --host / --port   Virtuoso SQL listener (default: localhost:1111).
#
# Prerequisites:
#   isql — Virtuoso command-line SQL tool (on PATH)

set -euo pipefail

# ---------------------------------------------------------------------------
# defaults
# ---------------------------------------------------------------------------
HOST="localhost"
PORT="1111"
USER="dba"
PASS="dba"
GRAPH=""
STAGE_DIR=""
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

# If the file pattern is a single file and it exists, use that name;
# otherwise trust the --pattern argument.
if [[ -f "${LOAD_DIR}/${ARCHIVE_NAME}" ]] && [[ "$PATTERN" = "*.nt.gz" ]]; then
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
