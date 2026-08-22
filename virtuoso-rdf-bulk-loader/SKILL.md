---
name: virtuoso-rdf-bulk-loader
description: Generate and run Virtuoso isql bulk-load scripts for RDF directories. Takes a source folder plus optional graph IRI, file pattern/formats, and load mode (directory-wide via ld_dir + rdf_loader_run, or per-file named graphs via TTLP_MT with an auto prefix preamble), and emits a ready-to-run .sql. Use when bulk-loading RDF files from a folder into a Virtuoso quad store via isql, regenerating loader scripts after store changes, or simplifying repeated folder loads.
whenToUse: Use when the user asks to bulk-load RDF from a directory into Virtuoso via isql, generate an isql loader script from a source folder with configurable graph/format arguments, or refresh loader scripts after the source folder changes.
---

# Virtuoso RDF Bulk Loader — isql loader generation from a source folder

Generate a ready-to-run isql `.sql` from a local folder of RDF files. Two modes:

| Mode | Mechanism | Use for |
|---|---|---|
| `dir` (default) | `ld_dir` + `rdf_loader_run` — one named graph for the whole folder; Virtuoso auto-detects format (N-Triples, Turtle, RDF/XML, N-Quads, TriG, JSON-LD, Notation3) and reads gzip/bzip2 natively | Simple bulk ingestion, mixed formats, compressed archives |
| `per-file` | `TTLP_MT` — one named graph per file (Turtle family: `.ttl`, `.nt`, `.trig`), optional auto prefix-preamble and CLEAR-before-load | Exact per-document graphs (e.g. an agent memory store), re-loadable deltas |

## Workflow

1. **Elicit** (never guess): source folder (must be accessible to the **Virtuoso server process** — `ld_dir` registers server-side paths), target graph IRI (dir mode), file pattern or format list.
2. **Generate**:
   ```bash
   python3 scripts/generate-bulk-load-sql.py \
     --source-dir /path/to/rdf/ \
     --graph https://example.com/my-graph \
     --pattern '*.ttl' \
     --out bulk-load.sql
   ```
3. **Run** (your credentials, never displayed):
   ```bash
   isql 1111 dba <dba-password> -f bulk-load.sql
   ```
4. **Monitor** (the generated script ends with the load_list check):
   ```sql
   select * from db.dba.load_list where ll_state <> 2;
   ```
   `ll_state 2` = done; rows remaining = still pending/errored (`ll_error` column).
5. **Verify** (generated script ends with per-graph counts):
   ```sql
   SPARQL SELECT ?g (COUNT(*) AS ?t) WHERE { GRAPH ?g { ?s ?p ?o } } GROUP BY ?g;
   ```

## Options (`generate-bulk-load-sql.py`)

| Flag | Default | Meaning |
|---|---|---|
| `--source-dir` | *(required)* | Folder containing the RDF files (server-visible path) |
| `--graph` | `urn:dav:/DAV/home/kidehen/bulk-load/` | Target named graph (dir mode) |
| `--pattern` | `*.*` | `ld_dir` pattern, e.g. `*.ttl`, `*.nt.gz`, `*.nq` |
| `--formats` | — | Shorthand expanding to patterns, e.g. `ttl,nt,nq` |
| `--mode` | `dir` | `dir` (ld_dir) or `per-file` (TTLP_MT per document) |
| `--graph-base` | `urn:dav:/DAV/home/kidehen/bulk-load/` | IRI prefix for per-file graphs (file relpath appended) |
| `--preamble` | off | per-file mode: prepend store-wide prefix union so prefix-undeclared Turtle loads |
| `--clear` | off | Emit `SPARQL CLEAR GRAPH` before loading (idempotent re-runs) |
| `--out` | `bulk-load.sql` | Output path |
| `--dry-run` | off | Print the script instead of writing |

## Notes

- **Server-side paths**: `ld_dir` paths are read by the Virtuoso server, not your client. For a remote Virtuoso, stage files on the server first.
- **Idempotency**: `ld_dir` does not double-load identical files; `rdf_loader_run()` may be re-run safely. `--clear` makes full re-runs replace the graph.
- **Troubleshooting**: load failures, permission issues, DAV paths, and named-graph management — see the `virtuoso-rdf-loader` skill (ld_dir + rdf_loader_run deep-dive).
- This skill is the generator generalization of the agent-rdf-memory loader (`agent-rdf-memory/scripts/generate-loader-sql.py`); that store's `refresh-loader.sh` is the same pattern in action.
