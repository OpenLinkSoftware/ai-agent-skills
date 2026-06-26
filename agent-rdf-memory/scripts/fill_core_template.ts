/**
 * Fill core.ttl template placeholders with runtime values — TypeScript edition (Node.js ≥ 18, no npm deps).
 * Identical behavior to fill_core_template.py.
 *
 * Usage:
 *   npx tsx fill_core_template.ts --model "DeepSeek V4 Pro" --env "Claude Code" --output-root "/Users/kidehen/Documents/LLMs/DeepSeek/"
 *   LLM_MODEL="DeepSeek V4 Pro" AGENT_ENV="Claude Code" npx tsx fill_core_template.ts
 *   npx tsx fill_core_template.ts --model "..." --env "..." --out /tmp/core-filled.ttl
 *
 * Importable:
 *   import { fill } from "./fill_core_template.ts";
 *   const ttl = fill({ model: "DeepSeek V4 Pro", env: "Claude Code" });
 */

import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const MODEL_OUTPUT_ROOTS: Record<string, string> = {
  deepseek:        "/Users/kidehen/Documents/LLMs/DeepSeek/",
  deepseek_v4pro:  "/Users/kidehen/Documents/LLMs/DeepSeek/",
  claude:          "/Users/kidehen/Documents/LLMs/Claude Generated/",
  claude_sonnet:   "/Users/kidehen/Documents/LLMs/Claude Generated/",
  minimax:         "/Users/kidehen/Documents/LLMs/MiniMax Generated/",
  kimi:            "/Users/kidehen/Documents/LLMs/kimi/",
  kimi_k2:         "/Users/kidehen/Documents/LLMs/kimi/",
  grok:            "/Users/kidehen/Documents/LLMs/Grok/",
  gpt5:            "/Users/kidehen/Documents/LLMs/GPT5-Chat-Generated/",
  gpt5_chat:       "/Users/kidehen/Documents/LLMs/GPT5-Chat-Generated/",
  qwen:            "/Users/kidehen/Documents/LLMs/Alibaba Qwen/",
  glm:             "/Users/kidehen/Documents/LLMs/glm/",
  big_pickle:      "/Users/kidehen/Documents/LLMs/Big Pickle/",
};

function findCoreTtl(): string {
  // Resolve relative to this script: agent-rdf-memory/scripts/ → ../core.ttl
  const scriptDir = dirname(
    typeof __filename !== "undefined"
      ? __filename
      : fileURLToPath(import.meta.url),
  );
  const candidate = resolve(scriptDir, "..", "core.ttl");
  if (existsSync(candidate)) return candidate;

  // Fallback: search upward from cwd for agent-rdf-memory/core.ttl
  let dir = process.cwd();
  for (let i = 0; i < 10; i++) {
    const probe = join(dir, "agent-rdf-memory", "core.ttl");
    if (existsSync(probe)) return probe;
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }

  throw new Error(
    "Cannot locate agent-rdf-memory/core.ttl. " +
    "Run from the repo root or set CORE_TTL_PATH.",
  );
}

interface FillOptions {
  model: string;
  env: string;
  outputRoot?: string;
  corePath?: string;
}

export function fill(opts: FillOptions): string {
  const corePath = opts.corePath ?? process.env["CORE_TTL_PATH"] ?? findCoreTtl();
  let text = readFileSync(corePath, "utf-8");

  let outputRoot = opts.outputRoot;
  if (!outputRoot) {
    const modelKey = opts.model.toLowerCase().replace(/[\s-]/g, "_");
    outputRoot = MODEL_OUTPUT_ROOTS[modelKey];
  }
  if (!outputRoot) {
    // Last resort: extract the first schema:value from the template
    const m = text.match(/schema:value\s+"([^"]+)"/);
    if (m) outputRoot = m[1];
  }

  const subs: Record<string, string> = {
    "{LLM_MODEL}": opts.model,
    "{AGENT_ENV_NAME}": opts.env,
  };
  if (outputRoot) subs["{OUTPUT_PATH}"] = outputRoot;

  for (const [placeholder, value] of Object.entries(subs)) {
    text = text.replaceAll(placeholder, value);
  }
  return text;
}

function parseArgs(argv: string[]): {
  model?: string; env?: string; outputRoot?: string;
  corePath?: string; out?: string;
} {
  const result: Record<string, string | undefined> = {};
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--model": case "-m":       result["model"] = argv[++i]; break;
      case "--env": case "-e":         result["env"] = argv[++i]; break;
      case "--output-root": case "-o": result["outputRoot"] = argv[++i]; break;
      case "--core-path": case "-c":   result["corePath"] = argv[++i]; break;
      case "--out": case "-O":         result["out"] = argv[++i]; break;
    }
  }
  return result;
}

function cli(): void {
  const argv = process.argv.slice(2);
  const args = parseArgs(argv);

  const model = args["model"] ?? process.env["LLM_MODEL"];
  const env = args["env"] ?? process.env["AGENT_ENV"];
  const outputRoot = args["outputRoot"] ?? process.env["OUTPUT_ROOT"];
  const corePath = args["corePath"] ?? process.env["CORE_TTL_PATH"];
  const out = args["out"];

  if (!model) {
    process.stderr.write("Error: --model is required (or set LLM_MODEL env var)\n");
    process.exit(1);
  }
  if (!env) {
    process.stderr.write("Error: --env is required (or set AGENT_ENV env var)\n");
    process.exit(1);
  }

  const result = fill({ model, env, outputRoot, corePath });

  if (out) {
    writeFileSync(out, result, "utf-8");
    process.stderr.write(`Filled core.ttl written to ${out}\n`);
  } else {
    process.stdout.write(result);
  }
}

if (
  process.argv[1] &&
  (process.argv[1].endsWith("fill_core_template.ts") ||
    process.argv[1].endsWith("fill_core_template.js"))
) {
  cli();
}
