# ODBC Connection String Formats

## Standard DSN-based Connection Strings

Used with `iodbctest`, `isql`, and application connection APIs.

```
DSN=<dsn_name>;UID=<username>;PWD=<password>
```

**Examples:**
```
DSN=Local Virtuoso;UID=dba;PWD=dba
DSN=PostgresLite;UID=postgres;PWD=secret
DSN=Azure SQL Server;UID=admin@myserver;PWD=P@ssw0rd
```

---

## DSN-less (Driver Direct) Connection Strings

Bypasses `odbc.ini` entirely — useful for testing a driver directly.

### OpenLink Virtuoso (Unicode)
```
DRIVER=/Library/ODBC/OpenLink Virtuoso ODBC Driver (Unicode).bundle/Contents/MacOS/OpenLink Virtuoso ODBC Driver (Unicode);HOST=localhost;PORT=1111;DATABASE=DB;UID=dba;PWD=dba
```

### OpenLink Virtuoso v5.0
```
DRIVER=/Library/ODBC/OpenLink Virtuoso ODBC Driver v5.0.bundle/Contents/MacOS/OpenLink Virtuoso ODBC Driver v5.0;HOST=localhost;PORT=1111;UID=dba;PWD=dba
```

### Generic format
```
DRIVER=<driver_name_from_odbcinst.ini>;SERVER=<host>;PORT=<port>;DATABASE=<db>;UID=<user>;PWD=<pass>
```

---

## iODBC Usage

```bash
# DSN-based
echo "SELECT 'ok'; quit" | /usr/local/iODBC/bin/iodbctest "DSN=Local Virtuoso;UID=dba;PWD=dba"

# Unicode variant
echo "SELECT 'ok'; quit" | /usr/local/iODBC/bin/iodbctestw "DSN=Local Virtuoso;UID=dba;PWD=dba"

# DSN-less
echo "quit" | /usr/local/iODBC/bin/iodbctest "DRIVER=OpenLink Virtuoso ODBC Driver (Unicode);HOST=localhost;PORT=1111;UID=dba;PWD=dba"
```

---

## unixODBC Usage

```bash
# DSN-based (positional: DSN UID PWD)
isql "Local Virtuoso" dba dba -b

# DSN-based with options
echo "SELECT 'ok'" | isql "Local Virtuoso" dba dba -b -d"|" -c

# Unicode variant
iusql "Local Virtuoso" dba dba -b

# With connection string (iusql supports this)
iusql "DSN=Local Virtuoso;UID=dba;PWD=dba" -b
```

### isql Options
| Flag | Effect |
|---|---|
| `-b` | Batch mode (no prompts) |
| `-i` | Unverbose (suppress headers) |
| `-c` | Show column names on first row |
| `-dx` | Delimit columns with character `x` |
| `-w` | Wrap output in HTML table |
| `-m N` | Limit display width to N chars |

---

## Common DSN Parameters by Driver Type

### Virtuoso (OpenLink)
| Key | Description | Example |
|---|---|---|
| `Host` | Server hostname | `localhost` |
| `Port` | Virtuoso port | `1111` |
| `Database` | Catalog/DB | `DB` |
| `UID` | Username | `dba` |
| `PWD` | Password | `dba` |
| `Encrypt` | SSL mode | `0` / `1` / `3` |

### PostgreSQL (OpenLink Lite)
| Key | Description | Example |
|---|---|---|
| `Host` | PG server | `localhost` |
| `Port` | PG port | `5432` |
| `Database` | Database name | `mydb` |
| `UID` | Username | `postgres` |
| `PWD` | Password | — |

### MySQL (OpenLink Lite)
| Key | Description | Example |
|---|---|---|
| `Host` | MySQL server | `localhost` |
| `Port` | MySQL port | `3306` |
| `Database` | Schema name | `mydb` |
| `UID` | Username | `root` |
| `PWD` | Password | — |

### SQL Server (OpenLink Lite)
| Key | Description | Example |
|---|---|---|
| `Host` | SQL Server host | `myserver.database.windows.net` |
| `Port` | SQL Server port | `1433` |
| `Database` | Database name | `master` |
| `UID` | Login | `sa` |
| `PWD` | Password | — |

---

## Notes

- DSN names with spaces must be **quoted** in shell: `"DSN=Local Virtuoso;..."`
- `PWD` in the connection string overrides the `odbc.ini` value
- For SSL/TLS connections to Virtuoso set `Encrypt=3` (require) or `Encrypt=1` (prefer)
- The `Driver` key in DSN-less strings can use either the driver name (from `odbcinst.ini`) or the full path to the `.bundle`/`.so`
