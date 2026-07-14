#!/usr/bin/env python3
"""
Generate a variant of the World Cup 2026 TTL that includes:
- TSV-derived hash IRIs for players, countries, clubs
- All TSV attributes on those hash IRIs (including ones missing from TTL)
- owl:sameAs links from TTL entities to TSV hash IRIs
"""

import csv, io, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from collections import defaultdict, Counter

import rdflib
from rdflib.namespace import RDF, OWL

# --- CONFIG ---
TSV_PATH   = "/Users/kidehen/Documents/CSV Files/players-enriched.tsv"
SOURCE_TTL = "/Users/kidehen/Documents/LLMs/GPT5-Chat-Generated/rdf/world-cup-2026-country-player-guide-meshup-gpt5-chat-1.ttl"
OUTPUT_TTL = "/Users/kidehen/Documents/LLMs/GPT5-Chat-Generated/rdf/world-cup-2026-country-player-guide-meshup-gpt5-chat-1-tsv-variant.ttl"
TSV_BASE   = "https://github.com/matyuschenko/fifa-wc2026-players/blob/main/data/players.tsv"

POSITION_MAP = {"GK": "Goalkeeper", "DF": "Defender", "MF": "Midfielder", "FW": "Forward"}
UA = "WC2026-TTLVariant/1.0"

# --- Utility ---
def strip_country(s):
    return re.sub(r'\s+\([A-Z]{3}\)$', '', s).strip()

def make_slug(name):
    name = name.strip()
    name = re.sub(r'\s*\([A-Z]{3}\)\s*$', '', name)
    name = re.sub(r'[^\w\s.-]', '', name)
    name = re.sub(r'\s+', '-', name)
    return name

# --- 1. Parse enriched TSV ---
print("=== Step 1: Parse enriched TSV ===")
with open(TSV_PATH, newline="") as f:
    rows = list(csv.DictReader(f, delimiter="\t"))
n = len(rows)
print(f"  {n} rows  |  {len(rows[0]) if rows else 0} columns")

country_rows = {}
player_by_qid = {}
player_by_team_shirt = {}
club_names_set = set()

for r in rows:
    t = r["Team"]
    s = r["#"]
    q = r.get("PLAYER_WIKIDATA", "")
    country_rows.setdefault(t, r)
    if q:
        player_by_qid[q] = r
    player_by_team_shirt[(t, s)] = r
    club_names_set.add(r["CLUB"])

country_info = {}
for t in country_rows:
    m = re.match(r'^(.+?)\s+\(([A-Z]{3})\)$', t)
    country_info[t] = {"display": m.group(1).strip(), "code": m.group(2)} if m else {"display": t, "code": t[:3].upper()}

club_names = sorted(club_names_set)
print(f"  {len(country_rows)} teams  |  {len(club_names)} unique clubs")

# --- 2. Parse source TTL ---
print("\n=== Step 2: Parse source TTL ===")
g = rdflib.Graph()
g.parse(SOURCE_TTL, format="turtle")
print(f"  {len(g)} triples")

SCHEMA_PERSON = rdflib.URIRef("http://schema.org/Person")
SCHEMA_SPORTSTEAM = rdflib.URIRef("http://schema.org/SportsTeam")
SCHEMA_COUNTRY = rdflib.URIRef("http://schema.org/Country")
SCHEMA_NAME = rdflib.URIRef("http://schema.org/name")
SCHEMA_MEMBEROF = rdflib.URIRef("http://schema.org/memberOf")
SCHEMA_ADDPROP = rdflib.URIRef("http://schema.org/additionalProperty")

ttl_by_qid = {}
ttl_by_dbpedia = {}
ttl_by_team_shirt = {}

for s, _ in g.subject_objects(RDF.type):
    pass
for s, p, o in g.triples((None, RDF.type, SCHEMA_PERSON)):
    has_shirt = False
    shirt_num = None
    team_uri = None
    wd_qid = None
    for _, p2, o2 in g.triples((s, None, None)):
        if p2 == SCHEMA_ADDPROP:
            for _, p3, o3 in g.triples((o2, None, None)):
                if str(p3) == "http://schema.org/name" and str(o3) == "shirt number":
                    has_shirt = True
                if str(p3) == "http://schema.org/value":
                    shirt_num = str(o3)
        elif p2 == SCHEMA_MEMBEROF:
            team_uri = str(o2)
        elif p2 == OWL.sameAs:
            m = re.search(r'/entity/(Q\d+)', str(o2))
            if m:
                wd_qid = m.group(1)
    if has_shirt and shirt_num:
        s_str = str(s)
        if wd_qid:
            ttl_by_qid[wd_qid] = s
        if "dbpedia.org" in s_str:
            ttl_by_dbpedia[s_str] = s
        if team_uri and shirt_num:
            ttl_by_team_shirt[(team_uri, shirt_num)] = s

print(f"  Players indexed: Q-ID={len(ttl_by_qid)}, DBpedia={len(ttl_by_dbpedia)}, (team,shirt)={len(ttl_by_team_shirt)}")

# Index team entities
ttl_team_by_qid = {}
ttl_team_by_name = {}
for s, _, _ in g.triples((None, RDF.type, SCHEMA_SPORTSTEAM)):
    qid = name = None
    for _, p2, o2 in g.triples((s, None, None)):
        if p2 == OWL.sameAs:
            m = re.search(r'/entity/(Q\d+)', str(o2))
            if m: qid = m.group(1)
        elif p2 == SCHEMA_NAME:
            name = str(o2)
    if qid: ttl_team_by_qid[qid] = s
    if name: ttl_team_by_name[name.lower()] = s
for s, _, _ in g.triples((None, RDF.type, SCHEMA_COUNTRY)):
    qid = name = None
    for _, p2, o2 in g.triples((s, None, None)):
        if p2 == OWL.sameAs:
            m = re.search(r'/entity/(Q\d+)', str(o2))
            if m: qid = m.group(1)
        elif p2 == SCHEMA_NAME:
            name = str(o2)
    if qid: ttl_team_by_qid[qid] = s
    if name: ttl_team_by_name[name.lower()] = s

print(f"  Team/country entities indexed: Q-ID={len(ttl_team_by_qid)}, name={len(ttl_team_by_name)}")

# --- 3. Club Wikidata/DBpedia resolution ---
print("\n=== Step 3: Club Wikidata/DBpedia resolution ===")

DBPEDIA_SPARQL = "https://dbpedia.org/sparql"
WIKI_API = "https://en.wikipedia.org/w/api.php"
json_accept = "application/sparql-results+json"

def dbpedia_query(q):
    data = urllib.parse.urlencode({"query": q, "format": "json"}).encode()
    req = urllib.request.Request(DBPEDIA_SPARQL, data=data,
                                 headers={"User-Agent": UA, "Accept": json_accept})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["results"]["bindings"]

def wiki_query(params):
    params["format"] = "json"
    url = f"{WIKI_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def normalize(s):
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s.lower()

club_clean_names = {cn: strip_country(cn) for cn in club_names}
unique_clean = sorted(set(club_clean_names.values()))
club_qid_map = {}  # clean_name -> (wikidata_uri, dbpedia_uri)

# Phase 1: DBpedia direct label match via VALUES
print("  Phase 1: DBpedia direct label match...")
BATCH_SZ = 100
for i in range(0, len(unique_clean), BATCH_SZ):
    batch = unique_clean[i:i+BATCH_SZ]
    labels = " ".join(f'"{cn}"@en' for cn in batch)
    q = f"""PREFIX dbo: <http://dbpedia.org/ontology/>
SELECT ?club ?name WHERE {{
  VALUES ?name {{ {labels} }}
  ?club a dbo:SoccerClub .
  ?club rdfs:label ?name .
}}"""
    results = dbpedia_query(q)
    for b in results:
        label = b["name"]["value"]
        dbp_uri = b["club"]["value"]
        club_qid_map[label] = (None, dbp_uri)
    print(f"    batch {i//BATCH_SZ+1}/{(len(unique_clean)+BATCH_SZ-1)//BATCH_SZ}: {len(results)} matches", end="")
    if len(results) < len(batch):
        print(f"  ({(len(batch)-len(results))} unmatched)")
    else:
        print()
    time.sleep(0.3)

matched_dbp = len(club_qid_map)
print(f"  Phase 1 matches: {matched_dbp}/{len(unique_clean)}")

# Phase 2: Progressive DBpedia matching (suffix/prefix variants)
unmatched = [c for c in unique_clean if c not in club_qid_map]
print(f"  Phase 2: progressive DBpedia matching for {len(unmatched)} clubs...")

def try_dbp_match(club_names, label="  "):
    """Query DBpedia with a list of club names, return set of matched names."""
    matched_set = set()
    for j in range(0, len(club_names), BATCH_SZ):
        batch = club_names[j:j+BATCH_SZ]
        labels = " ".join(f'"{cn}"@en' for cn in batch)
        q = f"""PREFIX dbo: <http://dbpedia.org/ontology/>
SELECT ?club ?name WHERE {{
  VALUES ?name {{ {labels} }}
  ?club a dbo:SoccerClub .
  ?club rdfs:label ?name .
}}"""
        try:
            results = dbpedia_query(q)
            for b in results:
                cn2 = b["name"]["value"]
                dbp_uri = b["club"]["value"]
                club_qid_map[cn2] = (None, dbp_uri)
                matched_set.add(cn2)
        except Exception as e:
            print(f"{label}DBpedia error: {e}")
        time.sleep(0.5)
    return matched_set

# Strategy 2a: Strip "FC", "CF", "SC", "AC", "FK", "JK" suffixes
alt_names = []
for cn in unmatched:
    for sfx in [" FC", " CF", " SC", " AC", " FK", " JK", " SCC", " F.C.", " C.F.", " S.C."]:
        if cn.endswith(sfx):
            alt_names.append(cn[:-len(sfx)])
            break
    else:
        alt_names.append(None)

matched2 = set()
names_to_try = [a for a in alt_names if a is not None]
if names_to_try:
    m = try_dbp_match(list(set(names_to_try)))
    for orig, alt in zip(unmatched, alt_names):
        if alt and alt in m and orig not in club_qid_map:
            club_qid_map[orig] = club_qid_map[alt]
            matched2.add(orig)
print(f"    suffix-strip: +{len(matched2)}")

# Strategy 2b: Strip prefixes
unmatched2 = [c for c in unique_clean if c not in club_qid_map]
alt_names2 = []
for cn in unmatched2:
    for pref in ["FC ", "CF ", "SC ", "AC ", "SSC ", "AFC ", "AS ", "CA ", "CD ", "CF ", "CR ", "CS "]:
        if cn.startswith(pref):
            alt_names2.append(cn[len(pref):])
            break
    else:
        alt_names2.append(None)

matched2b = set()
names_to_try2 = [a for a in alt_names2 if a is not None]
if names_to_try2:
    m = try_dbp_match(list(set(names_to_try2)))
    for orig, alt in zip(unmatched2, alt_names2):
        if alt and alt in m and orig not in club_qid_map:
            club_qid_map[orig] = club_qid_map[alt]
            matched2b.add(orig)
print(f"    prefix-strip: +{len(matched2b)}")

# Strategy 2c: Normalized match (strip punctuation, collapse spaces)
unmatched3 = [c for c in unique_clean if c not in club_qid_map]
if unmatched3:
    # Fetch additional DBpedia labels for normalized matching
    all_db_labels = {}
    offset = 0
    LIMIT_DB = 20000
    while offset < 100000:
        q = f"""PREFIX dbo: <http://dbpedia.org/ontology/>
SELECT DISTINCT ?name ?club WHERE {{
  ?club a dbo:SoccerClub .
  ?club rdfs:label ?name .
  FILTER(LANG(?name) = "en")
}} ORDER BY ?name LIMIT {LIMIT_DB} OFFSET {offset}"""
        try:
            results = dbpedia_query(q)
            for b in results:
                all_db_labels[normalize(b["name"]["value"])] = (b["name"]["value"], b["club"]["value"])
            if len(results) < LIMIT_DB:
                break
            offset += LIMIT_DB
        except:
            break

    for cn in unmatched3:
        n = normalize(cn)
        db = all_db_labels.get(n)
        if db:
            club_qid_map[cn] = (None, db[1])
        if cn in club_qid_map:
            continue
        # Try removing last word
        words = n.split()
        for i in range(len(words)-1, 1, -1):
            prefix = " ".join(words[:i])
            db = all_db_labels.get(prefix)
            if db:
                club_qid_map[cn] = (None, db[1])
                break
    print(f"    normalized match: +{sum(1 for c in unmatched3 if c in club_qid_map)}")

matched_dbp2 = sum(1 for v in club_qid_map.values() if v and v[1])
print(f"  Total with DBpedia URIs: {matched_dbp2}/{len(unique_clean)}")

# Phase 3: Resolve Wikidata QIDs from DBpedia URIs (batched)
print(f"  Phase 3: Resolve Wikidata QIDs from {matched_dbp2} DBpedia URIs...")
cn_by_dbp = {}
for cn, v in club_qid_map.items():
    if v and v[1]:
        cn_by_dbp.setdefault(v[1], []).append(cn)

dbp_uris = sorted(cn_by_dbp.keys())
WIKI_BATCH = 50
for i in range(0, len(dbp_uris), WIKI_BATCH):
    batch = dbp_uris[i:i+WIKI_BATCH]
    titles = "|".join(u.rsplit("/", 1)[-1] for u in batch)
    try:
        r = wiki_query({"action": "query", "prop": "pageprops", "titles": titles,
                       "ppprop": "wikibase_item"})
        for _, page in r.get("query", {}).get("pages", {}).items():
            qid = page.get("pageprops", {}).get("wikibase_item")
            title = page.get("title", "").replace(" ", "_")
            if qid and title:
                dbp_key = f"http://dbpedia.org/resource/{title}"
                wd_uri = f"https://www.wikidata.org/entity/{qid}"
                for cn in cn_by_dbp.get(dbp_key, []):
                    club_qid_map[cn] = (wd_uri, club_qid_map[cn][1])
    except Exception as e:
        print(f"    batch {i//WIKI_BATCH+1}: {e}")
    time.sleep(1.5)
    if (i+WIKI_BATCH) % 200 == 0 or (i+WIKI_BATCH) >= len(dbp_uris):
        print(f"    {min(i+WIKI_BATCH, len(dbp_uris))}/{len(dbp_uris)}")

matched_wd = sum(1 for v in club_qid_map.values() if v and v[0])
print(f"  Final: {matched_wd} with Wikidata  |  {matched_dbp2} with DBpedia")

# --- 4. Build TTL output ---
print("\n=== Step 4: Build TTL output ===")

with open(SOURCE_TTL) as f:
    source_lines = f.read().split("\n")

new_section_lines = []

def ttl_lit(val, lang="en"):
    if not val: return None
    val_esc = val.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{val_esc}"@{lang}'

def ttl_uri(u):
    return f"<{u}>"

def ttl_date(dob):
    m = re.match(r'(\d{2})/(\d{2})/(\d{4})', dob)
    if m: return f'"{m.group(3)}-{m.group(2)}-{m.group(1)}"^^xsd:date'
    m = re.match(r'(\d{4}-\d{2}-\d{2})', dob)
    if m: return f'"{m.group(1)}"^^xsd:date'
    return ttl_lit(dob)

def emit_entity(lines):
    lines[-1] = lines[-1].rstrip(" ;") + " ."
    new_section_lines.append("  ".join(lines) + "\n")

# Index team DBpedia URIs for matching
team_dbp_uri = {}
for s, _, _ in g.triples((None, RDF.type, SCHEMA_SPORTSTEAM)):
    s_str = str(s)
    if "dbpedia.org" in s_str:
        for _, p2, o2 in g.triples((s, None, None)):
            if p2 == SCHEMA_NAME:
                team_dbp_uri[str(o2).lower()] = s_str
                break

# --- 4a. Countries ---
print("  Generating country entities...")
country_iri = {}
for team in country_rows:
    inf = country_info[team]
    disp = inf["display"]
    code = inf["code"]
    iri = f"{TSV_BASE}#team-{make_slug(disp)}-{code}"
    country_iri[team] = iri

    ttl_ent = None
    for nk in [disp.lower(), team.lower()]:
        if nk in ttl_team_by_name:
            ttl_ent = ttl_team_by_name[nk]
            break

    lines = [f"{ttl_uri(iri)} a schema:Country ;",
             f"  schema:name {ttl_lit(disp)} ;",
             f"  schema:alternateName {ttl_lit(code)} ;"]
    if ttl_ent:
        lines.append(f"  owl:sameAs {ttl_uri(str(ttl_ent))} ;")
    emit_entity(lines)

# --- 4b. Players ---
print("  Generating player entities...")
player_iri = {}
matched_pl = 0

for r in rows:
    team = r["Team"]
    shirt = r["#"]
    pos = r["POS"]
    full_name = r["PLAYER NAME"]
    first_n = r.get("FIRST NAME(S)", "")
    last_n = r.get("LAST NAME(S)", "")
    shirt_n = r.get("NAME ON SHIRT", "")
    dob = r["DOB"]
    club = r["CLUB"]
    height = r.get("HEIGHT (CM)", "")
    pl_qid = r.get("PLAYER_WIKIDATA", "")
    pl_dbp = r.get("PLAYER_DBPEDIA", "")

    inf = country_info[team]
    cslug = make_slug(inf["display"])
    code = inf["code"]
    lslug = make_slug(last_n or full_name)
    iri = f"{TSV_BASE}#{cslug}-{code}-{shirt}-{lslug}"
    player_iri[(team, shirt)] = iri

    # Find TTL entity
    ttl_ent = None
    if pl_qid and pl_qid in ttl_by_qid:
        ttl_ent = str(ttl_by_qid[pl_qid])
    if not ttl_ent and pl_dbp and pl_dbp in ttl_by_dbpedia:
        ttl_ent = str(ttl_by_dbpedia[pl_dbp])
    if not ttl_ent:
        tk = inf["display"].lower()
        td = team_dbp_uri.get(tk)
        if td and (td, shirt) in ttl_by_team_shirt:
            ttl_ent = str(ttl_by_team_shirt[(td, shirt)])
    if ttl_ent:
        matched_pl += 1

    lines = [f"{ttl_uri(iri)} a schema:Person ;",
             f"  schema:name {ttl_lit(full_name)} ;"]
    if first_n:
        lines.append(f"  schema:givenName {ttl_lit(first_n)} ;")
    if last_n:
        lines.append(f"  schema:familyName {ttl_lit(last_n)} ;")
    if shirt_n and shirt_n != full_name:
        lines.append(f"  schema:alternateName {ttl_lit(shirt_n)} ;")
    if pos:
        lines.append(f"  schema:jobTitle {ttl_lit(POSITION_MAP.get(pos, pos))} ;")
    if dob:
        lines.append(f"  schema:birthDate {ttl_date(dob)} ;")
    if height:
        lines.append(f"  schema:height {int(height)} ;")
    if club:
        clean_club = strip_country(club)
        if clean_club in club_qid_map and club_qid_map[clean_club][0]:
            lines.append(f"  schema:affiliation {ttl_uri(club_qid_map[clean_club][0])} ;")
        else:
            lines.append(f"  schema:affiliation {ttl_lit(club)} ;")
    if team in country_iri:
        lines.append(f"  schema:memberOf {ttl_uri(country_iri[team])} ;")
    if ttl_ent:
        lines.append(f"  owl:sameAs {ttl_uri(ttl_ent)} ;")
    emit_entity(lines)

print(f"    {len(rows)} player entities  |  matched: {matched_pl}")

# --- 4c. Clubs ---
print("  Generating club entities...")
club_iri = {}
slugs_seen = set()

for cn in club_names:
    clean = strip_country(cn)
    cslug = make_slug(cn)
    while cslug in slugs_seen:
        cslug = cslug + "-" + str(abs(hash(cn)) & 0xFFFF)
    slugs_seen.add(cslug)

    iri = f"{TSV_BASE}#club-{cslug}"
    club_iri[cn] = iri

    qid_r = club_qid_map.get(clean)
    lines = [f"{ttl_uri(iri)} a schema:SportsTeam ;",
             f"  schema:name {ttl_lit(cn)} ;"]
    if clean != cn:
        lines.append(f"  schema:alternateName {ttl_lit(clean)} ;")
    if qid_r and qid_r[0]:
        lines.append(f"  owl:sameAs {ttl_uri(qid_r[0])} ;")
        if qid_r[1]:
            lines.append(f"  owl:sameAs {ttl_uri(qid_r[1])} ;")
    emit_entity(lines)

wd_count = sum(1 for cn in club_names if club_qid_map.get(strip_country(cn), (None,))[0])
dbp_count2 = sum(1 for cn in club_names if club_qid_map.get(strip_country(cn), (None, None))[1])
print(f"    {len(club_names)} entities  |  Wikidata: {wd_count}  |  DBpedia: {dbp_count2}")

# --- 4d. owl:sameAs from TTL entities to TSV IRIs ---
print("  Adding owl:sameAs links from TTL entities to TSV IRIs...")
sameas_count = 0
for r in rows:
    team = r["Team"]
    shirt = r["#"]
    pl_qid = r.get("PLAYER_WIKIDATA", "")
    pl_dbp = r.get("PLAYER_DBPEDIA", "")
    iri = player_iri.get((team, shirt))
    if not iri:
        continue
    ttl_ent = None
    if pl_qid and pl_qid in ttl_by_qid:
        ttl_ent = ttl_by_qid[pl_qid]
    if not ttl_ent and pl_dbp and pl_dbp in ttl_by_dbpedia:
        ttl_ent = ttl_by_dbpedia[pl_dbp]
    if ttl_ent:
        new_section_lines.append(f"{ttl_uri(str(ttl_ent))} owl:sameAs {ttl_uri(iri)} .\n")
        sameas_count += 1

# Country sameAs
for team, iri in country_iri.items():
    inf = country_info[team]
    disp = inf["display"]
    ttl_ent = None
    for nk in [disp.lower(), team.lower()]:
        if nk in ttl_team_by_name:
            ttl_ent = ttl_team_by_name[nk]
            break
    if ttl_ent:
        new_section_lines.append(f"{ttl_uri(str(ttl_ent))} owl:sameAs {ttl_uri(iri)} .\n")

print(f"    owl:sameAs links added: {sameas_count}")

# --- 5. Write output ---
print("\n=== Step 5: Write output ===")

# Insert TSV prefix
has_owl = any(l.startswith("@prefix owl:") for l in source_lines)
last_prefix = max(i for i, l in enumerate(source_lines) if l.startswith("@prefix "))

prefix_new = []
if not has_owl:
    prefix_new.append("@prefix owl: <http://www.w3.org/2002/07/owl#> .")
prefix_new.append(f"@prefix tsv: <{TSV_BASE}#> .")

output_lines = source_lines[:last_prefix+1] + prefix_new + source_lines[last_prefix+1:]
output_lines.append("")
output_lines.append("#" + "=" * 68)
output_lines.append("# TSV-derived entity layer (players, countries, clubs)")
output_lines.append("# Source: " + TSV_BASE)
output_lines.append("#" + "=" * 68)
output_lines.append("")
output_lines.extend(new_section_lines)

output = "\n".join(output_lines) + "\n"
with open(OUTPUT_TTL, "w") as f:
    f.write(output)

# --- Summary ---
print(f"\n  Output: {OUTPUT_TTL}")
print(f"  Size: {os.path.getsize(OUTPUT_TTL):,} bytes")
print(f"  New triples: {len(new_section_lines)}")

# --- Verify ---
print("\n=== Verification ===")
g2 = rdflib.Graph()
try:
    g2.parse(OUTPUT_TTL, format="turtle")
    ok = True
except Exception as e:
    print(f"  PARSE ERROR: {e}")
    ok = False

if ok:
    print(f"  Parsed OK: {len(g2)} triples total")

    tsv_people = sum(1 for _, o in g2.subject_objects(RDF.type) if str(o) == "http://schema.org/Person" and TSV_BASE in str(_))
    tsv_countries = sum(1 for _, o in g2.subject_objects(RDF.type) if str(o) == "http://schema.org/Country" and TSV_BASE in str(_))
    tsv_teams = sum(1 for _, o in g2.subject_objects(RDF.type) if str(o) == "http://schema.org/SportsTeam" and TSV_BASE in str(_))

    print(f"  TSV Person entities:      {tsv_people}")
    print(f"  TSV Country entities:     {tsv_countries}")
    print(f"  TSV SportsTeam entities:  {tsv_teams}")

    # Count owl:sameAs from TTL -> TSV
    sameas_total = sum(1 for _, _, o in g2.triples((None, OWL.sameAs, None)) if TSV_BASE in str(o))
    print(f"  owl:sameAs → TSV IRIs:    {sameas_total}")

    # Check known samples
    checks = [
        ("Algeria-ALG-1-MASTIL", "schema:Person"),
        ("Argentina-ARG-10-MESSI", "schema:Person"),
        ("Brazil-BRA-7-PAIXÃO-DE-OLIVEIRA-JÚNIOR", "schema:Person"),
        ("England-ENG-9-KANE", "schema:Person"),
        ("team-Algeria-ALG", "schema:Country"),
        ("club-Real-Madrid-C.-F.", "schema:SportsTeam"),
        ("club-Manchester-City-FC", "schema:SportsTeam"),
        ("club-FC-Bayern-München", "schema:SportsTeam"),
    ]
    for frag, typ in checks:
        uri = rdflib.URIRef(f"{TSV_BASE}#{frag}")
        rtype = rdflib.URIRef(f"http://schema.org/{typ[len('schema:'):]}")
        found = (uri, RDF.type, rtype) in g2
        print(f"  {'✓' if found else '✗'} {frag}")

print("\nDone!")
