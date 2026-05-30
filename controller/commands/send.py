from json import dumps
from typing import Literal

from config import Settings
from gamestate import GameState
from handler import HandlerDisconnectedError, HandlerNotConnectedError

from .common import Command


class SendCommandError(Exception):
    pass


class SendCommand(Command):
    command: Literal["send"] = "send"
    message: str

    def invoke(self, settings: Settings, state: GameState) -> str:
        message = self.message.strip()
        if not message:
            raise SendCommandError("message must not be empty")

        handler = state.handler
        if handler is None:
            raise SendCommandError("handler pipe not available")

        try:
            handler.send(message)
        except HandlerNotConnectedError as e:
            raise SendCommandError(str(e)) from e
        except HandlerDisconnectedError as e:
            raise SendCommandError(str(e)) from e

        return dumps({"sent": message})
