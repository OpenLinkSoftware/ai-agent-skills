# Common ODBC Error Codes and Fixes

## SQLSTATE Reference

### Connection Errors

| SQLSTATE | Message | Cause | Fix |
|---|---|---|---|
| `08001` | Client unable to establish connection | Host/port unreachable | Verify server is running; check Host/Port in DSN |
| `08003` | Connection not open | Stale handle | Re-connect; restart application |
| `08S01` | Communication link failure | Network dropped mid-session | Check network; retry |
| `28000` | Invalid authorization specification | Wrong UID or PWD | Correct credentials in DSN or connection string |
| `IM002` | Data source name not found | DSN missing from `odbc.ini` | Add DSN entry to `/Library/ODBC/odbc.ini` |
| `IM003` | Driver not found | Driver path invalid in `odbcinst.ini` | Check `.bundle` path exists |
| `IM004` | Driver's SQLAllocHandle failed | Driver binary corrupt or wrong arch | Reinstall driver; check arm64 vs x86_64 |
| `IM006` | Driver's SQLSetConnectAttr failed | Driver rejected a connection attribute | Remove unsupported attributes from DSN |
| `S1000` | General error / Login failed | Authentication rejected | Verify UID/PWD against target database |

### Query Errors

| SQLSTATE | Message | Cause | Fix |
|---|---|---|---|
| `42000` | Syntax error or access violation | Bad SQL syntax or permission denied | Check query syntax; verify user privileges |
| `42S02` | Table or view not found | Object does not exist | Check schema/table name |
| `22003` | Numeric value out of range | Data overflow | Check column types |
| `HY000` | General error | Varies | Check full error message text |
| `HYT00` | Timeout expired | Query or connection timeout | Increase timeout; optimize query |
| `HYT01` | Connection timeout expired | Server too slow to respond | Check server load; increase `ConnectionTimeout` |

---

## iODBC-Specific Messages

| Message Fragment | Meaning |
|---|---|
| `Driver connected!` | Successful connection |
| `[ODBC][Driver Manager]` prefix | Error raised by iODBC, not the driver |
| `[OpenLink]` prefix | Error raised by OpenLink driver |
| `iODBC Error` + no SQLSTATE | Driver manager config issue |

## unixODBC-Specific Messages

| Message Fragment | Meaning |
|---|---|
| `[unixODBC]` prefix | Error raised by unixODBC driver manager |
| `[ODBC Driver Manager]` | Driver manager layer error |
| `SQLDriverConnect` failed | Connection string issue |
| `Can't open lib` | Driver `.so` path wrong or missing |

---

## Diagnostic Steps

1. **Run `odbcinst -j`** — confirms which config files unixODBC is actually reading
2. **Run `iodbc-config --prefix`** — confirms iODBC installation root
3. **Check driver binary exists** — `ls "/Library/ODBC/<DriverName>.bundle/Contents/MacOS/"`
4. **Test with minimal connection string** — `DSN=name;UID=user;PWD=pass` (no extras)
5. **Try Unicode binary** — if ANSI `iodbctest`/`isql` fails, try `iodbctestw`/`iusql`
6. **Check file permissions** — `ls -l /Library/ODBC/odbc.ini` (needs read access)
