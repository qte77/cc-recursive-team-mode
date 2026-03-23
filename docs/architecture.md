---
title: Architecture - cc-recursive-team-mode
description: Technical architecture for recursive Claude Code subprocess spawning with CLAUDECODE guard management
category: technical
created: 2026-03-22
updated: 2026-03-22
version: 1.0.0
---

# Architecture: cc-recursive-team-mode

## Overview

cc-recursive-team-mode solves a single root problem: Claude Code sets `CLAUDECODE=1` in its process environment, and child `claude` processes inherit this variable and refuse to start. The harness clears the guard variable before subprocess invocation, captures stream-json output, and parses CC session artifacts into typed Python models for evaluation and orchestration pipelines.

The design is intentionally minimal — a shell primitive for direct invocation and a Python wrapper for programmatic use. No CC source modifications are required; all behavior is driven by env var manipulation.

## Components

### Shell Primitive: `scripts/cc-recursive-team.sh`

Handles env clearing, subprocess lifecycle, and raw stream-json capture.

Responsibilities:

- Unset `CLAUDECODE` before invoking `claude -p`
- Optionally set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` for teams mode
- Pass `--output-format stream-json` and `--max-turns` flags
- Forward stdout to a capture file; stream stderr to the caller
- Exit with the child process exit code

### Python Wrapper: `src/cc_recursive/runner.py`

Provides a `run()` function that invokes the shell primitive via `subprocess.run()` with env filtering and returns a typed `RunResult`.

Responsibilities:

- Build the subprocess env via denylist (inherit parent env minus CLAUDECODE)
- Enforce `timeout` limit (exit code 124 on breach); `max_budget` modeled but not yet enforced
- Parse stream-json lines from stdout into `RunResult`
- Expose a synchronous `run(config: RunConfig) -> RunResult` interface

### Pydantic Models: `src/cc_recursive/models.py`

`RunConfig` — input to `run()`:

| Field | Type | Default | Purpose |
|---|---|---|---|
| `prompt` | `str` | required | The prompt passed to `claude -p` |
| `timeout` | `float` | `300.0` | Wall-clock timeout in seconds |
| `max_turns` | `int` | `20` | `--max-turns` flag value |
| `max_budget` | `float \| None` | `None` | USD budget cap; None = unlimited |
| `teams` | `bool` | `False` | Enable `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` |
| `output_format` | `str` | `"stream-json"` | CC output format flag |

`RunResult` — output from `run()`:

| Field | Type | Purpose |
|---|---|---|
| `exit_code` | `int` | Subprocess exit code |
| `duration_s` | `float` | Wall-clock execution time in seconds |
| `tokens` | `int` | Total tokens consumed (input + output) |
| `cost_usd` | `float` | Estimated cost in USD from stream-json metadata |
| `tool_calls` | `list[str]` | Names of tools invoked during the run |
| `raw_output` | `str` | Raw stream-json text for downstream parsing |

### CC Session Artifact Parser: `src/cc_recursive/artifact_parser.py`

Parses `~/.claude` JSONL session files produced during subprocess execution.

Responsibilities:

- Locate the most recent session file written during a run window
- Extract `tool_use` blocks with inputs, outputs, and timestamps
- Reconstruct subagent invocation trees (parent/child relationships)
- Extract task DAGs from `TodoWrite` and `Task` events (teams mode)

## Data Flow

```text
caller → RunConfig → runner.py → subprocess(CLAUDECODE= claude -p ...) → stream-json → RunResult
                                                                      |
                                                            ~/.claude/ JSONL → artifact_parser.py → traces
```

## Environment Variable Reference

| Variable | Purpose | Default |
|---|---|---|
| `CLAUDECODE` | CC sets this to `1` to detect nested invocations. Must be cleared (`CLAUDECODE=`) to allow recursive spawning. | `1` (set by CC) |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | Enables parallel multi-agent teams orchestration within the subprocess. | unset |
| `CLAUDE_CODE_SUBAGENT_MODEL` | Model used by subagents spawned by the child CC process. | inherits CC default |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | Disables telemetry and non-essential network traffic in the subprocess. | unset |
| `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS` | Suppresses git-related system prompt injections in the subprocess. | unset |
| `CLAUDE_CODE_DISABLE_1M_CONTEXT` | Prevents CC from using 1M-token context window in the subprocess. | unset |
| `CLAUDE_CODE_EFFORT_LEVEL` | Controls reasoning effort in the subprocess (`low`, `medium`, `high`). | `high` |

## Directory Structure

```text
cc-recursive-team-mode/
├── scripts/
│   └── cc-recursive-team.sh
├── src/
│   └── cc_recursive/
│       ├── __init__.py
│       ├── runner.py
│       ├── models.py
│       └── artifact_parser.py
├── tests/
├── docs/
│   ├── UserStory.md
│   ├── architecture.md
│   └── TODO.md
└── README.md
```

## Design Decisions

**Shell primitive first, Python wrapper second.** The shell script is the minimal reproducible proof that recursive spawning works. The Python wrapper adds structure on top of a known-working primitive — not the other way around.

**Env denylist, not allowlist.** Child claude process inherits the parent's full environment minus `CLAUDECODE`. An allowlist approach was tried first but proved too restrictive — claude requires Node.js runtime vars, Codespaces auth tokens, XDG vars, etc. that vary by environment. Since the child has the same privilege level as the parent, full env inheritance is safe.

**No CC source modifications.** All behavior is achieved through env var manipulation and CLI flags. This keeps the harness compatible with future CC versions without requiring patches.

**stream-json requires `--verbose`.** In `-p` (print) mode, `--output-format stream-json` requires the `--verbose` flag or claude exits with an error. The runner adds `--verbose` automatically when `output_format == "stream-json"`.

**PLAIN profile uses `--setting-sources user`.** The `--bare` flag was considered for PLAIN profile but it disables OAuth/keychain auth, breaking Codespaces environments. `--setting-sources user` loads user settings (including auth) but skips project-level `.claude/` config (skills, rules, CLAUDE.md), achieving the desired A/B separation without auth breakage.

**`/loop` is single-shot in `-p` mode.** `/loop` accepts syntax in `-p` mode but the session exits after the first iteration, killing the cron scheduler. Recurring execution requires a persistent interactive session or an external loop.
