---
name: csv-to-rdf-det-generator
description: "Create or update a custom DAV DET that accepts CSV uploads, transforms them to RDF, and then writes to the Quad Store. Use when the task is to scaffold, modify, or document a CSV-backed ingestion DET with DAV hook functions, CSV-to-RDF mapping logic, graph assignment rules, verification SQL, SPARQL checks, and packaging notes."
---

# CSV to RDF DET Generator

Use this skill when building a DAV DET that ingests CSV, transforms it to RDF, and persists the result to the Quad Store.

## What This Skill Produces

- DET SQL scaffolding for CSV ingestion
- guidance for CSV-to-RDF transformation flow before Quad Store load
- graph assignment and metadata persistence rules
- verification SQL and SPARQL probes
- packaging guidance for Virtuoso source and VAD trees

## Trigger Conditions

Use this skill when the user asks to:

- create a CSV ingestion DET
- transform CSV to RDF before graph load
- build a WebDAV-backed CSV-to-RDF pipeline
- scaffold DAV hooks for CSV uploads with Quad Store side effects

## Workflow

1. Identify the DET name, CSV shape, and target RDF model.
2. Define graph assignment rules and mapping strategy.
3. Load `references/det-hook-checklist.md`.
4. Load `references/csv-to-rdf-pipeline.md`.
5. Load `references/csv-mapping-design.md`.
6. Generate or update runtime SQL using `references/csv-det-template.md`.
7. Generate validation SQL, SPARQL, and WebDAV probes from `references/verification-queries.md`.

## Output Requirements

- treat CSV transformation as an explicit step before Quad Store upload
- define how headers, datatypes, IRIs, and row identity are derived
- keep mapping assumptions documented
- ensure `_DAV_DIR_LIST` returns a proper array of DAV rows

## References

- `references/det-hook-checklist.md`
- `references/csv-to-rdf-pipeline.md`
- `references/csv-mapping-design.md`
- `references/csv-det-template.md`
- `references/verification-queries.md`

