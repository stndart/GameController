"""Kill game processes (tracked launcher PID or by image name)."""

from __future__ import annotations

import subprocess
from json import dumps
from typing import Any, Literal

from config import Settings
from gamestate import CommandError, GameState
from gamestate.gamestate import SessionPhase

from .common import Command
from .processes import DEFAULT_KILL_IMAGES


class KillCommandError(CommandError):
    pass


def _taskkill_by_image(image: str) -> dict[str, Any]:
    proc = subprocess.run(
        ["taskkill", "/F", "/IM", image],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "image": image,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def _taskkill_by_pid(pid: int) -> dict[str, Any]:
    proc = subprocess.run(
        ["taskkill", "/F", "/PID", str(pid)],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "pid": pid,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


class KillCommand(Command):
    command: Literal["kill"] = "kill"
    all: bool = False

    def invoke(self, settings: Settings, state: GameState) -> str:
        if self.all:
            killed = [_taskkill_by_image(image) for image in DEFAULT_KILL_IMAGES]
            if state._running or state.progress.phase not in (
                SessionPhase.idle,
                SessionPhase.ended,
            ):
                state.end_session()
            return dumps({"killed": killed})

        pid = state.game_pid or state.progress.launcher_pid
        if pid is None:
            raise KillCommandError("No game running")
        result = _taskkill_by_pid(pid)
        state.end_session()
        return dumps({"killed": [result]})
