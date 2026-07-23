#!/usr/bin/env python3
"""Classify an HTML replacement document as input to an OSDI skin-authoring decision.

Reports, per document:
  - structure: full document vs fragment (tidy will normalize fragments)
  - chrome: whether the page carries its own nav/header/footer/masthead
  - external assets that must resolve from the live origin
  - commonality signals: font family, CSS custom-property names, Bootstrap
    usage, nav/toggle markup — the inputs to a cross-document commonality
    assessment (see references/skin-commonality-assessment.md)

This does NOT recommend a deploy path. Self-contained chrome means the
document is a candidate new skin, not a page to strip-and-deploy under the
current skin unmodified. Whether it becomes a shared skin, a per-site skin,
or (as a stopgap only) a passthrough override is a design decision made
after comparing commonality signals across ALL candidate documents in the
batch — run this script on each one first, then compare by eye or with
--compare.

Usage:
  check_chrome_conflict.py <file-or-url> [--insecure]
  check_chrome_conflict.py --compare <file-or-url> <file-or-url> [...] [--insecure]

Exit codes: 0 = no self-contained chrome (document is plain content)
            2 = self-contained chrome detected (candidate new skin — see
                references/skin-commonality-assessment.md before deciding
                shared vs per-site vs passthrough)
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
FONT_FAMILY = re.compile(r"family=([A-Za-z0-9+:@;.,]+)")
CSS_CUSTOM_PROP = re.compile(r"(--[a-zA-Z0-9-]+)\s*:")
NAV_TOGGLE = re.compile(r"navbar-toggler|hamburger|mobile-menu|btn-nav", re.I)


def load(source: str, insecure: bool) -> str:
    if re.match(r"^https?://", source):
        ctx = ssl._create_unverified_context() if insecure else None
        with urllib.request.urlopen(source, context=ctx, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    with open(source, encoding="utf-8", errors="replace") as f:
        return f.read()


def classify(source: str, html: str) -> dict:
    has_doctype = bool(re.search(r"<!doctype\b", html, re.I))
    has_html = bool(re.search(r"<html\b", html, re.I))
    has_body = bool(re.search(r"<body\b", html, re.I))
    full_doc = has_doctype and has_html and has_body
    rdfa_doctype = bool(re.search(r"<!doctype[^>]*rdfa", html, re.I))

    return {
        "source": source,
        "size": len(html),
        "full_doc": full_doc,
        "rdfa_doctype": rdfa_doctype,
        "chrome_tags": sorted({m.group(1).lower() for m in CHROME_TAG.finditer(html)}),
        "chrome_classes": sorted({m.group(1).lower() for m in CHROME_CLASS.finditer(html)}),
        "assets": sorted({m.group(1) for m in EXTERNAL_ASSET.finditer(html)}),
        "fonts": sorted({m.group(1) for m in FONT_FAMILY.finditer(html)}),
        "css_props": sorted({m.group(1) for m in CSS_CUSTOM_PROP.finditer(html)}),
        "bootstrap": bool(re.search(r"bootstrap", html, re.I)),
        "nav_toggle": sorted({m.group(0).lower() for m in NAV_TOGGLE.finditer(html)}),
    }


def print_single(c: dict) -> int:
    print(f"source        : {c['source']}")
    print(f"size          : {c['size']} bytes")
    print(f"structure     : {'full document' if c['full_doc'] else 'fragment (tidy will wrap it)'}")
    if c["rdfa_doctype"]:
        print("doctype       : XHTML+RDFa — engine SKIPS tidy for this document")
    print(f"chrome tags   : {', '.join(c['chrome_tags']) or 'none'}")
    print(f"chrome classes: {', '.join(c['chrome_classes']) or 'none'}")
    print(f"fonts         : {', '.join(c['fonts']) or 'none'}")
    print(f"bootstrap     : {'yes' if c['bootstrap'] else 'no'}")
    print(f"nav toggle    : {', '.join(c['nav_toggle']) or 'none'}")
    print(f"css props ({len(c['css_props'])}): {', '.join(c['css_props']) or 'none'}")
    print(f"external assets ({len(c['assets'])}):")
    for a in c["assets"]:
        print(f"  - {a}")

    has_chrome = bool(c["chrome_tags"] or c["chrome_classes"])
    if has_chrome:
        print("\nRESULT: self-contained chrome detected — this is a candidate NEW SKIN,")
        print("not a page to strip-and-deploy under the unchanged current skin.")
        print("Compare fonts/css props/bootstrap/nav-toggle against any sibling")
        print("candidates (--compare) before deciding shared vs per-site vs passthrough")
        print("— see references/skin-commonality-assessment.md and skin-authoring-howto.md.")
        return 2
    print("\nRESULT: no self-contained chrome; this document is plain content,")
    print("safe to deploy under the current live skin unmodified.")
    return 0


def print_compare(classifications: list) -> int:
    print(f"{'source':<40} {'fonts':<20} {'bootstrap':<10} {'nav-toggle':<15} css-props")
    for c in classifications:
        print(
            f"{c['source']:<40} {','.join(c['fonts']) or '-':<20} "
            f"{'yes' if c['bootstrap'] else 'no':<10} "
            f"{','.join(c['nav_toggle']) or '-':<15} {','.join(c['css_props']) or '-'}"
        )
    all_props = [set(c["css_props"]) for c in classifications]
    shared_props = set.intersection(*all_props) if all_props else set()
    all_fonts = {tuple(c["fonts"]) for c in classifications}
    print(f"\nshared css custom-property names across ALL candidates: {sorted(shared_props) or 'none'}")
    print(f"distinct font sets across candidates: {len(all_fonts)} (1 = all match)")
    if shared_props and len(all_fonts) == 1:
        print("\nSIGNAL: strong commonality — a shared 'zion'-style skin is worth considering.")
    else:
        print("\nSIGNAL: weak/no commonality — separate per-site skins are more likely correct.")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    insecure = "--insecure" in argv
    argv = [a for a in argv if a != "--insecure"]

    if argv and argv[0] == "--compare":
        sources = argv[1:]
        if len(sources) < 2:
            print(__doc__)
            return 1
        classifications = []
        for s in sources:
            try:
                classifications.append(classify(s, load(s, insecure)))
            except Exception as e:
                print(f"ERROR: cannot load {s}: {e}")
                return 1
        return print_compare(classifications)

    if len(argv) != 1:
        print(__doc__)
        return 1
    try:
        html = load(argv[0], insecure)
    except Exception as e:
        print(f"ERROR: cannot load {argv[0]}: {e}")
        return 1
    return print_single(classify(argv[0], html))


if __name__ == "__main__":
    sys.exit(main())
