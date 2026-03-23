# OpenLink UDA DSN Parameter Reference

## DSN Types

| Type | Wizard Style | Use Case |
|---|---|---|
| **MT** (Multi-Tier) | `wods/wost/woco/wod` | Remote database via OpenLink Request Broker |
| **VIRT** (Virtuoso) | Virtuoso wizard | Virtuoso RDBMS/triple store |
| **ULITE** (Unix Lite) | `udbcdsn/udbcsetup` | Single-tier direct driver connection |

---

## MT (Multi-Tier) DSN Parameters

Multi-Tier DSNs connect through the OpenLink Request Broker running on a remote host.

| Parameter | Key in odbc.ini | Description | Default |
|---|---|---|---|
| Data Source Name | `[section name]` | The DSN label | — |
| Driver | `Driver` | Path to MT driver `.bundle`/`.so` | — |
| Host | `Host` | Hostname or IP of the broker machine | `localhost` |
| Port | `Port` | Broker listen port | `5000` |
| Server Type | `ServerType` | Database engine type (see templates below) | — |
| Database | `Database` | Target database, schema, or SID | — |
| Username | `UserName` | Default login (can be overridden at connect) | — |
| Read Only | `ReadOnly` | `Yes`/`No` — disallow write operations | `No` |
| Fetch Buffer Size | `FetchBufferSize` | Rows to prefetch per network round-trip | `99` |
| Use SSL | `UseSSL` | Encrypt broker connection | `0` |
| Defer Long Fetch | `DeferLongFetch` | Lazy-fetch LONG/LOB columns | `0` |
| No Login Box | `NoLoginBox` | Suppress credentials dialog | `0` |
| SQL DBMS Name | `SqlDbmsName` | Override reported DBMS name | — |
| Options | `Options` | Driver-specific options string | — |

### Example MT DSN (`odbc.ini`)

```ini
[ODBC Data Sources]
My Oracle DB = OpenLink Generic ODBC Driver v8.0

[My Oracle DB]
Driver          = /Library/ODBC/OpenLink Generic ODBC Driver v8.0.bundle/Contents/MacOS/...
Host            = dbserver.example.com
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

---

## VIRT (Virtuoso) DSN Parameters

| Parameter | Key | Description |
|---|---|---|
| Driver | `Driver` | Virtuoso ODBC driver path |
| Address | `Address` | `host:port` (e.g. `localhost:1111`) |
| Last User | `LastUser` | Cached last-used UID |
| PWD Clear Text | `PWDClearText` | `0` = encrypted, `1` = plaintext |
| Wide As UTF16 | `WideAsUTF16` | Unicode mode |
| Daylight | `Daylight` | Timezone daylight saving |
| Round Robin | `RoundRobin` | Load balance across multiple servers |
| No System Tables | `NoSystemTables` | Hide system tables in metadata |
| Treat Views As Tables | `TreatViewsAsTables` | Compatibility flag |

---

## Supported Server Types (70+ templates from `template.ini`)

### Oracle
`Oracle 6`, `Oracle 7`, `Oracle 8.0.x`, `Oracle 8.1.x`, `Oracle 9.x`, `Oracle 10.x`, `Oracle 11.x`, `Oracle 12.x`, `Oracle 18.x`, `Oracle 19.x`

### Microsoft SQL Server
`SQL Server 4`, `SQL Server 6`, `SQL Server 7`, `SQL Server 2000`, `SQL Server 2005`

### MySQL
`MySQL 3.x`, `MySQL 4.x`, `MySQL 5.x`, `MySQL 8.x`

### PostgreSQL
`PostgreSQL 6.x`, `PostgreSQL 7.x`, `PostgreSQL 8.x`, `PostgreSQL 9.x`, `PostgreSQL 10+`

### Sybase
`Sybase 10`, `Sybase 11`, `Sybase 12`, `Sybase ASE 15`

### Informix
`Informix 5`, `Informix 7`, `Informix 9`, `Informix 10`, `Informix 11`

### IBM DB2
`DB2 6`, `DB2 7`, `DB2 8`, `DB2 9`, `DB2 10`

### Other
`Ingres 6.4`, `Ingres II`, `Progress 8.x`, `Progress 9.x`, `Progress 10.x`, `Progress OpenEdge 11`, `Unify`, `JDBC Bridge`, `Virtuoso`, `Generic ODBC`

---

## Request Broker Connection

MT DSNs route through the **OpenLink Request Broker** (`oplrqb`), which must be running on the target host.

| Component | Default Port |
|---|---|
| Request Broker | `5000` |
| Admin Assistant (www_sv) | `8000` |
| Virtuoso SQL | `1111` |
| Virtuoso HTTP | `8890` |

### Broker Config Location
`/Library/Application Support/openlink/bin/openlink.ini` (macOS)
`/etc/openlink/openlink.ini` (Linux)

---

## Driver Locations (macOS)

| Driver | Bundle Path |
|---|---|
| Generic ODBC v8.0 | `/Library/ODBC/OpenLink Generic ODBC Driver v8.0.bundle/...` |
| Generic ODBC v9.0 | `/Library/ODBC/OpenLink Generic ODBC Driver v9.0.bundle/...` |
| Virtuoso Unicode | `/Library/ODBC/OpenLink Virtuoso ODBC Driver (Unicode).bundle/...` |
| SQL Server Lite v8.0 | `/Library/ODBC/OpenLink SQL Server Lite Driver (Unicode) v8.0.bundle/...` |
| PostgreSQL Lite v8.0 | `/Library/ODBC/OpenLink PostgreSQL Lite Driver (Unicode) v8.0.bundle/...` |
| MySQL Lite v8.0 | `/Library/ODBC/OpenLink MySQL 8.x Lite Driver (Unicode) v8.0.bundle/...` |
| JDBC Lite v9.0 | `/Library/ODBC/OpenLink JDBC Lite Driver (Unicode) v9.0.bundle/...` |
