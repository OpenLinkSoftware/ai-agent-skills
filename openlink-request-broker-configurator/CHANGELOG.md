# Changelog — openlink-request-broker-configurator

## v1.0.0 — 2026-03-24

### Added
- Initial release: view, add, edit, and remove entries in the OpenLink Request Broker rule book (`oplrqb.ini`)
- **ODBC Agent wizard** — discovers host DSNs from OS config files or www_sv, presents a list for user selection, generates per-DSN `[generic_odbc_<dsn>]` agent sections, Domain Alias entries, and Mapping Rules
- **JDBC Agent wizard** — scans `$CLASSPATH` and common JAR directories, matches JARs against a driver registry (Virtuoso, Oracle, PostgreSQL, SQL Server, MySQL, Informix, OpenLink), prompts for URL parameters, generates `[Environment JDBC<n>]` sections, `[generic_jdbc<n>]` agent sections, Domain Aliases, and Mapping Rules
- **Mode C** — www_sv HTTP Admin Assistant (preferred): all operations via curl to `brkbook`, `brksetup`, `brkagents`, `brkmaped`, `brkalias`, `brklog`, `brkver`, `brkconn`, `brkinit`, `brkzero`, `brklic`
- **Mode A** — direct file access fallback: Python `RawConfigParser(strict=False, delimiters=('=',))` for all sections; `inicheck` validation before broker reinit
- Full Mapping Rules management: list, add, delete, reorder
- DB Agent section management (`[generic_*]` and `[Environment *]` sections)
- Broker global settings: `[Request Broker]`, `[Protocol TCP]`, `[Communications]`, `[Security]`
- Broker reinit (`oplshut +reinit` / `/scripts/brkinit`) and full restart for macOS and Linux
- Broker log viewing via www_sv or direct file tail; version detection
- `references/rulebook-structure.md` — complete parameter reference grounded in actual `oplrqb.ini`
- `references/broker-www_sv-endpoints.md` — broker www_sv endpoint reference with full POST field specs and curl examples
- `references/jdbc-driver-registry.md` — JAR filename patterns, driver classes, URL templates, and pre-existing JDBC slot table
- `references/odbc-dsn-examples.md` — ODBC DSN config file locations, DSN-to-broker-rule generation walkthrough (Domain Alias + agent section + mapping rule), five DSN type examples (Multi-Tier, Virtuoso, PostgreSQL Lite, MySQL Lite, SQL Server), token naming convention, ReadOnly/ReUse recommendations, FetchBufferSize guidance
