"""Integration tests — real claude -p invocation.

These tests invoke the real claude binary. They cost money and require:
- claude CLI installed and authenticated
- Network access to Anthropic API
- ANTHROPIC_API_KEY in environment

Run explicitly: make test_integration
Excluded from make test by default.
"""

import shutil
from pathlib import Path

import pytest

from cc_recursive.models import RunConfig, RunProfile
from cc_recursive.prompts import load_prompt
from cc_recursive.runner import run

pytestmark = pytest.mark.integration

# Skip entire module if claude binary not found
if not shutil.which("claude"):
    pytest.skip("claude binary not found", allow_module_level=True)

_TESTS_PROMPTS_DIR = Path(__file__).parent / "prompts"

# Reason: Minimal config to keep cost low — 1 turn, short timeout, PLAIN profile
CHEAP_CONFIG = RunConfig(
    prompt=load_prompt("cheap", prompts_dir=_TESTS_PROMPTS_DIR),
    timeout=60.0,
    max_turns=1,
)


class TestRealClaudeInvocation:
    """End-to-end tests with real claude -p subprocess."""

    def test_run_returns_valid_result(self):
        """Real claude -p should return RunResult with exit_code 0."""
        result = run(CHEAP_CONFIG)
        assert result.exit_code == 0

    def test_run_captures_tokens_and_cost(self):
        """Real run should report non-zero tokens and cost."""
        result = run(CHEAP_CONFIG)
        assert result.tokens > 0
        assert result.cost_usd > 0.0

    def test_run_captures_duration(self):
        """Real run should report positive duration."""
        result = run(CHEAP_CONFIG)
        assert result.duration_s > 0.0

    def test_run_has_raw_output(self):
        """Real run should produce non-empty raw_output."""
        result = run(CHEAP_CONFIG)
        assert len(result.raw_output) > 0

    def test_run_plain_profile_works(self):
        """PLAIN profile (--config-dir /dev/null) should complete successfully."""
        config = RunConfig(
            prompt=load_prompt("cheap", prompts_dir=_TESTS_PROMPTS_DIR),
            timeout=60.0,
            max_turns=1,
            profile=RunProfile.PLAIN,
        )
        result = run(config)
        assert result.exit_code == 0

    def test_run_enhanced_profile_works(self):
        """ENHANCED profile should complete successfully."""
        # Reason: ENHANCED loads hooks/plugins/CLAUDE.md which adds startup time
        config = RunConfig(
            prompt=load_prompt("cheap", prompts_dir=_TESTS_PROMPTS_DIR),
            timeout=120.0,
            max_turns=1,
            profile=RunProfile.ENHANCED,
        )
        result = run(config)
        assert result.exit_code == 0

    def test_run_timeout_enforced(self):
        """Very short timeout should produce exit_code=124."""
        config = RunConfig(
            prompt=load_prompt("timeout", prompts_dir=_TESTS_PROMPTS_DIR),
            timeout=0.001,
            max_turns=1,
        )
        result = run(config)
        assert result.exit_code == 124


class TestRealCodingTasks:
    """Integration tests with real coding tasks that exercise CC tool use."""

    def test_run_solo_validate(self):
        """Solo CC should run make validate and use Bash tool."""
        config = RunConfig(
            prompt=load_prompt("validate_repo", prompts_dir=_TESTS_PROMPTS_DIR),
            timeout=300.0,
            max_turns=5,
        )
        result = run(config)
        assert result.exit_code == 0
        assert result.tokens > 0
        assert len(result.tool_calls) > 0

    def test_run_solo_review(self):
        """Solo CC should read runner.py and use Read tool."""
        config = RunConfig(
            prompt=load_prompt("review_runner", prompts_dir=_TESTS_PROMPTS_DIR),
            timeout=300.0,
            max_turns=3,
        )
        result = run(config)
        assert result.exit_code == 0
        assert result.tokens > 0
        assert len(result.tool_calls) > 0

    def test_run_teams_validate(self):
        """Teams CC should run make validate with parallel agents."""
        config = RunConfig(
            prompt=load_prompt("validate_repo", prompts_dir=_TESTS_PROMPTS_DIR),
            timeout=300.0,
            max_turns=5,
            teams=True,
        )
        result = run(config)
        assert result.exit_code == 0
        assert result.tokens > 0

    def test_run_teams_review(self):
        """Teams CC should review runner.py with parallel agents."""
        config = RunConfig(
            prompt=load_prompt("review_runner", prompts_dir=_TESTS_PROMPTS_DIR),
            timeout=300.0,
            max_turns=3,
            teams=True,
        )
        result = run(config)
        assert result.exit_code == 0
        assert result.tokens > 0
