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
  require(html, 'd3@7', "D3 runtime missing");
  requireAny(html, ['clickDistance(6)', 'd3.drag()', '.drag()'], "D3 drag behavior missing");
  requireAnyRegex(html, [/\.append\(['"]a['"]\)[\s\S]{0,200}(href|xlink:href)/, /<a[^>]+href="https:\/\/linkeddata\.uriburner\.com\/describe\/\?url=/], "Resolver-backed SVG/label anchors missing");
  requireAny(html, ["xlink:href", ".attr('href'", '.attr("href"', 'href="https://linkeddata.uriburner.com/describe/?url='], "Resolver href missing");
  requireAny(html, ['data-resolver-href', 'describe/?url=', 'RESOLVER'], "KG resolver href audit/pattern missing");

  // ── SPARQL explorer ─────────────────────────────────────────────────────────
  requireAny(html, ['id="sparql-explorer"', 'sparql-explore-box', 'Explore Knowledge Graph'], "Footer SPARQL explorer missing");
  requireAny(html, ['id="sparqlGraph"', 'SPARQL_GRAPH', 'Named graph'], "Footer named graph selector/IRI missing");
  requireAny(html, ['id="sparqlRecipe"', 'exploreQueries', 'liveQueries', 'Query recipe'], "Footer query recipe selector/quick links missing");
  requireAny(html, ['id="sparqlText"', '<textarea', 'liveQueries', 'exploreQueries'], "Footer editable SPARQL textarea or query recipes missing");
  requireAny(html, ['id="sparqlFormat"', 'text/x-html+tr', 'text%2Fx-html%2Btr'], "Footer SPARQL format display/guidance missing");
  require(html, 'text/x-html+tr', "SELECT result format guidance missing");
  require(html, 'text/x-html-nice-turtle', "DESCRIBE/CONSTRUCT result format guidance missing");
  require(html, 'encodeURIComponent', "SPARQL live link encoding missing");

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
  require(html, "https://linkeddata.uriburner.com/describe/?url=", "URIBurner resolver pattern missing");
  require(html, "https://linkeddata.uriburner.com/sparql", "URIBurner SPARQL endpoint missing");
  require(html, "https://virtuoso.openlinksw.com/", "OpenLink Virtuoso attribution missing");

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
  if (!/\.on\(["']click["'][\s\S]{0,200}resolv/.test(html))
    fail("Node click handler missing resolver call — nodes must open resolver on click");

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
