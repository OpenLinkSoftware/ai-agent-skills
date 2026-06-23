# FIFA Ontology — Complete Property Reference

## Table of Contents
1. [Match Properties](#match-properties)
2. [Team Properties](#team-properties)
3. [Player Properties](#player-properties)
4. [Goal Properties](#goal-properties)
5. [Booking Properties](#booking-properties)
6. [Substitution Properties](#substitution-properties)
7. [PlayerMatchAppearance Properties](#playermatchappearance-properties)
8. [MatchEvent Properties](#matchevent-properties)
9. [EventQualifier Properties](#eventqualifier-properties)
10. [Stadium & City Properties](#stadium--city-properties)
11. [Weather Properties](#weather-properties)
12. [BallPossession Properties](#ballpossession-properties)
13. [SquadMembership & TeamMembership](#squadmembership--teammembership)
14. [WorldRanking Properties](#worldranking-properties)
15. [Official, OfficialAssignment & OfficialType](#official-officialassignment--officialtype)
16. [CoachAssignment Properties](#coachassignment-properties)
17. [Country Properties](#country-properties)
18. [PowerRanking Properties](#powerranking-properties)
19. [Analytics Report Properties](#analytics-report-properties)

---

## Match Properties

| Property | Type | Range | Notes |
|---|---|---|---|
| `fifa:matchId` | Datatype | `xsd:integer` | Internal ID |
| `fifa:matchNumber` | Datatype | `xsd:integer` | Sequential number |
| `fifa:matchDay` | Datatype | `xsd:integer` | Day within group stage |
| `fifa:matchStatus` | Datatype | `xsd:integer` | Status code |
| `fifa:matchTime` | Datatype | `xsd:string` | Local kick-off time string |
| `fifa:date` | Datatype | `xsd:dateTime` | UTC datetime |
| `fifa:localDate` | Datatype | `xsd:dateTime` | Local datetime |
| `fifa:attendance` | Datatype | `xsd:integer` | Stadium attendance |
| `fifa:homeTeam` | Object | `fifa:Team` | Home team |
| `fifa:awayTeam` | Object | `fifa:Team` | Away team |
| `fifa:homeTeamScore` | Datatype | `xsd:integer` | FT home goals |
| `fifa:awayTeamScore` | Datatype | `xsd:integer` | FT away goals |
| `fifa:homeTeamPenaltyScore` | Datatype | `xsd:integer` | Penalty shootout home |
| `fifa:awayTeamPenaltyScore` | Datatype | `xsd:integer` | Penalty shootout away |
| `fifa:aggregateHomeTeamScore` | Datatype | `xsd:integer` | Two-leg aggregate |
| `fifa:aggregateAwayTeamScore` | Datatype | `xsd:integer` | Two-leg aggregate |
| `fifa:winner` | Object | `fifa:Team` | Winning team (absent for draws) |
| `fifa:resultType` | Datatype | `xsd:integer` | 1=normal FT, 2=AET, 3=penalties |
| `fifa:homeTeamTactics` | Object | `fifa:Tactic` | Home formation |
| `fifa:awayTeamTactics` | Object | `fifa:Tactic` | Away formation |
| `fifa:stadium` | Object | `fifa:Stadium` | Venue |
| `fifa:stage` | Object | `fifa:Stage` | Tournament stage |
| `fifa:season` | Object | `fifa:Season` | Edition/year |
| `fifa:competition` | Object | `fifa:Competition` | Parent competition |
| `fifa:group` | Object | `fifa:Group` | Group (if group stage) |
| `fifa:weather` | Object | `fifa:Weather` | Conditions |
| `fifa:ballPossession` | Object | `fifa:BallPossession` | Possession stats |
| `fifa:hasGoal` | Object | `fifa:Goal` | Each goal (multi-valued) |
| `fifa:hasBooking` | Object | `fifa:Booking` | Each booking (multi-valued) |
| `fifa:hasSubstitution` | Object | `fifa:Substitution` | Each sub (multi-valued) |
| `fifa:hasPlayerAppearance` | Object | `fifa:PlayerMatchAppearance` | Lineup entries |
| `fifa:hasCoach` | Object | `fifa:CoachAssignment` | Coach links |
| `fifa:hasStaffAssignment` | Object | `fifa:StaffAssignment` | Staff links |
| `fifa:hasOfficial` | Object | `fifa:Official` | Referee/official links (links to the Official person node directly) |
| `fifa:hasOfficialAssignment` | Object | `fifa:OfficialAssignment` | Official assignment records (has localised role label) |
| `fifa:hasHeadToHeadAnalysis` | Object | `fifa:HeadToHeadAnalysis` | H2H reports (two per match, one per team) |
| `fifa:hasNewsArticle` | Object | `schema:NewsArticle` | FIFA Plus news articles covering the match |
| `fifa:hasEvent` | Object | `fifa:MatchEvent` | Timeline events |
| `fifa:idIfes` | Datatype | `xsd:string` | IFES system ID |
| `fifa:idStatsPerform` | Datatype | `xsd:string` | Stats Perform / Opta ID (from `Properties.IdStatsPerform`) |
| `fifa:leg` | Datatype | `xsd:integer` | Leg number (two-legged ties) |
| `fifa:isHomeMatch` | Datatype | `xsd:boolean` | Neutral venue flag |
| `fifa:officialityStatus` | Datatype | `xsd:integer` | Officiality code |
| `fifa:timeDefined` | Datatype | `xsd:boolean` | Whether kick-off time is confirmed |
| `fifa:matchReportUrl` | Datatype | `xsd:anyURI` | Link to match report |
| `fifa:lastPeriodUpdate` | Datatype | `xsd:string` | Last status update string |
| `fifa:placeHolderA` | Datatype | `xsd:string` | TBD team slot A |
| `fifa:placeHolderB` | Datatype | `xsd:string` | TBD team slot B |
| `fifa:homeTeamWinProbabilityByFifaRank` | Datatype | `xsd:decimal` | Inferred home-team win probability (Elo logistic from FIFA ranking points) |
| `fifa:awayTeamWinProbabilityByFifaRank` | Datatype | `xsd:decimal` | Inferred away-team win probability |
| `fifa:homeTeamLossProbabilityByFifaRank` | Datatype | `xsd:decimal` | Inferred home-team loss probability |
| `fifa:awayTeamLossProbabilityByFifaRank` | Datatype | `xsd:decimal` | Inferred away-team loss probability |
| `prov:wasDerivedFrom` | Object | `xsd:anyURI` | FIFA API URL this resource was derived from (W3C PROV-O) |

---

## Team Properties

| Property | Type | Range | Notes |
|---|---|---|---|
| `rdfs:label` | Datatype | `xsd:string` | Full team name |
| `fifa:teamId` | Datatype | `xsd:integer` | Internal ID |
| `fifa:abbreviation` | Datatype | `xsd:string` | 3-letter code (e.g. BRA) |
| `fifa:shortName` | Datatype | `xsd:string` | Short display name |
| `fifa:teamType` | Datatype | `xsd:integer` | Type code |
| `fifa:footballType` | Datatype | `xsd:integer` | Football type code |
| `fifa:idAssociation` | Datatype | `xsd:string` | Association/confederation ID |
| `fifa:idCountry` | Object | — | Country entity |
| `fifa:inConfederation` | Object | — | Confederation entity |
| `fifa:hasWorldRanking` | Object | `fifa:WorldRanking` | Ranking node(s) |
| `fifa:hasPlayer` | Object | `fifa:Player` | Direct player links |
| `fifa:foundationYear` | Datatype | `xsd:integer` | Year founded |

---

## Player Properties

| Property | Type | Range | Notes |
|---|---|---|---|
| `rdfs:label` | Datatype | `xsd:string` | Full player name |
| `fifa:playerId` | Datatype | `xsd:integer` | Internal ID |
| `fifa:jerseyNum` | Datatype | `xsd:integer` | Squad jersey number |
| `fifa:birthDate` | Datatype | `xsd:dateTime` | Date of birth |
| `fifa:height` | Datatype | `xsd:decimal` | Height in cm |
| `fifa:weight` | Datatype | `xsd:decimal` | Weight in kg |
| `fifa:gender` | Datatype | `xsd:integer` | Gender code |
| `fifa:position` | Object | `fifa:Position` | Registered position |
| `fifa:realPosition` | Object | `fifa:Position` | Actual playing position |
| `fifa:realPositionSide` | Object | `fifa:PositionSide` | Side of field |
| `fifa:shortClubName` | Datatype | `xsd:string` | Club affiliation |
| `fifa:specialStatus` | Datatype | `xsd:integer` | Special status code |
| `fifa:activeStatus` | Datatype | `xsd:integer` | Active/retired |
| `fifa:ageType` | Datatype | `xsd:integer` | Age category code |
| `fifa:pictureUrl` | Datatype | `xsd:anyURI` | Headshot URL |
| `fifa:playerPictureUrl` | Datatype | `xsd:anyURI` | Alternative picture URL |
| `fifa:alias` | Datatype | `xsd:string` | Known alias/nickname |
| `fifa:idCountry` | Object | — | Nationality |
| `fifa:playsForTeam` | Object | `fifa:TeamMembership` | Team membership records |

---

## Goal Properties

| Property | Type | Range | Notes |
|---|---|---|---|
| `rdfs:label` | Datatype | `xsd:string` | Typically scorer's name |
| `fifa:goalMinute` | Datatype | `xsd:integer` | Minute scored |
| `fifa:goalType` | Object | `fifa:GoalType` | Regular / Penalty / Own Goal |
| `fifa:goalPeriod` | Object | `fifa:MatchPeriod` | Which period |
| `fifa:assistPlayer` | Object | `fifa:Player` | Assisting player (optional) |
| `fifa:player` | Object | `fifa:Player` | Scoring player (check both this and rdfs:label) |
| `fifa:team` | Object | `fifa:Team` | Scoring team |
| `fifa:timelineEvent` | Object | `fifa:MatchEvent` | Corresponding raw timeline event (for qualifier/VAR detail) |

---

## Booking Properties

| Property | Type | Range | Notes |
|---|---|---|---|
| `fifa:bookingCard` | Object | `fifa:CardType` | Yellow/Second Yellow/Red |
| `fifa:bookingMinute` | Datatype | `xsd:integer` | Minute of booking |
| `fifa:bookingPeriod` | Object | `fifa:MatchPeriod` | Period of booking |
| `fifa:bookingReason` | Datatype | `rdfs:Literal` | Reason text/code |
| `fifa:player` | Object | `fifa:Player` | Booked player |
| `fifa:team` | Object | `fifa:Team` | Team of booked player |
| `fifa:staff` | Object | — | Booked staff member (optional) |
| `fifa:timelineEvent` | Object | `fifa:MatchEvent` | Corresponding raw timeline event |

---

## Substitution Properties

| Property | Type | Range | Notes |
|---|---|---|---|
| `fifa:playerOff` | Object | `fifa:Player` | Player leaving |
| `fifa:playerOffName` | Datatype | `xsd:string` | Name string (denormalized) |
| `fifa:playerOn` | Object | `fifa:Player` | Player entering |
| `fifa:playerOnName` | Datatype | `xsd:string` | Name string (denormalized) |
| `fifa:substitutionMinute` | Datatype | `xsd:integer` | Minute of sub |
| `fifa:substitutionPeriod` | Object | `fifa:MatchPeriod` | Period |
| `fifa:substitutionReason` | Datatype | `rdfs:Literal` | Reason text/code |
| `fifa:substitutePosition` | Datatype | `xsd:integer` | Position code |
| `fifa:team` | Object | `fifa:Team` | Team making the substitution |
| `fifa:timelineEvent` | Object | `fifa:MatchEvent` | Corresponding raw timeline event |

---

## PlayerMatchAppearance Properties

| Property | Type | Range | Notes |
|---|---|---|---|
| `fifa:player` | Object | `fifa:Player` | The player |
| `fifa:shirtNumber` | Datatype | `xsd:integer` | Match shirt number |
| `fifa:captain` | Datatype | `xsd:boolean` | Captain flag |
| `fifa:fieldStatus` | Datatype | `xsd:integer` | 1=starting XI, 2=substitute |
| `fifa:playerStatus` | Datatype | `xsd:integer` | Status code |
| `fifa:position` | Object | `fifa:Position` | Position in this match |
| `fifa:realPosition` | Object | `fifa:Position` | Actual position played |
| `fifa:realPositionSide` | Object | `fifa:PositionSide` | Side |
| `fifa:lineupX` | Datatype | `xsd:decimal` | Formation X coordinate |
| `fifa:lineupY` | Datatype | `xsd:decimal` | Formation Y coordinate |

---

## MatchEvent Subclasses

Three intermediate subclasses of `fifa:MatchEvent` group related event types:

| Class | URI | Subclass of | Members |
|---|---|---|---|
| Goal | `fifa:Goal` | `fifa:MatchEvent` | EventType-34, -39, -41 |
| Foul | `fifa:Foul` | `fifa:MatchEvent` | EventType-2, -3, -4, -18 |
| Set Piece | `fifa:SetPiece` | `fifa:MatchEvent` | EventType-14, -16, -24 |

Use these for category-level queries: `?event a fifa:Foul .` matches all foul and card events without needing `VALUES`.

## MatchEvent Properties

> **Event typing**: Events are typed as individuals via `rdf:type`, not via a datatype property. Use `?event a fifa:EventType-18 .` to filter by specific type, or `?event a fifa:Foul .` for the broader category. There is no `fifa:eventType` datatype property.

| Property | Type | Range | Notes |
|---|---|---|---|
| `rdf:type` | — | `fifa:EventType-N` or subclass | **Primary filter** — e.g. `a fifa:EventType-18`, `a fifa:Foul`, `a fifa:Goal` |
| `fifa:eventId` | Datatype | `xsd:string` | Unique event ID |
| `fifa:eventDescription` | Datatype | `xsd:string` | Description text |
| `fifa:eventTimestamp` | Datatype | `xsd:dateTime` | Wall-clock time |
| `fifa:eventMatchMinute` | Datatype | `xsd:string` | Display minute (e.g. "45+2") |
| `fifa:eventPeriod` | Object | `fifa:MatchPeriod` | Period |
| `fifa:eventTeam` | Object | `fifa:Team` | Team associated |
| `fifa:eventPlayer` | Object | `fifa:Player` | Primary player (e.g. fouler, scorer) |
| `fifa:eventSubPlayer` | Object | `fifa:Player` | Secondary player (e.g. fouled player, subbed-on) |
| `fifa:eventSubTeam` | Object | `fifa:Team` | Secondary team |
| `fifa:eventHomeGoals` | Datatype | `xsd:integer` | Running home score at event |
| `fifa:eventAwayGoals` | Datatype | `xsd:integer` | Running away score at event |
| `fifa:eventHomePenaltyGoals` | Datatype | `xsd:integer` | Running penalty score (home) |
| `fifa:eventAwayPenaltyGoals` | Datatype | `xsd:integer` | Running penalty score (away) |
| `fifa:positionX` | Datatype | `xsd:decimal` | X coordinate of event location on the field |
| `fifa:positionY` | Datatype | `xsd:decimal` | Y coordinate of event location on the field |
| `fifa:goalGatePositionY` | Datatype | `xsd:decimal` | Y coordinate of ball at goal line (goal events) |
| `fifa:goalGatePositionZ` | Datatype | `xsd:decimal` | Z coordinate (height) of ball at goal line (goal events) |
| `fifa:varIncident` | Datatype | `xsd:integer` | VAR incident type code |
| `fifa:varReason` | Datatype | `xsd:integer` | Reason for VAR review |
| `fifa:varStatus` | Datatype | `xsd:integer` | Status of VAR review |
| `fifa:varResult` | Datatype | `xsd:integer` | Outcome of VAR review |
| `fifa:hasQualifier` | Object | `fifa:EventQualifier` | Supplementary qualifier annotation(s) on an event |

---

## EventQualifier Properties

`fifa:EventQualifier` nodes are attached to `fifa:MatchEvent` via `fifa:hasQualifier`. A single event can have multiple qualifiers. Each qualifier carries one or more of the following:

| Property | Type | Range | Notes |
|---|---|---|---|
| `fifa:qualifierId` | Datatype | `xsd:integer` | Qualifier type code |
| `fifa:qualifierRecordId` | Datatype | `xsd:string` | Unique qualifier record ID |
| `fifa:pitchZone` | Datatype | `xsd:integer` | Pitch zone where event occurred |
| `fifa:gkXCoordinate` | Datatype | `xsd:decimal` | Goalkeeper X position |
| `fifa:gkYCoordinate` | Datatype | `xsd:decimal` | Goalkeeper Y position |
| `fifa:goalmouthYCoordinate` | Datatype | `xsd:decimal` | Ball Y coordinate at goalmouth |
| `fifa:goalmouthZCoordinate` | Datatype | `xsd:decimal` | Ball Z (height) at goalmouth |
| `fifa:blockedXCoordinate` | Datatype | `xsd:decimal` | X position of blocked shot |
| `fifa:blockedYCoordinate` | Datatype | `xsd:decimal` | Y position of blocked shot |
| `fifa:jerseyNumbers` | Datatype | `xsd:string` | Jersey numbers involved in the qualifier |
| `fifa:playerPosition` | Datatype | `xsd:integer` | Player position code in qualifier context |
| `fifa:injuredPlayer` | Object | `fifa:Player` | Injured player (injury qualifiers) |
| `fifa:relatedEvent` | Object | `fifa:MatchEvent` | Primary related event |
| `fifa:oppositeRelatedEvent` | Object | `fifa:MatchEvent` | Opposing related event |
| `fifa:secondRelatedEvent` | Object | `fifa:MatchEvent` | Secondary related event |

---

## Stadium & City Properties

### Stadium
| Property | Type | Range | Notes |
|---|---|---|---|
| `rdfs:label` | Datatype | `xsd:string` | Stadium name |
| `fifa:stadiumId` | Datatype | `xsd:integer` | Internal ID |
| `fifa:hasRoof` | Datatype | `xsd:boolean` | Covered stadium |
| `fifa:city` | Object | `fifa:City` | Host city |
| `fifa:latitude` | Datatype | `xsd:decimal` | Geo coordinate |
| `fifa:longitude` | Datatype | `xsd:decimal` | Geo coordinate |
| `fifa:length` | Datatype | `xsd:decimal` | Pitch length (m) |
| `fifa:width` | Datatype | `xsd:decimal` | Pitch width (m) |
| `fifa:postalCode` | Datatype | `xsd:string` | Postal code |
| `fifa:street` | Datatype | `xsd:string` | Street address |
| `fifa:foundationYear` | Datatype | `xsd:integer` | Year built |

### City
| Property | Type | Range | Notes |
|---|---|---|---|
| `rdfs:label` | Datatype | `xsd:string` | City name |
| `fifa:cityId` | Datatype | `xsd:integer` | Internal ID |
| `fifa:idCountry` | Object | — | Country |
| `fifa:latitude` | Datatype | `xsd:decimal` | Geo coordinate |
| `fifa:longitude` | Datatype | `xsd:decimal` | Geo coordinate |

---

## Weather Properties

| Property | Type | Range | Notes |
|---|---|---|---|
| `fifa:temperature` | Datatype | `xsd:string` | Temperature string (includes unit) |
| `fifa:humidity` | Datatype | `xsd:string` | Humidity string |
| `fifa:windSpeed` | Datatype | `xsd:string` | Wind speed string |
| `fifa:weatherType` | Datatype | `xsd:integer` | Weather condition code |
| `fifa:weatherTypeLocalized` | Datatype | `xsd:string` | Human-readable condition |

---

## BallPossession Properties

| Property | Type | Range | Notes |
|---|---|---|---|
| `fifa:overallHome` | Datatype | `xsd:decimal` | Home possession % |
| `fifa:overallAway` | Datatype | `xsd:decimal` | Away possession % |

---

## SquadMembership & TeamMembership

### SquadMembership (Player → Team via Season)
`fifa:hasPlayer` on `fifa:Team` links **directly to `fifa:Player`**. To navigate squad memberships (with season context), use `fifa:inSquad` on the player:

Access via: `?player fifa:inSquad ?sm . ?sm fifa:forTeam ?team ; fifa:duringSeason ?season .`

| Property | Type | Range |
|---|---|---|
| `fifa:forTeam` | Object | `fifa:Team` |
| `fifa:duringSeason` | Object | `fifa:Season` |

### TeamMembership (Player → Team with dates)
Access via: `?player fifa:playsForTeam ?tm . ?tm fifa:team ?team .`

| Property | Type | Range |
|---|---|---|
| `fifa:team` | Object | `fifa:Team` |
| `fifa:fromJoinDate` | Datatype | `xsd:dateTime` |
| `fifa:fromLeaveDate` | Datatype | `xsd:dateTime` |

---

## WorldRanking Properties

| Property | Type | Range | Notes |
|---|---|---|---|
| `fifa:rankingValue` | Datatype | `xsd:integer` | Numeric rank |
| `fifa:asOfDatetime` | Datatype | `xsd:dateTime` | Snapshot date |

Access via: `?team fifa:hasWorldRanking ?wr . ?wr fifa:rankingValue ?rank ; fifa:asOfDatetime ?rankDate .`

---

## Official, OfficialAssignment & OfficialType

### Class overview

| Class | URI | Notes |
|---|---|---|
| `fifa:Official` | Person | The referee or assistant — has `rdfs:label` (name), `fifa:officialType`, `fifa:idCountry` |
| `fifa:OfficialAssignment` | Assignment record | The official ↔ match link — has `fifa:officialTypeLocalized` role string |
| `fifa:OfficialType` | Role taxonomy | Named class for official role types (e.g. Referee, Fourth official, VAR) |

> **Key pattern**: `fifa:hasOfficial` on `fifa:Match` links **directly to `fifa:Official`** (the person node). To reach the assignment record and its localised role label, navigate via `fifa:OfficialAssignment` using `fifa:official` → `fifa:Official`.

### fifa:Official Properties

| Property | Type | Range | Notes |
|---|---|---|---|
| `rdfs:label` | Datatype | `xsd:string` | Official's full name |
| `fifa:officialType` | Datatype | `xsd:integer` | Role code (integer) |
| `fifa:idCountry` | Object | `fifa:Country` | Nationality |

### fifa:OfficialAssignment Properties

| Property | Type | Range | Notes |
|---|---|---|---|
| `fifa:official` | Object | `fifa:Official` | The official person |
| `fifa:officialType` | Datatype | `xsd:integer` | Role code |
| `fifa:officialTypeLocalized` | Datatype | `xsd:string` | Human-readable role (e.g. "Referee", "Fourth official", "Video Assistant Referee") |
| `fifa:idCountry` | Object | `fifa:Country` | Official's nationality (may be on Official node directly) |

### fifa:OfficialType Properties

`fifa:OfficialType` is a named class for the role taxonomy. Its instances carry `rdfs:label` with values such as "Referee", "Assistant Referee", "Fourth official", "Video Assistant Referee". Query to discover all role types:

```sparql
SELECT ?type ?label WHERE {
  ?type a fifa:OfficialType ;
        rdfs:label ?label .
} ORDER BY ?label
```

### Access patterns

```sparql
# All officials for a match (direct from hasOfficial)
SELECT ?matchLabel ?officialName ?roleCode WHERE {
  ?match a fifa:Match ;
         rdfs:label ?matchLabel ;
         fifa:hasOfficial ?official .
  ?official rdfs:label ?officialName .
  OPTIONAL { ?official fifa:officialType ?roleCode }
}

# Using OfficialAssignment to get localised role label
SELECT ?matchLabel ?officialName ?roleLabel WHERE {
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
```

---

## CoachAssignment Properties

| Property | Type | Range | Notes |
|---|---|---|---|
| `fifa:coach` | Object | `fifa:Coach` | The coach |
| `fifa:coachRole` | Datatype | `xsd:integer` | Role code (head coach, assistant, etc.) |
| `fifa:team` | Object | `fifa:Team` | Which team side |

Access via: `?match fifa:hasCoach ?ca . ?ca fifa:coach ?coach ; fifa:team ?team .`

---

## Country Properties

`fifa:Country` is a named class used for team nationality, player nationality, official nationality, city country, and stadium country. Instances are identified by football association codes.

| Property | Type | Range | Notes |
|---|---|---|---|
| `rdfs:label` | Datatype | `xsd:string` | Country name |
| `fifa:idCountry` | Datatype | `xsd:string` | Association code (e.g. "BRA", "FRA") |

Access via: `?player fifa:idCountry ?country . ?country rdfs:label ?countryName .`

Also used on: `fifa:Team`, `fifa:Official`, `fifa:Stadium`, `fifa:City`, `fifa:OfficialAssignment`.

---

## PowerRanking Properties

Lives in **`urn:fifa:powerrankings`**. IRI pattern: `fifa-kg:powerranking-{teamId}-{genTs}`.

A new snapshot is written **only when a team's rated-match count or rank changes**.

| Property | Type | Range | Notes |
|---|---|---|---|
| `fifa:hasTeam` | Object | `fifa:Team` | The ranked team |
| `fifa:hasConfederation` | Object | `fifa:Confederation` | The team's confederation |
| `fifa:gender` | Object | `fifa:Gender` | `fifa:Male` or `fifa:Female` |
| `fifa:rank` | Datatype | `xsd:integer` | Ranking position in this snapshot |
| `fifa:prevRank` | Datatype | `xsd:integer` | Ranking position in the previous edition |
| `fifa:rankingMovement` | Datatype | `xsd:integer` | Net change (positive = moved up) |
| `fifa:ratedMatches` | Datatype | `xsd:integer` | Matches counted toward the ranking |
| `fifa:totalPoints` | Datatype | `xsd:decimal` | Ranking points total |
| `fifa:prevPoints` | Datatype | `xsd:decimal` | Previous ranking points |
| `fifa:generatedAt` | Datatype | `xsd:dateTime` | Ingestion timestamp |

Use `MAX(fifa:generatedAt)` to get the latest snapshot per team.

---

## Analytics Report Properties

All `fifa:TeamMatchAnalyticsReport` and `fifa:PlayerMatchAnalyticsReport` resources live in **`urn:worldcup:kg:2026:analytics`**.

### Core Links

| Property | Type | Range | Notes |
|---|---|---|---|
| `fifa:match` | Object | `fifa:Match` | The match this report covers |
| `fifa:team` | Object | `fifa:Team` | The team (TeamMatchAnalyticsReport) |
| `fifa:player` | Object | `fifa:Player` | The player (PlayerMatchAnalyticsReport) |
| `fifa:generatedAt` | Datatype | `xsd:dateTime` | Snapshot timestamp; use MAX() for latest |

### New Analytics Metrics (added 2026)

All are `rdf:type fifa:AnalyticsMetricProperty`, domain `fifa:MatchAnalyticsReport`, range `xsd:decimal`.

| Property | Description |
|---|---|
| `fifa:xG` | Expected goals — probability-weighted sum of chances |
| `fifa:threat` | FIFA Expected Threat (xT) — danger generated by on-ball actions |
| `fifa:pitchControl` | Overall share of pitch modelled as controlled |
| `fifa:finalThirdPitchControl` | Pitch control share in the attacking final third |
| `fifa:matchesPlayed` | Number of matches the report covers |
| `fifa:cleanSheets` | Matches without conceding |
| `fifa:ballRecoveryTime` | Avg time to recover ball after losing possession |
| `fifa:numberOfInvolvements` | Touches/actions in possession sequences |
| `fifa:numberOfPossessionSequences` | Total distinct possession sequences |
| `fifa:numberOfShotEndingSequences` | Possession sequences ending with a shot |
| `fifa:goalkeeperSaves` | Total saves by goalkeeper |
| `fifa:goalkeeperSavesOnTarget` | Saves against on-target attempts |
| `fifa:goalkeeperSavePercentage` | % of on-target attempts saved |
| `fifa:directRedCards` | Straight red cards (not from second caution) |
| `fifa:indirectRedCards` | Red cards from second yellow |
| `fifa:attemptAtGoalAgainstOnTarget` | Opponent shots on target |
| `fifa:attemptAtGoalFromBallProgression` | Shots from ball progressions |
| `fifa:attemptAtGoalFromCorner` | Shots from corners |
| `fifa:attemptAtGoalFromCross` | Shots from crosses |
| `fifa:attemptAtGoalFromPass` | Shots from passes |
| `fifa:attemptAtGoalFromPenalty` | Shots as penalty kicks |
| `fifa:attemptAtGoalFromRebound` | Shots from rebounds |
| `fifa:attemptAtGoalFromOther` | Shots from other / uncategorised play |
| `fifa:linebreaksAttemptedAttackingLineOnly` | Linebreaks vs. attacking line only |
| `fifa:linebreaksAttemptedAttackingLineCompletedOnly` | Completed linebreaks vs. attacking line only |
| `fifa:linebreaksAttemptedMidfieldLineOnly` | Linebreaks vs. midfield line only |
| `fifa:linebreaksAttemptedMidfieldLineCompletedOnly` | Completed linebreaks vs. midfield line only |
| `fifa:linebreaksAttemptedDefensiveLineOnly` | Linebreaks vs. defensive line only |
| `fifa:linebreaksAttemptedDefensiveLineCompletedOnly` | Completed linebreaks vs. defensive line only |
