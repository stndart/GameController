"""
MCP server exposing ctl client commands (requires elevated daemon: gsudo ctl -d).

Tool surface mirrors `just` recipes in the repo root justfile (see AGENTS.md).
Daemon/stop are intentionally omitted.
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
    relaunch,
    send,
    stages,
    status,
    wait_for_stage,
    wait_lobby,
)
from client_rpc import DaemonNotRunningError
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "game-controller",
    instructions=(
        "FA-EMU game controller client. Requires the elevated ctl daemon "
        "(gsudo ctl -d or just daemon-bg). Does not start the daemon. "
        "Game path defaults to launch.yaml GAME_PATH unless game_exe is set. "
        "MCP tools match `just` recipes in this repo (ctl_* names)."
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
    """Check ctl daemon is running and elevated (`just ping`)."""
    return _run_tool(ping)


@mcp.tool()
def ctl_processes() -> str:
    """List PIDs for GAME.exe and GameLauncher.exe (`just processes`)."""
    return _run_tool(processes)


@mcp.tool()
def ctl_status() -> str:
    """Current session run_id, progress, and stages (`just status`)."""
    return _run_tool(status)


@mcp.tool()
def ctl_stages() -> str:
    """Known game stages and stages seen in the current session (`just stages`)."""
    return _run_tool(stages)


@mcp.tool()
def ctl_kill() -> str:
    """Kill the tracked GAME.exe / launcher session (`just kill`)."""
    return _run_tool(kill, all=False)


@mcp.tool()
def ctl_kill_all() -> str:
    """Kill all GAME.exe and GameLauncher.exe processes (`just kill-all`)."""
    return _run_tool(kill, all=True)


@mcp.tool()
def ctl_copy_dll(dll_config: str = "debug", game_exe: str = "") -> str:
    """Copy TheGame.dll next to GAME.exe (`just copy-dll`)."""
    return _run_tool(
        copy_dll,
        dll_config=dll_config,
        game_exe=game_exe or None,
    )


@mcp.tool()
def ctl_clear_logs(game_exe: str = "") -> str:
    """Delete shipping log files next to GAME.exe (`just clear-logs`)."""
    return _run_tool(clear_logs, game_exe=game_exe or None)


@mcp.tool()
def ctl_copy_logs(game_exe: str = "") -> str:
    """Copy shipping logs into logs/runs/<run_id>/ (`just copy-logs`)."""
    return _run_tool(copy_logs, game_exe=game_exe or None)


@mcp.tool()
def ctl_copy_logs_run(run_id: str, game_exe: str = "") -> str:
    """Copy shipping logs into logs/runs/<run_id>/ for a specific run (`just copy-logs-run`)."""
    return _run_tool(copy_logs, run_id=run_id, game_exe=game_exe or None)


@mcp.tool()
def ctl_launch(
    server_ip: str = "",
    game_exe: str = "",
    env: str = "",
) -> str:
    """Clear shipping logs, fetch credentials, and start the game (`just launch`)."""
    return _run_tool(
        launch,
        game_exe=game_exe or None,
        server_ip=server_ip or None,
        offline=False,
        proxy=False,
        env=env or None,
    )


@mcp.tool()
def ctl_relaunch(
    server_ip: str = "",
    game_exe: str = "",
    env: str = "",
    dll_config: str = "debug",
) -> str:
    """Copy TheGame.dll then launch (`just relaunch`)."""
    return _run_tool(
        relaunch,
        game_exe=game_exe or None,
        server_ip=server_ip or None,
        offline=False,
        proxy=False,
        env=env or None,
        dll_config=dll_config,
    )


@mcp.tool()
def ctl_launch_offline(
    server_ip: str = "",
    game_exe: str = "",
    env: str = "",
) -> str:
    """Launch with --proxy: local entry (127.0.0.1) + real auth (`just launch-offline`)."""
    return _run_tool(
        launch,
        game_exe=game_exe or None,
        server_ip=server_ip or None,
        offline=False,
        proxy=True,
        env=env or None,
    )


@mcp.tool()
def ctl_wait_menu(timeout: float = 120.0) -> str:
    """Block until game stage shard_select (`just wait-menu`)."""
    return _run_tool(wait_for_stage, stage="shard_select", timeout=timeout)


@mcp.tool()
def ctl_wait_stage(stage: str, timeout: float = 120.0) -> str:
    """Block until the game reaches a diagnostics stage (`just wait-stage`)."""
    return _run_tool(wait_for_stage, stage=stage, timeout=timeout)


@mcp.tool()
def ctl_wait_lobby(shard_timeout: float = 120.0, lobby_timeout: float = 10.0) -> str:
    """Wait shard_select, send nav_pass_shard_select, wait lobby (`just wait-lobby`)."""
    return _run_tool(
        wait_lobby,
        shard_timeout=shard_timeout,
        lobby_timeout=lobby_timeout,
    )


@mcp.tool()
def ctl_commands() -> str:
    """List handler commands supported by the connected game (`just commands`)."""
    return _run_tool(handler_commands)


@mcp.tool()
def ctl_send(message: str) -> str:
    """Send a line-oriented command to the game on the handler pipe (`just send`)."""
    return _run_tool(send, message=message)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
