# FA-EMU launch control via controller/ (pip install -e . → `ctl` on PATH).
#
# One-time elevated daemon:
#   just daemon-bg
# Then non-elevated client commands:
#   just ping
#   just launch
#
# Game path: copy launch.yaml.example → launch.yaml (or ctl -p / MCP game_exe).

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

ctl := "uv run ctl"

default:
    @just --list

# --- daemon (elevated; gsudo / UAC once) ---

daemon:
    gsudo {{ctl}} -d

daemon-bg:
    gsudo {{ctl}} -d --background

# --- client (non-elevated; requires daemon) ---

ping:
    {{ctl}} ping

processes:
    {{ctl}} processes

status:
    {{ctl}} status

stages:
    {{ctl}} stages

stop:
    {{ctl}} stop

kill:
    {{ctl}} kill

kill-all:
    {{ctl}} kill --all

# e.g. just copy-dll debug-diag-no-map  →  build/msvc-x86-debug-diag-no-map/bin/TheGame.dll
copy-dll dll_config="debug":
    {{ctl}} copy-dll --dll-config {{dll_config}}

clear-logs:
    {{ctl}} clear-logs

copy-logs:
    {{ctl}} copy-logs

copy-logs-run run_id:
    {{ctl}} copy-logs --run-id {{run_id}}

# Pass ctl flags through, e.g. just launch --env TEST_VAR=kek  or  just launch -s 1.2.3.4
# Empty -s (just launch -s "") means no server IP override (API / defaults).
launch *flags:
    {{ctl}} launch {{flags}}

relaunch *flags:
    {{ctl}} copy-dll
    {{ctl}} launch {{flags}}

# Local entry (127.0.0.1) + real auth for transparent proxy (just server::proxy).
launch-offline *flags:
    {{ctl}} launch --proxy {{flags}}

wait-menu:
    {{ctl}} wait-for-stage shard_select --timeout 120

wait-lobby:
    just wait-stage shard_select 120
    just send nav_pass_shard_select
    just wait-stage lobby 10

wait-s delay="5":
    #!python
    import time
    time.sleep(float("{{delay}}"))

wait-stage stage timeout="120":
    {{ctl}} wait-for-stage {{stage}} --timeout {{timeout}}

commands:
    {{ctl}} commands

send message:
    {{ctl}} send {{message}}
