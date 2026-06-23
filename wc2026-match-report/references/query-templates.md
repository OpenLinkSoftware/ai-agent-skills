# Query Templates — WC2026 Match Report

All queries target `https://demo.openlinksw.com/sparql`.

**Variables to substitute:**
- `{MATCH_ID}` — numeric match ID (e.g. `400021491`)
- `{MATCH_IRI}` — `http://demo.openlinksw.com/fifa-kg#match-{MATCH_ID}`

---

## Team Name Aliases

| User term | KG `rdfs:label` |
|---|---|
| DR Congo / Congo DR | `Congo DR` |
| South Korea | `Korea Republic` |
| Bosnia | `Bosnia and Herzegovina` |
| Czech Republic | `Czechia` |
| USA | `United States` |
| Ivory Coast | `Côte d'Ivoire` |
| Turkey | `Türkiye` |
| Iran | `IR Iran` |
| Curacao | `Curaçao` |

---

## Q1 — Match Overview

```sparql
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?match ?homeTeam ?awayTeam ?homeScore ?awayScore ?date ?stadium ?city
       ?attendance ?homeTactic ?awayTactic ?group ?stage
       ?temp ?humidity ?wind ?weatherDesc ?homePoss ?awayPoss
FROM <urn:worldcup:kg:2026>
WHERE {
  ?match a fifa:Match ; fifa:matchId "{MATCH_ID}" ;
    fifa:homeTeam ?ht ; fifa:awayTeam ?at ;
    fifa:homeTeamScore ?homeScore ; fifa:awayTeamScore ?awayScore ; fifa:date ?date .
  ?ht rdfs:label ?homeTeam . ?at rdfs:label ?awayTeam .
  OPTIONAL { ?match fifa:stadium ?s . ?s rdfs:label ?stadium .
    OPTIONAL { ?s fifa:city ?c . ?c rdfs:label ?city } }
  OPTIONAL { ?match fifa:attendance ?attendance }
  OPTIONAL { ?match fifa:homeTeamTactics ?htac . ?htac rdfs:label ?homeTactic }
  OPTIONAL { ?match fifa:awayTeamTactics ?atac . ?atac rdfs:label ?awayTactic }
  OPTIONAL { ?match fifa:group ?g . ?g rdfs:label ?group }
  OPTIONAL { ?match fifa:stage ?st . ?st rdfs:label ?stage }
  OPTIONAL { ?match fifa:weather ?w .
    ?w fifa:temperature ?temp ; fifa:humidity ?humidity ;
       fifa:windSpeed ?wind ; fifa:weatherTypeLocalized ?weatherDesc }
  OPTIONAL { ?match fifa:ballPossession ?bp .
    ?bp fifa:overallHome ?homePoss ; fifa:overallAway ?awayPoss }
}
```

---

## Q2 — Goals

```sparql
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?goal ?minute ?goalType ?scorer ?scorerName ?team ?teamName ?assist ?assistName
FROM <urn:worldcup:kg:2026>
WHERE {
  ?match a fifa:Match ; fifa:matchId "{MATCH_ID}" ; fifa:hasGoal ?goal .
  ?goal fifa:goalMinute ?minute ; fifa:team ?team ; fifa:player ?scorer .
  ?team rdfs:label ?teamName . ?scorer rdfs:label ?scorerName .
  OPTIONAL { ?goal fifa:goalType ?gt . ?gt rdfs:label ?goalType }
  OPTIONAL { ?goal fifa:assistPlayer ?assist . ?assist rdfs:label ?assistName }
}
ORDER BY ?minute
```

**Goal type coded values:** `fifa:GoalType-1` = Penalty, `fifa:GoalType-2` = Regular, `fifa:GoalType-3` = Own Goal.

---

## Q3 — Bookings

```sparql
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?minute ?cardType ?player ?playerName ?team ?teamName
FROM <urn:worldcup:kg:2026>
WHERE {
  ?match a fifa:Match ; fifa:matchId "{MATCH_ID}" ; fifa:hasBooking ?booking .
  ?booking fifa:bookingMinute ?minute ; fifa:bookingCard ?card ; fifa:team ?team .
  ?card rdfs:label ?cardType . ?team rdfs:label ?teamName .
  OPTIONAL { ?booking fifa:player ?player . ?player rdfs:label ?playerName }
}
ORDER BY ?minute
```

**Card type coded values:** `fifa:CardType-1` = Yellow, `fifa:CardType-2` = Second Yellow, `fifa:CardType-3` = Straight Red.

---

## Q4 — Substitutions

```sparql
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?minute ?playerOn ?playerOnName ?playerOff ?playerOffName ?team ?teamName
FROM <urn:worldcup:kg:2026>
WHERE {
  ?match a fifa:Match ; fifa:matchId "{MATCH_ID}" ; fifa:hasSubstitution ?sub .
  ?sub fifa:substitutionMinute ?minute ; fifa:playerOn ?playerOn ;
       fifa:playerOff ?playerOff ; fifa:team ?team .
  ?playerOn rdfs:label ?playerOnName . ?playerOff rdfs:label ?playerOffName .
  ?team rdfs:label ?teamName .
}
ORDER BY ?minute
```

---

## Q5 — Head Coaches (CoachRole-0 only)

```sparql
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?coach ?coachName ?team ?teamName
FROM <urn:worldcup:kg:2026>
WHERE {
  ?match a fifa:Match ; fifa:matchId "{MATCH_ID}" ; fifa:hasCoach ?assignment .
  ?assignment fifa:coach ?coach ; fifa:team ?team ; fifa:hasRole fifa:CoachRole-0 .
  ?coach rdfs:label ?coachName . ?team rdfs:label ?teamName .
}
```

**Important:** `fifa:CoachRole-0` = Head Coach only. Omitting this filter returns all support staff.

---

## Q6 — Hero Article & Image

```sparql
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX schema: <http://schema.org/>
SELECT ?article ?headline ?description ?imageUrl ?articleUrl
FROM <urn:worldcup:kg:2026>
WHERE {
  ?match a fifa:Match ; fifa:matchId "{MATCH_ID}" ; fifa:hasNewsArticle ?article .
  ?article schema:headline ?headline .
  OPTIONAL { ?article schema:description ?description }
  OPTIONAL { ?article schema:image ?img . ?img schema:url ?imageUrl }
  OPTIONAL { ?article schema:url ?articleUrl }
  FILTER(!CONTAINS(str(?articleUrl), "preview") && !CONTAINS(str(?articleUrl), "live-stream"))
}
LIMIT 1
```

---

## Q7 — Squad / Lineup

```sparql
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?player ?playerName ?team ?teamName ?shirt ?captain ?lineupX ?lineupY ?fieldStatus
FROM <urn:worldcup:kg:2026>
WHERE {
  ?match a fifa:Match ; fifa:matchId "{MATCH_ID}" ; fifa:hasPlayerAppearance ?app .
  ?app fifa:player ?player ; fifa:team ?team ; fifa:shirtNumber ?shirt .
  ?player rdfs:label ?playerName . ?team rdfs:label ?teamName .
  OPTIONAL { ?app fifa:captain ?captain }
  OPTIONAL { ?app fifa:lineupX ?lineupX }
  OPTIONAL { ?app fifa:lineupY ?lineupY }
  OPTIONAL { ?app fifa:fieldStatus ?fieldStatus }
}
ORDER BY ?teamName ?shirt
```

**Starter inference:** If `lineupX`/`lineupY` are available, use those. Otherwise infer starters as squad members NOT in the substitution `playerOn` set. Limit to 11 per team.

---

## Q8 — Team Analytics (latest snapshot)

```sparql
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?teamName ?possession ?passes ?passesCompleted ?attemptAtGoal ?attemptAtGoalOnTarget
       ?goals ?xG ?yellowCards ?corners ?foulsAgainst ?offsides
       ?highPress ?counterPress ?defensivePressures ?threat ?pitchControl ?finalThirdPC
       ?attackTrans ?defTrans ?buildUpOpp ?buildUpUnopp ?counterattack ?finalThird
       ?midBlock ?midPress ?lowBlock ?setPieces ?progression ?recovery ?generatedAt
WHERE {
  GRAPH <urn:worldcup:kg:2026:analytics> {
    ?report a fifa:TeamMatchAnalyticsReport ;
            fifa:match <{MATCH_IRI}> ; fifa:team ?team ;
            fifa:generatedAt ?generatedAt .
    { SELECT ?team (MAX(?gen) AS ?generatedAt) WHERE {
        GRAPH <urn:worldcup:kg:2026:analytics> {
          ?r a fifa:TeamMatchAnalyticsReport ;
             fifa:match <{MATCH_IRI}> ; fifa:team ?team ; fifa:generatedAt ?gen .
        } } GROUP BY ?team }
    OPTIONAL { ?report fifa:possession ?possession }
    OPTIONAL { ?report fifa:passes ?passes }
    OPTIONAL { ?report fifa:passesCompleted ?passesCompleted }
    OPTIONAL { ?report fifa:attemptAtGoal ?attemptAtGoal }
    OPTIONAL { ?report fifa:attemptAtGoalOnTarget ?attemptAtGoalOnTarget }
    OPTIONAL { ?report fifa:goals ?goals }
    OPTIONAL { ?report fifa:xG ?xG }
    OPTIONAL { ?report fifa:yellowCards ?yellowCards }
    OPTIONAL { ?report fifa:corners ?corners }
    OPTIONAL { ?report fifa:foulsAgainst ?foulsAgainst }
    OPTIONAL { ?report fifa:offsides ?offsides }
    OPTIONAL { ?report fifa:phaseAggregateHighPress ?highPress }
    OPTIONAL { ?report fifa:phaseAggregateCounterPress ?counterPress }
    OPTIONAL { ?report fifa:defensivePressuresApplied ?defensivePressures }
    OPTIONAL { ?report fifa:threat ?threat }
    OPTIONAL { ?report fifa:pitchControl ?pitchControl }
    OPTIONAL { ?report fifa:finalThirdPitchControl ?finalThirdPC }
    OPTIONAL { ?report fifa:phaseAggregateAttackingTransition ?attackTrans }
    OPTIONAL { ?report fifa:phaseAggregateDefensiveTransition ?defTrans }
    OPTIONAL { ?report fifa:phaseAggregateBuildUpOpposed ?buildUpOpp }
    OPTIONAL { ?report fifa:phaseAggregateBuildUpUnopposed ?buildUpUnopp }
    OPTIONAL { ?report fifa:phaseAggregateCounterattack ?counterattack }
    OPTIONAL { ?report fifa:phaseAggregateFinalThird ?finalThird }
    OPTIONAL { ?report fifa:phaseAggregateMidBlock ?midBlock }
    OPTIONAL { ?report fifa:phaseAggregateMidPress ?midPress }
    OPTIONAL { ?report fifa:phaseAggregateLowBlock ?lowBlock }
    OPTIONAL { ?report fifa:phaseAggregateSetPieces ?setPieces }
    OPTIONAL { ?report fifa:phaseAggregateProgression ?progression }
    OPTIONAL { ?report fifa:phaseAggregateRecovery ?recovery }
  }
  GRAPH <urn:worldcup:kg:2026> { ?team rdfs:label ?teamName }
}
```

---

## Q9 — Player Analytics (latest snapshot, top 30 by distance)

```sparql
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?player ?playerName ?totalDistance ?sprints ?topSpeed ?avgSpeed
       ?passes ?goals ?assists ?timePlayed ?generatedAt
WHERE {
  GRAPH <urn:worldcup:kg:2026:analytics> {
    ?report a fifa:PlayerMatchAnalyticsReport ;
            fifa:match <{MATCH_IRI}> ; fifa:player ?player ;
            fifa:generatedAt ?generatedAt .
    { SELECT ?player (MAX(?gen) AS ?generatedAt) WHERE {
        GRAPH <urn:worldcup:kg:2026:analytics> {
          ?r a fifa:PlayerMatchAnalyticsReport ;
             fifa:match <{MATCH_IRI}> ; fifa:player ?player ; fifa:generatedAt ?gen .
        } } GROUP BY ?player }
    OPTIONAL { ?report fifa:totalDistance ?totalDistance }
    OPTIONAL { ?report fifa:sprints ?sprints }
    OPTIONAL { ?report fifa:topSpeed ?topSpeed }
    OPTIONAL { ?report fifa:avgSpeed ?avgSpeed }
    OPTIONAL { ?report fifa:passes ?passes }
    OPTIONAL { ?report fifa:goals ?goals }
    OPTIONAL { ?report fifa:assists ?assists }
    OPTIONAL { ?report fifa:timePlayed ?timePlayed }
  }
  GRAPH <urn:worldcup:kg:2026> { ?player rdfs:label ?playerName }
}
ORDER BY DESC(?totalDistance)
LIMIT 30
```

**Note:** Analytics reports have no `fifa:team`. Cross-reference `?playerName` against squad appearance data to assign team.
