# Verification Checklist — WC2026 Match Report

Run these checks against the generated HTML before declaring the report complete.

```bash
F="path/to/report.html"
```

## Python verification script (recommended)

```python
import re
html = open(F).read()

checks = [
    ("og:image", len(re.findall('og:image', html)) >= 1),
    ("hero-image-wrap", len(re.findall('hero-image-wrap', html)) >= 1),
    ("digitalhub.fifa.com", len(re.findall('digitalhub\\.fifa\\.com', html)) >= 1),
    ("Image source caption", len(re.findall('Image source', html)) >= 1),
    ("≥22 player circles", len(re.findall('<circle', html[html.find('id="formations"'):html.find('id="squads"')])) >= 22),
    ("≥10 entity-links in #core-players", len(re.findall('entity-link', html[html.find('id="core-players"'):html.find('id="sparql"')])) >= 10),
    ("Pressing gauges", len(re.findall('press-item', html)) >= 3),
    ("Timeline events", len(re.findall('tl-event', html)) >= 5),
    ("Distance & Speed card", len(re.findall(r'Distance.*Speed|Speed.*Distance', html, re.I)) >= 1),
    ("Distinct accent/accent-dim", (lambda a,d: a and d and a!=d)(
        (re.search(r'--accent:\s*([^;]+)', html) or re.search(r'x', '')).group(1).strip() if re.search(r'--accent:\s*([^;]+)', html) else '',
        (re.search(r'--accent-dim:\s*([^;]+)', html) or re.search(r'x', '')).group(1).strip() if re.search(r'--accent-dim:\s*([^;]+)', html) else ''
    )),
    ("7 attribution cards", len(re.findall('<div class="attr-card">', html)) == 7),
    ("Copyright line", len(re.findall('© 2026 OpenLink Software · FIFA World Cup 2026 Match Intelligence', html)) >= 1),
    ("copyAnchor calls", len(re.findall('copyAnchor', html)) >= 5),
]

all_pass = True
for name, result in checks:
    status = "✅" if result else "❌ FAIL"
    if not result: all_pass = False
    print(f"{status} {name}")

print(f"\n{'✅ ALL GATES PASS' if all_pass else '❌ FAILURES — fix before delivering'}")
```

## Manual checks (not automatable)

- Coach names are visible in the hero section and are entity-linked
- Formation SVGs show player names beneath circles
- Pressing gauge bars render with distinct colours (not identical)
- Dark mode toggle (🌙 button) switches theme correctly
- Navigation panel drag works on desktop
- Section title hover shows 🔗 icon and tooltip
- SPARQL accordion expands/collapses on click
- Live SPARQL query links open in new tab
