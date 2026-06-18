/**
 * RDF Infographic Generator — TypeScript edition (Node.js ≥ 18, requires n3).
 * Builds self-contained HTML infographics from RDF data.
 * Mirrors generate_infographic.py — same CLI flags, same behavior.
 *
 * Usage:
 *   npx tsx generate_infographic.ts --ttl input.ttl --output out.html
 *   npx tsx generate_infographic.ts --ttl input.ttl -o out.html --title "My Title" --tagline "..."
 */

import { existsSync } from "node:fs";
import { assembleHtml, type AssembleHtmlOptions } from "./html_assembler.ts";

interface Args {
  ttl?: string;
  output?: string;
  title: string;
  description: string;
  tagline: string;
  heroTagline: string;
  metaHtml: string;
  sourceUrl: string;
  sourceLabel: string;
  resolverPattern: string;
}

function parseArgs(argv: string[]): Args {
  const args: Args = {
    title: "",
    description: "",
    tagline: "",
    heroTagline: "",
    metaHtml: "",
    sourceUrl: "",
    sourceLabel: "",
    resolverPattern: "https://linkeddata.uriburner.com/describe/?url=",
  };
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--ttl":               args.ttl          = argv[++i]; break;
      case "--output": case "-o": args.output       = argv[++i]; break;
      case "--title":             args.title         = argv[++i]; break;
      case "--description":       args.description   = argv[++i]; break;
      case "--tagline":           args.tagline        = argv[++i]; break;
      case "--hero-tagline":      args.heroTagline    = argv[++i]; break;
      case "--meta-html":         args.metaHtml       = argv[++i]; break;
      case "--source-url":        args.sourceUrl      = argv[++i]; break;
      case "--source-label":      args.sourceLabel    = argv[++i]; break;
      case "--resolver-pattern":  args.resolverPattern = argv[++i]; break;
    }
  }
  return args;
}

function main(): number {
  const args = parseArgs(process.argv.slice(2));

  if (!args.ttl) {
    process.stderr.write("Error: --ttl is required\n");
    process.stderr.write(
      "Usage: npx tsx generate_infographic.ts --ttl input.ttl --output out.html\n",
    );
    return 1;
  }
  if (!args.output) {
    process.stderr.write("Error: --output/-o is required\n");
    return 1;
  }
  if (!existsSync(args.ttl)) {
    process.stderr.write(`Error: RDF file not found: ${args.ttl}\n`);
    return 1;
  }

  const opts: AssembleHtmlOptions = {
    rdfPath:         args.ttl,
    outputPath:      args.output,
    title:           args.title,
    description:     args.description,
    tagline:         args.tagline,
    heroTagline:     args.heroTagline,
    metaHtml:        args.metaHtml,
    sourceUrl:       args.sourceUrl,
    sourceLabel:     args.sourceLabel,
    resolverPattern: args.resolverPattern,
  };

  const success = assembleHtml(opts);
  return success ? 0 : 1;
}

if (
  process.argv[1] &&
  (process.argv[1].endsWith("generate_infographic.ts") ||
    process.argv[1].endsWith("generate_infographic.js"))
) {
  process.exit(main());
}
