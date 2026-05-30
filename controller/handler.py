"""Handler named pipe: game client reads line-oriented commands from the daemon."""

from __future__ import annotations

from threading import Lock, Thread
from time import sleep

from pipe import PipeDisconnectedError, PipeServer


class HandlerNotConnectedError(OSError):
    """No game client is connected on the handler pipe."""


class HandlerDisconnectedError(OSError):
    """Handler pipe peer disconnected during send."""


class HandlerPipeSession:
    """Accepts a game client and forwards newline-terminated commands."""

    def __init__(self, pipe_name: str) -> None:
        self._pipe_name = pipe_name
        self._pipe = PipeServer(pipe_name)
        self._lock = Lock()
        self._connected = False
        self._running = False
        self._thread: Thread | None = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = Thread(
            target=self._thread_func, name="handler-pipe", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        with self._lock:
            self._connected = False
        self._pipe.force_disconnect()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        self._thread = None

    def send(self, message: str) -> None:
        with self._lock:
            if not self._connected:
                raise HandlerNotConnectedError("no game connected on handler pipe")
            if not self._pipe.write_message(message):
                self._mark_disconnected_locked()
                raise HandlerDisconnectedError(
                    "handler pipe disconnected while sending"
                )

    def _mark_disconnected_locked(self) -> None:
        self._connected = False
        self._pipe.force_disconnect()

    def _mark_disconnected(self) -> None:
        with self._lock:
            self._mark_disconnected_locked()

    def _thread_func(self) -> None:
        while self._running:
            try:
                while self._running and not self._pipe.accept():
                    sleep(0.1)

                if not self._running:
                    break

                with self._lock:
                    self._connected = True
                print(f"[daemon] handler connected pipe={self._pipe_name}")

                while self._running:
                    try:
                        self._pipe.read_message(timeout=0.5)
                    except TimeoutError:
                        continue
                    except PipeDisconnectedError:
                        break
                    except Exception as e:
                        print(f"[daemon] handler read error: {e}")
                        break

            except Exception as e:
                print(f"[daemon] handler unexpected error: {e}")
            finally:
                with self._lock:
                    was_connected = self._connected
                    self._mark_disconnected_locked()
                if was_connected:
                    print(f"[daemon] handler disconnected pipe={self._pipe_name}")
