#!/usr/bin/env python3
"""
Stop hook for the Agent RDF Memory Protocol's storage rule.

Registered in ~/.claude/settings.json under hooks.Stop. Receives:
  {session_id, transcript_path, cwd, hook_event_name, stop_hook_active}

It refuses to let the agent finish a turn (prints {"decision":"block","reason":...})
when the session has produced an artifact or changed memory and no session file has
been written since. See preferences.ttl Step 319 and
howto/session-retrieval-and-record-preflight.ttl.

What counts:
  * trigger  = a Write/Edit/NotebookEdit to a path that is not scratch (/tmp, /var/folders,
               a scratchpad dir) and is not agent-rdf-memory/sessions/*.ttl or index.ttl
  * recorded = a Write/Edit to agent-rdf-memory/sessions/*.ttl made AFTER the latest trigger,
               or a session file whose modification time is later than the latest trigger
               (so a record written from the shell counts too)
The check compares position in the transcript, so a second artifact built later in the same
session asks for the session file to be brought up to date again.

Then, whenever index.ttl or a session file was changed during the current turn, it runs
scripts/validate-memory-shapes.py --strict on just those files (memory-shapes.ttl, plus
index-shapes.ttl for index.ttl) and blocks with the violations listed: an index entry
outside any list, two entries of one list sharing a position, a missing position or item
link, an undated document entity. Files changed in earlier turns are not re-checked, so
an old problem elsewhere in the store never blocks an unrelated turn.

Fails OPEN: malformed input, no transcript, no agent-rdf-memory folder anywhere in play,
stop_hook_active (already blocked once on this stop), or any error all exit 0 without blocking.

Escape hatch: AGENT_SESSION_RECORD_GATE=off.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

MEMORY_DIR = 'agent-rdf-memory'
TEMP_PREFIXES = ('/tmp/', '/private/tmp/', '/var/folders/', '/private/var/folders/')
EDIT_TOOLS = ('Write', 'Edit', 'NotebookEdit', 'MultiEdit')
SESSION_RE = re.compile(r'agent-rdf-memory/sessions/[^/]+\.ttl$')
STORE = Path(__file__).resolve().parent.parent
VALIDATOR = STORE / 'scripts' / 'validate-memory-shapes.py'


def ts_epoch(value) -> float | None:
    try:
        return datetime.datetime.fromisoformat(str(value).replace('Z', '+00:00')).timestamp()
    except (TypeError, ValueError):
        return None


def shape_violations(turn_start: float | None) -> str | None:
    """Strict-validate index.ttl and session files changed during this turn.

    Returns a block reason, or None when they conform or the check cannot run.
    """
    if turn_start is None or not VALIDATOR.exists():
        return None
    files = []
    index = STORE / 'index.ttl'
    if index.exists() and index.stat().st_mtime >= turn_start:
        files.append(index)
    sessions = STORE / 'sessions'
    if sessions.is_dir():
        files += [f for f in sorted(sessions.glob('*.ttl')) if f.stat().st_mtime >= turn_start]
    if not files:
        return None
    try:
        run = subprocess.run([sys.executable, str(VALIDATOR), '--strict', '--details', *map(str, files)],
                             capture_output=True, text=True, timeout=180, cwd=str(STORE))
    except (OSError, subprocess.SubprocessError):
        return None
    if run.returncode != 1:
        return None  # conforms (0), or the validator itself failed: fail open
    details = [l.strip() for l in run.stdout.splitlines() if l.startswith('  ') and ' :: ' in l]
    shown = '; '.join(details[:8]) + (f' (and {len(details) - 8} more)' if len(details) > 8 else '')
    return (f'[memory-shapes] Memory files changed this turn do not conform to the store\'s SHACL shapes: '
            f'{shown}. Fix them, then re-run python3 scripts/validate-memory-shapes.py --strict --details '
            f'{" ".join(f.relative_to(STORE).as_posix() for f in files)}. Rule: howto/memory-shacl-validation.ttl. '
            f'Override: AGENT_SESSION_RECORD_GATE=off.')


def is_scratch(p: str) -> bool:
    return p.startswith(TEMP_PREFIXES) or '/scratchpad/' in p


def main() -> int:
    if os.environ.get('AGENT_SESSION_RECORD_GATE', '').lower() == 'off':
        return 0
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    if payload.get('stop_hook_active'):
        return 0

    tp = payload.get('transcript_path', '')
    p = Path(tp) if tp else None
    if p is None or not p.exists():
        return 0
    cwd = payload.get('cwd', '') or ''

    last_trigger = -1
    last_trigger_ts = None
    turn_start = None
    last_session = -1
    index_written = False
    # In play when the working directory holds agent-rdf-memory/ or sits inside it.
    memory_in_play = bool(cwd) and (Path(cwd, MEMORY_DIR).is_dir() or f'/{MEMORY_DIR}' in cwd + '/')
    seq = 0
    try:
        with p.open(encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if d.get('type') == 'user':
                    msg = d.get('message', {})
                    content = msg.get('content') if isinstance(msg, dict) else None
                    # A user turn starts with the user's own text, not with a tool result.
                    if isinstance(content, str) or (isinstance(content, list) and any(
                            isinstance(b, dict) and b.get('type') == 'text' for b in content)):
                        turn_start = ts_epoch(d.get('timestamp')) or turn_start
                    continue
                if d.get('type') != 'assistant':
                    continue
                msg = d.get('message', {})
                if not isinstance(msg, dict):
                    continue
                for block in msg.get('content', []) or []:
                    if not isinstance(block, dict) or block.get('type') != 'tool_use':
                        continue
                    if block.get('name') not in EDIT_TOOLS:
                        continue
                    inp = block.get('input') or {}
                    fp = inp.get('file_path') or inp.get('notebook_path') or ''
                    if not fp:
                        continue
                    seq += 1
                    if f'{MEMORY_DIR}/' in fp:
                        memory_in_play = True
                    if SESSION_RE.search(fp):
                        last_session = seq
                    elif fp.endswith(f'{MEMORY_DIR}/index.ttl'):
                        index_written = True
                    elif not is_scratch(fp):
                        last_trigger = seq
                        last_trigger_ts = ts_epoch(d.get('timestamp')) or last_trigger_ts
    except OSError:
        return 0

    if not memory_in_play:
        return 0

    recorded = last_trigger < 0 or last_session > last_trigger
    if not recorded and last_trigger_ts is not None and (STORE / 'sessions').is_dir():
        # A session file written from the shell after the latest trigger counts as a record.
        recorded = any(f.stat().st_mtime > last_trigger_ts for f in (STORE / 'sessions').glob('*.ttl'))
    if recorded:
        reason = shape_violations(turn_start)
        if reason:
            print(json.dumps({'decision': 'block', 'reason': reason}))
        return 0

    today = datetime.date.today().isoformat()
    parts = [
        f'[session-record] This session has produced files or changed memory, and no session file '
        f'has been written since. Before the final report, write '
        f'{MEMORY_DIR}/sessions/{today}-{{llm-id}}-{{agent-env}}.ttl in Turtle (the default; do not ask '
        f'which format), using the model id from the system prompt in the filename.',
    ]
    if not index_written:
        parts.append('Then add its entry to index.ttl.')
    parts.append(
        'Then parse-validate every .ttl you touched with rdflib and check that each relative link '
        'resolves. Rule: preferences.ttl Step 319. Override: AGENT_SESSION_RECORD_GATE=off.'
    )
    print(json.dumps({'decision': 'block', 'reason': ' '.join(parts)}))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 - a guard must never wedge the session
        sys.exit(0)
