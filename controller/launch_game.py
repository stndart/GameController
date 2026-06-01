#!/usr/bin/env python3
"""
Minimal FA-EMU launch automation.

Fetches a fresh launch token via GET /auth/launch (same as the Electron app),
writes config.ini, spawns GameLauncher.exe. No patch download or hash checks.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml
from config import REPO_ROOT
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

LAUNCH_CONFIG_FILE = REPO_ROOT / "launch.yaml"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        yaml_file=LAUNCH_CONFIG_FILE,
        yaml_file_encoding="utf-8",
        extra="ignore",
        env_file=None,
    )

    LAUNCHER_ROOT: Path = Path(r"C:\Users\Svyat\AppData\Local\Programs\fa-emu-launcher")
    GAME_PATH: Path = Path(r"G:\Games\FA\FA-EMU\Shipping\GAME.exe")
    # Directory containing build/msvc-x86-*/bin/TheGame.dll (default: parent of GameController).
    DLL_BUILD_ROOT: Path | None = None
    API_BASE: str = "https://inx.fa-emu.com/api/v1"
    DEFAULT_SERVER_IP: str = "137.184.201.52"

    # Login session uuid (store.json "token"). Leave empty to read from store.json.
    ACCOUNT_TOKEN: str = ""
    # Optional login if store.json is missing or session expired.
    ACCOUNT_USERNAME: str = ""
    ACCOUNT_PASSWORD: str = ""

    LANGUAGE: str = "EN"
    ENABLE_DISCORD_PRESENCE: bool = False
    ENABLE_EXCLUSIVE_FULLSCREEN: bool = False
    SHOW_INGAME_FPS_COUNTER: bool = True

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

    def dll_build_root(self) -> Path:
        if self.DLL_BUILD_ROOT is not None:
            return Path(self.DLL_BUILD_ROOT)
        return REPO_ROOT.parent

    def save(
        self,
        path: Path | None = None,
        *,
        exclude_defaults: bool = False,
    ) -> None:
        target = path or LAUNCH_CONFIG_FILE
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

    def get_store_path(self) -> Path:
        return self.LAUNCHER_ROOT / "store.json"

    def get_config_path(self) -> Path:
        return self.LAUNCHER_ROOT / "resources" / "assets" / "launcher" / "config.ini"

    def get_game_launcher_exe(self) -> Path:
        return (
            self.LAUNCHER_ROOT
            / "resources"
            / "assets"
            / "launcher"
            / "GameLauncher.exe"
        )


def _api_request(
    settings: Settings,
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    url = f"{settings.API_BASE}{path}"
    req_headers = dict(headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = raw
        raise RuntimeError(f"{method} {path} failed: HTTP {e.code}: {payload}") from e


def load_account_token(settings: Settings, cli_token: str | None = None) -> str:
    if cli_token:
        return cli_token.strip()
    if settings.ACCOUNT_TOKEN:
        return settings.ACCOUNT_TOKEN.strip()
    if not settings.get_store_path().is_file():
        raise RuntimeError(
            f"no session: {settings.get_store_path()} missing. Log in via FA-EMU Launcher once, "
            "set ACCOUNT_TOKEN, or pass --session-token / --username + --password"
        )
    data = json.loads(settings.get_store_path().read_text(encoding="utf-8"))
    token = data.get("token")
    if not token:
        raise RuntimeError(f'no "token" in {settings.get_store_path()}')
    return str(token).strip()


def login(settings: Settings, username: str, password: str) -> str:
    status, data = _api_request(
        settings,
        "POST",
        "/auth/login",
        body={"username": username, "passwd": password},
    )
    if status != 201:
        raise RuntimeError(f"login failed: HTTP {status}: {data}")
    if not isinstance(data, dict) or not data.get("uuid"):
        raise RuntimeError(f"login response missing uuid: {data}")
    return str(data["uuid"])


def fetch_launch_credentials(settings: Settings, account_token: str) -> dict[str, Any]:
    status, data = _api_request(
        settings,
        "GET",
        "/auth/launch",
        headers={"X-Access-Token": account_token},
    )
    if status != 201:
        raise RuntimeError(f"auth/launch failed: HTTP {status}: {data}")
    if not isinstance(data, dict) or not data.get("token"):
        raise RuntimeError(f"auth/launch response missing token: {data}")
    return data


def server_override_env(server_ip: str) -> dict[str, str]:
    """Env vars read by TheGame.dll (Readme.md: THEGAME_SERVER_*)."""
    return {
        "THEGAME_SERVER_OVERRIDE": "ON",
        "THEGAME_SERVER_IP": server_ip,
    }


def write_config(
    settings: Settings, game_path: Path, launch_token: str, server_ip: str
) -> None:
    lines = [
        "[Launcher]",
        "",
        f"game_path={game_path}",
        f"m_token={launch_token}",
        f"m_serverIp={server_ip}",
        f"m_lang={settings.LANGUAGE}",
        f"m_enableDiscordPresence={settings.ENABLE_DISCORD_PRESENCE or 0}",
        f"m_enableExclusiveFullscreen={settings.ENABLE_EXCLUSIVE_FULLSCREEN or 0}",
        f"m_showFpsCounter={settings.SHOW_INGAME_FPS_COUNTER or 0}",
    ]
    settings.get_config_path().parent.mkdir(parents=True, exist_ok=True)
    settings.get_config_path().write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")


def parse_env_string(spec: str) -> dict[str, str]:
    """Parse ``name=value;name2=value2`` into a dict for subprocess env."""
    if not spec.strip():
        return {}
    result: dict[str, str] = {}
    for part in spec.split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"invalid env entry (expected name=value): {part!r}")
        name, _, value = part.partition("=")
        name = name.strip()
        if not name:
            raise ValueError(f"invalid env entry (empty name): {part!r}")
        result[name] = value
    return result


def spawn_game_launcher(
    settings: Settings,
    launch_token: str,
    kernel_check_disable: bool,
    extra_env: dict[str, str] | None = None,
) -> subprocess.Popen:
    args = [str(settings.get_game_launcher_exe()), launch_token]
    if kernel_check_disable:
        args.append("kernel-check-disable")

    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW

    popen_kwargs: dict[str, Any] = {
        "args": args,
        "cwd": str(settings.LAUNCHER_ROOT),
        "creationflags": creationflags,
    }
    if extra_env:
        popen_kwargs["env"] = {**os.environ, **extra_env}

    return subprocess.Popen(**popen_kwargs)


def resolve_server_ip(
    settings: Settings,
    cli_server_ip: str | None,
    launch_data: dict[str, Any],
    *,
    offline: bool = False,
    proxy: bool = False,
) -> str:
    if cli_server_ip is not None and cli_server_ip.strip() != "":
        return cli_server_ip.strip()
    if offline or proxy:
        return "127.0.0.1"
    api_ip = launch_data.get("server_ip")
    if api_ip:
        return str(api_ip)
    return settings.DEFAULT_SERVER_IP


def main() -> int:
    settings = Settings()

    parser = argparse.ArgumentParser(
        description="Launch FA-EMU: fetch launch token, write config.ini, spawn GameLauncher.exe.",
    )
    parser.add_argument(
        "-p",
        "--game_exe",
        type=Path,
        default=settings.GAME_PATH,
        help="Full path to GAME.exe (written as game_path in config.ini)",
    )
    parser.add_argument(
        "-s",
        "--server-ip",
        default=None,
        help=f"Override emulator server IP (default: from API, else {settings.DEFAULT_SERVER_IP})",
    )
    parser.add_argument(
        "--session-token",
        default=None,
        help="Account session token (login uuid). Default: store.json next to launcher",
    )
    parser.add_argument(
        "--username", default=None, help="Login instead of store.json session"
    )
    parser.add_argument("--password", default=None, help="Password for --username")
    parser.add_argument(
        "--offline",
        default=False,
        action="store_true",
        help="Run the game in localhost mode",
    )
    parser.add_argument(
        "--proxy",
        default=False,
        action="store_true",
        help="Local ProudNet entry (127.0.0.1) with real launch token (transparent proxy)",
    )
    parser.add_argument(
        "--env",
        default=None,
        metavar="VAR=val;VAR2=val2",
        help="Extra environment variables for GameLauncher (semicolon-separated).",
    )
    args = parser.parse_args()

    if (args.username is None) != (args.password is None):
        print("error: --username and --password must be used together", file=sys.stderr)
        return 1

    game_exe = args.game_exe.resolve()
    if not game_exe.is_file():
        print(f"error: GAME.exe not found: {game_exe}", file=sys.stderr)
        return 1
    if not settings.get_game_launcher_exe().is_file():
        print(
            f"error: GameLauncher.exe not found: {settings.get_game_launcher_exe()}",
            file=sys.stderr,
        )
        return 1

    try:
        launch_data = dict()
        use_upstream_auth = not args.offline or args.proxy
        if use_upstream_auth:
            if args.username:
                account_token = login(settings, args.username, args.password)
            else:
                account_token = load_account_token(settings, args.session_token)

            launch_data = fetch_launch_credentials(settings, account_token)
            launch_token = str(launch_data["token"])
        else:
            launch_token = args.session_token or "localhost"

        server_ip = resolve_server_ip(
            settings,
            args.server_ip,
            launch_data,
            offline=args.offline,
            proxy=args.proxy,
        )
        kernel_check_disable = launch_data.get("kernel_check_disable") is True

        write_config(settings, game_exe, launch_token, server_ip)
        extra_env = parse_env_string(args.env) if args.env else {}
        extra_env = {**server_override_env(server_ip), **extra_env}
        proc = spawn_game_launcher(
            settings, launch_token, kernel_check_disable, extra_env=extra_env
        )
    except (RuntimeError, urllib.error.URLError, OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(
        f"config={settings.get_config_path()} game={game_exe} server={server_ip} "
        f"kernel_check_disable={kernel_check_disable} pid={proc.pid}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
