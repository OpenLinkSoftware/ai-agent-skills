/**
 * Validate the RDF infographic strict harness contract — TypeScript edition (Node.js ≥ 18, no npm deps).
 * Identical behavior to validate-harness-contract.py except RDF file parsing
 * (--ttl / --jsonld) requires the n3 package (Phase 2). Passing those flags
 * without n3 installed emits a warning and skips the parse check.
 *
 * Usage:
 *   npx tsx validate-harness-contract.ts page.html [--ttl graph.ttl] [--jsonld graph.jsonld]
 */

import { readFileSync } from "node:fs";

const failures: string[] = [];

function fail(message: string): void {
  failures.push(message);
}

function require(html: string, needle: string, label: string): void {
  if (!html.includes(needle)) fail(label);
}

function requireRegex(html: string, pattern: RegExp, label: string): void {
  if (!pattern.test(html)) fail(label);
}

function requireAny(html: string, needles: string[], label: string): void {
  if (!needles.some(n => html.includes(n))) fail(label);
}

function requireAnyRegex(html: string, patterns: RegExp[], label: string): void {
  if (!patterns.some(p => p.test(html))) fail(label);
}

function forbidRegex(html: string, pattern: RegExp, label: string): void {
  if (pattern.test(html)) fail(label);
}

// Classes emitted by rdf_infographic_harness's attributionFooter(),
// footerSparqlWorkbench() and kgExplorerShell(). Each one appearing in the
// page must also have a CSS rule somewhere in the page.
//
// WHY. Until 2026-08-20 not one template in this skill defined any of these,
// so every page assembled from the harness helpers rendered its footer as
// full-bleed unstyled text and its SPARQL workbench as bare form controls with
// the percent-encoded query URL bleeding across the page. Nothing caught it:
// valid HTML, no console error, correct content, and a full PASS from this
// validator — the page was simply, silently, unstyled. harnessStyles() now
// ships the CSS with the markup; this gate notices when a page skips it.
const HARNESS_STYLED_CLASSES = [
  "attribution-panel", "attribution-inner", "attribution-grid",
  "attribution-card", "attribution-label", "attribution-links",
  "attribution-pill", "entity-link",
  "sparql-launch", "sparql-head", "sparql-grid", "sparql-field",
  "sparql-editor", "sparql-actions", "sparql-link-preview", "sparql-note",
  "run-query",
];

function checkHarnessClassStyling(html: string): void {
  const styleBlocks = [...html.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)]
    .map((m) => m[1]).join("\n");
  // Body = everything outside <style>, so a class named only inside a CSS
  // comment or selector is not mistaken for markup usage.
  const body = html.replace(/<style[^>]*>[\s\S]*?<\/style>/g, "");
  const used = new Set<string>();
  for (const m of body.matchAll(/class="([^"]+)"/g)) {
    for (const c of m[1].split(/\s+/)) if (c) used.add(c);
  }
  const defined = new Set(
    [...styleBlocks.matchAll(/\.([A-Za-z][\w-]+)/g)].map((m) => m[1]),
  );
  const unstyled = HARNESS_STYLED_CLASSES
    .filter((c) => used.has(c) && !defined.has(c)).sort();
  if (unstyled.length) {
    fail(
      `Harness-emitted classes present in the markup with no CSS rule anywhere in ` +
      `the page: ${unstyled.join(", ")}. The page renders unstyled in those regions ` +
      `(typically the attribution footer and/or the SPARQL workbench). Append ` +
      `harnessStyles() to the page stylesheet, or define equivalent rules in the ` +
      `selected template.`,
    );
  }
}

function parseArgs(argv: string[]): { html: string; ttl?: string; jsonld?: string } {
  let html = "";
  let ttl: string | undefined;
  let jsonld: string | undefined;
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--ttl") { ttl = argv[++i]; }
    else if (argv[i] === "--jsonld") { jsonld = argv[++i]; }
    else if (!html) { html = argv[i]; }
  }
  return { html, ttl, jsonld };
}

async function validateRdf(path: string | undefined, fmt: string): Promise<void> {
  if (!path) return;
  try {
    // Phase 2 will add n3-based RDF parsing here.
    // For now, check the file is readable and non-empty as a basic sanity check.
    const { existsSync } = await import("node:fs");
    if (!existsSync(path)) {
      fail(`RDF file not found: ${path}`);
      return;
    }
    const content = readFileSync(path, "utf-8").trim();
    if (!content) fail(`RDF file is empty: ${path}`);
  } catch (err) {
    fail(`RDF file check failed for ${path}: ${(err as Error).message}`);
  }
}

async function main(): Promise<number> {
  const argv = process.argv.slice(2);
  if (!argv.length) {
    process.stderr.write(
      "Usage: npx tsx validate-harness-contract.ts page.html [--ttl graph.ttl] [--jsonld graph.jsonld]\n",
    );
    return 1;
  }

  const args = parseArgs(argv);
  if (!args.html) {
    process.stderr.write("Error: HTML file argument required\n");
    return 1;
  }

  const html = readFileSync(args.html, "utf-8");

  // ── POSH links ──────────────────────────────────────────────────────────────
  require(html, 'rel="related"', 'POSH related link missing');
  require(html, 'rel="alternate"', 'POSH alternate link missing');
  require(html, 'application/ld+json', 'Embedded JSON-LD missing');

  // ── Navigation ──────────────────────────────────────────────────────────────
  requireAny(html, ['class="section-nav"', 'id="nav-panel"', 'aria-label="Section navigation"'], "Navigation panel missing");
  requireAnyRegex(html, [/class="nav-toggle"[^>]*(aria-label="Expand navigation"|title="Expand)/, /id="nav-toggle"/, /toggleNav\(/], "Navigation collapsed expand toggle missing");
  requireAny(html, ['theme-toggle', 'id="theme-btn"', 'themeCycle', 'toggleTheme'], "Page theme toggle missing");

  // ── KG Explorer ─────────────────────────────────────────────────────────────
  requireAny(html, ['id="kg-explorer"', 'id="kg"', 'Knowledge Graph Explorer'], "KG Explorer missing");
  requireAny(html, ['id="kgControlsToggle"', 'id="nav-toggle"', 'btn-basic', 'btn-advanced'], "KG controls/mode controls missing");
  requireAnyRegex(html, [/id="kgToolbar" hidden/, /#nav-body\{[^}]*max-height:0/, /id="settings-panel"\s+style="display:none/, /#settings-panel\{display:none/], "KG controls/settings are not clearly closed by default");
  requireAny(html, ['id="settingsPanel" hidden', 'id="settings-panel"', 'settingsPanel.hidden=true'], "Advanced settings panel missing");
  requireAny(html, ['data-mode="Basic"', 'btn-basic', "switchMode('basic')"], "Basic mode toggle missing");
  requireAny(html, ['data-mode="Advanced"', 'btn-advanced', "switchMode('advanced')"], "Advanced mode toggle missing");
  requireAny(html, ['data-density="Core"', 'density-core', "setDensity('core')"], "Core density toggle missing");
  requireAny(html, ['data-density="Full"', 'density-full', "setDensity('full')"], "Full density toggle missing");
  requireAny(html, ['data-advanced-control hidden', 'settings-btn', 'display:none'], "Advanced-only controls not hidden by default");
  requireAny(html, ['id="predicateSelectAll"', 'selectAll', 'Select All', 'All</button>'], "Predicate Select All missing");
  requireAny(html, ['id="predicateDeselectAll"', 'deselectAll', 'Deselect', 'None</button>'], "Predicate Deselect All missing");
  requireAny(html, ['id="literalToggle"', 'literal', 'Literals'], "Literal filter missing");
  requireAny(html, ['id="resolverPreference"', 'resolver', 'RESOLVER'], "Resolver preference/pattern missing");
  requireAny(html, ['id="arrowStyle"', 'arrow', 'marker-end'], "Arrow style/directed arrows missing");
  forbidRegex(html, /(value=["']dual["']|arrowStyle\s*=\s*['"]dual['"]|>\s*Dual\b)/s, "Dual-arrow option/default found — KG Explorer edges must be single, directed (subject-to-object) arrowheads only; use 'directed'/'none', never 'dual'");
  forbidRegex(html, /marker-start\s*[:=]\s*['"]?url\(#/s, "marker-start found on a KG Explorer edge — edges must carry marker-end only (single directed arrowhead), never a start-side arrowhead implying bidirectionality");
  requireAnyRegex(html, [/<script src="https:\/\/d3js\.org\/d3\.v7[^"]*"/, /<script src="https:\/\/cdn\.jsdelivr\.net\/npm\/d3@7\/[^"]*"/], "D3 runtime script tag missing or using a non-resolving URL (e.g. https://d3js.org/d3@7, which 404s — use d3.v7.min.js or the jsdelivr path)");
  requireAny(html, ['clickDistance(6)', 'd3.drag()', '.drag()'], "D3 drag behavior missing");
  requireAny(html, ['d3.zoom(', 'd3.zoom ('], "D3 zoom (whole-graph pan/zoom) missing — SKILL.md Validation Checklist requires 'KG Explorer D3 zoom is focus-activated'");
  requireAny(html, ['kg-active', 'kgActive'], "KG zoom-isolation visual indicator (kg-active class) missing");
  requireAnyRegex(html, [/on\(['"]\.zoom['"],\s*null\)/], "Zoom isolation release handler missing — outside click must call svg.on('.zoom', null) to detach, per SKILL.md's zoom-isolation requirement (never attach zoom on init)");
  requireAnyRegex(html, [/\.append\(['"]a['"]\)[\s\S]{0,200}(href|xlink:href)/, /<a[^>]+href="https:\/\/linkeddata\.uriburner\.com\/describe\/\?url=/], "Resolver-backed SVG/label anchors missing");
  requireAny(html, ["xlink:href", ".attr('href'", '.attr("href"', 'href="https://linkeddata.uriburner.com/describe/?url='], "Resolver href missing");
  requireAny(html, ['data-resolver-href', 'describe/?url=', 'RESOLVER'], "KG resolver href audit/pattern missing");

  // ── SPARQL explorer ─────────────────────────────────────────────────────────
  requireAny(html, ['id="sparql-explorer"', 'sparql-explore-box', 'Explore Knowledge Graph'], "Footer SPARQL explorer missing");
  requireAny(html, ['id="sparqlGraph"', 'SPARQL_GRAPH', 'Named graph'], "Footer named graph selector/IRI missing");
  // A single visible canonical query block (sparql-block/sparql-code, per footer-sparql-explorer-gate.ttl
  // Gate 2/4) is an explicitly sanctioned replacement for the interactive recipe selector — not a gap.
  requireAny(html, ['id="sparqlRecipe"', 'exploreQueries', 'liveQueries', 'Query recipe', 'sparql-accordion', 'sparql-block', 'sparql-code'], "Footer query recipe selector/quick links missing");
  requireAny(html, ['id="sparqlText"', '<textarea', 'liveQueries', 'exploreQueries', 'sparql-code'], "Footer editable SPARQL textarea or query recipes missing");
  requireAny(html, ['id="sparqlFormat"', 'text/x-html+tr', 'text%2Fx-html%2Btr'], "Footer SPARQL format display/guidance missing");
  require(html, 'text/x-html+tr', "SELECT result format guidance missing");
  require(html, 'text/x-html-nice-turtle', "DESCRIBE/CONSTRUCT result format guidance missing");
  require(html, 'encodeURIComponent', "SPARQL live link encoding missing");

  // Footer SPARQL Button with Format Toggle contract (SKILL.md): a dedicated
  // id="sparqlBtn" CTA, scoped to the DAV-uploaded graph IRI (never the source
  // document IRI), using the canonical SAMPLE-based entity-summary query.
  require(html, 'id="sparqlBtn"', 'Footer SPARQL \'Explore Knowledge Graph using SPARQL\' CTA (id="sparqlBtn") missing');
  require(html, 'DAV/demos/daas/', "SPARQL queries not scoped to the DAV-uploaded graph IRI (https://linkeddata.uriburner.com/DAV/demos/daas/{filename}) — see 'Document IRI vs SPARQL GRAPH IRI' rule");
  requireAny(html, ['sampleEntity', 'SAMPLE(?s)', 'SAMPLE%28%3Fs%29'], "Canonical entity-type-summary query (SAMPLE(?s) AS ?sampleEntity ...) missing from SPARQL button/recipes");
  requireAny(html, ['entityCount', 'entityCount)', '%3FentityCount'], "Canonical entity-type-summary query's ?entityCount projection missing");

  // ── Attribution items ───────────────────────────────────────────────────────
  for (const label of [
    "Source material",
    "Companion files",
    "Skills used",
    "Generation environment",
    "Linked Data runtime",
    "Named graphs",
    "Resolver pattern",
    "Extraction provenance",
  ]) {
    require(html, label, `Attribution item missing: ${label}`);
  }
  checkHarnessClassStyling(html);

  require(html, "https://linkeddata.uriburner.com/describe/?url=", "URIBurner resolver pattern missing");
  require(html, "https://linkeddata.uriburner.com/sparql", "URIBurner SPARQL endpoint missing");
  require(html, "https://virtuoso.openlinksw.com/", "OpenLink Virtuoso attribution missing");

  // Responsive head-to-head comparison dual presentation (SKILL.md harness item 15).
  // Conditional: only when a multi-column comparison matrix is present.
  const hasResponsiveFlag =
    html.includes('data-comparison-layout="responsive"') ||
    html.includes("data-comparison-layout='responsive'");
  const theadBlocks = [
    ...html.matchAll(
      /<table[^>]*class="[^"]*comparison-table[^"]*"[^>]*>[\s\S]*?<thead>([\s\S]*?)<\/thead>/gi,
    ),
  ];
  let multiCol = theadBlocks.some((m) => (m[1].match(/<th\b/gi) || []).length >= 3);
  if (!multiCol && /class="[^"]*comparison-table[^"]*"/.test(html)) {
    const tbl = html.match(
      /<table[^>]*class="[^"]*comparison-table[^"]*"[^>]*>([\s\S]*?)<\/table>/i,
    );
    if (tbl && (tbl[1].match(/<th\b/gi) || []).length >= 3) multiCol = true;
  }
  if (multiCol || hasResponsiveFlag) {
    requireAny(
      html,
      ['comparison-table-view', 'data-comparison-layout="responsive"'],
      "Multi-column comparison matrix missing .comparison-table-view wrapper (responsive dual presentation)",
    );
    requireAny(
      html,
      ['comparison-cards-view', 'class="comp-card"', "class='comp-card'"],
      "Multi-column comparison matrix missing phone cards (.comparison-cards-view / .comp-card) — table-only horizontal scroll is not sufficient",
    );
    requireAny(
      html,
      ['max-width: 900px', 'max-width:900px', '@media(max-width:900px)', '@media (max-width: 900px)'],
      "Responsive comparison breakpoint (max-width: 900px) missing — cards must show on phones",
    );
    // First-column aspect labels must be resolver-linked to TTL dimension entities
    const aspectLinked =
      /<(?:td)[^>]*class="[^"]*(?:td-aspect|td-dim)[^"]*"[^>]*>\s*<a[^>]+href="[^"]*describe\/\?url=/i.test(
        html,
      ) ||
      /class="comp-row-label"\s*>\s*<a[^>]+href="[^"]*describe\/\?url=/i.test(html);
    if (!aspectLinked) {
      fail(
        "Comparison aspect/dimension labels are not resolver-linked — first column of each table row " +
          "(and card .comp-row-label) MUST link via describe/?url= to ComparisonDimension/DefinedTerm IRIs from the companion TTL",
      );
    }
  }

  // ── KG-curation attribution (agent-rdf-memory/howto/kg-curation-attribution.ttl) ──
  // Documented as a recurring miss (5 occurrences); this is a blocking gate now,
  // not just memory/grep discipline.
  require(html, "KG curated by", "Hero-meta 'KG curated by ... on behalf of' attribution line missing");
  require(html, "on behalf of", "Hero-meta delegation phrase ('on behalf of') missing");
  requireAny(html, ['"accountablePerson"', "'accountablePerson'"], "JSON-LD accountablePerson missing");
  requireAny(html, ['"prov:actedOnBehalfOf"', "'prov:actedOnBehalfOf'"], "JSON-LD prov:actedOnBehalfOf missing");
  if (html.includes("prov:actedOnBehalfOf")) {
    const badTargetRe = /"prov:actedOnBehalfOf"\s*:\s*\{\s*"@id"\s*:\s*"([^"]*(?:anthropic\.com|openai\.com|github\.com)[^"]*)"/g;
    const badTargets: string[] = [];
    let bm: RegExpExecArray | null;
    while ((bm = badTargetRe.exec(html)) !== null) badTargets.push(bm[1]);
    if (badTargets.length) {
      fail(`prov:actedOnBehalfOf points at a tool/LLM IRI instead of the human principal: ${badTargets.join(", ")}`);
    }
  }

  // ── Link target discipline ──────────────────────────────────────────────────
  const anchorRe = /<a\s+[^>]*href="([^"]+)"[^>]*>/g;
  const badExternal: string[] = [];
  const badFragment: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = anchorRe.exec(html)) !== null) {
    const tag = m[0];
    const href = m[1];
    if (!href.startsWith("#") && !tag.includes('target="_blank"')) badExternal.push(tag);
    if (href.startsWith("#") && tag.includes('target="_blank"')) badFragment.push(tag);
  }
  if (badExternal.length) fail(`${badExternal.length} non-fragment links missing target="_blank"`);
  if (badFragment.length) fail(`${badFragment.length} fragment links incorrectly open in new tab`);

  // ── kgData payload ──────────────────────────────────────────────────────────
  const kgPayloadRe = /const (?:kgData|_kgDataFull|kgFull)\s*=\s*(\{[\s\S]*?\});/;
  const kgMatch = kgPayloadRe.exec(html);
  if (kgMatch) {
    try {
      const data = JSON.parse(kgMatch[1]) as { nodes?: { id: string }[]; links?: { source: string; target: string }[] };
      const nodes = data.nodes ?? [];
      const links = data.links ?? [];
      const ids = new Set(nodes.map(n => n.id));
      if (nodes.length === 0) fail("Embedded kgData payload is empty (0 nodes) — likely a bypass stub");
      if (links.length === 0) fail("Embedded kgData payload has 0 links — likely a bypass stub");
      const orphans = links.filter(l => !ids.has(l.source) || !ids.has(l.target));
      if (orphans.length) fail(`KG payload has ${orphans.length} orphan links`);
    } catch {
      fail("Embedded kgData payload is not valid JSON");
    }
  } else {
    fail("Embedded kgData payload missing (no kgData, _kgDataFull, or kgFull variable found)");
  }

  // ── KG interactivity contract ───────────────────────────────────────────────
  if (!/\.append\(["']a["']\)[\s\S]{0,400}data-resolver-href/.test(html))
    fail("Edge labels not resolver-backed SVG anchors — predAnchor must use .append('a') with data-resolver-href attribute");
  if (!/pred-anchor\s+a|predAnchor[\s\S]{0,200}\.append\(["']a["']\)/.test(html))
    fail("Edge label SVG anchors missing — .pred-anchor a pattern not found in CSS or JS");
  if (!html.includes('id="sparqlBtn"'))
    fail('SPARQL explore button id="sparqlBtn" missing');
  // Accepted: (a) a plain .on('click', ...) resolver call, or (b) the click-distance-guard
  // pattern (kg-explorer-d3-patterns.ttl step-clickGuard) measured in drag.on('end') --
  // this is the CORRECT pattern and must not be rejected for lacking a separate click handler.
  const hasPlainClick = /\.on\(["']click["'][\s\S]{0,200}resolv/i.test(html);
  const hasClickGuard = /on\(["']end["'][\s\S]{0,500}(?:dist|distance)[\s\S]{0,150}<\s*6[\s\S]{0,300}resolv/i.test(html);
  if (!hasPlainClick && !hasClickGuard)
    fail("Node click handler missing resolver call — nodes must open resolver on click (via .on('click', ...) or the click-distance-guard pattern in drag.on('end'))");

  // ── RDF file checks (Phase 2 will add full parse) ──────────────────────────
  await validateRdf(args.ttl, "turtle");
  await validateRdf(args.jsonld, "json-ld");

  if (failures.length) {
    console.log("FAIL");
    for (const item of failures) console.log(`- ${item}`);
    return 1;
  }
  console.log("PASS: RDF infographic harness contract checks passed");
  return 0;
}

main().then(code => process.exit(code)).catch(err => {
  process.stderr.write(`Error: ${(err as Error).message}\n`);
  process.exit(1);
});
