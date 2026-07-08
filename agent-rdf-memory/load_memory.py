#!/usr/bin/env python3
"""SessionStart hook: compact RDF memory loader with GATE enforcement.

Reads core.ttl, preferences.ttl step index (with inline schema:text excerpts),
index.ttl session names, the most recent session, and the critical whoami format
spec from howto/agent-identity.ttl.

Injects a prominent GATE instruction requiring full reads of the memory files
before ANY response — the compact injection is a safety net, not a replacement.

WHY THIS GATE EXISTS (do not remove):
  Compact injection of step names without content made prior sessions skip the
  full-read protocol — the agent thought memory was "already loaded." Step 23's
  whoami format spec (in howto/agent-identity.ttl) was never loaded by the hook,
  causing a protocol violation on a simple "whoami" query. The GATE instruction
  is the programmatic backstop that prevents this class of failure.
"""
import json, os, glob, re

BASE = os.environ.get(
    'AGENT_RDF_MEMORY',
    os.path.join(os.path.dirname(os.path.abspath(__file__)))
)
MAX_SESSION = 3072   # cap most-recent session at 3 KB

# ═══════════════════════════════════════════════════════════════════════════════
# GATE — textually unskippable, appears FIRST in injected context
# ═══════════════════════════════════════════════════════════════════════════════
ctx = (
    '╔══════════════════════════════════════════════════════════════════╗\n'
    '║  ⚠️  GATE — MUST EXECUTE BEFORE ANY RESPONSE  ⚠️              ║\n'
    '╠══════════════════════════════════════════════════════════════════╣\n'
    '║  This compact injection is a SAFETY NET, not a replacement.     ║\n'
    '║  You MUST still execute the full Agent RDF Memory Protocol:     ║\n'
    '║    (1) ls agent-rdf-memory/ and all subfolders                  ║\n'
    '║    (2) Read agent-rdf-memory/core.ttl                           ║\n'
    '║    (3) Read agent-rdf-memory/preferences.ttl                    ║\n'
    '║    (4) Read agent-rdf-memory/index.ttl                          ║\n'
    '║    (5) Follow index.ttl refs to relevant howto/*.ttl files      ║\n'
    '║  Compact injection = step NAMES + critical TEXT only.           ║\n'
    '║  howto/ files = FULL specification text. Do NOT skip them.     ║\n'
    '║  Skipping full reads = contract violation = repetitive failure. ║\n'
    '║  See step-memoryProtocol (pos 5) in preferences.ttl.           ║\n'
    '╚══════════════════════════════════════════════════════════════════╝\n\n'
    '=== AGENT RDF MEMORY (compact) ===\n\n'
    'WRITE RULE: All behavioral rules and preferences MUST be written to '
    'agent-rdf-memory/ as valid Turtle (new schema:HowToStep in preferences.ttl '
    '+ companion howto/<topic>.ttl). '
    'The flat markdown store at .claude/projects/.../memory/ is a SECONDARY INDEX '
    'only — never the primary or sole write target for behavioral rules.\n\n'
)

# ── 0. Whoami format spec — injected inline because this is the spec that was ──
#    missed when prior sessions skipped the full-read protocol. It lives in a
#    howto/ file that the compact injection never loaded, so the agent answered
#    from CLAUDE.md prose instead of the canonical format.
try:
    agent_id = open(os.path.join(BASE, 'howto/agent-identity.ttl')).read()
    m = re.search(
        r':step-whoamiFormat.*?schema:text\s+"""(.*?)"""\s*@en',
        agent_id, re.DOTALL
    )
    if m:
        ctx += (
            '--- CRITICAL: whoami format (howto/agent-identity.ttl) ---\n'
            + m.group(1).strip() + '\n\n'
        )
except Exception as e:
    ctx += f'ERROR howto/agent-identity.ttl: {e}\n\n'

# ── 1. core.ttl — user identity and output-path routing ──────────────────────
def strip_comments(text):
    """Remove Turtle comment lines and collapse consecutive blank lines."""
    out, prev_blank = [], False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith('#'):
            continue
        blank = s == ''
        if blank and prev_blank:
            continue
        out.append(line)
        prev_blank = blank
    return '\n'.join(out)

try:
    raw = open(os.path.join(BASE, 'core.ttl')).read()
    ctx += '--- core.ttl ---\n' + strip_comments(raw) + '\n'
except Exception as e:
    ctx += f'ERROR core.ttl: {e}\n'

# ── 2. preferences.ttl — step index with names, howto refs, and text excerpts ─
try:
    prefs = open(os.path.join(BASE, 'preferences.ttl')).read()

    # --- 2a. Step index: name + position + howto reference + step ID ---
    # Captures step-id for correlation with text_map (2b).
    steps = []
    for m in re.finditer(r':(step-\w+)\s+a\s+schema:HowToStep[^.]+\.', prefs, re.DOTALL):
        block   = m.group(0)
        step_id = m.group(1)
        pos     = re.search(r'schema:position\s+([\d.]+)', block)
        name    = re.search(r'schema:name\s+"([^"]+)"@en', block)
        seealso = re.search(r'rdfs:seeAlso\s+<([^>]+)>', block)
        if pos and name:
            steps.append((float(pos.group(1)), name.group(1),
                          seealso.group(1) if seealso else '', step_id))

    # --- 2b. schema:text excerpts (separate pass — handles triple-quoted strings) ---
    # Uses a tempered greedy token (?!:step-) to stay within one step block.
    text_map = {}  # step-id → first-line excerpt
    for m in re.finditer(
        r':(step-\w+)\s+a\s+schema:HowToStep\s*;'
        r'(?:(?!:step-).)*?'
        r'schema:text\s+("""|")(.*?)\2\s*@en',
        prefs, re.DOTALL
    ):
        step_id = m.group(1)
        full_text = m.group(3).strip()
        first_line = full_text.split('\n')[0].strip()
        if len(first_line) > 160:
            first_line = first_line[:157] + '…'
        text_map[step_id] = first_line

    ctx += '\n--- preferences.ttl (step index) ---\n'
    for _, name, ref, step_id in sorted(steps, key=lambda x: x[0]):
        line = f'  • {name}'
        if ref:
            line += f'  → {ref}'
        # Append text excerpt inline if available
        if step_id in text_map:
            line += f'\n    └ {text_map[step_id]}'
        ctx += line + '\n'

except Exception as e:
    ctx += f'ERROR preferences.ttl: {e}\n'

# ── 3. Last 3 session names from index.ttl ───────────────────────────────────
try:
    idx   = open(os.path.join(BASE, 'index.ttl')).read()
    names = re.findall(r'schema:name\s+"([^"]+)"@en', idx)
    ctx  += '\n--- index.ttl (last 3 sessions) ---\n'
    for n in names[-3:]:
        ctx += f'  {n}\n'
except Exception as e:
    ctx += f'ERROR index.ttl: {e}\n'

# ── 4. Most recent session .ttl, capped at 3 KB ──────────────────────────────
sessions = sorted(glob.glob(os.path.join(BASE, 'sessions', '*.ttl')))
if sessions:
    fname = os.path.basename(sessions[-1])
    try:
        content = open(sessions[-1]).read()
        if len(content) > MAX_SESSION:
            content = (content[:MAX_SESSION] +
                       f'\n... [truncated — full file: sessions/{fname}]\n')
        ctx += f'\n--- sessions/{fname} ---\n' + content
    except Exception as e:
        ctx += f'ERROR {fname}: {e}\n'

# ── Emit ─────────────────────────────────────────────────────────────────────
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'SessionStart',
        'additionalContext': ctx
    }
}))
