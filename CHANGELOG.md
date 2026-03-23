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
- TDD test suite: 27 tests (11 model, 13 runner, 3 shell script), 96% coverage
- Hypothesis property tests for model field invariants
- Project scaffold: pyproject.toml, Makefile, devcontainer, GitHub templates
- LICENSE.md (MIT), SECURITY.md
- `RunProfile` enum: `PLAIN` (bare CC) vs `ENHANCED` (with .claude/ config)
- `skip_permissions` field (default True) — passes `--dangerously-skip-permissions`
- Profile-based `--config-dir /dev/null` injection for PLAIN mode
- Shell script `--no-skip-permissions` flag
- "Recurring Execution" README section documenting `/loop` limitation
