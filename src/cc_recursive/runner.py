"""Python wrapper for recursive Claude Code subprocess invocation.

Clears the CLAUDECODE guard variable, applies env allowlist filtering,
invokes ``claude -p`` via subprocess.run, parses stream-json output, and
returns a typed RunResult.

Example:
    >>> from cc_recursive import run, RunConfig
    >>> result = run(RunConfig(prompt="hello", timeout=30.0))
    >>> result.exit_code
    0
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from typing import Any

from cc_recursive.models import RunConfig, RunResult

# Reason: Denylist approach — child claude inherits parent env (same privilege level)
# but CLAUDECODE must be removed for recursive spawning to work.
_CC_ENV_DENYLIST: frozenset[str] = frozenset({"CLAUDECODE"})

_TIMEOUT_EXIT_CODE = 124  # Matches bash `timeout` command convention


def _build_env(config: RunConfig) -> dict[str, str]:
    """Build the subprocess environment dict from config.

    Args:
        config: RunConfig controlling env construction.

    Returns:
        Clean env dict for the subprocess.
    """
    env: dict[str, str] = {k: v for k, v in os.environ.items() if k not in _CC_ENV_DENYLIST}
    if config.teams:
        env["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"
    else:
        env.pop("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", None)
    return env


def _parse_stream_json(stdout: str) -> tuple[int, float, list[str]]:
    """Extract tokens, cost_usd, and tool_calls from stream-json stdout.

    Args:
        stdout: Raw stream-json text from CC subprocess stdout.

    Returns:
        Tuple of (tokens, cost_usd, tool_calls).
    """
    tokens = 0
    cost_usd = 0.0
    tool_calls: list[str] = []

    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            event: dict[str, Any] = json.loads(stripped)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type", "")

        if event_type == "result":
            cost_usd = float(event.get("total_cost_usd", 0.0))
            usage = event.get("usage", {})
            tokens = int(usage.get("input_tokens", 0)) + int(usage.get("output_tokens", 0))
        elif event_type == "assistant":
            message = event.get("message", {})
            for block in message.get("content", []):
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    name = block.get("name")
                    if name:
                        tool_calls.append(str(name))

    return tokens, cost_usd, tool_calls


def run(config: RunConfig) -> RunResult:
    """Invoke claude -p as a subprocess, parse output, return RunResult.

    Args:
        config: RunConfig specifying prompt, timeout, teams mode, etc.

    Returns:
        RunResult with exit_code, duration_s, tokens, cost_usd, tool_calls, raw_output.
    """
    cmd = ["claude"]
    if config.skip_permissions:
        cmd.append("--dangerously-skip-permissions")
    cmd.extend(["-p", config.prompt, "--output-format", config.output_format])
    # Reason: stream-json requires --verbose in print mode
    if config.output_format == "stream-json":
        cmd.append("--verbose")
    cmd.extend(["--max-turns", str(config.max_turns)])
    env = _build_env(config)

    start = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=config.timeout,
        )
        duration_s = time.perf_counter() - start
        exit_code = proc.returncode
        raw_output = proc.stdout or ""
    except subprocess.TimeoutExpired:
        duration_s = time.perf_counter() - start
        return RunResult(
            exit_code=_TIMEOUT_EXIT_CODE,
            duration_s=duration_s,
            tokens=0,
            cost_usd=0.0,
            tool_calls=[],
            raw_output="",
        )

    tokens, cost_usd, tool_calls = _parse_stream_json(raw_output)
    return RunResult(
        exit_code=exit_code,
        duration_s=duration_s,
        tokens=tokens,
        cost_usd=cost_usd,
        tool_calls=tool_calls,
        raw_output=raw_output,
    )
