#!/usr/bin/env python3
"""
Live PreToolUse gate for the Agent RDF Memory Protocol.

Registered in ~/.claude/settings.json against the Read/Write/Edit matchers.
Receives the standard Claude Code PreToolUse payload on stdin:
  {session_id, transcript_path, cwd, hook_event_name, tool_name, tool_input}

Unlike validate-memory-protocol.py (a post-hoc auditor invoked with a
transcript path as argv[1]), this script runs live, once per matched tool
call, and must never hang or crash the tool call it's guarding -- a prior
version of this hook pointed at a filename that didn't exist on disk, which
caused every Read/Write/Edit in the session to fail outright. This version
is deliberately non-blocking: it always exits 0. Its only effect is an
advisory stderr note when the three core memory files have not yet been
read this session and the tool call in question is not itself part of
satisfying that gate.

Usage (invoked by the harness, not run manually):
  echo '<PreToolUse JSON>' | python3 check-memory-gate.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

MEMORY_DIR = 'agent-rdf-memory'
CORE_FILES = ('core.ttl', 'preferences.ttl', 'index.ttl')


def path_under_memory(file_path: str):
    """Relative path under agent-rdf-memory/, or None if not under it."""
    if not file_path:
        return None
    marker = f'{MEMORY_DIR}/'
    idx = file_path.find(marker)
    if idx == -1:
        marker_win = f'{MEMORY_DIR}\\'
        idx = file_path.find(marker_win)
    if idx == -1:
        return None
    return file_path[idx + len(marker):]


def core_files_already_read(transcript_path: str) -> bool:
    """Scan the transcript so far for prior Read tool_use calls of all three core files."""
    p = Path(transcript_path)
    if not p.exists():
        return False

    seen: set[str] = set()
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
                if d.get('type') != 'assistant':
                    continue
                message = d.get('message', {})
                if not isinstance(message, dict):
                    continue
                for block in message.get('content', []) or []:
                    if not isinstance(block, dict) or block.get('type') != 'tool_use':
                        continue
                    if block.get('name') != 'Read':
                        continue
                    fp = (block.get('input') or {}).get('file_path', '')
                    rel = path_under_memory(fp)
                    if rel:
                        for core in CORE_FILES:
                            if rel == core or rel.endswith(f'/{core}'):
                                seen.add(core)
    except OSError:
        return False

    return all(core in seen for core in CORE_FILES)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        # Malformed/empty stdin -- never let a parsing problem block the tool call.
        return 0

    tool_name = payload.get('tool_name', '')
    tool_input = payload.get('tool_input', {}) or {}
    transcript_path = payload.get('transcript_path', '')

    target_path = tool_input.get('file_path', '')

    # Reading/writing/editing anything under agent-rdf-memory/ is itself how the
    # protocol gets satisfied -- never gate on those.
    if path_under_memory(target_path) is not None:
        return 0

    if core_files_already_read(transcript_path):
        return 0

    print(
        f'[memory-gate] Advisory: {tool_name} on {target_path or "(no path)"} -- '
        f'the Agent RDF Memory Protocol core files ({", ".join(CORE_FILES)}) have not '
        f'all been read yet this session. Not blocking; consider reading them.',
        file=sys.stderr,
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
