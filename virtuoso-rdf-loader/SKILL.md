---
name: virtuoso-rdf-loader
description: Bulk-load RDF archives (N-Triples, Turtle, RDF/XML, N-Quads, TriG, JSON-LD, Notation3 — gzip-compressed or raw) into a Virtuoso instance via isql, using ld_dir + rdf_loader_run. Covers single-file loads, directory-wide ingestion, load monitoring, named-graph management (clear/replace/append), and troubleshooting. Triggers on phrases like "load this RDF into Virtuoso", "bulk load into Virtuoso", "ingest .nt.gz into Virtuoso", or any request to push RDF data to a Virtuoso SPARQL endpoint via isql.
---

# Virtuoso RDF Bulk Loader Skill
## ld_dir + rdf_loader_run · isql · N-Triples · Turtle · RDF/XML · N-Quads · TriG · JSON-LD · Notation3 · gzip

## Purpose

Load RDF archives directly into a Virtuoso quad store — no pre-extraction needed. Virtuoso's `ld_dir` + `rdf_loader_run` reads compressed files (`.gz`, `.bz2`) natively and supports every major RDF serialization. The skill provides:

- **Single-file loads** — one archive → one named graph
- **Directory loads** — every matching file in a server-side directory
- **Graph management** — clear before load, append, or replace
- **Progress monitoring** — poll `DB.DBA.LOAD_LIST` until completion
- **Error triage** — interpret load errors and suggest fixes

### Supported Formats

| Format | Extensions | Notes |
|--------|-----------|-------|
| N-Triples | `.nt`, `.nt.gz`, `.nt.bz2` | Line-based; fastest for bulk |
| Turtle | `.ttl`, `.ttl.gz`, `.ttl.bz2` | Compact; common for LOD |
| RDF/XML | `.rdf`, `.rdf.gz`, `.rdf.bz2` | Legacy; still widespread |
| N-Quads | `.nq`, `.nq.gz`, `.nq.bz2` | Quad format; includes graph IRIs |
| TriG | `.trig`, `.trig.gz` | Multi-graph Turtle superset |
| JSON-LD | `.jsonld`, `.jsonld.gz` | JSON-based; web-friendly |
| Notation3 | `.n3`, `.n3.gz` | Superset of Turtle |
| OWL | `.owl`, `.owl.gz` | RDF/XML variant |

All formats are handled by the same `ld_dir` + `rdf_loader_run` pipeline — no format-specific flags needed.

---

## Execution Routing

Default order for data ingestion:

1. **isql CLI** — direct `isql host:port` execution (preferred; always available)
2. **MCP** — if a `virtuoso-support-agent` MCP server is connected, it can relay SQL
3. **SPARQL INSERT** — via SPARQL endpoint when isql path is unavailable (wraps individual INSERTs; unsuitable for bulk)
4. **URIBurner upload** — when the data is at a URL and URIBurner's sponger is available

If the user names a specific mode, honor that preference.

---

## Step 0 — Connection Detection (Always Run First)

```bash
# Check isql availability
which isql

# Quick connectivity test
echo "SELECT 'ok';" | isql <host>:<port> <user> <pass> 2>&1 | head -3
```

If isql is not found, ask the user for:
- isql path, OR
- Virtuoso host:port credentials to try MCP, OR
- SPARQL endpoint URL for fallback loading

---

## Step 1 — Gather Parameters

Before any load, collect:

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| `--host` | Yes | — | Virtuoso SQL listener hostname |
| `--port` | No | `1111` | Virtuoso SQL listener port |
| `--user` | No | `dba` | isql user |
| `--pass` | No | `dba` | isql password |
| `--graph` | Yes | — | Target named-graph IRI |
| `--dir` | Yes | — | Server-side directory containing RDF files |
| `--pattern` | No | `*.*` | File pattern for `ld_dir` (match the format you're loading) |
| `--mode` | No | `append` | `append`, `clear`, or `replace` |

**`--dir` must be accessible to the Virtuoso server process** — `ld_dir` registers server-side paths, not client-side paths. For remote Virtuoso, the files must already be on the server.

### Recommended Patterns by Format

| Loading… | Use `--pattern` |
|----------|-----------------|
| N-Triples | `*.nt.gz` |
| Turtle | `*.ttl.gz` |
| RDF/XML | `*.rdf.gz` |
| N-Quads | `*.nq.gz` |
| TriG | `*.trig.gz` |
| JSON-LD | `*.jsonld.gz` |
| Notation3 | `*.n3.gz` |
| All formats in directory | `*` |

### Mode Behavior

| Mode | SQL executed before load | Result |
|------|--------------------------|--------|
| `append` | *(none)* | Triples added to existing graph |
| `clear` | `SPARQL CLEAR GRAPH <iri>` | Graph emptied, then loaded |
| `replace` | `SPARQL CLEAR GRAPH <iri>` then load | Same as clear + load |


---

## Step 2 — Register and Load

The core workflow (two SQL calls):

```sql
-- Register files (any supported format)
ld_dir ('/data/rdf/incoming/', '*.nt.gz', 'https://example.com/my-graph');

-- Start the loader (runs asynchronously in the server)
rdf_loader_run ();
```

Execute via isql:

```bash
isql ${HOST}:${PORT} ${USER} ${PASS} <<EOF
ld_dir ('${LOAD_DIR}', '${PATTERN}', '${GRAPH}');
rdf_loader_run ();
CHECKPOINT;
EOF
```

### ld_dir Parameters (Full Signature)

```sql
ld_dir (
  in dir         varchar,   -- server-side directory path
  in file_pattern varchar,  -- e.g. '*.nt.gz', '*.ttl.gz', '*.nq.gz', '*'
  in graph_iri   varchar    -- target named graph
);
```

**Key points:**
- `ld_dir` is **idempotent** — calling it twice with the same files does not double-load
- Files are matched by name in `DB.DBA.LOAD_LIST` — renaming a file after registration re-triggers it
- `rdf_loader_run()` can be called multiple times safely; it processes pending entries only
- The loader auto-detects the RDF format from file content — no format flag required
- The loader runs on **server threads** — isql returns immediately

---

## Step 3 — Monitor Progress

Poll `DB.DBA.LOAD_LIST` until no rows remain in progress:

```sql
SELECT
  ll_file,
  ll_graph,
  CASE ll_state
    WHEN 0 THEN 'PENDING'
    WHEN 1 THEN 'LOADING'
    WHEN 2 THEN 'DONE'
    WHEN 3 THEN 'FAILED'
  END AS state,
  ll_started,
  ll_done,
  ll_rows,
  ll_error
FROM DB.DBA.LOAD_LIST;
```

### ll_state Meanings

| ll_state | Status | Action |
|----------|--------|--------|
| 0 | Pending | Waiting — loader will pick it up |
| 1 | Loading | In progress — wait |
| 2 | Done | Success — committed |
| 3 | Failed | See `ll_error` column |

Monitor loop:

```bash
while true; do
  STATUS=$(isql ${HOST}:${PORT} ${USER} ${PASS} <<'EOSQL' 2>/dev/null)
    SELECT ll_file, ll_state, ll_error
    FROM DB.DBA.LOAD_LIST
    WHERE ll_state IN (0, 1, 3);
EOSQL
  if echo "$STATUS" | grep -q 'No\. of rows\|0 rows'; then
    echo "All loads complete."
    break
  fi
  echo "$STATUS"
  sleep 5
done
```

---

## Step 4 — Verify

After loading, check the row count in the target graph:

```sql
SPARQL
SELECT (COUNT(*) AS ?triples)
FROM <${GRAPH}>
WHERE { ?s ?p ?o };
```

Or via isql:

```bash
isql ${HOST}:${PORT} ${USER} ${PASS} <<EOF
SPARQL SELECT (COUNT(*) AS ?triples) FROM <${GRAPH}> WHERE { ?s ?p ?o };
EOF
```

For a spot check, sample 10 triples from the graph:

```sql
SPARQL SELECT * FROM <${GRAPH}> WHERE { ?s ?p ?o } LIMIT 10;
```

---

## Bundled Shell Script

`scripts/bulk-load-rdf.sh` automates Steps 2–3 for single-file or directory loads. Invoke it from the skill directory:

```bash
./scripts/bulk-load-rdf.sh \
    --host     localhost \
    --port     1111 \
    --user     dba \
    --pass     dba \
    --graph    https://example.com/my-graph \
    --dir      /data/rdf/incoming \
    --pattern  "*.nt.gz" \
    dataset.nt.gz
```

| Flag | Purpose |
|------|---------|
| `--host` / `--port` | Virtuoso SQL listener |
| `--user` / `--pass` | isql credentials |
| `--graph` | Target named-graph IRI |
| `--dir` | Server-side staging directory |
| `--pattern` | File pattern for `ld_dir` |
| `--no-copy` | Skip `cp` — files already in `--dir` |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `No file(s) found` in LOAD_LIST | `ld_dir` path not server-accessible | Verify `--dir` exists on the server; check permissions |
| `ll_state = 3` (FAILED) | Malformed data or encoding issue | Check `ll_error`; validate the RDF file; try one file interactively via `DB.DBA.TTLP()` |
| Load stuck at `PENDING` | Loader not running or blocked | Call `rdf_loader_run()` again; check server error log |
| Duplicate triples | Same files loaded twice | Clear graph, delete from `LOAD_LIST`, then re-register and re-load |
| `Permission denied` on `--dir` | Virtuoso server user can't read directory | `chmod 755` the directory and `chmod 644` the files |
| `.gz` files not recognised | Pattern doesn't match files on disk | Use the correct pattern for the file extension |
| Wrong graph IRI in N-Quads/TriG | File contains its own graph IRIs | N-Quads/TriG files specify graphs inline — `ld_dir`'s graph becomes a default for triples not in a named graph |
| Out of disk / transaction log full | Bulk load exceeds temp space | Increase `TempSpace` / `TransactionLog` in `virtuoso.ini`; load in smaller batches |

---

## Loading Without ld_dir (Single-File Interactive)

For one-offs where `ld_dir` isn't practical, pipe a decompressed file directly to isql. `DB.DBA.TTLP()` auto-detects the format:

```bash
gunzip -c data.nt.gz | isql ${HOST}:${PORT} ${USER} ${PASS} <<'EOF'
DB.DBA.TTLP (
  file_to_string_output ('/dev/stdin'),
  '',
  'https://example.com/my-graph',
  0
);
EOF
```

Prefer `ld_dir` + `rdf_loader_run` for everything except single small files — it's parallel, transactional, restartable, and format-agnostic.

---

## Quick Reference

| Task | SQL / Command |
|------|---------------|
| Register files | `ld_dir('/path/', '*.nt.gz', 'graph-iri');` |
| Start loader | `rdf_loader_run();` |
| Check progress | `SELECT * FROM DB.DBA.LOAD_LIST WHERE ll_state < 2;` |
| Clear graph | `SPARQL CLEAR GRAPH <iri>;` |
| Count triples | `SPARQL SELECT (COUNT(*) AS ?c) FROM <iri> WHERE {?s ?p ?o};` |
| Remove registration | `DELETE FROM DB.DBA.LOAD_LIST WHERE ll_file LIKE '%pattern%';` |
| Force re-load | Delete from LOAD_LIST + `ld_dir` again + `rdf_loader_run` |
| Set parallel loaders | `rdf_loader_run(max_files => 8);` |
| Check server log | `tail -f virtuo<port>.log` on server |

---

## Initialization Sequence

When invoked:

⛔ **PRE-BUILD CHECK**: Before producing output, re-read the relevant workflow section above and re-read any checklists or verification gates defined in this skill. Confirm each checklist item before writing output. Apply the CLAUDE.md Anti-Drift Protocol: re-read spec section before build, gate-first validation, section-by-section delivery.

1. Run Step 0 — verify isql is available and Virtuoso is reachable
2. Ask for: host, port, credentials, graph IRI, server-side directory, file pattern
3. Determine the RDF format from file extensions — confirm with user
4. Confirm mode (append / clear / replace)
5. If mode is `clear` or `replace`: warn user, then execute `SPARQL CLEAR GRAPH`
6. Run `ld_dir` to register files with the correct pattern
7. Run `rdf_loader_run` to start loading
8. Poll `DB.DBA.LOAD_LIST` until all files report `ll_state = 2` (done)
9. Run verification count query — report triples loaded per file
10. If any files report `ll_state = 3` (failed), surface `ll_error` and troubleshoot

---

## Reference Files

| File | Contents |
|------|----------|
| `references/ldir-parameters.md` | Full `ld_dir` parameter reference, all supported formats and patterns, `rdf_loader_run` options, `LOAD_LIST` schema, graph management |
| `scripts/bulk-load-rdf.sh` | Shell script automating register → load → monitor |

---

## Version
**2.0.0** — Format-agnostic. Supports N-Triples, Turtle, RDF/XML, N-Quads, TriG, JSON-LD, Notation3, OWL — gzip-compressed or raw. Same `ld_dir` + `rdf_loader_run` pipeline for all.
