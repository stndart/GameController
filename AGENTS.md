# AGENTS.md

## Setup commands
- `uv sync`

## MCP (Cursor / Claude Desktop)

Client commands are also exposed as MCP tools (no `just` / justfile path required). The elevated **daemon must already be running** (check with `ping` command).

**Setup:** `uv sync` once (creates `.venv` with `ctl-mcp`).

**When this repo is the Cursor workspace root**, use the committed [`.cursor/mcp.json`](.cursor/mcp.json) (launcher script + `${workspaceFolder}`). Reload MCP in Cursor. Tools are prefixed with `ctl_`.

**When configuring `~/.cursor/mcp.json` globally** (any workspace), `uv run ctl-mcp` without a project path fails (`program not found`). Pin the project:

```json
"game-controller": {
  "command": "C:\\Program Files\\Python311\\Scripts\\uv.exe",
  "args": [
    "run",
    "--project",
    "C:\\path\\to\\controller\\",
    "ctl-mcp"
  ]
}
```

Or point at the venv entrypoint after `uv sync`:

```json
"command": "C:\\path\\to\\controller\\.venv\\Scripts\\ctl-mcp.exe",
"args": []
```

Do **not** run `mcp_server.py` with system Python - dependencies live in this repo's `.venv` only.

`ctl_stop`, `daemon`, and `daemon-bg` are intentionally **not** exposed over MCP (human-only per below).

## Usage

- `just --list` - all recipes in this repo's [justfile](justfile)

### Config

- [`ctl.yaml`](ctl.yaml) - pipe names, DLL paths, `game_log_files` (copy from [`ctl.yaml.example`](ctl.yaml.example))
- [`launch.yaml`](launch.yaml) - `GAME_PATH`, `LAUNCHER_ROOT`, optional `DLL_BUILD_ROOT` (copy from [`launch.yaml.example`](launch.yaml.example)); used when `ctl` / `just` omit `-p`
- `launch` / `relaunch` / `launch-offline` run `clear-logs` then start the game (no extra log clearing inside launch RPC)

### Supported commands

MCP tools mirror root `just` recipes.

- `ping` - daemon status
- `processes` - list of running GAME.exe / GameLauncher.exe
- `status` - current session status
- `stages` - known stages + seen stages for current session
- `kill` - kills the tracked GAME.exe session
- `kill-all` - kills all running GAME.exe / GameLauncher.exe processes
- `copy-dll [dll_config=debug]` - CMake preset or `msvc-x86-*` name → `build/msvc-x86-<preset>/bin/TheGame.dll`
- `clear-logs` - deletes shipping log files next to GAME.exe (per `game_log_files` in ctl.yaml)
- `copy-logs` - copies shipping logs into `logs/runs/<run_id>/`
- `copy-logs-run <run_id>` - copies logs for a specific run id
- `launch` - clear-logs, then exchange credentials and start; pass ctl flags (e.g. `-s 1.2.3.4`, `--env VAR=val`)
- `relaunch` - `copy-dll` then `launch` (same optional ctl flags as `launch`)
- `launch-offline` - clear-logs, then `ctl launch --proxy` (local entry + real auth for transparent proxy)
- `wait-menu` - blocks until `shard_select` (alias for `wait-stage shard_select`)
- `wait-stage <stage> [timeout=120]` - blocks until a diagnostics stage
- `wait-lobby` - `wait-stage shard_select`, `send nav_pass_shard_select`, `wait-stage lobby`
- `commands` - list handler commands the game supports (handler pipe)
- `send <message>` - send a line-oriented command on the handler pipe (e.g. `nav_pass_shard_select`); game must reply `ok`

### Commands available only with human approval

- `stop` - stops the daemon
- `daemon`, `daemon-bg` - start elevated daemon (UAC / gsudo)
