import shutil
from json import dumps
from pathlib import Path
from typing import Literal

from config import REPO_ROOT, Settings
from gamestate import CommandError, GameState
from launch_game import Settings as LaunchSettings

from .common import Command


class CopyDllCommandError(CommandError):
    pass


def dll_path_for_config(dll_config: str) -> Path:
    build_dir = (
        dll_config if dll_config.startswith("msvc-x86-") else f"msvc-x86-{dll_config}"
    )
    return REPO_ROOT.parent / "build" / build_dir / "bin" / "TheGame.dll"


def resolve_dll_source(dll_config: str, dll_source: str | None) -> Path:
    if dll_source:
        return Path(dll_source).resolve()
    return dll_path_for_config(dll_config).resolve()


class CopyDllCommand(Command):
    command: Literal["copy_dll"] = "copy_dll"
    dll_config: str = "debug"
    dll_source: str | None = None
    game_exe: str | None = None

    def invoke(self, settings: Settings, state: GameState) -> str:
        launch_settings = LaunchSettings()
        if self.game_exe is not None:
            launch_settings.GAME_PATH = Path(self.game_exe)

        game_exe = launch_settings.GAME_PATH.resolve()
        if not game_exe.is_file():
            raise CopyDllCommandError(f"GAME.exe not found: {game_exe}")

        source = resolve_dll_source(self.dll_config, self.dll_source)
        if not source.is_file():
            raise CopyDllCommandError(
                f"TheGame.dll not found for {self.dll_config}: {source}. "
                "Build first or pass --dll-source."
            )

        target = game_exe.with_name(source.name)
        shutil.copy2(source, target)
        return dumps({"source": str(source), "target": str(target)})
