/**
 * HTML Assembler — TypeScript edition (Node.js ≥ 18, requires n3).
 * Assembles RDF data into a self-contained HTML infographic.
 * Mirrors html_assembler.py — same signature, same output.
 *
 * Install: npm install (from rdf-infographic-skill/scripts/)
 * Import:  import { assembleHtml } from "./html_assembler.ts";
 */

import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { basename, dirname, join, relative, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import {
  buildKgdata,
  extractNarrative,
  getBaseIri,
  validateOrphans,
} from "./rdf_parser.ts";

const __dirname_compat = dirname(
  typeof __filename !== "undefined"
    ? __filename
    : fileURLToPath(import.meta.url),
);
const TEMPLATES_DIR = join(__dirname_compat, "templates");
const VALIDATOR    = join(__dirname_compat, "validate-harness-contract.ts");

// ── Mini Jinja2-compatible template engine ────────────────────────────────────

function escHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function resolvePath(ctx: Record<string, unknown>, path: string): unknown {
  const parts = path.split(".");
  let val: unknown = ctx;
  for (const p of parts) {
    if (val == null || typeof val !== "object") return "";
    val = (val as Record<string, unknown>)[p];
  }
  return val ?? "";
}

function renderTemplate(tpl: string, ctx: Record<string, unknown>): string {
  // 1. {% for item in list %}...{% endfor %}
  tpl = tpl.replace(
    /\{%-?\s*for\s+(\w+)\s+in\s+(\w+)\s*-?%\}([\s\S]*?)\{%-?\s*endfor\s*-?%\}/g,
    (_, item, listName, body) => {
      const list = resolvePath(ctx, listName);
      if (!Array.isArray(list)) return "";
      return list
        .map((el: unknown) => renderTemplate(body, { ...ctx, [item]: el }))
        .join("");
    },
  );

  // 2. {% if var %}...{% endif %} (truthy check; no else branch needed)
  tpl = tpl.replace(
    /\{%-?\s*if\s+([\w.]+)\s*-?%\}([\s\S]*?)\{%-?\s*endif\s*-?%\}/g,
    (_, cond, body) =>
      resolvePath(ctx, cond) ? renderTemplate(body, ctx) : "",
  );

  // 3. {{ a or b }} — Jinja2-style fallback expression
  tpl = tpl.replace(
    /\{\{\s*([\w.]+)\s+or\s+([\w.]+)\s*\}\}/g,
    (_, a, b) => String(resolvePath(ctx, a) || resolvePath(ctx, b) || ""),
  );

  // 4. {{ var|e }} — HTML-escaped output
  tpl = tpl.replace(
    /\{\{\s*([\w.]+)\|e\s*\}\}/g,
    (_, path) => escHtml(String(resolvePath(ctx, path))),
  );

  // 5. {{ var }} and {{ obj.prop }} — raw output
  tpl = tpl.replace(
    /\{\{\s*([\w.]+)\s*\}\}/g,
    (_, path) => String(resolvePath(ctx, path)),
  );

  return tpl;
}

// ── Template asset loader ─────────────────────────────────────────────────────

function loadAsset(name: string): string {
  const assetPath = join(TEMPLATES_DIR, name);
  if (!existsSync(assetPath)) throw new Error(`Missing template asset: ${assetPath}`);
  return readFileSync(assetPath, "utf-8");
}

// ── Narrative builder ─────────────────────────────────────────────────────────

interface NavLink { href: string; label: string; }
interface SparqlRecipe { label: string; query: string; }

function makeSectionHtml(id: string, title: string, inner: string): string {
  return (
    `<section class="section section-alt" id="${id}">` +
    `<h2>${title}<a class="headline-anchor" href="#${id}" aria-label="Link to this section">¶</a></h2>` +
    `${inner}` +
    `</section>`
  );
}

function resolverLink(iri: string, pattern: string): string {
  return pattern + encodeURIComponent(iri);
}

function renderNarrative(
  rdfPath: string,
  baseIri: string,
  resolverPattern: string,
): { html: string; navLinks: NavLink[]; sections: string[] } {
  const narrative = extractNarrative(rdfPath, baseIri);
  const navLinks: NavLink[] = [{ href: "#hero", label: "Overview" }];
  const htmlParts: string[] = [];
  const sections: string[] = [];

  if (narrative.people.length) {
    let inner = "";
    for (const p of narrative.people) {
      const href = resolverLink(p.iri, resolverPattern);
      inner += `<div class="card"><h3><a href="${href}" target="_blank" rel="noopener noreferrer">${escHtml(p.name)}</a></h3><p>${escHtml(p.description)}</p></div>`;
    }
    htmlParts.push(makeSectionHtml("people", "People", `<div class="cards-grid">${inner}</div>`));
    navLinks.push({ href: "#people", label: "People" });
    sections.push("people");
  }

  if (narrative.organizations.length) {
    let inner = "";
    for (const o of narrative.organizations) {
      const href = resolverLink(o.iri, resolverPattern);
      inner += `<div class="card"><h3><a href="${href}" target="_blank" rel="noopener noreferrer">${escHtml(o.name)}</a></h3><p>${escHtml(o.description)}</p></div>`;
    }
    htmlParts.push(makeSectionHtml("organizations", "Organizations", `<div class="cards-grid">${inner}</div>`));
    navLinks.push({ href: "#organizations", label: "Organizations" });
    sections.push("organizations");
  }

  if (narrative.faq.length) {
    let inner = '<div class="faq-list">';
    for (const faq of narrative.faq) {
      const lo = faq.iri ? `<a href="${resolverLink(faq.iri, resolverPattern)}" target="_blank" rel="noopener noreferrer">` : "";
      const lc = faq.iri ? "</a>" : "";
      inner +=
        `<div class="faq-item anim-fade">` +
        `<div class="faq-question">${lo}${escHtml(faq.question)}${lc}<span class="faq-chevron">▼</span></div>` +
        `<div class="faq-answer"><p>${escHtml(faq.answer)}</p></div>` +
        `</div>`;
    }
    inner += "</div>";
    htmlParts.push(makeSectionHtml("faq", "Frequently Asked Questions", inner));
    navLinks.push({ href: "#faq", label: "FAQ" });
    sections.push("faq");
  }

  if (narrative.glossary.length) {
    let inner = '<div class="glossary-grid">';
    for (const g of narrative.glossary) {
      const lo = g.iri ? `<a href="${resolverLink(g.iri, resolverPattern)}" target="_blank" rel="noopener noreferrer">` : "";
      const lc = g.iri ? "</a>" : "";
      inner += `<div class="glossary-term"><h4>${lo}${escHtml(g.term)}${lc}</h4><p>${escHtml(g.definition)}</p></div>`;
    }
    inner += "</div>";
    htmlParts.push(makeSectionHtml("glossary", "Glossary of Terms", inner));
    navLinks.push({ href: "#glossary", label: "Glossary" });
    sections.push("glossary");
  }

  if (narrative.howto.length) {
    let inner = '<div class="howto-list">';
    narrative.howto.forEach((step, i) => {
      const lo = step.iri ? `<a href="${resolverLink(step.iri, resolverPattern)}" target="_blank" rel="noopener noreferrer">` : "";
      const lc = step.iri ? "</a>" : "";
      inner +=
        `<div class="howto-step anim-fade">` +
        `<div class="howto-num">${i + 1}</div>` +
        `<div class="howto-content"><h4>${lo}${escHtml(step.step)}${lc}</h4><p>${escHtml(step.description)}</p></div>` +
        `</div>`;
    });
    inner += "</div>";
    htmlParts.push(makeSectionHtml("howto", "How-To Guide", inner));
    navLinks.push({ href: "#howto", label: "HowTo" });
    sections.push("howto");
  }

  navLinks.push(
    { href: "#kg-explorer", label: "KG Explorer" },
    { href: "#sparql-explorer", label: "SPARQL" },
    { href: "#footer", label: "Footer" },
  );

  return { html: htmlParts.join("\n"), navLinks, sections };
}

function renderJsonLd(
  title: string,
  description: string,
  baseIri: string,
  rdfRelPath: string,
): string {
  return JSON.stringify(
    {
      "@context": { "@vocab": "http://schema.org/", "@language": "en" },
      "@type": "Article",
      "@id": baseIri,
      headline: title,
      description,
      mainEntity: { "@type": "CreativeWork", "@id": baseIri },
      sameAs: rdfRelPath,
    },
    null,
    2,
  );
}

function buildSparqlRecipes(baseIri: string): SparqlRecipe[] {
  return [
    {
      label: "All triples (sample)",
      query: "SELECT ?s ?p ?o\nWHERE { ?s ?p ?o }\nLIMIT 25",
    },
    {
      label: "Entity types summary",
      query:
        "SELECT ?type (COUNT(?s) AS ?count)\nWHERE { ?s a ?type }\nGROUP BY ?type\nORDER BY DESC(?count)",
    },
    {
      label: "Named graph triples",
      query: `SELECT ?s ?p ?o\nFROM <${baseIri}>\nWHERE { ?s ?p ?o }\nLIMIT 25`,
    },
  ];
}

// ── Public API ────────────────────────────────────────────────────────────────

export interface AssembleHtmlOptions {
  rdfPath: string;
  outputPath: string;
  title?: string;
  description?: string;
  sourceUrl?: string;
  sourceLabel?: string;
  resolverPattern?: string;
  tagline?: string;
  heroTagline?: string;
  metaHtml?: string;
}

export function assembleHtml(opts: AssembleHtmlOptions): boolean {
  const {
    rdfPath,
    outputPath,
    title: titleOpt = "",
    description: descOpt = "",
    sourceUrl = "",
    sourceLabel = "",
    resolverPattern = "https://linkeddata.uriburner.com/describe/?url=",
    tagline = "",
    heroTagline = "",
    metaHtml = "",
  } = opts;

  const stem   = basename(rdfPath).replace(/\.[^.]+$/, "");
  const title  = titleOpt  || `Knowledge Graph Infographic — ${stem}`;
  const description = descOpt || `Interactive infographic generated from ${basename(rdfPath)}`;

  const baseIri       = getBaseIri(rdfPath);
  const rdfRelPath    = relative(dirname(resolve(outputPath)), resolve(rdfPath));
  const rdfFilename   = basename(rdfPath);
  const outputFilename = basename(outputPath);

  console.log("Parsing RDF...");
  const kgdata  = buildKgdata(rdfPath);
  console.log(`  Nodes: ${kgdata.nodes.length}, Links: ${kgdata.links.length}`);

  const orphans = validateOrphans(kgdata);
  if (orphans.length) {
    console.log(`  Warning: ${orphans.length} orphan nodes — ${orphans.slice(0, 5).join(", ")}`);
  } else {
    console.log("  Zero orphan nodes");
  }

  console.log("Extracting narrative...");
  const { html: narrativeHtml, navLinks, sections } = renderNarrative(
    rdfPath, baseIri, resolverPattern,
  );
  console.log(`  Sections: ${sections.join(", ") || "(none)"}`);

  const jsonldContent  = renderJsonLd(title, description, baseIri, rdfRelPath);
  const sparqlRecipes  = buildSparqlRecipes(baseIri);
  const defaultSparql  = sparqlRecipes[0].query;
  const cssContent     = loadAsset("styles.css");
  const kgExplorerJs   = loadAsset("kg_explorer.js");
  const kgdataJson     = JSON.stringify(kgdata);

  console.log("Assembling HTML...");
  const templateStr = loadAsset("base_template.html");
  const html = renderTemplate(templateStr, {
    title,
    description,
    tagline,
    hero_tagline:    heroTagline,
    meta_html:       metaHtml,
    rdf_rel_path:    rdfRelPath,
    rdf_filename:    rdfFilename,
    output_filename: outputFilename,
    base_iri:        baseIri,
    css_content:     cssContent,
    jsonld_content:  jsonldContent,
    kgdata_json:     kgdataJson,
    kg_explorer_js:  kgExplorerJs,
    nav_links:       navLinks,
    narrative_html:  narrativeHtml,
    sparql_recipes:  sparqlRecipes,
    default_sparql:  defaultSparql,
    source_url:      sourceUrl,
    source_label:    sourceLabel,
  });

  mkdirSync(dirname(resolve(outputPath)), { recursive: true });
  writeFileSync(outputPath, html, "utf-8");
  const sizeKb = (statSync(outputPath).size / 1024).toFixed(1);
  console.log(`Written: ${outputPath} (${sizeKb} KB)`);

  if (existsSync(VALIDATOR)) {
    console.log("Running harness contract validation...");
    const result = spawnSync(
      "npx",
      ["tsx", VALIDATOR, outputPath, "--ttl", rdfPath],
      { encoding: "utf-8", shell: true },
    );
    if (result.status === 0) {
      console.log("  PASS");
      return true;
    }
    console.log("  FAIL");
    if (result.stdout) console.log("  " + result.stdout.replace(/\n/g, "\n  "));
    return false;
  }

  console.log(`  Validator not found at ${VALIDATOR}`);
  return true;
}
