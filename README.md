# cc-recursive-team-mode

Recursive Claude Code subprocess spawning with CLAUDECODE guard management

## Problem

Claude Code sets `CLAUDECODE=1` in its process environment. Child `claude` processes inherit this variable and refuse to start, making recursive spawning impossible by default. Attempting to run `claude -p "prompt"` from within a CC session results in an immediate exit with an error.

The fix is to clear the guard variable explicitly before invoking the child process:

```bash
CLAUDECODE= claude -p "prompt"
```

This harness provides a shell script and Python wrapper that automate guard clearing, capture structured stream-json output, and parse CC session artifacts for evaluation and orchestration use cases.

## Quick Start

Clear the guard and invoke CC as a subprocess:

```bash
# Minimal invocation — clears CLAUDECODE, runs in headless mode
CLAUDECODE= claude -p "Summarize this repo in one sentence."

# With teams mode and budget cap
CLAUDECODE= CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 \
  claude -p "Analyze src/ for performance issues." \
  --output-format stream-json \
  --max-turns 10
```

Using the Python wrapper (Phase 1):

```python
from cc_recursive.runner import run

result = run(
    prompt="Write a test for src/main.py",
    timeout=120,
    max_budget=0.50,
    teams=True,
)
print(result.cost_usd, result.tokens, result.tool_calls)
```

## Features

- **Guard clearing**: Automatically unsets `CLAUDECODE` before spawning child processes
- **stream-json parsing**: Parses CC stream-json output into a typed `RunResult` Pydantic model
- **Teams support**: Activates `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` for parallel agent orchestration in subprocesses
- **Timeout and budget limits**: Terminates subprocesses cleanly when wall-clock or cost thresholds are exceeded
- **Env var filtering**: Passes only an explicit allowlist of env vars to child processes to prevent credential leakage
- **Session artifact parsing**: Extracts tool_use blocks, subagent trees, and task DAGs from `~/.claude` JSONL files

## Environment Variable Reference

| Variable | Purpose | Default |
|---|---|---|
| `CLAUDECODE` | CC sets this to `1` to detect nested invocations. Must be cleared (`CLAUDECODE=`) to allow recursive spawning. | `1` (set by CC) |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | Enables parallel multi-agent teams orchestration within the subprocess. | unset |
| `CLAUDE_CODE_SUBAGENT_MODEL` | Model used by subagents spawned by the child CC process. | inherits CC default |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | Disables telemetry and non-essential network traffic in the subprocess. Useful for cost control and offline testing. | unset |
| `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS` | Suppresses git-related system prompt injections in the subprocess. | unset |
| `CLAUDE_CODE_DISABLE_1M_CONTEXT` | Prevents CC from using 1M-token context window in the subprocess. Reduces cost for small tasks. | unset |
| `CLAUDE_CODE_EFFORT_LEVEL` | Controls reasoning effort in the subprocess (`low`, `medium`, `high`). | `high` |

## Status

**Phase 0 — Documentation only.** No implementation code exists yet. Foundational docs (README, UserStory, architecture, TODO) are complete. Phase 1 implementation (shell script + Python wrapper + RunResult model) is next.

See [docs/TODO.md](docs/TODO.md) for the full task breakdown.

## Related Repos

- [coding-agent-eval](https://github.com/qte77/coding-agent-eval) — Evaluation framework for coding agents (PydanticAI-based MAS)
- [multi-tasking-quality-benchmark](https://github.com/qte77/multi-tasking-quality-benchmark) — WakaTime + quality metrics correlation benchmark
- [coding-agents-research](https://github.com/qte77/coding-agents-research) — Research notes and landscape analysis for coding agents

## License

MIT
