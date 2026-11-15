# Data Twingler — Query Templates Reference

Placeholders: `{G}` = graph IRI, `{E}` = endpoint IRI,
`{Name}` = matched name from index step, `{Article Title}` = article title.

For 2-step templates (T5, T6, T7):
1. Run the **index query** to get a list of `?name` values.
2. Similarity-match the user's input to the closest `?name`.
3. Assign the match to `{Name}` and run the **final query**.
4. If prompt has multiple items, use `FILTER(?name IN ("a","b",...))`.

---

## T1 — Entire Data Space Exploration

**Trigger:** "Provide a starting point for exploring this Data Space"

```sparql
SPARQL
SELECT (SAMPLE(?s) AS ?EntityID) (COUNT(*) AS ?count) (?o AS ?EntityTypeID) (?g AS ?kg)
WHERE { GRAPH ?g { ?s a ?o. } }
GROUP BY ?o ?g
HAVING (COUNT(*) > 20000)
ORDER BY ASC(?g) DESC(?count)
LIMIT 50
```

---

## T2 — Specific Knowledge Graph Exploration

**Trigger:** "Provide a starting point for exploring knowledge graph {G}"
**Hint:** If `{G}` not provided, bind to `?g`.

```sparql
SPARQL
SELECT (SAMPLE(?s) AS ?EntityID) (COUNT(*) AS ?count) (?o AS ?EntityTypeID)
WHERE { GRAPH {G} { ?s a ?o. } }
GROUP BY ?o
ORDER BY DESC(?count)
LIMIT 50
```

---

## T3 — KG Exploration with Reasoning & Inference

**Trigger:** "Explore knowledge graph {G} with reasoning & inference applied"

```sparql
SPARQL DEFINE input:inference "urn:rdfs:subclass:subproperty:inference:rules"
SELECT (SAMPLE(?s) AS ?EntityID) (COUNT(*) AS ?count) (?o AS ?EntityTypeID)
WHERE { GRAPH {G} { ?s a ?o. } }
GROUP BY ?o
ORDER BY DESC(?count)
LIMIT 50
```

---

## T4 — Remote Endpoint KG Exploration (SPARQL-FED via SPASQL)

**Trigger:** "Using the endpoint {E}, explore the knowledge graph {G}"

```sparql
SPARQL
SELECT ?s ?count ?o
WHERE {
  SERVICE <{E}> {
    SELECT ?s (COUNT(?s) AS ?count) ?o
    WHERE { GRAPH <{G}> { ?s a ?o . } }
    GROUP BY ?s ?o
    ORDER BY DESC(?count)
    LIMIT 50
  }
}
```

---

## T5 — How-To Oriented Exploration (2-step)

**Trigger:** "How to {User Input}"

### Step 0.5 — Structured HowTo preflight (before broad discovery)

For T5 prompts, first enumerate `schema:HowTo` nodes directly. Match against
the HowTo IRI, name, description, and any known source/article text. Include
named-entity spelling variants from the prompt (for example, `Akash` and
`Aakash`) in `{term1}`, `{term2}`, etc.

```sparql
SPARQL
SELECT DISTINCT ?howto ?name ?description ?article ?articleTitle ?g
WHERE {
  GRAPH ?g {
    ?howto a schema:HowTo.
    OPTIONAL { ?howto schema:name ?name }
    OPTIONAL { ?howto schema:description ?description }
    OPTIONAL {
      ?howto schema:isPartOf|^schema:hasPart ?article.
      OPTIONAL {
        ?article (schema:name | schema:headline | schema:title | rdfs:label) ?articleTitle.
      }
    }
    BIND(LCASE(CONCAT(
      STR(?howto), " ",
      COALESCE(STR(?name), ""), " ",
      COALESCE(STR(?description), ""), " ",
      COALESCE(STR(?article), ""), " ",
      COALESCE(STR(?articleTitle), "")
    )) AS ?searchText)
    FILTER (
      CONTAINS(?searchText, "{term1}") ||
      CONTAINS(?searchText, "{term2}") ||
      CONTAINS(?searchText, "{term3}")
    )
  }
}
LIMIT 80
```

When this preflight finds a HowTo, retrieve its ordered steps before using
broad keyword/entity discovery:

```sparql
SPARQL
SELECT DISTINCT ?step ?position ?name ?text
WHERE {
  GRAPH {G} {
    <{HowToIRI}> schema:step ?step.
    ?step a schema:HowToStep.
    OPTIONAL { ?step schema:position ?position }
    OPTIONAL { ?step schema:name ?name }
    OPTIONAL { ?step schema:text ?stepText }
    OPTIONAL { ?step schema:itemListElement ?itemText }
    BIND(COALESCE(?stepText, ?itemText) AS ?text)
  }
}
ORDER BY ASC(?position)
```

### Step 1 — Index query (build `?name` list)

```sparql
SPARQL
SELECT DISTINCT ?name
WHERE {
  GRAPH {G} {
    ?guide a schema:HowTo; schema:name ?name.
    OPTIONAL {
      ?article schema:hasPart ?guide;
               (schema:name | schema:headline | schema:title | rdfs:label) "{Article Title}".
      OPTIONAL { ?article schema:datePublished ?datePublished }
      OPTIONAL { ?article schema:author [schema:name ?author] }
    }
  }
}
```

### Step 2 — Final query (after matching `{Name}`)

```sparql
SPARQL
SELECT DISTINCT ?guide ?name ?step ?position ?text ?article ?articleTitle ?publisher ?publisherName
WHERE {
  GRAPH {G} {
    ?guide a schema:HowTo; schema:step ?step.
    ?step schema:name ?text; schema:position ?position.
    ?guide schema:name "{Name}".
    OPTIONAL {
      ?article schema:hasPart ?guide;
               (schema:name | schema:headline | schema:title | rdfs:label) "{Article Title}";
               schema:publisher ?publisher.
      ?publisher schema:name ?publisherName.
    }
  }
}
ORDER BY ASC(?position)
```

---

## T6 — Question-Oriented Exploration (2-step)

**Trigger:** "{Question}" in context of an article or graph

### Step 1 — Index query (multi-graph UNION)

```sparql
SPARQL
SELECT DISTINCT ?name
WHERE {
  { OPTIONAL { GRAPH ?g {
      ?article (schema:name | schema:headline | schema:title | rdfs:label) ?title ;
               (schema:hasPart | schema:mainEntity | schema:question) ?question.
      OPTIONAL { ?article schema:datePublished ?datePublished }
      OPTIONAL { ?article schema:author [schema:name ?author] }
      ?question a schema:Question; schema:name ?name.
  } } }
  UNION
  { OPTIONAL { GRAPH ?g1 {
      ?article (schema:name | schema:headline | schema:title | rdfs:label) "{Article Title}" ;
               ((schema:hasPart | schema:articleSection))/((schema:mainEntity | schema:hasPart)) ?question.
      OPTIONAL { ?article schema:datePublished ?datePublished }
      ?question a schema:Question; schema:name ?name.
  } } }
  UNION
  { OPTIONAL { GRAPH ?g2 {
      ?article (schema:name | schema:headline | schema:title | rdfs:label) "{Article Title}" ;
               (schema:hasPart/schema:hasPart) ?question.
      OPTIONAL { ?article schema:datePublished ?datePublished }
      ?question a schema:Question; schema:name ?name.
  } } }
}
```

### Step 1 Fallback 1 — Direct Question scan (no article relationship)

If the primary index query returns zero results, try this pattern **once**:

```sparql
SPARQL
SELECT DISTINCT ?s ?name
WHERE {
  GRAPH {G} {
    ?s a schema:Question.
    OPTIONAL { ?s schema:name ?name }
    OPTIONAL { ?s schema:text ?name }
  }
}
```

### Step 1 Fallback 2 — Broad index (key-term search)

If Fallback 1 also returns zero results, try this pattern **once** more:

```sparql
SPARQL
PREFIX bif: <bif:>
SELECT DISTINCT ?s ?o
WHERE {
  GRAPH {G} {
    ?s ?p ?o .
    ?o bif:contains '({term})'
  }
}
LIMIT 20
```

### Step 2 — Final query (after matching `{Name}`)

```sparql
SPARQL
SELECT DISTINCT ?question ?name ?answer ?answerText ?article ?articleTitle ?publisher ?publisherName
WHERE {
  { OPTIONAL { GRAPH {G} {
      ?question a schema:Question; schema:name ?name; schema:acceptedAnswer ?answer.
      FILTER (?name = "{Name}").
      ?answer schema:text ?answerText.
      ?article (schema:hasPart | schema:mainEntity | schema:question) ?question;
               (schema:name | schema:headline | schema:title | rdfs:label) "{Article Title}";
               schema:publisher ?publisher.
      ?publisher schema:name ?publisherName.
  } } }
  UNION { OPTIONAL { GRAPH {G1} {
      ?question a schema:Question; schema:name "{Name}"; schema:acceptedAnswer ?answer.
      ?answer schema:text ?answerText.
      ?article ((schema:hasPart | schema:articleSection))/((schema:mainEntity | schema:hasPart)) ?question;
               (schema:name | schema:headline | schema:title | rdfs:label) "{Article Title}";
               schema:publisher ?publisher.
      ?publisher schema:name ?publisherName.
  } } }
  UNION { OPTIONAL { GRAPH {G2} {
      ?question a schema:Question; schema:name "{Name}"; schema:acceptedAnswer ?answer.
      ?answer schema:text ?answerText.
      ?article (schema:hasPart/schema:hasPart) ?question;
               (schema:name | schema:headline | schema:title | rdfs:label) "{Article Title}";
               schema:publisher ?publisher.
      ?publisher schema:name ?publisherName.
  } } }
}
ORDER BY ASC(?name)
```

**Alternative final query** (when the Question uses `schema:text` instead of `schema:name`):

```sparql
SPARQL
SELECT DISTINCT ?question ?text ?answer ?answerText
WHERE {
  GRAPH {G} {
    ?question a schema:Question; schema:text ?text; schema:acceptedAnswer ?answer.
    FILTER (?text = "{Name}").
    ?answer schema:text ?answerText.
  }
}
```

---

## T7 — Defined Terms Exploration (2-step)

**Trigger:** "Define the term {User Input}"

### Step 1 — Index query (build `?name` list)

```sparql
SPARQL
SELECT DISTINCT ?name
WHERE {
  GRAPH {G} {
    ?article schema:hasPart ?termSet;
             (schema:name | schema:headline | schema:title | rdfs:label) "{Article Title}".
    OPTIONAL { ?article schema:datePublished ?datePublished }
    OPTIONAL { ?article schema:author [schema:name ?author] }
    ?termSet a schema:DefinedTermSet; schema:hasDefinedTerm ?term.
    ?term schema:name ?name.
  }
}
```

### Step 2 — Final query (after matching `{Name}`)

```sparql
SPARQL
SELECT DISTINCT ?term ?name ?desc ?article ?articleTitle ?publisher ?publisherName ?author ?authorName ?authorUrl
WHERE {
  GRAPH {G} {
    ?term a schema:DefinedTerm; schema:name "{Name}"; schema:description ?desc.
    OPTIONAL {
      ?article schema:about ?term;
               (schema:name | schema:headline | schema:title | rdfs:label) "{Article Title}";
               schema:publisher ?publisher.
      ?publisher schema:name ?publisherName.
    }
    OPTIONAL {
      ?article schema:author ?author.
      ?author schema:url ?authorUrl; schema:name ?authorName.
    }
  }
}
ORDER BY ASC(?name)
```

---

## T8 — Direct Entity Description (1-step, no index required)

**Trigger:** "What is {X}?", "Can you explain what {X} is?", "Tell me about {X}"
— when the Graph IRI Discovery step (Step 1) returns a `?s1` with `?o1` as a
`schema:description` or `schema:text` attached to a non-article entity type
(`schema:Product`, `schema:SoftwareApplication`, `schema:HowTo`, etc.)

### Execution

No index query is needed. The `?s1` IRI and `?o1` literal from Step 1 are the
answer. Run a follow-up describe query to enrich the result:

```sparql
SPARQL
SELECT DISTINCT ?p ?o
WHERE {
  GRAPH {G} {
    <{s1}> ?p ?o .
  }
}
```

Present the `?o1` value from Step 1 as the primary answer, enriched with
additional properties from this describe query (features, type, brand, etc.).

---

## VP — Vector Capability Probe (mandatory before any vector step)

Run once per endpoint per session, before T9, VD, the legacy cosine path, or a
vector semantic-variant retry. Cache the outcome as the endpoint's capability
record (see the Vector Capability Probe Gate in `SKILL.md`).

**Probe 1 — `bif:vector_search`:**

```sparql
SELECT ?doc
WHERE {
  ?doc bif:vector_search "probe" option (INDEX *, LIMIT 1, ef_search 1) .
}
```

| Response | Record |
|---|---|
| Rows, or an empty result set | `bif_vector_search = yes` |
| `SP030` syntax error at `INDEX` (the compiler does not know the option list) or unknown `bif:vector_search` | `bif_vector_search = no` |
| `VEC58` / `VEC59` (no active index, or several when none named) | `yes`, but name an index explicitly |
| Timeout, TLS or network failure | `unknown` — report it; do not record `no` |

**Probe 2 — legacy cosine (only if Probe 1 says `no`):**

```sparql
PREFIX vvec: <http://www.openlinksw.com/ontology/vvec#>
ASK { ?t vvec:hasEmbedding true }
```

If `true`, call the function once on one embedded entity:

```sparql
PREFIX vvec: <http://www.openlinksw.com/ontology/vvec#>
SELECT ?t (sql:vvec_cosine_similarity_openai(?t, "probe") AS ?score)
WHERE { ?t vvec:hasEmbedding true }
LIMIT 1
```

A result means `vvec_cosine = yes`; `SR186` (no permission to execute) means
`vvec_cosine = auth-required`.

Observed 2026-11-15 (re-probe every session; these are hints only):

| Endpoint | Probe 1 | Probe 2 |
|---|---|---|
| `https://vec.demo.openlinksw.com/sparql` | yes | no embedded entities |
| `https://demo.openlinksw.com/sparql` | no (`SP030` at `INDEX`) | ASK true; function `SR186` → auth-required |
| `https://linkeddata.uriburner.com/sparql` | no vector support (per OpenLink) | — |

---

## VD — Vector Discovery (Graph IRI Discovery step 1b-A)

Used inside T5–T8 discovery, alongside the keyword query, when the endpoint's
`bif_vector_search = yes`. Returns graph, type and label per hit so the hit
feeds the index and final steps directly. Verified on vec.demo.openlinksw.com.

```sparql
DEFINE input:storage ""
SELECT ?doc ?score
       (SAMPLE(?t) AS ?type) (SAMPLE(?l) AS ?label) (SAMPLE(?g) AS ?graph)
WHERE {
  ?doc bif:vector_search "{user prompt}"
    option (INDEX *, ranking relevance, score ?score,
            LIMIT {Vector Discovery Candidates}, ef_search 100) .
  OPTIONAL { GRAPH ?g { ?doc a ?t } }
  OPTIONAL { ?doc rdfs:label | schema:name ?l }
}
GROUP BY ?doc ?score
ORDER BY DESC(?score)
```

`?graph` / `?type` can be unbound for hits whose type triple lives in no named
graph the caller can read; describe such hits with T8. Rank by row order
(`ranking relevance` already merges per-index ranks) when fusing with the
keyword list.

---

## VX — Vector Hit Expansion (Graph IRI Discovery step 1d)

One hop, both directions, from the top fused seeds. Verified on
vec.demo.openlinksw.com. Declare every prefix — `dct:` and `dbo:` are not
predefined everywhere (`SP030 Undefined namespace prefix`).

```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
SELECT ?seed ?p ?n (SAMPLE(?l) AS ?label)
WHERE {
  VALUES ?seed { <{seed-IRI-1}> <{seed-IRI-2}> <{seed-IRI-3}> }
  { ?seed ?p ?n } UNION { ?n ?p ?seed }
  FILTER (isIRI(?n))
  FILTER (?p IN (owl:sameAs, skos:exactMatch, skos:related, skos:broader,
                 dbo:wikiPageRedirects, schema:about, schema:isPartOf,
                 schema:mentions, rdfs:seeAlso))
  OPTIONAL { ?n rdfs:label | schema:name ?l }
}
GROUP BY ?seed ?p ?n
LIMIT 50
```

---

## T9 — Vector / Hybrid Search with Index Selection

**Trigger:** "Vector search for {X}", "Semantic search for {X}",
"Hybrid search for {X}"

**Prerequisite:** the endpoint passed VP Probe 1 in this session. If not, say
so and offer `https://vec.demo.openlinksw.com/sparql`.

### Vector search — all indexes

```sparql
SPARQL DEFINE input:storage ""
SELECT ?doc ?score ?distance
WHERE {
  ?doc bif:vector_search "reset customer password"
  option (
    INDEX *,
    ranking relevance,
    score ?score,
    distance ?distance,
    LIMIT 10,
    ef_search 100
  ) .
}
ORDER BY DESC(?score)
;
```

Replace the example search text with the user's text, escaped as a SPARQL
string literal. Preserve natural language for `bif:vector_search`; the boolean
term rules for `bif:contains` do not apply to it. The values above are T9
defaults, independently configurable by the user. Return a table with document
IRI, score, and distance. For HTTP SPARQL execution, omit the leading `SPARQL`
SQL command marker and terminal semicolon; retain `DEFINE input:storage ""`.

Syntax pitfalls verified live on vec.demo.openlinksw.com (2026-11-15):

- The wildcard is bare `INDEX *`. The quoted form `INDEX '*'` fails with
  `SP030 syntax error at ''*''`.
- `score_limit`, `distance_limit` and `ranking raw` across indexes bound to
  different embedding models fail with `VEC68` (e.g. `minilm-384-local` vs
  `granite-384-local` on vec.demo). With `INDEX *` the default is
  `ranking relevance` (merge by rank within each index) and no score/distance
  limit. Apply limits only on a single index, or on a list of indexes that
  share a model and metric.
- Do not name the `score` / `distance` variable `?s`; it receives the
  subject instead of the value.
- One `INDEX` option per search; several indexes go in one parenthesised list.

### Select one or several indexes

Replace only the `INDEX *` option in the query above:

| Scope | Replacement |
|---|---|
| All available indexes | `INDEX *` (bare; never quoted) |
| One selected index | `INDEX <{IndexIRI}>` — `score_limit` / `distance_limit` are safe here |
| Selected indexes for graphs gx through z | `INDEX (<{IndexIRIForGx}>, <{IndexIRIForGy}>, <{IndexIRIForGz}>)` |

The list is comma-separated inside parentheses, under a single `INDEX` option;
expand or shorten it to the requested set. Substitute verified index IRIs from
T10 or the user's supplied index configuration. A named graph IRI identifies
an index's data scope; `INDEX` takes the associated **index IRI**, which can
differ from the graph IRI. If their mapping is unclear, inspect the selected
index's metadata/configuration or ask for the association. Do not invent it.

Keep `ef_search >= LIMIT`. When using `score_limit` or `distance_limit` across
multiple indexes, select indexes sharing the same embedding model and distance
metric. If a wildcard search reports incompatible indexes, narrow the set;
do not silently discard the requested thresholds.

Syntax and option constraints:
[Virtuoso vector index API reference](https://www.openlinksw.com/virtuoso/docs/vector-index/api-reference/).

### Hybrid search — two forms

**Do not put `bif:contains` in the same query as `bif:vector_search`.** On
vec.demo.openlinksw.com (2026-11-15) every such combination — `FILTER EXISTS`
with or without `GRAPH`, or a plain join — returned **0 rows**, even when each
search alone matched the same entity (`dbr:Password_reset`). A join with a
`score` option on `bif:contains` fails with `SQ200 No column sc`.

**Form A — fused union (default; widens recall).** Run T9 and the keyword
query separately, then fuse by rank, never by raw score, using the
vector-corroborated fusion in `SKILL.md` step 1c: vector hits ranked 1–10
with score ≥ 0.70 form the ranked list (`1/(60 + vector_rank)`, plus
`1/(60 + keyword_rank)` when the keyword search also found them); keyword hits
outside that window are appended after it, labelled keyword-only. Entities
found by either search are kept. Report keyword rank, vector rank, vector
score, fused score and corroboration status per entity.

**Form B — vector candidates that must contain required words (narrows).**
Use a string filter on the hit's text, not `bif:contains`. Verified on
vec.demo.openlinksw.com:

```sparql
DEFINE input:storage ""
PREFIX dbo: <http://dbpedia.org/ontology/>
SELECT DISTINCT ?doc ?score
WHERE {
  ?doc bif:vector_search "reset customer password"
    option (INDEX *, ranking relevance, score ?score, LIMIT 20, ef_search 100) .
  ?doc rdfs:label | schema:name | schema:description | dbo:description ?text .
  FILTER (CONTAINS(LCASE(STR(?text)), "password"))
}
ORDER BY DESC(?score)
```

Add one `CONTAINS` per required word, joined with `&&`. This is an
intersection: the vector candidate limit applies before the filter, so fewer
rows may survive; raise `LIMIT` and `ef_search` together when requested. If the
required words are missing, elicit them first. Name the form used when
reporting results.

---

## T10 — Vector Index Discovery (on request)

**Trigger:** "List vector indexes", "Find available vector indexes",
"Which vector indexes can I search?"

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?index ?label ?comment
WHERE {
  GRAPH <urn:vvec:indexes> {
    ?index ?p ?o .
    OPTIONAL { ?index rdfs:label ?label }
    OPTIONAL { ?index rdfs:comment ?comment }
  }
}
ORDER BY ?index
```

Run on the requested endpoint (default: the `Vector Search Endpoint`,
`https://vec.demo.openlinksw.com/sparql`; URIBurner has no vector indexes).
For SQL/SPASQL execution,
prefix this query with `SPARQL`. Tabulate all three columns, retaining indexes
whose optional label/comment is absent. Offer the returned `?index` IRIs as
T9 selections. This query lists resources recorded in the index metadata
graph; a row alone does not establish index readiness or its graph mapping.
If no rows are returned, report that no index metadata was **readable** on
that endpoint rather than inventing index IRIs — and do not conclude that the
endpoint lacks vector search. `<urn:vvec:indexes>` is an RDF view over
`DB.DBA.SPARQL_VEC_INDEX`, which ships with no grants for non-DBA readers, so
anonymous callers get nothing (observed on vec.demo.openlinksw.com, where
`bif:vector_search` works). Vector support is decided by VP only. Index IRIs
can also be read from `VEC68` error text, or obtained from the endpoint's
administrator. Run discovery when requested; it is not mandatory before every
vector search.

---

## Example Queries (for `/test_query` validation)

### SPARQL — Persons from DBpedia
```sparql
SELECT DISTINCT ?s
WHERE {
  ?s a schema:Person.
  FILTER (CONTAINS(STR(?s), "dbpedia")).
}
ORDER BY ASC(?s)
LIMIT 10
```

### SPARQL-FED — Spike Lee Films
```sparql
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX dbo: <http://dbpedia.org/ontology/>
SELECT * WHERE {
  SERVICE <http://dbpedia.org/sparql> {
    SELECT ?movie WHERE {
      ?movie rdf:type dbo:Film ; dbo:director dbr:Spike_Lee .
    } LIMIT 10
  }
}
```

### SPASQL — Spike Lee Films (SQL wrapper)
```sql
SELECT movie
FROM (SPARQL
  PREFIX dbr: <http://dbpedia.org/resource/>
  PREFIX dbo: <http://dbpedia.org/ontology/>
  SELECT ?movie WHERE {
    SERVICE <http://dbpedia.org/sparql> {
      ?movie rdf:type dbo:Film ; dbo:director dbr:Spike_Lee .
    }
  }
) AS movies
```

### SQL — Default
```sql
SELECT TOP 20 * FROM Demo.Demo.Customers
```

### GraphQL — Movies
```graphql
query MyQuery { Movies { iri name description director { name } } }
```
