#!/usr/bin/env python3
"""Sanity-check a weblog-from-webdav skill bundle."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


CHECKS = {
    "templates/deploy-weblog-opl-site.sql": [
        "DAV_RES_UPLOAD_STRSES_INT",
        "string_output",
        "RSS",
        "Atom",
    ],
    "templates/deploy-weblog-opl-site-facet.sql": [
        "schema:category",
        "dict_iter_next",
        "contains",
        "._%",
    ],
    "SKILL.md": [
        "isql-engine",
        "webdav-posts",
        "WebDAV is then used for the post-publication workflow",
    ],
    "references/webdav-mode.md": [
        "not the engine setup channel",
        "switch to `isql` engine bootstrap",
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    missing: list[str] = []
    for rel, needles in CHECKS.items():
        path = args.skill_dir / rel
        if not path.exists():
            missing.append(f"missing file: {rel}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for needle in needles:
            if needle not in text:
                missing.append(f"{rel}: missing marker {needle!r}")
    if missing:
        for item in missing:
            print(item, file=sys.stderr)
        return 1
    print("weblog-from-webdav bundle markers OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
