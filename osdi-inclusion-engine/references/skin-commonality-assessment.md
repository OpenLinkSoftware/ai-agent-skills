# Skin Commonality Assessment

Before authoring any new skin(s), decide whether the candidate mockups share enough to justify **one shared skin** or need **separate skins per site**. This is a design judgment, not a script output — but a quick structural scan gives concrete signal to ground the conversation.

## What to Compare

For each candidate mockup, extract:

- **Font family** (`@font-face` / Google Fonts `family=` params)
- **CSS custom property names** (`--token:` declarations) — matching *names* (not just similar colors) indicate a shared design-token vocabulary worth centralizing
- **CSS framework usage** — Bootstrap classes present or absent
- **Nav/menu markup pattern** — hamburger/toggler class names, whether a dynamic mobile-menu script is present, and whether it's the same script

`scripts/check_chrome_conflict.py` reports chrome tags/classes and external assets per file; supplement it with a manual grep across candidates for the four points above (see worked example below for the exact greps).

## Decision Rule

- **Shared fonts, shared custom-property names, same CSS framework choice, same nav/menu JS pattern** across most/all candidates → author **one shared skin** (`zion` per the naming suggestion — deliberately the inverse of `matrix`: the shared `PostProcess.xslt` supplies structure/behavior, and a per-site `<xsl:include href="{site}/xslt/layout.xslt"/>` supplies the variation). This keeps conditionality in the skin low: differences live in separate included files, not in `<xsl:choose>` branches keyed on `$site`.
- **Divergent fonts, no shared token names, inconsistent framework usage, different nav patterns** → the mockups are not one design system wearing different skins — they're three unrelated designs. Author **one new skin per site** following `references/skin-authoring-howto.md`. Forcing a shared skin here would require heavy `<xsl:choose test="$site='...'">` branching — exactly the conditionality this process is meant to minimize.

## Worked Example — virtuoso / uda / ps Mockups (2026-07)

Structural scan across the three replacement homepages:

| | Virtuoso | UDA | PS |
|---|---|---|---|
| Font | Inter | Montserrat | Inter |
| CSS custom properties | `--accent-strong`, `--accent`, `--font-body`, `--font-display`, `--font-mono`, `--rule` | `--acc`, `--bd`, `--bg`, `--border-c`, `--cloud`, `--fog`, `--ink`, `--ol-blue-lt` | `--bg-light`, `--ink`, `--muted`, `--ols-blue-dark`, `--ols-blue-medium`, `--ols-button-hover`, `--ols-check`, `--ols-cta` |
| Bootstrap | Yes (5.3.3, `navbar`/`navbar-expand-lg` classes) | No | No |
| Nav/menu markup | Bootstrap navbar, no custom toggle class | `btn-nav`/`btn-nav-ghost`/`btn-nav-solid`, custom `hdr-nav` | Plain `<header class="masthead">`, no toggle markup found |

**Finding: not enough commonality.** Across all three, only `--rule` is a shared token name (confirmed via `check_chrome_conflict.py --compare`), and that's plausibly coincidental rather than a deliberate shared vocabulary — `--ink` is shared only between UDA and PS, not all three. Fonts split 2:1 (Virtuoso/PS both Inter, UDA Montserrat) but the matching pair doesn't correlate with any other shared trait. Bootstrap appears in exactly one of three. Nav-toggle markup (`btn-nav`) appears only in UDA. **Recommendation for this batch: three separate new skins, not a shared `zion` skin** — a shared skin here would need per-site conditionals for font, tokens, framework, and nav markup simultaneously, which is the antithesis of low-conditionality skin design.

Reproduce the scan directly with the script (preferred — avoids manual grep drift):

```bash
python3 scripts/check_chrome_conflict.py --compare virtuoso.html uda.html ps.html
```

which prints the per-file font/bootstrap/nav-toggle/css-props table above, the shared-property-name intersection across ALL candidates, and a signal line (strong/weak commonality).

If a future batch of mockups *does* share tokens/fonts/framework/nav pattern, re-run this comparison and revisit the `zion` shared-skin option — the decision is per-batch, not fixed by this precedent.
