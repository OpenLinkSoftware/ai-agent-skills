# Setup

## Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install eth_account requests jsonschema
pip install "x402[requests,evm,extensions]"
```

Required packages: `eth_account`, `requests`, `urllib3`, and the `x402`
Python SDK (v2, from the x402 Foundation) with the `requests` and `evm`
extras. `jsonschema` (and the SDK's `extensions` extra) is required too, even
for a plain fetch with no extensions of your own — the SDK validates a
server-offered extension in the *challenge itself* before creating a payment
payload. Observed live 2026-08-19: an `ods-qa.openlinksw.com` challenge
advertised `eip2612GasSponsoring` (gasless Permit2 approval), and without
`jsonschema` installed the SDK raised `ImportError` deep inside payload
creation — `Extensions validation requires jsonschema` — even though nothing
in this script or its arguments mentions extensions. Missing it fails at the
worst possible time: after the challenge is already decoded and the wallet
address printed, not at import time.

## The two `x402` package sources

Both report version **2.19.0**; the version number alone does not tell them
apart. They differ in exactly one way that matters here.

| Source | `set_spend_controls` | Effect |
|---|:---:|---|
| PyPI — `pip install x402` | absent | `--max-amount` is **not enforced**; the script warns on stderr and proceeds |
| Local checkout of <https://github.com/x402-foundation/x402> | present | `--max-amount` is enforced per payment |

Installing from a local checkout:

```bash
pip install "x402[requests,evm] @ file:///path/to/x402/python/x402"
```

The upstream script was verified end-to-end against the real
<https://x402.org/facilitator> using a local checkout. Either source settles
payments correctly — only the spend cap differs.

**Consequence for the agent:** if the warning appears, the cap is advisory.
The amount the *server* asks for is what gets signed. Say this to the user
before paying rather than after.

## Funding the buyer wallet

The `--key` wallet is the one spent from. It must hold testnet USDC on the
network the server's `PAYMENT-REQUIRED` `accepts[]` advertises — Base Sepolia
(`eip155:84532`) by default.

Fund at <https://faucet.circle.com>, selecting **Base Sepolia**.

An unfunded wallet produces `invalid_exact_evm_insufficient_balance` from the
facilitator. That is the expected failure, not a bug.

## Key storage

The buyer private key lives in the **OS credential store**, never in this
skill. Resolution order is `--key` → `$EVM_PRIVATE_KEY` → credential store →
hidden interactive prompt; see the Key Resolution section of `SKILL.md`.

Store one (the **user** runs this — the bare `-w` prompts, so the value never
passes through the agent or a command line):

```bash
security add-generic-password -s x402-buyer-evm-key -a default -T /usr/bin/security -w
```

`-T /usr/bin/security` is required, or non-interactive reads hang on a GUI
approval dialog.

Verify it reads back without prompting:

```bash
perl -e 'alarm 8; exec @ARGV' security find-generic-password -s x402-buyer-evm-key -a default -w >/dev/null && echo OK
```

(`timeout` does not exist on stock macOS; perl's `alarm` is the portable guard
against a keychain item whose ACL triggers a blocking dialog.)

Off macOS, `pip install keyring` first — **it is required there**, not optional
as it is on macOS, since there is no `/usr/bin/security`-style fallback binary
on Linux or Windows:

```bash
python3 -c "import keyring,getpass; keyring.set_password('x402-buyer-evm-key','default',getpass.getpass())"
```

`keyring` routes to the native store per OS — macOS Keychain, Secret Service
on Linux (GNOME Keyring / KWallet via D-Bus), Credential Manager on Windows
(DPAPI). A `keyring`-created item and a `security`-created item are the same
item on macOS.

⚠️ **Headless Linux** (a server or container with no Secret Service daemon
running): `keyring` may raise on `get_password`/`set_password`, or may
silently fall through to a non-secure backend rather than a real encrypted
store. Check before relying on it:

```bash
python3 -c "import keyring; print(keyring.get_keyring())"
```

On such a host, set `$EVM_PRIVATE_KEY` from your own secret manager instead of
expecting the OS credential store to be present.

The Keychain path above was verified end-to-end on macOS against a real item.
The Linux and Windows paths follow directly from `keyring`'s documented
backend routing but have not been separately exercised on those platforms.

## Test identities

Public addresses only. The buyer's private key is in the credential store under
`x402-buyer-evm-key` / `default`, not in any file here.

- **Seller** (server-side `opl_shop_x402_pay_to` registry key; receives settled
  testnet USDC — no private key needed): `0xb410b5E894Ce8CF5C68c21f26887C17Cf1200C79`
- **Buyer** (what the skill pays from): `0x0102257Dc714323EAA4541Ca73A4A3A2BF2ab553`

⚠️ Testnet only — these hold no real value. **Never fund them with real
assets.** The buyer key was migrated out of the script docstring and into the
Keychain on 2026-08-19; if you are working from an older copy of `x402_get.py`,
it still has the key inline and that copy should be discarded.
