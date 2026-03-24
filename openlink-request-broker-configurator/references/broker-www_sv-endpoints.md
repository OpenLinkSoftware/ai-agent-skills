# www_sv Broker Endpoint Reference

Broker-specific endpoints provided by the OpenLink Admin Assistant HTTP server (`www_sv`).

---

## Server Details

| Item | Value |
|---|---|
| Binary (macOS) | `/Library/Application Support/openlink/bin/www_sv` |
| Binary (Linux) | `/opt/openlink/bin/www_sv` |
| Default port | `8000` |
| Config | `/Library/Application Support/openlink/bin/w3config/www_sv.ini` |
| Auth | HTTP Basic (default user: `admin`) |
| Version | v1.60, Release 9.0 |

**Start / stop:**
```bash
# Check running
curl -s http://localhost:8000/ | grep -i openlink

# Start (background)
nohup "/Library/Application Support/openlink/bin/www_sv" > /tmp/www_sv.log 2>&1 &

# Stop
pkill -f www_sv
```

**Auth levels in `www_sv.ini`:**
| Level | Access |
|---|---|
| `0` | Deny |
| `1` | Read only |
| `2` | Read + update |
| `3` | Full admin |

---

## Broker Script Summary

| Endpoint | Method | Level | Description |
|---|---|---|---|
| `/scripts/brkbook` | GET | 1 | Full rulebook — HTML view |
| `/scripts/brkbook?mode=plain` | GET | 1 | Raw plain-text rulebook (parse with configparser) |
| `/scripts/brkbook?mode=save` | GET | 1 | Download rulebook as a file |
| `/scripts/brksetup` | GET/POST | 2 | Broker global settings editor |
| `/scripts/brkagents` | GET | 1 | List all `[generic_*]` agent sections |
| `/scripts/brkagents?agent=<name>` | GET | 1 | View one agent section |
| `/scripts/brkagents` | POST | 2 | Create or edit an agent section |
| `/scripts/brkmaped` | GET | 1 | View all mapping rules |
| `/scripts/brkmaped` | POST | 2 | Add, edit, or delete a mapping rule |
| `/scripts/brkalias?atype=<type>` | GET | 1 | View an alias section |
| `/scripts/brkalias` | POST | 2 | Add or edit an alias entry |
| `/scripts/brklog` | GET | 1 | View broker log file |
| `/scripts/brkver` | GET | 1 | Broker version string |
| `/scripts/brkconn` | GET | 1 | Active connection status |
| `/scripts/brkinit` | GET | 2 | Reinitialize broker (reload rulebook without full restart) |
| `/scripts/brklic` | GET | 1 | License information |
| `/scripts/brklic2` | GET | 1 | Extended license view |
| `/scripts/brkzero` | GET/POST | 3 | Zero Config administration (warn before use) |

---

## Curl Examples

Replace `<uid>`, `<pwd>` with www_sv credentials.

### View rulebook (plain text — for parsing)
```bash
curl -s -u <uid>:<pwd> "http://localhost:8000/scripts/brkbook?mode=plain"
```

### Download rulebook as file
```bash
curl -s -u <uid>:<pwd> "http://localhost:8000/scripts/brkbook?mode=save" \
  -o /tmp/oplrqb_backup.ini
```

### View broker version
```bash
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brkver
```

### View broker log
```bash
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brklog
```

### View active connections
```bash
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brkconn
```

### Reinitialize broker (reload rulebook)
```bash
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brkinit
```

### View all agent sections
```bash
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brkagents
```

### View one agent section
```bash
curl -s -u <uid>:<pwd> "http://localhost:8000/scripts/brkagents?agent=generic_odbc"
```

### View mapping rules
```bash
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/brkmaped
```

### View Domain Aliases
```bash
curl -s -u <uid>:<pwd> "http://localhost:8000/scripts/brkalias?atype=Domain+Aliases"
```

### View host DSNs (for ODBC wizard)
```bash
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/odbcdsn
```

---

## POST Parameter Reference

### `/scripts/brksetup` — Broker Global Settings

| Field | Section | Description |
|---|---|---|
| `BinaryDirectory` | `[Request Broker]` | Path to broker and agent binaries |
| `Listen` | `[Protocol TCP]` | Client listen port (default: 5001) |
| `MaxAgents` | `[Request Broker]` | Max spawned agents (0 = unlimited) |
| `MaxConnections` | `[Request Broker]` | Max simultaneous connections (0 = unlimited) |
| `HostNameResolver` | `[Request Broker]` | `Yes` / `No` — resolve IPs to hostnames |
| `LingerTimeout` | `[Request Broker]` | Disconnected agent linger time (seconds) |
| `PingWatchdog` | `[Protocol TCP]` | `No` / `Yes` — send keep-alive packets |
| `PingInterval` | `[Protocol TCP]` | Keep-alive interval (seconds) |
| `SendSize` | `[Communications]` | Send buffer size (bytes) |
| `ReceiveSize` | `[Communications]` | Receive buffer size (bytes) |
| `BrokerTimeout` | `[Communications]` | Utility contact timeout (seconds) |
| `StartupBy` | `[Security]` | Regex: users who may start the broker |
| `ShutdownBy` | `[Security]` | Regex: users who may shut down the broker |
| `ShutdownFrom` | `[Security]` | Regex: hosts from which shutdown is permitted |

Example:
```bash
curl -s -u <uid>:<pwd> -X POST http://localhost:8000/scripts/brksetup \
  -d "Listen=5001&MaxAgents=0&HostNameResolver=Yes&BrokerTimeout=30"
```

---

### `/scripts/brkagents` — DB Agent Section

| Field | Description |
|---|---|
| `agent` | Section name (e.g. `generic_odbc`, `generic_odbc_MyDSN`) — **required** |
| `Program` | Agent binary name |
| `Description` | Human-readable description |
| `CommandLine` | Additional startup flags |
| `Directory` | Working directory for spawned process |
| `Database` | Forced database/DSN name |
| `UserID` | Forced login UID |
| `Password` | Forced login password |
| `ConnectOptions` | Driver-specific connect options |
| `ReadOnly` | `Yes` / `No` |
| `ServerOptions` | Native DB server option string |
| `OpsysLogin` | `Yes` / `No` |
| `ReUse` | `never`, `always`, `upto <n>`, `ifreadonly`, `ifsame database`, etc. |
| `Environment` | Names the `[Environment X]` section |
| `SSLKeyFile` | SSL certificate file |
| `SSLRequired` | `No` / `Yes` |

Example — create DSN-specific ODBC agent:
```bash
curl -s -u <uid>:<pwd> -X POST http://localhost:8000/scripts/brkagents \
  -d "agent=generic_odbc_MyDSN&Program=odbc_mv&Environment=ODBC&ReUse=always&Database=MyDSN&Description=ODBC+agent+for+MyDSN"
```

Example — update JDBC slot CLASSPATH via Environment section edit (use brksetup or direct file edit — www_sv does not expose Environment sections directly via brkagents POST):
> For `[Environment JDBC<n>]` changes, use direct file edit (Mode A) or the general `brksetup` form.

---

### `/scripts/brkmaped` — Mapping Rules

| Field | Description |
|---|---|
| `action` | `add`, `delete`, or `edit` |
| `domain` | Domain token (from `[Domain Aliases]`) |
| `db` | Database alias token or `*` |
| `uid` | User alias token or `*` |
| `opsys` | Opsys alias token or `*` |
| `machine` | Machine alias token or `*` |
| `appl` | Application alias token or `*` |
| `mode` | Connection mode or `*` |
| `target` | For `accept`: agent section name; for `reject`: error message string |
| `rule` | 1-based rule index (required for `delete` and `edit`) |

Example — add DSN-specific ODBC rule:
```bash
curl -s -u <uid>:<pwd> -X POST http://localhost:8000/scripts/brkmaped \
  -d "action=add&domain=odbc&db=MyDSN&uid=*&opsys=*&machine=*&appl=*&mode=*&target=generic_odbc_MyDSN"
```

Example — add JDBC rule:
```bash
curl -s -u <uid>:<pwd> -X POST http://localhost:8000/scripts/brkmaped \
  -d "action=add&domain=jdbc14&db=*&uid=*&opsys=*&machine=*&appl=*&mode=*&target=generic_jdbc14"
```

Example — delete rule at index 3:
```bash
curl -s -u <uid>:<pwd> -X POST http://localhost:8000/scripts/brkmaped \
  -d "action=delete&rule=3"
```

---

### `/scripts/brkalias` — Alias Sections

| Field | Description |
|---|---|
| `atype` | Alias section name (URL-encoded): `Domain+Aliases`, `Database+Aliases`, `Opsys+Aliases`, `Machine+Aliases`, `Application+Aliases`, `User+Aliases` |
| `action` | `add`, `edit`, or `delete` |
| `key` | Left-hand side of the alias entry (regex pattern) |
| `value` | Right-hand side (alias token) |

Example — add a Domain Alias for a custom JDBC driver:
```bash
curl -s -u <uid>:<pwd> -X POST http://localhost:8000/scripts/brkalias \
  -d "atype=Domain+Aliases&action=add&key=PostgreSQL+JDBC&value=jdbc14"
```

Example — add a Domain Alias for a DSN name:
```bash
curl -s -u <uid>:<pwd> -X POST http://localhost:8000/scripts/brkalias \
  -d "atype=Domain+Aliases&action=add&key=MyDSN&value=odbc_mydsn"
```

---

## Response Parsing

www_sv returns HTML for all endpoints. To detect success or failure programmatically:

```bash
# Check for success
curl -s -u <uid>:<pwd> -X POST http://localhost:8000/scripts/brkmaped \
  -d "action=add&..." | grep -i "configuration updated\|successfully"

# Check for failure
curl -s -u <uid>:<pwd> -X POST http://localhost:8000/scripts/brkmaped \
  -d "action=add&..." | grep -i "failed\|error\|sorry"
```

For the plain-text rulebook, pipe directly to Python configparser:
```python
import subprocess, configparser, io

result = subprocess.run(
    ['curl', '-s', '-u', f'{uid}:{pwd}', 'http://localhost:8000/scripts/brkbook?mode=plain'],
    capture_output=True, text=True
)
cfg = configparser.RawConfigParser(strict=False, delimiters=('=',))
cfg.read_string(result.stdout)
```
