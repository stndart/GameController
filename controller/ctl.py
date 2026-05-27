"""Elevated thegame-ctl daemon: named-pipe RPC and diagnostics session state."""

from __future__ import annotations

import json
import logging
import os
from time import sleep

from commands import StopCommand, command_adapter
from config import Settings
from gamestate import GameState
from pipe import PipeServer

log = logging.getLogger(__name__)


class Ctl:
    """Accepts JSON commands on the control pipe and mutates shared session state."""

    settings: Settings
    ctl_pipe: PipeServer
    diag_pipe: PipeServer
    state: GameState
    _running: bool = False

    def __init__(self, settings: Settings):
        self.settings = settings
        self.ctl_pipe = PipeServer(settings.ctl_pipe_name)
        self.diag_pipe = PipeServer(settings.diagnostics_pipe_name)
        self.state = GameState(self.diag_pipe)

    def run_daemon(self) -> None:
        self._running = True
        log.info(
            f"thegame-ctl daemon pid={os.getpid()} pipe={self.settings.ctl_pipe_name}"
        )
        log.info("Press Ctrl+C to stop the daemon")
        while self._running:
            try:
                sleep(0.1)
                if self.ctl_pipe.accept():
                    command = self.ctl_pipe.read_message()
                    log.info(f"Received command: {command}")
                    self.ctl_pipe.write_message(self.execute_command(command))
                    self.ctl_pipe.disconnect()
            except KeyboardInterrupt:
                print("Keyboard interrupt received")
                break
            except Exception:
                raise

        print("Daemon stopped")

    def execute_command(self, command: str) -> str:
        command_data = command_adapter.validate_json(command)
        if isinstance(command_data, StopCommand):
            self._running = False
            return json.dumps({"status": "ok"})

        try:
            res = command_data.invoke(self.settings, self.state)
        except Exception as e:
            print(f"Error executing command <{command_data.command}>: {e}")
            return json.dumps(
                {
                    "status": "error",
                    "error": str(e),
                }
            )
        return json.dumps({"status": "ok", **json.loads(res)})


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    Ctl(Settings()).run_daemon()


if __name__ == "__main__":
    main()
