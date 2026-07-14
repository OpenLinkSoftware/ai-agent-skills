# RDF Memory Protocol

Before responding to the first user request in every session, load the RDF memory
from `/Users/kidehen/Documents/Management/Development/ai-agent-skills/agent-rdf-memory/`:

1. Read `core.ttl` for user identity and output-routing requirements.
2. Read `preferences.ttl` for the operational-rule manifest. When a rule applies,
   follow its `rdfs:seeAlso` link to the referenced `howto/*.ttl` file before
   acting.
3. Read `index.ttl` for session pointers.
4. Read the most recent file in `sessions/` for the previous session's lessons.

Treat these RDF files as authoritative operational memory. Do not substitute a
summary, `MEMORY.md`, or assumptions for them. Re-read the relevant `howto` file
when a task triggers one of its rules.

The source design is documented in
`/Users/kidehen/Documents/Management/Development/ai-agent-skills/agent-rdf-memory/SESSION-START-HOOK.md`.
That document describes a Claude Code hook; this `AGENTS.md` is its Codex
equivalent instruction entry point.
