#!/usr/bin/env python3
import argparse, json, os, re, subprocess, sys
from urllib.parse import parse_qs, unquote, urlparse, urljoin

import requests
from requests.auth import HTTPDigestAuth
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF

SCHEMA = "https://schema.org/"
SCHEMA_BASES = (SCHEMA, "http://schema.org/")
S = lambda term: URIRef(SCHEMA + term)
schema_terms = lambda term: tuple(URIRef(base + term) for base in SCHEMA_BASES)

OPLLIC_URI_PARAMETER = URIRef("http://www.openlinksw.com/ontology/licenses#uriParameter")
OPLOFR_OFFER_NUMBER = URIRef("http://www.openlinksw.com/ontology/offers#offerNumber")
DEFAULT_RESOURCE_PREDICATES = (
    *schema_terms("url"), *schema_terms("contentUrl"), *schema_terms("identifier"),
    OPLLIC_URI_PARAMETER,
)
DEFAULT_ITEM_ID_PREDICATES = (OPLOFR_OFFER_NUMBER,)


def _parse_rdf_response(response, url):
    ctype = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    fmts = {"text/turtle": "turtle", "application/ld+json": "json-ld",
            "application/rdf+xml": "xml", "application/n-triples": "nt"}
    fmt = fmts.get(ctype)
    if fmt:
        g = Graph(); g.parse(data=response.text, format=fmt, publicID=url); return g
    last = None
    for candidate in ("turtle", "json-ld", "xml", "nt"):
        try:
            g = Graph(); g.parse(data=response.text, format=candidate, publicID=url); return g
        except Exception as e: last = e
    raise RuntimeError(f"Unable to parse RDF from {url}: {last}")


def _header_values(response, name):
    raw_headers = getattr(getattr(response, "raw", None), "headers", None)
    if raw_headers is not None and hasattr(raw_headers, "getlist"):
        values = raw_headers.getlist(name)
        if values:
            return values
    value = response.headers.get(name)
    return [value] if value else []


def _link_records(response, base_url):
    records = []
    for header in _header_values(response, "Link"):
        for match in re.finditer(r"<([^>]+)>\s*;\s*([^,]+)", header):
            target, params = match.groups()
            rel = re.search(r"(?:^|;)\s*rel=\"?([^;\",]+)", ";" + params, re.I)
            typ = re.search(r"(?:^|;)\s*type=\"?([^;\",]+)", ";" + params, re.I)
            rels = tuple((rel.group(1).lower().split() if rel else []))
            records.append({"url": urljoin(base_url, target), "rels": rels,
                            "type": typ.group(1) if typ else None})
    return records


def _rdf_links(response, base_url):
    links = []
    for record in _link_records(response, base_url):
        rels = set(record["rels"])
        typ = record["type"]
        if rels.intersection({"describedby", "alternate", "offer", "payment"}) and (not typ or "rdf" in typ.lower() or "turtle" in typ.lower() or "json" in typ.lower()):
            links.append(record["url"])
    return links


def _authentication_challenges(response):
    challenges = []
    scheme_start = re.compile(r"(?:^|,\s*)([A-Za-z][A-Za-z0-9._~-]*)\s+")
    for header in _header_values(response, "WWW-Authenticate"):
        matches = list(scheme_start.finditer(header))
        if not matches:
            continue
        for index, match in enumerate(matches):
            start = match.start(1)
            end = matches[index + 1].start() if index + 1 < len(matches) else len(header)
            raw = header[start:end].strip().rstrip(",")
            challenges.append({"scheme": match.group(1), "raw": raw})
    return challenges


def _auth_params(raw_challenge):
    body = raw_challenge.split(None, 1)[1] if " " in raw_challenge else ""
    params = {}
    pattern = re.compile(r'([A-Za-z][A-Za-z0-9_-]*)=(?:"((?:\\.|[^"\\])*)"|([^,\s]+))')
    for match in pattern.finditer(body):
        params[match.group(1).lower()] = (match.group(2) if match.group(2) is not None else match.group(3))
    return params


def resource_access_metadata(response, resource_url, identity_established=False):
    challenges = _authentication_challenges(response)
    payment_challenges = [dict(_auth_params(c["raw"]), raw=c["raw"])
                          for c in challenges if c["scheme"].lower() == "payment"]
    links = _link_records(response, resource_url)
    status = response.status_code
    errors = []
    if 200 <= status < 300:
        state = "access_granted"
    elif status == 401:
        state = "authentication_failed" if identity_established else "authentication_required"
    elif status == 402:
        if not identity_established:
            state = "protocol_error"
            errors.append("payment challenge was issued before authenticated identity was established")
        elif not payment_challenges:
            state = "protocol_error"
            errors.append("402 response lacks WWW-Authenticate: Payment challenge metadata")
        else:
            state = "payment_required"
    elif status == 403:
        state = "access_denied"
    elif 300 <= status < 400:
        state = "redirect"
    else:
        state = "unexpected_response"
    return {
        "status": status,
        "state": state,
        "identity_established": bool(identity_established),
        "authentication_schemes": [c["scheme"] for c in challenges],
        "payment_challenges": payment_challenges,
        "links": links,
        "payment_receipt": response.headers.get("Payment-Receipt"),
        "location": response.headers.get("Location"),
        "content_type": response.headers.get("Content-Type"),
        "protocol_errors": errors,
    }


def probe_resource(session, resource_url, identity_established=False):
    response = session.get(resource_url, stream=True, allow_redirects=False, timeout=30)
    try:
        return resource_access_metadata(response, resource_url, identity_established)
    finally:
        response.close()


def configure_identity(session, args):
    established = bool(args.identity_established)
    bearer_token = os.environ.get(args.bearer_token_env) if args.bearer_token_env else None
    if args.bearer_token_env and bearer_token is None:
        raise ValueError("OAuth access-token environment variable is missing")
    dpop_proof = os.environ.get(args.dpop_proof_env) if args.dpop_proof_env else None
    if bearer_token and (args.digest_user_env or args.digest_password_env):
        raise ValueError("Bearer/DPoP and Digest cannot share the Authorization header; choose one identity scheme")
    if bearer_token:
        token_type = (args.oauth_token_type or "Bearer").strip()
        if token_type.lower() not in ("bearer", "dpop"):
            raise ValueError("--oauth-token-type must be Bearer or DPoP")
        session.headers["Authorization"] = f"{token_type} {bearer_token}"
        if token_type.lower() == "dpop":
            if not dpop_proof:
                raise ValueError("--dpop-proof-env is required when --oauth-token-type DPoP")
            session.headers["DPoP"] = dpop_proof
        established = True
    elif dpop_proof:
        raise ValueError("--dpop-proof-env requires an OAuth access token")
    for mapping in args.identity_header_env:
        if "=" not in mapping:
            raise ValueError("--identity-header-env requires HEADER=ENV_VAR")
        header, env_name = mapping.split("=", 1)
        value = os.environ.get(env_name)
        if not header.strip() or value is None:
            raise ValueError(f"Missing identity header name or environment variable: {env_name}")
        session.headers[header.strip()] = value
        established = True
    if args.digest_user_env or args.digest_password_env:
        if not (args.digest_user_env and args.digest_password_env):
            raise ValueError("both --digest-user-env and --digest-password-env are required")
        username = os.environ.get(args.digest_user_env)
        password = os.environ.get(args.digest_password_env)
        if username is None or password is None:
            raise ValueError("Digest credential environment variable is missing")
        session.auth = HTTPDigestAuth(username, password)
        established = True
    if args.client_cert:
        session.cert = (args.client_cert, args.client_key) if args.client_key else args.client_cert
        established = True
    if args.accept_payment:
        session.headers["Accept-Payment"] = args.accept_payment
    return established


def fetch_rdf(url, session):
    headers = {"Accept": "text/turtle, application/ld+json, application/rdf+xml, application/n-triples;q=0.9, */*;q=0.1"}
    r = session.get(url, headers=headers, timeout=30)
    # Protected resources may expose RDF metadata on any authentication/payment
    # error, not only 402. Inspect RDF bodies and typed Link relations first.
    if r.status_code >= 400:
        ctype = r.headers.get("content-type", "").lower()
        rdf_body = any(token in ctype for token in ("turtle", "ld+json", "rdf+xml", "n-triples"))
        try:
            graph = _parse_rdf_response(r, url) if rdf_body else None
            if graph:
                return graph
        except Exception:
            pass
        for linked in _rdf_links(r, url):
            try:
                return fetch_rdf(linked, session)
            except Exception:
                continue
        r.raise_for_status()
    r.raise_for_status()
    return _parse_rdf_response(r, url)


def first_obj(g, subj, pred):
    return next(iter(g.objects(subj, pred)), None)


def first_obj_any(g, subj, predicates):
    if subj is None:
        return None, None
    for pred in predicates:
        value = first_obj(g, subj, pred)
        if value is not None:
            return value, pred
    return None, None


def _offer_subjects(g):
    offers = set()
    for offer_type in schema_terms("Offer"):
        offers.update(g.subjects(RDF.type, offer_type))
    return offers


def _item_offered(g, offer):
    return first_obj_any(g, offer, schema_terms("itemOffered"))[0]


def _offer_value(g, offer, term):
    value, pred = first_obj_any(g, offer, schema_terms(term))
    if value is not None:
        return value, pred, None
    specification, _ = first_obj_any(g, offer, schema_terms("priceSpecification"))
    value, pred = first_obj_any(g, specification, schema_terms(term))
    return value, pred, specification


def find_offer(g, resource_url, resource_predicates=None):
    resource = URIRef(resource_url)
    resource_predicates = tuple(resource_predicates or DEFAULT_RESOURCE_PREDICATES)
    candidates = []
    for offer in _offer_subjects(g):
        score = 0
        item = _item_offered(g, offer)
        if item == resource:
            score = max(score, 120)
        for pred in resource_predicates:
            if (offer, pred, resource) in g:
                score = max(score, 100)
            if item is not None and (item, pred, resource) in g:
                score = max(score, 110)
        if score:
            if _offer_value(g, offer, "price")[0] is not None: score += 5
            if _offer_value(g, offer, "priceCurrency")[0] is not None: score += 5
            candidates.append((score, str(offer), offer))
    if not candidates:
        raise RuntimeError("No schema:Offer in RDF matches the supplied resource URL")
    candidates.sort(reverse=True)
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        raise RuntimeError("Multiple equally ranked schema:Offer resources match; explicit selection required")
    return candidates[0][2]


def _values(iris):
    return " ".join(f"<{iri}>" for iri in iris)


def sparql_offer_graph(session, endpoint, resource_url, resource_predicates=None):
    """Query direct and item-mediated resource relations across Schema.org namespaces."""
    if urlparse(resource_url).scheme not in ("http", "https"):
        raise ValueError("resource URL must be an HTTP(S) IRI")
    resource_predicates = tuple(resource_predicates or DEFAULT_RESOURCE_PREDICATES)
    query = f"""SELECT ?offer ?item ?matchedNode ?matchPredicate ?priceSpec ?currencySpec
       ?offerSku ?offerProductID ?offerIdentifier ?offerNumber
       ?itemSku ?itemProductID ?itemIdentifier ?price ?currency ?availability ?seller
WHERE {{
  VALUES ?offerType {{ {_values(schema_terms("Offer"))} }}
  VALUES ?itemOfferedPred {{ {_values(schema_terms("itemOffered"))} }}
  ?offer a ?offerType .
  OPTIONAL {{ ?offer ?itemOfferedPred ?item }}
  {{ FILTER(?item = <{resource_url}>) BIND(?item AS ?matchedNode) BIND(?itemOfferedPred AS ?matchPredicate) }}
  UNION
  {{ VALUES ?resourcePred {{ {_values(resource_predicates)} }}
     ?offer ?resourcePred <{resource_url}> .
     BIND(?offer AS ?matchedNode) BIND(?resourcePred AS ?matchPredicate) }}
  UNION
  {{ VALUES ?resourcePred {{ {_values(resource_predicates)} }}
     ?item ?resourcePred <{resource_url}> .
     BIND(?item AS ?matchedNode) BIND(?resourcePred AS ?matchPredicate) }}
  OPTIONAL {{ VALUES ?offerSkuPred {{ {_values(schema_terms("sku"))} }} ?offer ?offerSkuPred ?offerSku }}
  OPTIONAL {{ VALUES ?offerProductIDPred {{ {_values(schema_terms("productID"))} }} ?offer ?offerProductIDPred ?offerProductID }}
  OPTIONAL {{ VALUES ?offerIdentifierPred {{ {_values(schema_terms("identifier"))} }} ?offer ?offerIdentifierPred ?offerIdentifier }}
  OPTIONAL {{ ?offer <{OPLOFR_OFFER_NUMBER}> ?offerNumber }}
  OPTIONAL {{ VALUES ?itemSkuPred {{ {_values(schema_terms("sku"))} }} ?item ?itemSkuPred ?itemSku }}
  OPTIONAL {{ VALUES ?itemProductIDPred {{ {_values(schema_terms("productID"))} }} ?item ?itemProductIDPred ?itemProductID }}
  OPTIONAL {{ VALUES ?itemIdentifierPred {{ {_values(schema_terms("identifier"))} }} ?item ?itemIdentifierPred ?itemIdentifier }}
  OPTIONAL {{
    {{ VALUES ?pricePred {{ {_values(schema_terms("price"))} }} ?offer ?pricePred ?price }}
    UNION
    {{ VALUES ?specPred {{ {_values(schema_terms("priceSpecification"))} }}
       VALUES ?pricePred {{ {_values(schema_terms("price"))} }}
       ?offer ?specPred ?priceSpec . ?priceSpec ?pricePred ?price }}
  }}
  OPTIONAL {{
    {{ VALUES ?currencyPred {{ {_values(schema_terms("priceCurrency"))} }} ?offer ?currencyPred ?currency }}
    UNION
    {{ VALUES ?specPred {{ {_values(schema_terms("priceSpecification"))} }}
       VALUES ?currencyPred {{ {_values(schema_terms("priceCurrency"))} }}
       ?offer ?specPred ?currencySpec . ?currencySpec ?currencyPred ?currency }}
  }}
  OPTIONAL {{ VALUES ?availabilityPred {{ {_values(schema_terms("availability"))} }} ?offer ?availabilityPred ?availability }}
  OPTIONAL {{ VALUES ?sellerPred {{ {_values(schema_terms("seller"))} }} ?offer ?sellerPred ?seller }}
}} LIMIT 50"""
    r = session.get(endpoint, params={"query": query, "format": "application/sparql-results+json"}, timeout=30)
    r.raise_for_status()
    try:
        rows = r.json().get("results", {}).get("bindings", [])
    except ValueError as e:
        raise RuntimeError(f"SPARQL endpoint did not return JSON results: {e}") from e
    g = Graph()
    for row in rows:
        offer, item = row.get("offer", {}).get("value"), row.get("item", {}).get("value")
        if not offer:
            continue
        offer_ref = URIRef(offer)
        item_ref = URIRef(item) if item else None
        g.add((offer_ref, RDF.type, S("Offer")))
        if item_ref is not None:
            g.add((offer_ref, S("itemOffered"), item_ref))
        matched = row.get("matchedNode", {}).get("value")
        if matched and matched != resource_url:
            g.add((URIRef(matched), S("url"), URIRef(resource_url)))
        fields = (("offerSku", offer_ref, "sku"), ("offerProductID", offer_ref, "productID"),
                  ("offerIdentifier", offer_ref, "identifier"), ("itemSku", item_ref, "sku"),
                  ("itemProductID", item_ref, "productID"), ("itemIdentifier", item_ref, "identifier"),
                  ("availability", offer_ref, "availability"), ("seller", offer_ref, "seller"))
        for key, subj, pred_name in fields:
            if subj is None:
                continue
            binding = row.get(key)
            if not binding or not binding.get("value"):
                continue
            value = binding["value"]
            term = URIRef(value) if binding.get("type") == "uri" else Literal(value)
            g.add((subj, S(pred_name), term))
        specification_value = (row.get("priceSpec", {}).get("value") or
                               row.get("currencySpec", {}).get("value"))
        price_subject = offer_ref
        if specification_value:
            price_subject = URIRef(specification_value)
            g.add((offer_ref, S("priceSpecification"), price_subject))
        for key, pred_name in (("price", "price"), ("currency", "priceCurrency")):
            binding = row.get(key)
            if binding and binding.get("value"):
                value = binding["value"]
                term = URIRef(value) if binding.get("type") == "uri" else Literal(value)
                g.add((price_subject, S(pred_name), term))
        offer_number = row.get("offerNumber")
        if offer_number and offer_number.get("value"):
            g.add((offer_ref, OPLOFR_OFFER_NUMBER, Literal(offer_number["value"])))
    return g


def discover_offer(session, resource_url, rdf_url=None, merchant_origin=None,
                   sparql_endpoint=None, resource_predicates=None):
    """Use merchant SPARQL first, then dereference RDF when needed."""
    endpoint = sparql_endpoint or urljoin((merchant_origin or origin(resource_url)).rstrip("/") + "/", "sparql")
    try:
        graph = sparql_offer_graph(session, endpoint, resource_url, resource_predicates)
        if graph:
            return graph, find_offer(graph, resource_url, resource_predicates), {"method": "sparql", "endpoint": endpoint}
        reason = "no matching schema:Offer"
    except Exception as exc:
        reason = str(exc)
    rdf_source = rdf_url or resource_url
    graph = fetch_rdf(rdf_source, session)
    return graph, find_offer(graph, resource_url, resource_predicates), {
        "method": "rdf_dereference", "url": rdf_source, "sparql_fallback_reason": reason}


def _potential_action_item_id(g, offer):
    action, _ = first_obj_any(g, offer, schema_terms("potentialAction"))
    if not isinstance(action, URIRef):
        return None
    query = parse_qs(urlparse(str(action)).query)
    for key in ("item", "sku", "product", "product_id"):
        values = query.get(key)
        if values and values[0].strip():
            return unquote(values[0].strip())
    return None


def offer_to_record(g, offer, resource_url, item_id_override=None,
                    item_id_predicates=None, allow_action_item_id=False):
    item = _item_offered(g, offer)
    item_id = item_id_override.strip() if item_id_override else None
    item_id_source = "cli_override" if item_id else None
    # Prefer identifiers on itemOffered if it is a resource, then on Offer.
    subjects = [item, offer] if item is not None else [offer]
    if not item_id:
        for term in ("sku", "productID", "identifier"):
            for subj in subjects:
                v, pred = first_obj_any(g, subj, schema_terms(term))
                if isinstance(v, Literal) and str(v).strip():
                    item_id = str(v).strip()
                    item_id_source = str(pred)
                    break
            if item_id: break
    if not item_id:
        for pred in tuple(item_id_predicates or DEFAULT_ITEM_ID_PREDICATES):
            for subj in subjects:
                v = first_obj(g, subj, pred) if subj is not None else None
                if isinstance(v, Literal) and str(v).strip():
                    item_id = str(v).strip()
                    item_id_source = str(pred)
                    break
            if item_id: break
    if not item_id and allow_action_item_id:
        item_id = _potential_action_item_id(g, offer)
        item_id_source = "schema:potentialAction query parameter" if item_id else None
    if not item_id:
        raise RuntimeError("Offer lacks an accepted UCP item identifier; use schema:sku/productID/identifier, a configured --item-id-predicate, or explicit --item-id")
    price, _, price_spec = _offer_value(g, offer, "price")
    currency, _, currency_spec = _offer_value(g, offer, "priceCurrency")
    availability, _, _ = _offer_value(g, offer, "availability")
    seller, _, _ = _offer_value(g, offer, "seller")
    return {
        "resource_url": resource_url,
        "offer_iri": str(offer),
        "item_offered": str(item) if item is not None else resource_url,
        "ucp_item_id": item_id,
        "ucp_item_id_source": item_id_source,
        "rdf_price": str(price) if price is not None else None,
        "rdf_currency": str(currency) if currency is not None else None,
        "price_specification": str(price_spec or currency_spec) if (price_spec or currency_spec) else None,
        "availability": str(availability) if availability is not None else None,
        "seller": str(seller) if seller is not None else None,
    }


def origin(url):
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def discover_ucp(session, base_origin, profile_url=None):
    u = profile_url or urljoin(base_origin.rstrip("/") + "/", ".well-known/ucp")
    r = session.get(u, headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    profile = r.json()
    ucp = profile.get("ucp", profile)
    services = ucp.get("services", {})
    shopping = services.get("dev.ucp.shopping") if isinstance(services, dict) else None
    if shopping is None and isinstance(services, list):
        shopping = next((s for s in services if s.get("name") == "dev.ucp.shopping" or s.get("id") == "dev.ucp.shopping"), None)
    rest = None
    service_version = None
    if isinstance(shopping, list):
        rest = next((s for s in shopping if s.get("transport") == "rest" and s.get("endpoint")), None)
    elif isinstance(shopping, dict):
        service_version = shopping.get("version")
        if isinstance(shopping.get("rest"), dict):
            rest = shopping["rest"]
        elif shopping.get("transport") in (None, "rest") and shopping.get("endpoint"):
            rest = shopping
    if not rest:
        raise RuntimeError("UCP profile does not advertise a dev.ucp.shopping REST endpoint")
    caps = ucp.get("capabilities", {})
    if isinstance(caps, dict):
        checkout_capability = caps.get("dev.ucp.shopping.checkout")
    elif isinstance(caps, list):
        checkout_capability = next((c for c in caps if isinstance(c, dict) and c.get("name") == "dev.ucp.shopping.checkout"), None)
    else:
        checkout_capability = None
    if checkout_capability is None:
        raise RuntimeError("UCP profile does not advertise dev.ucp.shopping.checkout")
    return {"profile_url": u, "endpoint": rest["endpoint"].rstrip("/"),
            "version": rest.get("version") or service_version or ucp.get("version"),
            "checkout_capability": checkout_capability,
            "payment_handlers": profile.get("payment", {}).get("handlers", []),
            "profile": profile}


def create_checkout(session, endpoint, item_id, quantity, agent_profile=None):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if agent_profile:
        headers["UCP-Agent"] = f'profile="{agent_profile}"'
    body = {"line_items": [{"item": {"id": item_id}, "quantity": quantity}]}
    r = session.post(endpoint + "/checkout-sessions", headers=headers, json=body, timeout=30)
    r.raise_for_status()
    return r.json()


def checkout_summary(obj):
    out = {"checkout_id": obj.get("id"), "checkout_status": obj.get("status")}
    # Preserve likely totals without assuming one dated schema.
    for k in ("total", "totals", "currency", "payment", "messages", "continue_url"):
        if k in obj: out[k] = obj[k]
    return out


def run_mpp(command_template, resource_url):
    command = command_template.replace("{url}", resource_url)
    proc = subprocess.run(command, shell=True, capture_output=True, text=True)
    return {"command": command, "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def main():
    ap = argparse.ArgumentParser(description="RDF offer -> UCP checkout -> MPP protected-resource purchase")
    ap.add_argument("--resource-url", required=True)
    ap.add_argument("--rdf-url", help="RDF description URL; defaults to resource URL")
    ap.add_argument("--sparql-endpoint", help="Merchant SPARQL endpoint; defaults to <merchant-origin>/sparql")
    ap.add_argument("--merchant-origin", help="Origin containing /.well-known/ucp; defaults to resource origin")
    ap.add_argument("--quantity", type=int, default=1)
    ap.add_argument("--agent-profile")
    ap.add_argument("--identity-header-env", action="append", default=[], metavar="HEADER=ENV_VAR",
                    help="Send an identity header whose value comes from an environment variable; repeatable")
    ap.add_argument("--digest-user-env", help="Environment variable containing the Digest username")
    ap.add_argument("--digest-password-env", help="Environment variable containing the Digest password")
    ap.add_argument("--bearer-token-env", help="Environment variable containing an OAuth access token (never emitted)")
    ap.add_argument("--oauth-token-type", choices=("Bearer", "DPoP"), default="Bearer",
                    help="OAuth HTTP authorization scheme; defaults to Bearer")
    ap.add_argument("--dpop-proof-env", help="Environment variable containing the per-request DPoP proof JWT")
    ap.add_argument("--client-cert", help="PEM client certificate path for identity authentication")
    ap.add_argument("--client-key", help="PEM client private-key path used with --client-cert")
    ap.add_argument("--identity-established", action="store_true",
                    help="Assert that ambient session state establishes identity without exposing credentials")
    ap.add_argument("--accept-payment", help="Advertise supported payment methods, e.g. stripe/charge")
    ap.add_argument("--access-probe-only", action="store_true",
                    help="Test authentication/ACL/payment response metadata and stop")
    ap.add_argument("--resource-predicate", action="append", default=[], metavar="IRI",
                    help="Additional RDF predicate that explicitly links an offer/item to the resource; repeatable")
    ap.add_argument("--item-id-predicate", action="append", default=[], metavar="IRI",
                    help="Additional RDF predicate containing a literal UCP item ID; repeatable")
    ap.add_argument("--item-id", help="Explicit merchant UCP item ID override")
    ap.add_argument("--allow-action-item-id", action="store_true",
                    help="Allow item/sku/product query parameter from schema:potentialAction as the UCP item ID")
    ap.add_argument("--mpp-command", help="MPP-aware command template; use {url} placeholder, e.g. 'npx mppx {url}'")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.quantity < 1: raise SystemExit("quantity must be >= 1")
    s = requests.Session()
    try:
        identity_established = configure_identity(s, args)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    access = probe_resource(s, args.resource_url, identity_established)
    result = {"resource_url": args.resource_url, "resource_access": access}
    if args.access_probe_only:
        print(json.dumps(result, indent=2)); return
    if not args.dry_run and access["state"] != "payment_required":
        result["mpp"] = {"status": "not_executed", "reason": access["state"]}
        print(json.dumps(result, indent=2))
        if access["state"] not in ("access_granted",):
            sys.exit(3)
        return
    resource_predicates = DEFAULT_RESOURCE_PREDICATES + tuple(URIRef(v) for v in args.resource_predicate)
    item_id_predicates = DEFAULT_ITEM_ID_PREDICATES + tuple(URIRef(v) for v in args.item_id_predicate)
    linked_rdf_url = next((link["url"] for link in access["links"]
                           if set(link["rels"]).intersection({"describedby", "alternate"})), None)
    linked_ucp_profile = next((link["url"] for link in access["links"]
                               if set(link["rels"]).intersection({"ucp", "service-desc"})), None)
    g, offer, discovery = discover_offer(s, args.resource_url, args.rdf_url or linked_rdf_url, args.merchant_origin,
                                         args.sparql_endpoint, resource_predicates)
    rec = offer_to_record(g, offer, args.resource_url, args.item_id,
                          item_id_predicates, args.allow_action_item_id)
    ucp = discover_ucp(s, args.merchant_origin or origin(args.resource_url), linked_ucp_profile)
    result.update({"offer": rec, "offer_discovery": discovery,
                   "ucp": {k:v for k,v in ucp.items() if k != "profile"}})

    if args.dry_run:
        result["checkout_request"] = {"line_items": [{"item": {"id": rec["ucp_item_id"]}, "quantity": args.quantity}]}
        result["mpp"] = {"status": "not_executed", "reason": "dry_run"}
        print(json.dumps(result, indent=2)); return

    checkout = create_checkout(s, ucp["endpoint"], rec["ucp_item_id"], args.quantity, args.agent_profile)
    result["checkout"] = checkout_summary(checkout)

    if not args.mpp_command:
        result["mpp"] = {"status": "handoff_required", "resource_url": args.resource_url,
                         "note": "Run with --mpp-command using an MPP-aware client to fulfill HTTP 402 payment."}
        print(json.dumps(result, indent=2)); return

    mpp = run_mpp(args.mpp_command, args.resource_url)
    result["mpp"] = mpp
    result["warning"] = "MPP payment success does not by itself imply UCP checkout completion; reconcile only through a merchant-supported receipt/payment-handler binding."
    print(json.dumps(result, indent=2))
    if mpp["exit_code"] != 0: sys.exit(mpp["exit_code"])

if __name__ == "__main__":
    main()
