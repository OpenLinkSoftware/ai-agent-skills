#!/usr/bin/env python3
"""Publish WebDAV weblog posts and apply schema:category metadata per upload.

This is the WebDAV-post workflow companion to the Virtuoso-side VSP engine. It
uploads ordinary files via PUT, derives category labels from the document text,
sets schema:category with PROPPATCH, and verifies the property with PROPFIND.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote, urljoin

SCHEMA_NS = "https://schema.org/"


def xml_escape(value: str) -> str:
    return html.escape(value, quote=True)


def build_url(base_url: str, resource: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", quote(resource.lstrip("/")))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def clean_title(text: str, fallback: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    if not match:
        return fallback
    title = re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()
    return title or fallback


def add_cat(cats: list[str], label: str) -> None:
    if label and label not in cats:
        cats.append(label)


def detect_fifa_player_categories(text: str) -> list[str]:
    lower = text.lower()
    cats: list[str] = []
    if "player intelligence report" not in lower or "fifa world cup" not in lower:
        return cats
    add_cat(cats, "FIFA Player Intelligence Reports")
    add_cat(cats, "FIFA World Cup 2026")
    country_match = re.search(r"Player intelligence report for .*?\(([^,#)]+)", text, re.I | re.S)
    if not country_match:
        country_match = re.search(r"2026 FIFA World Cup\s*[·-]\s*([^·<\n]+)\s*[·-]", text, re.I)
    if country_match:
        country = re.sub(r"\s+", " ", html.unescape(country_match.group(1))).strip(" .;:-")
        if country:
            add_cat(cats, f"National Team: {country}")
    position_match = re.search(r"2026 FIFA World Cup\s*[·-]\s*[^·<\n]+\s*[·-]\s*([^·<#\n]+)", text, re.I)
    if position_match:
        position = re.sub(r"\s+", " ", html.unescape(position_match.group(1))).strip(" .;:-")
        if position:
            add_cat(cats, f"Position: {position}")
    if any(token in lower for token in ("shot map", "creation map", "temporal analytics", "assists")):
        add_cat(cats, "Player Analytics")
    return cats


def detect_generic_categories(text: str) -> list[str]:
    lower = text.lower()
    cats: list[str] = []
    signals = [
        ("Semantic Web, RDF & Linked Data", ("linked data", "semantic web", "rdf", "ontology")),
        ("Knowledge Graphs", ("knowledge graph", "knowledge graphs", "entity", "relationship")),
        ("AI Agents & LLMs", ("ai agent", "agentic", "llm", "chatgpt", "gpt")),
        ("APIs, Protocols & Agent Skills", ("api", "rest", "oauth", "mcp", "a2a", "skill")),
        ("Virtuoso Platform", ("virtuoso", "webdav", "vsp", "sparql", "spasql", "sql")),
        ("Analytics & Data Engineering", ("analytics", "data engineering", "etl", "elt", "lakehouse")),
        ("Identity, Security & Privacy", ("security", "privacy", "webid", "identity", "certificate")),
        ("Cloud Storage & S3", ("s3", "bucket", "object storage", "cloud storage")),
        ("FIFA World Cup & Football", ("fifa", "world cup", "football", "soccer")),
    ]
    for label, tokens in signals:
        if any(token in lower for token in tokens):
            add_cat(cats, label)
    if not cats:
        add_cat(cats, "WebDAV Published Documents")
    return cats[:8]


def infer_categories(path: Path, profile: str, explicit: str | None) -> str:
    if explicit:
        parts = [p.strip() for chunk in explicit.split(";") for p in chunk.split(",")]
        return "; ".join(p for p in parts if p)
    text = read_text(path)
    if profile == "fifa-player-reports":
        cats = detect_fifa_player_categories(text)
    elif profile == "generic":
        cats = detect_generic_categories(text)
    else:
        cats = detect_fifa_player_categories(text) or detect_generic_categories(text)
    return "; ".join(cats)


def category_prop_xml(categories: str) -> str:
    return f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<D:propertyupdate xmlns:D=\"DAV:\" xmlns:schema=\"https://schema.org/\">
  <D:set>
    <D:prop>
      <schema:category>{xml_escape(categories)}</schema:category>
    </D:prop>
  </D:set>
</D:propertyupdate>
"""


def category_propfind_xml() -> str:
    return """<?xml version=\"1.0\" encoding=\"utf-8\"?>
<D:propfind xmlns:D=\"DAV:\" xmlns:schema=\"https://schema.org/\">
  <D:prop><schema:category /></D:prop>
</D:propfind>
"""


def curl_base(args: argparse.Namespace) -> list[str]:
    cmd = ["curl", "--fail", "--silent", "--show-error", "--location", "--anyauth"]
    if args.insecure:
        cmd.append("--insecure")
    if args.curl_config:
        cmd.extend(["--config", args.curl_config])
    if args.user:
        password = os.environ.get(args.password_env) if args.password_env else None
        if args.password_env and password is None:
            raise RuntimeError(f"Missing password environment variable: {args.password_env}")
        cmd.extend(["--user", f"{args.user}:{password or ''}"])
    if args.bearer_env:
        token = os.environ.get(args.bearer_env)
        if token is None:
            raise RuntimeError(f"Missing bearer token environment variable: {args.bearer_env}")
        cmd.extend(["--oauth2-bearer", token])
    if args.cert_type:
        cmd.extend(["--cert-type", args.cert_type])
    if args.cert:
        cmd.extend(["--cert", args.cert])
    if args.cacert:
        cmd.extend(["--cacert", args.cacert])
    if args.on_behalf_of:
        cmd.extend(["-H", f"On-Behalf-Of: {args.on_behalf_of}"])
    return cmd


def run_curl(cmd: list[str], dry_run: bool) -> str:
    if dry_run:
        print(f"DRY-RUN\t{' '.join(cmd)}")
        return ""
    completed = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return completed.stdout


def put_file(args: argparse.Namespace, path: Path, url: str) -> None:
    cmd = curl_base(args) + ["-T", str(path), url]
    run_curl(cmd, args.dry_run)


def proppatch_categories(args: argparse.Namespace, url: str, categories: str) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".xml", delete=False) as tmp:
        tmp.write(category_prop_xml(categories))
        tmp_path = tmp.name
    try:
        cmd = curl_base(args) + ["-X", "PROPPATCH", "-H", "Content-Type: application/xml", "--data-binary", f"@{tmp_path}", url]
        run_curl(cmd, args.dry_run)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def verify_category(args: argparse.Namespace, url: str, expected: str) -> bool:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".xml", delete=False) as tmp:
        tmp.write(category_propfind_xml())
        tmp_path = tmp.name
    try:
        cmd = curl_base(args) + ["-X", "PROPFIND", "-H", "Depth: 0", "-H", "Content-Type: application/xml", "--data-binary", f"@{tmp_path}", url]
        xml = run_curl(cmd, args.dry_run)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    if args.dry_run:
        return True
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return expected in xml
    values = [el.text or "" for el in root.findall(f".//{{{SCHEMA_NS}}}category")]
    return any(value.strip() == expected for value in values)


def publish_one(args: argparse.Namespace, path: Path) -> int:
    if path.name.startswith("._") or path.name == ".DS_Store":
        print(f"skipped-sidecar\t{path}")
        return 0
    if not path.is_file():
        print(f"not-a-file\t{path}", file=sys.stderr)
        return 1
    resource = args.remote_name or path.name
    url = build_url(args.base_url, resource)
    categories = infer_categories(path, args.profile, args.category)
    title = clean_title(read_text(path), path.name)
    print(f"publish\t{path}\t->\t{url}")
    put_file(args, path, url)
    if args.no_category:
        print(f"uploaded\t{resource}\tcategory=skipped")
        return 0
    if not categories:
        print(f"no-category\t{resource}", file=sys.stderr)
        return 1
    print(f"schema:category\t{resource}\t{categories}")
    proppatch_categories(args, url, categories)
    if not verify_category(args, url, categories):
        print(f"verify-failed\t{resource}\t{categories}", file=sys.stderr)
        return 1
    print(f"verified\t{resource}\ttitle={title}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload WebDAV weblog posts and set schema:category per file.")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--base-url", required=True, help="Target WebDAV collection URL")
    parser.add_argument("--profile", choices=["auto", "generic", "fifa-player-reports"], default="auto")
    parser.add_argument("--category", help="Explicit schema:category text for all uploaded files")
    parser.add_argument("--remote-name", help="Remote filename; only valid with one local file")
    parser.add_argument("--no-category", action="store_true", help="Upload only, without PROPPATCH metadata")
    parser.add_argument("--user")
    parser.add_argument("--password-env")
    parser.add_argument("--bearer-env")
    parser.add_argument("--curl-config")
    parser.add_argument("--cert-type")
    parser.add_argument("--cert")
    parser.add_argument("--cacert")
    parser.add_argument("--on-behalf-of")
    parser.add_argument("--insecure", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.remote_name and len(args.files) != 1:
        print("--remote-name can only be used with one local file", file=sys.stderr)
        return 2
    failures = 0
    try:
        for path in args.files:
            failures += publish_one(args, path)
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"error\t{exc}", file=sys.stderr)
        return 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
