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
if exist icon.ico set ICON_FILE=--icon=icon.ico
if exist icon.png set ICON_FILE=--icon=icon.png
if exist assets\icon.ico set ICON_FILE=--icon=assets\icon.ico
if exist assets\icon.png set ICON_FILE=--icon=assets\icon.png

uv run pyinstaller --onefile --windowed --name "FontMerge" %ICON_FILE% --add-data "src;src" src\font_merge\main.py

echo Build completed! Check the dist\ directory for FontMerge.exe

echo.
echo Creating installer package...

REM Check if Inno Setup is available
where iscc >nul 2>nul
if %errorlevel% neq 0 (
    echo Warning: Inno Setup Compiler (iscc) not found in PATH.
    echo Please install Inno Setup to create installer package.
    echo Executable build completed without installer.
    goto end
)

REM Create resources directory if it doesn't exist
if not exist resources mkdir resources

REM Copy icon to resources directory if it exists
if exist icon.ico copy icon.ico resources\icon.ico
if exist icon.png copy icon.png resources\icon.png
if exist assets\icon.ico copy assets\icon.ico resources\icon.ico
if exist assets\icon.png copy assets\icon.png resources\icon.png

REM Convert PNG to ICO if needed for installer (requires ImageMagick or similar)
if exist icon.png if not exist resources\icon.ico (
    echo Note: Converting PNG to ICO format for installer compatibility
    REM Try to use magick command if available
    where magick >nul 2>nul
    if %errorlevel% equ 0 (
        magick icon.png resources\icon.ico
        echo Converted icon.png to icon.ico
    ) else (
        echo Warning: ImageMagick not found. Copying PNG as ICO for installer.
        copy icon.png resources\icon.ico >nul 2>nul
    )
)

REM Ensure we have an icon file for the installer
if not exist resources\icon.ico if exist resources\icon.png (
    copy resources\icon.png resources\icon.ico >nul 2>nul
    echo Using PNG icon as ICO for installer compatibility
)

REM Create app directory structure for installer
if not exist dist\app mkdir dist\app
if exist dist\FontMerge.exe (
    move dist\FontMerge.exe dist\app\FontMerge.exe
    echo Moved executable to dist\app\ for installer packaging
)

REM Run Inno Setup to create installer
echo Running Inno Setup Compiler...
iscc windows-installer.iss

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Build and packaging completed successfully!
    echo ========================================
    echo Executable: dist\app\FontMerge.exe
    echo Installer: dist\FontMerge-1.0.0.exe
    echo.
) else (
    echo Error: Failed to create installer package.
    echo Executable is available at: dist\app\FontMerge.exe
)

goto end

:end