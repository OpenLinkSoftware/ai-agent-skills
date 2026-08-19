#!/usr/bin/env python3
"""x402 v2 test client: GET any URL, pay a 402 challenge automatically.

Fetches a URL; if the server responds with a 402 carrying a PAYMENT-REQUIRED
header, this signs a real EIP-3009 "exact" authorization with the given EVM
private key, retries with a PAYMENT-SIGNATURE header, and prints the
PAYMENT-RESPONSE settlement result (or the final status/body if none).

Built to exercise OPL Shop's x402 support in opl_shop_x402_mpp.sql /
opl_shop_dav_mpp.sql / opl_shop_sparql_mpp.sql / opl_shop_opal_mpp.sql, which
by default talks to the real public testnet facilitator at
https://x402.org/facilitator (Base Sepolia, no setup/auth required).

-------------------------------------------------------------------------------
SETUP
-------------------------------------------------------------------------------
This script needs: eth_account, requests, urllib3, jsonschema, and the `x402`
Python SDK (v2, from the x402 Foundation, with the `requests`, `evm`, and
`extensions` extras).

    python3 -m venv .venv && source .venv/bin/activate
    pip install eth_account requests jsonschema
    pip install "x402[requests,evm,extensions]"

jsonschema / the extensions extra is required even for a plain fetch with no
extensions of your own -- the SDK validates any extension the SERVER'S
challenge advertises (e.g. eip2612GasSponsoring, seen live against
ods-qa.openlinksw.com 2026-08-19) before it will create a payment payload at
all. Missing it fails deep inside signing -- after the challenge already
decoded and the buyer address already printed -- with:
  ImportError: Extensions validation requires jsonschema. Install with: pip install x402[extensions]

Optionally also `pip install keyring`, which lets the private key be read from
the OS credential store on any platform (macOS Keychain, Secret Service on
Linux, Credential Manager on Windows).

  - macOS:           optional -- without it the script shells out to
                      /usr/bin/security for the same Keychain item.
  - Linux / Windows: REQUIRED -- there is no fallback binary; without it the
                      key resolver skips the credential store and prompts on
                      every run. On headless Linux (no Secret Service daemon)
                      `keyring` may fail or silently use a non-secure backend;
                      check with `python3 -c "import keyring; print(keyring.get_keyring())"`.

Two sources for the `x402` package have, at times, behaved differently:

  - Plain `pip install x402` from PyPI: at 2.19.0 this lacked
    x402ClientSync.set_spend_controls, so --max-amount went unenforced (the
    script detects this and warns on stderr rather than failing). RE-VERIFIED
    2026-08-19: PyPI now ships 2.20.0, which DOES have set_spend_controls --
    the cap is enforced from a plain `pip install x402` today. Still check at
    runtime (the script does) rather than assuming either way, since PyPI's
    version can move again.
  - A local checkout of https://github.com/x402-foundation/x402 (e.g. this
    machine's /Users/imitko/virtuoso/x402) may be ahead of PyPI at any given
    time, sometimes at the SAME reported version number -- confusingly,
    version number alone doesn't tell the two apart. Install it
    with:
        pip install "x402[requests,evm] @ file:///Users/imitko/virtuoso/x402/python/x402"
    This is what was used to verify this script end-to-end against the real
    x402.org facilitator.

Either way works for actually paying and settling; only the spend cap differs.

-------------------------------------------------------------------------------
USAGE
-------------------------------------------------------------------------------
    python x402_get.py [URL] [--key PRIVATE_KEY] [--key-account NAME]
                        [--max-amount 20] [--no-keychain]
                        [--digest-user USER --digest-pass PASS]
                        [--cert P12_PATH] [--cert-account NAME] [--no-port-rewrite]
                        [--secure]

    URL             Defaults to https://localhost:8443/DAV/data/paid.txt
    --key           EVM private key (0x...) of the BUYER wallet that pays.
                    Usually omitted -- see KEY RESOLUTION below. This is the
                    wallet whose
                    USDC balance is spent -- it must hold testnet USDC on
                    whatever network the server's PAYMENT-REQUIRED accepts[]
                    advertises (Base Sepolia, eip155:84532, by default).
                    Fund it at https://faucet.circle.com (select Base Sepolia).
    --max-amount    Spend cap per payment as a dollar string, e.g. "$20"
                    (default: $20). The x402 SDK refuses to pay more than
                    this per request regardless of what the server asks for.
    --digest-user / --digest-pass
                    Optional HTTP Digest auth credentials, needed for the
                    OPL Shop DAV endpoint (WebDAV requires Digest auth
                    independently of the x402 payment layer).
    --cert          PKCS#12 client certificate for WebID-TLS / NetID-TLS.
                    Some resource servers gate the x402 challenge itself
                    behind a WebID-TLS-authenticated redirect -- the 402
                    never appears until the cert is presented. Passing this
                    flag switches the request onto that path AND rewrites
                    the URL's port to 5443 (see WEBID-TLS below) unless
                    --no-port-rewrite is also given. The passphrase resolves
                    the same way the buyer key does -- see KEY RESOLUTION --
                    under credential-store service x402-buyer-p12-passphrase
                    (--cert-account selects which label, default "default").
    --secure        Verify TLS certificates. Omit for a local server with a
                    self-signed cert (localhost:8443 uses one by default).

Example against the local shop's paid test file:

    python x402_get.py "https://localhost:8443/DAV/data/paid.txt" \\
        --digest-user demo --digest-pass ****

Example against a WebID-TLS-gated resource (port auto-rewritten to 5443):

    python x402_get.py "https://ods-qa.openlinksw.com/DAV/home/USER/Items/file.pdf" \\
        --cert /path/to/cert.p12

The key and the certificate passphrase both resolve from the Keychain (or
prompt) -- neither is ever passed on the command line, where it would land in
shell history and in `ps` output.

-------------------------------------------------------------------------------
WEBID-TLS / NETID-TLS
-------------------------------------------------------------------------------
OpenLink resource servers (Virtuoso VDB) put the WebID-TLS / NetID-TLS
handshake on a DEDICATED port -- observed live 2026-08-19 against
ods-qa.openlinksw.com:

  :443 (or no explicit port)  -> TLS connects, but the server NEVER issues a
                                  CertificateRequest. Falls straight through
                                  to a 401 Digest challenge; the resource's
                                  x402 challenge is never reached this way,
                                  no matter what certificate is available.

  :5443                        -> CertificateRequest issued, client cert
                                  accepted, 302 redirect to a ?k=... capability
                                  URL, which THEN returns the real 402
                                  PAYMENT-REQUIRED.

Passing --cert makes this automatic: the URL's port is rewritten to 5443
before any request is sent, UNLESS the URL already names an explicit port
other than 443 (a local test server on a custom port is left alone -- that is
a deliberate override, not a miss). Use --no-port-rewrite to disable the
rewrite outright.

The client certificate must be presented on every hop of the exchange, not
just the first request -- this script sets it once on the whole session used
for both the initial GET and the signed payment retry, on the assumption that
x402_requests(client) yields a requests.Session-compatible object (true of
every other call this script already makes on it). That assumption has not
been independently verified against the x402 SDK's internals in the
environment this script was authored in, since the SDK is not installed
there. If a settlement attempt fails with a permission/principal error despite
a correctly signed payment, verify this first.

-------------------------------------------------------------------------------
KEY RESOLUTION
-------------------------------------------------------------------------------
The buyer private key is resolved from the first source that yields a value:

  1. --key on the command line        (discouraged: shell history, ps output)
  2. $EVM_PRIVATE_KEY in the environment
  3. The OS credential store          <-- normal path
       service: x402-buyer-evm-key
       account: --key-account, default "default"
  4. An interactive prompt            (input is never echoed)

After a successful prompt the script offers to save the key to the credential
store, so step 4 happens once per wallet and step 3 covers every later run.

To store a key yourself, without it passing through any other process, run the
interactive form -- the bare -w takes the value from a hidden prompt:

    security add-generic-password -s x402-buyer-evm-key -a default \\
        -T /usr/bin/security -w

The -T /usr/bin/security flag is REQUIRED. It puts the security binary on the
item's ACL so later reads return the value directly; without it macOS raises a
"security wants to access..." GUI dialog and a non-interactive read HANGS.

Off macOS (Linux/Windows), the equivalent -- `pip install keyring` first, it
is required there, not optional:

    python3 -c "import keyring,getpass; \\
        keyring.set_password('x402-buyer-evm-key','default',getpass.getpass())"

-------------------------------------------------------------------------------
TEST IDENTITIES (Base Sepolia testnet only -- NEVER fund with real assets)
-------------------------------------------------------------------------------
Seller (configured server-side as the opl_shop_x402_pay_to registry key --
receives settled testnet USDC; no private key needed for anything here):
    address:     0xb410b5E894Ce8CF5C68c21f26887C17Cf1200C79

Buyer (the wallet this script pays from; fund it with testnet USDC before
expecting a real settlement to succeed):
    address:     0x0102257Dc714323EAA4541Ca73A4A3A2BF2ab553

Its throwaway private key is NOT stored in this file. It lives in the OS
credential store under x402-buyer-evm-key / default and is read at runtime.
A private key in a source file is a private key in every clone, diff, and
backup of the repo -- even a valueless testnet one, whose real cost is that it
teaches the pattern.

Without funding, expect the facilitator to reject the payment with
"invalid_exact_evm_insufficient_balance" -- that's the correct, expected
failure mode for an empty wallet and confirms the whole pipeline (header
shapes, base64 encoding, EIP-712 signing, facilitator /verify + /settle
calls) is wired correctly end to end.
"""

import argparse
import getpass
import os
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit, urlunsplit

import requests
import urllib3
from eth_account import Account

from x402 import x402ClientSync
from x402.http import x402HTTPClientSync
from x402.http.clients import x402_requests
from x402.mechanisms.evm.exact.register import register_exact_evm_client
from x402.mechanisms.evm.signers import EthAccountSignerWithRPC

DEFAULT_URL = "https://localhost:8443/DAV/data/paid.txt"

# OS credential store coordinates for the buyer private key. The account name
# is a wallet label, so several wallets can coexist under one service.
KEYCHAIN_SERVICE = "x402-buyer-evm-key"
DEFAULT_KEY_ACCOUNT = "default"

EVM_KEY_RE = re.compile(r"\A0x[0-9a-fA-F]{64}\Z")

# WebID-TLS / NetID-TLS client-certificate passphrase, stored separately from
# the EVM key above -- a resource server's WebID-TLS gate and the on-chain
# wallet are two independent credentials.
CERT_KEYCHAIN_SERVICE = "x402-buyer-p12-passphrase"
DEFAULT_CERT_ACCOUNT = "default"

# OpenLink resource servers (Virtuoso VDB) put the WebID-TLS / NetID-TLS
# handshake on a DEDICATED port, not on the plain HTTPS port. Port 443 (or no
# explicit port) accepts the TLS connection but never issues a client
# certificate request -- it falls through to Digest/401 and NEVER reaches an
# x402 challenge that sits behind a WebID-TLS-gated redirect. Observed live
# 2026-08-19 against ods-qa.openlinksw.com: :443 -> 401 Digest, no CertificateRequest
# in the handshake at all; :5443 -> CertificateRequest, cert accepted, 302 to a
# ?k=... capability URL, which THEN issues the real 402 PAYMENT-REQUIRED.
WEBID_TLS_PORT = 5443
DEFAULT_RPC_URL = "https://base-sepolia-rpc.publicnode.com"

# Content-Types safe to print straight to the console.
TEXT_CONTENT_TYPES = ("text/", "application/json", "application/xml", "application/problem+json")


def keychain_get(service: str, account: str) -> str | None:
    """Read a secret from the OS credential store; None if absent or unreadable.

    Prefers the `keyring` package, which routes to the right native store per
    OS (macOS Keychain, Secret Service on Linux, Credential Manager on
    Windows). Falls back to /usr/bin/security so macOS works without the extra
    dependency.
    """
    try:
        import keyring

        value = keyring.get_password(service, account)
        if value:
            return value.strip()
    except Exception:
        # No keyring package, or no usable backend on this host. Not an error:
        # the caller falls through to the next source in the chain.
        pass

    if sys.platform != "darwin":
        return None

    try:
        # The alarm guard matters. An item whose ACL excludes /usr/bin/security
        # makes macOS raise a GUI approval dialog, which would hang this call
        # indefinitely when run non-interactively. `timeout` does not exist on
        # stock macOS; perl's alarm is the portable equivalent.
        result = subprocess.run(
            ["perl", "-e", "alarm 8; exec @ARGV",
             "security", "find-generic-password",
             "-s", service, "-a", account, "-w"],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return None

    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def keychain_set(service: str, account: str, secret: str) -> bool:
    """Store a secret in the OS credential store. True on success."""
    try:
        import keyring

        keyring.set_password(service, account, secret)
        return True
    except Exception:
        pass

    if sys.platform != "darwin":
        return False

    try:
        # -T /usr/bin/security puts the security binary on the new item's ACL,
        # so later reads return the value instead of raising a GUI prompt.
        # -U updates in place; reaching here means the user asked to save.
        result = subprocess.run(
            ["security", "add-generic-password",
             "-s", service, "-a", account,
             "-D", "EVM private key",
             "-T", "/usr/bin/security",
             "-U", "-w", secret],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def resolve_private_key(explicit: str | None, account: str, use_keychain: bool) -> str:
    """Resolve the buyer key: --key, then env, then credential store, then prompt.

    Exits with a message rather than returning something unusable.
    """
    source = None
    key = None

    if explicit:
        key, source = explicit.strip(), "--key argument"
    elif os.getenv("EVM_PRIVATE_KEY"):
        key, source = os.environ["EVM_PRIVATE_KEY"].strip(), "$EVM_PRIVATE_KEY"
    elif use_keychain:
        key = keychain_get(KEYCHAIN_SERVICE, account)
        if key:
            source = f"credential store ({KEYCHAIN_SERVICE}/{account})"

    prompted = False
    if not key:
        if not sys.stdin.isatty():
            print(
                f"Error: no EVM private key. Tried --key, $EVM_PRIVATE_KEY, and the\n"
                f"credential store ({KEYCHAIN_SERVICE}/{account}); stdin is not a\n"
                f"terminal, so it cannot be prompted for. Store it once with:\n"
                f"  security add-generic-password -s {KEYCHAIN_SERVICE} -a {account} "
                f"-T /usr/bin/security -w",
                file=sys.stderr,
            )
            sys.exit(1)
        key = getpass.getpass(
            f"Buyer EVM private key (0x..., not echoed) [{account}]: "
        ).strip()
        source, prompted = "interactive prompt", True

    if not EVM_KEY_RE.match(key):
        print(
            "Error: that does not look like an EVM private key "
            "(expected 0x followed by 64 hex characters).",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Key source: {source}")

    if prompted and use_keychain:
        answer = input(
            f"Save this key to the credential store as "
            f"{KEYCHAIN_SERVICE}/{account}? [y/N]: "
        ).strip().lower()
        if answer in ("y", "yes"):
            if keychain_set(KEYCHAIN_SERVICE, account, key):
                print("Saved. Later runs will not prompt.")
            else:
                print("Could not save to the credential store.", file=sys.stderr)

    return key


def rewrite_for_webid_tls(url: str) -> str:
    """Rewrite a URL's port to WEBID_TLS_PORT (5443) when it's on the default
    HTTPS port -- the port the WebID-TLS/NetID-TLS handshake actually lives on
    for OpenLink resource servers. See the WEBID_TLS_PORT comment for why.

    A URL that already names an explicit, non-443 port (e.g. a local test
    server on :8443) is left untouched -- that is a deliberate override, not
    an oversight, and this function must not fight it.
    """
    parts = urlsplit(url)
    if parts.scheme != "https":
        return url  # WebID-TLS is a TLS-layer mechanism; nothing to rewrite off-TLS.

    host = parts.hostname or ""
    port = parts.port  # None when the URL has no explicit port (implicit 443)
    if port not in (None, 443):
        return url  # explicit non-default port -- respect it

    userinfo = ""
    if parts.username:
        userinfo = parts.username + (f":{parts.password}" if parts.password else "") + "@"
    netloc = f"{userinfo}{host}:{WEBID_TLS_PORT}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def resolve_cert_passphrase(explicit: str | None, account: str, use_keychain: bool) -> str:
    """Resolve the PKCS#12 client-certificate passphrase.

    Same four-source chain as resolve_private_key, under a SEPARATE credential-
    store service (CERT_KEYCHAIN_SERVICE) -- the WebID-TLS certificate and the
    on-chain wallet are unrelated credentials and must not share a namespace.
    """
    source = None
    passphrase = None

    if explicit:
        passphrase, source = explicit, "--cert-pass argument"
    elif os.getenv("X402_CERT_PASSPHRASE"):
        passphrase, source = os.environ["X402_CERT_PASSPHRASE"], "$X402_CERT_PASSPHRASE"
    elif use_keychain:
        passphrase = keychain_get(CERT_KEYCHAIN_SERVICE, account)
        if passphrase:
            source = f"credential store ({CERT_KEYCHAIN_SERVICE}/{account})"

    prompted = False
    if not passphrase:
        if not sys.stdin.isatty():
            print(
                f"Error: no PKCS#12 passphrase. Tried --cert-pass, "
                f"$X402_CERT_PASSPHRASE, and the credential store "
                f"({CERT_KEYCHAIN_SERVICE}/{account}); stdin is not a terminal. "
                f"Store it once with:\n"
                f"  security add-generic-password -s {CERT_KEYCHAIN_SERVICE} "
                f"-a {account} -T /usr/bin/security -w",
                file=sys.stderr,
            )
            sys.exit(1)
        passphrase = getpass.getpass(
            f"PKCS#12 passphrase for {{account}} (not echoed) [{account}]: ".format(account=account)
        )
        source, prompted = "interactive prompt", True

    print(f"Certificate passphrase source: {source}")

    if prompted and use_keychain:
        answer = input(
            f"Save this passphrase to the credential store as "
            f"{CERT_KEYCHAIN_SERVICE}/{account}? [y/N]: "
        ).strip().lower()
        if answer in ("y", "yes"):
            if keychain_set(CERT_KEYCHAIN_SERVICE, account, passphrase):
                print("Saved. Later runs will not prompt.")
            else:
                print("Could not save to the credential store.", file=sys.stderr)

    return passphrase


def extract_pem_from_p12(p12_path: str, passphrase: str) -> str:
    """Decrypt a PKCS#12 bundle to a combined (cert+key) PEM file for `requests`.

    `requests`' `cert=` parameter cannot consume a PKCS#12 bundle directly --
    only PEM. This is the one sanctioned case for a PEM extract: the tool
    genuinely cannot use the .p12 file as-is. The passphrase is passed via env,
    never argv (so it never appears in `ps`), and the extracted PEM contains an
    UNENCRYPTED private key -- it exists only for the lifetime of this process,
    mode 0600, in a private temp directory, and callers MUST delete it in a
    finally block (see main()).
    """
    if not os.path.isfile(p12_path):
        print(f"Error: certificate file not found: {p12_path}", file=sys.stderr)
        sys.exit(1)

    fd, pem_path = tempfile.mkstemp(prefix="x402-buyer-cert-", suffix=".pem")
    os.close(fd)
    os.chmod(pem_path, 0o600)

    env = os.environ.copy()
    env["X402_BUYER_P12_PW"] = passphrase
    try:
        result = subprocess.run(
            ["openssl", "pkcs12", "-in", p12_path, "-nodes",
             "-passin", "env:X402_BUYER_P12_PW", "-out", pem_path],
            capture_output=True, text=True, check=False, env=env,
        )
    finally:
        del env  # drop our copy holding the passphrase promptly

    if result.returncode != 0:
        os.unlink(pem_path)
        stderr = result.stderr.strip()
        if "mac verify" in stderr.lower() or "invalid password" in stderr.lower():
            print("Error: PKCS#12 passphrase did not unlock the certificate.", file=sys.stderr)
        else:
            print(f"Error: could not extract PEM from {p12_path}: {stderr}", file=sys.stderr)
        sys.exit(1)

    return pem_path


def is_printable_body(response) -> bool:
    """Best-effort check that a response body is safe to dump to a terminal.

    Trusts a declared text-ish Content-Type, but falls back to sniffing the
    first bytes for a NUL byte (a cheap, reliable binary indicator) in case
    the server mislabels it.
    """
    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith(TEXT_CONTENT_TYPES):
        return False
    return b"\x00" not in response.content[:1024]


def print_body_summary(response, url: str) -> None:
    """Print the response body if it's text; otherwise save it and say so."""
    content_type = response.headers.get("Content-Type", "(unknown)")
    size = len(response.content)

    if not response.content:
        print("Body: (empty)")
        return

    if is_printable_body(response):
        print(f"Body: {response.text[:2000]}")
        return

    name = unquote(os.path.basename(urlsplit(url).path)) or "response.bin"
    out_path = os.path.join(os.getcwd(), name)
    with open(out_path, "wb") as f:
        f.write(response.content)
    print(f"Body: {size} bytes of {content_type}, not text -- saved to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pay an x402 402 challenge and fetch a URL.")
    parser.add_argument("url", nargs="?", default=DEFAULT_URL, help="Resource URL to fetch")
    parser.add_argument(
        "--key",
        default=None,
        help=(
            "EVM private key (0x...) of the buyer wallet. Discouraged -- it lands in "
            "shell history and in ps output. Normally omit it and let the key resolve "
            "from $EVM_PRIVATE_KEY, the OS credential store, or a hidden prompt."
        ),
    )
    parser.add_argument(
        "--key-account",
        default=DEFAULT_KEY_ACCOUNT,
        help=(
            f"Wallet label to look up in the credential store under service "
            f"{KEYCHAIN_SERVICE} (default: {DEFAULT_KEY_ACCOUNT}). Use different "
            f"labels to keep several wallets side by side."
        ),
    )
    parser.add_argument(
        "--no-keychain",
        action="store_true",
        help="Skip the credential store entirely (use --key or $EVM_PRIVATE_KEY only)",
    )
    parser.add_argument(
        "--cert",
        default=None,
        metavar="P12_PATH",
        help=(
            "PKCS#12 client certificate for WebID-TLS / NetID-TLS. Presence of this "
            "flag switches the request onto WebID-TLS: the target URL's port is "
            "auto-rewritten to WEBID_TLS_PORT (5443) unless it already names an "
            "explicit non-443 port. See --no-port-rewrite to disable that."
        ),
    )
    parser.add_argument(
        "--cert-pass",
        default=None,
        help="PKCS#12 passphrase inline -- discouraged, same reasons as --key",
    )
    parser.add_argument(
        "--cert-account",
        default=DEFAULT_CERT_ACCOUNT,
        help=(
            f"Credential-store label for the PKCS#12 passphrase, under service "
            f"{CERT_KEYCHAIN_SERVICE} (default: {DEFAULT_CERT_ACCOUNT})."
        ),
    )
    parser.add_argument(
        "--no-port-rewrite",
        action="store_true",
        help="With --cert, keep the URL's original port instead of rewriting to 5443",
    )
    parser.add_argument(
        "--max-amount",
        default="$20",
        help='Spend cap per payment, e.g. "$20" (default: $20)',
    )
    parser.add_argument("--digest-user", default=None, help="HTTP Digest auth username")
    parser.add_argument("--digest-pass", default=None, help="HTTP Digest auth password")
    parser.add_argument(
        "--rpc-url",
        default=DEFAULT_RPC_URL,
        help=(
            "EVM RPC endpoint the signer reads on-chain state from (current Permit2 "
            "allowance, EIP-2612 nonce) -- needed for gasless Permit2 approval via the "
            "eip2612GasSponsoring extension. Default: a public Base Sepolia RPC."
        ),
    )
    parser.add_argument(
        "--secure",
        action="store_true",
        help="Verify TLS certs (default is insecure, for self-signed local servers)",
    )
    args = parser.parse_args()

    pem_path = None
    if args.cert:
        if not args.no_port_rewrite:
            rewritten = rewrite_for_webid_tls(args.url)
            if rewritten != args.url:
                print(f"WebID-TLS: rewrote target port to {WEBID_TLS_PORT} "
                      f"({args.url} -> {rewritten})")
                args.url = rewritten
        cert_passphrase = resolve_cert_passphrase(
            args.cert_pass, args.cert_account, use_keychain=not args.no_keychain
        )
        pem_path = extract_pem_from_p12(args.cert, cert_passphrase)
        del cert_passphrase
        print(f"Client certificate: {args.cert} (WebID-TLS)")

    private_key = resolve_private_key(
        args.key, args.key_account, use_keychain=not args.no_keychain
    )

    if not args.secure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    account = Account.from_key(private_key)
    print(f"Buyer address: {account.address}")

    client = x402ClientSync()
    if hasattr(client, "set_spend_controls"):
        client.set_spend_controls({"max_amount_per_payment": args.max_amount})
    else:
        # Older/published x402 SDK builds don't have spend_controls at all
        # (it's present in a newer checkout of the SDK repo but not yet on
        # PyPI as of x402==2.19.0) -- proceed without a cap in that case.
        print(
            f"Note: installed x402 SDK has no set_spend_controls; "
            f"--max-amount ({args.max_amount}) will not be enforced.",
            file=sys.stderr,
        )
    register_exact_evm_client(client, EthAccountSignerWithRPC(account, rpc_url=args.rpc_url))
    http_client = x402HTTPClientSync(client)

    auth = None
    if args.digest_user:
        # Some Virtuoso VAL configs challenge with WWW-Authenticate: Basic
        # instead of Digest depending on the request's User-Agent (observed:
        # curl's default UA gets Digest, python-requests's default UA gets
        # Basic, for the identical URL/credentials). requests.HTTPDigestAuth
        # silently no-ops on a Basic challenge rather than falling back, so
        # probe once to see which scheme is actually offered before picking.
        probe = requests.get(args.url, cert=pem_path, verify=args.secure)
        challenge = probe.headers.get("WWW-Authenticate", "")
        if challenge.lower().startswith("basic"):
            auth = requests.auth.HTTPBasicAuth(args.digest_user, args.digest_pass or "")
        else:
            auth = requests.auth.HTTPDigestAuth(args.digest_user, args.digest_pass or "")

    try:
        print(f"GET {args.url}\n")
        with x402_requests(client) as session:
            if pem_path:
                # ASSUMPTION, not independently verified against x402 SDK
                # internals (the SDK is not installed in the environment this
                # script was authored in): x402_requests(client) yields an
                # object used exactly like a requests.Session (the pre-existing
                # code below already calls .get(url, auth=..., verify=...) on
                # it), so setting .cert here should carry the client
                # certificate through every hop this session makes -- the
                # initial WebID-TLS-gated redirect AND the x402 payment retry.
                # ACP's MPP flow requires the cert on every hop (see
                # acp-client/SKILL.md's WebID-TLS session-reuse note); if a
                # settlement attempt fails with a permission/principal error
                # despite a valid signature, verify this assumption first.
                session.cert = pem_path
            response = session.get(args.url, auth=auth, verify=args.secure)

            print(f"Status: {response.status_code}")
            print_body_summary(response, args.url)
            x402_error = response.headers.get("X-X402-Error")
            if x402_error:
                print(f"X-X402-Error: {x402_error}")


            try:
                settle_response = http_client.get_payment_settle_response(
                    lambda name: response.headers.get(name)
                )
                print("\nSettlement:")
                print(settle_response.model_dump_json(indent=2))
            except ValueError:
                print("\nNo PAYMENT-RESPONSE header found (no payment was made or needed)")
    finally:
        if pem_path:
            os.unlink(pem_path)


if __name__ == "__main__":
    main()
