# Changelog — openlink-license-manager

## v1.5.0 — 2026-03-24

### Added
- License directory validation before `+start` on macOS/Linux: checks existence and presence of `.lic` files
- Decision table for all directory-check outcomes (exists+lic, exists+no-lic, missing)
- Halts with actionable message when `$OPL_LICENSE_DIR` is unset and OS default path is missing or empty
- Troubleshooting row: `+directory` path missing or empty

## v1.4.0 — 2026-03-24

### Added
- macOS/Linux: version detection before `+start`; derives `+directory` value for v1.3.6+
- Windows: PowerShell `Start-Service`/`Stop-Service -Force`/`Restart-Service` as Priority 1
- Windows: `net start/stop` and `sc` demoted to Priority 2 fallback
- Windows: `Set-Service -StartupType` for enable/disable auto-start via PowerShell

## v1.3.0 — 2026-03-24

### Added
- Step 1 Check A: symlink detection at `/usr/local/bin/oplmgr` before passwordless sudo check
- Automatic symlink creation attempt (`sudo ln -s`) when symlink is missing
- Skill self-heals symlink when passwordless sudo is already configured for another rule

## v1.2.0 — 2026-03-24

### Changed
- All macOS `sudo` commands now use `/usr/local/bin/oplmgr` symlink (sudoers cannot handle paths with spaces)
- Sudoers setup instructions updated to include symlink creation step

### Added
- Troubleshooting row: `expected a fully-qualified path name` (sudoers parse error with space in path)

## v1.1.0 — 2026-03-24

### Added
- Step 1 Check B: passwordless sudo pre-check (`sudo -n`) before issuing any privileged command
- Setup instructions for `/etc/sudoers.d/oplmgr` on macOS and Linux (systemd)
- Troubleshooting row: `sudo: a terminal is required` (no TTY in non-interactive Claude Code shell)

## v1.0.0 — 2026-03-24

### Added
- Initial release: start, stop, restart, status, and enable/disable at boot for the OpenLink License Manager (`oplmgr`)
- macOS: direct `oplmgr +start/+stop` binary (Priority 1) with `launchctl load/unload` fallback (Priority 2)
- Linux: systemd service management (`systemctl`) with manual binary fallback for non-systemd systems
- Windows: `net start/stop` service commands and `sc config` for auto-start configuration
- OS and init-system auto-detection (Darwin / Linux + systemd check / Windows)
- Confirmation-before-execution rule for all privileged commands
- `oplmgr -?` version detection with behavioral notes for v1.3.5 vs v1.3.6+
- Automatic post-action status check after start/stop
- Troubleshooting table covering common failure modes across all platforms
