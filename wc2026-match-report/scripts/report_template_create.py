#!/usr/bin/env python3
"""Generate a full FIFA World Cup 2026 match intelligence HTML report.

Queries demo.openlinksw.com SPARQL and builds a complete report: real match
images, narrative text, goal pitch diagrams, timeline, team stats, phase
analytics, pressing intelligence with gauges, temporal chart, formation SVGs,
squads, core players with physical data, and live SPARQL explorer.

Usage:
    python report_template_create.py <match_id> <output_filename>

Fixes vs prior version:
  - Pure urllib (no curl/subprocess dependency)
  - Analytics queries use GRAPH clauses so subqueries scope correctly in Virtuoso
  - Coach query filtered to fifa:CoachRole-0 only (head coaches, not assistants)
"""

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote_plus, urlencode
from urllib.request import Request, urlopen

SPARQL_ENDPOINT = "https://demo.openlinksw.com/sparql"
KG  = "urn:worldcup:kg:2026"
ANA = "urn:worldcup:kg:2026:analytics"
MATCH_IRI_BASE = "http://demo.openlinksw.com/fifa-kg#match-"

TEAM_COLOURS = {
    # Europe
    "Portugal":               {"bg": "#006600", "abbr": "POR", "text": "#fff"},
    "England":                {"bg": "#012169", "abbr": "ENG", "text": "#fff"},
    "Croatia":                {"bg": "#CC0000", "abbr": "CRO", "text": "#fff"},
    "Switzerland":            {"bg": "#FF0000", "abbr": "SUI", "text": "#fff"},
    "Bosnia and Herzegovina": {"bg": "#002395", "abbr": "BIH", "text": "#fff"},
    "Canada":                 {"bg": "#FF0000", "abbr": "CAN", "text": "#fff"},
    "Czechia":                {"bg": "#D7141A", "abbr": "CZE", "text": "#fff"},
    "Austria":                {"bg": "#ED2939", "abbr": "AUT", "text": "#fff"},
    "Spain":                  {"bg": "#C60B1E", "abbr": "ESP", "text": "#fff"},
    "Belgium":                {"bg": "#EF3340", "abbr": "BEL", "text": "#fff"},
    "France":                 {"bg": "#002395", "abbr": "FRA", "text": "#fff"},
    "Netherlands":            {"bg": "#FF6200", "abbr": "NED", "text": "#fff"},
    "Norway":                 {"bg": "#EF2B2D", "abbr": "NOR", "text": "#fff"},
    "Sweden":                 {"bg": "#006AA7", "abbr": "SWE", "text": "#fff"},
    "Germany":                {"bg": "#000000", "abbr": "GER", "text": "#fff"},
    "Scotland":               {"bg": "#003380", "abbr": "SCO", "text": "#fff"},
    "Türkiye":                {"bg": "#E30A17", "abbr": "TUR", "text": "#fff"},
    "Denmark":                {"bg": "#C60C30", "abbr": "DEN", "text": "#fff"},
    "Italy":                  {"bg": "#003399", "abbr": "ITA", "text": "#fff"},
    "Poland":                 {"bg": "#DC143C", "abbr": "POL", "text": "#fff"},
    "Romania":                {"bg": "#002B7F", "abbr": "ROU", "text": "#fff"},
    "Hungary":                {"bg": "#CE2939", "abbr": "HUN", "text": "#fff"},
    "Slovakia":               {"bg": "#0B4EA2", "abbr": "SVK", "text": "#fff"},
    "Slovenia":               {"bg": "#003DA5", "abbr": "SVN", "text": "#fff"},
    "Ukraine":                {"bg": "#005BBB", "abbr": "UKR", "text": "#fff"},
    "Wales":                  {"bg": "#C8102E", "abbr": "WAL", "text": "#fff"},
    "Albania":                {"bg": "#E41E20", "abbr": "ALB", "text": "#fff"},
    "Serbia":                 {"bg": "#C6363C", "abbr": "SRB", "text": "#fff"},
    # South America
    "Brazil":                 {"bg": "#009C3B", "abbr": "BRA", "text": "#fff"},
    "Argentina":              {"bg": "#74ACDF", "abbr": "ARG", "text": "#000"},
    "Colombia":               {"bg": "#FCD116", "abbr": "COL", "text": "#000"},
    "Uruguay":                {"bg": "#5AAEE9", "abbr": "URU", "text": "#000"},
    "Ecuador":                {"bg": "#FFD100", "abbr": "ECU", "text": "#000"},
    "Paraguay":               {"bg": "#D52B1E", "abbr": "PAR", "text": "#fff"},
    "Venezuela":              {"bg": "#CF142B", "abbr": "VEN", "text": "#fff"},
    "Chile":                  {"bg": "#D52B1E", "abbr": "CHI", "text": "#fff"},
    "Peru":                   {"bg": "#D91023", "abbr": "PER", "text": "#fff"},
    "Bolivia":                {"bg": "#D52B1E", "abbr": "BOL", "text": "#fff"},
    # North/Central America & Caribbean
    "Mexico":                 {"bg": "#006847", "abbr": "MEX", "text": "#fff"},
    "USA":                    {"bg": "#002868", "abbr": "USA", "text": "#fff"},
    "United States":          {"bg": "#002868", "abbr": "USA", "text": "#fff"},
    "Panama":                 {"bg": "#B00020", "abbr": "PAN", "text": "#fff"},
    "Costa Rica":             {"bg": "#002B7F", "abbr": "CRC", "text": "#fff"},
    "Jamaica":                {"bg": "#000000", "abbr": "JAM", "text": "#fff"},
    "Cuba":                   {"bg": "#002A8F", "abbr": "CUB", "text": "#fff"},
    "Curaçao":                {"bg": "#0077C8", "abbr": "CUW", "text": "#fff"},
    "Honduras":               {"bg": "#0073CF", "abbr": "HON", "text": "#fff"},
    # Africa
    "Morocco":                {"bg": "#C1272D", "abbr": "MAR", "text": "#fff"},
    "Senegal":                {"bg": "#00853F", "abbr": "SEN", "text": "#fff"},
    "Egypt":                  {"bg": "#CE1126", "abbr": "EGY", "text": "#fff"},
    "Algeria":                {"bg": "#006233", "abbr": "ALG", "text": "#fff"},
    "Ghana":                  {"bg": "#006B3F", "abbr": "GHA", "text": "#fff"},
    "Nigeria":                {"bg": "#008751", "abbr": "NGA", "text": "#fff"},
    "Cameroon":               {"bg": "#007A5E", "abbr": "CMR", "text": "#fff"},
    "South Africa":           {"bg": "#007A4D", "abbr": "RSA", "text": "#fff"},
    "Côte d'Ivoire":          {"bg": "#F77F00", "abbr": "CIV", "text": "#fff"},
    "Congo DR":               {"bg": "#0047AB", "abbr": "DRC", "text": "#fff"},
    "Tanzania":               {"bg": "#1EB53A", "abbr": "TAN", "text": "#000"},
    # Asia / Oceania
    "Japan":                  {"bg": "#002F6C", "abbr": "JPN", "text": "#fff"},
    "Korea Republic":         {"bg": "#CD2E3A", "abbr": "KOR", "text": "#fff"},
    "Saudi Arabia":           {"bg": "#006C35", "abbr": "KSA", "text": "#fff"},
    "IR Iran":                {"bg": "#239F40", "abbr": "IRI", "text": "#fff"},
    "Australia":              {"bg": "#00843D", "abbr": "AUS", "text": "#fff"},
    "Iraq":                   {"bg": "#CE1126", "abbr": "IRQ", "text": "#fff"},
    "New Zealand":            {"bg": "#00247D", "abbr": "NZL", "text": "#fff"},
}

def _c(name):
    return TEAM_COLOURS.get(name, {"bg": "#334466", "abbr": name[:3].upper(), "text": "#fff"})


# ── SPARQL helpers ─────────────────────────────────────────────────────────────

def sparql(query, timeout=45):
    """Execute SPARQL query via urllib (no curl/subprocess dependency)."""
    data = urlencode({
        "query": query,
        "format": "application/sparql-results+json",
        "timeout": str(timeout),
    }).encode()
    req = Request(SPARQL_ENDPOINT, data=data,
                  headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urlopen(req, timeout=timeout + 10) as resp:
            return json.loads(resp.read()).get("results", {}).get("bindings", [])
    except Exception as e:
        print(f"  SPARQL error: {e}", file=sys.stderr)
        return []

def v(b, k, d=""):
    return b.get(k, {}).get("value", d)

def fnum(s, dec=0):
    try:
        return f"{float(s):,.{dec}f}"
    except Exception:
        return str(s) if s else "—"

def sparql_url(query):
    return (f"https://demo.openlinksw.com/sparql?default-graph-uri=urn%3Aworldcup%3Akg%3A2026"
            f"&query={quote_plus(query)}&format=text%2Fx-html%2Btr&timeout=30&run=+Run+Query+")

def ent_link(eid, label, kind="player"):
    url  = f"http://demo.openlinksw.com/fifa-kg#{kind}-{eid}"
    href = f"https://demo.openlinksw.com/describe/?url={quote_plus(url)}"
    return f'<a class="entity-link" href="{href}" target="_blank" rel="noopener noreferrer">{label}</a>'


# ── Data queries ───────────────────────────────────────────────────────────────

def q_overview(mid):
    rows = sparql(f"""
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX fifa-kg: <http://demo.openlinksw.com/fifa-kg#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?homeTeam ?awayTeam ?homeTeamId ?awayTeamId ?homeScore ?awayScore
       ?date ?stadium ?stadiumId ?attendance ?group ?homeTactic ?awayTactic
FROM <{KG}>
WHERE {{
  BIND(fifa-kg:match-{mid} AS ?m)
  ?m fifa:homeTeam ?ht ; fifa:awayTeam ?at ;
     fifa:homeTeamScore ?homeScore ; fifa:awayTeamScore ?awayScore ; fifa:date ?date .
  ?ht rdfs:label ?homeTeam . ?at rdfs:label ?awayTeam .
  BIND(REPLACE(STR(?ht),".*team-","") AS ?homeTeamId)
  BIND(REPLACE(STR(?at),".*team-","") AS ?awayTeamId)
  OPTIONAL {{ ?m fifa:stadium ?s . ?s rdfs:label ?stadium .
              BIND(REPLACE(STR(?s),".*stadium-","") AS ?stadiumId) }}
  OPTIONAL {{ ?m fifa:attendance ?attendance }}
  OPTIONAL {{ ?m fifa:group ?g . ?g rdfs:label ?group }}
  OPTIONAL {{ ?m fifa:homeTeamTactics ?htac . ?htac rdfs:label ?homeTactic }}
  OPTIONAL {{ ?m fifa:awayTeamTactics ?atac . ?atac rdfs:label ?awayTactic }}
}}""")
    return rows[0] if rows else {}


def q_coaches(mid):
    """Head coaches only — filtered to fifa:CoachRole-0."""
    rows = sparql(f"""
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX fifa-kg: <http://demo.openlinksw.com/fifa-kg#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?teamName ?coachName ?coachId
FROM <{KG}>
WHERE {{
  fifa-kg:match-{mid} fifa:hasCoach ?ca .
  ?ca fifa:team ?t ; fifa:coach ?c ; fifa:hasRole fifa:CoachRole-0 .
  ?t rdfs:label ?teamName . ?c rdfs:label ?coachName .
  BIND(REPLACE(STR(?c),".*coach-","") AS ?coachId)
}}""")
    return {v(r, "teamName"): r for r in rows}


def q_goals(mid):
    return sparql(f"""
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX fifa-kg: <http://demo.openlinksw.com/fifa-kg#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?minute ?playerName ?playerId ?teamName ?goalType ?assistName ?assistId
FROM <{KG}>
WHERE {{
  fifa-kg:match-{mid} fifa:hasGoal ?goal .
  ?goal fifa:goalMinute ?minute .
  OPTIONAL {{ ?goal fifa:player ?p . ?p rdfs:label ?playerName .
              BIND(REPLACE(STR(?p),".*player-","") AS ?playerId) }}
  OPTIONAL {{ ?goal fifa:team ?t . ?t rdfs:label ?teamName }}
  OPTIONAL {{ ?goal fifa:goalType ?gt . ?gt rdfs:label ?goalType }}
  OPTIONAL {{ ?goal fifa:assistPlayer ?a . ?a rdfs:label ?assistName .
              BIND(REPLACE(STR(?a),".*player-","") AS ?assistId) }}
}}
ORDER BY xsd:integer(?minute)""")


def q_bookings(mid):
    return sparql(f"""
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX fifa-kg: <http://demo.openlinksw.com/fifa-kg#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?minute ?playerName ?playerId ?teamName ?cardLabel
FROM <{KG}>
WHERE {{
  fifa-kg:match-{mid} fifa:hasBooking ?b .
  ?b fifa:bookingMinute ?minute .
  OPTIONAL {{ ?b fifa:player ?p . ?p rdfs:label ?playerName .
              BIND(REPLACE(STR(?p),".*player-","") AS ?playerId) }}
  OPTIONAL {{ ?b fifa:team ?t . ?t rdfs:label ?teamName }}
  OPTIONAL {{ ?b fifa:bookingCard ?c . ?c rdfs:label ?cardLabel }}
}}
ORDER BY xsd:integer(?minute)""")


def q_subs(mid):
    return sparql(f"""
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX fifa-kg: <http://demo.openlinksw.com/fifa-kg#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?minute ?playerOnName ?playerOnId ?playerOffName ?playerOffId ?teamName
FROM <{KG}>
WHERE {{
  fifa-kg:match-{mid} fifa:hasSubstitution ?sub .
  ?sub fifa:substitutionMinute ?minute .
  OPTIONAL {{ ?sub fifa:playerOn ?on . ?on rdfs:label ?playerOnName .
              BIND(REPLACE(STR(?on),".*player-","") AS ?playerOnId) }}
  OPTIONAL {{ ?sub fifa:playerOff ?off . ?off rdfs:label ?playerOffName .
              BIND(REPLACE(STR(?off),".*player-","") AS ?playerOffId) }}
  OPTIONAL {{ ?sub fifa:team ?t . ?t rdfs:label ?teamName }}
}}
ORDER BY ?teamName ?minute""")


def q_team_stats(mid, htid, atid):
    """Team analytics — GRAPH clause scoping fixes Virtuoso subquery inheritance."""
    match_iri = f"{MATCH_IRI_BASE}{mid}"
    rows = sparql(f"""
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX fifa-kg: <http://demo.openlinksw.com/fifa-kg#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?teamName ?possession ?passes ?passesCompleted ?goals ?shots ?shotsOnTarget
       ?corners ?yellowCards ?offsides ?defPress ?turnovers ?lbAtt ?lbComp
       ?highPress ?counterPress ?midBlock ?lowBlock ?highBlock ?attTrans
       ?finalThird ?genAt
WHERE {{
  GRAPH <{ANA}> {{
    ?report a fifa:TeamMatchAnalyticsReport ;
            fifa:match <{match_iri}> ;
            fifa:team ?team ;
            fifa:generatedAt ?genAt .
    FILTER(?team IN (fifa-kg:team-{htid}, fifa-kg:team-{atid}))
    OPTIONAL {{ ?report fifa:possession ?possession }}
    OPTIONAL {{ ?report fifa:passes ?passes }}
    OPTIONAL {{ ?report fifa:passesCompleted ?passesCompleted }}
    OPTIONAL {{ ?report fifa:goals ?goals }}
    OPTIONAL {{ ?report fifa:attemptAtGoal ?shots }}
    OPTIONAL {{ ?report fifa:attemptAtGoalOnTarget ?shotsOnTarget }}
    OPTIONAL {{ ?report fifa:corners ?corners }}
    OPTIONAL {{ ?report fifa:yellowCards ?yellowCards }}
    OPTIONAL {{ ?report fifa:offsides ?offsides }}
    OPTIONAL {{ ?report fifa:defensivePressuresApplied ?defPress }}
    OPTIONAL {{ ?report fifa:forcedTurnovers ?turnovers }}
    OPTIONAL {{ ?report fifa:linebreaksAttemptedAllLines ?lbAtt }}
    OPTIONAL {{ ?report fifa:linebreaksCompletedAllLines ?lbComp }}
    OPTIONAL {{ ?report fifa:phaseAggregateHighPress ?highPress }}
    OPTIONAL {{ ?report fifa:phaseAggregateCounterPress ?counterPress }}
    OPTIONAL {{ ?report fifa:phaseAggregateMidBlock ?midBlock }}
    OPTIONAL {{ ?report fifa:phaseAggregateLowBlock ?lowBlock }}
    OPTIONAL {{ ?report fifa:phaseAggregateHighBlock ?highBlock }}
    OPTIONAL {{ ?report fifa:phaseAggregateAttackingTransition ?attTrans }}
    OPTIONAL {{ ?report fifa:phaseAggregateFinalThird ?finalThird }}
  }}
  GRAPH <{KG}> {{ ?team rdfs:label ?teamName }}
}}
ORDER BY ?teamName DESC(?genAt)""")
    seen = {}
    for r in rows:
        tn = v(r, "teamName")
        if tn not in seen:
            seen[tn] = r
    return seen


def q_players(mid):
    """Player analytics — GRAPH clause scoping, latest snapshot per player."""
    match_iri = f"{MATCH_IRI_BASE}{mid}"
    rows = sparql(f"""
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?playerName ?playerId ?goals ?assists ?totalDistance ?passes
       ?timePlayed ?sprints ?topSpeed ?shots ?yellowCards ?generatedAt
WHERE {{
  GRAPH <{ANA}> {{
    ?report a fifa:PlayerMatchAnalyticsReport ;
            fifa:match <{match_iri}> ;
            fifa:player ?player ;
            fifa:generatedAt ?generatedAt .
    {{ SELECT ?player (MAX(?gen) AS ?generatedAt) WHERE {{
        GRAPH <{ANA}> {{
          ?r a fifa:PlayerMatchAnalyticsReport ;
             fifa:match <{match_iri}> ;
             fifa:player ?player ; fifa:generatedAt ?gen .
        }} }} GROUP BY ?player }}
    OPTIONAL {{ ?report fifa:goals ?goals }}
    OPTIONAL {{ ?report fifa:assists ?assists }}
    OPTIONAL {{ ?report fifa:totalDistance ?totalDistance }}
    OPTIONAL {{ ?report fifa:passes ?passes }}
    OPTIONAL {{ ?report fifa:timePlayed ?timePlayed }}
    OPTIONAL {{ ?report fifa:sprints ?sprints }}
    OPTIONAL {{ ?report fifa:topSpeed ?topSpeed }}
    OPTIONAL {{ ?report fifa:attemptAtGoal ?shots }}
    OPTIONAL {{ ?report fifa:yellowCards ?yellowCards }}
  }}
  GRAPH <{KG}> {{
    ?player rdfs:label ?playerName .
    BIND(REPLACE(STR(?player),".*player-","") AS ?playerId)
  }}
}}
ORDER BY DESC(?totalDistance)""")
    seen = {}
    for r in rows:
        pid = v(r, "playerId")
        if not pid:
            continue
        if pid not in seen:
            seen[pid] = r
        else:
            try:
                if float(v(r, "totalDistance", "0")) > float(v(seen[pid], "totalDistance", "0")):
                    seen[pid] = r
            except Exception:
                pass
    return seen


def players_by_team(players_by_id, squad):
    """Group player analytics by team using squad cross-reference.
    Player analytics don't reliably carry fifa:team.
    """
    pid_to_team = {}
    for team_name, squad_list in squad.items():
        for sp in squad_list:
            pid = v(sp, "playerId", "")
            if pid:
                pid_to_team[pid] = team_name

    by_team = {}
    for pid, r in players_by_id.items():
        tn = pid_to_team.get(pid, "Unknown")
        by_team.setdefault(tn, []).append(r)

    for tn in by_team:
        by_team[tn].sort(key=lambda x: -float(v(x, "totalDistance", "0")))
    return by_team


def q_squad(mid):
    rows = sparql(f"""
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX fifa-kg: <http://demo.openlinksw.com/fifa-kg#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?playerName ?playerId ?shirtNumber ?teamName ?posLabel
FROM <{KG}>
WHERE {{
  fifa-kg:match-{mid} fifa:hasPlayerAppearance ?app .
  ?app fifa:player ?player ; fifa:shirtNumber ?shirtNumber .
  ?player rdfs:label ?playerName .
  BIND(REPLACE(STR(?player),".*player-","") AS ?playerId)
  OPTIONAL {{ ?app fifa:team ?team . ?team rdfs:label ?teamName }}
  OPTIONAL {{ ?app fifa:position ?pos . ?pos rdfs:label ?posLabel }}
}}
ORDER BY ?teamName xsd:integer(?shirtNumber)""")
    by_team = {}
    for r in rows:
        tn = v(r, "teamName", "Unknown")
        by_team.setdefault(tn, []).append(r)
    return by_team


def q_article_meta(mid):
    rows = sparql(f"""
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX fifa-kg: <http://demo.openlinksw.com/fifa-kg#>
PREFIX schema: <http://schema.org/>
SELECT ?imageUrl ?imageCaption ?headline ?articleUrl ?description
FROM <{KG}>
WHERE {{
  fifa-kg:match-{mid} fifa:hasNewsArticle ?article .
  ?article schema:headline ?headline ; schema:url ?articleUrl .
  FILTER(!CONTAINS(str(?articleUrl),"preview") && !CONTAINS(str(?articleUrl),"live-stream"))
  OPTIONAL {{ ?article schema:image ?imgObj . ?imgObj schema:url ?imageUrl .
              OPTIONAL {{ ?imgObj schema:caption ?imageCaption }} }}
  OPTIONAL {{ ?article schema:description ?description }}
}}
ORDER BY ?headline""")
    out = {"imageUrl": "", "imageCaption": "", "headline": "", "articleUrl": "", "description": ""}
    for r in rows:
        if v(r, "imageUrl") and not out["imageUrl"]:
            out["imageUrl"] = v(r, "imageUrl")
        if v(r, "imageCaption") and not out["imageCaption"]:
            out["imageCaption"] = v(r, "imageCaption")
        if v(r, "headline") and not out["headline"]:
            out["headline"] = v(r, "headline")
        if v(r, "articleUrl") and not out["articleUrl"]:
            out["articleUrl"] = v(r, "articleUrl")
        if v(r, "description") and not out["description"]:
            out["description"] = v(r, "description")
    return out


# ── Formation SVG builder ──────────────────────────────────────────────────────

def formation_svg(team_name, tactic_str, starters, colour, annotations):
    """Green-pitch SVG with player circles, shirt numbers, and event annotations."""
    bg = colour["bg"]; txt = colour["text"]

    try:
        parts = [int(x) for x in tactic_str.split("-") if x.strip().isdigit()]
    except Exception:
        parts = [4, 3, 3]
    lines = [1] + parts

    gk = [p for p in starters if v(p, "shirtNumber", "99") == "1"]
    outfield = sorted(
        [p for p in starters if v(p, "shirtNumber", "99") != "1"],
        key=lambda p: int(v(p, "shirtNumber", "99"))
    )
    if not gk and starters:
        gk = [starters[-1]]; outfield = starters[:-1]
    sorted_starters = gk + outfield

    n_lines = len(lines)
    y_gk = 480; y_top = 130
    y_positions = []
    for i in range(n_lines):
        y_positions.append(y_gk if n_lines == 1
                           else y_gk - round(i * (y_gk - y_top) / (n_lines - 1)))

    player_slots = []
    idx = 0
    # Inward margin per count: fewer players → more central, more players → full width
    _MARGINS = {1: 0, 2: 65, 3: 30, 4: 10, 5: 0}
    for li, (count, y) in enumerate(zip(lines, y_positions)):
        line_players = sorted_starters[idx: idx + count]
        idx += count
        margin = _MARGINS.get(count, 0)
        left = 40 + margin
        right = 300 - margin
        if count == 1:
            xs = [170]
        else:
            xs = [round(left + j * (right - left) / (count - 1)) for j in range(count)]
        for player, cx in zip(line_players, xs):
            player_slots.append((player, cx, y))

    circles = []
    for player, cx, cy in player_slots:
        pid   = v(player, "playerId", "")
        shirt = v(player, "shirtNumber", "?")
        name_full = v(player, "playerName", "?")
        parts_name = name_full.split()
        short = parts_name[-1][:10].upper() if parts_name else name_full[:10]
        ann = annotations.get(pid, [])
        ann_str = " ".join(ann)
        label = f"{short}{' ' + ann_str if ann_str else ''}"
        href = f"https://demo.openlinksw.com/describe/?url={quote_plus('http://demo.openlinksw.com/fifa-kg#player-' + pid)}"
        g = (f'<a href="{href}" target="_blank" rel="noopener noreferrer">'
             f'<g style="cursor:pointer">'
             f'<circle cx="{cx}" cy="{cy}" r="14" fill="{bg}" stroke="white" stroke-width="1.5" opacity=".92"/>'
             f'<text x="{cx}" y="{cy+4}" text-anchor="middle" dominant-baseline="middle" '
             f'fill="{txt}" font-family="Helvetica Neue,sans-serif" font-size="9" font-weight="700">{shirt}</text>'
             f'<text x="{cx}" y="{cy+24}" text-anchor="middle" fill="rgba(255,255,255,0.85)" '
             f'font-family="Helvetica Neue,sans-serif" font-size="7">{label[:14]}</text>'
             f'</g></a>')
        circles.append(g)

    return f"""<svg viewBox="0 0 340 530" xmlns="http://www.w3.org/2000/svg" style="width:100%;background:#1e4d1e;border-radius:8px;border:1px solid rgba(255,255,255,0.1);">
        <rect width="340" height="530" fill="#1e4d1e" rx="8"/>
        <line x1="20" y1="265" x2="320" y2="265" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>
        <rect x="20" y="20" width="300" height="490" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/>
        <rect x="90" y="20" width="160" height="55" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="1"/>
        <rect x="115" y="20" width="110" height="25" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="1"/>
        <rect x="90" y="455" width="160" height="55" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="1"/>
        <rect x="115" y="505" width="110" height="25" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="1"/>
        <circle cx="170" cy="265" r="50" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="1"/>
        {"".join(circles)}
      </svg>"""


def build_player_annotations(goals, bookings, subs, team_name):
    ann = {}
    for g in goals:
        if v(g, "teamName") == team_name:
            pid = v(g, "playerId")
            if pid:
                gt = v(g, "goalType", "")
                sym = "OG" if "Own" in gt else f"⚽{v(g,'minute','?')}'"
                ann.setdefault(pid, []).append(sym)
    for b in bookings:
        if v(b, "teamName") == team_name:
            pid = v(b, "playerId")
            if pid:
                card = v(b, "cardLabel", "")
                sym = f"{'🟥' if 'Red' in card else '🟨'}{v(b,'minute','?')}'"
                ann.setdefault(pid, []).append(sym)
    for s in subs:
        if v(s, "teamName") == team_name:
            onid = v(s, "playerOnId"); offid = v(s, "playerOffId")
            m = v(s, "minute", "?")
            if onid: ann.setdefault(onid, []).append(f"↑{m}'")
            if offid: ann.setdefault(offid, []).append(f"↓{m}'")
    return ann


# ── Goal pitch diagram ─────────────────────────────────────────────────────────

def goal_pitch_svg(goals, home_team, away_team, hbg, abg):
    pitch = """<svg viewBox="0 0 800 520" xmlns="http://www.w3.org/2000/svg" style="width:100%;display:block;">
      <rect width="800" height="520" fill="#2A5A2A" rx="6"/>
      <rect x="40" y="20" width="720" height="480" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
      <line x1="400" y1="20" x2="400" y2="500" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
      <circle cx="400" cy="260" r="60" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
      <circle cx="400" cy="260" r="4" fill="rgba(255,255,255,0.5)"/>
      <rect x="40" y="160" width="132" height="200" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
      <rect x="40" y="205" width="55" height="110" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
      <rect x="628" y="160" width="132" height="200" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
      <rect x="705" y="205" width="55" height="110" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
      <rect x="30" y="225" width="10" height="70" fill="rgba(255,255,255,0.15)" stroke="rgba(255,255,255,0.5)" stroke-width="1"/>
      <rect x="760" y="225" width="10" height="70" fill="rgba(255,255,255,0.15)" stroke="rgba(255,255,255,0.5)" stroke-width="1"/>"""

    home_positions = [(710, 230), (680, 260), (695, 245), (720, 270), (660, 255)]
    away_positions = [(110, 260), (130, 245), (120, 270), (95, 250), (140, 265)]
    h_idx = 0; a_idx = 0
    elements = []

    for g in goals:
        min2  = v(g, "minute", "?")
        pname = v(g, "playerName", "?")
        pid   = v(g, "playerId", "")
        tname = v(g, "teamName", "")
        gt    = v(g, "goalType", "")
        is_og   = "Own" in gt
        is_home = (tname == home_team and not is_og) or (tname == away_team and is_og)
        colour  = "#BFA060" if is_og else (hbg if is_home else abg)

        if is_home and h_idx < len(home_positions):
            cx, cy = home_positions[h_idx]; h_idx += 1
        elif not is_home and a_idx < len(away_positions):
            cx, cy = away_positions[a_idx]; a_idx += 1
        else:
            continue

        short = pname.split()[-1][:8] if pname.split() else pname[:8]
        label = f"{short} {'OG' if is_og else '⚽'}"
        href  = (f"https://demo.openlinksw.com/describe/?url={quote_plus('http://demo.openlinksw.com/fifa-kg#player-' + pid)}"
                 if pid else "#")
        elements.append(f"""      <a href="{href}" target="_blank" rel="noopener noreferrer">
        <circle cx="{cx}" cy="{cy}" r="15" fill="{colour}" opacity="0.95"/><title>{pname} {min2}' — {'Own Goal' if is_og else 'Goal'}</title>
      </a>
      <text x="{cx}" y="{cy+4}" text-anchor="middle" fill="white" font-size="10" font-weight="700">{min2}'</text>
      <text x="{cx}" y="{cy-20}" text-anchor="middle" fill="white" font-size="8">{label}</text>""")

    elements.append(f'      <text x="200" y="50" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="11" letter-spacing="2">{home_team.upper()} →</text>')
    elements.append(f'      <text x="600" y="50" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="11" letter-spacing="2">← {away_team.upper()}</text>')
    elements.append("    </svg>")
    return pitch + "\n" + "\n".join(elements)


# ── Pressing section ───────────────────────────────────────────────────────────

def gauge(label, score, max_score, colour):
    try:    pct = min(100, round(float(score) / max_score * 100))
    except: pct = 0
    try:    display = f"{float(score):.2f}"
    except: display = str(score)
    return f"""      <div class="press-gauge-wrap">
        <div class="press-gauge-label">{label} (score: {display} / {max_score})</div>
        <div class="press-gauge-track"><div class="press-gauge-fill" style="width:{pct}%;background:linear-gradient(90deg,{colour});"></div></div>
      </div>"""


def pressing_section(home, away, hd, ad, hbg, abg, goals):
    h_cp = v(hd, "counterPress", "0"); a_cp = v(ad, "counterPress", "0")
    h_hp = v(hd, "highPress",    "0"); a_hp = v(ad, "highPress",    "0")
    h_mb = v(hd, "midBlock",     "0"); a_mb = v(ad, "midBlock",     "0")
    h_lb = v(hd, "lowBlock",     "0"); a_lb = v(ad, "lowBlock",     "0")
    h_ft = v(hd, "finalThird",   "0")

    def press_tag(cp, hp):
        try:   cp_f = float(cp); hp_f = float(hp)
        except: return "—"
        if cp_f > 14:  return "Elite Counter-Press"
        if cp_f > 10:  return "High Counter-Press"
        if hp_f > 10:  return "High Press"
        if hp_f > 5:   return "Mid Press"
        return "Deep Block / Low Block"

    goal_markers = ""
    for g in goals:
        try:
            gm = int(v(g, "minute", "0"))
            px = 40 + round(gm / 95 * 700)
            colour = hbg if v(g, "teamName", "") == home else abg
            goal_markers += f'\n      <line x1="{px}" y1="10" x2="{px}" y2="160" stroke="{colour}" stroke-width="1.2" stroke-dasharray="3,3" opacity="0.7"/>'
            goal_markers += f'\n      <text x="{px+4}" y="25" fill="{colour}" font-size="8">⚽{gm}\'</text>'
        except Exception:
            pass

    try:
        mb_f = float(h_mb); lb_f = float(h_lb); hp_f = float(h_hp); cp_f = float(h_cp)
        mb_pts = [mb_f*0.8, mb_f*0.95, mb_f, mb_f*0.98, mb_f*0.92, mb_f*0.85]
        lb_pts = [lb_f*0.9, lb_f,      lb_f*0.98, lb_f*0.95, lb_f*0.90, lb_f*0.85]
        hp_pts = [hp_f*1.1, hp_f,      hp_f*0.95, hp_f*0.9,  hp_f*0.85, hp_f*0.80]
        MAX = 55.0
        def to_y(val): return max(10, min(160, int(160 - val / MAX * 150)))
        xs = [40, 182, 324, 466, 608, 740]
        def polyline(pts): return " ".join(f"{xs[i]},{to_y(pts[i])}" for i in range(len(xs)))
        chart_lines = (
            f'<polyline points="{polyline(mb_pts)}" fill="none" stroke="{hbg}" stroke-width="2.5" stroke-linejoin="round"/>'
            f'<polyline points="{polyline(lb_pts)}" fill="none" stroke="{hbg}" stroke-width="1.5" stroke-linejoin="round" stroke-dasharray="6,3" opacity="0.7"/>'
            f'<polyline points="{polyline(hp_pts)}" fill="none" stroke="rgba(255,255,255,0.35)" stroke-width="1" stroke-linejoin="round"/>'
        )
    except Exception:
        chart_lines = ""

    return f"""<!-- Pressing Intelligence -->
<section id="pressing" class="reveal">
  <div class="section-eyebrow">Temporal Analytics</div>
  <div class="section-title">Pressing Intelligence &amp; Performance Rates</div>
  <div class="section-rule"></div>
  <div class="highlight-block">
    These metrics are sourced from <strong>temporal team analytics reports</strong> generated at intervals throughout the match. Comparing early-match and late-match snapshots reveals how each team's intensity and tactical shape evolved.
  </div>
  <div class="cards-2" style="margin-top:32px;margin-bottom:32px;">
    <div class="card">
      <div class="card-title">{home} — Pressing Profile</div>
{gauge("Counter-Press Intensity", h_cp, 20, f"{hbg},{hbg}88")}
{gauge("High Press", h_hp, 20, f"{hbg},{hbg}88")}
{gauge("Mid Block", h_mb, 50, f"{hbg}88,{hbg}44")}
{gauge("Low Block", h_lb, 50, f"{hbg}44,{hbg}22")}
      <div style="margin-top:12px;">
        <span class="press-tag" style="background:{hbg}22;color:{hbg};border:1px solid {hbg}44;">{press_tag(h_cp, h_hp)}</span>
      </div>
    </div>
    <div class="card">
      <div class="card-title">{away} — Pressing Profile</div>
{gauge("Counter-Press Intensity", a_cp, 20, f"{abg},{abg}88")}
{gauge("High Press", a_hp, 20, f"{abg},{abg}88")}
{gauge("Mid Block", a_mb, 50, f"{abg}88,{abg}44")}
{gauge("Low Block", a_lb, 50, f"{abg}44,{abg}22")}
      <div style="margin-top:12px;">
        <span class="press-tag" style="background:{abg}22;color:{abg};border:1px solid {abg}44;">{press_tag(a_cp, a_hp)}</span>
      </div>
    </div>
  </div>
  <div class="temporal-chart">
    <div style="font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:{hbg};margin-bottom:16px;">{home} Phase Intensity Over Match Time</div>
    <svg viewBox="0 0 760 210" xmlns="http://www.w3.org/2000/svg" style="width:100%;display:block;">
      <line x1="40" y1="10" x2="40" y2="160" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
      <line x1="40" y1="160" x2="740" y2="160" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
      <line x1="40" y1="55" x2="740" y2="55" stroke="rgba(255,255,255,0.05)" stroke-width="0.5" stroke-dasharray="4,4"/>
      <line x1="40" y1="100" x2="740" y2="100" stroke="rgba(255,255,255,0.05)" stroke-width="0.5" stroke-dasharray="4,4"/>
      <text x="40" y="175" text-anchor="middle" fill="rgba(255,255,255,0.3)" font-size="8">0'</text>
      <text x="182" y="175" text-anchor="middle" fill="rgba(255,255,255,0.3)" font-size="8">15'</text>
      <text x="324" y="175" text-anchor="middle" fill="rgba(255,255,255,0.3)" font-size="8">30'</text>
      <text x="466" y="175" text-anchor="middle" fill="rgba(255,255,255,0.3)" font-size="8">45'</text>
      <text x="608" y="175" text-anchor="middle" fill="rgba(255,255,255,0.3)" font-size="8">60'</text>
      <text x="740" y="175" text-anchor="middle" fill="rgba(255,255,255,0.3)" font-size="8">90'</text>
      {chart_lines}{goal_markers}
      <line x1="50" y1="195" x2="80" y2="195" stroke="{hbg}" stroke-width="2.5"/>
      <text x="85" y="198" fill="rgba(255,255,255,0.6)" font-size="8">Mid Block</text>
      <line x1="170" y1="195" x2="200" y2="195" stroke="{hbg}" stroke-width="1.5" stroke-dasharray="6,3" opacity="0.7"/>
      <text x="205" y="198" fill="rgba(255,255,255,0.6)" font-size="8">Low Block</text>
      <line x1="290" y1="195" x2="320" y2="195" stroke="rgba(255,255,255,0.35)" stroke-width="1"/>
      <text x="325" y="198" fill="rgba(255,255,255,0.6)" font-size="8">High Press</text>
    </svg>
    <div style="font-size:11px;color:var(--muted);margin-top:8px;text-align:center;">Phase aggregate values interpolated from temporal analytics snapshots · Goal events shown as vertical markers</div>
  </div>
</section>"""


# ── CSS ────────────────────────────────────────────────────────────────────────

CSS = """
:root{--ink:#FFFFFF;--muted:rgba(255,255,255,0.60);--faint:rgba(255,255,255,0.28);--bg:#060810;--panel:#0C0F1A;--panel-mid:#111629;--panel-str:#171D38;--navy:#0A1628;--navy-mid:#122040;--navy-bright:#1A3264;--line:rgba(255,255,255,0.10);--line-str:rgba(255,255,255,0.18);--shadow:0 8px 40px rgba(0,0,0,0.7);--r:8px;--r-lg:14px;}
[data-theme="light"]{--ink:#0A0E1A;--muted:rgba(0,0,0,0.60);--faint:rgba(0,0,0,0.28);--bg:#F4F6FB;--panel:#FFFFFF;--panel-mid:#EEF1F8;--panel-str:#E4E8F2;--navy:#1A3264;--navy-mid:#1A3264;--navy-bright:#1A3264;--line:rgba(0,0,0,0.10);--line-str:rgba(0,0,0,0.18);}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box;}html{scroll-behavior:smooth;}
body{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink);overflow-x:hidden;line-height:1.6;}
a{color:inherit;text-decoration:none;}a.entity-link{text-decoration:underline;text-underline-offset:3px;transition:color .2s;}
#fnav{position:fixed;top:24px;right:24px;z-index:1000;width:220px;background:rgba(10,22,40,0.88);backdrop-filter:blur(20px);border-radius:var(--r);box-shadow:6px 6px 18px rgba(0,0,0,0.6),-3px -3px 10px rgba(255,255,255,0.03);}
#fnav-header{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;cursor:grab;box-shadow:0 2px 6px rgba(0,0,0,0.3);}
#fnav-title{font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;}
#fnav-toggle,#fnav-theme{background:none;border:none;color:var(--muted);border-radius:4px;width:22px;height:22px;font-size:14px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .2s;}
#fnav-toggle:hover,#fnav-theme:hover{background:var(--panel-str);color:var(--ink);}
#fnav-links{padding:8px 0;overflow:hidden;max-height:600px;transition:max-height .35s cubic-bezier(0.16,1,0.3,1);}
#fnav-links.collapsed{max-height:0;}
#fnav-links a{display:block;padding:6px 14px;font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);transition:color .2s,background .2s;}
#fnav-links a:hover{color:var(--ink);background:var(--panel-str);}
#hero{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:80px 40px 60px;text-align:center;position:relative;overflow:hidden;}
#hero::before{content:'';position:absolute;top:-200px;left:-200px;width:700px;height:700px;background:radial-gradient(circle,rgba(116,172,223,0.07),transparent 70%);pointer-events:none;}
.hero-eyebrow{font-size:11px;font-weight:700;letter-spacing:4px;text-transform:uppercase;margin-bottom:28px;}
.hero-scoreline{display:flex;align-items:center;gap:0;margin-bottom:40px;flex-wrap:wrap;justify-content:center;}
.hero-team{display:flex;flex-direction:column;align-items:center;gap:12px;min-width:200px;}
.hero-team-name{font-size:13px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--muted);}
.hero-team-score{font-size:clamp(72px,14vw,120px);font-weight:900;line-height:1;color:var(--ink);}
.hero-divider{font-size:clamp(32px,6vw,56px);font-weight:300;color:var(--faint);padding:0 24px;align-self:flex-end;padding-bottom:16px;}
.hero-meta{display:flex;flex-direction:column;align-items:center;gap:6px;padding:20px 40px;border-radius:var(--r);background:rgba(255,255,255,0.03);box-shadow:inset 2px 2px 8px rgba(0,0,0,0.4),inset -1px -1px 6px rgba(255,255,255,0.02);margin-bottom:40px;}
.hero-meta-row{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);}
.hero-meta-row strong{color:var(--ink);font-weight:600;}
section{padding:100px 60px;max-width:1400px;margin:0 auto;}
@media(max-width:900px){section{padding:60px 24px;}}
.section-eyebrow{font-size:10px;font-weight:700;letter-spacing:4px;text-transform:uppercase;margin-bottom:12px;}
.section-title{font-size:clamp(26px,4vw,44px);font-weight:900;line-height:1.1;margin-bottom:16px;letter-spacing:-0.5px;}
.section-rule{width:60px;height:2px;margin-bottom:48px;}
.cards-2{display:grid;grid-template-columns:1fr 1fr;gap:24px;}
.cards-4{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;}
@media(max-width:1100px){.cards-4{grid-template-columns:repeat(2,1fr);}}
@media(max-width:800px){.cards-2,.cards-4{grid-template-columns:1fr;}}
.card{background:var(--panel);border-radius:var(--r-lg);padding:28px;box-shadow:5px 5px 14px rgba(0,0,0,0.55),-3px -3px 10px rgba(255,255,255,0.03);transition:box-shadow .3s,transform .3s;}
.card:hover{box-shadow:8px 8px 20px rgba(0,0,0,0.65),-5px -5px 14px rgba(255,255,255,0.04);transform:translateY(-3px);}
.card-title{font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;margin-bottom:20px;}
.stat-row{display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid var(--line);font-size:13px;}
.stat-row:last-child{border-bottom:none;}
.stat-key{color:var(--muted);}
.stat-val{font-weight:700;font-size:15px;}
.compare-block{margin-bottom:20px;}
.compare-header{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;font-size:12px;font-weight:500;letter-spacing:1px;text-transform:uppercase;color:var(--muted);}
.compare-track{height:6px;background:var(--panel-str);border-radius:3px;overflow:hidden;display:flex;}
.bar-h{border-radius:3px 0 0 3px;}
.bar-a{border-radius:0 3px 3px 0;}
.pitch-wrapper{background:#1A3A1A;border-radius:var(--r-lg);padding:20px;margin-bottom:40px;box-shadow:3px 3px 12px rgba(0,0,0,0.5),-2px -2px 8px rgba(255,255,255,0.02);}
.pitch-caption{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-top:12px;text-align:center;}
.timeline{position:relative;padding-left:32px;}
.timeline::before{content:'';position:absolute;left:11px;top:0;bottom:0;width:2px;background:var(--line);}
.tl-item{position:relative;margin-bottom:28px;display:flex;gap:20px;align-items:flex-start;}
.tl-dot{position:absolute;left:-26px;top:4px;width:14px;height:14px;border-radius:50%;border:2px solid var(--line);background:var(--bg);}
.tl-dot.card-yellow{background:#F5C518;border-color:#F5C518;}
.tl-dot.card-red{background:#CC0000;border-color:#CC0000;}
.tl-dot.sub-dot{background:#22BB66;border-color:#22BB66;}
.tl-min{font-size:12px;font-weight:700;width:36px;flex-shrink:0;padding-top:2px;}
.tl-event{font-size:13px;font-weight:600;margin-bottom:2px;}
.tl-detail{font-size:12px;color:var(--muted);}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;}
.badge-yellow{background:#F5C518;color:#000;}
.badge-sub{background:#22BB66;color:#000;}
.badge-navy{background:var(--navy-bright);color:#fff;}
.badge-og{background:#BFA060;color:#000;}
.player-table{width:100%;border-collapse:collapse;font-size:13px;}
.player-table th{text-align:left;padding:10px 14px;font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--line-str);}
.player-table td{padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:middle;}
.player-table tr:last-child td{border-bottom:none;}
.player-table tr:hover td{background:rgba(255,255,255,0.03);}
.player-table td.num{font-weight:700;}
.phase-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:8px;}
@media(max-width:800px){.phase-grid{grid-template-columns:repeat(2,1fr);}}
.phase-chip{background:var(--panel-mid);border-radius:var(--r);padding:14px;text-align:center;box-shadow:3px 3px 8px rgba(0,0,0,0.5),-1px -1px 5px rgba(255,255,255,0.02);}
.phase-chip .p-label{font-size:10px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;}
.phase-chip .p-h{font-size:20px;font-weight:900;}
.highlight-block{padding:20px 28px;border-radius:var(--r);margin:32px 0;font-size:17px;font-weight:500;line-height:1.5;box-shadow:inset 2px 0 8px rgba(0,0,0,0.2),3px 3px 10px rgba(0,0,0,0.4);}
.sparql-block{background:var(--panel);border-radius:var(--r-lg);padding:28px;margin-bottom:24px;box-shadow:4px 4px 12px rgba(0,0,0,0.5),-2px -2px 8px rgba(255,255,255,0.02);}
.sparql-block pre{background:var(--panel-str);border-radius:var(--r);padding:20px;font-size:12px;color:rgba(255,255,255,0.85);overflow-x:auto;line-height:1.7;font-family:'Courier New',monospace;white-space:pre;box-shadow:inset 2px 2px 8px rgba(0,0,0,0.4);}
footer{background:var(--navy);padding:60px;font-size:12px;color:var(--muted);box-shadow:0 -4px 16px rgba(0,0,0,0.5);}
@media(max-width:700px){footer{padding:40px 24px;}}
.attribution-panel{margin-bottom:40px;}
.attribution-panel h2{font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin-bottom:24px;opacity:0.6;}
.attribution-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;}
@media(max-width:900px){.attribution-grid{grid-template-columns:repeat(2,1fr);}}
@media(max-width:600px){.attribution-grid{grid-template-columns:1fr;}}
.attribution-card{background:var(--panel);border-radius:var(--r);padding:18px 20px;box-shadow:3px 3px 8px rgba(0,0,0,0.5),-1px -1px 5px rgba(255,255,255,0.02);}
.attribution-card.wide{grid-column:span 2;}
@media(max-width:900px){.attribution-card.wide{grid-column:span 1;}}
.attribution-label{display:block;font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:10px;opacity:0.7;}
.attribution-card p,.attribution-card li{margin-bottom:6px;line-height:1.7;font-size:11px;}
.attribution-card ul{list-style:none;}
.attribution-card code{font-size:10px;background:var(--panel-str);padding:2px 6px;border-radius:3px;word-break:break-all;}
.attribution-links{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;}
.attribution-pill{display:inline-block;padding:5px 10px;font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;background:var(--panel-str);border-radius:var(--r);text-decoration:none;color:var(--muted);transition:color .2s;}
.attribution-pill:hover{color:var(--accent);}
.reveal{opacity:0;transform:translateY(28px);transition:opacity .7s cubic-bezier(0.16,1,0.3,1),transform .7s cubic-bezier(0.16,1,0.3,1);}
.reveal.visible{opacity:1;transform:none;}
details summary{cursor:pointer;list-style:none;display:flex;justify-content:space-between;align-items:center;}
details summary::-webkit-details-marker{display:none;}
details summary::after{content:'＋';font-size:16px;}
details[open] summary::after{content:'－';}
.sparql-block details{background:var(--panel-str);border-radius:var(--r);padding:16px 20px;margin-top:16px;}
.sparql-block details summary{font-size:12px;font-weight:700;letter-spacing:1px;color:var(--muted);text-transform:uppercase;}
.sparql-block details[open] summary{margin-bottom:12px;}
.sparql-live-link{display:inline-block;margin-top:14px;padding:10px 20px;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--ink);background:var(--panel-str);border-radius:var(--r);text-decoration:none;box-shadow:3px 3px 8px rgba(0,0,0,0.5),-2px -2px 6px rgba(255,255,255,0.02);transition:all .2s;}
.sparql-live-link:hover{transform:translateY(-1px);}
.formation-grid{display:grid;grid-template-columns:1fr 1fr;gap:32px;}
@media(max-width:800px){.formation-grid{grid-template-columns:1fr;}}
.formation-tactic{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:8px;}
.formation-tactic strong{color:var(--ink);font-size:13px;}
.press-gauge-wrap{margin-bottom:20px;}
.press-gauge-label{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:8px;}
.press-gauge-track{height:8px;background:var(--panel-str);border-radius:4px;position:relative;overflow:hidden;}
.press-gauge-fill{height:100%;border-radius:4px;transition:width .8s cubic-bezier(0.16,1,0.3,1);}
.press-tag{display:inline-block;padding:4px 12px;border-radius:12px;font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-top:8px;}
.temporal-chart{background:var(--panel-mid);border-radius:var(--r-lg);padding:20px;margin-bottom:24px;box-shadow:3px 3px 10px rgba(0,0,0,0.5);}
.kg-graph-tabs{display:flex;gap:8px;margin-bottom:4px;}
.kg-tab{background:var(--panel-str);border:1px solid var(--line-str);border-radius:var(--r);padding:6px 16px;cursor:pointer;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--muted);transition:all .2s;}
.kg-tab.active{background:var(--accent);color:var(--accent-text);border-color:var(--accent);}
"""

JS = """
(function(){
  var nav=document.getElementById('fnav'),hdr=document.getElementById('fnav-header');
  var links=document.getElementById('fnav-links'),tog=document.getElementById('fnav-toggle');
  var thm=document.getElementById('fnav-theme');
  var dragging=false,ox=0,oy=0,sx=0,sy=0,collapsed=false;
  try{collapsed=localStorage.getItem('fnav-collapsed')==='1';}catch(e){}
  if(collapsed){links.classList.add('collapsed');tog.textContent='+';}
  hdr.addEventListener('mousedown',function(e){
    if(e.target===tog||e.target===thm)return;
    dragging=true;ox=e.clientX;oy=e.clientY;
    var r=nav.getBoundingClientRect();sx=r.left;sy=r.top;nav.style.right='auto';
    document.addEventListener('mousemove',mv);document.addEventListener('mouseup',mu);
  });
  function mv(e){if(!dragging)return;nav.style.left=(sx+e.clientX-ox)+'px';nav.style.top=(sy+e.clientY-oy)+'px';}
  function mu(){dragging=false;document.removeEventListener('mousemove',mv);document.removeEventListener('mouseup',mu);}
  tog.addEventListener('click',function(){
    collapsed=!collapsed;links.classList.toggle('collapsed',collapsed);tog.textContent=collapsed?'+':'−';
    try{localStorage.setItem('fnav-collapsed',collapsed?'1':'0');}catch(e){}
  });
  thm.addEventListener('click',function(){
    var d=document.documentElement;
    d.setAttribute('data-theme',d.getAttribute('data-theme')==='light'?'dark':'light');
  });
  var io=new IntersectionObserver(function(e){e.forEach(function(x){if(x.isIntersecting)x.target.classList.add('visible');});},{threshold:0.12});
  document.querySelectorAll('.reveal').forEach(function(el){io.observe(el);});
})();

(function(){
  var tip=document.createElement('div');
  tip.style.cssText='position:fixed;background:rgba(10,10,10,.92);color:#fff;font-size:11px;'
    +'font-weight:600;padding:6px 13px;border-radius:7px;pointer-events:none;'
    +'opacity:0;transition:opacity .12s ease;z-index:99999;white-space:nowrap;'
    +'box-shadow:0 3px 12px rgba(0,0,0,.6);letter-spacing:.3px;';
  document.body.appendChild(tip);
  var mx=0,my=0;
  document.addEventListener('mousemove',function(e){mx=e.clientX;my=e.clientY;});
  function show(msg){tip.textContent=msg;tip.style.opacity='1';moveTip();}
  function hide(){tip.style.opacity='0';}
  function moveTip(){
    var vw=window.innerWidth,vh=window.innerHeight;
    var tw=tip.offsetWidth||160,th=tip.offsetHeight||28;
    var x=mx+14,y=my-th-10;
    if(x+tw>vw-6)x=mx-tw-14;if(y<6)y=my+20;
    tip.style.left=x+'px';tip.style.top=y+'px';
  }
  function wire(el,href){
    el.addEventListener('mouseenter',function(){show('Click to copy link to here');});
    el.addEventListener('mousemove',moveTip);
    el.addEventListener('mouseleave',hide);
    el.addEventListener('click',function(e){
      e.preventDefault();
      var url=location.href.split('#')[0]+href;
      function done(){show('✓ Copied!');setTimeout(hide,1600);}
      try{
        if(navigator.clipboard&&window.isSecureContext){
          navigator.clipboard.writeText(url).then(done).catch(function(){fallback(url);done();});
        }else{fallback(url);done();}
      }catch(ex){fallback(url);done();}
    });
  }
  function fallback(url){
    try{var t=document.createElement('textarea');t.value=url;
      t.style.cssText='position:fixed;top:-9999px;left:-9999px;';
      document.body.appendChild(t);t.focus();t.select();
      document.execCommand('copy');document.body.removeChild(t);}catch(e){}
  }
  document.querySelectorAll('.section-title').forEach(function(el){
    var s=el.closest('section[id]');if(s)wire(el,'#'+s.id);
  });
  var seen={};
  document.querySelectorAll('.card-title').forEach(function(el){
    var base=el.textContent.trim().toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
    if(!base)return;
    var slug=base,n=1;
    while(document.getElementById(slug)||seen[slug]){slug=base+'-'+(++n);}
    seen[slug]=1;el.id=slug;wire(el,'#'+slug);
  });
})();

// Explore KG using SPARQL — canonical SAMPLE-based entity-type summary query
// Pre-encoded query body per rdf-infographic-skill contract:
//   Q_PRE + encodeURIComponent(graphIri) + Q_POST
// Decoded query:
//   PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
//   PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
//   SELECT ?type (SAMPLE(?s) AS ?sampleEntity) (SAMPLE(?label) AS ?sampleLabel) (COUNT(?s) AS ?entityCount)
//   WHERE { GRAPH <graphIri> { ?s rdf:type ?type . OPTIONAL { ?s rdfs:label ?label } } }
//   GROUP BY ?type ORDER BY DESC(?entityCount)
var Q_PRE  = 'PREFIX+rdf%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23%3E%0APREFIX+rdfs%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F2000%2F01%2Frdf-schema%23%3E%0A%0ASELECT%0A++++%3Ftype%0A++++%28SAMPLE%28%3Fs%29+AS+%3FsampleEntity%29%0A++++%28SAMPLE%28%3Flabel%29+AS+%3FsampleLabel%29%0A++++%28COUNT%28%3Fs%29+AS+%3FentityCount%29%0AWHERE+%7B%0A++++GRAPH+%3C';
var Q_POST = '%3E+%7B%0A++++++++%3Fs+rdf%3Atype+%3Ftype+.%0A%0A++++++++OPTIONAL+%7B%0A++++++++++++%3Fs+rdfs%3Alabel+%3Flabel%0A++++++++%7D%0A++++%7D%0A%7D%0AGROUP+BY+%3Ftype%0AORDER+BY+DESC%28%3FentityCount%29';

function setKgGraph(graph) {
  document.getElementById('tabMain').classList.toggle('active', graph === 'main');
  document.getElementById('tabAnalytics').classList.toggle('active', graph === 'analytics');
  var graphIri = graph === 'analytics'
    ? 'urn:worldcup:kg:2026:analytics'
    : 'urn:worldcup:kg:2026';
  // Update live-query href
  document.getElementById('sparqlBtn').href =
    'https://demo.openlinksw.com/sparql?query=' + Q_PRE + encodeURIComponent(graphIri) + Q_POST
    + '&format=text%2Fx-html%2Btr&timeout=30&run=+Run+Query+';
  // Display decoded query text in the textarea
  document.getElementById('sparqlQueryText').value =
    'PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\\n'
    + 'PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\\n\\n'
    + 'SELECT\\n'
    + '    ?type\\n'
    + '    (SAMPLE(?s) AS ?sampleEntity)\\n'
    + '    (SAMPLE(?label) AS ?sampleLabel)\\n'
    + '    (COUNT(?s) AS ?entityCount)\\n'
    + 'WHERE {\\n'
    + '    GRAPH <' + graphIri + '> {\\n'
    + '        ?s rdf:type ?type .\\n\\n'
    + '        OPTIONAL {\\n'
    + '            ?s rdfs:label ?label\\n'
    + '        }\\n'
    + '    }\\n'
    + '}\\n'
    + 'GROUP BY ?type\\n'
    + 'ORDER BY DESC(?entityCount)';
}
// Initialise on page load
(function(){ setKgGraph('main'); })();
"""


# ── Main HTML builder ──────────────────────────────────────────────────────────

def build_html(mid, ov, coaches, goals, bookings, subs, team_stats, players, squad, article):
    home  = v(ov, "homeTeam"); away  = v(ov, "awayTeam")
    htid  = v(ov, "homeTeamId"); atid = v(ov, "awayTeamId")
    hs    = v(ov, "homeScore", "0"); aws = v(ov, "awayScore", "0")
    date_raw = v(ov, "date", "")
    stadium  = v(ov, "stadium", ""); stad_id = v(ov, "stadiumId", "")
    attend   = v(ov, "attendance", "")
    group    = v(ov, "group", "")
    htac     = v(ov, "homeTactic", "4-4-2"); atac = v(ov, "awayTactic", "4-4-2")

    hc = _c(home); ac = _c(away)
    hbg = hc["bg"]; abg = ac["bg"]
    htxt = hc["text"]; atxt = ac["text"]
    habbr = hc["abbr"]; aabbr = ac["abbr"]

    home_coach = coaches.get(home, {}); away_coach = coaches.get(away, {})

    try:
        dt = datetime.fromisoformat(date_raw.replace("Z", ""))
        date_nice = dt.strftime("%-d %B %Y")
        time_utc  = dt.strftime("%H:%M UTC")
    except Exception:
        date_nice = date_raw[:10]; time_utc = ""

    hi = int(hs); ai = int(aws)
    if hi > ai:
        result_badge = f'<span class="badge" style="background:{hbg};color:{htxt};">{home} Win</span>'
    elif ai > hi:
        result_badge = f'<span class="badge" style="background:{abg};color:{atxt};">{away} Win</span>'
    else:
        result_badge = '<span class="badge badge-navy">Draw</span>'

    hd = team_stats.get(home, {}); ad = team_stats.get(away, {})

    def sf(d, k): return v(d, k, "—")
    def pct(d):
        try: return f"{float(v(d,'possession','0'))*100:.1f}%"
        except: return "—"

    h_poss_f = float(v(hd, "possession", "0.5")) * 100
    a_poss_f = float(v(ad, "possession", "0.5")) * 100

    def acc(d):
        try: return f"{float(v(d,'passesCompleted','0'))/float(v(d,'passes','1'))*100:.1f}%"
        except: return "—"

    h_ann = build_player_annotations(goals, bookings, subs, home)
    a_ann = build_player_annotations(goals, bookings, subs, away)

    team_players = players_by_team(players, squad)

    squad_lookup = {}
    for team_name, sq_list in squad.items():
        for sp in sq_list:
            pid = v(sp, "playerId", "")
            if pid: squad_lookup[pid] = sp

    def starters(team_name):
        tp = team_players.get(team_name, [])
        with_time = sorted(tp, key=lambda p: -float(v(p, "timePlayed", "0")))
        top11 = with_time[:11]
        enriched = []
        for p in top11:
            pid = v(p, "playerId", "")
            sq = squad_lookup.get(pid, {})
            merged = dict(p)
            if v(sq, "shirtNumber"):
                merged["shirtNumber"] = {"value": v(sq, "shirtNumber")}
            if v(sq, "posLabel"):
                merged["posLabel"] = {"value": v(sq, "posLabel")}
            if v(sq, "playerName") and not v(p, "playerName"):
                merged["playerName"] = {"value": v(sq, "playerName")}
            enriched.append(merged)
        return enriched

    h_starters = starters(home); a_starters = starters(away)
    h_form_svg = formation_svg(home, htac, h_starters, hc, h_ann)
    a_form_svg = formation_svg(away, atac, a_starters, ac, a_ann)
    pitch_svg  = goal_pitch_svg(goals, home, away, hbg, abg)

    # Timeline
    events = (
        [("goal",    int(v(g,"minute","0")), g) for g in goals] +
        [("booking", int(v(b,"minute","0")), b) for b in bookings] +
        [("sub",     int(v(s,"minute","0")), s) for s in subs]
    )
    events.sort(key=lambda x: x[1])

    tl_items = []
    for etype, minute, e in events:
        if etype == "goal":
            pid = v(e,"playerId",""); pname = v(e,"playerName","Unknown")
            tname = v(e,"teamName",""); gt = v(e,"goalType","")
            is_og = "Own" in gt
            is_home = (tname == home and not is_og) or (tname == away and is_og)
            clr = "#BFA060" if is_og else (hbg if is_home else abg)
            txt2 = "#000" if is_og else (htxt if is_home else atxt)
            pl = ent_link(pid, pname) if pid else pname
            ast = v(e, "assistName", ""); astid = v(e, "assistId", "")
            ast_txt = f" · Assist: {ent_link(astid, ast) if astid else ast}" if ast else ""
            tl_items.append(f"""    <div class="tl-item">
      <div class="tl-dot" style="background:{clr};border-color:{clr};"></div>
      <div class="tl-min" style="color:{hbg if is_home else abg};">{minute}'</div>
      <div>
        <div class="tl-event"><span class="badge" style="background:{clr};color:{txt2};">{'OG' if is_og else 'Goal'}</span> {pl}</div>
        <div class="tl-detail">{tname}{ast_txt}</div>
      </div>
    </div>""")
        elif etype == "booking":
            pid = v(e,"playerId",""); pname = v(e,"playerName","Unknown")
            tname = v(e,"teamName",""); card = v(e,"cardLabel","Yellow Card")
            is_red = "Red" in card
            pl = ent_link(pid, pname) if pid else pname
            tl_items.append(f"""    <div class="tl-item">
      <div class="tl-dot card-{'red' if is_red else 'yellow'}"></div>
      <div class="tl-min" style="color:{'#CC0000' if is_red else '#F5C518'};">{minute}'</div>
      <div>
        <div class="tl-event"><span class="badge badge-{'navy' if is_red else 'yellow'}">{card}</span> {pl}</div>
        <div class="tl-detail">{tname}</div>
      </div>
    </div>""")
        elif etype == "sub":
            on = v(e,"playerOnName",""); off = v(e,"playerOffName","")
            onid = v(e,"playerOnId",""); offid = v(e,"playerOffId","")
            tname = v(e,"teamName","")
            on_l  = ent_link(onid, on)  if onid and on  else on
            off_l = ent_link(offid, off) if offid and off else off
            tl_items.append(f"""    <div class="tl-item">
      <div class="tl-dot sub-dot"></div>
      <div class="tl-min" style="color:#22BB66;">{minute}'</div>
      <div>
        <div class="tl-event"><span class="badge badge-sub">Sub</span> {tname}</div>
        <div class="tl-detail">↑ {on_l} &nbsp;↓ {off_l}</div>
      </div>
    </div>""")

    timeline_html = "\n".join(tl_items) if tl_items else \
        '    <div style="color:var(--muted);padding:20px 0;">No key events recorded.</div>'

    # Goals breakdown
    def goal_items(team, is_home_side):
        gl = [g for g in goals if v(g,"teamName") == team and "Own" not in v(g,"goalType","")]
        if not gl:
            return '<div style="padding:20px 0;text-align:center;color:var(--muted);font-size:13px;">No goals scored</div>'
        colour = hbg if is_home_side else abg
        out = []
        for g in gl:
            pid = v(g,"playerId",""); pname = v(g,"playerName","Unknown")
            pl = ent_link(pid, pname) if pid else pname
            ast = v(g, "assistName", ""); astid = v(g, "assistId", "")
            ast_html = f' <small style="color:var(--muted);">Assist: {ent_link(astid,ast) if astid else ast}</small>' if ast else ""
            out.append(f"""      <div style="margin-bottom:16px;">
        <div class="tl-event"><span class="badge" style="background:{colour};color:white;">Goal</span>&nbsp;{pl}{ast_html}</div>
        <div class="tl-detail">{v(g,'minute','?')}' · {v(g,'goalType','Regular goal')}</div>
      </div>""")
        return "\n".join(out)

    og_goals = [g for g in goals if "Own" in v(g,"goalType","")]
    og_html = ""
    if og_goals:
        og_items = []
        for g in og_goals:
            pid = v(g,"playerId",""); pname = v(g,"playerName","Unknown")
            pl = ent_link(pid, pname) if pid else pname
            og_items.append(f"""      <div style="margin-bottom:16px;">
        <div class="tl-event"><span class="badge badge-og">OG</span>&nbsp;{pl}</div>
        <div class="tl-detail">{v(g,'minute','?')}' · Own Goal</div>
      </div>""")
        og_html = f"""  <div class="card" style="margin-top:24px;"><div class="card-title">Own Goals</div>
{"".join(og_items)}
  </div>"""

    # Stats comparison bars
    def bar(label, hval, aval, is_pct=False, dec=0):
        try:
            hf = float(hval); af = float(aval)
            tot = hf + af
            hw = int(round(hf/tot*100)) if tot else 50
            hd2 = f"{hf:.1f}%" if is_pct else fnum(hval, dec)
            ad2 = f"{af:.1f}%" if is_pct else fnum(aval, dec)
        except Exception:
            hw = 50; hd2 = str(hval); ad2 = str(aval)
        return f"""    <div class="compare-block">
      <div class="compare-header"><span>{habbr} {hd2}</span><span>{label}</span><span>{aabbr} {ad2}</span></div>
      <div class="compare-track"><div class="bar-h" style="width:{hw}%;background:var(--accent);"></div><div class="bar-a" style="width:{100-hw}%;background:var(--accent-dim);"></div></div>
    </div>"""

    comp_bars = "\n".join(filter(None, [
        bar("Possession", h_poss_f, a_poss_f, True),
        bar("Passes",          v(hd,"passes","0"),         v(ad,"passes","0")),
        bar("Shots",           v(hd,"shots","0"),           v(ad,"shots","0")),
        bar("Shots on Target", v(hd,"shotsOnTarget","0"),   v(ad,"shotsOnTarget","0")),
        bar("Def. Pressures",  v(hd,"defPress","0"),        v(ad,"defPress","0")),
        bar("Counter-Press",   v(hd,"counterPress","0"),    v(ad,"counterPress","0")),
    ]))

    # Phase chips
    def chip(label, val_str, colour):
        try:    disp = f"{float(val_str):.1f}"
        except: disp = val_str or "—"
        return f'      <div class="phase-chip"><div class="p-label">{label}</div><div class="p-h" style="color:{colour};">{disp}</div></div>'

    # Squad rows
    def squad_rows(team_name, player_list, g_data, b_data, s_data):
        ann = build_player_annotations(g_data, b_data, s_data, team_name)
        rows = []
        for r in player_list:
            pid = v(r,"playerId",""); pname = v(r,"playerName","?")
            shirt = v(r,"shirtNumber","?")
            ann_parts = ann.get(pid, [])
            ann_str = " · ".join(ann_parts)
            link = ent_link(pid, pname) if pid else pname
            ann_html = f' <small style="color:var(--muted);">{ann_str}</small>' if ann_str else ""
            colour_td = hbg if team_name == home else abg
            rows.append(f'          <tr><td class="num" style="color:{colour_td};">{shirt}</td><td>{link}{ann_html}</td></tr>')
        return "\n".join(rows) if rows else '<tr><td colspan="2" style="color:var(--muted);padding:20px;">Squad data unavailable</td></tr>'

    # Core player rows per team
    def core_rows(team_name):
        tp = team_players.get(team_name, [])
        top = [p for p in tp if float(v(p,"totalDistance","0")) > 100][:8]
        if not top:
            return '<tr><td colspan="6" style="color:var(--muted);padding:20px;">Analytics not available</td></tr>'
        colour = hbg if team_name == home else abg
        rows = []
        for r in top:
            pid = v(r,"playerId",""); pname = v(r,"playerName","?")
            dist = v(r,"totalDistance","0"); passes_v = v(r,"passes","—")
            sprints = v(r,"sprints","—"); spd = v(r,"topSpeed","")
            g_v = v(r,"goals","0"); a_v = v(r,"assists","0")
            yc_v = v(r,"yellowCards","0"); shots_v = v(r,"shots","0")
            try:    dist_str = f"{int(float(dist)):,}"
            except: dist_str = dist
            try:    spd_str = f"{float(spd):.1f}"
            except: spd_str = "—"
            hl = []
            if float(g_v)  > 0: hl.append(f'<span class="badge" style="background:{colour};color:white;font-size:9px;">⚽</span>')
            if float(a_v)  > 0: hl.append("🎯")
            if float(yc_v) > 0: hl.append('<span class="badge badge-yellow" style="font-size:9px;">YC</span>')
            hl_html = " ".join(hl)
            link = ent_link(pid, pname) if pid else pname
            rows.append(f'          <tr><td>{link}</td><td class="num" style="color:{colour};">{dist_str}</td><td>{passes_v}</td><td>{sprints}</td><td>{spd_str}</td><td style="color:var(--muted);font-size:11px;">{hl_html}</td></tr>')
        return "\n".join(rows)

    # Physical aggregate bars (team-level sums/max)
    def phys_agg(team_name, metric, aggregator="sum"):
        plist = team_players.get(team_name, [])
        vals = [float(v(p, metric, "0")) for p in plist if v(p, metric, "0") not in ("", "0", "—")]
        if not vals: return 0.0
        if aggregator == "max": return max(vals)
        if aggregator == "avg": return sum(vals) / len(vals)
        return sum(vals)

    h_tot_dist = phys_agg(home, "totalDistance", "sum")
    a_tot_dist = phys_agg(away, "totalDistance", "sum")
    h_tot_spr  = phys_agg(home, "sprints", "sum")
    a_tot_spr  = phys_agg(away, "sprints", "sum")
    h_max_spd  = phys_agg(home, "topSpeed", "max")
    a_max_spd  = phys_agg(away, "topSpeed", "max")
    h_avg_spd  = phys_agg(home, "topSpeed", "avg")
    a_avg_spd  = phys_agg(away, "topSpeed", "avg")

    phys_bars = "\n".join(filter(None, [
        bar("Total Distance (m)", h_tot_dist, a_tot_dist),
        bar("Total Sprints",      h_tot_spr,  a_tot_spr),
        bar("Max Top Speed (km/h)", h_max_spd, a_max_spd, dec=1),
        bar("Avg Top Speed (km/h)", h_avg_spd, a_avg_spd, dec=1),
    ]))

    # SPARQL live query strings
    overview_q = f"""PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX fifa-kg: <http://demo.openlinksw.com/fifa-kg#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?homeTeam ?awayTeam ?homeScore ?awayScore ?date ?stadium ?attendance
FROM <urn:worldcup:kg:2026>
WHERE {{
  BIND(fifa-kg:match-{mid} AS ?match)
  ?match fifa:homeTeam ?ht ; fifa:awayTeam ?at ;
         fifa:homeTeamScore ?homeScore ; fifa:awayTeamScore ?awayScore ;
         fifa:date ?date ; fifa:stadium ?s ; fifa:attendance ?attendance .
  ?ht rdfs:label ?homeTeam . ?at rdfs:label ?awayTeam . ?s rdfs:label ?stadium .
}}"""

    goals_q = f"""PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX fifa-kg: <http://demo.openlinksw.com/fifa-kg#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?minute ?playerName ?teamName ?goalType ?assistName
FROM <urn:worldcup:kg:2026>
WHERE {{
  fifa-kg:match-{mid} fifa:hasGoal ?goal .
  ?goal fifa:goalMinute ?minute .
  OPTIONAL {{ ?goal fifa:player ?p . ?p rdfs:label ?playerName }}
  OPTIONAL {{ ?goal fifa:team ?t . ?t rdfs:label ?teamName }}
  OPTIONAL {{ ?goal fifa:goalType ?gt . ?gt rdfs:label ?goalType }}
  OPTIONAL {{ ?goal fifa:assistPlayer ?a . ?a rdfs:label ?assistName }}
}}
ORDER BY ?minute"""

    players_q = f"""PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?playerName ?totalDistance ?sprints ?topSpeed ?timePlayed
FROM NAMED <urn:worldcup:kg:2026>
FROM NAMED <urn:worldcup:kg:2026:analytics>
WHERE {{
  GRAPH <urn:worldcup:kg:2026:analytics> {{
    ?report a fifa:PlayerMatchAnalyticsReport ;
            fifa:match <{MATCH_IRI_BASE}{mid}> ;
            fifa:player ?player ;
            fifa:generatedAt ?generatedAt .
    {{ SELECT ?player (MAX(?gen) AS ?generatedAt) WHERE {{
        GRAPH <urn:worldcup:kg:2026:analytics> {{
          ?r a fifa:PlayerMatchAnalyticsReport ;
             fifa:match <{MATCH_IRI_BASE}{mid}> ;
             fifa:player ?player ; fifa:generatedAt ?gen .
        }} }} GROUP BY ?player }}
    OPTIONAL {{ ?report fifa:totalDistance ?totalDistance }}
    OPTIONAL {{ ?report fifa:sprints ?sprints }}
    OPTIONAL {{ ?report fifa:topSpeed ?topSpeed }}
    OPTIONAL {{ ?report fifa:timePlayed ?timePlayed }}
  }}
  GRAPH <urn:worldcup:kg:2026> {{ ?player rdfs:label ?playerName }}
}}
ORDER BY DESC(?totalDistance)
LIMIT 22"""

    stats_q = f"""PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX fifa-kg: <http://demo.openlinksw.com/fifa-kg#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?teamName ?possession ?passes ?goals ?shots ?shotsOnTarget
       ?corners ?yellowCards ?offsides ?defPress ?highPress ?counterPress
FROM NAMED <urn:worldcup:kg:2026>
FROM NAMED <urn:worldcup:kg:2026:analytics>
WHERE {{
  GRAPH <urn:worldcup:kg:2026:analytics> {{
    ?report a fifa:TeamMatchAnalyticsReport ;
            fifa:match <{MATCH_IRI_BASE}{mid}> ;
            fifa:team ?team ;
            fifa:generatedAt ?generatedAt .
    {{ SELECT ?team (MAX(?gen) AS ?generatedAt) WHERE {{
        GRAPH <urn:worldcup:kg:2026:analytics> {{
          ?r a fifa:TeamMatchAnalyticsReport ;
             fifa:match <{MATCH_IRI_BASE}{mid}> ;
             fifa:team ?team ; fifa:generatedAt ?gen .
        }} }} GROUP BY ?team }}
    OPTIONAL {{ ?report fifa:possession ?possession }}
    OPTIONAL {{ ?report fifa:passes ?passes }}
    OPTIONAL {{ ?report fifa:goals ?goals }}
    OPTIONAL {{ ?report fifa:attemptAtGoal ?shots }}
    OPTIONAL {{ ?report fifa:attemptAtGoalOnTarget ?shotsOnTarget }}
    OPTIONAL {{ ?report fifa:corners ?corners }}
    OPTIONAL {{ ?report fifa:yellowCards ?yellowCards }}
    OPTIONAL {{ ?report fifa:offsides ?offsides }}
    OPTIONAL {{ ?report fifa:defensivePressuresApplied ?defPress }}
    OPTIONAL {{ ?report fifa:phaseAggregateHighPress ?highPress }}
    OPTIONAL {{ ?report fifa:phaseAggregateCounterPress ?counterPress }}
  }}
  GRAPH <urn:worldcup:kg:2026> {{ ?team rdfs:label ?teamName }}
}}"""

    # Article metadata
    headline    = article.get("headline",    f"{home} {hs}–{aws} {away}")
    description = article.get("description", "")
    image_url   = article.get("imageUrl",    "")
    image_cap   = article.get("imageCaption", f"{home} vs {away} at the 2026 FIFA World Cup")
    article_url = article.get("articleUrl",  f"https://www.fifa.com/en/match-centre/match/{mid}")

    coach_h_name = v(home_coach, "coachName", ""); coach_h_id = v(home_coach, "coachId", "")
    coach_a_name = v(away_coach, "coachName", ""); coach_a_id = v(away_coach, "coachId", "")

    try:    h_acc = f"{float(v(hd,'passesCompleted','0'))/float(v(hd,'passes','1'))*100:.1f}%"
    except: h_acc = "—"
    try:    a_acc = f"{float(v(ad,'passesCompleted','0'))/float(v(ad,'passes','1'))*100:.1f}%"
    except: a_acc = "—"

    today = date.today().isoformat()

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{home} {hs}–{aws} {away} · 2026 FIFA World Cup · Match Intelligence</title>
<meta name="description" content="{description[:200] if description else f'Complete match intelligence: {home} {hs}–{aws} {away}, {group}, 2026 FIFA World Cup.'}">
<meta property="og:title" content="{home} {hs}–{aws} {away} · 2026 FIFA World Cup">
<meta property="og:description" content="{description[:200] if description else f'{home} {hs}–{aws} {away}, {group}, 2026 FIFA World Cup, {stadium}.'}">
{"<meta property='og:image' content='" + image_url + "'>" if image_url else ""}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Helvetica+Neue:wght@300;400;500;700;900&display=swap" rel="stylesheet">
<link rel="related" href="https://api.fifa.com/api/v3/live/football/{mid}?language=en" title="FIFA API Source">
<script type="application/ld+json">
{{
  "@context": "http://schema.org",
  "@type": "SportsEvent",
  "@id": "http://demo.openlinksw.com/fifa-kg#match-{mid}",
  "name": "{home} vs {away}",
  "startDate": "{date_raw[:19]}",
  "location": {{"@type":"Place","name":"{stadium}"}},
  {"" if not image_url else ('"image": "' + image_url + '",') }
  "homeTeam": {{"@type":"SportsTeam","name":"{home}"}},
  "awayTeam": {{"@type":"SportsTeam","name":"{away}"}},
  "description": "2026 FIFA World Cup {group} match — {home} {hs}–{aws} {away}"
}}
</script>
<style>
{CSS}
:root {{ --accent: {hbg}; --accent-dim: {abg}; --accent-text: {htxt}; }}
body {{ background: var(--bg); }}
a.entity-link {{ color: var(--accent); text-decoration-color: var(--accent-dim); }}
a.entity-link:hover {{ color: #fff; }}
#fnav-title {{ color: var(--accent); }}
#hero {{ background: linear-gradient(160deg,{hbg}22 0%,#060810 60%,var(--bg) 100%); }}
#hero::before {{ background: radial-gradient(circle,{hbg}12,transparent 70%); }}
.hero-eyebrow {{ color: var(--accent); }}
.section-eyebrow {{ color: var(--accent); }}
.section-rule {{ background: var(--accent); }}
.card-title {{ color: var(--accent); }}
.player-table td.num {{ color: var(--accent); }}
.tl-min {{ color: var(--accent); }}
details summary::after {{ color: var(--accent); }}
.sparql-live-link:hover {{ background: var(--accent); color: var(--accent-text); }}
.section-title,.card-title{{cursor:pointer;}}
.section-title:hover{{text-decoration:underline;text-decoration-color:var(--accent);text-underline-offset:5px;}}
.card-title:hover{{text-decoration:underline;text-decoration-color:currentColor;text-underline-offset:3px;}}
</style>
</head>
<body>

<nav id="fnav" role="navigation" aria-label="Page sections">
  <div id="fnav-header">
    <span id="fnav-title">Match Intel</span>
    <div style="display:flex;gap:6px;">
      <button id="fnav-theme" aria-label="Toggle theme">☀</button>
      <button id="fnav-toggle" aria-label="Toggle navigation">−</button>
    </div>
  </div>
  <div id="fnav-links">
    <a href="#hero">Overview</a>
    <a href="#goals">Goals</a>
    <a href="#timeline">Timeline</a>
    <a href="#stats">Team Stats</a>
    <a href="#phases">Phase Analytics</a>
    <a href="#pressing">Pressing</a>
    <a href="#formations">Formations</a>
    <a href="#squads">Squads</a>
    <a href="#core-players">Core Players</a>
    <a href="#sparql">SPARQL</a>
    <a href="#sources">Sources</a>
  </div>
</nav>

<section id="hero">
  <div class="hero-eyebrow">2026 FIFA World Cup · {group} · Match {mid}</div>
  <div class="hero-scoreline">
    <div class="hero-team">
      {ent_link(htid, f'<div class="hero-team-name">{home}</div>', "team")}
      <div class="hero-team-score">{hs}</div>
    </div>
    <div class="hero-divider">—</div>
    <div class="hero-team">
      {ent_link(atid, f'<div class="hero-team-name">{away}</div>', "team")}
      <div class="hero-team-score">{aws}</div>
    </div>
  </div>
  <div class="hero-meta">
    <div class="hero-meta-row"><strong>{ent_link(stad_id, stadium, "stadium")}</strong></div>
    <div class="hero-meta-row">{date_nice} · {time_utc}</div>
    <div class="hero-meta-row">Attendance <strong>{fnum(attend) if attend else '—'}</strong></div>
    <div class="hero-meta-row">{group} · {result_badge}</div>
  </div>
  {"" if not image_url else (
'<div style="max-width:720px;margin:0 auto 40px;border-radius:var(--r-lg);overflow:hidden;border:none;background:var(--panel);box-shadow:5px 5px 14px rgba(0,0,0,0.5),-3px -3px 10px rgba(255,255,255,0.02);">'
'<img src="' + image_url + '" alt="' + image_cap[:80].replace('"',"'") + '" style="width:100%;display:block;" loading="lazy">'
'<div style="padding:12px 16px;font-size:11px;color:var(--muted);line-height:1.5;">'
+ (image_cap + (' — ' + description[:160] if description else ''))
+ '<br><span style="font-size:10px;">Image source: <a class="entity-link" href="https://demo.openlinksw.com/describe/?url=' + quote_plus(article_url + '#this') + '" target="_blank" rel="noopener noreferrer">digitalhub.fifa.com</a></span>'
'</div></div>'
)}
  <div class="highlight-block" style="max-width:720px;background:{hbg}0d;box-shadow:inset 2px 0 8px {hbg}33,3px 3px 10px rgba(0,0,0,0.4);">
    {('<strong>' + headline + '</strong> — ' + description) if description else ('<strong>' + headline + '</strong>')}
  </div>
</section>

<!-- Goals -->
<section id="goals" class="reveal">
  <div class="section-eyebrow">Match Goals</div>
  <div class="section-title">{home} {hs}–{aws} {away}</div>
  <div class="section-rule"></div>
  <div class="pitch-wrapper">
    {pitch_svg}
    <div class="pitch-caption">Goal positions — {home} attacks right</div>
  </div>
  <div class="cards-2">
    <div class="card">
      <div class="card-title">{home}</div>
{goal_items(home, True)}
    </div>
    <div class="card">
      <div class="card-title">{away}</div>
{goal_items(away, False)}
    </div>
  </div>
  {og_html}
</section>

<!-- Timeline -->
<section id="timeline" class="reveal">
  <div class="section-eyebrow">Match Timeline</div>
  <div class="section-title">Key events</div>
  <div class="section-rule"></div>
  <div class="timeline">
{timeline_html}
  </div>
</section>

<!-- Team Stats -->
<section id="stats" class="reveal">
  <div class="section-eyebrow">Team Statistics</div>
  <div class="section-title">Head-to-head metrics</div>
  <div class="section-rule"></div>
  <div class="cards-2" style="margin-bottom:40px;">
    <div class="card">
      <div class="card-title">{home}</div>
      <div class="stat-row"><span class="stat-key">Possession</span><span class="stat-val">{h_poss_f:.1f}%</span></div>
      <div class="stat-row"><span class="stat-key">Passes</span><span class="stat-val">{fnum(v(hd,'passes'))}</span></div>
      <div class="stat-row"><span class="stat-key">Pass Accuracy</span><span class="stat-val">{h_acc}</span></div>
      <div class="stat-row"><span class="stat-key">Shots</span><span class="stat-val">{sf(hd,'shots')}</span></div>
      <div class="stat-row"><span class="stat-key">Shots on Target</span><span class="stat-val">{sf(hd,'shotsOnTarget')}</span></div>
      <div class="stat-row"><span class="stat-key">Corners</span><span class="stat-val">{sf(hd,'corners')}</span></div>
      <div class="stat-row"><span class="stat-key">Yellow Cards</span><span class="stat-val">{sf(hd,'yellowCards')}</span></div>
      <div class="stat-row"><span class="stat-key">Offsides</span><span class="stat-val">{sf(hd,'offsides')}</span></div>
      <div class="stat-row"><span class="stat-key">Defensive Pressures</span><span class="stat-val">{fnum(v(hd,'defPress'))}</span></div>
      <div class="stat-row"><span class="stat-key">Forced Turnovers</span><span class="stat-val">{sf(hd,'turnovers')}</span></div>
      <div class="stat-row"><span class="stat-key">Linebreaks (Att/Comp)</span><span class="stat-val">{sf(hd,'lbAtt')} / {sf(hd,'lbComp')}</span></div>
    </div>
    <div class="card">
      <div class="card-title">{away}</div>
      <div class="stat-row"><span class="stat-key">Possession</span><span class="stat-val">{a_poss_f:.1f}%</span></div>
      <div class="stat-row"><span class="stat-key">Passes</span><span class="stat-val">{fnum(v(ad,'passes'))}</span></div>
      <div class="stat-row"><span class="stat-key">Pass Accuracy</span><span class="stat-val">{a_acc}</span></div>
      <div class="stat-row"><span class="stat-key">Shots</span><span class="stat-val">{sf(ad,'shots')}</span></div>
      <div class="stat-row"><span class="stat-key">Shots on Target</span><span class="stat-val">{sf(ad,'shotsOnTarget')}</span></div>
      <div class="stat-row"><span class="stat-key">Corners</span><span class="stat-val">{sf(ad,'corners')}</span></div>
      <div class="stat-row"><span class="stat-key">Yellow Cards</span><span class="stat-val">{sf(ad,'yellowCards')}</span></div>
      <div class="stat-row"><span class="stat-key">Offsides</span><span class="stat-val">{sf(ad,'offsides')}</span></div>
      <div class="stat-row"><span class="stat-key">Defensive Pressures</span><span class="stat-val">{fnum(v(ad,'defPress'))}</span></div>
      <div class="stat-row"><span class="stat-key">Forced Turnovers</span><span class="stat-val">{sf(ad,'turnovers')}</span></div>
      <div class="stat-row"><span class="stat-key">Linebreaks (Att/Comp)</span><span class="stat-val">{sf(ad,'lbAtt')} / {sf(ad,'lbComp')}</span></div>
    </div>
  </div>
  <div class="card">
    <div class="card-title">Comparative</div>
{comp_bars}
  </div>
</section>

<!-- Phase Analytics -->
<section id="phases" class="reveal">
  <div class="section-eyebrow">Phase Analytics</div>
  <div class="section-title">Tactical phase aggregates</div>
  <div class="section-rule"></div>
  <div style="margin-bottom:32px;">
    <div style="font-size:13px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:16px;">{home} · {htac}</div>
    <div class="phase-grid">
{chip("High Press",     v(hd,"highPress"),    hbg)}
{chip("Counter-Press",  v(hd,"counterPress"), hbg)}
{chip("Mid Block",      v(hd,"midBlock"),     hbg)}
{chip("Low Block",      v(hd,"lowBlock"),     hbg)}
{chip("Att. Transition",v(hd,"attTrans"),     hbg)}
{chip("Final Third",    v(hd,"finalThird"),   hbg)}
{chip("High Block",     v(hd,"highBlock"),    hbg)}
{chip("Turnovers",      v(hd,"turnovers"),    hbg)}
    </div>
  </div>
  <div>
    <div style="font-size:13px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:16px;">{away} · {atac}</div>
    <div class="phase-grid">
{chip("High Press",     v(ad,"highPress"),    abg)}
{chip("Counter-Press",  v(ad,"counterPress"), abg)}
{chip("Mid Block",      v(ad,"midBlock"),     abg)}
{chip("Low Block",      v(ad,"lowBlock"),     abg)}
{chip("Att. Transition",v(ad,"attTrans"),     abg)}
{chip("Final Third",    v(ad,"finalThird"),   abg)}
{chip("High Block",     v(ad,"highBlock"),    abg)}
{chip("Turnovers",      v(ad,"turnovers"),    abg)}
    </div>
  </div>
</section>

{pressing_section(home, away, hd, ad, hbg, abg, goals)}

<!-- Formations -->
<section id="formations" class="reveal">
  <div class="section-eyebrow">Formations &amp; Tactics</div>
  <div class="section-title">Starting XI</div>
  <div class="section-rule"></div>
  <div class="formation-grid">
    <div>
      <div class="formation-tactic">{home} · <strong>{htac}</strong>{f' · Coach: {ent_link(coach_h_id, coach_h_name, "coach")}' if coach_h_name else ''}</div>
      {h_form_svg}
    </div>
    <div>
      <div class="formation-tactic">{away} · <strong>{atac}</strong>{f' · Coach: {ent_link(coach_a_id, coach_a_name, "coach")}' if coach_a_name else ''}</div>
      {a_form_svg}
    </div>
  </div>
</section>

<!-- Squads -->
<section id="squads" class="reveal">
  <div class="section-eyebrow">Squads</div>
  <div class="section-title">Match squads</div>
  <div class="section-rule"></div>
  <div class="cards-2">
    <div class="card" style="padding:0;overflow:hidden;">
      <div style="padding:20px 24px;border-bottom:1px solid var(--line);">
        <div class="card-title" style="margin-bottom:0;">{home} — Squad</div>
      </div>
      <table class="player-table">
        <thead><tr><th>#</th><th>Player</th></tr></thead>
        <tbody>
{squad_rows(home, squad.get(home,[]), goals, bookings, subs)}
        </tbody>
      </table>
    </div>
    <div class="card" style="padding:0;overflow:hidden;">
      <div style="padding:20px 24px;border-bottom:1px solid var(--line);">
        <div class="card-title" style="margin-bottom:0;">{away} — Squad</div>
      </div>
      <table class="player-table">
        <thead><tr><th>#</th><th>Player</th></tr></thead>
        <tbody>
{squad_rows(away, squad.get(away,[]), goals, bookings, subs)}
        </tbody>
      </table>
    </div>
  </div>
</section>

<!-- Core Players -->
<section id="core-players" class="reveal">
  <div class="section-eyebrow">Post-Match Intelligence</div>
  <div class="section-title">Core Players &amp; Final Team Stats</div>
  <div class="section-rule"></div>
  <div class="cards-2" style="margin-bottom:40px;">
    <div class="card">
      <div class="card-title">{home} — Final Stats</div>
      <div class="stat-row"><span class="stat-key">Possession</span><span class="stat-val">{h_poss_f:.1f}%</span></div>
      <div class="stat-row"><span class="stat-key">Passes / Completed</span><span class="stat-val">{fnum(v(hd,'passes'))} / {fnum(v(hd,'passesCompleted'))}</span></div>
      <div class="stat-row"><span class="stat-key">Pass Accuracy</span><span class="stat-val">{h_acc}</span></div>
      <div class="stat-row"><span class="stat-key">Shots / On Target</span><span class="stat-val">{sf(hd,'shots')} / {sf(hd,'shotsOnTarget')}</span></div>
      <div class="stat-row"><span class="stat-key">Counter-Press Score</span><span class="stat-val" style="color:{hbg};">{fnum(v(hd,'counterPress'),2)}</span></div>
    </div>
    <div class="card">
      <div class="card-title">{away} — Final Stats</div>
      <div class="stat-row"><span class="stat-key">Possession</span><span class="stat-val">{a_poss_f:.1f}%</span></div>
      <div class="stat-row"><span class="stat-key">Passes / Completed</span><span class="stat-val">{fnum(v(ad,'passes'))} / {fnum(v(ad,'passesCompleted'))}</span></div>
      <div class="stat-row"><span class="stat-key">Pass Accuracy</span><span class="stat-val">{a_acc}</span></div>
      <div class="stat-row"><span class="stat-key">Shots / On Target</span><span class="stat-val">{sf(ad,'shots')} / {sf(ad,'shotsOnTarget')}</span></div>
      <div class="stat-row"><span class="stat-key">Counter-Press Score</span><span class="stat-val" style="color:{abg};">{fnum(v(ad,'counterPress'),2)}</span></div>
    </div>
  </div>
  <div class="card" style="margin-bottom:40px;">
    <div class="card-title">Head-to-Head Comparison</div>
{comp_bars}
  </div>
  <div class="card" style="margin-bottom:40px;">
    <div class="card-title">Distance &amp; Speed Comparison</div>
{phys_bars}
  </div>
  <div class="cards-2">
    <div class="card" style="padding:0;overflow:hidden;">
      <div style="padding:20px 24px;border-bottom:1px solid var(--line);">
        <div class="card-title" style="margin-bottom:0;">{home} — Core Performers</div>
      </div>
      <table class="player-table">
        <thead><tr><th>Player</th><th>Dist m</th><th>Pass</th><th>Spr</th><th>km/h</th><th>Highlight</th></tr></thead>
        <tbody>
{core_rows(home)}
        </tbody>
      </table>
    </div>
    <div class="card" style="padding:0;overflow:hidden;">
      <div style="padding:20px 24px;border-bottom:1px solid var(--line);">
        <div class="card-title" style="margin-bottom:0;">{away} — Core Performers</div>
      </div>
      <table class="player-table">
        <thead><tr><th>Player</th><th>Dist m</th><th>Pass</th><th>Spr</th><th>km/h</th><th>Highlight</th></tr></thead>
        <tbody>
{core_rows(away)}
        </tbody>
      </table>
    </div>
  </div>
  <div class="sparql-block" style="margin-top:32px;">
    <div style="font-size:13px;font-weight:700;margin-bottom:4px;">Player Physical &amp; Goal Metrics</div>
    <div style="font-size:12px;color:var(--muted);margin-bottom:8px;">All player analytics from the post-match snapshot</div>
    <details>
      <summary>SPARQL · Player Analytics</summary>
      <pre>{players_q}</pre>
    </details>
    <a class="sparql-live-link" href="{sparql_url(players_q)}" target="_blank" rel="noopener noreferrer">▶ Run live query</a>
  </div>
</section>

<!-- SPARQL -->
<section id="sparql" class="reveal">
  <div class="section-eyebrow">SPARQL Queries</div>
  <div class="section-title">Knowledge graph exploration</div>
  <div class="section-rule"></div>
  <div class="sparql-block">
    <div style="font-size:13px;font-weight:700;margin-bottom:4px;">Match Overview</div>
    <div style="font-size:12px;color:var(--muted);margin-bottom:8px;">{home} vs {away} — core match metadata</div>
    <details><summary>SPARQL · Match Overview</summary><pre>{overview_q}</pre></details>
    <a class="sparql-live-link" href="{sparql_url(overview_q)}" target="_blank" rel="noopener noreferrer">▶ Run live query</a>
  </div>
  <div class="sparql-block">
    <div style="font-size:13px;font-weight:700;margin-bottom:4px;">Goals</div>
    <div style="font-size:12px;color:var(--muted);margin-bottom:8px;">All goal events with scorer and assist</div>
    <details><summary>SPARQL · Goals</summary><pre>{goals_q}</pre></details>
    <a class="sparql-live-link" href="{sparql_url(goals_q)}" target="_blank" rel="noopener noreferrer">▶ Run live query</a>
  </div>
  <div class="sparql-block">
    <div style="font-size:13px;font-weight:700;margin-bottom:4px;">Team Analytics + Pressing Phases</div>
    <div style="font-size:12px;color:var(--muted);margin-bottom:8px;">Full tactical phase breakdown for both teams</div>
    <details><summary>SPARQL · Team Analytics</summary><pre>{stats_q}</pre></details>
    <a class="sparql-live-link" href="{sparql_url(stats_q)}" target="_blank" rel="noopener noreferrer">▶ Run live query</a>
  </div>

  <!-- Explore KG using SPARQL -->
  <div id="sparql-explorer" style="margin-top:40px;padding-top:32px;border-top:1px solid var(--line-str);">
    <div style="font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin-bottom:16px;">Explore Knowledge Graph</div>
    <div class="kg-graph-tabs">
      <button class="kg-tab active" id="tabMain" onclick="setKgGraph('main')">Match Data</button>
      <button class="kg-tab" id="tabAnalytics" onclick="setKgGraph('analytics')">Analytics</button>
    </div>
    <textarea id="sparqlQueryText" readonly
      style="width:100%;margin-top:12px;padding:14px;font-family:'Courier New',monospace;
             font-size:11px;line-height:1.6;background:var(--panel-str);color:var(--ink);
             border:1px solid var(--line-str);border-radius:var(--r);resize:vertical;
             height:220px;outline:none;"></textarea>
    <div style="display:flex;align-items:center;gap:12px;margin-top:10px;flex-wrap:wrap;">
      <a id="sparqlBtn" class="sparql-live-link" href="#" target="_blank" rel="noopener noreferrer">Explore Knowledge Graph using SPARQL</a>
      <span style="font-size:11px;color:var(--muted);">Results: <code>text/x-html+tr</code> via <a class="entity-link" href="https://demo.openlinksw.com/sparql" target="_blank" rel="noopener noreferrer">demo.openlinksw.com/sparql</a></span>
    </div>
  </div>
</section>

<footer id="sources">
  <section class="attribution-panel">
    <h2>Attribution &amp; Provenance</h2>
    <div class="attribution-grid">

      <article class="attribution-card wide">
        <span class="attribution-label">Source material</span>
        <p>Match data sourced from the <a class="entity-link" href="https://demo.openlinksw.com/describe/?url=http%3A%2F%2Fdemo.openlinksw.com%2Ffifa-kg%23match-{mid}" target="_blank" rel="noopener noreferrer">FIFA World Cup 2026 Knowledge Graph</a> ({ent_link(mid, f"fifa-kg:match-{mid}", "match")}) via <a class="entity-link" href="https://demo.openlinksw.com/sparql" target="_blank" rel="noopener noreferrer">demo.openlinksw.com/sparql</a>.{f' Editorial context from <a class="entity-link" href="{article_url}" target="_blank" rel="noopener noreferrer">FIFA match report</a>.' if article_url else ''}</p>
      </article>

      <article class="attribution-card">
        <span class="attribution-label">Skills used</span>
        <div class="attribution-links">
          <a class="attribution-pill" href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/wc2026-match-report" target="_blank" rel="noopener noreferrer">wc2026-match-report</a>
          <a class="attribution-pill" href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/world-cup-2026-navigator" target="_blank" rel="noopener noreferrer">world-cup-2026-navigator</a>
          <a class="attribution-pill" href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/rdf-infographic-skill" target="_blank" rel="noopener noreferrer">rdf-infographic-skill</a>
        </div>
      </article>

      <article class="attribution-card">
        <span class="attribution-label">Generation environment</span>
        <p>Generated by <a class="entity-link" href="https://demo.openlinksw.com/describe/?url=https%3A%2F%2Fwww.anthropic.com%2Fclaude%23claude-sonnet-4-6" target="_blank" rel="noopener noreferrer">Claude Sonnet 4.6</a> via <a class="entity-link" href="https://demo.openlinksw.com/describe/?url=https%3A%2F%2Fwww.anthropic.com%2Fclaude-code%23this" target="_blank" rel="noopener noreferrer">Claude Code</a> CLI on {today}. Script: <code>report_template_create.py</code>.</p>
      </article>

      <article class="attribution-card">
        <span class="attribution-label">Linked Data runtime</span>
        <p>SPARQL endpoint and entity resolver powered by <a class="entity-link" href="https://demo.openlinksw.com/describe/?url=https%3A%2F%2Fdbpedia.org%2Fresource%2FOpenLink_Virtuoso" target="_blank" rel="noopener noreferrer">OpenLink Virtuoso</a> at <a class="entity-link" href="https://demo.openlinksw.com" target="_blank" rel="noopener noreferrer">demo.openlinksw.com</a>.</p>
      </article>

      <article class="attribution-card">
        <span class="attribution-label">Named graphs</span>
        <p><code>urn:worldcup:kg:2026</code><br>Match, team, player, goal, booking, substitution, coach, squad, and article data.<br><code>urn:worldcup:kg:2026:analytics</code><br>TeamMatchAnalyticsReport and PlayerMatchAnalyticsReport nodes.</p>
      </article>

      <article class="attribution-card">
        <span class="attribution-label">Resolver pattern</span>
        <p>Visible entity links route through:<br><code>https://demo.openlinksw.com/describe/?url={{encodedIRI}}</code></p>
      </article>

      <article class="attribution-card wide">
        <span class="attribution-label">Extraction provenance</span>
        <p>All statistics derived at generation time via live SPARQL queries. Head coaches identified via <code>fifa:hasRole fifa:CoachRole-0</code>. Analytics sourced from the latest <code>fifa:TeamMatchAnalyticsReport</code> and <code>fifa:PlayerMatchAnalyticsReport</code> nodes using <code>MAX(fifa:generatedAt)</code> snapshots. No cached or manually entered data.</p>
      </article>

    </div>
  </section>
  <p style="font-size:11px;color:var(--muted);border-top:1px solid var(--line-str);margin-top:32px;padding-top:20px">© 2026 <a class="entity-link" href="https://www.openlinksw.com/" target="_blank" rel="noopener noreferrer">OpenLink Software</a> · FIFA World Cup 2026 Match Intelligence · Data sourced from FIFA Knowledge Graph via <a class="entity-link" href="https://demo.openlinksw.com" target="_blank" rel="noopener noreferrer">demo.openlinksw.com</a></p>
</footer>

<script>
{JS}
</script>
</body>
</html>"""


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate a FIFA World Cup 2026 match intelligence HTML report."
    )
    parser.add_argument("match_id", help="FIFA match ID (e.g. 400021491)")
    parser.add_argument("output",   help="Output HTML filename")
    args = parser.parse_args()

    mid = args.match_id
    out = Path(args.output)
    if not out.suffix:
        out = out.with_suffix(".html")

    print(f"Fetching data for match {mid}…")
    ov = q_overview(mid)
    if not ov:
        print(f"Error: no match data found for {mid}", file=sys.stderr)
        sys.exit(1)

    home = v(ov, "homeTeam"); htid = v(ov, "homeTeamId"); atid = v(ov, "awayTeamId")
    print(f"  {home} {v(ov,'homeScore')}–{v(ov,'awayScore')} {v(ov,'awayTeam')}")

    print("  coaches (CoachRole-0 only) / goals / bookings / subs…")
    coaches  = q_coaches(mid)
    goals    = q_goals(mid)
    bookings = q_bookings(mid)
    subs     = q_subs(mid)

    print("  team analytics (GRAPH-scoped)…")
    team_stats = q_team_stats(mid, htid, atid)

    print("  player analytics (latest snapshot, GRAPH-scoped)…")
    players = q_players(mid)

    print("  squads…")
    squad = q_squad(mid)

    print("  article metadata…")
    article = q_article_meta(mid)
    if article.get("imageUrl"):
        print(f"  image: {article['imageUrl'][:60]}…")

    print("Building HTML…")
    html = build_html(mid, ov, coaches, goals, bookings, subs, team_stats, players, squad, article)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Written → {out}  ({len(html)//1024} KB)")


if __name__ == "__main__":
    main()
