"""Non-elevated ctl client operations (shared by CLI and MCP)."""

from __future__ import annotations

from pathlib import Path

from client_rpc import DaemonNotRunningError, rpc
from commands import (
    ClearLogsCommand,
    CommandsCommand,
    CopyDllCommand,
    CopyLogsCommand,
    KillCommand,
    LaunchCommand,
    ListStagesCommand,
    PingCommand,
    ProcessesCommand,
    SendCommand,
    StatusCommand,
    StopCommand,
    WaitForStageCommand,
)
from config import Settings
from launch_game import Settings as LaunchSettings
from launch_game import parse_env_string


def default_game_exe(game_exe: Path | str | None = None) -> Path:
    if game_exe is None:
        return LaunchSettings().GAME_PATH.resolve()
    return Path(game_exe).resolve()


def ping() -> dict:
    return rpc(PingCommand())


def processes() -> dict:
    return rpc(ProcessesCommand())


def status() -> dict:
    return rpc(StatusCommand())


def stages() -> dict:
    return rpc(ListStagesCommand())


def wait_for_stage(stage: str, *, timeout: float = 120.0) -> dict:
    timeout = max(timeout, 0.0)
    return rpc(
        WaitForStageCommand(stage=stage, timeout=timeout),
        timeout=timeout + 10.0,
    )


def launch(
    *,
    game_exe: Path | str | None = None,
    server_ip: str | None = None,
    offline: bool = False,
    proxy: bool = False,
    env: str | dict[str, str] | None = None,
) -> dict:
    parsed_env: dict[str, str] = {}
    if env:
        parsed_env = parse_env_string(env) if isinstance(env, str) else env
    game = str(default_game_exe(game_exe))
    rpc(ClearLogsCommand(game_exe=game))
    return rpc(
        LaunchCommand(
            game_exe=game,
            server_ip=server_ip,
            offline=offline,
            proxy=proxy,
            env=parsed_env,
        ),
        timeout=130.0,
    )


def kill(*, all: bool = False) -> dict:
    return rpc(KillCommand(all=all))


def copy_dll(
    *,
    dll_config: str = "debug",
    dll_source: Path | str | None = None,
    game_exe: Path | str | None = None,
) -> dict:
    return rpc(
        CopyDllCommand(
            dll_config=dll_config,
            dll_source=str(dll_source) if dll_source else None,
            game_exe=str(default_game_exe(game_exe)),
        )
    )


def clear_logs(*, game_exe: Path | str | None = None) -> dict:
    return rpc(ClearLogsCommand(game_exe=str(default_game_exe(game_exe))))


def copy_logs(
    *,
    run_id: str | None = None,
    game_exe: Path | str | None = None,
) -> dict:
    return rpc(
        CopyLogsCommand(
            run_id=run_id,
            game_exe=str(default_game_exe(game_exe)),
        )
    )


def handler_commands() -> dict:
    settings = Settings()
    timeout = settings.handler_response_timeout + 10.0
    return rpc(CommandsCommand(), timeout=timeout)


def send(message: str) -> dict:
    settings = Settings()
    timeout = settings.handler_response_timeout + 10.0
    return rpc(SendCommand(message=message), timeout=timeout)


def stop() -> None:
    rpc(StopCommand())


__all__ = [
    "DaemonNotRunningError",
    "clear_logs",
    "copy_dll",
    "copy_logs",
    "default_game_exe",
    "handler_commands",
    "kill",
    "launch",
    "ping",
    "processes",
    "send",
    "stages",
    "status",
    "stop",
    "wait_for_stage",
]
