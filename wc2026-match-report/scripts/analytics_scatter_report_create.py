#!/usr/bin/env python3
"""
analytics_scatter_report_create.py
Generate Simon Brunson-style analytics scatter-plot reports for FIFA WC2026.

Data is fetched live from the Knowledge Graph at page-load time (client-side SPARQL),
so the output HTML is always up-to-date when opened.  No server-side SPARQL needed.

Usage
-----
  python3 scripts/analytics_scatter_report_create.py \\
    --title "RUNNING DATA" --emoji "🏃" \\
    --subtitle "Player-Level Relationships" \\
    --desc "How total volume, high-speed work, top speed and sprint metres are connecting" \\
    --note "Players with 45+ tournament minutes" \\
    --chart "totalDistance,highSpeedDistance,Total distance (m),High-speed distance (m)" \\
    --chart "topSpeed,sprintMetres,Top speed (km/h),Sprint metres (m)" \\
    --min-minutes 45 \\
    --out reports/20260623-running-data.html

Each --chart argument:  xKey,yKey[,xAxisLabel,yAxisLabel[,Card Title]]
  xKey and yKey are required; labels default to human-readable names; title defaults to "xLabel vs yLabel".

Available metric keys
---------------------
  totalDistance     highSpeedDistance   sprintMetres    topSpeed       avgSpeed
  minutesPlayed     sprints             passes          passesCompleted passAccuracy
  assists           goals               shots           shotsOnTarget   takeOns
  crosses           crossesCompleted    foulsWon        foulsCommitted  forcedTurnovers
  yellowCards       corners
"""

import argparse
import json
import sys
from html import escape as he

ENDPOINT = "https://demo.openlinksw.com/sparql"
KG       = "urn:worldcup:kg:2026"
ANA      = "urn:worldcup:kg:2026:analytics"

VALID_METRICS = {
    "totalDistance", "highSpeedDistance", "sprintMetres", "topSpeed", "avgSpeed",
    "minutesPlayed", "sprints", "passes", "passesCompleted", "passAccuracy",
    "assists", "goals", "shots", "shotsOnTarget", "takeOns", "crosses",
    "crossesCompleted", "foulsWon", "foulsCommitted", "forcedTurnovers",
    "yellowCards", "corners",
}

DEFAULT_LABELS = {
    "totalDistance":    "Total Distance (m)",
    "highSpeedDistance":"High-Speed Distance (m)",
    "sprintMetres":     "Sprint Metres (m)",
    "topSpeed":         "Top Speed (km/h)",
    "avgSpeed":         "Avg Speed (km/h)",
    "minutesPlayed":    "Minutes Played",
    "sprints":          "Sprints",
    "passes":           "Total Passes",
    "passesCompleted":  "Passes Completed",
    "passAccuracy":     "Pass Accuracy (%)",
    "assists":          "Assists",
    "goals":            "Goals",
    "shots":            "Shots",
    "shotsOnTarget":    "Shots on Target",
    "takeOns":          "Take-Ons Completed",
    "crosses":          "Crosses",
    "crossesCompleted": "Crosses Completed",
    "foulsWon":         "Fouls Won",
    "foulsCommitted":   "Fouls Committed",
    "forcedTurnovers":  "Turnovers Won",
    "yellowCards":      "Yellow Cards",
    "corners":          "Corners",
}


# ── Argument parsing ───────────────────────────────────────────────────────────

def parse_chart(spec, idx):
    """Parse one --chart argument: 'xKey,yKey[,xLabel,yLabel[,Title]]'"""
    parts = [p.strip() for p in spec.split(",")]
    if len(parts) < 2:
        sys.exit(f"--chart {idx}: expected at least 'xKey,yKey', got: {spec!r}")
    xk, yk = parts[0], parts[1]
    for k in (xk, yk):
        if k not in VALID_METRICS:
            sys.exit(f"--chart {idx}: unknown metric {k!r}.\nValid: {sorted(VALID_METRICS)}")
    xl    = parts[2] if len(parts) > 2 else DEFAULT_LABELS.get(xk, xk)
    yl    = parts[3] if len(parts) > 3 else DEFAULT_LABELS.get(yk, yk)
    title = parts[4] if len(parts) > 4 else f"{xl} vs {yl}"
    return {"xKey": xk, "yKey": yk, "xLabel": xl, "yLabel": yl, "title": title}


# ── SPARQL query (single comprehensive query, only min_minutes varies) ─────────

_SPARQL_TMPL = """\
PREFIX fifa: <https://www.openlinksw.com/ontology/fifa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?player ?playerName
       (SAMPLE(?posCode)                                          AS ?position)
       (SUM(COALESCE(?totalDist,0))                              AS ?totalDistance)
       (SUM(COALESCE(?hsRun,0)+COALESCE(?hsSprint,0))           AS ?highSpeedDistance)
       (SUM(COALESCE(?hsSprint,0))                              AS ?sprintMetres)
       (MAX(COALESCE(?topSpd,0))                                AS ?topSpeed)
       (AVG(COALESCE(?avgSpd,0))                                AS ?avgSpeed)
       (SUM(COALESCE(?mins,0))                                  AS ?minutesPlayed)
       (SUM(COALESCE(?sprints,0))                               AS ?sprints)
       (SUM(COALESCE(?passes,0))                                AS ?passes)
       (SUM(COALESCE(?passesCmpl,0))                            AS ?passesCompleted)
       (SUM(COALESCE(?assists,0))                               AS ?assists)
       (SUM(COALESCE(?goals,0))                                 AS ?goals)
       (SUM(COALESCE(?shots,0))                                 AS ?shots)
       (SUM(COALESCE(?shotsOT,0))                               AS ?shotsOnTarget)
       (SUM(COALESCE(?takeOns,0))                               AS ?takeOns)
       (SUM(COALESCE(?crosses,0))                               AS ?crosses)
       (SUM(COALESCE(?crossesCmpl,0))                           AS ?crossesCompleted)
       (SUM(COALESCE(?foulsFor,0))                              AS ?foulsWon)
       (SUM(COALESCE(?foulsAg,0))                               AS ?foulsCommitted)
       (SUM(COALESCE(?forcedTO,0))                              AS ?forcedTurnovers)
       (SUM(COALESCE(?corners,0))                               AS ?corners)
WHERE {
  { SELECT ?player ?match (MAX(?gen) AS ?latestGen)
    WHERE { GRAPH <ANA_GRAPH> {
      ?r a fifa:PlayerMatchAnalyticsReport ;
         fifa:player ?player ; fifa:match ?match ; fifa:generatedAt ?gen .
    } } GROUP BY ?player ?match }

  GRAPH <ANA_GRAPH> {
    ?report a fifa:PlayerMatchAnalyticsReport ;
            fifa:player ?player ; fifa:match ?match ; fifa:generatedAt ?latestGen .
    OPTIONAL { ?report fifa:totalDistance                ?totalDist   }
    OPTIONAL { ?report fifa:distanceHighSpeedRunning     ?hsRun       }
    OPTIONAL { ?report fifa:distanceHighSpeedSprinting   ?hsSprint    }
    OPTIONAL { ?report fifa:topSpeed                     ?topSpd      }
    OPTIONAL { ?report fifa:avgSpeed                     ?avgSpd      }
    OPTIONAL { ?report fifa:timePlayed                   ?mins        }
    OPTIONAL { ?report fifa:sprints                      ?sprints     }
    OPTIONAL { ?report fifa:passes                       ?passes      }
    OPTIONAL { ?report fifa:passesCompleted              ?passesCmpl  }
    OPTIONAL { ?report fifa:assists                      ?assists     }
    OPTIONAL { ?report fifa:goals                        ?goals       }
    OPTIONAL { ?report fifa:attemptAtGoal                ?shots       }
    OPTIONAL { ?report fifa:attemptAtGoalOnTarget        ?shotsOT     }
    OPTIONAL { ?report fifa:takeOnsCompleted             ?takeOns     }
    OPTIONAL { ?report fifa:crosses                      ?crosses     }
    OPTIONAL { ?report fifa:crossesCompleted             ?crossesCmpl }
    OPTIONAL { ?report fifa:foulsFor                     ?foulsFor    }
    OPTIONAL { ?report fifa:foulsAgainst                 ?foulsAg     }
    OPTIONAL { ?report fifa:forcedTurnovers              ?forcedTO    }
    OPTIONAL { ?report fifa:corners                      ?corners     }
  }

  GRAPH <KG_GRAPH> {
    ?player rdfs:label ?playerName .
    OPTIONAL {
      ?player fifa:realPosition ?posNode .
      BIND(IF(?posNode=fifa:Position-0,"GK",
           IF(?posNode=fifa:Position-1,"DF",
           IF(?posNode=fifa:Position-2,"MF",
           IF(?posNode=fifa:Position-3,"FW","?")))) AS ?posCode)
    }
  }
}
GROUP BY ?player ?playerName
HAVING (SUM(COALESCE(?mins,0)) >= MIN_MINUTES)
ORDER BY DESC(?totalDistance)
LIMIT 600"""

def build_sparql(min_minutes):
    return (_SPARQL_TMPL
            .replace("ANA_GRAPH", ANA)
            .replace("KG_GRAPH", KG)
            .replace("MIN_MINUTES", str(min_minutes)))


# ── HTML sections ──────────────────────────────────────────────────────────────

def _chart_card(i, ch):
    return (
        f'      <!-- Chart {i} -->\n'
        f'      <div class="chart-card">\n'
        f'        <div class="ch-header">\n'
        f'          <div class="ch-num">{i}</div>\n'
        f'          <div class="ch-title">{he(ch["title"])}</div>\n'
        f'        </div>\n'
        f'        <div class="ch-meta">{he(ch["xLabel"])} vs {he(ch["yLabel"])}'
        f' &nbsp;·&nbsp; <span class="ch-hint">scroll to zoom · drag to pan · click dot for player profile</span></div>\n'
        f'        <div class="ch-wrap">\n'
        f'          <button class="btn-reset" id="reset{i}" title="Reset zoom">↺ Reset zoom</button>\n'
        f'          <canvas id="chart{i}"></canvas>\n'
        f'        </div>\n'
        f'        <div class="insight">\n'
        f'          <span class="ins-icon">🎯</span>\n'
        f'          <span class="ins-text" id="insight{i}">–</span>\n'
        f'        </div>\n'
        f'      </div>'
    )


def _chart_setup(i, ch):
    xk = ch["xKey"]
    yk = ch["yKey"]
    xl = json.dumps(ch["xLabel"])
    yl = json.dumps(ch["yLabel"])
    # Speed charts: only include players with real speed data
    pool = f"players.filter(p => p.topSpeed > 5)" if "topSpeed" in (xk, yk) else "players"
    return (
        f"    // Chart {i}: {he(ch['title'])}\n"
        f"    const p{i}   = {pool};\n"
        f"    const out{i} = pickOutliers(p{i}, '{xk}', '{yk}');\n"
        f"    const ds{i}  = buildDatasets(p{i}, '{xk}', '{yk}', out{i});\n"
        f"    const c{i}   = makeChart('chart{i}', ds{i}, {xl}, {yl});\n"
        f"    document.getElementById('insight{i}').innerHTML = autoInsight(p{i}, '{xk}', '{yk}', {xl}, {yl});\n"
        f"    document.getElementById('reset{i}').addEventListener('click', () => {{\n"
        f"      c{i}.resetZoom();\n"
        f"      document.getElementById('reset{i}').classList.remove('visible');\n"
        f"    }});"
    )


def build_html(title, emoji, subtitle, desc, note, charts, min_minutes):
    n = len(charts)
    grid_cols = "1fr" if n == 1 else "1fr 1fr"
    page_title = f"WC2026 – {title}"
    sparql_str = build_sparql(min_minutes)
    card_html  = "\n".join(_chart_card(i + 1, ch) for i, ch in enumerate(charts))
    setup_js   = "\n\n".join(_chart_setup(i + 1, ch) for i, ch in enumerate(charts))

    css = """\
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Helvetica Neue', Arial, sans-serif;
  background: #f0ede8;
  color: #1a1a1a;
  min-height: 100vh;
}

.page { max-width: 960px; margin: 0 auto; padding: 14px 16px 22px; }

/* ── HEADER ── */
.header {
  display: flex; align-items: stretch;
  border-bottom: 3px solid #111; padding-bottom: 10px; margin-bottom: 5px; gap: 0;
}
.hdr-brand {
  display: flex; flex-direction: column; justify-content: center;
  padding-right: 14px; border-right: 1.5px solid #bbb; min-width: 110px;
}
.hdr-trophy { font-size: 26px; line-height: 1; }
.hdr-wc  { font-size: 10px; font-weight: 900; color: #111; letter-spacing: 0.4px; margin-top: 3px; }
.hdr-host { font-size: 8px; color: #666; letter-spacing: 0.3px; margin-top: 1px; }
.hdr-main {
  display: flex; flex-direction: column; justify-content: center; padding: 2px 14px 0;
}
.report-title {
  font-size: 44px; font-weight: 900; color: #111; letter-spacing: -2px;
  text-transform: uppercase; line-height: 1; white-space: nowrap;
  display: flex; align-items: center; gap: 4px;
}
.title-icon { font-size: 34px; display: inline-block; }
.hdr-center {
  flex: 1; display: flex; flex-direction: column; justify-content: center;
  align-items: center; padding: 0 12px;
  border-left: 1.5px solid #bbb; border-right: 1.5px solid #bbb;
}
.pl-title { font-size: 15px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.4px; color: #111; text-align: center; }
.pl-sub   { font-size: 9px; color: #555; text-align: center; max-width: 230px; line-height: 1.55; margin-top: 4px; }
.pl-note  { font-size: 8px; color: #999; text-align: center; margin-top: 3px; font-style: italic; }

/* ── STATES ── */
.data-thru { font-size: 8.5px; color: #999; text-align: right; margin-top: 4px; margin-bottom: 8px; font-style: italic; }
.loading-box { text-align: center; padding: 70px 20px; color: #888; }
.spin { font-size: 36px; display: block; margin-bottom: 14px; animation: spin 1.4s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading-msg { font-size: 13px; color: #777; }
.error-box {
  background: #fff3f3; border: 1px solid #ffbaba; border-radius: 6px;
  padding: 20px; color: #c00; font-size: 11px; text-align: center; line-height: 1.7;
}
.error-box code { background: #f8e8e8; padding: 1px 5px; border-radius: 3px; font-family: monospace; }

/* ── CHARTS ── */
.charts-row { display: grid; gap: 12px; }
.chart-card {
  background: #ffffff; border: 1px solid #d6d0c8; border-radius: 4px;
  padding: 11px 11px 9px; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.ch-header { display: flex; align-items: center; gap: 7px; margin-bottom: 2px; }
.ch-num {
  width: 20px; height: 20px; border-radius: 50%; background: #111; color: #fff;
  font-size: 11px; font-weight: 800; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.ch-title { font-size: 11.5px; font-weight: 800; text-transform: uppercase; color: #111; letter-spacing: 0.15px; }
.ch-meta  { font-size: 8.5px; color: #888; margin-left: 27px; margin-bottom: 7px; }
.ch-hint  { color: #c0bbb5; font-style: italic; }
.insight  {
  display: flex; gap: 7px; align-items: flex-start;
  background: #f8f5f0; border: 1px solid #e4ddd4; border-radius: 3px;
  padding: 7px 8px; margin-top: 7px;
}
.ins-icon { font-size: 13px; flex-shrink: 0; line-height: 1.3; }
.ins-text { font-size: 9px; color: #444; line-height: 1.6; }
.ins-text a { color: #1a52b8; text-decoration: none; font-weight: 700; border-bottom: 1px dotted #1a52b8; }
.ins-text a:hover { border-bottom-style: solid; }

/* ── CHART CONTROLS ── */
.ch-wrap { position: relative; height: 268px; }
.btn-reset {
  position: absolute; top: 5px; right: 5px; z-index: 10;
  font-size: 9px; font-family: inherit; padding: 3px 7px;
  background: rgba(255,255,255,0.92); border: 1px solid #ccc; border-radius: 3px;
  cursor: pointer; color: #666; display: none;
}
.btn-reset.visible { display: block; }
.btn-reset:hover { background: #fff; color: #111; border-color: #888; }

/* ── BOTTOM ── */
.bottom {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 11px; padding-top: 9px; border-top: 1px solid #c8c0b8;
  flex-wrap: wrap; gap: 8px;
}
.legend { display: flex; gap: 16px; flex-wrap: wrap; }
.leg-item { display: flex; align-items: center; gap: 5px; font-size: 10.5px; color: #333; }
.leg-dot  { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.source   { font-size: 8px; color: #999; text-align: right; line-height: 1.7; }
.source a { color: #1a52b8; text-decoration: none; }

/* ── MODAL ── */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.48); z-index: 2000;
  display: flex; align-items: center; justify-content: center;
  animation: fade-in 0.12s ease;
}
@keyframes fade-in { from { opacity: 0 } to { opacity: 1 } }
.modal-box {
  background: #fff; border-radius: 6px; box-shadow: 0 12px 40px rgba(0,0,0,0.30);
  min-width: 260px; max-width: 360px; width: 90vw; overflow: hidden;
  animation: slide-up 0.14s ease;
}
@keyframes slide-up { from { transform: translateY(10px) } to { transform: translateY(0) } }
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 11px 14px 9px; background: #f8f5f0; border-bottom: 1px solid #e4ddd4;
}
.modal-title { font-size: 11px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.4px; color: #111; }
.modal-close { background: none; border: none; cursor: pointer; font-size: 13px; color: #999; padding: 0 2px; line-height: 1; font-family: inherit; }
.modal-close:hover { color: #111; }
.modal-hint { font-size: 9px; color: #888; padding: 8px 14px 4px; font-style: italic; }
.modal-list { list-style: none; padding: 4px 0 8px; margin: 0; max-height: 340px; overflow-y: auto; }
.modal-list li a {
  display: flex; align-items: center; gap: 8px; padding: 9px 14px;
  font-size: 11px; color: #1a1a1a; text-decoration: none;
  border-bottom: 1px solid #f5f2ee; transition: background 0.08s;
}
.modal-list li:last-child a { border-bottom: none; }
.modal-list li a:hover { background: #f0ede8; color: #111; }
.modal-pos {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 16px; border-radius: 2px;
  font-size: 8.5px; font-weight: 800; color: #fff; flex-shrink: 0; letter-spacing: 0.3px;
}
.modal-player-name { font-weight: 600; flex: 1; }
.modal-arrow { color: #bbb; font-size: 10px; }"""

    js_static = r"""
// ── Position styling ──────────────────────────────────────────────────────────
const POS_STYLE = {
  DF: { fill: 'rgba(29,92,166,0.72)',   stroke: 'rgba(29,92,166,1)'   },
  MF: { fill: 'rgba(26,127,64,0.72)',  stroke: 'rgba(26,127,64,1)'   },
  FW: { fill: 'rgba(200,57,43,0.72)',  stroke: 'rgba(200,57,43,1)'   },
  GK: { fill: 'rgba(92,99,112,0.72)', stroke: 'rgba(92,99,112,1)'   },
  '?':{ fill: 'rgba(170,170,170,0.5)', stroke: 'rgba(170,170,170,1)' },
};
const POS_BADGE_COLOR = { DF:'#1d5ca6', MF:'#1a7f40', FW:'#c8392b', GK:'#5c6370', '?':'#999' };

// ── Fetch ─────────────────────────────────────────────────────────────────────
async function sparql(query) {
  const url = `${ENDPOINT}?query=${encodeURIComponent(query)}&format=application%2Fsparql-results%2Bjson`;
  const res = await fetch(url, { headers: { Accept: 'application/sparql-results+json' } });
  if (!res.ok) throw new Error(`SPARQL endpoint returned HTTP ${res.status}: ${res.statusText}`);
  return res.json();
}

// ── Parse rows ────────────────────────────────────────────────────────────────
function parseRows(data) {
  return data.results.bindings.map(r => {
    const g = k => +(r[k]?.value || 0);
    const p = {
      uri:              r.player?.value || '',
      name:             r.playerName?.value || 'Unknown',
      pos:              r.position?.value || '?',
      totalDistance:    g('totalDistance'),
      highSpeedDistance:g('highSpeedDistance'),
      sprintMetres:     g('sprintMetres'),
      topSpeed:         g('topSpeed'),
      avgSpeed:         g('avgSpeed'),
      minutesPlayed:    g('minutesPlayed'),
      sprints:          g('sprints'),
      passes:           g('passes'),
      passesCompleted:  g('passesCompleted'),
      assists:          g('assists'),
      goals:            g('goals'),
      shots:            g('shots'),
      shotsOnTarget:    g('shotsOnTarget'),
      takeOns:          g('takeOns'),
      crosses:          g('crosses'),
      crossesCompleted: g('crossesCompleted'),
      foulsWon:         g('foulsWon'),
      foulsCommitted:   g('foulsCommitted'),
      forcedTurnovers:  g('forcedTurnovers'),
      corners:          g('corners'),
    };
    p.passAccuracy = p.passes > 0 ? +(100 * p.passesCompleted / p.passes).toFixed(1) : 0;
    return p;
  }).filter(p => p.minutesPlayed > 0);
}

// ── /describe link ────────────────────────────────────────────────────────────
function describeLink(p) {
  if (!p.uri) return p.name;
  return `<a href="https://demo.openlinksw.com/describe/?url=${encodeURIComponent(p.uri)}" target="_blank" rel="noopener">${p.name}</a>`;
}

// ── Auto-insight ──────────────────────────────────────────────────────────────
function autoInsight(players, xKey, yKey, xLabel, yLabel) {
  if (!players.length) return '–';
  const fmt = v => v >= 10000 ? (v/1000).toFixed(1)+' km' : v >= 1000 ? v.toLocaleString() : v % 1 === 0 ? v : v.toFixed(1);
  const byX = [...players].sort((a,b) => b[xKey]-a[xKey]);
  const byY = [...players].sort((a,b) => b[yKey]-a[yKey]);
  const topX = byX[0], topY = byY[0];
  const samePlayer = topX.name === topY.name;
  if (samePlayer) {
    return `${describeLink(topX)} leads both axes — <b>${fmt(topX[xKey])}</b> ${xLabel.toLowerCase()} and <b>${fmt(topX[yKey])}</b> ${yLabel.toLowerCase()}.`;
  }
  return `${describeLink(topX)} leads ${xLabel.toLowerCase()} at <b>${fmt(topX[xKey])}</b>. `
       + `${describeLink(topY)} tops ${yLabel.toLowerCase()} with <b>${fmt(topY[yKey])}</b> — `
       + `revealing distinct physical profiles across positions.`;
}

// ── Outlier label selection ───────────────────────────────────────────────────
function pickOutliers(players, xKey, yKey, n=9) {
  const sortBy = k => [...players].sort((a,b) => b[k]-a[k]);
  const names = new Set();
  sortBy(xKey).slice(0,n).forEach(p => names.add(p.name));
  sortBy(yKey).slice(0,n).forEach(p => names.add(p.name));
  return names;
}

// ── Build Chart.js datasets ───────────────────────────────────────────────────
function buildDatasets(players, xKey, yKey, labelNames) {
  const groups = {};
  Object.keys(POS_STYLE).forEach(k => (groups[k] = []));
  players.forEach(p => {
    const pos = POS_STYLE[p.pos] ? p.pos : '?';
    groups[pos].push({ x:p[xKey], y:p[yKey], uri:p.uri, playerName:p.name,
                       _label: labelNames.has(p.name) ? p.name : null });
  });
  return Object.entries(groups).filter(([,pts]) => pts.length > 0).map(([pos,pts]) => ({
    label: pos, data: pts,
    backgroundColor: POS_STYLE[pos].fill, borderColor: POS_STYLE[pos].stroke,
    borderWidth: 0.5, pointRadius: 3.5, pointHoverRadius: 6, pointHitRadius: 8,
  }));
}

// ── Create chart ──────────────────────────────────────────────────────────────
function makeChart(id, datasets, xLabel, yLabel) {
  return new Chart(document.getElementById(id), {
    type: 'scatter', data: { datasets },
    options: {
      responsive: true, maintainAspectRatio: false, animation: { duration: 600 },
      onClick: (event, _elements, chart) => {
        const RADIUS = 12;
        const hits = [];
        chart.data.datasets.forEach(ds => {
          ds.data.forEach(pt => {
            const px = chart.scales.x.getPixelForValue(pt.x);
            const py = chart.scales.y.getPixelForValue(pt.y);
            if (Math.hypot(px-event.x, py-event.y) <= RADIUS)
              hits.push({ uri:pt.uri, name:pt.playerName, pos:ds.label,
                          dist:Math.hypot(px-event.x, py-event.y) });
          });
        });
        if (!hits.length) return;
        hits.sort((a,b) => a.dist-b.dist);
        if (hits.length === 1) {
          if (hits[0].uri) window.open(
            `https://demo.openlinksw.com/describe/?url=${encodeURIComponent(hits[0].uri)}`,
            '_blank','noopener');
        } else { showPlayerModal(hits); }
      },
      onHover: (ev, els) => { if (ev.native?.target) ev.native.target.style.cursor = els.length ? 'pointer' : 'default'; },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => {
              const d = ctx.raw;
              const fmt = v => Number.isInteger(v) ? v.toLocaleString() : v.toFixed(1);
              return `${d.playerName}  (${fmt(d.x)}, ${fmt(d.y)})`;
            },
            footer: () => '↗ Click to open player profile',
          },
          footerFont: { size:9, style:'italic' }, footerColor: '#aaa',
        },
        datalabels: {
          display: ctx => !!ctx.dataset.data[ctx.dataIndex]._label,
          formatter: val => val._label,
          font: { size:7.5, weight:'700', family:'Helvetica Neue, Arial, sans-serif' },
          color: '#111', backgroundColor: 'rgba(255,255,255,0.82)', borderRadius: 2,
          padding: { top:1, bottom:1, left:2, right:2 },
          anchor:'end', align:'top', offset:3, clamp:true,
        },
        zoom: {
          zoom:  { wheel:{ enabled:true }, pinch:{ enabled:true }, mode:'xy',
                   onZoom: ({chart}) => chart.canvas.parentElement.querySelector('.btn-reset')?.classList.add('visible') },
          pan:   { enabled:true, mode:'xy',
                   onPan:  ({chart}) => chart.canvas.parentElement.querySelector('.btn-reset')?.classList.add('visible') },
        },
      },
      scales: {
        x: { title:{ display:true, text:xLabel, font:{ size:9.5, weight:'700' }, color:'#666' },
             grid:{ color:'rgba(0,0,0,0.05)' }, ticks:{ font:{ size:8.5 }, color:'#999', maxTicksLimit:8 } },
        y: { title:{ display:true, text:yLabel, font:{ size:9.5, weight:'700' }, color:'#666' },
             grid:{ color:'rgba(0,0,0,0.05)' }, ticks:{ font:{ size:8.5 }, color:'#999', maxTicksLimit:7 } },
      },
    },
  });
}

// ── Modal ─────────────────────────────────────────────────────────────────────
function showPlayerModal(hits) {
  const list = document.getElementById('modalList');
  list.innerHTML = '';
  hits.forEach(p => {
    const li = document.createElement('li');
    const a  = document.createElement('a');
    a.href = p.uri ? `https://demo.openlinksw.com/describe/?url=${encodeURIComponent(p.uri)}` : '#';
    a.target = '_blank'; a.rel = 'noopener';
    const badge = document.createElement('span');
    badge.className = 'modal-pos'; badge.textContent = p.pos;
    badge.style.background = POS_BADGE_COLOR[p.pos] || '#999';
    const name = document.createElement('span');
    name.className = 'modal-player-name'; name.textContent = p.name;
    const arrow = document.createElement('span');
    arrow.className = 'modal-arrow'; arrow.textContent = '↗';
    a.append(badge, name, arrow); li.appendChild(a); list.appendChild(li);
  });
  document.getElementById('playerModal').style.display = 'flex';
}
function closeModal() { document.getElementById('playerModal').style.display = 'none'; }
document.getElementById('modalClose').addEventListener('click', closeModal);
document.getElementById('playerModal').addEventListener('click', e => { if (e.target===document.getElementById('playerModal')) closeModal(); });
document.addEventListener('keydown', e => { if (e.key==='Escape') closeModal(); });"""

    sparql_json = json.dumps(sparql_str)  # encode SPARQL as a JS string literal

    return "\n".join([
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"<title>{he(page_title)}</title>",
        f'<meta name="description" content="{he(subtitle)} — {he(desc)} — FIFA World Cup 2026 analytics via the OpenLink Knowledge Graph.">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:title" content="{he(page_title)}">',
        f'<meta property="og:description" content="{he(desc)}">',
        '<meta property="og:site_name" content="FIFA World Cup 2026 · OpenLink Software">',
        '<script type="application/ld+json">',
        json.dumps({
            "@context": "https://schema.org",
            "@type": "Dataset",
            "name": page_title,
            "description": desc,
            "creator": {"@type": "Organization", "name": "OpenLink Software", "url": "https://www.openlinksw.com"},
            "keywords": ["FIFA World Cup 2026", "player analytics", "knowledge graph", title],
        }, indent=2),
        "</script>",
        '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>',
        '<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>',
        '<script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8/hammer.min.js"></script>',
        '<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.1/dist/chartjs-plugin-zoom.min.js"></script>',
        "<style>",
        css,
        "</style>",
        "</head>",
        "<body>",
        '<div class="page">',
        "",
        "  <!-- ── HEADER ── -->",
        '  <div class="header">',
        '    <div class="hdr-brand">',
        '      <div class="hdr-trophy">🏆</div>',
        '      <div class="hdr-wc">WORLD CUP 2026</div>',
        '      <div class="hdr-host">UNITED STATES | CANADA | MEXICO</div>',
        "    </div>",
        '    <div class="hdr-main">',
        f'      <div class="report-title">{he(title)} <span class="title-icon">{emoji}</span></div>',
        "    </div>",
        '    <div class="hdr-center">',
        f'      <div class="pl-title">{he(subtitle)}</div>',
        f'      <div class="pl-sub">{he(desc)}</div>',
        f'      <div class="pl-note">{he(note)}</div>',
        "    </div>",
        "  </div>",
        "",
        '  <div class="data-thru" id="dataThru">Data through World Cup 2026</div>',
        "",
        "  <!-- ── LOADING ── -->",
        '  <div id="loadingBox" class="loading-box">',
        '    <span class="spin">⚽</span>',
        '    <div class="loading-msg">Fetching player data from OpenLink FIFA Knowledge Graph…</div>',
        "  </div>",
        "",
        "  <!-- ── ERROR ── -->",
        '  <div id="errorBox" class="error-box" style="display:none;"></div>',
        "",
        "  <!-- ── CONTENT ── -->",
        '  <div id="content" style="display:none;">',
        f'    <div class="charts-row" style="grid-template-columns:{grid_cols};">',
        card_html,
        "    </div>",
        "",
        '    <!-- ── BOTTOM BAR ── -->',
        '    <div class="bottom">',
        '      <div class="legend">',
        '        <div class="leg-item"><div class="leg-dot" style="background:#1d5ca6;"></div><span><b>DF</b> Defender</span></div>',
        '        <div class="leg-item"><div class="leg-dot" style="background:#1a7f40;"></div><span><b>MF</b> Midfielder</span></div>',
        '        <div class="leg-item"><div class="leg-dot" style="background:#c8392b;"></div><span><b>FW</b> Forward</span></div>',
        '        <div class="leg-item"><div class="leg-dot" style="background:#5c6370;"></div><span><b>GK</b> Goalkeeper</span></div>',
        "      </div>",
        '      <div class="source" id="sourceBlock">',
        '        🌐 <b>Source:</b> <a href="https://demo.openlinksw.com/sparql" target="_blank" rel="noopener">OpenLink FIFA Knowledge Graph ↗</a>',
        f"        &nbsp;|&nbsp; demo.openlinksw.com<br>Player-level tournament totals · min {min_minutes} minutes played",
        "      </div>",
        "    </div>",
        "  </div>",
        "",
        "  <!-- ── PLAYER SELECTION MODAL ── -->",
        '  <div id="playerModal" class="modal-overlay" style="display:none;" role="dialog" aria-modal="true" aria-labelledby="modalTitle">',
        '    <div class="modal-box">',
        '      <div class="modal-header">',
        '        <span class="modal-title" id="modalTitle">Select Player</span>',
        '        <button class="modal-close" id="modalClose" aria-label="Close">✕</button>',
        "      </div>",
        '      <p class="modal-hint">Multiple players at this location — choose one to open their profile:</p>',
        '      <ul class="modal-list" id="modalList"></ul>',
        "    </div>",
        "  </div>",
        "",
        "</div><!-- /page -->",
        "",
        "<script>",
        "Chart.register(ChartDataLabels);",
        "Chart.register(ChartZoom);",
        "",
        f"const ENDPOINT = {json.dumps(ENDPOINT)};",
        f"const QUERY = {sparql_json};",
        "",
        js_static,
        "",
        "// ── Main ──────────────────────────────────────────────────────────────────────",
        "(async function main() {",
        "  try {",
        "    const raw     = await sparql(QUERY);",
        "    const players = parseRows(raw);",
        "    if (!players.length) throw new Error('No player data returned. The analytics graph may be empty or the endpoint unreachable.');",
        "",
        setup_js,
        "",
        "    // Update data-through line",
        "    const today = new Date().toLocaleDateString('en-US', { day:'numeric', month:'long', year:'numeric' });",
        "    document.getElementById('dataThru').textContent = `Data through ${today} · ${players.length.toLocaleString()} players`;",
        "    document.getElementById('loadingBox').style.display = 'none';",
        "    document.getElementById('content').style.display    = '';",
        "  } catch (err) {",
        "    console.error('[WC2026 Analytics]', err);",
        "    document.getElementById('loadingBox').style.display = 'none';",
        "    const box = document.getElementById('errorBox');",
        "    box.style.display = '';",
        "    box.innerHTML = `<strong>⚠️ Could not load data</strong><br><br>${err.message}<br><br>`",
        f"      + `<small>Endpoint: <code>{ENDPOINT}</code> — check the browser console for details.</small>`;",
        "  }",
        "})();",
        "</script>",
        "</body>",
        "</html>",
    ])


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Generate a Simon Brunson-style scatter analytics report for FIFA WC2026.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--title",       default="ANALYTICS",   help="Big headline text (uppercase, e.g. 'RUNNING DATA')")
    ap.add_argument("--emoji",       default="📊",          help="Icon placed next to the headline (e.g. '🏃')")
    ap.add_argument("--subtitle",    default="Player Analytics",  help="Centre-panel title")
    ap.add_argument("--desc",        default="Player-level relationships across the tournament", help="Centre-panel description")
    ap.add_argument("--note",        default="Players with 45+ tournament minutes", help="Small italic note in centre panel")
    ap.add_argument("--chart",       action="append", dest="charts", metavar="SPEC",
                    help="Chart spec: xKey,yKey[,xLabel,yLabel[,Title]]. Repeat for multiple charts (max 4).")
    ap.add_argument("--min-minutes", type=int, default=45, help="Minimum minutes played filter (default: 45)")
    ap.add_argument("--out",         default=None, help="Output HTML path (default: wc2026-analytics.html)")
    args = ap.parse_args()

    if not args.charts:
        # Default: reproduce the running data example
        args.charts = [
            "totalDistance,highSpeedDistance,Total distance (m),High-speed distance (m),Total Distance vs High-Speed Distance",
            "topSpeed,sprintMetres,Top speed (km/h),Sprint metres (m),Top Speed vs Sprint Metres",
        ]

    if len(args.charts) > 4:
        sys.exit("A maximum of 4 charts per report is supported.")

    charts = [parse_chart(spec, i+1) for i, spec in enumerate(args.charts)]
    html   = build_html(args.title, args.emoji, args.subtitle, args.desc, args.note, charts, args.min_minutes)
    out    = args.out or "wc2026-analytics.html"

    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    chart_desc = ", ".join(f"{c['xKey']} vs {c['yKey']}" for c in charts)
    print(f"✓ wrote {out}  ({len(html):,} bytes)  · {len(charts)} chart(s): {chart_desc}")


if __name__ == "__main__":
    main()
