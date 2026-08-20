#!/usr/bin/env bash
# Bootstrap a testnet buyer wallet via Circle CLI's --testnet mode.
#
# Two-path testnet funding for the x402-buyer skill (see SKILL.md
# "Testnet funding via Circle CLI" and references/setup.md Path 2):
#
#   1. Authenticate in testnet mode and list the Circle agent wallet.
#   2. `circle wallet fund` on a TESTNET chain draws 20 testnet USDC from
#      the Circle faucet (no fiat, no QR transfer needed).
#   3. Transfer testnet USDC to the self-custody buyer EOA the skill's
#      x402_get.py signs with (resolved from the OS credential store).
#
# An agent wallet CANNOT sign x402 payments: it is MPC-custodial (key shares
# are never exposed) and x402 settlement verifies EIP-3009 offchain via
# ecrecover, which needs the raw EVM key. The agent wallet is the FUNDING
# SOURCE; the transfer step moves testnet USDC to the buyer EOA.
#
# TESTNET-ONLY BY CONSTRUCTION: the chain argument is validated against the
# Circle testnet identifier list below. A mainnet chain (BASE, ETH, ...) is
# refused outright. Nothing here touches mainnet.
#
# Usage:
#   ./circle-testnet-funding.sh <buyer-eoa-address> [--chain BASE-SEPOLIA] [--amount 1.0]
#
# Examples:
#   ./circle-testnet-funding.sh 0x0102257Dc714323EAA4541Ca73A4A3A2BF2ab553
#   ./circle-testnet-funding.sh 0x0102257Dc714323EAA4541Ca73A4A3A2BF2ab553 --chain ETH-SEPOLIA --amount 0.5

set -euo pipefail

BUYER="${1:?usage: circle-testnet-funding.sh <buyer-eoa-address> [--chain BASE-SEPOLIA] [--amount 1.0]}"
CHAIN="BASE-SEPOLIA"
AMOUNT="1.0"

while [ $# -gt 1 ]; do
  case "$2" in
    --chain) CHAIN="${3:?--chain needs a value}"; shift 2 ;;
    --amount) AMOUNT="${3:?--amount needs a value}"; shift 2 ;;
    *) echo "unknown option: $2" >&2; exit 2 ;;
  esac
done

# Testnet identifiers only (Circle agent-wallet supported blockchains).
# Mainnet identifiers (BASE, ETH, ARB, ...) are refused.
case "$CHAIN" in
  BASE-SEPOLIA|ARB-SEPOLIA|ETH-SEPOLIA|OP-SEPOLIA|MATIC-AMOY|AVAX-FUJI|UNI-SEPOLIA|MONAD-TESTNET|ARC-TESTNET) ;;
  *) echo "REFUSED: '$CHAIN' is not a Circle testnet identifier. Use --chain BASE-SEPOLIA (default) or another testnet from the list; mainnet is never allowed by this script." >&2; exit 3 ;;
esac

command -v circle >/dev/null 2>&1 || {
  echo "Circle CLI not found. Install with: npm install -g @circle-fin/cli (Node.js v20.18.2+ required)" >&2
  exit 4
}

echo "== Circle CLI testnet funding: chain=$CHAIN buyer=$BUYER amount=$AMOUNT =="

echo ""
echo "[1/5] Authenticate in testnet mode (Circle emails a one-time password)"
read -r -p "   Circle account email: " EMAIL
[ -n "$EMAIL" ] || { echo "no email given; aborting" >&2; exit 5; }
echo "      circle wallet login $EMAIL --testnet"
circle wallet login "$EMAIL" --testnet

echo ""
echo "[2/5] List the agent wallet (auto-created on all supported blockchains)"
circle wallet list --type agent --chain "$CHAIN" --output json

echo ""
echo "   >> Copy the agent wallet address from the list above."
echo "   >> It is the FUNDING SOURCE. It cannot sign x402 payments."
read -r -p "   Enter the agent wallet address: " AGENT_WALLET
[ -n "$AGENT_WALLET" ] || { echo "no address given; aborting" >&2; exit 5; }

echo ""
echo "[3/5] Fund from the Circle faucet (testnet: 20 testnet USDC, no --method/--amount)"
circle wallet fund --address "$AGENT_WALLET" --chain "$CHAIN"

echo ""
echo "[4/5] Confirm the funds arrived"
circle wallet balance --address "$AGENT_WALLET" --chain "$CHAIN"

echo ""
echo "[5/5] Transfer testnet USDC to the self-custody buyer EOA the skill signs with"
echo "      circle wallet transfer $BUYER --amount $AMOUNT --address $AGENT_WALLET --chain $CHAIN"
read -r -p "   Execute this testnet transfer? [y/N] " CONFIRM
case "$CONFIRM" in
  y|Y|yes|YES)
    circle wallet transfer "$BUYER" --amount "$AMOUNT" --address "$AGENT_WALLET" --chain "$CHAIN"
    echo "Transfer submitted. Verify the buyer balance before paying:"
    echo "  python3 scripts/x402_get.py <target-url> --max-amount \"\$20\""
    ;;
  *) echo "Skipped. The buyer EOA is not funded; re-run when ready." ;;
esac
