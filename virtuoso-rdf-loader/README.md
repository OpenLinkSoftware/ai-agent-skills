# Virtuoso RDF Bulk Loader

Quick single-command RDF → Virtuoso (any format — N-Triples, Turtle, RDF/XML, N-Quads, TriG, JSON-LD, Notation3):

```bash
./scripts/bulk-load-rdf.sh \
    --host  localhost --port  1111 \
    --user  dba       --pass  dba \
    --graph https://example.com/my-graph \
    --dir   /data/rdf/incoming \
    --pattern "*.nt.gz" \
    dataset.nt.gz
```

No extraction needed — Virtuoso reads `.gz` natively. The loader auto-detects the RDF format from file content.

See `SKILL.md` for the full workflow, all supported formats, troubleshooting, and isql-based manual execution.
