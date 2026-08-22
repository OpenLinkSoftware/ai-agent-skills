# Changelog

All notable changes to this skill are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versioning
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-08-19

### Added

- **Testnet funding via Circle CLI** — new section in `SKILL.md` and expanded
  `references/setup.md` "Funding the buyer wallet" with a second funding path:
  bootstrap a Circle agent wallet in `--testnet` mode, draw 20 testnet USDC
  from the Circle faucet with `circle wallet fund`, and transfer it to the
  self-custody buyer EOA the script signs with.
- `examples/circle-testnet-funding.sh` — guided, **testnet-only by
  construction** helper: authenticates (`circle wallet login --testnet`),
  lists/funds/checks the agent wallet, and — only after explicit
  confirmation — transfers testnet USDC to the buyer EOA. Mainnet chain
  identifiers are refused outright.
- Documentation of the architectural constraint: Circle Agent Wallets are
  MPC-custodial (key shares never exposed) and cannot sign x402 payments;
  the x402 settlement path verifies EIP-3009 offchain via `ecrecover`, which
  requires the raw EVM private key. Agent wallet = funding source, never
  signer.
- Supported Circle testnet chain identifiers listed for `--chain`
  (`BASE-SEPOLIA`, `ARB-SEPOLIA`, `ETH-SEPOLIA`, `OP-SEPOLIA`, `MATIC-AMOY`,
  `AVAX-FUJI`, `UNI-SEPOLIA`, `MONAD-TESTNET`, `ARC-TESTNET`).

### Changed

- Version bumped `1.3.0` → `1.4.0` in `SKILL.md` frontmatter.

## [1.3.0] - 2026-08-19

### Fixed

- `jsonschema` + the SDK's `extensions` extra added to every install line:
  the x402 Python SDK validates server-offered extensions (e.g.
  `eip2612GasSponsoring`) before creating a payment payload, so a plain fetch
  without `jsonschema` fails deep inside signing.
- Corrected stale note: PyPI's `x402==2.20.0` **does** ship
  `set_spend_controls` (the earlier 2.19.0 distinction no longer applies).

## [1.2.0] - 2026-08-19

### Added

- WebID-TLS / NetID-TLS support: `--cert` PKCS#12 client-certificate flag
  with automatic port rewrite to **5443** (the port where the WebID-TLS
  handshake lives on OpenLink resource servers), passphrase resolution from
  a separate credential-store service (`x402-buyer-p12-passphrase`), and
  sanitized PEM extraction for the requests session.
- `examples/probe-challenge.sh` client-cert support with the same port
  rewrite.

## [1.1.0] - 2026-08-19

### Added

- Buyer EVM key migrated out of the script docstring into the OS credential
  store (`x402-buyer-evm-key`) with a four-source key resolver
  (`--key` → `$EVM_PRIVATE_KEY` → credential store → interactive prompt),
  `--key-account` labels, `--no-keychain`, and a printed `Key source:` line.

## [1.0.0] - 2026-08-19

### Added

- Initial release: x402 v2 buyer-side client (`scripts/x402_get.py`) built
  from a user-supplied reference implementation, exercising OPL Shop's x402
  support (DAV, SPARQL, OPAL, generic MPP endpoints) against the public Base
  Sepolia facilitator.
