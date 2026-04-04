---
name: openlink-request-broker-configurator
description: "Configure and manage the OpenLink Request Broker (oplrqb) rule book
  (oplrqb.ini). Primary use: configure ODBC Agent rules from host DSNs and JDBC Agent
  rules from discovered JDBC driver JARs. Also covers general Mapping Rules, DB Agent
  sections (generic_*), Environment sections, broker global settings, alias sections,
  reinit/restart, log viewing, and version detection. Two modes: (C) www_sv HTTP Admin
  Assistant on port 8000 — preferred; (A) direct file edit + CLI — fallback. Use when
  the user asks to configure ODBC or JDBC agents, add or edit mapping rules, view or
  edit the broker rule book, restart or reinitialize the broker."
---

# OpenLink Request Broker Configurator Skill

## Purpose

Configure and manage the OpenLink Request Broker (`oplrqb`) rule book (`oplrqb.ini`). The rule book controls:
- **Mapping Rules** — which DB agent handles each incoming connection request
- **`[generic_<name>]` sections** — per-agent program, environment, and connection defaults
- **`[Environment <type>]`sections** — OS environment variables injected into each agent process
- **Broker global settings** — port, timeouts, security, protocol parameters

Primary use cases: configure ODBC Agent rules from host-installed DSNs and JDBC Agent rules from discovered JDBC driver JARs.

**→ Full parameter reference:** Read `references/rulebook-structure.md`
**→ www_sv endpoint reference:** Read `references/broker-www_sv-endpoints.md`
**→ JDBC driver registry:** Read `references/jdbc-driver-registry.md`
**→ ODBC DSN examples and token naming:** Read `references/odbc-dsn-examples.md`

---

## Execution Routing

Default execution order:

1. **Mode C (www_sv)** — HTTP Admin Assistant at `http://localhost:8000` (preferred when available)
2. **Mode A (direct file edit + CLI)** — edit `oplrqb.ini` directly and use `oplrqb` CLI commands
3. **Terminal-owned OAuth flow** — when a REST endpoint requires OAuth 2.0 authentication, execute the OAuth flow from the terminal (authorization code, client credentials, or device flow), capture the Bearer token, and inject it into subsequent REST/OpenAPI calls via `Authorization: Bearer {token}` headers
4. **MCP** — if a remote MCP-enabled Virtuoso instance exposes broker management tools

If the user names a specific mode or protocol, follow that preference instead.

---

## Step 0 — Mode Detection

Always run first.

```bash
# 1. Is www_sv responding? (Mode C)
curl -s http://localhost:8000/ | grep -i "openlink\|admin" | head -3

# 2. Is www_sv binary present but not running?
ls "/Library/Application Support/openlink/bin/www_sv" 2>/dev/null   # macOS
ls /opt/openlink/bin/www_sv 2>/dev/null                              # Linux

# 3. Is the rulebook directly accessible? (Mode A)
ls "/Library/Application Support/openlink/bin/oplrqb.ini" 2>/dev/null  # macOS
ls /opt/openlink/bin/oplrqb.ini 2>/dev/null                             # Linux
```

**Decision:**
- www_sv responds at port 8000 → **Mode C**
- www_sv binary found but not running → ask user "www_sv is installed but not running — start it?" → if yes, start it (see below) → **Mode C**
- Rulebook file accessible but www_sv unavailable → **Mode A**
- Neither → ask user which path to take

**Starting www_sv (macOS):**
```bash
nohup "/Library/Application Support/openlink/bin/www_sv" > /tmp/www_sv.log 2>&1 &
sleep 2 && curl -s http://localhost:8000/ | grep -i openlink
```

**Credentials:** www_sv uses HTTP Basic Authentication. Prompt for `uid` and `pwd` once at session start. Never write credentials to disk.

---

## Platform Paths

| Resource | macOS | Linux |
|---|---|---|
| Rule book | `/Library/Application Support/openlink/bin/oplrqb.ini` | `/opt/openlink/bin/oplrqb.ini` |
| Broker binary | `/Library/Application Support/openlink/bin/oplrqb` | `/opt/openlink/bin/oplrqb` |
| Shutdown util | `/Library/Application Support/openlink/bin/oplshut` | `/opt/openlink/bin/oplshut` |
| inicheck util | `/Library/Application Support/openlink/bin/inicheck` | `/opt/openlink/bin/inicheck` |
| Log (default) | `/Library/Application Support/openlink/bin/oplrqb.log` | `/opt/openlink/bin/oplrqb.log` |
| www_sv binary | `/Library/Application Support/openlink/bin/www_sv` | `/opt/openlink/bin/www_sv` |
| ODBC config (system) | `/Library/ODBC/odbc.ini` | `/etc/odbc.ini` |
| ODBC config (user) | `~/Library/ODBC/odbc.ini` | `~/.odbc.ini` |

---

## Mode C — www_sv HTTP Admin Assistant (Preferred)

Base URL: `http://localhost:8000`
Auth: `-u <uid>:<pwd>` on every curl call.

### C1. Discover Host DSNs (for ODBC Agent wizard)

```bash
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/odbcdsn
```

Parse the HTML response to extract DSN names, or use Mode A's configparser approach for a clean list.

### C2. View Full Rulebook (plain text)

```bash
curl -s -u <uid>:<pwd> "http://localhost:8000/scripts/brkbook?mode=plain"
```

Parse with Python `configparser.RawConfigParser(strict=False, delimiters=('=',))`.

Download as file:
```bash
curl -s -u <uid>:<pwd> "http://localhost:8000/scripts/brkbook?mode=save" -o /tmp/oplrqb_backup.ini
```

### C3. View / Edit Broker Global Settings

```bash
# View
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brksetup

# Edit — POST changed keys
curl -s -u <uid>:<pwd> -X POST http://localhost:8000/scripts/brksetup \
  -d "BinaryDirectory=%2FLibrary%2FApplication+Support%2Fopenlink%2Fbin&Listen=5001&MaxAgents=0&HostNameResolver=Yes"
```

**POST fields:** `BinaryDirectory`, `Listen`, `MaxAgents`, `MaxConnections`, `HostNameResolver`, `LingerTimeout`, `PingWatchdog`, `PingInterval`, `SendSize`, `ReceiveSize`, `BrokerTimeout`, `StartupBy`, `ShutdownBy`, `ShutdownFrom`

### C4. View / Edit DB Agent Sections

```bash
# List all agent sections
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brkagents

# View one agent
curl -s -u <uid>:<pwd> "http://localhost:8000/scripts/brkagents?agent=generic_odbc"

# Edit an agent — POST
curl -s -u <uid>:<pwd> -X POST http://localhost:8000/scripts/brkagents \
  -d "agent=generic_odbc_MyDSN&Program=odbc_mv&Environment=ODBC&ReUse=always&Database=MyDSN&Description=ODBC+agent+for+MyDSN"
```

**POST fields:** `agent`, `Program`, `Description`, `CommandLine`, `Directory`, `Database`, `UserID`, `Password`, `ConnectOptions`, `ReadOnly`, `ServerOptions`, `OpsysLogin`, `ReUse`, `Environment`, `SSLKeyFile`, `SSLRequired`

### C5. View / Edit Mapping Rules

```bash
# View
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brkmaped

# Add a rule
curl -s -u <uid>:<pwd> -X POST http://localhost:8000/scripts/brkmaped \
  -d "action=add&domain=odbc&db=MyDSN&uid=*&opsys=*&machine=*&appl=*&mode=*&target=generic_odbc_MyDSN"

# Delete a rule (by 1-based index)
curl -s -u <uid>:<pwd> -X POST http://localhost:8000/scripts/brkmaped \
  -d "action=delete&rule=<index>"
```

**Rule fields:** `domain`, `db`, `uid`, `opsys`, `machine`, `appl`, `mode`; `target` = `generic_<name>` for accept or a message for reject.

### C6. View / Edit Alias Sections

```bash
# View Domain Aliases
curl -s -u <uid>:<pwd> "http://localhost:8000/scripts/brkalias?atype=Domain+Aliases"

# Add a Domain Alias
curl -s -u <uid>:<pwd> -X POST http://localhost:8000/scripts/brkalias \
  -d "atype=Domain+Aliases&action=add&key=MyDB+JDBC&value=myjdbc"
```

Valid `atype` values: `Domain Aliases`, `Database Aliases`, `Opsys Aliases`, `Machine Aliases`, `Application Aliases`, `User Aliases`

### C7. Utility Endpoints

```bash
# Reinitialize broker (reload rulebook — preferred after edits)
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brkinit

# View broker log
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brklog

# Broker version
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brkver

# Active connections
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brkconn

# License info
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brklic
```

**Success detection:** POST responses contain "Configuration Updated" on success, "Sorry, this operation failed" on error.

---

## Mode A — Direct File Operations (Fallback)

### A1. Read Rulebook

```python
import configparser, os

RULEBOOK_PATHS = [
    '/Library/Application Support/openlink/bin/oplrqb.ini',  # macOS
    '/opt/openlink/bin/oplrqb.ini',                          # Linux
    '/etc/openlink/oplrqb.ini',                              # Linux alt
]

def read_rulebook():
    cfg = configparser.RawConfigParser(strict=False, delimiters=('=',))
    for path in RULEBOOK_PATHS:
        if os.path.exists(path):
            cfg.read(path)
            return cfg, path
    return None, None

cfg, path = read_rulebook()
for section in cfg.sections():
    print(f'\n[{section}]')
    for k, v in cfg.items(section):
        print(f'  {k} = {v}')
```

> **Important:** Use `RawConfigParser(strict=False, delimiters=('=',))`. The `[Mapping Rules]` section contains keys like `odbc:*:*:*:*:*:*` — colons in keys will confuse the default parser if colon is treated as a delimiter.

### A2. Discover Host DSNs (for ODBC Agent wizard)

```python
import configparser, os

def list_dsns():
    dsns = []
    paths = [
        '/Library/ODBC/odbc.ini',            # macOS system
        os.path.expanduser('~/Library/ODBC/odbc.ini'),  # macOS user
        '/etc/odbc.ini',                      # Linux system
        os.path.expanduser('~/.odbc.ini'),    # Linux user
    ]
    for p in paths:
        if os.path.exists(p):
            cfg = configparser.RawConfigParser(strict=False)
            cfg.read(p)
            for sec in cfg.sections():
                if sec.lower() not in ('odbc data sources',):
                    dsns.append(sec)
    return sorted(set(dsns))

print('\n'.join(list_dsns()))
```

### A3. Validate After Edits

Always run `inicheck` before attempting a broker reinit:

```bash
# macOS
"/Library/Application Support/openlink/bin/inicheck" \
  "/Library/Application Support/openlink/bin/oplrqb.ini"

# Linux
/opt/openlink/bin/inicheck /opt/openlink/bin/oplrqb.ini
```

Exit code 0 = valid. Any error output must be fixed before proceeding.

### A4. Editing Sections

Use the Read tool to read the rulebook, then the Edit tool to make targeted replacements. Prefer line-precise edits to preserve existing comments.

**Appending a new agent section** — add after the last `[generic_odbc*]` block:
```ini
[generic_odbc_MyDSN]
Description     = ODBC agent for MyDSN
Program         = odbc_mv
Environment     = ODBC
ReUse           = always
Database        = MyDSN
;Userid         =
;Password       =
;ReadOnly       = Yes
```

**Appending a new Environment section** — add after `[Environment ODBC]`:
```ini
[Environment JDBC_MyDriver]
CLASSPATH       = /path/to/mydriver.jar
```

**Adding a Mapping Rule** — insert before the `odbc:*:*:*:*:*:*` catch-all in `[Mapping Rules]`:
```ini
odbc:MyDSN:*:*:*:*:*         = accept generic_odbc_MyDSN
```

---

## ODBC Agent Configuration Wizard

When the user asks to configure ODBC agents:

### Step ODBC-1: Discover DSNs

**Mode C:**
```bash
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/odbcdsn
```
Parse HTML for DSN names, or parse odbc.ini directly (Mode A method above).

**Mode A:** Use `list_dsns()` Python snippet above.

### Step ODBC-2: Present List

Display discovered DSNs and ask: "Which DSNs should have dedicated ODBC Agent rules? Enter DSN names (comma-separated) or 'all' for a single catch-all rule."

### Step ODBC-3: Generate for Each Selected DSN

For each DSN `<dsnname>` (URL-encode spaces as `+` for POST, or use underscore-normalized names for section keys):

**Domain Alias** — add to `[Domain Aliases]` if not already present:
```ini
<dsnname>   = odbc_<normalized_name>
```
Where `<normalized_name>` is the DSN name lowercased with spaces replaced by underscores.

**Agent section** `[generic_odbc_<normalized_name>]`:
```ini
[generic_odbc_<normalized_name>]
Description     = ODBC agent for <dsnname>
Program         = odbc_mv
Environment     = ODBC
ReUse           = always
Database        = <dsnname>
```

**Mapping Rule** in `[Mapping Rules]` — insert before the existing `odbc:*:*:*:*:*:*` catch-all:
```ini
odbc:<dsnname>:*:*:*:*:*     = accept generic_odbc_<normalized_name>
```

### Step ODBC-4: Catch-all Fallback (if user selects "all")

Ensure this rule exists (it is in the default rulebook already):
```ini
odbc:*:*:*:*:*:*             = accept generic_odbc
```

And the stock `[generic_odbc]` section is present:
```ini
[generic_odbc]
Description     = Default settings for ODBC agent
Program         = odbc_mv
Environment     = ODBC
ReUse           = always
```

### Step ODBC-5: Reinitialize

After all changes: reinitialize the broker (see Step 6 below).

---

## JDBC Agent Configuration Wizard

When the user asks to configure JDBC agents:

### Step JDBC-1: Discover JDBC Driver JARs

```bash
# 1. Scan $CLASSPATH entries for JAR files
echo $CLASSPATH | tr ':' '\n' | grep '\.jar$'

# 2. Check common JAR directories if $CLASSPATH is unset or empty
for d in /usr/local/lib ~/lib /opt/jdbc /Library/Java/Extensions /usr/share/java; do
  ls "$d"/*.jar 2>/dev/null
done

# 3. Peek inside each JAR for JDBC SPI registration
# (run for each discovered JAR)
unzip -p <jar-path> META-INF/services/java.sql.Driver 2>/dev/null
```

### Step JDBC-2: Match JARs to Driver Registry

**→ Full registry with URL templates:** Read `references/jdbc-driver-registry.md`

Quick reference:

| JAR Pattern | Driver Class | Default JDBC Version |
|---|---|---|
| `virtuoso-jdbc*.jar` | `virtuoso.jdbc4.Driver` | JDBC 4 |
| `ojdbc*.jar` | `oracle.jdbc.OracleDriver` | JDBC 4 |
| `postgresql-*.jar` | `org.postgresql.Driver` | JDBC 4 |
| `mssql-jdbc-*.jar` | `com.microsoft.sqlserver.jdbc.SQLServerDriver` | JDBC 4 |
| `mysql-connector*.jar` | `com.mysql.cj.jdbc.Driver` | JDBC 4 |
| `ifxjdbc.jar` | `com.informix.jdbc.IfxDriver` | JDBC 4 |
| `openlink-jdbc*.jar` | `openlink.jdbc4.Driver` | JDBC 4 |

### Step JDBC-3: Present Discovered Drivers

List matched drivers and ask: "Which JDBC drivers should have agent rules? Enter numbers (comma-separated) or 'all'."

### Step JDBC-4: Prompt for URL Parameters

For each selected driver, display the URL template from the registry and prompt:
- Host (default: `localhost`)
- Port (default: driver-specific)
- Database/SID/Schema name

### Step JDBC-5: Generate for Each Selected Driver

Select the appropriate JDBC version slot. The rulebook has pre-defined slots `jdbc11` through `jdbc18`. Use the first unused slot, or create a new labeled slot.

**`[Environment JDBC<n>]`** — update or create:
```ini
[Environment JDBC<n>]
CLASSPATH       = <jar-path>
```

**`[generic_jdbc<n>]`** — agent section:
```ini
[generic_jdbc<n>]
Description     = <Driver display name> JDBC agent
Program         = jdbc<n>_sv
Environment     = JDBC<n>
ReUse           = never
;Database       = <jdbc-url-with-filled-params>
```

**Domain Alias** in `[Domain Aliases]`:
```ini
<DbType> JDBC   = jdbc<n>
```

**Mapping Rule** in `[Mapping Rules]`:
```ini
jdbc<n>:*:*:*:*:*:*           = accept generic_jdbc<n>
```

### Step JDBC-6: Reinitialize

After all changes: reinitialize the broker (see Step 6 below).

---

## Step 6 — Broker Restart / Reinitialize

Always confirm with the user before executing privileged commands.

**Reinitialize (preferred after rulebook edits — reloads config, keeps connections alive):**

```bash
# Via www_sv (Mode C)
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brkinit

# Via CLI (Mode A) — macOS
"/Library/Application Support/openlink/bin/oplshut" +reinit

# Via CLI (Mode A) — Linux (systemd)
sudo systemctl reload oplrqb

# Via CLI (Mode A) — Linux (direct)
/opt/openlink/bin/oplshut +reinit
```

**Full restart:**

```bash
# macOS
"/Library/Application Support/openlink/bin/oplshut" +yes
nohup "/Library/Application Support/openlink/bin/oplrqb" > /tmp/oplrqb_start.log 2>&1 &
sleep 3 && curl -s http://localhost:8000/scripts/brkver

# Linux (systemd)
sudo systemctl restart oplrqb
sudo systemctl status oplrqb

# Linux (direct)
/opt/openlink/bin/oplshut +yes
nohup /opt/openlink/bin/oplrqb > /tmp/oplrqb_start.log 2>&1 &
```

**Sudo note:** If `oplshut` requires sudo and Claude Code has no TTY, configure passwordless sudo (same pattern as `openlink-license-manager` skill):
```bash
echo 'USERNAME ALL=(ALL) NOPASSWD: /path/to/oplshut' | sudo tee /etc/sudoers.d/oplshut && sudo chmod 440 /etc/sudoers.d/oplshut
```

---

## Quick Reference Table

| Task | Mode C (www_sv) | Mode A (Direct file) |
|---|---|---|
| View full rulebook | `curl .../brkbook?mode=plain` | `configparser.read(oplrqb.ini)` |
| Discover host DSNs | `curl .../odbcdsn` | Parse `odbc.ini` with configparser |
| Configure ODBC agents | ODBC wizard (Steps ODBC-1–5) | ODBC wizard (Steps ODBC-1–5) |
| Configure JDBC agents | JDBC wizard (Steps JDBC-1–6) | JDBC wizard (Steps JDBC-1–6) |
| Edit broker globals | POST to `brksetup` | Edit `[Request Broker]` section |
| View mapping rules | `curl .../brkmaped` | Read `[Mapping Rules]` section |
| Add mapping rule | POST to `brkmaped` `action=add` | Append line to `[Mapping Rules]` |
| View agent settings | `curl .../brkagents?agent=<name>` | Read `[generic_<name>]` section |
| Edit agent settings | POST to `brkagents` | Edit `[generic_<name>]` section |
| View broker log | `curl .../brklog` | `tail` the log file |
| Version | `curl .../brkver` | `oplrqb +version` |
| Reload rulebook | `curl .../brkinit` | `oplshut +reinit` |
| Full restart | Stop + start | `oplshut +yes` → `oplrqb &` |
| Validate edits | Automatic (www_sv) | `inicheck oplrqb.ini` |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| www_sv not responding | Not started or port conflict | Start binary; check port 8000 not taken |
| www_sv auth fails | Wrong admin password | Check `www_sv.ini` `[User admin]` Password |
| `brkbook?mode=plain` empty | Rulebook path wrong in www_sv | Verify `oplrqb.ini` path |
| Edit not taking effect | Broker not reinitialized | `oplshut +reinit` or `brkinit` |
| `inicheck` errors | Bad ini syntax | Fix syntax; re-run `inicheck` |
| Mapping rule not matching | Wrong rule order or alias mismatch | Put specific rules above catch-all; verify `[Domain Aliases]` token for the domain |
| Agent not found / rejected | Missing `[generic_x]` section | Add agent section; verify `Program` binary path |
| `+reinit` fails | Broker not currently running | Start broker first |
| No DSNs found | ODBC config not at default path | Specify path explicitly or check `$ODBCINI` |
| JAR not matched | Non-standard JAR filename | Peek inside JAR: `unzip -p <jar> META-INF/services/java.sql.Driver` |
| JDBC agent rejected | CLASSPATH not set in `[Environment JDBC<n>]` | Add `CLASSPATH = <jar-path>` to the environment section |
| `oplshut` sudo: terminal required | No TTY in Claude Code shell | Configure passwordless sudo for `oplshut` |

---

## Initialization Sequence

When invoked:
1. Run Step 0 — detect OS, check www_sv, resolve rulebook path
2. If www_sv binary found but not running: offer to start it
3. Report: mode, OS, rulebook path, broker version, listen port
4. Prompt www_sv credentials if Mode C (session only)
5. Ask what to do:
   - **Configure ODBC Agents** → run ODBC wizard (Steps ODBC-1 through ODBC-5)
   - **Configure JDBC Agents** → run JDBC wizard (Steps JDBC-1 through JDBC-6)
   - **View rulebook** → full plain-text dump
   - **Edit mapping rules** → show current rules; offer add/delete
   - **Edit agent settings** → list agents; offer edit
   - **Edit broker global settings** → show current; offer edit
   - **View broker log** → tail last 50 lines
   - **Reinitialize / restart broker** → confirm then execute
   - **Validate** → run `inicheck` and report result

---

## Version
**1.0.0** — Initial release. ODBC and JDBC agent configuration wizards with host DSN discovery and JDBC driver auto-detection. Full rule book management via www_sv HTTP (Mode C) and direct file access (Mode A). macOS and Linux support.
