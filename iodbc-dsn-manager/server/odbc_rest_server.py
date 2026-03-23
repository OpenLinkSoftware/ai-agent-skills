#!/usr/bin/env python3
"""
ODBC REST Server — wraps iODBC / unixODBC for remote access.
Binds to 127.0.0.1:8899 by default (use --host 0.0.0.0 to expose on LAN).

Endpoints:
  GET  /info              Driver manager version and config paths
  GET  /dsns              List all DSNs (system + user)
  GET  /dsn/<name>        Inspect a DSN section
  GET  /drivers           List all installed drivers
  GET  /driver/<name>     Inspect a driver section
  POST /test              Test DSN connectivity
                          Body: {"dsn": "...", "uid": "...", "pwd": "...", "query": "..."}

All responses are JSON. Errors return {"error": "..."} with an appropriate HTTP status.
"""

import argparse
import configparser
import json
import os
import platform
import shutil
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


# ---------------------------------------------------------------------------
# Platform-aware path resolution
# ---------------------------------------------------------------------------

def get_paths():
    system = platform.system()
    if system == "Darwin":
        return {
            "system_dsn":    Path("/Library/ODBC/odbc.ini"),
            "system_driver": Path("/Library/ODBC/odbcinst.ini"),
            "user_dsn":      Path.home() / "Library/ODBC/odbc.ini",
            "iodbctest":     Path("/usr/local/iODBC/bin/iodbctest"),
            "iodbctestw":    Path("/usr/local/iODBC/bin/iodbctestw"),
            "isql":          shutil.which("isql") or "",
            "iusql":         shutil.which("iusql") or "",
            "odbcinst":      shutil.which("odbcinst") or "",
            "iodbc_config":  Path("/usr/local/iODBC/bin/iodbc-config"),
            "os":            "Darwin",
        }
    else:  # Linux
        return {
            "system_dsn":    Path("/etc/odbc.ini"),
            "system_driver": Path("/etc/odbcinst.ini"),
            "user_dsn":      Path.home() / ".odbc.ini",
            "iodbctest":     Path(shutil.which("iodbctest") or ""),
            "iodbctestw":    Path(shutil.which("iodbctestw") or ""),
            "isql":          shutil.which("isql") or "",
            "iusql":         shutil.which("iusql") or "",
            "odbcinst":      shutil.which("odbcinst") or "",
            "iodbc_config":  Path(shutil.which("iodbc-config") or ""),
            "os":            "Linux",
        }

PATHS = get_paths()


# ---------------------------------------------------------------------------
# ODBC config helpers
# ---------------------------------------------------------------------------

def read_ini(path: Path) -> configparser.RawConfigParser:
    cfg = configparser.RawConfigParser()
    if path.exists():
        cfg.read(str(path))
    return cfg


def list_dsns() -> dict:
    result = {"system": {}, "user": {}}
    for scope, key in (("system", "system_dsn"), ("user", "user_dsn")):
        cfg = read_ini(PATHS[key])
        if cfg.has_section("ODBC Data Sources"):
            result[scope] = dict(cfg.items("ODBC Data Sources"))
    return result


def inspect_dsn(name: str) -> dict | None:
    for key in ("system_dsn", "user_dsn"):
        cfg = read_ini(PATHS[key])
        if cfg.has_section(name):
            return dict(cfg.items(name))
    return None


def list_drivers() -> dict:
    result = {"system": {}}
    cfg = read_ini(PATHS["system_driver"])
    if cfg.has_section("ODBC Drivers"):
        result["system"] = dict(cfg.items("ODBC Drivers"))
    return result


def inspect_driver(name: str) -> dict | None:
    cfg = read_ini(PATHS["system_driver"])
    if cfg.has_section(name):
        return dict(cfg.items(name))
    return None


def get_info() -> dict:
    info = {
        "os": PATHS["os"],
        "paths": {k: str(v) for k, v in PATHS.items() if k not in ("os",)},
        "available": {
            "iodbctest":  bool(PATHS["iodbctest"] and Path(PATHS["iodbctest"]).exists()),
            "iodbctestw": bool(PATHS["iodbctestw"] and Path(PATHS["iodbctestw"]).exists()),
            "isql":       bool(PATHS["isql"]),
            "iusql":      bool(PATHS["iusql"]),
            "odbcinst":   bool(PATHS["odbcinst"]),
        },
    }
    # iodbc-config version
    iodbc_cfg = PATHS["iodbc_config"]
    if iodbc_cfg and Path(iodbc_cfg).exists():
        try:
            out = subprocess.check_output([str(iodbc_cfg), "--version"], text=True).strip()
            info["iodbc_version"] = out
        except Exception:
            pass
    # unixODBC version via odbcinst -j
    if PATHS["odbcinst"]:
        try:
            out = subprocess.check_output(
                [PATHS["odbcinst"], "-j"], text=True, stderr=subprocess.STDOUT
            )
            info["unixodbc_info"] = out.strip()
        except Exception:
            pass
    return info


def test_connection(dsn: str, uid: str, pwd: str, query: str = "SELECT 'OK'") -> dict:
    """
    Run a non-interactive connection test.
    Tries iodbctest first (macOS primary), falls back to isql.
    """
    conn_str = f"DSN={dsn};UID={uid};PWD={pwd}"
    sql_input = f"{query};\nquit\n"
    errors = []

    # --- Try iodbctest ---
    for binary_key in ("iodbctest", "iodbctestw"):
        binary = PATHS[binary_key]
        if binary and Path(binary).exists():
            try:
                result = subprocess.run(
                    [str(binary), conn_str],
                    input=sql_input,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                output = result.stdout + result.stderr
                success = "Driver connected!" in output
                return {
                    "driver_manager": "iODBC",
                    "binary": str(binary),
                    "success": success,
                    "output": output.strip(),
                }
            except subprocess.TimeoutExpired:
                errors.append(f"{binary_key}: timeout")
            except Exception as e:
                errors.append(f"{binary_key}: {e}")
            break  # only try one iodbctest variant

    # --- Try isql ---
    if PATHS["isql"]:
        try:
            result = subprocess.run(
                [PATHS["isql"], dsn, uid, pwd, "-b"],
                input=f"{query}\n",
                capture_output=True,
                text=True,
                timeout=15,
            )
            output = result.stdout + result.stderr
            success = result.returncode == 0 and "error" not in output.lower()
            return {
                "driver_manager": "unixODBC",
                "binary": PATHS["isql"],
                "success": success,
                "output": output.strip(),
            }
        except subprocess.TimeoutExpired:
            errors.append("isql: timeout")
        except Exception as e:
            errors.append(f"isql: {e}")

    return {"success": False, "error": "No ODBC test binary available", "details": errors}


# ---------------------------------------------------------------------------
# HTTP request handler
# ---------------------------------------------------------------------------

class ODBCHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"[{self.address_string()}] {fmt % args}", file=sys.stderr)

    def send_json(self, data, status=200):
        body = json.dumps(data, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        self.send_json({"error": message}, status)

    def read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path).rstrip("/")

        if path == "/info":
            self.send_json(get_info())

        elif path == "/dsns":
            self.send_json(list_dsns())

        elif path.startswith("/dsn/"):
            name = path[len("/dsn/"):]
            data = inspect_dsn(name)
            if data is None:
                self.send_error_json(f"DSN '{name}' not found", 404)
            else:
                self.send_json(data)

        elif path == "/drivers":
            self.send_json(list_drivers())

        elif path.startswith("/driver/"):
            name = path[len("/driver/"):]
            data = inspect_driver(name)
            if data is None:
                self.send_error_json(f"Driver '{name}' not found", 404)
            else:
                self.send_json(data)

        elif path == "/health":
            self.send_json({"status": "ok", "os": PATHS["os"]})

        else:
            self.send_error_json("Unknown endpoint", 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path).rstrip("/")

        if path == "/test":
            body = self.read_body()
            dsn = body.get("dsn", "").strip()
            uid = body.get("uid", "").strip()
            pwd = body.get("pwd", "").strip()
            query = body.get("query", "SELECT 'OK'").strip()

            if not dsn:
                self.send_error_json("'dsn' is required")
                return

            result = test_connection(dsn, uid, pwd, query)
            status = 200 if result.get("success") else 502
            self.send_json(result, status)

        else:
            self.send_error_json("Unknown endpoint", 404)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ODBC REST Server")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8899,
                        help="Port (default: 8899)")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), ODBCHandler)
    print(f"ODBC REST Server listening on http://{args.host}:{args.port}", file=sys.stderr)
    print(f"OS: {PATHS['os']}", file=sys.stderr)
    print(f"System DSN: {PATHS['system_dsn']}", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)


if __name__ == "__main__":
    main()
