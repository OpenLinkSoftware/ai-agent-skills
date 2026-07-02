# Common Scene Patterns

Reusable scene patterns for screencast storyboards, in both YAML and RDF Turtle.

## Pattern 1: Multi-URL Data Walkthrough

Explore multiple linked data resources in sequence.

YAML:
```yaml
output: /Users/kidehen/Movies/screencasts/data-walkthrough.webm
url: https://linkeddata.uriburner.com:5443/DAV/demos/resource-1.ttl
viewport:
  width: 1440
  height: 900
cursor:
  visible: true
  clicks: true
  color: "#1a73e8"

scenes:
- name: "Raw Turtle document"
  do:
  - pause: 2

- name: "HTML rendering"
  open: https://linkeddata.uriburner.com:5443/DAV/demos/resource-1.html
  wait_for: body
  do:
  - pause: 2

- name: "SPARQL query results"
  open: "https://linkeddata.uriburner.com:5443/sparql/?query=SELECT+...&format=text%2Fx-html%2Btr"
  wait_for: body
  do:
  - pause: 3
```

RDF Turtle:
```turtle
@prefix : <#> .
@prefix schema: <http://schema.org/> .
@prefix sc: <https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/screencast-recorder/ontology#>.

:storyboard a schema:HowTo ;
  schema:name "Data Walkthrough"@en ;
  schema:url <https://linkeddata.uriburner.com:5443/DAV/demos/resource-1.ttl> ;
  sc:viewportWidth 1440 ;
  sc:viewportHeight 900 ;
  sc:cursorVisible true ;
  sc:cursorClicks true ;
  sc:cursorColor "#1a73e8" ;
  schema:step :scene-1, :scene-2, :scene-3 .

:scene-1 a schema:HowToStep ;
  schema:position 1 ;
  schema:name "Raw Turtle document"@en ;
  schema:direction [
    a sc:PauseAction ;
    sc:pauseDuration 2.0
  ] .

:scene-2 a schema:HowToStep ;
  schema:position 2 ;
  schema:name "HTML rendering"@en ;
  schema:url <https://linkeddata.uriburner.com:5443/DAV/demos/resource-1.html> ;
  schema:direction [
    a sc:WaitForAction ;
    sc:selector "body"
  ], [
    a sc:PauseAction ;
    sc:pauseDuration 2.0
  ] .
```

## Pattern 2: Local Server Demo

Start a dev server, prepare demo data, record interaction:

```yaml
output: /Users/kidehen/Movies/screencasts/server-demo.webm
python: |
  from pathlib import Path
  root = Path("/tmp/demo-data")
  root.mkdir(parents=True, exist_ok=True)
  (root / "index.html").write_text("<h1>Demo App</h1>")
server: python3 -m http.server 8765 --directory /tmp/demo-data
url: http://localhost:8765/
viewport:
  width: 1440
  height: 900
cursor: true

scenes:
- name: "App loads"
  do:
  - pause: 2

- name: "Navigate to feature"
  do:
  - click: "a.feature-link"
  - wait_for: "h1"
  - pause: 2
```

## Pattern 3: Authenticated Resource Tour

For mTLS-protected endpoints (port 5443). Browser picks up cert from Keychain automatically; add `--ignore-certificate-errors` for self-signed server certs.

```yaml
output: /Users/kidehen/Movies/screencasts/auth-demo.webm
url: https://linkeddata.uriburner.com:5443/some/resource
viewport:
  width: 1440
  height: 900
cursor: true

scenes:
- name: "Resource loaded (mTLS automatic)"
  do:
  - pause: 2

- name: "Query with results"
  open: "https://linkeddata.uriburner.com:5443/sparql/?query=..."
  wait_for: body
  do:
  - pause: 3
```

Recording command:
```bash
shot-scraper video storyboard.yml --mp4 --browser-arg --ignore-certificate-errors
```

## Pattern 4: Clipboard Demo

Monkey-patch clipboard API for demo data (from Simon Willison's pattern):

```yaml
javascript: |
  (() => {
    let clipboardText = "";
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      get: () => ({
        writeText: async (text) => { clipboardText = String(text); },
        readText: async () => clipboardText,
      }),
    });
  })();
scenes:
- name: "Bulk insert"
  do:
  - click: "button[data-action='insert']"
  - wait_for: "#dialog[open]"
  - click: ".bulk-insert-tab"
  - wait_for: ".bulk-textarea"
  - fill:
      into: ".bulk-textarea"
      text: |
        col1,col2,col3
        val1,val2,val3
        val4,val5,val6
  - click: ".preview-btn"
  - wait_for: "text=Previewing"
  - pause: 1
```

## Pattern 5: Clipboard Viewport Clipping

When recording on retina/HiDPI displays, use `--browser-arg` to force pixel-perfect rendering:

```bash
shot-scraper video storyboard.yml --mp4 \
  --browser-arg --force-device-scale-factor=1
```

## RDF → YAML Conversion

To author storyboards in RDF Turtle and convert to YAML:

```bash
python3 scripts/ttl-to-yaml.py storyboard.ttl -o storyboard.yml
shot-scraper video storyboard.yml --mp4
```

## Post-Recording Log

To generate an RDF log of a completed recording:

```bash
python3 scripts/yaml-to-ttl.py storyboard.yml \
  -o /Users/kidehen/Movies/screencasts/2026-07-01-session.log.ttl
```
