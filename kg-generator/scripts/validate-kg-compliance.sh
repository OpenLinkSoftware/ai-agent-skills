#!/usr/bin/env bash
# validate-kg-compliance.sh — Automated compliance audit for KG generator output
# Usage: ./validate-kg-compliance.sh <file.ttl|file.jsonld> [--turtle|--jsonld]

set -euo pipefail

FILE="$1"
FORMAT="${2:-}"

if [ ! -f "$FILE" ]; then
  echo "ERROR: File not found: $FILE"
  exit 1
fi

# Auto-detect format from extension
if [ -z "$FORMAT" ]; then
  case "$FILE" in
    *.ttl)   FORMAT="--turtle" ;;
    *.jsonld) FORMAT="--jsonld" ;;
    *)       echo "ERROR: Cannot auto-detect format. Pass --turtle or --jsonld"; exit 1 ;;
  esac
fi

PASS=0
FAIL=0
CONTENT=$(cat "$FILE")

pass() { echo "  PASS  $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL  $1 — $2"; FAIL=$((FAIL + 1)); }

echo "=== KG Compliance Audit: $FILE ==="
echo ""

if [ "$FORMAT" = "--turtle" ]; then
  # ── Turtle-specific checks ──

  # 1. schema: namespace is HTTP not HTTPS
  if echo "$CONTENT" | grep -q '@prefix[[:space:]]\+schema:[[:space:]]*<http://schema.org/>'; then
    pass "schema: namespace uses http://schema.org/"
  elif echo "$CONTENT" | grep -q '@prefix[[:space:]]\+schema:[[:space:]]*<https://schema.org/>'; then
    fail "schema: namespace uses https://schema.org/ (must be http://schema.org/)" "Change @prefix schema: <https://schema.org/> to <http://schema.org/>"
  else
    fail "schema: namespace not found or uses non-standard prefix" "Add @prefix schema: <http://schema.org/>"
  fi

  # 2. No file: scheme IRIs
  if echo "$CONTENT" | grep -q 'file://'; then
    fail "file: scheme IRIs found" "$(echo "$CONTENT" | grep -n 'file://' | head -3 | sed 's/^/    Line /')"
  else
    pass "No file: scheme IRIs"
  fi

  # 3. FAQPage wrapper with mainEntity
  if echo "$CONTENT" | grep -q 'schema:FAQPage'; then
    pass "schema:FAQPage present"
    if echo "$CONTENT" | grep -q 'schema:mainEntity'; then
      pass "FAQPage has schema:mainEntity"
    else
      fail "FAQPage missing schema:mainEntity" "Add schema:mainEntity listing all question IRIs"
    fi
  else
    fail "No schema:FAQPage wrapper" "Wrap all schema:Question entities in a schema:FAQPage"
  fi

  # 4. DefinedTermSet wrapper with hasDefinedTerm
  if echo "$CONTENT" | grep -q 'schema:DefinedTermSet'; then
    pass "schema:DefinedTermSet present"
    if echo "$CONTENT" | grep -q 'schema:hasDefinedTerm'; then
      pass "DefinedTermSet has schema:hasDefinedTerm"
    else
      fail "DefinedTermSet missing schema:hasDefinedTerm" "Add schema:hasDefinedTerm listing all term IRIs"
    fi
  else
    fail "No schema:DefinedTermSet wrapper" "Wrap all glossary terms in a schema:DefinedTermSet"
  fi

  # 5. Main article/report has schema:hasPart
  if echo "$CONTENT" | grep -q 'schema:hasPart'; then
    pass "Article has schema:hasPart"
  else
    fail "Article missing schema:hasPart" "Add schema:hasPart linking FAQPage, DefinedTermSet, and HowTo"
  fi

  # 6. owl:sameAs used for DBpedia (not schema:sameAs)
  if echo "$CONTENT" | grep -q 'schema:sameAs.*dbpedia'; then
    fail "schema:sameAs used for DBpedia links" "Replace schema:sameAs with owl:sameAs"
  else
    pass "No schema:sameAs for DBpedia"
  fi

  # 7. Prefix declarations use expanded IRIs for external namespaces
  if echo "$CONTENT" | grep -qE 'owl:[[:space:]]*<http://www.w3.org/2002/07/owl#>'; then
    pass "owl: namespace declared"
  else
    fail "owl: namespace not declared" "Add @prefix owl: <http://www.w3.org/2002/07/owl#>"
  fi

  # 8. @prefix : uses https: (not file:)
  BASE=$(echo "$CONTENT" | sed -n 's/.*@prefix[[:space:]]*:[[:space:]]*<\([^>]*\)>.*/\1/p' | head -1)
  if [ -n "$BASE" ]; then
    if echo "$BASE" | grep -q '^https\?://'; then
      pass "@prefix : uses $BASE"
    else
      fail "@prefix : uses non-HTTP scheme: $BASE" "Use the canonical https: URL of the source document"
    fi
  fi

  # 9. FAQ question count
  FAQ_COUNT=$(echo "$CONTENT" | grep -c 'a schema:Question')
  if [ "$FAQ_COUNT" -ge 8 ]; then
    pass "FAQ question count: $FAQ_COUNT"
  else
    fail "FAQ question count: $FAQ_COUNT (should be >= 8)" "Add more schema:Question entities"
  fi

  # 10. HowTo steps (if present)
  HOWTO_COUNT=$(echo "$CONTENT" | grep -c 'a schema:HowToStep' || true)
  if [ "$HOWTO_COUNT" -gt 0 ]; then
    if echo "$CONTENT" | grep -q 'a schema:HowTo'; then
      pass "HowTo present ($HOWTO_COUNT steps)"
    else
      fail "HowToSteps present but no schema:HowTo wrapper" "Wrap steps in a schema:HowTo"
    fi
  fi

  # 11. Ontology: rdfs:isDefinedBy on classes and properties
  ONTOLOGY_COUNT=$(echo "$CONTENT" | grep -c 'a owl:Ontology' || true)
  if [ "$ONTOLOGY_COUNT" -gt 0 ]; then
    HAS_NAME=$(echo "$CONTENT" | grep -c 'schema:name' || true)
    HAS_DESC=$(echo "$CONTENT" | grep -c 'schema:description' || true)
    if [ "$HAS_NAME" -gt 0 ] && [ "$HAS_DESC" -gt 0 ]; then
      pass "Ontology has schema:name and schema:description"
    else
      fail "Ontology missing schema:name or schema:description" "Add schema:name and schema:description to the owl:Ontology"
    fi
    CLASS_COUNT=$(echo "$CONTENT" | grep -c 'a owl:Class' || true)
    PROP_COUNT=$(echo "$CONTENT" | grep -c 'a owl:ObjectProperty' || true)
    DEFINEDBY_COUNT=$(echo "$CONTENT" | grep -c 'rdfs:isDefinedBy' || true)
    NEEDED=$((CLASS_COUNT + PROP_COUNT))
    if [ "$DEFINEDBY_COUNT" -ge "$NEEDED" ]; then
      pass "All classes/properties have rdfs:isDefinedBy ($DEFINEDBY_COUNT/$NEEDED)"
    else
      fail "Missing rdfs:isDefinedBy ($DEFINEDBY_COUNT of $NEEDED classes/properties)" "Add rdfs:isDefinedBy : to each class and property"
    fi
  fi

  # 12. Fully expanded DBpedia/Wikidata IRIs (not CURIEs)
  if echo "$CONTENT" | grep -qE 'dbo:|dbp:|dbr:|wd:|wdt:'; then
    CURIEs=$(echo "$CONTENT" | grep -nE 'dbo:|dbp:|dbr:|wd:|wdt:' | head -5)
    fail "Prefixed DBpedia/Wikidata CURIEs found (must be fully expanded)" "$CURIEs"
  else
    pass "No DBpedia/Wikidata CURIEs (all expanded)"
  fi

elif [ "$FORMAT" = "--jsonld" ]; then
  # ── JSON-LD-specific checks ──

  # 1. @base set
  if echo "$CONTENT" | grep -q '"@base"'; then
    pass "@base present"
  else
    fail "@base not set" "Add @base with the canonical source URL"
  fi

  # 2. schema: namespace HTTP not HTTPS
  if echo "$CONTENT" | grep -q '"schema":[[:space:]]*"http://schema.org/"'; then
    pass "schema: namespace uses http://schema.org/"
  elif echo "$CONTENT" | grep -q 'schema.*https://schema.org/'; then
    fail "schema: namespace uses https://schema.org/" "Change to http://schema.org/"
  fi

  # 3. FAQPage
  if echo "$CONTENT" | grep -q '"FAQPage"'; then
    pass "schema:FAQPage present"
  else
    fail "No schema:FAQPage" "Wrap questions in a FAQPage"
  fi

  # 4. DefinedTermSet
  if echo "$CONTENT" | grep -q '"DefinedTermSet"'; then
    pass "schema:DefinedTermSet present"
  else
    fail "No schema:DefinedTermSet" "Wrap glossary terms in a DefinedTermSet"
  fi

  # 5. hasPart
  if echo "$CONTENT" | grep -q '"hasPart"'; then
    pass "hasPart linking present"
  else
    fail "No hasPart" "Use hasPart to link FAQ, glossary, howto to article"
  fi

  # 6. owl:sameAs (not schema:sameAs)
  if echo "$CONTENT" | grep -q '"schema:sameAs".*dbpedia'; then
    fail "schema:sameAs used for DBpedia" "Replace with owl:sameAs"
  else
    pass "No schema:sameAs for DBpedia"
  fi

  # 7. Question count
  Q_COUNT=$(echo "$CONTENT" | grep -o '"Question"' | wc -l | tr -d ' ')
  if [ "$Q_COUNT" -ge 8 ]; then
    pass "Question count: $Q_COUNT"
  else
    fail "Question count: $Q_COUNT (should be >= 8)" "Add more Question entities"
  fi

  # 8. No file: IRIs
  if echo "$CONTENT" | grep -q 'file://'; then
    fail "file: scheme IRIs found"
  else
    pass "No file: scheme IRIs"
  fi

  # 9. owl:sameAs uses @id
  if echo "$CONTENT" | grep -q '"owl:sameAs".*\n.*@id'; then
    pass "owl:sameAs uses @id"
  elif echo "$CONTENT" | grep -q '"owl:sameAs"' && ! echo "$CONTENT" | grep -q '"owl:sameAs".*@id'; then
    fail "owl:sameAs may have plain literal values" "Use @id for owl:sameAs values"
  else
    pass "No owl:sameAs issues detected"
  fi
fi

# ── Common checks for both formats ──

# Smart quotes check
if echo "$CONTENT" | grep -q $'\xe2\x80\x9c\|\xe2\x80\x9d'; then
  fail "Smart/curly quotes found" "$(echo "$CONTENT" | grep -n $'\xe2\x80\x9c' | head -3)"
else
  pass "No smart/curly quotes"
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ "$FAIL" -gt 0 ]; then
  echo "COMPLIANCE: FAIL ($FAIL issue(s) to fix)"
  exit 1
else
  echo "COMPLIANCE: PASS"
  exit 0
fi
