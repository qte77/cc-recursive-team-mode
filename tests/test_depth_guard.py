"""Tests for the recursive spawn-depth guard (docs/TODO.md backlog: "Depth control").

Each spawn passes its depth to the child in CC_RECURSIVE_DEPTH (absent = 0, the top-level
caller). A spawn that would go past the maximum depth is refused with DEPTH_EXCEEDED_EXIT_CODE and
never starts claude. Both entry points share the env var, so the depth survives run() and the shell
script in either order.

Mock strategy: run() tests patch subprocess.run. The shell-script tests run the real script with a
stub `claude` on PATH that only prints the depth it received; no real claude calls.
"""

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from cc_recursive.models import RunConfig
from cc_recursive.runner import DEPTH_ENV_VAR, DEPTH_EXCEEDED_EXIT_CODE, run

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "cc-recursive-team.sh"


def _env_without_depth() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in (DEPTH_ENV_VAR, "CC_MAX_DEPTH")}


class TestRunDepthGuard:
    """run() passes depth + 1 to the child and refuses to spawn past max_depth."""

    def test_top_level_run_passes_depth_one(self, sample_config, mock_subprocess_success):
        """Given no depth in the env, the child should get depth 1."""
        with patch.dict(os.environ, _env_without_depth(), clear=True):
            with patch(
                "cc_recursive.runner.subprocess.run", return_value=mock_subprocess_success
            ) as mock_run:
                run(sample_config)
        assert mock_run.call_args[1]["env"][DEPTH_ENV_VAR] == "1"

    def test_nested_run_increments_depth(self, sample_config, mock_subprocess_success):
        """Given depth 1 in the env (a child of a guarded spawn), the grandchild should get 2."""
        with patch.dict(os.environ, {DEPTH_ENV_VAR: "1"}):
            with patch(
                "cc_recursive.runner.subprocess.run", return_value=mock_subprocess_success
            ) as mock_run:
                run(sample_config)
        assert mock_run.call_args[1]["env"][DEPTH_ENV_VAR] == "2"

    def test_run_refuses_past_max_depth_without_spawning(self, mock_subprocess_success):
        """Given depth == max_depth, should return the depth exit code and never call claude."""
        config = RunConfig(prompt="hello", max_depth=2)
        with patch.dict(os.environ, {DEPTH_ENV_VAR: "2"}):
            with patch(
                "cc_recursive.runner.subprocess.run", return_value=mock_subprocess_success
            ) as mock_run:
                result = run(config)
        mock_run.assert_not_called()
        assert result.exit_code == DEPTH_EXCEEDED_EXIT_CODE
        assert result.tokens == 0

    @pytest.mark.parametrize("bad", ["abc", "-1", "1.5", ""])
    def test_run_fails_closed_on_malformed_depth(self, bad, sample_config, mock_subprocess_success):
        """Given a depth value that is not a non-negative integer, should refuse rather than guess."""
        with patch.dict(os.environ, {DEPTH_ENV_VAR: bad}):
            with patch(
                "cc_recursive.runner.subprocess.run", return_value=mock_subprocess_success
            ) as mock_run:
                result = run(sample_config)
        mock_run.assert_not_called()
        assert result.exit_code == DEPTH_EXCEEDED_EXIT_CODE

    def test_exit_code_is_distinct_from_timeout(self):
        """The depth exit code must not collide with the timeout code (124) or success/error."""
        assert DEPTH_EXCEEDED_EXIT_CODE not in (0, 1, 124)


@pytest.fixture
def stub_claude(tmp_path):
    """A fake `claude` on PATH that prints the depth it was started with."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "claude"
    stub.write_text(f'#!/usr/bin/env bash\necho "depth=${{{DEPTH_ENV_VAR}:-unset}}"\n')
    stub.chmod(0o755)
    return bin_dir


def _run_script(stub_dir: Path, extra_env: dict[str, str], *args: str):
    env = _env_without_depth()
    env["PATH"] = f"{stub_dir}{os.pathsep}{env.get('PATH', '')}"
    env.update(extra_env)
    return subprocess.run(
        ["bash", str(SCRIPT_PATH), "--prompt", "hi", "--timeout", "10", *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


class TestShellScriptDepthGuard:
    """scripts/cc-recursive-team.sh applies the same guard through the same env var."""

    def test_top_level_script_passes_depth_one(self, stub_claude):
        proc = _run_script(stub_claude, {})
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.strip() == "depth=1"

    def test_script_continues_a_run_spawned_depth(self, stub_claude):
        """Given depth 1 set by run() (Python path), the script should pass depth 2 on."""
        proc = _run_script(stub_claude, {DEPTH_ENV_VAR: "1"})
        assert proc.stdout.strip() == "depth=2"

    def test_script_refuses_past_max_depth(self, stub_claude):
        proc = _run_script(stub_claude, {DEPTH_ENV_VAR: "2", "CC_MAX_DEPTH": "2"})
        assert proc.returncode == DEPTH_EXCEEDED_EXIT_CODE
        assert "depth" in proc.stderr.lower()
        assert proc.stdout == ""

    def test_script_max_depth_flag_overrides_env(self, stub_claude):
        proc = _run_script(
            stub_claude, {DEPTH_ENV_VAR: "1", "CC_MAX_DEPTH": "5"}, "--max-depth", "1"
        )
        assert proc.returncode == DEPTH_EXCEEDED_EXIT_CODE

    def test_script_fails_closed_on_malformed_depth(self, stub_claude):
        proc = _run_script(stub_claude, {DEPTH_ENV_VAR: "abc"})
        assert proc.returncode == DEPTH_EXCEEDED_EXIT_CODE
        assert proc.stdout == ""
