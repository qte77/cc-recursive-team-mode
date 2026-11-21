# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Spawn-depth guard: `run()` and `scripts/cc-recursive-team.sh` pass `CC_RECURSIVE_DEPTH` (depth + 1) to the child and refuse a spawn past `max_depth` (`RunConfig.max_depth`, `CC_MAX_DEPTH`, `--max-depth`; default 2) with **exit code 3**, without starting claude. A malformed inherited depth is refused the same way

- `RunConfig` and `RunResult` Pydantic models with field validation
- `run()` Python wrapper — subprocess invocation with env denylist, stream-json parsing, timeout handling (exit code 124)
- `scripts/cc-recursive-team.sh` — shell primitive with `--prompt`, `--timeout`, `--max-turns`, `--teams`, `--output-format` flags
- Public API: `from cc_recursive import run, RunConfig, RunResult`
- TDD test suite: 54 unit + 7 integration tests, 95% coverage
- Hypothesis property tests for model field invariants
- Project scaffold: pyproject.toml, Makefile, devcontainer, GitHub templates
- LICENSE.md (MIT), SECURITY.md
- `RunProfile` enum: `PLAIN` (bare CC) vs `ENHANCED` (with .claude/ config)
- `skip_permissions` field (default True) — passes `--dangerously-skip-permissions`
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

- `RunSettings(BaseSettings)` — env-var-driven config with `CC_` prefix (pydantic-settings)
- `RunConfig` inherits `RunSettings` — backward-compatible, env vars override defaults
- `CC_BINARY` env var for custom claude CLI path (default: `"claude"`)
- Prompt catalog: `prompts/` dir with `load_prompt()` loader — no hardcoded prompts in code
- `prompts/validate.txt`, `prompts/review.txt`, `prompts/benchmark.txt`

### Changed

- CodeQL workflow: `actions/checkout` and `github/codeql-action` pinned to full commit SHAs
  (v7.0.1, v4.39.3) instead of the `v7` / `v4` tags.
- CI workflow: `actions/checkout` and `actions/setup-python` pinned to full commit SHAs
  (v7.0.1, v7.1.0) instead of the `v7` tags, which point at the same commits today.
- CI and CodeQL workflows hardened: checkouts no longer persist the token
  (`persist-credentials: false`), `GITHUB_TOKEN` is read-only in CI and scoped per job in CodeQL, uv comes from
  `astral-sh/setup-uv` (SHA-pinned, uv 0.13.7) instead of an unpinned `pip install uv`, and both jobs have a
  timeout and a per-ref concurrency group that cancels superseded PR runs.
- CI caches uv's downloads through `astral-sh/setup-uv` (its default cache); `make setup_dev` installs the
  same uv as CI (`uv==0.13.7`), and the CodeQL job drops `actions: read`, which a public repo does not need.
- Profile PLAIN no longer uses `--config-dir` or `--bare` — profile distinction is caller-controlled via working directory content
