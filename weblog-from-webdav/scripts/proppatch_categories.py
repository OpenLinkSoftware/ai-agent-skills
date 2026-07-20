#!/usr/bin/env python3
"""Apply schema:category WebDAV properties from a TSV file.

TSV columns: resource, categories
categories may be separated with semicolons or commas.
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote, urljoin


def category_text(raw: str) -> str:
    parts = [p.strip() for chunk in raw.split(";") for p in chunk.split(",")]
    return "; ".join(p for p in parts if p)


def prop_xml(categories: str) -> str:
    escaped = (
        categories.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<D:propertyupdate xmlns:D="DAV:" xmlns:schema="https://schema.org/">
  <D:set>
    <D:prop>
      <schema:category>{escaped}</schema:category>
    </D:prop>
  </D:set>
</D:propertyupdate>
"""


def build_url(base_url: str, resource: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", quote(resource.lstrip("/")))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--tsv", required=True, type=Path)
    parser.add_argument("--user")
    parser.add_argument("--password-env")
    parser.add_argument("--curl-config")
    parser.add_argument("--cert-type")
    parser.add_argument("--cert")
    parser.add_argument("--cacert")
    parser.add_argument("--on-behalf-of")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    password = os.environ.get(args.password_env) if args.password_env else None
    if args.password_env and password is None:
        print(f"Missing password environment variable: {args.password_env}", file=sys.stderr)
        return 2

    with args.tsv.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            resource = (row.get("resource") or row.get("filename") or "").strip()
            categories = category_text(row.get("categories") or row.get("schema:category") or "")
            if not resource or not categories or resource.startswith("._"):
                continue
            url = build_url(args.base_url, resource)
            if args.dry_run:
                delegation = f" on-behalf-of={args.on_behalf_of}" if args.on_behalf_of else ""
                print(f"PROPPATCH {url} schema:category={categories}{delegation}")
                continue
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".xml", delete=False) as tmp:
                tmp.write(prop_xml(categories))
                tmp_path = tmp.name
            try:
                cmd = ["curl", "--fail", "--silent", "--show-error", "--anyauth", "-X", "PROPPATCH"]
                if args.curl_config:
                    cmd.extend(["--config", args.curl_config])
                if args.user:
                    cmd.extend(["--user", f"{args.user}:{password or ''}"])
                if args.cert_type:
                    cmd.extend(["--cert-type", args.cert_type])
                if args.cert:
                    cmd.extend(["--cert", args.cert])
                if args.cacert:
                    cmd.extend(["--cacert", args.cacert])
                if args.on_behalf_of:
                    cmd.extend(["-H", f"On-Behalf-Of: {args.on_behalf_of}"])
                cmd.extend(["-H", "Content-Type: application/xml", "--data-binary", f"@{tmp_path}", url])
                subprocess.run(cmd, check=True)
                print(f"updated\t{resource}")
            finally:
                Path(tmp_path).unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
