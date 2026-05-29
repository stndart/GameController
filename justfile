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

copy-dll dll_config="debug":
    {{ctl}} copy-dll --dll-config {{dll_config}} -p "{{game_exe}}"

copy-logs:
    {{ctl}} copy-logs -p "{{game_exe}}"

copy-logs-run run_id:
    {{ctl}} copy-logs --run-id {{run_id}} -p "{{game_exe}}"

launch server_ip="":
    {{ctl}} launch -p "{{game_exe}}" -s "{{server_ip}}"

launch-offline server_ip="127.0.0.1":
    {{ctl}} launch -p "{{game_exe}}" -s "{{server_ip}}" --offline

# Offline launch with autonav (writes TheGame.nav_auto; passes --nav-auto to daemon).
launch-offline-nav server_ip="127.0.0.1":
    {{ctl}} launch -p "{{game_exe}}" -s "{{server_ip}}" --offline --nav-auto create_room

# Offline launch: enter lobby then exit to shard picker (THEGAME_NAV_AUTO=exit_lobby).
launch-offline-exit-nav server_ip="127.0.0.1":
    {{ctl}} launch -p "{{game_exe}}" -s "{{server_ip}}" --offline --nav-auto exit_lobby

wait-menu:
    {{ctl}} wait-for-stage server_ready --timeout 120

wait-stage stage timeout="120":
    {{ctl}} wait-for-stage {{stage}} --timeout {{timeout}}

run-session dll_config="debug":
    {{ctl}} copy-dll --dll-config {{dll_config}} -p "{{game_exe}}"
    {{ctl}} launch -p "{{game_exe}}"
    {{ctl}} wait-for-stage server_ready --timeout 120
    {{ctl}} kill --all
    {{ctl}} copy-logs -p "{{game_exe}}"

run-session-offline dll_config="debug" server_ip="127.0.0.1":
    {{ctl}} copy-dll --dll-config {{dll_config}} -p "{{game_exe}}"
    {{ctl}} launch -p "{{game_exe}}" -s "{{server_ip}}" --offline
    {{ctl}} wait-for-stage server_ready --timeout 180
    {{ctl}} kill --all
    {{ctl}} copy-logs -p "{{game_exe}}"

# Nav/RMI matrix (reloads ctl.env each launch; needs elevated daemon + fresh Python).
run-nav-matrix:
    uv run python scripts/run_nav_matrix.py

# exit_lobby autonav: lobby → server_ready, then collect logs.
run-exit-lobby-test dll_config="debug" server_ip="127.0.0.1" timeout="180":
    {{ctl}} copy-dll --dll-config {{dll_config}} -p "{{game_exe}}"
    {{ctl}} launch -p "{{game_exe}}" -s "{{server_ip}}" --offline --nav-auto exit_lobby
    {{ctl}} wait-for-stage server_ready --timeout {{timeout}}
    {{ctl}} kill --all
    {{ctl}} copy-logs -p "{{game_exe}}"
