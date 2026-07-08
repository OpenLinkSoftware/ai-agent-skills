# FIFA World Cup 2026 Match Intelligence Report Skill

**Name:** `wc2026-match-report`  
**Version:** 1.2.0  
**Description:** Generate a complete single-file HTML intelligence report for the FIFA World Cup 2026 from live Knowledge Graph data. Three report types:

| Type | Subject | Script |
|---|---|---|
| **Match report** (default) | a fixture (Team A vs Team B) | `scripts/report_template_create.py <match_id> <out>` |
| **Player report** | a single player across the tournament | `scripts/player_report_create.py <player_id\|name> [--out …]` |
| **Analytics scatter report** | tournament-wide player comparisons | `scripts/analytics_scatter_report_create.py [--chart …] [--out …]` |

Pick the **player report** whenever the request is about one person ("create a player report for Jude Bellingham", "player intelligence for Olise"). Pick the **analytics scatter report** for tournament-wide cross-player comparisons ("running data report", "passing volume vs accuracy", "Simon Brunson-style chart"). Everything below with no specific heading refers to the match report.

---

## Analytics Scatter Report Mode

Use `scripts/analytics_scatter_report_create.py` when the request is about **comparing all players across one or two metrics** — running data, passing efficiency, physical load, attacking output. This produces a Simon Brunson-style infographic: cream background, bold print-inspired header, numbered Chart.js scatter cards with zoom/pan, auto-generated insights, and click-through to player `/describe/` profiles. Data is fetched live by the browser at page-load time — no server-side SPARQL needed.

**Trigger phrases:**
- "running data report", "Simon Brunson-style report", "scatter chart for all players"
- "compare [metric] vs [metric] across the tournament"
- "passing volume vs accuracy chart", "physical load comparison"
- "who covers the most distance", "speed vs sprint metres"

**Script location:** `scripts/analytics_scatter_report_create.py` in `simon-bronwell/` style output  
**Output directory:** `simon-bronwell/` under the working directory (or specify with `--out`)

```bash
# Running data (reproduces the existing fatigue-index example):
python3 scripts/analytics_scatter_report_create.py \
  --title "RUNNING DATA" --emoji "🏃" \
  --subtitle "Player-Level Relationships" \
  --desc "How total volume, high-speed work, top speed and sprint metres are connecting" \
  --note "Players with 45+ tournament minutes" \
  --chart "totalDistance,highSpeedDistance,Total distance (m),High-speed distance (m),Total Distance vs High-Speed Distance" \
  --chart "topSpeed,sprintMetres,Top speed (km/h),Sprint metres (m),Top Speed vs Sprint Metres" \
  --out simon-bronwell/YYYYMMDD-running-data.html

# Passing intelligence:
python3 scripts/analytics_scatter_report_create.py \
  --title "PASSING INTELLIGENCE" --emoji "🎯" \
  --subtitle "Volume & Accuracy" \
  --desc "How passing volume and accuracy relate across all outfield players" \
  --chart "passes,passAccuracy,Total Passes,Pass Accuracy (%),Volume vs Accuracy" \
  --chart "passes,assists,Total Passes,Assists,Pass Volume vs Creativity" \
  --out simon-bronwell/YYYYMMDD-passing-intelligence.html

# Attacking output:
python3 scripts/analytics_scatter_report_create.py \
  --title "ATTACKING OUTPUT" --emoji "⚽" \
  --subtitle "Shots, Goals & Creativity" \
  --desc "Comparing shot volume, on-target accuracy and assist creation across forwards and midfielders" \
  --chart "shots,goals,Shots,Goals,Shot Volume vs Goals" \
  --chart "shots,shotsOnTarget,Shots,Shots on Target,Shot Volume vs Accuracy" \
  --out simon-bronwell/YYYYMMDD-attacking-output.html
```

**Available metric keys** (use as `xKey` / `yKey` in `--chart`):

| Key | Description |
|---|---|
| `totalDistance` | Total distance run (m) |
| `highSpeedDistance` | High-speed distance: zones 4+5 (m) |
| `sprintMetres` | Sprint metres: zone 5 only (m) |
| `topSpeed` | Maximum recorded speed (km/h) |
| `avgSpeed` | Average speed (km/h) |
| `minutesPlayed` | Total minutes played |
| `sprints` | Sprint count |
| `passes` | Total passes attempted |
| `passesCompleted` | Passes completed |
| `passAccuracy` | Pass completion % (derived) |
| `assists` | Assists |
| `goals` | Goals |
| `shots` | Shots (attempts at goal) |
| `shotsOnTarget` | Shots on target |
| `takeOns` | Take-ons completed |
| `crosses` | Crosses |
| `crossesCompleted` | Successful crosses |
| `foulsWon` | Fouls won |
| `foulsCommitted` | Fouls committed |
| `forcedTurnovers` | Turnovers forced |
| `yellowCards` | Yellow cards |
| `corners` | Corners taken |

**`--chart` format:** `xKey,yKey[,xAxisLabel,yAxisLabel[,Card Title]]`  
Labels default to human-readable names if omitted; card title defaults to "xLabel vs yLabel".

**Options:**
- `--title` — big uppercase headline (e.g. `"RUNNING DATA"`)
- `--emoji` — icon beside the headline (e.g. `"🏃"`)  
- `--subtitle` — centre-panel heading
- `--desc` — centre-panel description text
- `--note` — small italic note (e.g. minimum minutes qualifier)
- `--min-minutes` — SPARQL HAVING filter, default `45`
- `--out` — output file path

**Design notes (Simon Brunson style):**
- Cream/beige page background `#f0ede8`, white chart cards, black ink typography
- Compact header: brand column | big title | centre meta panel
- Position-coded dots: DF=blue, MF=green, FW=red, GK=grey
- Zoom/pan with reset button; click dot → `/describe/` player profile; click clustered dots → selection modal
- Auto-generated insight below each chart naming top performers with `/describe/` hyperlinks
- JSON-LD + OG metadata in `<head>`; source attribution in footer

---

## Operating Modality — Read This First

**You are a modern UI/UX expert specialising in sports intelligence report design** for the duration of any task that uses this skill. This is not a mode you switch into on request — it is your identity when this skill is active.

What this means in practice:

- **Report design intent before implementation** — before writing any HTML, decide the visual narrative: match header (teams, score, venue), then statistical sections (possession, shots, formation), then event timeline, then player ratings. The layout must feel like a premium sports broadcast graphic, not a data dump.
- **Team colour identity** — where team colours are available from the KG, use them as accent colours for each team's side of the report (possession bars, formation highlights, stat comparisons). Never use generic blue/red as defaults when real team colours are known.
- **Lineup lists are grouped by role, not tabular** — display starters grouped as Goalkeeper / Defender / Midfield / Attack, followed by Substitutions, Coach, and Assistant Coaches. Use `fifa:playerStatus` (1=starter, 2=sub) and `fifa:position` URI code to group. A flat undifferentiated list is a design defect.
- **Timeline events need iconography** — goals (⚽), yellow cards (🟨), red cards (🟥), substitutions (↕), and VAR decisions each need a distinct visual marker in the match timeline, not just text labels.
- **Stat bars over raw numbers** — wherever a percentage or comparative metric exists (possession, pass accuracy, shots on target), render it as a proportional bar alongside the number. Raw numbers in a table with no visual encoding underuse the medium.
- **Colour token discipline** — use CSS variables for all base colours; override with team-specific colours only for team-attributed elements.
- **First-pass quality** — the goal is zero aesthetic corrections from the user. Deliver a report that reads like a professional post-match intelligence brief.

---

## Trigger Phrases

**Match report** — use when the user says any of:
- "generate a match report for X vs Y"
- "match intelligence report for [Team A] vs [Team B]"
- "produce a WC2026 report for [fixture]"
- "create a FIFA report for [match]"
- "run the match report script for [match_id]"

**Player report** — use when the request centres on one player:
- "create a player report for [Player]"
- "player intelligence report for [Player]"
- "WC2026 report for [Player]" (a person, not a fixture)
- "run the player report script for [player_id]"

---

## Player Report Mode

When the request is about a **single player**, run the player generator instead of the match one. It queries the KG live and emits the full player report — hero, tournament snapshot, an **assist→goal creation map** and a **shot map** drawn from real event XY coordinates, an in-match **temporal "how he changes the game"** section (Chart.js line charts + first/second-half split), match log, passing, physical, attacking, squad-comparison charts (assist leaders + creative-profile radar), defensive, progression, SPARQL, and sources.

```bash
# By name (resolved to a player id via SPARQL automatically):
python3 scripts/player_report_create.py "Jude Bellingham"

# By numeric player id, with options:
python3 scripts/player_report_create.py 448202 \
  --out <output_dir>/jude-bellingham-wc2026-report.html \
  --image "https://digitalhub.fifa.com/transform/.../BELLINGHAM_..."   # optional hero photo
```

Options: `--out` (default `<name>-wc2026-report.html`), `--image` (optional hero photo URL — omit if not known), `--accent` / `--accent2` (default: **auto from the player's nation**, using the same palette as `references/team-colours.md`).

**Behaviour & guarantees (already handled by the script — do not re-implement):**
- **Name → id**: a non-numeric first argument is resolved via `rdfs:label` match; ambiguous names print candidates and use the closest. Prefer passing the id when known.
- **Event coordinates**: uses `fifa:eventPlayer` + `fifa:positionX/Y`; attacking direction is normalised per (match, half) so the player always attacks right. See `world-cup-2026-navigator` for the coordinate/temporal model.
- **Temporal**: in-match `fifa:PlayerMatchAnalyticsReport` snapshots keyed by `fifa:timePlayed` (not `generatedAt`).
- **KG deep-links**: hero name → the player's `/describe`; assist markers → the **assist event** instance; shot markers → the **shot event** instance. Tooltips are instant, page-CSS styled (no native browser tooltips).
- **Theming**: light/dark aware; charts re-theme via a `data-theme` MutationObserver.
- Chart.js 4.4.3 is loaded from CDN; the rest is a self-contained single file (Python 3 stdlib only, no third-party deps).

Only fall back to hand-building if Python 3 is unavailable — the script is the source of truth for the player report, exactly as `report_template_create.py` is for the match report. Do **not** edit `report_template_create.py` for player-report work.

**Player-report verification** (quick gate): no unresolved `{placeholders}`; 12 `<section>`s; 6 `<canvas>` charts; 2 pitch `<svg>`s; hero name is an `<a>` to `/describe`; every `svg a[data-tip]` href resolves to a `/fifa-kg/event-*` (assist/shot) or player IRI; `--accent` matches the nation.

---

## Companion Skills (load before any query or HTML work)

| Skill | Purpose |
|---|---|
| `world-cup-2026-navigator` | Correct SPARQL property URIs, coded values, named graph routing |
| `rdf-infographic-skill` | Visual design, colour contrast, entity-link styling, footer attribution contract |

---

## Execution Routing (priority order)

0. **Player report?** If the request is about one player, use `scripts/player_report_create.py <player_id|name>` (see **Player Report Mode** above) and skip the match steps.
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
| 6 | All coaches — head (`fifa:CoachRole-0`) + assistants (`fifa:CoachRole-1`) | `urn:worldcup:kg:2026` |
| 7 | Squad / lineup (`fifa:hasPlayerAppearance`, `fifa:playerStatus`, `fifa:position`) | `urn:worldcup:kg:2026` |
| 8 | Team analytics (latest `MAX(fifa:generatedAt)` snapshot) | `urn:worldcup:kg:2026:analytics` |
| 9 | Player analytics (latest snapshot, cross-ref squad for team assignment) | `urn:worldcup:kg:2026:analytics` |

**Critical notes:**
- Analytics graph uses match IRI (`http://demo.openlinksw.com/fifa-kg#match-{id}`), not `matchId`. Use `GRAPH` clauses to scope subqueries.
- `fifa:CoachRole-0` = Head Coach; `fifa:CoachRole-1` = Assistant Coach.
- Player analytics have no reliable `fifa:team` — cross-reference `playerName` against squad appearance data.
- Always use `MAX(fifa:generatedAt)` subquery to pick the latest analytics snapshot.
- **`fifa:Tactic-*` entities have no `rdfs:label`** — extract formation from URI: `BIND(REPLACE(STR(?htac),".*#Tactic-","") AS ?homeTactic)`.
- **`fifa:CardType-*` entities have no `rdfs:label`** — extract code from URI: `BIND(REPLACE(STR(?c),".*#CardType-","") AS ?cardCode)`. Only two codes exist in WC2026 data: `1`=Yellow, `2`=Red card (straight or second yellow — both coded identically). `CardType-3` is not present in the data.
- **`fifa:Position-*` entities have no `rdfs:label`** — extract code from URI: `BIND(REPLACE(STR(?pos),".*#Position-","") AS ?posCode)`. Code 0=GK, 1=DEF, 2=MID, 3=FWD.
- **`fifa:playerStatus`** on `fifa:PlayerAppearance`: 1=starter, 2=substitute.
- None of the above coded-value entity types carry `rdfs:label` — always extract from the URI local name.

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
| `#formations` | Lineup cards: GK / DEF / MID / ATK / Subs / Coach / Assistant Coaches |
| `#core-players` | Top players by distance + Distance & Speed Comparison card |
| `#sparql` | SPARQL accordion (≥3 numbered queries with live links) |
| `#sources` | Attribution footer (7 cards) |

## Step 7 — 12-point verification gate

Run before saving. All must pass:

1. `og:image` meta tag present
2. Hero image from `digitalhub.fifa.com` in captioned `<div>` with "Image source" line
3. `#formations` section contains both lineup cards with `lineup-group` elements for GK / DEF / MID / ATK
4. Substitutions group present in each lineup card
5. Coach and Assistant Coaches groups present in each lineup card
6. ≥ 10 entity-link player rows in `#core-players`
7. Pressing gauges populated
8. Timeline populated (all goals, bookings, subs)
9. Red cards (`CardType-2`) show 🟥 in timeline and annotations — never 🟨
10. Distance & Speed Comparison `compare-block` card with `var(--accent)` / `var(--accent-dim)` bars
11. `--accent` ≠ `--accent-dim` (visually distinct colours)
12. Attribution footer has exactly 7 `<div class="attr-card">` elements
13. Footer copyright: `© 2026 OpenLink Software · FIFA World Cup 2026 Match Intelligence`
14. Head coaches identified via `fifa:CoachRole-0`; assistant coaches via `fifa:CoachRole-1`
15. Section/card `.section-title` and `.card-title` elements have `onclick="copyAnchor(this)"` and hover tooltip

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
