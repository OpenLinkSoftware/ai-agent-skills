#!/usr/bin/env python3
"""Classify an HTML replacement document for OSDI deployment.

Reports:
  - structure: full document vs fragment (tidy will normalize fragments)
  - chrome: whether the page carries its own nav/header/footer/masthead
  - external assets that must resolve from the live origin
  - deploy recommendation (passthrough skin vs default skin)

Usage:
  check_chrome_conflict.py <file-or-url> [--insecure]

Exit codes: 0 = no chrome conflict (default skin OK)
            2 = self-contained chrome detected (passthrough skin required)
            1 = fetch/parse error
"""
import re
import ssl
import sys
import urllib.request

CHROME_TAG = re.compile(r"<(nav|header|footer)\b[^>]*>", re.I)
CHROME_CLASS = re.compile(
    r'(?:class|id)\s*=\s*"[^"]*\b(masthead|navbar|site-header|site-footer|topbar|top-bar)\b[^"]*"',
    re.I,
)
EXTERNAL_ASSET = re.compile(
    r'(?:href|src)\s*=\s*"(https?://[^"]+\.(?:css|js|woff2?)[^"]*|https?://fonts\.[^"]+)"',
    re.I,
)


def load(source: str, insecure: bool) -> str:
    if re.match(r"^https?://", source):
        ctx = ssl._create_unverified_context() if insecure else None
        with urllib.request.urlopen(source, context=ctx, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    with open(source, encoding="utf-8", errors="replace") as f:
        return f.read()


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--insecure"]
    insecure = "--insecure" in sys.argv[1:]
    if len(args) != 1:
        print(__doc__)
        return 1
    try:
        html = load(args[0], insecure)
    except Exception as e:
        print(f"ERROR: cannot load {args[0]}: {e}")
        return 1

    has_doctype = bool(re.search(r"<!doctype\b", html, re.I))
    has_html = bool(re.search(r"<html\b", html, re.I))
    has_body = bool(re.search(r"<body\b", html, re.I))
    full_doc = has_doctype and has_html and has_body
    rdfa_doctype = bool(re.search(r"<!doctype[^>]*rdfa", html, re.I))

    chrome_tags = sorted({m.group(1).lower() for m in CHROME_TAG.finditer(html)})
    chrome_classes = sorted({m.group(1).lower() for m in CHROME_CLASS.finditer(html)})
    assets = sorted({m.group(1) for m in EXTERNAL_ASSET.finditer(html)})

    has_chrome = bool(chrome_tags or chrome_classes)

    print(f"source        : {args[0]}")
    print(f"size          : {len(html)} bytes")
    print(f"structure     : {'full document' if full_doc else 'fragment (tidy will wrap it)'}")
    if rdfa_doctype:
        print("doctype       : XHTML+RDFa — engine SKIPS tidy for this document")
    print(f"chrome tags   : {', '.join(chrome_tags) or 'none'}")
    print(f"chrome classes: {', '.join(chrome_classes) or 'none'}")
    print(f"external assets ({len(assets)}):")
    for a in assets:
        print(f"  - {a}")

    if has_chrome:
        print("\nRECOMMENDATION: self-contained chrome detected.")
        print("Deploy under the passthrough skin via a per-URL xslt_sheet override")
        print("(templates/skin-override.sql). Deploying under openlink/responsive")
        print("skins would stack duplicate masthead/nav/footer chrome.")
        return 2
    print("\nRECOMMENDATION: no self-contained chrome detected; default site skin is safe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
