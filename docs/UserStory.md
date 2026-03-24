---
title: User Story - cc-recursive-team-mode
description: User stories for recursive Claude Code subprocess spawning with CLAUDECODE guard management
category: requirements
created: 2026-03-22
updated: 2026-03-22
version: 1.0.0
---

# User Story: cc-recursive-team-mode

## Problem Statement

Claude Code sets `CLAUDECODE=1` in its process environment, preventing nested `claude -p` calls from starting. There is no structured way to spawn CC subprocesses from within a CC session, capture their output programmatically, or parse CC session artifacts for evaluation.

## Target Users

AI agent developers running CC recursively for evaluation or orchestration.

## Value Proposition

Enable recursive CC spawning with structured output capture, so developers can build evaluation harnesses, orchestration pipelines, and comparison benchmarks that invoke CC as a subprocess.

## User Stories

- As a developer, I want to spawn a CC subprocess from within a CC session so that I can run nested agent tasks without the CLAUDECODE guard blocking execution.
- As a developer, I want to capture structured output (tokens, cost, tool calls, duration) from a CC subprocess so that I can analyze execution metrics programmatically.
- As a developer, I want to enable teams mode in a CC subprocess so that I can leverage parallel agent orchestration in nested runs.
- As a developer, I want to set timeout and budget limits on CC subprocesses so that I can prevent runaway cost and execution time.
- As a developer, I want to parse CC session artifacts (~/.claude JSONL, tasks, plans) so that I can extract execution traces for evaluation.

## Success Criteria

1. `CLAUDECODE= claude -p 'prompt'` returns exit code 0 and valid JSON output when run from within a CC session.
2. `RunResult` Pydantic model captures exit_code, duration_s, tokens, cost_usd, and tool_calls from stream-json output.
3. Teams mode activates when `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set in the subprocess environment.
4. Subprocess terminates cleanly when timeout or budget limit is exceeded.
5. Session artifact parser extracts tool_use blocks, subagent trees, and task DAGs from ~/.claude JSONL files.

## Constraints

- Python 3.13+, shell script + Python wrapper
- No CC source code modifications — env var manipulation only
- Must work in both interactive and headless (`claude -p`) modes
- Stream-json output format required for structured parsing

## Out of Scope

- Claude Agent SDK integration (Phase 2)
- GUI or web interface
- Modifying CC's internal guard mechanism
