---
name: "screencast-recorder"
description: "Record screencast videos of web application interactions using shot-scraper video. Use when the user says: record a screencast, record a video demo, make a walkthrough of, record this session, record what you just did, add voice-over narration, or mix narration into a screencast. Handles mTLS-authenticated endpoints (linkeddata.uriburner.com:5443), local dev server demos, after-the-fact recording from curl session history, optional OpenAI TTS MP3 generation, dual-format storyboards (YAML/RDF Turtle), and DEFAULT distribution HTML that MUST embed the primary MP4 via HTML5 video (never download-only). Male default voice: onyx."
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

### Step 6: Deliver recording files

Report to the user:

> "Screencast recorded:
>   MP4:  {SCREENCAST_DIR}/{filename}.mp4
>   WebM: {SCREENCAST_DIR}/{filename}.webm"

### Step 6b: Distribution HTML — embed the MP4 (DEFAULT, BLOCKING)

**Default behavior:** every screencast bundle that includes a distributable presentation page MUST embed the primary MP4 with an in-document HTML5 `<video>` player. Download-only pages fail delivery.

Required pattern (bundle-relative paths; prefer narrated mux when present):

```html
<div class="player">
  <video id="screencast-player" controls playsinline
         poster="poster.jpg" preload="metadata"
         width="1440" height="900"
         aria-label="{description}">
    <source src="{filename}-with-voiceover.mp4" type="video/mp4" />
    <source src="{filename}.mp4" type="video/mp4" />
    <source src="{filename}.webm" type="video/webm" />
    <p>Your browser does not support embedded HTML5 video.
       <a href="{filename}-with-voiceover.mp4">Download the MP4</a>.</p>
  </video>
</div>
```

Also required on the same page:
- Filename: `{model-display-id}-{topic-slug}-presentation.html` (not bare `presentation.html`)
- Bundle path: `{model-root}/screencasts/{bundle}/`
- POSH `rel="enclosure"` + JSON-LD `VideoObject.contentUrl` matching the primary embedded file
- Hero/footer on-behalf-of attribution

Gate contract (preferences): `step-screencastEmbedMp4` (pos 156), companion howto `agent-rdf-memory/howto/screencast-distribution-artifacts.ttl` (`:stepEmbedPrimaryMp4`).

Validation before handoff:
```bash
# Must find an embedded player sourcing the primary MP4
grep -E '<video[^>]*controls' "{presentation}.html"
grep -E 'src="[^"]+\.mp4"' "{presentation}.html"
# Relative media files must exist next to the HTML
test -f "{SCREENCAST_DIR}/{filename}-with-voiceover.mp4" || test -f "{SCREENCAST_DIR}/{filename}.mp4"
```

### Optional: Voice-over Narration

When the user wants voice-over narration, generate a standalone MP3 first and ask the user to approve the voice quality before modifying the screencast.

Use `scripts/screencast-openai-voiceover.py` when the user wants an OpenAI TTS narration track:

```bash
python3 scripts/screencast-openai-voiceover.py \
  --text-file narration.txt \
  --output "{SCREENCAST_DIR}/{filename}-voiceover.mp3" \
  --voice onyx \
  --instructions "Speak as a calm, confident technical narrator. Keep the pace measured and clear."
```

Default voice for male narration is **onyx**; use **coral** (or another OpenAI TTS voice) only when the user requests a different voice.

The script requires `OPENAI_API_KEY` and the Python `openai` package. If local Python dependencies are broken, tell the user clearly and either repair the environment with approval or ask them to provide an externally generated MP3.

#### Fallback: local/offline narration via Piper

If OpenAI TTS is unreachable (no API key, out of quota, network down) and the user wants to proceed without waiting, offer `scripts/screencast-piper-voiceover.py` as a local, offline alternative. It is an **optional dependency** -- nothing installs at skill-load time. The script installs `piper-tts` (pip) and downloads the requested voice model (one-time, ~50-120MB depending on quality tier) only when actually run, and only if not already cached under `~/.cache/piper-voices/`.

```bash
python3 scripts/screencast-piper-voiceover.py \
  --text-file narration.txt \
  --output "{SCREENCAST_DIR}/{filename}-voiceover.mp3" \
  --voice en_US-ryan-high
```

Default voice for male narration is **en_US-ryan-high** (highest quality tier). Other male options: `en_US-norman-medium`, `en_US-bryce-medium`, `en_US-hfc_male-medium`, `en_GB-alan-medium`, `en_GB-northern_english_male-medium`. Full voice list: https://huggingface.co/rhasspy/piper-voices/tree/main/en

**Known limitation, state this to the user before using it:** Piper has no style/instructions prompt -- it is fixed-voice, fixed-prosody synthesis. There is no way to ask for "steady, unhurried power" or any other delivery style the way the OpenAI path's `--instructions` allows. The script's defaults (`--length-scale 1.05`, `--noise-scale 0.5`, `--noise-w-scale 0.6`, all tuned down/up from Piper's own stock defaults of 1.0/0.667/0.8) are the closest numeric PROXY for a steady, measured delivery -- flatter variation and a touch slower pace -- but this is an approximation, not real style control. It cannot add emphasis, warmth, urgency, or any other directed quality; the voice choice itself carries most of the tone. If the user needs precise, describable style control, OpenAI TTS (or another cloud provider) remains the better fit -- Piper is for when a narration is needed and no cloud TTS is reachable, not a drop-in style-equivalent replacement.

The upstream project (`OHF-Voice/piper1-gpl`) is GPL-3.0 licensed. That is not a practical concern for local, personal use of the installed tool, but do not bundle/redistribute the package or voice models as part of a shipped product without checking license compatibility first.

After the user approves the MP3, mux it into the MP4 while preserving captions:

```bash
ffmpeg -y \
  -i "{SCREENCAST_DIR}/{filename}.mp4" \
  -i "{SCREENCAST_DIR}/{filename}-voiceover.mp3" \
  -map 0:v -map 1:a -map 0:s? \
  -c:v copy -c:a aac -b:a 160k -c:s copy \
  -shortest -movflags +faststart \
  "{SCREENCAST_DIR}/{filename}-with-voiceover.mp4"
```

Verify the output with `ffprobe` and keep the original silent MP4 unless the user explicitly asks to replace it.

**After muxing, the distribution HTML `<video>` primary `<source>` MUST point at `{filename}-with-voiceover.mp4`.**

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
