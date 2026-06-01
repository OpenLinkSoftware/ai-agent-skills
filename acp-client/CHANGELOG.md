# Changelog

## 1.0.2 — 2026-05-30

### Added

- **Balance payment method**: Added `handler_id: "balance"` as an alternative to Stripe SPT for completing checkouts when the user has sufficient ACP account credit.

## 1.0.1 — 2026-05-30

### Added

- **Product catalog**: Added Special Price and Retail Price columns for all catalogued offers.
- **Price validation note**: Documented the $0 checkout issue and the `2024-01` vs `2024-02` version discrepancy.

### Fixed

- **Product catalog**: Corrected JDBC to ODBC bridge driver offer IRI from `2024-02` (zero-priced, causes payment decline) to `2024-01` ($49.99, validated working).

## 1.0.0 — 2026-05-29

### Initial Release

- Intent-driven ACP client skill derived from `acp_curl.sh`
- Natural language purchase intent mapping ("I want to purchase X")
- Product catalog resolution from OpenLink TTL sources:
  - Virtuoso Enterprise Offers
  - OPAL Knowledge Graph Access Offers
  - UDA Lite Edition Offers
- Full checkout flow: create → get total → Stripe SPT → complete
- Cart lifecycle: create → get → update → cancel
- Order retrieval
- Manual OAuth bearer token acquisition via `applications.vsp`
- Composable `curl` recipes with `jq`/`awk` JSON helpers
- Human-readable and `--json` output modes
