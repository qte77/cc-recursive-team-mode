"""Integration tests — real claude -p invocation.

These tests invoke the real claude binary. They cost money and require:
- claude CLI installed and authenticated
- Network access to Anthropic API
- ANTHROPIC_API_KEY in environment

Run explicitly: make test_integration
Excluded from make test by default.
"""

import shutil

import pytest

from cc_recursive.models import RunConfig, RunProfile
from cc_recursive.runner import run

pytestmark = pytest.mark.integration

# Skip entire module if claude binary not found
if not shutil.which("claude"):
    pytest.skip("claude binary not found", allow_module_level=True)

# Reason: Minimal config to keep cost low — 1 turn, short timeout, PLAIN profile
CHEAP_CONFIG = RunConfig(
    prompt="What is 2+2? Answer with just the number.",
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
            prompt="What is 2+2? Answer with just the number.",
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
            prompt="What is 2+2? Answer with just the number.",
            timeout=120.0,
            max_turns=1,
            profile=RunProfile.ENHANCED,
        )
        result = run(config)
        assert result.exit_code == 0

    def test_run_timeout_enforced(self):
        """Very short timeout should produce exit_code=124."""
        config = RunConfig(
            prompt="Write a 10000 word essay about the history of computing.",
            timeout=0.001,
            max_turns=1,
        )
        result = run(config)
        assert result.exit_code == 124
