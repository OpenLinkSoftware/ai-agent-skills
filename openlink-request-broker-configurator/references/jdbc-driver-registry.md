# JDBC Driver Registry

Driver-to-URL mapping derived from test files in the OpenLink JDBC examples collection.

---

## Driver Discovery Priority

1. **`$CLASSPATH`** — split by `:` (Unix) or `;` (Windows); scan for `*.jar` files matching patterns below
2. **Common JAR directories** (if `$CLASSPATH` unset or no matches):
   - `/usr/local/lib/`
   - `~/lib/`
   - `/opt/jdbc/`
   - `/Library/Java/Extensions/` (macOS)
   - `/usr/share/java/` (Linux)
3. **JDBC SPI inspection** — peek inside each JAR for registered driver class:
   ```bash
   unzip -p <jar-path> META-INF/services/java.sql.Driver 2>/dev/null
   ```
   The SPI file lists the driver class name(s) registered by that JAR.

---

## Driver Registry

### Virtuoso (OpenLink)

| Field | Value |
|---|---|
| JAR pattern | `virtuoso-jdbc*.jar` |
| Driver class | `virtuoso.jdbc4.Driver` |
| URL template | `jdbc:virtuoso://<host>:1111/charset=UTF-8/log_enable=2` |
| Default port | `1111` |
| URL variants | `jdbc:virtuoso://<host>:1111/UID=dba/PWD=dba` |
| Broker env section | `[Environment JDBC4]` (or any available JDBC slot) |
| Domain Alias | `Virtuoso JDBC = jdbc4` |

### Oracle

| Field | Value |
|---|---|
| JAR pattern | `ojdbc*.jar` (e.g. `ojdbc8.jar`, `ojdbc11.jar`) |
| Driver class | `oracle.jdbc.OracleDriver` |
| URL template | `jdbc:oracle:thin:@<host>:1521:<SID>` |
| Default port | `1521` |
| URL variants | `jdbc:oracle:thin:@<host>:<port>/<service_name>` (service name form) |
| Domain Alias | `Oracle JDBC = jdbc<n>` |

### PostgreSQL

| Field | Value |
|---|---|
| JAR pattern | `postgresql-*.jar` (e.g. `postgresql-42.7.3.jar`) |
| Driver class | `org.postgresql.Driver` |
| URL template | `jdbc:postgresql://<host>:5432/<database>` |
| Default port | `5432` |
| URL variants | `jdbc:postgresql://<host>:<port>/<db>?user=<uid>&password=<pwd>` |
| Domain Alias | `PostgreSQL JDBC = jdbc<n>` |

### SQL Server (Microsoft)

| Field | Value |
|---|---|
| JAR pattern | `mssql-jdbc-*.jar` (e.g. `mssql-jdbc-12.6.0.jre11.jar`) |
| Driver class | `com.microsoft.sqlserver.jdbc.SQLServerDriver` |
| URL template | `jdbc:sqlserver://<host>:1433;databaseName=<db>;encrypt=true` |
| Default port | `1433` |
| URL variants | `jdbc:sqlserver://<host>:<port>;databaseName=<db>;trustServerCertificate=true` |
| Domain Alias | `SQLServer JDBC = jdbc<n>` |

### MySQL

| Field | Value |
|---|---|
| JAR pattern | `mysql-connector-java-*.jar` or `mysql-connector-j-*.jar` |
| Driver class | `com.mysql.cj.jdbc.Driver` |
| URL template | `jdbc:mysql://<host>:3306/<database>?useSSL=false&serverTimezone=UTC` |
| Default port | `3306` |
| URL variants | `jdbc:mysql://<host>:<port>/<db>?user=<uid>&password=<pwd>` |
| Domain Alias | `MySQL JDBC = jdbc<n>` |

### Informix

| Field | Value |
|---|---|
| JAR pattern | `ifxjdbc.jar` or `ifxjdbc-*.jar` |
| Driver class | `com.informix.jdbc.IfxDriver` (also `com.informix.jdbc.InformixDriver`) |
| URL template | `jdbc:informix-sqli://<host>:1526/<database>:INFORMIXSERVER=<server>` |
| Default port | `1526` |
| URL variants | `jdbc:informix-sqli://<host>:<port>/<db>:INFORMIXSERVER=<srv>` |
| Domain Alias | `Informix JDBC = jdbc<n>` |

### OpenLink Multi-Tier JDBC (bridges to remote DBs via Request Broker)

| Field | Value |
|---|---|
| JAR pattern | `openlink-jdbc*.jar` or `megathin*.jar` |
| Driver class | `openlink.jdbc4.Driver` |
| URL template (ODBC DSN form) | `jdbc:openlink://ODBC/DSN=<dsnname>` |
| URL template (direct form) | `jdbc:openlink://<broker-host>:5000/SVT=<ServerType>/DATABASE=<db>/OPTIONS=<opts>` |
| Default broker port | `5000` |
| URL examples | `jdbc:openlink://ODBC/DSN=Oracle MT` |
| | `jdbc:openlink://oracle-host:5000/SVT=Oracle 18.x/OPTIONS=XE` |
| | `jdbc:openlink://informix-host:5000/SVT=Informix 11/DATABASE=stores_demo/OPTIONS=ol_informix1410` |
| | `jdbc:openlink://sqlserver-host:5000/SVT=SQLServer/DATABASE=northwind/OPTIONS=-H dev-gw.openlinksw.com -P 1433` |
| Domain Alias | `OpenLink JDBC = jdbc<n>` |

---

## Pre-existing JDBC Slots in Rulebook

The default `oplrqb.ini` ships with JDBC slots pre-defined for the ODBC-JDBC bridge:

| Slot | Domain Alias | Agent Section | Program |
|---|---|---|---|
| jdbc11 | `Jdbc 1.1 = jdbc11` | `[generic_jdbc11]` | `jdbc11_sv` |
| jdbc12 | `Jdbc 1.2 = jdbc12` | `[generic_jdbc12]` | `jdbc12_sv` |
| jdbc13 | `Jdbc 1.3 = jdbc13` | `[generic_jdbc13]` | `jdbc13_sv` |
| jdbc14 | `Jdbc 1.4 = jdbc14` | `[generic_jdbc14]` | `jdbc14_sv` |
| jdbc15 | `Jdbc 1.5 = jdbc15` | `[generic_jdbc15]` | `jdbc15_sv` |
| jdbc16 | `Jdbc 1.6 = jdbc16` | `[generic_jdbc16]` | `jdbc16_sv` |
| jdbc17 | `Jdbc 1.7 = jdbc17` | `[generic_jdbc17]` | `jdbc17_sv` |
| jdbc18 | `Jdbc 1.8 = jdbc18` | `[generic_jdbc18]` | `jdbc18_sv` |

When configuring a JDBC driver, reuse one of these existing slots (update its `[Environment JDBC<n>]` `CLASSPATH`) or append a new custom slot (e.g. `jdbcvirt`, `jdbcpgr`) with a matching Domain Alias.

---

## CLASSPATH Note

The `[Environment JDBC<n>]` section injects `CLASSPATH` into the agent process before it connects. The CLASSPATH must point to the driver JAR, not the directory containing it:

```ini
[Environment JDBC14]
CLASSPATH   = /usr/local/lib/postgresql-42.7.3.jar
```

Multiple JARs: separate with `:` on Unix:
```ini
CLASSPATH   = /usr/local/lib/postgresql-42.7.3.jar:/usr/local/lib/other.jar
```

---

## Java Version Compatibility

| Driver | Minimum Java | Recommended JAR |
|---|---|---|
| Oracle | Java 8+ | `ojdbc8.jar` (Java 8), `ojdbc11.jar` (Java 11+) |
| PostgreSQL | Java 8+ | `postgresql-42.x.x.jar` |
| SQL Server | Java 8+ | `mssql-jdbc-12.x.x.jre8.jar` (Java 8), `.jre11.jar` (Java 11+) |
| MySQL | Java 8+ | `mysql-connector-j-8.x.x.jar` |
| Virtuoso | Java 7+ | `virtuoso-jdbc4.jar` |
| Informix | Java 8+ | `ifxjdbc.jar` |
| OpenLink | Java 7+ | `megathin4_1.jar` or `openlink-jdbc4.jar` |
