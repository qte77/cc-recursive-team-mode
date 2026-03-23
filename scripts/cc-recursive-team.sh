#!/usr/bin/env bash
# cc-recursive-team.sh — Recursive Claude Code subprocess invocation.
#
# Clears CLAUDECODE guard, optionally enables teams mode, and invokes
# claude -p with stream-json capture. Forwards the subprocess exit code.
#
# Usage:
#   scripts/cc-recursive-team.sh --prompt "your prompt" [OPTIONS]
#
# Options:
#   --prompt TEXT         Prompt for claude -p (required)
#   --timeout SECONDS     Wall-clock timeout (default: 300)
#   --max-turns N         --max-turns flag value (default: 20)
#   --teams               Enable CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
#   --output-format FMT   CC output format (default: stream-json)
#   --no-skip-permissions  Do NOT pass --dangerously-skip-permissions (default: on)

set -euo pipefail

PROMPT=""
TIMEOUT=300
MAX_TURNS=20
TEAMS=false
SKIP_PERMISSIONS=true
OUTPUT_FORMAT="stream-json"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prompt)       PROMPT="$2";        shift 2 ;;
        --timeout)      TIMEOUT="$2";       shift 2 ;;
        --max-turns)    MAX_TURNS="$2";     shift 2 ;;
        --teams)        TEAMS=true;         shift   ;;
        --output-format) OUTPUT_FORMAT="$2"; shift 2 ;;
        --no-skip-permissions) SKIP_PERMISSIONS=false; shift ;;
        *) echo "Unknown flag: $1" >&2; exit 1 ;;
    esac
done

if [[ -z "$PROMPT" ]]; then
    echo "Error: --prompt is required" >&2
    exit 1
fi

# Clear the CC nested-invocation guard
unset CLAUDECODE

if [[ "$TEAMS" == "true" ]]; then
    export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
fi

CMD=(timeout "$TIMEOUT" claude)
if [[ "$SKIP_PERMISSIONS" == "true" ]]; then
    CMD+=(--dangerously-skip-permissions)
fi
CMD+=(-p "$PROMPT" --output-format "$OUTPUT_FORMAT" --max-turns "$MAX_TURNS")

exec "${CMD[@]}"
