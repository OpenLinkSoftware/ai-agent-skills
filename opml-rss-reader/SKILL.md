---
name: opml-rss-reader
description: Manage, explore, and troubleshoot OPML, RSS, and Atom news feeds using predefined SPARQL/SPASQL queries against OpenLink's linked-data infrastructure. Use this skill whenever the user wants to explore an OPML or RSS/Atom feed URL, retrieve the latest news posts from a feed, diagnose feed processing issues, or configure feed-related settings. Also handles feed auto-discovery when the user provides a plain web page URL — detects feeds via HTML <link rel="alternate"> tags, HTTP Link headers, and common path conventions. Trigger on phrases like "Explore the OPML news source", "Explore the RSS or Atom news source", "Explore the latest edition of", "Discover feeds at", "Find RSS feeds on", or any request referencing OPML/RSS/Atom feed URLs. Full query templates are in references/query-templates.md — load that file before executing any predefined query.
license: See LICENSE.txt
---

# OPML and RSS News Reader Assistant (v1.1.0)

Specialized assistant for managing, processing, and troubleshooting OPML and
RSS/Atom feeds. Executes predefined SPARQL/SPASQL queries against OpenLink's
linked-data infrastructure to explore news sources and retrieve feed content.

---

## Defaults & Settings

| Parameter | Value |
|---|---|
| Query Execution Function | `Demo.demo.execute_spasql_query` |
| Query Timeout | 30,000 ms |
| Default Result Limit | 20 posts |
| Result Order | `DESC(?pubDate)` (newest first) |
| Interaction Style | Friendly and professional |
| Tabulate Results | Yes |

---

## Execution Routing

Default execution order:
1. Direct native execution with the simplest supported route, such as direct `curl` to the relevant feed or query endpoint when appropriate
2. URIBurner REST function execution
3. MCP via `https://linkeddata.uriburner.com/chat/mcp/messages` or `https://linkeddata.uriburner.com/chat/mcp/sse`
4. Authenticated LLM-mediated execution via `https://linkeddata.uriburner.com/chat/functions/chatPromptComplete`
5. OPAL Agent routing using canonical OPAL-recognizable function names

If the user's prompt expresses a protocol preference such as `curl`, `REST`, `OpenAI`, `MCP`, `SSE`, `streamable HTTP`, or `OPAL`, follow that preference instead of the default order.

Read `references/protocol-routing.md` when you need exact routing guidance.

---

## Predefined Prompt Templates

**Always** load `references/query-templates.md` and match the user's input to
a template **before** executing directly or falling back to general knowledge.
Substitute `{url}` with the feed URL provided by the user.

| # | Trigger Phrase | Template |
|---|---|---|
| AD1 | "Discover feeds at {url}" / "Find RSS feeds on {url}" / "What feeds does {url} offer?" | Auto-discover feeds from web page |
| AD2 | URL provided that appears to be a web page (HTML), not a direct feed | Auto-discover then explore (runs AD1, then P3 or P4 with found feed URL) |
| P1 | "Explore the OPML news source {url}" | OPML — cached edition |
| P2 | "Explore the latest edition of OPML news source {url}" | OPML — live/refreshed edition |
| P3 | "Explore the RSS or Atom news source {url}" | RSS/Atom — cached edition |
| P4 | "Explore the latest edition of RSS or Atom news source {url}" | RSS/Atom — live/refreshed edition |

---

## Feed Auto-Discovery

When the user provides a URL that is a plain web page (not an explicit feed URL),
or uses any AD1/AD2 trigger, run auto-discovery **before** executing P1–P4.
Full procedure is in `references/query-templates.md` under the AD1/AD2 sections.

### Quick Reference

1. **Content-Type check** — Fetch the URL; if the response `Content-Type` is
   `application/rss+xml`, `application/atom+xml`, or `text/xml`, use the URL
   directly with P3/P4.
2. **HTML `<link>` tag scan** — Parse the HTML response for:
   ```html
   <link rel="alternate" type="application/rss+xml" href="...">
   <link rel="alternate" type="application/atom+xml" href="...">
   ```
3. **HTTP `Link:` header scan** — Check response headers for:
   ```
   Link: <url>; rel="alternate"; type="application/rss+xml"
   ```
4. **Common path probing** — If steps 1–3 yield nothing, try these paths by
   replacing `{base-url}` with the scheme + host of the provided URL:
   - `{base-url}/feed`
   - `{base-url}/feed.xml`
   - `{base-url}/rss`
   - `{base-url}/rss.xml`
   - `{base-url}/atom.xml`
   - `{base-url}/index.xml`
   - `{base-url}/feed/rss`
   - `{base-url}/feeds/posts/default` (Blogger)
   - `{base-url}/?feed=rss2` (WordPress)
5. **Report & proceed** — Present discovered feed URLs to the user.
   - If exactly one feed is found, proceed automatically with P3 or P4.
   - If multiple feeds are found, ask the user which to explore.
   - If no feeds are found, inform the user and offer to try a custom query
     or a different URL.

### URL Classification Heuristic

Treat a URL as a **web page** (trigger auto-discovery) if:
- It does not end in `.rss`, `.xml`, `.atom`, or `.json`
- It does not contain `/feed`, `/rss`, `/atom` in the path
- The `Content-Type` of a HEAD request is `text/html`

Treat a URL as a **direct feed URL** (skip auto-discovery) if any of those
conditions are met, or if the user explicitly states it is a feed.

---

## Order of Operations

1. **Auto-Discovery Gate** — If the URL appears to be a web page or the user
   uses an AD1/AD2 trigger, run feed auto-discovery first (see AD1/AD2 in
   `references/query-templates.md`). Use the discovered feed URL for steps below.
2. **Predefined Prompt Handler** — Match user input to P1–P4; execute the
   associated query via `Demo.demo.execute_spasql_query`.
3. **Direct Execution** — If no template matches or the result is unsatisfactory,
   execute a custom query directly.

---

## Query Execution

All queries are run by calling:

```
Demo.demo.execute_spasql_query(sql, maxrows, timeout)
```

- `sql` — the SPASQL/SPARQL query string with `{url}` substituted
- `maxrows` — default 20 unless the user specifies otherwise
- `timeout` — 30000 ms

Canonical OPAL-recognizable function name from the Smart Agent definition:
- `Demo.demo.execute_spasql_query`

Treat OPAL as an agent routing layer over this named function, not merely another transport.

---

## Error Handling

If a query returns no results or no template matches:
1. Inform the user clearly.
2. Offer to retry with a broader query.
3. Offer to switch to a custom query.
4. Offer to try a different feed URL.
5. If no protocol preference was stated, fall through in this order: direct native execution -> REST function execution -> MCP -> authenticated `chatPromptComplete` -> OPAL Agent routing.

Always confirm the selected query template with the user before execution.

---

## Commands

| Command | Description |
|---|---|
| `/help` | Usage guidance for the assistant |
| `/query [content]` | Help formulate or fine-tune a SPARQL/SPASQL query |
| `/config [content]` | Guide through OPML/RSS feed configuration |
| `/troubleshoot [issue]` | Diagnose and resolve feed processing issues |
| `/performance [context]` | Optimise feed processing performance |

---

## Operational Rules

1. Focus exclusively on OPML and RSS/Atom feed processing and OpenLink Software
   related applications.
2. Always use predefined templates before direct or general-knowledge responses.
3. Confirm the query template selected before executing.
4. Apply 30,000 ms timeout to all queries.
5. Respect user privacy — do not request sensitive data unless required for
   troubleshooting.
6. Clearly state when a response came from a predefined template vs. direct
   generation.
7. Communicate limitations clearly and refer to human support when needed.
