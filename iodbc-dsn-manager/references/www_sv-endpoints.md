# www_sv HTTP Endpoint Reference

## Server Details

| Item | Value |
|---|---|
| Binary | `/Library/Application Support/openlink/bin/www_sv` |
| Default port | `8000` |
| Config | `/Library/Application Support/openlink/bin/w3config/www_sv.ini` |
| Web root | `/Library/Application Support/openlink/bin/w3config/html/` |
| Include (Tcl libs) | `/Library/Application Support/openlink/bin/w3config/include/` |
| Scripts | `/Library/Application Support/openlink/bin/w3config/html/scripts/` |
| Version | v1.60, Release 9.0 |
| Auth | HTTP Basic (default user: `admin`) |

---

## Start / Stop

```bash
# Check if running
curl -s http://localhost:8000/ | grep -i openlink

# Start (foreground)
"/Library/Application Support/openlink/bin/www_sv" &

# Start (background, log to file)
nohup "/Library/Application Support/openlink/bin/www_sv" \
  > /tmp/www_sv.log 2>&1 &

# Stop
pkill -f www_sv
```

---

## Core Endpoints

### Navigation
| Path | Description |
|---|---|
| `GET /` | Root — redirects to `/index.html` |
| `GET /index.html` | Frameset entry point (menu + content) |
| `GET /about.html` | About the Admin Assistant |

### DSN Management
| Path | Method | Description |
|---|---|---|
| `/scripts/odbcdsn` | GET | List all DSNs; shows form to select/edit |
| `/scripts/odbcdsn?dsn=<name>` | GET | Inspect named DSN |
| `/scripts/odbcdsn` | POST | Create or update a DSN |
| `/scripts/wods` | GET/POST | Wizard tab 1: Data Source name/driver |
| `/scripts/wost` | GET/POST | Wizard tab 2: Server Type selection |
| `/scripts/woco` | GET/POST | Wizard tab 3: Communication (Host/Port/SSL) |
| `/scripts/wod` | GET/POST | Wizard tab 4: Options / Debug |
| `/scripts/udbcdsn` | GET/POST | Unix Lite DSN configuration |
| `/scripts/udbcsetup` | GET/POST | Unix Lite setup wizard |

### Testing
| Path | Description |
|---|---|
| `/scripts/oplisql` | Interactive SQL tool — test a DSN connection |
| `/scripts/dsntest` | DSN connectivity test (returns pass/fail) |

### Driver & Broker Admin
| Path | Description |
|---|---|
| `/scripts/brksetup` | Request Broker configuration |
| `/scripts/brkagents` | Broker agent pool management |
| `/scripts/brkzero` | Reset broker configuration |
| `/scripts/brklog` | View broker logs |
| `/scripts/brkver` | Broker version info |
| `/scripts/brkbook` | Rulebook viewer |

### Web Services
| Path | Description |
|---|---|
| `/Xmla/Service.asmx` | XML/A SOAP endpoint (Discover, Execute) |
| `/Xmla/Service.asmx?wsdl` | WSDL descriptor |
| `/services.disco` | Service discovery |

---

## Authentication

`www_sv` uses HTTP Basic Authentication.

```bash
# All curl calls require credentials:
curl -s -u admin:<password> http://localhost:8000/scripts/odbcdsn

# Or pass in URL:
curl -s http://admin:<password>@localhost:8000/scripts/odbcdsn
```

Access levels stored in `www_sv.ini`:
| Level | Meaning |
|---|---|
| `0` | Deny |
| `1` | Read only |
| `2` | Read + update |
| `3` | Full admin |

---

## Key Config File: `www_sv.ini`

```ini
[HTTPServer]
HTTPPort        = 8000
HTTPTimeout     = 60
DocumentRoot    = /Library/Application Support/openlink/bin/w3config/html

[Users]
admin = <encrypted_password>

[User admin]
AccessLevel = 3
```

---

## DSN Form Parameters (POST to `/scripts/odbcdsn`)

Common fields across DSN types:

| Field | Description |
|---|---|
| `dsn` | DSN name |
| `driver` | Driver name (from odbcinst.ini) |
| `action` | `add`, `edit`, `delete` |
| `Host` | Remote host (MT) |
| `Port` | Remote port (MT) |
| `ServerType` | DB server type (MT, from template.ini) |
| `Database` | Target database/schema |
| `UserName` | Default UID |
| `Password` | Default PWD |
| `UseSSL` | `0` or `1` |
| `ReadOnly` | `0` or `1` |
| `FetchBufferSize` | Row fetch buffer (MT) |
| `DeferLongFetch` | `0` or `1` (MT) |
| `NoLoginBox` | `0` or `1` (MT) |
| `Address` | `host:port` format (Virtuoso) |

---

## Tcl Include Libraries (for reference)

| File | Purpose |
|---|---|
| `common.tcl` | Shared UI procedures |
| `forms.tcl` | Form/RecordSet management |
| `wizard.tcl` | Wizard UI generation |
| `auth.tcl` | Authentication + host access control |
| `odbcdsn.tcl` | DSN read/write routines |
| `udbcdsn.tcl` | Unix Lite DSN routines |
| `dsntest.tcl` | DSN connection testing |
| `rulebook.tcl` | Request Broker rulebook handling |
| `drivers.ini` | Driver/wizard configuration (21KB) |
| `template.ini` | 70+ DB server type templates (24KB) |
