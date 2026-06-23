---
name: world-cup-2026-navigator
description: >
  Expert navigator for the OpenLink FIFA World Cup Knowledge Graph and RDF
  ontology (https://www.openlinksw.com/ontology/fifa#). Use this skill whenever
  an agent needs to write SPARQL queries against FIFA World Cup knowledge graph
  data, look up correct property URIs, understand class hierarchies, interpret
  numeric coded values (card types, match periods, event types, positions,
  tactics), design query patterns for matches, players, teams, goals, bookings,
  substitutions, lineups, weather, rankings, analytics metrics, match officials,
  referees, country/nationality data, FIFA power rankings, win probability,
  expected goals (xG), pitch control, goalkeeper saves, or the power rankings
  named graph (urn:fifa:powerrankings).
  Trigger this skill for ANY FIFA ontology or KG query-writing task, even if the
  user just says "write a SPARQL for FIFA data", "how do I query
  goals/players/match events", "show me analytics for a team", "compare player
  distances run", "possession stats", "pressing intensity", "query match
  analytics reports", "who refereed a match", "list officials by role", "find
  players by country", "FIFA world rankings", "power rankings", "win probability",
  "xG", "expected goals", "pitch control", "goalkeeper stats", or "query
  urn:fifa:powerrankings".
---

# World Cup Knowledge Graph Navigator

## Namespace Prefixes

Always declare these prefixes at the top of every SPARQL query:

```sparql
PREFIX fifa:      <https://www.openlinksw.com/ontology/fifa#>
PREFIX position:  <https://fifa.com/position#>
PREFIX positionSide: <https://fifa.com/positionSide#>
PREFIX rdfs:      <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd:       <http://www.w3.org/2001/XMLSchema#>
```

For ontology metadata queries also declare:

```sparql
PREFIX dc:     <http://purl.org/dc/elements/1.1/>
PREFIX cc:     <http://creativecommons.org/ns#>
PREFIX owl:    <http://www.w3.org/2002/07/owl#>
PREFIX prov:   <http://www.w3.org/ns/prov#>
```

**Full namespace URIs (for reference):**

| Prefix | Full URI | Used for |
|---|---|---|
| `fifa:` | `https://www.openlinksw.com/ontology/fifa#` | All classes, most properties |
| `position:` | `https://fifa.com/position#` | Position instances (0=GK, 1=DEF, 2=MID, 3=FWD) |
| `positionSide:` | `https://fifa.com/positionSide#` | Position side instances (1=right, 2=center, 3=left) |
| `dc:` | `http://purl.org/dc/elements/1.1/` | Ontology metadata (creator) |
| `cc:` | `http://creativecommons.org/ns#` | Ontology license (CC-BY-SA 3.0) |
| `prov:` | `http://www.w3.org/ns/prov#` | PROV-O (prov:wasDerivedFrom) |

---

## Named Graphs

| Graph | Contents |
|---|---|
| `urn:worldcup:kg:2026` | Main graph: competition, season, stage, group, team, player, squad, match, stadium, coach, staff, officials, lineup, goals, bookings, substitutions, timeline events, head-to-head analysis |
| `urn:worldcup:kg:2026:analytics` | Temporal snapshots: `fifa:TeamMatchAnalyticsReport`, `fifa:PlayerMatchAnalyticsReport`, `fifa:PlayerPowerRanking`. Each call appends a timestamped report. |
| `urn:worldcup:kg:past-matches` | Historical matches from the H2H API not in the 2026 season graph. Same `fifa:Match` structure as the main graph. |
| `urn:fifa:powerrankings` | Temporal snapshots of the FIFA/Coca-Cola world ranking (`fifa:PowerRanking`), one per team. Also holds `fifa:Confederation`, `fifa:Gender`, and team stub nodes. Self-contained graph. |

When writing SPARQL, always specify the graph with `FROM <graph-iri>` or `GRAPH <graph-iri> { }` unless you want to query all graphs (which can cause duplicates if the same match IRI appears in both the main and analytics graphs).

---

## Ontology Metadata

```turtle
<https://www.openlinksw.com/ontology/fifa#> rdf:type owl:Ontology ;
    rdfs:label "FIFA World Cup Ontology" ;
    dc:creator <https://github.com/danielhmills/#this> ;
    cc:license <https://creativecommons.org/licenses/by-sa/3.0/> .
```

License: **CC-BY-SA 3.0**.

---

## Class Reference

| Class | URI | Notes |
|---|---|---|
| Competition | `fifa:Competition` | e.g. FIFA World Cup |
| Season | `fifa:Season` | A season/edition of a competition (e.g. 2022 World Cup) |
| Stage | `fifa:Stage` | Group stage, Round of 16, Final, etc. |
| Group | `fifa:Group` | Groups A–H within a stage |
| Match | `fifa:Match` | Central hub — connects everything |
| Team | `fifa:Team` | National teams |
| Player | `fifa:Player` | Individual players |
| Stadium | `fifa:Stadium` | Venue |
| City | `fifa:City` | Host city |
| Goal | `fifa:Goal` | A goal event; subclass of `fifa:MatchEvent` |
| Booking | `fifa:Booking` | Yellow/red card event |
| Substitution | `fifa:Substitution` | Player swap event |
| GoalType | `fifa:GoalType` | Controlled vocabulary for goal types (penalty, regular, own) |
| CardType | `fifa:CardType` | Controlled vocabulary for card types |
| MatchPeriod | `fifa:MatchPeriod` | Controlled vocabulary for match periods |
| PlayerMatchAppearance | `fifa:PlayerMatchAppearance` | Lineup slot for a player in a match |
| MatchEvent | `fifa:MatchEvent` | Abstract base class for all timeline events |
| Foul | `fifa:Foul` | Subclass of MatchEvent — fouls and disciplinary events |
| SetPiece | `fifa:SetPiece` | Subclass of MatchEvent — free kicks, corners, throw-ins |
| EventQualifier | `fifa:EventQualifier` | Supplementary annotation attached to a match event — spatial coordinates, jersey numbers, injured-player refs, cross-event links |
| Coach | `fifa:Coach` | Team coach |
| CoachRole | `fifa:CoachRole` | Coded role held by a coach (Head Coach, Assistant Coach) |
| Staff | `fifa:Staff` | Non-playing technical/support staff member — can appear on `fifa:Booking` |
| StaffRole | `fifa:StaffRole` | Coded role held by a staff member |
| CoachAssignment | `fifa:CoachAssignment` | Coach ↔ Match link |
| StaffAssignment | `fifa:StaffAssignment` | Staff ↔ Match link |
| Official | `fifa:Official` | A match official (referee, assistant, etc.) |
| OfficialAssignment | `fifa:OfficialAssignment` | Official ↔ Match assignment record |
| OfficialType | `fifa:OfficialType` | Named class for role taxonomy (Referee, VAR, etc.) |
| Country | `fifa:Country` | Country/football association — nationality of teams, players, officials |
| Tactic | `fifa:Tactic` | Formation (e.g. 4-3-3) |
| Weather | `fifa:Weather` | Match weather data |
| BallPossession | `fifa:BallPossession` | Possession % per match |
| WorldRanking | `fifa:WorldRanking` | Team ranking snapshot at a point in time |
| **PowerRanking** | `fifa:PowerRanking` | Timestamped FIFA/Coca-Cola world ranking snapshot per team. Lives in `urn:fifa:powerrankings`. |
| SquadMembership | `fifa:SquadMembership` | Team ↔ Player during a specific season |
| TeamMembership | `fifa:TeamMembership` | Player ↔ Team with temporal bounds |
| **MatchAnalyticsReport** | `fifa:MatchAnalyticsReport` | Abstract base for analytics reports |
| **TeamMatchAnalyticsReport** | `fifa:TeamMatchAnalyticsReport` | Per-team analytics report for a match (`urn:worldcup:kg:2026:analytics`) |
| **PlayerMatchAnalyticsReport** | `fifa:PlayerMatchAnalyticsReport` | Per-player analytics report for a match (`urn:worldcup:kg:2026:analytics`) |
| PlayerPowerRanking | `fifa:PlayerPowerRanking` | Timestamped player in-match performance ranking snapshot (`urn:worldcup:kg:2026:analytics`) |
| HeadToHeadAnalysis | `fifa:HeadToHeadAnalysis` | H2H stats between two teams for a match |
| Organization | `fifa:Organization` | Governing/organizational body |
| Confederation | `fifa:Confederation` | Continental confederation (UEFA, CONMEBOL, etc.); subClassOf `fifa:Organization` |
| Gender | `fifa:Gender` | Gender category (instances: `fifa:Male`, `fifa:Female`) |
| AnalyticsMetricProperty | `fifa:AnalyticsMetricProperty` | Meta-class tagging all analytics datatype properties |

---

## The Match Node — Query Hub

`fifa:Match` is the central node. Nearly all interesting data hangs off it:

```
fifa:Match
  ├── fifa:homeTeam / fifa:awayTeam              → fifa:Team
  ├── fifa:homeTeamScore / fifa:awayTeamScore    → xsd:integer
  ├── fifa:winner                                → fifa:Team
  ├── fifa:date / fifa:localDate                 → xsd:dateTime
  ├── fifa:attendance                            → xsd:integer
  ├── fifa:stadium                               → fifa:Stadium
  ├── fifa:stage                                 → fifa:Stage
  ├── fifa:season                                → fifa:Season
  ├── fifa:competition                           → fifa:Competition
  ├── fifa:group                                 → fifa:Group
  ├── fifa:homeTeamTactics / fifa:awayTeamTactics → fifa:Tactic
  ├── fifa:weather                               → fifa:Weather
  ├── fifa:ballPossession                        → fifa:BallPossession
  ├── fifa:hasGoal                               → fifa:Goal
  ├── fifa:hasBooking                            → fifa:Booking
  ├── fifa:hasSubstitution                       → fifa:Substitution
  ├── fifa:hasPlayerAppearance                   → fifa:PlayerMatchAppearance
  ├── fifa:hasCoach                              → fifa:CoachAssignment
  ├── fifa:hasStaffAssignment                    → fifa:StaffAssignment
  ├── fifa:hasOfficial                           → fifa:Official  (direct person node)
  ├── fifa:hasOfficialAssignment                 → fifa:OfficialAssignment
  ├── fifa:hasHeadToHeadAnalysis                 → fifa:HeadToHeadAnalysis
  ├── fifa:hasNewsArticle                        → schema:NewsArticle (FIFA Plus articles)
  ├── fifa:hasEvent                              → fifa:MatchEvent
  │                                                  ├── fifa:hasQualifier → fifa:EventQualifier
  │                                                  ├── fifa:Goal      (subclass)
  │                                                  ├── fifa:Foul      (subclass)
  │                                                  └── fifa:SetPiece  (subclass)
  ├── fifa:hasTeamAnalyticsReport                → fifa:TeamMatchAnalyticsReport
  └── fifa:hasPlayerAnalyticsReport              → fifa:PlayerMatchAnalyticsReport
```

**Inferred match probability properties** (derived via SPIN rules in `wc2026_power_ranking_inference.sql`):

| Property | Description |
|---|---|
| `fifa:homeTeamWinProbabilityByFifaRank` | Home-team win probability (0–100 %) via Elo logistic: 1/(1+10^((awayPts-homePts)/600)) |
| `fifa:awayTeamWinProbabilityByFifaRank` | Away-team win probability: 1/(1+10^((homePts-awayPts)/600)) |
| `fifa:homeTeamLossProbabilityByFifaRank` | Home-team loss probability = away win probability |
| `fifa:awayTeamLossProbabilityByFifaRank` | Away-team loss probability = home win probability |

---

## PowerRanking — FIFA/Coca-Cola World Rankings

### Named Graph

All `fifa:PowerRanking` data lives in **`urn:fifa:powerrankings`**. The graph is self-contained and also holds `fifa:Confederation`, `fifa:Gender`, and team stub nodes.

### IRI Pattern

```
http://demo.openlinksw.com/fifa-kg#powerranking-{teamId}-{genTs}
```
`{genTs}` = ingestion timestamp (`yyyymmddTHHMMSS`).

### PowerRanking Properties

| Property | Type | Range | Notes |
|---|---|---|---|
| `fifa:hasTeam` | Object | `fifa:Team` | The team described |
| `fifa:hasConfederation` | Object | `fifa:Confederation` | The team's confederation |
| `fifa:gender` | Object | `fifa:Gender` | `fifa:Male` or `fifa:Female` |
| `fifa:rank` | Datatype | `xsd:integer` | Ranking position in this snapshot |
| `fifa:prevRank` | Datatype | `xsd:integer` | Previous ranking position |
| `fifa:rankingMovement` | Datatype | `xsd:integer` | Net change (positive = moved up) |
| `fifa:ratedMatches` | Datatype | `xsd:integer` | Matches counted towards ranking |
| `fifa:totalPoints` | Datatype | `xsd:decimal` | Ranking points total |
| `fifa:prevPoints` | Datatype | `xsd:decimal` | Previous ranking points |
| `fifa:generatedAt` | Datatype | `xsd:dateTime` | Ingestion timestamp |

A new snapshot is recorded **only when a team's rated-match count or rank changes** — to avoid redundant data. Use `MAX(fifa:generatedAt)` to retrieve the latest snapshot for each team.

### PowerRanking Query Pattern

```sparql
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?team ?teamName ?confederation ?rank ?rankingMovement ?totalPoints ?generatedAt
WHERE {
  GRAPH <urn:fifa:powerrankings> {
    ?snapshot a fifa:PowerRanking ;
              fifa:hasTeam ?team ;
              fifa:hasConfederation ?confederation ;
              fifa:rank ?rank ;
              fifa:rankingMovement ?rankingMovement ;
              fifa:totalPoints ?totalPoints ;
              fifa:generatedAt ?generatedAt .
    ?team rdfs:label ?teamName .
    # Restrict to latest snapshot per team
    {
      SELECT ?team (MAX(?gen) AS ?generatedAt)
      WHERE {
        GRAPH <urn:fifa:powerrankings> {
          ?r a fifa:PowerRanking ; fifa:hasTeam ?team ; fifa:generatedAt ?gen .
        }
      }
      GROUP BY ?team
    }
  }
}
ORDER BY ?rank
LIMIT 50
```

---

## Analytics Reports

### Class Hierarchy

```
fifa:MatchAnalyticsReport  (abstract base)
  ├── fifa:TeamMatchAnalyticsReport    — one report per team per match
  └── fifa:PlayerMatchAnalyticsReport  — one report per player per match
```

Both live in **`urn:worldcup:kg:2026:analytics`**. Both share the same pool of `fifa:AnalyticsMetricProperty` datatype properties (all `xsd:decimal`). Each report carries `fifa:generatedAt` (`xsd:dateTime`) for temporal versioning.

### Accessing Analytics Reports

```sparql
# Team-level analytics (from analytics graph)
?match fifa:hasTeamAnalyticsReport ?report .
?report fifa:match ?match ; fifa:team ?team ; fifa:generatedAt ?generatedAt .

# Player-level analytics
?match fifa:hasPlayerAnalyticsReport ?report .
?report fifa:match ?match ; fifa:player ?player ; fifa:generatedAt ?generatedAt .
```

### Discovering Available Metrics

```sparql
SELECT ?prop ?label WHERE {
  ?prop rdf:type fifa:AnalyticsMetricProperty ;
        rdfs:label ?label .
}
ORDER BY ?label
```

### Analytics Metric Properties

All have domain `fifa:MatchAnalyticsReport`, range `xsd:decimal`. Use `OPTIONAL` for every metric — not all reports populate every field.

**Shooting & Goals**

| Property | Description |
|---|---|
| `fifa:goals` | Goals scored |
| `fifa:goalsConceded` | Goals conceded |
| `fifa:goalsConcededFromAttemptAtGoalAgainst` | Goals conceded from opponent shots |
| `fifa:goalsFromDirectFreeKicks` | Goals from direct free kicks |
| `fifa:goalsInsideThePenaltyArea` | Goals scored inside the box |
| `fifa:goalsOutsideThePenaltyArea` | Goals scored outside the box |
| `fifa:ownGoals` | Own goals |
| `fifa:xG` | Expected goals — probability-weighted sum of chances |
| `fifa:attemptAtGoal` | Total attempts at goal |
| `fifa:attemptAtGoalAgainst` | Opponent attempts at goal |
| `fifa:attemptAtGoalAgainstOnTarget` | Opponent attempts on target |
| `fifa:attemptAtGoalBlocked` | Attempts blocked |
| `fifa:attemptAtGoalOnTarget` | Attempts on target |
| `fifa:attemptAtGoalOffTarget` | Attempts off target |
| `fifa:attemptAtGoalFromFreeKicks` | Attempts from free kicks |
| `fifa:attemptAtGoalInsideThePenaltyArea` | Attempts from inside the box |
| `fifa:attemptAtGoalInsideThePenaltyAreaOnTarget` | Attempts from inside box on target |
| `fifa:attemptAtGoalOutsideThePenaltyArea` | Attempts from outside the box |
| `fifa:attemptAtGoalOutsideThePenaltyAreaOnTarget` | Attempts from outside box on target |
| `fifa:headedAttemptAtGoal` | Headed attempts |
| `fifa:penalties` | Penalties awarded |
| `fifa:penaltiesScored` | Penalties scored |
| `fifa:attemptAtGoalFromBallProgression` | Attempts from ball progressions |
| `fifa:attemptAtGoalFromCorner` | Attempts from corners |
| `fifa:attemptAtGoalFromCross` | Attempts from crosses |
| `fifa:attemptAtGoalFromPass` | Attempts from passes |
| `fifa:attemptAtGoalFromPenalty` | Attempts taken as penalty kicks |
| `fifa:attemptAtGoalFromRebound` | Attempts from rebounds |
| `fifa:attemptAtGoalFromOther` | Attempts from other / uncategorised |

**Passing & Ball Control**

| Property | Description |
|---|---|
| `fifa:passes` | Total passes attempted |
| `fifa:passesCompleted` | Passes completed |
| `fifa:possession` | Ball possession % |
| `fifa:crosses` | Crosses attempted |
| `fifa:crossesCompleted` | Crosses completed |
| `fifa:assists` | Assists |
| `fifa:attemptedBallProgressions` | Ball progressions attempted |
| `fifa:completedBallProgressions` | Ball progressions completed |
| `fifa:attemptedSwitchesOfPlay` | Switches of play attempted |
| `fifa:completedSwitchesOfPlay` | Switches of play completed |
| `fifa:distributionsUnderPressure` | Distributions under pressure |
| `fifa:distributionsCompletedUnderPressure` | Distributions completed under pressure |
| `fifa:takeOnsCompleted` | Take-ons (dribbles) completed |
| `fifa:numberOfInvolvements` | Touches/actions in possession sequences |
| `fifa:numberOfPossessionSequences` | Total distinct possession sequences |
| `fifa:numberOfShotEndingSequences` | Possession sequences ending with a shot |
| `fifa:ballRecoveryTime` | Avg time to recover ball after losing possession |

**Threat & Pitch Control**

| Property | Description |
|---|---|
| `fifa:threat` | FIFA Expected Threat (xT) — value of on-ball actions moving toward goal |
| `fifa:pitchControl` | Overall share of pitch controlled (by player positions/reachability) |
| `fifa:finalThirdPitchControl` | Pitch control share in the attacking final third |

**Defensive**

| Property | Description |
|---|---|
| `fifa:defensivePressuresApplied` | Defensive pressures applied |
| `fifa:directDefensivePressuresApplied` | Direct defensive pressures |
| `fifa:forcedTurnovers` | Turnovers forced |
| `fifa:foulsFor` | Fouls won |
| `fifa:foulsAgainst` | Fouls committed |
| `fifa:yellowCards` | Yellow cards (analytics count) |
| `fifa:redCards` | Red cards (analytics count) |
| `fifa:directRedCards` | Straight red cards (not from second caution) |
| `fifa:indirectRedCards` | Red cards from second yellow card |
| `fifa:offsides` | Offsides |
| `fifa:goalkeeperDefensiveActionsInsidePenaltyArea` | GK actions inside box |
| `fifa:goalkeeperDefensiveActionsOutsidePenaltyArea` | GK actions outside box |
| `fifa:goalkeeperGoalPreventions` | GK goal preventions |
| `fifa:goalkeeperSaves` | Total saves made by the goalkeeper |
| `fifa:goalkeeperSavesOnTarget` | Saves against on-target attempts |
| `fifa:goalkeeperSavePercentage` | % of on-target attempts saved |
| `fifa:cleanSheets` | Matches completed without conceding |

**Set Pieces**

| Property | Description |
|---|---|
| `fifa:corners` | Corners |
| `fifa:freeKicks` | Free kicks |
| `fifa:directFreeKicks` | Direct free kicks |
| `fifa:indirectFreeKicks` | Indirect free kicks |
| `fifa:goalKicks` | Goal kicks |
| `fifa:throwIns` | Throw-ins |

**Linebreaks & Progressions**

| Property | Description |
|---|---|
| `fifa:linebreaksAttempted` | Linebreaks attempted |
| `fifa:linebreaksAttemptedCompleted` | Linebreaks completed |
| `fifa:linebreaksAttemptedAllLines` | Linebreaks attempted across all lines |
| `fifa:linebreaksCompletedAllLines` | Linebreaks completed across all lines |
| `fifa:linebreaksAttemptedAttackingLine` | vs. attacking line (combined) |
| `fifa:linebreaksAttemptedAttackingLineCompleted` | vs. attacking line completed (combined) |
| `fifa:linebreaksAttemptedAttackingLineOnly` | vs. attacking line only |
| `fifa:linebreaksAttemptedAttackingLineCompletedOnly` | vs. attacking line only, completed |
| `fifa:linebreaksAttemptedMidfieldLine` | vs. midfield line (combined) |
| `fifa:linebreaksAttemptedMidfieldLineCompleted` | vs. midfield line completed (combined) |
| `fifa:linebreaksAttemptedMidfieldLineOnly` | vs. midfield line only |
| `fifa:linebreaksAttemptedMidfieldLineCompletedOnly` | vs. midfield line only, completed |
| `fifa:linebreaksAttemptedDefensiveLine` | vs. defensive line (combined) |
| `fifa:linebreaksAttemptedDefensiveLineCompleted` | vs. defensive line completed (combined) |
| `fifa:linebreaksAttemptedDefensiveLineOnly` | vs. defensive line only |
| `fifa:linebreaksAttemptedDefensiveLineCompletedOnly` | vs. defensive line only, completed |
| `fifa:linebreaksAttemptedAttackingAndMidfieldLine` | vs. attacking + midfield lines |
| `fifa:linebreaksCompletedAttackingAndMidfieldLine` | vs. attacking + midfield completed |
| `fifa:linebreaksAttemptedMidfieldAndDefensiveLine` | vs. midfield + defensive lines |
| `fifa:linebreaksCompletedMidfieldAndDefensiveLine` | vs. midfield + defensive completed |
| `fifa:linebreaksAttemptedUnderPressure` | Linebreaks under pressure |
| `fifa:linebreaksCompletedUnderPressure` | Linebreaks under pressure completed |

**Receptions & Offers to Receive**

| Property | Description |
|---|---|
| `fifa:receivedOffersToReceive` | Offers to receive acted upon |
| `fifa:offersToReceiveTotal` | Total offers to receive |
| `fifa:offersToReceiveInBehind` | Offers to receive in behind |
| `fifa:offersToReceiveInBetween` | Offers to receive in between lines |
| `fifa:offersToReceiveInFront` | Offers to receive in front |
| `fifa:offersToReceiveInside` | Offers to receive inside |
| `fifa:offersToReceiveOutside` | Offers to receive outside |
| `fifa:receptionsInBehind` | Receptions in behind |
| `fifa:receptionsBetweenMidfieldAndDefensiveLine` | Receptions between midfield and defensive line |
| `fifa:receptionsUnderPressure` | Receptions under pressure |
| `fifa:receptionsUnderDirectPressure` | Receptions under direct pressure |
| `fifa:receptionsUnderIndirectPressure` | Receptions under indirect pressure |
| `fifa:receptionsUnderNoPressure` | Receptions under no pressure |

**Final Third Entries**

| Property | Description |
|---|---|
| `fifa:finalThirdEntriesReceptionCentralChannel` | Final third entries via central channel |
| `fifa:finalThirdEntriesReceptionInsideLeftChannel` | Final third entries inside left channel |
| `fifa:finalThirdEntriesReceptionInsideRightChannel` | Final third entries inside right channel |
| `fifa:finalThirdEntriesReceptionLeftChannel` | Final third entries left channel |
| `fifa:finalThirdEntriesReceptionRightChannel` | Final third entries right channel |

**Tactical Phase Aggregates**

| Property | Description |
|---|---|
| `fifa:phaseAggregateAttackingTransition` | Attacking transition phase |
| `fifa:phaseAggregateDefensiveTransition` | Defensive transition phase |
| `fifa:phaseAggregateBuildUpOpposed` | Build-up play (opposed) |
| `fifa:phaseAggregateBuildUpUnopposed` | Build-up play (unopposed) |
| `fifa:phaseAggregateCounterPress` | Counter-press phase |
| `fifa:phaseAggregateCounterattack` | Counterattack phase |
| `fifa:phaseAggregateFinalThird` | Final third phase |
| `fifa:phaseAggregateHighBlock` | High defensive block phase |
| `fifa:phaseAggregateHighPress` | High press phase |
| `fifa:phaseAggregateMidBlock` | Mid block phase |
| `fifa:phaseAggregateMidPress` | Mid press phase |
| `fifa:phaseAggregateLowBlock` | Low block phase |
| `fifa:phaseAggregateLowPress` | Low press phase |
| `fifa:phaseAggregateLongBall` | Long ball phase |
| `fifa:phaseAggregateProgression` | Progression phase |
| `fifa:phaseAggregateRecovery` | Recovery phase |
| `fifa:phaseAggregateSetPieces` | Set pieces phase |

**Physical / Movement (Player-level)**

| Property | Description |
|---|---|
| `fifa:totalDistance` | Total distance covered |
| `fifa:distanceWalking` | Distance walking |
| `fifa:distanceJogging` | Distance jogging |
| `fifa:distanceLowSpeedSprinting` | Distance at low-speed sprint |
| `fifa:distanceHighSpeedRunning` | Distance at high-speed running |
| `fifa:distanceHighSpeedSprinting` | Distance at high-speed sprint |
| `fifa:avgSpeed` | Average speed |
| `fifa:topSpeed` | Top speed |
| `fifa:sprints` | Number of sprints |
| `fifa:speedRuns` | Number of speed runs |
| `fifa:timePlayed` | Minutes played |
| `fifa:substitutionsIn` | Times substituted on |
| `fifa:substitutionsOut` | Times substituted off |

**Aggregate / Multi-match**

| Property | Description |
|---|---|
| `fifa:matchesPlayed` | Number of matches the report aggregates |

---

## Coded Value Reference

> **Critical**: Many properties use instance URIs, not raw integers.

### Card Types (`fifa:bookingCard`)
| Instance URI | Label |
|---|---|
| `fifa:CardType-1` | Yellow Card |
| `fifa:CardType-2` | Second Yellow Card |
| `fifa:CardType-3` | Straight Red Card |

### Goal Types (`fifa:goalType`)
| Instance URI | Label |
|---|---|
| `fifa:GoalType-1` | Penalty Goal |
| `fifa:GoalType-2` | Regular Goal |
| `fifa:GoalType-3` | Own Goal |

### Match Periods
| Instance URI | Label |
|---|---|
| `fifa:MatchPeriod-0` | Pre-Match |
| `fifa:MatchPeriod-3` | First Half |
| `fifa:MatchPeriod-4` | Half-Time |
| `fifa:MatchPeriod-5` | Second Half |
| `fifa:MatchPeriod-7` | Extra Time First Half |
| `fifa:MatchPeriod-8` | Extra Time Half-Time |
| `fifa:MatchPeriod-9` | Extra Time Second Half |
| `fifa:MatchPeriod-10` | Full Time |
| `fifa:MatchPeriod-11` | Penalty Kicks |

### Gender Instances
| Instance URI | Label |
|---|---|
| `fifa:Male` | Male |
| `fifa:Female` | Female |

### Positions (`fifa:position`, `fifa:realPosition`)

Two sets of position instances exist in the ontology, both typed as `a fifa:Position`:

| Instance URI | Namespace | Label | Used by |
|---|---|---|---|
| `position:0` / `fifa:Position-0` | `position:` / `fifa:` | Goalkeeper | squad loader / JSON match loader |
| `position:1` / `fifa:Position-1` | `position:` / `fifa:` | Defender | squad loader / JSON match loader |
| `position:2` / `fifa:Position-2` | `position:` / `fifa:` | Midfielder | squad loader / JSON match loader |
| `position:3` / `fifa:Position-3` | `position:` / `fifa:` | Forward | squad loader / JSON match loader |

> **Position IRI in practice**: The JSON match loader emits `fifa:Position-N` IRIs for `fifa:PlayerMatchAppearance` nodes. The squad loader emits `position:N` IRIs on `fifa:Player` bio nodes. When querying lineups use `fifa:Position-N`; when querying player bio use `position:N`. To cover both, use `UNION` or `VALUES ?pos { position:3 fifa:Position-3 }`.

### Position Sides (`fifa:realPositionSide`, `fifa:positionSide`)

**`positionSide:` namespace** (squad loader bio data, `https://fifa.com/positionSide#`):

| Instance URI | Label |
|---|---|
| `positionSide:1` | right side |
| `positionSide:2` | center |
| `positionSide:3` | left side |

**`fifa:` namespace** (JSON match loader lineup data):

| Instance URI | Label |
|---|---|
| `fifa:PositionSide-1` | right side |
| `fifa:PositionSide-2` | center |
| `fifa:PositionSide-3` | Unknown (side not determined) |

> `fifa:PositionSide-3` is "Unknown" (side not determined), whereas `positionSide:3` is the canonical "left side" individual.

### Tactics
| Instance URI | Label |
|---|---|
| `fifa:Tactic-4-3-3` | 4-3-3 |
| `fifa:Tactic-4-4-2` | 4-4-2 |
| `fifa:Tactic-4-5-1` | 4-5-1 |
| `fifa:Tactic-3-5-2` | 3-5-2 |
| `fifa:Tactic-3-4-3` | 3-4-3 |
| `fifa:Tactic-3-6-1` | 3-6-1 |
| `fifa:Tactic-5-3-2` | 5-3-2 |
| `fifa:Tactic-5-4-1` | 5-4-1 |

### Official Type Instances
| Instance URI | Label |
|---|---|
| `fifa:OfficialType-1` | Referee |
| `fifa:OfficialType-2` | Assistant Referee 1 |
| `fifa:OfficialType-3` | Assistant Referee 2 |
| `fifa:OfficialType-4` | Fourth official |
| `fifa:OfficialType-5` | Video Assistant Referee (VAR) |
| `fifa:OfficialType-6` | Reserve referee |
| `fifa:OfficialType-8` | Assistant VAR |
| `fifa:OfficialType-9` | Support VAR |

### Coach Role Instances
| Instance URI | Label |
|---|---|
| `fifa:CoachRole-0` | Head Coach |
| `fifa:CoachRole-1` | Assistant Coach |

### Event Types (subclasses of `fifa:MatchEvent` via `rdf:type`)

> **OWL equivalentClass notes**: `fifa:EventType-0` ≡ `fifa:Goal`, `fifa:EventType-2` ≡ `fifa:Booking`, `fifa:EventType-5` ≡ `fifa:Substitution`. The preferred classes are `fifa:Goal`, `fifa:Booking`, `fifa:Substitution` — use those rather than the coded EventType equivalents.

**Subclass hierarchy:**
```
fifa:MatchEvent
  ├── fifa:Goal      (preferred — equiv: EventType-0)
  │     ├── fifa:EventType-34  (Own goal)
  │     ├── fifa:EventType-39  (Free Kick goal)
  │     └── fifa:EventType-41  (Penalty Goal)
  ├── fifa:Booking   (preferred — equiv: EventType-2)
  │     ├── fifa:EventType-3   (Red card)
  │     └── fifa:EventType-4   (Second Caution - Red Card)
  ├── fifa:Foul
  │     └── fifa:EventType-18  (Foul)
  ├── fifa:SetPiece
  │     ├── fifa:EventType-14  (Free Kick)
  │     ├── fifa:EventType-16  (Corner)
  │     └── fifa:EventType-24  (Throw In)
  ├── fifa:Substitution (preferred — equiv: EventType-5)
  ├── fifa:EventType-1   (Assist)
  ├── fifa:EventType-6   (Penalty Awarded)
  ├── fifa:EventType-7   (Start Time)
  ├── fifa:EventType-8   (End Time)
  ├── fifa:EventType-9   (Pause Time)
  ├── fifa:EventType-10  (Resume Time)
  ├── fifa:EventType-12  (Attempt at Goal)
  ├── fifa:EventType-15  (Offside)
  ├── fifa:EventType-17  (Goal Prevention)
  ├── fifa:EventType-19  (Coin Toss)
  ├── fifa:EventType-23  (Dropped Ball)
  ├── fifa:EventType-25  (Clearance)
  ├── fifa:EventType-26  (Match end)
  ├── fifa:EventType-27  (Aerial Duel)
  ├── fifa:EventType-33  (Attempt Missed)
  ├── fifa:EventType-49  (Attempt Missed)
  ├── fifa:EventType-51  (Penalty missed)
  ├── fifa:EventType-57  (Goal Prevention)
  ├── fifa:EventType-60  (Penalty missed)
  ├── fifa:EventType-65  (Penalty missed)
  ├── fifa:EventType-71  (VAR)
  └── fifa:EventType-72  (Penalty Conceded!)
```

**Use intermediate classes for category-level queries:**
```sparql
?event a fifa:Foul .     # all foul-related events
?event a fifa:Goal .     # all goal events
?event a fifa:SetPiece . # all set pieces
?event a fifa:EventType-18 . # foul only, not cards
```

**WRONG — there is no `fifa:eventType` datatype property:**
```sparql
# ?event fifa:eventType 18 .   ← DO NOT USE
```

### Spatial Properties on `fifa:MatchEvent`

| Property | Range | Description |
|---|---|---|
| `fifa:positionX` | `xsd:decimal` | X coordinate of event on the field |
| `fifa:positionY` | `xsd:decimal` | Y coordinate of event on the field |
| `fifa:goalGatePositionX` | `xsd:decimal` | X coordinate of ball position at goal gate |
| `fifa:goalGatePositionY` | `xsd:decimal` | Y coordinate of ball at the goal line |
| `fifa:goalGatePositionZ` | `xsd:decimal` | Z coordinate (height) of ball at the goal line |

### Other `fifa:MatchEvent` Properties

| Property | Range | Description |
|---|---|---|
| `fifa:typeLabel` | `xsd:string` | Localised human-readable label for the event type |
| `fifa:hasStoppageTime` | `xsd:integer` | Stoppage time minutes added at end of period |
| `fifa:eventMatchMinute` | `xsd:string` | Match minute string (e.g. `"90'+7'"`) |
| `fifa:eventTimestamp` | `xsd:dateTime` | Timestamp at which the event occurred |
| `fifa:eventHomeGoals` | `xsd:integer` | Home-team goal tally at time of event |
| `fifa:eventAwayGoals` | `xsd:integer` | Away-team goal tally at time of event |

### VAR Properties on `fifa:MatchEvent`

These appear on `fifa:EventType-71` (VAR) events:

| Property | Range | Description |
|---|---|---|
| `fifa:varIncident` | `xsd:integer` | VAR incident type code |
| `fifa:varReason` | `xsd:integer` | Reason for VAR review |
| `fifa:varStatus` | `xsd:integer` | Status of VAR review |
| `fifa:varResult` | `xsd:integer` | Outcome of VAR review |
| `fifa:varDecision` | `xsd:integer` | VAR decision outcome (`VarNotificationData/Decision`) |

### EventQualifier — Supplementary Annotations

A `fifa:MatchEvent` can have zero or more `fifa:EventQualifier` nodes attached via `fifa:hasQualifier`. These carry spatial and cross-event data: goalkeeper positions, goalmouth coordinates, blocked shot locations, jersey numbers, injured-player references, and links to related events.

```sparql
?match fifa:hasEvent ?event .
?event fifa:hasQualifier ?q .
?q fifa:qualifierId         ?qid ;
   fifa:qualifierRecordId   ?recId .
OPTIONAL { ?q fifa:pitchZone              ?zone }
OPTIONAL { ?q fifa:gkXCoordinate         ?gkX }
OPTIONAL { ?q fifa:gkYCoordinate         ?gkY }
OPTIONAL { ?q fifa:goalmouthYCoordinate  ?gmY }
OPTIONAL { ?q fifa:goalmouthZCoordinate  ?gmZ }
OPTIONAL { ?q fifa:blockedXCoordinate    ?blkX }
OPTIONAL { ?q fifa:blockedYCoordinate    ?blkY }
OPTIONAL { ?q fifa:jerseyNumbers         ?jerseys }
OPTIONAL { ?q fifa:playerPosition        ?playerPos }
OPTIONAL { ?q fifa:injuredPlayer         ?injPlayer }
OPTIONAL { ?q fifa:relatedEvent          ?relEvt }
OPTIONAL { ?q fifa:oppositeRelatedEvent  ?oppEvt }
OPTIONAL { ?q fifa:secondRelatedEvent    ?secEvt }
```

### `fifa:timelineEvent` — Cross-Reference to Timeline

Links a derived live-match entity (`fifa:Goal`, `fifa:Booking`, `fifa:Substitution`) back to the corresponding raw `fifa:MatchEvent` in the timeline. Use it to join structured live data (typed properties like `fifa:goalMinute`, `fifa:goalType`, `fifa:player`) with the full event-qualifier annotations.

```sparql
?match fifa:hasGoal ?goal .
?goal  fifa:timelineEvent ?event .
?event fifa:hasQualifier ?q .
?q     fifa:goalmouthYCoordinate ?gmY ;
       fifa:goalmouthZCoordinate ?gmZ .
```

---

## Key Property Quick Reference

### Match Scores & Result
```sparql
?match fifa:homeTeamScore ?homeScore ;
       fifa:awayTeamScore ?awayScore ;
       fifa:winner        ?winnerTeam ;
       fifa:resultType    ?resultType .   # 1=normal, 2=AET, 3=penalties
```

### Goal Details
```sparql
?match fifa:hasGoal ?goal .
?goal  rdfs:label        ?goalLabel ;
       fifa:goalMinute   ?minute ;
       fifa:goalPeriod   fifa:MatchPeriod-3 ;
       fifa:goalType     fifa:GoalType-1 ;
       fifa:assistPlayer ?assistingPlayer ;
       fifa:team         ?scoringTeam ;
       fifa:player       ?scorer .
```

### Booking Details
```sparql
?match fifa:hasBooking ?booking .
?booking fifa:bookingCard   fifa:CardType-1 ;
         fifa:bookingMinute ?minute ;
         fifa:bookingPeriod ?period ;
         fifa:bookingReason ?reasonCode ;
         fifa:team          ?bookedTeam ;
         fifa:player        ?bookedPlayer .
OPTIONAL { ?booking fifa:coach  ?coach }   # coach booking (fifa:Coach)
OPTIONAL { ?booking fifa:staff  ?staff }   # staff booking (fifa:Staff)
OPTIONAL { ?booking fifa:timelineEvent ?event }
```

### Substitution Details
```sparql
?match fifa:hasSubstitution ?sub .
?sub  fifa:playerOff          ?outPlayer ;
      fifa:playerOffName      ?outName ;
      fifa:playerOn           ?inPlayer ;
      fifa:playerOnName       ?inName ;
      fifa:substitutionMinute ?minute ;
      fifa:substitutionPeriod ?period ;
      fifa:substitutionReason ?reason .
```

### Player Lineup
```sparql
?match fifa:hasPlayerAppearance ?appearance .
?appearance fifa:player       ?player ;
            fifa:team         ?team ;
            fifa:shirtNumber  ?shirt ;
            fifa:captain      ?isCaptain ;
            fifa:fieldStatus  ?fieldStatus ; # 1=starting, 2=substitute
            fifa:position     ?pos ;
            fifa:lineupX      ?x ;
            fifa:lineupY      ?y .
```

### Player Bio
```sparql
?player rdfs:label          ?name ;
        fifa:playerId       ?id ;
        fifa:birthDate      ?dob ;
        fifa:height         ?height ;
        fifa:weight         ?weight ;
        fifa:jerseyNum      ?jersey ;
        fifa:realPosition   ?realPos ;
        fifa:realPositionSide ?side .
```

### Team & Squad
```sparql
?team rdfs:label           ?teamName ;
      fifa:teamId          ?id ;
      fifa:abbreviation    ?abbr ;
      fifa:hasWorldRanking ?ranking ;
      fifa:hasPlayer       ?player .       # direct → fifa:Player

# Squad membership via inSquad (player → SquadMembership)
?player fifa:inSquad ?squadMembership .
?squadMembership fifa:forTeam     ?team ;
                 fifa:duringSeason ?season .

# Team membership (temporal) via hasTeamMembership (player → TeamMembership)
?player fifa:hasTeamMembership ?membership .
?membership fifa:team          ?team ;
            fifa:duringSeason  ?season ;
            fifa:fromJoinDate  ?joined ;
            fifa:fromLeaveDate ?left .
```

### Weather
```sparql
?match fifa:weather ?weather .
?weather fifa:temperature          ?temp ;
         fifa:humidity             ?humidity ;
         fifa:windSpeed            ?wind ;
         fifa:weatherTypeLocalized ?description .
```

### Ball Possession
```sparql
?match fifa:ballPossession ?poss .
?poss fifa:overallHome ?homePct ;
      fifa:overallAway ?awayPct .
```

### Stadium & Location
```sparql
?match fifa:stadium ?stadium .
?stadium rdfs:label ?stadiumName ;
         fifa:hasRoof ?hasRoof ;
         fifa:city ?city .
?city rdfs:label ?cityName .
OPTIONAL { ?stadium fifa:capacity   ?capacity }
OPTIONAL { ?stadium fifa:latitude   ?lat }
OPTIONAL { ?stadium fifa:longitude  ?lon }
OPTIONAL { ?stadium fifa:length     ?pitchLength }
OPTIONAL { ?stadium fifa:width      ?pitchWidth }
```

---

## Common Query Patterns

### Pattern 1: All Goals in a Match
```sparql
SELECT ?match ?matchLabel ?goalMinute ?periodLabel ?goalTypeLabel ?scorerName ?assistName
WHERE {
  ?match a fifa:Match ;
         rdfs:label ?matchLabel ;
         fifa:hasGoal ?goal .
  ?goal  fifa:goalMinute ?goalMinute ;
         fifa:goalPeriod ?period ;
         fifa:goalType   ?goalType .
  ?period   rdfs:label ?periodLabel .
  ?goalType rdfs:label ?goalTypeLabel .
  OPTIONAL { ?goal rdfs:label ?scorerName }
  OPTIONAL { ?goal fifa:assistPlayer ?assist . ?assist rdfs:label ?assistName }
}
ORDER BY ?goalMinute
```

### Pattern 2: Match Results with Score
```sparql
SELECT ?match ?homeTeamName ?awayTeamName ?homeScore ?awayScore ?winnerName ?date
WHERE {
  ?match a fifa:Match ;
         fifa:homeTeam      ?homeTeam ;
         fifa:awayTeam      ?awayTeam ;
         fifa:homeTeamScore ?homeScore ;
         fifa:awayTeamScore ?awayScore ;
         fifa:date          ?date .
  ?homeTeam rdfs:label ?homeTeamName .
  ?awayTeam rdfs:label ?awayTeamName .
  OPTIONAL { ?match fifa:winner ?winner . ?winner rdfs:label ?winnerName }
}
ORDER BY ?date
```

### Pattern 3: Player Appearances (Starting XI)
```sparql
SELECT ?match ?playerName ?shirtNumber ?posLabel ?isCaptain
WHERE {
  ?match a fifa:Match ;
         fifa:hasPlayerAppearance ?app .
  ?app   fifa:player      ?player ;
         fifa:shirtNumber ?shirtNumber ;
         fifa:fieldStatus 1 ;
         fifa:captain     ?isCaptain .
  ?player rdfs:label ?playerName .
  OPTIONAL { ?player fifa:realPosition ?pos . ?pos rdfs:label ?posLabel }
}
```

### Pattern 4: Yellow/Red Cards by Team
```sparql
SELECT ?team ?teamName (COUNT(?booking) AS ?cards)
WHERE {
  ?match a fifa:Match ;
         fifa:hasBooking ?booking .
  ?booking fifa:bookingCard fifa:CardType-1 ;  # Yellow; CardType-3 for straight red
           fifa:team ?team .
  ?team rdfs:label ?teamName .
}
GROUP BY ?team ?teamName
ORDER BY DESC(?cards)
```

### Pattern 5: Tactics Used Per Match
```sparql
SELECT ?matchLabel ?homeTeamName ?homeTacticLabel ?awayTeamName ?awayTacticLabel
WHERE {
  ?match a fifa:Match ;
         rdfs:label ?matchLabel ;
         fifa:homeTeam ?homeTeam ; fifa:awayTeam ?awayTeam ;
         fifa:homeTeamTactics ?homeTactic ;
         fifa:awayTeamTactics ?awayTactic .
  ?homeTeam rdfs:label ?homeTeamName .
  ?awayTeam rdfs:label ?awayTeamName .
  ?homeTactic rdfs:label ?homeTacticLabel .
  ?awayTactic rdfs:label ?awayTacticLabel .
}
```

### Pattern 6: Team Analytics for a Match
```sparql
SELECT ?match ?matchLabel ?reportLabel
       ?passes ?passesCompleted ?possession
       ?attemptAtGoal ?goals ?xG ?yellowCards
WHERE {
  ?match a fifa:Match ;
         rdfs:label ?matchLabel ;
         fifa:hasTeamAnalyticsReport ?report .
  ?report rdfs:label ?reportLabel .
  OPTIONAL { ?report fifa:passes           ?passes }
  OPTIONAL { ?report fifa:passesCompleted  ?passesCompleted }
  OPTIONAL { ?report fifa:possession       ?possession }
  OPTIONAL { ?report fifa:attemptAtGoal    ?attemptAtGoal }
  OPTIONAL { ?report fifa:goals            ?goals }
  OPTIONAL { ?report fifa:xG              ?xG }
  OPTIONAL { ?report fifa:yellowCards      ?yellowCards }
}
ORDER BY ?matchLabel
```

### Pattern 7: Player Physical Performance
```sparql
SELECT ?matchLabel ?reportLabel
       ?totalDistance ?distanceHighSpeedSprinting ?topSpeed ?sprints ?timePlayed
WHERE {
  ?match a fifa:Match ;
         rdfs:label ?matchLabel ;
         fifa:hasPlayerAnalyticsReport ?report .
  ?report rdfs:label ?reportLabel .
  OPTIONAL { ?report fifa:totalDistance              ?totalDistance }
  OPTIONAL { ?report fifa:distanceHighSpeedSprinting ?distanceHighSpeedSprinting }
  OPTIONAL { ?report fifa:topSpeed                   ?topSpeed }
  OPTIONAL { ?report fifa:sprints                    ?sprints }
  OPTIONAL { ?report fifa:timePlayed                 ?timePlayed }
}
ORDER BY DESC(?totalDistance)
```

### Pattern 8: Top Teams by Pressing Intensity
```sparql
SELECT ?team ?teamName
       (SUM(?highPress) AS ?totalHighPress)
       (SUM(?counterPress) AS ?totalCounterPress)
WHERE {
  ?match a fifa:Match ;
         fifa:hasTeamAnalyticsReport ?report .
  { ?match fifa:homeTeam ?team } UNION { ?match fifa:awayTeam ?team }
  ?team rdfs:label ?teamName .
  OPTIONAL { ?report fifa:phaseAggregateHighPress    ?highPress }
  OPTIONAL { ?report fifa:phaseAggregateCounterPress ?counterPress }
}
GROUP BY ?team ?teamName
ORDER BY DESC(?totalHighPress)
```

### Pattern 9: Linebreak Efficiency by Team
```sparql
SELECT ?team ?teamName
       (SUM(?attempted) AS ?attempted)
       (SUM(?completed) AS ?completed)
WHERE {
  ?match a fifa:Match ;
         fifa:hasTeamAnalyticsReport ?report .
  { ?match fifa:homeTeam ?team } UNION { ?match fifa:awayTeam ?team }
  ?team rdfs:label ?teamName .
  OPTIONAL { ?report fifa:linebreaksAttemptedAllLines ?attempted }
  OPTIONAL { ?report fifa:linebreaksCompletedAllLines ?completed }
}
GROUP BY ?team ?teamName
HAVING (SUM(?attempted) > 0)
ORDER BY DESC(SUM(?completed))
```

### Pattern 10: Match Officials
```sparql
# Direct access via fifa:hasOfficial → fifa:Official
SELECT ?match ?matchLabel ?official ?officialName ?roleCode
WHERE {
  ?match a fifa:Match ;
         rdfs:label ?matchLabel ;
         fifa:hasOfficial ?official .
  ?official rdfs:label ?officialName .
  OPTIONAL { ?official fifa:officialType ?roleCode }
}
ORDER BY ?matchLabel

# With localised role label via OfficialAssignment
SELECT ?match ?matchLabel ?official ?officialName ?roleLabel
WHERE {
  ?match a fifa:Match ;
         rdfs:label ?matchLabel ;
         fifa:hasOfficial ?official .
  ?official rdfs:label ?officialName .
  OPTIONAL {
    ?assignment a fifa:OfficialAssignment ;
                fifa:official ?official ;
                fifa:officialTypeLocalized ?roleLabel .
  }
}
ORDER BY ?matchLabel
```

### Pattern 11: Top Scorers
```sparql
SELECT ?player ?playerName (COUNT(?goal) AS ?goals)
WHERE {
  ?match a fifa:Match ;
         fifa:hasGoal ?goal .
  ?goal fifa:player ?player .
  ?player rdfs:label ?playerName .
  FILTER NOT EXISTS { ?goal a fifa:EventType-34 }  # exclude own goals
}
GROUP BY ?player ?playerName
ORDER BY DESC(?goals)
```

### Pattern 12: Players by Position and Side
```sparql
# All forwards in the tournament
SELECT ?player ?playerName ?teamName ?sideLabel
WHERE {
  ?match a fifa:Match ;
         fifa:hasPlayerAppearance ?app .
  ?app fifa:player ?player ;
       fifa:position fifa:Position-3 .   # or position:3
  OPTIONAL { ?app fifa:realPositionSide ?side . ?side rdfs:label ?sideLabel }
  ?player rdfs:label ?playerName .
  OPTIONAL { ?app fifa:team ?team . ?team rdfs:label ?teamName . }
}
```

### Pattern 13: FIFA World Rankings (PowerRanking graph)
```sparql
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?team ?teamName ?confederation ?rank ?prevRank ?rankingMovement ?totalPoints ?generatedAt
WHERE {
  GRAPH <urn:fifa:powerrankings> {
    ?snapshot a fifa:PowerRanking ;
              fifa:hasTeam ?team ;
              fifa:hasConfederation ?confederation ;
              fifa:rank ?rank ;
              fifa:prevRank ?prevRank ;
              fifa:rankingMovement ?rankingMovement ;
              fifa:totalPoints ?totalPoints ;
              fifa:generatedAt ?generatedAt .
    ?team rdfs:label ?teamName .
    {
      SELECT ?team (MAX(?gen) AS ?generatedAt)
      WHERE {
        GRAPH <urn:fifa:powerrankings> {
          ?r a fifa:PowerRanking ; fifa:hasTeam ?team ; fifa:generatedAt ?gen .
        }
      }
      GROUP BY ?team
    }
  }
}
ORDER BY ?rank
LIMIT 50
```

### Pattern 14: Match Win Probabilities (Inferred)
```sparql
SELECT ?match ?homeTeam ?awayTeam ?homeWinProb ?awayWinProb
WHERE {
  GRAPH <urn:worldcup:kg:2026> {
    ?match a fifa:Match ;
           fifa:homeTeam ?homeTeamRes ;
           fifa:awayTeam ?awayTeamRes .
    OPTIONAL { ?match fifa:homeTeamWinProbabilityByFifaRank ?homeWinProb }
    OPTIONAL { ?match fifa:awayTeamWinProbabilityByFifaRank ?awayWinProb }
    ?homeTeamRes rdfs:label ?homeTeam .
    ?awayTeamRes rdfs:label ?awayTeam .
  }
}
ORDER BY ?match
```

### Pattern 15: xG and Threat Comparison
```sparql
SELECT ?match ?matchLabel ?team ?teamName ?xG ?threat ?pitchControl ?finalThirdPitchControl
WHERE {
  GRAPH <urn:worldcup:kg:2026:analytics> {
    ?report a fifa:TeamMatchAnalyticsReport ;
            fifa:match ?match ;
            fifa:team ?team ;
            fifa:generatedAt ?generatedAt .
    OPTIONAL { ?report fifa:xG ?xG }
    OPTIONAL { ?report fifa:threat ?threat }
    OPTIONAL { ?report fifa:pitchControl ?pitchControl }
    OPTIONAL { ?report fifa:finalThirdPitchControl ?finalThirdPitchControl }
    {
      SELECT ?match ?team (MAX(?gen) AS ?generatedAt)
      WHERE {
        GRAPH <urn:worldcup:kg:2026:analytics> {
          ?r a fifa:TeamMatchAnalyticsReport ;
             fifa:match ?match ; fifa:team ?team ; fifa:generatedAt ?gen .
        }
      }
      GROUP BY ?match ?team
    }
  }
  GRAPH <urn:worldcup:kg:2026> {
    ?match rdfs:label ?matchLabel .
    ?team rdfs:label ?teamName .
  }
}
ORDER BY ?match
```

---

## Query Best Practices

1. **Prefer analytics reports over raw events for aggregate stats** — when a metric exists in `fifa:PlayerMatchAnalyticsReport` or `fifa:TeamMatchAnalyticsReport` (goals, passes, distance, possession, xG, etc.), always use it via `fifa:hasPlayerAnalyticsReport` / `fifa:hasTeamAnalyticsReport` rather than counting raw event nodes. Counting raw `fifa:Goal` events can produce incorrect aggregates; the analytics reports are the authoritative pre-aggregated source of truth.

   **Use analytics (correct):**
   ```sparql
   ?match fifa:hasPlayerAnalyticsReport ?report .
   ?report fifa:player ?player ;
           fifa:goals  ?goalsInMatch .
   ```
   **Avoid for aggregates (can produce wrong totals):**
   ```sparql
   ?match fifa:hasGoal ?goal .
   ?goal fifa:player ?player .   # ← raw event count, unreliable for aggregates
   ```

2. **Always use `rdfs:label` for human-readable names** — teams, players, stadiums, cities, periods, goal types, card types all have labels.
3. **Always SELECT both the URI and the label** — include the subject URI variable alongside its `rdfs:label`. The URI is a stable identifier for follow-up queries.
4. **Use `OPTIONAL` for nullable fields** — weather, possession, tactics, winner, and every analytics metric.
5. **Always use instance URIs, never raw integers for typed values** — `fifa:goalType`, `fifa:bookingCard`, `fifa:goalPeriod`, and event types all use instance URIs. There is **no** `fifa:eventType` datatype property; filter by `?event a fifa:EventType-N .`
6. **The player in a Goal/Booking** is declared via `fifa:player`. A `rdfs:label` on the event node may carry the name as a fallback.
7. **Squad and team membership navigation**: `fifa:hasPlayer` on `fifa:Team` points **directly to `fifa:Player`**. To navigate squad membership use `fifa:inSquad` on the player (→ `fifa:SquadMembership`) with `fifa:forTeam` and `fifa:duringSeason`. For temporal club membership use `fifa:hasTeamMembership` (→ `fifa:TeamMembership`).
8. **Match-centric traversal**: Start from `?match a fifa:Match` and follow `fifa:has*` outward.
9. **Aggregate queries**: Always include the URI in `GROUP BY` alongside the label.
10. **Analytics reports use `OPTIONAL` for every metric** — not every report will have every metric populated.
11. **`fifa:AnalyticsMetricProperty` as discovery tool** — query `?p rdf:type fifa:AnalyticsMetricProperty` to enumerate available analytics predicates dynamically.
12. **`fifa:team` and `fifa:player` are multi-domain** — usable directly on `fifa:Goal`, `fifa:Booking`, `fifa:PlayerMatchAppearance`, `fifa:CoachAssignment`, `fifa:TeamMatchAnalyticsReport`, and `fifa:PlayerMatchAnalyticsReport`.
13. **`fifa:Official` vs `fifa:OfficialAssignment` vs `fifa:OfficialType`**:
    - `fifa:Official` = the **person**. Has `rdfs:label`, `fifa:officialType` (integer), `fifa:idCountry`.
    - `fifa:OfficialAssignment` = the **assignment record**. Has `fifa:official`, `fifa:officialType` (integer), `fifa:officialTypeLocalized` (human-readable, e.g. `"Referee"`).
    - `fifa:OfficialType` = the **role taxonomy class**. Instances have `rdfs:label` values like "Referee", "Assistant VAR".
    - `fifa:hasOfficial` links to the **person node**. `fifa:hasOfficialAssignment` links to the **assignment record**.
14. **`fifa:position` on `fifa:PlayerMatchAppearance`** — the position assigned for a specific match appearance; no need to go through the player node.
15. **EventQualifier for spatial detail** — navigate from `?event fifa:hasQualifier ?q` for goalkeeper position, goalmouth coordinates, pitch zone, or blocked-shot location. Use `OPTIONAL` for every qualifier property.
16. **`fifa:timelineEvent` bridges live entities and the timeline** — follow `?liveEntity fifa:timelineEvent ?event` to reach the `fifa:MatchEvent` with full qualifier annotations and VAR data.
17. **Provider identifiers** — matches carry `fifa:matchId`, `fifa:idIfes` (IFES), and `fifa:idStatsPerform` (Stats Perform/Opta). Use `fifa:idIfes` when querying the analytics endpoint.
18. **PowerRanking graph isolation** — `urn:fifa:powerrankings` is self-contained. Always use `GRAPH <urn:fifa:powerrankings>` when querying it; otherwise team stubs in that graph may collide with full team nodes in the main graph.
19. **Use preferred event classes** — `fifa:Goal`, `fifa:Booking`, `fifa:Substitution` are the preferred classes for events; the `owl:equivalentClass` EventType coded variants (EventType-0, EventType-2, EventType-5) will eventually be superseded.

---

## Reference Files

For deep property listings, see:
- `references/properties.md` — complete property table with domains, ranges, and data types
- `references/coded-values.md` — expanded coded value tables with usage examples

Read these only when you need exhaustive detail beyond what the SKILL.md tables cover.
