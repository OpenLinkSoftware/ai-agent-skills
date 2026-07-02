# Storyboard YAML Schema Reference

Full reference for `shot-scraper video` YAML storyboard format.
Source: https://shot-scraper.datasette.io/en/stable/video.html

## Top-Level Keys

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `output` | string | yes* | Output WebM filename. *Can be omitted if `-o` is used |
| `url` | string | conditional | Starting URL. Omit only if first scene has `open:` |
| `viewport` | mapping | no | Browser viewport `{width, height}`. Default: 1280x720 |
| `cursor` | bool/mapping | no | Show cursor dot and click rings. See cursor config below |
| `wait` | number | no | Seconds to pause after page loads, before scenes start |
| `wait_for` | string | no | Selector to wait for after page loads |
| `wait_for_url` | string | no | URL pattern to wait for (glob supported) |
| `javascript` | string | no | JS to run in page after initial load, before scenes |
| `sh` | string/list | no | Shell command to run before server starts |
| `python` | string | no | Python code to run before server starts |
| `server` | string/list | no | Command to run as server during recording |
| `scenes` | list | **yes** | Array of scene definitions |

### Viewport

```yaml
viewport:
  width: 1440
  height: 900
```

### Cursor

Simple mode — shows default orange cursor with click rings:

```yaml
cursor: true
```

Configured mode:

```yaml
cursor:
  visible: true
  clicks: true
  color: "#ff4f00"
  size: 18
  click_size: 44
```

## Scene Keys

| Key | Type | Description |
|-----|------|-------------|
| `name` | string | Optional label shown in progress messages |
| `open` | string | Navigate to URL at start of scene (relative URLs resolve) |
| `wait_for` | string | Selector to wait for before scene actions |
| `wait_for_url` | string | URL pattern to wait for |
| `sh` | string/list | Shell command before scene actions |
| `python` | string | Python code before scene actions |
| `do` | list | **Required** — list of actions to execute |

## Actions (inside `do:` list)

### click

```yaml
- click: "button#submit"
- click:
    selector: "button#submit"
    button: right
    count: 2
```

### type

Types text with optional per-keystroke delay:

```yaml
- type:
    into: "#search"
    text: "datasette"
    delay_ms: 50
```

`into:` and `selector:` are aliases.

### fill

Immediately fills a field with text:

```yaml
- fill:
    into: "#email"
    text: "demo@example.com"
```

### press

Presses a key (on focused element or specific selector):

```yaml
- press: Enter
- press:
    selector: "#search"
    key: Enter
```

### scroll

```yaml
- scroll: 800          # scroll down 800px
- scroll:
    y: 800
    duration: 1.2
- scroll:
    to: "#pricing"
    duration: 1
```

### pause

```yaml
- pause: 0.5
- pause: 2
```

### wait_for

```yaml
- wait_for: ".loaded"
- wait_for: "text=Search Results"
```

### wait_for_url

```yaml
- wait_for_url: "**/pricing"
```

### open

Navigate to URL during a scene (relative URLs resolve):

```yaml
- open: /pricing
- open: https://example.com/page
```

### screenshot

Capture a screenshot during recording:

```yaml
- screenshot: step-2.png
- screenshot:
    output: form.png
    selector: "#signup-form"
- screenshot:
    output: full-page.png
    full_page: true
```

### sh

Shell command during a scene:

```yaml
- sh: echo "Updated" > index.html
- sh:
  - touch
  - updated.html
```

### python

Python code during a scene:

```yaml
- python: |
    content = open("index.html").read()
    open("index.html", "w").write(content.upper())
```

### javascript / js

Run JS in the browser page context:

```yaml
- javascript: |
    document.querySelector("h1").style.outline = "4px solid red";
- js: window.scrollTo(0, 0)
```

## Complete Example

```yaml
output: demo.webm
url: https://example.com
viewport:
  width: 1280
  height: 720
cursor:
  visible: true
  clicks: true
  color: "#ff4f00"
wait_for: "text=Quick start"

scenes:
- name: Home page
  do:
  - pause: 1

- name: Search
  do:
  - click: "input.search"
  - type:
      into: "input.search"
      text: "test query"
      delay_ms: 25
  - press: Enter
  - wait_for: "text=Results"
  - pause: 2
```

## CLI Options

| Flag | Description |
|------|-------------|
| `-o, --output FILE` | Override output filename |
| `-a, --auth FILENAME` | Path to JSON auth context file |
| `--timeout INTEGER` | Wait timeout in ms |
| `-b, --browser [chromium\|firefox\|webkit\|chrome\|chrome-beta]` | Browser selection |
| `--browser-arg TEXT` | Additional browser arguments |
| `--user-agent TEXT` | Custom User-Agent |
| `--log-console` | Write console.log to stderr |
| `--fail` | Fail on HTTP errors |
| `--skip` | Skip pages with HTTP errors |
| `--bypass-csp` | Bypass Content Security Policy |
| `--silent` | Suppress progress messages |
| `--auth-username TEXT` | HTTP Basic auth username |
| `--auth-password TEXT` | HTTP Basic auth password |
| `--leave-server` | Keep server running after recording |
| `--mp4` | Also convert to MP4 via ffmpeg |
