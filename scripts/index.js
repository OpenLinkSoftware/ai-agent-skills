#!/usr/bin/env node
/* generate-index.js — produce index.html for a directory of knowledge-graph HTML files */

const fs = require('fs');
const path = require('path');

const PALETTE = ['#F59E0B','#10B981','#6366F1','#EF4444','#8B5CF6','#06B6D4','#EC4899','#F97316','#14B8A6','#E11D48'];

const USAGE = 'Usage: node scripts/generate-index.js <directory>';

// ── CLI ──────────────────────────────────────────────────────────────
const dir = process.argv[2];
if (!dir) { console.error(USAGE); process.exit(1); }
const absDir = path.resolve(dir);
if (!fs.statSync(absDir).isDirectory()) { console.error('Not a directory: ' + absDir); process.exit(1); }

// ── Scan (recursive, one level deep) ─────────────────────────────────
function scanDir(dir, prefix) {
  const results = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const e of entries) {
    if (e.name.startsWith('.') || e.name === 'index.html') continue;
    const full = path.join(dir, e.name);
    const rel = prefix ? prefix + '/' + e.name : e.name;
    if (e.isDirectory()) {
      results.push(...scanDir(full, rel));
    } else if (/\.html?$/i.test(e.name)) {
      results.push({ fp: full, rel: rel });
    }
  }
  return results;
}

const htmlFiles = scanDir(absDir, '');
if (htmlFiles.length === 0) { console.error('No .html files found in ' + absDir); process.exit(1); }

// ── Parse metadata from each HTML file ───────────────────────────────
const entries = [];
htmlFiles.forEach(({ fp, rel }) => {
  const raw = fs.readFileSync(fp, 'utf8');
  const meta = extractMeta(raw);

  entries.push({
    file: rel,
    title: meta.title || path.basename(rel).replace(/\.html?$/, ''),
    desc: meta.description || '',
    date: meta.date || dateFromStat(fp),
    publisher: meta.publisher || '',
    author: meta.author || '',
    keywords: meta.keywords,
    theme: meta.theme || inferTheme(meta.keywords),
  });
});

// Sort date-descending
entries.sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')));

// ── Derive themes ────────────────────────────────────────────────────
const themeMap = {};
entries.forEach(e => {
  const t = e.theme || 'general';
  if (!themeMap[t]) themeMap[t] = { label: capitalise(t), color: nextColor(Object.keys(themeMap).length), count: 0 };
  themeMap[t].count++;
});
const themeKeys = Object.keys(themeMap);

// ── Stats ────────────────────────────────────────────────────────────
const dateSpan = entries.length > 1
  ? `${entries[entries.length-1].date} to ${entries[0].date}`
  : entries[0] ? entries[0].date : '—';

// ── Templates ────────────────────────────────────────────────────────
const cssSrc = path.join(__dirname, '..', 'templates', 'corpus-index.css');
const jsSrc  = path.join(__dirname, '..', 'templates', 'corpus-index.js');
const cssOut = path.join(absDir, 'index.css');
const jsOut  = path.join(absDir, 'index.js');
fs.copyFileSync(cssSrc, cssOut);
fs.copyFileSync(jsSrc,  jsOut);

// ── Render data array ────────────────────────────────────────────────
const dataJSON = JSON.stringify(entries.map(e => ({
  title: e.title,
  publisher: e.publisher,
  author: e.author,
  date: e.date,
  theme: e.theme,
  desc: e.desc,
  tags: e.keywords,
  file: e.file,
})), null, 4);

const themeJSON = JSON.stringify(themeMap, null, 4);

// ── Assemble HTML ────────────────────────────────────────────────────
const dirName = path.basename(absDir);
const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${escapeHTML(dirName)} — Index</title>
<link rel="stylesheet" href="index.css">
<style>
/* ── Dynamic theme pill colours ── */
${themeKeys.map(t => `.pill[data-t="${t}"].on { background: ${themeMap[t].color}; }`).join('\n')}
</style>
</head>
<body>

<div class="hero">
  <div class="hero-inner">
    <div class="eyebrow">LOcal Directory · File Index · ${entryCount(entries.length)}</div>
    <h1>${escapeHTML(dirName)}</h1>
    <p>Auto-generated index of ${entries.length} knowledge-graph HTML file${entries.length !== 1 ? 's' : ''} in this directory</p>
    <div class="stats">
      <div><div class="stat-num">${entries.length}</div><div class="stat-lbl">Files</div></div>
      <div><div class="stat-num">${themeKeys.length}</div><div class="stat-lbl">Themes</div></div>
      <div><div class="stat-num">${dateSpan.split(' to ').length}</div><div class="stat-lbl">Timespan</div></div>
    </div>
  </div>
</div>

<div class="controls">
  <input class="search" type="text" id="q" placeholder="🔍  Search titles, topics…" oninput="render()">
  <div class="pills">
    <button class="pill on" data-t="all" onclick="setTheme('all',this)">All</button>
${themeKeys.map(t => `    <button class="pill" data-t="${t}" onclick="setTheme('${t}',this)">${themeMap[t].label} (${themeMap[t].count})</button>`).join('\n')}
  </div>
  <div class="view-btns">
    <button class="vbtn on" id="gBtn" onclick="setView('grid')">⊞ Grid</button>
    <button class="vbtn" id="tBtn" onclick="setView('timeline')">↕ Timeline</button>
    <button class="vbtn" id="tbBtn" onclick="setView('table')">☰ Table</button>
  </div>
</div>

<div class="main">
  <div id="gv"><div class="grid" id="grid"></div><div class="nores" id="nores"><div class="nores-icon">🔍</div><div style="font-weight:600;margin-bottom:4px">No results</div><div>Try a different search or filter</div></div></div>
  <div class="timeline" id="tv"></div>
  <div class="tview" id="tbv"><table class="dtable"><thead><tr><th onclick="sortBy('title')">Title ↕</th><th onclick="sortBy('publisher')">Publisher ↕</th><th onclick="sortBy('date')">Date ↕</th><th onclick="sortBy('theme')">Theme ↕</th><th>Topics</th><th>Links</th></tr></thead><tbody id="tbody"></tbody></table></div>
</div>

<div class="footer" id="foot"></div>

<script>
var THEMES = ${themeJSON};
var DATA = ${dataJSON};
var activeTheme = 'all', activeView = 'grid', sortCol = null, sortAsc = true;

document.getElementById('foot').innerHTML = 'Auto-generated index &nbsp;·&nbsp; <strong>${escapeHTML(absDir)}</strong> &nbsp;·&nbsp; ${new Date().toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric'})}';
</script>
<script src="index.js"></script>
<script>render();</script>
</body>
</html>`;

// ── Write ────────────────────────────────────────────────────────────
const outPath = path.join(absDir, 'index.html');
fs.writeFileSync(outPath, html, 'utf8');
console.log('Written: ' + outPath);
console.log('  ' + entries.length + ' entries, ' + themeKeys.length + ' themes');

// ── Helpers ──────────────────────────────────────────────────────────
function extractMeta(raw) {
  const m = {};
  const titleM = raw.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  if (titleM) m.title = titleM[1].replace(/<[^>]+>/g, '').trim();

  const descM = raw.match(/<meta\s+name=["']description["']\s+content=["']([^"']*)["']/i);
  if (descM) m.description = descM[1].trim();

  const kwM = raw.match(/<meta\s+name=["']keywords["']\s+content=["']([^"']*)["']/i);
  if (kwM) m.keywords = kwM[1].split(/\s*,\s*/).filter(Boolean);

  const authorM = raw.match(/<meta\s+name=["']author["']\s+content=["']([^"']*)["']/i);
  if (authorM) m.author = authorM[1].trim();

  const dateM = raw.match(/<meta\s+name=["']date["']\s+content=["']([^"']*)["']/i);
  if (dateM) m.date = dateM[1].trim();

  // Try JSON-LD
  const ldM = raw.match(/<script\s+type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/i);
  if (ldM) {
    try {
      const ld = JSON.parse(ldM[1]);
      const graph = ld['@graph'] || [ld];
      const article = graph.find(n => /Article|WebPage|CreativeWork/i.test(n['@type'])) || graph[0] || {};
      if (article.datePublished && !m.date) m.date = article.datePublished;
      if (article.description && !m.description) m.description = article.description;
      if (article.keywords && !m.keywords) {
        m.keywords = typeof article.keywords === 'string'
          ? article.keywords.split(/\s*,\s*/)
          : article.keywords;
      }
      const authorNode = graph.find(n => /Person|Organization/.test(n['@type']));
      if (authorNode && authorNode.name && !m.author) m.author = authorNode.name;
      const pubNode = graph.find(n => n['@type'] === 'Organization' || n['@type'] === 'NewsMediaOrganization');
      if (pubNode && pubNode.name) m.publisher = pubNode.name;
    } catch (e) { /* ignore */ }
  }

  return m;
}

function dateFromStat(fp) {
  const s = fs.statSync(fp);
  return s.mtime.toISOString().split('T')[0];
}

function inferTheme(keywords) {
  if (!keywords || keywords.length === 0) return 'general';
  return keywords[0].toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function capitalise(s) {
  return s.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function nextColor(i) { return PALETTE[i % PALETTE.length]; }

function entryCount(n) {
  if (n === 0) return 'No files';
  if (n === 1) return '1 file';
  if (n < 100) return n + ' files';
  return n + ' files';
}

function escapeHTML(str) {
  return String(str || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}