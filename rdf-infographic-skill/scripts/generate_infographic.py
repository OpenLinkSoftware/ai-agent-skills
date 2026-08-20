#!/usr/bin/env python3
"""
RDF Infographic Generator — Build self-contained HTML infographics from RDF data.

Usage:
    python3 generate_infographic.py --ttl input.ttl --output out.html
    python3 generate_infographic.py --ttl input.ttl --output out.html --title "My Title" --tagline "..." --source-url "..."

The generator parses the RDF, extracts entities and narrative sections,
then assembles a complete HTML infographic with:
  - Floating navigation with theme toggle
  - D3.js Knowledge Graph Explorer (Basic/Advanced modes)
  - FAQ, glossary, HowTo sections (auto-extracted from RDF annotations)
  - SPARQL query workbench
  - Attribution footer
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from html_assembler import assemble_html


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate RDF-backed HTML infographic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--ttl", required=True, help="Input RDF file (Turtle/JSON-LD/NTriples)")
    parser.add_argument("--output", "-o", required=True, help="Output HTML file path")
    parser.add_argument("--title", default="", help="Page title (default: derived from RDF)")
    parser.add_argument("--description", default="", help="Meta description")
    parser.add_argument("--tagline", default="", help="Hero tagline text")
    parser.add_argument("--hero-tagline", default="", help="Hero metadata line (e.g. author + source)")
    parser.add_argument("--meta-html", default="", help="Hero meta HTML (published date, source link)")
    parser.add_argument("--source-url", default="", help="Source URL for attribution")
    parser.add_argument("--source-label", default="", help="Source label for attribution")
    parser.add_argument("--resolver-pattern", default="https://linkeddata.uriburner.com/describe/?url=",
                        help="Resolver URL pattern (default: URIBurner)")
    parser.add_argument("--llm-name", default="Claude Sonnet 5",
                        help="Executing LLM/model name for the KG-curation attribution line (default: Claude Sonnet 5)")
    parser.add_argument("--llm-url", default="https://www.anthropic.com/claude",
                        help="Executing LLM's canonical product page (default: https://www.anthropic.com/claude)")
    parser.add_argument("--revised-by-name", default="",
                        help="Model that REVISED an artifact an earlier model generated "
                             "(e.g. after a mid-session /model switch). Recorded alongside "
                             "--llm-name, never replacing it.")
    parser.add_argument("--revised-by-url", default="",
                        help="Canonical product page for --revised-by-name")
    parser.add_argument("--agent-env", default="",
                        help="Optional agent/runtime environment label for footer generation-environment card (e.g. 'Grok CLI (Grok Build TUI)')")

    args = parser.parse_args()

    rdf_path = Path(args.ttl)
    if not rdf_path.exists():
        print(f"Error: RDF file not found: {rdf_path}", file=sys.stderr)
        return 1

    success = assemble_html(
        rdf_path=args.ttl,
        output_path=args.output,
        title=args.title,
        description=args.description,
        tagline=args.tagline,
        hero_tagline=args.hero_tagline,
        meta_html=args.meta_html,
        source_url=args.source_url,
        source_label=args.source_label,
        resolver_pattern=args.resolver_pattern,
        llm_name=args.llm_name,
        revised_by_name=args.revised_by_name,
        revised_by_url=args.revised_by_url,
        llm_url=args.llm_url,
        agent_env=args.agent_env,
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
