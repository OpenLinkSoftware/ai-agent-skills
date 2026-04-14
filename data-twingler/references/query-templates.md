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
