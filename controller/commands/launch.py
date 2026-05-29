"""Launch GAME.exe via GameLauncher with fresh launch credentials."""

from __future__ import annotations

import urllib.error
from json import dumps
from pathlib import Path
from typing import Any, Literal

from config import Settings
from gamestate import CommandError, GameState
from launch_game import (
    Settings as LaunchSettings,
)
from launch_game import (
    fetch_launch_credentials,
    load_account_token,
    resolve_server_ip,
    spawn_game_launcher,
    write_config,
    write_nav_auto,
    write_server_override,
)

from .common import Command
from .copy_logs import clear_shipping_game_logs


class LaunchCommandError(CommandError):
    pass


class LaunchCommand(Command):
    command: Literal["launch"] = "launch"
    game_exe: str | None = None
    server_ip: str | None = None
    offline: bool = False
    # Passed from CLI (client env); daemon does not inherit THEGAME_NAV_AUTO from shell.
    nav_auto: str | None = None

    def invoke(self, settings: Settings, state: GameState) -> str:
        if state._running:
            raise LaunchCommandError("Game is already running")

        launch_settings = LaunchSettings()
        if self.game_exe is not None:
            launch_settings.GAME_PATH = Path(self.game_exe)

        game_exe = launch_settings.GAME_PATH.resolve()
        if not game_exe.is_file():
            raise LaunchCommandError("GAME.exe not found")

        launch_data: dict[str, Any] = {}
        try:
            if not self.offline:
                account_token = load_account_token(launch_settings)
                launch_data = fetch_launch_credentials(launch_settings, account_token)
                launch_token = str(launch_data["token"])
            else:
                launch_token = "localhost"

            server_ip = resolve_server_ip(
                launch_settings,
                self.server_ip,
                launch_data,
                offline=self.offline,
            )
            kernel_check_disable = launch_data.get("kernel_check_disable") is True

            clear_shipping_game_logs(game_exe)
            write_config(launch_settings, game_exe, launch_token, server_ip)
            write_server_override(game_exe, server_ip)
            nav_mode = (
                (self.nav_auto or "").strip()
                or settings.thegame_nav_auto.strip()
                or settings.game_child_env().get("THEGAME_NAV_AUTO", "")
            ).strip()
            write_nav_auto(game_exe, nav_mode)
            child_env = settings.game_child_env()
            if nav_mode:
                child_env["THEGAME_NAV_AUTO"] = nav_mode
            proc = spawn_game_launcher(
                launch_settings,
                launch_token,
                kernel_check_disable,
                extra_env=child_env,
            )
        except (RuntimeError, urllib.error.URLError, OSError) as e:
            raise LaunchCommandError(f"Failed to launch game: {e}") from e

        try:
            state.start(proc.pid)
        except RuntimeError as e:
            raise LaunchCommandError(str(e)) from e

        print(
            f"run_id={state.run_id} config={launch_settings.get_config_path()} "
            f"game={game_exe} server={server_ip} "
            f"kernel_check_disable={kernel_check_disable} "
            f"launcher_pid={proc.pid} game_pid={state.game_pid}"
        )
        return dumps(
            {
                "run_id": state.run_id,
                "pid": state.game_pid,
                "launcher_pid": proc.pid,
                "run_dir": str(state.run_dir_path) if state.run_dir_path else None,
            }
        )
