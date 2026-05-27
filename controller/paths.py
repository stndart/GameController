"""Log and run directory paths for controller sessions."""

from __future__ import annotations

import json
import re
import secrets
from pathlib import Path

from config import REPO_ROOT

LOGS_ROOT = REPO_ROOT / "logs"
CTL_LOGS_DIR = LOGS_ROOT / "ctl"
RUNS_DIR = LOGS_ROOT / "runs"

RUN_SEQ_WIDTH = 3
_RUN_DIR_RE = re.compile(rf"^(\d{{{RUN_SEQ_WIDTH}}})_(.+)$")

LAST_RUN_FILE = CTL_LOGS_DIR / "last_run.json"

EVENTS_FILE = "events.jsonl"
META_FILE = "meta.json"
GAME_LOGS_FILE = "game_logs.txt"
GAME_NETLOGS_FILE = "game_netlogs.txt"
SHIPPING_LOGS_FILE = "logs.txt"
SHIPPING_NETLOGS_FILE = "netlogs.txt"


def ensure_logs_dirs() -> None:
    CTL_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)


def _next_run_seq() -> int:
    ensure_logs_dirs()
    max_seq = -1
    for entry in RUNS_DIR.iterdir():
        if not entry.is_dir():
            continue
        m = _RUN_DIR_RE.match(entry.name)
        if m:
            max_seq = max(max_seq, int(m.group(1)))
    return max_seq + 1


def new_run_id() -> str:
    return f"{_next_run_seq():0{RUN_SEQ_WIDTH}d}_{secrets.token_hex(4)}"


def run_dir_name(run_id: str) -> str:
    """Resolve canonical run folder name (NNN_<suffix> or legacy bare id)."""
    if (RUNS_DIR / run_id).is_dir():
        return run_id
    m = _RUN_DIR_RE.match(run_id)
    suffix = m.group(2) if m else run_id
    matches = [p for p in RUNS_DIR.glob(f"*_{suffix}") if p.is_dir()]
    if len(matches) == 1:
        return matches[0].name
    if len(matches) > 1:
        names = ", ".join(p.name for p in matches)
        raise ValueError(f"ambiguous run_id {run_id!r}: {names}")
    if m:
        return run_id
    return run_id


def run_dir(run_id: str) -> Path:
    path = RUNS_DIR / run_dir_name(run_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def events_path(run_id: str) -> Path:
    return run_dir(run_id) / EVENTS_FILE


def meta_path(run_id: str) -> Path:
    return run_dir(run_id) / META_FILE


def write_last_run(run_id: str, run_dir_path: Path) -> None:
    ensure_logs_dirs()
    payload = {"run_id": run_id, "run_dir": str(run_dir_path.resolve())}
    LAST_RUN_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_last_run() -> dict | None:
    if not LAST_RUN_FILE.is_file():
        return None
    return json.loads(LAST_RUN_FILE.read_text(encoding="utf-8"))


def resolve_run_id(run_id: str | None) -> str:
    if run_id:
        return run_dir_name(run_id)
    last = read_last_run()
    if not last or not last.get("run_id"):
        raise ValueError(
            "no run_id and no last run; launch a session first or pass run_id"
        )
    return run_dir_name(str(last["run_id"]))


def merge_meta(run_id: str, patch: dict) -> None:
    path = meta_path(run_id)
    meta: dict = {}
    if path.is_file():
        meta = json.loads(path.read_text(encoding="utf-8"))
    meta.update(patch)
    path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
