---
name: "screencast-recorder"
description: "Record screencast videos of web application interactions using shot-scraper video. Use when the user says: record a screencast, record a video demo, make a walkthrough of, record this session, record what you just did. Handles mTLS-authenticated endpoints (linkeddata.uriburner.com:5443), local dev server demos, and after-the-fact recording from curl session history. Dual-format storyboards: YAML (native input for shot-scraper) and RDF Turtle (optional input, auto-generated session log)."
---

Record WebM/MP4 screencasts of browser interactions using `shot-scraper video`. Accepts YAML storyboards natively or RDF Turtle via the `ttl-to-yaml.py` converter.

## Prerequisite Check

Before recording, verify `shot-scraper` is available:

```bash
command -v shot-scraper >/dev/null 2>&1 || uv tool install shot-scraper
```

Install Playwright browsers if missing:
```bash
shot-scraper install 2>/dev/null || python3 -m playwright install chromium
```

## Output Convention

Recordings go to `{LLM_ROOT}/{model}/screencasts/` where `{LLM_ROOT}` is the canonical LLM root from preferences artifact-routing rules (`{LLM_ROOT}`), and `{model}` is the model-specific output directory (e.g., `Big Pickle`, `DeepSeek`, `Claude Generated`). Use descriptive filenames: `{YYYY-MM-DD}-{topic}.mp4` (with companion `.webm`).

When recording, derive the path at runtime by looking up the model's output path per `agent-rdf-memory/howto/artifact-routing.ttl` and appending `screencasts/`.

## Workflow

### Step 1: Determine Mode (disambiguate automatically)

**Mode A — curl → screencast**: User explored resources via mtls-curl commands. Parse the conversation for curl URLs, present the extracted URL list to the user.

**Mode B — direct browser**: URLs were discussed directly (not via curl). Present them as-is.

If neither is clear, ask: "What URLs or resources should the screencast show?"

### Step 2: Elicit Scene List

Present a curated list to the user with numbered scenes:

> "I found these URLs from the session:
>  1. {url-1}
>  2. {url-2}
>  3. {url-3}
>
> Want all of them? Adjust order? Add scene names? Set pauses between scenes?"

Capture user preferences:
- **Scene ordering** — reorder, drop, or add scenes
- **Scene names** — labels for each scene (shown in progress output)
- **Pauses** — how long to pause on each scene (default 2s for readability)
- **Cursor** — visible cursor with click rings enabled by default
- **Viewport** — default 1440x900 (wider for SPARQL result pages)

### Step 3: Build Storyboard

Construct the `storyboard.yml`. The user may also provide a `storyboard.ttl` — in that case, run:

```bash
python3 scripts/ttl-to-yaml.py storyboard.ttl -o storyboard.yml
```

Core storyboard structure (hand-authored):

```yaml
output: {SCREENCAST_DIR}/{filename}.webm
url: {starting-url}
viewport:
  width: 1440
  height: 900
cursor:
  visible: true
  clicks: true
  color: "#1a73e8"
wait_for: body

scenes:
- name: "{scene-1-name}"
  do:
  - pause: 2
- name: "{scene-2-name}"
  open: "{scene-2-url}"
  wait_for: body
  do:
  - pause: 2
```

### Step 4: Handle Auth

Detect mTLS-requiring endpoints (port `:5443`, host `linkeddata.uriburner.com`).

On macOS, Chromium picks up client certificates from the Keychain automatically — no special config needed.

For self-signed server certs on port 5443, add browser args:

```bash
shot-scraper video storyboard.yml --mp4 --browser-arg --ignore-certificate-errors
```

For other auth mechanisms, use:
- `--auth` : cookie-based auth JSON file (see shot-scraper auth docs)
- `--auth-username` / `--auth-password` : HTTP Basic auth

### Step 5: Record

```bash
shot-scraper video storyboard.yml --mp4 [--browser-arg --ignore-certificate-errors]
```

Always include `--mp4` to produce both WebM and MP4 outputs.

After recording, verify both files exist.

### Step 6: Deliver

Report to the user:

> "Screencast recorded:
>   MP4:  {SCREENCAST_DIR}/{filename}.mp4
>   WebM: {SCREENCAST_DIR}/{filename}.webm"

### Step 7: Log (Post-Recording)

Generate an RDF Turtle log of the recording session and append to `agent-rdf-memory/`:

```bash
python3 scripts/yaml-to-ttl.py storyboard.yml -o {SCREENCAST_DIR}/{filename}.log.ttl
```

This produces a queryable record of what was recorded, when, and which URLs were visited.

## Dual-Format Storyboard Support

The skill accepts storyboards in two formats:

### YAML (Native)
Standard `storyboard.yml` consumed directly by `shot-scraper video`.
See `references/storyboard-schema.md` for the full schema.
See `templates/` for ready-to-use starter templates.

### RDF Turtle
A `storyboard.ttl` using schema.org + the screencast ontology.
See `references/screencast-ontology.ttl` for the term definitions.
See `templates/*.ttl` for starter templates.

Convert TTL → YAML before recording:

```bash
python3 scripts/ttl-to-yaml.py storyboard.ttl -o storyboard.yml
shot-scraper video storyboard.yml --mp4
```

### Post-Recording Log (Auto-generated RDF)
After recording, generate a `.log.ttl` file with recording metadata.
This can be loaded into SPARQL-queriable memory or directly into `agent-rdf-memory/`.

## HTML Report Mode (no-webapp demos)

When no browser URL exists (e.g., a CLI-only session), generate a self-contained HTML summary page, serve it locally via Python, and record a walkthrough of the report:

```yaml
python: |
  from pathlib import Path
  html = "<html><body><h1>Session Summary</h1>..."
  Path("/tmp/screencast-report.html").write_text(html)
server: python3 -m http.server 8765 --directory /tmp
url: http://localhost:8765/screencast-report.html
```

## Elicitation Best Practices

- Present scenes as a numbered list with URLs visible
- Ask about pauses: "How long on each scene? Default 2s?"
- Ask about cursor: "Visible cursor with click rings?"
- For long/multi-URL sessions, suggest grouping by purpose rather than URL count
- Always confirm before recording — recording takes real time (pauses add up)

## References

- **storyboard-schema.md** — complete YAML syntax reference
- **common-patterns.md** — reusable scene patterns (YAML + TTL)
- **screencast-ontology.ttl** — RDF ontology for storyboard Turtle representation

## Scripts

- `scripts/ensure-shot-scraper.sh` — install prerequisites
- `scripts/ttl-to-yaml.py` — convert RDF Turtle → YAML storyboard
- `scripts/yaml-to-ttl.py` — convert YAML storyboard → RDF Turtle log
