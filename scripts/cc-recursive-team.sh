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
# Spawn-depth guard (cooperative: unsetting the variables, or calling claude directly, skips it).
# The child gets CC_RECURSIVE_DEPTH = this process's depth + 1 (absent = 0) and CC_MAX_DEPTH = the
# effective limit, the same variables and rules as the Python runner. --max-depth can lower an
# inherited CC_MAX_DEPTH but not raise it, so the limit binds the whole tree. A spawn past the
# limit, or a depth or limit that is not 1-9 ASCII digits (empty included), exits 3 without
# starting claude.

set -euo pipefail

PROMPT=""
TIMEOUT=300
MAX_TURNS=20
TEAMS=false
SKIP_PERMISSIONS=true
OUTPUT_FORMAT="stream-json"
MAX_DEPTH_FLAG=""
DEPTH_EXCEEDED_EXIT_CODE=3

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prompt)       PROMPT="$2";        shift 2 ;;
        --timeout)      TIMEOUT="$2";       shift 2 ;;
        --max-turns)    MAX_TURNS="$2";     shift 2 ;;
        --teams)        TEAMS=true;         shift   ;;
        --output-format) OUTPUT_FORMAT="$2"; shift 2 ;;
        --no-skip-permissions) SKIP_PERMISSIONS=false; shift ;;
        --max-depth)    MAX_DEPTH_FLAG="$2"; shift 2 ;;
        *) echo "Unknown flag: $1" >&2; exit 1 ;;
    esac
done

if [[ -z "$PROMPT" ]]; then
    echo "Error: --prompt is required" >&2
    exit 1
fi

# Reason: an explicit digit list, not [0-9], which can match non-ASCII digits in a UTF-8 locale;
# at most 9 digits, so shell arithmetic cannot overflow.
is_count() { [[ "$1" =~ ^[0123456789]{1,9}$ ]]; }
refuse() { echo "Error: $1" >&2; exit "$DEPTH_EXCEEDED_EXIT_CODE"; }

DEPTH="${CC_RECURSIVE_DEPTH-0}"
is_count "$DEPTH" || refuse "CC_RECURSIVE_DEPTH must be 1-9 digits, got '$DEPTH'"
if [[ -n "$MAX_DEPTH_FLAG" ]]; then
    is_count "$MAX_DEPTH_FLAG" || refuse "--max-depth must be 1-9 digits, got '$MAX_DEPTH_FLAG'"
    LIMIT=$((10#$MAX_DEPTH_FLAG))
else
    LIMIT=2
fi
if [[ -n "${CC_MAX_DEPTH+set}" ]]; then
    is_count "$CC_MAX_DEPTH" || refuse "CC_MAX_DEPTH must be 1-9 digits, got '$CC_MAX_DEPTH'"
    if [[ -z "$MAX_DEPTH_FLAG" ]] || (( 10#$CC_MAX_DEPTH < LIMIT )); then
        LIMIT=$((10#$CC_MAX_DEPTH))
    fi
fi
CHILD_DEPTH=$((10#$DEPTH + 1))
if (( CHILD_DEPTH > LIMIT )); then
    refuse "recursive spawn depth $CHILD_DEPTH exceeds max depth $LIMIT"
fi
export CC_RECURSIVE_DEPTH="$CHILD_DEPTH" CC_MAX_DEPTH="$LIMIT"

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
