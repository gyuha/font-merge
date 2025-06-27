@echo off
REM Windows batch script for building font-merge application

echo Font-Merge Build Script for Windows
echo ===================================

REM Check if uv is available
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: uv is not installed. Please install uv first.
    exit /b 1
)

REM Parse command line arguments
if "%1"=="--clean" (
    goto clean
) else if "%1"=="--help" (
    goto help
) else if "%1"=="-h" (
    goto help
) else (
    goto build
)

:clean
echo Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec
if exist __pycache__ rmdir /s /q __pycache__
echo Clean completed.
goto end

:help
echo Usage: %0 [--clean^|--help]
echo   --clean  Clean build artifacts
echo   --help   Show this help message
goto end

:build
echo Installing PyInstaller...
uv add pyinstaller

echo Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec
if exist __pycache__ rmdir /s /q __pycache__

echo Building Windows executable...
set ICON_FILE=
if exist assets\icon.ico set ICON_FILE=--icon=assets\icon.ico

uv run pyinstaller --onefile --windowed --name "FontMerge" %ICON_FILE% --add-data "src;src" src\font_merge\main.py

echo Build completed! Check the dist\ directory for FontMerge.exe
goto end

:end