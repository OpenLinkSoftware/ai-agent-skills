# RDF Memory Protocol

## Step 0 — Load-Path Gate (before the file-read sequence)

Before executing the mandatory file-read sequence below, check the most recent
session TTL (newest file in `sessions/`) for `onto:usedFileReads` or
`onto:usedSparqlEndpoint`:

- **Found** → skip elicitation; load memory via the recorded method.
- **Absent** → STOP and elicit from the user:

  > "Memory loading preference for this session:\n>
  > (1) File reads  [default]\n>
  > (2) SPARQL — localhost:8890/sparql  [local Virtuoso]\n>
  > (3) SPARQL — other endpoint / other URI"

  Record the choice in the current session TTL as:
  - `:session onto:usedFileReads true .` (option 1)
  - `:session onto:usedSparqlEndpoint <{endpoint-url}> .` (option 2 or 3)

  Wait for the user's selection, then proceed to the load sequence below using
the chosen method. On all subsequent sessions where a recorded choice exists,
skip this elicitation silently and reuse the recorded method.

## Mandatory Retrieval Sequence

Before responding to the first user request in every session, load the RDF memory
from `/Users/kidehen/Documents/Management/Development/ai-agent-skills/agent-rdf-memory/`:

1. Read `core.ttl` for user identity and output-routing requirements.
2. Read `preferences.ttl` for the public operational-rule manifest.
3. If present, read `preferences.private.ttl` as a local-only private overlay;
   private overlay values take precedence over public defaults and must not be
   required for public reuse of the memory harness.
4. Read `ontology.ttl` for prompt-intent classes, retrieval policies, and
   ontology-routed context selection rules.
5. Read `index.ttl` for session pointers.
6. Determine the current prompt intent, then prefer SPARQL context selection
   against the configured endpoint to retrieve relevant preference topics,
   `rdfs:seeAlso` howto documents, and recent-session context.
7. Treat `{CNAME}` in SPARQL templates as the selected endpoint host or endpoint
   family, not as literal localhost. Determine the operating value from the
   private overlay when present, otherwise from public endpoint configuration or
   the current task context.
8. If SPARQL context selection is unavailable or incomplete, fall back to direct
   file reads and read the most recent file in `sessions/` for previous-session
   lessons.
9. When a rule applies, follow its `rdfs:seeAlso` link to the referenced
   `howto/*.ttl` file before acting.

Treat these RDF files as authoritative operational memory. Do not substitute a
summary, `MEMORY.md`, or assumptions for them. Re-read the relevant `howto` file
when a task triggers one of its rules.

The source design is documented in
`/Users/kidehen/Documents/Management/Development/ai-agent-skills/agent-rdf-memory/SESSION-START-HOOK.md`.
That document describes a Claude Code hook; this `AGENTS.md` is its Codex
equivalent instruction entry point.
