# S3 API Query Client

Query data directly at S3 and S3-compatible endpoints — no bulk download required:

```bash
# Query a public AWS bucket's Parquet index in place
./scripts/duckdb-s3-query.sh --sql "
  SELECT url_host_registered_domain, count(*) AS pages
  FROM read_parquet('s3://commoncrawl/cc-index/table/cc-main/warc/crawl=CC-MAIN-2018-05/subset=warc/*.parquet')
  WHERE url_host_tld = 'no'
  GROUP BY url_host_registered_domain
  ORDER BY pages DESC LIMIT 20"

# Same technique against a Hugging Face Storage Bucket (S3-compatible gateway)
./scripts/duckdb-s3-query.sh \
  --sql-file query.sql \
  --endpoint s3.hf.co/<namespace> \
  --key-id "$S3_KEY_ID" --secret "$S3_SECRET"

# List objects under a prefix
./scripts/s3-list.sh --bucket commoncrawl --prefix cc-index/table/cc-main/warc/ --anonymous
```

Covers AWS S3 (public and private buckets), Hugging Face Storage Buckets (`s3.hf.co`), and other S3-compatible stores (Cloudflare R2, MinIO, Wasabi, Backblaze B2) via DuckDB `httpfs` for in-place SQL, plus AWS CLI/boto3/rclone for object-level operations.

See `SKILL.md` for the full workflow, endpoint profiles, query templates (T1–T7), and troubleshooting. Worked examples for querying the Common Crawl Foundation index — both the AWS-hosted columnar index and a Hugging Face Storage Bucket-hosted index — are in `examples/`.
