"""Tests for cc_recursive.prompts — prompt catalog loader.

Mock strategy: Uses real files in prompts/ and tests/prompts/ dirs.
"""

from pathlib import Path

import pytest

from cc_recursive.prompts import load_prompt

TESTS_PROMPTS_DIR = Path(__file__).parent / "prompts"


class TestLoadPrompt:
    """load_prompt() loads plain text prompts by name."""

    def test_load_prompt_by_name(self):
        """Should load validate.txt content from default prompts/ dir."""
        prompt = load_prompt("validate")
        assert prompt == "Run make validate and report results"

    def test_load_prompt_strips_whitespace(self):
        """Should strip trailing newlines from loaded prompt."""
        prompt = load_prompt("validate")
        assert not prompt.endswith("\n")

    def test_load_prompt_missing_raises(self):
        """Should raise FileNotFoundError for nonexistent prompt."""
        with pytest.raises(FileNotFoundError):
            load_prompt("nonexistent")

    def test_load_prompt_custom_dir(self):
        """Should load from custom dir when prompts_dir specified."""
        prompt = load_prompt("cheap", prompts_dir=TESTS_PROMPTS_DIR)
        assert prompt == "What is 2+2? Answer with just the number."
