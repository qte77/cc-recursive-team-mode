# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `RunConfig` and `RunResult` Pydantic models with field validation
- `run()` Python wrapper — subprocess invocation with env allowlist, stream-json parsing, timeout handling (exit code 124)
- `scripts/cc-recursive-team.sh` — shell primitive with `--prompt`, `--timeout`, `--max-turns`, `--teams`, `--output-format` flags
- Public API: `from cc_recursive import run, RunConfig, RunResult`
- TDD test suite: 38 tests (17 model, 17 runner, 4 shell script), 97% coverage
- Hypothesis property tests for model field invariants
- Project scaffold: pyproject.toml, Makefile, devcontainer, GitHub templates
- LICENSE.md (MIT), SECURITY.md
- `RunProfile` enum: `PLAIN` (bare CC) vs `ENHANCED` (with .claude/ config)
- `skip_permissions` field (default True) — passes `--dangerously-skip-permissions`
- Profile-based `--config-dir /dev/null` injection for PLAIN mode
- Shell script `--no-skip-permissions` flag
- `/loop` note: accepts syntax in `-p` but session exits after first iteration
- `artifact_parser.py` — session JSONL extraction, subagent tree reconstruction
- `ToolUseEvent`, `SubagentNode`, `SessionArtifacts` Pydantic models
- `parse_session()`, `extract_tool_uses()`, `find_session_jsonl()`, `find_subagents()` functions
- CI workflow (`.github/workflows/ci.yaml`) — lint, type check, test on push/PR
- Integration tests (`tests/test_integration.py`) — 7 real `claude -p` tests, excluded from `make test` by default
- `make test_integration` recipe for explicit integration test execution
- Env denylist approach (replaced allowlist) — child claude inherits full parent env minus CLAUDECODE
- `--verbose` flag auto-added when `output_format == "stream-json"` (required by CC in `-p` mode)

### Changed

- Profile PLAIN no longer uses `--config-dir` or `--bare` — profile distinction is caller-controlled via working directory content
