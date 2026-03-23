"""Tests for cc_recursive.models — RunConfig and RunResult Pydantic models.

Mock strategy: None — pure Pydantic model tests, no external I/O.
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from cc_recursive.models import RunConfig, RunProfile, RunResult


class TestRunConfigDefaults:
    """RunConfig default values match architecture.md specification."""

    def test_run_config_defaults(self):
        """Given only prompt, should use documented defaults."""
        # Arrange / Act
        config = RunConfig(prompt="hello")
        # Assert
        assert config.timeout == 300.0
        assert config.max_turns == 20
        assert config.max_budget is None
        assert config.teams is False
        assert config.output_format == "stream-json"

    def test_run_config_all_fields(self):
        """Given all fields provided, should store all values."""
        # Arrange / Act
        config = RunConfig(
            prompt="test prompt",
            timeout=60.0,
            max_turns=5,
            max_budget=1.00,
            teams=True,
            output_format="stream-json",
        )
        # Assert
        assert config.prompt == "test prompt"
        assert config.timeout == 60.0
        assert config.max_turns == 5
        assert config.max_budget == 1.00
        assert config.teams is True

    def test_run_config_prompt_required(self):
        """Given no prompt, should raise ValidationError."""
        with pytest.raises(ValidationError):
            RunConfig()  # type: ignore[call-arg]

    def test_run_config_prompt_empty_string_rejected(self):
        """Given empty prompt string, should raise ValidationError."""
        with pytest.raises(ValidationError):
            RunConfig(prompt="")


class TestRunResultConstruction:
    """RunResult accepts valid numeric values including zeros."""

    def test_run_result_from_parsed_data(self):
        """Given parsed data dict, should store all fields."""
        # Arrange / Act
        result = RunResult(
            exit_code=0,
            duration_s=12.5,
            tokens=1500,
            cost_usd=0.03,
            tool_calls=["Read", "Bash"],
            raw_output='{"type":"result"}',
        )
        # Assert
        assert result.exit_code == 0
        assert result.duration_s == 12.5
        assert result.tokens == 1500
        assert result.cost_usd == 0.03
        assert result.tool_calls == ["Read", "Bash"]

    def test_run_result_zero_cost(self):
        """Given zero cost and tokens, should be valid."""
        result = RunResult(
            exit_code=0, duration_s=0.1, tokens=0, cost_usd=0.0, tool_calls=[], raw_output=""
        )
        assert result.tokens == 0
        assert result.cost_usd == 0.0

    def test_run_result_nonzero_exit_code(self):
        """Given non-zero exit code, should be valid."""
        result = RunResult(
            exit_code=1, duration_s=5.0, tokens=100, cost_usd=0.001, tool_calls=[], raw_output=""
        )
        assert result.exit_code == 1


class TestRunProfile:
    """RunProfile enum values."""

    def test_run_profile_plain_value(self):
        """PLAIN profile should equal 'plain'."""
        assert RunProfile.PLAIN == "plain"

    def test_run_profile_enhanced_value(self):
        """ENHANCED profile should equal 'enhanced'."""
        assert RunProfile.ENHANCED == "enhanced"


class TestRunConfigProfileAndPermissions:
    """RunConfig profile and skip_permissions fields."""

    def test_run_config_skip_permissions_default_true(self):
        """Default skip_permissions should be True (headless use case)."""
        config = RunConfig(prompt="test")
        assert config.skip_permissions is True

    def test_run_config_profile_default_plain(self):
        """Default profile should be PLAIN."""
        config = RunConfig(prompt="test")
        assert config.profile == RunProfile.PLAIN

    def test_run_config_enhanced_profile(self):
        """Can set profile to ENHANCED."""
        config = RunConfig(prompt="test", profile=RunProfile.ENHANCED)
        assert config.profile == RunProfile.ENHANCED

    def test_run_config_skip_permissions_false(self):
        """Can disable skip_permissions."""
        config = RunConfig(prompt="test", skip_permissions=False)
        assert config.skip_permissions is False


class TestRunConfigHypothesis:
    """Property-based tests for RunConfig field invariants."""

    @given(timeout=st.floats(min_value=0.001, max_value=86400.0, allow_nan=False))
    def test_run_config_timeout_positive(self, timeout: float):
        """Given any positive timeout, RunConfig should accept it."""
        config = RunConfig(prompt="test", timeout=timeout)
        assert config.timeout > 0

    @given(max_turns=st.integers(min_value=1, max_value=1000))
    def test_run_config_max_turns_positive_int(self, max_turns: int):
        """Given any positive max_turns, RunConfig should accept it."""
        config = RunConfig(prompt="test", max_turns=max_turns)
        assert config.max_turns >= 1


class TestRunResultHypothesis:
    """Property-based tests for RunResult field invariants."""

    @given(tokens=st.integers(min_value=0, max_value=10_000_000))
    def test_run_result_tokens_non_negative(self, tokens: int):
        """Given any non-negative token count, RunResult should accept it."""
        result = RunResult(
            exit_code=0, duration_s=1.0, tokens=tokens, cost_usd=0.0, tool_calls=[], raw_output=""
        )
        assert result.tokens >= 0

    @given(cost=st.floats(min_value=0.0, max_value=1000.0, allow_nan=False))
    def test_run_result_cost_non_negative(self, cost: float):
        """Given any non-negative cost, RunResult should accept it."""
        result = RunResult(
            exit_code=0, duration_s=1.0, tokens=0, cost_usd=cost, tool_calls=[], raw_output=""
        )
        assert result.cost_usd >= 0.0
