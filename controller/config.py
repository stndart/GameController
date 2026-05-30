from pathlib import Path

import yaml
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CTL_CONFIG_FILE = REPO_ROOT / "ctl.yaml"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        yaml_file=CTL_CONFIG_FILE,
        yaml_file_encoding="utf-8",
        extra="ignore",
        env_file=None,
    )

    ctl_pipe_name: str = "thegame-ctl"
    diagnostics_pipe_name: str = "thegame-diagnostics"
    handler_pipe_name: str = "thegame-handler"
    handler_response_timeout: float = 30.0

    dll_debug_path: Path = (
        REPO_ROOT.parent / "build" / "msvc-x86-debug" / "bin" / "TheGame.dll"
    )
    dll_release_path: Path = (
        REPO_ROOT.parent / "build" / "msvc-x86-release" / "bin" / "TheGame.dll"
    )

    game_log_files: list[tuple[str, str]] = [
        ("logs.txt", "game_logs.txt"),
        ("netlogs.txt", "game_netlogs.txt"),
        ("proudnet_tcp.txt", "game_proudnet_tcp.txt"),
    ]

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            YamlConfigSettingsSource(settings_cls),
        )

    @property
    def dll_configs(self) -> dict[str, Path]:
        return {
            "debug": self.dll_debug_path,
            "release": self.dll_release_path,
        }

    def save(
        self,
        path: Path | None = None,
        *,
        exclude_defaults: bool = False,
    ) -> None:
        target = path or CTL_CONFIG_FILE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            yaml.safe_dump(
                self.model_dump(mode="json", exclude_defaults=exclude_defaults),
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )


def fresh_settings() -> Settings:
    """Re-read ctl.yaml (daemon is long-lived; reloaded on each launch)."""
    return Settings()
