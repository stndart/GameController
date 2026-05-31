# MCP launcher: run from any cwd; uses this repo's uv project / .venv.
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

$venvMcp = Join-Path $RepoRoot ".venv\Scripts\ctl-mcp.exe"
if (Test-Path $venvMcp) {
    & $venvMcp @args
    exit $LASTEXITCODE
}

if (Get-Command uv -ErrorAction SilentlyContinue) {
    & uv run ctl-mcp @args
    exit $LASTEXITCODE
}

Write-Error "No .venv\Scripts\ctl-mcp.exe and 'uv' not on PATH. Run 'uv sync' in: $RepoRoot"
exit 1
