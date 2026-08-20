# Editorial Enhancement Module

A set of reusable components extracted from an aesthetic-enhancement pass over an already-generated, already-validated infographic (the Coyle/Idehen ontologies-meshup collection, Claude Sonnet 5, 2026-08-20). This is **not a template** — it is a layer that sits on top of whichever base template was selected from `template-options.md`. Use it when the source content has quantitative claims worth foregrounding, or a relational structure between multiple meshed sources (responds-to / meshes-with / cites / extends), regardless of which base template is in play.

All six pieces below are generalized from the worked instance; none of the specific numbers, entity names, or copy in this document are meant to be reused verbatim — every instance must be derived from that document's own companion RDF, per the harness contract's RDF-source-of-truth requirement.

## When to reach for this module

| Signal in the source | Component to add |
|---|---|
| A composition/decay/growth statistic buried in prose (a % that compounds, a rate that multiplies over steps or time) | Stat band + trend figure |
| The source's argument turns on a named binary or two-way contrast (X vs. Y, inside vs. outside, before vs. after) | Duality panel |
| The RDF contains a synthesis/critical-perspective/cross-reference section connecting this document to other meshed sources | Mesh cards |
| The document meshes 2+ named source documents | Source strip |
| Every section currently renders as an identical panel with no visual hierarchy | Section rhythm fix (do this one regardless of the others) |

## 1. Section rhythm fix (do this first, always)

**The bug this fixes:** a client-side IIFE recomputing `.section-alt` by DOM parity already exists in most generated pages (search for `topLevel.forEach` + `classList.toggle('section-alt', i % 2 === 0)`). If a "featured" section variant (e.g. `.section-feature`) declares its own `background-color`, that IIFE cannot override it, so the section stays visually tinted even when the alternation would put it in the flush slot — producing two adjacent tinted sections and breaking the rhythm. Give any featured-section variant a `background-image` accent wash instead of a `background-color`, so it always layers over whatever the rhythm assigns:

```css
.section-feature{
  position:relative;
  /* background-COLOR deliberately omitted — see note above */
  background-image:linear-gradient(180deg,var(--accent-soft),transparent 260px);
  border-radius:12px;margin-bottom:2rem;padding:4rem 2rem;
  border-top:2px solid var(--primary)
}
```

Verify with a DOM query before delivery, not by eye:

```js
const tops=[...document.querySelectorAll('.section')].filter(el=>!el.parentElement.closest('.section'));
const rows=tops.map(el=>getComputedStyle(el).backgroundColor);
const dupes=rows.filter((c,i)=>i>0&&c===rows[i-1]&&c!=='rgba(0, 0, 0, 0)');
console.log('adjacent same-background sections:', dupes.length); // must be 0
```

## 2. Source strip

An N-source provenance strip for a meshup document — one card per meshed source, the anchor/primary source visually distinguished, each name resolver-linked to its own RDF entity.

```css
.source-strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(205px,1fr));gap:.85rem;margin-top:1.6rem}
.source-item{display:flex;gap:.7rem;align-items:flex-start;background:var(--card-bg);border:1px solid var(--border);border-radius:11px;padding:.85rem 1rem;box-shadow:var(--card-shadow);min-width:0;transition:box-shadow .25s,transform .25s}
.source-item:hover{box-shadow:var(--card-hover-shadow);transform:translateY(-2px)}
.source-mark{flex-shrink:0;width:26px;height:26px;border-radius:7px;background:var(--accent-soft);color:var(--primary);display:flex;align-items:center;justify-content:center;font-size:.66rem;font-weight:700;letter-spacing:.02em}
.source-item.is-anchor .source-mark{background:var(--primary);color:var(--on-accent)}
.source-name{display:block;font-size:.86rem;font-weight:600;line-height:1.35;color:var(--primary);overflow-wrap:anywhere}
.source-role{display:block;font-size:.72rem;color:var(--text-secondary);margin-top:.18rem;line-height:1.4}
```

**Track-width gotcha:** pick `minmax()` so N sources fit on one row at the container's actual measured width — do the arithmetic (`N × track + (N-1) × gap ≤ container width`) rather than guessing a round number like `230px`. A too-wide minimum silently drops to `N-1` columns and orphans one card onto its own row.

Markup: one `.source-item` per meshed document, `.is-anchor` on the primary/anchor source, name wrapped in the resolver link, role line naming author/platform/relationship to the anchor.

## 3. Stat band + trend figure

Surfaces a buried quantitative claim (a rate, a compounding statistic, a threshold) as the first thing a reader sees in that section, not the last sentence of a paragraph.

```css
.stat-band{display:grid;grid-template-columns:repeat(auto-fit,minmax(186px,1fr));gap:1rem;margin:1.9rem 0 0}
.stat-tile{position:relative;background:var(--card-bg);border:1px solid var(--border);border-radius:14px;padding:1.3rem 1.3rem 1.15rem 1.5rem;box-shadow:var(--card-shadow);overflow:hidden;min-width:0}
.stat-tile::before{content:'';position:absolute;top:0;bottom:0;left:0;width:3px;background:var(--tone,var(--primary))}
.stat-figure{font-family:'Poppins',sans-serif;font-size:2rem;font-weight:700;line-height:1;letter-spacing:-.035em;color:var(--tone,var(--primary))}
.stat-expr{display:block;margin-top:.5rem;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.74rem;color:var(--text-secondary)}
.stat-label{display:block;margin-top:.5rem;font-size:.82rem;line-height:1.5;color:var(--text)}
```

Set `--tone` per tile inline (`style="--tone:var(--danger)"`) using semantic colour, not decoration: `--danger` for a figure the source frames as a problem/collapse, `--success` for one it frames as a win, `--accent-warm` for a neutral/baseline figure.

For the companion trend figure, generate an inline SVG with numeric coordinates computed directly from the source's own formula (do not hand-place points) — see the worked instance's Python generation code for the coordinate-mapping pattern (`px(x)`/`py(y)` closures over a fixed viewBox, one `<polyline>` per series, gridlines from axis ticks, end-label placed at the final data point). Reuse `.decay-figure`/`.dx-curve`/`.dx-grid`/`.dx-axis`/`.dx-tick` class names from the worked instance if the shape is genuinely a decay/growth curve; for other trend shapes (bar comparison, scatter), follow the same "compute from source formula, not by eye" discipline but choose SVG primitives that fit the actual data shape.

**Every visual entity in the figure that maps to an RDF instance must be a resolver-linked SVG `<a>`**, per the harness contract's resolver-link requirement — do not ship a purely decorative chart with no entity links when the underlying values exist as RDF literals.

## 4. Duality panel

For a source whose argument turns on a named two-way contrast — two dimensions of one concept, before/after, inside/outside.

```css
.duality-quote{margin:1.9rem 0 0;padding:1.1rem 1.4rem;border-left:3px solid var(--primary);background:var(--accent-soft);border-radius:0 11px 11px 0;font-family:'Poppins',sans-serif;font-size:1.05rem;font-weight:600;line-height:1.5;color:var(--text)}
.duality{display:grid;grid-template-columns:1fr 1fr;gap:1.15rem;margin-top:1.15rem}
.duality-card{position:relative;background:var(--card-bg);border:1px solid var(--border);border-radius:14px;padding:1.4rem 1.5rem;box-shadow:var(--card-shadow);min-width:0}
.duality-card::before{content:'';position:absolute;top:0;left:1.5rem;right:1.5rem;height:2px;background:var(--tone,var(--primary));border-radius:0 0 2px 2px}
.duality-flag{display:inline-flex;align-items:center;gap:.4rem;font-size:.66rem;font-weight:700;text-transform:uppercase;letter-spacing:.13em;color:var(--tone,var(--primary))}
.duality-flag::before{content:'';width:6px;height:6px;border-radius:50%;background:currentColor}
@media(max-width:768px){.duality{grid-template-columns:1fr}}
```

Only build this when the RDF actually models the two sides as distinct typed entities (e.g. two instances of a shared class with a boolean or enum property distinguishing them) — the panel should render the graph's own structure, not an editorial invention layered on top of undifferentiated prose. If the source's contrast exists only in prose with no RDF entities behind it, either mint the two entities in the companion TTL first, or skip this component.

## 5. Mesh cards

For rendering a synthesis/critical-perspective/cross-reference section — the part of a meshup document that states how multiple sources relate, not just that they were consulted.

```css
.mesh-list{display:grid;gap:1.35rem;margin-top:2rem}
.mesh-card{position:relative;background:var(--card-bg);border:1px solid var(--border);border-left:3px solid var(--primary);border-radius:0 14px 14px 0;padding:1.55rem 1.7rem 1.4rem;box-shadow:var(--card-shadow);min-width:0}
.mesh-head{display:flex;align-items:baseline;gap:.85rem;margin-bottom:.6rem}
.mesh-index{flex-shrink:0;font-size:.78rem;font-weight:700;color:var(--primary);background:var(--accent-soft);border-radius:6px;padding:.2rem .5rem}
.mesh-rel{display:flex;flex-wrap:wrap;align-items:center;gap:.45rem;margin-top:1.05rem;padding-top:.95rem;border-top:1px solid var(--border)}
.mesh-rel-label{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.13em;color:var(--text-secondary)}
.mesh-chip{display:inline-flex;align-items:center;gap:.35rem;font-size:.76rem;font-weight:500;color:var(--primary);background:var(--bg-alt);border:1px solid var(--border);border-radius:999px;padding:.28rem .7rem}
.mesh-chip.is-source{border-style:dashed}
```

One `.mesh-card` per critical-perspective/synthesis RDF entity, full `schema:description` text (never truncate — this was a real bug in the worked instance's first draft: a card cut off mid-sentence because a generator-produced summary field was shorter than the full RDF literal). Two `.mesh-rel` rows per card: "Responds to" (the argument-move/claim entity this perspective addresses) and "Meshes with" (the other source document it connects to), each populated from whatever RDF property the companion TTL actually uses for that relation (e.g. a reused external `karp:respondsTo`-style property, or `schema:mentions`) — do not invent relation labels the graph doesn't support.

## 6. Verification

All six components must pass the same gates as everything else in the harness contract — this module does not relax any of them:

- `scripts/validate-harness-contract.py` — 0 failures, same as any other change to the page.
- No visible truncation: `grep -oP '<p>[^<]{60,}?…</p>'` on the output must return nothing.
- Contrast: every new text/background pairing must be checked with **alpha-compositing over the true ancestor background stack**, not `getComputedStyle().color`/`.backgroundColor` read in isolation — a translucent `--accent-soft` background composited over a light-mode `--bg-alt` and a dark-mode `--bg` can differ enough to flip a pass/fail. Also settle CSS transitions before reading (`await new Promise(r=>setTimeout(r,600))` after any theme toggle) — a mid-transition read produces a false failure.
- No horizontal overflow at 390px width: `document.documentElement.scrollWidth <= window.innerWidth + 1`.
- Both themes: re-run every check with `data-theme="dark"` and `data-theme="light"` explicitly set, not just the system default.
