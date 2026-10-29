#!/usr/bin/env python3
"""
YouID did:nostr Link Consistency Gate (generate_identity.sh Step 7).

Checks, across all four representations of a generated WebID bundle —
profile.ttl, profile.jsonld, profile_rdfa.html (embedded JSON-LD + RDFa) and
index.html (embedded JSON-LD + embedded Turtle + RDFa) — that:

  1. the did:nostr identifier is a valid secp256k1 x-only key (on the curve)
  2. the Multikey publicKeyMultibase == 'fe70102' + the DID's hex key
  3. the npub (schema:identifier) bech32-decodes to the same hex key
  4. the WebID → DID relation is present, is the EXPECTED one for the mode
     (same → owl:sameAs, agent → oplcert:hasIdentityDelegate) and the other
     relation is absent
  5. all of the above agree across every representation

Usage: nostr_link_gate.py <out_dir> <webid> <did:nostr:...> <same|agent>
Exit 0 = pass, 1 = fail.
"""

import json
import os
import re
import sys

import rdflib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nostr_crypto import normalize  # noqa: E402

SEC = "https://w3id.org/security#"
OWL_SAMEAS = "http://www.w3.org/2002/07/owl#sameAs"
OPL_DELEGATE = "http://www.openlinksw.com/schemas/cert#hasIdentityDelegate"
SCHEMA_ID = "http://schema.org/identifier"
BASE = "urn:youid:gate-base"


def facts_from_graph(g, webid, did):
    W, D = rdflib.URIRef(webid), rdflib.URIRef(did)
    mb = {str(o) for vm in g.objects(D, rdflib.URIRef(SEC + "verificationMethod"))
          for o in g.objects(vm, rdflib.URIRef(SEC + "publicKeyMultibase"))}
    return {
        "sameAs": (W, rdflib.URIRef(OWL_SAMEAS), D) in g,
        "delegate": (W, rdflib.URIRef(OPL_DELEGATE), D) in g,
        "multibase": mb,
        "npub": {str(o) for o in g.objects(D, rdflib.URIRef(SCHEMA_ID))},
    }


def merge(a, b):
    if a is None:
        return b
    return {"sameAs": a["sameAs"] or b["sameAs"], "delegate": a["delegate"] or b["delegate"],
            "multibase": a["multibase"] | b["multibase"], "npub": a["npub"] | b["npub"]}


def html_graph(content, fmt_blocks):
    """Parse embedded <script> blocks + RDFa into one graph."""
    g = rdflib.Graph()
    for mime, fmt in fmt_blocks:
        for m in re.finditer(r'<script[^>]*type="%s"[^>]*>(.*?)</script>' % re.escape(mime), content, re.S):
            try:
                g.parse(data=m.group(1), format=fmt, publicID=BASE)
            except Exception as e:  # malformed block = gate failure, reported by caller
                raise ValueError(f"embedded {mime} block does not parse: {e}")
    return g


def rdfa_facts(content, webid, did):
    """Minimal RDFa reader for the prof_rdfa.tpl nostr block (rdflib has no RDFa parser)."""
    f = {"sameAs": False, "delegate": False, "multibase": set(), "npub": set()}
    for m in re.finditer(r'<div about="([^"]+)"><div rel="([^"]+)" resource="([^"]+)"></div></div>', content):
        if m.group(1) == webid and m.group(3) == did:
            f["sameAs"] |= m.group(2) == "owl:sameAs"
            f["delegate"] |= m.group(2) == "oplcert:hasIdentityDelegate"
    blk = re.search(r'<div typeof="rdfs:Resource" about="%s">(.*?)</div>\s*</div>\s*</div>\s*</div>'
                    % re.escape(did), content, re.S)
    if blk:
        f["npub"] |= set(re.findall(r'property="schema:identifier" content="([^"]+)"', blk.group(1)))
        f["multibase"] |= set(re.findall(r'property="sec:publicKeyMultibase"[^>]*content="([^"]+)"', blk.group(1)))
    return f


def main(out_dir, webid, did, mode):
    info = normalize(did)
    fail = False

    def check(ok, msg):
        nonlocal fail
        print(f"  {'✓' if ok else '✗'} {msg}")
        fail |= not ok

    check(info["valid"], f"{did[:28]}… is a valid secp256k1 x-only key")
    expect_mb, expect_npub = info["multibase"], info["npub"]

    files = {}
    g = rdflib.Graph()
    g.parse(os.path.join(out_dir, "profile.ttl"), format="turtle")
    files["profile.ttl"] = facts_from_graph(g, webid, did)

    g = rdflib.Graph()
    g.parse(os.path.join(out_dir, "profile.jsonld"), format="json-ld")
    files["profile.jsonld"] = facts_from_graph(g, webid, did)

    for name, blocks in (("profile_rdfa.html", [("application/ld+json", "json-ld")]),
                         ("index.html", [("application/ld+json", "json-ld"), ("text/turtle", "turtle")])):
        with open(os.path.join(out_dir, name)) as fh:
            content = fh.read()
        facts = facts_from_graph(html_graph(content, blocks), webid, did)
        facts = merge(facts, rdfa_facts(content, webid, did))
        files[name] = facts
        # the RDFa layer on its own must also carry the link (it is what RDFa-only consumers see)
        r = rdfa_facts(content, webid, did)
        check(r["sameAs"] if mode == "same" else r["delegate"], f"{name}: RDFa layer carries the {mode} link")

    for name, f in files.items():
        if mode == "same":
            check(f["sameAs"], f"{name}: <WebID> owl:sameAs <{did[:24]}…>")
            check(not f["delegate"], f"{name}: no hasIdentityDelegate (mode=same)")
        else:
            check(f["delegate"], f"{name}: <WebID> oplcert:hasIdentityDelegate <{did[:24]}…>")
            check(not f["sameAs"], f"{name}: no owl:sameAs to the agent DID (mode=agent)")
        check(f["multibase"] == {expect_mb}, f"{name}: publicKeyMultibase == fe70102+hex")
        check(f["npub"] == {expect_npub}, f"{name}: npub decodes to the DID key")

    return 1 if fail else 0


if __name__ == "__main__":
    if len(sys.argv) != 5 or sys.argv[4] not in ("same", "agent"):
        print(__doc__)
        sys.exit(2)
    sys.exit(main(*sys.argv[1:]))
