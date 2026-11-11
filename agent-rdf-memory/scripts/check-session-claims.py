#!/usr/bin/env python3
"""
check-session-claims.py - compare the files a session record claims with the disk and the transcript.

A session record is an account written by the agent that ran the session. This is the first,
narrow, deterministic step toward the post's dreaming pass (check notes against transcripts):
it does not judge prose, it checks the one kind of claim a script can settle, namely
"this file exists" and "this file was written or edited in the session".

For every file path named in the record's literals it reports:

  OK             on disk, and the transcript shows it written, edited or named in a command
  NO-TRACE       on disk, but the transcript never mentions it (it may predate the session)
  NOT-ON-DISK    named in the record but not found: a claimed artifact that does not exist
  TRANSCRIPT-ONLY  not applicable here: use --written to list files the transcript wrote that
                 the record never names (work the record omits)

Report-only: it writes nothing and exits 0, or 1 with --strict when a path is NOT-ON-DISK.

Usage:
  python3 check-session-claims.py sessions/2026-11-11-claude_fable_5_2-claude_code.ttl
  python3 check-session-claims.py SESSION.ttl --transcript ~/.claude/projects/<project>/<id>.jsonl
  python3 check-session-claims.py SESSION.ttl --written     also list files the record omits
"""
import argparse
import glob
import json
import os
import pathlib
import re
import sys

import rdflib

STORE = pathlib.Path(__file__).resolve().parent.parent
REPO = STORE.parent
EXT = r"(?:py|ttl|md|html|sh|sql|json|jsonld|js|css|txt|csv)"
ABS = re.compile(r"/Users/[^\"'\n<>]*?\." + EXT + r"\b")
REL = re.compile(r"(?<![\w/.:-])((?:[\w.-]+/)+[\w.-]+\." + EXT + r")\b")
BARE = re.compile(r"(?<![\w/.:-])([\w-]+\." + EXT + r")\b")
ROOTS = [STORE, REPO, STORE / "scripts", STORE / "howto", STORE / "drafts", STORE / "sessions",
         STORE / "entities", pathlib.Path("/Users/kidehen/Documents/LLMs/Claude Generated")]


def default_transcript():
    base = pathlib.Path.home() / ".claude" / "projects"
    slug = str(REPO).replace("/", "-").replace(" ", "-")
    d = base / slug
    files = sorted(d.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True) if d.exists() else []
    return files[0] if files else None


def claimed_paths(session):
    g = rdflib.Graph()
    g.parse(str(session), format="turtle", publicID=pathlib.Path(session).resolve().as_uri())
    found = {}
    for o in g.objects():
        if not isinstance(o, rdflib.Literal):
            continue
        text = str(o)
        text_wo_urls = re.sub(r"https?://\S+", " ", text)
        for m in ABS.finditer(text_wo_urls):
            found.setdefault(m.group(0), "absolute")
        rest = ABS.sub(" ", text_wo_urls)
        for m in REL.finditer(rest):
            found.setdefault(m.group(1), "relative")
        rest = REL.sub(" ", rest)
        for m in BARE.finditer(rest):
            found.setdefault(m.group(1), "bare")
    return found


def resolve(path, kind):
    if kind == "absolute":
        return pathlib.Path(path) if os.path.exists(path) else None
    for root in ROOTS:
        cand = root / path
        if cand.exists():
            return cand
    if kind == "bare":
        for root in (STORE, REPO / "kg-generator", REPO / "rdf-infographic-skill",
                     pathlib.Path("/Users/kidehen/Documents/LLMs/Claude Generated/_build")):
            hits = glob.glob(str(root / "**" / path), recursive=True)
            if hits:
                return pathlib.Path(hits[0])
    return None


def transcript_evidence(path):
    written, commands = set(), []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                content = (rec.get("message") or {}).get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    inp = block.get("input") or {}
                    if block.get("name") in ("Write", "Edit", "NotebookEdit") and inp.get("file_path"):
                        written.add(inp["file_path"])
                    elif block.get("name") == "Bash" and inp.get("command"):
                        commands.append(inp["command"])
    except OSError as exc:
        sys.exit(f"cannot read transcript {path}: {exc}")
    return written, "\n".join(commands)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session")
    ap.add_argument("--transcript")
    ap.add_argument("--written", action="store_true")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    transcript = pathlib.Path(a.transcript).expanduser() if a.transcript else default_transcript()
    if not transcript or not transcript.exists():
        sys.exit("no transcript found: pass --transcript PATH")
    written, commands = transcript_evidence(transcript)
    claims = claimed_paths(a.session)
    rows = []
    for path, kind in sorted(claims.items()):
        found = resolve(path, kind)
        base = os.path.basename(path)
        traced = any(w.endswith(path) or os.path.basename(w) == base for w in written) or base in commands
        status = "NOT-ON-DISK" if found is None else ("OK" if traced else "NO-TRACE")
        rows.append((status, path))
    order = {"NOT-ON-DISK": 0, "NO-TRACE": 1, "OK": 2}
    print(f"session record: {a.session}\ntranscript:     {transcript}")
    print(f"{len(claims)} file paths named; transcript shows {len(written)} files written or edited\n")
    for status, path in sorted(rows, key=lambda r: (order[r[0]], r[1])):
        print(f"  {status:<12} {path}")
    summary = {s: sum(1 for r in rows if r[0] == s) for s in order}
    print("\n" + ", ".join(f"{n} {s}" for s, n in summary.items()))
    if a.written:
        named = {os.path.basename(p) for p in claims}
        omitted = sorted(w for w in written if os.path.basename(w) not in named
                         and "/scratchpad/" not in w and "/tmp/" not in w)
        print(f"\nfiles the transcript wrote or edited that the record does not name ({len(omitted)}):")
        for w in omitted:
            print("  " + w)
    if a.strict and summary["NOT-ON-DISK"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
