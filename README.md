# TheGameController

Elevated Windows daemon plus a non-elevated CLI for launching FA-EMU with TheGame.dll diagnostics. Commands are **composable** (copy DLL → launch → wait for stage → kill → copy logs); there is no monolithic `diagnostics-run` RPC.

## Setup

```powershell
uv sync
```

Credentials are read from `store.json` / `launch.yaml` (`launch_game`). To get `store.json`, launch the game once with "official" Fa-emu launcher, the `store.json` file will appear next to the launcher.

### MCP (optional)

Run `uv sync`, then open this folder as the Cursor workspace (uses `[.cursor/mcp.json](.cursor/mcp.json)`) or add a `game-controller` server to `~/.cursor/mcp.json` with `uv run --project <path-to-this-repo> ctl-mcp` (see [AGENTS.md](AGENTS.md)). Requires the elevated daemon; do not use bare system `python` on `mcp_server.py`.

Config files (optional):


| File                  | Purpose                                                             |
| --------------------- | ------------------------------------------------------------------- |
| `ctl.yaml`            | Pipe names, DLL paths, `game_log_files` (`Settings` in `config.py`) |
| `ctl.yaml.example`    | Defaults; copy to `ctl.yaml` and edit                               |
| `launch.yaml`         | Game path, launcher root, DLL build root (`launch_game.Settings`)   |
| `launch.yaml.example` | Defaults; copy to `launch.yaml` and edit                            |


`game_log_files` in `ctl.yaml` is re-read on each `copy-logs` / `clear-logs` RPC (`fresh_settings()`).

**One-time elevated daemon** (UAC / gsudo):

```powershell
gsudo ctl -d # or `just daemon`
# or detached:
gsudo ctl -d --background # or `just daemon-bg`
```

Daemon prints `[stage] ...` lines when the game reports new `game_stage` phases.

## Typical workflow

```powershell
just relaunch
just wait-menu
just kill
just copy-logs
```

Artifacts land in `logs/runs/<run_id>/`:


| File           | Content                                                      |
| -------------- | ------------------------------------------------------------ |
| `events.jsonl` | NDJSON diagnostics events from the DLL                       |
| `meta.json`    | Run metadata, `game_stages`, progress                        |
| `game_*.txt`   | Copied from shipping dir (`copy-logs`, per `game_log_files`) |


`logs/ctl/last_run.json` points at the latest run for `copy-logs` without `--run-id`.

## Stages

Known phases (see `stages.py`)


| Stage                  | When                                                          |
| ---------------------- | ------------------------------------------------------------- |
| `started`              | Diagnostics pipe connected                                    |
| `intro`                | CGameIntro onPreProcess                                       |
| `login`                | CGameLogin onPreProcess                                       |
| `connecting_to_server` | TCPSocket::Connect :7000                                      |
| `shard_select`         | Shard picker UI (`CGameServer` onPreProcess end @ `0x4347CC`) |
| `lobby`                | Main menu (chat, Quick/Custom match)                          |
| `room_list`            | Custom match room list                                        |
| `party_room`           | Party / matchmaking room                                      |
| `room`                 | Waiting room                                                  |
| `char_select`          | Character select                                              |
| `map_loading`          | Map load                                                      |
| `in_game`              | In match                                                      |


```powershell
ctl stages                       # catalog + stages seen this session
ctl wait-for-stage shard_select  # blocks this RPC until stage or timeout
just wait-menu                   # alias for wait-stage shard_select
just wait-lobby                  # shard_select → nav_pass_shard_select → lobby
```

`wait-for-stage` only blocks the **client connection** handling that request; other commands can be issued from another terminal if needed (the daemon serves one RPC at a time per connection).

Exit code `1` if the stage was not reached before `--timeout` (default 120s).

### Handler pipe

The game DLL connects to `handler_pipe_name` in `ctl.yaml` (default `thegame-handler`) as a named-pipe **client** on a duplex pipe. Protocol: one UTF-8 line per message, `\n`-terminated.

- Daemon → game: command line (e.g. `nav-menu`, or `commands` to list handlers).
- Game → daemon: one response line. Success for normal commands is `ok`. For `commands`, a comma-separated list of handler names (e.g. `nav-menu,shard-choice`).
- `handler_response_timeout` in `ctl.yaml` (default 30s) limits how long the daemon waits for a response.

`ctl send nav-menu` / `just send nav-menu` sends a command and requires `ok`. `ctl commands` / `just commands` sends `commands` and returns the parsed list in the RPC JSON (`handlers`). Fails if no game client is connected, the peer disconnects, the response times out, or `send` gets a non-`ok` line; the daemon keeps running.

## Troubleshooting

- **daemon not running** - start with `gsudo ctl -d`; client connect times out after 30s by default.
- **TheGame.dll not found** - build diagnostics dll from [here](https://github.com/stndart/TheGame) and copy to the game directory.
- **wait-for-stage times out** - watch daemon `[stage]` logs; increase `--timeout` or confirm the hooked build is loaded. If stages stop after `started`, check daemon did not log `diag_disconnected` immediately.
- **No last run for copy-logs** - run `launch` first or pass `--run-id`.

