# AGENTS.md

## Setup commands
- `uv sync`

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
- `copy-dll [dll_config=]` - copies fresh dll to the game directory. dll_config=debug/release (debug by default)
- `clear-logs` - deletes shipping log files next to GAME.exe (per `game_log_files` in ctl.yaml)
- `copy-logs` - copies shipping logs into `logs/runs/<run_id>/` (names from `game_log_files`)
- `copy-logs-run <run_id>` - copies logs from game directory with specified run_id.
- `launch [server_ip=]` - clear-logs, then exchange credentials and start the game. `<server_ip>` is overriden if not empty.
- `launch-offline [server_ip=]` - clear-logs, then start the game without fetching credentials (auth disabled).
- `wait-menu` - blocks until game stage `server_ready` (alias for `wait-stage server_ready`)
- `wait-stage <stage> [timeout=]` - blocks until specific game stage. timeout=120 by default.
### Commands available only with human approval

- `stop` - stops the daemon. Daemon can be only started by human, so this action alone is destructive for workflow.
- `daemon` and `deamon-bg`. Daemon requires elevation with UAC, so only human can do this.
