#!/usr/bin/env python3
"""
YouID Nostr crypto helpers — dependency-free (stdlib only).

Provides everything the did:nostr parts of the skill need without pulling in
coincurve/secp256k1 bindings:

  * secp256k1 point arithmetic + x-only public key validation (lift_x)
  * BIP-340 Schnorr sign / verify (the signature scheme Nostr uses)
  * NIP-19 bech32 encode/decode for npub / nsec
  * did:nostr multibase (`fe70102` + hex) per the did:nostr spec
  * NIP-01 event id computation, signing and verification
  * Raw 32-byte secret -> SEC1 ECPrivateKey DER (for the optional PKCS#12 export)

This is a reference-quality implementation (constant-time is NOT a goal). It is
used for verification, test fixtures and the optional .p12 export — key
GENERATION for real identities is delegated to create-agent (nostr-tools).

CLI (handy for scripts and gates):
  nostr_crypto.py normalize <npub|hex|did:nostr:...>   -> JSON {hex,npub,did,multibase,valid}
  nostr_crypto.py pubkey <secret-hex>                  -> x-only pubkey hex
  nostr_crypto.py sec1der <secret-hex> <out.der>       -> write SEC1 DER private key
  nostr_crypto.py sign-event <secret-hex> <event.json> -> signed event JSON on stdout
  nostr_crypto.py verify-event <event.json>            -> exit 0 if id+sig valid
  nostr_crypto.py patch-did <did.json> <webid> <same|agent> [relay...]  -> write link + relays
  nostr_crypto.py selftest                             -> BIP-340 test vectors
"""

import hashlib
import json
import os
import sys

# ── secp256k1 ────────────────────────────────────────────────────────────────
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
     0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)

MULTIBASE_PREFIX = "fe70102"   # f=base16-lower, e701=secp256k1-pub varint, 02=even-y


def point_add(p1, p2):
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    if p1[0] == p2[0] and p1[1] != p2[1]:
        return None
    if p1 == p2:
        lam = (3 * p1[0] * p1[0] * pow(2 * p1[1], P - 2, P)) % P
    else:
        lam = ((p2[1] - p1[1]) * pow(p2[0] - p1[0], P - 2, P)) % P
    x3 = (lam * lam - p1[0] - p2[0]) % P
    return (x3, (lam * (p1[0] - x3) - p1[1]) % P)


def point_mul(pt, n):
    r = None
    for i in range(256):
        if (n >> i) & 1:
            r = point_add(r, pt)
        pt = point_add(pt, pt)
    return r


def lift_x(x):
    """Return the even-y point with x-coordinate x, or None if x is not on the curve."""
    if x >= P:
        return None
    y_sq = (pow(x, 3, P) + 7) % P
    y = pow(y_sq, (P + 1) // 4, P)
    if pow(y, 2, P) != y_sq:
        return None
    return (x, y if y % 2 == 0 else P - y)


def tagged_hash(tag, msg):
    th = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(th + th + msg).digest()


def _b(x):
    return x.to_bytes(32, "big")


def _i(b):
    return int.from_bytes(b, "big")


def xonly_pubkey(seckey_hex):
    d = _i(bytes.fromhex(seckey_hex))
    if not 1 <= d < N:
        raise ValueError("secret key out of range")
    return _b(point_mul(G, d)[0]).hex()


def schnorr_sign(msg, seckey_hex, aux=None):
    d0 = _i(bytes.fromhex(seckey_hex))
    if not 1 <= d0 < N:
        raise ValueError("secret key out of range")
    Pt = point_mul(G, d0)
    d = d0 if Pt[1] % 2 == 0 else N - d0
    aux = aux if aux is not None else os.urandom(32)
    t = _b(d ^ _i(tagged_hash("BIP0340/aux", aux)))
    k0 = _i(tagged_hash("BIP0340/nonce", t + _b(Pt[0]) + msg)) % N
    if k0 == 0:
        raise RuntimeError("nonce is zero")
    R = point_mul(G, k0)
    k = k0 if R[1] % 2 == 0 else N - k0
    e = _i(tagged_hash("BIP0340/challenge", _b(R[0]) + _b(Pt[0]) + msg)) % N
    sig = _b(R[0]) + _b((k + e * d) % N)
    if not schnorr_verify(msg, _b(Pt[0]).hex(), sig.hex()):
        raise RuntimeError("produced signature does not verify")
    return sig.hex()


def schnorr_verify(msg, pubkey_hex, sig_hex):
    try:
        pk, sig = bytes.fromhex(pubkey_hex), bytes.fromhex(sig_hex)
    except ValueError:
        return False
    if len(pk) != 32 or len(sig) != 64:
        return False
    Pt = lift_x(_i(pk))
    r, s = _i(sig[:32]), _i(sig[32:])
    if Pt is None or r >= P or s >= N:
        return False
    e = _i(tagged_hash("BIP0340/challenge", sig[:32] + pk + msg)) % N
    R = point_add(point_mul(G, s), point_mul(Pt, N - e))
    return R is not None and R[1] % 2 == 0 and R[0] == r


# ── bech32 (NIP-19) ──────────────────────────────────────────────────────────
_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def _polymod(values):
    gen = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for v in values:
        b = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ v
        for i in range(5):
            chk ^= gen[i] if ((b >> i) & 1) else 0
    return chk


def _hrp_expand(hrp):
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def _convertbits(data, frombits, tobits, pad=True):
    acc, bits, ret, maxv = 0, 0, [], (1 << tobits) - 1
    for v in data:
        acc = (acc << frombits) | v
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad and bits:
        ret.append((acc << (tobits - bits)) & maxv)
    elif not pad and (bits >= frombits or ((acc << (tobits - bits)) & maxv)):
        raise ValueError("invalid padding")
    return ret


def bech32_encode(hrp, data_bytes):
    data = _convertbits(data_bytes, 8, 5)
    poly = _polymod(_hrp_expand(hrp) + data + [0] * 6) ^ 1
    chk = [(poly >> 5 * (5 - i)) & 31 for i in range(6)]
    return hrp + "1" + "".join(_CHARSET[d] for d in data + chk)


def bech32_decode(s):
    s = s.lower()
    pos = s.rfind("1")
    hrp, data = s[:pos], [_CHARSET.find(c) for c in s[pos + 1:]]
    if pos < 1 or -1 in data or _polymod(_hrp_expand(hrp) + data) != 1:
        raise ValueError("invalid bech32 string")
    return hrp, bytes(_convertbits(data[:-6], 5, 8, pad=False))


# ── did:nostr helpers ────────────────────────────────────────────────────────
def normalize(identifier):
    """Accept npub / 64-hex / did:nostr:<hex> and return every representation."""
    v = identifier.strip()
    if v.startswith("did:nostr:"):
        hexkey = v[len("did:nostr:"):]
    elif v.startswith("npub1"):
        hrp, raw = bech32_decode(v)
        if hrp != "npub" or len(raw) != 32:
            raise ValueError("not an npub")
        hexkey = raw.hex()
    else:
        hexkey = v
    hexkey = hexkey.lower()
    if len(hexkey) != 64 or any(c not in "0123456789abcdef" for c in hexkey):
        raise ValueError(f"not a 64-char hex public key: {identifier}")
    return {
        "hex": hexkey,
        "npub": bech32_encode("npub", bytes.fromhex(hexkey)),
        "did": f"did:nostr:{hexkey}",
        "multibase": MULTIBASE_PREFIX + hexkey,
        "valid": lift_x(_i(bytes.fromhex(hexkey))) is not None,
    }


OPL_ON_BEHALF_OF = "http://www.openlinksw.com/schemas/cert#onBehalfOf"


def patch_did_document(path, webid, mode, relays):
    """Write the DID side of a WebID link (+ relay services) into agent.did.json.

    mode 'same'  → alsoKnownAs [webid]              (DID and WebID denote the same agent)
    mode 'agent' → oplcert:onBehalfOf {"@id": webid} (DID is an agent acting for the WebID)
    """
    with open(path) as f:
        doc = json.load(f)
    if webid:
        if mode == "same":
            doc.pop(OPL_ON_BEHALF_OF, None)
            aka = doc.get("alsoKnownAs", [])
            if webid not in aka:
                aka.append(webid)
            doc["alsoKnownAs"] = aka
            print(f"  ✓ alsoKnownAs → {webid}   (same agent)")
        elif mode == "agent":
            doc.pop("alsoKnownAs", None)
            doc[OPL_ON_BEHALF_OF] = {"@id": webid}
            print(f"  ✓ oplcert:onBehalfOf → {webid}   (agent acting for the WebID principal)")
        else:
            raise ValueError("mode must be 'same' or 'agent'")
    if relays:
        svc = [s for s in doc.get("service", []) if s.get("type") != "Relay"]
        for i, r in enumerate(relays, 1):
            if not r.startswith("wss://"):
                raise ValueError(f"relay must be wss:// — got {r}")
            if r.count("/") == 2:      # origin-level relay URL MUST end with '/' (spec)
                r += "/"
            svc.append({"id": f"{doc['id']}#relay{i}", "type": "Relay", "serviceEndpoint": r})
        doc["service"] = svc
        print(f"  ✓ {len(relays)} relay service(s)")
    with open(path, "w") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")


def minimal_did_document(hexkey, also_known_as=None):
    """did:nostr spec 'Minimal Resolution' document (offline, key-only)."""
    did = f"did:nostr:{hexkey}"
    doc = {
        "@context": ["https://www.w3.org/ns/did/v1",
                     "https://www.w3.org/ns/cid/v1",
                     "https://w3id.org/nostr/context"],
        "id": did,
        "type": "DIDNostr",
        "verificationMethod": [{
            "id": f"{did}#key1",
            "type": "Multikey",
            "controller": did,
            "publicKeyMultibase": MULTIBASE_PREFIX + hexkey,
        }],
        "authentication": ["#key1"],
        "assertionMethod": ["#key1"],
    }
    if also_known_as:
        doc["alsoKnownAs"] = list(also_known_as)
    return doc


# ── NIP-01 events ────────────────────────────────────────────────────────────
def event_id(ev):
    ser = json.dumps([0, ev["pubkey"], ev["created_at"], ev["kind"], ev["tags"], ev["content"]],
                     separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(ser.encode()).hexdigest()


def sign_event(ev, seckey_hex):
    ev = dict(ev)
    ev["pubkey"] = xonly_pubkey(seckey_hex)
    ev["id"] = event_id(ev)
    ev["sig"] = schnorr_sign(bytes.fromhex(ev["id"]), seckey_hex)
    return ev


def verify_event(ev):
    return (event_id(ev) == ev.get("id")
            and schnorr_verify(bytes.fromhex(ev["id"]), ev["pubkey"], ev["sig"]))


# ── SEC1 DER private key (for optional PKCS#12 export) ───────────────────────
def sec1_der(seckey_hex):
    """ECPrivateKey ::= SEQ { version 1, OCTET STRING key, [0] OID secp256k1 }"""
    key = bytes.fromhex(seckey_hex)
    if len(key) != 32:
        raise ValueError("secret key must be 32 bytes")
    oid = bytes.fromhex("06052b8104000a")                 # 1.3.132.0.10 secp256k1
    body = bytes.fromhex("020101") + b"\x04\x20" + key + b"\xa0" + bytes([len(oid)]) + oid
    return b"\x30" + bytes([len(body)]) + body


# ── self test (BIP-340 official vectors 0-3 + a negative) ────────────────────
_VECTORS = [
    ("0000000000000000000000000000000000000000000000000000000000000003",
     "F9308A019258C31049344F85F89D5229B531C845836F99B08601F113BCE036F9",
     "0000000000000000000000000000000000000000000000000000000000000000",
     "0000000000000000000000000000000000000000000000000000000000000000",
     "E907831F80848D1069A5371B402410364BDF1C5F8307B0084C55F1CE2DCA821525F66A4A85EA8B71E482A74F382D2CE5EBEEE8FDB2172F477DF4900D310536C0"),
    ("B7E151628AED2A6ABF7158809CF4F3C762E7160F38B4DA56A784D9045190CFEF",
     "DFF1D77F2A671C5F36183726DB2341BE58FEAE1DA2DECED843240F7B502BA659",
     "0000000000000000000000000000000000000000000000000000000000000001",
     "243F6A8885A308D313198A2E03707344A4093822299F31D0082EFA98EC4E6C89",
     "6896BD60EEAE296DB48A229FF71DFE071BDE413E6D43F917DC8DCF8C78DE33418906D11AC976ABCCB20B091292BFF4EA897EFCB639EA871CFA95F6DE339E4B0A"),
]


def selftest():
    ok = True
    for sk, pk, aux, msg, sig in _VECTORS:
        got_pk = xonly_pubkey(sk)
        got_sig = schnorr_sign(bytes.fromhex(msg), sk, bytes.fromhex(aux))
        good = (got_pk == pk.lower() and got_sig == sig.lower()
                and schnorr_verify(bytes.fromhex(msg), pk.lower(), sig.lower()))
        print(f"  {'✓' if good else '✗'} BIP-340 vector sk={sk[:8]}…")
        ok &= good
    bad = not schnorr_verify(bytes.fromhex(_VECTORS[1][3]), _VECTORS[1][1].lower(),
                             "00" + _VECTORS[1][4].lower()[2:])
    print(f"  {'✓' if bad else '✗'} tampered signature rejected")
    # did:nostr spec example npub mapping
    ex = normalize("124c0fa99407182ece5a24fad9b7f6674902fc422843d3128d38a0afbee0fdd2")
    npub_ok = ex["npub"] == "npub1zfxql2v5quvzanj6ynadndlkvays9lzz9ppaxy5d8zs2l0hqlhfq8fdyst"
    print(f"  {'✓' if npub_ok else '✗'} did:nostr spec example npub mapping")
    return ok and bad and npub_ok


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "normalize":
        print(json.dumps(normalize(argv[2]), indent=2))
    elif cmd == "pubkey":
        print(xonly_pubkey(argv[2].strip()))
    elif cmd == "sec1der":
        with open(argv[3], "wb") as f:
            f.write(sec1_der(argv[2].strip()))
    elif cmd == "sign-event":
        with open(argv[3]) as f:
            print(json.dumps(sign_event(json.load(f), argv[2].strip())))
    elif cmd == "verify-event":
        with open(argv[2]) as f:
            ok = verify_event(json.load(f))
        print("valid" if ok else "INVALID")
        return 0 if ok else 1
    elif cmd == "patch-did":
        patch_did_document(argv[2], argv[3], argv[4], argv[5:])
    elif cmd == "selftest":
        return 0 if selftest() else 1
    else:
        print(f"unknown command {cmd}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
