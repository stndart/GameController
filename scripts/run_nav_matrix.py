#!/usr/bin/env python3
"""Run nav/RMI ctl experiments; requires elevated daemon (reloads ctl.env each launch)."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

CTL_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = CTL_DIR / "ctl.env"
GAME = r"G:\Games\FA\FA-EMU\Shipping\GAME.exe"

CASES: list[tuple[str, str, str, str, list[str]]] = [
    ("baseline", "create_room", "", "lobby", ["mode=create_room", '"phase":"lobby"']),
    # Floor send (sub_A0B290) from DLL still AVs — expect FAIL until wrapper is RE'd.
    ("chat_ping", "create_room", "chat_ping", "lobby", ["0x3AD2", "global chat"]),
    ("quick_match", "create_room", "quick_match", "lobby", ["0x3EE4", "quick match"]),
    ("exit_lobby", "exit_lobby", "", "server_ready", ["exit_to_server", '"phase":"server_ready"']),
    (
        "leave_room",
        "create_room",
        "leave_room",
        "room",
        ["0x3F45", "leave room"],
    ),
]


def write_ctl_env(nav_auto: str, nav_action: str) -> None:
    lines: list[str] = []
    if nav_auto:
        lines.append(f"thegame_nav_auto={nav_auto}")
    if nav_action:
        lines.append(f"thegame_nav_action={nav_action}")
    ENV_FILE.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def ctl(*args: str, timeout: float = 130.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "ctl", *args],
        cwd=CTL_DIR,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def main() -> int:
    ping = ctl("ping", timeout=10.0)
    if ping.returncode != 0:
        print("ctl ping failed", ping.stderr, file=sys.stderr)
        return 1
    body = json.loads(ping.stdout)
    if not body.get("elevated"):
        print("daemon not elevated — run: just ctl::daemon-bg", file=sys.stderr)
        return 1

    ctl("kill", "--all", timeout=30.0)
    time.sleep(1.0)

    results: list[tuple[str, str, bool, str]] = []

    for name, nav_auto, nav_action, wait_stage, needles in CASES:
        write_ctl_env(nav_auto, nav_action)
        nav_flag = ["--nav-auto", nav_auto] if nav_auto else []
        launch = ctl(
            "launch",
            "-p",
            GAME,
            "-s",
            "127.0.0.1",
            "--offline",
            *nav_flag,
            timeout=130.0,
        )
        if launch.returncode != 0:
            results.append((name, "-", False, f"launch: {launch.stderr or launch.stdout}"))
            continue
        run_id = json.loads(launch.stdout).get("run_id", "?")
        wait_timeout = "180" if wait_stage == "room" else "120"
        wait = ctl(
            "wait-for-stage",
            wait_stage,
            "--timeout",
            wait_timeout,
            timeout=float(wait_timeout) + 15.0,
        )
        ctl("copy-logs", "-p", GAME, timeout=30.0)
        events = CTL_DIR / "logs" / "runs" / str(run_id) / "events.jsonl"
        text = events.read_text(encoding="utf-8", errors="replace") if events.is_file() else ""
        crashed = "0xC0000005" in text or '"phase":"diag_disconnected"' in text
        ok = wait.returncode == 0 and not crashed
        for n in needles:
            if n not in text:
                ok = False
        note = "ok" if ok else f"wait={wait.returncode} crash={crashed}"
        results.append((name, run_id, ok, note))
        ctl("kill", "--all", timeout=30.0)
        time.sleep(2.0)

    print("\n=== nav matrix ===")
    for name, run_id, ok, note in results:
        print(f"{'PASS' if ok else 'FAIL':4} {name:12} {run_id}  {note}")
    return 0 if all(r[2] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
