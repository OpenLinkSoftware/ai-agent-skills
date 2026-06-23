# FIFA World Cup 2026 Match Intelligence Report Skill

**Name:** `wc2026-match-report`  
**Version:** 1.0.0  
**Description:** Generate a complete single-file HTML match intelligence report for any FIFA World Cup 2026 fixture from live Knowledge Graph data.

---

## Trigger Phrases

Use this skill when the user says any of:
- "generate a match report for X vs Y"
- "match intelligence report for [Team A] vs [Team B]"
- "produce a WC2026 report for [fixture]"
- "create a FIFA report for [match]"
- "run the match report script for [match_id]"

---

## Companion Skills (load before any query or HTML work)

| Skill | Purpose |
|---|---|
| `world-cup-2026-navigator` | Correct SPARQL property URIs, coded values, named graph routing |
| `rdf-infographic-skill` | Visual design, colour contrast, entity-link styling, footer attribution contract |

---

## Execution Routing (priority order)

1. **Script** — `scripts/report_template_create.py <match_id> <output_path>` (preferred when Python 3 is available)
2. **Inline build** — fetch data via curl + construct HTML section-by-section per `references/query-templates.md`
3. **LLM fallback** — synthesise from inline rules in this file (last resort)

---

## Step 0 — Load companion skills

```
/world-cup-2026-navigator
/rdf-infographic-skill
```

## Step 1 — Resolve match ID

SPARQL endpoint: `https://demo.openlinksw.com/sparql`  
Named graph: `urn:worldcup:kg:2026`

```sparql
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?match ?matchId ?homeTeam ?awayTeam ?homeScore ?awayScore ?date ?stadium
FROM <urn:worldcup:kg:2026>
WHERE {
  ?match a fifa:Match ; fifa:matchId ?matchId ;
         fifa:homeTeam ?ht ; fifa:awayTeam ?at ;
         fifa:homeTeamScore ?homeScore ; fifa:awayTeamScore ?awayScore ; fifa:date ?date .
  ?ht rdfs:label ?homeTeam . ?at rdfs:label ?awayTeam .
  OPTIONAL { ?match fifa:stadium ?s . ?s rdfs:label ?stadium }
  FILTER(
    CONTAINS(LCASE(str(?homeTeam)), "TEAM_A") ||
    CONTAINS(LCASE(str(?awayTeam)), "TEAM_B")
  )
}
ORDER BY ?date
```

Replace `TEAM_A` / `TEAM_B` with lowercase name fragments. See `references/query-templates.md` for full team name aliases.

**Match IRI pattern:** `http://demo.openlinksw.com/fifa-kg#match-{matchId}`  
Use this IRI (not `matchId`) when querying the analytics graph.

## Step 2 — Determine output filename

Format: `YYYYMMDD-hometeam-vs-awayteam.html`  
- Date = UTC date from `?date` (first 10 chars, hyphens removed)  
- Team names lowercased, spaces → hyphens, special chars dropped  
- Home team (per KG) always first

**Output path (per model routing rules):**  
- Claude Sonnet/Opus → `/Users/kidehen/Documents/LLMs/Claude Generated/webpages/`
- DeepSeek → `/Users/kidehen/Documents/LLMs/DeepSeek/webpages/`
- (see preferences.ttl `step-outputDirs` for full routing table)

## Step 3 — Run the script

```bash
python3 /path/to/wc2026-match-report/scripts/report_template_create.py \
  <match_id> \
  <output_path>/<filename>.html
```

The script handles: SPARQL queries for all 8 data categories, team colours, CSS variables, formation SVGs, analytics bars, pressing gauges, timeline, attribution footer.

If the script is unavailable, use `references/query-templates.md` and build section-by-section.

## Step 4 — Data categories

| # | Data | Graph |
|---|---|---|
| 1 | Match overview (teams, score, tactics, attendance, weather) | `urn:worldcup:kg:2026` |
| 2 | Hero article + image (`fifa:hasNewsArticle` → `schema:image`) | `urn:worldcup:kg:2026` |
| 3 | Goals (`fifa:hasGoal`) | `urn:worldcup:kg:2026` |
| 4 | Bookings (`fifa:hasBooking`) | `urn:worldcup:kg:2026` |
| 5 | Substitutions (`fifa:hasSubstitution`) | `urn:worldcup:kg:2026` |
| 6 | Head coaches — filter `fifa:hasRole fifa:CoachRole-0` ONLY | `urn:worldcup:kg:2026` |
| 7 | Team analytics (latest `MAX(fifa:generatedAt)` snapshot) | `urn:worldcup:kg:2026:analytics` |
| 8 | Player analytics (latest snapshot, cross-ref squad for team assignment) | `urn:worldcup:kg:2026:analytics` |

**Critical notes:**
- Analytics graph uses match IRI (`http://demo.openlinksw.com/fifa-kg#match-{id}`), not `matchId`. Use `GRAPH` clauses to scope subqueries.
- `fifa:CoachRole-0` = Head Coach. All other `CoachRole-N` are assistants/support staff.
- Player analytics have no reliable `fifa:team` — cross-reference `playerName` against squad appearance data.
- Always use `MAX(fifa:generatedAt)` subquery to pick the latest analytics snapshot.

## Step 5 — Colour rules

See `references/team-colours.md` for all 48 WC2026 teams.

- Home team colour → `--accent` CSS variable
- Away team colour → `--accent-dim` CSS variable
- Comparative bars use `var(--accent)` / `var(--accent-dim)` — never hardcoded hex
- Perceived brightness ≤ 128 → white text `#fff`; brightness > 128 → black text `#000`
- For similar-hue matchups → use alternate kit colour for away side

## Step 6 — 11-section HTML structure

| Anchor | Section |
|---|---|
| `#hero` | Score banner, stadium, attendance, weather, head coaches |
| `#goals` | Goal log (minute, scorer, team, type, assist) |
| `#timeline` | Chronological event strip (goals + bookings + subs) |
| `#stats` | Head-to-head comparison bars (possession, passes, shots, xG, …) |
| `#phases` | Tactical phase aggregate grid |
| `#pressing` | Pressing intensity & threat gauges |
| `#formations` | Two SVG formation diagrams (≥11 circles per team) |
| `#squads` | Full squad tables (starters + subs) |
| `#core-players` | Top players by distance + Distance & Speed Comparison card |
| `#sparql` | SPARQL accordion (≥3 numbered queries with live links) |
| `#sources` | Attribution footer (7 cards) |

## Step 7 — 12-point verification gate

Run before saving. All must pass:

1. `og:image` meta tag present
2. Hero image from `digitalhub.fifa.com` in captioned `<div>` with "Image source" line
3. ≥ 22 player circles across both formation SVGs (11 per team)
4. ≥ 10 entity-link player rows in `#core-players`
5. Pressing gauges populated
6. Timeline populated (all goals, bookings, subs)
7. Distance & Speed Comparison `compare-block` card with `var(--accent)` / `var(--accent-dim)` bars
8. `--accent` ≠ `--accent-dim` (visually distinct colours)
9. Attribution footer has exactly 7 `<div class="attr-card">` elements
10. Footer copyright: `© 2026 OpenLink Software · FIFA World Cup 2026 Match Intelligence`
11. Head coaches identified via `fifa:CoachRole-0` — not assistants
12. Section/card `.section-title` and `.card-title` elements have `onclick="copyAnchor(this)"` and hover tooltip

---

## References

- `references/query-templates.md` — All 8 SPARQL queries, parameterised, with GRAPH clauses
- `references/team-colours.md` — Hex colours + text colours for all 48 WC2026 teams
- `references/verification.md` — Extended verification checklist with grep commands

## Scripts

- `scripts/report_template_create.py` — Main generation engine (Python 3, stdlib only)

---

## Example

```bash
# Norway vs Senegal (match ID 400021491)
python3 scripts/report_template_create.py \
  400021491 \
  "/Users/kidehen/Documents/LLMs/Claude Generated/webpages/20260623-norway-vs-senegal.html"
```

Output: self-contained HTML, ~84 KB, passes all 12 verification gates.
