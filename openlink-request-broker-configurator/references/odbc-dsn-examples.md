# ODBC DSN Examples and Guidelines

How host-installed ODBC DSNs are discovered and mapped to Request Broker agent rules.

---

## DSN Discovery

### Config File Locations

| Scope | macOS | Linux |
|---|---|---|
| System DSNs | `/Library/ODBC/odbc.ini` | `/etc/odbc.ini` |
| User DSNs | `~/Library/ODBC/odbc.ini` | `~/.odbc.ini` |
| Driver registry | `/Library/ODBC/odbcinst.ini` | `/etc/odbcinst.ini` |
| Override via env | `$ODBCINI` | `$ODBCINI` |
| Override via env | `$ODBCINSTINI` | `$ODBCINSTINI` |

Both system and user DSNs should be merged when building the selection list.

### Reading DSNs (Mode A)

```python
import configparser, os

def list_dsns():
    dsns = {}
    paths = [
        '/Library/ODBC/odbc.ini',
        os.path.expanduser('~/Library/ODBC/odbc.ini'),
        '/etc/odbc.ini',
        os.path.expanduser('~/.odbc.ini'),
        os.environ.get('ODBCINI', ''),
    ]
    for p in filter(os.path.exists, paths):
        cfg = configparser.RawConfigParser(strict=False)
        cfg.read(p)
        for section in cfg.sections():
            if section.lower() not in ('odbc data sources', 'odbc drivers'):
                # Read key parameters for display
                driver = cfg.get(section, 'Driver', fallback='')
                desc   = cfg.get(section, 'Description', fallback='')
                host   = cfg.get(section, 'Host', fallback=
                         cfg.get(section, 'Address', fallback=''))
                dsns[section] = {'Driver': driver, 'Description': desc, 'Host': host}
    return dsns

for name, info in list_dsns().items():
    print(f"  {name:30s}  {info['Driver']}")
```

### Reading DSNs (Mode C — www_sv)

```bash
curl -s -u <uid>:<pwd> http://localhost:8000/scripts/odbcdsn
```

Parse the HTML response for DSN names, or use the Mode A method above for a clean list.

---

## From DSN to Broker Rule

For each selected DSN, three things are added to `oplrqb.ini`:

### 1. Domain Alias in `[Domain Aliases]`

Maps the DSN name (as supplied by the client) to an internal token. Normalize spaces to underscores for the token.

```ini
[Domain Aliases]
; DSN name as client sends it  → internal token
My Virtuoso DB                  = odbc_my_virtuoso_db
Northwind                       = odbc_northwind
Oracle MT                       = odbc_oracle_mt
```

Pattern: prefix with `odbc_` to avoid collisions with native agent tokens.

### 2. Agent Section `[generic_odbc_<token>]`

```ini
[generic_odbc_northwind]
Description     = ODBC agent for Northwind DSN
Program         = odbc_mv
Environment     = ODBC
ReUse           = always
Database        = Northwind
```

The `Database` key is the exact DSN name as it appears in `odbc.ini` — the broker passes this to the ODBC driver manager.

### 3. Mapping Rule in `[Mapping Rules]`

Insert **before** the generic catch-all `odbc:*:*:*:*:*:*`:

```ini
odbc:northwind:*:*:*:*:*       = accept generic_odbc_northwind
```

The first field (`odbc`) matches the `Odbc = odbc` alias already in `[Domain Aliases]`. The second field (`northwind`) matches the DSN token added in step 1.

---

## DSN Type Examples

### Multi-Tier DSN (connects via the Request Broker to a remote database)

```ini
[Oracle Production]
Driver          = /Library/ODBC/OpenLink Generic ODBC Driver v9.0.bundle/Contents/MacOS/liboplodbcu.dylib
Host            = db.example.com
Port            = 5000
ServerType      = Oracle 19.x
Database        = ORCL
UserName        = scott
ReadOnly        = No
FetchBufferSize = 99
UseSSL          = 0
DeferLongFetch  = 0
NoLoginBox      = 0
```

Broker rule generated:
```ini
; [Domain Aliases]
Oracle Production   = odbc_oracle_production

; [generic_odbc_oracle_production]
Program    = odbc_mv
Environment = ODBC
ReUse      = always
Database   = Oracle Production

; [Mapping Rules]
odbc:oracle_production:*:*:*:*:* = accept generic_odbc_oracle_production
```

---

### Virtuoso DSN (direct connection to a local or remote Virtuoso instance)

```ini
[Local Virtuoso]
Driver          = /Library/ODBC/OpenLink Virtuoso ODBC Driver (Unicode).bundle/Contents/MacOS/virtodbc_r.dylib
Address         = localhost:1111
LastUser        = dba
PWDClearText    = 0
WideAsUTF16     = 1
```

Broker rule generated:
```ini
; [Domain Aliases]
Local Virtuoso   = odbc_local_virtuoso

; [generic_odbc_local_virtuoso]
Program    = odbc_mv
Environment = ODBC
ReUse      = always
Database   = Local Virtuoso

; [Mapping Rules]
odbc:local_virtuoso:*:*:*:*:* = accept generic_odbc_local_virtuoso
```

---

### PostgreSQL Lite DSN (single-tier direct driver connection)

```ini
[Northwind PG]
Driver          = /Library/ODBC/OpenLink PostgreSQL Lite Driver (Unicode) v8.0.bundle/Contents/MacOS/liboplodbcu.dylib
Host            = pgserver.example.com
Port            = 5432
Database        = northwind
UserName        = pguser
ReadOnly        = No
```

Broker rule generated:
```ini
; [Domain Aliases]
Northwind PG   = odbc_northwind_pg

; [generic_odbc_northwind_pg]
Program    = odbc_mv
Environment = ODBC
ReUse      = always
Database   = Northwind PG

; [Mapping Rules]
odbc:northwind_pg:*:*:*:*:* = accept generic_odbc_northwind_pg
```

---

### MySQL Lite DSN

```ini
[MySQL Dev]
Driver          = /Library/ODBC/OpenLink MySQL 8.x Lite Driver (Unicode) v8.0.bundle/Contents/MacOS/liboplodbcu.dylib
Host            = 127.0.0.1
Port            = 3306
Database        = devdb
UserName        = root
ReadOnly        = No
```

---

### SQL Server DSN (via unixODBC + FreeTDS or Microsoft ODBC Driver)

```ini
[SQL Server Reports]
Driver          = ODBC Driver 18 for SQL Server
Server          = tcp:sqlserver.example.com,1433
Database        = ReportsDB
Encrypt         = yes
TrustServerCertificate = yes
```

---

## Catch-all ODBC Rule

When the user selects "all DSNs" rather than specific ones, use the existing generic catch-all (already in the default rulebook):

```ini
; [Domain Aliases] — already present:
Odbc            = odbc

; [generic_odbc] — already present:
[generic_odbc]
Description     = Default settings for ODBC agent
Program         = odbc_mv
Environment     = ODBC
ReUse           = always

; [Mapping Rules] — already present:
odbc:*:*:*:*:*:*   = accept generic_odbc
```

The client must supply the DSN name as the `Database` parameter in the connection string; the broker passes it through to the ODBC driver manager.

---

## Naming Convention for Tokens

When generating Domain Alias tokens from DSN names:
1. Lowercase the DSN name
2. Replace spaces and special characters with underscores
3. Prefix with `odbc_` to avoid collisions with native tokens (e.g. `ora190`, `mys5`)
4. Truncate to 32 characters if needed

| DSN Name | Token |
|---|---|
| `Northwind` | `odbc_northwind` |
| `My Oracle DB` | `odbc_my_oracle_db` |
| `Local Virtuoso` | `odbc_local_virtuoso` |
| `SQL Server Reports` | `odbc_sql_server_reports` |

---

## ReadOnly and ReUse Recommendations

| Use Case | ReadOnly | ReUse |
|---|---|---|
| Reporting / BI (read-only workload) | `Yes` | `always` |
| General read-write | `No` | `always` |
| Multi-user with strict session isolation | `No` | `never` |
| Pooled connections | `No` | `upto 10` |
| Read-only and connection pooling | `Yes` | `ifreadonly` |

---

## FetchBufferSize Guidance

`FetchBufferSize` is set in the MT DSN (in `odbc.ini`), not in the broker agent section. It controls how many rows are prefetched per network round-trip from the broker to the client.

| Scenario | Recommended Value |
|---|---|
| Default / general use | `99` |
| Large result sets, high-latency network | `500`–`1000` |
| LOB-heavy queries with `DeferLongFetch = 1` | `99` (leave default) |
| Minimize memory per connection | `1`–`10` |

---

## Related Reference

- `iodbc-dsn-manager` skill — `references/mt-dsn-parameters.md`: complete MT, Virtuoso, and Unix Lite DSN parameter tables
- `iodbc-dsn-manager` skill — `references/connection-string-formats.md`: DSN and DSN-less connection string syntax for iODBC and unixODBC
