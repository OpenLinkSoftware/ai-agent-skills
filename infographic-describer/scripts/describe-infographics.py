#!/usr/bin/env python3
"""Generate RDF-Turtle descriptions for files in a WebDAV directory."""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


# Category IRIs for content-explorer-metadata.ttl
CATEGORY_IRIS = {
    "infographic": "https://www.openlinksw.com/DAV/www2.openlinksw.com/data/content-explorer/ttl/content-explorer-metadata.ttl#Infographic",
    "guide": "https://www.openlinksw.com/DAV/www2.openlinksw.com/data/content-explorer/ttl/content-explorer-metadata.ttl#Guide",
    "demo": "https://www.openlinksw.com/DAV/www2.openlinksw.com/data/content-explorer/ttl/content-explorer-metadata.ttl#Demo",
    "survey": "https://www.openlinksw.com/DAV/www2.openlinksw.com/data/content-explorer/ttl/content-explorer-metadata.ttl#Survey",
}

# MIME type mapping
MIME_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "mp4": "video/mp4",
    "html": "text/html",
}

# Schema type mapping
SCHEMA_TYPES = {
    "png": "schema:ImageObject",
    "jpg": "schema:ImageObject",
    "jpeg": "schema:ImageObject",
    "mp4": "schema:VideoObject",
    "html": "schema:WebPage",
}


def stem_to_name(stem):
    """Convert filename stem to human-readable name."""
    name = stem.replace("_", " ").replace("-", " ")
    name = re.sub(r"\s+", " ", name).strip()
    return name


def detect_categories(stem):
    """Detect categories from filename patterns."""
    lower = stem.lower()
    cats = []
    for keyword, iri in CATEGORY_IRIS.items():
        if keyword in lower:
            cats.append(iri)
    if not cats:
        cats.append(CATEGORY_IRIS["infographic"])
    return cats


def list_directory(base_url):
    """List files in a WebDAV directory."""
    req = urllib.request.Request(base_url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=30)
    html = resp.read().decode()
    files = re.findall(r'title="File - ([^"]+)"', html)
    return files


def check_describe(stem, ext, dav_prefix):
    """Check if a file has describe data in the triplestore."""
    iri = f"{dav_prefix}/{stem}.{ext}"
    query = f"DESCRIBE <{iri}>"
    url = "http://www.openlinksw.com/sparql?query=" + urllib.parse.quote(query) + "&output=text%2Fn3"

    req = urllib.request.Request(url, headers={"Accept": "text/n3, */*", "User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=30)
    data = resp.read().decode()
    return "Empty" not in data and len(data.strip()) > 50


def check_thumbnail(stem, category_dir):
    """Check if a thumbnail exists for the file."""
    url = f"https://www.openlinksw.com/data/content-explorer/thumbnails/{category_dir}-{stem}.avif"
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.status == 200
    except Exception:
        return False


def generate_turtle(entries, dav_prefix):
    """Generate Turtle from entries."""
    lines = [
        "@prefix schema: <http://schema.org/> .",
        "@prefix rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix wdrs:   <http://www.w3.org/2007/05/powder-s#> .",
        "@prefix xsd:    <http://www.w3.org/2001/XMLSchema#> .",
        "",
    ]

    for entry in entries:
        stem = entry["stem"]
        ext = entry["ext"]
        content_url = entry["content_url"]
        schema_type = SCHEMA_TYPES.get(ext, "schema:CreativeWork")
        mime_type = MIME_TYPES.get(ext, "application/octet-stream")
        name = entry["name"]
        description = entry["description"]
        categories = entry["categories"]
        thumbnail = entry.get("thumbnail_url")

        escaped_name = name.replace("\\", "\\\\").replace('"', '\\"')
        escaped_desc = description.replace("\\", "\\\\").replace('"', '\\"')

        lines.append(f"<{content_url}#this>")
        lines.append(f"    a {schema_type} ;")
        lines.append(f'    schema:name "{escaped_name}" ;')
        lines.append(f'    schema:description "{escaped_desc}" ;')
        lines.append(f'    schema:encodingFormat "{mime_type}" ;')
        lines.append(f"    schema:contentUrl <{content_url}> ;")

        if thumbnail:
            lines.append(f"    schema:thumbnailUrl <{thumbnail}> ;")

        cat_triples = " ,\n        ".join(f"<{c}>" for c in categories)
        lines.append(f"    schema:category {cat_triples} ;")

        encoded_iri = urllib.parse.quote(content_url, safe="")
        describe_url = f"https://www.openlinksw.com/describe/?url={encoded_iri}"
        lines.append(f"    wdrs:describedby <{describe_url}> .")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate RDF-Turtle descriptions for WebDAV directory files")
    parser.add_argument("--directory", required=True, help="WebDAV directory path (e.g., infographics)")
    parser.add_argument("--dav-prefix", default="https://www.openlinksw.com/DAV/www2.openlinksw.com/data", help="DAV base prefix")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--category-dir", help="Thumbnail category directory name (default: same as --directory)")
    parser.add_argument("--skip-thumbnails", action="store_true", help="Skip thumbnail probing")
    parser.add_argument("--skip-describe", action="store_true", help="Skip describe endpoint probing")
    parser.add_argument("--delay", type=float, default=0.3, help="Delay between requests (seconds)")
    args = parser.parse_args()

    category_dir = args.category_dir or args.directory
    base_url = f"https://www.openlinksw.com/data/{args.directory}/"
    dav_prefix = f"{args.dav_prefix}/{args.directory}"

    print(f"Listing {base_url}...")
    files = list_directory(base_url)
    print(f"Found {len(files)} files")

    entries = []
    for i, filename in enumerate(files):
        stem, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        content_url = f"{dav_prefix}/{filename}"
        name = stem_to_name(stem)
        categories = detect_categories(stem)

        entry = {
            "stem": stem,
            "ext": ext,
            "filename": filename,
            "content_url": content_url,
            "name": name,
            "description": f"Infographic: {name}",
            "categories": categories,
        }

        if not args.skip_thumbnails and ext in ("png", "jpg", "jpeg"):
            if check_thumbnail(stem, category_dir):
                entry["thumbnail_url"] = f"https://www.openlinksw.com/data/content-explorer/thumbnails/{category_dir}-{stem}.avif"
                print(f"  [{i+1}/{len(files)}] {filename}: has thumbnail")
            else:
                print(f"  [{i+1}/{len(files)}] {filename}: no thumbnail")
        else:
            print(f"  [{i+1}/{len(files)}] {filename}")

        entries.append(entry)
        if (i + 1) % 10 == 0:
            time.sleep(args.delay)

    turtle = generate_turtle(entries, dav_prefix)

    output_path = args.output or f"/Users/kidehen/Documents/RDF_DATA/shacl-shapes/{args.directory}-descriptions.ttl"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(turtle)

    # Validate
    try:
        from rdflib import Graph
        g = Graph()
        g.parse(output_path, format="turtle")
        print(f"\nValid Turtle: {len(g)} triples, {len(set(g.subjects()))} entities")
    except ImportError:
        print(f"\nSaved {len(entries)} descriptions to {output_path}")

    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
