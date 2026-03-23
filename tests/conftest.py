"""Shared fixtures for cc-recursive-team-mode tests.

All tests follow Arrange/Act/Assert with inline comments.
subprocess.run is always mocked; no real claude invocations.
"""

import json
import subprocess
from unittest.mock import MagicMock

import pytest

from cc_recursive.models import RunConfig

SAMPLE_STREAM_JSON_LINES = [
    json.dumps({"type": "system", "subtype": "init", "session_id": "sess-abc123"}),
    json.dumps(
        {
            "type": "assistant",
            "message": {"content": [{"type": "tool_use", "name": "Read"}]},
        }
    ),
    json.dumps(
        {
            "type": "result",
            "subtype": "success",
            "total_cost_usd": 0.003,
            "usage": {"input_tokens": 500, "output_tokens": 200},
            "num_turns": 2,
        }
    ),
]
SAMPLE_STREAM_JSON_OUTPUT = "\n".join(SAMPLE_STREAM_JSON_LINES)


@pytest.fixture
def sample_config():
    """RunConfig with typical values for runner tests."""
    return RunConfig(prompt="Summarize this repo.", timeout=60.0, max_turns=5)


@pytest.fixture
def sample_config_teams():
    """RunConfig with teams=True for teams-mode tests."""
    return RunConfig(prompt="Analyze src/.", teams=True)


@pytest.fixture
def mock_subprocess_success():
    """Mock subprocess.CompletedProcess simulating a successful claude run."""
    mock = MagicMock(spec=subprocess.CompletedProcess)
    mock.returncode = 0
    mock.stdout = SAMPLE_STREAM_JSON_OUTPUT
    mock.stderr = ""
    return mock


@pytest.fixture
def mock_subprocess_failure():
    """Mock subprocess.CompletedProcess simulating a failed claude run."""
    mock = MagicMock(spec=subprocess.CompletedProcess)
    mock.returncode = 1
    mock.stdout = ""
    mock.stderr = "claude: error message"
    return mock
