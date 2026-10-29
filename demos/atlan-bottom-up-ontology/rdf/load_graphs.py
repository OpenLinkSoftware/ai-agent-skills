#!/usr/bin/env python3
import subprocess, urllib.request, urllib.error, urllib.parse, ssl, base64
from pathlib import Path

BASE = Path("/Users/kidehen/Documents/Management/Development/ai-agent-skills/demos/atlan-bottom-up-ontology")
ISQL = "/Applications/Virtuoso 8.3.app/Contents/virtuoso/bin/isql"
SQL_PW = subprocess.check_output(
    ["/usr/bin/security", "find-generic-password", "-s", "uriburner-isql", "-a", "kidehen", "-w"],
    text=True,
).rstrip("\n")
ABOX = BASE / "rdf" / "abox-from-sql.ttl"
ONT = BASE / "ontology" / "atlan-cc.ttl"
G = "http://localhost:8890/atlan-cc#"
GO = "http://localhost:8890/schemas/atlan-cc/"


def http_put(url, data, content_type, user=None, password=None):
    req = urllib.request.Request(url, data=data, method="PUT")
    req.add_header("Content-Type", content_type)
    if user:
        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        req.add_header("Authorization", "Basic " + token)
    ctx = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            return r.status, r.read()[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:400]
    except Exception as e:
        return -1, str(e).encode()


abox = ABOX.read_bytes()
ont = ONT.read_bytes()
for path in ["/sparql-graph-crud-auth", "/sparql-graph-crud"]:
    url = f"http://localhost:8890{path}?graph-uri=" + urllib.parse.quote(G, safe="")
    code, body = http_put(url, abox, "text/turtle", "kidehen", SQL_PW)
    print("PUT", path, "abox", code, body[:200])

url = f"http://localhost:8890/sparql-graph-crud-auth?graph-uri=" + urllib.parse.quote(GO, safe="")
code, body = http_put(url, ont, "text/turtle", "kidehen", SQL_PW)
print("PUT ont", code, body[:200])

script = f"""SPARQL CLEAR GRAPH <{G}>;
SPARQL LOAD <file://{ABOX}> INTO GRAPH <{G}>;
SPARQL LOAD <file://{ONT}> INTO GRAPH <{GO}>;
SPARQL SELECT (COUNT(*) AS ?c) WHERE {{ GRAPH <{G}> {{ ?s ?p ?o }} }};
"""
r = subprocess.run([ISQL, "localhost:1111", "kidehen", SQL_PW], input=script, text=True, capture_output=True)
print("ISQL OUT:\n", r.stdout[-2500:])
print("ISQL ERR:\n", r.stderr[-500:])
