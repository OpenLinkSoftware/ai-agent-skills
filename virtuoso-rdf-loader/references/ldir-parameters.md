# ld_dir Parameter Reference

## Supported RDF Formats

All formats supported by Virtuoso's `rdf_loader_run` — no format-specific flags needed; the loader auto-detects from file content.

| Format | Extensions | Quad-safe | Notes |
|--------|-----------|-----------|-------|
| N-Triples | `.nt`, `.nt.gz`, `.nt.bz2` | No | Line-based; fastest bulk format |
| Turtle | `.ttl`, `.ttl.gz`, `.ttl.bz2` | No | Compact; most common in LOD |
| RDF/XML | `.rdf`, `.rdf.gz`, `.rdf.bz2` | No | Legacy; still widespread |
| N-Quads | `.nq`, `.nq.gz`, `.nq.bz2` | Yes | Quad format; includes graph IRIs inline |
| TriG | `.trig`, `.trig.gz` | Yes | Multi-graph Turtle superset |
| JSON-LD | `.jsonld`, `.jsonld.gz` | No | JSON-based; web-friendly |
| Notation3 | `.n3`, `.n3.gz` | No | Superset of Turtle |
| OWL | `.owl`, `.owl.gz` | No | RDF/XML variant |

**Quad-safe formats** (N-Quads, TriG): each triple can specify its own graph IRI. The `ld_dir` graph parameter acts as a default for triples that don't name a graph. For triples-only formats (N-Triples, Turtle, RDF/XML, JSON-LD), all triples go into the `ld_dir`-specified graph.

## ld_dir Signature

```sql
ld_dir (
  in dir         varchar,   -- server-side directory path (must be accessible to Virtuoso process)
  in file_pattern varchar,  -- glob pattern matching files in dir
  in graph_iri   varchar    -- target named-graph IRI for all matched files
);
```

## Common Patterns

| Pattern | Matches |
|---------|---------|
| `*.nt.gz` | Gzip-compressed N-Triples |
| `*.ttl.gz` | Gzip-compressed Turtle |
| `*.rdf.gz` | Gzip-compressed RDF/XML |
| `*.nq.gz` | Gzip-compressed N-Quads |
| `*.trig.gz` | Gzip-compressed TriG |
| `*.jsonld.gz` | Gzip-compressed JSON-LD |
| `*.n3.gz` | Gzip-compressed Notation3 |
| `*.nt` | Uncompressed N-Triples |
| `*.ttl` | Uncompressed Turtle |
| `*.rdf` | Uncompressed RDF/XML |
| `*.nq` | Uncompressed N-Quads |
| `*.trig` | Uncompressed TriG |
| `*.jsonld` | Uncompressed JSON-LD |
| `data-*.nt.gz` | Files matching a prefix pattern |
| `*` | All files (use when loading mixed formats) |

## rdf_loader_run Options

```sql
rdf_loader_run (
  in max_files   integer := 0,    -- max concurrent files (0 = all registered)
  in log_mode    integer := 1     -- 0=off, 1=log to virtuo<port>.log
);
```

### Parallelism

Set `max_files` to control concurrent load threads:

```sql
-- Load 4 files at a time
rdf_loader_run (max_files => 4);

-- Load all registered files (default)
rdf_loader_run ();
```

Each file gets one loader thread. Small files benefit from more parallelism; large single files are inherently single-threaded per file. Split large dumps into multiple chunks (e.g., `split -l 1000000`) to exploit parallelism for N-Triples/N-Quads.

### Format Auto-Detection

`rdf_loader_run` detects the RDF format by examining file content, not the extension. Files that fail to parse should be checked with a standalone parser before re-attempting.

## DB.DBA.LOAD_LIST Schema

| Column | Type | Description |
|--------|------|-------------|
| `ll_file` | VARCHAR | File path as registered |
| `ll_graph` | VARCHAR | Target graph IRI |
| `ll_state` | INTEGER | 0=PENDING, 1=LOADING, 2=DONE, 3=FAILED |
| `ll_started` | DATETIME | When loading began |
| `ll_done` | DATETIME | When loading completed |
| `ll_host` | INTEGER | Server host ID |
| `ll_work_time` | INTEGER | Load duration (ms) |
| `ll_error` | VARCHAR | Error message if `ll_state = 3` |
| `ll_rows` | INTEGER | Triples loaded |

## Clearing / Resetting Load Registrations

Remove stale entries (files that no longer exist or you want to re-register):

```sql
-- Remove specific files
DELETE FROM DB.DBA.LOAD_LIST
WHERE ll_file = '/path/to/file.nt.gz';

-- Remove all entries for a pattern
DELETE FROM DB.DBA.LOAD_LIST
WHERE ll_file LIKE '%dataset%';

-- Purge all pending entries
DELETE FROM DB.DBA.LOAD_LIST
WHERE ll_state = 0;
```

After deleting from LOAD_LIST, re-register with `ld_dir` and re-run `rdf_loader_run`.

## Named Graph Management

```sql
-- Clear a graph before reloading
SPARQL CLEAR GRAPH <https://example.com/my-graph>;

-- Drop a graph entirely (removes triples + frees index space)
SPARQL DROP SILENT GRAPH <https://example.com/my-graph>;

-- Check if a graph exists
SPARQL ASK FROM <https://example.com/my-graph> WHERE { ?s ?p ?o };

-- Count triples in a graph
SPARQL SELECT (COUNT(*) AS ?c) FROM <https://example.com/my-graph> WHERE { ?s ?p ?o };
```

## RDF_QUAD Direct Inspection

When SPARQL-level checks are insufficient, query the quad store directly:

```sql
-- Count triples by graph (SQL)
SELECT G, COUNT(*) AS triples
FROM DB.DBA.RDF_QUAD
GROUP BY G
ORDER BY triples DESC
LIMIT 20;

-- Look up a graph IRI ID
SELECT RI_ID, RI_NAME
FROM DB.DBA.RDF_IRI
WHERE RI_NAME = 'https://example.com/my-graph';

-- Triples for a specific graph (first 10)
SELECT TOP 10 * FROM DB.DBA.RDF_QUAD
WHERE G = iri_to_id('https://example.com/my-graph');
```

## Server-Side File Requirements

The directory passed to `ld_dir` must be:

1. **Readable by the Virtuoso server process** (check `virtuoso.ini` for `ServerRoot` and the user the server runs as)
2. **On the server's filesystem** — not the client's (unless they're the same machine)
3. **Stable** — don't move or delete files while loading is in progress

For remote Virtuoso, transfer files first:
```bash
scp *.nt.gz user@virtuoso-host:/data/rdf/incoming/
```
Then use `--dir /data/rdf/incoming` and `--no-copy` with the script.

## N-Quads / TriG Graph IRI Handling

N-Quads and TriG files embed graph IRIs within the data. The `ld_dir` graph parameter interacts with these as follows:

- Triples with an **explicit graph** in the file → loaded into that graph
- Triples **without** a graph (the default graph in TriG) → loaded into the `ld_dir` graph
- This means a single N-Quads/TriG file can populate multiple graphs

To load N-Quads/TriG into a single graph regardless of the file's own graph assignments, use the `--graph` parameter and the loader will override. Check `virtuoso.ini` for `RdfLoaderQuadMapping` to control this behavior.
