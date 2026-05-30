"""
Non-elevated CLI for the thegame-ctl daemon.

Start the daemon once (elevated):  ctl -d
Then:  ctl ping | launch | wait-for-stage server_ready | kill --all | copy-logs
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

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
from commands.common import Command
from config import REPO_ROOT, Settings
from launch_game import Settings as LaunchSettings
from pipe import PipeClient

DAEMON_HINT = (
    "daemon not running; start once with:\n  gsudo ctl -d\n  # or: just daemon-bg"
)


class DaemonNotRunningError(RuntimeError):
    pass


def rpc(command: Command, *, timeout: float = 30.0) -> dict:
    """Send one command to the daemon and return the parsed response body."""
    settings = Settings()
    connect_timeout = max(1, math.ceil(timeout))
    try:
        client = PipeClient(settings.ctl_pipe_name, timeout=connect_timeout)
    except (TimeoutError, FileNotFoundError) as e:
        raise DaemonNotRunningError(DAEMON_HINT) from e

    try:
        if not client.write_message(command.model_dump_json()):
            raise DaemonNotRunningError("Failed to invoke rpc.")
        raw = client.read_message(timeout=timeout)
    finally:
        client.close()

    payload = json.loads(raw)
    if payload.get("status") == "error":
        raise RuntimeError(payload.get("error", "unknown error"))
    if payload.get("status") != "ok":
        raise RuntimeError(f"unexpected response: {payload}")
    return payload


def _print_result(result: dict) -> None:
    print(json.dumps(result, indent=2))


def _game_exe(args: argparse.Namespace) -> Path:
    return (args.game_exe or LaunchSettings().GAME_PATH).resolve()


def run_daemon_background() -> int:
    """Spawn detached daemon process."""
    script = Path(__file__).resolve()
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
    proc = subprocess.Popen(
        [sys.executable, str(script), "-d", "--foreground"],
        cwd=str(REPO_ROOT),
        creationflags=creationflags,
    )
    print(f"daemon started in background pid={proc.pid}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="FA-EMU control client (requires elevated daemon: ctl -d).",
    )
    parser.add_argument(
        "-d",
        "--daemon",
        action="store_true",
        help="Run elevated daemon server (use with gsudo).",
    )
    parser.add_argument("--foreground", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--background",
        action="store_true",
        help="With -d: detach daemon process.",
    )

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("ping", help="Check daemon is running and elevated.")
    sub.add_parser("processes", help="List GAME.exe / GameLauncher.exe PIDs.")
    sub.add_parser("status", help="Session run_id, stages, and progress.")
    sub.add_parser("stages", help="Known stages and stages seen this session.")
    sub.add_parser("stop", help="Stop the daemon.")

    sub.add_parser(
        "commands",
        help="List handler commands supported by the connected game.",
    )

    send_p = sub.add_parser(
        "send",
        help="Send a line-oriented command to the game via the handler pipe.",
    )
    send_p.add_argument(
        "message",
        help="Command text, e.g. nav-menu (newline added by daemon).",
    )

    wait_p = sub.add_parser(
        "wait-for-stage",
        help="Block until game reaches a diagnostics stage (or timeout).",
    )
    wait_p.add_argument("stage", help="game_state phase name, e.g. server_ready")
    wait_p.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Seconds to wait (default: 120).",
    )

    launch_p = sub.add_parser(
        "launch", help="Clear logs, copy config, spawn GameLauncher."
    )
    launch_p.add_argument("-p", "--game-exe", type=Path, default=None)
    launch_p.add_argument("-s", "--server-ip", default=None)
    launch_p.add_argument(
        "--offline",
        action="store_true",
        help="Use localhost token (no API).",
    )

    kill_p = sub.add_parser("kill", help="Force-kill game processes.")
    kill_p.add_argument(
        "--all",
        action="store_true",
        help="Kill GAME.exe and GameLauncher.exe.",
    )

    copy_dll_p = sub.add_parser("copy-dll", help="Copy TheGame.dll next to GAME.exe.")
    copy_dll_p.add_argument(
        "--dll-config",
        choices=["debug", "debug-wire", "release"],
        default="debug",
    )
    copy_dll_p.add_argument("--dll-source", type=Path, default=None)
    copy_dll_p.add_argument("-p", "--game-exe", type=Path, default=None)

    clear_logs_p = sub.add_parser(
        "clear-logs",
        help="Delete shipping game log files next to GAME.exe.",
    )
    clear_logs_p.add_argument("-p", "--game-exe", type=Path, default=None)

    copy_logs_p = sub.add_parser(
        "copy-logs",
        help="Copy shipping game logs into run dir (see ctl.yaml game_log_files).",
    )
    copy_logs_p.add_argument("--run-id", default=None)
    copy_logs_p.add_argument("-p", "--game-exe", type=Path, default=None)

    return parser


def _handle_ping(_args: argparse.Namespace) -> int:
    _print_result(rpc(PingCommand()))
    return 0


def _handle_processes(_args: argparse.Namespace) -> int:
    _print_result(rpc(ProcessesCommand()))
    return 0


def _handle_status(_args: argparse.Namespace) -> int:
    _print_result(rpc(StatusCommand()))
    return 0


def _handle_stages(_args: argparse.Namespace) -> int:
    _print_result(rpc(ListStagesCommand()))
    return 0


def _handle_wait_for_stage(args: argparse.Namespace) -> int:
    timeout = max(args.timeout, 0.0)
    result = rpc(
        WaitForStageCommand(stage=args.stage, timeout=timeout),
        timeout=timeout + 10.0,
    )
    _print_result(result)
    return 0 if result.get("reached") else 1


def _handle_launch(args: argparse.Namespace) -> int:
    game = str(_game_exe(args))
    _print_result(rpc(ClearLogsCommand(game_exe=game)))
    result = rpc(
        LaunchCommand(
            game_exe=game,
            server_ip=args.server_ip,
            offline=args.offline,
        ),
        timeout=130.0,
    )
    _print_result(result)
    return 0


def _handle_kill(args: argparse.Namespace) -> int:
    _print_result(rpc(KillCommand(all=args.all)))
    return 0


def _handle_copy_dll(args: argparse.Namespace) -> int:
    _print_result(
        rpc(
            CopyDllCommand(
                dll_config=args.dll_config,
                dll_source=str(args.dll_source) if args.dll_source else None,
                game_exe=str(_game_exe(args)),
            )
        )
    )
    return 0


def _handle_clear_logs(args: argparse.Namespace) -> int:
    _print_result(rpc(ClearLogsCommand(game_exe=str(_game_exe(args)))))
    return 0


def _handle_copy_logs(args: argparse.Namespace) -> int:
    _print_result(
        rpc(
            CopyLogsCommand(
                run_id=args.run_id,
                game_exe=str(_game_exe(args)),
            )
        )
    )
    return 0


def _handle_stop(_args: argparse.Namespace) -> int:
    rpc(StopCommand())
    return 0


def _handle_send(args: argparse.Namespace) -> int:
    settings = Settings()
    timeout = settings.handler_response_timeout + 10.0
    _print_result(rpc(SendCommand(message=args.message), timeout=timeout))
    return 0


def _handle_commands(_args: argparse.Namespace) -> int:
    settings = Settings()
    timeout = settings.handler_response_timeout + 10.0
    _print_result(rpc(CommandsCommand(), timeout=timeout))
    return 0


DISPATCH: dict[str, Callable[[argparse.Namespace], int]] = {
    "ping": _handle_ping,
    "processes": _handle_processes,
    "status": _handle_status,
    "stages": _handle_stages,
    "wait-for-stage": _handle_wait_for_stage,
    "launch": _handle_launch,
    "kill": _handle_kill,
    "copy-dll": _handle_copy_dll,
    "clear-logs": _handle_clear_logs,
    "copy-logs": _handle_copy_logs,
    "commands": _handle_commands,
    "send": _handle_send,
    "stop": _handle_stop,
}


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.daemon:
        if args.background and not args.foreground:
            return run_daemon_background()
        from ctl import Ctl

        Ctl(Settings()).run_daemon()
        return 0

    if not args.command:
        parser.print_help()
        return 0

    handler = DISPATCH.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    try:
        return handler(args)
    except DaemonNotRunningError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except (RuntimeError, ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
