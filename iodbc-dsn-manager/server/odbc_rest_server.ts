/**
 * ODBC REST Server — TypeScript edition (Node.js ≥ 18, no npm deps).
 * Wraps iODBC / unixODBC for remote access.
 * Mirrors odbc_rest_server.py — same endpoints, same JSON contract.
 * Binds to 127.0.0.1:8899 by default (use --host 0.0.0.0 to expose on LAN).
 *
 * Usage:
 *   npx tsx odbc_rest_server.ts
 *   npx tsx odbc_rest_server.ts --port 9000 --host 0.0.0.0
 *
 * Endpoints:
 *   GET  /info              Driver manager version and config paths
 *   GET  /dsns              List all DSNs (system + user)
 *   GET  /dsn/<name>        Inspect a DSN section
 *   GET  /drivers           List all installed drivers
 *   GET  /driver/<name>     Inspect a driver section
 *   GET  /health            Liveness check
 *   POST /test              Test DSN connectivity
 *                           Body: {"dsn":"...","uid":"...","pwd":"...","query":"..."}
 */

import http from "node:http";
import os   from "node:os";
import { existsSync, readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { join } from "node:path";

// ── Minimal INI parser (replaces configparser) ────────────────────────────────

type IniConfig = Record<string, Record<string, string>>;

function parseIni(content: string): IniConfig {
  const cfg: IniConfig = {};
  let current: Record<string, string> | null = null;
  for (const rawLine of content.split("\n")) {
    const line = rawLine.trim();
    if (!line || line.startsWith(";") || line.startsWith("#")) continue;
    const secMatch = line.match(/^\[(.+)\]$/);
    if (secMatch) {
      const name = secMatch[1].trim();
      cfg[name] = cfg[name] ?? {};
      current = cfg[name];
      continue;
    }
    if (current) {
      const eq = line.indexOf("=");
      if (eq > 0) {
        current[line.slice(0, eq).trim().toLowerCase()] = line.slice(eq + 1).trim();
      }
    }
  }
  return cfg;
}

function readIni(filePath: string): IniConfig {
  if (!existsSync(filePath)) return {};
  try { return parseIni(readFileSync(filePath, "utf-8")); } catch { return {}; }
}

// ── Platform-aware path resolution ───────────────────────────────────────────

function whichBin(cmd: string): string {
  const r = spawnSync("which", [cmd], { encoding: "utf-8" });
  return r.status === 0 ? r.stdout.trim() : "";
}

interface OdbcPaths {
  system_dsn:    string;
  system_driver: string;
  user_dsn:      string;
  iodbctest:     string;
  iodbctestw:    string;
  isql:          string;
  iusql:         string;
  odbcinst:      string;
  iodbc_config:  string;
  os:            string;
}

function getPaths(): OdbcPaths {
  const home = os.homedir();
  if (process.platform === "darwin") {
    return {
      system_dsn:    "/Library/ODBC/odbc.ini",
      system_driver: "/Library/ODBC/odbcinst.ini",
      user_dsn:      join(home, "Library/ODBC/odbc.ini"),
      iodbctest:     "/usr/local/iODBC/bin/iodbctest",
      iodbctestw:    "/usr/local/iODBC/bin/iodbctestw",
      isql:          whichBin("isql"),
      iusql:         whichBin("iusql"),
      odbcinst:      whichBin("odbcinst"),
      iodbc_config:  "/usr/local/iODBC/bin/iodbc-config",
      os:            "Darwin",
    };
  }
  return {
    system_dsn:    "/etc/odbc.ini",
    system_driver: "/etc/odbcinst.ini",
    user_dsn:      join(home, ".odbc.ini"),
    iodbctest:     whichBin("iodbctest"),
    iodbctestw:    whichBin("iodbctestw"),
    isql:          whichBin("isql"),
    iusql:         whichBin("iusql"),
    odbcinst:      whichBin("odbcinst"),
    iodbc_config:  whichBin("iodbc-config"),
    os:            "Linux",
  };
}

const PATHS = getPaths();

// ── ODBC config helpers ───────────────────────────────────────────────────────

function listDsns(): { system: Record<string, string>; user: Record<string, string> } {
  const result = { system: {} as Record<string, string>, user: {} as Record<string, string> };
  for (const [scope, key] of [["system", "system_dsn"], ["user", "user_dsn"]] as const) {
    const cfg = readIni(PATHS[key]);
    if (cfg["ODBC Data Sources"]) result[scope] = cfg["ODBC Data Sources"];
  }
  return result;
}

function inspectDsn(name: string): Record<string, string> | null {
  for (const key of ["system_dsn", "user_dsn"] as const) {
    const cfg = readIni(PATHS[key]);
    if (cfg[name]) return cfg[name];
  }
  return null;
}

function listDrivers(): { system: Record<string, string> } {
  const cfg = readIni(PATHS.system_driver);
  return { system: cfg["ODBC Drivers"] ?? {} };
}

function inspectDriver(name: string): Record<string, string> | null {
  const cfg = readIni(PATHS.system_driver);
  return cfg[name] ?? null;
}

function getInfo(): Record<string, unknown> {
  const { os: osName, ...pathsRest } = PATHS;
  const info: Record<string, unknown> = {
    os: osName,
    paths: Object.fromEntries(Object.entries(pathsRest).map(([k, v]) => [k, String(v)])),
    available: {
      iodbctest:  existsSync(PATHS.iodbctest),
      iodbctestw: existsSync(PATHS.iodbctestw),
      isql:       Boolean(PATHS.isql),
      iusql:      Boolean(PATHS.iusql),
      odbcinst:   Boolean(PATHS.odbcinst),
    },
  };

  if (PATHS.iodbc_config && existsSync(PATHS.iodbc_config)) {
    const r = spawnSync(PATHS.iodbc_config, ["--version"], { encoding: "utf-8" });
    if (r.status === 0) info.iodbc_version = r.stdout.trim();
  }
  if (PATHS.odbcinst) {
    const r = spawnSync(PATHS.odbcinst, ["-j"], { encoding: "utf-8", stderr: "pipe" });
    if (r.status === 0) info.unixodbc_info = (r.stdout + (r.stderr ?? "")).trim();
  }
  return info;
}

function testConnection(
  dsn: string, uid: string, pwd: string, query = "SELECT 'OK'",
): Record<string, unknown> {
  const connStr  = `DSN=${dsn};UID=${uid};PWD=${pwd}`;
  const sqlInput = `${query};\nquit\n`;
  const errors: string[] = [];

  for (const key of ["iodbctest", "iodbctestw"] as const) {
    const binary = PATHS[key];
    if (!binary || !existsSync(binary)) continue;
    try {
      const r = spawnSync(binary, [connStr], {
        input: sqlInput, encoding: "utf-8", timeout: 15_000,
      });
      const output = (r.stdout ?? "") + (r.stderr ?? "");
      return {
        driver_manager: "iODBC",
        binary,
        success: output.includes("Driver connected!"),
        output:  output.trim(),
      };
    } catch (e) {
      errors.push(`${key}: ${(e as Error).message}`);
    }
    break;
  }

  if (PATHS.isql) {
    try {
      const r = spawnSync(PATHS.isql, [dsn, uid, pwd, "-b"], {
        input: `${query}\n`, encoding: "utf-8", timeout: 15_000,
      });
      const output = (r.stdout ?? "") + (r.stderr ?? "");
      return {
        driver_manager: "unixODBC",
        binary:  PATHS.isql,
        success: (r.status === 0) && !output.toLowerCase().includes("error"),
        output:  output.trim(),
      };
    } catch (e) {
      errors.push(`isql: ${(e as Error).message}`);
    }
  }

  return { success: false, error: "No ODBC test binary available", details: errors };
}

// ── HTTP server ───────────────────────────────────────────────────────────────

function sendJson(res: http.ServerResponse, data: unknown, status = 200): void {
  const body = JSON.stringify(data, null, 2);
  res.writeHead(status, {
    "Content-Type":   "application/json",
    "Content-Length": Buffer.byteLength(body),
  });
  res.end(body);
}

function sendError(res: http.ServerResponse, message: string, status = 400): void {
  sendJson(res, { error: message }, status);
}

function handleGet(pathname: string, res: http.ServerResponse): void {
  if (pathname === "/info") {
    sendJson(res, getInfo());
  } else if (pathname === "/dsns") {
    sendJson(res, listDsns());
  } else if (pathname.startsWith("/dsn/")) {
    const name = pathname.slice("/dsn/".length);
    const data = inspectDsn(name);
    data ? sendJson(res, data) : sendError(res, `DSN '${name}' not found`, 404);
  } else if (pathname === "/drivers") {
    sendJson(res, listDrivers());
  } else if (pathname.startsWith("/driver/")) {
    const name = pathname.slice("/driver/".length);
    const data = inspectDriver(name);
    data ? sendJson(res, data) : sendError(res, `Driver '${name}' not found`, 404);
  } else if (pathname === "/health") {
    sendJson(res, { status: "ok", os: PATHS.os });
  } else {
    sendError(res, "Unknown endpoint", 404);
  }
}

function handlePost(pathname: string, rawBody: string, res: http.ServerResponse): void {
  if (pathname !== "/test") {
    sendError(res, "Unknown endpoint", 404);
    return;
  }
  let body: Record<string, string> = {};
  try { body = JSON.parse(rawBody) as Record<string, string>; } catch { /* empty body ok */ }

  const dsn   = (body["dsn"]   ?? "").trim();
  const uid   = (body["uid"]   ?? "").trim();
  const pwd   = (body["pwd"]   ?? "").trim();
  const query = (body["query"] ?? "SELECT 'OK'").trim();

  if (!dsn) {
    sendError(res, "'dsn' is required");
    return;
  }

  const result = testConnection(dsn, uid, pwd, query);
  sendJson(res, result, result["success"] ? 200 : 502);
}

function createOdbcServer(): http.Server {
  return http.createServer((req, res) => {
    const raw  = req.url ?? "/";
    const pathname = decodeURIComponent(raw.split("?")[0]).replace(/\/+$/, "") || "/";

    process.stderr.write(`[${new Date().toISOString()}] ${req.socket.remoteAddress} ${req.method} ${pathname}\n`);

    if (req.method === "GET") {
      handleGet(pathname, res);
    } else if (req.method === "POST") {
      let body = "";
      req.on("data", chunk => (body += chunk));
      req.on("end", () => handlePost(pathname, body, res));
    } else {
      sendError(res, "Method not allowed", 405);
    }
  });
}

// ── CLI entry point ───────────────────────────────────────────────────────────

function main(): void {
  let host = "127.0.0.1";
  let port = 8899;
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--host" && argv[i + 1]) host = argv[++i];
    else if (argv[i] === "--port" && argv[i + 1]) port = parseInt(argv[++i], 10);
  }

  const server = createOdbcServer();
  server.listen(port, host, () => {
    process.stderr.write(`ODBC REST Server listening on http://${host}:${port}\n`);
    process.stderr.write(`OS: ${PATHS.os}\n`);
    process.stderr.write(`System DSN: ${PATHS.system_dsn}\n`);
  });

  process.on("SIGINT",  () => { process.stderr.write("\nStopped.\n"); server.close(); process.exit(0); });
  process.on("SIGTERM", () => { server.close(); process.exit(0); });
}

if (
  process.argv[1] &&
  (process.argv[1].endsWith("odbc_rest_server.ts") ||
    process.argv[1].endsWith("odbc_rest_server.js"))
) {
  main();
}
