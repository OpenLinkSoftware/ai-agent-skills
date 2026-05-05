#!/usr/bin/env node
/* backfill-rdf-related.js — add POSH <link rel="related"> and JSON-LD "relatedLink" to HTML files that have adjacent RDF */

const fs = require('fs');
const path = require('path');

const dirs = process.argv.slice(2);
if (dirs.length === 0) {
  console.error('Usage: node scripts/backfill-rdf-related.js <dir1> <dir2> ...');
  process.exit(1);
}

const RDF_EXTS = ['.jsonld', '.ttl', '.rdf', '.nt'];
const TYPE_MAP = { '.jsonld': 'application/ld+json', '.ttl': 'text/turtle', '.rdf': 'application/rdf+xml', '.nt': 'application/n-triples' };

let total = 0;

dirs.forEach(dir => {
  const abs = path.resolve(dir);
  if (!fs.statSync(abs).isDirectory()) { console.error('Not a directory: ' + abs); return; }

  const files = fs.readdirSync(abs).filter(f => /\.html?$/i.test(f) && f !== 'index.html');
  files.forEach(f => {
    const fp = path.join(abs, f);
    const base = f.replace(/\.html?$/i, '');

    // Find adjacent RDF — same dir, then sibling rdf/ dir, then fuzzy match
    let rdfFile = null;
    for (const ext of RDF_EXTS) {
      if (fs.existsSync(path.join(abs, base + ext))) {
        rdfFile = base + ext;
        break;
      }
    }
    // Check sibling rdf/ directory
    if (!rdfFile) {
      const siblingRdf = path.join(abs, '..', 'rdf');
      if (fs.existsSync(siblingRdf)) {
        for (const ext of RDF_EXTS) {
          const exact = path.join(siblingRdf, base + ext);
          if (fs.existsSync(exact)) { rdfFile = '../rdf/' + base + ext; break; }
        }
        // Fuzzy: bidirectional substring match
        if (!rdfFile) {
          const rdffiles = fs.readdirSync(siblingRdf).filter(f => RDF_EXTS.includes(path.extname(f)));
          const match = rdffiles.find(r => {
            const rBase = r.replace(/\.\w+$/, '');
            return r.startsWith(base) || base.startsWith(rBase) || rBase.startsWith(base);
          });
          if (match) rdfFile = '../rdf/' + match;
        }
      }
    }
    if (!rdfFile) return;

    let raw = fs.readFileSync(fp, 'utf8');
    let changed = false;

    // 1. Add POSH <link rel="related"> if not present
    if (!/<link[^>]*rel=["'][^"']*related[^"']*["']/i.test(raw)) {
      const linkTag = `<link rel="related" href="${rdfFile}" type="${TYPE_MAP[path.extname(rdfFile)] || 'application/ld+json'}">`;
      // Insert after last <link> or after <meta charset> or before </head>
      const lastLink = raw.match(/<link[^>]*\/?>/gi);
      if (lastLink && lastLink.length > 0) {
        const pos = raw.lastIndexOf(lastLink[lastLink.length - 1]) + lastLink[lastLink.length - 1].length;
        raw = raw.slice(0, pos) + '\n' + linkTag + raw.slice(pos);
      } else if (/<meta\s+charset/i.test(raw)) {
        raw = raw.replace(/(<meta\s+charset[^>]*>)/i, '$1\n' + linkTag);
      } else {
        raw = raw.replace(/<\/head>/i, '  ' + linkTag + '\n</head>');
      }
      changed = true;
    }

    // 2. Add JSON-LD "relatedLink" as IRI if not present
    const rdfIRI = '{"@id": "' + rdfFile + '"}';
    if (!/"relatedLink"/.test(raw) && /<script\s+type=["']application\/ld\+json["'][^>]*>/i.test(raw)) {
      raw = raw.replace(
        /(<script\s+type=["']application\/ld\+json["'][^>]*>\s*\{[\s\S]*?)("headline"|"name"|"@type")([\s\S]*?)(\s*"@graph")/i,
        (match, before, prop, middle, after) => {
          return before + '"relatedLink": ' + rdfIRI + ',\n  ' + prop + middle + after;
        }
      );
      if (!/"relatedLink"/.test(raw)) {
        raw = raw.replace(
          /("datePublished"\s*:\s*"[^"]*",)/,
          '$1\n  "relatedLink": ' + rdfIRI + ','
        );
      }
      if (!/"relatedLink"/.test(raw)) {
        raw = raw.replace(
          /("owl:sameAs"\s*:\s*\{[^}]*\})/,
          '$1,\n  "relatedLink": ' + rdfIRI
        );
      }
      changed = !!/"relatedLink"/.test(raw);
    }

    // 3. Fix relatedLink from literal string to IRI form
    if (/"relatedLink"\s*:\s*"(?!\s*\{)[^"]*"/.test(raw)) {
      raw = raw.replace(/"relatedLink"\s*:\s*"([^"]+)"/g, '"relatedLink": {"@id": "$1"}');
      changed = true;
    }

    if (changed) {
      fs.writeFileSync(fp, raw, 'utf8');
      console.log('Updated: ' + fp + '  → ' + rdfFile);
      total++;
    }
  });
});

console.log('\nDone. ' + total + ' files updated.');
