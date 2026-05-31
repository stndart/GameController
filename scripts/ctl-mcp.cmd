@echo off
setlocal
set "REPO_ROOT=%~dp0.."
cd /d "%REPO_ROOT%"

if exist "%REPO_ROOT%\.venv\Scripts\ctl-mcp.exe" (
  "%REPO_ROOT%\.venv\Scripts\ctl-mcp.exe" %*
  exit /b %ERRORLEVEL%
)

where uv >nul 2>&1
if %ERRORLEVEL% equ 0 (
  uv run ctl-mcp %*
  exit /b %ERRORLEVEL%
)

echo Run 'uv sync' in %REPO_ROOT% first. 1>&2
exit /b 1
