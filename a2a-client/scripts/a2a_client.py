#!/usr/bin/env python3
"""Small OPAL A2A JSON-RPC client with no hardcoded deployment hostnames."""

from __future__ import annotations

import argparse
import http.server
import json
import os
import sys
import threading
import uuid
import webbrowser
from dataclasses import dataclass
from typing import Any
from urllib import error, parse, request


DEFAULT_A2A_PATH = "/chat/api/a2a"
AGENT_CARD_PATH = "/.well-known/agent.json"


@dataclass
class Target:
    agent_base: str | None
    agent_url: str | None
    card_url: str | None


def die(message: str, code: int = 2) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


def normalize_base(url: str) -> str:
    return url.rstrip("/")


def same_origin(url: str) -> str:
    parts = parse.urlsplit(url)
    if not parts.scheme or not parts.netloc:
        die(f"expected absolute URL, got {url!r}")
    return parse.urlunsplit((parts.scheme, parts.netloc, "", "", ""))


def resolve_card_url(target: Target) -> str:
    if target.card_url:
        return target.card_url
    if target.agent_base:
        return normalize_base(target.agent_base) + AGENT_CARD_PATH
    if target.agent_url:
        return same_origin(target.agent_url) + AGENT_CARD_PATH
    die("provide --agent-base, --agent-url, or --card-url")


def resolve_agent_url(target: Target, card: dict[str, Any] | None = None) -> str:
    if target.agent_url:
        return target.agent_url
    if card and isinstance(card.get("url"), str):
        return card["url"]
    if target.agent_base:
        return normalize_base(target.agent_base) + DEFAULT_A2A_PATH
    die("provide --agent-url or --agent-base")


def http_json(
    url: str,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=60) as resp:
            payload = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        die(f"HTTP {exc.code} from {url}: {detail}")
    except error.URLError as exc:
        die(f"request failed for {url}: {exc.reason}")
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        die(f"response from {url} was not JSON: {payload[:500]}")


def http_sse(url: str, body: dict[str, Any], token: str | None = None) -> None:
    headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=300) as resp:
            for raw in resp:
                line = raw.decode("utf-8", "replace").rstrip("\n")
                if line.startswith("data:"):
                    print(line[5:].strip())
                elif line:
                    print(line)
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        die(f"HTTP {exc.code} from {url}: {detail}")
    except error.URLError as exc:
        die(f"stream request failed for {url}: {exc.reason}")


def token_from_args(args: argparse.Namespace, target: Target, card: dict[str, Any] | None = None) -> str | None:
    if args.token:
        return args.token
    token_env = args.token_env or os.environ.get("OPAL_A2A_TOKEN_ENV")
    if token_env:
        token = os.environ.get(token_env)
        if not token:
            die(f"environment variable {token_env} is not set")
        return token
    token = os.environ.get("OPAL_A2A_TOKEN")
    if token:
        return token
    if getattr(args, "oauth_auth_code", False):
        token = fetch_auth_code_token(args, target, card)
        maybe_save_token(args, token)
        return token
    if getattr(args, "oauth_client_credentials", False):
        client_id = os.environ.get(args.client_id_env)
        client_secret = os.environ.get(args.client_secret_env)
        if not client_id or not client_secret:
            die(f"set {args.client_id_env} and {args.client_secret_env}")
        token_url = args.token_url or token_url_from_card(card)
        if not token_url:
            die("no token URL supplied and none found in Agent Card")
        return fetch_client_credentials_token(token_url, client_id, client_secret, args.scope)
    return None


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def maybe_save_token(args: argparse.Namespace, token: str) -> None:
    env_name = args.save_token_env
    if not env_name:
        return
    if not env_name.replace("_", "").isalnum() or env_name[0].isdigit():
        die(f"invalid environment variable name: {env_name}")
    line = f"export {env_name}={shell_quote(token)}\n"
    if args.save_token_env_file:
        with open(args.save_token_env_file, "w", encoding="utf-8") as fh:
            fh.write(line)
        try:
            os.chmod(args.save_token_env_file, 0o600)
        except OSError:
            pass
        print(f"Wrote bearer token export to {args.save_token_env_file}", file=sys.stderr)
        return
    print(line, file=sys.stderr)


def oidc_discovery_url(target: Target, card: dict[str, Any] | None, issuer: str | None) -> str:
    if issuer:
        return normalize_base(issuer) + "/.well-known/openid-configuration"
    if target.agent_base:
        return normalize_base(target.agent_base) + "/.well-known/openid-configuration"
    if target.agent_url:
        return same_origin(target.agent_url) + "/.well-known/openid-configuration"
    if card and isinstance(card.get("url"), str):
        return same_origin(card["url"]) + "/.well-known/openid-configuration"
    die("provide --oauth-issuer, --agent-base, or --agent-url for OAuth discovery")


def registration_url_from_discovery(discovery: dict[str, Any]) -> str | None:
    value = discovery.get("registration_endpoint")
    return value if isinstance(value, str) else None


def authorization_url_from_discovery(discovery: dict[str, Any]) -> str | None:
    value = discovery.get("authorization_endpoint")
    return value if isinstance(value, str) else None


def token_url_from_discovery(discovery: dict[str, Any]) -> str | None:
    value = discovery.get("token_endpoint")
    return value if isinstance(value, str) else None


def token_url_from_card(card: dict[str, Any] | None) -> str | None:
    if not card:
        return None
    auth = card.get("authentication") or {}
    creds = auth.get("credentials")
    if isinstance(creds, str):
        try:
            creds = json.loads(creds)
        except json.JSONDecodeError:
            return None
    if isinstance(creds, dict) and isinstance(creds.get("tokenUrl"), str):
        return creds["tokenUrl"]
    return None


def post_form_json(url: str, form: dict[str, str]) -> dict[str, Any]:
    data = parse.urlencode(form).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        die(f"OAuth request failed with HTTP {exc.code}: {detail}")
    except error.URLError as exc:
        die(f"OAuth request failed: {exc.reason}")


def dynamic_register_client(
    registration_url: str,
    client_name: str,
    redirect_uri: str,
    scope: str | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "client_name": client_name,
        "redirect_uris": [redirect_uri],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
    }
    if scope:
        body["scope"] = scope
    return http_json(registration_url, method="POST", body=body)


def wait_for_auth_code(redirect_uri: str, timeout: int) -> str:
    parsed = parse.urlsplit(redirect_uri)
    if parsed.hostname not in {"localhost", "127.0.0.1"}:
        die("redirect URI must use localhost or 127.0.0.1")
    port = parsed.port
    if port is None:
        die("redirect URI must include an explicit port")
    callback_path = parsed.path or "/"
    result: dict[str, str] = {}

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:
            return

        def do_GET(self) -> None:
            url = parse.urlsplit(self.path)
            params = parse.parse_qs(url.query)
            if url.path != callback_path:
                self.send_response(404)
                self.end_headers()
                return
            if "code" in params:
                result["code"] = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<html><body>OAuth complete. You can return to the terminal.</body></html>")
            elif "error" in params:
                result["error"] = params["error"][0]
                self.send_response(400)
                self.end_headers()
            else:
                self.send_response(400)
                self.end_headers()

    server = http.server.HTTPServer(("127.0.0.1", port), CallbackHandler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    thread.join(timeout)
    server.server_close()
    if "error" in result:
        die(f"OAuth authorization failed: {result['error']}")
    if "code" not in result:
        die(f"timed out waiting {timeout}s for OAuth callback")
    return result["code"]


def fetch_auth_code_token(args: argparse.Namespace, target: Target, card: dict[str, Any] | None) -> str:
    discovery = http_json(oidc_discovery_url(target, card, args.oauth_issuer))
    registration_url = args.registration_url or registration_url_from_discovery(discovery)
    authorization_url = args.authorization_url or authorization_url_from_discovery(discovery)
    token_url = args.token_url or token_url_from_discovery(discovery) or token_url_from_card(card)
    if not registration_url:
        die("no registration endpoint supplied or found in OIDC discovery")
    if not authorization_url:
        die("no authorization endpoint supplied or found in OIDC discovery")
    if not token_url:
        die("no token endpoint supplied or found in OIDC discovery/Agent Card")
    scope = args.scope or "openid webid"
    client = dynamic_register_client(registration_url, args.client_name, args.redirect_uri, scope)
    client_id = client.get("client_id")
    client_secret = client.get("client_secret")
    if not isinstance(client_id, str):
        die("dynamic registration response did not include client_id")
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": args.redirect_uri,
        "scope": scope,
    }
    auth_url = authorization_url + "?" + parse.urlencode(params)
    print(f"Open this authorization URL:\n{auth_url}", file=sys.stderr)
    if args.open_browser:
        webbrowser.open(auth_url)
    code = wait_for_auth_code(args.redirect_uri, args.oauth_timeout)
    form = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": args.redirect_uri,
        "client_id": client_id,
    }
    if isinstance(client_secret, str):
        form["client_secret"] = client_secret
    payload = post_form_json(token_url, form)
    token = payload.get("access_token")
    if not isinstance(token, str):
        die("OAuth token response did not include access_token")
    return token


def fetch_client_credentials_token(
    token_url: str,
    client_id: str,
    client_secret: str,
    scope: str | None,
) -> str:
    form = {"grant_type": "client_credentials"}
    if scope:
        form["scope"] = scope
    data = parse.urlencode(form).encode("utf-8")
    password_mgr = request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, token_url, client_id, client_secret)
    opener = request.build_opener(request.HTTPBasicAuthHandler(password_mgr))
    req = request.Request(
        token_url,
        data=data,
        headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with opener.open(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        die(f"OAuth token request failed with HTTP {exc.code}: {detail}")
    except error.URLError as exc:
        die(f"OAuth token request failed: {exc.reason}")
    token = payload.get("access_token")
    if not isinstance(token, str):
        die("OAuth token response did not include access_token")
    return token


def rpc(method: str, params: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": uuid.uuid4().hex, "method": method, "params": params}


def message_params(args: argparse.Namespace) -> dict[str, Any]:
    parts: list[dict[str, Any]] = [{"type": "text", "text": args.message}]
    for path in args.file or []:
        with open(path, "rb") as fh:
            content = fh.read()
        parts.append(
            {
                "type": "file",
                "file": {
                    "name": os.path.basename(path),
                    "bytesBase64": __import__("base64").b64encode(content).decode("ascii"),
                },
            }
        )
    params: dict[str, Any] = {"message": {"role": "user", "parts": parts}}
    if args.context_id:
        params["contextId"] = args.context_id
    if args.session_id:
        params["sessionId"] = args.session_id
    return params


def extract_text(value: Any) -> list[str]:
    texts: list[str] = []
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            texts.append(value["text"])
        for child in value.values():
            texts.extend(extract_text(child))
    elif isinstance(value, list):
        for item in value:
            texts.extend(extract_text(item))
    return texts


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def add_target_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--agent-base", help="Base URL, for example https://{CNAME}. Must be supplied or elicited.")
    parser.add_argument("--agent-url", help="Full A2A endpoint URL, for example https://{CNAME}/chat/api/a2a.")
    parser.add_argument("--card-url", help="Explicit Agent Card URL. Defaults to same origin /.well-known/agent.json.")


def add_auth_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--token", help="Bearer/API token. Prefer --token-env to avoid shell history exposure.")
    parser.add_argument("--token-env", help="Environment variable containing bearer/API token.")
    parser.add_argument("--oauth-auth-code", action="store_true", help="Dynamically register a client and obtain a bearer token with OAuth2 Authorization Code.")
    parser.add_argument("--oauth-issuer", help="OAuth issuer/base URL for OIDC discovery. Defaults to the selected A2A target origin.")
    parser.add_argument("--registration-url", help="Explicit OAuth dynamic client registration URL.")
    parser.add_argument("--authorization-url", help="Explicit OAuth authorization URL.")
    parser.add_argument("--redirect-uri", default="http://localhost:12345/callback", help="Local OAuth redirect URI.")
    parser.add_argument("--client-name", default="OPAL A2A Client", help="Dynamic OAuth client name.")
    parser.add_argument("--open-browser", action="store_true", help="Open the authorization URL in the default browser.")
    parser.add_argument("--oauth-timeout", type=int, default=300, help="Seconds to wait for the OAuth callback.")
    parser.add_argument("--save-token-env", help="After OAuth Authorization Code flow, emit or save an export for this environment variable name.")
    parser.add_argument("--save-token-env-file", help="Write the --save-token-env export line to this file with mode 0600 instead of printing it.")
    parser.add_argument("--oauth-client-credentials", action="store_true", help="Obtain bearer token with OAuth2 client credentials.")
    parser.add_argument("--client-id-env", default="OAUTH_CLIENT_ID", help="Environment variable for OAuth client id.")
    parser.add_argument("--client-secret-env", default="OAUTH_CLIENT_SECRET", help="Environment variable for OAuth client secret.")
    parser.add_argument("--token-url", help="OAuth2 token URL. If omitted, try Agent Card authentication.credentials.tokenUrl.")
    parser.add_argument("--scope", help="Optional OAuth2 scope string.")


def env_base_url() -> str | None:
    base_url = os.environ.get("OPAL_A2A_BASE_URL")
    if base_url:
        return base_url
    cname = os.environ.get("OPAL_A2A_CNAME")
    if not cname:
        return None
    if cname.startswith("http://") or cname.startswith("https://"):
        return cname
    return f"https://{cname}"


def target_from_args(args: argparse.Namespace) -> Target:
    return Target(
        agent_base=args.agent_base or env_base_url(),
        agent_url=args.agent_url or os.environ.get("OPAL_A2A_URL"),
        card_url=args.card_url or os.environ.get("OPAL_A2A_CARD_URL"),
    )


def command_card(args: argparse.Namespace) -> None:
    card = http_json(resolve_card_url(target_from_args(args)))
    print_json(card)


def command_send(args: argparse.Namespace, subscribe: bool = False) -> None:
    target = target_from_args(args)
    card = http_json(resolve_card_url(target))
    agent_url = resolve_agent_url(target, card)
    token = token_from_args(args, target, card)
    method = "tasks/sendSubscribe" if subscribe else "tasks/send"
    payload = rpc(method, message_params(args))
    if subscribe:
        http_sse(agent_url, payload, token)
        return
    result = http_json(agent_url, method="POST", body=payload, token=token)
    if args.text_only:
        for text in extract_text(result):
            print(text)
    else:
        print_json(result)


def command_get(args: argparse.Namespace) -> None:
    target = target_from_args(args)
    card = http_json(resolve_card_url(target))
    agent_url = resolve_agent_url(target, card)
    token = token_from_args(args, target, card)
    result = http_json(agent_url, method="POST", body=rpc("tasks/get", {"id": args.task_id}), token=token)
    print_json(result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OPAL A2A JSON-RPC client")
    sub = parser.add_subparsers(dest="command", required=True)

    card = sub.add_parser("card", help="Fetch Agent Card")
    add_target_args(card)
    card.set_defaults(func=command_card)

    send = sub.add_parser("send", help="Send a tasks/send request")
    add_target_args(send)
    add_auth_args(send)
    send.add_argument("--message", required=True)
    send.add_argument("--file", action="append", help="File to attach; repeat for multiple files.")
    send.add_argument("--context-id")
    send.add_argument("--session-id")
    send.add_argument("--text-only", action="store_true")
    send.set_defaults(func=command_send)

    subscribe = sub.add_parser("subscribe", help="Send a tasks/sendSubscribe request and print stream events")
    add_target_args(subscribe)
    add_auth_args(subscribe)
    subscribe.add_argument("--message", required=True)
    subscribe.add_argument("--file", action="append")
    subscribe.add_argument("--context-id")
    subscribe.add_argument("--session-id")
    subscribe.add_argument("--text-only", action="store_true")
    subscribe.set_defaults(func=lambda args: command_send(args, subscribe=True))

    get = sub.add_parser("get", help="Fetch task status with tasks/get")
    add_target_args(get)
    add_auth_args(get)
    get.add_argument("--task-id", required=True)
    get.set_defaults(func=command_get)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
