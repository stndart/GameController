import ctypes
from json import dumps
from typing import Literal

from config import Settings
from gamestate import GameState

from .common import Command

shell32 = ctypes.WinDLL("shell32", use_last_error=True)


class PingCommand(Command):
    command: Literal["ping"] = "ping"

    def invoke(self, settings: Settings, state: GameState) -> str:
        return dumps({"version": "1", "elevated": bool(shell32.IsUserAnAdmin())})
