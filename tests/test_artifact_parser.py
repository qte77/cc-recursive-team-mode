"""Tests for cc_recursive.artifact_parser — session JSONL parsing.

Mock strategy: All tests use tmp_path fixtures. No real ~/.claude/ access.
"""


from cc_recursive.artifact_parser import (
    extract_tool_uses,
    find_session_jsonl,
    find_subagents,
    parse_session,
)


class TestExtractToolUses:
    """extract_tool_uses() extracts tool_use blocks from session JSONL."""

    def test_extracts_tool_names(self, session_jsonl_file):
        """Should extract Read and Bash tool names."""
        events = extract_tool_uses(session_jsonl_file)
        names = [e.name for e in events]
        assert names == ["Read", "Bash"]

    def test_extracts_tool_use_ids(self, session_jsonl_file):
        """Each event should have a toolu_ prefixed id."""
        events = extract_tool_uses(session_jsonl_file)
        assert all(e.tool_use_id.startswith("toolu_") for e in events)

    def test_extracts_tool_inputs(self, session_jsonl_file):
        """Each event should have an input dict."""
        events = extract_tool_uses(session_jsonl_file)
        assert events[0].input == {"file_path": "/src/main.py"}
        assert events[1].input == {"command": "make test"}

    def test_extracts_timestamps(self, session_jsonl_file):
        """Each event should have a timestamp from the outer record."""
        events = extract_tool_uses(session_jsonl_file)
        assert events[0].timestamp == "2026-03-23T10:00:01.000Z"
        assert events[1].timestamp == "2026-03-23T10:00:03.000Z"

    def test_skips_non_assistant_lines(self, session_jsonl_file):
        """Should not extract from system, user, or result lines."""
        events = extract_tool_uses(session_jsonl_file)
        # Only 2 tool_use blocks exist (in assistant messages)
        assert len(events) == 2

    def test_handles_empty_file(self, tmp_path):
        """Empty JSONL file should return empty list."""
        f = tmp_path / "empty.jsonl"
        f.write_text("")
        assert extract_tool_uses(f) == []

    def test_handles_malformed_json(self, tmp_path):
        """Should skip bad lines and return valid ones."""
        import json

        content = "not json\n" + json.dumps(
            {
                "type": "assistant",
                "message": {
                    "content": [{"type": "tool_use", "id": "toolu_x", "name": "Edit", "input": {}}],
                    "stop_reason": "tool_use",
                },
                "timestamp": "t",
            }
        )
        f = tmp_path / "malformed.jsonl"
        f.write_text(content)
        events = extract_tool_uses(f)
        assert len(events) == 1
        assert events[0].name == "Edit"


class TestFindSessionJsonl:
    """find_session_jsonl() locates the most recent session file."""

    def test_finds_most_recent(self, mock_claude_project_dir):
        """Should return the newer JSONL file."""
        result = find_session_jsonl(mock_claude_project_dir)
        assert result is not None
        assert result.name == "new-session-uuid.jsonl"

    def test_filters_by_mtime(self, mock_claude_project_dir):
        """With after= param set to future, should return None."""
        import time

        result = find_session_jsonl(mock_claude_project_dir, after=time.time() + 9999)
        assert result is None

    def test_returns_none_empty_dir(self, tmp_path):
        """No JSONLs in dir should return None."""
        empty = tmp_path / "empty-project"
        empty.mkdir()
        assert find_session_jsonl(empty) is None


class TestFindSubagents:
    """find_subagents() finds subagent JSONL files for a session."""

    def test_finds_subagent_files(self, mock_claude_project_dir):
        """Should find the subagent JSONL."""
        session = mock_claude_project_dir / "new-session-uuid.jsonl"
        subs = find_subagents(session)
        assert len(subs) == 1
        assert "agent-abc123def456" in subs[0].name

    def test_no_subagents_dir(self, mock_claude_project_dir):
        """Session without subagents dir should return empty list."""
        session = mock_claude_project_dir / "old-session-uuid.jsonl"
        assert find_subagents(session) == []


class TestParseSession:
    """parse_session() builds full SessionArtifacts with subagent tree."""

    def test_parses_full_session(self, mock_claude_project_dir):
        """Should return SessionArtifacts with tool_uses and subagents."""
        session = mock_claude_project_dir / "new-session-uuid.jsonl"
        artifacts = parse_session(session)
        assert artifacts.session_id == "sess-main-001"
        assert len(artifacts.tool_uses) == 2
        assert len(artifacts.subagents) == 1

    def test_total_tool_calls_includes_subagents(self, mock_claude_project_dir):
        """total_tool_calls should count root (2) + subagent (1) = 3."""
        session = mock_claude_project_dir / "new-session-uuid.jsonl"
        artifacts = parse_session(session)
        assert artifacts.total_tool_calls == 3

    def test_session_without_subagents(self, session_jsonl_file):
        """Session with no subagents dir should have empty subagents list."""
        artifacts = parse_session(session_jsonl_file)
        assert artifacts.subagents == []
        assert artifacts.total_tool_calls == 2
