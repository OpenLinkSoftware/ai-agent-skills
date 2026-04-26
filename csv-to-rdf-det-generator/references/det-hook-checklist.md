# DET Hook Checklist

Required:

- `[DetName]_DAV_SEARCH_ID`
- `[DetName]_DAV_MAKE_ID`
- `[DetName]_DAV_DIR_SINGLE`
- `[DetName]_DAV_DIR_LIST`
- `[DetName]_DAV_RES_UPLOAD`
- `[DetName]_DAV_DELETE`

Recommended:

- `[DetName]_DAV_COL_CREATE`
- `[DetName]_DAV_GET_PARENT`
- property accessors

For CSV-backed DETs, upload logic must also:

- parse CSV
- transform rows to RDF
- load RDF into the target graph
- persist enough metadata for delete/update behavior

