# Query Templates (T1–T7 expanded)

Load this file before constructing any predefined query — it has the full parameter notes that SKILL.md only summarizes.

## T1 — List bucket / prefix contents

```bash
# Recursive listing, human-readable
aws [--no-sign-request | --profile <name>] s3 ls s3://<bucket>/<prefix>/ --recursive

# JSON, for scripting (ListObjectsV2 — required for HF/most gateways)
aws [--no-sign-request | --profile <name>] s3api list-objects-v2 \
  --bucket <bucket> --prefix <prefix>/ --query 'Contents[].{Key:Key,Size:Size}'
```

boto3 equivalent:

```python
paginator = s3.get_paginator("list_objects_v2")
for page in paginator.paginate(Bucket="<bucket>", Prefix="<prefix>/"):
    for obj in page.get("Contents", []):
        print(obj["Key"], obj["Size"])
```

## T2 — Head object (existence + metadata, no body transfer)

```bash
aws [--no-sign-request | --profile <name>] s3api head-object --bucket <bucket> --key <key>
```

## T3 — Get / download one object

```bash
aws [--no-sign-request | --profile <name>] s3 cp s3://<bucket>/<key> <local-path>
```

boto3:

```python
s3.download_file("<bucket>", "<key>", "<local-path>")
```

## T4 — Query a remote object in place (DuckDB httpfs)

```sql
INSTALL httpfs; LOAD httpfs;
-- optional CREATE SECRET block for non-AWS / private endpoints, see endpoint-profiles.md

SELECT * FROM read_parquet('s3://<bucket>/<key-or-glob>.parquet') LIMIT 20;
SELECT * FROM read_csv('s3://<bucket>/<key>.csv', header=true) LIMIT 20;
SELECT * FROM read_json_auto('s3://<bucket>/<key>.json') LIMIT 20;
```

Glob patterns (`*`, `**`) work across many Parquet files at once — DuckDB only reads the row groups/columns a query actually needs, so filter early (`WHERE`) and select only needed columns rather than `SELECT *` on wide tables.

## T5 — Common Crawl columnar index

Index root: `s3://commoncrawl/cc-index/table/cc-main/warc/`, partitioned by `crawl=<CRAWL-ID>/subset=<warc|robotstxt|crawldiagnostics>/`.

⚠️ **Verified live 2026-07-02:** anonymous `s3://commoncrawl/...` access (`ListObjectsV2` and `GetObject` alike) currently returns `403 Forbidden`, despite Common Crawl's docs saying `--no-sign-request` works. The confirmed-working path is the HTTPS distribution instead:

```bash
# Discover the current crawl ID
curl -s https://data.commoncrawl.org/cc-index/collections/index.html

# Discover part-file keys for that crawl (no ListBucket needed)
curl -s "https://data.commoncrawl.org/crawl-data/<CRAWL-ID>/cc-index-table.paths.gz" | gunzip -c | grep "subset=warc/"
```

```sql
INSTALL httpfs; LOAD httpfs;

SELECT url_host_registered_domain, count(*) AS pages
FROM read_parquet('https://data.commoncrawl.org/cc-index/table/cc-main/warc/crawl=<CRAWL-ID>/subset=warc/<part-file>.parquet')
WHERE url_host_tld = '<tld>'
GROUP BY url_host_registered_domain
HAVING count(*) >= 100
ORDER BY pages DESC;
```

If real signed AWS credentials are available, the original `s3://commoncrawl/.../*.parquet` glob form is worth retrying with `--profile <name>` — it can scan every part-file in one call, which the HTTPS form can't (no directory listing over plain HTTPS, so pass an explicit list of part-file URLs built from the manifest above).

## T6 — Crawl index published as a Hugging Face Storage Bucket

```sql
INSTALL httpfs; LOAD httpfs;
CREATE SECRET hf (
    TYPE s3, KEY_ID 'HFAK...', SECRET '...',
    ENDPOINT 's3.hf.co/<namespace>', URL_STYLE 'path', REGION 'us-east-1'
);

SELECT * FROM read_parquet('s3://<bucket>/<path>/*.parquet')
WHERE <filter-condition>
LIMIT 100;
```

Discover the real bucket/path first with `aws --profile hf s3 ls s3://<bucket>/` — do not assume a layout.

## T7 — Bulk copy/sync between two S3-compatible stores

```ini
# ~/.config/rclone/rclone.conf
[aws]
type = s3
provider = AWS
access_key_id = AKIA...
secret_access_key = ...
region = us-east-1

[hf]
type = s3
provider = Other
endpoint = https://s3.hf.co/<namespace>
access_key_id = HFAK...
secret_access_key = ...
region = us-east-1
force_path_style = true
list_version = 2
upload_cutoff = 2G
chunk_size = 2G
```

```bash
rclone copy aws:<source-bucket> hf:<dest-bucket> --progress --transfers 16 --checkers 16
rclone sync aws:<source-bucket> hf:<dest-bucket> --progress   # mirrors; deletes extras at destination
rclone check aws:<source-bucket> hf:<dest-bucket>             # verify after a large import
```
