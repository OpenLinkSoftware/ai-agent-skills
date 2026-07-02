# Worked Example — Replicating the "Query Common Crawl via Hugging Face S3" Workflow

This replicates the pattern described in [Daniel van Strien's LinkedIn post](https://www.linkedin.com/posts/danielvanstrien_the-latest-common-crawl-foundation-crawl-share-7478044935850696704-YOAw/): the latest Common Crawl Foundation crawl's URL index (2.1 billion rows, including 20.9M PDFs) is published as a Hugging Face **Storage Bucket** with an S3-compatible API, and queried directly with DuckDB — no download, no cost for read operations.

## 1. Get S3 credentials for the Hugging Face gateway

1. Create or reuse a Hugging Face **User Access Token** with **Read** scope: https://huggingface.co/settings/tokens
2. From that token's dropdown, choose **Generate S3 credentials**.
3. Copy the access key (`HFAK…`) and secret — the secret is shown once.

## 2. Discover the real bucket/namespace and path

Do not guess the bucket name — list it first:

```bash
aws --profile hf s3 ls s3://<namespace-or-bucket>/
```

(Configure the `hf` profile as shown in `references/endpoint-profiles.md` first, pointing `endpoint_url` at `https://s3.hf.co/<namespace>`.)

## 3. Query the index in place with DuckDB

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

-- adjust bucket/path to what Step 2 discovered
SELECT count(*) FROM read_parquet('s3://<bucket>/<index-path>/*.parquet');

SELECT url, content_type
FROM read_parquet('s3://<bucket>/<index-path>/*.parquet')
WHERE content_type = 'application/pdf'
LIMIT 20;
```

## 4. Notes

- `URL_STYLE 'path'` is mandatory — without it DuckDB tries virtual-hosted-style addressing (`<bucket>.s3.hf.co`), which the HF gateway does not serve, and the query fails with "Could not resolve hostname".
- The HF gateway is single-region (`us-east-1`) — always set `REGION 'us-east-1'` regardless of where the client runs.
- `ListObjectsV1` is unsupported on the gateway; if using `aws s3api list-objects` instead of `s3 ls`, force `list-objects-v2`.
- Because DuckDB only pulls the row groups/columns a query touches, scanning a multi-billion-row Parquet index for a handful of matching rows is fast and effectively free even from a laptop — this is the "for $0" result in the source post.
