/**
 * YouID Template Filler — TypeScript edition (Node.js ≥ 18, no npm deps).
 * Identical behavior to template_fill.py.
 *
 * Template syntax:
 *   %{key}      Simple substitution (error if key missing)
 *   !{key}      Conditional line: whole line removed if key is empty/unset
 *   !!{key}     Conditional block start (alone on its own line)
 *   !!{key}...  Prefix variant: line is conditional on key being set
 *   !!.         Conditional block end
 *
 * Usage:
 *   npx tsx template_fill.ts <template_file> <data_json_file> [output_file]
 *   npx tsx template_fill.ts <template_file> -                [output_file]
 *   (pass - to read data JSON from stdin)
 */

import { readFileSync, writeFileSync } from "node:fs";
import { createInterface } from "node:readline";

type Data = Record<string, unknown>;

function isSet(val: unknown): boolean {
  if (val == null) return false;
  return String(val).length > 0;
}

/** Split text into lines keeping the trailing newline on each line (like Python's splitlines(keepends=True)). */
function splitLinesKeepEnds(text: string): string[] {
  const lines: string[] = [];
  let pos = 0;
  while (pos < text.length) {
    const nl = text.indexOf("\n", pos);
    if (nl === -1) { lines.push(text.slice(pos)); break; }
    lines.push(text.slice(pos, nl + 1));
    pos = nl + 1;
  }
  return lines;
}

function processConditionalBlocks(lines: string[], data: Data): string[] {
  const result: string[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];

    // !!{key} alone on a line — start of conditional block
    const blockStart = line.match(/^(\s*)!!\{(\w+)\}\s*(\r?\n)?$/);
    if (blockStart) {
      const key = blockStart[2];
      const blockLines: string[] = [];
      i++;
      while (i < lines.length) {
        if (lines[i].trimStart().startsWith("!!.")) { i++; break; }
        blockLines.push(lines[i]);
        i++;
      }
      if (isSet(data[key])) result.push(...blockLines);
      continue;
    }

    // !!{key}content — prefix variant: line conditioned on key
    const blockPrefix = line.match(/^(\s*)!!\{(\w+)\}(.*\r?\n?)$/);
    if (blockPrefix) {
      const [, indent, key, rest] = blockPrefix;
      if (isSet(data[key])) result.push(indent + rest);
      i++;
      continue;
    }

    result.push(line);
    i++;
  }
  return result;
}

function processConditionalLines(lines: string[], data: Data): string[] {
  const result: string[] = [];
  for (const line of lines) {
    const conditionals = [...line.matchAll(/!\{(\w+)\}/g)];
    if (conditionals.length === 0) {
      result.push(line);
      continue;
    }
    const allSatisfied = conditionals.every(m => isSet(data[m[1]]));
    if (allSatisfied) {
      result.push(line.replace(/!\{(\w+)\}/g, ""));
    }
    // else: entire line is removed
  }
  return result;
}

function substituteValues(lines: string[], data: Data): string[] {
  return lines.map(line =>
    line.replace(/%\{(\w+)\}/g, (_, key: string) => {
      if (!(key in data) || data[key] == null) {
        throw new Error(`Missing required template variable: ${key}`);
      }
      return String(data[key]);
    }),
  );
}

export function fillTemplate(templateText: string, data: Data): string {
  let lines = splitLinesKeepEnds(templateText);
  lines = processConditionalBlocks(lines, data);
  lines = processConditionalLines(lines, data);
  lines = substituteValues(lines, data);
  return lines.join("");
}

async function readStdin(): Promise<string> {
  const rl = createInterface({ input: process.stdin, crlfDelay: Infinity });
  const chunks: string[] = [];
  for await (const line of rl) chunks.push(line);
  return chunks.join("\n");
}

async function main(): Promise<void> {
  const argv = process.argv.slice(2);
  if (argv.length < 2) {
    process.stderr.write(
      "Usage: npx tsx template_fill.ts <template_file> <data_json|-> [output_file]\n",
    );
    process.exit(1);
  }

  const [templateFile, dataSource, outputFile] = argv;
  const templateText = readFileSync(templateFile, "utf-8");

  const dataStr =
    dataSource === "-" ? await readStdin() : readFileSync(dataSource, "utf-8");
  const data: Data = JSON.parse(dataStr);

  const result = fillTemplate(templateText, data);

  if (outputFile) {
    writeFileSync(outputFile, result, "utf-8");
  } else {
    process.stdout.write(result);
  }
}

// Run CLI only when invoked directly (not when imported as a module)
if (
  process.argv[1] &&
  (process.argv[1].endsWith("template_fill.ts") ||
    process.argv[1].endsWith("template_fill.js"))
) {
  main().catch(err => {
    process.stderr.write(`Error: ${err.message}\n`);
    process.exit(1);
  });
}
