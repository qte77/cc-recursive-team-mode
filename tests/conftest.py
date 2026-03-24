"""Shared fixtures for cc-recursive-team-mode tests.

All tests follow Arrange/Act/Assert with inline comments.
subprocess.run is always mocked; no real claude invocations.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from cc_recursive.models import RunConfig, RunProfile
from cc_recursive.prompts import load_prompt

_TESTS_PROMPTS_DIR = Path(__file__).parent / "prompts"

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
    return RunConfig(prompt=load_prompt("validate"), timeout=60.0, max_turns=5)


@pytest.fixture
def sample_config_teams():
    """RunConfig with teams=True for teams-mode tests."""
    return RunConfig(prompt=load_prompt("review"), teams=True)


@pytest.fixture
def sample_config_enhanced():
    """RunConfig with ENHANCED profile."""
    return RunConfig(prompt=load_prompt("review"), profile=RunProfile.ENHANCED)


@pytest.fixture
def sample_config_no_skip():
    """RunConfig with skip_permissions=False."""
    return RunConfig(prompt=load_prompt("validate"), skip_permissions=False)


SAMPLE_SESSION_JSONL_LINES = [
    json.dumps(
        {
            "type": "system",
            "subtype": "init",
            "sessionId": "sess-main-001",
            "timestamp": "2026-03-23T10:00:00.000Z",
        }
    ),
    json.dumps(
        {
            "type": "assistant",
            "message": {
                "id": "msg_01",
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_read1",
                        "name": "Read",
                        "input": {"file_path": "/src/main.py"},
                    }
                ],
                "stop_reason": "tool_use",
            },
            "uuid": "uuid-1",
            "timestamp": "2026-03-23T10:00:01.000Z",
            "sessionId": "sess-main-001",
        }
    ),
    json.dumps(
        {
            "type": "user",
            "message": {"role": "user", "content": [{"type": "tool_result", "content": "ok"}]},
            "uuid": "uuid-2",
            "timestamp": "2026-03-23T10:00:02.000Z",
        }
    ),
    json.dumps(
        {
            "type": "assistant",
            "message": {
                "id": "msg_02",
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_bash1",
                        "name": "Bash",
                        "input": {"command": "make test"},
                    }
                ],
                "stop_reason": "tool_use",
            },
            "uuid": "uuid-3",
            "timestamp": "2026-03-23T10:00:03.000Z",
            "sessionId": "sess-main-001",
        }
    ),
    json.dumps(
        {
            "type": "result",
            "subtype": "success",
            "total_cost_usd": 0.05,
            "usage": {"input_tokens": 1000, "output_tokens": 500},
        }
    ),
]
SAMPLE_SESSION_JSONL = "\n".join(SAMPLE_SESSION_JSONL_LINES)


@pytest.fixture
def session_jsonl_file(tmp_path):
    """Write sample session JSONL to tmp_path, return Path."""
    f = tmp_path / "sess-main-001.jsonl"
    f.write_text(SAMPLE_SESSION_JSONL)
    return f


@pytest.fixture
def mock_claude_project_dir(tmp_path):
    """Create a mock ~/.claude/projects/{slug}/ with session files and subagent."""
    project_dir = tmp_path / "-project-slug"
    project_dir.mkdir()

    # Older session
    old = project_dir / "old-session-uuid.jsonl"
    old.write_text(SAMPLE_SESSION_JSONL_LINES[0] + "\n")

    # Newer session
    new = project_dir / "new-session-uuid.jsonl"
    new.write_text(SAMPLE_SESSION_JSONL)

    # Subagent for the newer session
    subagent_dir = project_dir / "new-session-uuid" / "subagents"
    subagent_dir.mkdir(parents=True)
    subagent = subagent_dir / "agent-abc123def456.jsonl"
    subagent_jsonl = json.dumps(
        {
            "type": "assistant",
            "message": {
                "id": "msg_sub",
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_sub1",
                        "name": "Grep",
                        "input": {"pattern": "TODO"},
                    }
                ],
                "stop_reason": "tool_use",
            },
            "uuid": "uuid-sub",
            "timestamp": "2026-03-23T10:01:00.000Z",
            "sessionId": "sess-sub-001",
        }
    )
    subagent.write_text(subagent_jsonl)

    return project_dir


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
