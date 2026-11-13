#!/usr/bin/env python3
"""
jev-route-steps.py - shadow pass: ask TypeSafe Jev which topic each unrouted step belongs to.

preferences.ttl has steps attached to no topic howto. scripts/memory-maintenance.py suggests a
topic by trigger-phrase match. This script asks Jev (System One, preferences Step 306) the same
question as a typed Choice over the topic candidates, with a Score for how clearly one topic fits,
and sets the answers beside the phrase-match suggestion. It is REPORT-ONLY: it writes one JSON
file and prints a summary; it changes no memory file. Applying assignments is a separate,
reviewed step.

Contract (probed 2026-11-12 against https://api.typesafe.ai/v1/systemone):
  POST, Authorization: Bearer <key>, body {model, state, questions}
  choice question  {"type":"choice","criteria":{option: description}}
  score question   {"type":"score","criteria":[level 0, level 1, ...]}
  reply            answers.<q>.choice/confidence/probabilities, answers.<q>.score/legend

Privacy: the key is read from TYPESAFE_API_KEY (or a login shell) and is never printed or logged.
Each request carries only the step's position, name and the first 300 characters of its text,
with emails, home paths and Keychain commands redacted. A step whose name or text concerns
credentials is NOT sent; it is listed as withheld and classified locally.

Fails open: no key, a network error or an API error for a step is recorded and the run continues.

Usage:
  python3 jev-route-steps.py --limit 5          try five steps
  python3 jev-route-steps.py                    every unrouted step
  python3 jev-route-steps.py --out FILE.json    where to write the results
  python3 jev-route-steps.py --dry-run          show the first request body, send nothing
"""
import argparse
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

STORE = pathlib.Path(__file__).resolve().parent.parent
ENDPOINT = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
SENSITIVE = re.compile(r"keychain|password|passphrase|credential|secret|api[ _-]?key|token|p12|\.pem|webid-tls|bearer", re.I)
LEVELS = [
    "clearly belongs to one topic",
    "mostly one topic, with another plausible",
    "could equally belong to two or more topics",
]


def load_maintenance():
    spec = importlib.util.spec_from_file_location("memory_maintenance", STORE / "scripts" / "memory-maintenance.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def get_key():
    key = os.environ.get("TYPESAFE_API_KEY", "")
    if key:
        return key
    try:
        out = subprocess.run(["zsh", "-lic", 'printf %s "$TYPESAFE_API_KEY"'], capture_output=True, text=True, timeout=20)
        return out.stdout.strip().splitlines()[-1] if out.stdout.strip() else ""
    except Exception:
        return ""


def redact(text):
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[email]", text)
    text = re.sub(r"/Users/[^\s\"')]+", "~", text)
    text = re.sub(r"security\s+find-generic-password[^\n]*", "[keychain command]", text)
    return re.sub(r"\s+", " ", text).strip()


def topic_candidates(mm):
    g, _ = mm.load(STORE / "preferences.ttl")
    S = mm.SCHEMA
    crit = {}
    for t in g.subjects(mm.RDF.type, S.Thing):
        tid = str(t).rsplit("#", 1)[-1]
        if tid.startswith("topic-"):
            name = mm.literal(g, t, S.name)
            desc = mm.literal(g, t, S.description)
            crit[tid[len("topic-"):]] = (name + ": " + desc)[:240]
    crit["none"] = "Stands alone: fits none of the topics above."
    return crit


def call(key, state, criteria, timeout=40):
    body = {
        "model": MODEL,
        "state": state,
        "questions": {
            "topic": {"type": "choice", "criteria": criteria},
            "fit": {"type": "score", "criteria": LEVELS},
        },
    }
    req = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--only", help="comma-separated step ids to ask about, for example step-memoryShaclValidation")
    ap.add_argument("--out")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-confidence", type=float, default=0.8)
    a = ap.parse_args()
    mm = load_maintenance()
    _, steps = mm.collect_steps()
    by_id = {v["id"]: v for v in steps.values()}   # keyed by id: positions are not unique in the store
    rows = [r for r in mm.check_unrouted(steps)]
    if a.only:
        wanted = set(a.only.split(","))
        rows = [r for r in rows if r["id"] in wanted]
    if a.limit:
        rows = rows[: a.limit]
    criteria = topic_candidates(mm)
    key = "" if a.dry_run else get_key()
    if not a.dry_run and not key:
        sys.exit("TYPESAFE_API_KEY not available: set it, or run from a shell that has it. Nothing was sent.")
    results, usage, withheld = [], 0, 0
    for i, r in enumerate(rows, 1):
        step = by_id[r["id"]]
        entry = {"step": r["step"], "id": r["id"], "name": step["name"][:120], "phrase_match": r["suggested_topic"]}
        if SENSITIVE.search(step["name"] + " " + step["text"][:600]):
            entry["status"] = "withheld: concerns credentials; classify locally"
            withheld += 1
            results.append(entry)
            continue
        state = redact(f"Step {step['position']}: {step['name']}. {step['text'][:300]}")
        if a.dry_run:
            print(json.dumps({"state": state, "criteria": criteria}, indent=2)[:1800])
            return
        try:
            reply = call(key, state, criteria)
            ans = reply["answers"]["topic"]
            fit = reply["answers"]["fit"]
            entry.update({
                "status": "ok", "jev_topic": ans["choice"], "confidence": ans["confidence"],
                "top3": sorted(ans["probabilities"].items(), key=lambda kv: -kv[1])[:3],
                "fit": fit["score"], "fit_meaning": fit["legend"].get(str(int(fit["score"])), ""),
                "served_by": reply.get("model"),
            })
            usage += reply.get("usage", {}).get("input_tokens", 0) + reply.get("usage", {}).get("output_tokens", 0)
        except urllib.error.HTTPError as exc:
            entry["status"] = f"error: HTTP {exc.code}"
        except Exception as exc:
            entry["status"] = f"error: {str(exc)[:80]}"
        results.append(entry)
        if i % 20 == 0:
            print(f"  ... {i}/{len(rows)}", file=sys.stderr)
        time.sleep(0.15)
    ok = [e for e in results if e.get("status") == "ok"]
    agree = [e for e in ok if e["jev_topic"] == e["phrase_match"]]
    low = [e for e in ok if e["confidence"] < a.min_confidence]
    out = pathlib.Path(a.out) if a.out else pathlib.Path(os.environ.get("TMPDIR", "/tmp")) / "jev-route-steps.json"
    out.write_text(json.dumps({"model": MODEL, "criteria": list(criteria), "results": results}, indent=1), encoding="utf-8")
    print(f"steps asked: {len(rows)} | answered: {len(ok)} | withheld: {withheld} | errors: {len(results) - len(ok) - withheld}")
    print(f"Jev agrees with the phrase match on {len(agree)} of {len(ok)}; "
          f"{len(low)} answers below confidence {a.min_confidence}; tokens used: {usage}")
    counts = {}
    for e in ok:
        counts[e["jev_topic"]] = counts.get(e["jev_topic"], 0) + 1
    print("Jev's topics:", ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1])))
    print(f"results written to {out}")


if __name__ == "__main__":
    main()
