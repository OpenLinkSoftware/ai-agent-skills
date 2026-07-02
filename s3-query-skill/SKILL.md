---
name: s3-query-skill
description: Client-side S3 API access for querying data directly at S3 and S3-compatible endpoints — AWS S3 public/private buckets, Hugging Face Storage Buckets (s3.hf.co), Cloudflare R2, MinIO, Wasabi, Backblaze B2 — without a full download. Uses DuckDB's httpfs extension to run SQL directly against remote Parquet/CSV/JSON/ND-JSON objects (e.g. querying the Common Crawl columnar index or a Hugging Face-hosted crawl index in place), plus AWS CLI/boto3 for object-level list/head/get/put and rclone for bulk cross-store copy. Triggers on phrases like "query data in an S3 bucket", "query an S3 API endpoint", "read a Parquet file from S3 without downloading it", "list objects in this bucket", "query the Common Crawl index", "connect to a Hugging Face Storage Bucket via S3", or any request to read/query/list/copy data at an `s3://` URI or S3-compatible HTTPS endpoint.
---

# S3 API Query Client Skill
## DuckDB httpfs · AWS CLI / boto3 · rclone · S3-compatible endpoints

## Purpose

Act as the **client side of the S3 API** — read and query data that already lives at an S3 or S3-compatible endpoint, in place, without a bulk download. The skill covers two access modes:

- **In-place SQL query** — DuckDB's `httpfs` extension runs `SELECT` directly against remote Parquet/CSV/JSON objects over the S3 protocol (range requests only pull the bytes a query needs). This is the pattern behind [Daniel van Strien's post](https://www.linkedin.com/posts/danielvanstrien_the-latest-common-crawl-foundation-crawl-share-7478044935850696704-YOAw/) on querying the 2.1-billion-row Common Crawl Foundation index straight from a laptop, "for $0" — the index is published as an S3-compatible Hugging Face Storage Bucket and queried with DuckDB, no download step.
- **Object-level operations** — list, head, get, put, and sync via AWS CLI / boto3 / rclone, for browsing a bucket or pulling specific objects (e.g. individual WARC/WAT/WET files).

### Supported Endpoint Types

| Endpoint type | Example | Auth | Notes |
|---|---|---|---|
| AWS S3 — public/anonymous bucket | `s3://commoncrawl/` | none in theory (`--no-sign-request`) | ⚠️ **Verified 2026-07-02: currently returns 403 on both `ListObjectsV2` and `GetObject` via anonymous/unsigned requests** — see the Common Crawl access note below for the working alternative |
| AWS S3 — private bucket | `s3://your-bucket/` | AWS access key/secret or SSO profile | Standard AWS auth chain |
| Hugging Face Storage Buckets | `https://s3.hf.co/<namespace>` | HF User Access Token → S3-style key (`HFAK…`) + secret | Path-style addressing required; single region `us-east-1`; `ListObjectsV1` unsupported |
| Cloudflare R2 / MinIO / Wasabi / Backblaze B2 / other S3-compatible | custom `endpoint_url` | provider-issued key/secret | Same client shape as HF; only `endpoint_url` + addressing style change |

### ⚠️ Common Crawl access note (verified live 2026-07-02)

Common Crawl's own [get-started docs](https://commoncrawl.org/get-started) describe `s3://commoncrawl/` as anonymously readable via `--no-sign-request`. Live testing during this skill's build did **not** confirm that — both `aws --no-sign-request s3 ls s3://commoncrawl/` and an unsigned `GetObject`/`HeadObject` returned `403 Forbidden` (confirmed with raw unsigned `curl` too, ruling out a local AWS CLI config issue). Either the bucket policy changed since those docs were written, or anonymous access now requires a signed request from an actual AWS account — this skill cannot confirm which without valid AWS credentials to test with.

**What does work today, verified live:** Common Crawl's HTTPS/CloudFront distribution at `https://data.commoncrawl.org/<key>` — confirmed `200 OK` and correct `206 Partial Content` on an explicit `Range:` request, meaning DuckDB's `httpfs` can query Parquet files there in place (`read_parquet('https://data.commoncrawl.org/...')`) with **no credentials at all**, using the same range-request mechanism as the S3 path. Object *discovery* (since `ListBucket` isn't available anonymously) goes through Common Crawl's own manifest files instead — e.g. `crawl-data/<CRAWL-ID>/warc.paths.gz` and `crawl-data/<CRAWL-ID>/cc-index-table.paths.gz` list every WARC/Parquet key for that crawl. See `examples/common-crawl-aws-columnar-index.md` for the confirmed working recipe.

If the user has real AWS credentials, re-test the signed (non-anonymous) path — the bucket may simply require sign-in now rather than being closed off entirely.

If the user names a specific tool or protocol ("use DuckDB", "use boto3", "use rclone"), honor that preference over the default routing below.

---

## Execution Routing

Default priority order:

1. **DuckDB CLI (`httpfs` extension)** — preferred whenever the goal is to *query* remote data (filter, aggregate, join, sample) rather than fetch whole objects. Zero download, zero local storage.
2. **AWS CLI (`aws s3` / `aws s3api`)** — for object-level browsing: `ls`, `cp`, `head-object`, `get-object`. Always available once the AWS CLI is installed; works against any S3-compatible endpoint via `--endpoint-url`.
3. **boto3 (Python)** — when the S3 access is one step inside a larger script/pipeline rather than a one-off interactive command.
4. **rclone** — for bulk copy/sync of many objects between two S3-compatible stores (e.g. importing an AWS bucket into a Hugging Face Storage Bucket).

---

## Step 0 — Tool Detection (Always Run First)

```bash
command -v duckdb  && duckdb --version
command -v aws     && aws --version
command -v python3 && python3 -c "import boto3; print(boto3.__version__)" 2>/dev/null
command -v rclone  && rclone --version | head -1
```

Report which tools are present. If `duckdb` is missing and the task is a query (not a plain download), offer to install it (`brew install duckdb` / `pip install duckdb`) or fall back to `aws s3api select-object-content` / boto3 for the same result — ask the user which they prefer rather than silently choosing.

---

## Step 1 — Identify Endpoint & Credentials

Before running anything, collect:

| Parameter | Required | Notes |
|---|---|---|
| Bucket / namespace | Yes | For HF Storage Buckets this is `namespace/bucket`; see addressing note below |
| Object key / prefix | Yes for queries against a specific object; optional for `list` | |
| `endpoint_url` | Only for non-AWS S3-compatible stores | e.g. `https://s3.hf.co/<namespace>` |
| Region | Yes | `us-east-1` for AWS Common Crawl bucket and for the HF gateway (single-region) |
| Auth mode | Yes | `anonymous` / `--no-sign-request`, an AWS profile, or an access-key + secret pair |
| Addressing style | Only for non-AWS endpoints | `path` — required for HF and most self-hosted S3-compatible stores |

**Never fabricate an access key, secret, or endpoint URL.** If the user hasn't supplied credentials for a private bucket, ask for them (or for the location of an existing AWS profile / HF token) rather than guessing. Public/anonymous buckets are supposed to need no credentials — use `--no-sign-request` (AWS CLI) or omit the DuckDB `CREATE SECRET` entirely and rely on unsigned HTTPS range requests. In practice, verify this per bucket: `s3://commoncrawl/` is documented as anonymous-read but was found to reject unsigned requests during this skill's build (see the access note above) — always confirm a bucket's actual anonymous-access behavior with a cheap probe (`head-object` on a known key) before building a workflow on top of it.

### Configuring an AWS CLI profile for a non-AWS S3-compatible endpoint

```ini
# ~/.aws/config
[profile hf]
region = us-east-1
endpoint_url = https://s3.hf.co/<namespace>
s3 =
    addressing_style = path
    multipart_threshold = 2GB
    multipart_chunksize = 2GB
request_checksum_calculation = when_required
response_checksum_validation = when_required
```

```ini
# ~/.aws/credentials
[hf]
aws_access_key_id = HFAK...
aws_secret_access_key = ...
```

The two checksum settings are required for recent AWS CLI (≥ 2.23) / boto3 versions against gateways that don't parse trailing CRC32 checksums (e.g. the HF gateway).

### Configuring DuckDB for a non-AWS S3-compatible endpoint

```sql
INSTALL httpfs;
LOAD httpfs;

CREATE SECRET s3_endpoint (
    TYPE s3,
    KEY_ID 'HFAK...',
    SECRET '...',
    ENDPOINT 's3.hf.co/<namespace>',   -- host only, no scheme
    URL_STYLE 'path',                  -- required — virtual-hosted style is not served
    REGION 'us-east-1'
);
```

For **plain AWS S3 public buckets** (e.g. Common Crawl), no secret is needed — DuckDB will make unsigned requests once `httpfs` is loaded, or set `SET s3_region='us-east-1';` if the bucket enforces regional access.

### boto3 client for a non-AWS S3-compatible endpoint

```python
import boto3
from botocore.config import Config

s3 = boto3.client(
    "s3",
    endpoint_url="https://s3.hf.co/<namespace>",
    aws_access_key_id="HFAK...",
    aws_secret_access_key="...",
    config=Config(
        region_name="us-east-1",
        s3={"addressing_style": "path"},
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    ),
)
```

For anonymous AWS access, use `Config(signature_version=botocore.UNSIGNED)` instead of passing keys.

---

## Step 2 — Query Templates

### T1 — List bucket / prefix contents

```bash
# AWS, public bucket (works for anonymous-read buckets in general;
# s3://commoncrawl/ specifically currently rejects this — see access note above)
aws --no-sign-request s3 ls s3://commoncrawl/cc-index/table/cc-main/warc/ --recursive | head -50

# Non-AWS S3-compatible endpoint (profile from Step 1)
aws --profile hf s3 ls s3://my-bucket/ --recursive
```

### T2 — Head an object (existence + metadata check)

```bash
aws --no-sign-request s3api head-object --bucket <public-bucket> --key <known-key>
aws --profile hf s3api head-object --bucket my-bucket --key some/object.parquet
```

### T3 — Get / download a single object

```bash
# Anonymous AWS bucket (verify anonymous access works first — see access note above)
aws --no-sign-request s3 cp s3://<public-bucket>/<key> ./
# For Common Crawl specifically, use the confirmed HTTPS path instead:
curl -O "https://data.commoncrawl.org/crawl-data/<CRAWL-ID>/segments/<SEGMENT>/warc/<FILE>.warc.gz"

aws --profile hf s3 cp s3://my-bucket/models/model.safetensors ./
```

### T4 — Query a remote Parquet/CSV/JSON object in place (no download)

```sql
INSTALL httpfs; LOAD httpfs;
SELECT * FROM read_parquet('s3://my-bucket/data.parquet') LIMIT 20;
SELECT count(*) FROM read_csv('s3://my-bucket/data.csv');
```

This is the core "query an S3 API endpoint" capability — DuckDB issues HTTP range requests against the object, so only the row groups/columns the query touches are transferred.

### T5 — Query the Common Crawl columnar index (verified working recipe)

The Parquet-formatted index is logically at `s3://commoncrawl/cc-index/table/cc-main/warc/`, partitioned by `crawl` and `subset` — but see the access note above: anonymous `s3://` reads currently 403. The verified-working path is the HTTPS distribution, reading individual part-files discovered via the crawl's manifest (DuckDB's `read_parquet` glob can't enumerate an HTTPS directory the way it can an `s3://` bucket, so list the part-files explicitly):

```bash
# 1. Discover the real part-file keys for a crawl + subset (no S3 ListBucket needed)
curl -s "https://data.commoncrawl.org/crawl-data/<CRAWL-ID>/cc-index-table.paths.gz" \
  | gunzip -c | grep "subset=warc/" 
```

```sql
-- 2. Query the discovered part-file(s) directly — no credentials required
INSTALL httpfs; LOAD httpfs;

SELECT url_host_registered_domain, count(*) AS pages
FROM read_parquet('https://data.commoncrawl.org/cc-index/table/cc-main/warc/crawl=<CRAWL-ID>/subset=warc/part-00000-....c000.gz.parquet')
WHERE url_host_tld = '<tld>'
GROUP BY url_host_registered_domain
HAVING count(*) >= 100
ORDER BY pages DESC;
```

If the user has real (signed) AWS credentials, the original `s3://commoncrawl/...` glob form with partition-filtered wildcards may still work and is more convenient (one call scans every matching part-file) — worth retrying with `--profile <aws-profile>` instead of `--no-sign-request`.

### T6 — Query a crawl index published as a Hugging Face Storage Bucket

Same technique as T5, pointed at the HF S3 gateway instead of AWS — replicates the workflow in the referenced LinkedIn post:

```sql
INSTALL httpfs; LOAD httpfs;

CREATE SECRET hf (
    TYPE s3,
    KEY_ID 'HFAK...',
    SECRET '...',
    ENDPOINT 's3.hf.co/<namespace>',
    URL_STYLE 'path',
    REGION 'us-east-1'
);

SELECT * FROM read_parquet('s3://<bucket>/<path-to-index>/*.parquet')
WHERE <filter-condition>
LIMIT 100;
```

Ask the user for the exact bucket/path — do not guess the Common Crawl Foundation's HF bucket name; confirm it from the post/documentation they point to, or have them run `aws --profile hf s3 ls s3://<bucket>/` first to discover the real layout.

### T7 — Bulk copy/sync between two S3-compatible stores

```bash
rclone copy aws:my-source-bucket hf:my-bucket --progress --transfers 16 --checkers 16
rclone sync aws:my-source-bucket hf:my-bucket --progress   # mirrors, deletes extras at destination
```

`rclone.conf` needs one remote per store (`type = s3`, `provider = AWS` vs `provider = Other`, `endpoint`, `force_path_style = true`, `list_version = 2` for gateways that only support `ListObjectsV2`).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Could not resolve hostname <bucket>.s3.hf.co` | DuckDB/boto3 defaulted to virtual-hosted-style addressing | Set `URL_STYLE 'path'` (DuckDB) or `s3={"addressing_style":"path"}` (boto3) |
| `AccessDenied` on a public AWS bucket | Signed request sent to an anonymous-only bucket | Add `--no-sign-request` (CLI) or `signature_version=UNSIGNED` (boto3) |
| Slow/expensive cross-region transfer from `s3://commoncrawl/` | Querying from outside `us-east-1` | Run the query from a `us-east-1` compute instance, or accept the egress cost |
| `ListObjectsV1 not supported` type errors against HF gateway | Client defaulting to the older listing API | Force `ListObjectsV2` (`--profile` config, or `list_version = 2` in rclone) |
| Trailing-checksum errors against a gateway | Recent AWS CLI/boto3 sends `aws-chunked` CRC32 by default | Set `request_checksum_calculation` / `response_checksum_validation` to `when_required` |
| DuckDB query scans far more data than expected | Glob pattern doesn't use the partition columns | Filter on `crawl=`/`subset=` (or the store's partition scheme) directly in the S3 path glob |
| `403 Forbidden` on anonymous `s3://commoncrawl/...` (`ListObjectsV2` or `GetObject`) | Verified 2026-07-02: anonymous S3 API access to this bucket is currently denied, despite Common Crawl's docs saying `--no-sign-request` works | Use `https://data.commoncrawl.org/<key>` instead (HTTPS, range-request-capable, no credentials) — discover keys via `crawl-data/<CRAWL-ID>/*.paths.gz` manifests rather than `ListBucket`; or retry with real signed AWS credentials if available |

---

## Initialization Sequence

When invoked:

⛔ **PRE-BUILD CHECK**: Before producing output, re-read the relevant workflow section above. Apply the CLAUDE.md Anti-Drift Protocol: re-read spec section before build, gate-first validation, section-by-section delivery.

1. Run Step 0 — detect which of `duckdb` / `aws` / `boto3` / `rclone` are available.
2. Ask whether the task is a **query** (filter/aggregate remote data → prefer DuckDB) or an **object operation** (list/get/put a specific file → prefer AWS CLI/boto3).
3. Identify the endpoint type from the user's bucket/URL (AWS, Hugging Face Storage Bucket, or other S3-compatible) and collect the Step 1 parameters. Never fabricate credentials or endpoint URLs — ask if not supplied.
4. Run the matching query template (T1–T7), substituting the user's real bucket/key/path values.
5. Report results concisely; for large query results, summarize row counts and show a sample rather than dumping everything.
6. If credentials were used, do not echo the secret key back in full in any output or memory record — reference the profile/secret name only.

---

## Reference Files

| File | Contents |
|---|---|
| `references/endpoint-profiles.md` | Full connection profiles for AWS S3 (public + private), Hugging Face Storage Buckets, and generic S3-compatible stores (R2, MinIO, Wasabi, B2) |
| `references/query-templates.md` | Expanded T1–T7 templates plus additional DuckDB/boto3/rclone recipes |
| `examples/common-crawl-aws-columnar-index.md` | Worked example querying `s3://commoncrawl/cc-index/table/cc-main/warc/` |
| `examples/common-crawl-hf-storage-bucket.md` | Worked example replicating the LinkedIn-post workflow against a Hugging Face Storage Bucket |
| `scripts/duckdb-s3-query.sh` | Wrapper: loads `httpfs`, optionally creates a named secret from env vars, runs a supplied SQL file/string against an S3 path |
| `scripts/s3-list.sh` | Wrapper around `aws s3 ls` / `aws s3api list-objects-v2` supporting both anonymous and profile-based auth |

---

## Version
**1.0.0** — Initial release. Covers AWS S3 (public + private), Hugging Face Storage Buckets, and generic S3-compatible endpoints via DuckDB httpfs, AWS CLI, boto3, and rclone.
