from json import dumps
from typing import Literal

from config import Settings
from gamestate import GameState
from handler import (
    HandlerDisconnectedError,
    HandlerNotConnectedError,
    HandlerTimeoutError,
)

from .common import Command


class CommandsCommandError(Exception):
    pass


class CommandsCommand(Command):
    command: Literal["commands"] = "commands"

    def invoke(self, settings: Settings, state: GameState) -> str:
        handler = state.handler
        if handler is None:
            raise CommandsCommandError("handler pipe not available")

        timeout = settings.handler_response_timeout
        try:
            response = handler.request("commands", timeout=timeout)
        except HandlerNotConnectedError as e:
            raise CommandsCommandError(str(e)) from e
        except HandlerDisconnectedError as e:
            raise CommandsCommandError(str(e)) from e
        except HandlerTimeoutError as e:
            raise CommandsCommandError(str(e)) from e

        handlers = [part.strip() for part in response.split(",") if part.strip()]
        return dumps({"handlers": handlers})
