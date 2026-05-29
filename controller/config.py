from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[1]
CTL_ENV_FILE = REPO_ROOT / "ctl.env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(CTL_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ctl_pipe_name: str = "thegame-ctl"
    diagnostics_pipe_name: str = "thegame-diagnostics"

    dll_debug_path: Path = (
        REPO_ROOT.parent / "build" / "msvc-x86-debug" / "bin" / "TheGame.dll"
    )
    dll_release_path: Path = (
        REPO_ROOT.parent / "build" / "msvc-x86-release" / "bin" / "TheGame.dll"
    )
    dll_debug_wire_path: Path = (
        REPO_ROOT.parent
        / "build"
        / "msvc-x86-debug-wire"
        / "bin"
        / "TheGame.dll"
    )

    # Copied into GAME.exe process env at launch (GameLauncher child inherits).
    thegame_nav_auto: str = ""
    thegame_nav_action: str = ""

    def game_child_env(self) -> dict[str, str]:
        import os

        env = dict(os.environ)
        nav = self.thegame_nav_auto.strip()
        if nav:
            env["THEGAME_NAV_AUTO"] = nav
        else:
            env.pop("THEGAME_NAV_AUTO", None)
        action = self.thegame_nav_action.strip()
        if action:
            env["THEGAME_NAV_ACTION"] = action
        else:
            env.pop("THEGAME_NAV_ACTION", None)
        return env

    @property
    def dll_configs(self) -> dict[str, Path]:
        return {
            "debug": self.dll_debug_path,
            "debug-wire": self.dll_debug_wire_path,
            "release": self.dll_release_path,
        }


def fresh_settings() -> Settings:
    """Re-read ctl/ctl.env (daemon is long-lived; temp until proper reload)."""
    return Settings()
