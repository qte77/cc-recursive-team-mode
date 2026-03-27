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
from cc_recursive import run, RunConfig, RunProfile

# Plain-vanilla: bare CC, no skills/rules/CLAUDE.md
result = run(RunConfig(prompt="Run make validate on this repo", timeout=120))

# Enhanced: CC with full project config (.claude/, skills, rules)
result = run(RunConfig(
    prompt="Run make validate on this repo",
    timeout=120,
    teams=True,
    profile=RunProfile.ENHANCED,
))
print(f"exit={result.exit_code} tokens={result.tokens} cost=${result.cost_usd:.4f}")
print(f"tools: {result.tool_calls}")
```

### Development

```bash
make setup_dev     # Install deps (uv + all groups)
make test              # Unit tests (54 tests, 95% coverage)
make test_integration  # Integration tests (7 tests, real claude -p)
make validate          # lint + type_check + test_coverage
```

## Features

- **Guard clearing**: Automatically unsets `CLAUDECODE` before spawning child processes
- **Permission bypass**: `--dangerously-skip-permissions` by default for headless autonomous execution
- **Run profiles**: `PLAIN` (bare CC, no .claude/ config) vs `ENHANCED` (with skills, rules, CLAUDE.md) for controlled A/B comparison
- **stream-json parsing**: Parses CC stream-json output into a typed `RunResult` Pydantic model
- **Teams support**: Activates `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` for parallel agent orchestration in subprocesses
- **Timeout handling**: Terminates subprocesses cleanly when wall-clock timeout is exceeded (exit code 124)
- **Env denylist**: Child inherits parent env minus `CLAUDECODE` — safe for same-privilege subprocess
- **Session artifact parsing**: Extracts tool_use blocks and reconstructs subagent trees from `~/.claude` JSONL files

## Use Cases

### 1. Self-validate recursively

CC invokes itself to run `make validate` on this repo — the harness proves itself.

```python
from cc_recursive import run, RunConfig

result = run(RunConfig(prompt="Run make validate and report results", timeout=300))
print(f"exit={result.exit_code} cost=${result.cost_usd:.4f} tools={result.tool_calls}")
```

### 2. A/B compare plain vs enhanced CC

Run the same prompt with and without project config to measure scaffolding impact.

```python
from cc_recursive import run, RunConfig, RunProfile

plain = run(RunConfig(prompt="Fix the lint error in src/", profile=RunProfile.PLAIN))
enhanced = run(RunConfig(prompt="Fix the lint error in src/", profile=RunProfile.ENHANCED))
print(f"PLAIN: tokens={plain.tokens} cost=${plain.cost_usd:.4f}")
print(f"ENHANCED: tokens={enhanced.tokens} cost=${enhanced.cost_usd:.4f}")
```

### 3. Teams mode benchmark

Compare solo vs teams CC on the same task.

```python
from cc_recursive import run, RunConfig

solo = run(RunConfig(prompt="Add tests for runner.py", timeout=120))
teams = run(RunConfig(prompt="Add tests for runner.py", timeout=120, teams=True))
print(f"Solo: {solo.tokens} tokens, ${solo.cost_usd:.4f}")
print(f"Teams: {teams.tokens} tokens, ${teams.cost_usd:.4f}")
```

### 4. Parse session artifacts after a run

Extract tool usage and subagent trees from CC session files.

```python
from pathlib import Path
from cc_recursive import parse_session

artifacts = parse_session(Path("~/.claude/projects/-my-project/session.jsonl").expanduser())
print(f"Tools: {[t.name for t in artifacts.tool_uses]}")
print(f"Subagents: {len(artifacts.subagents)}")
print(f"Total calls: {artifacts.total_tool_calls}")
```

### 5. Shell — headless batch execution

```bash
# Solo, plain, 5 turns max
scripts/cc-recursive-team.sh --prompt "Summarize README.md" --max-turns 5

# Teams mode, no permission bypass
scripts/cc-recursive-team.sh --prompt "Review src/" --teams --no-skip-permissions
```

## Configuration via Environment Variables

All `RunSettings` fields can be overridden via `CC_` prefixed env vars:

```bash
CC_TIMEOUT=60 CC_TEAMS=true CC_BINARY=/usr/local/bin/claude uv run python -c "
from cc_recursive import RunConfig
c = RunConfig(prompt='test')
print(c.timeout, c.teams, c.binary)  # 60.0 True /usr/local/bin/claude
"
```

## Prompt Catalog

Prompts are plain text files in `prompts/`, loaded by name:

```python
from cc_recursive import load_prompt, run, RunConfig

result = run(RunConfig(prompt=load_prompt("validate")))
```

Add new prompts by creating `.txt` files in `prompts/`.

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

## Note on `/loop`

CC's `/loop` command accepts syntax in `-p` mode but does not persist — the session exits after the first iteration, killing the cron scheduler. `/loop` requires a persistent interactive session for recurring execution.

## Status

**Phase 5 complete.** Models, runner, profiles, artifact parser, CI, integration tests (solo + teams on real coding tasks), pydantic-settings, prompt catalog. 71 unit + 11 integration tests, 96% coverage.

See [docs/TODO.md](docs/TODO.md) for the full task breakdown.

## Related Repos

- [coding-agent-eval](https://github.com/qte77/coding-agent-eval) — Evaluation framework for coding agents (PydanticAI-based MAS)
- [multi-tasking-quality-benchmark](https://github.com/qte77/multi-tasking-quality-benchmark) — WakaTime + quality metrics correlation benchmark
- [coding-agents-research](https://github.com/qte77/coding-agents-research) — Research notes and landscape analysis for coding agents

## License

Apache-2.0
