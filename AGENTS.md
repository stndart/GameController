# AGENTS.md

## Setup commands
- `uv sync`

## MCP (Cursor / Claude Desktop)

Client commands are also exposed as MCP tools (no `just` / justfile path required). The elevated **daemon must already be running** (`gsudo ctl -d` or `just daemon-bg`).

**Setup:** `uv sync` once (creates `.venv` with `ctl-mcp`).

**When this repo is the Cursor workspace root**, use the committed [`.cursor/mcp.json`](.cursor/mcp.json) (launcher script + `${workspaceFolder}`). Reload MCP in Cursor. Tools are prefixed with `ctl_`.

**When configuring `~/.cursor/mcp.json` globally** (any workspace), `uv run ctl-mcp` without a project path fails (`program not found`). Pin the project:

```json
"game-controller": {
  "command": "C:\\Program Files\\Python311\\Scripts\\uv.exe",
  "args": [
    "run",
    "--project",
    "C:\\Users\\Svyat\\Desktop\\RE\\GameController",
    "ctl-mcp"
  ]
}
```

Or point at the venv entrypoint after `uv sync`:

```json
"command": "C:\\Users\\Svyat\\Desktop\\RE\\GameController\\.venv\\Scripts\\ctl-mcp.exe",
"args": []
```

Do **not** run `mcp_server.py` with system Python — dependencies live in this repo’s `.venv` only.

`ctl_stop` / daemon start are intentionally **not** exposed over MCP (human-only per below).

## Usage (from game repo root)

- `just --list` - all recipes; controller client commands are under **`ctl::`**
- **`just ctl::<command>`** - e.g. `just ctl::ping`, `just ctl::copy-dll`, `just ctl::launch-offline`, `just ctl::wait-stage shard_choice`, `just ctl::kill-all`
- `just ping` at repo root is an **alias** for `just ctl::ping` only; do **not** assume `just copy-dll` / `just kill-all` exist at root.

When this tree is a submodule, parent `justfile` should `mod ctl` the same way.

### Config

- [`ctl.yaml`](ctl.yaml) — pipe names, DLL paths, `game_log_files` (copy from [`ctl.yaml.example`](ctl.yaml.example))
- `launch` runs `clear-logs` then starts the game (no log clearing inside launch RPC)

### Supported commands (invoke as `just ctl::<name>`)

- `ping` - daemon status
- `processes` - list of running GAME.exe / GameLauncher.exe
- `status` - current session status
- `stages` - known stages + seen stages for current session
- `kill` - kills the running GAME.exe instance.
- `kill-all` - kills all running GAME.exe / GameLauncher.exe processes
- `copy-dll [dll_config=debug]` - any CMake build preset (e.g. `debug-diag-no-map`) or full `msvc-x86-*` name; resolves to `build/msvc-x86-<preset>/bin/TheGame.dll`
- `clear-logs` - deletes shipping log files next to GAME.exe (per `game_log_files` in ctl.yaml)
- `copy-logs` - copies shipping logs into `logs/runs/<run_id>/` (names from `game_log_files`)
- `copy-logs-run <run_id>` - copies logs from game directory with specified run_id.
- `launch [server_ip=]` - clear-logs, then exchange credentials and start the game. `<server_ip>` is overriden if not empty.
- `launch-offline [server_ip=]` - clear-logs, then start the game without fetching credentials (auth disabled).
- `wait-menu` - blocks until game stage `server_ready` (alias for `wait-stage server_ready`)
- `wait-stage <stage> [timeout=]` - blocks until specific game stage. timeout=120 by default.
- `commands` - list handler commands the game supports (handler pipe)
- `send <message>` - send a line-oriented command to the game on the handler pipe (e.g. `nav-menu`); game must reply `ok`
### Commands available only with human approval

- `stop` - stops the daemon. Daemon can be only started by human, so this action alone is destructive for workflow.
- `daemon` and `deamon-bg`. Daemon requires elevation with UAC, so only human can do this.
