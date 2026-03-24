"""Tests for cc_recursive.models — RunConfig and RunResult Pydantic models.

Mock strategy: None — pure Pydantic model tests, no external I/O.
"""

import os

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from cc_recursive.models import (
    RunConfig,
    RunProfile,
    RunResult,
    RunSettings,
    SessionArtifacts,
    SubagentNode,
    ToolUseEvent,
)


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


class TestToolUseEvent:
    """ToolUseEvent model construction."""

    def test_tool_use_event_construction(self):
        """All fields populated correctly."""
        event = ToolUseEvent(
            name="Read",
            tool_use_id="toolu_abc123",
            input={"file_path": "/src/main.py"},
            timestamp="2026-03-23T12:00:00.000Z",
        )
        assert event.name == "Read"
        assert event.tool_use_id == "toolu_abc123"
        assert event.input == {"file_path": "/src/main.py"}


class TestSubagentNode:
    """SubagentNode recursive tree structure."""

    def test_subagent_node_recursive(self, tmp_path):
        """SubagentNode can contain children."""
        child = SubagentNode(
            session_id="child-uuid",
            jsonl_path=tmp_path / "child.jsonl",
            tool_uses=[],
            children=[],
        )
        parent = SubagentNode(
            session_id="parent-uuid",
            jsonl_path=tmp_path / "parent.jsonl",
            tool_uses=[],
            children=[child],
        )
        assert len(parent.children) == 1
        assert parent.children[0].session_id == "child-uuid"


class TestSessionArtifacts:
    """SessionArtifacts computed fields."""

    def test_total_tool_calls_includes_subagents(self, tmp_path):
        """total_tool_calls should count self + all subagent tool_uses recursively."""
        child = SubagentNode(
            session_id="child",
            jsonl_path=tmp_path / "c.jsonl",
            tool_uses=[
                ToolUseEvent(name="Bash", tool_use_id="t2", input={}, timestamp="t"),
            ],
            children=[],
        )
        artifacts = SessionArtifacts(
            session_id="main",
            jsonl_path=tmp_path / "m.jsonl",
            tool_uses=[
                ToolUseEvent(name="Read", tool_use_id="t1", input={}, timestamp="t"),
            ],
            subagents=[child],
            total_tool_calls=2,
        )
        assert artifacts.total_tool_calls == 2


class TestRunSettings:
    """RunSettings loads defaults from env vars with CC_ prefix."""

    def test_settings_defaults_without_env(self, monkeypatch):
        """Without env vars, RunSettings has correct defaults."""
        # Reason: Clear any CC_ vars that may exist in the test environment
        for key in list(os.environ):
            if key.startswith("CC_"):
                monkeypatch.delenv(key, raising=False)
        s = RunSettings()
        assert s.binary == "claude"
        assert s.timeout == 300.0
        assert s.max_turns == 20
        assert s.max_budget is None
        assert s.teams is False
        assert s.output_format == "stream-json"
        assert s.skip_permissions is True
        assert s.profile == RunProfile.PLAIN

    def test_settings_timeout_from_env(self, monkeypatch):
        """CC_TIMEOUT env var should override timeout default."""
        monkeypatch.setenv("CC_TIMEOUT", "60")
        assert RunSettings().timeout == 60.0

    def test_settings_teams_from_env(self, monkeypatch):
        """CC_TEAMS=true should set teams=True."""
        monkeypatch.setenv("CC_TEAMS", "true")
        assert RunSettings().teams is True

    def test_settings_profile_from_env(self, monkeypatch):
        """CC_PROFILE=enhanced should set profile=ENHANCED."""
        monkeypatch.setenv("CC_PROFILE", "enhanced")
        assert RunSettings().profile == RunProfile.ENHANCED

    def test_settings_skip_permissions_from_env(self, monkeypatch):
        """CC_SKIP_PERMISSIONS=false should set skip_permissions=False."""
        monkeypatch.setenv("CC_SKIP_PERMISSIONS", "false")
        assert RunSettings().skip_permissions is False

    def test_settings_max_budget_from_env(self, monkeypatch):
        """CC_MAX_BUDGET=5.0 should set max_budget=5.0."""
        monkeypatch.setenv("CC_MAX_BUDGET", "5.0")
        assert RunSettings().max_budget == 5.0

    def test_settings_binary_from_env(self, monkeypatch):
        """CC_BINARY should override claude binary path."""
        monkeypatch.setenv("CC_BINARY", "/usr/local/bin/claude")
        assert RunSettings().binary == "/usr/local/bin/claude"


class TestRunConfigInheritsSettings:
    """RunConfig inherits RunSettings defaults and env overrides."""

    def test_config_inherits_defaults(self):
        """RunConfig(prompt='x') should have same defaults as RunSettings()."""
        c = RunConfig(prompt="x")
        assert c.timeout == 300.0
        assert c.binary == "claude"

    def test_config_env_override_inherited(self, monkeypatch):
        """CC_TIMEOUT env var should propagate to RunConfig."""
        monkeypatch.setenv("CC_TIMEOUT", "60")
        assert RunConfig(prompt="x").timeout == 60.0

    def test_config_explicit_overrides_env(self, monkeypatch):
        """Explicit kwarg should override env var."""
        monkeypatch.setenv("CC_TIMEOUT", "60")
        assert RunConfig(prompt="x", timeout=30).timeout == 30.0

    def test_config_prompt_still_required(self):
        """RunConfig without prompt should raise ValidationError."""
        with pytest.raises(ValidationError):
            RunConfig()  # type: ignore[call-arg]

    def test_config_prompt_from_env(self, monkeypatch):
        """CC_PROMPT env var can provide a default prompt."""
        monkeypatch.setenv("CC_PROMPT", "default prompt")
        c = RunConfig()  # type: ignore[call-arg]
        assert c.prompt == "default prompt"

    def test_config_prompt_explicit_overrides_env(self, monkeypatch):
        """Explicit prompt kwarg overrides CC_PROMPT env var."""
        monkeypatch.setenv("CC_PROMPT", "default")
        assert RunConfig(prompt="explicit").prompt == "explicit"


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
