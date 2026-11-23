@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY="
if exist "%LOCALAPPDATA%\Programs\Python\Python39\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
if not defined PY if exist "C:\Python39\python.exe" set "PY=C:\Python39\python.exe"
if not defined PY (
  py -3.9 -c "import sys" >nul 2>nul && set "PY=py -3.9"
)
if not defined PY (
  python -c "import sys; assert sys.version_info[:2]==(3,9)" >nul 2>nul && set "PY=python"
)

if not defined PY (
  echo.
  echo [ERROR] Python 3.9 64-bit was not found.
  echo Please install Python 3.9 64-bit and add it to PATH.
  echo Download: https://www.python.org/downloads/release/python-3910/
  echo.
  pause
  exit /b 1
)

start "" %PY% main.py
