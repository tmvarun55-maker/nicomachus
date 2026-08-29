@echo off
REM Launcher so `nicomachus ...` works from any directory.
REM With no arguments it opens the interactive session.
setlocal
set "NICO_HOME=%~dp0"
pushd "%NICO_HOME%"
if "%~1"=="" (
    python -m nicomachus serve
) else (
    python -m nicomachus %*
)
set "RC=%ERRORLEVEL%"
popd
endlocal & exit /b %RC%
