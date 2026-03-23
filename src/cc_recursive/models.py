"""Pydantic models for cc-recursive-team-mode: RunConfig and RunResult.

Example:
    >>> from cc_recursive.models import RunConfig, RunResult
    >>> config = RunConfig(prompt="Summarize src/", timeout=60.0)
    >>> config.teams
    False
"""

from __future__ import annotations

from enum import StrEnum

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
