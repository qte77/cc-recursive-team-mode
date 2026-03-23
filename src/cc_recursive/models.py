"""Pydantic models for cc-recursive-team-mode: RunConfig and RunResult.

Example:
    >>> from cc_recursive.models import RunConfig, RunResult
    >>> config = RunConfig(prompt="Summarize src/", timeout=60.0)
    >>> config.teams
    False
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class RunProfile(StrEnum):
    """CC execution profile controlling skills/rules/CLAUDE.md injection.

    Attributes:
        PLAIN: No .claude/, no CLAUDE.md — bare CC without agentic scaffolding.
        ENHANCED: Full project config: .claude/, skills, rules, CLAUDE.md.
    """

    PLAIN = "plain"
    ENHANCED = "enhanced"


class RunConfig(BaseModel):
    """Input configuration for a CC subprocess run.

    Attributes:
        prompt: Prompt passed to claude -p. Required, non-empty.
        timeout: Wall-clock timeout in seconds.
        max_turns: --max-turns flag value for claude.
        max_budget: USD cost cap; None means unlimited.
        teams: Whether to enable CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS.
        output_format: CC --output-format flag value.
    """

    prompt: str = Field(..., min_length=1, description="Prompt passed to claude -p")
    timeout: float = Field(default=300.0, gt=0, description="Wall-clock timeout in seconds")
    max_turns: int = Field(default=20, ge=1, description="--max-turns flag value")
    max_budget: float | None = Field(
        default=None, ge=0, description="USD budget cap; None = unlimited"
    )
    teams: bool = Field(default=False, description="Enable CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS")
    output_format: str = Field(default="stream-json", description="CC --output-format flag")
    skip_permissions: bool = Field(
        default=True, description="Pass --dangerously-skip-permissions for headless execution"
    )
    profile: RunProfile = Field(
        default=RunProfile.PLAIN,
        description="CC config profile: plain (bare) or enhanced (with .claude/)",
    )


class RunResult(BaseModel):
    """Output from a completed CC subprocess run.

    Attributes:
        exit_code: Subprocess exit code (0 = success).
        duration_s: Wall-clock execution time in seconds.
        tokens: Total tokens consumed (input + output).
        cost_usd: Estimated cost in USD from stream-json metadata.
        tool_calls: Names of tools invoked during the run.
        raw_output: Raw stream-json text for downstream parsing.
    """

    exit_code: int = Field(description="Subprocess exit code")
    duration_s: float = Field(ge=0.0, description="Wall-clock duration in seconds")
    tokens: int = Field(ge=0, description="Total tokens consumed")
    cost_usd: float = Field(ge=0.0, description="Estimated cost in USD")
    tool_calls: list[str] = Field(default_factory=list, description="Tool names invoked")
    raw_output: str = Field(default="", description="Raw stream-json stdout")


class ToolUseEvent(BaseModel):
    """A single tool invocation extracted from a CC session JSONL.

    Attributes:
        name: Tool name (e.g. "Read", "Bash", "Edit").
        tool_use_id: CC-assigned tool call ID ("toolu_...").
        input: Tool arguments as a dict.
        timestamp: ISO 8601 timestamp from the outer JSONL record.
    """

    name: str = Field(description="Tool name")
    tool_use_id: str = Field(description="Tool call ID")
    input: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    timestamp: str = Field(default="", description="ISO 8601 timestamp")


class SubagentNode(BaseModel):
    """A node in the subagent invocation tree.

    Attributes:
        session_id: Session UUID from the JSONL sessionId field.
        jsonl_path: Path to the subagent's JSONL file.
        tool_uses: Tool invocations in this subagent's session.
        children: Nested subagents spawned by this agent.
    """

    model_config = {"arbitrary_types_allowed": True}

    session_id: str = Field(description="Session UUID")
    jsonl_path: Path = Field(description="Path to JSONL file")
    tool_uses: list[ToolUseEvent] = Field(default_factory=list)
    children: list[SubagentNode] = Field(default_factory=list)


class SessionArtifacts(BaseModel):
    """Parsed artifacts from a CC session JSONL and its subagents.

    Attributes:
        session_id: Root session UUID.
        jsonl_path: Path to the root session JSONL file.
        tool_uses: Tool invocations in the root session.
        subagents: Subagent tree nodes.
        total_tool_calls: Total count across root + all subagents.
    """

    model_config = {"arbitrary_types_allowed": True}

    session_id: str = Field(description="Root session UUID")
    jsonl_path: Path = Field(description="Path to root JSONL file")
    tool_uses: list[ToolUseEvent] = Field(default_factory=list)
    subagents: list[SubagentNode] = Field(default_factory=list)
    total_tool_calls: int = Field(ge=0, description="Total tool calls across all agents")
