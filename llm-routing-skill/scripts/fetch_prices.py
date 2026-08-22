#!/usr/bin/env python3
"""fetch_prices.py — Fetch current + historical LLM pricing from llm-prices.com.

The llm-prices project (github.com/simonw/llm-prices, https://www.llm-prices.com/)
is the canonical dynamic pricing source for this skill. This script pulls its
two live JSON feeds and caches them locally so the routing-graph build has a
fresh, reproducible input.

Endpoints (documented in llm-prices/README.md):
  current-v1.json     — one price record per model (input/output/cached per MTok)
  historical-v1.json  — every price change window (from_date/to_date)

Usage:
  python3 scripts/fetch_prices.py                 # cache to scripts/.cache/
  python3 scripts/fetch_prices.py --out /tmp/     # cache elsewhere
  python3 scripts/fetch_prices.py --no-cache      # print to stdout only

Exit codes: 0 ok; 1 network failure (cache left untouched).
"""
import argparse
import json
import os
import sys
import urllib.request

BASE = "https://www.llm-prices.com"
FEEDS = {
    "current": f"{BASE}/current-v1.json",
    "historical": f"{BASE}/historical-v1.json",
}


def fetch(url: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "llm-routing-skill/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch llm-prices.com JSON feeds")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), ".cache"),
                    help="cache directory (default: scripts/.cache)")
    ap.add_argument("--no-cache", action="store_true", help="print to stdout, write nothing")
    args = ap.parse_args()

    if args.no_cache:
        for name, url in FEEDS.items():
            data = fetch(url)
            print(f"# {name}")
            print(json.dumps(data, indent=2))
        return 0

    os.makedirs(args.out, exist_ok=True)
    for name, url in FEEDS.items():
        path = os.path.join(args.out, f"{name}-v1.json")
        data = fetch(url)
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2)
        updated = data.get("updated_at", "n/a")
        count = len(data.get("prices", []))
        print(f"OK  {name:10s} -> {path}  (updated_at={updated}, {count} records)")

    print("Prices fetched. Run scripts/build_routing_graph.py to rebuild the graph.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # network / json errors
        print(f"ERROR: fetch failed: {exc}", file=sys.stderr)
        sys.exit(1)
