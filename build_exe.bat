@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

rem 一键打包：onedir + windowed，产物在 dist\DATA SHIFT\DATA SHIFT.exe
rem 分发时把整个 dist\DATA SHIFT\ 文件夹压成 zip，不能只拷 exe

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] .venv\Scripts\python.exe not found. Run from repo root.
    pause
    exit /b 1
)

echo [1/2] Building "DATA SHIFT" ...
rem 2026-11-25 起要带中文字体（仓库唯一的外部素材）；音效仍是现场合成，没有音频文件。
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onedir --windowed ^
    --name "DATA SHIFT" --add-data "src\assets;src\assets" ^
    --distpath dist --workpath build src\main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Re-run with --console to see the traceback.
    pause
    exit /b 1
)

echo.
echo [2/2] Done: dist\DATA SHIFT\DATA SHIFT.exe
pause
