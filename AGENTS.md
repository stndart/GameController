# AGENTS.md

## Setup commands
- `uv sync`

## Usage (from game repo root)

- `just --list` - all recipes; controller client commands are under **`ctl::`**
- **`just ctl::<command>`** - e.g. `just ctl::ping`, `just ctl::copy-dll`, `just ctl::launch-offline`, `just ctl::wait-stage shard_choice`, `just ctl::kill-all`
- `just ping` at repo root is an **alias** for `just ctl::ping` only; do **not** assume `just copy-dll` / `just kill-all` exist at root.

When this tree is a submodule, parent `justfile` should `mod ctl` the same way.

### Supported commands (invoke as `just ctl::<name>`)

- `ping` - daemon status
- `processes` - list of running GAME.exe / GameLauncher.exe
- `status` - current session status
- `stages` - known stages + seen stages for current session
- `kill` - kills the running GAME.exe instance.
- `kill-all` - kills all running GAME.exe / GameLauncher.exe processes
- `copy-dll [dll_config=]` - copies fresh dll to the game directory. dll_config=debug/release (debug by default)
- `copy-logs` - copies `logs.txt`, `netlogs.txt`, and `proudnet_tcp.txt` from the game directory to `logs/runs/<run_id>/` (`game_logs.txt`, `game_netlogs.txt`, `game_proudnet_tcp.txt`)
- `copy-logs-run <run_id>` - copies logs from game directory with specified run_id.
- `copy-proudnet-tcp` - copies only `proudnet_tcp.txt` next to GAME.exe into the current run dir
- `copy-proudnet-tcp-run <run_id>` - same with an explicit run id
- `clear-proudnet-tcp` - deletes `proudnet_tcp.txt` next to GAME.exe (also cleared on `launch` / `launch-offline` with the other shipping logs)
- `launch [server_ip=]` - exchanges the credentials for token and starts the game. `<server_ip>` is overriden if not empty. The game logs are cleared before start.
- `launch-offline [server_ip=]` - starts the game without fetching the credentials (auth disabled).
- `wait-menu` - blocks until game stage `server_ready` (shard picker done; alias for `wait-stage server_ready`)
- `wait-stage <stage> [timeout=]` - blocks until specific game stage. timeout=120 by default.
- `run-session [dll_config=]` - chains `copy-dll`, `launch`, `wait-menu` (`server_ready`), `kill-all` and `copy-logs`. dll_config=debug by default.
- `run-session-offline [dllconfig=] [server_ip=]` - the same chain except `launch` is replaced with `launch-offline [server_ip]`. server_ip=127.0.0.1 by default.

### Commands not working at the moment
- `launch` and `run-session` - auth server is down, the game stucks at "connecting_to_server" stage.

### Commands available only with human approval

- `stop` - stops the daemon. Daemon can be only started by human, so this action alone is destructive for workflow.
- `daemon` and `deamon-bg`. Daemon requires elevation with UAC, so only human can do this.