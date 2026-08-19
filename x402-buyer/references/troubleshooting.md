# Troubleshooting

## `invalid_exact_evm_insufficient_balance`

**Not a bug.** This is the correct, expected outcome for an empty buyer wallet,
and it confirms the whole pipeline is wired correctly end to end — header
shapes, base64 encoding, EIP-712 signing, and the facilitator's `/verify` +
`/settle` calls all ran.

Fix: fund the buyer wallet with testnet USDC at <https://faucet.circle.com>
(select Base Sepolia). Report the result to the user as a successful pipeline
test with an unfunded wallet, not as a failure.

## `Note: installed x402 SDK has no set_spend_controls`

Some PyPI releases of `x402` don't publish `x402ClientSync.set_spend_controls`
— `--max-amount` is **not enforced** on those, and the server's quoted amount
is what gets signed. Re-verified 2026-08-19: PyPI's current 2.20.0 *does* have
it, so this warning shouldn't appear on a fresh install today — but don't
assume either way. The script checks at runtime and prints this warning when
it's actually absent; treat the warning as authoritative over any assumption
based on a version number, since two sources have reported the identical
version number with different capabilities before. See [setup.md](setup.md).

Tell the user the cap is advisory **before** paying, whenever this warning
appears.

## `ImportError: Extensions validation requires jsonschema`

`jsonschema` (and the SDK's `extensions` extra) isn't installed. This is
required even for a plain fetch with no extensions of your own, because the
SDK validates any extension the *server's* challenge advertises before
creating a payment payload — `eip2612GasSponsoring` (gasless Permit2
approval) is common. Fails deep in the call stack, after the challenge is
already decoded and the buyer address already printed, which reads more like
a mid-run crash than a missing dependency:

```bash
pip install jsonschema
pip install "x402[extensions]"
```

Then rerun the exact same command — nothing else needs to change.

## `Error: no EVM private key. Tried --key, $EVM_PRIVATE_KEY, and the credential store`

Every source in the chain came up empty **and** stdin is not a terminal, so the
script could not prompt. This is the normal message from a non-interactive
context (a pipe, a CI job, a background call).

Fix: either store the key once (see [setup.md](setup.md)), export
`$EVM_PRIVATE_KEY`, or rerun where a prompt can be answered. Do not work around
it by putting the key in `--key` inside a script.

## Prompted for the key when it should have come from the Keychain

Check, in order:

1. **Account label.** The lookup is `x402-buyer-evm-key` / `--key-account`
   (default `default`). A key saved under a different label will not be found.
   List what exists: `security dump-keychain 2>/dev/null | grep -A1 x402-buyer-evm-key`
2. **`--no-keychain`** was passed, which skips the store entirely.
3. **Missing ACL entry.** An item created without `-T /usr/bin/security` cannot
   be read non-interactively — it raises a GUI dialog, and the script's 8-second
   alarm guard gives up and falls through to the prompt. Re-create it with the
   `-T` flag.

## Keychain read hangs, or a "security wants to access" dialog appears

The item's ACL does not include `/usr/bin/security`. The script guards its own
reads with `perl -e 'alarm 8; exec @ARGV'` so it degrades to a prompt instead of
hanging, but the underlying fix is to re-create the item with
`-T /usr/bin/security`. Never disable the guard — `timeout` is not available on
stock macOS, so `alarm` is the only portable protection here.

## `Error: that does not look like an EVM private key`

The resolved value is not `0x` + 64 hex characters. A common cause is a
credential-store item holding a wallet *address* (42 chars) rather than the
private key, or a value with a trailing newline from a copy-paste.

## No `PAYMENT-RESPONSE` header found

Printed as "No PAYMENT-RESPONSE header found (no payment was made or needed)".
Either the resource was not paywalled, or the request failed before the payment
step. Check the HTTP status and any `X-X402-Error` value.

## TLS certificate errors

A self-signed local server (`https://localhost:8443`) needs `--secure` omitted;
that is the default. If a **remote** host fails verification, do not disable
verification to get past it — report it.

## Digest auth appears to be ignored

`requests.HTTPDigestAuth` silently no-ops when the server challenges with
`Basic` rather than `Digest`. The script already probes for the offered scheme
and picks accordingly. If auth still fails, confirm the credentials against the
endpoint directly with `curl` before blaming the payment layer.

## Wrong network

If `accepts[]` names a network where the wallet holds nothing, verification
fails even with a funded wallet elsewhere. Decode the challenge (see the
SKILL.md probe) and compare its network against where the funds actually are.
Base Sepolia is `eip155:84532`.

## Binary response body

The script sniffs the `Content-Type` and, as a fallback, the first 1024 bytes
for a NUL byte. Non-text bodies are written to a file in the current working
directory named from the URL path, and reported by path and size rather than
dumped to the terminal.


## Always prompted on Linux/Windows, credential store never used

`keyring` is not installed, or it is installed but has no usable backend on
this host. It is **required** off macOS — there is no fallback binary the way
`/usr/bin/security` covers macOS.

```bash
pip install keyring
python3 -c "import keyring; print(keyring.get_keyring())"
```

If that prints something other than a real backend (e.g. a `fail.Keyring` or
`null` keyring), the host has no Secret Service daemon (common on headless
Linux servers and containers). Set `$EVM_PRIVATE_KEY` from your own secret
manager instead — do not try to make `keyring` work on a host with no desktop
session or keyring daemon running.


## `401 Digest` on port 443, but the user says this is an x402/WebID-TLS resource

Not a contradiction — port 443 on an OpenLink/Virtuoso resource server never
issues a `CertificateRequest`, so it falls through to Digest regardless of
what certificate is available. Retry with `--cert /path/to/cert.p12`, which
auto-rewrites the URL's port to **5443**. See `references/protocol.md`'s
WebID-TLS section for the full three-hop sequence this was reverse-engineered
from (443 -> Digest dead end; 5443 -> cert accepted -> 302 `?k=...` -> real 402).

## `Error: no PKCS#12 passphrase. Tried --cert-pass, $X402_CERT_PASSPHRASE, and the credential store`

Same shape as the missing-EVM-key error, different credential. Store the
passphrase once:

```bash
security add-generic-password -s x402-buyer-p12-passphrase -a default -T /usr/bin/security -w
```

## `Error: PKCS#12 passphrase did not unlock the certificate`

The resolved passphrase is wrong for the given `--cert` file. If it came from
the credential store, the stored value may be stale (re-created cert, rotated
passphrase) — overwrite the item and try again. This is a distinct failure
from an EVM key shape error; it comes from `openssl pkcs12`'s own MAC
verification, not from this script's validation.

## Settlement fails with a permission/principal error despite a correctly signed payment, when `--cert` was used

This script sets the client certificate once on the whole `requests`-like
session the x402 SDK hands back, on the assumption that setting `.cert` on it
carries through every request that session makes — including the signed
payment retry, not just the first GET. That assumption follows from how the
rest of this script already uses that object, but has not been independently
verified against the x402 SDK's own internals. If this happens, capture a
`curl -v` trace of the retry request and confirm the certificate was actually
present in the TLS handshake (`Request CERT` followed by an outbound
`Certificate` message) — if it wasn't, the session did not carry the cert
through and this needs a fix in how the certificate is attached, not a retry.
