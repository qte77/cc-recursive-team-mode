"""Tests for scripts/cc-recursive-team.sh.

Mock strategy: No subprocess execution — file system checks only.
"""

import os
import stat
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "cc-recursive-team.sh"


class TestShellScriptExists:
    """Shell script is present at the expected location."""

    def test_script_file_exists(self):
        """Given the repo, should find cc-recursive-team.sh."""
        assert SCRIPT_PATH.exists(), f"Script not found at {SCRIPT_PATH}"

    def test_script_is_executable(self):
        """Given the script file, should have executable bit set."""
        mode = os.stat(SCRIPT_PATH).st_mode
        assert mode & stat.S_IXUSR, "Script owner execute bit not set"

    def test_script_has_bash_shebang(self):
        """Given the script file, first line should be a bash shebang."""
        first_line = SCRIPT_PATH.read_text().splitlines()[0]
        assert first_line.startswith("#!/"), f"No shebang found: {first_line!r}"
        assert "bash" in first_line, f"Non-bash shebang: {first_line!r}"
