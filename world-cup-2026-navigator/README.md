# World Cup 2026 Navigator Skill

Expert navigator for the OpenLink FIFA World Cup Knowledge Graph and RDF ontology. Query match data, players, teams, goals, analytics, and world rankings using SPARQL.

## Overview

This Claude Code skill provides authoritative guidance for writing SPARQL queries against the FIFA World Cup 2026 Knowledge Graph hosted on Virtuoso. It covers class hierarchies, property URIs, coded values, and query patterns for every type of match data.

## Installation

```bash
# Copy to Claude Code skills directory
cp -r world-cup-2026-navigator ~/.claude/skills/

# Or use as a skill bundle
# (ZIP file can be distributed)
```

## Usage

### Match Results

```
User: "Show me all group stage match results with scores"

Skill: Writes correct SPARQL using fifa:Match, fifa:homeTeamScore, fifa:awayTeamScore
       against urn:worldcup:kg:2026
```

### Analytics & xG

```
User: "Compare xG and pitch control for all Round of 16 matches"

Skill: Queries urn:worldcup:kg:2026:analytics using fifa:TeamMatchAnalyticsReport,
       joins with main graph for labels, returns latest snapshot per team per match
```

### FIFA World Rankings

```
User: "List the top 20 FIFA world rankings with movement"

Skill: Queries urn:fifa:powerrankings using fifa:PowerRanking,
       applies MAX(fifa:generatedAt) pattern for latest snapshot per team
```

## Features

✅ Correct namespace prefixes for every query
✅ Named graph guidance (`urn:worldcup:kg:2026`, `:analytics`, `urn:fifa:powerrankings`)
✅ Complete class reference — Match, Player, Team, Goal, Booking, Official, Analytics
✅ Coded value tables — card types, goal types, match periods, positions, event types
✅ 15+ ready-to-use query patterns covering all common use cases
✅ Analytics metrics reference (100+ properties for shooting, passing, pressing, physical)
✅ Win probability inference formulas (Elo logistic via FIFA power rankings)
✅ EventQualifier and timeline event navigation for spatial/VAR data
✅ Anti-trap guidance (no raw integer filters, use instance URIs; prefer analytics reports over raw event counts)

## Examples

See `references/properties.md` for the complete property table with domains, ranges, and data types.
See `references/coded-values.md` for expanded coded value tables with usage examples.

## File Structure

```
world-cup-2026-navigator/
├── SKILL.md                    # Main skill definition
├── README.md                   # This file
└── references/
    ├── properties.md           # Complete property table
    └── coded-values.md         # Expanded coded value reference
```

## How It Works

1. **User asks a FIFA KG question**
   - Example: "Who scored in the Argentina vs France final?"

2. **Skill selects the correct graph and classes**
   - Main graph for match events, analytics graph for metrics
   - PowerRankings graph for FIFA/Coca-Cola world rankings

3. **Skill applies coded values correctly**
   - Instance URIs: `fifa:CardType-1`, `fifa:GoalType-2`, `fifa:MatchPeriod-5`
   - No raw integer filters on typed properties

4. **Skill avoids known anti-patterns**
   - Uses analytics reports for aggregate stats, not raw event counts
   - Applies `MAX(fifa:generatedAt)` for latest analytics snapshot
   - Uses `GRAPH` clause to prevent cross-graph collisions

5. **Output returned to the agent**
   - Executable SPARQL with correct prefixes
   - Execution notes (which graph, which endpoint, which pattern)

## Named Graphs

| Graph | Contents |
|---|---|
| `urn:worldcup:kg:2026` | Matches, teams, players, goals, bookings, substitutions, lineups, coaches, officials, stadiums, weather |
| `urn:worldcup:kg:2026:analytics` | `TeamMatchAnalyticsReport`, `PlayerMatchAnalyticsReport`, `PlayerPowerRanking` — timestamped snapshots |
| `urn:worldcup:kg:past-matches` | Historical H2H matches outside the 2026 season |
| `urn:fifa:powerrankings` | FIFA/Coca-Cola world rankings — `PowerRanking` snapshots per team |

## Key Namespace Prefixes

```sparql
PREFIX fifa:         <https://www.openlinksw.com/ontology/fifa#>
PREFIX position:     <https://fifa.com/position#>
PREFIX positionSide: <https://fifa.com/positionSide#>
PREFIX rdfs:         <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd:          <http://www.w3.org/2001/XMLSchema#>
```

## Common Trigger Phrases

- "Write a SPARQL for FIFA data"
- "Query goals / bookings / match events"
- "Show analytics for a team"
- "Compare xG / possession / pressing intensity"
- "FIFA world rankings / power rankings"
- "Win probability", "expected goals", "pitch control"
- "Who refereed a match", "list officials by role"
- "Find players by country / position"
- "Query urn:fifa:powerrankings"

## Ontology

- **Namespace**: `https://www.openlinksw.com/ontology/fifa#`
- **License**: CC-BY-SA 3.0
- **Creator**: Daniel Heward-Mills

## Version

1.0.0
