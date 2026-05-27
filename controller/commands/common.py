from config import Settings
from gamestate import GameState
from pydantic import BaseModel


class Command(BaseModel):
    command: str

    def invoke(self, settings: Settings, state: GameState) -> str:
        raise NotImplementedError("Subclasses must implement this method")
