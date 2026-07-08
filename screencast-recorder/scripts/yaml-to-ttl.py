#!/usr/bin/env python3
"""Convert YAML storyboard → RDF Turtle log for agent-rdf-memory.

Usage:
  python3 yaml-to-ttl.py storyboard.yml -o session.log.ttl
  python3 yaml-to-ttl.py storyboard.yml                       # prints to stdout
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml",
          file=sys.stderr)
    sys.exit(1)

try:
    import rdflib
    from rdflib import URIRef, Literal, BNode, RDF, RDFS
    from rdflib.namespace import XSD
except ImportError:
    print("Error: rdflib is required. Install with: pip install rdflib",
          file=sys.stderr)
    sys.exit(1)

SC = rdflib.Namespace(
    "https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/"
    "screencast-recorder/ontology#"
)
SCHEMA = rdflib.Namespace("http://schema.org/")

# Map YAML action keys → RDF action classes
YAML_ACTION_MAP = {
    "click": SCHEMA.ClickAction,
    "fill": SCHEMA.WriteAction,
    "type": SCHEMA.WriteAction,
    "open": SCHEMA.NavigateAction,
    "press": SCHEMA.ActivateAction,
    "pause": SCHEMA.SuspendAction,
    "screenshot": SCHEMA.CreateAction,
    "scroll": SC.ScrollAction,
    "wait_for": SC.WaitForAction,
    "javascript": SC.JavascriptAction,
    "js": SC.JavascriptAction,
    "sh": SC.ShellCommand,
    "python": SC.PythonAction,
}


def make_bnode():
    return BNode()


def add_action(g, action_dict, doc_base):
    """Convert a YAML action dict to RDF triples, return the action node."""
    if not isinstance(action_dict, dict) or len(action_dict) != 1:
        return None

    action_key = list(action_dict.keys())[0]
    action_val = action_dict[action_key]

    action_cls = YAML_ACTION_MAP.get(action_key)
    if action_cls is None:
        return None

    node = make_bnode()
    g.add((node, RDF.type, action_cls))

    if action_key == "click":
        if isinstance(action_val, str):
            g.add((node, SC.selector, Literal(action_val)))
        elif isinstance(action_val, dict):
            selector = action_val.get("selector")
            if selector:
                g.add((node, SC.selector, Literal(selector)))
            button = action_val.get("button")
            if button:
                g.add((node, SC.clickButton, Literal(button)))
            count = action_val.get("count")
            if count:
                g.add((node, SC.clickCount, Literal(int(count))))

    elif action_key == "fill":
        if isinstance(action_val, dict):
            into = action_val.get("into") or action_val.get("selector")
            text = action_val.get("text")
            if into:
                g.add((node, SC.selector, Literal(into)))
            if text:
                g.add((node, SC.actionText, Literal(text, lang="en")))

    elif action_key == "type":
        if isinstance(action_val, dict):
            into = action_val.get("into") or action_val.get("selector")
            text = action_val.get("text")
            delay = action_val.get("delay_ms")
            if into:
                g.add((node, SC.selector, Literal(into)))
            if text:
                g.add((node, SC.actionText, Literal(text, lang="en")))
            if delay is not None:
                g.add((node, SC.delayMs, Literal(int(delay))))

    elif action_key == "open":
        if isinstance(action_val, str):
            g.add((node, SC.selector, Literal(action_val)))

    elif action_key == "press":
        if isinstance(action_val, str):
            g.add((node, SC.pressKey, Literal(action_val)))
        elif isinstance(action_val, dict):
            selector = action_val.get("selector")
            key = action_val.get("key")
            if selector:
                g.add((node, SC.selector, Literal(selector)))
            if key:
                g.add((node, SC.pressKey, Literal(key)))

    elif action_key == "pause":
        duration = float(action_val) if action_val is not None else 1.0
        g.add((node, SC.pauseDuration, Literal(duration)))

    elif action_key == "screenshot":
        if isinstance(action_val, str):
            g.add((node, SC.screenshotOutput, Literal(action_val)))
        elif isinstance(action_val, dict):
            output = action_val.get("output")
            if output:
                g.add((node, SC.screenshotOutput, Literal(output)))
            selector = action_val.get("selector")
            if selector:
                g.add((node, SC.selector, Literal(selector)))
            full_page = action_val.get("full_page")
            if full_page is not None:
                g.add((node, SC.fullPage,
                       Literal(str(full_page).lower() == "true")))

    elif action_key == "scroll":
        if isinstance(action_val, (int, float)):
            g.add((node, SC.scrollY, Literal(int(action_val))))
        elif isinstance(action_val, dict):
            x = action_val.get("x")
            y = action_val.get("y")
            to_val = action_val.get("to")
            dur = action_val.get("duration")
            if x is not None:
                g.add((node, SC.scrollX, Literal(int(x))))
            if y is not None:
                g.add((node, SC.scrollY, Literal(int(y))))
            if to_val:
                g.add((node, SC.scrollToTarget, Literal(to_val)))
            if dur is not None:
                g.add((node, SC.smoothDuration, Literal(float(dur))))

    elif action_key == "wait_for":
        if isinstance(action_val, str):
            g.add((node, SC.selector, Literal(action_val)))

    elif action_key in ("javascript", "js"):
        if isinstance(action_val, str):
            g.add((node, SC.actionText, Literal(action_val, lang="en")))

    elif action_key == "sh":
        if isinstance(action_val, str):
            g.add((node, SC.actionText, Literal(action_val, lang="en")))

    elif action_key == "python":
        if isinstance(action_val, str):
            g.add((node, SC.actionText, Literal(action_val, lang="en")))

    return node


def convert_storyboard(g, data, doc_base):
    """Convert parsed YAML storyboard to RDF triples. Returns the HowTo node."""
    howto = BNode()
    g.add((howto, RDF.type, SCHEMA.HowTo))

    # Name
    g.add((howto, SCHEMA.name, Literal("Screencast Recording", lang="en")))

    # Output video
    output = data.get("output")
    if output:
        video = BNode()
        g.add((video, RDF.type, SCHEMA.VideoObject))
        g.add((video, SCHEMA.name, Literal(str(Path(output).name))))
        g.add((video, SC.recordedWith, Literal("shot-scraper video")))
        g.add((video, SC.outputPath, Literal(str(output))))
        g.add((howto, SCHEMA.result, video))

    # URL
    url = data.get("url")
    if url:
        g.add((howto, SCHEMA.url, URIRef(url)))

    # Viewport
    vp = data.get("viewport", {})
    if vp.get("width"):
        g.add((howto, SC.viewportWidth, Literal(int(vp["width"]))))
    if vp.get("height"):
        g.add((howto, SC.viewportHeight, Literal(int(vp["height"]))))

    # Cursor
    cursor = data.get("cursor")
    if isinstance(cursor, bool) and cursor:
        g.add((howto, SC.cursorVisible, Literal(True)))
        g.add((howto, SC.cursorClicks, Literal(True)))
    elif isinstance(cursor, dict):
        if "visible" in cursor:
            g.add((howto, SC.cursorVisible, Literal(bool(cursor["visible"]))))
        if "clicks" in cursor:
            g.add((howto, SC.cursorClicks, Literal(bool(cursor["clicks"]))))
        if "color" in cursor:
            g.add((howto, SC.cursorColor, Literal(str(cursor["color"]))))
        if "size" in cursor:
            g.add((howto, SC.cursorSize, Literal(int(cursor["size"]))))
        if "click_size" in cursor:
            g.add((howto, SC.cursorClickSize,
                   Literal(int(cursor["click_size"]))))

    # Wait
    wait = data.get("wait")
    if wait is not None:
        g.add((howto, SCHEMA.performTime, Literal(float(wait))))

    # Wait for selector
    wait_for = data.get("wait_for")
    if wait_for:
        g.add((howto, SC.waitForSelector, Literal(str(wait_for))))

    # Wait for URL
    wait_for_url = data.get("wait_for_url")
    if wait_for_url:
        g.add((howto, SC.waitForUrlPattern, Literal(str(wait_for_url))))

    # JavaScript
    js = data.get("javascript")
    if js:
        g.add((howto, SC.javascriptCode, Literal(str(js), lang="en")))

    # Shell
    sh_cmd = data.get("sh")
    if sh_cmd:
        g.add((howto, SC.shellCommand, Literal(str(sh_cmd), lang="en")))

    # Python
    py_code = data.get("python")
    if py_code:
        g.add((howto, SC.pythonCode, Literal(str(py_code), lang="en")))

    # Server
    server = data.get("server")
    if server:
        if isinstance(server, list):
            g.add((howto, SC.serverCommand,
                   Literal(" ".join(str(s) for s in server))))
        else:
            g.add((howto, SC.serverCommand, Literal(str(server))))

    # Scenes
    scenes = data.get("scenes", [])
    for idx, scene_data in enumerate(scenes, start=1):
        scene = BNode()
        g.add((scene, RDF.type, SCHEMA.HowToStep))
        g.add((scene, SCHEMA.position, Literal(int(idx))))
        g.add((howto, SCHEMA.step, scene))

        # Scene name
        name = scene_data.get("name")
        if name:
            g.add((scene, SCHEMA.name, Literal(name, lang="en")))

        # Scene URL
        scene_url = scene_data.get("open")
        if scene_url:
            g.add((scene, SCHEMA.url, URIRef(scene_url)))

        # Scene wait_for
        scene_wait = scene_data.get("wait_for")
        if scene_wait:
            g.add((scene, SC.waitForSelector, Literal(scene_wait)))

        # Scene sh
        scene_sh = scene_data.get("sh")
        if scene_sh:
            g.add((scene, SC.shellCommand, Literal(scene_sh, lang="en")))

        # Scene python
        scene_py = scene_data.get("python")
        if scene_py:
            g.add((scene, SC.pythonCode, Literal(scene_py, lang="en")))

        # Actions
        actions = scene_data.get("do", [])
        for act_idx, act_data in enumerate(actions, start=1):
            action_node = add_action(g, act_data, doc_base)
            if action_node is not None:
                g.add((scene, SCHEMA.direction, action_node))
                g.add((action_node, SCHEMA.position, Literal(int(act_idx))))

    return howto


def main():
    parser = argparse.ArgumentParser(
        description="Convert YAML storyboard → RDF Turtle log"
    )
    parser.add_argument("input", help="Input .yml file")
    parser.add_argument("-o", "--output", help="Output .ttl file (default: stdout)")
    args = parser.parse_args()

    try:
        data = yaml.safe_load(Path(args.input).read_text())
    except Exception as e:
        print(f"Error reading {args.input}: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict):
        print(f"Invalid storyboard: expected a YAML mapping", file=sys.stderr)
        sys.exit(1)

    now = datetime.now(timezone.utc)

    g = rdflib.Graph()
    g.bind("schema", SCHEMA)
    g.bind("sc", SC)

    # Document entity
    doc_uri = URIRef("")
    g.add((doc_uri, RDF.type, SCHEMA.CreativeWork))
    g.add((doc_uri, SCHEMA.name,
           Literal(f"Screencast Log: {Path(args.input).name}", lang="en")))
    g.add((doc_uri, SCHEMA.dateCreated,
           Literal(now.strftime("%Y-%m-%dT%H:%M:%SZ"), datatype=XSD.dateTime)))
    g.add((doc_uri, SCHEMA.dateModified,
           Literal(now.strftime("%Y-%m-%dT%H:%M:%SZ"), datatype=XSD.dateTime)))

    # Convert
    howto = convert_storyboard(g, data, doc_uri)
    g.add((doc_uri, SCHEMA.about, howto))

    output = g.serialize(format="turtle", base=None)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
