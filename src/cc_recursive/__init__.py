"""cc-recursive-team-mode: Recursive Claude Code subprocess spawning.

Public API:
    run: Invoke claude -p as a subprocess and return a RunResult.
    RunConfig: Input configuration model.
    RunResult: Output result model.
"""

from cc_recursive.artifact_parser import parse_session
from cc_recursive.models import (
    RunConfig,
    RunProfile,
    RunResult,
    SessionArtifacts,
    SubagentNode,
    ToolUseEvent,
)
from cc_recursive.runner import run

__all__ = [
    "parse_session",
    "run",
    "RunConfig",
    "RunProfile",
    "RunResult",
    "SessionArtifacts",
    "SubagentNode",
    "ToolUseEvent",
]
__version__ = "0.1.0"
