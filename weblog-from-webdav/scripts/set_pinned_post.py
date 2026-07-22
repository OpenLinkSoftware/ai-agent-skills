#!/usr/bin/env python3
"""Set or remove schema:position WebDAV metadata for a pinned weblog post."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote, urljoin


def escape_xml(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def prop_xml(action: str, value: str) -> str:
    if action == "unpin":
        return """<?xml version="1.0" encoding="utf-8"?>
<D:propertyupdate xmlns:D="DAV:" xmlns:schema="https://schema.org/">
  <D:remove>
    <D:prop>
      <schema:position/>
    </D:prop>
  </D:remove>
</D:propertyupdate>
"""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<D:propertyupdate xmlns:D="DAV:" xmlns:schema="https://schema.org/">
  <D:set>
    <D:prop>
      <schema:position>{escape_xml(value)}</schema:position>
    </D:prop>
  </D:set>
</D:propertyupdate>
"""


def build_url(base_url: str, resource: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", quote(resource.lstrip("/")))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pin or unpin one WebDAV weblog post using schema:position metadata."
    )
    parser.add_argument("--base-url", required=True, help="WebDAV collection URL")
    parser.add_argument("--resource", required=True, help="Post filename or path below the collection")
    parser.add_argument("--action", choices=("pin", "unpin"), default="pin")
    parser.add_argument("--position", default="1", help="Non-zero value used for pinned posts")
    parser.add_argument("--user")
    parser.add_argument("--password-env")
    parser.add_argument("--curl-config")
    parser.add_argument("--cert-type")
    parser.add_argument("--cert")
    parser.add_argument("--cacert")
    parser.add_argument("--on-behalf-of")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.resource.startswith("._"):
        print("Refusing to pin macOS sidecar resource.", file=sys.stderr)
        return 2
    if args.action == "pin" and (not args.position or args.position == "0"):
        print("--position must be non-zero when pinning.", file=sys.stderr)
        return 2

    password = os.environ.get(args.password_env) if args.password_env else None
    if args.password_env and password is None:
        print(f"Missing password environment variable: {args.password_env}", file=sys.stderr)
        return 2

    url = build_url(args.base_url, args.resource)
    value = args.position if args.action == "pin" else "0"
    if args.dry_run:
        delegation = f" on-behalf-of={args.on_behalf_of}" if args.on_behalf_of else ""
        print(f"PROPPATCH {url} schema:position={value} action={args.action}{delegation}")
        return 0

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".xml", delete=False) as tmp:
        tmp.write(prop_xml(args.action, value))
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
        print(f"{args.action}ned\t{args.resource}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
