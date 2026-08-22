#!/bin/bash
# refresh-loader.sh — regenerate load-agent-rdf-memory.sql from the current store,
# then print the commands to load it and verify the graph (credentials are yours).
#
# Usage:
#   bash refresh-loader.sh            # regenerate + print isql/gate commands
#   bash refresh-loader.sh --check    # regenerate, then run the SPARQL gate
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STORE="${AGENT_RDF_MEMORY_STORE:-$(dirname "$HERE")}"   # agent-rdf-memory/
PY="${HERE}/generate-loader-sql.py"
SQL="${HERE}/load-agent-rdf-memory.sql"
GATE="${HERE}/session-graph-gate.py"

echo "== regenerating loader from store: $STORE =="
python3 "$PY" --store "$STORE" --out "$SQL"

echo
echo "== run the load with YOUR credentials (password never shown) =="
echo "    isql 1111 dba <dba-password> -f \"$SQL\""

if [ "${1:-}" = "--check" ]; then
    echo
    echo "== verifying session graphs via SPARQL =="
    python3 "$GATE" check --all
fi
