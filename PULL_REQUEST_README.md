# Enhance Data Twingler HowTo Discovery

## Summary

This PR improves the Data Twingler skill's handling of "How to..." and workflow-style prompts by adding a structured `schema:HowTo` discovery preflight before broader keyword, entity-description, or semantic fallback paths.

The change addresses a retrieval failure mode where an existing HowTo could be missed when the prompt used adjacent wording or variant entity spelling, such as `Akash` vs. `Aakash`.

## Changes

- Adds a T5 Structured HowTo Preflight section to `data-twingler/SKILL.md`.
- Adds a non-negotiable rule requiring direct `schema:HowTo` enumeration for T5 and step/workflow requests.
- Adds a Step 0.5 query template to `data-twingler/references/query-templates.md`.
- Retrieves ordered `schema:step` / `schema:HowToStep` details as soon as a HowTo candidate is found.
- Includes named-entity spelling variants in candidate matching.
- Repackages `data-twingler.zip` after the skill changes.

## Rationale

The previous workflow could over-weight broad keyword graph discovery and semantic inference before explicitly checking the KG's structured HowTo shape. That made it possible to miss a directly modeled `schema:HowTo`, especially when the user's wording did not exactly match the article or entity labels.

The new preflight makes HowTo retrieval type-driven first:

1. Detect step/workflow-oriented prompts.
2. Enumerate `schema:HowTo` candidates directly.
3. Match against the HowTo IRI, name, description, source/article text, and spelling variants.
4. Retrieve ordered HowTo steps before falling back to broader discovery.

## Validation

- Confirmed the modified sections are present in:
  - `data-twingler/SKILL.md`
  - `data-twingler/references/query-templates.md`
- Verified the staged skill change before commit:
  - `2 files changed, 100 insertions(+), 13 deletions(-)`
- Confirmed the package was regenerated in a follow-up commit:
  - `data-twingler.zip`

## Notes

A live URIBurner smoke test from the local session returned a Virtuoso permission error unrelated to the template content:

```text
No permission to execute procedure OAI.DBA.ASSISTANT_ID_TO_URI
```

Because of that endpoint-side permission issue, validation was limited to file inspection, git diff review, and package regeneration.

