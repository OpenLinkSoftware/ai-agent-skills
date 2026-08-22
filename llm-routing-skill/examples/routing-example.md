# Routing Example — right-sizing a mixed agent workload

This example walks the full workflow from SKILL.md for a realistic agent:
an internal knowledge assistant that answers employee questions with RAG,
summarizes documents, generates code snippets, and plans multi-step analyses.

All CLI outputs below were captured from the current graph
(145 models, prices updated 2026-08-13).

## The five sub-steps, classified

| # | Agent sub-step | Task type | Required level |
|---|----------------|-----------|----------------|
| 1 | Chunk + embed incoming documents | `embedding` | L1 (special: embedding-only) |
| 2 | Answer grounded questions from retrieved chunks | `question-answering-open` | L2 |
| 3 | Summarize long threads for digest emails | `summarization` | L2 |
| 4 | Generate a Python script to transform a dataset | `code-generation` | L3 |
| 5 | Plan the end-to-end analysis (tools, ordering) | `planning-decomposition` | L4 |

## Decisions (cost tier `medium`, balanced policy)

```
$ python3 scripts/route.py question-answering-open medium
RECOMMENDED:  Ministral 3B 24.10   L2  $0.04/MTok  latency=very-low
Escalation:  Ministral 3B ($0.04) → Ministral 8B ($0.10) → Claude Opus 4.5 ($25)

$ python3 scripts/route.py summarization medium
RECOMMENDED:  Ministral 3B 24.10   L2  $0.04/MTok  latency=very-low
Escalation:  Ministral 3B ($0.04) → Ministral 8B ($0.10) → Claude Opus 4.5 ($25)

$ python3 scripts/route.py code-generation medium
RECOMMENDED:  DeepSeek-V4-Flash   L3  $0.28/MTok  latency=low
Escalation:  DeepSeek-V4-Flash ($0.28) → Codestral ($0.90) → Claude Opus 4.5 ($25)

$ python3 scripts/route.py planning-decomposition high --policy quality-first
RECOMMENDED:  Claude Opus 4.5   L5  $25/MTok  latency=high
Escalation:  GPT-5.6 Luna ($1.20) → GPT-5.1 Codex mini ($2.00) → Claude Opus 4.5 ($25)
```

## Why these choices (the Pareto reasoning)

- **Grounding QA (L2)** and **summarization (L2)** are high-volume and
  quality-tolerant — the cheapest L2 model on the Pareto frontier wins
  (Ministral 3B at $0.04/MTok), with Ministral 8B as the next ladder rung.
- **Code generation (L3)** needs real code capability; DeepSeek-V4-Flash sits
  on the frontier at L3 with a low price. The ladder keeps Codestral (code
  specialist, $0.90) as the mid-rung and a frontier model as the safety net.
- **Planning (L4)** is low-volume and correctness-sensitive — `quality-first`
  within the `high` tier picks the top-capability model (Claude Opus 4.5, L5),
  while the ladder documents the cheaper escalation path (GPT-5.6 Luna →
  GPT-5.1 Codex mini) for when cost matters more.
- **Embedding** has no dedicated embedding models in the current llm-prices
  feed — the graph correctly reports an empty frontier/ladder, signaling the
  operator should choose an embedding provider outside this graph (or add
  embedding models to the profiles).

## Governance applied

- Approved model list: only vendors with data-residency commitments matching
  our EU region → `--vendor google --vendor mistral` for PII-touching steps.
- Cost cap: all steps run at tier ≤ `medium` except `planning-decomposition`
  at `high`.

## Feedback recorded

Each sub-step's output was scored; records appended to
`references/feedback-log.ttl`. After ~100 runs, review showed Ministral 3B
consistently scoring 4/5 on summarization — the seed profile stays; if it had
scored 2/5, the `family_rules` entry would be downgraded and the graph rebuilt.
