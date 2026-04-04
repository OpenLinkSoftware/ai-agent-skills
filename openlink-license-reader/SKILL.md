---
name: openlink-license-reader
description: "Read and display OpenLink Software license files (.lic) in a beautified, human-readable format. Parses ASN.1 DER-encoded license files using openssl, extracts all license fields, flags expired licenses visually, and supports single-file or directory-wide scanning. Use when the user asks to read, inspect, check, or list OpenLink license files."
---

# OpenLink License Reader Skill

## Purpose
Parse and display OpenLink `.lic` files (ASN.1 DER-encoded) in a clean, human-readable format using `openssl asn1parse`. Flags expired licenses. Supports single file or full directory scan.

---

## Execution Routing

Default execution order when REST or remote access is needed:

1. **Local execution** — parse license files directly using `openssl asn1parse` (primary mode)
2. **URIBurner REST functions** — for remote license validation or registry lookups
3. **Terminal-owned OAuth flow** — when a REST endpoint requires OAuth 2.0 authentication, execute the OAuth flow from the terminal (authorization code, client credentials, or device flow), capture the Bearer token, and inject it into subsequent REST/OpenAPI calls via `Authorization: Bearer {token}` headers
4. **MCP** — if a remote MCP-enabled service exposes license validation tools

If the user names a specific mode or protocol, follow that preference instead.

---

## Step 0 — Locate License File(s)

Resolve the target in this priority order:

| Priority | Source | Detail |
|---|---|---|
| 1 | **Explicit filename** | User provides a path — use as-is, skip all other steps |
| 2 | **`$OPL_LICENSE_DIR`** | Check env var; scan that directory for `*.lic` files |
| 3 | **OS default path** | See table below |

### OS Default License Paths

| OS | Default Path |
|---|---|
| macOS | `/Library/Application Support/openlink/Licenses` |
| Linux | `/etc/oplmgr/` |
| Windows | `C:\Program Files\OpenLink Software\UDA\bin\` |

```bash
# Detect OS
uname -s   # Darwin = macOS, Linux = Linux

# Check env var
echo $OPL_LICENSE_DIR

# List license files in resolved directory
ls "/Library/Application Support/openlink/Licenses/"*.lic 2>/dev/null
```

If multiple `.lic` files are found and no specific file was requested:
- **Default:** scan all and produce a summary table (one row per file)
- **On request:** inspect a single named file in full detail

---

## Step 1 — Parse the License File

```bash
openssl asn1parse -in "{license-file}" -i -inform der
```

> Do NOT use `-dump` unless the user explicitly asks to see the raw hex dump.

Parse the output with Python to extract all key-value pairs:

```python
import subprocess, re, sys
from datetime import datetime

def parse_license(filepath):
    result = subprocess.run(
        ['openssl', 'asn1parse', '-in', filepath, '-i', '-inform', 'der'],
        capture_output=True, text=True
    )
    lines = result.stdout.splitlines()
    fields = {}
    product = None
    i = 0
    while i < len(lines):
        line = lines[i]
        # Product name: second PRINTABLESTRING at depth 2, before the fields SEQUENCE
        if not product and 'd=2' in line and 'PRINTABLESTRING' in line:
            m = re.search(r'PRINTABLESTRING\s+:(.*)', line)
            if m:
                product = m.group(1).strip()
        # Key-value pairs: consecutive PRINTABLESTRING at depth 4
        if 'd=4' in line and 'PRINTABLESTRING' in line:
            m = re.search(r'PRINTABLESTRING\s+:(.*)', line)
            if m:
                key = m.group(1).strip()
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if 'd=4' in next_line and 'PRINTABLESTRING' in next_line:
                        mv = re.search(r'PRINTABLESTRING\s+:(.*)', next_line)
                        if mv:
                            fields[key] = mv.group(1).strip()
                            i += 2
                            continue
        i += 1
    return product, fields
```

**→ Full field reference and decode tables:** Read `references/asn1-field-map.md`

---

## Step 2 — Beautified Single-File Output

Present all extracted fields as a formatted table. Apply decode tables from `references/asn1-field-map.md` for `WSType`, `Availability`, `Platform`, and `Modules`.

### Status Logic

```python
from datetime import datetime

def license_status(expire_date_str):
    if not expire_date_str or expire_date_str.strip() == '':
        return '**PERPETUAL**'
    try:
        # Format: "Thu Mar 18 00:00:00 2027 GMT"
        dt = datetime.strptime(expire_date_str.strip(), '%a %b %d %H:%M:%S %Y %Z')
        if dt < datetime.utcnow():
            return '**EXPIRED** ⚠️'
        else:
            days = (dt - datetime.utcnow()).days
            return f'**ACTIVE** (expires in {days} days)'
    except Exception:
        return expire_date_str
```

### Output Format

```
## License: virtuoso.lic

| Field              | Value                                                        |
|--------------------|--------------------------------------------------------------|
| Product            | virtuoso                                                     |
| Registered To      | https://my.openlinksw.com/dataspace/person/kidehen@...       |
| Serial Number      | GNvyBBRU/MTaRKMt8KlcQC0jdUM=                                |
| Release            | 8.3                                                          |
| Edition            | Enterprise (WSType=3)                                        |
| Availability       | Enabled                                                      |
| Platform           | Any (_ANY_)                                                  |
| Users              | 20                                                           |
| Connections        | 20                                                           |
| CPUs               | 128                                                          |
| Modules            | COLUMNSTORE, CLUSTER, ABAC, BI, REPL, VAL, VDB, SPIN        |
| Clients            | ODBC, JDBC, OLEDB, DOTNET, XMLA                              |
| Disable SNBC       | Yes                                                          |
| Unique ID          | B9C96F39D0985C6A002612A5BF503E33                             |
| Expire Date        | **PERPETUAL**                                                |

Status: **PERPETUAL**
```

For expired licenses, the Status line reads:
```
Status: **EXPIRED** ⚠️  (expired: Thu Mar 18 00:00:00 2023 GMT)
```

---

## Step 3 — Directory Summary Mode

When scanning a directory, produce a compact summary table:

```
| File              | Product   | Registered To              | Release | Edition    | Connections | Expires                      | Status        |
|-------------------|-----------|----------------------------|---------|------------|-------------|------------------------------|---------------|
| virtuoso.lic      | virtuoso  | kidehen@openlinksw.com     | 8.3     | Enterprise | 20          | Perpetual                    | **PERPETUAL** |
| oplrqb.lic        | oplrqb    | OpenLink Internal Use      | 10.0    | Enterprise | 100         | Thu Mar 18 00:00:00 2027 GMT | **ACTIVE**    |
| oracle19.lic      | oracle19  | OpenLink Internal Use      | 9.0     | Enterprise | 50          | Thu Mar 18 00:00:00 2023 GMT | **EXPIRED** ⚠️|
```

Sort order: EXPIRED first (to draw attention), then ACTIVE, then PERPETUAL.

---

## Step 4 — Raw Dump (On Request Only)

Only show the raw `openssl asn1parse` output if the user explicitly asks ("show raw", "show dump", "show ASN.1"):

```bash
openssl asn1parse -in "{license-file}" -i -dump -inform der
```

Present as a fenced code block.

---

## Initialization Sequence

When invoked:
1. Run Step 0 — resolve license file(s)
2. If single file resolved (explicit path or user selection): run Steps 1–2 (full detail)
3. If directory resolved with multiple files: run Step 3 (summary table), then offer to inspect any individual file
4. Always offer: "Show raw ASN.1 dump?" after displaying results

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `openssl: command not found` | openssl not installed | Install via `brew install openssl` (macOS) or `apt install openssl` (Linux) |
| `unable to load` error | File not DER-encoded or corrupted | Verify file is a valid `.lic` file |
| `error reading` | Wrong path or permissions | Check path and `ls -l` the file |
| All fields empty | Wrong `-inform` (try `-inform pem`) | Try both `der` and `pem` |
| `ExpireDate` blank | Perpetual license | Treat as no expiry — display **PERPETUAL** |

---

## Reference Files

| File | Contents |
|---|---|
| `references/asn1-field-map.md` | All known OpenLink ASN.1 license fields with decode tables for WSType, Availability, Platform, Modules |
| `references/openssl-asn1parse-guide.md` | How to interpret raw openssl asn1parse output; depth/indentation meaning |

---

## Version
**1.0.0** — Initial release. Single-file and directory scan modes. ASN.1 DER parsing via openssl. Beautified output with expiry status, edition decode, and module/client lists.
