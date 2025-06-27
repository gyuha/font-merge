#!/usr/bin/env python3
"""
Cross-platform build script for font-merge application
Supports Windows and macOS executable generation using PyInstaller
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def build_windows():
    """Build Windows executable"""
    print("Building Windows executable...")

    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name",
        "FontMerge",
        "--icon",
        "assets/icon.ico" if Path("assets/icon.ico").exists() else None,
        "--add-data",
        "src;src",
        "src/font_merge/main.py",
    ]

    # Remove None values
    cmd = [arg for arg in cmd if arg is not None]

    subprocess.check_call(cmd)
    print("Windows build completed! Check dist/FontMerge.exe")


def build_macos():
    """Build macOS application bundle"""
    print("Building macOS application...")

    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name",
        "FontMerge",
        "--icon",
        "assets/icon.icns" if Path("assets/icon.icns").exists() else None,
        "--add-data",
        "src:src",
        "src/font_merge/main.py",
    ]

    # Remove None values
    cmd = [arg for arg in cmd if arg is not None]

    subprocess.check_call(cmd)
    print("macOS build completed! Check dist/FontMerge.app")


def clean_build():
    """Clean previous build artifacts"""
    print("Cleaning previous build artifacts...")

    dirs_to_clean = ["build", "dist", "__pycache__"]
    files_to_clean = ["*.spec"]

    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            import shutil

            shutil.rmtree(dir_name)
            print(f"Removed {dir_name}/")

    for pattern in files_to_clean:
        import glob

        for file in glob.glob(pattern):
            os.remove(file)
            print(f"Removed {file}")


def main():
    """Main build function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        clean_build()
        return

    # Install PyInstaller
    install_pyinstaller()

    # Clean previous builds
    clean_build()

    # Detect platform and build accordingly
    system = platform.system().lower()

    if system == "windows":
        build_windows()
    elif system == "darwin":
        build_macos()
    else:
        print(f"Unsupported platform: {system}")
        print("This script supports Windows and macOS only.")
        sys.exit(1)


if __name__ == "__main__":
    main()
