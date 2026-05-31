"""RPC transport to the elevated ctl daemon."""

from __future__ import annotations

import json
import math

from commands.common import Command
from config import Settings
from pipe import PipeClient

DAEMON_HINT = (
    "daemon not running; start once with:\n  gsudo ctl -d\n  # or: just daemon-bg"
)


class DaemonNotRunningError(RuntimeError):
    pass


def rpc(command: Command, *, timeout: float = 30.0) -> dict:
    """Send one command to the daemon and return the parsed response body."""
    settings = Settings()
    connect_timeout = max(1, math.ceil(timeout))
    try:
        client = PipeClient(settings.ctl_pipe_name, timeout=connect_timeout)
    except (TimeoutError, FileNotFoundError) as e:
        raise DaemonNotRunningError(DAEMON_HINT) from e

    try:
        if not client.write_message(command.model_dump_json()):
            raise DaemonNotRunningError("Failed to invoke rpc.")
        raw = client.read_message(timeout=timeout)
    finally:
        client.close()

    payload = json.loads(raw)
    if payload.get("status") == "error":
        raise RuntimeError(payload.get("error", "unknown error"))
    if payload.get("status") != "ok":
        raise RuntimeError(f"unexpected response: {payload}")
    return payload
