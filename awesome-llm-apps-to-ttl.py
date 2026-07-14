#!/usr/bin/env python3
"""
Generate Turtle knowledge graph from awesome-llm-apps README
and OpenLink ai-agent-skills repository.

Models the awesome-llm-apps repo as schema:Collection with
skos:Concept categories and schema:SoftwareApplication apps + descriptions.

Meshes in ai-agent-skills as a second linked schema:Collection of
schema:SoftwareApplication skills with their own category scheme.

Output: /Users/kidehen/Documents/RDF_DATA/awesome-llm-apps.ttl
"""

import os
import re
import sys
import urllib.request

# ── Configuration ──────────────────────────────────────────────

LLM_REPO = "Shubhamsaboo/awesome-llm-apps"
LLM_BASE = f"https://github.com/{LLM_REPO}"
README_URL = f"https://raw.githubusercontent.com/{LLM_REPO}/main/README.md"

SKILLS_REPO = "OpenLinkSoftware/ai-agent-skills"
SKILLS_BASE = f"https://github.com/{SKILLS_REPO}"
SKILLS_HASH = SKILLS_BASE + "#"

OUTPUT_PATH = "/Users/kidehen/Documents/RDF_DATA/awesome-llm-apps.ttl"

# ── Creator data ───────────────────────────────────────────────

CREATOR = {
    "slug": "shubham-saboo",
    "name": "Shubham Saboo",
    "github": "https://github.com/Shubhamsaboo",
    "linkedin": "https://www.linkedin.com/in/shubhamsaboo/",
    "twitter": "https://twitter.com/Saboo_Shubham_",
    "website": "https://www.theunwindai.com",
}

# ── Language breakdown (from GitHub page metadata) ─────────────

LANGUAGES = {
    "Python": {"slug": "python", "percentage": 54.6},
    "TypeScript": {"slug": "typescript", "percentage": 21.6},
    "JavaScript": {"slug": "javascript", "percentage": 16.4},
    "HTML": {"slug": "html", "percentage": 4.5},
    "CSS": {"slug": "css", "percentage": 2.5},
    "Dockerfile": {"slug": "dockerfile", "percentage": 0.2},
}

# ── Skills data (from SKILL.md across 30 directories) ─────────

SKILL_CATEGORIES = [
    {
        "slug": "knowledge-graph-rdf",
        "name": "Knowledge Graph & RDF",
        "description": "Skills for generating and processing RDF knowledge graphs",
    },
    {
        "slug": "data-access-query",
        "name": "Data Access & Query",
        "description": "Skills for querying data spaces and knowledge graphs via SQL, SPARQL, and other protocols",
    },
    {
        "slug": "virtuoso-admin",
        "name": "Virtuoso Administration",
        "description": "Skills for managing and configuring OpenLink Virtuoso instances",
    },
    {
        "slug": "uriburner-opal",
        "name": "URIBurner / OPAL",
        "description": "Skills for the URIBurner semantic data discovery and MCP server platform",
    },
    {
        "slug": "identity-security",
        "name": "Identity & Security",
        "description": "Skills for digital identity generation and secure communication",
    },
    {
        "slug": "commerce-payment",
        "name": "Commerce & Payment",
        "description": "Skills for e-commerce and payment processing",
    },
    {
        "slug": "content-feeds",
        "name": "Content & Feeds",
        "description": "Skills for content feed management and WebDAV operations",
    },
    {
        "slug": "fifa-world-cup",
        "name": "World Cup / FIFA",
        "description": "Skills for FIFA World Cup knowledge graphs and analytics",
    },
    {
        "slug": "browser-ui",
        "name": "Browser & UI",
        "description": "Skills for browser automation and screencast recording",
    },
    {
        "slug": "det-generators",
        "name": "DET Generators",
        "description": "Skills for generating Virtuoso Data Export Transformer plugins",
    },
    {
        "slug": "fediverse",
        "name": "Fediverse",
        "description": "Skills for ActivityPub/Fediverse interactions",
    },
]

SKILLS = [
    {
        "slug": "kg-generator",
        "name": "kg-generator",
        "description": "Generate comprehensive Knowledge Graphs (RDF-Turtle by default, or JSON-LD and other RDF serializations on request) from content at file: or http(s): scheme URLs.",
        "version": None,
        "cat": "knowledge-graph-rdf",
    },
    {
        "slug": "rdf-infographic-skill",
        "name": "rdf-infographic-skill",
        "description": "Generate sophisticated, interactive HTML infographics and optional Markdown companion documents from RDF data in any format (Turtle, RDF/XML, N-Triples, JSON-LD).",
        "version": None,
        "cat": "knowledge-graph-rdf",
    },
    {
        "slug": "document-to-kg-skill",
        "name": "document-to-kg-skill",
        "description": "Transforms documents or text into RDF-based Knowledge Graphs using schema.org terms via a 4-step workflow.",
        "version": "1.0.0",
        "cat": "knowledge-graph-rdf",
    },
    {
        "slug": "linked-data-skills",
        "name": "linked-data-skills",
        "description": "Generates Knowledge Graphs from relational database objects via Virtuoso RDF Views, or from documents transformed to RDF using schema.org terms.",
        "version": "3.2.0",
        "cat": "knowledge-graph-rdf",
    },
    {
        "slug": "fuxi-engineer",
        "name": "fuxi-engineer",
        "description": "Use FuXi for semantic web reasoning needs (RDF, RDFS, OWL, RIF, SPARQL) with forward and backward chaining.",
        "version": None,
        "cat": "knowledge-graph-rdf",
    },
    {
        "slug": "data-twingler",
        "name": "data-twingler",
        "description": "Execute SQL, SPARQL, SPASQL, SPARQL-FED, and GraphQL queries against live data spaces and knowledge graphs via OpenLink's OpenAPI-compliant web services.",
        "version": "2.0.86",
        "cat": "data-access-query",
    },
    {
        "slug": "dbpedia-query-skill",
        "name": "dbpedia-query-skill",
        "description": "Transform natural language questions into SPARQL queries for DBpedia and generate beautiful HTML results pages.",
        "version": None,
        "cat": "data-access-query",
    },
    {
        "slug": "wikidata-query-skill",
        "name": "wikidata-query-skill",
        "description": "Transform natural language questions into SPARQL queries for Wikidata and generate beautiful HTML results pages.",
        "version": None,
        "cat": "data-access-query",
    },
    {
        "slug": "s3-query-skill",
        "name": "s3-query-skill",
        "description": "Client-side S3 API access for querying data at S3-compatible endpoints (AWS, Hugging Face, Cloudflare R2, MinIO) via DuckDB httpfs, AWS CLI, and rclone.",
        "version": None,
        "cat": "data-access-query",
    },
    {
        "slug": "iodbc-dsn-manager",
        "name": "iodbc-dsn-manager",
        "description": "Configure and verify ODBC Data Source Names (DSNs) using iODBC or unixODBC on macOS and Linux.",
        "version": None,
        "cat": "data-access-query",
    },
    {
        "slug": "virtuoso-support-agent",
        "name": "virtuoso-support-agent",
        "description": "Technical support and database management for OpenLink Virtuoso Server with RDF Views generation, SPARQL queries, and comprehensive database operations using 23 MCP tools.",
        "version": None,
        "cat": "virtuoso-admin",
    },
    {
        "slug": "virtuoso-rdf-loader",
        "name": "virtuoso-rdf-loader",
        "description": "Bulk-load RDF archives (N-Triples, Turtle, RDF/XML, N-Quads, TriG, JSON-LD, Notation3) into a Virtuoso instance via isql using ld_dir and rdf_loader_run.",
        "version": None,
        "cat": "virtuoso-admin",
    },
    {
        "slug": "openlink-license-manager",
        "name": "openlink-license-manager",
        "description": "Start, stop, restart, enable at boot, and check the status of the OpenLink License Manager (oplmgr) daemon on macOS, Linux, and Windows.",
        "version": None,
        "cat": "virtuoso-admin",
    },
    {
        "slug": "openlink-license-reader",
        "name": "openlink-license-reader",
        "description": "Read and display OpenLink Software license files (.lic) in a beautified, human-readable format by parsing ASN.1 DER-encoded files.",
        "version": None,
        "cat": "virtuoso-admin",
    },
    {
        "slug": "openlink-request-broker-configurator",
        "name": "openlink-request-broker-configurator",
        "description": "Configure and manage the OpenLink Request Broker (oplrqb) rule book including ODBC and JDBC agent rules, mapping rules, and broker settings.",
        "version": None,
        "cat": "virtuoso-admin",
    },
    {
        "slug": "uriburner-opal-agent-skills",
        "name": "uriburner-opal-agent-skills",
        "description": "Comprehensive toolkit for URIBurner MCP Server enabling semantic data discovery, Knowledge Graph exploration, SPARQL/SQL query execution, RDF sponging, and database management.",
        "version": None,
        "cat": "uriburner-opal",
    },
    {
        "slug": "youid",
        "name": "youid",
        "description": "Generate, verify, and manage Web-scale verifiable digital identities (NetIDs) using semantic web standards including X.509 certificates, WebID profiles, and identity card HTML pages.",
        "version": "1.0.1",
        "cat": "identity-security",
    },
    {
        "slug": "mtls-curl",
        "name": "mtls-curl",
        "description": "Execute mTLS (Mutual TLS) sessions using PKCS#12 certificate bundles for HTTP/HTTPS requests via curl or Virtuoso SQL via iSQL with WebID authentication.",
        "version": "1.1.0",
        "cat": "identity-security",
    },
    {
        "slug": "acp-client",
        "name": "acp-client",
        "description": "Intent-driven Adaptive Commerce Platform client handling natural-language purchase requests via checkout, cart, and order flows against OpenLink's ACP API.",
        "version": "1.1.0",
        "cat": "commerce-payment",
    },
    {
        "slug": "mpp-stripe-client",
        "name": "mpp-stripe-client",
        "description": "Machine Payment Protocol client using Stripe that handles the 402 challenge flow by creating Stripe Shared Payment Tokens and retrying resource retrieval.",
        "version": "1.0.0",
        "cat": "commerce-payment",
    },
    {
        "slug": "opml-rss-reader",
        "name": "opml-rss-reader",
        "description": "Manage, explore, and troubleshoot OPML, RSS, and Atom news feeds using predefined SPARQL/SPASQL queries against OpenLink's linked-data infrastructure.",
        "version": "1.2.0",
        "cat": "content-feeds",
    },
    {
        "slug": "rss-feed-generator",
        "name": "rss-feed-generator",
        "description": "Generate valid RSS 2.0 or Atom 1.0 feeds from web pages that lack a native feed by extracting post metadata from the page content.",
        "version": "1.0.0",
        "cat": "content-feeds",
    },
    {
        "slug": "set-webdav-resource-property",
        "name": "set-webdav-resource-property",
        "description": "Set custom WebDAV properties on resources via PROPPATCH requests using curl with support for arbitrary prefixed properties and batch processing.",
        "version": None,
        "cat": "content-feeds",
    },
    {
        "slug": "wc2026-match-report",
        "name": "wc2026-match-report",
        "description": "Generate a complete single-file HTML intelligence report for the FIFA World Cup 2026 from live Knowledge Graph data including match, player, and analytics reports.",
        "version": "1.2.0",
        "cat": "fifa-world-cup",
    },
    {
        "slug": "world-cup-2026-navigator",
        "name": "world-cup-2026-navigator",
        "description": "Expert navigator for the OpenLink FIFA World Cup Knowledge Graph and RDF ontology for writing SPARQL queries against FIFA data.",
        "version": None,
        "cat": "fifa-world-cup",
    },
    {
        "slug": "pinchtab",
        "name": "pinchtab",
        "description": "Browser automation through PinchTab for opening web pages, clicking through flows, filling forms, scraping text, and exporting screenshots or PDFs.",
        "version": None,
        "cat": "browser-ui",
    },
    {
        "slug": "screencast-recorder",
        "name": "screencast-recorder",
        "description": "Record screencast videos of web application interactions using shot-scraper video with dual-format YAML and RDF Turtle storyboards.",
        "version": None,
        "cat": "browser-ui",
    },
    {
        "slug": "csv-to-rdf-det-generator",
        "name": "csv-to-rdf-det-generator",
        "description": "Create custom DAV Data Export Transformers that accept CSV uploads, transform them to RDF, and write to the Quad Store with DAV hook functions.",
        "version": None,
        "cat": "det-generators",
    },
    {
        "slug": "rdf-det-variant-generator",
        "name": "rdf-det-variant-generator",
        "description": "Create custom DAV DET variants based on RDF Import DET for Virtuoso that ingest RDF documents into the Quad Store.",
        "version": None,
        "cat": "det-generators",
    },
    {
        "slug": "fediverse-crud",
        "name": "fediverse-crud",
        "description": "Perform ActivityPub read/write operations against Fediverse instances including Note, Like, Announce, Follow, Delete, and Undo with OAuth and WebFinger resolution.",
        "version": None,
        "cat": "fediverse",
    },
]

# Validate skills reference existing categories
CAT_SLUGS = {c["slug"] for c in SKILL_CATEGORIES}
for sk in SKILLS:
    assert sk["cat"] in CAT_SLUGS, f"Skill {sk['slug']} references unknown category {sk['cat']}"


# ── Helpers ───────────────────────────────────────────────────

def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "AwesomeLLMKg/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s


def heading_to_slug(heading: str) -> str:
    s = re.sub(r"[^\w\s-]", "", heading).strip()
    s = s.lower().strip()
    s = re.sub(r"\s+", "-", s)
    return s


def strip_emoji(text: str) -> str:
    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F1E0-\U0001F1FF"
        "\u200d"
        "\ufe0f"
        "\u00a9\u00ae\u2000-\u3300"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text).strip()


def escape_ttl(s: str) -> str:
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "\\r")
    return s


def strip_emoji_for_desc(text: str) -> str:
    """Remove emoji characters from text for description use."""
    return strip_emoji(text)


def generate_description(name: str, category_name: str) -> str:
    """Generate a factual description from app name and category."""
    cat = category_name.lower().strip()
    clean_name = strip_emoji_for_desc(name).strip()

    if "agent skill" in cat:
        prefix = "A starter AI agent"
    elif "multi-agent" in cat or "team" in cat:
        prefix = "A multi-agent team"
    elif "voice" in cat:
        prefix = "A voice-enabled AI agent"
    elif "rag" in cat:
        prefix = "A RAG implementation"
    elif "mcp" in cat or "canvas" in cat or "generative ui" in cat:
        prefix = "A generative AI application"
    elif "chat with data" in cat:
        prefix = "An agent for conversational data querying"
    elif "chat with doc" in cat:
        prefix = "An agent for document analysis"
    elif "chat with website" in cat or "chat with web" in cat:
        prefix = "An agent for web content interaction"
    elif "fine-tuning" in cat or "course" in cat:
        prefix = "A learning resource"
    elif "optimization" in cat or "tool" in cat:
        prefix = "An LLM optimization tool"
    elif "featured" in cat:
        prefix = "A featured AI application"
    elif "utility" in cat or "quick start" in cat:
        prefix = "A utility"
    else:
        prefix = "An AI application"

    return f"{prefix}: {clean_name}"


def parse_readme(raw: str) -> dict:
    """Parse README.md into structured data."""
    title_match = re.search(r"^#\s+.*?\n\n(.+?)\n", raw, re.MULTILINE)
    repo_desc = title_match.group(1).strip() if title_match else ""

    why_match = re.search(r"## 💡 Why this exists\n\n(.+?)\n##", raw, re.DOTALL)
    why_text = why_match.group(1).strip() if why_match else ""

    sections_raw = re.split(r"\n###\s+", raw)
    categories = []
    seen_slugs = set()

    for section in sections_raw:
        if not section.strip():
            continue

        lines = section.split("\n")
        heading = lines[0].strip()
        remaining_lines = lines[1:]

        cat_desc = ""
        if remaining_lines:
            first_line = remaining_lines[0].strip()
            if first_line.startswith("*") and first_line.endswith("*") and "[" not in first_line:
                cat_desc = first_line.strip("*").strip()
            else:
                for rl in remaining_lines:
                    if rl.strip().startswith("* [") or rl.strip().startswith("["):
                        break
                    cat_desc += rl.strip() + " "
                cat_desc = cat_desc.strip()

        apps = []
        bullet_pattern = re.compile(
            r"^\s*\*\s+\[([^\]]+)\]\(([^)]+)\)"
            r"(?:\s*-\s*(.+))?"
            r"(?:\s*<sub>([^<]*)</sub>)?\s*$"
        )
        link_pattern = re.compile(
            r"^\s*\[([^\]]+)\]\(([^)]+)\)\s*$"
        )

        for line in remaining_lines:
            stripped = line.strip()
            if not stripped:
                continue

            bm = bullet_pattern.match(line)
            if bm:
                name, url, desc, external_marker = bm.groups()
                external = bool(external_marker and "external" in external_marker)
                apps.append({
                    "name": (desc.strip() if desc else name.strip()),
                    "full_name": name.strip(),
                    "url": url.strip(),
                    "description": desc.strip() if desc else "",
                    "external": external,
                })
                continue

            lm = link_pattern.match(line)
            if lm:
                name, url = lm.groups()
                apps.append({
                    "name": name.strip(),
                    "full_name": name.strip(),
                    "url": url.strip(),
                    "description": "",
                    "external": False,
                })
                continue

        if not apps:
            continue

        cat_slug = heading_to_slug(heading)
        if cat_slug in seen_slugs:
            cat_slug = cat_slug + "-" + str(
                sum(1 for s in seen_slugs if s.startswith(cat_slug))
            )
        seen_slugs.add(cat_slug)

        clean_heading = strip_emoji(heading)
        heading_emoji = heading.replace(clean_heading, "").strip() or ""

        for app in apps:
            app_url = app["url"]
            if app_url.startswith("/"):
                app_url = f"https://github.com{app_url}"
            elif not app_url.startswith("http"):
                app_url = f"{LLM_BASE}/blob/main/{app_url}"
                app_url = app_url.rstrip("/")
            app["url"] = app_url

        categories.append({
            "slug": cat_slug,
            "heading": heading,
            "heading_clean": clean_heading,
            "emoji": heading_emoji,
            "description": cat_desc,
            "apps": apps,
        })

    return {
        "description": repo_desc,
        "why_text": why_text,
        "categories": categories,
    }


# ── Main generator ────────────────────────────────────────────

def build(output_path: str) -> None:
    raw = fetch_text(README_URL)
    data = parse_readme(raw)

    with open(output_path, "w", encoding="utf-8") as f:

        def w(s: str = "") -> None:
            f.write(s + "\n")

        # ── Prefix declarations ──
        w("@base <{}> .".format(LLM_BASE))
        w("@prefix : <{}#> .".format(LLM_BASE))
        w("@prefix skills: <{}#> .".format(SKILLS_BASE))
        w("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .")
        w("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
        w("@prefix owl: <http://www.w3.org/2002/07/owl#> .")
        w("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .")
        w("@prefix schema: <http://schema.org/> .")
        w("@prefix skos: <http://www.w3.org/2004/02/skos/core#> .")
        w("@prefix dct: <http://purl.org/dc/terms/> .")
        w("@prefix foaf: <http://xmlns.com/foaf/0.1/> .")
        w()

        # ── Repository / Collection ──
        repo_desc = escape_ttl(data["description"])
        why_text = escape_ttl(data.get("why_text", ""))

        w("# ────────────────────────────────────────────────────────")
        w("# Collection: Awesome LLM Apps")
        w("# ────────────────────────────────────────────────────────")
        w()
        w(":this a schema:Collection ;")
        w('    schema:name "Awesome LLM Apps"@en ;')
        w('    schema:description "{}"@en .'.format(repo_desc))
        w()

        # Creator
        w("# ── Creator ──")
        w(":{} a schema:Person ;".format(CREATOR["slug"]))
        w('    schema:name "{}"@en ;'.format(CREATOR["name"]))
        w("    schema:url <{}> ;".format(CREATOR["github"]))
        w("    schema:sameAs <{}> ;".format(CREATOR["linkedin"]))
        w("    schema:sameAs <{}> ;".format(CREATOR["twitter"]))
        w("    foaf:homepage <{}> ;".format(CREATOR["website"]))
        w("    dct:subject <#category/ai-agents> .")
        w()
        w(":this schema:creator :{} .".format(CREATOR["slug"]))
        w()

        # ── Languages ──
        w("# ── Programming Languages ──")
        for lang_name, lang_data in LANGUAGES.items():
            slug = lang_data["slug"]
            w("<#language/{}> a schema:ProgrammingLanguage ;".format(slug))
            w('    schema:name "{}"@en ;'.format(lang_name))
            w('    schema:identifier "{}" ;'.format(slug))
            w("    schema:url <https://{lang}.org/> .".format(
                lang=slug.replace("typescript", "typescriptlang")
                         .replace("javascript", "ecma-international")
                         .replace("dockerfile", "docker")
            ))
            w()

        w(":this schema:programmingLanguage")
        for i, (lang_name, lang_data) in enumerate(LANGUAGES.items()):
            sep = "," if i < len(LANGUAGES) - 1 else " ."
            w("    <#language/{}>{}".format(lang_data["slug"], sep))
        w()

        # ── Interaction Statistics ──
        w("# ── Statistics ──")
        w(":stats a schema:InteractionCounter ;")
        w("    schema:interactionType schema:FollowAction ;")
        w("    schema:userInteractionCount 117000 ;")
        w('    schema:description "GitHub Stars"@en .')
        w()
        w(":fork-stats a schema:InteractionCounter ;")
        w("    schema:interactionType schema:ShareAction ;")
        w("    schema:userInteractionCount 17400 ;")
        w('    schema:description "GitHub Forks"@en .')
        w()
        w(":this schema:interactionStatistic :stats, :fork-stats ;")
        w("    dct:license <https://www.apache.org/licenses/LICENSE-2.0> .")
        w()

        # ── Category Scheme ──
        w("# ── Category Scheme ──")
        w(":categories a skos:ConceptScheme ;")
        w('    rdfs:label "Awesome LLM Apps Categories"@en ;')
        w('    rdfs:comment "The 15 categories of AI agent and RAG app templates in the Awesome LLM Apps repository."@en ;')
        w("    dct:subject :this .")
        w()

        # ── Categories and apps ──
        apps_total = 0
        for cat in data["categories"]:
            cat_slug = cat["slug"]
            cat_name = cat["heading_clean"]
            cat_desc = escape_ttl(cat["description"])

            w("# ── Category: {} ──".format(cat_name))
            w("<#category/{}> a skos:Concept ;".format(cat_slug))
            w('    skos:prefLabel "{}"@en ;'.format(cat_name))
            w("    skos:inScheme :categories ;")
            w("    rdfs:isDefinedBy :this .")
            w()

            for app in cat["apps"]:
                app_path = app["url"].replace(LLM_BASE + "/blob/main/", "")
                app_slug = slugify(app_path)
                app_name = escape_ttl(app["name"])
                app_desc = escape_ttl(app["description"])

                if not app_desc:
                    app_desc = escape_ttl(generate_description(app["name"], cat_name))

                w("# ── App: {} ──".format(app_name))
                w("<#template/{}> a schema:SoftwareApplication ;".format(app_slug))
                w('    schema:name "{}"@en ;'.format(app_name))
                w('    schema:url <{}> ;'.format(app["url"]))
                w('    schema:description "{}"@en ;'.format(app_desc))
                w("    schema:applicationCategory <#category/{}> ;".format(cat_slug))
                w("    schema:isPartOf :this ;")
                if app["external"]:
                    w('    schema:isAccessibleForFree "true"^^xsd:boolean ;')
                    w("    schema:provider <{}> ;".format(
                        re.match(r"https?://([^/]+)", app["url"]).group(0)
                    ))
                w("    rdfs:isDefinedBy :this .")
                w()
                w(":this schema:hasPart <#template/{}> .".format(app_slug))
                w()
                apps_total += 1

        # ────────────────────────────────────────────────────────
        # Skills Collection (ai-agent-skills)
        # ────────────────────────────────────────────────────────
        w()
        w("# ────────────────────────────────────────────────────────")
        w("# Collection: OpenLink ai-agent-skills")
        w("# ────────────────────────────────────────────────────────")
        w()

        sk_hash = SKILLS_HASH

        w("# ── Related Link ──")
        w(":this schema:relatedLink <{}this> .".format(sk_hash))
        w("<{}this> schema:relatedLink :this .".format(sk_hash))
        w()

        w("<{}this> a schema:Collection ;".format(sk_hash))
        w('    schema:name "OpenLink AI Agent Skills"@en ;')
        w('    schema:description "A collection of 30 reusable AI agent skills for semantic web data sources, knowledge graphs, and databases in the OpenLink/Virtuoso/URIBurner ecosystem."@en ;')
        w("    schema:url <{}> ;".format(SKILLS_BASE))
        w("    dct:license <https://github.com/OpenLinkSoftware/ai-agent-skills/blob/main/LICENSE> ;")
        w("    rdfs:isDefinedBy <{}> .".format(SKILLS_BASE))
        w()

        # ── Skill Category Scheme ──
        w("# ── Skill Category Scheme ──")
        w("<{}skill-categories> a skos:ConceptScheme ;".format(sk_hash))
        w('    rdfs:label "OpenLink AI Agent Skill Categories"@en ;')
        w('    rdfs:comment "The 11 categories of skills in the OpenLink ai-agent-skills repository."@en ;')
        w("    dct:subject <{}this> .".format(sk_hash))
        w()

        for sc in SKILL_CATEGORIES:
            w("<{}category/{}> a skos:Concept ;".format(sk_hash, sc["slug"]))
            w('    skos:prefLabel "{}"@en ;'.format(sc["name"]))
            w('    rdfs:comment "{}"@en ;'.format(sc["description"]))
            w("    skos:inScheme <{}skill-categories> ;".format(sk_hash))
            w("    rdfs:isDefinedBy <{}this> .".format(sk_hash))
            w()

        # ── Individual skills ──
        w("# ── Skills ──")
        for sk in SKILLS:
            name = escape_ttl(sk["name"])
            desc = escape_ttl(sk["description"])
            version = sk["version"]
            skill_url = f"{SKILLS_BASE}/tree/main/{sk['slug']}"

            w("# ── Skill: {} ──".format(name))
            w("<{}> a schema:SoftwareApplication ;".format(sk_hash + sk["slug"]))
            w('    schema:name "{}"@en ;'.format(name))
            w('    schema:description "{}"@en ;'.format(desc))
            w("    schema:url <{}> ;".format(skill_url))
            if version:
                w('    schema:version "{}" ;'.format(version))
            w("    schema:applicationCategory <{}category/{}> ;".format(sk_hash, sk["cat"]))
            w("    schema:isPartOf <{}this> ;".format(sk_hash))
            w("    rdfs:isDefinedBy <{}this> .".format(sk_hash))
            w()
            w("<{}this> schema:hasPart <{}> .".format(sk_hash, sk_hash + sk["slug"]))
            w()

    print("Wrote {} categories, {} apps from awesome-llm-apps to {}".format(
        len(data["categories"]),
        apps_total,
        output_path,
    ))
    print("Wrote {} skills from ai-agent-skills to {}".format(
        len(SKILLS),
        output_path,
    ))
    print("Output: " + output_path)


if __name__ == "__main__":
    build(OUTPUT_PATH)
