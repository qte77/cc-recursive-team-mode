"""Prompt catalog loader — plain text files, no templating.

Loads prompts by name from a directory of ``.txt`` files.

Example:
    >>> from cc_recursive.prompts import load_prompt
    >>> prompt = load_prompt("validate")
    >>> print(prompt)
    Run make validate and report results
"""

from __future__ import annotations

from pathlib import Path

# Reason: Default prompts dir is at the repo root, not inside the package.
# This assumes the package is installed from the repo (editable or wheel with data).
_DEFAULT_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


def load_prompt(name: str, prompts_dir: Path | None = None) -> str:
    """Load a prompt by name from the prompts directory.

    Args:
        name: Prompt name (without .txt extension).
        prompts_dir: Directory to load from. Defaults to ``prompts/`` at repo root.

    Returns:
        Prompt text with leading/trailing whitespace stripped.

    Raises:
        FileNotFoundError: If the prompt file doesn't exist.
    """
    directory = prompts_dir or _DEFAULT_PROMPTS_DIR
    path = directory / f"{name}.txt"
    if not path.is_file():
        msg = f"Prompt not found: {path}"
        raise FileNotFoundError(msg)
    return path.read_text().strip()
