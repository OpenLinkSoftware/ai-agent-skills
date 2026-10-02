#!/usr/bin/env python3
"""
YouID identity resolver + link verifier for WebID ⇄ did:nostr.

Subcommands
-----------
  resolve <identifier> [--http-base URL | --domain HOST] [--relay wss://…]... [--json]
      did:nostr:… / npub1… / hex → DID document, using the did:nostr spec's strategy:
        1. HTTP resolution  https://<domain>/.well-known/did/nostr/<hex>.json   (--domain / --http-base)
        2. Offline minimal resolution from the key alone                         (always available)
        3. Enhanced resolution from relays: kind 0 profile, kind 3 follows,
           kind 10002 relay list — every event's id + BIP-340 signature is
           verified before use                                                   (--relay)
      http(s) WebID → fetched with content negotiation (Turtle / JSON-LD) and parsed.

  link <webid> <did:nostr:…> [--http-base URL | --domain HOST | --did-doc FILE] [--relay wss://…]...
      Two-sided verification. VERIFIED only when BOTH hold:
        WebID side: <webid> owl:sameAs <did>                    (mode same)
                or  <webid> oplcert:hasIdentityDelegate <did>   (mode agent)
                and the published Multikey == fe70102 + DID hex
        DID side:   alsoKnownAs ∋ webid   (same)  — DID document and/or signed kind 0
                or  oplcert:onBehalfOf = webid (agent)
      A signed kind 0 attestation counts as the strongest DID-side evidence (spec).

  prove <did:nostr:…> --key git:<dir> | keychain:<npub> | p12:<file>   [--http-base URL] [--relay …]
      Proof of control: signs a fresh random challenge (BIP-340) with the secret
      taken from the chosen custody option and verifies it against the key in the
      RESOLVED DID document. The secret is never printed. For p12 the password is
      read from env YOUID_P12_PASS.

Exit codes: 0 = pass/verified, 1 = failed/not verified, 2 = usage.
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request

import rdflib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nostr_crypto as nc  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OWL_SAMEAS = rdflib.URIRef("http://www.w3.org/2002/07/owl#sameAs")
OPL_DELEGATE = rdflib.URIRef("http://www.openlinksw.com/schemas/cert#hasIdentityDelegate")
SEC_VM = rdflib.URIRef("https://w3id.org/security#verificationMethod")
SEC_MB = rdflib.URIRef("https://w3id.org/security#publicKeyMultibase")
ACCEPT = "text/turtle, application/ld+json;q=0.9, application/rdf+xml;q=0.5"


def log(msg):
    print(msg, file=sys.stderr)


def http_get(url, accept):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "youid-resolver/1.2"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8"), r.headers.get("Content-Type", "")


# ── did:nostr resolution ────────────────────────────────────────────────────
def relay_query(relay, hexkey):
    out = subprocess.run(["node", os.path.join(HERE, "nostr_relay.mjs"), "query", relay, hexkey],
                         capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        err = [l for l in out.stderr.splitlines() if l.strip() and "trust settings" not in l]
        raise RuntimeError(err[-1] if err else f"exit {out.returncode}")
    return json.loads(out.stdout)


def resolve_nostr(identifier, http_base=None, domain=None, relays=(), did_doc_file=None):
    info = nc.normalize(identifier)
    hexkey, did = info["hex"], info["did"]
    trail = {"did": did, "npub": info["npub"], "valid_point": info["valid"], "methods": []}
    if not info["valid"]:
        raise ValueError(f"{did} is not a valid secp256k1 x-only key")

    doc = None
    if did_doc_file:
        with open(did_doc_file) as f:
            doc = json.load(f)
        trail["methods"].append(f"file:{did_doc_file}")
    elif http_base or domain:
        base = (http_base or f"https://{domain}").rstrip("/")
        url = f"{base}/.well-known/did/nostr/{hexkey}.json"
        body, ctype = http_get(url, "application/did+json, application/did+ld+json, application/json")
        doc = json.loads(body)
        trail["methods"].append(f"http:{url} ({ctype})")
    if doc is None:
        doc = nc.minimal_did_document(hexkey)
        trail["methods"].append("offline-minimal")

    # Integrity: whatever we fetched must describe THIS key
    if doc.get("id") != did:
        raise ValueError(f"DID document id {doc.get('id')} != {did}")
    mbs = {vm.get("publicKeyMultibase") for vm in doc.get("verificationMethod", [])}
    if info["multibase"] not in mbs:
        raise ValueError("DID document does not carry the key's publicKeyMultibase")

    signed_aka = []
    for relay in relays:
        try:
            events = relay_query(relay, hexkey)
        except Exception as e:  # relay enhancement is OPTIONAL per spec — degrade, don't fail
            trail["methods"].append(f"relay:{relay} (unreachable: {e})")
            continue
        good = [e for e in events if e.get("pubkey") == hexkey and nc.verify_event(e)]
        bad = len(events) - len(good)
        trail["methods"].append(f"relay:{relay} ({len(good)} verified event(s){f', {bad} REJECTED' if bad else ''})")
        latest = {}
        for e in good:
            if e["kind"] not in latest or e["created_at"] > latest[e["kind"]]["created_at"]:
                latest[e["kind"]] = e
        if 0 in latest:
            prof = json.loads(latest[0]["content"] or "{}")
            aka = prof.pop("alsoKnownAs", [])
            signed_aka += aka
            prof["created_at"] = latest[0]["created_at"]
            doc["profile"] = prof
        if 10002 in latest:
            svc = [s for s in doc.get("service", []) if s.get("type") != "Relay"]
            rs = [t[1] for t in latest[10002]["tags"] if t and t[0] == "r"]
            for i, r in enumerate(rs, 1):
                svc.append({"id": f"{did}#relay{i}", "type": "Relay", "serviceEndpoint": r})
            doc["service"] = svc
        if 3 in latest:
            doc["follows"] = [f"did:nostr:{t[1]}" for t in latest[3]["tags"] if t and t[0] == "p"]
    if signed_aka:
        doc["alsoKnownAs"] = sorted(set(doc.get("alsoKnownAs", [])) | set(signed_aka))
    trail["signed_alsoKnownAs"] = sorted(set(signed_aka))
    return doc, trail


# ── WebID side ──────────────────────────────────────────────────────────────
def load_webid(webid):
    doc_url = webid.split("#")[0]
    body, ctype = http_get(doc_url, ACCEPT)
    fmt = "json-ld" if "json" in ctype else "xml" if "rdf+xml" in ctype else "turtle"
    g = rdflib.Graph()
    g.parse(data=body, format=fmt, publicID=doc_url)
    return g, ctype


def webid_side(webid, did):
    g, ctype = load_webid(webid)
    W, D = rdflib.URIRef(webid), rdflib.URIRef(did)
    mbs = {str(o) for vm in g.objects(D, SEC_VM) for o in g.objects(vm, SEC_MB)}
    return {"content_type": ctype, "sameAs": (W, OWL_SAMEAS, D) in g,
            "delegate": (W, OPL_DELEGATE, D) in g, "multibase": sorted(mbs), "triples": len(g)}


# ── key custody sources (for `prove`) ───────────────────────────────────────
def secret_from(source):
    kind, _, ref = source.partition(":")
    if kind == "git":
        return subprocess.run(["git", "-C", ref, "config", "--local", "nostr.privkey"],
                              capture_output=True, text=True, check=True).stdout.strip()
    if kind == "keychain":
        return subprocess.run(["security", "find-generic-password", "-s", "youid-nostr", "-a", ref, "-w"],
                              capture_output=True, text=True, check=True).stdout.strip()
    if kind == "p12":
        if "YOUID_P12_PASS" not in os.environ:
            raise SystemExit("set YOUID_P12_PASS for p12: key sources")
        pem = subprocess.run(["openssl", "pkcs12", "-in", ref, "-nocerts", "-nodes", "-passin", "env:YOUID_P12_PASS"],
                             capture_output=True, check=True).stdout
        der = subprocess.run(["openssl", "ec", "-outform", "DER"], input=pem,
                             capture_output=True, check=True).stdout
        # SEC1 ECPrivateKey: 30 len 02 01 01 04 20 <32-byte secret> …
        if der[2:7] != bytes.fromhex("0201010420"):
            raise ValueError("unexpected SEC1 DER layout")
        return der[7:39].hex()
    raise SystemExit(f"unknown key source {source} (git:<dir> | keychain:<npub> | p12:<file>)")


# ── commands ────────────────────────────────────────────────────────────────
def cmd_resolve(a):
    if a.identifier.startswith(("http://", "https://")):
        g, ctype = load_webid(a.identifier)
        W = rdflib.URIRef(a.identifier)
        print(f"WebID {a.identifier}  ({ctype}, {len(g)} triples)")
        for p, label in ((OWL_SAMEAS, "owl:sameAs"), (OPL_DELEGATE, "oplcert:hasIdentityDelegate")):
            for o in sorted(g.objects(W, p)):
                print(f"  {label} → {o}")
        return 0
    doc, trail = resolve_nostr(a.identifier, a.http_base, a.domain, a.relay, a.did_doc)
    if a.json:
        print(json.dumps(doc, indent=2))
    else:
        print(f"{trail['did']}\n  npub:    {trail['npub']}\n  on-curve key: {trail['valid_point']}")
        for m in trail["methods"]:
            print(f"  via {m}")
        for k in ("alsoKnownAs", "service", "profile"):
            if k in doc:
                print(f"  {k}: {json.dumps(doc[k])}")
        if trail["signed_alsoKnownAs"]:
            print(f"  signed (kind 0) alsoKnownAs: {trail['signed_alsoKnownAs']}")
    return 0


def cmd_link(a):
    did = nc.normalize(a.did)["did"]
    expect_mb = nc.normalize(a.did)["multibase"]
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(f"  {'✓' if cond else '✗'} {msg}")
        ok &= bool(cond)

    print(f"WebID side — {a.webid}")
    w = webid_side(a.webid, did)
    mode = "same" if w["sameAs"] else "agent" if w["delegate"] else None
    check(mode is not None, f"WebID asserts a relation to {did[:30]}… "
                            f"({'owl:sameAs' if mode == 'same' else 'oplcert:hasIdentityDelegate' if mode else 'none'})")
    check(not (w["sameAs"] and w["delegate"]), "exactly one relation (not both sameAs and delegate)")
    check(w["multibase"] == [expect_mb], "WebID-published Multikey == fe70102 + DID hex")

    print(f"DID side — {did}")
    doc, trail = resolve_nostr(did, a.http_base, a.domain, a.relay, a.did_doc)
    for m in trail["methods"]:
        print(f"    resolved via {m}")
    if mode == "same":
        check(a.webid in doc.get("alsoKnownAs", []), "DID alsoKnownAs includes the WebID (reciprocal)")
        if a.relay:
            check(a.webid in trail["signed_alsoKnownAs"],
                  "reciprocal claim is signed by the DID key (kind 0 alsoKnownAs)")
    elif mode == "agent":
        obo = doc.get(nc.OPL_ON_BEHALF_OF, {})
        check((obo.get("@id") if isinstance(obo, dict) else obo) == a.webid,
              "DID oplcert:onBehalfOf = the WebID (reciprocal)")
        check(a.webid not in doc.get("alsoKnownAs", []), "agent DID does not claim to BE the WebID")
    print(f"\nLINK {'VERIFIED' if ok else 'NOT VERIFIED'} ({mode or 'no relation'})")
    return 0 if ok else 1


def cmd_prove(a):
    doc, trail = resolve_nostr(a.did, a.http_base, a.domain, a.relay, a.did_doc)
    mb = doc["verificationMethod"][0]["publicKeyMultibase"]
    if not mb.startswith(nc.MULTIBASE_PREFIX):
        raise ValueError(f"unsupported multibase {mb[:8]}")
    pub = mb[len(nc.MULTIBASE_PREFIX):]
    challenge = os.urandom(32)
    secret = secret_from(a.key)
    sig = nc.schnorr_sign(challenge, secret)
    del secret
    good = nc.schnorr_verify(challenge, pub, sig)
    print(f"  challenge {challenge.hex()[:16]}…  signed with {a.key.split(':')[0]} key")
    print(f"  {'✓' if good else '✗'} BIP-340 signature verifies against resolved {trail['did'][:30]}… "
          f"(via {trail['methods'][0]})")
    return 0 if good else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--http-base", help="override https://<domain> for .well-known resolution (testing)")
        p.add_argument("--domain", help="domain hosting /.well-known/did/nostr/<hex>.json")
        p.add_argument("--did-doc", help="local DID document file (instead of HTTP resolution)")
        p.add_argument("--relay", action="append", default=[], help="wss:// relay for enhanced resolution")

    p = sub.add_parser("resolve"); p.add_argument("identifier"); p.add_argument("--json", action="store_true"); common(p)
    p = sub.add_parser("link"); p.add_argument("webid"); p.add_argument("did"); common(p)
    p = sub.add_parser("prove"); p.add_argument("did"); p.add_argument("--key", required=True); common(p)
    a = ap.parse_args()
    return {"resolve": cmd_resolve, "link": cmd_link, "prove": cmd_prove}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
