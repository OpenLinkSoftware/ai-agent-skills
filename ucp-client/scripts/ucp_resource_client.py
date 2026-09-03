#!/usr/bin/env python3
import argparse, atexit, base64, json, os, re, shutil, stat, subprocess, sys, tempfile, time, uuid
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


def decode_payment_request(value):
    """Decode the base64url-encoded JSON in a WWW-Authenticate: Payment 'request' param
    (an opl-shop MPP extension carrying amount/currency/externalId). Returns a dict, or
    None if the value is missing or not decodable. Last-resort offer-identity source when
    a resource has no SPARQL/RDF-discoverable schema:Offer at all (see discover_offer's
    except-branch fallback in main()) -- --match-url is the preferred fix when the offer
    IS RDF-discoverable but under a different IRI string than the access URL."""
    if not value:
        return None
    padded = value + "=" * (-len(value) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(padded))
    except Exception:
        return None


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


def probe_resource(session, resource_url, identity_established=False, max_redirects=5):
    """GET the resource, following same-origin redirects (e.g. a session-key
    redirect a server issues before the real 401/402/200 response) up to
    max_redirects hops. A redirect to a different origin is NOT followed
    automatically -- it is reported as-is via resource_access_metadata,
    since blindly following would resend the Authorization header and
    present the client identity (cert/bearer token) to an unverified host.
    """
    url = resource_url
    original_origin = origin(resource_url)
    response = None
    try:
        for _ in range(max_redirects + 1):
            response = session.get(url, stream=True, allow_redirects=False, timeout=30)
            if 300 <= response.status_code < 400:
                location = response.headers.get("Location")
                if location:
                    next_url = urljoin(url, location)
                    if origin(next_url) == original_origin:
                        response.close()
                        url = next_url
                        continue
            return resource_access_metadata(response, resource_url, identity_established)
        return resource_access_metadata(response, resource_url, identity_established)
    finally:
        if response is not None:
            response.close()


def load_pkcs12_identity(p12_path, password):
    """Load a PKCS#12 (.p12/.pfx) client identity -- e.g. a WebID-TLS/NetID bundle -- and
    write its certificate chain + private key out as temporary PEM files. `requests` (via
    urllib3/ssl.SSLContext.load_cert_chain) has no native PKCS#12 support and requires file
    paths, not in-memory key material, so this is the unavoidable bridge.

    Returns (cert_path, key_path, tmp_dir). The temp dir is 0700, the key file 0600, and
    cleanup (shutil.rmtree) is registered via atexit by the caller -- see configure_identity.
    The password is read by the caller from an environment variable, never accepted on the
    command line, and never logged or re-emitted here.
    """
    from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
    with open(p12_path, "rb") as f:
        p12_data = f.read()
    try:
        key, cert, additional_certs = pkcs12.load_key_and_certificates(p12_data, password.encode())
    except Exception as exc:
        raise ValueError(f"could not load PKCS#12 bundle {p12_path}: {exc}") from exc
    if key is None or cert is None:
        raise ValueError(f"PKCS#12 bundle {p12_path} is missing a certificate or private key")
    tmp_dir = tempfile.mkdtemp(prefix="ucp-p12-")
    os.chmod(tmp_dir, stat.S_IRWXU)
    cert_path = os.path.join(tmp_dir, "cert.pem")
    key_path = os.path.join(tmp_dir, "key.pem")
    with open(cert_path, "wb") as f:
        for c in [cert] + list(additional_certs or []):
            f.write(c.public_bytes(Encoding.PEM))
    with open(key_path, "wb") as f:
        f.write(key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()))
    os.chmod(cert_path, stat.S_IRUSR | stat.S_IWUSR)
    os.chmod(key_path, stat.S_IRUSR | stat.S_IWUSR)
    return cert_path, key_path, tmp_dir


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
    if args.client_p12 and args.client_cert:
        raise ValueError("--client-p12 and --client-cert are alternative identity sources; choose one")
    if args.client_p12:
        if not args.client_p12_password_env:
            raise ValueError("--client-p12 requires --client-p12-password-env")
        password = os.environ.get(args.client_p12_password_env)
        if password is None:
            raise ValueError(f"{args.client_p12_password_env} is not set")
        cert_path, key_path, tmp_dir = load_pkcs12_identity(args.client_p12, password)
        atexit.register(shutil.rmtree, tmp_dir, ignore_errors=True)
        session.cert = (cert_path, key_path)
        established = True
    elif args.client_cert:
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


def _offer_query_body(resource_url, resource_predicates):
    return f"""
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
  OPTIONAL {{ VALUES ?sellerPred {{ {_values(schema_terms("seller"))} }} ?offer ?sellerPred ?seller }}"""


def _offer_query(resource_url, resource_predicates, graph_wrap=False):
    body = _offer_query_body(resource_url, resource_predicates)
    if graph_wrap:
        body = f"  GRAPH ?__mppGraph {{ {body}\n  }}"
    return f"""SELECT ?offer ?item ?matchedNode ?matchPredicate ?priceSpec ?currencySpec
       ?offerSku ?offerProductID ?offerIdentifier ?offerNumber
       ?itemSku ?itemProductID ?itemIdentifier ?price ?currency ?availability ?seller
WHERE {{
{body}
}} LIMIT 50"""


def sparql_offer_graph(session, endpoint, resource_url, resource_predicates=None, default_graph_uris=None):
    """Query direct and item-mediated resource relations across Schema.org namespaces.

    Quad stores (Virtuoso and others) commonly keep offer data in a named graph
    outside the SPARQL protocol default graph. If an unscoped query returns no
    rows and the caller did not explicitly scope the query via
    `default_graph_uris`, automatically retry once with the same WHERE clause
    wrapped in `GRAPH ?g { ... }` to scan across all named graphs before giving
    up to RDF dereference.
    """
    if urlparse(resource_url).scheme not in ("http", "https"):
        raise ValueError("resource URL must be an HTTP(S) IRI")
    resource_predicates = tuple(resource_predicates or DEFAULT_RESOURCE_PREDICATES)

    def run(query):
        params = [("query", query), ("format", "application/sparql-results+json")]
        for iri in (default_graph_uris or ()):
            params.append(("default-graph-uri", iri))
        r = session.get(endpoint, params=params, timeout=30)
        r.raise_for_status()
        try:
            return r.json().get("results", {}).get("bindings", [])
        except ValueError as e:
            raise RuntimeError(f"SPARQL endpoint did not return JSON results: {e}") from e

    rows = run(_offer_query(resource_url, resource_predicates, graph_wrap=False))
    if not rows and not default_graph_uris:
        rows = run(_offer_query(resource_url, resource_predicates, graph_wrap=True))
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
                   sparql_endpoint=None, resource_predicates=None, default_graph_uris=None):
    """Use merchant SPARQL first, then dereference RDF when needed."""
    endpoint = sparql_endpoint or urljoin((merchant_origin or origin(resource_url)).rstrip("/") + "/", "sparql")
    try:
        graph = sparql_offer_graph(session, endpoint, resource_url, resource_predicates, default_graph_uris)
        if graph:
            return graph, find_offer(graph, resource_url, resource_predicates), {"method": "sparql", "endpoint": endpoint}
        sparql_reason = "no matching schema:Offer"
    except Exception as exc:
        sparql_reason = str(exc)
    rdf_source = rdf_url or resource_url
    try:
        graph = fetch_rdf(rdf_source, session)
    except Exception as exc:
        # fetch_rdf already tries typed error bodies and Link-header alternates before
        # raising -- an exception here means offer discovery genuinely found nothing via
        # either path. Surface both reasons together instead of letting this propagate as
        # an unhandled HTTPError (main()'s caller decides how to report it).
        raise RuntimeError(
            f"offer discovery failed: SPARQL at {endpoint} ({sparql_reason}); "
            f"RDF dereference of {rdf_source} ({exc})") from exc
    return graph, find_offer(graph, resource_url, resource_predicates), {
        "method": "rdf_dereference", "url": rdf_source, "sparql_fallback_reason": sparql_reason}


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
    # payment_handlers per https://ucp.dev's discovery schema (source/schemas/ucp.json) lives
    # inside the ucp envelope, keyed by reverse-domain handler name -> list of handler entries
    # -- NOT the flat profile.payment.handlers shape some earlier/alternate merchants used.
    # Support both so this stays compatible either way.
    raw_handlers = ucp.get("payment_handlers")
    if isinstance(raw_handlers, dict):
        payment_handlers = [dict(entry, reverse_domain=name)
                            for name, entries in raw_handlers.items()
                            for entry in (entries or []) if isinstance(entry, dict)]
    elif isinstance(raw_handlers, list):
        payment_handlers = raw_handlers
    else:
        payment_handlers = profile.get("payment", {}).get("handlers", [])
    return {"profile_url": u, "endpoint": rest["endpoint"].rstrip("/"),
            "version": rest.get("version") or service_version or ucp.get("version"),
            "checkout_capability": checkout_capability,
            "payment_handlers": payment_handlers,
            "profile": profile}


def _ucp_mutation_headers(agent_profile=None):
    # UCP-Agent, request-id, idempotency-key and request-signature are required on every
    # mutating call by the reference dispatcher (UCP.DBA."checkout-sessions" in opl-shop's
    # ucp.sql) -- a request missing any of them gets a 422 before the body is even looked
    # at. request-signature is currently only checked for presence server-side, not
    # cryptographically verified, so a placeholder value is accepted.
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "UCP-Agent": f'profile="{agent_profile}"' if agent_profile else 'profile="urn:ucp-resource-client"',
        "request-id": f"req_{uuid.uuid4()}",
        "idempotency-key": str(uuid.uuid4()),
        "request-signature": "dummy_signature",
    }


def create_checkout(session, endpoint, item_id, quantity, agent_profile=None, currency="usd"):
    headers = _ucp_mutation_headers(agent_profile)
    body = {"line_items": [{"item": {"id": item_id}, "quantity": quantity}], "currency": currency}
    r = session.post(endpoint + "/checkout-sessions", headers=headers, json=body, timeout=30)
    r.raise_for_status()
    return r.json()


def get_checkout(session, endpoint, checkout_id, agent_profile=None):
    headers = {"Accept": "application/json"}
    if agent_profile:
        headers["UCP-Agent"] = f'profile="{agent_profile}"'
    r = session.get(f"{endpoint}/checkout-sessions/{checkout_id}", headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()


def checkout_total(checkout_obj):
    for t in checkout_obj.get("totals", []) or []:
        if t.get("type") == "total":
            return t.get("amount")
    return None


def get_test_stripe_spt(stripe_api_key, amount, currency="usd", payment_method="pm_card_visa", expires_at=None):
    """Fetch a Stripe test-mode Shared Payment Token, capped at `amount` (minor units).
    Never log or return the API key itself."""
    if expires_at is None:
        expires_at = int(time.time()) + 3600
    resp = requests.post(
        "https://api.stripe.com/v1/test_helpers/shared_payment/granted_tokens",
        auth=(stripe_api_key, ""),
        data={
            "payment_method": payment_method,
            "usage_limits[currency]": currency,
            "usage_limits[max_amount]": amount,
            "usage_limits[expires_at]": expires_at,
        },
        timeout=30,
    )
    resp.raise_for_status()
    token = resp.json().get("id")
    if not token:
        raise RuntimeError("Stripe did not return an SPT id")
    return token


def complete_checkout(session, endpoint, checkout_id, spt_token, handler_id="opl_shop_stripe_spt", agent_profile=None):
    # payment.instruments[] shape per the UCP checkout schema; credential.type
    # "stripe_payment_token" is the Link Agent Wallet shape from
    # https://docs.stripe.com/agentic-commerce/ucp/stripe-payments-handler -- the same
    # Shared Payment Token ACP.DBA.STRIPE_PAYMENT/STRIPE_SUBSCRIPTION_PAYMENT already accept
    # in the opl-shop reference merchant.
    headers = _ucp_mutation_headers(agent_profile)
    body = {"payment": {"instruments": [{
        "id": "instr_1", "handler_id": handler_id, "type": "link", "selected": True,
        "credential": {"type": "stripe_payment_token", "token": spt_token},
    }]}}
    r = session.post(f"{endpoint}/checkout-sessions/{checkout_id}/complete", headers=headers, json=body, timeout=30)
    r.raise_for_status()
    return r.json()


def get_order(session, endpoint, order_id, agent_profile=None):
    headers = {"Accept": "application/json"}
    if agent_profile:
        headers["UCP-Agent"] = f'profile="{agent_profile}"'
    r = session.get(f"{endpoint}/orders/{order_id}", headers=headers, timeout=30)
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


def fetch_product_feed(session, feed_url):
    """Fetch and parse a merchant product feed (RSS 2.0 with the Google Merchant `g:`
    namespace, e.g. opl-shop's /shop/feed?rss). Every item already carries its offer IRI
    (`link`/`guid`, directly usable as a UCP item id), a compact `g:id`, and `g:price` as a
    single "<amount> <CURRENCY>" string -- this is a complete, pre-authenticated offer
    catalog, so a caller with a feed URL can skip the resource probe / 401 / 402 / RDF /
    SPARQL discovery flow entirely and go straight to "which offer do you want to check out."
    Returns a list of dicts: title, description, link, guid, feed_item_id, price, currency,
    product_type, brand.
    """
    import xml.etree.ElementTree as ET
    r = session.get(feed_url, headers={"Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.1"},
                    timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    g_ns = "{http://base.google.com/ns/1.0}"

    def text(el, tag, namespaced=False):
        found = el.find(f"{g_ns}{tag}" if namespaced else tag)
        return found.text.strip() if found is not None and found.text else None

    items = []
    for el in root.iter("item"):
        price_raw = text(el, "price", namespaced=True)
        price, currency = None, None
        if price_raw:
            parts = price_raw.rsplit(" ", 1)
            price, currency = (parts[0], parts[1]) if len(parts) == 2 else (price_raw, None)
        items.append({
            "title": text(el, "title"),
            "description": text(el, "description"),
            "link": text(el, "link"),
            "guid": text(el, "guid"),
            "feed_item_id": text(el, "id", namespaced=True),
            "price": price,
            "currency": currency,
            "product_type": text(el, "product_type", namespaced=True),
            "brand": text(el, "brand", namespaced=True),
        })
    return items


def select_feed_items(items, feed_item_id=None, feed_search=None):
    """Filter feed items by --feed-item-id (matched against feed_item_id/guid/link) or
    --feed-search (case-insensitive substring match on title). Returns the matching list;
    empty means neither selector was given (caller should list everything)."""
    if feed_item_id:
        return [it for it in items
                if feed_item_id in (it.get("feed_item_id"), it.get("guid"), it.get("link"))]
    if feed_search:
        needle = feed_search.lower()
        return [it for it in items if needle in (it.get("title") or "").lower()]
    return []


def feed_item_to_record(item):
    item_id = item.get("link") or item.get("guid") or item.get("feed_item_id")
    return {
        "resource_url": None,
        "offer_iri": item.get("link") or item.get("guid"),
        "item_offered": None,
        "ucp_item_id": item_id,
        "ucp_item_id_source": "product_feed",
        "rdf_price": item.get("price"),
        "rdf_currency": item.get("currency"),
        "price_specification": None,
        "availability": None,
        "seller": item.get("brand"),
    }


def checkout_and_pay(s, ucp, rec, args, result):
    """Shared tail for both the --resource-url (RDF/SPARQL/402-driven) and --product-feed
    entry points: create the checkout, then either complete it via Stripe SPT, hand off to
    an --mpp-command against the protected resource, or report handoff_required. Always
    prints the final JSON result and terminates the process (return or sys.exit)."""
    try:
        checkout = create_checkout(s, ucp["endpoint"], rec["ucp_item_id"], args.quantity, args.agent_profile,
                                   currency=(rec.get("rdf_currency") or "usd"))
    except requests.exceptions.HTTPError as exc:
        resp = exc.response
        result["checkout_error"] = {
            "status": resp.status_code if resp is not None else None,
            "body": (resp.text[:2000] if resp is not None else None),
            "endpoint": ucp["endpoint"] + "/checkout-sessions",
        }
        result["mpp"] = {"status": "not_executed", "reason": "checkout_creation_failed"}
        print(json.dumps(result, indent=2))
        sys.exit(4)
    result["checkout"] = checkout_summary(checkout)

    if args.complete_with_stripe_spt:
        total = checkout_total(checkout)
        if total is None:
            result["mpp"] = {"status": "not_executed", "reason": "checkout has no totals[type=total] entry"}
            print(json.dumps(result, indent=2)); sys.exit(5)
        stripe_key = os.environ.get(args.stripe_api_key_env)
        if not stripe_key:
            result["mpp"] = {"status": "not_executed",
                             "reason": f"{args.stripe_api_key_env} is not set"}
            print(json.dumps(result, indent=2)); sys.exit(5)
        try:
            spt = get_test_stripe_spt(stripe_key, total, currency=checkout.get("currency", "usd"),
                                      payment_method=args.stripe_payment_method)
            completed = complete_checkout(s, ucp["endpoint"], checkout["id"], spt,
                                          args.stripe_payment_handler_id, args.agent_profile)
        except Exception as exc:
            result["mpp"] = {"status": "failed", "error": str(exc)}
            print(json.dumps(result, indent=2)); sys.exit(5)
        result["checkout"] = checkout_summary(completed)
        result["mpp"] = {"status": "completed", "method": "stripe_spt"}
        order_id = (completed.get("order") or {}).get("id")
        if order_id:
            try:
                result["order"] = get_order(s, ucp["endpoint"], order_id, args.agent_profile)
            except Exception as exc:
                result["order_error"] = str(exc)
        print(json.dumps(result, indent=2))
        return

    if not args.mpp_command:
        result["mpp"] = {"status": "handoff_required", "resource_url": args.resource_url,
                         "note": "Run with --complete-with-stripe-spt to complete the UCP "
                                 "checkout via Stripe, or --mpp-command using an MPP-aware "
                                 "client to fulfill the resource's own HTTP 402 payment."}
        print(json.dumps(result, indent=2)); return

    if not args.resource_url:
        result["mpp"] = {"status": "not_executed",
                         "reason": "--mpp-command requires --resource-url (nothing to pay a "
                                   "resource-level 402 for when checkout came from --product-feed)"}
        print(json.dumps(result, indent=2)); sys.exit(5)

    mpp = run_mpp(args.mpp_command, args.resource_url)
    result["mpp"] = mpp
    result["warning"] = "MPP payment success does not by itself imply UCP checkout completion; reconcile only through a merchant-supported receipt/payment-handler binding."
    print(json.dumps(result, indent=2))
    if mpp["exit_code"] != 0: sys.exit(mpp["exit_code"])


def main():
    ap = argparse.ArgumentParser(description="RDF offer -> UCP checkout -> MPP protected-resource purchase")
    ap.add_argument("--resource-url", help="Protected resource IRI. Required unless --product-feed is used "
                    "instead (they are alternative entry points -- a resource URL drives the 401/402/RDF "
                    "discovery flow, a feed URL skips straight to an offer list).")
    ap.add_argument("--product-feed", help="Merchant product feed URL (RSS 2.0 + Google Merchant 'g:' "
                    "namespace, e.g. https://<shop>/shop/feed?rss). When given, skips the resource probe, "
                    "401/402 handling, and RDF/SPARQL offer discovery entirely -- the feed already lists "
                    "every purchasable offer with its price/currency/item id, pre-authenticated (feeds are "
                    "typically public). Combine with --feed-item-id or --feed-search to select one item and "
                    "proceed straight to checkout; with neither, all feed items are listed and the process "
                    "stops so the caller can choose.")
    ap.add_argument("--feed-item-id", help="Select a --product-feed item by its g:id, guid, or link (offer "
                    "IRI). Must match exactly one item.")
    ap.add_argument("--feed-search", help="Select --product-feed item(s) by case-insensitive substring match "
                    "on title. Must match exactly one item to proceed to checkout.")
    ap.add_argument("--match-url", help="Canonical resource IRI to match against RDF/SPARQL offers, if different "
                    "from --resource-url. Use this when the merchant's published resource identifier and the "
                    "actual access endpoint differ (e.g. access requires a distinct mTLS port not present in the "
                    "resource's public IRI). Defaults to --resource-url.")
    ap.add_argument("--rdf-url", help="RDF description URL; defaults to resource URL")
    ap.add_argument("--sparql-endpoint", help="Merchant SPARQL endpoint; defaults to <merchant-origin>/sparql")
    ap.add_argument("--sparql-default-graph", action="append", default=[], metavar="IRI",
                    help="SPARQL protocol default-graph-uri parameter(s) to scope offer discovery to a named "
                    "graph; repeatable. When omitted, an unscoped query that returns no rows is automatically "
                    "retried scanning all named graphs before falling back to RDF dereference.")
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
    ap.add_argument("--client-p12", help="PKCS#12 (.p12/.pfx) client identity bundle path -- e.g. a "
                    "WebID-TLS/NetID certificate -- as an alternative to --client-cert/--client-key. "
                    "Converted to temporary PEM files in memory via the cryptography library (requests "
                    "has no native PKCS#12 support); the temp files are 0600, in a 0700 directory, and "
                    "removed on process exit. Requires --client-p12-password-env.")
    ap.add_argument("--client-p12-password-env", help="Environment variable containing the PKCS#12 "
                    "bundle's password. Never accepted on the command line, never emitted.")
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
    ap.add_argument("--complete-with-stripe-spt", action="store_true",
                    help="Complete the UCP checkout itself via a Stripe test-mode Shared "
                         "Payment Token, then fetch the resulting order. Distinct from "
                         "--mpp-command, which pays the protected resource's own 402 "
                         "challenge directly rather than completing the UCP checkout.")
    ap.add_argument("--stripe-api-key-env", default="STRIPE_API_KEY",
                    help="Environment variable containing the Stripe secret key (test mode; "
                         "never emitted). Default: STRIPE_API_KEY")
    ap.add_argument("--stripe-payment-method", default="pm_card_visa",
                    help="Stripe test payment method to back the SPT. Default: pm_card_visa")
    ap.add_argument("--stripe-payment-handler-id", default="opl_shop_stripe_spt",
                    help="handler_id sent in the payment instrument; must match a handler "
                         "the merchant advertises at /.well-known/ucp. Default: opl_shop_stripe_spt")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.quantity < 1: raise SystemExit("quantity must be >= 1")
    if not args.resource_url and not args.product_feed:
        raise SystemExit("either --resource-url or --product-feed is required")
    if args.resource_url and args.product_feed:
        raise SystemExit("--resource-url and --product-feed are alternative entry points; pass only one")
    s = requests.Session()
    try:
        identity_established = configure_identity(s, args)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    if args.product_feed:
        items = fetch_product_feed(s, args.product_feed)
        result = {"product_feed": args.product_feed, "feed_item_count": len(items)}
        matches = select_feed_items(items, args.feed_item_id, args.feed_search)
        if not args.feed_item_id and not args.feed_search:
            result["feed_items"] = items
            result["note"] = ("No --feed-item-id/--feed-search given -- choose one of the "
                              "feed_items above and re-run with --feed-item-id (its feed_item_id, "
                              "guid, or link) or --feed-search (a title substring) to proceed to checkout.")
            print(json.dumps(result, indent=2)); return
        if len(matches) != 1:
            result["feed_items"] = matches if matches else items
            result["error"] = ("no feed item matches the given selector" if not matches else
                               "multiple feed items match; narrow --feed-search or use --feed-item-id")
            print(json.dumps(result, indent=2))
            sys.exit(1 if not matches else 2)
        rec = feed_item_to_record(matches[0])
        merchant_origin = args.merchant_origin or origin(args.product_feed)
        ucp = discover_ucp(s, merchant_origin)
        result.update({"selected_offer": matches[0], "offer": rec,
                       "offer_discovery": {"method": "product_feed", "feed_url": args.product_feed},
                       "ucp": {k: v for k, v in ucp.items() if k != "profile"}})
        if args.dry_run:
            result["checkout_request"] = {"line_items": [{"item": {"id": rec["ucp_item_id"]}, "quantity": args.quantity}]}
            result["mpp"] = {"status": "not_executed", "reason": "dry_run"}
            print(json.dumps(result, indent=2)); return
        checkout_and_pay(s, ucp, rec, args, result)
        return

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
    match_url = args.match_url or args.resource_url
    if match_url != args.resource_url:
        result["match_url"] = match_url
    try:
        g, offer, discovery = discover_offer(s, match_url, args.rdf_url or linked_rdf_url, args.merchant_origin,
                                             args.sparql_endpoint, resource_predicates, args.sparql_default_graph)
        rec = offer_to_record(g, offer, match_url, args.item_id,
                              item_id_predicates, args.allow_action_item_id)
    except Exception as exc:
        # Fall back to the offer identity embedded in the resource's own 402 Payment
        # challenge (WWW-Authenticate: Payment ...request=<base64url JSON>), when present.
        # Some protected resources (e.g. MPP/x402-gated personal files) carry no
        # SPARQL/RDF-discoverable schema:Offer at all -- --match-url doesn't help there
        # since there's no RDF to match against -- but the challenge itself names the exact
        # offer IRI used to price the checkout. Confirmed against a live resource.
        decoded = None
        if not args.item_id:
            for challenge in access.get("payment_challenges", []):
                decoded = decode_payment_request(challenge.get("request"))
                if decoded and decoded.get("externalId"):
                    break
                decoded = None
        if not args.item_id and (not decoded or not decoded.get("externalId")):
            result["offer_discovery_error"] = str(exc)
            result["mpp"] = {"status": "not_executed", "reason": "offer_discovery_failed"}
            print(json.dumps(result, indent=2))
            sys.exit(4)
        item_id = args.item_id.strip() if args.item_id else decoded["externalId"]
        rec = {
            "resource_url": match_url,
            "offer_iri": item_id,
            "item_offered": match_url,
            "ucp_item_id": item_id,
            "ucp_item_id_source": "cli_override" if args.item_id else "payment_challenge_external_id",
            "rdf_price": decoded.get("amount") if decoded else None,
            "rdf_currency": decoded.get("currency") if decoded else None,
            "price_specification": None,
            "availability": None,
            "seller": decoded.get("recipient") if decoded else None,
        }
        discovery = {"method": "payment_challenge" if decoded else "cli_override", "sparql_rdf_error": str(exc)}
    ucp = discover_ucp(s, args.merchant_origin or origin(args.resource_url), linked_ucp_profile)
    result.update({"offer": rec, "offer_discovery": discovery,
                   "ucp": {k:v for k,v in ucp.items() if k != "profile"}})

    if args.dry_run:
        result["checkout_request"] = {"line_items": [{"item": {"id": rec["ucp_item_id"]}, "quantity": args.quantity}]}
        result["mpp"] = {"status": "not_executed", "reason": "dry_run"}
        print(json.dumps(result, indent=2)); return

    checkout_and_pay(s, ucp, rec, args, result)

if __name__ == "__main__":
    main()
