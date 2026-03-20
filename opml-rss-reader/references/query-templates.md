# OPML & RSS News Reader — Query Templates Reference

All queries are executed via `Demo.demo.execute_spasql_query(sql, maxrows, timeout)`.
Substitute `{url}` with the feed URL supplied by the user before executing.
Default `maxrows` = 20, `timeout` = 30000.

---

## AD1 — Feed Auto-Discovery from Web Page URL

**Trigger:** "Discover feeds at {url}" / "Find RSS feeds on {url}" /
"What feeds does {url} offer?" / any URL that is classified as a web page
(see URL Classification Heuristic in SKILL.md).

**Purpose:** Discover RSS/Atom feed URLs embedded in or associated with a
plain web page before attempting to explore feed content.

### Step-by-Step Procedure

#### Step 1 — Content-Type Check (HEAD request)

```bash
curl -sI {url}
```

Inspect the `Content-Type` response header:
- `application/rss+xml` → URL is already a feed; proceed directly with P3/P4.
- `application/atom+xml` → URL is already a feed; proceed directly with P3/P4.
- `text/xml` → likely a feed; proceed directly with P3.
- `text/html` → web page; continue to Step 2.

#### Step 2 — HTML `<link>` Tag Scan

```bash
curl -sL {url} | grep -i '<link[^>]*rel=["\']alternate["\']'
```

Look for tags matching either of:
```html
<link rel="alternate" type="application/rss+xml" href="{feed-url}" title="...">
<link rel="alternate" type="application/atom+xml" href="{feed-url}" title="...">
```

Extract all `href` values. Resolve relative paths against the base URL.
If one or more feed URLs are found, collect them and jump to **Step 5**.

#### Step 3 — HTTP `Link:` Header Scan

Re-examine the HEAD response headers from Step 1 for:
```
Link: <{feed-url}>; rel="alternate"; type="application/rss+xml"
Link: <{feed-url}>; rel="alternate"; type="application/atom+xml"
```

Extract the linked URL(s). If found, collect them and jump to **Step 5**.

#### Step 4 — Common Path Probing

Extract `{base-url}` = scheme + host from the provided URL (e.g., `https://example.com`).
Probe each of the following with a HEAD request and check for a 200 response
and a feed `Content-Type`:

| Candidate Path | Notes |
|---|---|
| `{base-url}/feed` | Most common (WordPress, Ghost, Hugo) |
| `{base-url}/feed.xml` | Static site generators |
| `{base-url}/rss` | Common alternative |
| `{base-url}/rss.xml` | Common alternative |
| `{base-url}/atom.xml` | Atom feeds |
| `{base-url}/index.xml` | Hugo default |
| `{base-url}/feed/rss` | Some CMS platforms |
| `{base-url}/feeds/posts/default` | Blogger |
| `{base-url}/?feed=rss2` | WordPress query-string style |

Record any path that returns HTTP 200 with a feed `Content-Type`.

#### Step 5 — Report & Proceed

Present results to the user in a table:

| # | Feed URL | Title (if known) | Type |
|---|---|---|---|
| 1 | `{feed-url-1}` | … | RSS / Atom |
| 2 | `{feed-url-2}` | … | RSS / Atom |

- **Exactly one feed found** → confirm with the user and proceed automatically
  with P3 (cached) or P4 (live), substituting the discovered feed URL.
- **Multiple feeds found** → ask the user which feed to explore.
- **No feeds found** → inform the user clearly; offer to try a custom SPARQL
  query, a different URL, or manual feed URL entry.

---

## AD2 — Auto-Discover and Explore (Combined Shortcut)

**Trigger:** User provides a plain web page URL with an "explore" or "read"
intent but does not use explicit P1–P4 trigger phrasing, **and** the URL is
classified as a web page rather than a direct feed URL.

**Procedure:** Run the full AD1 procedure. Once a feed URL is confirmed,
automatically execute P3 (if the user wants cached content) or P4 (if the
user wants the latest content). If the user has not expressed a freshness
preference, default to P4 (live/refreshed edition).

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
| URL is a plain web page; user wants to find feeds | AD1 |
| URL is a plain web page; user wants to explore/read feeds | AD2 (AD1 → P3 or P4) |
| OPML feed, content already ingested | P1 |
| OPML feed, want freshest content | P2 |
| RSS or Atom feed, content already ingested | P3 |
| RSS or Atom feed, want freshest content | P4 |
| Feed type unknown | Run AD1 first; if a direct feed URL, try P3 |

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
