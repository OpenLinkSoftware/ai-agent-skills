---
name: openlink-license-manager
description: "Start, stop, restart, enable at boot, and check the status of the OpenLink License Manager (oplmgr) daemon on macOS, Linux, and Windows. Detects OS and init system automatically. Use when the user asks to start, stop, restart, enable, disable, or check the status of the OpenLink License Manager or oplmgr."
---

# OpenLink License Manager Skill

## Purpose
Manage the OpenLink License Manager daemon (`oplmgr`) lifecycle across macOS, Linux, and Windows. Covers start, stop, restart, status, enable/disable at boot, and version detection.

---

## Step 0 — Detect OS and Init System

```bash
# Detect OS
uname -s   # Darwin = macOS, Linux = Linux
           # Windows: uname absent; detect via %OS% or assume Windows if neither works

# On Linux only — detect init system
systemctl --version 2>/dev/null && echo "systemd" || echo "manual"
```

| `uname -s` output | OS |
|---|---|
| `Darwin` | macOS |
| `Linux` | Linux |
| (absent / error) | Windows |

If OS detection is ambiguous, ask the user to confirm their OS before proceeding.

---

## Step 1 — Pre-flight Checks (macOS and Linux only)

Run these checks in order before attempting any privileged command. Claude Code runs non-interactively (no TTY), so both the symlink and passwordless sudo must be in place.

### Check A — Symlink at `/usr/local/bin/oplmgr`

`sudoers` cannot handle paths containing spaces. The real binary lives at `/Library/Application Support/openlink/bin/oplmgr`, so a space-free symlink is required.

```bash
ls -la /usr/local/bin/oplmgr 2>/dev/null && echo "symlink OK" || echo "symlink MISSING"
```

**If symlink is MISSING**, attempt to create it automatically:

```bash
sudo ln -s "/Library/Application Support/openlink/bin/oplmgr" /usr/local/bin/oplmgr
```

- If this `sudo` succeeds (passwordless sudo already configured for another rule or user is root): proceed.
- If this `sudo` fails with a password prompt error: inform the user and ask them to run the command in Terminal.app:
  ```bash
  sudo ln -s "/Library/Application Support/openlink/bin/oplmgr" /usr/local/bin/oplmgr
  ```
  Then retry from the top of Step 1.

On Linux: no symlink is needed if the binary path already contains no spaces (e.g. `/opt/openlink/oplmgr/oplmgr`).

---

### Check B — Passwordless sudo for `/usr/local/bin/oplmgr`

```bash
sudo -n /usr/local/bin/oplmgr +stop 2>&1; echo "exit:$?"
# exit:0 or a non-password error = passwordless sudo OK
# "sudo: a password is required" = NOT configured
```

**If passwordless sudo is NOT configured**, stop and inform the user:

> Passwordless `sudo` is not configured for `oplmgr`. Please run the following in Terminal.app:
>
> ```bash
> echo 'YOUR_USERNAME ALL=(ALL) NOPASSWD: /usr/local/bin/oplmgr' | sudo tee /etc/sudoers.d/oplmgr && sudo chmod 440 /etc/sudoers.d/oplmgr
> ```
>
> On Linux (systemd), grant passwordless sudo for `systemctl` instead:
> ```bash
> echo 'YOUR_USERNAME ALL=(ALL) NOPASSWD: /bin/systemctl start oplmgr.service, /bin/systemctl stop oplmgr.service, /bin/systemctl restart oplmgr.service, /bin/systemctl status oplmgr.service' | sudo tee /etc/sudoers.d/oplmgr && sudo chmod 440 /etc/sudoers.d/oplmgr
> ```
>
> Then return here and retry.

**Windows**: no pre-flight checks needed — Administrator privilege is handled by the OS service manager.

---

## Step 2 — Show Command and Confirm

**Always display the exact command(s) that will be run and ask the user to confirm before executing.**

Present the applicable command from the tables below, then proceed only on confirmation.

---

## Step 3 — Command Reference by Platform

### macOS

#### Priority 1 — Direct binary (preferred)

Try `oplmgr` from its installation directory first:

```bash
# Locate the binary (prefer symlink at /usr/local/bin/oplmgr)
which oplmgr 2>/dev/null || ls /usr/local/bin/oplmgr 2>/dev/null
```

Before starting, detect the version and derive and validate the `+directory` value:

```bash
# Step A: Detect version
/usr/local/bin/oplmgr 2>&1 | head -5

# Step B: Derive license directory
LICENSE_DIR="${OPL_LICENSE_DIR:-/Library/Application Support/openlink/Licenses}"

# Step C: Validate — directory must exist and contain at least one .lic file
ls "${LICENSE_DIR}"/*.lic 2>/dev/null | head -1
```

**Decision table:**

| Condition | Action |
|---|---|
| Directory exists and contains `.lic` files | Proceed — use as `+directory` |
| Directory exists but no `.lic` files | Warn the user; ask them to confirm the correct license directory before proceeding |
| Directory does not exist | Halt — inform the user that no license directory was found and ask for the correct path |
| `$OPL_LICENSE_DIR` is unset and default missing | Halt — inform the user with the exact message below |

**If no valid license directory is found**, stop and inform the user:

> No license directory could be found. Neither `$OPL_LICENSE_DIR` nor the default path (`/Library/Application Support/openlink/Licenses/`) exists or contains `.lic` files.
> Please provide the path to the directory containing your OpenLink license files, then retry.

| Version | Start command |
|---|---|
| v1.3.6+ | `sudo /usr/local/bin/oplmgr +start +directory "<validated-license-dir>"` |
| v1.3.5 and earlier | `sudo /usr/local/bin/oplmgr +start` (uses `$OPL_LICENSE_DIR` automatically; warn if unset) |

| Action | Command |
|---|---|
| Start (v1.3.6+) | `sudo /usr/local/bin/oplmgr +start +directory "<validated-license-dir>"` |
| Start (v1.3.5−) | `sudo /usr/local/bin/oplmgr +start` |
| Stop | `sudo /usr/local/bin/oplmgr +stop` |
| Status | `ps aux \| grep -i oplmgr \| grep -v grep` |
| Version | `/usr/local/bin/oplmgr 2>&1 \| head -5` |

Canonical binary location: `/Library/Application Support/openlink/bin/oplmgr`
Symlink (no spaces — required for sudoers): `/usr/local/bin/oplmgr`

> **Important:** Always use `/usr/local/bin/oplmgr` (the symlink) for `sudo` commands. The real path contains spaces which `sudoers` cannot handle.

#### Priority 2 — launchctl fallback (if binary unavailable or for boot persistence)

| Action | Command |
|---|---|
| Start | `sudo /bin/launchctl load "/Library/LaunchDaemons/com.openlinksw.oplmgr.plist"` |
| Stop | `sudo /bin/launchctl unload "/Library/LaunchDaemons/com.openlinksw.oplmgr.plist"` |
| Status | `sudo launchctl list \| grep oplmgr` |
| Enable at boot | Persistent automatically via LaunchDaemon plist (no separate enable step needed) |

> Note: If a non-default license directory is used, edit the plist at `/Library/LaunchDaemons/com.openlinksw.oplmgr.plist` to reflect the new path before loading.

---

### Linux — systemd (preferred when available)

```bash
# Check for systemd
systemctl --version 2>/dev/null
```

| Action | Command |
|---|---|
| Start | `sudo systemctl start oplmgr.service` |
| Stop | `sudo systemctl stop oplmgr.service` |
| Restart | `sudo systemctl restart oplmgr.service` |
| Status | `sudo systemctl status oplmgr.service` |
| Enable at boot | `sudo systemctl enable oplmgr.service` |
| Disable at boot | `sudo systemctl disable oplmgr.service` |
| Version | `oplmgr -?` |

---

### Linux — Manual (no systemd)

| Action | Command |
|---|---|
| Start (v1.3.6+) | `sudo /opt/openlink/oplmgr/oplmgr +start +directory "${OPL_LICENSE_DIR:-/etc/oplmgr}"` |
| Start (v1.3.5−) | `sudo /opt/openlink/oplmgr/oplmgr -start` |
| Stop | `sudo /opt/openlink/oplmgr/oplmgr -stop` |
| Status | `ps aux \| grep -i oplmgr \| grep -v grep` |
| Enable at boot | N/A — manual start only |
| Version | `/opt/openlink/oplmgr/oplmgr 2>&1 \| head -5` |

> Note: Installation path may vary. Common alternatives: `/opt/openlink/bin/oplmgr`, or per-product `bin/` directories. Check `$OPL_LICENSE_DIR` for hints.

---

### Windows

> Administrator privileges are required for all service operations.

#### Priority 1 — PowerShell (preferred)

| Action | Command |
|---|---|
| Start | `powershell -Command "Start-Service -Name 'OpenLink License Manager'"` |
| Stop | `powershell -Command "Stop-Service -Name 'OpenLink License Manager' -Force"` |
| Restart | `powershell -Command "Restart-Service -Name 'OpenLink License Manager' -Force"` |
| Status | `powershell -Command "Get-Service -Name 'OpenLink License Manager'"` |
| Enable auto-start | `powershell -Command "Set-Service -Name 'OpenLink License Manager' -StartupType Automatic"` |
| Disable auto-start | `powershell -Command "Set-Service -Name 'OpenLink License Manager' -StartupType Manual"` |
| Version | `powershell -Command "& '$env:windir\oplmgr.exe' -?"` |

#### Priority 2 — net / sc (fallback)

| Action | Command |
|---|---|
| Start | `net start "OpenLink License Manager"` |
| Stop | `net stop "OpenLink License Manager"` |
| Restart | `net stop "OpenLink License Manager" && net start "OpenLink License Manager"` |
| Status | `sc query "OpenLink License Manager"` |
| Enable auto-start | `sc config "OpenLink License Manager" start= auto` |
| Disable auto-start | `sc config "OpenLink License Manager" start= demand` |
| Version | `%windir%\oplmgr.exe -?` |

> On 64-bit Windows with mixed 32/64-bit installations: consolidate all license files in a single directory (e.g. `C:\Program Files\OpenLink Software\Licenses\`) to avoid bitness-mismatch issues with the registry lookup at:
> `HKLM\SOFTWARE\OpenLink Software\License Manager\License Directories\`

---

## Step 4 — Version Detection and Behavioral Notes

```bash
oplmgr -?
```

| Version | Behavior |
|---|---|
| **v1.3.5 and earlier** | Uses `$OPL_LICENSE_DIR` environment variable only to locate license files |
| **v1.3.6 and later** | Supports `+directory` parameter; searches `$OPL_LICENSE_DIR`, `+directory` paths, and PATH for `*.lic` files |

Default license directories by version and OS:

| OS | v1.3.5 and earlier | v1.3.6 and later |
|---|---|---|
| macOS | `/Library/Application Support/openlink/bin/` | `/Library/Application Support/openlink/Licenses/` |
| Linux | `$OPL_LICENSE_DIR` (set by `openlink.sh`) | `/etc/oplmgr/` |
| Windows | Registry-defined directories | Registry-defined directories |

---

## Step 5 — Post-Action Status Check

After any start or stop action, automatically run the status command for the detected platform and display the result to confirm the operation succeeded.

---

## Initialization Sequence

When invoked:
1. Run Step 0 — detect OS and (on Linux) init system
2. Run Step 1, Check A — verify symlink exists; attempt to create it automatically if missing
3. Run Step 1, Check B — verify passwordless sudo; halt with setup instructions if not configured
4. Run Step 2 — show the relevant command(s) and ask for confirmation
5. Execute on confirmation — run the command
6. Run Step 5 — show status output

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `sudo: a terminal is required` | No TTY — Claude Code runs non-interactively | Configure passwordless sudo via `/etc/sudoers.d/oplmgr` (see Step 1) |
| `expected a fully-qualified path name` | sudoers parse error — path contains spaces | Create symlink at `/usr/local/bin/oplmgr` and use that in the sudoers rule (see Step 1) |
| `oplmgr: command not found` | Binary not in PATH | Use full path (see Step 3 Priority 1 section for platform) |
| `launchctl: no plist found` | plist missing or path wrong | Check `/Library/LaunchDaemons/com.openlinksw.oplmgr.plist` exists |
| `Unit oplmgr.service not found` | No systemd unit installed | Fall back to manual start/stop commands |
| `Access denied` / `5: Access is denied` | Insufficient privileges on Windows | Run command prompt as Administrator |
| Service starts then stops immediately | License file not found | Check `$OPL_LICENSE_DIR` / default license path for valid `.lic` files |
| `+directory` path missing or empty | `$OPL_LICENSE_DIR` unset and default path doesn't exist | Supply the license directory path explicitly when prompted (see Step 3 decision table) |
| `sc query` shows `STOPPED` after start attempt | Service misconfigured | Check Windows Event Viewer for oplmgr errors |

---

## Version
**1.5.0** — License directory validation added before `+start` on macOS/Linux: checks existence and presence of `.lic` files; halts with actionable message when `$OPL_LICENSE_DIR` is unset and the OS default path is missing or empty. Added troubleshooting row for `+directory` path missing or empty.

**1.4.0** — macOS/Linux start now detects version and derives `+directory` value before issuing `+start` (v1.3.6+ only). Windows: PowerShell `Start-Service`/`Stop-Service` added as Priority 1; net/sc demoted to Priority 2 fallback.

**1.3.0** — Step 1 now includes Check A (symlink detection + automatic creation attempt) before Check B (passwordless sudo). Skill self-heals the symlink when possible without user intervention.

**1.2.0** — macOS commands now use `/usr/local/bin/oplmgr` symlink throughout (sudoers cannot handle paths with spaces). Setup instructions updated to include symlink creation step. Added `expected a fully-qualified path name` to troubleshooting table.

**1.1.0** — Added passwordless sudo pre-check (Step 1) with setup instructions for macOS and Linux. Added `sudo: a terminal is required` to troubleshooting table.

**1.0.0** — Initial release. macOS (binary + launchctl fallback), Linux (systemd + manual fallback), Windows (service). Version detection and behavioral notes for v1.3.5 vs v1.3.6+.
