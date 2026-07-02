# S3 & S3-Compatible Endpoint Profiles

Connection details for the endpoint types this skill supports. Fill in the bracketed values from what the user provides — never invent a bucket name, namespace, or credential.

---

## 1. AWS S3 — Public / Anonymous Bucket

Example: Common Crawl (`s3://commoncrawl/`).

| Setting | Value |
|---|---|
| Auth | none in theory — `--no-sign-request` (CLI) or unsigned requests |
| Region | bucket-specific; Common Crawl requires `us-east-1` to avoid cross-region transfer fees |
| Addressing | default (virtual-hosted) |

```bash
aws --no-sign-request s3 ls s3://commoncrawl/crawl-data/ 
aws --no-sign-request s3 cp s3://commoncrawl/<key> ./
```

```sql
-- DuckDB: no CREATE SECRET needed for public buckets
INSTALL httpfs; LOAD httpfs;
SET s3_region='us-east-1';
SELECT * FROM read_parquet('s3://commoncrawl/<path>/*.parquet') LIMIT 10;
```

```python
import boto3
from botocore import UNSIGNED
from botocore.config import Config
s3 = boto3.client("s3", region_name="us-east-1", config=Config(signature_version=UNSIGNED))
```

⚠️ **Verified live 2026-07-02: this does not currently work for the Common Crawl bucket.** Both unsigned `ListObjectsV2` and unsigned `GetObject`/`HeadObject` against `s3://commoncrawl/` returned `403 Forbidden` when tested (confirmed with raw unsigned `curl`, ruling out a client config issue) — despite Common Crawl's own docs stating `--no-sign-request` works. Confirmed working alternative: `https://data.commoncrawl.org/<key>` over plain HTTPS (no credentials, range-request-capable — DuckDB's `read_parquet('https://...')` works identically to the `s3://` form). Discover keys via the crawl's `*.paths.gz` manifests instead of `ListBucket`. See `examples/common-crawl-aws-columnar-index.md` for the confirmed recipe. If the user has real signed AWS credentials, retest the `s3://` form with a real profile — it may simply require sign-in now rather than being closed off.

---

## 2. AWS S3 — Private Bucket

| Setting | Value |
|---|---|
| Auth | AWS access key/secret, SSO profile, or instance role |
| Region | bucket's actual region |
| Addressing | default |

```bash
aws --profile <profile-name> s3 ls s3://<bucket>/
```

```python
s3 = boto3.client("s3")  # picks up default credential chain
```

---

## 3. Hugging Face Storage Buckets

Gateway: `https://s3.hf.co/<namespace>` (namespace = HF username or organization).

| Setting | Value | Why |
|---|---|---|
| `endpoint_url` | `https://s3.hf.co/<namespace>` | Scopes requests to the namespace |
| `region` | `us-east-1` | Gateway is single-region |
| `addressing_style` | `path` | Buckets are path segments, not subdomains |
| `request_checksum_calculation` | `when_required` | Gateway doesn't parse trailing CRC32 checksums |
| `response_checksum_validation` | `when_required` | Same reason, response side |

Credentials: generate an HF **User Access Token** (Settings → Access Tokens), then "Generate S3 credentials" from that token's dropdown. Access key is prefixed `HFAK…`; the secret is shown once.

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

```sql
CREATE SECRET hf (
    TYPE s3, KEY_ID 'HFAK...', SECRET '...',
    ENDPOINT 's3.hf.co/<namespace>', URL_STYLE 'path', REGION 'us-east-1'
);
```

**Known limitations:** `ListObjectsV1` unsupported (use v2), only `/` delimiter, no ACLs/bucket policies/object tagging/versioning/SSE, `GetObject` responds with a 302 CDN redirect (AWS CLI/boto3/aws-sdk-rust are proxied automatically; other clients like `rclone`/`s5cmd`/`curl` follow the redirect natively).

---

## 4. Generic S3-Compatible (Cloudflare R2, MinIO, Wasabi, Backblaze B2, etc.)

Same shape as the Hugging Face profile — only `endpoint_url`, region, and addressing style change per provider. Ask the user for:

- `endpoint_url` (provider-specific, e.g. `https://<account-id>.r2.cloudflarestorage.com` for R2)
- Access key ID / secret access key
- Region (some providers accept `auto` or a fixed string)
- Whether path-style addressing is required (most self-hosted stores: yes)

Do not guess a provider's endpoint pattern — confirm it against the provider's own docs or ask the user to paste it.
