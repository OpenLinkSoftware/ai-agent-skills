# OPML & RSS News Reader — Query Templates Reference

All queries are executed via `Demo.demo.execute_spasql_query(sql, maxrows, timeout)`.
Substitute `{url}` with the feed URL supplied by the user before executing.
Default `timeout` = 30000.

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

Explores the cached version of the OPML feed. `get:soft "soft"` applies
Virtuoso's native cache management. Use when a forced refresh is not required.

```sparql
SPARQL
DEFINE get:soft "soft"
DEFINE input:grab-iri "{url}"
DEFINE input:grab-var "feed"

PREFIX schema: <http://schema.org/>
PREFIX sioc: <http://rdfs.org/sioc/ns#>

SELECT DISTINCT ?feed (?post AS ?postID)
  (CONCAT('https://linkeddata.uriburner.com/describe/?uri=', STR(?post)) AS ?postDescUrl)
  ?pubDate ?postTitle ?postUrl
WHERE {
  GRAPH <{url}> {
    ?s a schema:DataFeed.
    ?s sioc:link ?feed .
  }
  GRAPH ?feed {
    ?feed_entry schema:mainEntity ?blog.
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

Forces an unconditional refresh of the OPML feed via `get:refresh "0"`,
bypassing any cached version.

```sparql
SPARQL
DEFINE get:soft "soft"
DEFINE get:refresh "0"
DEFINE input:grab-iri "{url}"
DEFINE input:grab-var "feed"

PREFIX schema: <http://schema.org/>
PREFIX sioc: <http://rdfs.org/sioc/ns#>

SELECT DISTINCT ?feed (?post AS ?postID)
  (CONCAT('https://linkeddata.uriburner.com/describe/?uri=', STR(?post)) AS ?postDescUrl)
  ?pubDate ?postTitle ?postUrl
WHERE {
  GRAPH <{url}> {
    ?s a schema:DataFeed.
    ?s sioc:link ?feed .
  }
  GRAPH ?feed {
    ?feed_entry schema:mainEntity ?blog.
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

Explores an RSS or Atom feed with Virtuoso's native cache management.
`OPTIONAL` clauses handle feeds where title, link, or date predicates may be absent.

```sparql
SPARQL
DEFINE get:soft "soft"
DEFINE input:grab-iri "{url}"

PREFIX schema: <http://schema.org/>
PREFIX sioc: <http://rdfs.org/sioc/ns#>

SELECT DISTINCT ?feed (?post AS ?postID)
  (CONCAT('https://linkeddata.uriburner.com/describe/?uri=', STR(?post)) AS ?postDescUrl)
  ?pubDate ?postTitle ?postUrl
WHERE {
  GRAPH <{url}> {
    ?feed a schema:DataFeed ;
          schema:dataFeedElement ?post.
    OPTIONAL { ?post schema:title ?postTitle }
    OPTIONAL { ?post schema:dateCreated | schema:datePublished ?pubDate }
    OPTIONAL { ?post schema:relatedLink ?postUrl }
  }
}
ORDER BY DESC(?pubDate)
```

---

## P4 — RSS or Atom News Source (Latest / Live Edition)

**Trigger:** "Explore the latest edition of RSS or Atom news source {url}"

Forces an unconditional refresh via `get:refresh "0"`.

```sparql
SPARQL
DEFINE get:soft "soft"
DEFINE get:refresh "0"
DEFINE input:grab-iri "{url}"

PREFIX schema: <http://schema.org/>
PREFIX sioc: <http://rdfs.org/sioc/ns#>

SELECT DISTINCT ?feed (?post AS ?postID)
  (CONCAT('https://linkeddata.uriburner.com/describe/?uri=', STR(?post)) AS ?postDescUrl)
  ?pubDate ?postTitle ?postUrl
WHERE {
  GRAPH <{url}> {
    ?feed a schema:DataFeed ;
          schema:dataFeedElement ?post.
    OPTIONAL { ?post schema:title ?postTitle }
    OPTIONAL { ?post schema:dateCreated | schema:datePublished ?pubDate }
    OPTIONAL { ?post schema:relatedLink ?postUrl }
  }
}
ORDER BY DESC(?pubDate)
```

---

## Template Selection Guide

| Condition | Use |
|---|---|
| URL is a plain web page; user wants to find feeds | AD1 |
| URL is a plain web page; user wants to explore/read feeds | AD2 (AD1 → P3 or P4) |
| OPML feed, no forced refresh needed | P1 |
| OPML feed, force refresh | P2 |
| RSS or Atom feed, no forced refresh needed | P3 |
| RSS or Atom feed, force refresh | P4 |
| Feed type unknown | Run AD1 first; if a direct feed URL, try P3 |

---

## Pragma Reference

| Pragma | Effect |
|---|---|
| `DEFINE get:soft "soft"` | Activates Virtuoso's native cache management |
| `DEFINE get:refresh "0"` | Forces unconditional refresh, bypassing cache |
| `DEFINE input:grab-iri "{url}"` | Specifies the IRI for the Sponger to process |
| `DEFINE input:grab-var "feed"` | Tells the Sponger to also process the `?feed` variable IRI |

---

## Predicate Reference

| Predicate | Meaning |
|---|---|
| `schema:DataFeed` | The feed container entity |
| `sioc:link` | Link from DataFeed to the actual feed IRI (OPML) |
| `schema:mainEntity` | Blog/channel entity within the feed graph |
| `schema:dataFeedElement` | Individual post/item within the blog or feed |
| `schema:title` | Post title |
| `schema:relatedLink` | Post canonical URL |
| `schema:datePublished` | Post publication date |
| `schema:dateCreated` | Post creation date (RSS fallback) |
