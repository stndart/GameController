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

# debug | release only; other presets → copy-dll-any <build_dir>
copy-dll dll_config="debug":
    {{ctl}} copy-dll --dll-config {{dll_config}} -p "{{game_exe}}"

copy-dll-debug:
    {{ctl}} copy-dll --dll-config debug -p "{{game_exe}}"

copy-dll-release:
    {{ctl}} copy-dll --dll-config release -p "{{game_exe}}"

# e.g. just ctl::copy-dll-any msvc-x86-debug-nohooks  →  ../build/msvc-x86-debug-nohooks/bin/TheGame.dll
copy-dll-any build_dir:
    {{ctl}} copy-dll --dll-source "../build/{{build_dir}}/bin/TheGame.dll" -p "{{game_exe}}"

clear-logs:
    {{ctl}} clear-logs -p "{{game_exe}}"

copy-logs:
    {{ctl}} copy-logs -p "{{game_exe}}"

copy-logs-run run_id:
    {{ctl}} copy-logs --run-id {{run_id}} -p "{{game_exe}}"

launch server_ip="":
    {{ctl}} launch -p "{{game_exe}}"{{ if server_ip != '' { ' -s ' + server_ip } else { '' } }}

# Local entry (127.0.0.1) + real auth for transparent proxy (just server::proxy).
launch-offline server_ip="127.0.0.1":
    {{ctl}} launch -p "{{game_exe}}" -s "{{server_ip}}" --proxy

# Python ProudNet emulator (just server::ensure); localhost launch token.
launch-dummy server_ip="127.0.0.1":
    {{ctl}} launch -p "{{game_exe}}" -s "{{server_ip}}" --offline

wait-menu:
    {{ctl}} wait-for-stage server_ready --timeout 120

wait-stage stage timeout="120":
    {{ctl}} wait-for-stage {{stage}} --timeout {{timeout}}

commands:
    {{ctl}} commands

send message:
    {{ctl}} send {{message}}
