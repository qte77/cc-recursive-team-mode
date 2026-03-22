---
title: TODO - cc-recursive-team-mode
description: Task tracker for recursive Claude Code subprocess spawning harness
category: implementation
created: 2026-03-22
updated: 2026-03-22
version: 1.0.0
---

# TODO: cc-recursive-team-mode

## Done

- [x] Repository created
- [x] Foundational docs: README, UserStory, architecture, TODO

## Next

- [ ] Shell script: `scripts/cc-recursive-team.sh` — env clearing, subprocess invocation, stream-json capture, exit code forwarding
- [ ] Python wrapper: `src/cc_recursive/runner.py` — `subprocess.run()` with env allowlist filtering, timeout enforcement, budget limit via stream-json monitoring
- [ ] Pydantic models: `src/cc_recursive/models.py` — `RunConfig` and `RunResult` with full field definitions
- [ ] Package init: `src/cc_recursive/__init__.py` — public API export (`run`, `RunConfig`, `RunResult`)
- [ ] Unit tests for `RunConfig` validation and `RunResult` parsing from fixture stream-json

## Backlog

- [ ] Session artifact parser: `src/cc_recursive/artifact_parser.py` — locate session JSONL, extract tool_use blocks, reconstruct subagent trees, extract task DAGs
- [ ] Teams orchestration support: pass `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` via `RunConfig.teams`, validate artifact collection in teams mode
- [ ] Depth control: detect and limit recursive spawn depth (guard against unbounded recursion)
- [ ] Integration tests: end-to-end test invoking real `claude -p` with `CLAUDECODE=` cleared, asserting `RunResult` fields
- [ ] CI: GitHub Actions workflow for lint, type check, unit tests
- [ ] `pyproject.toml`, `Makefile` — project tooling setup (ruff, pyright, pytest)

## Deferred

- [ ] Claude Agent SDK integration (Phase 2) — replace subprocess invocation with SDK-native recursive agent calls when the SDK supports it
- [ ] Multi-hop recursive spawning — CC spawning CC spawning CC (depth > 1); requires depth tracking and cost attribution per level
- [ ] Wakapi support — correlate CC subprocess run durations with Wakapi session data for developer productivity analysis
