#!/usr/bin/env python3
"""
DRAFT FOR REVIEW - not wired into any hook. Prototype of a slimmed SessionStart
injection plus an on-demand intent pack for agent-rdf-memory.

Every section is the result of a SPARQL query against the designated memory
store. The query text is the same for both store kinds; only the graph base
differs:

  filesystem   the local Turtle files, loaded into an rdflib Dataset whose named
               graphs mirror the endpoint's (one graph per file). Implemented here.
  endpoint     the same queries with the graph base bound to the endpoint's
               (urn:dav:/DAV/home/<user>/agent-rdf-memory/), run through
               load_memory.py's existing authenticated sparql_csv(). NOT run by
               this prototype: it never touches credentials. Use --print-queries
               to get the endpoint-ready text.

Usage:
  slim_injection.py                         session-start index (filesystem)
  slim_injection.py --intent KgExplorerTask on-demand pack for one intent
  slim_injection.py --llm-id claude_fable_5_2   scope recent sessions to a model
  slim_injection.py --print-queries --graph-base urn:dav:/DAV/home/kidehen/agent-rdf-memory/
"""
import argparse
import pathlib
import sys

STORE = pathlib.Path(__file__).resolve().parent.parent
CORE_GRAPHS = ["ontology.ttl", "preferences.ttl", "index.ttl"]

# Steps injected at every session start, whatever the prompt. This list is a
# reviewer decision, hand-picked here from existing step IRIs in preferences.ttl.
# A marker triple on the step would replace it (see the draft notes).
ALWAYS_ON = [
    "step-approval",
    "step-noFabricatedUrls",
    "step-gitWorkflow",
    "step-noUnauthorizedDeletion",
    "step-secretRedaction",
    "step-modelIdentityPreflight",
    "step-memoryProtocol",
    "step-promptRecording",
]

PREFIXES = """PREFIX onto: <{GB}ontology.ttl#>
PREFIX pref: <{GB}preferences.ttl#>
PREFIX schema: <http://schema.org/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

QUERIES = {
    # Q1: the always-on steps, by IRI.
    "always_on": """
SELECT ?step ?name (SAMPLE(?doc) AS ?howto)
WHERE {{
  GRAPH <{GB}preferences.ttl> {{
    VALUES ?step {{ {STEPS} }}
    ?step schema:name ?name .
    OPTIONAL {{ ?step rdfs:seeAlso ?doc }}
  }}
}}
GROUP BY ?step ?name
""",
    # Q2: routing table. One row per topic howto, with its step count and the
    # intent (if any) that routes to its topic.
    "topics": """
SELECT ?howto ?name (COUNT(DISTINCT ?step) AS ?steps) (SAMPLE(?i) AS ?intent)
WHERE {{
  GRAPH <{GB}preferences.ttl> {{
    pref:agentBehaviorGuide schema:hasPart ?howto .
    OPTIONAL {{ ?howto schema:name ?name }}
    OPTIONAL {{ ?howto schema:step ?step }}
  }}
  OPTIONAL {{
    GRAPH <{GB}ontology.ttl> {{ ?i onto:routesToTopic ?topic }}
    FILTER(STRAFTER(STR(?topic), "#topic-") = STRAFTER(STR(?howto), "#howto-"))
  }}
}}
GROUP BY ?howto ?name
ORDER BY DESC(?steps)
""",
    # Q3: trigger phrases per intent, for classifying the first prompt.
    "phrases": """
SELECT ?intent (GROUP_CONCAT(DISTINCT ?p; separator=", ") AS ?phrases)
WHERE {{
  GRAPH <{GB}ontology.ttl> {{ ?intent onto:routesToTopic ?t ; onto:triggerPhrase ?p }}
}}
GROUP BY ?intent
ORDER BY ?intent
""",
    # Q4: most recent sessions from the index. {LLM} narrows to one model's files.
    "recent": """
SELECT ?pos ?doc ?name
WHERE {{
  GRAPH <{GB}index.ttl> {{
    ?item schema:position ?pos ; schema:item ?doc .
    OPTIONAL {{ ?item schema:name ?name }}
    FILTER(CONTAINS(STR(?doc), "{LLM}"))
  }}
}}
ORDER BY DESC(xsd:decimal(?pos))
LIMIT 3
""",
    # Q5: step totals, to show how much the index leaves out.
    "totals": """
SELECT (COUNT(DISTINCT ?s) AS ?all) (COUNT(DISTINCT ?routed) AS ?reachable)
WHERE {{
  GRAPH <{GB}preferences.ttl> {{
    ?s a schema:HowToStep .
    OPTIONAL {{ ?h schema:step ?s . BIND(?s AS ?routed) }}
  }}
}}
""",
    # Q6: on-demand pack, part 1. The steps of the topic the intent routes to,
    # plus the howtos the intent itself requires.
    "pack_topic": """
SELECT ?step ?pos ?name (SAMPLE(?doc) AS ?howto)
WHERE {{
  GRAPH <{GB}ontology.ttl> {{ onto:{INTENT} onto:routesToTopic ?topic }}
  BIND(IRI(REPLACE(STR(?topic), "#topic-", "#howto-")) AS ?h)
  GRAPH <{GB}preferences.ttl> {{
    ?h schema:step ?step .
    ?step schema:name ?name .
    OPTIONAL {{ ?step schema:position ?pos }}
    OPTIONAL {{ ?step rdfs:seeAlso ?doc }}
  }}
}}
GROUP BY ?step ?pos ?name
ORDER BY xsd:decimal(?pos)
""",
    "pack_required": """
SELECT ?kind ?doc
WHERE {{
  GRAPH <{GB}ontology.ttl> {{
    {{ onto:{INTENT} onto:requiresHowTo ?doc . BIND("required" AS ?kind) }}
    UNION
    {{ onto:{INTENT} onto:optionalHowTo ?doc . BIND("optional" AS ?kind) }}
  }}
}}
ORDER BY ?kind ?doc
""",
    # Q7: on-demand pack, part 2. Steps attached to no topic howto, matched on
    # the intent's trigger phrases. A stopgap until those steps are assigned.
    "pack_unrouted": """
SELECT ?step ?pos ?name (SAMPLE(?doc) AS ?howto)
WHERE {{
  GRAPH <{GB}ontology.ttl> {{ onto:{INTENT} onto:triggerPhrase ?p }}
  GRAPH <{GB}preferences.ttl> {{
    ?step a schema:HowToStep ; schema:name ?name .
    FILTER NOT EXISTS {{ ?any schema:step ?step }}
    FILTER(CONTAINS(LCASE(STR(?name)), LCASE(STR(?p))))
    OPTIONAL {{ ?step schema:position ?pos }}
    OPTIONAL {{ ?step rdfs:seeAlso ?doc }}
  }}
}}
GROUP BY ?step ?pos ?name
ORDER BY xsd:decimal(?pos)
""",
}


def render(name, gb, **kw):
    body = QUERIES[name].format(GB=gb, **kw)
    return PREFIXES.format(GB=gb) + body


def load_filesystem():
    from rdflib import Dataset, URIRef
    gb = STORE.as_uri() + "/"
    ds = Dataset()
    for f in CORE_GRAPHS:
        ds.graph(URIRef(gb + f)).parse(str(STORE / f), format="turtle", publicID=gb + f)
    return ds, gb


def short(value, gb):
    """Compress a store IRI to a mem: CURIE so no base IRI is repeated."""
    return "" if value is None else str(value).replace(gb, "mem:")


def session_index(ds, gb, llm_id):
    q = lambda n, **kw: list(ds.query(render(n, gb, **kw)))
    out = ["=== AGENT RDF MEMORY: session index ===", ""]
    out += [
        "Purpose: memory exists so a corrected mistake is not repeated and so work",
        "resumes where the last session stopped. Load what this prompt needs.",
        "",
        "Store: filesystem  " + str(STORE),
        "  mem: = the store's graph base (one named graph per file)",
        "",
        "Before acting on the first prompt:",
        "  1. Match the prompt to an intent below (trigger hints).",
        "  2. Pull that intent's pack:  slim_injection.py --intent <Intent>",
        "  3. Read the howto a matching step links to before doing what it governs.",
        "",
        "Always on:",
    ]
    steps = " ".join("pref:" + s for s in ALWAYS_ON)
    rows = {short(r.step, gb): r for r in q("always_on", STEPS=steps)}
    for s in ALWAYS_ON:
        r = rows.get("mem:preferences.ttl#" + s)
        if r:
            out.append(f"  - {r.name}  [{short(r.howto, gb)}]")
    phrases = {short(r.intent, gb).split("#")[-1]: str(r.phrases) for r in q("phrases")}
    out += ["", "Topics (steps | intent | trigger hints):"]
    for r in q("topics"):
        topic = short(r.howto, gb).split("#howto-")[-1]
        intent = short(r.intent, gb).split("#")[-1] if r.intent else "(no intent defined)"
        hints = phrases.get(intent, "")
        out.append(f"  - {topic}: {r.steps} | {intent}" + (f" | {hints}" if hints else ""))
    tot = q("totals")[0]
    out += [
        "",
        f"Steps: {tot.all} in preferences.ttl, {tot.reachable} attached to a topic. The other",
        f"{int(tot.all) - int(tot.reachable)} are matched to an intent by trigger phrase only.",
        "",
        "Recent sessions" + (f" ({llm_id})" if llm_id else "") + ":",
    ]
    for r in q("recent", LLM=llm_id or ""):
        out.append(f"  - {r.pos}: {str(r.name)[:110]}  [{short(r.doc, gb)}]")
    out += [
        "",
        "Identity question (whoami, who are you): read mem:howto/agent-identity.ttl first.",
        "Memory-graph state tables: ask before running load_memory.py --state-table.",
        "Write rule: behavioural rules go to preferences.ttl plus howto/<topic>.ttl.",
    ]
    return "\n".join(out) + "\n"


def intent_pack(ds, gb, intent):
    q = lambda n: list(ds.query(render(n, gb, INTENT=intent)))
    out = [f"=== AGENT RDF MEMORY: pack for {intent} ===", ""]
    req = q("pack_required")
    if req:
        out.append("Howtos named by the intent:")
        out += [f"  - {r.kind}: {short(r.doc, gb)}" for r in req]
        out.append("")
    routed = q("pack_topic")
    out.append(f"Topic steps ({len(routed)}):")
    out += [f"  - [{r.pos}] {r.name}  [{short(r.howto, gb)}]" for r in routed]
    loose = q("pack_unrouted")
    out += ["", f"Unrouted steps matched on trigger phrases ({len(loose)}):"]
    out += [f"  - [{r.pos}] {r.name}  [{short(r.howto, gb)}]" for r in loose]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--intent")
    ap.add_argument("--llm-id", default="")
    ap.add_argument("--print-queries", action="store_true")
    ap.add_argument("--graph-base")
    a = ap.parse_args()
    if a.print_queries:
        gb = a.graph_base or (STORE.as_uri() + "/")
        fill = dict(STEPS=" ".join("pref:" + s for s in ALWAYS_ON),
                    LLM=a.llm_id, INTENT=a.intent or "KgExplorerTask")
        for name in QUERIES:
            print(f"# ---- {name} ----")
            print(render(name, gb, **fill))
        return
    ds, gb = load_filesystem()
    text = intent_pack(ds, gb, a.intent) if a.intent else session_index(ds, gb, a.llm_id)
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
