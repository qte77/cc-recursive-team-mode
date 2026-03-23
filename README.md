# cc-recursive-team-mode

> Recursive Claude Code subprocess spawning with CLAUDECODE guard management

## Why

Claude Code sets `CLAUDECODE=1` to prevent accidental recursive spawning. This is a safety guard — but it also blocks legitimate use cases: evaluation harnesses, agent orchestration pipelines, and automated benchmarks that need to invoke `claude -p` as a subprocess from within a CC session.

This repo provides a shell script and Python wrapper that clear the guard, capture structured stream-json output, and return typed results. The repo itself serves as both the implementation **and** the test fixture — when CC runs `make validate` recursively on this codebase, the harness proves itself.

## Quick Start

### Shell

```bash
# Clear the guard and invoke CC headless
scripts/cc-recursive-team.sh --prompt "Summarize this repo." --max-turns 5

# With teams mode
scripts/cc-recursive-team.sh --prompt "Analyze src/" --teams --timeout 120
```

### Python

```python
from cc_recursive import run, RunConfig

result = run(RunConfig(
    prompt="Run make validate on this repo",
    timeout=120,
    teams=True,
))
print(f"exit={result.exit_code} tokens={result.tokens} cost=${result.cost_usd:.4f}")
print(f"tools: {result.tool_calls}")
```

### Development

```bash
make setup_dev     # Install deps (uv + all groups)
make test          # Run all tests (27 tests, 96% coverage)
make validate      # lint + type_check + test_coverage
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

**Phase 1 — Shell script + Python wrapper + models.** Core functionality implemented with TDD (27 tests, 96% coverage). Artifact parser deferred to Phase 2.

See [docs/TODO.md](docs/TODO.md) for the full task breakdown.

## Related Repos

- [coding-agent-eval](https://github.com/qte77/coding-agent-eval) — Evaluation framework for coding agents (PydanticAI-based MAS)
- [multi-tasking-quality-benchmark](https://github.com/qte77/multi-tasking-quality-benchmark) — WakaTime + quality metrics correlation benchmark
- [coding-agents-research](https://github.com/qte77/coding-agents-research) — Research notes and landscape analysis for coding agents

## License

MIT
