#!/usr/bin/env python3
"""Validate a generated WebDAV weblog VSP/isql bundle."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def find_one(bundle: Path, pattern: str) -> Path | None:
    matches = sorted(bundle.glob(pattern))
    return matches[0] if matches else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path, help="Directory containing generated index.vsp and deploy SQL")
    parser.add_argument("--facet", action="store_true", help="Require facet/category markers")
    args = parser.parse_args()

    bundle = args.bundle
    missing: list[str] = []
    if not bundle.is_dir():
        print(f"not a directory: {bundle}", file=sys.stderr)
        return 2

    index = bundle / "index.vsp"
    deploy = find_one(bundle, "deploy*.sql")
    route = find_one(bundle, "*route*.sql")
    readme = find_one(bundle, "README*")

    if not index.exists():
        missing.append("missing index.vsp")
        index_text = ""
    else:
        index_text = read(index)

    if deploy is None:
        missing.append("missing deploy*.sql")
        deploy_text = ""
    else:
        deploy_text = read(deploy)

    route_text = read(route) if route else ""
    readme_text = read(readme) if readme else ""
    all_text = "\n".join([index_text, deploy_text, route_text, readme_text])

    checks = [
        ("index.vsp starts as VSP", index_text.lstrip().startswith("<?vsp")),
        ("dynamic DAV resource enumeration", "WS.WS.SYS_DAV_RES" in index_text),
        ("sidecar exclusion", "._%" in index_text or "._*" in index_text),
        ("RSS handling", re.search(r"rss", index_text, re.I) is not None),
        ("Atom handling", re.search(r"atom", index_text, re.I) is not None),
        ("AtomPub handling", re.search(r"atompub|atomsvc", index_text, re.I) is not None),
        ("deploy uses string_output", "string_output" in deploy_text),
        ("deploy populates stream with http()", "http (vsp_content, vsp_stream)" in deploy_text or "http(vsp_content, vsp_stream)" in deploy_text),
        ("deploy uses DAV_RES_UPLOAD_STRSES_INT", "DAV_RES_UPLOAD_STRSES_INT" in deploy_text),
        ("deploy uploads index.vsp", "index.vsp" in deploy_text and "DAV_RES_UPLOAD" in deploy_text),
        ("route setup present", "VHOST_DEFINE" in all_text or route is not None),
        ("verification query for HTTP_PATH", "DB.DBA.HTTP_PATH" in deploy_text),
        ("verification query for SYS_DAV_RES", "WS.WS.SYS_DAV_RES" in deploy_text),
        ("no isql macro-like replacement tokens", re.search(r"\$[0-9]", all_text) is None),
        ("no unsafe lcase/lower over http_param/coalesce", re.search(r"\b(?:lcase|lower)\s*\(\s*coalesce\s*\(\s*http_param", all_text, re.I) is None),
        ("run notes present", readme is not None),
    ]

    if args.facet:
        checks.extend([
            ("facet schema:category marker", "schema:category" in all_text),
            ("facet property table marker", "WS.WS.SYS_DAV_PROP" in all_text or "DAV_PROP" in all_text),
            ("facet dict iterator marker", "dict_iter_next" in all_text),
        ])

    for label, ok in checks:
        if not ok:
            missing.append(label)

    if missing:
        for item in missing:
            print(f"FAIL: {item}", file=sys.stderr)
        return 1

    print("generated WebDAV weblog bundle OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
