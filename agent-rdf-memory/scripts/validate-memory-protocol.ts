/**
 * Validate Agent RDF Memory Protocol compliance from a session transcript.
 * TypeScript edition (Node.js ≥ 18, no npm deps).
 * Mirrors validate-memory-protocol.py — same checks, same exit codes.
 *
 * Usage:
 *   npx tsx validate-memory-protocol.ts transcript.jsonl
 *   npx tsx validate-memory-protocol.ts transcript.jsonl --verbose
 *   npx tsx validate-memory-protocol.ts transcript.jsonl --strict
 */

import { existsSync, readFileSync } from "node:fs";

const MEMORY_DIR = "agent-rdf-memory";

const CORE_FILES: Array<[string, string]> = [
  ["core.ttl",        "Protocol step 2: Read core.ttl"],
  ["preferences.ttl", "Protocol step 3: Read preferences.ttl"],
  ["index.ttl",       "Protocol step 4: Read index.ttl"],
];

const REF_SUBDIRS = ["howto/", "sessions/", "projects/", "entities/"];

// ── Event extraction ──────────────────────────────────────────────────────────

interface ToolUseEvent {
  event_type: "tool_use";
  name: string;
  input: Record<string, unknown>;
  line_number: number;
}
interface TextEvent {
  event_type: "assistant_text" | "user_text";
  text: string;
  line_number: number;
}
type Event = ToolUseEvent | TextEvent;

function extractEvents(transcriptPath: string): Event[] {
  const events: Event[] = [];
  const lines = readFileSync(transcriptPath, "utf-8").split("\n");

  for (let lineNum = 1; lineNum <= lines.length; lineNum++) {
    const line = lines[lineNum - 1].trim();
    if (!line) continue;

    let d: Record<string, unknown>;
    try {
      d = JSON.parse(line) as Record<string, unknown>;
    } catch {
      continue;
    }

    const recordType = d["type"] as string | undefined;

    if (recordType === "assistant") {
      const message = d["message"] as Record<string, unknown> | undefined;
      const content = (message?.["content"] ?? []) as unknown[];
      for (const block of content) {
        if (typeof block !== "object" || block === null) continue;
        const b = block as Record<string, unknown>;
        if (b["type"] === "tool_use") {
          events.push({
            event_type:  "tool_use",
            name:        (b["name"] as string) ?? "",
            input:       (b["input"] as Record<string, unknown>) ?? {},
            line_number: lineNum,
          });
        } else if (b["type"] === "text") {
          const text = ((b["text"] as string) ?? "").trim();
          if (text) events.push({ event_type: "assistant_text", text, line_number: lineNum });
        }
      }
    } else if (recordType === "user") {
      const message = d["message"] as Record<string, unknown> | undefined;
      const content = (message?.["content"] ?? []) as unknown[];
      for (const block of content) {
        if (typeof block !== "object" || block === null) continue;
        const b = block as Record<string, unknown>;
        if (b["type"] === "text") {
          const text = ((b["text"] as string) ?? "").trim();
          if (text) events.push({ event_type: "user_text", text, line_number: lineNum });
        }
      }
    }
  }

  return events;
}

// ── Path helper ───────────────────────────────────────────────────────────────

function pathUnderMemory(filePath: string): string | null {
  const marker = `${MEMORY_DIR}/`;
  let idx = filePath.indexOf(marker);
  if (idx === -1) {
    const markerWin = `${MEMORY_DIR}\\`;
    idx = filePath.indexOf(markerWin);
  }
  if (idx === -1) {
    const stripped = filePath.replace(/[/\\]+$/, "");
    return stripped.endsWith(MEMORY_DIR) ? "" : null;
  }
  return filePath.slice(idx + marker.length);
}

// ── Main validation ───────────────────────────────────────────────────────────

function validate(transcriptPath: string, verbose: boolean, strict: boolean): number {
  if (!existsSync(transcriptPath)) {
    console.log(`FAIL: transcript file not found: ${transcriptPath}`);
    return 1;
  }

  const events = extractEvents(transcriptPath);
  if (verbose) console.log(`Extracted ${events.length} events from transcript`);

  const failures: string[] = [];

  // ── Step 1: Directory listing ─────────────────────────────────────────────
  let dirListed = false;
  for (const ev of events) {
    if (ev.event_type !== "tool_use") continue;
    const e = ev as ToolUseEvent;
    if (e.name === "Bash") {
      const cmd = (e.input["command"] as string) ?? "";
      if (cmd.includes("ls") && cmd.includes(MEMORY_DIR)) {
        dirListed = true;
        if (verbose) {
          const snippet = cmd.slice(0, 120).replace(/\n/g, " ");
          console.log(`  [PASS] Step 1 (line ${e.line_number}): ls ${MEMORY_DIR}/ — ${snippet}`);
        }
        break;
      }
    }
  }
  if (!dirListed) {
    failures.push(
      `Protocol step 1: Did not list ${MEMORY_DIR}/ directory. ` +
      `No Bash "ls" command targeting ${MEMORY_DIR} found in transcript.`
    );
  }

  // ── Steps 2-4: Read core memory files ────────────────────────────────────
  const readFiles = new Set<string>();
  const readLineNumbers = new Map<string, number>();

  for (const ev of events) {
    if (ev.event_type !== "tool_use") continue;
    const e = ev as ToolUseEvent;
    if (e.name !== "Read") continue;
    const fp = (e.input["file_path"] as string) ?? "";
    const rel = pathUnderMemory(fp);
    if (rel !== null && rel !== "") {
      readFiles.add(rel);
      if (!readLineNumbers.has(rel)) readLineNumbers.set(rel, e.line_number);
    }
  }

  for (const [filename, label] of CORE_FILES) {
    const found = readFiles.has(filename) ||
      [...readFiles].some(r => r === filename || r.endsWith("/" + filename) || r.endsWith("\\" + filename));
    if (found) {
      if (verbose) {
        const matches = [...readFiles].filter(r => r === filename || r.endsWith("/" + filename));
        const line = readLineNumbers.get(matches[0] ?? filename) ?? "?";
        console.log(`  [PASS] ${label} (line ${line})`);
      }
    } else {
      failures.push(label);
    }
  }

  // ── Step 5: Follow references ─────────────────────────────────────────────
  const beyondCore: string[] = [];
  for (const rel of readFiles) {
    const base = rel.split("/").pop()?.split("\\").pop() ?? rel;
    if (["core.ttl", "preferences.ttl", "index.ttl"].includes(base)) continue;
    if (
      REF_SUBDIRS.some(sub => rel.startsWith(sub)) ||
      (rel.endsWith(".ttl") && !rel.includes("/") && !rel.includes("\\"))
    ) {
      beyondCore.push(rel);
    }
  }

  if (beyondCore.length) {
    if (verbose) {
      for (const rel of beyondCore) {
        const line = readLineNumbers.get(rel) ?? "?";
        console.log(`  [PASS] Step 5 (line ${line}): Followed reference → ${MEMORY_DIR}/${rel}`);
      }
    }
  } else {
    failures.push(
      `Protocol step 5: Did not follow index.ttl references. ` +
      `No additional files under ${MEMORY_DIR}/ read beyond core.ttl, preferences.ttl, index.ttl.`
    );
  }

  // ── Strict mode: timing check ─────────────────────────────────────────────
  if (strict) {
    const firstUserText = events.find(e => e.event_type === "user_text");
    if (firstUserText) {
      const firstResponse = events.find(
        e => e.event_type === "assistant_text" && e.line_number > firstUserText.line_number
      );
      if (firstResponse) {
        const protocolLines: number[] = [];

        for (const ev of events) {
          if (ev.event_type !== "tool_use") continue;
          const e = ev as ToolUseEvent;
          if (e.name === "Bash") {
            const cmd = (e.input["command"] as string) ?? "";
            if (cmd.includes("ls") && cmd.includes(MEMORY_DIR)) {
              protocolLines.push(e.line_number);
              break;
            }
          }
        }
        for (const ev of events) {
          if (ev.event_type !== "tool_use") continue;
          const e = ev as ToolUseEvent;
          if (e.name !== "Read") continue;
          const fp = (e.input["file_path"] as string) ?? "";
          if (pathUnderMemory(fp)) protocolLines.push(e.line_number);
        }

        if (protocolLines.length) {
          const lastRead = Math.max(...protocolLines);
          if (lastRead > firstResponse.line_number) {
            failures.push(
              `Strict mode: Last protocol read at line ${lastRead} occurred AFTER ` +
              `first substantive response at line ${firstResponse.line_number}. ` +
              `Protocol steps must execute before responding to the user.`
            );
          } else if (verbose) {
            console.log(
              `  [STRICT] All protocol reads (last at line ${lastRead}) ` +
              `precede first substantive response (line ${firstResponse.line_number})`
            );
          }
        } else if (verbose) {
          console.log("  [STRICT] No protocol reads found to check timing against");
        }
      } else if (verbose) {
        console.log("  [STRICT] No substantive assistant response found — skip timing check");
      }
    } else if (verbose) {
      console.log("  [STRICT] No user text prompt found — skip timing check");
    }
  }

  // ── Report ────────────────────────────────────────────────────────────────
  const toolUseCount = events.filter(e => e.event_type === "tool_use").length;

  if (failures.length) {
    console.log(`FAIL: ${failures.length} protocol step(s) not executed`);
    for (const item of failures) console.log(`  - ${item}`);
    if (verbose) {
      console.log(`\nAudited ${toolUseCount} tool calls across ${events.length} events in ${transcriptPath}`);
    }
    return 1;
  }

  console.log(
    `PASS: Agent RDF Memory Protocol executed — all 5 steps verified (${toolUseCount} tool calls audited)`
  );
  return 0;
}

// ── CLI ───────────────────────────────────────────────────────────────────────

function main(): number {
  const argv = process.argv.slice(2);
  if (!argv.length) {
    process.stderr.write(
      "Usage: npx tsx validate-memory-protocol.ts <transcript.jsonl> [--verbose] [--strict]\n"
    );
    return 1;
  }

  let transcriptPath: string | undefined;
  let verbose = false;
  let strict  = false;

  for (const arg of argv) {
    if (arg === "--verbose" || arg === "-v") verbose = true;
    else if (arg === "--strict") strict = true;
    else if (!arg.startsWith("--")) transcriptPath = arg;
  }

  if (!transcriptPath) {
    process.stderr.write("Error: transcript path required\n");
    return 1;
  }

  return validate(transcriptPath, verbose, strict);
}

if (
  process.argv[1] &&
  (process.argv[1].endsWith("validate-memory-protocol.ts") ||
    process.argv[1].endsWith("validate-memory-protocol.js"))
) {
  process.exit(main());
}
