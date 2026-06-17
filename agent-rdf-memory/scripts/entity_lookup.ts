/**
 * Entity Lookup — Wikidata & DBpedia Disambiguation via Jaro-Winkler.
 * TypeScript edition (Node.js ≥ 18, no npm deps — uses built-in fetch).
 * Mirrors entity_lookup.py — same public API, same CLI flags.
 *
 * Usage as module:
 *   import { lookup, best } from "./entity_lookup.ts";
 *   const results = await lookup("OpenAI", { entityType: "Organization" });
 *
 * Usage as CLI:
 *   npx tsx entity_lookup.ts --name "Snowflake Inc." --type Organization
 *   npx tsx entity_lookup.ts --name "Tim Berners-Lee" --source wikidata --json
 */

// ── Jaro-Winkler (inline, no external dep) ───────────────────────────────────

function jaro(s1: string, s2: string): number {
  if (s1 === s2) return 1;
  const len1 = s1.length, len2 = s2.length;
  if (len1 === 0 || len2 === 0) return 0;

  const matchDist = Math.max(Math.floor(Math.max(len1, len2) / 2) - 1, 0);
  const s1m = new Uint8Array(len1);
  const s2m = new Uint8Array(len2);
  let matches = 0;

  for (let i = 0; i < len1; i++) {
    const start = Math.max(0, i - matchDist);
    const end   = Math.min(i + matchDist + 1, len2);
    for (let j = start; j < end; j++) {
      if (s2m[j] || s1[i] !== s2[j]) continue;
      s1m[i] = s2m[j] = 1;
      matches++;
      break;
    }
  }

  if (matches === 0) return 0;
  let t = 0, k = 0;
  for (let i = 0; i < len1; i++) {
    if (!s1m[i]) continue;
    while (!s2m[k]) k++;
    if (s1[i] !== s2[k]) t++;
    k++;
  }
  return (matches / len1 + matches / len2 + (matches - t / 2) / matches) / 3;
}

function jaroWinkler(a: string, b: string): number {
  a = a.toLowerCase(); b = b.toLowerCase();
  const j = jaro(a, b);
  let p = 0;
  for (let i = 0; i < Math.min(4, a.length, b.length); i++) {
    if (a[i] !== b[i]) break;
    p++;
  }
  return j + p * 0.1 * (1 - j);
}

// ── Thresholds ────────────────────────────────────────────────────────────────

const SAMEAS_THRESHOLD   = 0.97;
const RELATED_THRESHOLD  = 0.88;
const SEEALSO_THRESHOLD  = 0.78;

// ── API endpoint templates ────────────────────────────────────────────────────

const WIKIDATA_SEARCH = (q: string) =>
  `https://www.wikidata.org/w/api.php?action=wbsearchentities&search=${encodeURIComponent(q)}&language=en&limit=10&format=json`;

const WIKIDATA_ASK = (qid: string, scopeQid: string) =>
  `https://query.wikidata.org/sparql?format=json&query=` +
  encodeURIComponent(
    `ASK { { wd:${qid} wdt:P31/wdt:P279* wd:${scopeQid} . } UNION { wd:${qid} wdt:P279* wd:${scopeQid} . } }`
  );

const DBPEDIA_LOOKUP = (q: string) =>
  `https://lookup.dbpedia.org/api/search?query=${encodeURIComponent(q)}&format=json&maxResults=10`;

// ── Entity-type → Wikidata Q-ID mappings ─────────────────────────────────────

const TYPE_WIKIDATA_SCOPE: Record<string, string> = {
  organization:       "Q43229",
  company:            "Q783794",
  corporation:        "Q167037",
  business:           "Q4830453",
  person:             "Q5",
  software:           "Q7397",
  softwareapplication:"Q166142",
  programminglanguage:"Q9143",
  database:           "Q8513",
  city:               "Q515",
  country:            "Q6256",
  product:            "Q2424752",
  event:              "Q1656682",
  conference:         "Q2020153",
  standard:           "Q317623",
  protocol:           "Q1323643",
  academicdiscipline: "Q11862829",
  university:         "Q3918",
  website:            "Q35127",
  book:               "Q571",
  film:               "Q11424",
  album:              "Q482994",
  concept:            "Q151885",
  technology:         "Q11016",
  ontology:           "Q324254",
  knowledgegraph:     "Q33002955",
};

// ── Entity-type → DBpedia class mappings ─────────────────────────────────────

const TYPE_DBPEDIA_SCOPE: Record<string, string> = {
  organization:       "dbo:Organisation",
  company:            "dbo:Company",
  corporation:        "dbo:Company",
  business:           "dbo:Company",
  person:             "dbo:Person",
  software:           "dbo:Software",
  softwareapplication:"dbo:Software",
  programminglanguage:"dbo:ProgrammingLanguage",
  city:               "dbo:City",
  country:            "dbo:Country",
  product:            "dbo:MeanOfTransportation",
  event:              "dbo:Event",
  conference:         "dbo:Convention",
  standard:           "dbo:Organisation",
  university:         "dbo:University",
  website:            "dbo:Website",
  book:               "dbo:Book",
  film:               "dbo:Film",
  album:              "dbo:Album",
};

// ── Types ─────────────────────────────────────────────────────────────────────

export interface EntityMatch {
  iri:          string;
  label:        string;
  score:        number;
  source:       "wikidata" | "dbpedia";
  relationship: "owl:sameAs" | "skos:related" | "rdfs:seeAlso";
  entityType?:  string;
  description?: string;
  altLabel?:    string;
}

export function toTurtleTriple(match: EntityMatch, subjectIri: string): string {
  const comment = `  # ${match.label} (${match.source}, score=${match.score.toFixed(3)})`;
  return `    ${match.relationship} <${match.iri}> .${comment}`;
}

// ── HTTP helpers ──────────────────────────────────────────────────────────────

async function getJson(url: string): Promise<unknown> {
  try {
    const res = await fetch(url, {
      headers: { "User-Agent": "entity-lookup-ts/1.0" },
      signal: AbortSignal.timeout(15_000),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

// ── Wikidata ──────────────────────────────────────────────────────────────────

async function checkWikidataInstance(qid: string, scopeQid: string): Promise<boolean> {
  try {
    const data = await getJson(WIKIDATA_ASK(qid, scopeQid)) as { boolean?: boolean } | null;
    return Boolean(data?.boolean);
  } catch {
    return false;
  }
}

async function searchWikidata(
  query: string,
  entityType?: string,
): Promise<Array<{ id: string; label: string; description: string; aliases: string[] }>> {
  const data = await getJson(WIKIDATA_SEARCH(query)) as { search?: unknown[] } | null;
  if (!data?.search) return [];

  let hits = (data.search as Array<{
    id?: string; label?: string; description?: string; aliases?: string[];
  }>).map(h => ({
    id:          h.id ?? "",
    label:       h.label ?? "",
    description: h.description ?? "",
    aliases:     h.aliases ?? [],
  })).filter(h => h.id);

  if (entityType) {
    const scopeQid = TYPE_WIKIDATA_SCOPE[entityType.toLowerCase()];
    if (scopeQid) {
      const checks = await Promise.all(hits.map(h => checkWikidataInstance(h.id, scopeQid)));
      const filtered = hits.filter((_, i) => checks[i]);
      if (filtered.length) hits = filtered;
    }
  }
  return hits;
}

// ── DBpedia ───────────────────────────────────────────────────────────────────

async function searchDbpedia(
  query: string,
  entityType?: string,
): Promise<Array<{ iri: string; label: string; description: string; categories: string[]; types: string[] }>> {
  const data = await getJson(DBPEDIA_LOOKUP(query)) as { docs?: unknown[] } | null;
  if (!data?.docs) return [];

  const results: Array<{ iri: string; label: string; description: string; categories: string[]; types: string[] }> = [];
  for (const doc of data.docs as Array<Record<string, unknown>>) {
    const iri   = (Array.isArray(doc["resource"]) ? (doc["resource"] as string[])[0] : "") ?? "";
    const label = (Array.isArray(doc["label"])    ? (doc["label"] as string[])[0]    : "") ?? "";
    if (!iri) continue;

    const typesRaw: string[] = Array.isArray(doc["type"]) ? doc["type"] as string[]
      : typeof doc["type"] === "string" ? [doc["type"]] : [];

    if (entityType) {
      const scopeCls = TYPE_DBPEDIA_SCOPE[entityType.toLowerCase()];
      if (scopeCls) {
        const scopeShort = scopeCls.split(":")[1];
        const matches = typesRaw.some(t =>
          t.endsWith("/" + scopeShort) || t.endsWith("#" + scopeShort) ||
          (t.includes(":") && t.split(":").pop() === scopeShort)
        );
        if (!matches) continue;
      }
    }

    results.push({
      iri,
      label,
      description: (Array.isArray(doc["comment"]) ? (doc["comment"] as string[])[0] : "") ?? "",
      categories:  Array.isArray(doc["category"]) ? doc["category"] as string[] : [],
      types:       typesRaw,
    });
  }
  return results;
}

// ── Scoring ───────────────────────────────────────────────────────────────────

function scoreAndAssign(
  query: string,
  candidates: Array<{ id?: string; iri?: string; label: string; description: string; aliases?: string[] }>,
  source: "wikidata" | "dbpedia",
): EntityMatch[] {
  const q = query.toLowerCase();
  const matches: EntityMatch[] = [];

  for (const c of candidates) {
    if (!c.label) continue;
    let score = jaroWinkler(q, c.label);
    for (const alias of c.aliases ?? []) {
      const s = jaroWinkler(q, alias);
      if (s > score) score = s;
    }
    if (score < SEEALSO_THRESHOLD) continue;

    const relationship: EntityMatch["relationship"] =
      score >= SAMEAS_THRESHOLD  ? "owl:sameAs"    :
      score >= RELATED_THRESHOLD ? "skos:related"  :
                                   "rdfs:seeAlso";

    const iri = source === "wikidata"
      ? `http://www.wikidata.org/entity/${c.id}`
      : (c.iri ?? "");
    if (!iri) continue;

    matches.push({
      iri,
      label:        c.label,
      score:        Math.round(score * 10_000) / 10_000,
      source,
      relationship,
      description:  c.description || undefined,
      altLabel:     c.aliases?.[0] ?? undefined,
    });
  }

  return matches.sort((a, b) => b.score - a.score);
}

// ── Public API ────────────────────────────────────────────────────────────────

export interface LookupOptions {
  entityType?:  string;
  dataSource?:  "wikidata" | "dbpedia" | "both";
  threshold?:   number;
}

export async function lookup(name: string, opts: LookupOptions = {}): Promise<EntityMatch[]> {
  const {
    entityType,
    dataSource = "both",
    threshold  = SEEALSO_THRESHOLD,
  } = opts;

  const allMatches: EntityMatch[] = [];

  if (dataSource === "wikidata" || dataSource === "both") {
    const hits = await searchWikidata(name, entityType);
    allMatches.push(...scoreAndAssign(name, hits, "wikidata"));
  }
  if (dataSource === "dbpedia" || dataSource === "both") {
    const hits = await searchDbpedia(name, entityType);
    allMatches.push(...scoreAndAssign(name, hits, "dbpedia"));
  }

  allMatches.sort((a, b) => b.score - a.score);
  const floor = Math.max(threshold, SEEALSO_THRESHOLD);
  return allMatches.filter(m => m.score >= floor);
}

export async function best(name: string, opts: LookupOptions = {}): Promise<EntityMatch | null> {
  const results = await lookup(name, opts);
  return results[0] ?? null;
}

// ── CLI ───────────────────────────────────────────────────────────────────────

interface CliArgs {
  name?: string;
  entityType?: string;
  source: "wikidata" | "dbpedia" | "both";
  threshold: number;
  json: boolean;
  subject?: string;
}

function parseCli(argv: string[]): CliArgs {
  const args: CliArgs = { source: "both", threshold: SEEALSO_THRESHOLD, json: false };
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--name": case "-n":       args.name       = argv[++i]; break;
      case "--type": case "-t":       args.entityType = argv[++i]; break;
      case "--source": case "-s":     args.source     = argv[++i] as CliArgs["source"]; break;
      case "--threshold":             args.threshold  = parseFloat(argv[++i]); break;
      case "--json": case "-j":       args.json       = true; break;
      case "--subject":               args.subject    = argv[++i]; break;
    }
  }
  return args;
}

async function main(): Promise<number> {
  const args = parseCli(process.argv.slice(2));

  if (!args.name) {
    process.stderr.write(
      "Error: --name is required\n" +
      "Usage: npx tsx entity_lookup.ts --name <entity> [--type <type>] [--source wikidata|dbpedia|both] [--json]\n"
    );
    return 1;
  }

  const results = await lookup(args.name, {
    entityType: args.entityType,
    dataSource: args.source,
    threshold:  args.threshold,
  });

  if (args.subject && results.length) {
    for (const m of results) console.log(toTurtleTriple(m, args.subject));
  } else if (args.json) {
    console.log(JSON.stringify(results, null, 2));
  } else {
    if (!results.length) {
      process.stderr.write(`No matches found for '${args.name}'\n`);
      return 1;
    }
    for (let i = 0; i < results.length; i++) {
      const m = results[i];
      const src = `[${m.source}]`.padEnd(12);
      const rel = m.relationship.padEnd(16);
      console.log(
        `${i + 1}. ${m.label.padEnd(40)} ${src} ${rel} ${m.score.toFixed(4)}  → ${m.iri}`
      );
      if (m.description) console.log(`   ${m.description.slice(0, 100)}`);
    }
  }

  return 0;
}

if (
  process.argv[1] &&
  (process.argv[1].endsWith("entity_lookup.ts") || process.argv[1].endsWith("entity_lookup.js"))
) {
  main().then(code => process.exit(code));
}
