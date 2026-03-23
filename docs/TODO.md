---
title: TODO - cc-recursive-team-mode
description: Task tracker for recursive Claude Code subprocess spawning harness
category: implementation
created: 2026-03-22
updated: 2026-03-23
version: 1.0.0
---

# TODO: cc-recursive-team-mode

## Done

- [x] Repository created
- [x] Foundational docs: README, UserStory, architecture, TODO
- [x] Project scaffold: pyproject.toml, Makefile, devcontainer, .gitignore, LICENSE.md, SECURITY.md
- [x] GitHub templates: PR template, issue templates (bug report, question)
- [x] Shell script: `scripts/cc-recursive-team.sh` — env clearing, flag parsing, stream-json capture
- [x] Pydantic models: `src/cc_recursive/models.py` — `RunConfig` and `RunResult` with field validation
- [x] Python wrapper: `src/cc_recursive/runner.py` — env allowlist, stream-json parsing, timeout (exit 124)
- [x] Public API: `src/cc_recursive/__init__.py` — exports `run`, `RunConfig`, `RunResult`
- [x] TDD test suite: 27 tests (96% coverage), Hypothesis property tests

## Next

- [ ] Session artifact parser: `src/cc_recursive/artifact_parser.py` — locate session JSONL, extract tool_use blocks, reconstruct subagent trees, extract task DAGs
- [ ] Integration tests: end-to-end test invoking real `claude -p` with `CLAUDECODE=` cleared, asserting `RunResult` fields
- [ ] CI: GitHub Actions workflow for lint, type check, unit tests

## Backlog

- [ ] Teams artifact validation: verify artifact collection works in teams mode
- [ ] Depth control: detect and limit recursive spawn depth (guard against unbounded recursion)
- [ ] `max_budget` mid-stream enforcement (requires streaming subprocess output)

## Deferred

- [ ] Claude Agent SDK integration (Phase 2) — replace subprocess invocation with SDK-native recursive agent calls when the SDK supports it
- [ ] Multi-hop recursive spawning — CC spawning CC spawning CC (depth > 1); requires depth tracking and cost attribution per level
- [ ] Wakapi support — correlate CC subprocess run durations with Wakapi session data for developer productivity analysis
