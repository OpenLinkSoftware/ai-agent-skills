#!/usr/bin/env bash
# duckdb-s3-query.sh — run a SQL query/file against an S3 or S3-compatible endpoint via DuckDB httpfs.
#
# Usage:
#   ./duckdb-s3-query.sh --sql "SELECT count(*) FROM read_parquet('s3://commoncrawl/...')" [--region us-east-1]
#   ./duckdb-s3-query.sh --sql-file query.sql --endpoint s3.hf.co/<namespace> --key-id "$S3_KEY_ID" --secret "$S3_SECRET"
#
# Anonymous AWS buckets need no --endpoint/--key-id/--secret; just pass --region if the bucket requires one.
# Non-AWS S3-compatible endpoints (Hugging Face Storage Buckets, R2, MinIO, ...) need --endpoint, --key-id, --secret.

set -euo pipefail

REGION="us-east-1"
URL_STYLE="path"
ENDPOINT=""
KEY_ID=""
SECRET=""
SQL=""
SQL_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sql) SQL="$2"; shift 2 ;;
    --sql-file) SQL_FILE="$2"; shift 2 ;;
    --endpoint) ENDPOINT="$2"; shift 2 ;;
    --key-id) KEY_ID="$2"; shift 2 ;;
    --secret) SECRET="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$SQL" && -z "$SQL_FILE" ]]; then
  echo "Provide --sql \"<query>\" or --sql-file <path>" >&2
  exit 1
fi

command -v duckdb >/dev/null || { echo "duckdb not found on PATH — install it (brew install duckdb / pip install duckdb) or use the AWS CLI/boto3 path instead." >&2; exit 1; }

PRELUDE="INSTALL httpfs; LOAD httpfs; SET s3_region='${REGION}';"

if [[ -n "$ENDPOINT" ]]; then
  if [[ -z "$KEY_ID" || -z "$SECRET" ]]; then
    echo "Non-AWS endpoint given but --key-id/--secret missing — refusing to guess credentials." >&2
    exit 1
  fi
  PRELUDE="${PRELUDE}
CREATE SECRET s3_endpoint (TYPE s3, KEY_ID '${KEY_ID}', SECRET '${SECRET}', ENDPOINT '${ENDPOINT}', URL_STYLE '${URL_STYLE}', REGION '${REGION}');"
fi

if [[ -n "$SQL_FILE" ]]; then
  BODY="$(cat "$SQL_FILE")"
else
  BODY="$SQL"
fi

duckdb -c "${PRELUDE}
${BODY}"
