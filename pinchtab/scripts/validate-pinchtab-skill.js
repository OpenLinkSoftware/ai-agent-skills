#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const skillDir = path.resolve(__dirname, "..");
const repoDir = path.resolve(skillDir, "..");
const checks = [];

function check(name, ok, detail = "") {
  checks.push({ name, ok, detail });
}

function read(rel) {
  return fs.readFileSync(path.join(skillDir, rel), "utf8");
}

function exists(rel) {
  return fs.existsSync(path.join(skillDir, rel));
}

const skill = read("SKILL.md");
const fm = skill.match(/^---\n([\s\S]*?)\n---/);
check("SKILL.md has YAML frontmatter", Boolean(fm));
check("frontmatter declares pinchtab", /^name:\s*pinchtab\s*$/m.test(fm ? fm[1] : ""));
check("frontmatter has description", /^description:\s*".{80,1024}"\s*$/m.test(fm ? fm[1] : ""));
check("SKILL.md references article collection workflow", skill.includes("references/article-collection.md"));

const required = [
  "TRUST.md",
  "agents/openai.yaml",
  "references/api.md",
  "references/commands.md",
  "references/env.md",
  "references/agent-optimization.md",
  "references/profiles.md",
  "references/mcp.md",
  "references/article-collection.md",
];
for (const rel of required) check(`${rel} exists`, exists(rel));

const openai = read("agents/openai.yaml");
check("openai.yaml names the skill", openai.includes('display_name: "PinchTab"'));
check("openai.yaml default prompt invokes $pinchtab", openai.includes("$pinchtab"));
check("openai.yaml has brand color", /brand_color:\s*"#[0-9A-Fa-f]{6}"/.test(openai));

check("no .DS_Store in skill package", !exists(".DS_Store"));

const help = spawnSync("pinchtab", ["--help"], { encoding: "utf8" });
check("pinchtab CLI is runnable", help.status === 0, (help.stderr || help.stdout || "").trim());

const codexSkills = path.join(require("os").homedir(), ".codex", "skills");
try {
  const stat = fs.lstatSync(codexSkills);
  if (stat.isSymbolicLink()) {
    const target = fs.realpathSync(codexSkills);
    check("Codex skills registration points at repo", target === repoDir, `${codexSkills} -> ${target}`);
  } else {
    check("Codex skills registration points at repo", false, `${codexSkills} is not a symlink`);
  }
} catch (error) {
  check("Codex skills registration points at repo", false, error.message);
}

let failed = 0;
for (const item of checks) {
  if (item.ok) {
    console.log(`PASS ${item.name}`);
  } else {
    failed += 1;
    console.error(`FAIL ${item.name}${item.detail ? `: ${item.detail}` : ""}`);
  }
}

process.exit(failed === 0 ? 0 : 1);
