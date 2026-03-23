# iODBC / unixODBC DSN Manager Skill

Configure and verify ODBC Data Source Names (DSNs) using the iODBC or unixODBC Driver Manager on **macOS or Linux**.

## Overview

This Claude Code skill lets you manage ODBC connectivity through natural language. It:

1. Lists all configured DSNs from `odbc.ini`
2. Inspects DSN and driver configuration details
3. Tests live connectivity using `iodbctest` (iODBC) or `isql` (unixODBC)
4. Adds or edits DSN entries in `odbc.ini`
5. Troubleshoots connection failures with diagnostic guidance

## Supported Driver Managers

| Driver Manager | Test Binary | Config Tool |
|---|---|---|
| iODBC | `iodbctest` / `iodbctestw` | `iodbc-config` |
| unixODBC | `isql` / `iusql` | `odbcinst` |

The skill auto-detects the OS at invocation time (`uname -s`) and selects the correct paths, binaries, and driver formats automatically.

### OS-specific config paths

| Resource | macOS | Linux |
|---|---|---|
| System DSNs | `/Library/ODBC/odbc.ini` | `/etc/odbc.ini` |
| System Drivers | `/Library/ODBC/odbcinst.ini` | `/etc/odbcinst.ini` |
| User DSNs | `~/Library/ODBC/odbc.ini` | `~/.odbc.ini` |
| Driver format | `.bundle` | `.so` |
| Default driver manager | iODBC | unixODBC |

## Installation

```bash
# Copy to Claude Code skills directory
cp -r iodbc-dsn-manager ~/.claude/skills/
```

Or load the ZIP bundle directly from its local path when prompted by Claude.

## Usage

### List all DSNs
```
User: "List all my ODBC DSNs"
Skill: Reads /Library/ODBC/odbc.ini and presents a DSN → Driver table
```

### Test a DSN
```
User: "Test the Local Virtuoso DSN"
Skill: Runs iodbctest with the DSN connection string and reports success or error
```

### Inspect a DSN
```
User: "Show me the config for the Demo DSN"
Skill: Extracts and displays the [Demo] section from odbc.ini
```

### Add a new DSN
```
User: "Add a DSN called MyPostgres pointing to localhost:5432"
Skill: Edits odbc.ini to add the entry with correct driver reference
```

### Troubleshoot
```
User: "Why can't I connect to the AWS MySQL DSN?"
Skill: Checks config, verifies driver binary, tests connection, reports findings
```

## Features

- Works with both iODBC and unixODBC driver managers
- Reads system (`/Library/ODBC/`) and user (`~/Library/ODBC/`) DSN configs
- Tests connectivity non-interactively (batch mode)
- Unicode driver support via `iodbctestw` / `iusql`
- Driver binary verification
- Structured troubleshooting for common ODBC errors

## File Structure

```
iodbc-dsn-manager/
├── SKILL.md                          # Main skill definition
├── README.md                         # This file
└── references/
    ├── odbc-error-codes.md           # Common ODBC error codes and fixes
    └── connection-string-formats.md  # Connection string syntax reference
```

## System Paths (macOS)

| Resource | Path |
|---|---|
| System DSNs | `/Library/ODBC/odbc.ini` |
| System Drivers | `/Library/ODBC/odbcinst.ini` |
| User DSNs | `~/Library/ODBC/odbc.ini` |
| iODBC binaries | `/usr/local/iODBC/bin/` |
| iODBC framework | `/Library/Frameworks/iODBC.framework` |
| unixODBC binaries | `/opt/homebrew/bin/` |

## Common Use Cases

1. **Verify Virtuoso connectivity** before running SPARQL/SQL queries
2. **Debug connection failures** in ODBC-dependent applications
3. **Add remote database DSNs** for cloud databases (Azure, AWS RDS, etc.)
4. **Inspect driver configuration** when an application can't load a driver
5. **Compare iODBC vs unixODBC** behavior for the same DSN

## Limitations

- macOS only (paths and driver bundle format are macOS-specific)
- Requires iODBC or unixODBC to be installed
- Cannot modify driver binaries — only config files
- Write operations require permission on `/Library/ODBC/odbc.ini`

## Version

1.0.0

## License

This skill is provided as-is for use with Claude Code.
