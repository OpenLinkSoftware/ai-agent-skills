# OPML & RSS News Reader — Query Templates Reference

All queries are executed via `Demo.demo.execute_spasql_query(sql, maxrows, timeout)`.
Substitute `{url}` with the feed URL supplied by the user before executing.
Default `maxrows` = 20, `timeout` = 30000.

---

## P1 — OPML News Source (Cached Edition)

**Trigger:** "Explore the OPML news source {url}"

Explores the cached (already-sponged) version of the OPML feed. Use when the
user wants to browse previously ingested content without triggering a live fetch.

```sparql
SPARQL
PREFIX schema: <http://schema.org/>
PREFIX sioc: <http://rdfs.org/sioc/ns#>

SELECT DISTINCT
  ?feed
  (?post AS ?postID)
  (CONCAT('https://linkeddata.uriburner.com/describe/?uri=', STR(?post)) AS ?postDescUrl)
  ?pubDate ?postTitle ?postUrl
FROM <{url}>
WHERE {
  ?s a schema:DataFeed ; sioc:link ?feed .
  GRAPH ?g {
    ?feed schema:mainEntity ?blog.
    ?blog schema:dataFeedElement ?post.
    ?post schema:title ?postTitle ;
          schema:relatedLink ?postUrl ;
          schema:datePublished ?pubDate.
  }
}
ORDER BY DESC(?pubDate)
LIMIT 20
```

---

## P2 — OPML News Source (Latest / Live Edition)

**Trigger:** "Explore the latest edition of OPML news source {url}"

Forces a live re-fetch of the OPML feed using `get:soft "soft"` and
`input:grab-var "feed"` pragmas to pull the freshest content.

```sparql
SPARQL
DEFINE get:soft "soft"
DEFINE input:grab-var "feed"

PREFIX schema: <http://schema.org/>
PREFIX sioc: <http://rdfs.org/sioc/ns#>

SELECT DISTINCT
  ?feed
  (?post AS ?postID)
  (CONCAT('https://linkeddata.uriburner.com/describe/?uri=', STR(?post)) AS ?postDescUrl)
  ?pubDate ?postTitle ?postUrl
FROM <{url}>
WHERE {
  ?s a schema:DataFeed.
  OPTIONAL { ?s sioc:link ?feed }.
  GRAPH ?g {
    ?feed schema:mainEntity ?blog.
    ?blog schema:dataFeedElement ?post.
    ?post schema:title ?postTitle ;
          schema:relatedLink ?postUrl ;
          schema:datePublished ?pubDate.
  }
}
ORDER BY DESC(?pubDate)
LIMIT 20
```

---

## P3 — RSS or Atom News Source (Cached Edition)

**Trigger:** "Explore the RSS or Atom news source {url}"

Explores a cached RSS or Atom feed. Uses OPTIONAL clauses to handle feeds
where title, text, date, or link predicates may be absent.

```sparql
SPARQL
PREFIX schema: <http://schema.org/>
PREFIX sioc: <http://rdfs.org/sioc/ns#>

SELECT DISTINCT
  ?feed
  (?post AS ?postID)
  (CONCAT('https://linkeddata.uriburner.com/describe/?uri=', STR(?post)) AS ?postDescUrl)
  ?pubDate ?postTitle ?postText ?postUrl
FROM <{url}>
WHERE {
  ?feed a schema:DataFeed ;
        foaf:topic | schema:dataFeedElement ?post.
  OPTIONAL { ?post schema:title ?postTitle }
  OPTIONAL { ?post schema:text ?postText }
  OPTIONAL { ?post schema:dateCreated | schema:datePublished ?pubDate }
  OPTIONAL { ?post schema:relatedLink ?postUrl }
}
ORDER BY DESC(?pubDate)
```

---

## P4 — RSS or Atom News Source (Latest / Live Edition)

**Trigger:** "Explore the latest edition of RSS or Atom news source {url}"

Forces a live re-fetch using `get:soft "soft"` and `get:refresh "0"` pragmas.
Replaces the hardcoded example URL below with the user's `{url}`.

```sparql
SPARQL
DEFINE get:soft "soft"
DEFINE get:refresh "0"

PREFIX schema: <http://schema.org/>
PREFIX sioc: <http://rdfs.org/sioc/ns#>

SELECT DISTINCT
  ?feed
  (?post AS ?postID)
  (CONCAT('<https://linkeddata.uriburner.com/describe/?uri=>', STR(?post)) AS ?postDescUrl)
  ?pubDate ?postTitle ?postText ?postUrl
FROM <{url}>
WHERE {
  ?feed a schema:DataFeed ;
        schema:dataFeedElement ?post.
  OPTIONAL { ?post schema:title ?postTitle }
  OPTIONAL { ?post schema:text ?postText }
  OPTIONAL { ?post schema:dateCreated | schema:datePublished ?pubDate }
  OPTIONAL { ?post schema:relatedLink ?postUrl }
}
ORDER BY DESC(?pubDate)
```

---

## Template Selection Guide

| Condition | Use |
|---|---|
| OPML feed, content already ingested | P1 |
| OPML feed, want freshest content | P2 |
| RSS or Atom feed, content already ingested | P3 |
| RSS or Atom feed, want freshest content | P4 |
| Feed type unknown | Try P3 first (broadest coverage) |

---

## Pragma Reference

| Pragma | Effect |
|---|---|
| `DEFINE get:soft "soft"` | Soft-fetch: pulls live content if not cached |
| `DEFINE get:refresh "0"` | Forces immediate refresh regardless of cache |
| `DEFINE input:grab-var "feed"` | Tells the sponger which variable to use as the feed IRI |

---

## Predicate Reference

| Predicate | Meaning |
|---|---|
| `schema:DataFeed` | The feed container entity |
| `sioc:link` | Link from DataFeed to the actual feed IRI |
| `schema:mainEntity` | Blog/channel entity within the feed graph |
| `schema:dataFeedElement` | Individual post/item within the blog |
| `schema:title` | Post title |
| `schema:text` | Post body text |
| `schema:relatedLink` | Post canonical URL |
| `schema:datePublished` | Post publication date |
| `schema:dateCreated` | Post creation date (RSS fallback) |
| `foaf:topic` | Alternative feed→post link (some RSS variants) |
