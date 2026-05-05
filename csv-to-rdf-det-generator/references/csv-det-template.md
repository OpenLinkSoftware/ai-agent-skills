# CSV DET Template Guidance

Use a DET pattern similar to graph-backed DAV ingestion DETs, but make CSV transformation an explicit pre-load stage.

Template requirements:

1. Upload handler stores the DAV row.
2. CSV is parsed deterministically.
3. RDF is generated before Quad Store load.
4. Graph and source metadata are persisted.
5. Delete behavior removes or reverses graph-side artifacts consistently.
6. Listing behavior remains pure DAV row shaping and must not depend on transformation success at list time.

Implementation note:

- keep CSV transformation separate from `_DAV_DIR_LIST`
- keep all back-end side effects in upload/delete/update paths

