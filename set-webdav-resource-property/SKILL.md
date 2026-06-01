---
name: set-webdav-resource-property
description: Set custom WebDAV properties on resources via PROPPATCH requests using curl. Supports arbitrary prefixed properties (schema:name, dc:title, etc.), auto-generated human-readable titles from filenames with type tags, batch processing, and known namespace defaults.
license: MIT
---

# WebDAV Custom Property Setting Skill

Set custom metadata properties on WebDAV resources via PROPPATCH requests using curl. This skill enables you to add human-readable titles, Dublin Core metadata, schema.org properties, and any custom namespace-prefixed property to files and directories on a WebDAV server (Virtuoso or any WebDAV-compliant server).

## When to Use This Skill

- Setting `schema:name` or `dc:title` on WebDAV-hosted resources
- Adding human-readable display titles to files with technical filenames
- Batch-setting metadata across multiple WebDAV resources
- Configuring DAV properties for resource discovery and browsing
- Adding custom namespace-prefixed properties to WebDAV resources

## Trigger Phrases

- "set WebDAV property"
- "set custom property on"
- "set DAV title"
- "PROPPATCH"
- "set schema:name on"
- "set dc:title for"
- "add metadata to WebDAV resource"

## Quick Workflow

### 1. Gather Required Parameters

```
-u USER        WebDAV username (required)
-p PASS        WebDAV password (if omitted, prompt interactively)
-b BASE        Base URL (required), e.g. https://www.openlinksw.com
-P PATH        Resource path (required), e.g. /dav/home/demo/docs/file.pdf
-n PROP        Property to set (default: schema:name). Use prefix:local form
-s NS_URI      Namespace URI for the prefix (optional; known defaults below)
-v             Verbose mode (show generated XML and responses)
```

### 2. Known Namespace Defaults

| Prefix | Namespace URI |
|--------|---------------|
| `schema` | `http://schema.org/` |
| `dc` | `http://purl.org/dc/elements/1.1/` |

If `-s` is not provided and the prefix matches a known default, the namespace is auto-declared on the PROPPATCH root element.

### 3. Set Property on a Single Resource

**Example:** Set `schema:name` on a PDF file:

```bash
curl -u "demo:demo" -X PROPPATCH "https://linkeddata.uriburner.com/dav/home/demo/docs/report.pdf" \
  -H "Content-Type: application/xml; charset=utf-8" \
  --data '<?xml version="1.0" encoding="utf-8"?>
<D:propertyupdate xmlns:D="DAV:" xmlns:schema="http://schema.org/">
  <D:set>
    <D:prop>
      <schema:name>Report (PDF)</schema:name>
    </D:prop>
  </D:set>
</D:propertyupdate>'
```

### 4. Set Property on Multiple Resources

For batch operations, iterate over a list of paths:

```bash
while IFS= read -r path; do
  [[ -z "$path" || "$path" =~ ^# ]] && continue
  filename="$(basename "$path")"
  basefn="${filename%.*}"
  ext="${filename##*.}"
  ext_lower="$(printf "%s" "$ext" | tr '[:upper:]' '[:lower:]')"
  case "$ext_lower" in
    pdf) type_tag="(PDF)" ;;
    mp4|mkv|webm) type_tag="(Video)" ;;
    png|jpg|jpeg|gif|svg) type_tag="(Image)" ;;
    wav|mp3|m4a) type_tag="(Audio)" ;;
    html|htm) type_tag="(WebPage)" ;;
    *) type_tag="" ;;
  esac
  title="$(printf "%s" "$basefn" | sed -E 's/%20/ /g; s/[_-]+/ /g; s/[[:space:]]+/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2)); print}') $(printf "%s" "$type_tag" | sed 's/[[:space:]]*$//')"
  curl -sS -u "demo:demo" -X PROPPATCH "https://linkeddata.uriburner.com${path}" \
    -H "Content-Type: application/xml; charset=utf-8" \
    --data "<?xml version=\"1.0\" encoding=\"utf-8\"?>
<D:propertyupdate xmlns:D=\"DAV:\" xmlns:schema=\"http://schema.org/\">
  <D:set>
    <D:prop>
      <schema:name>${title}</schema:name>
    </D:prop>
  </D:set>
</D:propertyupdate>" -w "HTTP %{http_code}\n"
done < paths.txt
```

### 5. Verify Property Was Set

Use a PROPFIND request to read back the property:

```bash
curl -u "demo:demo" -X PROPFIND "https://linkeddata.uriburner.com/dav/home/demo/docs/report.pdf" \
  -H "Depth: 0" \
  -H "Content-Type: application/xml" \
  --data '<?xml version="1.0" encoding="utf-8"?>
<D:propfind xmlns:D="DAV:" xmlns:schema="http://schema.org/">
  <D:prop>
    <schema:name/>
  </D:prop>
</D:propfind>'
```

## PROPPATCH XML Structure

The PROPPATCH body follows this pattern:

```xml
<?xml version="1.0" encoding="utf-8"?>
<D:propertyupdate xmlns:D="DAV:" xmlns:PREFIX="NAMESPACE_URI">
  <D:set>
    <D:prop>
      <PREFIX:localName>value</PREFIX:localName>
    </D:prop>
  </D:set>
</D:propertyupdate>
```

**Key rules:**
- The namespace declaration (`xmlns:PREFIX`) appears on the root `<D:propertyupdate>` element, not on the property element itself
- The property element contains only the plain text value
- Use `D:` prefix for DAV: namespace elements (`propertyupdate`, `set`, `prop`)

## Friendly Title Generation

When setting `schema:name` without an explicit value, generate a human-readable title from the filename:

1. Strip the file extension
2. Replace `%20`, `_`, and `-` with spaces
3. Collapse multiple spaces to single space
4. Title-case each word
5. Append a type tag based on extension:
   - `.pdf` → `(PDF)`
   - `.mp4`, `.mkv`, `.webm` → `(Video)`
   - `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg` → `(Image)`
   - `.wav`, `.mp3`, `.m4a` → `(Audio)`
   - `.html`, `.htm` → `(WebPage)`
   - Other → no tag

**Examples:**
- `ai-compute-race-3-tiers.pdf` → `Ai Compute Race 3 Tiers (PDF)`
- `quarterly_report_2026.xlsx` → `Quarterly Report 2026`
- `product%20demo.mp4` → `Product Demo (Video)`

## XML Escaping

When property values contain special characters, escape them:

| Character | Escape |
|-----------|--------|
| `&` | `&amp;` |
| `<` | `&lt;` |
| `>` | `&gt;` |
| `'` | `&apos;` |
| `"` | `&quot;` |

## Error Handling

- **HTTP 207 Multi-Status:** PROPPATCH succeeded (standard WebDAV response)
- **HTTP 401 Unauthorized:** Check credentials
- **HTTP 404 Not Found:** Resource path is incorrect
- **HTTP 405 Method Not Allowed:** Server does not support PROPPATCH
- **HTTP 423 Locked:** Resource is locked; unlock first or use Lock token header

## Scripts

- **`scripts/set-webdav-resource-property.sh`** — Full-featured shell script wrapping the curl PROPPATCH logic with argument parsing, batch processing, verbose mode, and namespace resolution.

## Getting Started

1. Identify the WebDAV server base URL and your credentials
2. Determine which property you want to set (e.g., `schema:name`, `dc:title`)
3. List the resource paths you want to update
4. Run the curl PROPPATCH commands or use the bundled script
5. Verify with PROPFIND

## Examples

### Set schema:name on a single file

```bash
curl -u "demo:demo" -X PROPPATCH "https://linkeddata.uriburner.com/dav/home/demo/docs/presentation.mp4" \
  -H "Content-Type: application/xml; charset=utf-8" \
  --data '<?xml version="1.0" encoding="utf-8"?>
<D:propertyupdate xmlns:D="DAV:" xmlns:schema="http://schema.org/">
  <D:set>
    <D:prop>
      <schema:name>Presentation (Video)</schema:name>
    </D:prop>
  </D:set>
</D:propertyupdate>'
```

### Set dc:title with custom namespace

```bash
curl -u "demo:demo" -X PROPPATCH "https://linkeddata.uriburner.com/dav/home/demo/docs/article.html" \
  -H "Content-Type: application/xml; charset=utf-8" \
  --data '<?xml version="1.0" encoding="utf-8"?>
<D:propertyupdate xmlns:D="DAV:" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <D:set>
    <D:prop>
      <dc:title>Article (WebPage)</dc:title>
    </D:prop>
  </D:set>
</D:propertyupdate>'
```

### Batch set with the bundled script

```bash
./scripts/set-webdav-resource-property.sh \
  -u demo -p demo -b https://linkeddata.uriburner.com \
  -f paths.txt -n schema:name -v
```

Where `paths.txt` contains:
```
/dav/home/demo/docs/report.pdf
/dav/home/demo/docs/presentation.mp4
/dav/home/demo/docs/article.html
```
