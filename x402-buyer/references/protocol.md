# x402 v2 — buyer's view of the protocol

## Roles

| Role | Who | What they hold |
|---|---|---|
| **Buyer** | this client | the EVM private key whose USDC is spent |
| **Server** | the resource host (e.g. OPL Shop) | the paywalled resource; a `pay_to` address |
| **Facilitator** | <https://x402.org/facilitator> by default | runs `/verify` and `/settle` against the chain |

The buyer never talks to the facilitator directly. It signs, and the *server*
takes the signature to the facilitator.

## The round trip

1. **`GET <url>`** — plain request, no payment.
2. **`402 Payment Required`** with a **`PAYMENT-REQUIRED`** header. The value
   is base64; decoded, it carries an `accepts[]` list of payment options —
   network, asset, amount, and pay-to address.
3. **Sign.** The client picks an acceptable option and signs an EIP-3009
   "exact" authorization (EIP-712 typed data) with the buyer key. Where the
   `eip2612GasSponsoring` extension applies, the signer first reads on-chain
   state — the current Permit2 allowance and the EIP-2612 nonce — from the
   configured RPC endpoint, so the Permit2 approval can be gasless.
4. **Retry `GET <url>`** with a **`PAYMENT-SIGNATURE`** header carrying the
   signed authorization.
5. **Server settles.** It calls the facilitator's `/verify`, then `/settle`.
6. **`200`** with the resource, plus a **`PAYMENT-RESPONSE`** header carrying
   the settlement result. On failure, an **`X-X402-Error`** header carries the
   reason.

## Header summary

| Header | Direction | Carries |
|---|---|---|
| `PAYMENT-REQUIRED` | server → buyer | base64 challenge; `accepts[]` options |
| `PAYMENT-SIGNATURE` | buyer → server | base64 signed EIP-3009 authorization |
| `PAYMENT-RESPONSE` | server → buyer | settlement result JSON |
| `X-X402-Error` | server → buyer | failure reason string |

## Networks

Default is **Base Sepolia**, CAIP-2 `eip155:84532`, settled in testnet USDC via
the public facilitator, which needs no setup or authentication. The wallet must
hold funds on whichever network `accepts[]` names — mainnet and testnet
balances are not interchangeable, and a wrong-network wallet fails at
verification.

## WebID-TLS / NetID-TLS

Some resource servers gate the x402 challenge itself behind a WebID-TLS
handshake — the `402` never appears until a client certificate is accepted.
Observed live 2026-08-19 against `ods-qa.openlinksw.com`:

1. `GET` on port 443 (or no explicit port): TLS connects, but the server never
   issues a `CertificateRequest`. Falls straight to `401 Digest`. The x402
   challenge is unreachable this way regardless of what certificate is
   available client-side.
2. `GET` on port **5443** with a client cert presented: `CertificateRequest`
   issued, cert accepted, `302 Found` with `Location:` pointing at the same
   path plus a `?k=<capability-token>` query parameter.
3. `GET` the `?k=...` URL, **still presenting the same client certificate**:
   returns the real `402 Payment Required` with `PAYMENT-REQUIRED` and
   `WWW-Authenticate: Payment` headers.

**Port 5443 is not optional or best-effort — it is where the WebID-TLS
handshake lives on these servers.** Port 443 accepting the TLS connection is
not evidence the resource lacks an x402 layer; it only proves the plain HTTPS
port doesn't request a certificate. Default to 5443 the first time a client
certificate is available, rather than discovering the need for it after a
misleading `401` on 443.

The certificate must be presented on **every** hop — the initial probe, the
redirect follow, and (per the same WebID-TLS session-reuse caveat `acp-client`
documents) the eventual signed-payment retry.

## Interaction with HTTP auth

The payment layer is independent of HTTP authentication. WebDAV endpoints such
as OPL Shop's DAV path require Digest auth *and* payment; both must succeed.

Some Virtuoso VAL configurations challenge with `WWW-Authenticate: Basic` or
`Digest` depending on the request's User-Agent, for the identical URL and
credentials — curl's default UA has been observed getting Digest where
python-requests' default UA gets Basic. `requests.HTTPDigestAuth` silently
no-ops against a Basic challenge instead of falling back, so the client probes
the challenge once and selects the scheme actually offered.

## Server-side implementation (OPL Shop)

`opl_shop_x402_mpp.sql`, `opl_shop_dav_mpp.sql`, `opl_shop_sparql_mpp.sql`, and
`opl_shop_opal_mpp.sql`. The seller address comes from the
`opl_shop_x402_pay_to` registry key.
