"""
Fill core.ttl template placeholders with runtime values.

Reads agent-rdf-memory/core.ttl, substitutes {LLM_MODEL}, {AGENT_ENV_NAME},
and {OUTPUT_PATH} from CLI args or environment variables, and writes the
filled Turtle to stdout or a specified output file.

Usage:
    # CLI with explicit args
    python fill_core_template.py \
        --model "DeepSeek V4 Pro" \
        --env "Claude Code" \
        --output-root "/Users/kidehen/Documents/LLMs/DeepSeek/"

    # CLI with env vars
    LLM_MODEL="DeepSeek V4 Pro" AGENT_ENV="Claude Code" \
    OUTPUT_ROOT="/Users/kidehen/Documents/LLMs/DeepSeek/" \
    python fill_core_template.py

    # Write to file
    python fill_core_template.py --model "..." --env "..." --output-root "..." \
        --out /tmp/core-filled.ttl

    # Import as module
    from fill_core_template import fill
    filled = fill(model="DeepSeek V4 Pro", env="Claude Code",
                  output_root="/Users/kidehen/Documents/LLMs/DeepSeek/")
"""

import argparse
import os
import re
import sys
from pathlib import Path

# ── Resolve core.ttl location ─────────────────────────────────────────────────

def _find_core_ttl() -> Path:
    """Find core.ttl relative to this script (agent-rdf-memory/scripts/ → ../core.ttl)."""
    script_dir = Path(__file__).resolve().parent
    candidate = script_dir.parent / "core.ttl"
    if candidate.exists():
        return candidate
    # Fallback: search from cwd upward
    for parent in Path.cwd().parents:
        probe = parent / "agent-rdf-memory" / "core.ttl"
        if probe.exists():
            return probe
    raise FileNotFoundError(
        "Cannot locate agent-rdf-memory/core.ttl. "
        "Run from the repo root or set CORE_TTL_PATH."
    )


# ── Output root lookup (model → path mapping) ─────────────────────────────────

# Mirrors the output paths defined in core.ttl itself, plus additional entries.
_MODEL_OUTPUT_ROOTS: dict[str, str] = {
    "deepseek":         "/Users/kidehen/Documents/LLMs/DeepSeek/",
    "deepseek_v4pro":   "/Users/kidehen/Documents/LLMs/DeepSeek/",
    "claude":           "/Users/kidehen/Documents/LLMs/Claude Generated/",
    "claude_sonnet":    "/Users/kidehen/Documents/LLMs/Claude Generated/",
    "minimax":          "/Users/kidehen/Documents/LLMs/MiniMax Generated/",
    "kimi":             "/Users/kidehen/Documents/LLMs/kimi/",
    "kimi_k2":          "/Users/kidehen/Documents/LLMs/kimi/",
    "grok":             "/Users/kidehen/Documents/LLMs/Grok/",
    "gpt5":             "/Users/kidehen/Documents/LLMs/GPT5-Chat-Generated/",
    "gpt5_chat":        "/Users/kidehen/Documents/LLMs/GPT5-Chat-Generated/",
    "qwen":             "/Users/kidehen/Documents/LLMs/Alibaba Qwen/",
    "glm":              "/Users/kidehen/Documents/LLMs/glm/",
    "big_pickle":       "/Users/kidehen/Documents/LLMs/Big Pickle/",
}


# ── Fill function ─────────────────────────────────────────────────────────────

def fill(
    model: str,
    env: str,
    output_root: str | None = None,
    core_path: str | Path | None = None,
) -> str:
    """Return core.ttl content with all {PLACEHOLDER} values substituted.

    Parameters
    ----------
    model : str
        LLM model name for {LLM_MODEL} (e.g. "DeepSeek V4 Pro").
    env : str
        Agent environment name for {AGENT_ENV_NAME} (e.g. "Claude Code").
    output_root : str, optional
        Filesystem path for {OUTPUT_PATH}.  If omitted, derived from *model*
        using the built-in lookup table.  Falls back to the value in the
        template file if neither the table nor the argument provides one.
    core_path : str or Path, optional
        Path to core.ttl.  Auto-detected relative to this script when omitted.

    Returns
    -------
    str
        The filled Turtle document.
    """
    path = Path(core_path) if core_path else _find_core_ttl()
    text = path.read_text(encoding="utf-8")

    # Derive output root if not explicitly provided
    if output_root is None:
        model_key = model.lower().replace(" ", "_").replace("-", "_")
        output_root = _MODEL_OUTPUT_ROOTS.get(model_key)

    if output_root is None:
        # Last resort: extract the first schema:value from the template itself
        m = re.search(r'schema:value\s+"([^"]+)"', text)
        if m:
            output_root = m.group(1)

    subs: dict[str, str] = {
        "{LLM_MODEL}": model,
        "{AGENT_ENV_NAME}": env,
    }
    if output_root:
        subs["{OUTPUT_PATH}"] = output_root

    for placeholder, value in subs.items():
        text = text.replace(placeholder, value)

    return text


# ── CLI ───────────────────────────────────────────────────────────────────────

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Fill core.ttl template placeholders with runtime values."
    )
    parser.add_argument(
        "--model", "-m",
        default=os.environ.get("LLM_MODEL"),
        help="LLM model name for {LLM_MODEL} (env: LLM_MODEL)",
    )
    parser.add_argument(
        "--env", "-e",
        default=os.environ.get("AGENT_ENV"),
        help="Agent environment name for {AGENT_ENV_NAME} (env: AGENT_ENV)",
    )
    parser.add_argument(
        "--output-root", "-o",
        default=os.environ.get("OUTPUT_ROOT"),
        help="Filesystem path for {OUTPUT_PATH} (env: OUTPUT_ROOT). "
             "Auto-derived from --model when omitted.",
    )
    parser.add_argument(
        "--core-path", "-c",
        default=os.environ.get("CORE_TTL_PATH"),
        help="Path to core.ttl (auto-detected when omitted).",
    )
    parser.add_argument(
        "--out", "-O",
        help="Write filled Turtle to this file instead of stdout.",
    )
    args = parser.parse_args()

    if not args.model:
        parser.error("--model is required (or set LLM_MODEL env var)")
    if not args.env:
        parser.error("--env is required (or set AGENT_ENV env var)")

    result = fill(
        model=args.model,
        env=args.env,
        output_root=args.output_root,
        core_path=args.core_path,
    )

    if args.out:
        Path(args.out).write_text(result, encoding="utf-8")
        print(f"✓ Filled core.ttl written to {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(result)


if __name__ == "__main__":
    _cli()
