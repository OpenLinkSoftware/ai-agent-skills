#!/usr/bin/env python3
"""
player_report_create.py — Generate a FIFA World Cup 2026 *player* intelligence
report (HTML) straight from the OpenLink FIFA Knowledge Graph.

Unlike report_template_create.py (which builds per-MATCH reports), this builds a
per-PLAYER report: hero, tournament snapshot, an assist->goal creation map drawn
from real event XY coordinates, an in-match temporal "how he changes the game"
section (Chart.js), a shot map, squad-context comparison charts, plus the usual
passing / physical / attacking / defensive / progression / SPARQL / sources
sections.

Usage:
    python3 player_report_create.py <playerId> [--out FILE] [--image URL]
                                    [--accent "#002395"] [--accent2 "#ED2939"]

Example:
    python3 player_report_create.py 485655 \
        --out michael-olise-wc2026-report.html \
        --image "https://digitalhub.fifa.com/transform/.../OLISE-Michael_485655"

Everything else (name, jersey, team, matches, stats, events, coordinates,
temporal snapshots, comparison) is queried live from:
    https://demo.openlinksw.com/sparql
graphs urn:worldcup:kg:2026 (+ :analytics).
"""
import sys, json, argparse, datetime
import urllib.parse, urllib.request, collections
from html import escape
from urllib.parse import quote_plus

ENDPOINT = "https://demo.openlinksw.com/sparql"
KG  = "urn:worldcup:kg:2026"
ANA = "urn:worldcup:kg:2026:analytics"
BASE = "http://demo.openlinksw.com/fifa-kg/"
DESCRIBE = "https://demo.openlinksw.com/describe/?url="
PFX = """PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""
# per-match series palette (extended if a player has >5 matches)
SERIES_COLORS = ["#22D3EE", "#A78BFA", "#FB923C", "#F472B6", "#34D399",
                 "#F59E0B", "#60A5FA", "#F87171"]

# National team primary colours (matches the wc2026-match-report team-colours table).
TEAM_COLORS = {
    "algeria":"#006233","argentina":"#74ACDF","australia":"#FFD700","austria":"#ED2939",
    "belgium":"#111827","bolivia":"#D52B1E","bosnia and herzegovina":"#002395","brazil":"#009C3B",
    "cameroon":"#007A5E","canada":"#FF0000","chile":"#D52B1E","colombia":"#FCD116","congo dr":"#007FFF",
    "costa rica":"#002B7F","côte d'ivoire":"#F77F00","cote d'ivoire":"#F77F00","croatia":"#FF0000",
    "cuba":"#002A8F","curaçao":"#002B7F","curacao":"#002B7F","czechia":"#D7141A","denmark":"#C60C30",
    "ecuador":"#FFD100","egypt":"#CE1126","england":"#1E3A8A","france":"#002395","germany":"#111827",
    "ghana":"#006B3F","honduras":"#0073CF","hungary":"#CE2939","ir iran":"#239F40","iran":"#239F40",
    "iraq":"#CE1126","italy":"#003399","jamaica":"#FED100","japan":"#003087","korea republic":"#C60C30",
    "south korea":"#C60C30","mexico":"#006847","morocco":"#C1272D","netherlands":"#FF6600",
    "new zealand":"#111827","nigeria":"#008751","norway":"#EF2B2D","panama":"#DA121A","paraguay":"#D52B1E",
    "peru":"#D91023","poland":"#DC143C","portugal":"#006600","romania":"#002B7F","saudi arabia":"#006C35",
    "scotland":"#003DA5","senegal":"#00853F","serbia":"#C6363C","slovakia":"#0B4EA2","slovenia":"#003DA5",
    "south africa":"#007A4D","spain":"#AA151B","switzerland":"#FF0000","tanzania":"#1EB53A",
    "türkiye":"#E30A17","turkiye":"#E30A17","turkey":"#E30A17","ukraine":"#005BBB","united states":"#002868",
    "usa":"#002868","uruguay":"#5EB6E4","venezuela":"#CF142B","wales":"#C8102E",
}
TEAM_FALLBACK = "#334466"

def _brightness(hexc):
    h = hexc.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return (r*299 + g*587 + b*114) / 1000

def team_accents(team_name):
    """Return (accent, accent2) for a nation — accent from the kit, accent2 a
    readable contrast (red for non-red kits, navy for red kits)."""
    accent = TEAM_COLORS.get((team_name or "").strip().lower(), TEAM_FALLBACK)
    h = accent.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    reddish = r > 150 and g < 110 and b < 110
    accent2 = "#0A2A6B" if reddish else "#ED2939"
    return accent, accent2

# ── SPARQL helper ─────────────────────────────────────────────────────────────
def run(q):
    params = {"query": PFX + q, "format": "application/sparql-results+json", "timeout": "60"}
    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))
    return [{k: v["value"] for k, v in b.items()} for b in data["results"]["bindings"]]

def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def describe(iri):
    return DESCRIBE + quote_plus(iri)

def resolve_player(fragment):
    """Resolve a name (or fragment) to a numeric player id. Prefers an exact
    label match; errors with candidates when ambiguous."""
    frag = fragment.strip().replace("'", "\\'")
    rows = run(f"""SELECT ?p ?name (SAMPLE(?jn) AS ?jersey) (SAMPLE(?tn) AS ?team)
      FROM <{KG}> WHERE {{
        ?p a fifa:Player ; rdfs:label ?name .
        OPTIONAL {{ ?p fifa:jerseyNum ?jn }}
        OPTIONAL {{ ?p fifa:playsForTeam ?t . ?t rdfs:label ?tn }}
        FILTER(CONTAINS(LCASE(?name), LCASE('{frag}')))
      }} GROUP BY ?p ?name ORDER BY ?name LIMIT 25""")
    if not rows:
        sys.exit(f"No player matches '{fragment}'.")
    def pid(iri): return iri.rstrip("#").split("player-")[-1].split("#")[0]
    exact = [r for r in rows if r["name"].strip().lower() == fragment.strip().lower()]
    pick = exact[0] if exact else rows[0]
    if len(rows) > 1 and not exact:
        print("Multiple matches — using the first. Candidates:", file=sys.stderr)
        for r in rows[:10]:
            print(f"  {pid(r['p']):>8}  {r['name']}  ({r.get('team','?')})", file=sys.stderr)
    print(f"Resolved '{fragment}' → {pick['name']} (id {pid(pick['p'])}, {pick.get('team','?')})", file=sys.stderr)
    return pid(pick["p"])

# ══════════════════════════════════════════════════════════════════════════════
# 1. DATA COLLECTION
# ══════════════════════════════════════════════════════════════════════════════
def collect(player_id):
    P = f"<{BASE}player-{player_id}#this>"
    d = {"player_iri": f"{BASE}player-{player_id}#this", "player_id": player_id}

    # ── bio ──
    bio = run(f"""SELECT ?name ?jersey ?dob ?pos ?posLabel ?team ?teamName ?teamId
      FROM <{KG}> WHERE {{
        {P} rdfs:label ?name .
        OPTIONAL {{ {P} fifa:jerseyNum ?jersey }}
        OPTIONAL {{ {P} fifa:birthDate ?dob }}
        OPTIONAL {{ {P} fifa:realPosition ?pos . OPTIONAL {{ ?pos rdfs:label ?posLabel }} }}
        OPTIONAL {{ {P} fifa:playsForTeam ?team . ?team rdfs:label ?teamName ; fifa:teamId ?teamId }}
      }} LIMIT 1""")
    if not bio:
        sys.exit(f"No player found for id {player_id}")
    b = bio[0]
    # Position instances (fifa:Position-N) carry no rdfs:label — derive from the code.
    POS_MAP = {"0": "Goalkeeper", "1": "Defender", "2": "Midfielder", "3": "Forward"}
    pos_code = (b.get("pos","").rstrip("#").split("-")[-1] if b.get("pos") else "")
    position = b.get("posLabel") or POS_MAP.get(pos_code, "")
    d.update({"name": b["name"], "jersey": b.get("jersey", ""), "dob": b.get("dob", ""),
              "position": position, "side": "",
              "team": b.get("teamName", ""), "team_iri": b.get("team", ""),
              "team_id": b.get("teamId", "")})
    T = f"<{d['team_iri']}>"

    # ── player photo from KG (schema:image) ──
    img_rows = run(f"""SELECT ?img FROM <{KG}> WHERE {{
        {P} <http://schema.org/image> ?img }} LIMIT 1""")
    d["kg_image"] = img_rows[0]["img"] if img_rows else ""

    # ── matches this player featured in (has analytics report) ──
    matches = run(f"""SELECT DISTINCT ?m ?ml ?date ?hs ?as ?ht ?htName ?at ?atName ?stageName
      FROM <{KG}> FROM <{ANA}> WHERE {{
        ?m a fifa:Match ; rdfs:label ?ml ; fifa:date ?date ;
           fifa:homeTeam ?ht ; fifa:awayTeam ?at ;
           fifa:homeTeamScore ?hs ; fifa:awayTeamScore ?as .
        ?ht rdfs:label ?htName . ?at rdfs:label ?atName .
        OPTIONAL {{ ?m fifa:stage ?st . ?st rdfs:label ?stageName }}
        ?r a fifa:PlayerMatchAnalyticsReport ; fifa:match ?m ; fifa:player {P} .
      }} ORDER BY ?date""")
    d["matches"] = matches

    # ── temporal analytics series (all snapshots) ──
    FIELDS = ["timePlayed","threat","totalDistance","passes","passesCompleted","assists",
              "goals","attemptAtGoal","attemptAtGoalOnTarget","sprints","topSpeed","avgSpeed",
              "foulsFor","foulsAgainst","forcedTurnovers","crosses","crossesCompleted","takeOnsCompleted",
              "yellowCards","corners"]
    opt = "\n".join(f"  OPTIONAL {{ ?r fifa:{f} ?{f} }}" for f in FIELDS)
    sel = " ".join(f"?{f}" for f in FIELDS)
    rows = run(f"""SELECT ?ml ?genAt {sel}
      FROM <{KG}> FROM <{ANA}> WHERE {{
        ?m a fifa:Match ; rdfs:label ?ml .
        ?r a fifa:PlayerMatchAnalyticsReport ; fifa:match ?m ;
           fifa:player {P} ; fifa:generatedAt ?genAt .
{opt}
      }} ORDER BY ?ml ?timePlayed ?genAt""")
    d["ana_rows"] = rows
    d["FIELDS"] = FIELDS

    # ── player events (coords) ──
    d["player_events"] = run(f"""SELECT ?ml ?evt ?typeLabel ?evtMin ?px ?py ?period
      FROM <{KG}> WHERE {{
        ?m a fifa:Match ; rdfs:label ?ml ; fifa:hasEvent ?evt .
        ?evt fifa:eventPlayer {P} .
        OPTIONAL {{ ?evt fifa:typeLabel ?typeLabel }}
        OPTIONAL {{ ?evt fifa:eventMatchMinute ?evtMin }}
        OPTIONAL {{ ?evt fifa:positionX ?px }} OPTIONAL {{ ?evt fifa:positionY ?py }}
        OPTIONAL {{ ?evt fifa:eventPeriod ?period }}
      }} ORDER BY ?ml ?evtMin""")

    # ── team attempt/goal events (goal-shot coords + attack direction) ──
    d["team_shots"] = run(f"""SELECT ?ml ?typeLabel ?evtMin ?px ?py ?period ?playerName
      FROM <{KG}> WHERE {{
        ?m a fifa:Match ; rdfs:label ?ml ; fifa:hasEvent ?evt .
        ?evt fifa:eventTeam {T} ; fifa:typeLabel ?typeLabel .
        FILTER(CONTAINS(?typeLabel,"Attempt") || CONTAINS(?typeLabel,"Goal"))
        OPTIONAL {{ ?evt fifa:eventMatchMinute ?evtMin }}
        OPTIONAL {{ ?evt fifa:positionX ?px }} OPTIONAL {{ ?evt fifa:positionY ?py }}
        OPTIONAL {{ ?evt fifa:eventPeriod ?period }}
        OPTIONAL {{ ?evt fifa:eventPlayer ?pl . ?pl rdfs:label ?playerName }}
      }} ORDER BY ?ml ?evtMin""")

    # ── team goals (scorer + minute + scorer iri) ──
    d["team_goals"] = run(f"""SELECT ?ml ?minute ?scorer ?scorerIri
      FROM <{KG}> WHERE {{
        ?m a fifa:Match ; rdfs:label ?ml ; fifa:hasGoal ?g .
        ?g fifa:goalMinute ?minute ; fifa:team {T} .
        OPTIONAL {{ ?g fifa:player ?sc . ?sc rdfs:label ?scorer .
                    BIND(STR(?sc) AS ?scorerIri) }}
      }} ORDER BY ?ml ?minute""")

    # ── squad comparison (team-mates aggregate) ──
    d["compare_rows"] = run(f"""SELECT ?pname ?ml ?genAt ?timePlayed ?assists ?goals ?threat
             ?crosses ?attemptAtGoal ?takeOnsCompleted ?passes
      FROM <{KG}> FROM <{ANA}> WHERE {{
        ?m a fifa:Match ; rdfs:label ?ml .
        ?r a fifa:PlayerMatchAnalyticsReport ; fifa:match ?m ; fifa:player ?p ; fifa:generatedAt ?genAt .
        ?p rdfs:label ?pname ; fifa:playsForTeam {T} .
        OPTIONAL {{ ?r fifa:timePlayed ?timePlayed }} OPTIONAL {{ ?r fifa:assists ?assists }}
        OPTIONAL {{ ?r fifa:goals ?goals }} OPTIONAL {{ ?r fifa:threat ?threat }}
        OPTIONAL {{ ?r fifa:crosses ?crosses }} OPTIONAL {{ ?r fifa:attemptAtGoal ?attemptAtGoal }}
        OPTIONAL {{ ?r fifa:takeOnsCompleted ?takeOnsCompleted }} OPTIONAL {{ ?r fifa:passes ?passes }}
      }}""")
    return d


# ══════════════════════════════════════════════════════════════════════════════
# 2. TRANSFORM
# ══════════════════════════════════════════════════════════════════════════════
def half_of(period_uri):
    if not period_uri: return "H1"
    n = period_uri.rstrip("#").split("-")[-1].split("#")[0]
    return {"3":"H1","4":"H1","5":"H2","7":"ET1","8":"ET1","9":"ET2"}.get(n, "H1")

def month_day(iso):
    try:
        dt = datetime.datetime.fromisoformat(iso.replace("Z","+00:00"))
        return dt.strftime("%-d %b")
    except Exception:
        return iso[:10]

def transform(d):
    FIELDS = d["FIELDS"]
    # match metadata keyed by label
    meta = {}
    order = []
    for m in d["matches"]:
        ml = m["ml"]
        if ml in meta:
            continue
        home = (m["ht"] == d["team_iri"])
        ts = int(m["hs"]) if home else int(m["as"])
        os_ = int(m["as"]) if home else int(m["hs"])
        opp = m["atName"] if home else m["htName"]
        res = ("W" if ts>os_ else "D" if ts==os_ else "L") + f" {ts}–{os_}"
        stage = m.get("stageName","")
        stage = {"First Stage":"Group Stage"}.get(stage, stage or "Group Stage")
        i = len(order)
        meta[ml] = {"key": ml, "iri": m["m"], "opp": opp, "home": home,
                    "short": opp[:3].upper(), "date": month_day(m["date"]),
                    "stage": stage, "res": res, "ts": ts, "os": os_,
                    "col": SERIES_COLORS[i % len(SERIES_COLORS)]}
        order.append(ml)
    d["meta"] = meta; d["order"] = order

    # temporal series: dedupe by timePlayed (keep last genAt), sorted
    series = collections.OrderedDict()
    for r in d["ana_rows"]:
        ml = r["ml"]; tp = num(r.get("timePlayed"))
        if tp is None: continue
        series.setdefault(ml, {})[round(tp,3)] = r
    temporal = {}
    for ml, dd in series.items():
        pts = []
        for tp in sorted(dd):
            r = dd[tp]
            pt = {"t": tp}
            for f in FIELDS:
                if f == "timePlayed": continue
                pt[f] = num(r.get(f))
            pts.append(pt)
        temporal[ml] = pts
    d["temporal"] = temporal

    # finals: cumulative fields -> max; threat -> last non-null; topSpeed -> max
    CUM = ["totalDistance","passes","passesCompleted","assists","goals","attemptAtGoal",
           "attemptAtGoalOnTarget","sprints","foulsFor","foulsAgainst","forcedTurnovers",
           "crosses","crossesCompleted","takeOnsCompleted","yellowCards","corners"]
    finals = {}
    for ml, pts in temporal.items():
        def cmax(f):
            v = [p[f] for p in pts if p.get(f) is not None]
            return max(v) if v else 0
        def lastnn(f):
            v = [p[f] for p in pts if p.get(f) is not None]
            return v[-1] if v else 0
        fin = {f: cmax(f) for f in CUM}
        fin["threat"] = lastnn("threat")
        fin["topSpeed"] = cmax("topSpeed")
        fin["timePlayed"] = max(p["t"] for p in pts)
        finals[ml] = fin
    d["finals"] = finals

    # aggregate totals
    agg = collections.defaultdict(float)
    for ml, fin in finals.items():
        for k, v in fin.items():
            if k in ("threat","topSpeed"): continue
            agg[k] += v
    agg["timePlayed"] = sum(fin["timePlayed"] for fin in finals.values())
    agg["topSpeed"] = max((fin["topSpeed"] for fin in finals.values()), default=0)
    d["agg"] = agg

    # ── attack-direction normalization (per match, per half) ──
    att = collections.defaultdict(list)
    for e in d["team_shots"]:
        if e.get("typeLabel") == "Attempt at Goal":
            px = num(e.get("px"))
            if px is not None:
                att[(e["ml"], half_of(e.get("period")))].append(px)
    flip = {k: (sum(v)/len(v) < 50) for k, v in att.items()}
    # robustness: a team always switches ends between H1 and H2, so if one half's
    # direction is unknown (no attempts that half) infer it as the opposite of a
    # known half in the same match.
    known_matches = {ml for (ml, h) in flip}
    for ml in known_matches:
        h1 = flip.get((ml, "H1")); h2 = flip.get((ml, "H2"))
        if h1 is None and h2 is not None: flip[(ml, "H1")] = not h2
        if h2 is None and h1 is not None: flip[(ml, "H2")] = not h1
        # extra time repeats the H1/H2 orientation pair
        if (ml, "H1") in flip:
            flip.setdefault((ml, "ET1"), flip[(ml, "H1")])
            flip.setdefault((ml, "ET2"), not flip[(ml, "H1")])
    def norm(px, py, ml, per):
        if px is None or py is None: return None, None
        if flip.get((ml, half_of(per)), False): return 100-px, 100-py
        return px, py

    # player assists + shots (normalized), keeping each event's own IRI
    assists, shots = [], []
    for e in d["player_events"]:
        X, Y = norm(num(e.get("px")), num(e.get("py")), e["ml"], e.get("period"))
        if e.get("typeLabel") == "Assist":
            assists.append({"ml": e["ml"], "min": e.get("evtMin"), "X": X, "Y": Y, "evt": e.get("evt")})
        elif e.get("typeLabel") == "Attempt at Goal":
            shots.append({"ml": e["ml"], "min": e.get("evtMin"), "X": X, "Y": Y, "evt": e.get("evt")})
    # corners per match (player)
    corners = collections.Counter(e["ml"] for e in d["player_events"] if e.get("typeLabel")=="Corner")
    d["corners_by_match"] = corners

    # pair each assist with the goal it created (scorer shot location)
    def surname(n): return n.split()[-1] if n else ""
    def find_shot(ml, minute, scorer):
        sm = surname(scorer)
        for e in d["team_shots"]:
            if e["ml"] != ml: continue
            if sm and sm.lower() in e.get("playerName","").lower():
                em = e.get("evtMin")
                if em is not None and abs(int(em)-int(minute)) <= 1:
                    X, Y = norm(num(e.get("px")), num(e.get("py")), ml, e.get("period"))
                    if X is not None:
                        return X, Y
        return None, None
    assist_goals = []
    for a in assists:
        ml, mn = a["ml"], a["min"]
        scorer = scorerIri = None
        for g in d["team_goals"]:
            if g["ml"] == ml and mn is not None and abs(int(g["minute"])-int(mn)) <= 1:
                scorer = g.get("scorer"); scorerIri = g.get("scorerIri"); break
        gx, gy = find_shot(ml, mn, scorer) if scorer else (None, None)
        m = meta[ml]
        assist_goals.append({"ml": ml, "min": mn, "assistX": a["X"], "assistY": a["Y"],
                             "scorer": scorer, "scorerIri": scorerIri, "goalX": gx, "goalY": gy,
                             "assistEvt": a.get("evt"),
                             "short": m["short"], "col": m["col"], "opp": m["opp"], "matchIri": m["iri"]})
    for s in shots:
        m = meta[s["ml"]]; s["short"]=m["short"]; s["col"]=m["col"]; s["opp"]=m["opp"]; s["matchIri"]=m["iri"]
    d["assists"] = assists; d["shots"] = shots; d["assist_goals"] = assist_goals

    # ── squad comparison aggregate ──
    best = {}
    for r in d["compare_rows"]:
        tp = num(r.get("timePlayed")) or 0
        key = (r["pname"], r["ml"])
        if key not in best or tp > best[key][0]:
            best[key] = (tp, r)
    cagg = collections.defaultdict(lambda: collections.defaultdict(float)); mins = collections.defaultdict(float)
    for (pn, ml), (tp, r) in best.items():
        for f in ["assists","goals","threat","crosses","attemptAtGoal","takeOnsCompleted","passes"]:
            v = num(r.get(f))
            if v: cagg[pn][f] += v
        mins[pn] += tp
    comp = [{"player": pn, "mins": round(mins[pn]), **{k: round(cagg[pn][k],2) for k in cagg[pn]}} for pn in cagg]
    comp.sort(key=lambda x: -x.get("assists",0))
    d["compare"] = comp
    return d


# ══════════════════════════════════════════════════════════════════════════════
# 3. PITCH SVGs  (attacking RIGHT; coords normalized)
# ══════════════════════════════════════════════════════════════════════════════
PX0, PY0, PW, PH = 55, 40, 890, 580

def _pitch_lines(x0, w, full=True, vb_h=660):
    LN = 'stroke="rgba(255,255,255,0.55)" stroke-width="2" fill="none"'
    s = f'<rect x="{x0-15}" y="{PY0-15}" width="{w+30}" height="{PH+30}" rx="14" fill="url(#turf)"/>'
    stripes = 6
    for i in range(stripes):
        if i % 2 == 0: continue
        sw = w/stripes
        s += f'\n<rect x="{x0+i*sw:.1f}" y="{PY0}" width="{sw:.1f}" height="{PH}" fill="#fff" opacity="0.028"/>'
    s += f'\n<rect x="{x0}" y="{PY0}" width="{w}" height="{PH}" {LN}/>'
    if full:
        s += f'\n<line x1="{x0+w/2}" y1="{PY0}" x2="{x0+w/2}" y2="{PY0+PH}" {LN}/>'
        s += f'\n<circle cx="{x0+w/2}" cy="{PY0+PH/2}" r="62" {LN}/>'
        s += f'\n<circle cx="{x0+w/2}" cy="{PY0+PH/2}" r="4" fill="rgba(255,255,255,0.55)"/>'
    # ── right-hand attacking goal, drawn to real pitch proportions ──
    # A full pitch is 105 m x 68 m. The visible width `w` spans the whole 105 m
    # (full pitch) or half of it, 52.5 m (half pitch); box depths scale with that.
    right = x0 + w
    span_m = 105.0 if full else 52.5          # metres represented across width w
    mppx   = w / span_m                        # svg px per metre along the length
    ypm    = PH / 68.0                          # svg px per metre across the width
    box_depth = 16.5 * mppx                     # penalty area depth (18-yard box)
    six_depth = 5.5  * mppx                     # goal area depth (6-yard box)
    pen_dist  = 11.0 * mppx                     # penalty spot distance from goal
    box_h = 40.32 * ypm; box_y = PY0 + (PH - box_h)/2
    six_h = 18.32 * ypm; six_y = PY0 + (PH - six_h)/2
    goal_h = 7.32 * ypm; goal_y = PY0 + (PH - goal_h)/2
    s += f'\n<rect x="{right-box_depth:.1f}" y="{box_y:.1f}" width="{box_depth:.1f}" height="{box_h:.1f}" {LN}/>'
    s += f'\n<rect x="{right-six_depth:.1f}" y="{six_y:.1f}" width="{six_depth:.1f}" height="{six_h:.1f}" {LN}/>'
    s += f'\n<rect x="{right}" y="{goal_y:.1f}" width="12" height="{goal_h:.1f}" fill="rgba(255,255,255,0.14)" stroke="rgba(255,255,255,0.55)" stroke-width="2"/>'
    for gy in range(1, 5):                      # net hatching
        yy = goal_y + gy*(goal_h/5)
        s += f'\n<line x1="{right}" y1="{yy:.1f}" x2="{right+12}" y2="{yy:.1f}" stroke="rgba(255,255,255,0.30)" stroke-width="0.6"/>'
    s += f'\n<circle cx="{right-pen_dist:.1f}" cy="{PY0+PH/2}" r="3.5" fill="rgba(255,255,255,0.55)"/>'
    # penalty arc: part of the 9.15 m circle around the spot that sits outside the box
    arc_rx = 9.15 * mppx; arc_ry = 9.15 * ypm
    dy = ((9.15**2 - 5.5**2) ** 0.5) * ypm      # half-chord where the arc meets the box edge
    s += (f'\n<path d="M {right-box_depth:.1f} {PY0+PH/2-dy:.1f} '
          f'A {arc_rx:.1f} {arc_ry:.1f} 0 0 1 {right-box_depth:.1f} {PY0+PH/2+dy:.1f}" {LN}/>')
    return s

def _svg_head(vb_h):
    return f'''<svg viewBox="0 0 1000 {vb_h}" xmlns="http://www.w3.org/2000/svg" style="width:100%;display:block;" role="img">
  <defs>
    <linearGradient id="turf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0f6b34"/><stop offset="1" stop-color="#0a5528"/></linearGradient>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="context-stroke"/></marker>
  </defs>'''

def _dot(cx, cy, r, fill, stroke="none", sw=0, op=1.0, title=None):
    t = f'<title>{escape(title)}</title>' if title else ''
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{op}">{t}</circle>'

def _txt(cx, cy, s, size=13, fill="#fff", weight=700, anchor="middle", op=1.0):
    return (f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="{anchor}" fill="{fill}" font-size="{size}" '
            f'font-weight="{weight}" opacity="{op}" style="font-family:Helvetica Neue,Arial,sans-serif">{escape(s)}</text>')

def _link(href, inner, tip=""):
    # tip drives the custom CSS tooltip (see .pitch-tip); aria-label keeps it accessible.
    t = f' data-tip="{escape(tip)}" aria-label="{escape(tip)}"' if tip else ""
    return f'<a href="{escape(href)}" target="_blank" rel="noopener noreferrer"{t} style="cursor:pointer">{inner}</a>'

def assist_map_svg(d):
    gx = lambda X: PX0 + X/100*PW
    gy = lambda Y: PY0 + Y/100*PH
    s = _svg_head(660) + "\n" + _pitch_lines(PX0, PW, full=True)
    s += "\n" + _txt(PX0+40, PY0-20, f"◄ {d['team'].upper()} BUILD-UP", 12, "rgba(255,255,255,0.5)", 700, "start")
    s += "\n" + _txt(PX0+PW-40, PY0-20, "FINISH ►", 12, "rgba(255,255,255,0.5)", 700, "end")
    for a in d["assist_goals"]:
        if a["assistX"] is None or a["goalX"] is None: continue
        ax, ay = gx(a["assistX"]), gy(a["assistY"]); bx, by = gx(a["goalX"]), gy(a["goalY"])
        col = a["col"]; mn = a["min"]; sc = (a["scorer"] or "").split()[-1].title()
        mx, my = (ax+bx)/2, (ay+by)/2 - 46
        # both ends of the vector deep-link to the assist event instance itself
        evt_href = describe(a["assistEvt"]) if a.get("assistEvt") else describe(a["matchIri"])
        atitle = f"Assist → {sc}, {mn}' vs {a['opp']} · click to open the assist event in the Knowledge Graph"
        gtitle = f"Finish by {sc}, {mn}' vs {a['opp']} · click to open the assist event in the Knowledge Graph"
        s += f'\n<path d="M {ax:.1f} {ay:.1f} Q {mx:.1f} {my:.1f} {bx:.1f} {by:.1f}" fill="none" stroke="{col}" stroke-width="3" stroke-linecap="round" opacity="0.85" marker-end="url(#arrow)"/>'
        s += "\n" + _link(evt_href, _dot(ax, ay, 13, "rgba(0,0,0,0.35)", col, 3, 1) + _dot(ax, ay, 6, col, "#0a0a0a", 1.5, 1), atitle)
        s += "\n" + _link(evt_href, _dot(bx, by, 10, col, "#0a0a0a", 2, 1) + _dot(bx, by, 4, "#fff", "none", 0, 1), gtitle)
        s += "\n" + _txt(bx, by-16, f"{sc} {mn}'", 12, "#fff", 800)
    return s + "\n</svg>"

def shot_map_svg(d):
    """Half pitch that FILLS the frame: attacking half occupies full width, goal right."""
    vb_h = 560
    x0 = PX0; w = PW              # fill full width
    s = _svg_head(vb_h) + "\n" + _pitch_lines(x0, w, full=False, vb_h=vb_h)
    s += "\n" + _txt(x0+20, PY0-16, f"{d['name'].split()[-1].upper()} SHOT LOCATIONS · attacking ►",
                     12, "rgba(255,255,255,0.55)", 700, "start")
    # remap attacking-half data X in [50,100] -> full width [0,100]
    def gx(X):
        if X < 50: X = 100 - X
        Xf = (X - 50) * 2                     # 50..100 -> 0..100
        return x0 + Xf/100*w
    gy = lambda Y: PY0 + Y/100*PH
    for sh in d["shots"]:
        if sh["X"] is None: continue
        cx, cy = gx(sh["X"]), gy(sh["Y"]); col = sh["col"]; mn = sh["min"]
        href = describe(sh["evt"]) if sh.get("evt") else describe(sh["matchIri"])
        title = f"Shot {mn}' vs {sh['opp']} · click to open the shot event in the Knowledge Graph"
        s += "\n" + _link(href,
                          _dot(cx, cy, 9, col, "#0a0a0a", 1.6, 0.92) + _dot(cx, cy, 3, "#fff", "none", 0, 0.9), title)
    return s + "\n</svg>"


# ══════════════════════════════════════════════════════════════════════════════
# 4. RENDER HTML
# ══════════════════════════════════════════════════════════════════════════════
def gauge(label_left, label_right, pct, col):
    return (f'<div class="gauge-label"><span>{label_left}</span><span>{label_right}</span></div>'
            f'<div class="gauge-track"><div class="gauge-fill" style="width:{pct}%;'
            f'background:linear-gradient(90deg,{col},{col}88);"></div></div>')

def build_html(d, image, accent, accent2):
    image = image or d.get("kg_image", "")
    m_order = [d["meta"][k] for k in d["order"]]
    finals = d["finals"]; agg = d["agg"]; meta = d["meta"]
    name = d["name"]; team = d["team"]; jersey = d["jersey"]
    player_desc = describe(d["player_iri"])
    n_matches = len(m_order)

    # aggregate numbers
    tot_assist = int(round(agg.get("assists",0)))
    tot_goals = int(round(agg.get("goals",0)))
    tot_dist = int(round(agg.get("totalDistance",0)))
    tot_pass = int(round(agg.get("passes",0))); tot_passc = int(round(agg.get("passesCompleted",0)))
    passpct = round(100*tot_passc/tot_pass,1) if tot_pass else 0
    tot_shots = int(round(agg.get("attemptAtGoal",0))); tot_sot = int(round(agg.get("attemptAtGoalOnTarget",0)))
    tot_time = agg.get("timePlayed",0); topspeed = round(agg.get("topSpeed",0),1)
    tot_fw = int(round(agg.get("foulsFor",0))); tot_fa = int(round(agg.get("foulsAgainst",0)))
    tot_yellow = int(round(agg.get("yellowCards",0)))
    dist_per90 = int(round(tot_dist/tot_time*90)) if tot_time else 0
    per90 = lambda v: round(v/tot_time*90,2) if tot_time else 0

    # dob / age
    age = ""
    if d["dob"]:
        try:
            by = datetime.date.fromisoformat(d["dob"][:10]); age = f"{(datetime.date(2026,7,3)-by).days//365} years old"
        except Exception: pass
    dob_disp = d["dob"][:10] if d["dob"] else ""

    # squad rank on assists
    rank = 1
    for r in d["compare"]:
        if r["player"] == name: break
        if r.get("assists",0) > tot_assist: rank += 1
    rank_word = {1:"#1", 2:"#2", 3:"#3"}.get(rank, f"#{rank}")

    # assist minute list & late-game note
    amins = sorted(int(a["min"]) for a in d["assist_goals"] if a["min"] is not None)
    late_mins = [x for x in amins if x >= 53]
    late = len(late_mins)
    amins_txt = ", ".join(f"{x}'" for x in late_mins)

    C = {"accent": accent, "accent2": accent2}

    # ---- helper builders ---------------------------------------------------
    def match_short_list():
        parts = []
        for m in m_order:
            fin = finals[m["key"]]; a = int(round(fin["assists"]))
            if a: parts.append(f"{a} vs {m['opp']}")
        return " · ".join(parts) if parts else "—"

    # snapshot cards
    def big(v, unit, sub, col=""):
        cs = f'color:{col};' if col else ''
        return (f'<div class="card" style="text-align:center;"><div class="stat-big" style="{cs}">{v}</div>'
                f'<div class="stat-unit">{unit}</div><div style="font-size:11px;color:var(--muted);margin-top:8px;">{sub}</div></div>')

    snapshot = "".join([
        big(tot_assist, "Assists", match_short_list(), "#22BB66"),
        big(f"{tot_dist/1000:.1f}k", "Total Distance (m)", f"{dist_per90:,} m per 90\""),
        big(f"{passpct:.0f}%", "Pass Completion", f"{tot_passc} / {tot_pass} passes"),
        big(topspeed, "Top Speed (km/h)", "Tournament peak"),
    ])
    snapshot2 = "".join([
        big(tot_goals if tot_goals else tot_shots, "Goals" if tot_goals else "Shots",
            f"{tot_sot} on target" if not tot_goals else f"from {tot_shots} shots"),
        big(f'{int(round(tot_time))}<small style="font-size:20px;">min</small>', "Time Played",
            f"{tot_time/n_matches:.0f} min per match" if n_matches else ""),
        big(tot_fw, "Fouls Won", f"{tot_fa} committed"),
        big(tot_yellow, "Yellow Cards", "No red cards" if tot_yellow==0 else ""),
    ])

    # match cards
    def match_card(m):
        fin = finals[m["key"]]; a=int(round(fin["assists"])); g=int(round(fin["goals"]))
        pc = int(round(fin["passes"])); pcc=int(round(fin["passesCompleted"]))
        pacc = f"{100*pcc/pc:.1f}%" if pc else "—"
        sh=int(round(fin["attemptAtGoal"])); sot=int(round(fin["attemptAtGoalOnTarget"]))
        home_lbl = f"{team} {m['ts']}–{m['os']} {m['opp']}" if m["home"] else f"{m['opp']} {m['os']}–{m['ts']} {team}"
        stats = [("Assists" if a!=1 else "Assist", a, "#22BB66" if a else ""),
                 ("Goals", g, "#FFD700" if g else "") if g else ("Distance (m)", f"{int(round(fin['totalDistance'])):,}", ""),
                 ("Played", f"{fin['timePlayed']:.0f}", ""),
                 ("Passes", pc, ""), ("Pass Acc", pacc, ""),
                 ("Shots", sh, ""), ("SoT", sot, ""),
                 ("Top Speed", round(fin["topSpeed"],1), "")]
        cells = "".join(f'<div class="match-stat"><div class="val"{f" style=color:{c}" if c else ""}>{v}</div>'
                        f'<div class="lbl">{lbl}</div></div>' for lbl,v,c in stats)
        return (f'<div class="match-card"><div class="match-card-header">'
                f'<div><span class="match-card-title">{home_lbl}</span><br>'
                f'<span class="match-card-sub">{m["date"]} 2026 · {m["stage"]} · #{jersey}</span></div>'
                f'<span class="badge" style="background:{accent};color:#fff;">{m["res"]}</span></div>'
                f'<div class="match-card-stats">{cells}</div></div>')
    matches_html = "".join(match_card(m) for m in m_order)

    # passing gauges
    pass_gauges = ""
    for m in m_order:
        fin=finals[m["key"]]; pc=int(round(fin["passes"])); pcc=int(round(fin["passesCompleted"]))
        acc = 100*pcc/pc if pc else 0
        pass_gauges += gauge(f"vs {m['opp']}", f"{pc} · {acc:.1f}%", round(acc), m["col"])

    # distance gauges
    maxd = max((finals[m["key"]]["totalDistance"] for m in m_order), default=1) or 1
    dist_gauges = ""
    for m in sorted(m_order, key=lambda x:-finals[x["key"]]["totalDistance"]):
        dval = finals[m["key"]]["totalDistance"]
        dist_gauges += gauge(f"vs {m['opp']}", f"{int(round(dval)):,} m", round(100*dval/maxd), m["col"])

    # fouls-won gauges
    maxf = max((finals[m["key"]]["foulsFor"] for m in m_order), default=1) or 1
    foul_gauges = ""
    for m in sorted(m_order, key=lambda x:-finals[x["key"]]["foulsFor"]):
        fv=finals[m["key"]]["foulsFor"]
        foul_gauges += gauge(f"vs {m['opp']}", f"{int(round(fv))}", round(100*fv/maxf) if maxf else 0, m["col"])

    # legend
    legend = "".join(f'<span class="legend-chip"><span class="legend-dot" style="background:{m["col"]}"></span>{m["opp"]} · {m["res"]}</span>' for m in m_order)

    # assist minis
    def surname(n): return (n or "").split()[-1].title()
    assist_minis = "".join(
        f'<div class="assist-mini" style="border-color:{a["col"]}"><div class="amin" style="color:{a["col"]}">{a["min"]}\'</div>'
        f'<div class="ato">→ {surname(a["scorer"])}</div><div class="amatch">{a["short"]} · assist</div></div>'
        for a in d["assist_goals"] if a["min"] is not None)

    # payload for charts
    payload = {
        "matches": [{"short": m["short"], "opp": m["opp"], "res": m["res"], "col": m["col"],
                     "temporal": [{"t": round(p["t"],2),
                                   "threat": round(p["threat"],2) if p.get("threat") is not None else None,
                                   "dist": round(p["totalDistance"],1) if p.get("totalDistance") is not None else None,
                                   "passes": p.get("passes"),
                                   } for p in d["temporal"][m["key"]]]} for m in m_order],
        "colors": {m["short"]: m["col"] for m in m_order},
    }
    # halves
    def at45(pts, f):
        v=[(p["t"], p[f]) for p in pts if p.get(f) is not None]
        if not v: return 0
        for i in range(len(v)-1):
            t0,a=v[i]; t1,b=v[i+1]
            if t0<=45<=t1: return b if t1==t0 else a+(b-a)*(45-t0)/(t1-t0)
        return v[-1][1] if v[-1][0]<45 else v[0][1]
    halves=[]
    for m in m_order:
        pts=d["temporal"][m["key"]]; fin=finals[m["key"]]
        d1=at45(pts,"totalDistance")
        halves.append({"short":m["short"],"col":m["col"],"d1":round(d1),"d2":round(fin["totalDistance"]-d1)})
    payload["halves"]=halves
    # radar (player vs top team-mate by threat)
    cmp={r["player"]:r for r in d["compare"]}
    others=[r for r in d["compare"] if r["player"]!=name]
    rival = max(others, key=lambda r:r.get("threat",0)).get("player") if others else name
    AX=[("assists","Assists"),("threat","Chance\nCreation"),("crosses","Crosses"),
        ("takeOnsCompleted","Take-ons"),("attemptAtGoal","Shots"),("passes","Passes")]
    rplayers=[name]+([rival] if rival!=name else [])
    def p90(r,f):
        mm=r.get("mins",1) or 1; return (r.get(f,0) or 0)/mm*90
    radar={"labels":[a[1] for a in AX],"sets":[]}
    for pn in rplayers:
        r=cmp.get(pn,{}); vals=[]
        for f,_ in AX:
            mx=max(p90(cmp[p],f) for p in rplayers if p in cmp) or 1
            vals.append(round(p90(r,f)/mx*100,1))
        radar["sets"].append({"player":surname(pn),"vals":vals})
    payload["radar"]=radar
    payload["compare"]=[r for r in d["compare"] if r.get("assists",0)>0 or r.get("goals",0)>0][:8]

    # SPARQL section
    def q_link(q):
        return (f'{ENDPOINT}?default-graph-uri={quote_plus(KG)}&query={quote_plus(q)}'
                f'&format=text%2Fx-html%2Btr&timeout=30&run=+Run+Query+')
    q_profile = f"""PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>

DESCRIBE <{d['player_iri']}>
FROM <{KG}>"""
    q_ana = f"""PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?matchLabel ?timePlayed ?assists ?goals ?totalDistance ?passes ?threat ?topSpeed
FROM <{KG}> FROM <{ANA}>
WHERE {{
  ?m a fifa:Match ; rdfs:label ?matchLabel .
  ?m fifa:hasPlayerAnalyticsReport ?r .
  ?r fifa:player <{d['player_iri']}> ; fifa:generatedAt ?g .
  OPTIONAL {{ ?r fifa:timePlayed ?timePlayed }} OPTIONAL {{ ?r fifa:assists ?assists }}
  OPTIONAL {{ ?r fifa:goals ?goals }} OPTIONAL {{ ?r fifa:totalDistance ?totalDistance }}
  OPTIONAL {{ ?r fifa:passes ?passes }} OPTIONAL {{ ?r fifa:threat ?threat }}
  OPTIONAL {{ ?r fifa:topSpeed ?topSpeed }}
}} ORDER BY ?matchLabel DESC(?g)"""
    q_events = f"""PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?matchLabel ?typeLabel ?minute ?positionX ?positionY
FROM <{KG}>
WHERE {{
  ?m a fifa:Match ; rdfs:label ?matchLabel ; fifa:hasEvent ?e .
  ?e fifa:eventPlayer <{d['player_iri']}> ; fifa:typeLabel ?typeLabel ;
     fifa:eventMatchMinute ?minute .
  OPTIONAL {{ ?e fifa:positionX ?positionX }} OPTIONAL {{ ?e fifa:positionY ?positionY }}
}} ORDER BY ?matchLabel xsd:integer(?minute)"""
    def sparql_block(title, sub, q):
        return (f'<div class="sparql-block"><div style="font-size:13px;font-weight:700;margin-bottom:4px;">{title}</div>'
                f'<div style="font-size:12px;color:var(--muted);margin-bottom:8px;">{sub}</div>'
                f'<details><summary>SPARQL</summary><pre>{escape(q)}</pre></details>'
                f'<a class="sparql-live-link" href="{escape(q_link(q))}" target="_blank" rel="noopener noreferrer">▶ Run live query</a></div>')
    sparql_html = (sparql_block("Player Profile", f"{name} — full metadata from the FIFA KG", q_profile)
                   + sparql_block("Analytics Across Matches", "Per-match analytics snapshots (temporal)", q_ana)
                   + sparql_block("Event Coordinates", "Every on-ball event with pitch XY coordinates", q_events))

    born = f'Born <strong>{dob_disp}</strong>' + (f' · {age}' if age else '')
    pos_only = " · ".join(x for x in [d["position"], d["side"]] if x) or "Player"
    pos_line = " · ".join(x for x in [team, d["position"], d["side"]] if x)

    # sub-card fragments
    hero_img = ""
    if image:
        hero_img = (f'<div style="max-width:500px;margin:0 auto 40px;border-radius:var(--r-lg);overflow:hidden;'
                    f'background:var(--panel);box-shadow:5px 5px 14px rgba(0,0,0,0.5);">'
                    f'<img src="{escape(image)}" alt="{escape(name)}" style="width:100%;display:block;" loading="lazy">'
                    f'<div style="padding:12px 16px;font-size:11px;color:var(--muted);">{escape(name)} — {escape(team)} National Team</div></div>')
    passing_card = (_row("Total Passes", f"{tot_pass:,}") + _row("Completed", f"{tot_passc:,}")
                    + _row("Completion Rate", f"{passpct:.1f}%") + _row('Passes per 90"', per90(tot_pass))
                    + _row("Crosses", int(round(agg.get('crosses',0)))) + _row("Crosses Completed", int(round(agg.get('crossesCompleted',0)))))
    speeds = sorted((finals[m["key"]]["topSpeed"] for m in m_order), reverse=True)
    second = round(speeds[1],1) if len(speeds) > 1 else "—"
    distance_card = (_row("Total Distance", f"{tot_dist:,} m") + _row("Per 90 Minutes", f"{dist_per90:,} m")
                     + _row("Most in a Match", _extreme(m_order,finals,'totalDistance',True))
                     + _row("Least in a Match", _extreme(m_order,finals,'totalDistance',False)))
    speed_card = (_row("Top Speed", f"{topspeed} km/h") + _row("Second Fastest", f"{second} km/h")
                  + _row("Total Sprints", int(round(agg.get('sprints',0))))
                  + _row("Fouls Won", tot_fw))

    return PAGE.format(
        name=escape(name), team=escape(team), jersey=escape(str(jersey)),
        accent=accent, accent2=accent2, image=escape(image or ""),
        player_desc=escape(player_desc), player_iri=escape(d["player_iri"]),
        pos_line=escape(pos_line), pos_only=escape(pos_only), born=born, n_matches=n_matches,
        n_app=n_matches, tot_assist=tot_assist, tot_goals=tot_goals,
        agg_line=f"{team} record across {n_matches} matches",
        wdl=_wdl(m_order),
        blurb=_blurb(name, team, rank_word, tot_assist, passpct, tot_dist, topspeed, late, amins_txt),
        hero_img=hero_img, passing_card=passing_card, distance_card=distance_card, speed_card=speed_card,
        snapshot=snapshot, snapshot2=snapshot2,
        assist_map=assist_map_svg(d), legend=legend, assist_minis=assist_minis,
        creation_intro=_creation_intro(name, team, rank_word, tot_assist, d["compare"], name),
        momentum_intro=_momentum_intro(late, amins_txt),
        matches_html=matches_html,
        total_passes=tot_pass, completed=tot_passc, passpct=passpct,
        passes90=per90(tot_pass), crosses=int(round(agg.get("crosses",0))),
        crossesc=int(round(agg.get("crossesCompleted",0))),
        pass_gauges=pass_gauges, best_acc_match=_peak_pass(m_order, finals),
        tot_dist_c=f"{tot_dist:,}", dist90=f"{dist_per90:,}",
        most_dist=_extreme(m_order,finals,'totalDistance',True),
        least_dist=_extreme(m_order,finals,'totalDistance',False),
        topspeed=topspeed, sprints=int(round(agg.get("sprints",0))),
        dist_gauges=dist_gauges,
        assist_rows=_assist_rows(m_order, finals), assists90=per90(tot_assist),
        tot_shots=tot_shots, tot_sot=tot_sot, sotpct=round(100*tot_sot/tot_shots,1) if tot_shots else 0,
        offt=tot_shots-tot_sot, most_shots=_extreme(m_order,finals,'attemptAtGoal',True),
        shots90=per90(tot_shots), goals_val=tot_goals,
        shot_map=shot_map_svg(d),
        fw=tot_fw, fa=tot_fa, turnovers=int(round(agg.get("forcedTurnovers",0))),
        yellows=tot_yellow, foul_gauges=foul_gauges,
        corners_total=int(sum(d["corners_by_match"].values())),
        threat_rows=_threat_rows(m_order, finals),
        sparql_html=sparql_html,
        payload=json.dumps(payload),
        gen_date="2026-07-03",
    )

def _wdl(ms):
    w=sum(1 for m in ms if m["res"][0]=="W"); dr=sum(1 for m in ms if m["res"][0]=="D"); l=sum(1 for m in ms if m["res"][0]=="L")
    return f"{w}–{dr}–{l} W–D–L"

def _blurb(name, team, rank, a, passpct, dist, spd, late, amins):
    late_line=f" And he saves it for late: {late} of his assists came at the 53rd minute or beyond ({amins})." if late>=2 else ""
    return (f"<strong>{team}'s {rank} creator at the World Cup.</strong> {name.split()[-1].title()} tops the squad with "
            f"<strong>{a} assists</strong>, blending <strong>{passpct:.0f}% passing</strong>, "
            f"<strong>{dist/1000:.1f} km covered</strong> and a <strong>{spd} km/h</strong> top speed.{late_line}")

def _creation_intro(name, team, rank, a, compare, self_name):
    ahead  = [r for r in compare if r["player"] != self_name and r.get("assists", 0) > a][:2]
    behind = [r for r in compare if r["player"] != self_name and r.get("assists", 0) < a][:2]
    if ahead:
        vs   = ", ".join(f"{r['player'].split()[-1].title()} ({int(round(r.get('assists',0)))})" for r in ahead)
        tail = f" — behind {vs} in the squad"
    elif behind:
        vs   = ", ".join(f"{r['player'].split()[-1].title()} ({int(round(r.get('assists',0)))})" for r in behind)
        tail = f" — more than {vs}"
    else:
        tail = ""
    return (f"<strong>{team}'s {rank} creator.</strong> {name.split()[-1].title()} produced <strong>{a} assists</strong>{tail}. "
            f"Every pass below is plotted from the <strong>real event coordinates</strong> in the FIFA Knowledge Graph: "
            f"the delivery point curving to the exact location each goal was finished from.")

def _momentum_intro(late, amins):
    if late>=2:
        return (f"<strong>The closer.</strong> {late} of the assists arrived at the <strong>53rd minute or later</strong> "
                f"({amins}). As legs tire, output rises — creativity, distance and top speed all climb after the break.")
    return ("<strong>Sustained influence.</strong> Tracking the time-stamped snapshots shows a player who keeps his "
            "output high from first whistle to last.")

def _peak_pass(ms, finals):
    best=None
    for m in ms:
        fin=finals[m["key"]]; pc=fin["passes"]
        if pc:
            acc=100*fin["passesCompleted"]/pc
            if best is None or acc>best[1]: best=(m["opp"], acc)
    return f"peaked at {best[1]:.1f}% vs {best[0]}" if best else ""

def _extreme(ms, finals, field, mx):
    vals=[(m["opp"], finals[m["key"]][field]) for m in ms]
    tgt=max(vals,key=lambda x:x[1]) if mx else min(vals,key=lambda x:x[1])
    return f"{int(round(tgt[1])):,} m vs {tgt[0]}" if 'dist' in field.lower() or 'Distance' in field else f"{int(round(tgt[1]))} vs {tgt[0]}"

def _assist_rows(ms, finals):
    rows="".join(f'<div class="stat-row"><span class="stat-key">vs {m["opp"]}</span>'
                 f'<span class="stat-val">{int(round(finals[m["key"]]["assists"]))}</span></div>' for m in ms)
    return rows

def _threat_rows(ms, finals):
    return "".join(f'<div class="stat-row"><span class="stat-key">vs {m["opp"]}</span>'
                   f'<span class="stat-val">{finals[m["key"]]["threat"]:.2f}</span></div>' for m in ms)

def _row(k,v): return f'<div class="stat-row"><span class="stat-key">{k}</span><span class="stat-val">{v}</span></div>'


# ── PAGE TEMPLATE (shell CSS/JS ported from the golden report) ────────────────
PAGE = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} · 2026 FIFA World Cup · Player Intelligence Report</title>
<meta name="description" content="Player intelligence report for {name} ({team}, #{jersey}) at the 2026 FIFA World Cup: assists, creation map, temporal analytics, shot map and charts from the FIFA Knowledge Graph.">
<meta property="og:type" content="profile">
<meta property="og:title" content="{name} · 2026 FIFA World Cup · Player Intelligence Report">
<meta property="og:description" content="Player intelligence report for {name} ({team}, #{jersey}) at the 2026 FIFA World Cup: assists, creation map, temporal analytics, shot map and charts from the FIFA Knowledge Graph.">
<meta property="og:image" content="{image}">
<meta property="og:url" content="{player_iri}">
<meta property="og:site_name" content="FIFA World Cup 2026 · OpenLink Software">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{name} · 2026 FIFA World Cup · Player Intelligence Report">
<meta name="twitter:description" content="Player intelligence report for {name} ({team}, #{jersey}) at the 2026 FIFA World Cup.">
<meta name="twitter:image" content="{image}">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "{name}",
  "url": "{player_iri}",
  "image": "{image}",
  "description": "Player intelligence report for {name} ({team}, #{jersey}) at the 2026 FIFA World Cup.",
  "memberOf": {{
    "@type": "SportsTeam",
    "name": "{team}",
    "sport": "Soccer"
  }},
  "creator": {{
    "@type": "Organization",
    "name": "OpenLink Software",
    "url": "https://www.openlinksw.com"
  }},
  "keywords": ["FIFA World Cup 2026", "{name}", "{team}", "player intelligence", "knowledge graph"]
}}
</script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<style>
:root{{--ink:#FFFFFF;--muted:rgba(255,255,255,0.60);--faint:rgba(255,255,255,0.28);--bg:#060810;--panel:#0C0F1A;--panel-mid:#111629;--panel-str:#171D38;--navy:#0A1628;--line:rgba(255,255,255,0.10);--line-str:rgba(255,255,255,0.18);--r:8px;--r-lg:14px;--accent:{accent};--accent-dim:{accent2};}}
[data-theme="light"]{{--ink:#0A0E1A;--muted:rgba(0,0,0,0.60);--faint:rgba(0,0,0,0.28);--bg:#F4F6FB;--panel:#FFFFFF;--panel-mid:#EEF1F8;--panel-str:#E4E8F2;--navy:#1A3264;--line:rgba(0,0,0,0.10);--line-str:rgba(0,0,0,0.18);}}
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box;}}html{{scroll-behavior:smooth;}}
body{{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink);overflow-x:hidden;line-height:1.6;}}
a{{color:inherit;text-decoration:none;}}a.entity-link{{text-decoration:underline;text-underline-offset:3px;transition:color .2s;}}
#fnav{{position:fixed;top:24px;right:24px;z-index:1000;width:220px;background:rgba(10,22,40,0.88);backdrop-filter:blur(20px);border-radius:var(--r);box-shadow:6px 6px 18px rgba(0,0,0,0.6);}}
#fnav-header{{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;cursor:grab;}}
#fnav-title{{font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;}}
#fnav-toggle,#fnav-theme{{background:none;border:none;color:var(--muted);border-radius:4px;width:22px;height:22px;font-size:14px;cursor:pointer;}}
#fnav-links{{padding:8px 0;overflow:hidden;max-height:640px;transition:max-height .35s cubic-bezier(0.16,1,0.3,1);}}
#fnav-links.collapsed{{max-height:0;}}
#fnav-links a{{display:block;padding:6px 14px;font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);transition:color .2s,background .2s;}}
#fnav-links a:hover{{color:var(--ink);background:var(--panel-str);}}
#hero{{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:80px 40px 60px;text-align:center;position:relative;overflow:hidden;}}
#hero::before{{content:'';position:absolute;top:-200px;left:-200px;width:700px;height:700px;background:radial-gradient(circle,{accent}12,transparent 70%);pointer-events:none;}}
.hero-eyebrow{{font-size:11px;font-weight:700;letter-spacing:4px;text-transform:uppercase;margin-bottom:28px;}}
.hero-scoreline{{display:flex;align-items:center;gap:20px;margin-bottom:40px;flex-wrap:wrap;justify-content:center;}}
.hero-badge{{font-size:clamp(48px,10vw,80px);font-weight:900;line-height:1;width:clamp(100px,20vw,160px);height:clamp(100px,20vw,160px);border-radius:50%;display:flex;align-items:center;justify-content:center;background:{accent};color:#fff;box-shadow:0 0 40px {accent}4d;}}
.hero-meta{{display:flex;flex-direction:column;align-items:center;gap:6px;padding:20px 40px;border-radius:var(--r);background:rgba(255,255,255,0.03);box-shadow:inset 2px 2px 8px rgba(0,0,0,0.4);margin-bottom:40px;}}
.hero-meta-row{{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);}}
.hero-meta-row strong{{color:var(--ink);font-weight:600;}}
section{{padding:100px 60px;max-width:1400px;margin:0 auto;}}
@media(max-width:900px){{section{{padding:60px 24px;}}}}
.section-eyebrow{{font-size:10px;font-weight:700;letter-spacing:4px;text-transform:uppercase;margin-bottom:12px;color:{accent};}}
.section-title{{font-size:clamp(26px,4vw,44px);font-weight:900;line-height:1.1;margin-bottom:16px;letter-spacing:-0.5px;cursor:pointer;}}
.section-title:hover{{text-decoration:underline;text-decoration-color:{accent};text-underline-offset:5px;}}
.section-rule{{width:60px;height:2px;margin-bottom:48px;background:{accent};}}
.cards-2{{display:grid;grid-template-columns:1fr 1fr;gap:24px;}}
.cards-4{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;}}
@media(max-width:1100px){{.cards-4{{grid-template-columns:repeat(2,1fr);}}}}
@media(max-width:800px){{.cards-2,.cards-4{{grid-template-columns:1fr;}}}}
.card{{background:var(--panel);border-radius:var(--r-lg);padding:28px;box-shadow:5px 5px 14px rgba(0,0,0,0.55),-3px -3px 10px rgba(255,255,255,0.03);transition:box-shadow .3s,transform .3s;}}
.card:hover{{transform:translateY(-3px);}}
.card-title{{font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;margin-bottom:20px;cursor:pointer;}}
.stat-row{{display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid var(--line);font-size:13px;}}
.stat-row:last-child{{border-bottom:none;}} .stat-key{{color:var(--muted);}} .stat-val{{font-weight:700;font-size:15px;}}
.highlight-block{{padding:20px 28px;border-radius:var(--r);margin:32px 0;font-size:17px;font-weight:500;line-height:1.5;box-shadow:inset 2px 0 8px rgba(0,0,0,0.2);background:{accent}0d;}}
.reveal{{opacity:0;transform:translateY(28px);transition:opacity .7s cubic-bezier(0.16,1,0.3,1),transform .7s cubic-bezier(0.16,1,0.3,1);}}
.reveal.visible{{opacity:1;transform:none;}}
.badge{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;}}
.badge-assist{{background:#22BB66;color:#000;}}
.stat-big{{font-size:clamp(36px,6vw,56px);font-weight:900;line-height:1.1;}}
.stat-unit{{font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-top:4px;}}
.match-card{{background:var(--panel-mid);border-radius:var(--r-lg);padding:20px;margin-bottom:16px;box-shadow:3px 3px 10px rgba(0,0,0,0.4);}}
.match-card-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;}}
.match-card-title{{font-size:13px;font-weight:700;letter-spacing:1px;}}
.match-card-sub{{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);}}
.match-card-stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:12px;}}
@media(max-width:600px){{.match-card-stats{{grid-template-columns:repeat(2,1fr);}}}}
.match-stat{{text-align:center;}} .match-stat .val{{font-size:18px;font-weight:900;}}
.match-stat .lbl{{font-size:9px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);margin-top:4px;}}
.gauge-track{{height:8px;background:var(--panel-str);border-radius:4px;overflow:hidden;margin-bottom:12px;}}
.gauge-fill{{height:100%;border-radius:4px;transition:width .8s cubic-bezier(0.16,1,0.3,1);}}
.gauge-label{{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;display:flex;justify-content:space-between;}}
footer{{background:var(--navy);padding:60px;font-size:12px;color:var(--muted);box-shadow:0 -4px 16px rgba(0,0,0,0.5);}}
.attribution-card{{background:var(--panel);border-radius:var(--r);padding:18px 20px;box-shadow:3px 3px 8px rgba(0,0,0,0.5);}}
.attribution-card.wide{{grid-column:span 2;}}
.attribution-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;}}
@media(max-width:900px){{.attribution-grid{{grid-template-columns:1fr;}}.attribution-card.wide{{grid-column:span 1;}}}}
.attribution-label{{display:block;font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:10px;opacity:0.7;}}
.attribution-card p{{font-size:11px;line-height:1.7;}} .attribution-card code{{font-size:10px;background:var(--panel-str);padding:2px 6px;border-radius:3px;word-break:break-all;}}
.attribution-links{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;}}
.attribution-pill{{display:inline-block;padding:5px 10px;font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;background:var(--panel-str);border-radius:var(--r);color:var(--muted);}}
details summary{{cursor:pointer;list-style:none;display:flex;justify-content:space-between;align-items:center;}}
details summary::-webkit-details-marker{{display:none;}} details summary::after{{content:'\FF0B';font-size:16px;}} details[open] summary::after{{content:'\FF0D';}}
.sparql-block{{background:var(--panel);border-radius:var(--r-lg);padding:28px;margin-bottom:24px;box-shadow:4px 4px 12px rgba(0,0,0,0.5);}}
.sparql-block pre{{background:var(--panel-str);border-radius:var(--r);padding:20px;font-size:12px;overflow-x:auto;line-height:1.7;font-family:'Courier New',monospace;white-space:pre;}}
.sparql-block details{{background:var(--panel-str);border-radius:var(--r);padding:16px 20px;margin-top:16px;}}
.sparql-block details summary{{font-size:12px;font-weight:700;letter-spacing:1px;color:var(--muted);text-transform:uppercase;}}
.sparql-live-link{{display:inline-block;margin-top:14px;padding:10px 20px;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;background:var(--panel-str);border-radius:var(--r);}}
/* charts + pitch */
.pitch-wrap{{background:linear-gradient(160deg,#0b1220,#0a1a12);border-radius:var(--r-lg);padding:14px;box-shadow:inset 0 2px 20px rgba(0,0,0,0.55),5px 5px 16px rgba(0,0,0,0.5);}}
.chart-card{{background:var(--panel);border-radius:var(--r-lg);padding:24px;box-shadow:5px 5px 14px rgba(0,0,0,0.55),-3px -3px 10px rgba(255,255,255,0.03);}}
.chart-sub{{font-size:11px;color:var(--muted);margin-bottom:16px;line-height:1.5;}}
.chart-holder{{position:relative;width:100%;}}
.legend-row{{display:flex;flex-wrap:wrap;gap:14px;margin:18px 0 4px;justify-content:center;}}
.legend-chip{{display:flex;align-items:center;gap:7px;font-size:11px;font-weight:600;letter-spacing:.5px;color:var(--muted);}}
.legend-dot{{width:12px;height:12px;border-radius:50%;}}
.assist-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-top:24px;}}
@media(max-width:1000px){{.assist-grid{{grid-template-columns:repeat(2,1fr);}}}}
@media(max-width:600px){{.assist-grid{{grid-template-columns:1fr;}}}}
.assist-mini{{background:var(--panel-mid);border-radius:var(--r);padding:14px 16px;box-shadow:3px 3px 10px rgba(0,0,0,.4);border-left:3px solid;}}
.assist-mini .amin{{font-size:22px;font-weight:900;line-height:1;}} .assist-mini .ato{{font-size:12px;font-weight:700;margin-top:6px;}}
.assist-mini .amatch{{font-size:9px;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);margin-top:5px;}}
.insight{{display:flex;gap:16px;align-items:flex-start;padding:20px 26px;border-radius:var(--r);margin:8px 0 0;background:linear-gradient(120deg,rgba(34,187,102,0.10),{accent}0d);box-shadow:inset 2px 0 10px rgba(0,0,0,.2);border-left:3px solid #22BB66;}}
.insight .ico{{font-size:26px;}} .insight p{{font-size:15px;line-height:1.55;margin:0;}} .insight strong{{color:var(--ink);}}
.charts-2{{display:grid;grid-template-columns:1fr 1fr;gap:20px;}}
@media(max-width:900px){{.charts-2{{grid-template-columns:1fr;}}}}
.pitch-caption{{font-size:11px;color:var(--muted);margin-top:12px;text-align:center;line-height:1.5;}}
.pitch-tip{{position:fixed;z-index:99999;pointer-events:none;opacity:0;transform:translateY(3px);transition:opacity .06s ease,transform .06s ease;background:var(--panel-str);color:var(--ink);font-size:12px;font-weight:600;letter-spacing:.2px;padding:8px 12px;border-radius:8px;max-width:260px;line-height:1.45;box-shadow:0 8px 24px rgba(0,0,0,.55);border:1px solid var(--line-str);}}
.pitch-tip.show{{opacity:1;transform:none;}}
.pitch-tip .tk{{display:block;font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);margin-top:5px;}}
svg a[data-tip]{{cursor:pointer;}}
</style>
</head>
<body>
<nav id="fnav" role="navigation" aria-label="Page sections">
  <div id="fnav-header"><span id="fnav-title">Player Intel</span>
    <div style="display:flex;gap:6px;"><button id="fnav-theme" aria-label="Toggle theme">☀</button><button id="fnav-toggle" aria-label="Toggle navigation">−</button></div>
  </div>
  <div id="fnav-links">
    <a href="#hero">Overview</a><a href="#snapshot">Snapshot</a><a href="#creation">Creation Map</a>
    <a href="#momentum">Momentum</a><a href="#matches">Match Log</a><a href="#passing">Passing</a>
    <a href="#physical">Physical</a><a href="#attacking">Attacking</a><a href="#creative">vs {team}</a>
    <a href="#defensive">Defensive</a><a href="#progression">Progression</a><a href="#sparql">SPARQL</a><a href="#sources">Sources</a>
  </div>
</nav>

<section id="hero">
  <div class="hero-eyebrow">2026 FIFA World Cup · {team} · {pos_only} · #{jersey}</div>
  <div class="hero-scoreline"><div class="hero-badge">{jersey}</div></div>
  <div class="hero-team-name" style="font-size:clamp(36px,6vw,64px);font-weight:900;margin-bottom:12px;">
    <a class="entity-link" href="{player_desc}" target="_blank" rel="noopener noreferrer" title="Open {name} in the FIFA Knowledge Graph">{name}</a>
  </div>
  <div class="hero-meta">
    <div class="hero-meta-row"><strong>{pos_line}</strong></div>
    <div class="hero-meta-row">{born}</div>
    <div class="hero-meta-row"><span class="badge" style="background:{accent};color:#fff;">{n_app} Appearances</span> <span class="badge badge-assist" style="margin-left:8px;">{tot_assist} Assists</span> <span class="badge" style="background:{accent2};color:#fff;margin-left:8px;">{tot_goals} Goals</span></div>
    <div class="hero-meta-row">{agg_line} · <strong>{wdl}</strong></div>
  </div>
  {hero_img}
  <div class="highlight-block" style="max-width:720px;">{blurb}</div>
</section>

<section id="snapshot" class="reveal">
  <div class="section-eyebrow">At a Glance</div><div class="section-title">Tournament Aggregate</div><div class="section-rule"></div>
  <div class="cards-4" style="margin-bottom:40px;">{snapshot}</div>
  <div class="cards-4">{snapshot2}</div>
</section>

<section id="creation" class="reveal">
  <div class="section-eyebrow" style="color:#22BB66;">Assist Geometry · from event XY coordinates</div>
  <div class="section-title">How {name} Creates Goals</div><div class="section-rule" style="background:#22BB66;"></div>
  <div class="insight" style="margin-bottom:32px;"><span class="ico">🎯</span><p>{creation_intro}</p></div>
  <div class="pitch-wrap">{assist_map}</div>
  <div class="legend-row">{legend}</div>
  <div class="pitch-caption">Hollow ring = assist origin · solid dot = finish location · arrow = pass-to-goal. Click any marker to open it in the Knowledge Graph. Coordinates normalised so {team} always attacks right.</div>
  <div class="assist-grid">{assist_minis}</div>
</section>

<section id="momentum" class="reveal">
  <div class="section-eyebrow" style="color:#FB923C;">Temporal Analytics · in-match snapshots</div>
  <div class="section-title">How He Changes the Game</div><div class="section-rule" style="background:#FB923C;"></div>
  <p style="max-width:820px;font-size:14px;color:var(--muted);margin-bottom:28px;line-height:1.7;">The FIFA Knowledge Graph stores <strong style="color:var(--ink)">time-stamped analytics snapshots</strong> taken throughout each match. Tracked against minutes played, they reveal <em>when</em> his influence peaks.</p>
  <div class="insight" style="margin-bottom:32px;"><span class="ico">⏱️</span><p>{momentum_intro}</p></div>
  <div class="charts-2">
    <div class="chart-card"><div class="card-title">Threat Trajectory (xT)</div><div class="chart-sub">In-match Expected Threat rating across the matches. Higher = more dangerous with the ball.</div><div class="chart-holder"><canvas id="cThreat" height="230"></canvas></div></div>
    <div class="chart-card"><div class="card-title">Distance Engine</div><div class="chart-sub">Cumulative ground covered vs minutes played — the work-rate ramp to the final whistle.</div><div class="chart-holder"><canvas id="cDist" height="230"></canvas></div></div>
    <div class="chart-card"><div class="card-title">Passing Volume Build-up</div><div class="chart-sub">Cumulative passes played through the match — how constantly involved he stays.</div><div class="chart-holder"><canvas id="cPass" height="230"></canvas></div></div>
    <div class="chart-card"><div class="card-title">First Half vs Second Half</div><div class="chart-sub">Distance covered per half — does he sustain his output after the interval?</div><div class="chart-holder"><canvas id="cHalves" height="230"></canvas></div></div>
  </div>
</section>

<section id="matches" class="reveal">
  <div class="section-eyebrow">Match by Match</div><div class="section-title">Performance Log</div><div class="section-rule"></div>
  {matches_html}
</section>

<section id="passing" class="reveal">
  <div class="section-eyebrow">Distribution</div><div class="section-title">Passing &amp; Creativity</div><div class="section-rule"></div>
  <div class="cards-2">
    <div class="card"><div class="card-title">Passing Volume</div>
      {passing_card}
    </div>
    <div class="card"><div class="card-title">Match-by-Match Passing</div>{pass_gauges}
      <div style="margin-top:16px;font-size:11px;color:var(--muted);">{best_acc_match}.</div></div>
  </div>
</section>

<section id="physical" class="reveal">
  <div class="section-eyebrow">Athletic Output</div><div class="section-title">Distance, Speed &amp; Intensity</div><div class="section-rule"></div>
  <div class="cards-2">
    <div class="card"><div class="card-title">Distance Coverage</div>{distance_card}</div>
    <div class="card"><div class="card-title">Speed &amp; Sprint</div>{speed_card}</div>
  </div>
  <div class="card" style="margin-top:24px;"><div class="card-title">Distance Per Match</div>{dist_gauges}</div>
</section>

<section id="attacking" class="reveal">
  <div class="section-eyebrow">Final Third</div><div class="section-title">Attacking Contribution</div><div class="section-rule"></div>
  <div class="cards-2">
    <div class="card"><div class="card-title">Assists Breakdown</div>
      <div class="stat-row"><span class="stat-key">Total Assists</span><span class="stat-val" style="color:#22BB66;font-size:20px;">{tot_assist}</span></div>
      {assist_rows}
      <div class="stat-row"><span class="stat-key">Assists per 90"</span><span class="stat-val">{assists90}</span></div></div>
    <div class="card"><div class="card-title">Shooting</div>
      <div class="stat-row"><span class="stat-key">Total Shots</span><span class="stat-val">{tot_shots}</span></div>
      <div class="stat-row"><span class="stat-key">Shots on Target</span><span class="stat-val">{tot_sot} ({sotpct}%)</span></div>
      <div class="stat-row"><span class="stat-key">Shots off Target</span><span class="stat-val">{offt}</span></div>
      <div class="stat-row"><span class="stat-key">Most Shots</span><span class="stat-val">{most_shots}</span></div>
      <div class="stat-row"><span class="stat-key">Shots per 90"</span><span class="stat-val">{shots90}</span></div>
      <div class="stat-row"><span class="stat-key">Goals</span><span class="stat-val" style="color:#BFA060;">{goals_val}</span></div></div>
  </div>
  <div class="card chart-card" style="margin-top:24px;"><div class="card-title">Shot Map · {tot_shots} attempts</div>
    <div class="chart-sub">Every attempt at goal, plotted from real event coordinates (attacking right). Click a marker to open the match in the Knowledge Graph.</div>
    <div class="pitch-wrap">{shot_map}</div><div class="legend-row">{legend}</div></div>
</section>

<section id="creative" class="reveal">
  <div class="section-eyebrow" style="color:#22D3EE;">Squad Context</div><div class="section-title">The Engine Room of {team}</div><div class="section-rule" style="background:#22D3EE;"></div>
  <div class="charts-2">
    <div class="chart-card"><div class="card-title">{team} Assist Leaders</div><div class="chart-sub">Assists across the tournament by {team} players.</div><div class="chart-holder"><canvas id="cAssistLeaders" height="260"></canvas></div></div>
    <div class="chart-card"><div class="card-title">Creative Profile</div><div class="chart-sub">Per-90 output vs the squad's other main threat, each axis scaled to the higher of the two.</div><div class="chart-holder"><canvas id="cRadar" height="260"></canvas></div></div>
  </div>
</section>

<section id="defensive" class="reveal">
  <div class="section-eyebrow">Work Rate</div><div class="section-title">Pressing &amp; Ball Recovery</div><div class="section-rule"></div>
  <div class="cards-2">
    <div class="card"><div class="card-title">Defensive Actions</div>
      <div class="stat-row"><span class="stat-key">Forced Turnovers</span><span class="stat-val">{turnovers}</span></div>
      <div class="stat-row"><span class="stat-key">Fouls Won</span><span class="stat-val">{fw}</span></div>
      <div class="stat-row"><span class="stat-key">Fouls Committed</span><span class="stat-val">{fa}</span></div>
      <div class="stat-row"><span class="stat-key">Yellow Cards</span><span class="stat-val">{yellows}</span></div></div>
    <div class="card"><div class="card-title">Fouls Won per Match</div>{foul_gauges}</div>
  </div>
</section>

<section id="progression" class="reveal">
  <div class="section-eyebrow">Progression</div><div class="section-title">Ball Progression &amp; Threat</div><div class="section-rule"></div>
  <div class="cards-2">
    <div class="card"><div class="card-title">Ball Progression</div>
      <div class="stat-row"><span class="stat-key">Corners Taken</span><span class="stat-val">{corners_total}</span></div>
      <div class="stat-row"><span class="stat-key">Crosses</span><span class="stat-val">{crosses}</span></div>
      <div class="stat-row"><span class="stat-key">Crosses Completed</span><span class="stat-val">{crossesc}</span></div></div>
    <div class="card"><div class="card-title">Expected Threat (xT) · final per match</div>{threat_rows}</div>
  </div>
</section>

<section id="sparql" class="reveal">
  <div class="section-eyebrow">Knowledge Graph</div><div class="section-title">SPARQL Queries</div><div class="section-rule"></div>
  {sparql_html}
</section>

<footer id="sources">
  <h2 style="font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin-bottom:24px;opacity:0.6;">Attribution &amp; Provenance</h2>
  <div class="attribution-grid">
    <article class="attribution-card wide"><span class="attribution-label">Source material</span>
      <p>All data sourced live from the <a class="entity-link" href="{player_desc}" target="_blank" rel="noopener noreferrer">FIFA World Cup 2026 Knowledge Graph</a> via <a class="entity-link" href="https://demo.openlinksw.com/sparql" target="_blank" rel="noopener noreferrer">demo.openlinksw.com/sparql</a>. Assist &amp; shot maps use real <code>fifa:positionX</code>/<code>fifa:positionY</code> event coordinates; momentum charts use time-stamped <code>fifa:PlayerMatchAnalyticsReport</code> snapshots.</p></article>
    <article class="attribution-card"><span class="attribution-label">Skills used</span>
      <div class="attribution-links"><a class="attribution-pill" href="https://demo.openlinksw.com/describe/?url=https%3A%2F%2Fwww.openlinksw.com%2Fontology%2Ffifa%23" target="_blank" rel="noopener noreferrer">world-cup-2026-navigator</a></div>
      <p>Ontology navigation, SPARQL patterns and the coordinate/temporal model.</p></article>
    <article class="attribution-card"><span class="attribution-label">Generation</span>
      <p>Generated by <code>player_report_create.py</code> on {gen_date}, driven by <a class="entity-link" href="https://demo.openlinksw.com/describe/?url=https%3A%2F%2Fwww.anthropic.com%2Fclaude-code%23this" target="_blank" rel="noopener noreferrer">Claude Code</a>.</p></article>
    <article class="attribution-card"><span class="attribution-label">Named graphs</span>
      <p><code>urn:worldcup:kg:2026</code> — matches, goals, events, coordinates.<br><code>urn:worldcup:kg:2026:analytics</code> — temporal analytics snapshots.</p></article>
    <article class="attribution-card"><span class="attribution-label">Runtime</span>
      <p>SPARQL endpoint powered by <a class="entity-link" href="https://demo.openlinksw.com/describe/?url=https%3A%2F%2Fdbpedia.org%2Fresource%2FOpenLink_Virtuoso" target="_blank" rel="noopener noreferrer">OpenLink Virtuoso</a>.</p></article>
    <article class="attribution-card"><span class="attribution-label">Resolver pattern</span>
      <p>Entity links route through:<br><code>https://demo.openlinksw.com/describe/?url={{IRI}}</code></p></article>
  </div>
  <p style="font-size:11px;color:var(--muted);border-top:1px solid var(--line-str);margin-top:32px;padding-top:20px;">© 2026 <a class="entity-link" href="https://www.openlinksw.com/" target="_blank" rel="noopener noreferrer">OpenLink Software</a> · FIFA World Cup 2026 Player Intelligence · {name} ({team}, #{jersey})</p>
</footer>

<script>
(function(){{
  var nav=document.getElementById('fnav'),hdr=document.getElementById('fnav-header');
  var links=document.getElementById('fnav-links'),tog=document.getElementById('fnav-toggle'),thm=document.getElementById('fnav-theme');
  var dragging=false,ox=0,oy=0,sx=0,sy=0,collapsed=false;
  try{{collapsed=localStorage.getItem('fnav-collapsed')==='1';}}catch(e){{}}
  if(collapsed){{links.classList.add('collapsed');tog.textContent='+';}}
  hdr.addEventListener('mousedown',function(e){{if(e.target===tog||e.target===thm)return;dragging=true;ox=e.clientX;oy=e.clientY;var r=nav.getBoundingClientRect();sx=r.left;sy=r.top;nav.style.right='auto';document.addEventListener('mousemove',mv);document.addEventListener('mouseup',mu);}});
  function mv(e){{if(!dragging)return;nav.style.left=(sx+e.clientX-ox)+'px';nav.style.top=(sy+e.clientY-oy)+'px';}}
  function mu(){{dragging=false;document.removeEventListener('mousemove',mv);document.removeEventListener('mouseup',mu);}}
  tog.addEventListener('click',function(){{collapsed=!collapsed;links.classList.toggle('collapsed',collapsed);tog.textContent=collapsed?'+':'−';try{{localStorage.setItem('fnav-collapsed',collapsed?'1':'0');}}catch(e){{}}}});
  thm.addEventListener('click',function(){{var dd=document.documentElement;dd.setAttribute('data-theme',dd.getAttribute('data-theme')==='light'?'dark':'light');}});
  var io=new IntersectionObserver(function(e){{e.forEach(function(x){{if(x.isIntersecting)x.target.classList.add('visible');}});}},{{threshold:0.10}});
  document.querySelectorAll('.reveal').forEach(function(el){{io.observe(el);}});
}})();

// ── instant, CSS-styled tooltips for the pitch markers (both maps) ──
(function(){{
  var tip=document.createElement('div');
  tip.className='pitch-tip';
  document.body.appendChild(tip);
  function place(e){{
    var pad=15, tw=tip.offsetWidth, th=tip.offsetHeight;
    var x=e.clientX+pad, y=e.clientY-th-8;
    if(x+tw>window.innerWidth-6) x=e.clientX-tw-pad;
    if(y<6) y=e.clientY+22;
    tip.style.left=x+'px'; tip.style.top=y+'px';
  }}
  function render(raw){{
    var i=raw.indexOf(' · ');
    if(i>-1){{ tip.innerHTML=''; tip.appendChild(document.createTextNode(raw.slice(0,i)));
      var cue=document.createElement('span'); cue.className='tk'; cue.textContent=raw.slice(i+3); tip.appendChild(cue); }}
    else tip.textContent=raw;
  }}
  function bind(a){{
    a.addEventListener('mouseenter',function(e){{render(a.getAttribute('data-tip'));tip.classList.add('show');place(e);}});
    a.addEventListener('mousemove',place);
    a.addEventListener('mouseleave',function(){{tip.classList.remove('show');}});
    a.addEventListener('blur',function(){{tip.classList.remove('show');}});
  }}
  document.querySelectorAll('svg a[data-tip]').forEach(bind);
}})();

(function(){{
  if(typeof Chart==='undefined')return;
  var D={payload};
  Chart.defaults.font.family="'Helvetica Neue', Helvetica, Arial, sans-serif";
  function dark(){{return document.documentElement.getAttribute('data-theme')!=='light';}}
  function grid(){{return dark()?'rgba(255,255,255,0.07)':'rgba(0,0,0,0.07)';}}
  function ink(){{return dark()?'rgba(255,255,255,0.60)':'rgba(0,0,0,0.60)';}}
  var CH=[]; function reg(c){{CH.push(c);return c;}}
  function lineOpts(xT,yT){{return{{responsive:true,maintainAspectRatio:false,interaction:{{mode:'nearest',intersect:false}},
    plugins:{{legend:{{display:true,labels:{{color:ink(),usePointStyle:true,boxWidth:8,font:{{size:11}}}}}},tooltip:{{callbacks:{{title:function(it){{return 'Min '+Math.round(it[0].parsed.x);}}}}}}}},
    scales:{{x:{{type:'linear',min:0,max:98,title:{{display:true,text:xT,color:ink()}},grid:{{color:grid()}},ticks:{{color:ink()}}}},y:{{beginAtZero:true,title:{{display:true,text:yT,color:ink()}},grid:{{color:grid()}},ticks:{{color:ink()}}}}}}}};}}
  function sl(field){{return D.matches.map(function(m){{return{{label:m.short,borderColor:D.colors[m.short],backgroundColor:D.colors[m.short],tension:0.35,borderWidth:2.5,pointRadius:2.5,pointHoverRadius:5,data:m.temporal.filter(function(p){{return p[field]!=null;}}).map(function(p){{return{{x:p.t,y:p[field]}};}})}};}});}}
  if(document.getElementById('cThreat'))reg(new Chart(document.getElementById('cThreat'),{{type:'line',data:{{datasets:sl('threat')}},options:lineOpts('Minutes played','Threat (xT)')}}));
  if(document.getElementById('cDist'))reg(new Chart(document.getElementById('cDist'),{{type:'line',data:{{datasets:sl('dist')}},options:lineOpts('Minutes played','Distance covered (m)')}}));
  if(document.getElementById('cPass'))reg(new Chart(document.getElementById('cPass'),{{type:'line',data:{{datasets:sl('passes')}},options:lineOpts('Minutes played','Passes played')}}));
  if(document.getElementById('cHalves'))reg(new Chart(document.getElementById('cHalves'),{{type:'bar',data:{{labels:D.halves.map(function(h){{return h.short;}}),datasets:[{{label:'First half',data:D.halves.map(function(h){{return h.d1;}}),backgroundColor:D.halves.map(function(h){{return h.col+'99';}}),borderColor:D.halves.map(function(h){{return h.col;}}),borderWidth:1,borderRadius:4}},{{label:'Second half',data:D.halves.map(function(h){{return h.d2;}}),backgroundColor:D.halves.map(function(h){{return h.col+'44';}}),borderColor:D.halves.map(function(h){{return h.col;}}),borderWidth:1,borderRadius:4,borderDash:[4,4]}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{labels:{{color:ink(),font:{{size:11}}}}}},tooltip:{{callbacks:{{label:function(c){{return c.dataset.label+': '+c.parsed.y.toLocaleString()+' m';}}}}}}}},scales:{{x:{{grid:{{color:grid()}},ticks:{{color:ink()}}}},y:{{beginAtZero:true,grid:{{color:grid()}},ticks:{{color:ink()}},title:{{display:true,text:'Distance (m)',color:ink()}}}}}}}}}}));
  var lead=D.compare.slice().sort(function(a,b){{return (b.assists||0)-(a.assists||0);}}).slice(0,7);
  if(document.getElementById('cAssistLeaders'))reg(new Chart(document.getElementById('cAssistLeaders'),{{type:'bar',data:{{labels:lead.map(function(r){{return r.player.split(' ').slice(-1)[0];}}),datasets:[{{label:'Assists',data:lead.map(function(r){{return r.assists||0;}}),backgroundColor:lead.map(function(r){{return r.player==='{name}'?'#22BB66':'#334066';}}),borderColor:lead.map(function(r){{return r.player==='{name}'?'#22BB66':'#4a5a80';}}),borderWidth:1,borderRadius:5}}]}},options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:function(c){{return c.parsed.x+' assists';}}}}}}}},scales:{{x:{{beginAtZero:true,grid:{{color:grid()}},ticks:{{color:ink(),precision:0}}}},y:{{grid:{{display:false}},ticks:{{color:ink(),font:{{weight:'700'}}}}}}}}}}}}));
  var rc=['#22BB66','{accent2}'];
  if(document.getElementById('cRadar'))reg(new Chart(document.getElementById('cRadar'),{{type:'radar',data:{{labels:D.radar.labels,datasets:D.radar.sets.map(function(s,i){{return{{label:s.player,data:s.vals,borderColor:rc[i],backgroundColor:rc[i]+'2e',borderWidth:2,pointBackgroundColor:rc[i],pointRadius:3}};}})}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{labels:{{color:ink(),usePointStyle:true,boxWidth:8}}}}}},scales:{{r:{{min:0,max:100,angleLines:{{color:grid()}},grid:{{color:grid()}},pointLabels:{{color:ink(),font:{{size:11,weight:'600'}}}},ticks:{{display:false,stepSize:25}}}}}}}}}}));
  new MutationObserver(function(){{CH.forEach(function(c){{if(c.options.plugins&&c.options.plugins.legend&&c.options.plugins.legend.labels)c.options.plugins.legend.labels.color=ink();if(c.options.scales)Object.values(c.options.scales).forEach(function(ax){{if(ax.grid)ax.grid.color=grid();if(ax.ticks)ax.ticks.color=ink();if(ax.angleLines)ax.angleLines.color=grid();if(ax.pointLabels)ax.pointLabels.color=ink();if(ax.title)ax.title.color=ink();}});c.update('none');}});}}).observe(document.documentElement,{{attributes:true,attributeFilter:['data-theme']}});
}})();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(
        description="Generate a FIFA WC2026 player intelligence report from the Knowledge Graph.")
    ap.add_argument("player", help='Numeric player id (e.g. 485655) OR a name/fragment (e.g. "Jude Bellingham").')
    ap.add_argument("--out", default=None, help="Output HTML path (default: <name>-wc2026-report.html)")
    ap.add_argument("--image", default="", help="Optional player photo URL for the hero.")
    ap.add_argument("--accent", default=None, help="Primary accent hex (default: auto from nation).")
    ap.add_argument("--accent2", default=None, help="Secondary accent hex (default: auto).")
    args = ap.parse_args()

    # Accept either a numeric id or a name fragment.
    player_id = args.player if args.player.isdigit() else resolve_player(args.player)

    d = collect(player_id)
    d = transform(d)

    # Auto-theme by nation unless the caller overrides the colours.
    accent, accent2 = team_accents(d.get("team", ""))
    accent = args.accent or accent
    accent2 = args.accent2 or accent2

    html = build_html(d, args.image, accent, accent2)

    out = args.out or (d["name"].lower().replace(" ", "-") + "-wc2026-report.html")
    with open(out, "w") as f:
        f.write(html)
    print(f"✓ wrote {out}  ({len(html):,} bytes)  · {d['name']} ({d.get('team','?')}) · "
          f"{len(d['order'])} matches · {int(round(d['agg'].get('assists',0)))} assists · "
          f"{len(d['assist_goals'])} assist maps · accent {accent}")


if __name__ == "__main__":
    main()
