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
#   --max-depth N         Deepest recursive spawn allowed (default: $CC_MAX_DEPTH or 2)
#
# Spawn-depth guard: the child gets CC_RECURSIVE_DEPTH = this process's depth + 1 (absent = 0,
# the same variable the Python runner uses). A spawn past the max depth, or a malformed depth,
# exits 3 without starting claude.

set -euo pipefail

PROMPT=""
TIMEOUT=300
MAX_TURNS=20
TEAMS=false
SKIP_PERMISSIONS=true
OUTPUT_FORMAT="stream-json"
MAX_DEPTH="${CC_MAX_DEPTH:-2}"
DEPTH_EXCEEDED_EXIT_CODE=3

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prompt)       PROMPT="$2";        shift 2 ;;
        --timeout)      TIMEOUT="$2";       shift 2 ;;
        --max-turns)    MAX_TURNS="$2";     shift 2 ;;
        --teams)        TEAMS=true;         shift   ;;
        --output-format) OUTPUT_FORMAT="$2"; shift 2 ;;
        --no-skip-permissions) SKIP_PERMISSIONS=false; shift ;;
        --max-depth)    MAX_DEPTH="$2";     shift 2 ;;
        *) echo "Unknown flag: $1" >&2; exit 1 ;;
    esac
done

if [[ -z "$PROMPT" ]]; then
    echo "Error: --prompt is required" >&2
    exit 1
fi

DEPTH="${CC_RECURSIVE_DEPTH:-0}"
if [[ ! "$DEPTH" =~ ^[0-9]+$ || ! "$MAX_DEPTH" =~ ^[0-9]+$ ]]; then
    echo "Error: CC_RECURSIVE_DEPTH and the max depth must be non-negative integers" >&2
    exit "$DEPTH_EXCEEDED_EXIT_CODE"
fi
if (( 10#$DEPTH + 1 > 10#$MAX_DEPTH )); then
    echo "Error: recursive spawn depth $((10#$DEPTH + 1)) exceeds max depth $MAX_DEPTH" >&2
    exit "$DEPTH_EXCEEDED_EXIT_CODE"
fi
export CC_RECURSIVE_DEPTH=$((10#$DEPTH + 1))

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
