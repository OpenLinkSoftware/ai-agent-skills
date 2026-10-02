#!/usr/bin/env python3
"""Small dependency-free XMLA SOAP 1.1 client."""

from __future__ import annotations

import argparse
import base64
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable
from xml.dom import minidom

SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
XMLA_NS = "urn:schemas-microsoft-com:xml-analysis"
ROWSET_NS = "urn:schemas-microsoft-com:xml-analysis:rowset"

ET.register_namespace("soap", SOAP_NS)
ET.register_namespace("xmla", XMLA_NS)


class ClientError(RuntimeError):
    """Expected request, transport, or XMLA response failure."""


def qname(namespace: str, local: str) -> str:
    return f"{{{namespace}}}{local}"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_assignments(values: Iterable[str], label: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ClientError(f"{label} must use NAME=VALUE: {value!r}")
        name, item_value = value.split("=", 1)
        name = name.strip()
        if not name:
            raise ClientError(f"{label} name cannot be empty")
        parsed[name] = item_value
    return parsed


def add_properties(parent: ET.Element, properties: dict[str, str]) -> None:
    properties_element = ET.SubElement(parent, qname(XMLA_NS, "Properties"))
    property_list = ET.SubElement(properties_element, qname(XMLA_NS, "PropertyList"))
    for name, value in properties.items():
        ET.SubElement(property_list, qname(XMLA_NS, name)).text = value


def envelope_with(operation: ET.Element) -> ET.Element:
    envelope = ET.Element(qname(SOAP_NS, "Envelope"))
    ET.SubElement(envelope, qname(SOAP_NS, "Header"))
    body = ET.SubElement(envelope, qname(SOAP_NS, "Body"))
    body.append(operation)
    return envelope


def build_discover(request_type: str, restrictions: dict[str, str], properties: dict[str, str]) -> bytes:
    operation = ET.Element(qname(XMLA_NS, "Discover"))
    ET.SubElement(operation, qname(XMLA_NS, "RequestType")).text = request_type
    restrictions_element = ET.SubElement(operation, qname(XMLA_NS, "Restrictions"))
    restriction_list = ET.SubElement(restrictions_element, qname(XMLA_NS, "RestrictionList"))
    for name, value in restrictions.items():
        ET.SubElement(restriction_list, qname(XMLA_NS, name)).text = value
    add_properties(operation, properties)
    return ET.tostring(envelope_with(operation), encoding="utf-8", xml_declaration=True)


def build_execute(statement: str, properties: dict[str, str]) -> bytes:
    operation = ET.Element(qname(XMLA_NS, "Execute"))
    command = ET.SubElement(operation, qname(XMLA_NS, "Command"))
    ET.SubElement(command, qname(XMLA_NS, "Statement")).text = statement
    add_properties(operation, properties)
    return ET.tostring(envelope_with(operation), encoding="utf-8", xml_declaration=True)


def pretty_xml(payload: bytes) -> str:
    try:
        return minidom.parseString(payload).toprettyxml(indent="  ")
    except Exception as exc:
        raise ClientError(f"response is not valid XML: {exc}") from exc


def child_value(element: ET.Element) -> Any:
    children = list(element)
    text = (element.text or "").strip()
    attributes = {local_name(name): value for name, value in element.attrib.items()}
    if not children and not attributes:
        return text
    result: dict[str, Any] = {}
    if attributes:
        result["@attributes"] = attributes
    for child in children:
        name = local_name(child.tag)
        value = child_value(child)
        if name in result:
            current = result[name]
            result[name] = current + [value] if isinstance(current, list) else [current, value]
        else:
            result[name] = value
    if text:
        result["_text"] = text
    return result


def find_fault(root: ET.Element) -> dict[str, Any] | None:
    fault = next((item for item in root.iter() if local_name(item.tag) == "Fault"), None)
    if fault is None:
        return None
    return {local_name(child.tag): child_value(child) for child in fault}


def normalize_response(payload: bytes) -> dict[str, Any]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ClientError(f"response is not valid XML: {exc}") from exc
    fault = find_fault(root)
    if fault is not None:
        return {"fault": fault}
    rows = []
    for element in root.iter():
        if element.tag == qname(ROWSET_NS, "row") or local_name(element.tag) == "row":
            rows.append({local_name(child.tag): child_value(child) for child in element})
    if rows:
        return {"row_count": len(rows), "rows": rows}
    body = next((item for item in root.iter() if local_name(item.tag) == "Body"), root)
    return {"row_count": 0, "response": child_value(body)}


def ssl_context(args: argparse.Namespace) -> ssl.SSLContext:
    if args.insecure:
        context = ssl._create_unverified_context()
    else:
        context = ssl.create_default_context(cafile=args.ca_cert)
    if args.client_cert:
        context.load_cert_chain(args.client_cert, args.client_key)
    return context


def auth_header(args: argparse.Namespace) -> str | None:
    bearer = os.environ.get(args.bearer_token_env)
    if bearer:
        return f"Bearer {bearer}"
    username = os.environ.get(args.username_env)
    password = os.environ.get(args.password_env)
    if username is None and password is None:
        return None
    if username is None or password is None:
        raise ClientError(
            f"basic authentication requires both {args.username_env} and {args.password_env}"
        )
    encoded = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
    return f"Basic {encoded}"


def send(args: argparse.Namespace, operation: str, payload: bytes) -> tuple[int, str, str, bytes]:
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "Accept": "text/xml, application/xml",
        "SOAPAction": f'"{XMLA_NS}:{operation}"',
        "User-Agent": "xmla-client-skill/1.0",
    }
    authorization = auth_header(args)
    if authorization:
        headers["Authorization"] = authorization
    request = urllib.request.Request(args.endpoint, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=args.timeout, context=ssl_context(args)) as response:
            return response.status, response.reason, response.headers.get("Content-Type", ""), response.read()
    except urllib.error.HTTPError as exc:
        response_body = exc.read()
        content_type = exc.headers.get("Content-Type", "") if exc.headers else ""
        return exc.code, str(exc.reason), content_type, response_body
    except urllib.error.URLError as exc:
        raise ClientError(f"transport failure: {exc.reason}") from exc


def write_output(text: str, destination: str | None) -> None:
    if destination:
        Path(destination).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
        if text and not text.endswith("\n"):
            sys.stdout.write("\n")


def render(payload: bytes, output_format: str) -> str:
    if output_format == "xml":
        return payload.decode("utf-8", errors="replace")
    if output_format == "pretty-xml":
        return pretty_xml(payload)
    return json.dumps(normalize_response(payload), indent=2, ensure_ascii=False)


def statement_from(args: argparse.Namespace) -> str:
    sources = sum(value is not None for value in (args.statement, args.statement_file)) + int(args.stdin)
    if sources != 1:
        raise ClientError("execute requires exactly one of --statement, --statement-file, or --stdin")
    if args.statement is not None:
        return args.statement
    if args.statement_file is not None:
        return Path(args.statement_file).read_text(encoding="utf-8")
    return sys.stdin.read()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Speak XMLA over SOAP 1.1")
    result.add_argument("--endpoint", required=True, help="XMLA HTTP(S) endpoint")
    result.add_argument("--data-source-info", help="XMLA DataSourceInfo property, e.g. DSN=Local_Instance")
    result.add_argument("--catalog", help="XMLA Catalog property")
    result.add_argument("--timeout", type=float, default=30.0, help="request timeout in seconds")
    result.add_argument("--username-env", default="XMLA_USERNAME")
    result.add_argument("--password-env", default="XMLA_PASSWORD")
    result.add_argument("--bearer-token-env", default="XMLA_BEARER_TOKEN")
    result.add_argument("--xmla-username-env", default="XMLA_PROPERTY_USERNAME")
    result.add_argument("--xmla-password-env", default="XMLA_PROPERTY_PASSWORD")
    result.add_argument("--ca-cert", help="CA bundle for server validation")
    result.add_argument("--client-cert", help="PEM client certificate or combined certificate/key")
    result.add_argument("--client-key", help="PEM client key when separate from --client-cert")
    result.add_argument("--insecure", action="store_true", help="disable TLS validation for approved diagnostics")
    result.add_argument("--dry-run", action="store_true", help="emit request without sending")
    result.add_argument("--show-request", action="store_true", help="pretty-print request to stderr")
    result.add_argument("--response-out", help="write the unmodified response bytes to this file")
    result.add_argument("--output", help="write formatted output to this file instead of stdout")

    subparsers = result.add_subparsers(dest="command", required=True)
    discover = subparsers.add_parser("discover", help="send an XMLA Discover request")
    discover.add_argument("--request-type", required=True)
    discover.add_argument("--restriction", action="append", default=[], metavar="NAME=VALUE")
    discover.add_argument("--property", action="append", default=[], metavar="NAME=VALUE")
    discover.add_argument("--output-format", choices=("json", "xml", "pretty-xml"), default="json")

    execute = subparsers.add_parser("execute", help="send an XMLA Execute request")
    statement_group = execute.add_mutually_exclusive_group()
    statement_group.add_argument("--statement")
    statement_group.add_argument("--statement-file")
    statement_group.add_argument("--stdin", action="store_true")
    execute.add_argument("--property", action="append", default=[], metavar="NAME=VALUE")
    execute.add_argument("--output-format", choices=("json", "xml", "pretty-xml"), default="json")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        properties = parse_assignments(args.property, "property")
        if args.data_source_info is not None:
            properties["DataSourceInfo"] = args.data_source_info
        if args.catalog is not None:
            properties["Catalog"] = args.catalog
        xmla_username = os.environ.get(args.xmla_username_env)
        xmla_password = os.environ.get(args.xmla_password_env)
        if (xmla_username is None) != (xmla_password is None):
            raise ClientError(
                f"XMLA property authentication requires both {args.xmla_username_env} "
                f"and {args.xmla_password_env}"
            )
        if xmla_username is not None:
            properties.setdefault("UserName", xmla_username)
            properties.setdefault("Password", xmla_password or "")
        properties.setdefault("Content", "SchemaData")

        if args.command == "discover":
            restrictions = parse_assignments(args.restriction, "restriction")
            payload = build_discover(args.request_type, restrictions, properties)
            operation = "Discover"
        else:
            payload = build_execute(statement_from(args), properties)
            operation = "Execute"

        if args.show_request:
            sys.stderr.write(pretty_xml(payload))
        if args.dry_run:
            write_output(render(payload, args.output_format), args.output)
            return 0

        status, reason, content_type, response = send(args, operation, payload)
        if args.response_out:
            Path(args.response_out).write_bytes(response)
        try:
            normalized = normalize_response(response)
        except ClientError:
            if status >= 400:
                raise ClientError(f"HTTP {status} {reason}; response is not XML")
            raise
        if "fault" in normalized:
            raise ClientError(
                f"HTTP {status} {reason}; SOAP Fault: "
                f"{json.dumps(normalized['fault'], ensure_ascii=False)}"
            )
        if status >= 400:
            raise ClientError(f"HTTP {status} {reason}")
        if args.show_request:
            sys.stderr.write(f"HTTP {status}; Content-Type: {content_type}\n")
        write_output(render(response, args.output_format), args.output)
        return 0
    except (ClientError, OSError) as exc:
        sys.stderr.write(f"xmla-client: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
