# AGENTS.md

This file provides guidance to AI agents when working with code in this repository.

## MANDATORY: Agent RDF Memory Protocol (Execute Before Every Task)

**This instruction takes precedence over all other guidance in this file.**

Before responding to any user request, you MUST execute this retrieval sequence:

1. **List** `agent-rdf-memory/` and all subfolders (`sessions/`, `projects/`, `entities/`)
2. **Read** `agent-rdf-memory/core.ttl`
3. **Read** `agent-rdf-memory/preferences.ttl`
4. **Read** `agent-rdf-memory/index.ttl`
5. **Follow** `index.ttl` references to any relevant session, project, or entity files
6. **Reason** over the loaded Turtle content before proceeding

After completing any meaningful task:

- Generate valid RDF-Turtle and write to the appropriate file in `agent-rdf-memory/` (see folder structure and rules below)
- Never store memory in context, comments, or any other location

If `agent-rdf-memory/` is inaccessible, report it as a critical error immediately.

### Precedence Hierarchy

1. `preferences.ttl` — the queryable source of truth for operational preferences
2. This file (`AGENTS.md`) — prose reference and policy
3. Unstated defaults — lowest priority

When `preferences.ttl` contradicts prose in this file, `preferences.ttl` wins.

---

## No Fabricated URLs

**Never fabricate, guess, construct, or hallucinate any URL.** This prohibition is absolute and covers every URL type: encoded live-editor links (pako, base64), API endpoints, documentation pages, download links, image URLs, resolver links, and any other URI.

A URL is only acceptable if produced by one of these methods:

1. **Verbatim** — copied exactly from a source the user provided
2. **Computed with a tool** — e.g., a Python script for pako encoding, `curl` for endpoint discovery
3. **Validated pattern** — constructed from a known, documented pattern where every path component is verified

If none of these apply, **omit the URL and ask the user for the correct one.** A fabricated URL that renders a blank page, a 404, or wrong content is worse than no URL at all. After computing an encoded URL with a tool, verify it actually works before including it in any document.

---

## Memory Folder (Source of Truth)

All memory operations MUST use this folder and nothing else:

`agent-rdf-memory/`

Never store memory in context, comments, separate files, or any other location.

### Folder Structure

- `core.ttl`          → Long-term knowledge, user preferences, core facts
- `preferences.ttl`   → Standing instructions encoded as `schema:HowTo` with `schema:HowToStep` entries. The queryable behavioral contract.
- `ontology.ttl`      → Custom vocabulary and prefixes (you may edit this)
- `index.ttl`         → Summary index of sessions and files
- `sessions/YYYY-MM-DD-{llm-id}-{agent-env}.ttl` → Episodic memory (one per day, LLM, and agent environment)
- `projects/<name>.ttl`     → Project-specific knowledge
- `entities/*.ttl`          → People, tools, preferences, etc.

### Session File Naming

Session files in `sessions/` MUST follow this naming pattern:

```
YYYY-MM-DD-{llm-id}-{agent-env}.ttl
```

| Component | Rule | Examples |
|-----------|------|----------|
| `YYYY-MM-DD` | ISO date of the session | `2026-05-27` |
| `{llm-id}` | Model identifier, lowercase, underscores for spaces/versions | `qwen3_6_plus`, `claude_opus_4_7`, `deepseek_v4pro`, `gpt_4o` |
| `{agent-env}` | Agent/runtime environment, lowercase | `claude_code`, `opencode`, `cowork` |

**Rules:**

1. If multiple sessions occur on the same day with the same LLM+agent combination, append a numeric suffix: `YYYY-MM-DD-{llm-id}-{agent-env}-N.ttl` (e.g., `2026-05-27-qwen3_6_plus-opencode-2.ttl`).
2. The LLM ID and agent environment MUST match the values used in generated artifact filenames for cross-referencing.
3. If the agent environment cannot be determined, omit it and use: `YYYY-MM-DD-{llm-id}.ttl`.

### RDF Serialization Format

Session memory defaults to **Turtle (.ttl)**. Before writing any session file, ask the user which RDF format they prefer:

> "Session memory format: (1) Turtle (.ttl) — default, (2) JSON-LD (.jsonld), (3) RDF/XML (.rdf), (4) N-Triples (.nt), or (5) N-Quads (.nq)?"

If the user has already specified a preference in a previous session, reuse that format. All folder structure filename examples show `.ttl` as the default — adjust the extension to match the chosen format.

### Retrieval Rule (Before Any Task That Needs Context)

You MUST:

1. Use `list_directory` (or `ls`) on `agent-rdf-memory/` and relevant subfolders.
2. Use `read_file` to load:
   - `agent-rdf-memory/core.ttl` (always)
   - `agent-rdf-memory/preferences.ttl` (always — this is the queryable behavioral contract)
   - `agent-rdf-memory/index.ttl`
   - Any relevant session/project/entity files
3. Reason over the loaded Turtle content before proceeding with the task.

### Storage Rule (After Completing Any Meaningful Task or Output)

You MUST:

1. Generate valid RDF-Turtle using `http://schema.org` and other relevant ontologies as applicable.
2. Use `write_file` or `edit_file` to write the new triples to the appropriate file(s) in `agent-rdf-memory/`.
3. Always include:
   - Proper prefixes (`@prefix schema: <http://schema.org/> .` etc.)
   - Timestamps (`schema:dateCreated`, `schema:dateModified`) — both MUST be set to the current time (`now()`) in ISO 8601 UTC format when creating a new file. For updates to existing files, update only `schema:dateModified`.
   - Unique relative hash-based IRIs leveraging namespace declaration: `@prefix : <#>;`
   - When referencing any skill from this repo (kg-generator, rdf-infographic-skill, document-to-kg-skill, etc.), use its canonical IRI: `https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/{skill-name}#this`. Never use local hash IRIs for skill entities.
   - Never use `file:` scheme IRIs (e.g., `<file:///path/to/file>`) for subjects or objects. Use Turtle relative IRIs with `<../>` notation for local file references (e.g., `<../../../../../LLMs/DeepSeek/rdf/file.ttl>`). Entity IRIs must be hash-based, not filesystem paths.
   - All characters in Turtle IRIs that are not valid IRI characters MUST be percent-encoded. Spaces in directory names (e.g., `Alibaba Qwen`) MUST be written as `%20` (e.g., `<../../../../../LLMs/Alibaba%20Qwen/rdf/file.ttl>`). Use `ls -ltha {relative-path}` to verify the relative path resolves correctly from the session file's directory.
   - Clear description of outcome, decisions, and inferred user preferences
   - **Self-describing document entity**: Every `.ttl` file MUST declare `: a schema:CreativeWork ; schema:about {primaryTopic} .` as its first triple (after prefixes). The `schema:about` points to the primary entity described in the file (e.g., `:sessionIndex` for `index.ttl`). This makes every memory file a queryable, first-class CreativeWork.

### Tool Preference

- Prefer `read_file`, `write_file`, `edit_file`, and `list_directory` for memory.
- Never attempt to use MCP, external databases, or vector stores unless explicitly allowed.

### Startup Injection (OpenCode / Runtime Config)

For environments using OpenCode or equivalent runtime configuration, add the mandatory retrieval sequence to `~/.config/opencode/opencode.jsonc` under `instructions.startup` so the memory protocol is injected into the system prompt on every session initialization. This creates defense in depth: even if the LLM skips the file-reading preamble, the runtime instruction enforces it.

### Enforcement

If you cannot access or write to `agent-rdf-memory/`, you must immediately report it as a critical error. This policy takes precedence over all other instructions regarding memory.

### Memory Write Trigger Phrases

Any user message containing one or more of these phrases is an `onto:triggerPreferencesUpdate` event. You MUST write to `agent-rdf-memory/` as valid Turtle cross-referenced from `preferences.ttl` — **never to the flat markdown system at `.claude/projects/…/memory/`**.

Trigger phrases (case-insensitive, partial match sufficient):

- "to be noted in memory"
- "remember this" / "please remember"
- "going forward" (when followed by a behavioral rule)
- "add to preferences" / "note in preferences"
- "record this" / "store this"
- "don't do that again" / "never do that again"
- "always do X" / "never do X" (when X describes agent behavior)
- "that's a rule" / "make that a rule"

**Write path:** new howto step in `preferences.ttl` (with `schema:position` incremented) **+** a companion `howto/<topic>.ttl` if the rule warrants a full HowTo document. The flat markdown memory under `.claude/projects/` is a secondary index only — it must never be the primary or sole write target for behavioral rules.

---

## What This Repository Is

A collection of reusable AI agent skills, each packaged as a directory + ZIP bundle. Skills encapsulate domain-specific execution knowledge for querying semantic web data sources, knowledge graphs, and databases — primarily in the OpenLink/Virtuoso/URIBurner ecosystem.

## Repository Structure

Each skill lives in its own directory with a corresponding `.zip` bundle:

```
<skill-name>/         # Skill source directory
  SKILL.md            # Primary skill definition — capabilities, routing rules, query templates
  README.md           # (optional) Quick-start guide
  CHANGELOG.md        # (optional) Version history
  examples/           # (optional) Sample queries and worked examples
  references/         # (optional) Query templates, protocol routing, extraction rules
  templates/          # (optional) HTML output templates
<skill-name>.zip      # Distributable bundle
```

**No build system, package manager, or test runner.** Skills are loaded directly into AI agent environments as-is.

## Skill Architecture

### SKILL.md Structure

Every SKILL.md defines:

1. **Metadata** — name, version, description
2. **Execution routing** (priority order): direct curl → URIBurner REST functions → MCP tools → chatPromptComplete (LLM-mediated) → OPAL Agent
3. **Query templates** — numbered (P1–P4, T1–T7, etc.) matched to trigger phrases with substitutable placeholders
4. **Output formats** — JSON, Markdown tables, or styled HTML pages

### Protocol Functions Referenced by Skills

- `Demo.demo.execute_spasql_query` — SPASQL execution (SQL + SPARQL hybrid)
- `UB.DBA.sparqlQuery` — Pure SPARQL against URIBurner
- `DB.DBA.graphqlQuery` — GraphQL against Virtuoso
- MCP tools (23 for virtuoso-support-agent, others for uriburner-opal-agent-skills)

### Authoritative Function/Procedure References

When adding or updating function references in any skill, consult these OpenAPI specs first:

- **Chat API:** https://linkeddata.uriburner.com/chat/api/openapi.yaml
- **Functions/Procedures API:** https://linkeddata.uriburner.com/chat/functions/openapi.yaml

### Key Routing Principle

Skills specify a fallback hierarchy. If a user explicitly names a protocol (e.g., "use MCP"), honor that preference over defaults.

## Skills in This Repo

| Skill | Purpose |
|-------|---------|
| `dbpedia-query-skill` | Natural language → SPARQL → DBpedia knowledge graph |
| `wikidata-query-skill` | Natural language → SPARQL → Wikidata knowledge base |
| `data-twingler` | SQL/SPARQL/SPASQL/SPARQL-FED/GraphQL against live data spaces |
| `opml-rss-reader` | Explore OPML/RSS/Atom feeds via predefined SPASQL queries |
| `rss-feed-generator` | Generate RSS 2.0 / Atom 1.0 feeds from pages lacking native feeds |
| `virtuoso-support-agent` | Technical support + RDF Views generation for OpenLink Virtuoso |
| `uriburner-opal-agent-skills` | URIBurner toolkit with SPARQL Agent 121 + OPAL routing |
| `s3-query-skill` | Client-side S3 API access — query Parquet/CSV/JSON in place via DuckDB httpfs, plus list/get/put via AWS CLI/boto3/rclone, against AWS S3 and S3-compatible endpoints (Hugging Face Storage Buckets, R2, MinIO, etc.) |

## Adding or Updating a Skill

1. Create or edit the skill directory and its `SKILL.md`
2. Update version metadata and CHANGELOG.md if applicable
3. **Always repackage the ZIP after any change** — delete first, then recreate:
   `rm <skill-name>.zip && zip -r <skill-name>.zip <skill-name>/ -x "*.DS_Store"`
   Deleting first is required: `zip -r` on an existing archive updates entries but does not remove deleted files. Always exclude `.DS_Store` with `-x "*.DS_Store"`.
   - Note: the RSS feed generator bundle is named `rss-feed-generator-skill.zip` (not `rss-feed-generator.zip`)
4. The root `README.md` intentionally stays minimal — detailed docs belong in each skill's `SKILL.md`

## Loading a Skill

Per the root README:

1. Ask the AI agent environment to load the skill bundle from its path: `file://<absolute-path>/<skill-name>.zip` or the directory path
2. Test using the usage examples in the skill's `SKILL.md`
3. Optionally schedule for automated runs

## Key People Reference (for KG generation)

| Person | LinkedIn | X/Twitter | Substack | Role |
|--------|----------|------------|----------|------|
| Kingsley Uyi Idehen | https://www.linkedin.com/in/kidehen#this | https://x.com/kidehen | https://substack.com/@kidehen | Founder & CEO of OpenLink Software, Virtuoso creator, Semantic Web pioneer |
| Veronika Heimsbakk | https://www.linkedin.com/in/vheimsbakk | — | https://veronahe.substack.com/ | Knowledge Graph Specialist, Author of SHACL for the Practitioner |

## Anti-Drift Protocol

Skill definitions are the build contract — not launch instructions. Drift happens when the contract is read once at invocation and then operated from memory. These rules prevent that.

### The Three Rules

1. **Re-read before build, not just before start.** Before writing each deliverable (HTML body, JS block, CSS, RDF section, configuration file), re-open the skill's relevant section — not the whole file, the specific section covering what you're about to write.
2. **Gate-first.** When a skill defines a verification checklist or compliance audit, write the automated check *before* writing the output. Build to make it pass. A gate that runs only after delivery is a post-mortem, not a gate.
3. **Section-by-section, not batch.** Generate one deliverable section → validate against its specific gates → fix → next section. A batch approach hides failures until everything is "done."

### When a Skill Is Loaded

- Identify every verification gate defined in the skill (checklists, audits, post-generation checks, harness contracts).
- Before producing any output, confirm the gates are understood and the verification script/process is ready.
- If a skill defines a "GATE: 0 failures required" or equivalent, treat it as a blocking deliverable — do not hand off to the user with known failures.

### When Multiple Skills Are Used Together

- Each skill's contract applies independently. Satisfying one skill's gates does not satisfy another's.
- When skills have overlapping requirements (e.g., both specify entity hyperlink patterns), the more specific skill takes precedence.
- When skills delegate to each other (e.g., kg-generator → rdf-infographic-skill for HTML/MD), the delegating skill's harness mode contract applies alongside the receiving skill's contract.

### Re-Read Trigger Phrases

Any time a skill defines numbered requirements, checklists, or named contracts (e.g., "Harness Mode," "Compliance Self-Audit," "Post-Generation Checklist"), re-read that section before writing the corresponding output. These are not reference material — they are the build specification.

## Critical Context

- **Navigation panel spec**: "movable, resizable, collapsible, visible in a closed compact header-bar state by default"
- **Entity hyperlinks**: ALL entity text (FAQ Q&A, glossary terms/defs, HowTo title/steps) must be hyperlinked to KG entity IRIs via resolver pattern `linkeddata.uriburner.com/describe/?url={url-encoded-iri}`
- **SPARQL accordion**: Use numbered accordion pattern with `accordion-num`, `accordion-toggle` (▼ indicator rotating 180°), syntax-highlighted `sparql-code`, and `sparql-run-btn` with play icon
- **Person IRIs**: LinkedIn first, then hash fallback (#this suffix for blank nodes)
- **Platinum Layer**: Kingsley's extension to the medallion architecture — using hyperlinks as stable standardized identifiers to turn the knowledge graph into a Semantic Web

## Skills Attribution Contract (rdf-infographic-skill + kg-generator)

Every generated HTML infographic footer MUST include a skills attribution line using the exact `<p>` prose format — NOT chip-style `<div>` elements:

```html
<!-- Single skill -->
<p style="margin-top:14px;color:var(--muted);font-size:0.86rem">
  Generated using <a href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/rdf-infographic-skill" target="_blank" rel="noopener noreferrer">rdf-infographic-skill</a>
</p>

<!-- Multiple skills -->
<p style="margin-top:14px;color:var(--muted);font-size:0.86rem">
  Generated using
  <a href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/kg-generator" target="_blank" rel="noopener noreferrer">kg-generator</a>,
  <a href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/rdf-infographic-skill" target="_blank" rel="noopener noreferrer">rdf-infographic-skill</a>
  via <a href="{llm-url}" target="_blank" rel="noopener noreferrer">{LLM Name}</a>.
  Linked Data resolved via <a href="https://linkeddata.uriburner.com/" target="_blank" rel="noopener noreferrer">URIBurner</a>
  (<a href="https://virtuoso.openlinksw.com/" target="_blank" rel="noopener noreferrer">Virtuoso</a>-backed).
</p>
```

### Attribution Rules

1. **Use `<p>` prose format** — never `<div class="skills-attribution">` with chip/button styling
2. **All tool/product names MUST be hyperlinked to their canonical homepages** — URIBurner → `https://linkeddata.uriburner.com/`, Virtuoso → `https://virtuoso.openlinksw.com/`, skill names → GitHub repo URLs, LLM → product URL
3. **Do NOT use resolver URLs for tool attribution** — the resolver (`linkeddata.uriburner.com/describe/?url=...`) is for semantic KG entities only, not product/tool credits
4. **Singular vs plural**: "Generated using {skill}" (singular) vs "Generated using {skill1}, {skill2}" (plural)
5. **Embedded JSON-LD `WebPage`** MUST include `prov:wasGeneratedBy` with canonical skill IRIs using `#this` suffix, `schema:name`, `schema:url` (GitHub without `#this`), and `schema:description`
6. **Canonical skill IRI pattern**: `https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/{skill-name}#this`
7. **No document-local hash IRIs** for skill entities (e.g., never `{source-url}#kgGeneratorSkill`)
8. **Remove unused `.skills-attribution` CSS** if not using the chip format

## RDF Language Tagging Contract

- **Turtle**: All string literals MUST carry `@en` language tags (e.g., `"text"@en`).
- **JSON-LD**: The `@context` MUST include `"@language": "en"` so all string values inherit the language tag implicitly.
- Both serializations MUST be semantically equivalent — untagged JSON-LD strings are a contract violation.

## Memory Note

**Never proactively fix or modify other documents without the user's express request and approval.** If the user asks about a specific document, ask for clarification or approval before making any changes. Focus only on the current task unless explicitly directed otherwise.
