#!/usr/bin/env python3
"""Convert RDF Turtle storyboard → YAML storyboard for shot-scraper video.

Usage:
  python3 ttl-to-yaml.py storyboard.ttl -o storyboard.yml
  python3 ttl-to-yaml.py storyboard.ttl                       # prints to stdout
"""

import argparse
import sys
from pathlib import Path

try:
    import rdflib
    from rdflib import URIRef, Literal, BNode, RDF, RDFS
except ImportError:
    print("Error: rdflib is required. Install with: pip install rdflib",
          file=sys.stderr)
    sys.exit(1)

SC = rdflib.Namespace(
    "https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/"
    "screencast-recorder/ontology#"
)
SCHEMA = rdflib.Namespace("http://schema.org/")

# Map RDF action classes → YAML action keys
ACTION_TYPE_MAP = {
    SCHEMA.ClickAction: "click",
    SCHEMA.WriteAction: "fill",
    SCHEMA.NavigateAction: "open",
    SCHEMA.ActivateAction: "press",
    SCHEMA.SuspendAction: "pause",
    SCHEMA.CreateAction: "screenshot",
    SC.ScrollAction: "scroll",
    SC.WaitForAction: "wait_for",
    SC.JavascriptAction: "javascript",
    SC.ShellCommand: "sh",
    SC.PythonAction: "python",
}

# Inverse: short names to help with inline type declarations
SHORT_TYPE_TO_ACTION = {
    "ClickAction": "click",
    "WriteAction": "fill",
    "NavigateAction": "open",
    "ActivateAction": "press",
    "SuspendAction": "pause",
    "CreateAction": "screenshot",
    "ScrollAction": "scroll",
    "WaitForAction": "wait_for",
    "JavascriptAction": "javascript",
    "ShellCommand": "sh",
    "PythonAction": "python",
}


def resolve_action_type(g, node):
    """Determine the YAML action key from an action node's RDF types."""
    for rdf_type in g.objects(node, RDF.type):
        uri = str(rdf_type)
        # Check full URI
        if rdf_type in ACTION_TYPE_MAP:
            return ACTION_TYPE_MAP[rdf_type]
        # Check short name
        short = uri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]
        if short in SHORT_TYPE_TO_ACTION:
            return SHORT_TYPE_TO_ACTION[short]
        # Check schema: URI pattern
        if uri.startswith("http://schema.org/"):
            short = uri.rsplit("/", 1)[-1]
            if short in SHORT_TYPE_TO_ACTION:
                return SHORT_TYPE_TO_ACTION[short]
    return None


def get_selector(g, node):
    """Resolve selector from various property names."""
    for prop in (SC.selector, SCHEMA.target, SCHEMA.url):
        val = g.value(node, prop)
        if val is not None:
            return str(val)
    return None


def get_text(g, node):
    """Resolve text content."""
    for prop in (SC.actionText, SCHEMA.name, SCHEMA.description):
        val = g.value(node, prop)
        if val is not None:
            return str(val)
    return None


def convert_action(g, node):
    """Convert an action RDF node to a YAML action dict."""
    action_type = resolve_action_type(g, node)
    if action_type is None:
        return None

    if action_type == "click":
        selector = get_selector(g, node)
        if selector:
            button = g.value(node, SC.clickButton)
            count = g.value(node, SC.clickCount)
            if button is not None or count is not None:
                entry = {"click": {"selector": selector}}
                if button is not None:
                    entry["click"]["button"] = str(button)
                if count is not None:
                    entry["click"]["count"] = int(count)
                return entry
            return {"click": selector}
        return None

    if action_type == "fill":
        selector = get_selector(g, node)
        text = get_text(g, node)
        if selector and text:
            delay = g.value(node, SC.delayMs)
            if delay is not None:
                return {
                    "type": {
                        "into": selector,
                        "text": text,
                        "delay_ms": int(delay),
                    }
                }
            return {"fill": {"into": selector, "text": text}}
        return None

    if action_type == "open":
        url = get_selector(g, node) or get_text(g, node)
        if url:
            return {"open": url}
        return None

    if action_type == "press":
        key = g.value(node, SC.pressKey)
        if key:
            selector = get_selector(g, node)
            if selector:
                return {"press": {"selector": selector, "key": str(key)}}
            return {"press": str(key)}
        return None

    if action_type == "pause":
        dur = g.value(node, SC.pauseDuration)
        if dur is not None:
            return {"pause": float(dur)}
        return {"pause": 1.0}

    if action_type == "screenshot":
        output = g.value(node, SC.screenshotOutput)
        selector = get_selector(g, node)
        full_page = g.value(node, SC.fullPage)
        if output:
            if selector or full_page is not None:
                entry = {"screenshot": {"output": str(output)}}
                if selector:
                    entry["screenshot"]["selector"] = str(selector)
                if full_page is not None:
                    entry["screenshot"]["full_page"] = (
                        str(full_page).lower() == "true"
                    )
                return entry
            return {"screenshot": str(output)}
        return None

    if action_type == "scroll":
        x = g.value(node, SC.scrollX)
        y = g.value(node, SC.scrollY)
        target = g.value(node, SC.scrollToTarget)
        dur = g.value(node, SC.smoothDuration)
        if target:
            entry = {"scroll": {"to": str(target)}}
            if dur is not None:
                entry["scroll"]["duration"] = float(dur)
            return entry
        if y is not None:
            entry = {"scroll": {"y": int(y)}}
            if x is not None:
                entry["scroll"]["x"] = int(x)
            if dur is not None:
                entry["scroll"]["duration"] = float(dur)
            return entry
        if x is not None:
            return {"scroll": int(x)}
        return None

    if action_type in ("wait_for",):
        selector = get_selector(g, node)
        if selector:
            return {"wait_for": str(selector)}
        return None

    if action_type in ("javascript", "js"):
        code = get_text(g, node)
        if code:
            return {"javascript": str(code)}
        return None

    if action_type == "sh":
        cmd = get_text(g, node)
        if cmd:
            return {"sh": str(cmd)}
        return None

    if action_type == "python":
        code = get_text(g, node)
        if code:
            return {"python": str(code)}
        return None

    return None


def convert_scene(g, scene_node):
    """Convert a schema:HowToStep to a YAML scene dict."""
    scene = {}
    name = g.value(scene_node, SCHEMA.name)
    if name:
        scene["name"] = str(name)

    url = g.value(scene_node, SCHEMA.url)
    if url:
        scene["open"] = str(url)

    wait_for_val = g.value(scene_node, SC.waitForSelector)
    if wait_for_val:
        scene["wait_for"] = str(wait_for_val)

    wait_for_url = g.value(scene_node, SC.waitForUrlPattern)
    if wait_for_url:
        scene["wait_for_url"] = str(wait_for_url)

    sh_val = g.value(scene_node, SC.shellCommand)
    if sh_val:
        scene["sh"] = str(sh_val)

    python_val = g.value(scene_node, SC.pythonCode)
    if python_val:
        scene["python"] = str(python_val)

    # Extract actions from schema:direction or schema:potentialAction
    actions = []
    for pred in (SCHEMA.direction, SCHEMA.potentialAction):
        for action_node in g.objects(scene_node, pred):
            action = convert_action(g, action_node)
            if action:
                actions.append(action)

    if actions:
        scene["do"] = actions

    return scene


def convert_storyboard(g, howto_node):
    """Convert a schema:HowTo node to a YAML storyboard dict."""
    sb = {}

    # Output video
    result = g.value(howto_node, SCHEMA.result)
    if result:
        # Prefer full path, fallback to name
        out_path = g.value(result, SC.outputPath)
        if out_path is not None:
            sb["output"] = str(out_path)
        else:
            name = g.value(result, SCHEMA.name)
            if name:
                sb["output"] = str(name)

    # URL
    url = g.value(howto_node, SCHEMA.url)
    if url:
        sb["url"] = str(url)

    # Viewport
    vw = g.value(howto_node, SC.viewportWidth)
    vh = g.value(howto_node, SC.viewportHeight)
    if vw or vh:
        vp = {}
        if vw:
            vp["width"] = int(vw)
        if vh:
            vp["height"] = int(vh)
        if vp:
            sb["viewport"] = vp
    else:
        # Check if viewport is an embedded MediaObject
        viewport_obj = g.value(howto_node, SCHEMA.about)  # not quite right
        # Default: 1440x900
        sb["viewport"] = {"width": 1440, "height": 900}

    # Cursor
    cv = g.value(howto_node, SC.cursorVisible)
    cc = g.value(howto_node, SC.cursorClicks)
    ccol = g.value(howto_node, SC.cursorColor)
    csize = g.value(howto_node, SC.cursorSize)
    cclick = g.value(howto_node, SC.cursorClickSize)

    if cv is not None or cc is not None or ccol is not None:
        cursor = {}
        if cv is not None:
            cursor["visible"] = str(cv).lower() == "true"
        if cc is not None:
            cursor["clicks"] = str(cc).lower() == "true"
        if ccol is not None:
            cursor["color"] = str(ccol)
        if csize is not None:
            cursor["size"] = int(csize)
        if cclick is not None:
            cursor["click_size"] = int(cclick)
        if cursor:
            sb["cursor"] = cursor

    # Top-level wait / wait_for
    wait_val = g.value(howto_node, SCHEMA.performTime)
    if wait_val:
        sb["wait"] = float(wait_val)

    wait_for_sel = g.value(howto_node, SC.waitForSelector)
    if wait_for_sel:
        sb["wait_for"] = str(wait_for_sel)

    wait_for_url = g.value(howto_node, SC.waitForUrlPattern)
    if wait_for_url:
        sb["wait_for_url"] = str(wait_for_url)

    # JavaScript
    js = g.value(howto_node, SC.javascriptCode)
    if js:
        sb["javascript"] = str(js)

    # Shell / Python / Server
    sh_cmd = g.value(howto_node, SC.shellCommand)
    if sh_cmd:
        sb["sh"] = str(sh_cmd)

    py_code = g.value(howto_node, SC.pythonCode)
    if py_code:
        sb["python"] = str(py_code)

    server_cmd = g.value(howto_node, SC.serverCommand)
    if server_cmd:
        sb["server"] = str(server_cmd)

    # Scenes
    scenes = []
    # Collect by schema:step, order by schema:position
    steps = list(g.objects(howto_node, SCHEMA.step))
    if not steps:
        steps = list(g.objects(howto_node, SCHEMA.hasPart))

    # Sort by position
    def get_position(node):
        pos = g.value(node, SCHEMA.position)
        if pos is not None:
            try:
                return float(pos)
            except (ValueError, TypeError):
                pass
        return 999

    steps.sort(key=get_position)

    for step_node in steps:
        scene = convert_scene(g, step_node)
        if scene:
            scenes.append(scene)

    if scenes:
        sb["scenes"] = scenes

    return sb


def find_howto(g):
    """Find the primary schema:HowTo node in the graph."""
    howtos = list(g.subjects(RDF.type, SCHEMA.HowTo))
    if len(howtos) == 1:
        return howtos[0]
    if len(howtos) > 1:
        # Prefer one with scene steps
        for h in howtos:
            if list(g.objects(h, SCHEMA.step)):
                return h
        return howtos[0]
    # Fallback: look for any node with schema:step
    for s, p, o in g.triples((None, SCHEMA.step, None)):
        return s
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Convert RDF Turtle storyboard → YAML"
    )
    parser.add_argument("input", help="Input .ttl file")
    parser.add_argument("-o", "--output", help="Output .yml file (default: stdout)")
    args = parser.parse_args()

    g = rdflib.Graph()
    try:
        g.parse(args.input, format="turtle")
    except Exception as e:
        print(f"Error parsing {args.input}: {e}", file=sys.stderr)
        sys.exit(1)

    howto = find_howto(g)
    if howto is None:
        print("No schema:HowTo found in the input file.", file=sys.stderr)
        sys.exit(1)

    sb = convert_storyboard(g, howto)
    if not sb:
        print("Empty storyboard — nothing to convert.", file=sys.stderr)
        sys.exit(1)

    try:
        import yaml
    except ImportError:
        print("Error: PyYAML is required. Install with: pip install pyyaml",
              file=sys.stderr)
        sys.exit(1)

    output = yaml.dump(sb, default_flow_style=False, sort_keys=False,
                       allow_unicode=True, width=120)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
