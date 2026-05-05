---
name: rdf-det-variant-generator
description: "Create or update a custom DAV DET variant based on RDF Import DET for Virtuoso. Use when the task is to scaffold, modify, or document a DET that ingests RDF documents into the Quad Store, supports one or more Virtuoso-supported RDF document types, implements the required _DAV_* hook family, or needs verification SQL, WebDAV probes, and VAD/source integration notes."
---

# RDF DET Variant Generator

Use this skill when building a custom DAV DET derived from the `RDFImport` pattern for RDF-bearing document types supported by Virtuoso.

## What This Skill Produces

- DET SQL scaffolding derived from `RDFImport`
- Hook coverage checklist for required `DB.DBA.<DetName>_DAV_*` functions
- Variants for multiple RDF document types
- Verification SQL and WebDAV probes
- Packaging guidance for:
  - `/Users/kidehen/Documents/Management/Development/virtuoso-engine/binsrc/yacutia/sql/`
  - `/Users/kidehen/Documents/Management/Development/ods-virtuoso/briefcase/sql/`

## Trigger Conditions

Use this skill when the user asks to:

- create a DET similar to RDF Import
- support additional RDF document types
- generate a new Quad Store ingestion DET
- scaffold a DAV DET that loads RDF into named graphs
- create or update DET SQL hooks and validation queries

## Workflow

1. Identify the DET name, target folders, and desired graph behavior.
2. Confirm the RDF document types to support.
3. Load the implementation checklist in `references/det-hook-checklist.md`.
4. Load the RDF-type guidance in `references/virtuoso-rdf-doc-types.md`.
5. Use `references/rdf-det-template.md` to generate or update the DET.
6. Generate validation queries from `references/verification-queries.md`.
7. Provide VAD/source integration notes and release/build reminders.

## Output Requirements

- Keep runtime SQL in Virtuoso procedure form.
- Keep verification artifacts separate from runtime code.
- When generating listing logic, prefer explicit vector accumulation unless there is a proven reason to use builder helpers.
- Ensure the DET returns a proper array of DAV row vectors from `_DAV_DIR_LIST`.

## References

- `references/det-hook-checklist.md`
- `references/virtuoso-rdf-doc-types.md`
- `references/rdf-det-template.md`
- `references/verification-queries.md`

