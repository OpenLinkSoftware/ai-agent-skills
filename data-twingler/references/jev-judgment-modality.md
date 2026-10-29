# Optional System One judgment modality (Jev / Laya / NanoJev)

Sister pattern to `agent-rdf-memory/howto/jev-judgment-modality.ttl` (preferences step 306).
Same `system_one(state, questions)` contract; different candidate space:

| Harness | Candidates Jev routes over |
|---|---|
| agent-rdf-memory | HowTo / HowToStep IRIs + compact session state |
| **Data Twingler** | Query language / template ids / endpoint & protocol rungs |

Jev **never authors** SPARQL, SQL, SPASQL, or GraphQL. Templates in
`query-templates.md` and the protocol ladder in this skill remain the source of
truth. Jev only **selects and gates**.

## Modality

| Value | Behavior |
|---|---|
| `none` | Existing LLM/deterministic routing only |
| `jev-shadow` (**published default**) | Call System One; log Choice/Noul/Score beside the skill’s current decision; **do not override** |
| `jev-active` | Honor System One when confidence/probability ≥ configured thresholds; else fall back |

Kill switch (any of these → skip System One, continue as today):

- `judgmentModality: none`
- missing provider key / timeout / API error
- config `enabled: false`
- user or state says `bypass jev` / `no jev`

## Provider

TypeSafe Jev (production), Laya (open weights), or NanoJev (lab stub) behind one
contract: `system_one(state, questions) → Choice | Noul | Score distributions`.

## State in (compact; never secrets)

- `utterance` — user prompt (short)
- `defaults` — skill Defaults & Settings snapshot (endpoint, limits, modality)
- `named_remote` — brand or URL if user named DBpedia/Wikidata/etc.
- `protocol_preference` — explicit curl/REST/MCP/OPAL if any
- `prior_result_sample` — optional thin sample (row count, empty?, error class)
- `same_error_count` — repeated empty/fail attempts this turn

Do **not** pass API keys, passwords, Bearer tokens, or raw PII payloads.

## Typed questions

Compose only what the turn needs; keep each atomic.

| Question | Shape | Candidates / meaning |
|---|---|---|
| `query_family` | Choice | `sparql` \| `sql` \| `spasql` \| `sparql_fed` \| `graphql` \| `local_rdf` \| `other` |
| `template_id` | Choice | Closed ids from `query-templates.md` (T1…Tn) plus `ad_hoc` |
| `endpoint_rung` | Choice | `uriburner_default` \| `named_remote` \| `kingsley` \| `demo` \| `local_files` |
| `protocol_rung` | Choice | `curl` \| `uriburner_rest` \| `oauth_then_rest` \| `mcp` \| `opal` — **explicit user preference wins first** |
| `intent_kind` | Choice | Align with vector candidate types: `howto` \| `defined_term` \| `live_query` \| `exploration` \| `other` |
| `results_good_enough` | Noul | Stop semantic-variant retries / protocol climb |
| `need_user_input` | Noul | Must elicit before another expensive attempt |
| `answer_quality` | Score | empty / thin / adequate / rich — drives LIMIT bump vs stop vs explain |
| `ambiguity` | Score | Feeds ask-vs-act and “retry variant vs ask” |

## Shadow → active

1. Published default is `jev-shadow`: execute the non-Jev route; append Jev advice +
   probabilities to the run log (or operator note).
2. Compare disagreements (wrong language, unnecessary FED, empty-result storms).
3. Promote a session or deployment to `jev-active` only when desired; if P(choice) and confidence meet mins, take that branch; else elicit or keep the non-Jev path. Drop back to `jev-shadow` anytime for observation-only.

## Flow

```
utterance + defaults
    → optional system_one(Choice/Noul/Score)
    → select template / endpoint / protocol (shadow: log only; active: honor)
    → execute via existing Execution Routing
    → optional Noul results_good_enough / Score answer_quality
    → stop | retry semantic variant | next protocol rung | elicit
```

## Related

- `agent-rdf-memory/howto/jev-judgment-modality.ttl`
- Skill Defaults: `judgmentModality`
