# FIFA Ontology — Coded Values & Extended Query Examples

## Table of Contents
1. [All Coded Values Summary](#all-coded-values-summary)
2. [Query Examples by Use Case](#query-examples-by-use-case)

---

## All Coded Values Summary

### Card Types
Used with: `fifa:bookingCard` on `fifa:Booking`

```sparql
# Yellow cards only
?booking fifa:bookingCard fifa:CardType-1 .

# Red cards (straight)
?booking fifa:bookingCard fifa:CardType-3 .

# Second yellow (also results in red)
?booking fifa:bookingCard fifa:CardType-2 .
```

### Goal Types
Used with: `fifa:goalType` on `fifa:Goal`

```sparql
# Penalty goals
?goal fifa:goalType fifa:GoalType-1 .

# Regular open-play goals
?goal fifa:goalType fifa:GoalType-2 .

# Own goals only
?goal fifa:goalType fifa:GoalType-3 .
```

### Match Periods
Used with: `fifa:goalPeriod`, `fifa:bookingPeriod`, `fifa:substitutionPeriod`, `fifa:eventPeriod`

```sparql
# Events in extra time
VALUES ?etPeriod { fifa:MatchPeriod-7 fifa:MatchPeriod-9 }
?goal fifa:goalPeriod ?etPeriod .

# Penalty shootout events
?event fifa:eventPeriod fifa:MatchPeriod-11 .
```

### Positions
Used with: `fifa:position`, `fifa:realPosition` on `fifa:Player` and `fifa:PlayerMatchAppearance`

Position instances are under the `pos:` (`https://fifa.com/position#`) namespace, formally typed `a fifa:Position`:

| URI | Label |
|---|---|
| `pos:0` | Goalkeeper |
| `pos:1` | Defender |
| `pos:2` | Midfielder |
| `pos:3` | Forward |

```sparql
# All forwards in the tournament
?player fifa:realPosition pos:3 .

# Goalkeepers in a match lineup
?app fifa:player ?player ;
     fifa:position pos:0 .
```

> **Note**: Both `pos:N` (`https://fifa.com/position#N`) and `fifa:Position-N` (`https://www.openlinksw.com/ontology/fifa#Position-N`) are valid `fifa:Position` instances defined in the ontology. Use `pos:N` as the canonical form in SPARQL queries.

### Position Sides
Used with: `fifa:realPositionSide`, `fifa:positionSide`

Position side instances are under the `pside:` (`https://fifa.com/positionSide#`) namespace, formally typed `a fifa:PositionSide`:

| URI | Label |
|---|---|
| `pside:1` | Right side |
| `pside:2` | Center |
| `pside:3` | Left side |

> **Note**: `pside:3` (`https://fifa.com/positionSide#3`) is "left side". The separate instance `fifa:PositionSide-3` (`https://www.openlinksw.com/ontology/fifa#PositionSide-3`) is labeled "Unknown" — both exist in the ontology but represent different individuals. Use `pside:N` for directional queries.

```sparql
# Left-sided players
?player fifa:realPositionSide pside:3 .

# Central players
?player fifa:realPositionSide pside:2 .
```

### Event Types (subclasses of `fifa:MatchEvent`)
Used with: `rdf:type` on event individuals — **not** a datatype property

Three intermediate classes allow category-level filtering without enumerating every `EventType-N`:

| Intermediate Class | Members |
|---|---|
| `fifa:Goal` | EventType-34 (Own goal), -39 (Free Kick goal), -41 (Penalty Goal) |
| `fifa:Foul` | EventType-2 (Yellow card), -3 (Red card), -4 (Second Caution), -18 (Foul) |
| `fifa:SetPiece` | EventType-14 (Free Kick), -16 (Corner), -24 (Throw In) |

```sparql
# All foul-related events (fouls + all card types)
?match fifa:hasEvent ?event .
?event a fifa:Foul .

# All goals (own goals, free kick goals, penalty goals) via subclass
?match fifa:hasEvent ?event .
?event a fifa:Goal .

# All set pieces
?match fifa:hasEvent ?event .
?event a fifa:SetPiece .

# Specific foul events only (not cards)
?match fifa:hasEvent ?event .
?event a fifa:EventType-18 .

# VAR decisions
?match fifa:hasEvent ?event .
?event a fifa:EventType-71 .

# Penalties awarded
?match fifa:hasEvent ?event .
?event a fifa:EventType-6 .
```

### Spatial Properties on `fifa:MatchEvent`

| Property | Applies to | Description |
|---|---|---|
| `fifa:positionX` | Any `fifa:MatchEvent` | X coordinate on field |
| `fifa:positionY` | Any `fifa:MatchEvent` | Y coordinate on field |
| `fifa:goalGatePositionY` | `fifa:Goal` events | Y coordinate of ball at goal line |
| `fifa:goalGatePositionZ` | `fifa:Goal` events | Z coordinate (height) of ball at goal line |

```sparql
# Field positions of all fouls
?match fifa:hasEvent ?event .
?event a fifa:Foul ;
       fifa:positionX ?x ;
       fifa:positionY ?y .

# Where goals entered the net (gate position)
?match fifa:hasEvent ?event .
?event a fifa:Goal ;
       fifa:goalGatePositionY ?gateY ;
       fifa:goalGatePositionZ ?gateZ .

# Combine field position with gate position for goal events
?match fifa:hasEvent ?event .
?event a fifa:Goal ;
       fifa:positionX ?shotX ;
       fifa:positionY ?shotY ;
       fifa:goalGatePositionY ?gateY ;
       fifa:goalGatePositionZ ?gateZ ;
       fifa:eventPlayer ?player .
?player rdfs:label ?playerName .
```

### VAR Properties on `fifa:MatchEvent`

Available on VAR-related events (`fifa:EventType-71` and events under VAR review):

| Property | Range | Description |
|---|---|---|
| `fifa:varIncident` | `xsd:integer` | VAR incident type |
| `fifa:varReason` | `xsd:integer` | Reason for VAR review |
| `fifa:varStatus` | `xsd:integer` | Current VAR review status |
| `fifa:varResult` | `xsd:integer` | Outcome of VAR review |

```sparql
# All VAR decisions in a match
SELECT ?event ?minute ?incident ?reason ?status ?result
WHERE {
  ?match a fifa:Match ;
         rdfs:label ?matchLabel ;
         fifa:hasEvent ?event .
  ?event a fifa:EventType-71 ;
         fifa:eventMatchMinute ?minute .
  OPTIONAL { ?event fifa:varIncident ?incident }
  OPTIONAL { ?event fifa:varReason   ?reason }
  OPTIONAL { ?event fifa:varStatus   ?status }
  OPTIONAL { ?event fifa:varResult   ?result }
}
ORDER BY ?minute
```

### EventQualifier Queries

```sparql
# Goalmouth coordinates for all goals (via EventQualifier)
SELECT ?match ?matchLabel ?event ?player ?playerName ?gmY ?gmZ
WHERE {
  ?match a fifa:Match ;
         rdfs:label ?matchLabel ;
         fifa:hasEvent ?event .
  ?event a fifa:Goal ;
         fifa:hasQualifier ?q .
  ?q fifa:goalmouthYCoordinate ?gmY ;
     fifa:goalmouthZCoordinate ?gmZ .
  OPTIONAL { ?event fifa:eventPlayer ?player . ?player rdfs:label ?playerName }
}

# Goalkeeper position data for attempts on goal
SELECT ?event ?minute ?gkX ?gkY
WHERE {
  ?match a fifa:Match ;
         fifa:hasEvent ?event .
  ?event a fifa:EventType-12 ;     # Attempt at Goal
         fifa:eventMatchMinute ?minute ;
         fifa:hasQualifier ?q .
  ?q fifa:gkXCoordinate ?gkX ;
     fifa:gkYCoordinate ?gkY .
}

# Cross-reference: live Goal entity → timeline event → qualifier
SELECT ?goal ?goalMinute ?player ?playerName ?gmY ?gmZ
WHERE {
  ?match a fifa:Match ;
         fifa:hasGoal ?goal .
  ?goal fifa:goalMinute ?goalMinute ;
        fifa:timelineEvent ?event .
  ?event fifa:hasQualifier ?q .
  OPTIONAL { ?q fifa:goalmouthYCoordinate ?gmY }
  OPTIONAL { ?q fifa:goalmouthZCoordinate ?gmZ }
  OPTIONAL { ?goal fifa:player ?player . ?player rdfs:label ?playerName }
}
```

### Result Types
Used with: `fifa:resultType` on `fifa:Match`

| Value | Meaning |
|---|---|
| 1 | Normal full time |
| 2 | After Extra Time (AET) |
| 3 | Decided by Penalty Shootout |

```sparql
# Matches decided by penalties
?match fifa:resultType 3 .
```

### Field Status (PlayerMatchAppearance)
| Value | Meaning |
|---|---|
| 1 | Starting XI |
| 2 | Substitute (bench) |

---

## Query Examples by Use Case

> **URI + Label rule**: Every query SELECTs both the entity URI and its `rdfs:label`. This enables clickable hyperlinks for users and stable identifiers for LLM follow-up queries. Always include both in `GROUP BY` for aggregate queries.

### Top Scorers (Most Goals)
```sparql
SELECT ?player ?playerName (COUNT(?goal) AS ?goals)
WHERE {
  ?match a fifa:Match ;
         fifa:hasGoal ?goal .
  ?goal fifa:player ?player .
  ?player rdfs:label ?playerName .
  FILTER NOT EXISTS { ?goal fifa:goalType fifa:GoalType-3 }  # exclude own goals (GoalType-3)
}
GROUP BY ?player ?playerName
ORDER BY DESC(?goals)
LIMIT 10
```

### All Red Cards in a Tournament
```sparql
SELECT ?match ?matchLabel ?player ?playerName ?booking ?minute ?period ?periodLabel
WHERE {
  ?match a fifa:Match ;
         rdfs:label ?matchLabel ;
         fifa:hasBooking ?booking .
  VALUES ?redCard { fifa:CardType-2 fifa:CardType-3 }
  ?booking fifa:bookingCard ?redCard ;
           fifa:bookingMinute ?minute ;
           fifa:bookingPeriod ?period .
  ?period rdfs:label ?periodLabel .
  OPTIONAL { ?booking fifa:player ?player . ?player rdfs:label ?playerName }
}
ORDER BY ?minute
```

### Matches at a Specific Stadium
```sparql
SELECT ?match ?matchLabel ?stadium ?stadiumName ?date ?homeTeam ?homeTeamName ?awayTeam ?awayTeamName ?homeScore ?awayScore
WHERE {
  ?match a fifa:Match ;
         rdfs:label ?matchLabel ;
         fifa:date ?date ;
         fifa:homeTeam ?homeTeam ;
         fifa:awayTeam ?awayTeam ;
         fifa:homeTeamScore ?homeScore ;
         fifa:awayTeamScore ?awayScore ;
         fifa:stadium ?stadium .
  ?stadium rdfs:label ?stadiumName .
  FILTER(CONTAINS(LCASE(?stadiumName), "maracana"))
  ?homeTeam rdfs:label ?homeTeamName .
  ?awayTeam rdfs:label ?awayTeamName .
}
ORDER BY ?date
```

### All Substitutions in a Match by Minute
```sparql
SELECT ?sub ?playerOff ?outName ?playerOn ?inName ?minute ?period ?periodLabel
WHERE {
  ?match a fifa:Match ;
         rdfs:label "Brazil vs Germany" ;
         fifa:hasSubstitution ?sub .
  ?sub fifa:playerOff     ?playerOff ;
       fifa:playerOffName ?outName ;
       fifa:playerOn      ?playerOn ;
       fifa:playerOnName  ?inName ;
       fifa:substitutionMinute ?minute ;
       fifa:substitutionPeriod ?period .
  ?period rdfs:label ?periodLabel .
}
ORDER BY ?minute
```

### Match Timeline (All Events in Order)
```sparql
SELECT ?event ?minute ?eventType ?eventTypeLabel ?player ?playerName ?team ?teamName ?homeGoals ?awayGoals
WHERE {
  ?match a fifa:Match ;
         rdfs:label ?matchLabel ;
         fifa:hasEvent ?event .
  ?event fifa:eventMatchMinute ?minute ;
         a ?eventType .
  ?eventType rdfs:label ?eventTypeLabel .
  FILTER(?eventType != fifa:MatchEvent)   # exclude the base class itself
  OPTIONAL { ?event fifa:eventPlayer ?player . ?player rdfs:label ?playerName }
  OPTIONAL { ?event fifa:eventTeam ?team . ?team rdfs:label ?teamName }
  OPTIONAL { ?event fifa:eventHomeGoals ?homeGoals }
  OPTIONAL { ?event fifa:eventAwayGoals ?awayGoals }
}
ORDER BY ?minute
```

### Team World Rankings at Tournament Start
```sparql
SELECT ?team ?teamName ?wr ?rankValue ?rankDate
WHERE {
  ?team a fifa:Team ;
        rdfs:label ?teamName ;
        fifa:hasWorldRanking ?wr .
  ?wr fifa:rankingValue ?rankValue ;
      fifa:asOfDatetime ?rankDate .
}
ORDER BY ?rankValue
```

### Players Who Scored and Were Also Booked
```sparql
SELECT DISTINCT ?player ?playerName
WHERE {
  ?match a fifa:Match ;
         fifa:hasGoal ?goal ;
         fifa:hasBooking ?booking .
  ?goal fifa:player ?player .
  ?booking fifa:player ?player .
  ?player rdfs:label ?playerName .
}
```

### Matches With Weather Data
```sparql
SELECT ?match ?matchLabel ?weather ?temp ?humidity ?wind ?condition
WHERE {
  ?match a fifa:Match ;
         rdfs:label ?matchLabel ;
         fifa:weather ?weather .
  ?weather fifa:temperature          ?temp ;
           fifa:humidity             ?humidity ;
           fifa:windSpeed            ?wind ;
           fifa:weatherTypeLocalized ?condition .
}
```

### Squad for a Team in a Season
```sparql
SELECT ?player ?playerName ?jersey ?pos ?posLabel
WHERE {
  ?team a fifa:Team ;
        rdfs:label "Brazil" ;
        fifa:hasPlayer ?player .
  ?player rdfs:label ?playerName ;
          fifa:jerseyNum ?jersey .
  OPTIONAL {
    ?player fifa:inSquad ?sm .
    ?sm fifa:forTeam ?team ;
        fifa:duringSeason ?season .
    ?season rdfs:label "2022" .
  }
  OPTIONAL {
    ?player fifa:realPosition ?pos .
    ?pos rdfs:label ?posLabel .
  }
}
ORDER BY ?jersey
```

### Goals Scored in Extra Time
```sparql
SELECT ?match ?matchLabel ?goal ?playerName ?minute
WHERE {
  ?match a fifa:Match ;
         rdfs:label ?matchLabel ;
         fifa:hasGoal ?goal .
  VALUES ?etPeriod { fifa:MatchPeriod-7 fifa:MatchPeriod-9 }
  ?goal fifa:goalPeriod ?etPeriod ;
        fifa:goalMinute ?minute .
  OPTIONAL { ?goal fifa:player ?player . ?player rdfs:label ?playerName }
}
ORDER BY ?minute
```

### Coaches Per Match
```sparql
SELECT ?match ?matchLabel ?coach ?coachName ?team ?teamName ?coachRole
WHERE {
  ?match a fifa:Match ;
         rdfs:label ?matchLabel ;
         fifa:hasCoach ?ca .
  ?ca fifa:coach ?coach ;
      fifa:coachRole ?coachRole .
  ?coach rdfs:label ?coachName .
  OPTIONAL { ?ca fifa:team ?team . ?team rdfs:label ?teamName }
}
```

### Matches Where a Team Played with 4-3-3
```sparql
SELECT ?match ?matchLabel ?date ?team ?teamName ?score
WHERE {
  ?match a fifa:Match ;
         rdfs:label ?matchLabel ;
         fifa:date ?date .
  {
    ?match fifa:homeTeamTactics fifa:Tactic-4-3-3 ;
           fifa:homeTeam ?team ;
           fifa:homeTeamScore ?score .
  } UNION {
    ?match fifa:awayTeamTactics fifa:Tactic-4-3-3 ;
           fifa:awayTeam ?team ;
           fifa:awayTeamScore ?score .
  }
  ?team rdfs:label ?teamName .
}
ORDER BY ?date
```

### Ball Possession Stats for All Matches
```sparql
SELECT ?match ?homeTeam ?homeTeamName ?awayTeam ?awayTeamName ?homePct ?awayPct
WHERE {
  ?match a fifa:Match ;
         fifa:homeTeam ?homeTeam ;
         fifa:awayTeam ?awayTeam ;
         fifa:ballPossession ?poss .
  ?homeTeam rdfs:label ?homeTeamName .
  ?awayTeam rdfs:label ?awayTeamName .
  ?poss fifa:overallHome ?homePct ;
        fifa:overallAway ?awayPct .
}
ORDER BY DESC(?homePct)
```
