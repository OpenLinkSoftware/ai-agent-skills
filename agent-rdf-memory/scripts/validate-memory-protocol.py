#!/usr/bin/env python3
"""
Validate that a session transcript followed the mandatory Agent RDF Memory Protocol.

Reads a Claude Code JSONL session transcript and checks that all 5 protocol
steps were executed via explicit Read/Bash tool calls. This is a programmatic
backstop — the SessionStart hook injection is the primary prevention mechanism;
this validator is the audit trail that proves compliance.

Modeled on validate-harness-contract.py (rdf-infographic-skill step 35).
GATE: 0 failures required before considering a session protocol-compliant.

Usage:
  python3 validate-memory-protocol.py transcript.jsonl
  python3 validate-memory-protocol.py transcript.jsonl --verbose
  python3 validate-memory-protocol.py transcript.jsonl --strict
  python3 validate-memory-protocol.py transcript.jsonl --check-load-path --session-ttl sessions/2026-07-14-deepseek_v4pro-pi.ttl
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


MEMORY_DIR = 'agent-rdf-memory'

CORE_FILES = [
    ('core.ttl',         'Protocol step 2: Read core.ttl'),
    ('preferences.ttl',  'Protocol step 3: Read preferences.ttl'),
    ('index.ttl',        'Protocol step 4: Read index.ttl'),
]

# Subdirectories that qualify as "following references" per step 5
REF_SUBDIRS = ('howto/', 'sessions/', 'projects/', 'entities/')


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def extract_events(transcript_path: str) -> list[dict]:
    """
    Parse JSONL transcript and return a chronological event stream.

    Each event is a dict with:
      type: 'tool_use' | 'tool_result' | 'assistant_text' | 'user_text'
      For tool_use: + name, input, line_number
      For others: + line_number
    """
    events: list[dict] = []
    if not os.path.exists(transcript_path):
        return events

    with open(transcript_path, encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue

            record_type = d.get('type', '')

            if record_type == 'assistant':
                message = d.get('message', {})
                if not isinstance(message, dict):
                    continue
                content = message.get('content', [])
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    block_type = block.get('type', '')
                    if block_type == 'tool_use':
                        events.append({
                            'event_type': 'tool_use',
                            'name': block.get('name', ''),
                            'input': block.get('input', {}),
                            'line_number': line_num,
                        })
                    elif block_type == 'text':
                        text = block.get('text', '').strip()
                        if text:
                            events.append({
                                'event_type': 'assistant_text',
                                'text': text,
                                'line_number': line_num,
                            })

            elif record_type == 'user':
                message = d.get('message', {})
                if not isinstance(message, dict):
                    continue
                content = message.get('content', [])
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get('type') == 'text':
                        text = block.get('text', '').strip()
                        if text:
                            events.append({
                                'event_type': 'user_text',
                                'text': text,
                                'line_number': line_num,
                            })

    return events


def path_under_memory(file_path: str) -> str | None:
    """
    Return the relative path under agent-rdf-memory/ if the file is inside it.
    Returns None if the path does not reference agent-rdf-memory/.

    Handles both absolute paths (/.../agent-rdf-memory/foo.ttl) and
    relative paths (agent-rdf-memory/foo.ttl).
    """
    marker = f'{MEMORY_DIR}/'
    idx = file_path.find(marker)
    if idx == -1:
        marker_win = f'{MEMORY_DIR}\\'
        idx = file_path.find(marker_win)
    if idx == -1:
        # Path might be exactly agent-rdf-memory (e.g., a directory listing)
        return '' if file_path.rstrip('/').rstrip('\\').endswith(MEMORY_DIR) else None
    return file_path[idx + len(marker):]


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Validate Agent RDF Memory Protocol compliance from a session transcript'
    )
    parser.add_argument(
        'transcript',
        help='Path to Claude Code JSONL session transcript'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print all detected protocol-relevant tool calls'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Also verify protocol reads occurred before first substantive assistant response'
    )
    parser.add_argument(
        '--check-load-path',
        action='store_true',
        help='Also verify that the session TTL records onto:usedFileReads or onto:usedSparqlEndpoint'
    )
    parser.add_argument(
        '--session-ttl',
        default=None,
        help='Path to the session TTL file (required when --check-load-path is used)'
    )
    args = parser.parse_args()

    transcript_path = Path(args.transcript)
    if not transcript_path.exists():
        print(f'FAIL: transcript file not found: {args.transcript}')
        return 1

    events = extract_events(str(transcript_path))

    if args.verbose:
        print(f'Extracted {len(events)} events from transcript')

    failures: list[str] = []

    # ── Step 1: Directory listing ─────────────────────────────────────────────
    dir_listed = False
    for ev in events:
        if ev['event_type'] != 'tool_use':
            continue
        name = ev.get('name', '')
        inp = ev.get('input', {})
        if name == 'Bash':
            cmd = inp.get('command', '')
            if 'ls' in cmd and MEMORY_DIR in cmd:
                dir_listed = True
                if args.verbose:
                    snippet = cmd[:120].replace('\n', ' ')
                    print(f'  [PASS] Step 1 (line {ev["line_number"]}): ls {MEMORY_DIR}/ — {snippet}')
                break

    if not dir_listed:
        fail(
            f'Protocol step 1: Did not list {MEMORY_DIR}/ directory. '
            f'No Bash "ls" command targeting {MEMORY_DIR} found in transcript.',
            failures
        )

    # ── Steps 2-4: Read core memory files ─────────────────────────────────────
    read_files: set[str] = set()  # relative paths under agent-rdf-memory/
    read_line_numbers: dict[str, int] = {}  # file → first read line

    for ev in events:
        if ev['event_type'] != 'tool_use':
            continue
        if ev.get('name') != 'Read':
            continue
        fp = ev.get('input', {}).get('file_path', '')
        rel = path_under_memory(fp)
        if rel is not None and rel:  # non-empty = actual file under agent-rdf-memory/
            read_files.add(rel)
            if rel not in read_line_numbers:
                read_line_numbers[rel] = ev['line_number']

    for filename, label in CORE_FILES:
        # Match exact filename or as a path component ending with the filename
        found = filename in read_files or any(
            r == filename or r.endswith('/' + filename) or r.endswith('\\' + filename)
            for r in read_files
        )
        if found:
            if args.verbose:
                line = read_line_numbers.get(filename, '?')
                # Find the specific matching key
                matches = [r for r in read_files if r == filename or r.endswith('/' + filename)]
                matched = matches[0] if matches else filename
                line = read_line_numbers.get(matched, '?')
                print(f'  [PASS] {label} (line {line})')
        else:
            fail(label, failures)

    # ── Step 5: Follow references ─────────────────────────────────────────────
    # Read at least one file under agent-rdf-memory/ beyond the 3 core files.
    # Qualifying files: under howto/, sessions/, projects/, entities/, or
    # root-level .ttl files other than the core 3 (e.g., ontology.ttl).
    beyond_core: list[str] = []
    for rel in read_files:
        basename = rel.split('/')[-1].split('\\')[-1]
        if basename in {'core.ttl', 'preferences.ttl', 'index.ttl'}:
            continue
        if any(rel.startswith(subdir) for subdir in REF_SUBDIRS) or (
            rel.endswith('.ttl') and '/' not in rel and '\\' not in rel
        ):
            beyond_core.append(rel)

    if beyond_core:
        if args.verbose:
            for rel in beyond_core:
                line = read_line_numbers.get(rel, '?')
                print(f'  [PASS] Step 5 (line {line}): Followed reference → {MEMORY_DIR}/{rel}')
    else:
        fail(
            f'Protocol step 5: Did not follow index.ttl references. '
            f'No additional files under {MEMORY_DIR}/ read beyond core.ttl, preferences.ttl, index.ttl.',
            failures
        )

    # ── Strict mode: timing check ─────────────────────────────────────────────
    if args.check_load_path:
        if not args.session_ttl:
            print('FAIL: --session-ttl is required when --check-load-path is used')
            return 1
        session_ttl_path = Path(args.session_ttl)
        if not session_ttl_path.exists():
            print(f'FAIL: session TTL file not found: {args.session_ttl}')
            return 1
        try:
            from rdflib import Graph
            g = Graph()
            g.parse(str(session_ttl_path), format='turtle')
            # Look for onto:usedFileReads or onto:usedSparqlEndpoint
            ONTO = 'file://{}/ontology.ttl#'.format(
                str(Path(args.session_ttl).resolve().parent.parent)
            )
            has_file_reads = any(
                str(p).endswith('usedFileReads') for p in g.predicates()
            )
            has_sparql_endpoint = any(
                str(p).endswith('usedSparqlEndpoint') for p in g.predicates()
            )
            if has_file_reads or has_sparql_endpoint:
                if args.verbose:
                    method = 'file reads' if has_file_reads else 'SPARQL endpoint'
                    print(f'  [PASS] Load path recorded: {method}')
            else:
                fail(
                    'Load-path check: Session TTL does not record onto:usedFileReads '
                    'or onto:usedSparqlEndpoint. Every session file must declare its '
                    'memory load path per howto/session-governance.ttl Step 16.',
                    failures
                )
        except ImportError:
            print('WARNING: rdflib not installed — skipping load-path check')
        except Exception as e:
            fail(f'Load-path check: Failed to parse session TTL: {e}', failures)

    # ── Strict mode: timing check ─────────────────────────────────────────────
    if args.strict:
        # (not just a tool_result). This is the "first substantive response."
        # If no such text exists, skip strict check.
        #
        # Find the first user_text event (actual prompt, not tool_result)
        first_user_text_line = None
        for ev in events:
            if ev['event_type'] == 'user_text':
                first_user_text_line = ev['line_number']
                break

        if first_user_text_line:
            # Find the first assistant_text after this user prompt
            first_response_line = None
            for ev in events:
                if ev['event_type'] == 'assistant_text' and ev['line_number'] > first_user_text_line:
                    first_response_line = ev['line_number']
                    break

            if first_response_line:
                # Collect all protocol read line numbers
                protocol_read_lines: list[int] = []
                # Step 1 (dir list) — find the line
                for ev in events:
                    if ev['event_type'] != 'tool_use':
                        continue
                    if ev.get('name') == 'Bash':
                        cmd = ev.get('input', {}).get('command', '')
                        if 'ls' in cmd and MEMORY_DIR in cmd:
                            protocol_read_lines.append(ev['line_number'])
                            break
                # Steps 2-5 (Read calls)
                for ev in events:
                    if ev['event_type'] != 'tool_use':
                        continue
                    if ev.get('name') != 'Read':
                        continue
                    fp = ev.get('input', {}).get('file_path', '')
                    if path_under_memory(fp):
                        protocol_read_lines.append(ev['line_number'])

                if protocol_read_lines:
                    last_protocol_read = max(protocol_read_lines)
                    if last_protocol_read > first_response_line:
                        fail(
                            f'Strict mode: Last protocol read at line {last_protocol_read} '
                            f'occurred AFTER first substantive response at line {first_response_line}. '
                            f'Protocol steps must execute before responding to the user.',
                            failures
                        )
                    elif args.verbose:
                        print(f'  [STRICT] All protocol reads (last at line {last_protocol_read}) '
                              f'precede first substantive response (line {first_response_line})')
                elif args.verbose:
                    print('  [STRICT] No protocol reads found to check timing against')
            elif args.verbose:
                print('  [STRICT] No substantive assistant response found — skip timing check')
        elif args.verbose:
            print('  [STRICT] No user text prompt found — skip timing check')

    # ── Report ────────────────────────────────────────────────────────────────
    tool_use_count = sum(1 for ev in events if ev['event_type'] == 'tool_use')

    if failures:
        print(f'FAIL: {len(failures)} protocol step(s) not executed')
        for item in failures:
            print(f'  - {item}')
        if args.verbose:
            print(f'\nAudited {tool_use_count} tool calls across {len(events)} events in {transcript_path}')
        return 1

    print(f'PASS: Agent RDF Memory Protocol executed — all 5 steps verified ({tool_use_count} tool calls audited)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
