"""Tests for cc_recursive.runner — run() function.

Mock strategy: subprocess.run is always patched. No real claude CLI calls.
"""

import os
import subprocess
from unittest.mock import patch

from cc_recursive.runner import run


class TestRunEnvFiltering:
    """run() builds a clean subprocess env that excludes credentials."""

    def test_run_removes_claudecode_from_env(self, sample_config, mock_subprocess_success):
        """Given CLAUDECODE in process env, should not appear in subprocess env."""
        # Arrange / Act
        with patch.dict(os.environ, {"CLAUDECODE": "1"}):
            with patch(
                "cc_recursive.runner.subprocess.run", return_value=mock_subprocess_success
            ) as mock_run:
                run(sample_config)
        # Assert
        env = mock_run.call_args[1]["env"]
        assert "CLAUDECODE" not in env

    def test_run_sets_teams_env_when_enabled(self, sample_config_teams, mock_subprocess_success):
        """Given teams=True, should set CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1."""
        with patch(
            "cc_recursive.runner.subprocess.run", return_value=mock_subprocess_success
        ) as mock_run:
            run(sample_config_teams)
        env = mock_run.call_args[1]["env"]
        assert env.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") == "1"

    def test_run_does_not_set_teams_env_when_disabled(self, sample_config, mock_subprocess_success):
        """Given teams=False, should not set teams env var."""
        with patch(
            "cc_recursive.runner.subprocess.run", return_value=mock_subprocess_success
        ) as mock_run:
            run(sample_config)
        env = mock_run.call_args[1]["env"]
        assert "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS" not in env

    def test_run_env_excludes_non_allowlist_vars(self, sample_config, mock_subprocess_success):
        """Given arbitrary env vars, should exclude non-allowlist vars."""
        with patch.dict(os.environ, {"MY_SECRET_TOKEN": "hunter2"}):
            with patch(
                "cc_recursive.runner.subprocess.run", return_value=mock_subprocess_success
            ) as mock_run:
                run(sample_config)
        env = mock_run.call_args[1]["env"]
        assert "MY_SECRET_TOKEN" not in env

    def test_run_env_includes_approved_claude_code_vars(
        self, sample_config, mock_subprocess_success
    ):
        """Given approved CLAUDE_CODE_* vars, should pass them through."""
        with patch.dict(os.environ, {"CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"}):
            with patch(
                "cc_recursive.runner.subprocess.run", return_value=mock_subprocess_success
            ) as mock_run:
                run(sample_config)
        env = mock_run.call_args[1]["env"]
        assert env.get("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC") == "1"


class TestRunSubprocessArgs:
    """run() passes correct CLI arguments to claude."""

    def test_run_passes_correct_args(self, sample_config, mock_subprocess_success):
        """Given RunConfig, should invoke claude with correct flags."""
        with patch(
            "cc_recursive.runner.subprocess.run", return_value=mock_subprocess_success
        ) as mock_run:
            run(sample_config)
        cmd = mock_run.call_args[0][0]
        assert "claude" in cmd[0]
        assert "-p" in cmd
        assert sample_config.prompt in cmd
        assert "--output-format" in cmd
        assert "stream-json" in cmd
        assert "--max-turns" in cmd
        assert str(sample_config.max_turns) in cmd

    def test_run_passes_timeout_to_subprocess(self, sample_config, mock_subprocess_success):
        """Given timeout in RunConfig, should pass timeout to subprocess.run."""
        with patch(
            "cc_recursive.runner.subprocess.run", return_value=mock_subprocess_success
        ) as mock_run:
            run(sample_config)
        assert mock_run.call_args[1].get("timeout") == sample_config.timeout


class TestRunOutputParsing:
    """run() parses stream-json stdout into RunResult fields."""

    def test_run_parses_tokens_and_cost(self, sample_config, mock_subprocess_success):
        """Given stream-json with result event, should extract tokens and cost."""
        with patch("cc_recursive.runner.subprocess.run", return_value=mock_subprocess_success):
            result = run(sample_config)
        assert result.tokens == 700  # 500 input + 200 output
        assert result.cost_usd == 0.003

    def test_run_captures_tool_calls(self, sample_config, mock_subprocess_success):
        """Given stream-json with tool_use events, should capture tool names."""
        with patch("cc_recursive.runner.subprocess.run", return_value=mock_subprocess_success):
            result = run(sample_config)
        assert "Read" in result.tool_calls

    def test_run_captures_duration(self, sample_config, mock_subprocess_success):
        """Given a completed run, duration_s should be a positive float."""
        with patch("cc_recursive.runner.subprocess.run", return_value=mock_subprocess_success):
            result = run(sample_config)
        assert result.duration_s > 0.0

    def test_run_captures_raw_output(self, sample_config, mock_subprocess_success):
        """Given stream-json stdout, raw_output should contain the stdout."""
        with patch("cc_recursive.runner.subprocess.run", return_value=mock_subprocess_success):
            result = run(sample_config)
        assert result.raw_output == mock_subprocess_success.stdout


class TestRunErrorHandling:
    """run() handles error conditions without raising."""

    def test_run_handles_timeout(self, sample_config):
        """Given subprocess.TimeoutExpired, should return RunResult with exit_code=124."""
        with patch(
            "cc_recursive.runner.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["claude"], timeout=60.0),
        ):
            result = run(sample_config)
        assert result.exit_code == 124

    def test_run_handles_nonzero_exit(self, sample_config, mock_subprocess_failure):
        """Given subprocess exit_code=1, should forward exit_code=1."""
        with patch("cc_recursive.runner.subprocess.run", return_value=mock_subprocess_failure):
            result = run(sample_config)
        assert result.exit_code == 1
