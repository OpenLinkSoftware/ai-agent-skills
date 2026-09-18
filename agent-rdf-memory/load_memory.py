#!/usr/bin/env python3
"""SessionStart hook: SPARQL-first RDF memory loader with filesystem fallback.

Preferred path:
  1. Resolve a SPARQL endpoint.
  2. Discover actual named graph IRIs in the target store.
  3. Build a compact context pack from ontology/preferences/index/howto/session
     graphs.

Fallback path:
  If the SPARQL path is unavailable or incomplete, read the local Turtle files
  directly, preserving the older compact injection behavior.
"""
import csv
import glob
import io
import json
import os
import re
import ssl
import subprocess
import sys
import urllib.parse
import urllib.request

BASE = os.environ.get(
    "AGENT_RDF_MEMORY",
    os.path.join(os.path.dirname(os.path.abspath(__file__)))
)
MAX_SESSION = 3072
SPARQL_TIMEOUT = float(os.environ.get("AGENT_RDF_MEMORY_SPARQL_TIMEOUT", "4"))
MAX_STEPS = int(os.environ.get("AGENT_RDF_MEMORY_MAX_STEPS", "80"))

# preferences.ttl Step 301: memory graphs are never queried anonymously.
# Two authentication methods, tried in AGENT_RDF_MEMORY_AUTH order:
#   webid-tls  client cert (PKCS#12) against AGENT_RDF_MEMORY_WEBID_ENDPOINT;
#              skipped unless that endpoint is set, because a listener that
#              never requests a client cert silently degrades to anonymous.
#   digest     dba account (Keychain item virtuoso-local-dba) against /sparql-auth.
# Secrets come from Keychain, stay in memory, and reach curl on stdin
# (never argv, env, logs or hook output).
AUTH_METHODS = [m.strip() for m in os.environ.get(
    "AGENT_RDF_MEMORY_AUTH", "webid-tls,digest").split(",") if m.strip()]
DBA_KEYCHAIN_SERVICE = os.environ.get("AGENT_RDF_MEMORY_DBA_KEYCHAIN", "virtuoso-local-dba")
DBA_USER = "dba"
WEBID_ENDPOINT = os.environ.get("AGENT_RDF_MEMORY_WEBID_ENDPOINT", "").strip()
WEBID_P12 = os.environ.get(
    "AGENT_RDF_MEMORY_WEBID_P12",
    "/Users/kidehen/Documents/Management/Marketing/WebID/Templates/YouID/"
    "link-in-bio-credentials-5/cert.p12",  # core.ttl :userPrincipalCredentials
)
WEBID_KEYCHAIN_SERVICE = os.environ.get("AGENT_RDF_MEMORY_WEBID_KEYCHAIN", "uriburner-p12")
GRAPH_PREFIX = os.environ.get(
    "AGENT_RDF_MEMORY_GRAPH_PREFIX", "urn:dav:/DAV/home/kidehen/agent-rdf-memory/")
AUTH_FOR = {}          # endpoint -> "webid-tls" | "digest"
DETAIL_FOLDERS = ("(root)", "entities")  # listed graph-by-graph in the state table
TYPE_ROWS = int(os.environ.get("AGENT_RDF_MEMORY_TYPE_ROWS", "20"))
CURIES = [
    ("http://schema.org/", "schema:"),
    ("https://www.openlinksw.com/ontology/opal/", "opal:"),
    ("http://www.w3.org/2002/07/owl#", "owl:"),
    ("http://www.w3.org/2000/01/rdf-schema#", "rdfs:"),
    ("http://www.w3.org/2004/02/skos/core#", "skos:"),
]


def curie(iri):
    for ns, pfx in CURIES:
        if iri.startswith(ns):
            return pfx + iri[len(ns):]
    if iri.startswith(GRAPH_PREFIX):
        return "mem:" + iri[len(GRAPH_PREFIX):]   # mem: = GRAPH_PREFIX
    return iri
_secrets = {}
_auth_failed = set()   # methods that got a 401 this run (lockout guard)


def strip_comments(text):
    """Remove Turtle comment lines and collapse consecutive blank lines."""
    out, prev_blank = [], False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            continue
        blank = s == ""
        if blank and prev_blank:
            continue
        out.append(line)
        prev_blank = blank
    return "\n".join(out)


def endpoint_candidates():
    """(endpoint, auth-method) pairs; every one is authenticated."""
    pairs = []
    extra = [x.strip() for x in os.environ.get(
        "AGENT_RDF_MEMORY_SPARQL_ENDPOINTS", "").split(",") if x.strip()]
    for method in AUTH_METHODS:
        if method == "webid-tls" and WEBID_ENDPOINT:
            pairs.append((WEBID_ENDPOINT, method))
        elif method == "digest":
            for ep in extra + ["https://localhost/sparql-auth",
                               "http://localhost:8890/sparql-auth"]:
                if (ep, method) not in pairs:
                    pairs.append((ep, method))
    return pairs


def https_context_for(endpoint):
    if endpoint.startswith("https://localhost") or endpoint.startswith("https://127.0.0.1"):
        return ssl._create_unverified_context()
    return None


def is_local(endpoint):
    host = urllib.parse.urlparse(endpoint).hostname or ""
    return host in ("localhost", "127.0.0.1", "::1")


def keychain_secret(service):
    """Read a generic-password item once; None if unavailable."""
    if service not in _secrets:
        try:
            out = subprocess.run(
                ["security", "find-generic-password", "-s", service,
                 "-a", os.environ.get("USER", ""), "-w"],
                capture_output=True, text=True, timeout=5,
            )
            _secrets[service] = out.stdout.rstrip("\n") if out.returncode == 0 else ""
        except Exception:
            _secrets[service] = ""
    return _secrets[service] or None


def curl_quote(value):
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def curl_auth_config(method):
    if method == "digest":
        pwd = keychain_secret(DBA_KEYCHAIN_SERVICE)
        if not pwd:
            raise RuntimeError(f"Keychain item {DBA_KEYCHAIN_SERVICE} unavailable")
        return "digest\n" + f"user = {curl_quote(DBA_USER + ':' + pwd)}\n"
    if method == "webid-tls":
        if not os.path.exists(WEBID_P12):
            raise RuntimeError(f"PKCS#12 bundle not found: {WEBID_P12}")
        pwd = keychain_secret(WEBID_KEYCHAIN_SERVICE)
        if not pwd:
            raise RuntimeError(f"Keychain item {WEBID_KEYCHAIN_SERVICE} unavailable")
        return ('cert-type = "P12"\n' + f"cert = {curl_quote(WEBID_P12)}\n"
                + f"pass = {curl_quote(pwd)}\n")
    raise RuntimeError(f"unknown auth method {method}")


def sparql_csv_auth(endpoint, method, query, timeout):
    """One authenticated request via curl; credentials passed on stdin."""
    if method in _auth_failed:
        raise RuntimeError(f"skipped: {method} login already failed this run (lockout guard)")
    config = curl_auth_config(method)
    cmd = ["curl", "-sS", "-K", "-", "-X", "POST",
           "--max-time", str(int(timeout) + 1),
           "-H", "Accept: text/csv",
           "--data-urlencode", f"query={query}",
           "--data-urlencode", "format=text/csv",
           "--data-urlencode", "timeout=30000",
           "-w", "\n%{http_code}", endpoint]
    if endpoint.startswith("https://") and is_local(endpoint):
        cmd.insert(1, "-k")  # localhost self-signed cert
    out = subprocess.run(cmd, input=config, capture_output=True, text=True, timeout=timeout + 3)
    if out.returncode != 0:
        raise RuntimeError(f"curl exit {out.returncode}: {out.stderr.strip()[:200]}")
    body, _, code = out.stdout.rpartition("\n")
    if code == "401":
        _auth_failed.add(method)
        raise RuntimeError(f"HTTP 401 with {method} credentials (not retrying)")
    if not code.startswith("2"):
        raise RuntimeError(f"HTTP {code}: {body[:300]}")
    return body


def sparql_csv(endpoint, query, timeout=SPARQL_TIMEOUT):
    method = AUTH_FOR.get(endpoint)
    if method:
        body = sparql_csv_auth(endpoint, method, query, timeout)
        if "SPARQL compiler" in body or "Virtuoso" in body[:600] and "Error" in body[:600]:
            raise RuntimeError(body[:600].replace("\n", " "))
        return list(csv.DictReader(io.StringIO(body)))
    data = urllib.parse.urlencode({
        "query": query,
        "format": "text/csv",
        "timeout": "30000",
    }).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Accept": "text/csv",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    context = https_context_for(endpoint)
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        body = response.read().decode("utf-8", errors="replace")
    if "SPARQL compiler" in body or "Virtuoso" in body[:600] and "Error" in body[:600]:
        raise RuntimeError(body[:600].replace("\n", " "))
    return list(csv.DictReader(io.StringIO(body)))


def sparql_quote(value):
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def first_working_endpoint():
    probe = "SELECT (COUNT(*) AS ?count) WHERE { GRAPH ?g { ?s ?p ?o } } LIMIT 1"
    errors = []
    for endpoint, method in endpoint_candidates():
        AUTH_FOR[endpoint] = method
        try:
            sparql_csv(endpoint, probe)
            return endpoint, errors
        except Exception as exc:
            errors.append(f"{endpoint} [{method}]: {exc}")
    return None, errors


def filename_from_graph(graph):
    return graph.rstrip("/").split("/")[-1]


def entity_base_from_graph(graph):
    # load-agent-rdf-memory.sql resolves relative IRIs against the graph IRI itself.
    if graph.startswith(GRAPH_PREFIX):
        return graph
    if graph.startswith("urn:dav:"):
        return "http:" + graph[len("urn:dav:"):]
    if "#" in graph:
        return graph.rsplit("#", 1)[0]
    return graph


def subject_for(graph, local_name):
    return entity_base_from_graph(graph) + "#" + local_name


def session_graph_from_doc(doc_iri):
    if "sessions/" in doc_iri:
        return GRAPH_PREFIX + "sessions/" + doc_iri.split("sessions/", 1)[1]
    if doc_iri.startswith("http:/DAV/"):
        return "urn:dav:" + doc_iri[len("http:"):]
    if doc_iri.startswith("https://localhost/DAV/"):
        return "urn:dav:" + doc_iri[len("https://localhost"):]
    return doc_iri


def discover_graphs(endpoint):
    raw_filters = os.environ.get(
        "AGENT_RDF_MEMORY_GRAPH_FILTERS",
        GRAPH_PREFIX,
    )
    filters = [item.strip() for item in raw_filters.split(",") if item.strip()]
    filter_expr = " || ".join(
        f"CONTAINS(STR(?g), {sparql_quote(item)})" for item in filters
    )
    wanted = [
        "core.ttl",
        "ontology.ttl",
        "preferences.ttl",
        "preferences.private.ttl",
        "index.ttl",
        "agent-identity.ttl",
        "virtuoso-sparql-formats.ttl",
        "virtuoso-workbench-query-dedup.ttl",
    ]
    wanted_expr = " || ".join(
        f"CONTAINS(STR(?g), {sparql_quote(item)})" for item in wanted
    )
    query = f"""
SELECT ?g ?type (COUNT(*) AS ?count) (SAMPLE(?s) AS ?sample)
WHERE {{
  GRAPH ?g {{ ?s a ?type . }}
  FILTER(({filter_expr}) && ({wanted_expr}))
}}
GROUP BY ?g ?type
ORDER BY ?g DESC(?count)
LIMIT 500
"""
    rows = sparql_csv(endpoint, query)
    graphs = {}
    for row in rows:
        graph = row.get("g", "")
        name = filename_from_graph(graph)
        if name:
            graphs[name] = graph
    return graphs, rows


def select_rows(endpoint, query, limit=None):
    rows = sparql_csv(endpoint, query)
    if limit is not None:
        return rows[:limit]
    return rows


def memory_state_table(endpoint):
    """SAMPLE()-based verification of the loaded memory graphs, one row per folder.

    Every on-disk .ttl is a named graph under GRAPH_PREFIX, so the query is
    scoped with one FROM NAMED per file; per-graph counts are taken in a
    subquery before the folder BINDs (string functions per triple are slow).
    """
    files = sorted(
        os.path.relpath(f, BASE)
        for f in glob.glob(os.path.join(BASE, "**", "*.ttl"), recursive=True)
        if not os.path.relpath(f, BASE).startswith("scripts" + os.sep)
    )
    empty = [rel for rel in files if os.path.getsize(os.path.join(BASE, rel)) == 0]
    files = [rel for rel in files if rel not in empty]  # zero-byte docs yield no graph
    def folder_of(rel):
        return rel.split("/", 1)[0] if "/" in rel else "(root)"
    on_disk = {}
    for rel in files:
        on_disk[folder_of(rel)] = on_disk.get(folder_of(rel), 0) + 1
    from_named = "\n".join(f"FROM NAMED <{GRAPH_PREFIX}{rel}>" for rel in files)
    query = f"""
SELECT ?folder (COUNT(?g) AS ?graphs) (SUM(?n) AS ?triples) (SAMPLE(?g) AS ?sampleGraph)
{from_named}
WHERE {{
  {{ SELECT ?g (COUNT(*) AS ?n) WHERE {{ GRAPH ?g {{ ?s ?p ?o }} }} GROUP BY ?g }}
  BIND(STRAFTER(STR(?g), "{GRAPH_PREFIX}") AS ?rel)
  BIND(IF(CONTAINS(?rel, "/"), STRBEFORE(?rel, "/"), "(root)") AS ?folder)
}}
GROUP BY ?folder ORDER BY ?folder
"""
    rows = {r.get("folder"): r for r in sparql_csv(endpoint, query)}
    lines = [
        "\n--- Memory graph state (SAMPLE() verification, Virtuoso) ---",
        f"Graph prefix: {GRAPH_PREFIX}",
        "| Folder | Files on disk | Graphs loaded | Triples | Sample graph | Status |",
        "|---|---:|---:|---:|---|---|",
    ]
    tot_disk = tot_loaded = tot_triples = 0
    for folder in sorted(set(on_disk) | set(rows)):
        r = rows.get(folder, {})
        disk = on_disk.get(folder, 0)
        loaded = int(r.get("graphs") or 0)
        triples = int(r.get("triples") or 0)
        sample = (r.get("sampleGraph") or "").replace(GRAPH_PREFIX, "")
        status = "OK" if loaded == disk else f"{disk - loaded:+d} not loaded"
        lines.append(f"| {folder} | {disk} | {loaded} | {triples} | {sample} | {status} |")
        tot_disk += disk; tot_loaded += loaded; tot_triples += triples
    lines.append(f"| **total** | {tot_disk} | {tot_loaded} | {tot_triples} | | "
                 f"{'OK' if tot_disk == tot_loaded else 'CHECK'} |")
    # Per-graph detail for the small core folders, so key registries (e.g.
    # entities/people.ttl) are visible by name rather than hidden behind SAMPLE().
    detail = [rel for rel in files if folder_of(rel) in DETAIL_FOLDERS]
    if detail:
        detail_query = (
            "SELECT ?g (COUNT(*) AS ?n)\n"
            + "\n".join(f"FROM NAMED <{GRAPH_PREFIX}{rel}>" for rel in detail)
            + "\nWHERE { GRAPH ?g { ?s ?p ?o } } GROUP BY ?g ORDER BY ?g"
        )
        counts = {r.get("g", "").replace(GRAPH_PREFIX, ""): int(r.get("n") or 0)
                  for r in sparql_csv(endpoint, detail_query)}
        lines += ["", "Core graphs (" + ", ".join(DETAIL_FOLDERS) + "):",
                  "| Graph | Triples | Status |", "|---|---:|---|"]
        for rel in detail:
            n = counts.get(rel, 0)
            lines.append(f"| {rel} | {n} | {'OK' if n else 'MISSING'} |")
    # Entity-type sampling across every memory graph.
    type_query = f"""
SELECT ?type (COUNT(DISTINCT ?s) AS ?instances) (COUNT(DISTINCT ?g) AS ?graphs)
       (SAMPLE(?s) AS ?sampleEntity) (SAMPLE(?g) AS ?sampleGraph)
{from_named}
WHERE {{ GRAPH ?g {{ ?s a ?type }} }}
GROUP BY ?type ORDER BY DESC(?instances) LIMIT {TYPE_ROWS}
"""
    lines += ["", f"Entity types (top {TYPE_ROWS} by instances, SAMPLE() entity per type):",
              "| Type | Instances | Graphs | Sample entity |", "|---|---:|---:|---|"]
    for r in sparql_csv(endpoint, type_query):
        lines.append(f"| {curie(r.get('type', ''))} | {r.get('instances')} | "
                     f"{r.get('graphs')} | {curie(r.get('sampleEntity', ''))} |")
    if empty:
        lines.append(f"Zero-byte documents excluded (no graph by construction): {', '.join(empty)}")
    lines.append("Folder-level check only; run scripts/full-store-graph-gate.py for per-document sync.")
    return lines


def build_sparql_context():
    endpoint, endpoint_errors = first_working_endpoint()
    if not endpoint:
        return (
            "--- SPARQL bootstrap ---\n"
            "Status: unavailable; using filesystem fallback.\n"
            + "\n".join(f"  {e}" for e in endpoint_errors[-3:])
            + "\n\n",
            False,
        )

    try:
        graphs, graph_rows = discover_graphs(endpoint)
    except Exception as exc:
        return (
            "--- SPARQL bootstrap ---\n"
            f"Endpoint: {endpoint}\n"
            f"Status: graph discovery failed ({exc}); using filesystem fallback.\n\n",
            False,
        )

    required = ["ontology.ttl", "preferences.ttl", "index.ttl"]
    missing = [name for name in required if name not in graphs]
    if missing:
        return (
            "--- SPARQL bootstrap ---\n"
            f"Endpoint: {endpoint}\n"
            "Status: incomplete graph set; using filesystem fallback.\n"
            f"Missing required graphs: {', '.join(missing)}\n"
            "Discovered graphs:\n"
            + "".join(f"  {row.get('g')} ({row.get('count')} triples)\n" for row in graph_rows[:12])
            + "\n",
            False,
        )

    ontology_graph = graphs["ontology.ttl"]
    preferences_graph = graphs["preferences.ttl"]
    private_graph = graphs.get("preferences.private.ttl")
    index_graph = graphs["index.ttl"]
    onto_base = entity_base_from_graph(ontology_graph) + "#"
    pref_base = entity_base_from_graph(preferences_graph) + "#"

    sections = [
        "--- SPARQL bootstrap ---",
        f"Endpoint: {endpoint}",
        "Status: used SPARQL context pack; filesystem fallback not used for compact bootstrap.",
        "Discovered graph/entity pattern:",
        f"  ontology graph: {ontology_graph}",
        f"  ontology entity base: {onto_base}",
        f"  preferences graph: {preferences_graph}",
        f"  index graph: {index_graph}",
    ]
    if private_graph:
        sections.append(f"  private overlay graph: {private_graph}")

    # preferences.ttl Step 302: the SAMPLE() state tables are ELICITED, not mandatory.
    if os.environ.get("AGENT_RDF_MEMORY_STATE_TABLE", "").lower() in ("1", "yes", "true"):
        try:
            sections.extend(memory_state_table(endpoint))
        except Exception as exc:
            sections.append(f"\n--- Memory graph state ---\n  unavailable: {exc}")
    else:
        sections += [
            "\n--- Memory graph state (ELICIT, do not run unasked) ---",
            "Memory is driven from Virtuoso. In your FIRST response, ask the user whether to",
            "run the SAMPLE()-based memory-graph verification (per-folder, core-graph and",
            "entity-type tables). Only on a yes, run:",
            f"  python3 {os.path.join(BASE, 'load_memory.py')} --state-table",
            "and present its tables to the user. On a no, proceed without them.",
        ]

    # Intent routing summary.
    try:
        intent = subject_for(ontology_graph, "VirtuosoSparqlTroubleshooting")
        query = f"""
PREFIX onto: <{onto_base}>
PREFIX schema: <http://schema.org/>
SELECT ?topic ?howto ?optionalHowto ?policy ?source ?recentRequired
WHERE {{
  GRAPH <{ontology_graph}> {{
    VALUES ?intent {{ <{intent}> }}
    OPTIONAL {{ ?intent onto:routesToTopic ?topic }}
    OPTIONAL {{ ?intent onto:requiresHowTo ?howto }}
    OPTIONAL {{ ?intent onto:optionalHowTo ?optionalHowto }}
    OPTIONAL {{ ?intent onto:retrievalPolicy ?policy }}
    OPTIONAL {{ ?intent onto:preferredContextSource ?source }}
    OPTIONAL {{ ?intent onto:requiresRecentSession ?recentRequired }}
  }}
}}
ORDER BY ?topic ?howto ?optionalHowto ?source
"""
        rows = select_rows(endpoint, query, limit=24)
        sections.append("\n--- ontology.ttl (intent routing sample) ---")
        for row in rows:
            bits = []
            for key in ("topic", "howto", "optionalHowto", "policy", "source", "recentRequired"):
                if row.get(key):
                    bits.append(f"{key}={row[key]}")
            if bits:
                sections.append("  " + " | ".join(bits))
    except Exception as exc:
        sections.append(f"\nERROR ontology intent query: {exc}")

    # Preference step index.
    try:
        query = f"""
PREFIX schema: <http://schema.org/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?step ?pos ?name ?text ?seealso
WHERE {{
  GRAPH <{preferences_graph}> {{
    ?step a schema:HowToStep .
    OPTIONAL {{ ?step schema:position ?pos }}
    OPTIONAL {{ ?step schema:name ?name }}
    OPTIONAL {{ ?step schema:text ?text }}
    OPTIONAL {{ ?step rdfs:seeAlso ?seealso }}
  }}
}}
ORDER BY xsd:decimal(?pos)
LIMIT {MAX_STEPS}
"""
        rows = select_rows(endpoint, query)
        sections.append("\n--- preferences.ttl (SPARQL step index) ---")
        for row in rows:
            name = row.get("name", "")
            if not name:
                continue
            line = f"  • {name}"
            if row.get("seealso"):
                line += f"  → {row['seealso']}"
            if row.get("text"):
                excerpt = row["text"].splitlines()[0][:160]
                line += f"\n    └ {excerpt}"
            sections.append(line)
    except Exception as exc:
        sections.append(f"\nERROR preferences step query: {exc}")

    # Private overlay policy, if loaded.
    if private_graph:
        try:
            query = f"""
PREFIX onto: <{onto_base}>
PREFIX schema: <http://schema.org/>
SELECT ?intent ?policy ?policyName ?policyDesc
WHERE {{
  GRAPH <{private_graph}> {{
    ?intent onto:retrievalPolicy ?policy .
    OPTIONAL {{ ?policy schema:name ?policyName }}
    OPTIONAL {{ ?policy schema:description ?policyDesc }}
  }}
}}
ORDER BY ?intent ?policy
LIMIT 20
"""
            rows = select_rows(endpoint, query)
            sections.append("\n--- preferences.private.ttl (SPARQL overlay) ---")
            for row in rows:
                sections.append(
                    f"  • {row.get('intent')} → {row.get('policyName') or row.get('policy')}"
                )
        except Exception as exc:
            sections.append(f"\nERROR private overlay query: {exc}")

    # Recent sessions from index.
    latest_session_graph = None
    try:
        query = f"""
PREFIX schema: <http://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?item ?pos ?sessionDoc ?name ?desc
WHERE {{
  GRAPH <{index_graph}> {{
    ?item schema:position ?pos ;
          schema:item ?sessionDoc .
    OPTIONAL {{ ?item schema:name ?name }}
    OPTIONAL {{ ?item schema:description ?desc }}
  }}
}}
ORDER BY DESC(xsd:decimal(?pos))
LIMIT 5
"""
        rows = select_rows(endpoint, query)
        sections.append("\n--- index.ttl (SPARQL recent sessions/items) ---")
        for idx, row in enumerate(rows):
            if idx == 0 and row.get("sessionDoc"):
                latest_session_graph = session_graph_from_doc(row["sessionDoc"])
            label = row.get("name") or row.get("sessionDoc") or row.get("item")
            sections.append(f"  {row.get('pos', '')}: {label}")
    except Exception as exc:
        sections.append(f"\nERROR index query: {exc}")

    if latest_session_graph:
        try:
            query = f"""
PREFIX schema: <http://schema.org/>
SELECT ?s ?name ?desc
WHERE {{
  GRAPH <{latest_session_graph}> {{
    ?s a ?type .
    OPTIONAL {{ ?s schema:name ?name }}
    OPTIONAL {{ ?s schema:description ?desc }}
  }}
}}
LIMIT 12
"""
            rows = select_rows(endpoint, query)
            if rows:
                sections.append(f"\n--- latest session graph ({latest_session_graph}) ---")
                for row in rows:
                    label = row.get("name") or row.get("s")
                    desc = row.get("desc", "")
                    if desc:
                        desc = " — " + desc[:180]
                    sections.append(f"  • {label}{desc}")
        except Exception as exc:
            sections.append(f"\nERROR latest session query: {exc}")

    # Critical whoami text from graph when available; otherwise local fallback
    # below will be used only if SPARQL bootstrap is incomplete.
    agent_identity_graph = graphs.get("agent-identity.ttl")
    if agent_identity_graph:
        try:
            query = f"""
PREFIX schema: <http://schema.org/>
SELECT ?step ?name ?text
WHERE {{
  GRAPH <{agent_identity_graph}> {{
    ?step schema:name ?name ;
          schema:text ?text .
    FILTER(CONTAINS(LCASE(STR(?name)), "whoami") || CONTAINS(STR(?step), "whoamiFormat"))
  }}
}}
LIMIT 3
"""
            rows = select_rows(endpoint, query)
            if rows:
                sections.append("\n--- CRITICAL: whoami format (SPARQL) ---")
                for row in rows:
                    sections.append(row.get("text", "").strip())
        except Exception as exc:
            sections.append(f"\nERROR whoami SPARQL query: {exc}")

    return "\n".join(sections) + "\n\n", True


def append_filesystem_context(ctx):
    ctx += "--- filesystem fallback ---\n"

    # Critical whoami format spec.
    try:
        agent_id = open(os.path.join(BASE, "howto/agent-identity.ttl")).read()
        m = re.search(
            r":step-whoamiFormat.*?schema:text\s+\"\"\"(.*?)\"\"\"\s*@en",
            agent_id,
            re.DOTALL,
        )
        if m:
            ctx += (
                "--- CRITICAL: whoami format (howto/agent-identity.ttl) ---\n"
                + m.group(1).strip()
                + "\n\n"
            )
    except Exception as e:
        ctx += f"ERROR howto/agent-identity.ttl: {e}\n\n"

    try:
        raw = open(os.path.join(BASE, "core.ttl")).read()
        ctx += "--- core.ttl ---\n" + strip_comments(raw) + "\n"
    except Exception as e:
        ctx += f"ERROR core.ttl: {e}\n"

    try:
        prefs = open(os.path.join(BASE, "preferences.ttl")).read()
        steps = []
        for m in re.finditer(r":(step-\w+)\s+a\s+schema:HowToStep[^.]+\.", prefs, re.DOTALL):
            block = m.group(0)
            step_id = m.group(1)
            pos = re.search(r"schema:position\s+([\d.]+)", block)
            name = re.search(r"schema:name\s+\"([^\"]+)\"@en", block)
            seealso = re.search(r"rdfs:seeAlso\s+<([^>]+)>", block)
            if pos and name:
                steps.append((float(pos.group(1)), name.group(1), seealso.group(1) if seealso else "", step_id))

        text_map = {}
        for m in re.finditer(
            r":(step-\w+)\s+a\s+schema:HowToStep\s*;"
            r"(?:(?!:step-).)*?"
            r"schema:text\s+(\"\"\"|\")(.*?)\2\s*@en",
            prefs,
            re.DOTALL,
        ):
            step_id = m.group(1)
            first_line = m.group(3).strip().split("\n")[0].strip()
            if len(first_line) > 160:
                first_line = first_line[:157] + "..."
            text_map[step_id] = first_line

        ctx += "\n--- preferences.ttl (step index) ---\n"
        for _, name, ref, step_id in sorted(steps, key=lambda x: x[0]):
            line = f"  * {name}"
            if ref:
                line += f"  -> {ref}"
            if step_id in text_map:
                line += f"\n    - {text_map[step_id]}"
            ctx += line + "\n"
    except Exception as e:
        ctx += f"ERROR preferences.ttl: {e}\n"

    private_path = os.path.join(BASE, "preferences.private.ttl")
    if os.path.exists(private_path):
        try:
            raw = open(private_path).read()
            ctx += "\n--- preferences.private.ttl (local overlay present) ---\n"
            for line in strip_comments(raw).splitlines()[:80]:
                ctx += line + "\n"
        except Exception as e:
            ctx += f"ERROR preferences.private.ttl: {e}\n"

    try:
        idx = open(os.path.join(BASE, "index.ttl")).read()
        names = re.findall(r"schema:name\s+\"([^\"]+)\"@en", idx)
        ctx += "\n--- index.ttl (last 3 sessions) ---\n"
        for n in names[-3:]:
            ctx += f"  {n}\n"
    except Exception as e:
        ctx += f"ERROR index.ttl: {e}\n"

    sessions = sorted(glob.glob(os.path.join(BASE, "sessions", "*.ttl")))
    if sessions:
        fname = os.path.basename(sessions[-1])
        try:
            content = open(sessions[-1]).read()
            if len(content) > MAX_SESSION:
                content = content[:MAX_SESSION] + f"\n... [truncated - full file: sessions/{fname}]\n"
            ctx += f"\n--- sessions/{fname} ---\n" + content
        except Exception as e:
            ctx += f"ERROR {fname}: {e}\n"
    return ctx


if "--state-table" in sys.argv:
    # On-demand mode (the user said yes to the elicitation): print only the tables.
    _endpoint, _errors = first_working_endpoint()
    if not _endpoint:
        print("Memory graph state unavailable; no authenticated endpoint:")
        print("\n".join(f"  {e}" for e in _errors))
        sys.exit(3)
    print("\n".join(memory_state_table(_endpoint)).lstrip("\n"))
    sys.exit(0)

ctx = (
    "╔══════════════════════════════════════════════════════════════════╗\n"
    "║  GATE - MUST EXECUTE BEFORE ANY RESPONSE                       ║\n"
    "╠══════════════════════════════════════════════════════════════════╣\n"
    "║  This compact injection is a SAFETY NET, not a replacement.     ║\n"
    "║  You MUST still execute the full Agent RDF Memory Protocol:     ║\n"
    "║    (1) ls agent-rdf-memory/ and all subfolders                  ║\n"
    "║    (2) Read agent-rdf-memory/core.ttl                           ║\n"
    "║    (3) Read public preferences.ttl                              ║\n"
    "║    (4) Read preferences.private.ttl if present                  ║\n"
    "║    (5) Read ontology.ttl and index.ttl                          ║\n"
    "║    (6) Follow refs to relevant howto/*.ttl and sessions         ║\n"
    "║  SPARQL bootstrap is preferred; filesystem reads are fallback.  ║\n"
    "╚══════════════════════════════════════════════════════════════════╝\n\n"
    "=== AGENT RDF MEMORY (compact) ===\n\n"
    "WRITE RULE: All behavioral rules and preferences MUST be written to "
    "agent-rdf-memory/ as valid Turtle (new schema:HowToStep in preferences.ttl "
    "+ companion howto/<topic>.ttl). "
    "The flat markdown store at .claude/projects/.../memory/ is a SECONDARY INDEX "
    "only - never the primary or sole write target for behavioral rules.\n\n"
)

sparql_context, sparql_ok = build_sparql_context()
ctx += sparql_context
if not sparql_ok:
    ctx = append_filesystem_context(ctx)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": ctx,
    }
}))
