"""Elevated thegame-ctl daemon: named-pipe RPC and diagnostics session state."""

from __future__ import annotations

import json
import os
from time import sleep

from commands import StopCommand, command_adapter
from config import Settings
from gamestate import GameState
from pipe import PipeDisconnectedError, PipeServer


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
        print(
            f"thegame-ctl daemon pid={os.getpid()} pipe={self.settings.ctl_pipe_name}"
        )
        print("Press Ctrl+C to stop the daemon")
        while self._running:
            try:
                sleep(0.1)
                if not self.ctl_pipe.accept():
                    continue
                try:
                    command = self.ctl_pipe.read_message(timeout=30.0)
                except (TimeoutError, PipeDisconnectedError) as e:
                    print(f"[daemon] control read failed: {e}")
                    self.ctl_pipe.force_disconnect()
                    continue
                try:
                    self.ctl_pipe.write_message(self.execute_command(command))
                except PipeDisconnectedError as e:
                    print(f"[daemon] control write failed: {e}")
                finally:
                    try:
                        self.ctl_pipe.disconnect()
                    except Exception:
                        self.ctl_pipe.force_disconnect()
            except KeyboardInterrupt:
                print("Keyboard interrupt received")
                break
            except Exception as e:
                print(f"[daemon] unexpected error: {e}")
                self.ctl_pipe.force_disconnect()

        print("Daemon stopped")

    def execute_command(self, command: str) -> str:
        command_data = command_adapter.validate_json(command)
        print(f"Received command: {command_data.command}")
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
    Ctl(Settings()).run_daemon()


if __name__ == "__main__":
    main()
