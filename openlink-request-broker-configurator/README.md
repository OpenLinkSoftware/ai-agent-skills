# OpenLink Request Broker Configurator Skill

Configure and manage the OpenLink Request Broker (`oplrqb`) rule book (`oplrqb.ini`) — the configuration file that controls how incoming database connection requests are routed to DB agents.

## What It Does

- **ODBC Agent wizard** — discovers DSNs installed on the host OS, presents a selection list, and generates dedicated agent sections and Mapping Rules for each chosen DSN
- **JDBC Agent wizard** — scans `$CLASSPATH` and common JAR directories, matches discovered JARs against a built-in driver registry (Virtuoso, Oracle, PostgreSQL, SQL Server, MySQL, Informix, OpenLink), prompts for connection parameters, and generates JDBC agent sections and rules
- **Full rule book management** — view, add, edit, and delete Mapping Rules, `[generic_*]` agent sections, `[Environment *]` sections, and alias sections
- **Broker global settings** — view and edit `[Request Broker]`, `[Protocol TCP]`, `[Communications]`, and `[Security]` sections
- **Broker operations** — reinitialize (reload rule book without restart), full restart, log viewing, version detection
- **Two modes** — www_sv HTTP Admin Assistant (preferred) or direct file edit (fallback)

## Supported Platforms

| OS | Mode C (www_sv) | Mode A (Direct file) |
|---|---|---|
| macOS | `http://localhost:8000` | `/Library/Application Support/openlink/bin/oplrqb.ini` |
| Linux | `http://localhost:8000` | `/opt/openlink/bin/oplrqb.ini` |

## Requirements

- OpenLink Request Broker installed (`oplrqb`)
- www_sv Admin Assistant (for Mode C) or direct file access (for Mode A)
- `inicheck` utility (for Mode A validation)
- Python 3 (for Mode A configparser operations)

## Usage Examples

- "Configure ODBC agents for the broker"
- "Set up JDBC agent rules from my installed drivers"
- "Show the broker rule book"
- "Add a mapping rule for the Northwind DSN"
- "View the DB agent settings for generic\_odbc"
- "Edit the Environment section for JDBC14"
- "View active broker connections"
- "Reinitialize the broker after my rule book changes"
- "Show the broker log"
- "What version of oplrqb is installed?"

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | Main skill definition — wizards, operations, curl patterns, direct file patterns |
| `references/rulebook-structure.md` | Complete section and key reference for `oplrqb.ini` |
| `references/broker-www_sv-endpoints.md` | www_sv broker endpoint reference with POST field specs |
| `references/jdbc-driver-registry.md` | JDBC driver JAR patterns, driver classes, URL templates |
| `references/odbc-dsn-examples.md` | ODBC DSN config examples, broker rule generation, token naming |

## Related Skills

| Skill | Purpose |
|---|---|
| `iodbc-dsn-manager` | Configure ODBC DSNs on the host OS |
| `openlink-license-manager` | Start, stop, and manage the OpenLink License Manager daemon |
| `openlink-license-reader` | Read and inspect OpenLink `.lic` license files |

## Version

**1.0.0** — Initial release. ODBC and JDBC agent configuration wizards with host DSN discovery and JDBC driver auto-detection. Full rule book management via www_sv HTTP (Mode C) and direct file access (Mode A).
