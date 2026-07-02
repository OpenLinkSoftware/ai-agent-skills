# Worked Example — Querying the Common Crawl Columnar Index In Place

Goal: run an aggregate SQL query against Common Crawl's Parquet-formatted columnar index without downloading any WARC files or the full index.

## ⚠️ Access note (verified live, 2026-07-02)

Common Crawl's own docs describe `s3://commoncrawl/` as anonymously readable via `--no-sign-request`. Live testing while building this skill found otherwise: both an unsigned `ListObjectsV2` and an unsigned `GetObject`/`HeadObject` against `s3://commoncrawl/` currently return `403 Forbidden` — confirmed with raw unsigned `curl` too, so it isn't a local AWS CLI misconfiguration. The bucket policy may have changed since the docs were written, or anonymous access may now require a signed request from a real AWS account.

**What is verified working today:** Common Crawl's HTTPS/CloudFront distribution, `https://data.commoncrawl.org/<key>` — confirmed `200 OK`, and confirmed `206 Partial Content` on an explicit `Range:` request. DuckDB's `httpfs` extension can read Parquet from a plain `https://` URL the same way it reads `s3://`, using the same range-request mechanism — so this still delivers in-place querying with **zero credentials and zero download**, it's just not going through the S3 API's `s3://` scheme.

## 1. Find the current crawl ID and its manifest

```bash
curl -s https://data.commoncrawl.org/cc-index/collections/index.html   # human-readable list of crawl IDs
```

Each crawl publishes a manifest of every columnar-index part-file:

```bash
curl -s "https://data.commoncrawl.org/crawl-data/<CRAWL-ID>/cc-index-table.paths.gz" | gunzip -c | head
```

Example output (crawl `CC-MAIN-2026-25`, confirmed live):

```
cc-index/table/cc-main/warc/crawl=CC-MAIN-2026-25/subset=crawldiagnostics/part-00000-b13edba3-e431-43c6-8915-a9f1c955272b.c000.gz.parquet
cc-index/table/cc-main/warc/crawl=CC-MAIN-2026-25/subset=crawldiagnostics/part-00001-b13edba3-e431-43c6-8915-a9f1c955272b.c000.gz.parquet
...
```

Filter that manifest for `subset=warc/` to get the part-files covering actual crawled pages (as opposed to `crawldiagnostics` or `robotstxt`).

## 2. Query a part-file in place with DuckDB

Confirmed working, run against the live endpoint while building this skill:

```python
import duckdb
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")

url = ("https://data.commoncrawl.org/cc-index/table/cc-main/warc/"
       "crawl=CC-MAIN-2026-25/subset=crawldiagnostics/"
       "part-00000-b13edba3-e431-43c6-8915-a9f1c955272b.c000.gz.parquet")

print(con.execute(f"SELECT count(*) FROM read_parquet('{url}')").fetchall())
# -> [(1491237,)]

print(con.execute(
    f"SELECT url_host_tld, count(*) c FROM read_parquet('{url}') "
    "GROUP BY url_host_tld ORDER BY c DESC LIMIT 5"
).fetchall())
# -> [('ru', 1290720), ('sa', 149906), ('run', 23117), ('rw', 18859), ('ruhr', 4710)]
```

Same thing from the DuckDB CLI:

```bash
duckdb -c "INSTALL httpfs; LOAD httpfs;
SELECT url_host_tld, count(*) c
FROM read_parquet('https://data.commoncrawl.org/cc-index/table/cc-main/warc/crawl=CC-MAIN-2026-25/subset=crawldiagnostics/part-00000-b13edba3-e431-43c6-8915-a9f1c955272b.c000.gz.parquet')
GROUP BY url_host_tld ORDER BY c DESC LIMIT 5;"
```

## 3. Scanning multiple part-files

DuckDB's glob expansion (`*.parquet`) works on `s3://` buckets (via `ListObjectsV2`) but not on a plain HTTPS directory listing, since `data.commoncrawl.org` doesn't expose directory listings. To scan more than one part-file over HTTPS, either:

- pass an explicit list: `read_parquet(['https://.../part-00000....parquet', 'https://.../part-00001....parquet'])`, built from the `cc-index-table.paths.gz` manifest, or
- if the user has real signed AWS credentials, retry the original `s3://commoncrawl/cc-index/table/cc-main/warc/crawl=<ID>/subset=warc/*.parquet` glob form with `--profile <aws-profile>` instead of `--no-sign-request` — this may work where anonymous access does not, and lets DuckDB expand the glob across every part-file in one call.

## 4. Notes

- `crawl=`/`subset=` are Hive-style partitions baked into the path — always filter to the exact crawl/subset you need rather than scanning everything.
- No AWS credentials were used for the confirmed query above — it is a plain authenticated-by-nothing HTTPS GET with range requests.
- To then fetch the actual WARC record for a matched row, use its `warc_filename` / `warc_record_offset` / `warc_record_length` columns with an HTTP Range request against `https://data.commoncrawl.org/<warc_filename>`.
