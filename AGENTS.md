# AGENTS.md

## Setup commands
- `uv sync`

## Usage
- `just` for list of commands
- `just <command> <args>` for commands

When used as a submodule, prefer this style (make sure parent "justfile" includes "mod controller").

- `just ctl` for list of commands
- `just ctl <command> <args>` for commands

### Supported commands

- `ping` - daemon status
- `processes` - list of running GAME.exe / GameLauncher.exe
- `status` - current session status
- `stages` - known stages + seen stages for current session
- `kill-all` - kills all running GAME.exe / GameLauncher.exe processes
- `copy-dll [dll_config=]` - copies fresh dll to the game directory. dll_config=debug/release (debug by default)
- `copy-logs` - copies logs from game directory to "logs/runs/`<run_id>`/"
- `copy-logs-run <run_id>` - copies logs from game directory with specified run_id.
- `launch [server_ip=]` - exchanges the credentials for token and starts the game. `<server_ip>` is overriden if not empty. The game logs are cleared before start.
- `launch-offline [server_ip=]` - starts the game without fetching the credentials (auth disabled).
- `wait-menu` - blocks until game stage "main_menu"
- `wait-stage <stage> [timeout=]` - blocks until specific game stage. timeout=120 by default.
- `run-session [dll_config=]` - chains `copy-dll`, `launch`, `wait-menu`, `kill-all` and `copy-logs`. dll_config=debug by default.
- `run-session-offline [dllconfig=] [server_ip=]` - the same chain except `launch` is replaced with `launch-offline [server_ip]`. server_ip=127.0.0.1 by default.

### Commands not working at the moment
- `kill` - kills the running GAME.exe instance. The PID is not captured correctly, so does nothing ATM.
- `launch` and `run-session` - auth server is down, the game stucks at "connecting_to_server" stage.

### Commands available only with human approval

- `stop` - stops the daemon. Daemon can be only started by human, so this action alone is destructive for workflow.
- `daemon` and `deamon-bg`. Daemon requires elevation with UAC, so only human can do this.