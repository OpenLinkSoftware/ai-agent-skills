#!/usr/bin/env node
// Regenerate references/catalog.json from the app in assets/.
//
// The app is the single source of truth for the showcase content: datasets, example queries, Sponger
// examples, explore datasets, faceted-browser links, OPAL agents and prompts, and section ids. The skill's
// Python scripts read the catalog this exports, so a change to the app reaches the skill by re-running:
//
//   node scripts/build_catalog.mjs
//
// It evaluates only the app's data sections (no DOM code), in an isolated vm context.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const appPath = path.join(root, 'assets', 'virtuoso-ai-value-prop.html');
const outPath = path.join(root, 'references', 'catalog.json');
const html = fs.readFileSync(appPath, 'utf8');

function slice(from, to) {
  const a = html.indexOf(from);
  const b = html.indexOf(to, a + 1);
  if (a < 0 || b < 0) throw new Error(`App section not found: ${from} … ${to}`);
  return html.slice(a, b);
}
const code = [
  slice('/* ---------- endpoints and link builders ---------- */', '/* ---------- SPARQL runner ---------- */'),
  slice('/* ---------- data: RDF Views sources ---------- */', '/* ---------- home ---------- */'),
  slice('/* ---------- Explore ---------- */', 'function fctTypeLink'),
].join('\n');

const cfgMatch = html.match(/<script type="application\/json" id="vap-config">([\s\S]*?)<\/script>/);
if (!cfgMatch) throw new Error('vap-config block not found in the app');
const config = JSON.parse(cfgMatch[1]);
const defaultProfile = config.profiles[config['default']];
const ctx = vm.createContext({ encodeURIComponent, JSON, Object, Array, String, RegExp, Math, window: { VAP_PROFILE: defaultProfile } });
vm.runInContext(code + `
;globalThis.__out = { EP, EP_AUTH_UB, QB, FCT_APP, DEMO_ACCOUNTS, SOURCES, ONTO, FCT, SPONGE_SRC, SPONGED, AGENTS, PROMPTS,
  FAQ, POSTS, EXPLORE_SETS, FCT_TYPE_LINKS, exploreQueryTemplate: exploreQuery('{GRAPH}'), exploreQueryTemplateNoLabel: exploreQuery('{GRAPH}', true) };`, ctx);
const d = ctx.__out;

const strip = s => String(s || '').replace(/<[^>]+>/g, '').replace(/&amp;/g, '&').replace(/\s+/g, ' ').trim();
const hrefs = s => [...String(s || '').matchAll(/href="([^"]+)"/g)].map(m => m[1]);

// section ids and titles, straight from the markup
const sections = [];
for (const m of html.matchAll(/<div class="view" id="view-([a-z-]+)">([\s\S]*?)(?=<div class="view" id="view-|<\/main>)/g)) {
  const view = m[1];
  for (const h of m[2].matchAll(/<h([12])\s+id="([^"]+)"[^>]*>([\s\S]*?)<\/h\1>/g)) {
    sections.push({ id: h[2], view, title: strip(h[3].replace(/<span class="l2">/, ' ')) });
  }
}

const catalog = {
  generatedFrom: 'assets/virtuoso-ai-value-prop.html',
  generatedAt: new Date().toISOString(),
  config,
  spasqlQueryBuilder: { permalink: { v: 1, url: '/XMLA', dsn: 'DSN=Local_Instance', uid: d.DEMO_ACCOUNTS[0].uid, pwd: d.DEMO_ACCOUNTS[0].pwd, path: null, tab: 'exec', idx: null, fkey: null, ref: null, exec: { sql: '{SQL}' } }, accounts: d.DEMO_ACCOUNTS.map(a => a.uid) },
  facetedBrowserDefaultApp: defaultProfile.facetedBrowser,
  views: ['home', 'rdf-views', 'ontologies', 'sponger', 'explore', 'agents', 'sources'],
  ontologies: { label: d.ONTO.label, meta: Object.fromEntries(d.ONTO.meta.map(([k, v]) => [k, strip(v)])) },
  sections,
  datasets: d.SOURCES.map(s => ({
    id: s.id, label: s.label, ep: s.ep, status: s.status || null,
    meta: Object.fromEntries(s.meta.map(([k, v]) => [k, strip(v)])),
    posts: s.meta.flatMap(([, v]) => hrefs(v)),
  })),
  examples: d.SOURCES.concat([d.ONTO]).flatMap(s => s.ex.map(e => ({
    id: e.id, dataset: s.id, view: s.id === 'ontology' ? 'ontologies' : 'rdf-views', ep: s.ep, lang: e.lang, title: e.title, description: strip(e.desc), query: e.code,
    verbatimUrl: e.verbatimUrl || null, postUrl: e.postUrl || null, abridged: !!e.noEnvelope,
    facetedBrowser: e.fct ? d.FCT[e.fct] : null,
  }))),
  sponger: d.SPONGED.map(g => ({
    id: g.id, source: g.url || d.SPONGE_SRC, title: g.title, description: strip(g.desc), ep: 'ub',
    query: g.q, respongeQuery: g.reQ || ('DEFINE get:soft "replace"\n' + g.q),
  })),
  exploreQueryTemplate: d.exploreQueryTemplate,
  exploreQueryTemplateNoLabel: d.exploreQueryTemplateNoLabel,
  exploreDatasets: d.EXPLORE_SETS.map(x => ({ id: x.id, label: x.label, ep: x.ep, graph: x.g, noLabel: !!x.noLabel, note: x.note || null, extras: (x.extras || []).map(k => d.FCT[k]), fallbackTypes: x.fallbackTypes || [] })),
  facetedTypeLinks: d.FCT_TYPE_LINKS,
  agents: d.AGENTS.map(a => ({ key: a.key, module: a.module, label: a.label, functions: a.functions })),
  prompts: d.PROMPTS.map(p => ({ agent: d.AGENTS[p.agent].key, text: p.q })),
  faq: d.FAQ.map(([q, a]) => ({ q, a })),
  sources: d.POSTS.map(p => ({ title: p.t, url: p.u, date: p.d || null, use: p.use })),
};

fs.writeFileSync(outPath, JSON.stringify(catalog, null, 2) + '\n');
console.log(`Profiles: ${Object.keys(config.profiles).join(', ')} (default ${config['default']}).`);
console.log(`Wrote ${path.relative(root, outPath)}: ${catalog.datasets.length} datasets, ${catalog.examples.length} examples, ` +
  `${catalog.sponger.length} Sponger examples, ${catalog.exploreDatasets.length} explore datasets, ${catalog.agents.length} agents, ${catalog.sections.length} sections.`);
