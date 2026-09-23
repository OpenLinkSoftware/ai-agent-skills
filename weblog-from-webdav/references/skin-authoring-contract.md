# Skin Authoring Contract

`templates/deploy-weblog-skinned.sql` renders the weblog with a selectable
skin (look-and-feel) as a configuration modality, resolved **at request
time** inside the deployed `index.vsp` — not baked in at deploy time, so
switching skins needs no redeploy.

## Resolution order

1. `?skin=<name>` query-string override on the current request.
2. The `weblog:skin` custom property set on the DAV **collection** resource
   (via `DB.DBA.DAV_PROP_SET`, read back through the shared
   `DB.DBA.WEBLOG_DAV_GET_COLLECTION_PROP` helper — collection properties
   live in `WS.WS.SYS_DAV_COL`/`PROP_TYPE='C'`, a different table and marker
   than the per-post `schema:category`/`schema:position` properties in
   `WS.WS.SYS_DAV_RES`/`PROP_TYPE='R'`; do not conflate the two).
3. The `default_skin` argument passed to `WEBLOG_DAV_DEPLOY_SKINNED` at
   deploy time.

Only `classic` and `editorial` are recognized values; anything else falls
back to the deploy-time default.

## What every skin must supply

All skins share the same business logic (post enumeration/dedup, pinning,
category/facet aggregation, calendar/search filtering, RSS/Atom/AtomPub
generation, the `?raw=` raw-content endpoint, and the `?nl_action=` newsletter
dispatcher) — none of that is skin-specific and must never be duplicated
per skin. A skin branch (`<?vsp if (skin = ''<name>'') { ?> ... <?vsp } ?>`)
only needs to supply:

- A `<style>` block defining, at minimum, these CSS custom properties so the
  shared newsletter band and footer theme correctly: `--accent`,
  `--accent-soft`, `--accent-quiet`, `--panel`, `--text`, `--muted`,
  `--border`, `--shadow`, `--rss`. Provide both a light default and a
  `html[data-theme="dark"]` / `@media (prefers-color-scheme: dark)` override
  pair, following the existing `classic`/`editorial` blocks.
- A masthead (`<header class="masthead">`) — can be structurally identical
  to another skin's, just restyled, or genuinely different layout.
- A "current post" / hero rendering branch, driven by the same `posts` /
  `pinned_posts` arrays and `idx` / `post_selected` variables the shared
  business logic already computed.
- An archive rendering branch (list or grid) over the same `posts` array.
- A search/date/category filter UI, submitting to `{{PUBLIC_ROUTE}}` via GET
  with `q` / `from` / `to` / `category` params (already parsed by the shared
  logic) — category chips can reuse `category_cloud`, built once and shared.

## What a skin must NOT do

- Re-implement post enumeration, pinning, category aggregation, or feed
  generation. These run once, before the skin branch, regardless of which
  skin is selected.
- Assume a raw post's URL is a plain file path. Always link to
  `{{PUBLIC_ROUTE}}?raw=<filename>` for `<iframe>` embeds — the VSP-only
  VHOST route (`is_brws=0`, `def_page=index.vsp`) dispatches every path
  under it to `index.vsp`, so a nested "real" file path is never reachable;
  see the `?raw=` handler comment in `deploy-weblog-skinned.sql` for the
  full explanation.
- Add its own newsletter subscribe form markup independent of the shared
  `.newsletter-band` section — that section is emitted once, outside the
  skin branch, and themed purely through the skin's own CSS variable values.

## Adding a third skin

1. Add the name to the two `if (skin <> ''classic'' and skin <> ''editorial'')`
   guards (skin resolution, and the `default_skin` normalization at the top
   of `WEBLOG_DAV_DEPLOY_SKINNED`).
2. Add a new `<?vsp if (skin = ''<name>'') { ?> ... <?vsp } else if (skin = ...) { ?>`
   branch for both the `<style>` block and the body-content block, following
   the pattern above.
3. Redeploy with `isql`, then verify with `?skin=<name>` before setting it as
   any collection's persistent default.
