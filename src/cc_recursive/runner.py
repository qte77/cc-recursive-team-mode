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
import re
import subprocess
import time
from typing import Any

from cc_recursive.models import RunConfig, RunResult

# Reason: Denylist (not allowlist) because claude's required env vars vary by
# environment (Codespaces OAuth tokens, Node.js runtime, XDG paths, etc.) and
# cannot be reliably enumerated. An allowlist was tried first but broke auth in
# Codespaces. Since the child process has the same privilege level as the parent,
# full env inheritance minus CLAUDECODE is safe.
_CC_ENV_DENYLIST: frozenset[str] = frozenset({"CLAUDECODE"})

_TIMEOUT_EXIT_CODE = 124  # Matches bash `timeout` command convention

# Spawn-depth guard (cooperative: a process that unsets these variables, or calls claude
# directly, is not counted). Each spawn passes its depth to the child in DEPTH_ENV_VAR (absent =
# 0, the top-level caller) and its effective limit in MAX_DEPTH_ENV_VAR, so the limit binds the
# whole tree: a nested caller can lower it but not raise it. scripts/cc-recursive-team.sh uses
# the same variables and rules, so both entry points share one count.
DEPTH_ENV_VAR = "CC_RECURSIVE_DEPTH"
MAX_DEPTH_ENV_VAR = "CC_MAX_DEPTH"
# Returned, without starting claude, when a spawn would exceed the limit or an inherited value is
# malformed (fail closed). Distinct from 124 (timeout); claude itself is not known to exit 3.
DEPTH_EXCEEDED_EXIT_CODE = 3

# 1-9 ASCII digits: the same rule as the shell script (no sign, no spaces, no overflow).
_COUNT = re.compile(r"[0123456789]{1,9}")


def _env_count(name: str) -> int | None:
    """The env var as a count; -1 when it is set but malformed, None when unset."""
    raw = os.environ.get(name)
    if raw is None:
        return None
    return int(raw) if _COUNT.fullmatch(raw) else -1


def _depth_and_limit(config: RunConfig) -> tuple[int, int] | None:
    """(child depth, effective limit), or None when an inherited value is malformed."""
    inherited_depth = _env_count(DEPTH_ENV_VAR)
    inherited_limit = _env_count(MAX_DEPTH_ENV_VAR)
    if inherited_depth == -1 or inherited_limit == -1:
        return None
    limit = config.max_depth if inherited_limit is None else min(config.max_depth, inherited_limit)
    return (inherited_depth or 0) + 1, limit


def _build_env(config: RunConfig, depth: int, limit: int) -> dict[str, str]:
    """Build the subprocess environment dict from config.

    Args:
        config: RunConfig controlling env construction.
        depth: Spawn depth the child runs at.
        limit: Effective max depth, passed on so it binds the whole tree.

    Returns:
        Clean env dict for the subprocess.
    """
    env: dict[str, str] = {k: v for k, v in os.environ.items() if k not in _CC_ENV_DENYLIST}
    env[DEPTH_ENV_VAR] = str(depth)
    env[MAX_DEPTH_ENV_VAR] = str(limit)
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
        exit_code is DEPTH_EXCEEDED_EXIT_CODE, and claude is not started, when the spawn would
        go past the effective max depth (config.max_depth, lowered by an inherited CC_MAX_DEPTH)
        or an inherited depth or limit is malformed.
    """
    guard = _depth_and_limit(config)
    if guard is None or guard[0] > guard[1]:
        return RunResult(
            exit_code=DEPTH_EXCEEDED_EXIT_CODE,
            duration_s=0.0,
            tokens=0,
            cost_usd=0.0,
            tool_calls=[],
            raw_output="",
        )

    cmd = [config.binary]
    if config.skip_permissions:
        cmd.append("--dangerously-skip-permissions")
    cmd.extend(["-p", config.prompt, "--output-format", config.output_format])
    # Reason: stream-json requires --verbose in print mode
    if config.output_format == "stream-json":
        cmd.append("--verbose")
    cmd.extend(["--max-turns", str(config.max_turns)])
    depth, limit = guard
    env = _build_env(config, depth, limit)

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
