@echo off
REM Adds your API key to this machine AND to the GitHub nightly run, in one step.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\add-key.ps1" %*
