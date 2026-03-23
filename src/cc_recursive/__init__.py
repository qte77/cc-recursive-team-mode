"""cc-recursive-team-mode: Recursive Claude Code subprocess spawning.

Public API:
    run: Invoke claude -p as a subprocess and return a RunResult.
    RunConfig: Input configuration model.
    RunResult: Output result model.
"""

from cc_recursive.models import RunConfig, RunProfile, RunResult
from cc_recursive.runner import run

__all__ = ["run", "RunConfig", "RunProfile", "RunResult"]
__version__ = "0.1.0"
