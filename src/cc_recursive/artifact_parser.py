"""CC session artifact parser — JSONL extraction, subagent trees.

Parses ``~/.claude/projects/{slug}/{session}.jsonl`` files to extract
tool_use events and reconstruct subagent invocation trees.

Example:
    >>> from cc_recursive.artifact_parser import parse_session
    >>> from pathlib import Path
    >>> artifacts = parse_session(Path("~/.claude/projects/-my-project/abc.jsonl"))
    >>> artifacts.total_tool_calls
    15
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cc_recursive.models import SessionArtifacts, SubagentNode, ToolUseEvent


def find_session_jsonl(project_dir: Path, after: float | None = None) -> Path | None:
    """Find the most recent session JSONL in a project directory.

    Args:
        project_dir: Path to ``~/.claude/projects/{slug}/``.
        after: If set, only consider files with mtime >= this unix timestamp.

    Returns:
        Path to the most recent JSONL, or None if none found.
    """
    jsonls = [f for f in project_dir.glob("*.jsonl") if f.is_file()]
    if after is not None:
        jsonls = [f for f in jsonls if f.stat().st_mtime >= after]
    if not jsonls:
        return None
    return max(jsonls, key=lambda f: f.stat().st_mtime)


def extract_tool_uses(jsonl_path: Path) -> list[ToolUseEvent]:
    """Extract tool_use blocks from assistant messages in a session JSONL.

    Args:
        jsonl_path: Path to a CC session JSONL file.

    Returns:
        List of ToolUseEvent extracted from assistant messages.
    """
    events: list[ToolUseEvent] = []
    text = jsonl_path.read_text()
    if not text.strip():
        return events

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            record: dict[str, Any] = json.loads(stripped)
        except json.JSONDecodeError:
            continue

        if record.get("type") != "assistant":
            continue

        timestamp = record.get("timestamp", "")
        message = record.get("message", {})
        for block in message.get("content", []):
            if isinstance(block, dict) and block.get("type") == "tool_use":
                events.append(
                    ToolUseEvent(
                        name=block.get("name", ""),
                        tool_use_id=block.get("id", ""),
                        input=block.get("input", {}),
                        timestamp=timestamp,
                    )
                )

    return events


def find_subagents(session_jsonl: Path) -> list[Path]:
    """Find subagent JSONL files for a given session.

    Subagents are stored at ``{session_uuid}/subagents/agent-*.jsonl``
    relative to the session JSONL's parent directory.

    Args:
        session_jsonl: Path to the parent session's JSONL file.

    Returns:
        List of Paths to subagent JSONL files.
    """
    session_uuid = session_jsonl.stem
    subagent_dir = session_jsonl.parent / session_uuid / "subagents"
    if not subagent_dir.is_dir():
        return []
    return sorted(subagent_dir.glob("agent-*.jsonl"))


def _extract_session_id(jsonl_path: Path) -> str:
    """Extract sessionId from the first record that has one.

    Args:
        jsonl_path: Path to a JSONL file.

    Returns:
        Session ID string, or the file stem as fallback.
    """
    for line in jsonl_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            record: dict[str, Any] = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        session_id = record.get("sessionId")
        if session_id:
            return str(session_id)
    return jsonl_path.stem


def _count_tool_uses(node_tool_uses: list[ToolUseEvent], children: list[SubagentNode]) -> int:
    """Count total tool uses across a node and all its children recursively."""
    total = len(node_tool_uses)
    for child in children:
        total += _count_tool_uses(child.tool_uses, child.children)
    return total


def parse_session(jsonl_path: Path) -> SessionArtifacts:
    """Parse a session JSONL into full SessionArtifacts with subagent tree.

    Args:
        jsonl_path: Path to the root session JSONL file.

    Returns:
        SessionArtifacts with tool_uses, subagents, and total_tool_calls.
    """
    session_id = _extract_session_id(jsonl_path)
    tool_uses = extract_tool_uses(jsonl_path)

    subagent_paths = find_subagents(jsonl_path)
    subagents: list[SubagentNode] = []
    for sub_path in subagent_paths:
        sub_tool_uses = extract_tool_uses(sub_path)
        sub_children_paths = find_subagents(sub_path)
        # Reason: Recursive subagent nesting is rare but possible in teams mode
        sub_children = [
            SubagentNode(
                session_id=_extract_session_id(p),
                jsonl_path=p,
                tool_uses=extract_tool_uses(p),
                children=[],
            )
            for p in sub_children_paths
        ]
        subagents.append(
            SubagentNode(
                session_id=_extract_session_id(sub_path),
                jsonl_path=sub_path,
                tool_uses=sub_tool_uses,
                children=sub_children,
            )
        )

    total = _count_tool_uses(tool_uses, subagents)

    return SessionArtifacts(
        session_id=session_id,
        jsonl_path=jsonl_path,
        tool_uses=tool_uses,
        subagents=subagents,
        total_tool_calls=total,
    )
