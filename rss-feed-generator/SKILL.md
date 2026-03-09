---
name: rss-feed-generator
description: >
  Generate valid RSS 2.0 or Atom 1.0 feeds from web pages that contain post
  lists but lack a native feed. Triggers on phrases like "generate a feed for",
  "create an RSS feed from", "make an Atom feed for", "this page has no RSS",
  or any request to produce a feed URL or feed XML from a blog/news/post-list
  page. The skill fetches the page, extracts post metadata, and outputs
  well-formed feed XML plus a self-hostable HTML wrapper with an embedded
  feed discovery link tag.
license: See LICENSE.txt
---

# RSS / Atom Feed Generator (v1.0.0)

Generates valid **RSS 2.0** or **Atom 1.0** XML feeds from any web page that
lists posts, articles, or news items but does not publish its own feed.

---

## Defaults & Settings

| Parameter         | Default value                          |
|-------------------|----------------------------------------|
| Preferred format  | RSS 2.0 (Atom 1.0 on request)          |
| Max items         | 20 (most-recent first)                 |
| Date fallback     | Page scrape date (ISO 8601, UTC)        |
| Description       | First 280 chars of post excerpt/lede   |
| Encoding          | UTF-8                                  |
| Output modes      | Raw XML · HTML page · Both             |
| Interaction style | Friendly and professional              |

---

## Trigger Phrases

| #  | User says …                                      | Action                              |
|----|--------------------------------------------------|-------------------------------------|
| T1 | "Generate an RSS/Atom feed for {url}"            | Fetch page → detect posts → emit XML|
| T2 | "This page has no feed: {url}"                   | Same as T1                          |
| T3 | "Create a feed from {url}"                       | Same as T1                          |
| T4 | "Convert {url} posts to RSS"                     | Same as T1                          |
| T5 | "Make a self-hostable feed for {url}"            | Emit XML + HTML wrapper             |
| T6 | "Update / refresh the feed for {url}"            | Re-scrape and re-emit               |

---

## Order of Operations

1. **Page Fetch** — Retrieve the target URL by invoking the `WEB_FETCH` function
   (defined in `https://linkeddata.uriburner.com/chat/functions/openapi.yaml`,
   endpoint `/WEB_FETCH`). Use whichever available protocol applies — REST, MCP,
   OPAL, or curl. Required parameter: `url`. Optional: `headers`, `max_redirects`,
   `timeout_seconds`. `WEB_FETCH` retrieves the page just like a web browser and
   returns the full page content for subsequent processing. See
   [protocol-routing.md](./references/protocol-routing.md) for exact invocation
   patterns per protocol.
2. **Feed Discovery** — Check `<link rel="alternate">` tags. If a feed already
   exists, report it and stop (offer to proxy/mirror instead).
3. **Post Extraction** — Use the heuristics in `references/extraction-rules.md`
   to identify post entries (title, URL, date, author, summary).
4. **Feed Assembly** — Build XML using the templates in
   `references/feed-templates.md`. Validate structure against the checklist
   in `references/validation-checklist.md`.
5. **Output** — Present the feed XML in a code block; optionally wrap in the
   HTML discovery page template from `references/html-wrapper-template.md`.
6. **Download Link** — Save the `.xml` file to `/mnt/user-data/outputs/` and
   present it with `present_files`.

---

## Extraction Heuristics (summary — full rules in references/)

### Structural signals to look for

- Repeated `<article>`, `<li>`, or `<div>` blocks with consistent class names
  (e.g., `post`, `entry`, `article`, `blog-post`, `card`)
- `<h1>`/`<h2>`/`<h3>` headings inside each block → **item title**
- `<a href>` on or near the heading → **item link** (resolve relative URLs)
- `<time datetime="…">` or text matching date patterns → **pubDate**
- First `<p>` inside the block (≤280 chars) → **description / summary**
- `<span class="author">` or byline text → **author**

### Date handling

| Situation                  | Strategy                                  |
|----------------------------|-------------------------------------------|
| `<time datetime="…">`      | Use ISO value directly                    |
| Human-readable date text   | Parse with locale awareness; emit RFC 822 |
| No date found              | Use today's date (UTC) with a `<!-- estimated -->` comment |
| Relative ("3 days ago")    | Calculate from scrape time                |

### URL normalisation

All item `<link>` values must be **absolute**. Resolve against the page's
`<base href>` if present, otherwise against the origin of the page URL.

---

## Feed Format Specs

### RSS 2.0 required elements

```
<rss version="2.0">
  <channel>
    <title>, <link>, <description>   ← required channel fields
    <item>
      <title>, <link>, <guid>        ← required per item
      <pubDate>                      ← RFC 822 (e.g. Mon, 01 Jan 2024 00:00:00 +0000)
      <description>                  ← plain text or CDATA-wrapped HTML
```

### Atom 1.0 required elements

```
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>, <id>, <updated>           ← required feed fields
  <entry>
    <title>, <id>, <updated>         ← required per entry
    <link href="…" rel="alternate"/> ← post URL
    <summary> or <content>           ← excerpt or full body
```

Full templates → `references/feed-templates.md`

---

## Output Modes

| Mode         | Description                                                         |
|--------------|---------------------------------------------------------------------|
| `xml`        | Raw feed XML in a fenced code block                                 |
| `file`       | Save to `/mnt/user-data/outputs/<slug>-feed.xml` and present link   |
| `html`       | HTML discovery page with `<link rel="alternate">` + embedded XML    |
| `both`       | `file` + `html` wrapper saved as `<slug>-feed-page.html`            |

Default: `file` (saves XML and presents download link).

---

## Error Handling

| Problem                            | Response                                                  |
|------------------------------------|-----------------------------------------------------------|
| Page returns non-200               | Report HTTP status; suggest checking URL or auth          |
| No repeating post structure found  | Show raw HTML skeleton; ask user to identify the pattern  |
| Feed already exists                | Report the existing feed URL; offer to mirror/augment     |
| Dates unparseable                  | Use today's date; flag items with `<!-- date-estimated -->`|
| Relative URLs unresolvable         | Ask user for the site's base URL                          |

---

## Commands

| Command              | Description                                              |
|----------------------|----------------------------------------------------------|
| `/help`              | Usage guidance for this skill                            |
| `/format [rss|atom]` | Override output format                                   |
| `/limit [n]`         | Set maximum number of feed items                         |
| `/fulltext`          | Attempt to embed full post body (fetches each post URL)  |
| `/validate`          | Run checklist from `references/validation-checklist.md`  |
| `/preview`           | Show first 3 items as formatted Markdown before XML      |

---

## Operational Rules

1. Always check for an existing feed before generating a synthetic one.
2. Never fabricate post content — only use text found on the page.
3. Escape `&`, `<`, `>` in text nodes; use CDATA for HTML description bodies.
4. All `<guid>` / Atom `<id>` values must be the canonical post URL.
5. Sort items newest-first by default (`pubDate` DESC).
6. Do not request or store credentials; only scrape publicly accessible pages.
7. Clearly label generated feeds as synthetic (add `<generator>` tag).
8. Respect `robots.txt` — do not scrape pages that disallow crawlers.
