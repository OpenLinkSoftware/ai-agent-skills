# did:nostr Support (T8) — Reference

YouID links a WebID (RSA / X.509, WebID-TLS) with a **did:nostr** identity (secp256k1 /
BIP-340 Schnorr, Nostr). The two keys are different kinds and are never merged. The
WebID keeps its RSA `cert:key` for WebID-TLS, and the did:nostr key is published beside
it as a W3C CID `Multikey`.

- Minting is done by [create-agent](https://github.com/melvincarvalho/create-agent) (`npx create-agent`, which uses nostr-tools).
- Spec: [did:nostr Method Specification](https://nostrcg.github.io/did-nostr/) (W3C Nostr CG). It is young and still changing. The facts below were checked against the live spec on 2026-09-28 (spec 0.1.1), so re-check them rather than recalling them.

## Spec facts used by the scripts

| Item | Value |
|------|-------|
| DID syntax | `did:nostr:<64-char lowercase hex x-only pubkey>` — the hex is canonical; `npub1…` (NIP-19 bech32) is display-only |
| Validity | the 32-byte value must be a field element and the x-coordinate of a curve point (`nostr_crypto.lift_x`) |
| `@context` | `["https://www.w3.org/ns/did/v1", "https://www.w3.org/ns/cid/v1", "https://w3id.org/nostr/context"]` |
| `type` | `DIDNostr` |
| Verification method | `Multikey`, `publicKeyMultibase` = `fe70102` + hex (`f` base16-lower, `e701` secp256k1-pub, `02` even-y) |
| `authentication` / `assertionMethod` | `["#key1"]` (relative); the VM's own `id`/`controller` stay absolute |
| `alsoKnownAs` | claims **the same entity**. The spec names "Linking a Nostr identity to a WebID for Solid applications" as a use case, and says to check reciprocal references |
| Signed attestation | `alsoKnownAs` inside a **kind 0** profile event is signed by the DID key, which the spec calls stronger assurance |
| Resolution order | 1. HTTP `https://<domain>/.well-known/did/nostr/<hex>.json` (serve as `application/did+json`) → 2. offline minimal (key only; MUST be supported) → 3. optional relay enhancement (kind 0 profile, kind 3 follows, kind 10002 relays) |
| Relay services | `{"type": "Relay", "serviceEndpoint": "wss://host/"}`; origin-level URLs MUST end in `/` |

The CID v1 context maps the RDF terms used in the WebID profile as follows: `Multikey` →
`https://w3id.org/security#Multikey`, `publicKeyMultibase` → `sec:publicKeyMultibase`
(datatype `sec:multibase`), `controller` → `sec:controller`, `verificationMethod` →
`sec:verificationMethod`, `alsoKnownAs` → `as:alsoKnownAs`.

## "Whose identity is this?" — the link mode (always elicit)

| Mode | Meaning | WebID side (profile) | DID side (agent.did.json) |
|------|---------|----------------------|---------------------------|
| `same` | the DID and the WebID denote the **same agent** (your own Nostr key) | `<webid> owl:sameAs <did:nostr:…>` | `alsoKnownAs: [webid]` (optionally also in a signed kind 0) |
| `agent` | the DID is a **distinct software agent** acting for the WebID's principal (create-agent's primary use) | `<webid> oplcert:hasIdentityDelegate <did:nostr:…>` | `"http://www.openlinksw.com/schemas/cert#onBehalfOf": {"@id": webid}` |

Never use `owl:sameAs` in `agent` mode. It would merge the person and their bot into one
entity, and every fact about one would be inferred about the other. `agent` mode follows
the delegation model in `delegation.md`: the delegator's graph holds `hasIdentityDelegate`
and the delegate's graph holds `onBehalfOf`.

**Limitation:** a did:nostr agent **cannot do WebID-TLS**. Verifiers check an RSA
`cert:key`, and browsers and TLS stacks don't offer secp256k1 client certificates. The
Step 6 delegation gate therefore exempts `did:nostr:` delegates from its RSA `cert:key`
requirement, and Step 7 checks their Multikey instead.

## Secret-key custody

| Option | How | Consumers |
|--------|-----|-----------|
| git config (default, create-agent) | `git -C <dir> config --local nostr.privkey` | aam, fund-agent, `resolve_did.py prove --key git:<dir>` |
| macOS Keychain (`-K`) | generic-password item, service `youid-nostr`, account = npub | `prove --key keychain:<npub>` |
| PKCS#12 (`-X`, optional) | secp256k1 key + self-signed X.509 (SAN: `URI:did:nostr:<hex>` + `URI:<webid>`), password-encrypted | portable backup; `prove --key p12:<file>` with `YOUID_P12_PASS` |

The `.p12` is **not** a WebID-TLS credential. OpenSSL handles secp256k1 fine, but browsers
and TLS client-auth stacks don't. The secret key is never written into the YouID output
bundle and is never printed.

## Scripts

| Script | Purpose |
|--------|---------|
| `generate_nostr_identity.sh` | T8: mint via create-agent, key gate, reciprocal link (`-w -R`), relays (`-r`), Keychain (`-K`), `.p12` (`-X -p`), `.well-known` copy (`-H`), reuse existing (`-E`) |
| `generate_identity.sh -N <id> -R same\|agent` | add the WebID side of the link + Multikey to all profile representations, the card, and vCard (`nostr:` URI, NIP-21) |
| `nostr_link_gate.py` | Step 7 gate (auto-run by `generate_identity.sh`) |
| `resolve_did.py resolve\|link\|prove` | did:nostr resolver (HTTP / offline / relay, all relay events signature-checked) + two-sided link verification + proof of control |
| `nostr_relay.mjs` | dependency-free NIP-01 relay client (Node ≥ 22 global WebSocket) |
| `nostr_crypto.py` | stdlib-only secp256k1, BIP-340, bech32, multibase, NIP-01 events, SEC1 DER; `selftest` runs BIP-340 vectors |

## Verification semantics (`resolve_did.py link`)

**VERIFIED** requires all of the following:

1. The WebID document asserts exactly one relation to the DID.
2. The Multikey published in the WebID document equals `fe70102` + the DID hex.
3. The DID document reciprocates: `alsoKnownAs` for `same`, `onBehalfOf` for `agent`, and an agent must not claim to *be* the WebID.

With `--relay`, `same` mode also requires the reciprocal claim to come from a signed
kind 0 event. A claim made on only one side reports **NOT VERIFIED**.

## Known constraints

- **URIBurner resolver:** `linkeddata.uriburner.com/describe/?url=did%3Anostr%3A…` does not describe `did:` IRIs; it shows an "Open this link?" interstitial (checked 2026-09-28). The card therefore shows the DID as plain copyable text, not a resolver link.
- **Sandboxed agents:** WebSocket upgrades through a filtering proxy may fail; relay enhancement then degrades to a warning, because it is optional per the spec.
