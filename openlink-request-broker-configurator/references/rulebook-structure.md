# OpenLink Request Broker Rulebook Structure

Complete parameter reference for `oplrqb.ini` (also distributed as `openlink.ini` on some installations).

Ground truth: `/Library/Application Support/openlink/bin/oplrqb.ini` (macOS)

---

## File Overview

| Item | Value |
|---|---|
| Primary name | `oplrqb.ini` |
| Alternate name | `openlink.ini` |
| macOS location | `/Library/Application Support/openlink/bin/oplrqb.ini` |
| Linux location | `/opt/openlink/bin/oplrqb.ini` or `/etc/openlink/oplrqb.ini` |
| Format | Windows INI (`;` comments, `key = value` pairs) |
| Include mechanism | `IncludeRulebook = <filename>` in `[Security]` (multiple allowed) |
| Validation tool | `inicheck <path-to-oplrqb.ini>` |
| Debug trace | Set `TraceRulebook = /tmp/debug.book` in `[Security]` — writes merged rulebook |

**configparser caveat:** Use `RawConfigParser(strict=False, delimiters=('=',))`. The `[Mapping Rules]` section contains colon-delimited keys (e.g. `odbc:*:*:*:*:*:*`) that will be misinterpreted if colon is treated as a key-value delimiter.

---

## `[Request Broker]`

Global broker parameters.

| Key | Default | Description |
|---|---|---|
| `BinaryDirectory` | `/Library/Application Support/openlink/bin` | Path to broker and agent binaries |
| `CommandLine` | `;+logfile /tmp/oplrqb.log +debug` | Startup flags (semicolon prefix = commented out) |
| `Protocols` | `tcp` | Active protocols: `tcp`, `spx`, `decnet` (comma-separated) |
| `MaxAgents` | `0` | Max spawned agent processes; `0` = unlimited |
| `MaxConnections` | `0` | Max simultaneous client connections; `0` = unlimited |
| `HostNameResolver` | `Yes` | Resolve IP addresses to hostnames for Machine Alias matching |
| `LingerTimeout` | `0` | Seconds a disconnected agent process lingers before termination; `0` = immediate |
| `SSLKeyFile` | _(unset)_ | SSL certificate filename (relative to BinaryDirectory) |
| `SSLRequired` | `No` | If `Yes`, all connections must use SSL |

**CommandLine flags:**
- `+logfile <path>` — write broker log to file
- `+loglevel <0-7>` — log verbosity (7 = maximum)
- `+debug` — enable debug output
- `+foreground` — run in foreground (for manual/test starts)
- `+configfile <path>` — use alternate rulebook file

---

## `[Protocol TCP]`

TCP protocol parameters.

| Key | Default | Description |
|---|---|---|
| `PingWatchdog` | `No` | Send keep-alive packets to check agent liveness |
| `PingInterval` | `600` | Keep-alive interval in seconds |
| `Listen` | `5001` | Port for client connections (the broker listen port) |
| `PortLow` | `5001` | First port in the agent TCP port range |
| `PortHigh` | _(unset)_ | Last port in the agent TCP port range; unset = no upper limit |
| `IPAddress` | _(unset)_ | Override the network interface address the broker binds to |

---

## `[Protocol SPX]`

IPX/SPX protocol parameters (legacy).

| Key | Default | Description |
|---|---|---|
| `SAPBroadcast` | `No` | Broadcast SAP registration packets |
| `SAPInterval` | `100` | SAP broadcast interval in seconds |
| `SAPServiceType` | `0x321F` | SAP service type identifier |
| `SAPServiceName` | `OPENLINK` | SAP service name advertised on the network |

---

## `[Communications]`

Network communication tuning.

| Key | Default | Description |
|---|---|---|
| `SendSize` | `16000` | Send buffer size in bytes |
| `ReceiveSize` | `4096` | Receive buffer size in bytes |
| `DataEncryption` | `No` | Encrypt outgoing network packets |
| `BrokerTimeout` | `30` | Timeout (seconds) for utilities (oplshut, etc.) to contact the broker |
| `ReceiveTimeout` | `10` | Timeout (seconds) for the broker to receive a response from an agent |
| `RetryTimeout` | `5` | Initial retry interval (seconds); doubles on each failure, max 30s |

---

## `[Security]`

Access control and rulebook composition.

| Key | Default | Description |
|---|---|---|
| `StartupBy` | `.*` | Regex: usernames that may start the broker |
| `ShutdownBy` | `.*` | Regex: usernames that may shut down the broker |
| `ShutdownFrom` | `localhost` | Regex: hostnames from which shutdown is permitted |
| `ValidUidRange` | `0, 50000` | Valid UID range for `OpsysLogin` agent spawning |
| `TraceRulebook` | _(unset)_ | Write the merged rulebook (including includes) to this path for debugging |
| `IncludeRulebook` | _(unset)_ | Path to an additional `.book` file to merge; multiple allowed |

> **Note:** Sections defined in the main `oplrqb.ini` take precedence over included rulebooks. Environment sections cannot be overridden by includes.

---

## `[Environment <type>]`

Environment variables injected into DB agent processes. One section per agent type. The `Environment` key in a `[generic_*]` section names the corresponding `[Environment X]` section.

### ODBC (`[Environment ODBC]`)
Typically empty — the ODBC driver manager reads its own config.

### JDBC (`[Environment JDBC11]` through `[Environment JDBC18]`)
| Key | Description |
|---|---|
| `CLASSPATH` | Path to the JDBC driver JAR file(s) — required for the agent to load the driver |

### Oracle (`[Environment ORACLE6]` through `[Environment ORACLE190]`)
| Key | Example | Description |
|---|---|---|
| `ORACLE_HOME` | `/dbs/oracle19` | Oracle client installation directory |
| `ORACLE_SID` | `ORCL` | Default database SID |
| `ODBC_CATALOGS` | `Y` | Enable catalog functions (after loading `odbccat9.sql`) |
| `SHOW_REMARKS` | `N` | Retrieve REMARKS column in `SQLColumns` |
| `CURSOR_SENSITIVITY` | `LOW` | Set to `HIGH` after loading `odbccat9.sql` |
| `LD_LIBRARY_PATH` | `/dbs/oracle19/lib` | Shared library path (Linux) |
| `SHLIB_PATH` | `/dbs/oracle19/lib` | Shared library path (HP-UX) |
| `LIBPATH` | `/dbs/oracle19/lib` | Shared library path (AIX) |

### Informix (`[Environment INFORMIX5]` through `[Environment INFORMIX11]`)
| Key | Example | Description |
|---|---|---|
| `INFORMIXDIR` | `/dbs/informix11` | Informix client directory |
| `INFORMIXSERVER` | `alpha` | Default Informix server name |
| `DELIMIDENT` | `Y` | Allow quoted identifiers |
| `OPL_INF_MULTISESS` | `Y` | Allow multiple sessions per connection |
| `OPL_SPACEPADCHAR` | `Y` | Pad CHAR fields with spaces |
| `CURSOR_SENSITIVITY` | `LOW` | Set to `HIGH` after loading `oplrvc.sql` |
| `FET_BUF_SIZE` | `65535` | Fetch buffer size |
| `CLIENT_LOCALE` | `EN_US.UTF8` | Uncomment for Unicode connections |
| `FORCE_ONLINE_DATABASE` | `0` | Force SE (0) or ONLINE (1) mode |

### DB2 (`[Environment DB2]`)
| Key | Example | Description |
|---|---|---|
| `DB2DIR` | `/dbs/DB2` | DB2 client installation directory |
| `DB2INSTANCE` | `DB2` | Default DB2 instance name |
| `CURSOR_SENSITIVITY` | `LOW` | Set to `HIGH` after loading `oplrvc.sql` |

### MySQL (`[Environment MYSQL3]` through `[Environment MYSQL5]`)
| Key | Description |
|---|---|
| `CURSOR_SENSITIVITY` | `LOW` — set to `HIGH` after loading `odbccat6.sql` |

### Ingres (`[Environment INGRES6]`, `[Environment INGRES_II]`)
| Key | Example | Description |
|---|---|---|
| `II_DATE_FORMAT` | `US` | Date format |
| `II_SYSTEM` | `/dbs` | Ingres installation base |
| `ING_SET` | `set lockmode session where readlock=nolock` | Default SET options |

### Virtuoso (`[Environment VIRT]`)
Typically empty — Virtuoso uses its own connection parameters.

---

## `[Domain Aliases]`

Maps client-supplied ServerType strings to internal domain tokens used in `[Mapping Rules]`. Supports regex on the left-hand side. First match wins. The last line `.*  = unknown` is the catch-all.

**Key examples from actual rulebook:**

```ini
[Domain Aliases]
DB2                = db2
Informix 11        = inf11
Odbc               = odbc
Oracle 6           = ora6
^Oracle 19.x$      = ora190
PostgreSQL         = pgr7
MySQL 5.x          = mys5
Virtuoso           = virt
SQLServer          = sql
Jdbc 1.1           = jdbc11
Jdbc 1.4           = jdbc14
jdbc|JDBC          = jdbc
.*                 = unknown
```

---

## `[Database Aliases]`, `[Opsys Aliases]`, `[Machine Aliases]`, `[Application Aliases]`, `[User Aliases]`

Same structure — regex on left, alias token on right. Used to normalize the corresponding field in a `[Mapping Rules]` entry.

**Key defaults:**

```ini
[Database Aliases]
demo       = demo

[Opsys Aliases]
java       = java
win32|msdos = msdos
.*         = other

[User Aliases]
scott|system = insecure
^$           = blank

[Machine Aliases]
localhost.*|loopback|127\.0\.0\.1  = localhost

[Application Aliases]
MSACCESS         = jet
MSQRY.*|EXCEL|WORD = msoffice
```

---

## `[Mapping Rules]`

**Format:** `domain:database:uid:opsys:machine:application:mode = accept <agent> | reject <message>`

- Fields are matched against the aliased values produced by the alias sections above
- `*` matches anything (wildcard)
- `blank` matches an empty field (e.g. no UID supplied)
- First matching rule wins — order matters
- `accept <agent>` routes the connection to the named `[generic_<agent>]` section
- `reject <message>` sends the message string back to the client

**Real examples from actual rulebook:**

```ini
[Mapping Rules]
; Reject well-known insecure account names on Windows/Jet clients
*:*:Admin:msdos:*:jet:*          = reject Admin user account is not registered

; JDBC bridge rules
jdbc11:*:*:*:*:*:*               = accept generic_jdbc11
jdbc14:*:*:*:*:*:*               = accept generic_jdbc14

; ODBC generic catch-all
odbc:*:*:*:*:*:*                 = accept generic_odbc

; Oracle 19.x — Jet/MSOffice clients get a separate agent
ora190:*:*:*:*:jet:*             = accept generic_ora190_jet
ora190:*:*:*:*:*:*               = accept generic_odbc

; DSN-specific ODBC rule (custom addition)
odbc:MyDSN:*:*:*:*:*             = accept generic_odbc_MyDSN
```

---

## `[generic_<name>]` — Database Server Agent Sections

Each section defines one DB agent type. The `[Mapping Rules]` `accept` target must match a section name.

| Key | Default | Description |
|---|---|---|
| `Description` | _(text)_ | Human-readable description of this agent |
| `Program` | _(binary name)_ | Agent binary name (resolved relative to `BinaryDirectory`) |
| `CommandLine` | _(empty)_ | Additional flags passed to the agent binary |
| `Environment` | _(env section name)_ | Names the `[Environment X]` section to use |
| `Directory` | _(empty)_ | Working directory for the spawned agent process |
| `Database` | _(empty)_ | Default database/DSN name (overrides client-supplied value if set) |
| `ConnectOptions` | _(empty)_ | Driver-specific connection option string |
| `UserID` | _(empty)_ | Forced login UID (overrides client-supplied UID if set) |
| `Password` | _(empty)_ | Forced login password |
| `ReadOnly` | `No` | If `Yes`, disallow write operations |
| `ServerOptions` | _(empty)_ | Options string passed to the DB server (native format) |
| `OpsysLogin` | `No` | If `Yes`, perform OS login before spawning the agent |
| `ReUse` | _(varies)_ | Agent reuse policy (see below) |
| `SSLKeyFile` | _(empty)_ | SSL certificate for this agent's connections |
| `SSLRequired` | `No` | Require SSL for this agent |

**ReUse values:**
| Value | Meaning |
|---|---|
| `never` | Spawn a new process for every connection |
| `always` | Reuse the same process for all connections |
| `upto <n>` | Reuse up to `n` connections per process |
| `ifreadonly` | Reuse only for read-only connections |
| `ifsame database` | Reuse if the same database is requested |
| `ifsame process` | Reuse within the same OS process |
| `ifsame options` | Reuse if connect options match |
| `ifsame application` | Reuse if application name matches |
| `ifsame user` | Reuse if UID matches |
| `ifsame machine` | Reuse if client machine matches |
| `ifsame opsys` | Reuse if client OS matches |

**ODBC agent example:**
```ini
[generic_odbc]
Description     = Default settings for ODBC agent
Program         = odbc_mv
Environment     = ODBC
ReUse           = always
;Database       =
;Userid         =
;Password       =
;ReadOnly       = Yes
```

**JDBC agent example:**
```ini
[generic_jdbc14]
Description     = Default settings for ODBC-JDBC JDK1.4 bridge agent
Program         = jdbc14_sv
CommandLine     =
Environment     = JDBC14
ReUse           = never
;Database       =
;Userid         =
;Password       =
;ReadOnly       = Yes
```

**DSN-specific ODBC agent example (custom):**
```ini
[generic_odbc_MyDSN]
Description     = ODBC agent for MyDSN
Program         = odbc_mv
Environment     = ODBC
ReUse           = always
Database        = MyDSN
```
