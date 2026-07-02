#!/usr/bin/env bash
# s3-list.sh — list objects under a bucket/prefix on AWS S3 or an S3-compatible endpoint.
#
# Usage:
#   ./s3-list.sh --bucket commoncrawl --prefix cc-index/table/cc-main/warc/ --anonymous
#   ./s3-list.sh --bucket my-bucket --prefix models/ --profile hf
#
# --anonymous maps to `aws --no-sign-request` (public AWS buckets, e.g. Common Crawl).
# --profile <name> uses a pre-configured ~/.aws/config profile (required for non-AWS
# S3-compatible endpoints such as Hugging Face Storage Buckets — see references/endpoint-profiles.md).

set -euo pipefail

BUCKET=""
PREFIX=""
ANONYMOUS=0
PROFILE=""
RECURSIVE=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bucket) BUCKET="$2"; shift 2 ;;
    --prefix) PREFIX="$2"; shift 2 ;;
    --anonymous) ANONYMOUS=1; shift ;;
    --profile) PROFILE="$2"; shift 2 ;;
    --no-recursive) RECURSIVE=0; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

[[ -n "$BUCKET" ]] || { echo "--bucket is required" >&2; exit 1; }
command -v aws >/dev/null || { echo "aws CLI not found on PATH" >&2; exit 1; }

ARGS=(s3 ls "s3://${BUCKET}/${PREFIX}")
[[ "$RECURSIVE" -eq 1 ]] && ARGS+=(--recursive)

if [[ "$ANONYMOUS" -eq 1 ]]; then
  aws --no-sign-request "${ARGS[@]}"
elif [[ -n "$PROFILE" ]]; then
  aws --profile "$PROFILE" "${ARGS[@]}"
else
  aws "${ARGS[@]}"
fi
