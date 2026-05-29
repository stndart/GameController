"""Known game_state phases from TheGame.dll diagnostics (keep in sync with src/hooks)."""

from __future__ import annotations

# Order matches typical boot / navigation flow (src/hooks/game_state.cpp).
KNOWN_STAGES: tuple[str, ...] = (
    "started",
    "intro",
    "login",
    "connecting_to_server",
    "shard_choice",
    "server_ready",
    "lobby",
    "room_list",
    "party_room",
    "room",
    "char_select",
    "map_loading",
    "in_game",
)


def is_known_stage(name: str) -> bool:
    return name in KNOWN_STAGES
