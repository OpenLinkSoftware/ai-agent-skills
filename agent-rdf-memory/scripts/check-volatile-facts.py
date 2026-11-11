#!/usr/bin/env python3
"""
check-volatile-facts.py - check the facts in core.ttl that go stale, without a model.

core.ttl records where credentials live and which paths and endpoints exist. Those facts
change, and a stale one has caused failed logins before. For each schema:value in core.ttl
this checks that the thing it names is still there:

  Keychain item   `security find-generic-password -s <service> [-a <account>] ...`
                  Existence only: the command is run WITHOUT -w or -g, so the secret is never
                  read, never printed and never leaves the Keychain.
  File or folder  an absolute path, with {CREDENTIALS_ROOT} expanded from core.ttl itself.
  Endpoint        an http(s) URL; any HTTP answer (including 401) counts as reachable.

It also probes the endpoints the loader uses by default.

Usage:
  python3 check-volatile-facts.py            table of results
  python3 check-volatile-facts.py --strict   exit 1 when any fact is missing or unreachable
  python3 check-volatile-facts.py --json
  python3 check-volatile-facts.py --skip-network
"""
import argparse
import json
import os
import pathlib
import re
import shlex
import ssl
import subprocess
import sys
import urllib.error
import urllib.request

STORE = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_ENDPOINTS = ["https://localhost/sparql-auth", "http://localhost:8890/sparql-auth"]
VALUE = re.compile(r'schema:value\s+"((?:[^"\\]|\\.)*)"')
NAME = re.compile(r'^(:[A-Za-z0-9_]+)\s+a\s+schema:PropertyValue', re.M)


def core_facts():
    text = (STORE / "core.ttl").read_text(encoding="utf-8")
    root = None
    m = re.search(r':credentialsRoot\b.*?schema:value\s+"([^"]+)"', text, re.S)
    if m:
        root = m.group(1)
    facts = []
    for block in re.split(r"\n(?=:[A-Za-z0-9_]+\s+a\s+)", text):
        head = re.match(r":([A-Za-z0-9_]+)\s+a\s+", block)
        v = VALUE.search(block)
        if head and v:
            facts.append((head.group(1), v.group(1).replace('\\"', '"')))
    return facts, root


def check_keychain(command):
    try:
        parts = shlex.split(command)
    except ValueError:
        return "UNPARSEABLE", "could not parse the recorded command"
    svc = acct = None
    for i, tok in enumerate(parts):
        if tok == "-s" and i + 1 < len(parts):
            svc = parts[i + 1]
        if tok == "-a" and i + 1 < len(parts):
            acct = parts[i + 1].replace("$USER", os.environ.get("USER", ""))
    if not svc:
        return "UNPARSEABLE", "no -s service in the recorded command"
    cmd = ["security", "find-generic-password", "-s", svc] + (["-a", acct] if acct else [])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except Exception as exc:
        return "UNCHECKED", f"could not run security: {exc}"
    if r.returncode == 0:
        return "OK", f"item {svc} exists"
    if "could not be found" in (r.stderr or ""):
        return "MISSING", f"no Keychain item {svc}" + (f" for account {acct}" if acct else "")
    return "UNCHECKED", (r.stderr or "").strip().splitlines()[0][:100] if r.stderr else f"exit {r.returncode}"


def check_path(value, root):
    p = value.replace("{CREDENTIALS_ROOT}", root or "{CREDENTIALS_ROOT}")
    if "{" in p:
        return "UNCHECKED", "unexpanded placeholder in " + p
    return ("OK", p) if os.path.exists(p) else ("MISSING", p)


def check_endpoint(url, timeout=4):
    ctx = ssl.create_default_context()
    if "localhost" in url or "127.0.0.1" in url:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    try:
        urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=timeout, context=ctx)
        return "OK", f"{url} answered"
    except urllib.error.HTTPError as exc:
        return "OK", f"{url} answered HTTP {exc.code}"
    except Exception as exc:
        return "UNREACHABLE", f"{url}: {str(exc)[:80]}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--skip-network", action="store_true")
    a = ap.parse_args()
    facts, root = core_facts()
    rows = []
    for name, value in facts:
        if value.startswith("security find-generic-password"):
            status, detail = check_keychain(value)
            kind = "keychain item"
        elif value.startswith("/") or value.startswith("{CREDENTIALS_ROOT}"):
            status, detail = check_path(value, root)
            kind = "path"
        elif value.startswith(("http://", "https://")):
            kind = "endpoint"
            status, detail = ("SKIPPED", value) if a.skip_network else check_endpoint(value)
        else:
            continue
        rows.append({"fact": name, "kind": kind, "status": status, "detail": detail})
    if not a.skip_network:
        for url in DEFAULT_ENDPOINTS:
            status, detail = check_endpoint(url)
            rows.append({"fact": "loader default endpoint", "kind": "endpoint", "status": status, "detail": detail})
    if a.json:
        print(json.dumps(rows, indent=2))
    else:
        print(f"core.ttl facts checked: {len(rows)}")
        for r in rows:
            print(f"  {r['status']:<11} {r['kind']:<13} {r['fact']:<34} {r['detail'][:90]}")
        bad = [r for r in rows if r["status"] in ("MISSING", "UNREACHABLE")]
        print(f"\n{len(bad)} missing or unreachable, "
              f"{sum(1 for r in rows if r['status'] in ('UNCHECKED', 'UNPARSEABLE'))} could not be checked.")
    if a.strict and any(r["status"] in ("MISSING", "UNREACHABLE") for r in rows):
        sys.exit(1)


if __name__ == "__main__":
    main()
