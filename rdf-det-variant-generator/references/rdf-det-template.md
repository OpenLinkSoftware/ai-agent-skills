# RDF DET Template Guidance

Use `RDFImport` as the behavioral baseline for:

- path virtualization
- DET id wrapping
- DAV row shaping
- graph-oriented upload and delete behavior

Template requirements:

1. Provide a `<DetName>__detName()` helper.
2. Centralize DET param get/set/remove helpers.
3. In `_DAV_RES_UPLOAD`, write DAV rows first, then persist DET metadata, then trigger RDF load or queueing.
4. In `_DAV_DIR_SINGLE`, rewrite visible path and display name if needed.
5. In `_DAV_DIR_LIST`, return a proper array of DAV row vectors.
6. In `_DAV_DELETE`, remove graph-backed artifacts consistently.

Implementation note:

- prefer explicit vector accumulation in `_DAV_DIR_LIST` if there is any doubt about builder helper behavior in the target path

