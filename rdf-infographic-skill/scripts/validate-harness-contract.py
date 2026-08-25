#!/usr/bin/env python3
"""
Validate the RDF infographic strict harness contract.

Usage:
  python3 validate-harness-contract.py page.html --ttl graph.ttl --jsonld graph.jsonld
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


# Prohibited path fragments — any of these appearing in the resolved path is an
# instant fail, regardless of what LLM_ROOT resolves to. These are the exact
# fallback locations named as prohibited in agent-rdf-memory/howto/artifact-routing.ttl
# (step-outputDirs, step-defaultOutputRoot, step-outputRootBlockingGate) — kg-output/
# has caused three documented misrouting recurrences (2026-08-06, 2026-08-08 x2)
# precisely because a fully-passing validator run gave false confidence that a file
# sitting there was correctly placed. This check exists so that can never happen again.
_PROHIBITED_PATH_FRAGMENTS = ("kg-output", "/tmp/", "/private/tmp/")


def _find_git_root(path: Path) -> Path | None:
    for parent in [path] + list(path.parents):
        if (parent / ".git").exists():
            return parent
    return None


# Classes emitted by rdf_infographic_harness's attribution_footer(),
# footer_sparql_workbench() and kg_explorer_shell(). Each one that appears in
# the page must also have a CSS rule somewhere in the page.
#
# WHY. Until 2026-08-20 not one template in this skill defined any of these,
# so every page hand-assembled from the harness helpers rendered its footer as
# full-bleed unstyled text and its SPARQL workbench as bare form controls with
# the percent-encoded query URL bleeding across the page. Nothing caught it:
# valid HTML, no console error, correct content, and a full PASS from this
# validator — the page was simply, silently, unstyled. The generalisable
# failure is markup from one generation meeting a stylesheet from another
# (the same drift produced a KG Explorer whose element ids the JS could not
# find). rdf_infographic_harness.harness_styles() now ships the CSS with the
# markup; this gate is what notices when a page skips it.
_HARNESS_STYLED_CLASSES = (
    "attribution-panel", "attribution-inner", "attribution-grid",
    "attribution-card", "attribution-label", "attribution-links",
    "attribution-pill", "entity-link",
    "sparql-launch", "sparql-head", "sparql-grid", "sparql-field",
    "sparql-editor", "sparql-actions", "sparql-link-preview", "sparql-note",
    "run-query",
)


def check_harness_class_styling(html: str, failures: list[str]) -> None:
    """Fail when harness-emitted markup lands on the page with no CSS rule."""
    style_blocks = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S))
    # Body = everything outside <style>, so a class name mentioned only inside
    # a CSS comment or selector is not mistaken for markup usage.
    body = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.S)
    used: set[str] = set()
    for attr in re.findall(r'class="([^"]+)"', body):
        used.update(attr.split())
    defined = set(re.findall(r"\.([A-Za-z][\w-]+)", style_blocks))
    unstyled = sorted(c for c in _HARNESS_STYLED_CLASSES if c in used and c not in defined)
    if unstyled:
        fail(
            "Harness-emitted classes present in the markup with no CSS rule anywhere in "
            f"the page: {', '.join(unstyled)}. The page renders unstyled in those regions "
            "(typically the attribution footer and/or the SPARQL workbench). Append "
            "rdf_infographic_harness.harness_styles() to the page stylesheet, or define "
            "equivalent rules in the selected template.",
            failures,
        )


def check_output_location(
    path: Path | None,
    expected_subdir: str,
    llm_root: Path,
    failures: list[str],
) -> None:
    """Fail if `path` is not under {llm_root}/<Model Dir>/<expected_subdir>/.

    This is a location gate, separate from and in addition to the artifact's
    internal contract checks below. A PASS from this script has repeatedly been
    misread as confirmation that the file was saved to the right place — it was
    never checking that. This function closes that gap.
    """
    if path is None:
        return
    resolved = path.resolve()
    resolved_str = str(resolved)

    for frag in _PROHIBITED_PATH_FRAGMENTS:
        if frag.strip("/") in resolved.parts or frag in resolved_str:
            fail(
                f"Output location violation: '{path}' resolves under a prohibited "
                f"fallback location ('{frag}'). See agent-rdf-memory/howto/"
                f"artifact-routing.ttl step-outputDirs — never kg-output/, a repo "
                f"working directory, or /tmp. Move the file under {llm_root}/"
                f"<Model Directory>/{expected_subdir}/ before delivery.",
                failures,
            )
            return

    git_root = _find_git_root(resolved)
    if git_root is not None:
        fail(
            f"Output location violation: '{path}' is inside a git repository "
            f"({git_root}) — generated artifacts must never be saved inside a "
            f"working repo. Route to {llm_root}/<Model Directory>/{expected_subdir}/ "
            f"per agent-rdf-memory/howto/artifact-routing.ttl.",
            failures,
        )
        return

    try:
        resolved.relative_to(llm_root.resolve())
    except ValueError:
        fail(
            f"Output location violation: '{path}' is not under the canonical LLM "
            f"root ({llm_root}). Every generated artifact must live at "
            f"{llm_root}/<Model Directory>/{{rdf,webpages,md}}/ per "
            f"agent-rdf-memory/howto/artifact-routing.ttl step-outputDirs.",
            failures,
        )
        return

    if resolved.parent.name != expected_subdir:
        fail(
            f"Output location violation: '{path}' is under the LLM root but its "
            f"parent directory is '{resolved.parent.name}', not the expected "
            f"'{expected_subdir}/' sibling folder.",
            failures,
        )


def require(html: str, needle: str, label: str, failures: list[str]) -> None:
    if needle not in html:
        fail(label, failures)


def require_regex(html: str, pattern: str, label: str, failures: list[str]) -> None:
    if not re.search(pattern, html, re.S):
        fail(label, failures)


def require_any(html: str, needles: list[str], label: str, failures: list[str]) -> None:
    if not any(needle in html for needle in needles):
        fail(label, failures)


def require_any_regex(html: str, patterns: list[str], label: str, failures: list[str]) -> None:
    if not any(re.search(pattern, html, re.S) for pattern in patterns):
        fail(label, failures)


def forbid_regex(html: str, pattern: str, label: str, failures: list[str]) -> None:
    if re.search(pattern, html, re.S):
        fail(label, failures)


def validate_rdf(path: str | None, fmt: str, failures: list[str]) -> None:
    if not path:
        return
    try:
        from rdflib import Graph

        Graph().parse(path, format=fmt)
    except Exception as exc:  # pragma: no cover - diagnostics script
        fail(f"RDF parse failed for {path}: {exc}", failures)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("html")
    parser.add_argument("--ttl")
    parser.add_argument("--jsonld")
    parser.add_argument(
        "--llm-root",
        default=str(Path.home() / "Documents" / "LLMs"),
        help="Canonical LLM_ROOT for the output-location gate (default: ~/Documents/LLMs)",
    )
    parser.add_argument(
        "--skip-location-check",
        action="store_true",
        help="Skip the output-location gate (only for validating a file mid-generation, before it has been moved to its final destination)",
    )
    args = parser.parse_args()

    html_path = Path(args.html)
    html = html_path.read_text(encoding="utf-8")
    failures: list[str] = []

    if not args.skip_location_check:
        llm_root = Path(args.llm_root)
        check_output_location(html_path, "webpages", llm_root, failures)
        if args.ttl:
            check_output_location(Path(args.ttl), "rdf", llm_root, failures)
        if args.jsonld:
            check_output_location(Path(args.jsonld), "rdf", llm_root, failures)

    require(html, 'rel="related"', "POSH related link missing", failures)
    require(html, 'rel="alternate"', "POSH alternate link missing", failures)
    require(html, 'application/ld+json', "Embedded JSON-LD missing", failures)

    require_any(html, ['class="section-nav"', 'id="nav-panel"', 'aria-label="Section navigation"', 'id="fnav"'], "Navigation panel missing", failures)
    require_any_regex(html, [r'class="nav-toggle"[^>]*(aria-label="Expand navigation"|title="Expand)', r'id="nav-toggle"', r'toggleNav\(', r'id="fnav-toggle"'], "Navigation collapsed expand toggle missing", failures)
    require_any(html, ['theme-toggle', 'id="theme-btn"', 'themeCycle', 'toggleTheme', 'id="fnav-theme"'], "Page theme toggle missing", failures)

    require_any(html, ['id="kg-explorer"', 'id="kg"', 'Knowledge Graph Explorer'], "KG Explorer missing", failures)
    # KG Explorer / SPARQL Workbench are always-visible sections, NOT wrapped
    # in a section-level <details> accordion (removed 2026-08-12 per explicit
    # user request — the collapsed-by-default treatment was itself flagged as
    # unwanted, superseding the prior aesthetics-motivated accordion rule).
    # Individual .sparql-card sample-query accordions inside the workbench are
    # unaffected and still closed-by-default.
    forbid_regex(html, re.escape('<details class="section-accordion" id="kg-explorer-accordion">'), "KG Explorer must NOT be wrapped in a section-level accordion (removed by explicit user request)", failures)
    forbid_regex(html, re.escape('<details class="section-accordion" id="sparql-explorer-accordion">'), "SPARQL Workbench must NOT be wrapped in a section-level accordion (removed by explicit user request)", failures)
    require_any(html, ['id="kgControlsToggle"', 'id="nav-toggle"', 'btn-basic', 'btn-advanced'], "KG controls/mode controls missing", failures)
    require_any_regex(html, [r'id="kgToolbar" hidden', r'#nav-body\{[^}]*max-height:0', r'id="settings-panel"\s+style="display:none', r'#settings-panel\{display:none', r'\[data-advanced-control\]\{display:none\}', r'#kg-settings\{[^}]*right:-\d'], "KG controls/settings are not clearly closed by default", failures)
    require_any(html, ['id="settingsPanel" hidden', 'id="settings-panel"', 'settingsPanel.hidden=true', 'id="kg-settings"'], "Advanced settings panel missing", failures)
    require_any(html, ['data-mode="Basic"', 'btn-basic', "switchMode('basic')"], "Basic mode toggle missing", failures)
    require_any(html, ['data-mode="Advanced"', 'btn-advanced', "switchMode('advanced')"], "Advanced mode toggle missing", failures)
    require_any(html, ['data-density="Core"', 'density-core', "setDensity('core')"], "Core density toggle missing", failures)
    require_any(html, ['data-density="Full"', 'density-full', "setDensity('full')"], "Full density toggle missing", failures)
    require_any(html, ['data-advanced-control hidden', 'settings-btn', 'display:none'], "Advanced-only controls not hidden by default", failures)
    require_any(html, ['id="predicateSelectAll"', 'selectAll', 'Select All', 'All</button>'], "Predicate Select All missing", failures)
    require_any(html, ['id="predicateDeselectAll"', 'deselectAll', 'Deselect', 'None</button>'], "Predicate Deselect All missing", failures)
    require_any(html, ['id="literalToggle"', 'literal', 'Literals'], "Literal filter missing", failures)
    require_any(html, ['id="resolverPreference"', 'resolver', 'RESOLVER'], "Resolver preference/pattern missing", failures)
    require_any(html, ['id="arrowStyle"', 'arrow', 'marker-end'], "Arrow style/directed arrows missing", failures)
    forbid_regex(html, r'''(value=["']dual["']|arrowStyle\s*=\s*['"]dual['"]|>\s*Dual\b)''', "Dual-arrow option/default found — KG Explorer edges must be single, directed (subject-to-object) arrowheads only; use 'directed'/'none', never 'dual'", failures)
    forbid_regex(html, r'''marker-start\s*[:=]\s*['"]?url\(#''', "marker-start found on a KG Explorer edge — edges must carry marker-end only (single directed arrowhead), never a start-side arrowhead implying bidirectionality", failures)
    require_any_regex(html, [r'<script src="https://d3js\.org/d3\.v7[^"]*"', r'<script src="https://cdn\.jsdelivr\.net/npm/d3@7/[^"]*"'], "D3 runtime script tag missing or using a non-resolving URL (e.g. https://d3js.org/d3@7, which 404s — use d3.v7.min.js or the jsdelivr path)", failures)
    require_any(html, ['clickDistance(6)', 'd3.drag()', '.drag()'], "D3 drag behavior missing", failures)
    require_any(html, ['d3.zoom(', 'd3.zoom ('], "D3 zoom (whole-graph pan/zoom) missing — SKILL.md Validation Checklist requires 'KG Explorer D3 zoom is focus-activated'", failures)
    require_any(html, ['kg-active', 'kgActive'], "KG zoom-isolation visual indicator (kg-active class) missing", failures)
    require_any_regex(html, [r"""on\(['"]\.zoom['"],\s*null\)"""], "Zoom isolation release handler missing — outside click must call svg.on('.zoom', null) to detach, per SKILL.md's zoom-isolation requirement (never attach zoom on init)", failures)
    require_any_regex(html, [r'\.append\([\'"]a[\'"]\).*?(href|xlink:href)', r'<a[^>]+href="https://linkeddata\.uriburner\.com/describe/\?url='], "Resolver-backed SVG/label anchors missing", failures)
    require_any(html, ['xlink:href', '.attr(\'href\'', '.attr("href"', 'href="https://linkeddata.uriburner.com/describe/?url='], "Resolver href missing", failures)
    require_any(html, ['data-resolver-href', 'describe/?url=', 'RESOLVER'], "KG resolver href audit/pattern missing", failures)

    require_any(html, ['id="sparql-explorer"', 'sparql-explore-box', 'Explore Knowledge Graph'], "Footer SPARQL explorer missing", failures)
    require_any(html, ['id="sparqlGraph"', 'SPARQL_GRAPH', 'Named graph'], "Footer named graph selector/IRI missing", failures)
    # A single visible canonical query block (sparql-block/sparql-code, per footer-sparql-explorer-gate.ttl
    # Gate 2/4) is an explicitly sanctioned replacement for the interactive recipe selector — not a gap.
    require_any(html, ['id="sparqlRecipe"', 'exploreQueries', 'liveQueries', 'Query recipe', 'sparql-accordion', 'sparql-block', 'sparql-code'], "Footer query recipe selector/quick links missing", failures)
    require_any(html, ['id="sparqlText"', '<textarea', 'liveQueries', 'exploreQueries', 'sparql-code'], "Footer editable SPARQL textarea or query recipes missing", failures)
    require_any(html, ['id="sparqlFormat"', 'text/x-html+tr', 'text%2Fx-html%2Btr'], "Footer SPARQL format display/guidance missing", failures)
    require(html, 'text/x-html+tr', "SELECT result format guidance missing", failures)
    require(html, 'text/x-html-nice-turtle', "DESCRIBE/CONSTRUCT result format guidance missing", failures)
    require(html, 'encodeURIComponent', "SPARQL live link encoding missing", failures)

    # Footer SPARQL Button with Format Toggle contract (SKILL.md): a dedicated
    # id="sparqlBtn" CTA, scoped to the DAV-uploaded graph IRI (never the source
    # document IRI), using the canonical SAMPLE-based entity-summary query.
    # Added after a documented gap: generate_infographic.py shipped a SPARQL
    # workbench whose graph selector defaulted to the source document IRI, and
    # this validator gave a false PASS because it never checked for any of
    # these three markers.
    require(html, 'id="sparqlBtn"', "Footer SPARQL 'Explore Knowledge Graph using SPARQL' CTA (id=\"sparqlBtn\") missing", failures)
    require(html, 'DAV/demos/daas/', "SPARQL queries not scoped to the DAV-uploaded graph IRI (https://linkeddata.uriburner.com/DAV/demos/daas/{filename}) — see 'Document IRI vs SPARQL GRAPH IRI' rule", failures)
    require_any(html, ['sampleEntity', 'SAMPLE(?s)', 'SAMPLE%28%3Fs%29'], "Canonical entity-type-summary query (SAMPLE(?s) AS ?sampleEntity ...) missing from SPARQL button/recipes", failures)
    require_any(html, ['entityCount', 'entityCount)', '%3FentityCount'], "Canonical entity-type-summary query's ?entityCount projection missing", failures)

    # SPARQL-bearing sections must be closed-by-default accordions, not a
    # wall of always-open verbatim query blocks (SKILL.md "SPARQL Query
    # Presentation": <details>/<summary>). Only checked when the companion
    # TTL actually declares schema:SoftwareSourceCode SPARQL examples, since
    # that is what the accordion wraps.
    if args.ttl:
        ttl_text = Path(args.ttl).read_text(encoding="utf-8")
        if "SoftwareSourceCode" in ttl_text and "SPARQL" in ttl_text:
            require(html, '<details class="sparql-card"', "SPARQL query examples must render as closed-by-default <details class=\"sparql-card\"> accordions, not always-open <div> blocks", failures)
            forbid_regex(html, r'<details class="sparql-card"[^>]*\bopen\b', "Sample-query <details> accordion must NOT carry an `open` attribute (closed by default)", failures)

    # Synopsis lede/body gate: a synopsis section with a spotlight panel and
    # CTA but no narrative prose reads as broken/sparse (a big mostly-empty
    # card). This happens when the main entity has no schema:abstract,
    # schema:articleBody, or schema:description for rdf_parser._extract_deck
    # to source the lede from. Caught 2026-08-15 on the RDF 1.2/Virtuoso
    # collection: schema:description was set but schema:abstract was not, and
    # rdf_parser.py at the time only looked at abstract/articleBody.
    if 'id="synopsis"' in html:
        require_any(html, ['class="lede"', 'class="syn-body"><p'], "Synopsis section has no lede/body prose — schema:abstract (or schema:articleBody/schema:description) is missing or empty on the main article entity, producing a sparse synopsis deck (spotlight panel + CTA only, no narrative text)", failures)

    for label in [
        "Source material",
        "Companion files",
        "Skills used",
        "Generation environment",
        "Linked Data runtime",
        "Named graphs",
        "Resolver pattern",
        "Extraction provenance",
    ]:
        require(html, label, f"Attribution item missing: {label}", failures)

    check_harness_class_styling(html, failures)

    require(html, "https://linkeddata.uriburner.com/describe/?url=", "URIBurner resolver pattern missing", failures)
    require(html, "https://linkeddata.uriburner.com/sparql", "URIBurner SPARQL endpoint missing", failures)
    require(html, "https://virtuoso.openlinksw.com/", "OpenLink Virtuoso attribution missing", failures)

    # Responsive head-to-head comparison dual presentation (SKILL.md harness item 15).
    # Conditional: only when a multi-column comparison matrix is present.
    # Soft markers: comparison-table with ≥3 header cells (aspect + ≥2 entities),
    # or explicit data-comparison-layout="responsive".
    has_responsive_flag = 'data-comparison-layout="responsive"' in html or "data-comparison-layout='responsive'" in html
    table_headers = re.findall(
        r'<table[^>]*class="[^"]*comparison-table[^"]*"[^>]*>.*?<thead>(.*?)</thead>',
        html,
        re.S | re.I,
    )
    multi_col = False
    for thead in table_headers:
        th_count = len(re.findall(r'<th\b', thead, re.I))
        if th_count >= 3:
            multi_col = True
            break
    if not multi_col and re.search(r'class="[^"]*comparison-table[^"]*"', html):
        # Fallback: count th in first comparison-table if thead missing
        m = re.search(r'<table[^>]*class="[^"]*comparison-table[^"]*"[^>]*>(.*?)</table>', html, re.S | re.I)
        if m and len(re.findall(r'<th\b', m.group(1), re.I)) >= 3:
            multi_col = True
    if multi_col or has_responsive_flag:
        require_any(
            html,
            ['comparison-table-view', 'data-comparison-layout="responsive"'],
            "Multi-column comparison matrix missing .comparison-table-view wrapper (responsive dual presentation)",
            failures,
        )
        require_any(
            html,
            ['comparison-cards-view', 'class="comp-card"', "class='comp-card'"],
            "Multi-column comparison matrix missing phone cards (.comparison-cards-view / .comp-card) — table-only horizontal scroll is not sufficient",
            failures,
        )
        require_any(
            html,
            ['max-width: 900px', 'max-width:900px', '@media(max-width:900px)', '@media (max-width: 900px)'],
            "Responsive comparison breakpoint (max-width: 900px) missing — cards must show on phones",
            failures,
        )
        # First-column aspect labels must be resolver-linked to TTL dimension entities
        # (td-aspect / td-dim anchors with describe/?url=).
        aspect_linked = re.search(
            r'<(?:td)[^>]*class="[^"]*(?:td-aspect|td-dim)[^"]*"[^>]*>\s*<a[^>]+href="[^"]*describe/\?url=',
            html,
            re.I,
        ) or re.search(
            r'class="comp-row-label"\s*>\s*<a[^>]+href="[^"]*describe/\?url=',
            html,
            re.I,
        )
        if not aspect_linked:
            fail(
                "Comparison aspect/dimension labels are not resolver-linked — first column of each table row "
                "(and card .comp-row-label) MUST link via describe/?url= to ComparisonDimension/DefinedTerm IRIs from the companion TTL",
                failures,
            )

    # KG-curation attribution (agent-rdf-memory/howto/kg-curation-attribution.ttl) —
    # documented as a recurring miss (5 occurrences); this is now a blocking gate,
    # not just a memory/grep discipline item.
    require(html, "KG curated by", "Hero-meta 'KG curated by ... on behalf of' attribution line missing", failures)
    require(html, "on behalf of", "Hero-meta delegation phrase ('on behalf of') missing", failures)
    require_any(html, ['"accountablePerson"', "'accountablePerson'"], "JSON-LD accountablePerson missing", failures)
    require_any(html, ['"prov:actedOnBehalfOf"', "'prov:actedOnBehalfOf'"], "JSON-LD prov:actedOnBehalfOf missing", failures)
    if 'prov:actedOnBehalfOf' in html:
        bad_targets = re.findall(r'"prov:actedOnBehalfOf"\s*:\s*\{\s*"@id"\s*:\s*"([^"]*(?:anthropic\.com|openai\.com|github\.com)[^"]*)"', html)
        if bad_targets:
            fail(f"prov:actedOnBehalfOf points at a tool/LLM IRI instead of the human principal: {bad_targets}", failures)

    anchors = [
        (m.group(0), m.group(1))
        for m in re.finditer(r'<a\s+[^>]*href="([^"]+)"[^>]*>', html)
    ]
    bad_external = [
        tag for tag, href in anchors if not href.startswith("#") and 'target="_blank"' not in tag
    ]
    bad_fragment = [
        tag for tag, href in anchors if href.startswith("#") and 'target="_blank"' in tag
    ]
    if bad_external:
        fail(f"{len(bad_external)} non-fragment links missing target=\"_blank\"", failures)
    if bad_fragment:
        fail(f"{len(bad_fragment)} fragment links incorrectly open in new tab", failures)

    # Match any of the common kgData variable patterns: kgData, _kgDataFull, kgFull
    kg_payload = re.search(
        r"const (?:kgData|_kgDataFull|kgFull)\s*=\s*(\{.*?\});",
        html, re.S
    )
    if kg_payload:
        import json

        try:
            data = json.loads(kg_payload.group(1))
        except json.JSONDecodeError:
            fail("Embedded kgData payload is not valid JSON", failures)
            data = {"nodes": [], "links": []}

        nodes = data.get("nodes", [])
        links = data.get("links", [])
        ids = {node["id"] for node in nodes}

        if len(nodes) == 0:
            fail("Embedded kgData payload is empty (0 nodes) — likely a bypass stub", failures)
        if len(links) == 0:
            fail("Embedded kgData payload has 0 links — likely a bypass stub", failures)

        orphans = [
            link for link in links
            if link.get("source") not in ids or link.get("target") not in ids
        ]
        if orphans:
            fail(f"KG payload has {len(orphans)} orphan links", failures)
    else:
        fail("Embedded kgData payload missing (no kgData, _kgDataFull, or kgFull variable found)", failures)

    # KG interactivity contract — implementation-agnostic outcome checks
    # Edge labels must be resolver-backed SVG <a> anchors with data-resolver-href
    if not re.search(r'\.append\(["\']a["\']\)[\s\S]{0,400}data-resolver-href', html):
        fail("Edge labels not resolver-backed SVG anchors — predAnchor must use .append('a') with data-resolver-href attribute", failures)
    # .pred-anchor g must contain an <a> element (CSS or JS pattern)
    if not re.search(r'pred-anchor\s+a|predAnchor[\s\S]{0,200}\.append\(["\']a["\']\)', html):
        fail("Edge label SVG anchors missing — .pred-anchor a pattern not found in CSS or JS", failures)
    # SPARQL explore button must be present
    if 'id="sparqlBtn"' not in html and 'sparql-run-btn' not in html:
        fail('SPARQL explore button id="sparqlBtn" or sparql-run-btn missing', failures)
    # Node click handlers must invoke any resolver function (resolver-agnostic).
    # Accepted patterns:
    #   (a) a plain .on('click', ...) handler that calls a resolver function
    #   (b) the click-distance-guard pattern (kg-explorer-d3-patterns.ttl step-clickGuard):
    #       distance is measured in drag.on('end') and a resolver call fires when the
    #       movement is below the click threshold -- this is the CORRECT pattern and must
    #       not be rejected just because there is no separate .on('click', ...) handler;
    #       a separate click handler racing against d3.drag() is the bug this pattern fixes.
    has_plain_click = re.search(r'\.on\(["\']click["\'][\s\S]{0,200}[Rr]esolv', html, re.S)
    has_click_guard = re.search(
        r'''on\(["']end["'][\s\S]{0,500}(?:dist|distance)[\s\S]{0,150}<\s*6[\s\S]{0,300}[Rr]esolv''',
        html, re.S
    )
    if not has_plain_click and not has_click_guard:
        fail("Node click handler missing resolver call — nodes must open resolver on click (via .on('click', ...) or the click-distance-guard pattern in drag.on('end'))", failures)

    # Section-order gates. Character-position comparison of the first id="..."
    # occurrence for each section id is the actual document order — codified
    # here (2026-08-18) after the same misordering recurred across multiple
    # collections despite being hand-fixed and recorded in session memory each
    # time: memory recorded the rule, but nothing enforced it at generation
    # time, so every fresh generate_infographic.py run regressed it again.
    def _pos(section_id: str) -> int | None:
        m = re.search(rf'id="{re.escape(section_id)}"', html)
        return m.start() if m else None

    pos_kg = _pos("kg-explorer")
    pos_sparql = _pos("sparql-workbench") or _pos("sparql-explorer")
    pos_howto = _pos("howto")
    pos_faq = _pos("faq")
    pos_glossary = _pos("glossary")

    if pos_howto is not None and pos_faq is not None and pos_howto > pos_faq:
        fail("Section order violation: HowTo must come before FAQ (standing order: HowTo, FAQ, Glossary, KG Explorer, SPARQL Workbench)", failures)
    if pos_faq is not None and pos_glossary is not None and pos_faq > pos_glossary:
        fail("Section order violation: FAQ must come before Glossary (standing order: HowTo, FAQ, Glossary, KG Explorer, SPARQL Workbench)", failures)
    if pos_howto is not None and pos_glossary is not None and pos_howto > pos_glossary:
        fail("Section order violation: HowTo must come before Glossary (standing order: HowTo, FAQ, Glossary, KG Explorer, SPARQL Workbench)", failures)
    if pos_glossary is not None and pos_kg is not None and pos_glossary > pos_kg:
        fail("Section order violation: KG Explorer must follow Glossary (standing order: HowTo, FAQ, Glossary, KG Explorer, SPARQL Workbench)", failures)
    if pos_glossary is not None and pos_sparql is not None and pos_glossary > pos_sparql:
        fail("Section order violation: SPARQL Workbench must follow Glossary (standing order: HowTo, FAQ, Glossary, KG Explorer, SPARQL Workbench)", failures)
    if pos_kg is not None and pos_sparql is not None and pos_kg > pos_sparql:
        fail("Section order violation: SPARQL Workbench must follow KG Explorer (standing order: HowTo, FAQ, Glossary, KG Explorer, SPARQL Workbench)", failures)

    # People and Organizations sections were removed by explicit user request
    # (2026-08-18) — a standalone name+description card grid duplicating what
    # resolver-linked mentions already surface inline. Catch a regenerated/
    # copied template that reintroduces either.
    if 'id="people"' in html:
        fail("People section present — removed by standing preference; do not render a dedicated People section", failures)
    if 'id="organizations"' in html:
        fail("Organizations section present — removed by standing preference; do not render a dedicated Organizations section", failures)

    validate_rdf(args.ttl, "turtle", failures)
    validate_rdf(args.jsonld, "json-ld", failures)

    if failures:
        print("FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("PASS: RDF infographic harness contract checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
