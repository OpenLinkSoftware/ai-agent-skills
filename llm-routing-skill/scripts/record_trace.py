#!/usr/bin/env python3
"""record_trace.py — Record a session routing trace (private, local-only).

Appends an llmr:RoutingTrace block to references/traces/ per routed execution,
in line with the session-trace guidelines in agent-rdf-memory/preferences.ttl:

  - OUTCOME-LEVEL ONLY: task, tier, policy, model, quality score, latency,
    cost, escalation events. Verbatim prompts and message content are NEVER
    recorded here (Step 36 secret redaction; traces stay private).
  - SESSION LINKAGE: each trace links via prov:wasInformedBy to the
    opal:ChatSession it came from (Step 25 intent-to-outcome traceability;
    Step 38 OPAL vocabulary).
  - PRIVATE BY DESIGN: traces are written to the LOCAL traces file only and
    are never part of the published routing-graph.ttl or any public upload.

Traces are harvested by scripts/harvest_traces.py to refine seed capability
profiles and rebuild the graph — the automatic feedback loop.

Usage:
  python3 scripts/record_trace.py code-generation deepseek-v4-flash \\
      --tier medium --policy balanced --score 4 --latency low --cost 0.028 \\
      --session https://.../sessions/2026-08-19-deepseek_v4flash-dsh-2.ttl#this \\
      --escalation deepseek-v4-flash --escalation codestral-latest
  python3 scripts/record_trace.py --dry-run ...   # print, don't append
  python3 scripts/record_trace.py --list          # show recorded traces

Exit codes: 0 appended; 1 usage/validation error.
"""
import argparse
import os
import re
import sys
from datetime import date, datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
TRACES = os.path.join(SKILL, "references", "traces")
TRACE_LOG = os.path.join(TRACES, "trace-log.ttl")

NS = {
    "llmr": "https://www.openlinksw.com/ontology/llm-routing#",
    "llmrm": "https://www.openlinksw.com/ontology/llm-routing/models/",
    "llmrt": "https://www.openlinksw.com/ontology/llm-routing/tasks/",
    "prov": "http://www.w3.org/ns/prov#",
    "schema": "http://schema.org/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
}

VALID_TIERS = ("low", "medium", "high", "max")
VALID_POLICIES = ("cost-first", "balanced", "quality-first", "latency-first")
VALID_LATENCY = ("very-low", "low", "medium", "high", "very-high")
SEQUENCE = 0  # incremented per append (see _next_seq)


def _esc(text):
    return str(text).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _next_seq():
    """Next trace sequence number based on existing trace-log content."""
    if not os.path.exists(TRACE_LOG):
        return 1
    txt = open(TRACE_LOG).read()
    nums = [int(m) for m in re.findall(r"#trace-(\d+)", txt)]
    return (max(nums) + 1) if nums else 1


def _prefix_preamble():
    return "\n".join(f"@prefix {p}: <{u}> ." for p, u in NS.items()) + "\n\n"


def build_trace(task, model, tier, policy, score, latency, cost,
                session_iri, escalation, date_iso, seq):
    mid = re.sub(r"[^A-Za-z0-9_.-]", "_", model)
    tid = re.sub(r"[^A-Za-z0-9_.-]", "_", task)
    # full <IRI> syntax for the trace subject — '#' is not legal in a
    # prefixed-name local part (same rule as the graph's reification nodes)
    trace_iri = f"<https://www.openlinksw.com/ontology/llm-routing/traces#trace-{seq}>"
    L = []
    A = L.append
    A(f"{trace_iri} a llmr:RoutingTrace, llmr:FeedbackRecord ;")
    A(f"    llmr:tracedTask llmrt:{tid} ;")
    A(f"    llmr:tracedModel llmrm:{mid} ;")
    A(f'    llmr:costTierUsed "{tier}"@en ;')
    A(f'    llmr:policyUsed "{policy}"@en ;')
    A(f'    llmr:qualityScore "{score}"^^xsd:integer ;')
    A(f'    llmr:observedLatency "{latency}"@en ;')
    if cost is not None:
        A(f'    llmr:costIncurred "{cost}"^^xsd:decimal ;')
    A(f'    llmr:feedbackDate "{date_iso}"^^xsd:date ;')
    if session_iri:
        A(f"    prov:wasInformedBy <{session_iri}> ;")
    if escalation:
        A("    llmr:escalationEvent " +
          " , ".join(f'"{_esc(e)}"@en' for e in escalation) + " ;")
    # strip trailing ' ;' and close
    body = "\n".join(A_line for A_line in L)
    body = body.rstrip(" ;") + " .\n"
    return body


def main():
    global SEQUENCE
    ap = argparse.ArgumentParser(description="Record a session routing trace (private, local-only)")
    ap.add_argument("task", nargs="?", help="task type id (e.g. code-generation)")
    ap.add_argument("model", nargs="?", help="model id (e.g. deepseek-v4-flash)")
    ap.add_argument("--tier", default="medium", choices=VALID_TIERS)
    ap.add_argument("--policy", default="balanced", choices=VALID_POLICIES)
    ap.add_argument("--score", type=int, required=True, help="quality score 1-5")
    ap.add_argument("--latency", default="low", choices=VALID_LATENCY)
    ap.add_argument("--cost", type=float, help="USD cost of the execution")
    ap.add_argument("--session", help="opal:ChatSession IRI this trace was informed by")
    ap.add_argument("--escalation", action="append", help="escalation event (repeatable, in order)")
    ap.add_argument("--date", default=date.today().isoformat(), help="ISO date (default today)")
    ap.add_argument("--dry-run", action="store_true", help="print the trace block, don't append")
    ap.add_argument("--list", action="store_true", help="show recorded traces")
    args = ap.parse_args()

    if args.list:
        if not os.path.exists(TRACE_LOG):
            print("no traces recorded yet")
            return 0
        print(open(TRACE_LOG).read())
        return 0

    if not args.task or not args.model:
        ap.error("task and model required (or use --list)")

    seq = _next_seq()
    block = build_trace(args.task, args.model, args.tier, args.policy,
                        args.score, args.latency, args.cost, args.session,
                        args.escalation, args.date, seq)

    if args.dry_run:
        print(_prefix_preamble() + block)
        return 0

    os.makedirs(TRACES, exist_ok=True)
    if not os.path.exists(TRACE_LOG):
        with open(TRACE_LOG, "w") as fh:
            fh.write("# LLM Routing Trace Log — PRIVATE. Outcome-level records of\n")
            fh.write("# routed executions. Never uploaded to public surfaces; never\n")
            fh.write("# contains prompts, message content, or secrets (preferences.ttl Step 36).\n\n")
            fh.write(_prefix_preamble())
            fh.write("<> a schema:CreativeWork ;\n")
            fh.write('    schema:name "LLM Routing Trace Log (private)"@en ;\n')
            fh.write('    schema:about <https://www.openlinksw.com/ontology/llm-routing/traces> .\n\n')
    with open(TRACE_LOG, "a") as fh:
        fh.write(block + "\n")
    print(f"trace #{seq} recorded: {args.task} -> {args.model} "
          f"(tier={args.tier}, policy={args.policy}, score={args.score}, "
          f"latency={args.latency}, cost={args.cost})")
    print(f"log: {TRACE_LOG}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
