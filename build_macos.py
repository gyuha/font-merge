#!/usr/bin/env python3
"""
macOS App Bundle Build Script for Font Merge
Builds app bundle using PyInstaller with proper configuration
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import PyInstaller
        print("✓ PyInstaller found")
    except ImportError:
        print("Installing PyInstaller with uv...")
        subprocess.check_call(["uv", "add", "pyinstaller"])
        print("✓ PyInstaller installed")


def clean_build():
    """Clean previous build artifacts"""
    print("🧹 Cleaning previous build artifacts...")
    
    dirs_to_clean = ["build", "dist", "__pycache__"]
    files_to_clean = ["*.spec"]
    
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"   Removed {dir_name}/")
    
    import glob
    for pattern in files_to_clean:
        for file in glob.glob(pattern):
            if file != "build_macos.spec":  # Keep our custom spec file
                os.remove(file)
                print(f"   Removed {file}")


def build_app():
    """Build macOS app bundle using PyInstaller"""
    print("🏗️  Building macOS app bundle...")
    
    # Use custom spec file
    spec_file = "build_macos.spec"
    
    if not Path(spec_file).exists():
        print(f"❌ Error: {spec_file} not found!")
        return False
    
    try:
        cmd = ["uv", "run", "pyinstaller", "--clean", spec_file]
        subprocess.check_call(cmd)
        print("✅ App bundle build completed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False


def verify_build():
    """Verify the built app bundle"""
    app_path = Path("dist/FontMerge.app")
    
    if not app_path.exists():
        print("❌ App bundle not found!")
        return False
    
    print("🔍 Verifying app bundle...")
    
    # Check if executable exists
    exe_path = app_path / "Contents/MacOS/FontMerge"
    if exe_path.exists():
        print("✓ Executable found")
    else:
        print("❌ Executable not found")
        return False
    
    # Check if icon exists
    icon_path = app_path / "Contents/Resources/icon.icns"
    if icon_path.exists():
        print("✓ Icon found")
    else:
        print("⚠️  Icon not found (optional)")
    
    # Check Info.plist
    plist_path = app_path / "Contents/Info.plist"
    if plist_path.exists():
        print("✓ Info.plist found")
    else:
        print("❌ Info.plist not found")
        return False
    
    print(f"✅ App bundle verification completed: {app_path}")
    return True


def main():
    """Main build function"""
    print("🚀 Font Merge macOS Build Script")
    print("=" * 40)
    
    # Check if we're on macOS
    if sys.platform != "darwin":
        print("❌ This script is for macOS only!")
        sys.exit(1)
    
    # Check dependencies
    check_dependencies()
    
    # Clean previous builds
    clean_build()
    
    # Build app
    if not build_app():
        sys.exit(1)
    
    # Verify build
    if not verify_build():
        sys.exit(1)
    
    print("\n🎉 macOS app bundle build completed successfully!")
    print("📁 App location: dist/FontMerge.app")
    print("💡 Next step: Run create_dmg.py to create installer DMG")


if __name__ == "__main__":
    main()