"""
MCP server exposing ctl client commands (requires elevated daemon: gsudo ctl -d).

See .cursor/mcp.json (workspace) or AGENTS.md (global ~/.cursor/mcp.json with uv --project).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from client_ops import (
    clear_logs,
    copy_dll,
    copy_logs,
    handler_commands,
    kill,
    launch,
    ping,
    processes,
    send,
    stages,
    status,
    wait_for_stage,
)
from client_rpc import DaemonNotRunningError
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "game-controller",
    instructions=(
        "FA-EMU game controller client. Requires the elevated ctl daemon "
        "(gsudo ctl -d or just daemon-bg). Does not start the daemon. "
        "Game path defaults to launch.yaml GAME_PATH unless game_exe is set."
    ),
)


def _format_result(result: dict) -> str:
    return json.dumps(result, indent=2)


def _run_tool(fn: Callable[..., dict], /, **kwargs: Any) -> str:
    try:
        return _format_result(fn(**kwargs))
    except DaemonNotRunningError as e:
        return _format_result({"status": "error", "error": str(e)})
    except (RuntimeError, ValueError, OSError) as e:
        return _format_result({"status": "error", "error": str(e)})


@mcp.tool()
def ctl_ping() -> str:
    """Check ctl daemon is running and elevated."""
    return _run_tool(ping)


@mcp.tool()
def ctl_processes() -> str:
    """List PIDs for GAME.exe and GameLauncher.exe."""
    return _run_tool(processes)


@mcp.tool()
def ctl_status() -> str:
    """Current session run_id, progress, and stages."""
    return _run_tool(status)


@mcp.tool()
def ctl_stages() -> str:
    """Known game stages and stages seen in the current session."""
    return _run_tool(stages)


@mcp.tool()
def ctl_wait_stage(stage: str, timeout: float = 120.0) -> str:
    """Block until the game reaches a diagnostics stage (e.g. server_ready, shard_choice)."""
    return _run_tool(wait_for_stage, stage=stage, timeout=timeout)


@mcp.tool()
def ctl_wait_menu(timeout: float = 120.0) -> str:
    """Block until game stage server_ready (alias for ctl_wait_stage)."""
    return _run_tool(wait_for_stage, stage="server_ready", timeout=timeout)


@mcp.tool()
def ctl_launch(
    server_ip: str = "",
    game_exe: str = "",
    env: str = "",
) -> str:
    """Clear shipping logs, fetch credentials, and start the game."""
    return _run_tool(
        launch,
        game_exe=game_exe or None,
        server_ip=server_ip or None,
        offline=False,
        proxy=False,
        env=env or None,
    )


@mcp.tool()
def ctl_launch_offline(
    server_ip: str = "127.0.0.1",
    game_exe: str = "",
    env: str = "",
) -> str:
    """Clear logs and launch with local entry + real auth (proxy mode; use with server proxy)."""
    return _run_tool(
        launch,
        game_exe=game_exe or None,
        server_ip=server_ip,
        offline=False,
        proxy=True,
        env=env or None,
    )


@mcp.tool()
def ctl_launch_dummy(
    server_ip: str = "127.0.0.1",
    game_exe: str = "",
    env: str = "",
) -> str:
    """Clear logs and launch with offline localhost token (no API auth)."""
    return _run_tool(
        launch,
        game_exe=game_exe or None,
        server_ip=server_ip,
        offline=True,
        proxy=False,
        env=env or None,
    )


@mcp.tool()
def ctl_kill() -> str:
    """Kill the tracked GAME.exe / launcher session."""
    return _run_tool(kill, all=False)


@mcp.tool()
def ctl_kill_all() -> str:
    """Kill all GAME.exe and GameLauncher.exe processes."""
    return _run_tool(kill, all=True)


@mcp.tool()
def ctl_relaunch(
    server_ip: str = "",
    game_exe: str = "",
    env: str = "",
) -> str:
    """Kill current session then launch (clear-logs + spawn)."""
    try:
        kill_result = kill(all=False)
        launch_result = launch(
            game_exe=game_exe or None,
            server_ip=server_ip or None,
            offline=False,
            proxy=False,
            env=env or None,
        )
        return _format_result({"kill": kill_result, "launch": launch_result})
    except DaemonNotRunningError as e:
        return _format_result({"status": "error", "error": str(e)})
    except (RuntimeError, ValueError, OSError) as e:
        return _format_result({"status": "error", "error": str(e)})


@mcp.tool()
def ctl_copy_dll(dll_config: str = "debug", game_exe: str = "") -> str:
    """Copy TheGame.dll next to GAME.exe (CMake preset or msvc-x86-* name)."""
    return _run_tool(
        copy_dll,
        dll_config=dll_config,
        game_exe=game_exe or None,
    )


@mcp.tool()
def ctl_clear_logs(game_exe: str = "") -> str:
    """Delete shipping log files next to GAME.exe (per ctl.yaml game_log_files)."""
    return _run_tool(clear_logs, game_exe=game_exe or None)


@mcp.tool()
def ctl_copy_logs(game_exe: str = "") -> str:
    """Copy shipping logs into logs/runs/<run_id>/ for the current session."""
    return _run_tool(copy_logs, game_exe=game_exe or None)


@mcp.tool()
def ctl_copy_logs_run(run_id: str, game_exe: str = "") -> str:
    """Copy shipping logs into logs/runs/<run_id>/ for a specific run."""
    return _run_tool(copy_logs, run_id=run_id, game_exe=game_exe or None)


@mcp.tool()
def ctl_commands() -> str:
    """List handler commands supported by the connected game (handler pipe)."""
    return _run_tool(handler_commands)


@mcp.tool()
def ctl_send(message: str) -> str:
    """Send a line-oriented command to the game on the handler pipe (must reply ok)."""
    return _run_tool(send, message=message)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
