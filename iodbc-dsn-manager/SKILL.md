---
name: iodbc-dsn-manager
description: Configure and verify ODBC Data Source Names (DSNs) using iODBC or unixODBC. Supports three execution modes in priority order: (C) OpenLink `www_sv` Admin Assistant HTTP server — preferred when available; (B) `odbc_rest_server.py` REST bridge — for remote/sandbox access; (A) local CLI via `iodbctest`/`isql`. Works on macOS and Linux. Covers all DSN types: MT (Multi-Tier), Virtuoso, Unix Lite, and single-tier. Use when the user asks to list, test, configure, add, or troubleshoot ODBC DSNs.
---

# ODBC DSN Manager Skill
## iODBC + unixODBC · macOS + Linux · www_sv · REST · Local CLI

## Purpose
Manage and verify ODBC Data Source Names using the best available interface — automatically selected in this priority order:

| Priority | Mode | When to use |
|---|---|---|
| **1 (preferred)** | **C — OpenLink Admin Assistant** | `www_sv` running (or startable) on port `8000` |
| **2** | **B — REST bridge** | `odbc_rest_server.py` running on the target machine |
| **3 (fallback)** | **A — Local CLI** | Claude Code running directly on the ODBC machine |

---

## Execution Routing

Default execution order for remote or REST interactions:

1. **Mode C (HTTP Admin Assistant)** — `www_sv` at `http://localhost:8000` (preferred when available)
2. **Mode B (REST bridge)** — `odbc_rest_server.py` REST endpoint
3. **Terminal-owned OAuth flow** — when a REST endpoint requires OAuth 2.0 authentication, execute the OAuth flow from the terminal (authorization code, client credentials, or device flow), capture the Bearer token, and inject it into subsequent REST/OpenAPI calls via `Authorization: Bearer {token}` headers
4. **Mode A (Local CLI)** — direct `iodbctest`/`isql` invocation
5. **MCP** — if an MCP-enabled Virtuoso instance is available for remote DSN operations

If the user names a specific mode or protocol, follow that preference instead.

---

## Step 0 — Mode Detection (Always Run First)

Run these checks in order and stop at the first match:

```bash
# 1. Check for www_sv (Mode C — preferred)
curl -s http://localhost:8000/ | grep -i "openlink\|admin assistant" | head -3

# 2. Check for www_sv binary (can we start it?)
ls "/Library/Application Support/openlink/bin/www_sv" 2>/dev/null

# 3. Check for local ODBC config (Mode A)
uname -s
ls /Library/ODBC/odbc.ini 2>/dev/null || ls /etc/odbc.ini 2>/dev/null
which iodbctest isql 2>/dev/null
```

**Decision logic:**
- www_sv responds at port 8000 → **Mode C**
- www_sv binary exists but not running → **ask user to start it** → if yes, start and use **Mode C**
- Local ODBC config and binaries found → **Mode A**
- Neither → ask user for REST server URL → **Mode B**

**Starting www_sv (if binary found but not running):**
```bash
nohup "/Library/Application Support/openlink/bin/www_sv" > /tmp/www_sv.log 2>&1 &
sleep 2 && curl -s http://localhost:8000/ | grep -i openlink
```

---

## Mode C — www_sv Admin Assistant (Preferred)

OpenLink's built-in HTTP configuration server. Provides wizard-based DSN management for all DSN types (MT, Virtuoso, Unix Lite) via a web interface backed by Tcl scripts that read/write `odbc.ini` directly.

**Base URL:** `http://localhost:8000`
**Auth:** HTTP Basic — ask user for credentials at start of session. Never store or write passwords to disk.
**→ Full endpoint reference:** Read `references/www_sv-endpoints.md`
**→ MT DSN parameters and server type templates:** Read `references/mt-dsn-parameters.md`

### C1. List All DSNs
```bash
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/odbcdsn
```
Parse the HTML response for DSN names and driver assignments. Present as a table grouped by DSN type (MT / Virtuoso / Unix Lite / other).

### C2. Inspect a DSN
```bash
curl -s -u <uid>:<pwd> "http://localhost:8000/scripts/odbcdsn?dsn=<name>"
```
Extract and display all parameters for the named DSN.

### C3. Create a DSN (Wizard Flow)

Step through the four wizard tabs, collecting parameters:

| Tab | Endpoint | Collects |
|---|---|---|
| 1 — Data Source | `/scripts/wods` | DSN name, Driver |
| 2 — Server Type | `/scripts/wost` | ServerType (from 70+ templates) |
| 3 — Communication | `/scripts/woco` | Host, Port, UseSSL |
| 4 — Options | `/scripts/wod` | Database, FetchBufferSize, ReadOnly, DeferLongFetch |

```bash
# Submit completed DSN form
curl -s -u <uid>:<pwd> -X POST http://localhost:8000/scripts/odbcdsn \
  -d "action=add&dsn=<name>&driver=<driver>&Host=<host>&Port=<port>&ServerType=<type>&Database=<db>"
```

For Virtuoso DSNs use the VIRT parameters (`Address=host:port`) instead of MT parameters.
For Unix Lite DSNs use `/scripts/udbcdsn`.

**→ Full parameter list by DSN type:** Read `references/mt-dsn-parameters.md`

### C4. Edit a DSN
```bash
curl -s -u <uid>:<pwd> -X POST http://localhost:8000/scripts/odbcdsn \
  -d "action=edit&dsn=<name>&<param>=<value>..."
```

### C5. Test a DSN
```bash
# Connection test
curl -s -u <uid>:<pwd> "http://localhost:8000/scripts/dsntest?dsn=<name>&uid=<u>&pwd=<p>"

# Interactive SQL test
curl -s -u <uid>:<pwd> "http://localhost:8000/scripts/oplisql?dsn=<name>&uid=<u>&pwd=<p>&sql=SELECT+'Connected'"
```

### C6. List Available Server Type Templates
```bash
# Templates are in the include directory — read directly
python3 -c "
import configparser
cfg = configparser.RawConfigParser()
cfg.read('/Library/Application Support/openlink/bin/w3config/include/template.ini')
for s in cfg.sections():
    print(s)
"
```

### C7. Request Broker Administration
```bash
# View broker config
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brksetup

# View broker logs
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brklog

# Broker version
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brkver
```

---

## Mode B — REST Bridge (`odbc_rest_server.py`)

Use when `www_sv` is not available and Claude is running remotely (sandbox / Linux). The target machine must be running `server/odbc_rest_server.py`.

Ask the user for the base URL (e.g., `http://192.168.1.10:8899`), then use `WebFetch`.

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `GET` | `/info` | Driver manager versions + config paths |
| `GET` | `/dsns` | All DSNs (system + user) |
| `GET` | `/dsn/<name>` | Inspect one DSN (URL-encode spaces as `%20`) |
| `GET` | `/drivers` | All installed drivers |
| `GET` | `/driver/<name>` | Inspect one driver |
| `POST` | `/test` | Test connectivity — body: `{"dsn":"...","uid":"...","pwd":"...","query":"..."}` |

### Start the REST server (on the ODBC machine)
```bash
python3 /usr/local/share/odbc-rest-server/odbc_rest_server.py --host 0.0.0.0 --port 8899
```

### Install as `launchd` service (macOS)
```bash
sudo mkdir -p /usr/local/var/log
cp server/com.openlink.odbc-rest-server.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.openlink.odbc-rest-server.plist
curl http://127.0.0.1:8899/health
```

> **Security note:** Bind to `127.0.0.1` by default. Use `--host 0.0.0.0` on trusted networks only.

---

## Mode A — Local CLI (Fallback)

Claude Code running directly on the machine with ODBC binaries installed.

### A0. OS Detection
```bash
OS=$(uname -s)   # Darwin = macOS, Linux = Linux
which iodbctest isql odbcinst 2>/dev/null
```

### Platform Paths

| Resource | macOS | Linux |
|---|---|---|
| System DSNs | `/Library/ODBC/odbc.ini` | `/etc/odbc.ini` |
| System Drivers | `/Library/ODBC/odbcinst.ini` | `/etc/odbcinst.ini` |
| User DSNs | `~/Library/ODBC/odbc.ini` | `~/.odbc.ini` |
| Driver format | `.bundle` | `.so` |
| iODBC test — ANSI | `/usr/local/iODBC/bin/iodbctest` | `iodbctest` |
| iODBC test — Unicode | `/usr/local/iODBC/bin/iodbctestw` | `iodbctestw` |
| unixODBC test — ANSI | `isql` | `isql` |
| unixODBC test — Unicode | `iusql` | `iusql` |
| Config confirm | `iodbc-config --prefix` | `odbcinst -j` |

### A1. List DSNs
Read `[ODBC Data Sources]` section from the correct `odbc.ini` using the Read tool or Python:
```bash
python3 -c "
import configparser
cfg = configparser.RawConfigParser()
cfg.read('/Library/ODBC/odbc.ini')
for k, v in cfg.items('ODBC Data Sources'):
    print(f'{k} = {v}')
"
```

### A2. Inspect a DSN
```bash
python3 -c "
import configparser
cfg = configparser.RawConfigParser()
cfg.read('/Library/ODBC/odbc.ini')
for k, v in cfg.items('My DSN'):
    print(f'{k} = {v}')
"
```

### A3. Test Connectivity

**iODBC:**
```bash
# ANSI
printf "SELECT 'Connected'\nquit\n" | /usr/local/iODBC/bin/iodbctest "DSN=<name>;UID=<u>;PWD=<p>"
# Unicode:
printf "SELECT 'Connected'\nquit\n" | /usr/local/iODBC/bin/iodbctestw "DSN=<name>;UID=<u>;PWD=<p>"
```

**unixODBC:**
```bash
# ANSI
echo "SELECT 'Connected'" | isql "<name>" <uid> <pwd> -b
# Unicode:
echo "SELECT 'Connected'" | iusql "<name>" <uid> <pwd> -b
# Wide output (full IRIs):
echo "SELECT 'Connected'" | isql "<name>" <uid> <pwd> -b -m 200
```

### A4. Add or Edit a DSN
Edit `/Library/ODBC/odbc.ini` (macOS) or `/etc/odbc.ini` (Linux) using the Edit tool.
Always add to both `[ODBC Data Sources]` and as a named `[DSN Name]` section.

### A5. Driver Info
```bash
/usr/local/iODBC/bin/iodbc-config --version --libs --cflags   # iODBC
odbcinst -j                                                   # unixODBC
```

---

## SPASQL (SPARQL via ODBC)

Virtuoso DSNs support SPARQL issued directly over ODBC by prefixing with `SPARQL` keyword:

```bash
# Via isql (wide output for full IRIs, then apply CURIEs in post-processing)
printf "SPARQL PREFIX foaf: <http://xmlns.com/foaf/0.1/> SELECT * WHERE { ?s a foaf:Person } LIMIT 10\nquit\n" \
  | isql "<DSN>" <uid> <pwd> -b -m 200
```

Always post-process full IRI output with Python to apply CURIE substitutions before presenting results.

---

## Troubleshooting Guide

| Symptom                         | Likely Cause                 | Fix                                          |
|---                              |---                           |---                                           |
| `www_sv` not responding         | Not started                  | Start binary or check port 8000              |
| `www_sv` auth fails             | Wrong admin password         | Check `www_sv.ini` `[Users]` section         |
| `Data source name not found`    | DSN not in `odbc.ini`        | Add DSN via Mode C wizard or Edit tool       |
| `Driver not found`              | Driver path wrong            | Check `.bundle` (macOS) / `.so` (Linux) path |
| `[28000] Login failed`          | Wrong UID/PWD                | Correct credentials                          |
| `[08001] Can't connect`         | Host/port unreachable        | Check server/broker is running               |
| `[IM004] SQLAllocHandle failed` | Driver binary bad/wrong arch | Reinstall driver                             |
| `Can't open lib` (Linux)        | `.so` path wrong             | Check `odbcinst.ini` Driver= path            |
| wrong unixODBC config           | Different path active        | Run `odbcinst -j` to confirm                 |
| REST bridge unreachable         | Server not started           | Run `odbc_rest_server.py` on target host     |

---

## Quick Reference

| Task                  | Mode C (`www_sv`)                                    | Mode A (Local CLI)                    |
|---                    |---                                                   |---                                    |
| List DSNs             | `curl .../scripts/odbcdsn`                           | Read `odbc.ini` `[ODBC Data Sources]` |
| Inspect DSN           | `curl .../scripts/odbcdsn?dsn=<name>`                | Read named section from `odbc.ini`    |
| Test connection       | `curl .../scripts/dsntest?dsn=...`                   | `iodbctest` / `isql`                  |
| Create DSN            | Wizard via `/scripts/wods` → `wost` → `woco` → `wod` | Edit `odbc.ini`                       |
| Server type templates | `/scripts/wost` or `template.ini`                    | `references/mt-dsn-parameters.md`     |
| Broker admin          | `/scripts/brksetup`, `/scripts/brklog`               | N/A                                   |
| SPASQL                | `isql` with `SPARQL ...` prefix                      | Same                                  |
| iODBC version         | `iodbc-config --version`                             | Same                                  |
| unixODBC paths        | `odbcinst -j`                                        | Same                                  |

---

## Initialization Sequence

When invoked:
1. Run Mode detection (Step 0) — check `www_sv`, then local ODBC, then ask for REST URL
2. If `www_sv` binary found but not running: **ask user** "`www_sv` is installed but not running — start it?" → start if yes
3. Report detected mode, OS, available driver managers, config paths
4. Obtain `www_sv` credentials if Mode C (session only — never written to disk)
5. List all DSNs grouped by type — present as a table
6. Ask what to do: **list**, **inspect**, **create**, **edit**, **test**, **broker admin**, or **troubleshoot**
7. Execute using the selected mode throughout the session

---

## Reference Files

| File                                         | Contents |
|---                                           |---|
| `references/www_sv-endpoints.md`             | `www_sv` HTTP endpoints, auth, form parameters, start/stop |
| `references/mt-dsn-parameters.md`            | MT/VIRT/ULITE DSN parameters, 70+ server type templates, driver paths |
| `references/odbc-error-codes.md`             | SQLSTATE error codes and fixes |
| `references/connection-string-formats.md`    | Connection string syntax for all driver types |
| `server/odbc_rest_server.py`                 | Python REST bridge for Mode B remote access |
| `server/com.openlink.odbc-rest-server.plist` | launchd service definition for REST bridge |

---

## Version
**2.0.0** — Enhanced with Mode C (www_sv Admin Assistant) as preferred execution mode. All DSN types supported (MT, Virtuoso, Unix Lite). Modes: C (www_sv) → B (REST bridge) → A (local CLI).
