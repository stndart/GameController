"""Copy and clear shipping game logs using Settings.game_log_files."""

from __future__ import annotations

import shutil
from json import dumps
from pathlib import Path
from typing import Literal

from config import Settings, fresh_settings
from gamestate import CommandError, GameState
from launch_game import Settings as LaunchSettings
from paths import merge_meta, resolve_run_id, run_dir

from .common import Command


class LogsCommandError(CommandError):
    pass


def resolve_game_exe(game_exe: str | None) -> Path:
    launch_settings = LaunchSettings()
    if game_exe is not None:
        launch_settings.GAME_PATH = Path(game_exe)
    return launch_settings.GAME_PATH.resolve()


def clear_game_logs(game_exe: Path, files: list[tuple[str, str]]) -> list[str]:
    shipping = game_exe.parent
    cleared: list[str] = []
    for src_name, _ in files:
        path = shipping / src_name
        if path.is_file():
            path.unlink()
            cleared.append(src_name)
    return cleared


def copy_game_logs_to_run(
    game_exe: Path,
    run_id: str,
    files: list[tuple[str, str]],
) -> dict[str, str]:
    shipping = game_exe.parent
    dest_dir = run_dir(run_id)
    copied: dict[str, str] = {}
    for src_name, dest_name in files:
        src = shipping / src_name
        if src.is_file():
            dest = dest_dir / dest_name
            shutil.copy2(src, dest)
            copied[dest_name] = str(dest)
    return copied


class ClearLogsCommand(Command):
    command: Literal["clear_logs"] = "clear_logs"
    game_exe: str | None = None

    def invoke(self, settings: Settings, state: GameState) -> str:
        runtime = fresh_settings()
        game_exe = resolve_game_exe(self.game_exe)
        cleared = clear_game_logs(game_exe, runtime.game_log_files)
        return dumps({"cleared": cleared})


class CopyLogsCommand(Command):
    command: Literal["copy_logs"] = "copy_logs"
    run_id: str | None = None
    game_exe: str | None = None

    def invoke(self, settings: Settings, state: GameState) -> str:
        try:
            run_id = resolve_run_id(self.run_id or state.run_id)
        except ValueError as e:
            raise LogsCommandError(str(e)) from e

        runtime = fresh_settings()
        game_exe = resolve_game_exe(self.game_exe)
        copied = copy_game_logs_to_run(game_exe, run_id, runtime.game_log_files)
        if copied:
            merge_meta(run_id, {"game_logs": copied})

        return dumps({"run_id": run_id, "copied": copied})
