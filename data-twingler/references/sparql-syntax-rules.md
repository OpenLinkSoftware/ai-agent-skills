# SPARQL Syntax Rules (Non-Negotiable)

Apply these structural rules to **all** SPARQL queries — template-based and ad-hoc alike.

---

## 1. UNION Placement

All `UNION` branches must be **inside** the `WHERE` block, each wrapped in braces `{ }`:

```sparql
-- ✅ Correct
SELECT ... WHERE {
  { GRAPH <g> { ?s ?p ?o } }
  UNION
  { GRAPH <g1> { ?s ?p ?o } }
}

-- ❌ Wrong — UNION outside WHERE or between separate WHERE clauses
SELECT ... WHERE {
  GRAPH <g> { ?s ?p ?o }
}
UNION
{
  GRAPH <g1> { ?s ?p ?o }
}
```

Each branch is a self-contained group.

---

## 2. SERVICE Block Requirements

Every `SERVICE` block **must** contain a `SELECT` with an inner `LIMIT`:

```sparql
-- ✅ Correct
SERVICE <http://dbpedia.org/sparql> {
  SELECT ?s WHERE { ... } LIMIT 10
}

-- ❌ Wrong — no inner LIMIT
SERVICE <http://dbpedia.org/sparql> {
  ?s ?p ?o .
}
```

---

## 3. bif:contains Usage

`bif:contains` is an **operator**, not a function. Do **not** wrap it in parentheses:

```sparql
-- ✅ Correct
?name bif:contains 'search term' OPTION (score ?sc)

-- ❌ Wrong — treated as function call
bif:contains(?name, 'search term')
```

Use single quotes only for the search string. Attach `OPTION` clause directly after the search string.

### 3.1. Boolean Search Expressions

`bif:contains` expects a **boolean search expression**, not natural language.
Bare multi-word strings without operators will cause a syntax error (`XM029`).

**Always use boolean operators between terms:**

```sparql
-- ✅ Correct — explicit AND
?o1 bif:contains 'multi-agent AND coordination' OPTION (score ?sc)

-- ✅ Correct — explicit OR
?o1 bif:contains 'agent OR orchestration' OPTION (score ?sc)

-- ✅ Correct — parenthesised group
?o1 bif:contains '(multi-agent AND coordination AND production)' OPTION (score ?sc)

-- ❌ Wrong — natural language causes XM029 syntax error
?o1 bif:contains 'multi-agent coordination mean here' OPTION (score ?sc)

-- ❌ Wrong — treated as function call
bif:contains(?name, 'multi-agent coordination')
```

**Term extraction rule:** When converting a user's natural language prompt
to a `bif:contains` expression, extract the key substantive terms and join
them with `AND`. Drop stop words ("what", "does", "mean", "here", etc.).

---

## 4. FILTER Placement

- `FILTER` clauses belong at the same level as the triple patterns they constrain.
- Do **not** nest `FILTER` inside `OPTIONAL` unless the filter applies only to that optional branch.
- When filtering across multiple values, use `IN()` or `OR` within a **single** `FILTER` block rather than multiple `FILTER` clauses.

```sparql
-- ✅ Correct — single FILTER with IN
FILTER (?name IN ("a", "b", "c"))

-- ✅ Correct — single FILTER with OR
FILTER (?name = "a" || ?name = "b" || ?name = "c")
```

---

## 5. GRAPH Block Structure

Each `GRAPH` clause must have its triple patterns fully enclosed:

```sparql
-- ✅ Correct
SELECT ... WHERE {
  GRAPH <iri> {
    ?s a ?type .
    ?s ?p ?o .
  }
}
```

When combining multiple graphs, use `UNION` inside `WHERE` (see Rule 1).

---

## 6. Pre-Execution Structural Validation

Before executing any SPARQL query, verify:
- All `UNION` branches are inside `WHERE` and braced `{ }`
- All `SERVICE` blocks have an inner `LIMIT`
- `bif:contains` is used as an operator (not a function)
- `FILTER` clauses are at the correct nesting level
- `OPTIONAL` blocks are properly closed
- No trailing or orphaned braces

---

## 7. Ad-Hoc Query Templates

When writing queries not covered by `query-templates.md`, follow these canonical structural patterns:

### Describe Entity
```sparql
SELECT DISTINCT ?s ?p ?o
WHERE {
  GRAPH <g> {
    <entity-iri> ?p ?o .
    BIND(<entity-iri> AS ?s)
  }
}
```

### Multi-Entity Describe (use UNION, not multiple WHERE blocks)
```sparql
SELECT DISTINCT ?s ?p ?o
WHERE {
  {
    GRAPH <g> { <entity1> ?p ?o . }
    BIND(<entity1> AS ?s)
  }
  UNION
  {
    GRAPH <g> { <entity2> ?p ?o . }
    BIND(<entity2> AS ?s)
  }
}
```

### Full-Text Search with Scoring
```sparql
PREFIX bif: <bif:>
SELECT ?s ?p ?o (?sc AS ?score)
WHERE {
  GRAPH ?g {
    ?s ?p ?o .
    ?o bif:contains '(term1 AND term2)' OPTION (score ?sc) .
    FILTER (?sc >= 10)
  }
}
ORDER BY DESC(?sc)
```
