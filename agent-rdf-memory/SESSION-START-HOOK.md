# Automatic RDF Memory Loading via SessionStart Hook

## How It Works

```mermaid
sequenceDiagram
    actor User
    participant CC as Claude Code Harness
    participant Hook as SessionStart Hook<br/>(Python script)
    participant FS as agent-rdf-memory/<br/>(filesystem)
    participant Model as Claude Agent<br/>(LLM context window)

    User->>CC: Opens new session in project directory
    CC->>Hook: Fires SessionStart event
    Hook->>FS: Read core.ttl
    FS-->>Hook: User identity, LLM output paths
    Hook->>FS: Read preferences.ttl
    FS-->>Hook: Lean manifest — 36 HowToStep entries with rdfs:seeAlso to howto/ docs
    Hook->>FS: Read index.ttl
    FS-->>Hook: Session index + file pointers
    Hook->>FS: Read sessions/*.ttl (most recent)
    FS-->>Hook: Lessons from last recorded session
    Hook-->>CC: JSON { hookSpecificOutput: { additionalContext: "..." } }
    CC->>Model: Injects all four files as additionalContext
    Note over Model: Agent starts with full operational<br/>memory loaded — before first user turn
    User->>Model: First message / task request
    Model-->>User: Response grounded in RDF memory<br/>(correct paths, rules, templates)
```

## Problem

Claude Code agents in this project were ignoring the authoritative `agent-rdf-memory/` system and instead operating from the auto-injected `MEMORY.md`. This caused recurring failures: wrong output directories, missed harness contract requirements, and template reuse rules being skipped — documented across multiple sessions (DeepSeek V4 Pro, Claude Sonnet 4.6).

Click [HERE](https://mermaid.live/edit#pako:eNp1VMtu2zAQ_JUFT0kr25KfsVAEKBQYaZFHEbWXwhdGWtlsJFIlqTqqYaAf0S_sl3QpGoabuL5ZnJndnR1yyzKVI4uZwe8NygyvBF9pXi0l0I9nVmn4YlD7_zXXVmSi5tJCkgA3kJS8yRESEoFrriUa8xp6rdSTA6d0KpRMLZ11H9896sHl2afWrpUEk2lR2_PX9EXqyHyF0vZ0XvQqrJRuB55ciBJNayxWJ5i31FZ51OZ7p-F5Nze3kClp8dnCRshcbYjvFdy8vcvLJInhvkZpQOIGjO8dhIRaq2-YWciFRmdQ62lJQiQ3VQwLOnkxLv6g0h7oMARdpDE8IM-pDY19a0t_ukh7Bx3XCYicmMK2AbieVWPrxtKUdm1Oy9UaC9Rul-a0ajQjzuazSi3WoGrU3FKbvATdkJenRckhfD4tlx6cIQi8BbcRqJUgb_V_1PZmmsEbJwlnlTIWyEwa9Px1gRtCExgKrSoouYcqneNB6KjKfnEf0_s72MKaPqU1ZqIQ2X3nXExfeZ4LP3LiExDDkvX7_SWDHeyOttnlJ4YP0u2bIliWUKhGdyOaLpQvlTz5TlkE9YOWt1foggfGJcFQ3OwaiobEjszvUumTDaXibrg_v37DIxaUDiqoaezGxcE2-t-c7kssOkhFhtBNgQFYbp7IKLrVZt9VB3QGOaLbhKnJVoSVVo10BSnbD1cL8F34a0I-u5D7vAU-IQHQbatLbtGcs4BVqCsucnpDtq7Oktk1VrhkztQcC96UdsmWckdQ3liVtjJjsdUNBqypc1LZPzksLnhp6CtdXRZv2TOLe_P-fBoOx7OLMIzG0XQ2CljL4vGoP5rMw3A0DWfjYRTOdgH7qRQpRP0omg2j-TAMp5Ph5GIy7eS-doe-Jg27Wh9qIe1P6Vv_BnZPISGQ3NAJmWJZPL0YB2yl3XyOv_sLcXq6ew) for live diagram.

## Solution

A `SessionStart` hook configured in `.claude/settings.json` reads the RDF memory files at the start of every new session and injects them as `additionalContext` into the model — no explicit instruction needed.

## What the Hook Does

On every session start, the hook runs a Python script that reads:

1. `agent-rdf-memory/core.ttl` — user identity, output path routing per LLM
2. `agent-rdf-memory/preferences.ttl` — lean manifest of all 36 operational rules (HowToSteps). Each step carries only `schema:position`, `schema:name`, `onto:hasTrigger` (where applicable), and `rdfs:seeAlso <howto/X.ttl>`. The full step text lives in 9 thematic howto docs under `agent-rdf-memory/howto/`, grouped by topic:
   - `session-governance.ttl` — approval, memory protocol, git, no-fabricated-URLs, curl auth, secret redaction, prompt recording
   - `artifact-routing.ttl` — output dirs, GPT-5 dirs, mashup/meshup, default output root
   - `skill-invocation.ttl` — skill chain, KG query mode, ZIP repackage, retrieval tool order
   - `infographic-authoring.ttl` — attribution, dark mode CSS, KG Explorer reuse, template selection
   - `harness-contract-compliance.ttl` — harness IDs, footer labels, SPARQL format, ERE workaround
   - `kg-explorer-ui-patterns.ttl` — nav placement, collapsed start, master close, orphans, toolbar groups, settings panel
   - `kg-explorer-d3-patterns.ttl` — simulation lifecycle, click guard, kgData regex
   - `rdf-document-authoring.ttl` — document entity declaration, schema:about usage
   - `agent-identity.ttl` — whoami format, Stripe sandbox card
3. `agent-rdf-memory/index.ttl` — session index with pointers to all past session files
4. The most recent session `.ttl` file — lessons learned from the last recorded session

The combined content is returned as `additionalContext`, making it part of the model's context window from the first turn. Agents follow `rdfs:seeAlso` into the relevant howto doc on demand for full step details.


## SPARQL-Preferred Context Selection

The hook remains fallback-safe: direct file reads are still mandatory enough to
bootstrap a session. When a Virtuoso endpoint is available, the preferred path is
to use SPARQL after prompt-intent analysis:

1. Load the minimum memory contract (`core.ttl`, `ontology.ttl`,
   public `preferences.ttl`, optional private `preferences.private.ttl`,
   `index.ttl`).
2. Classify the user prompt into an ontology intent such as
   `:VirtuosoSparqlTroubleshooting`, `:RdfAuthoringTask`,
   `:IdentityWebIdTask`, `:ArtifactRoutingTask`, `:KgExplorerTask`,
   `:MemoryProtocolTask`, or `:SkillWorkflowTask`.
3. Query `ontology.ttl` for `:routesToTopic`, `:requiresHowTo`,
   `:optionalHowTo`, `:retrievalPolicy`, `:preferredContextSource`, and
   `:requiresRecentSession`.
4. Query `preferences.ttl`, the selected `howto/*.ttl` graph(s), and
   `index.ttl`/session graphs for the compact context pack needed for that
   prompt.
5. If the endpoint path fails or returns insufficient context, fall back to the
   existing file-based reads.

Private overlays take precedence over public defaults when the same intent or
policy is asserted in both graphs. The public `preferences.private.example.ttl`
file documents the overlay shape without publishing private values.

`{CNAME}` is a template placeholder in reusable HTTPS SPARQL endpoint examples.
Bind it at runtime from the private overlay when present, otherwise from public
endpoint configuration or the current task context. The general pattern is
`https://{CNAME}/sparql`, including localhost when HTTPS is selected. The URL
`http://localhost:8890/sparql` is a local-only Virtuoso endpoint pattern; do not
rewrite it as `http://{CNAME}:8890/sparql` for remote targets. Public harness
files should not encode personal endpoint order, private paths, credentials, or
identity-specific preferences; those belong in gitignored `preferences.private.ttl`.

Named graph IRIs are discovered, not guessed. For local Virtuoso RDF Import DET
loads, graph IRIs commonly use `urn:dav:/DAV/home/{USER}/rdf-import-test/{file}`
while entity IRIs inside those graphs use `http:/DAV/home/{USER}/rdf-import-test/{file}#...`.
Use the SAMPLE-by-type graph discovery query before generating context-selector
URLs for a newly loaded corpus.

Example first-stage selector:

```sparql
PREFIX onto:   <http:/DAV/home/{USER}/rdf-import-test/ontology.ttl#>
PREFIX schema: <http://schema.org/>

SELECT ?intent ?topic ?howto ?optionalHowto ?policy ?source ?recentRequired
WHERE {
  GRAPH <urn:dav:/DAV/home/{USER}/rdf-import-test/ontology.ttl> {
    VALUES ?intent { onto:VirtuosoSparqlTroubleshooting }
    OPTIONAL { ?intent onto:routesToTopic ?topic }
    OPTIONAL { ?intent onto:requiresHowTo ?howto }
    OPTIONAL { ?intent onto:optionalHowTo ?optionalHowto }
    OPTIONAL { ?intent onto:retrievalPolicy ?policy }
    OPTIONAL { ?intent onto:preferredContextSource ?source }
    OPTIONAL { ?intent onto:requiresRecentSession ?recentRequired }
  }
}
```

## Files Changed

| File | Change |
|------|--------|
| `.claude/settings.json` | Created — contains the `SessionStart` hook |

## Activation

The hook is project-scoped and fires automatically for any new Claude Code session opened in this directory. To reload config in an already-running session, open `/hooks` in the Claude Code UI.

## Why Not CLAUDE.md or MEMORY.md?

- `CLAUDE.md` contains the *instruction* to read `agent-rdf-memory/` but relies on the agent following it — which has proven unreliable across multiple LLMs.
- `MEMORY.md` is auto-injected but only contains a summary index, not the operational rules.
- The hook enforces the protocol structurally: the memory files are loaded before the agent generates any response, regardless of what it "remembers" to do.
