#!/usr/bin/env python3
"""Classify an HTML replacement document for OSDI deployment.

Reports:
  - structure: full document vs fragment (tidy will normalize fragments)
  - chrome: which regions the page supplies itself (nav / header / footer)
  - external assets that must resolve from the live origin
  - a recommendation across the three remediation paths

This is a RECOMMENDER, not a gate. It cannot see the live config, so it does
not know whether the target site is on a composite skin (where Path C applies)
or a legacy one (where the choice is A or B). Read the live skin_manifest and
xslt_sheet for the target URL, then put the choice to the user.

Usage:
  check_chrome_conflict.py <file-or-url> [--insecure] [--composite]

  --composite   the target site is known to be on a composite skin, so
                Path C (regions_off) is available; prints the exact
                regions_off value to set.

Exit codes: 0 = no self-contained chrome (safe under any skin)
            2 = self-contained chrome detected (remediation choice required)
            1 = fetch/parse error
"""
import re
import ssl
import sys
import urllib.request

# Region names match the conventional region names in a composite skin bundle,
# so the detected set can be handed straight to regions_off.
REGION_PATTERNS = {
    "nav": [
        re.compile(r"<nav\b", re.I),
        re.compile(r'(?:class|id)\s*=\s*"[^"]*\b(?:navbar|site-nav|topbar|top-bar)\b', re.I),
    ],
    "header": [
        re.compile(r"<header\b", re.I),
        re.compile(r'(?:class|id)\s*=\s*"[^"]*\b(?:masthead|site-header)\b', re.I),
    ],
    "footer": [
        re.compile(r"<footer\b", re.I),
        re.compile(r'(?:class|id)\s*=\s*"[^"]*\b(?:site-footer|colophon)\b', re.I),
    ],
    "announcement": [
        re.compile(r'(?:class|id)\s*=\s*"[^"]*\b(?:annc|announcement|banner-strip)\b', re.I),
    ],
}

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
    argv = sys.argv[1:]
    insecure = "--insecure" in argv
    composite = "--composite" in argv
    args = [a for a in argv if not a.startswith("--")]
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

    regions = [name for name, pats in REGION_PATTERNS.items()
               if any(p.search(html) for p in pats)]
    assets = sorted({m.group(1) for m in EXTERNAL_ASSET.finditer(html)})

    print(f"source        : {args[0]}")
    print(f"size          : {len(html)} bytes")
    print(f"structure     : {'full document' if full_doc else 'fragment (tidy will wrap it)'}")
    if rdfa_doctype:
        print("doctype       : XHTML+RDFa — engine SKIPS tidy for this document")
    print(f"chrome regions: {', '.join(regions) or 'none'}")
    print(f"external assets ({len(assets)}):")
    for a in assets:
        print(f"  - {a}")

    if not regions:
        print("\nRECOMMENDATION: no self-contained chrome detected.")
        print("The page is safe under any skin; no remediation needed.")
        return 0

    print("\nSelf-contained chrome detected. Three remediations — the choice is the")
    print("user's, and depends on the LIVE skin for this URL, which this script")
    print("cannot see. Read skin_manifest, then xslt_sheet, before recommending.\n")

    if composite:
        print(f"  Path C (preferred here): regions_off = '{','.join(regions)}'")
        print("      Pure config, page-atomic. The page keeps canonical, feeds,")
        print("      data islands, analytics and the OPAL widget.")
    else:
        print("  Path C: NOT available — target is not known to be on a composite")
        print("      skin. Re-run with --composite once you have confirmed")
        print(f"      skin_manifest is set; the value would be '{','.join(regions)}'.")

    print("\n  Path A: per-URL xslt_sheet override to the passthrough skin.")
    print("      Page keeps its layout but forfeits canonical, feeds, JSON-LD")
    print("      SearchAction, data islands, analytics, OPAL widget and site nav.")
    print("\n  Path B: strip the page's own chrome and deploy under the live skin.")
    print(f"      Remove its {', '.join(regions)}; keep <style> blocks and content")
    print("      sections. No config change — a pure WebDAV PUT.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
