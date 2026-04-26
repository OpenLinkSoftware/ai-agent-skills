# DET Hook Checklist

Required hook family for a custom DAV DET:

- `[DetName]_DAV_SEARCH_ID`
- `[DetName]_DAV_MAKE_ID`
- `[DetName]_DAV_DIR_SINGLE`
- `[DetName]_DAV_DIR_LIST`
- `[DetName]_DAV_RES_UPLOAD`
- `[DetName]_DAV_DELETE`

Usually also:

- `[DetName]_DAV_COL_CREATE`
- `[DetName]_DAV_GET_PARENT`
- `[DetName]_DAV_PROP_GET`
- `[DetName]_DAV_PROP_SET`
- `[DetName]_DAV_PROP_LIST`
- `[DetName]_DAV_PROP_REMOVE`

Runtime invariants:

- `_DAV_SEARCH_ID` returns DET vectors where appropriate
- `_DAV_DIR_SINGLE` returns a valid 13-element DAV row vector
- `_DAV_DIR_LIST` returns an array of DAV row vectors
- upload persists any metadata needed by list/search/delete
- delete clears DAV state and back-end side effects

