"""List known game stages and stages seen in the current session."""

from __future__ import annotations

from json import dumps
from typing import Literal

from config import Settings
from gamestate import GameState
from gamestate.stages import KNOWN_STAGES

from .common import Command


class ListStagesCommand(Command):
    command: Literal["list_stages"] = "list_stages"

    def invoke(self, settings: Settings, state: GameState) -> str:
        return dumps(
            {
                "known": list(KNOWN_STAGES),
                "seen": list(state.progress.game_states),
            }
        )
