# OpenLink License Manager Skill

Start, stop, restart, enable at boot, and check the status of the OpenLink License Manager (`oplmgr`) daemon on macOS, Linux, and Windows.

## What It Does

- Detects the current OS and (on Linux) init system automatically
- Shows the exact command before executing — never runs privileged commands without confirmation
- Supports all three platforms: macOS, Linux (systemd and manual), Windows (service)
- On macOS: tries direct `oplmgr +start/+stop` binary first; falls back to `launchctl` for boot persistence
- On Linux: uses `systemctl` when available; falls back to manual binary invocation
- On Windows: manages via `net start/stop` and `sc config` for auto-start
- Detects `oplmgr` version and surfaces behavioral differences between v1.3.5 and v1.3.6+
- Runs a status check automatically after any start or stop action

## Supported Platforms

| OS | Method |
|---|---|
| macOS | `oplmgr +start/+stop` (binary) → `launchctl load/unload` (fallback) |
| Linux (systemd) | `systemctl start/stop/enable oplmgr.service` |
| Linux (manual) | `/opt/openlink/oplmgr/oplmgr -start/-stop` |
| Windows | `net start/stop "OpenLink License Manager"` + `sc config` |

## Requirements

- `sudo` access (macOS/Linux) or Administrator privileges (Windows)
- `oplmgr` binary or service installed

## Usage Examples

- "Start the license manager"
- "Stop oplmgr"
- "Restart the OpenLink License Manager"
- "Is oplmgr running?"
- "Enable oplmgr at boot on Linux"
- "Disable auto-start for the license manager on Windows"
- "What version of oplmgr is installed?"

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | Main skill definition — commands, platform routing, troubleshooting |

## Version

**1.5.0** — License directory validation, PowerShell priority on Windows, symlink self-healing, passwordless sudo pre-check, and `+directory` derivation for v1.3.6+.
