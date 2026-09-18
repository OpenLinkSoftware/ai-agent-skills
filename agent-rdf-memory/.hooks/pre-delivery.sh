#!/bin/bash
set -e
# Pre-delivery blocking gate — run before delivering any HTML+RDF set
# Usage: ./pre-delivery.sh /path/to/webpages/stem.html --ttl /path/to/rdf/stem.ttl --jsonld /path/to/rdf/stem.jsonld

HTML="$1"
TTL="$3"
JSONLD="$5"
if [ -z "$HTML" ]; then echo "Usage: $0 <html> --ttl <ttl> --jsonld <jsonld>"; exit 1; fi

echo "=== Gate: validate-harness-contract.py ==="
python3 /Users/kidehen/Documents/Management/Development/ai-agent-skills/rdf-infographic-skill/scripts/validate-harness-contract.py "$HTML" --ttl "$TTL" --jsonld "$JSONLD"
echo "=== Gate: KG curated by + actedOnBehalfOf ==="
grep -q "KG curated by" "$HTML" || { echo "FAIL: hero 'KG curated by' missing"; exit 1; }
grep -q "on behalf of" "$HTML" || { echo "FAIL: hero 'on behalf of' missing"; exit 1; }
grep -q "accountablePerson" "$HTML" || { echo "FAIL: JSON-LD accountablePerson missing"; exit 1; }
grep -q "actedOnBehalfOf" "$TTL" || { echo "FAIL: TTL actedOnBehalfOf missing"; exit 1; }
echo "=== Gate: guarded dark mode ==="
grep -q ':root:not(\[data-theme="light"\])' "$HTML" || grep -q ':root:not(\[data-theme' /Users/kidehen/Documents/Management/Development/ai-agent-skills/rdf-infographic-skill/scripts/templates/styles.css || { echo "FAIL: guarded :root:not([data-theme]) missing"; exit 1; }
echo "=== Gate: nav 9-gate checklist (howto/nav-gates-aggregated.ttl) ==="
grep -q 'id="floating-nav"' "$HTML" || { echo "FAIL: nav id floating-nav missing"; exit 1; }
grep -q 'id="nav-hide"' "$HTML" || { echo "FAIL: nav-hide missing"; exit 1; }
grep -q 'manuallyHidden' "$HTML" || { echo "FAIL: manuallyHidden flag missing"; exit 1; }
grep -q '__navFadeOut' "$HTML" || { echo "FAIL: __navFadeOut missing"; exit 1; }
echo "All gates PASS"
