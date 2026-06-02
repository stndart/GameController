"""Handler named pipe: duplex line-oriented commands and responses."""

from __future__ import annotations

from collections.abc import Callable
from threading import Lock, Thread
from time import sleep

from pipe import PipeDisconnectedError, PipeServer


class HandlerNotConnectedError(OSError):
    """No game client is connected on the handler pipe."""


class HandlerDisconnectedError(OSError):
    """Handler pipe peer disconnected during request."""


class HandlerTimeoutError(TimeoutError):
    """Timed out waiting for a handler pipe response."""


class HandlerResponseError(OSError):
    """Unexpected response line from the game."""


class HandlerPipeSession:
    """Accepts a game client and exchanges newline-terminated commands."""

    def __init__(self, pipe_name: str) -> None:
        self._pipe_name = pipe_name
        self._pipe = PipeServer(pipe_name)
        self._lock = Lock()
        self._connected = False
        self._running = False
        self._thread: Thread | None = None
        self._on_disconnect: Callable[[], None] | None = None

    def set_on_disconnect(self, callback: Callable[[], None] | None) -> None:
        self._on_disconnect = callback

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

    def reset_session(self) -> None:
        """Drop client state when the game exits (diagnostics disconnected)."""
        with self._lock:
            self._mark_disconnected_locked()

    def request(self, message: str, *, timeout: float) -> str:
        """Send a command and read one line response from the game."""
        with self._lock:
            if not self._connected:
                raise HandlerNotConnectedError("no game connected on handler pipe")
            if not self._pipe.write_message(message):
                self._mark_disconnected_locked()
                raise HandlerDisconnectedError(
                    "handler pipe disconnected while sending"
                )
            try:
                response = self._pipe.read_message(timeout=timeout)
            except TimeoutError as e:
                raise HandlerTimeoutError(
                    f"timed out waiting for handler response ({timeout}s)"
                ) from e
            except PipeDisconnectedError as e:
                self._mark_disconnected_locked()
                raise HandlerDisconnectedError(
                    "handler pipe disconnected while reading response"
                ) from e
            return response.strip()

    def send(self, message: str, *, timeout: float) -> None:
        """Send a command and require an ``ok`` response."""
        response = self.request(message, timeout=timeout)
        if response != "ok":
            raise HandlerResponseError(f"expected ok, got {response!r}")

    def _mark_disconnected_locked(self) -> None:
        self._connected = False
        self._pipe.force_disconnect()

    def _notify_disconnect(self) -> None:
        if self._on_disconnect is None:
            return
        try:
            self._on_disconnect()
        except Exception as e:
            print(f"[daemon] handler on_disconnect error: {e}")

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
                    with self._lock:
                        if not self._connected:
                            break
                    if not self._pipe.peer_connected():
                        with self._lock:
                            self._mark_disconnected_locked()
                        break
                    sleep(0.1)

            except Exception as e:
                print(f"[daemon] handler unexpected error: {e}")
            finally:
                with self._lock:
                    was_connected = self._connected
                    self._mark_disconnected_locked()
                self._pipe.prepare_for_accept()
                if was_connected:
                    print(f"[daemon] handler disconnected pipe={self._pipe_name}")
                    self._notify_disconnect()
