# Flow Report Template — Protocol/Delegation QA Reporting

Reusable structure for writing up a UCP and/or ACP (or other protocol) flow
test as a standalone Markdown report, illustrated with Mermaid sequence
diagrams. Originated 2026-09-14 from
`ucp-acp-flow-reports-obo-food-bookmark-claude_sonnet_5-1.md` (the agent-OBO-
principal QA round) — reuse this structure for future flow reports rather
than inventing a new layout each time. Copy the skeleton below and fill in
the bracketed placeholders; delete any section that genuinely doesn't apply
rather than leaving it as dead scaffolding.

## Why this structure

- **Header block** gives a reader everything needed to reproduce the test
  without reading the body: date, exact resource/endpoint, exact identity
  presented, and the one-line scope/boundary of what was (and wasn't)
  attempted — critical for anything touching payment/purchase flows, so a
  reader never has to wonder "did this spend real money?"
- **"Result" block first, sequence diagram second** — lead with the ground
  truth (raw HTTP status, raw JSON, raw response headers) before the
  narrative diagram, so the diagram is visibly *derived from* the evidence,
  not a substitute for it.
- **"What actually happened" vs "Contrast" diagrams** — always pair the
  observed sequence with at least one contrasting diagram showing what the
  *documented/expected* flow looks like for a different outcome (e.g. the
  unentitled-buyer path, or a different route/protocol choice). This is what
  makes the report legible to someone who wasn't there: it shows not just
  what happened, but where the branch point was and what the alternative
  would have looked like.
- **Cross-client/cross-surface agreement table** — when more than one
  implementation or code path was tested against the same scenario, a
  compact table showing they agree (or don't) is worth more than restating
  each result in prose three times.
- **Fixes-applied section, clearly separated** — any bugs fixed or corrections
  made *along the way* while producing the report go in their own section at
  the end, explicitly marked as orthogonal to the finding being reported.
  Never bury a tooling fix inside the narrative of a protocol/behavior
  finding — a reader trying to cite the finding later shouldn't have to
  untangle which parts are "what the server does" versus "what was broken in
  our own test client."

## Skeleton

```markdown
# [Flow Name] Report — [One-line scenario description]

**Date:** [YYYY-MM-DD]
**Resource / Endpoint:** `[exact URL or endpoint]`
**Identity presented:** [role] — `[exact WebID/credential identifier]`
**Delegation / auth asserted:** [header/token/etc, exact value or pattern]
**Scope:** [explicit boundary — e.g. "no new purchase was attempted or
completed at any point" — mandatory whenever payment/purchase flows are
anywhere near the scenario]

[One paragraph: what QA round or prior finding this closes out / continues,
with a link/reference to the prior report if one exists.]

---

## 1. [Flow/Client Name] Report

**Client:** [tool/script/skill name and exact invocation or command pattern]

**Result:**
\```[json|text]
[raw output — the actual status code, JSON, or response headers observed]
\```

[One paragraph interpreting the raw result in plain language.]

### Sequence — what actually happened

\```mermaid
sequenceDiagram
    participant [Actor1]
    participant [Actor2]
    [...]

    rect rgb(230,255,230)
    note over [Actor1],[Actor2]: [label the step/phase that mattered]
    [Actor1]->>[Actor2]: [exact request/action]
    [Actor2]-->>[Actor1]: [exact response]
    end

    note over [Actor1],[Actor2]: [steps that were NEVER REACHED, and why —\
    this line is often the most important one in the diagram]
\```

### Contrast — what this flow looks like for [the alternative outcome]

\```mermaid
sequenceDiagram
    [...]
\```
*(Shown for contrast only — not exercised in this test.)*

---

## 2. [Second Flow/Client Name] Report

[Repeat the same shape as Section 1 for each additional client/surface
tested against the same scenario.]

---

## 3. Cross-[Client/Surface] Agreement

| Surface | Method | Result |
|---|---|---|
| [surface 1] | [method] | [result] |
| [surface 2] | [method] | [result] |

[One sentence stating whether they agree, and what that agreement/disagreement
establishes.]

## 4. Fixes Applied This Session (unrelated to the finding itself)

1. **[file/component]** — [what was broken, root cause, what changed, how it
   was verified].
2. **[memory/documentation file]** — [what was corrected, and confirmation
   that it was corrected IN PLACE with a dated addendum rather than silently
   rewritten/deleted, per this campaign's standing convention of preserving
   historical accuracy of past observations].
```

## Notes on Mermaid usage specifically

- Use `rect rgb(230,255,230)` (soft green) to highlight the step that
  actually settled the outcome, and `rect rgb(255,250,230)` (soft amber) for
  a step that ran but turned out not to matter (e.g. an attempted-but-moot
  discovery step) — a consistent color convention across reports makes them
  scannable as a set, not just individually.
- Always put "NEVER REACHED" (or equivalent) as an explicit `note over` line
  rather than simply omitting the unreached steps — the omission alone reads
  as "these steps don't exist in this protocol," not "these steps exist but
  weren't triggered this time," which is a materially different and more
  useful claim.
- Keep participant names short and consistent across the "what happened" and
  "contrast" diagrams in the same report (e.g. always `Agent`, always `RS`)
  so a reader can visually diff the two diagrams at a glance.

## Where this applies

Any test of a UCP or ACP flow, an MPP 402 challenge/settlement, or a
WebID-TLS delegation/authorization scenario that's being written up as a
standalone report rather than just reported inline in chat. Cross-referenced
from `acp-client/SKILL.md`'s References section and from
`agent-rdf-memory/preferences.ttl` (see the step referencing this file) so a
future session finds it before inventing a new report layout.
