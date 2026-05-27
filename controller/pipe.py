from __future__ import annotations

from time import monotonic, sleep, time
from typing import TYPE_CHECKING, cast

import win32file
import win32pipe
import win32security
from win32.lib.winerror import (
    ERROR_BROKEN_PIPE,
    ERROR_NO_DATA,
    ERROR_PIPE_BUSY,
    ERROR_PIPE_LISTENING,
    ERROR_PIPE_NOT_CONNECTED,
)

if TYPE_CHECKING:
    import _win32typing  # pyright: ignore[reportMissingModuleSource]


MAX_BUFFER_SIZE = 100000


def _pipe_name(name: str) -> str:
    return f"\\\\.\\pipe\\{name}"


def _pipe_security_attributes() -> _win32typing.PySECURITY_ATTRIBUTES:
    """Allow non-elevated clients to talk to an elevated daemon."""
    sd = win32security.SECURITY_DESCRIPTOR()
    sd.Initialize()
    sd.SetSecurityDescriptorDacl(1, None, 0)  # NULL DACL # type: ignore
    sa = win32security.SECURITY_ATTRIBUTES()
    sa.SECURITY_DESCRIPTOR = sd
    return sa


class PipeHandle:
    handle: int

    def __init__(self, handle: int):
        self.handle = handle


class PipeMixin:
    pipe: PipeHandle

    def read_bytes(self) -> bytes:
        _error, message = win32file.ReadFile(self.pipe.handle, MAX_BUFFER_SIZE)
        message = cast(bytes, message)
        return message

    def read(self) -> str:
        return self.read_bytes().decode("utf-8")

    def write(self, data: bytes | str):
        if isinstance(data, str):
            data = data.encode("utf-8")
        win32file.WriteFile(self.pipe.handle, data)

    def read_message(self, timeout: float = 1) -> str:
        pending = b""
        ts = monotonic()
        while monotonic() - ts < timeout:
            try:
                pending += self.read_bytes()
            except win32pipe.error as e:
                if e.winerror == ERROR_NO_DATA:
                    if pending:
                        return pending.decode("utf-8")
                    else:
                        sleep(0.1)
                        continue
                elif e.winerror in [ERROR_BROKEN_PIPE, ERROR_PIPE_NOT_CONNECTED]:
                    return pending.decode("utf-8")
                raise e
        raise TimeoutError("Timeout reading from pipe")

    def write_message(self, data: bytes | str) -> bool:
        try:
            self.write(data)
        except win32pipe.error as e:
            if e.winerror == ERROR_BROKEN_PIPE:
                return False
            raise e
        return True


class PipeServer(PipeMixin):
    """Named pipe server for ctl or diagnostics sessions."""

    def __init__(self, name: str):
        self._pending = b""
        self.pipe = PipeHandle(
            win32pipe.CreateNamedPipe(
                _pipe_name(name),
                win32pipe.PIPE_ACCESS_DUPLEX,
                win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_NOWAIT,
                4,
                65536,
                65536,
                0,
                _pipe_security_attributes(),
            )
        )

    def __del__(self):
        self.force_disconnect()

    def accept(self) -> bool:
        try:
            win32pipe.ConnectNamedPipe(self.pipe.handle)
        except win32pipe.error as e:
            if e.winerror == ERROR_PIPE_LISTENING:
                return False
            raise e
        return True

    def disconnect(self):
        # blocks until client reads it all
        try:
            win32file.FlushFileBuffers(self.pipe.handle)
        except win32file.error as e:
            if e.winerror != ERROR_BROKEN_PIPE:
                raise e
        win32pipe.DisconnectNamedPipe(self.pipe.handle)

    def force_disconnect(self):
        # does not wait for client to read. Client would fail afterwards
        try:
            win32pipe.DisconnectNamedPipe(self.pipe.handle)
        except win32pipe.error:
            pass


class PipeClient(PipeMixin):
    _closed: bool = False

    def __init__(self, name: str, timeout: int = 1):
        ts = time()
        while time() - ts < timeout:
            sleep(0.1)
            try:
                # CreateFile returns PyHandle, not int
                self.pipe = cast(
                    PipeHandle,
                    win32file.CreateFile(
                        _pipe_name(name),
                        win32file.GENERIC_WRITE | win32file.GENERIC_READ,
                        0,
                        None,
                        win32file.OPEN_EXISTING,
                        0,
                        None,
                    ),
                )
                win32pipe.SetNamedPipeHandleState(
                    self.pipe.handle,
                    win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_NOWAIT,
                    None,
                    None,
                )
                break
            except win32file.error as e:
                if e.winerror == ERROR_PIPE_BUSY:
                    continue
                raise e
        else:
            raise TimeoutError(
                f"Failed to connect to pipe {name} after {timeout} seconds"
            )

    def __del__(self):
        self.close()

    def close(self):
        if not self._closed:
            win32file.CloseHandle(self.pipe.handle)
            self._closed = True
