# FA-EMU launch control via controller/ (pip install -e . → `ctl` on PATH).
#
# One-time elevated daemon:
#   just daemon-bg
# From repo root (parent justfile has `mod ctl`):
#   just ctl::ping
#   just ctl::run-session-offline
# (`just ping` at root is an alias to ctl::ping)

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

ctl := "uv run ctl"
game_exe := 'G:\Games\FA\FA-EMU\Shipping\GAME.exe'

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

# e.g. just ctl::copy-dll debug-diag-no-map  →  build/msvc-x86-debug-diag-no-map/bin/TheGame.dll
copy-dll dll_config="debug":
    {{ctl}} copy-dll --dll-config {{dll_config}} -p "{{game_exe}}"

clear-logs:
    {{ctl}} clear-logs -p "{{game_exe}}"

copy-logs:
    {{ctl}} copy-logs -p "{{game_exe}}"

copy-logs-run run_id:
    {{ctl}} copy-logs --run-id {{run_id}} -p "{{game_exe}}"

# Pass ctl flags through, e.g. just launch --env TEST_VAR=kek  or  just launch -s 1.2.3.4
# Empty -s (just launch -s "") means no server IP override (API / defaults).
launch *flags:
    {{ctl}} launch -p "{{game_exe}}" {{flags}}

relaunch *flags:
    {{ctl}} kill
    {{ctl}} launch -p "{{game_exe}}" {{flags}}

# Local entry (127.0.0.1) + real auth for transparent proxy (just server::proxy).
launch-offline *flags:
    {{ctl}} launch -p "{{game_exe}}" --proxy {{flags}}

# Python ProudNet emulator (just server::ensure); localhost launch token.
launch-dummy *flags:
    {{ctl}} launch -p "{{game_exe}}" --offline {{flags}}

wait-menu:
    {{ctl}} wait-for-stage shard_select --timeout 120

run-e2e-lobby:
    just ping
    just copy-dll
    just launch
    just wait-stage shard_select 120
    just wait-s 8
    just send nav_pass_shard_select
    just wait-s 15
    just wait-stage lobby 120
    just copy-logs

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
