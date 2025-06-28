#!/usr/bin/env python3
"""
Simple DMG Creation Script for Font Merge macOS App
Creates a basic DMG installer without complex customization
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def create_simple_dmg():
    """Create a simple DMG with drag-and-drop installation"""
    print("📦 Creating simple DMG installer...")

    # Check if app exists
    app_path = Path("dist/FontMerge.app")
    if not app_path.exists():
        print("❌ FontMerge.app not found in dist/")
        return False

    # DMG settings
    dmg_name = "FontMerge-1.0.0"
    dmg_path = Path(f"{dmg_name}.dmg")

    # Remove existing DMG
    if dmg_path.exists():
        dmg_path.unlink()
        print(f"✓ Removed existing {dmg_path}")

    # Create temporary directory for DMG contents
    temp_dir = Path("temp_dmg")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    try:
        # Copy app to temp directory preserving symlinks
        app_dest = temp_dir / "FontMerge.app"

        # Use cp -R to preserve symlinks and structure
        cp_cmd = ["cp", "-R", str(app_path), str(app_dest)]

        result = subprocess.run(cp_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ cp failed: {result.stderr}")
            # Fallback to shutil with symlinks=True
            shutil.copytree(app_path, app_dest, symlinks=True)
            print("✓ Copied app to temp directory (shutil with symlinks)")
        else:
            print("✓ Copied app to temp directory (cp -R preserving symlinks)")

        # Create Applications folder symlink
        apps_link = temp_dir / "Applications"
        os.symlink("/Applications", apps_link)
        print("✓ Created Applications symlink")

        # Create DMG using simple method
        print("🔨 Creating DMG...")
        cmd = [
            "hdiutil",
            "create",
            "-volname",
            "Font Merge",
            "-srcfolder",
            str(temp_dir),
            "-ov",
            "-format",
            "UDZO",
            str(dmg_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ DMG created successfully: {dmg_path}")

            # Check file size
            if dmg_path.exists():
                size_mb = dmg_path.stat().st_size / 1024 / 1024
                print(f"📏 DMG size: {size_mb:.1f} MB")

            return True
        else:
            print("❌ DMG creation failed:")
            print(f"Error: {result.stderr}")
            return False

    finally:
        # Clean up temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print("🧹 Cleaned up temporary files")

    return False


def main():
    """Main function"""
    print("📦 Font Merge - Simple DMG Creation Script")
    print("=" * 45)

    # Check if we're on macOS
    if sys.platform != "darwin":
        print("❌ This script is for macOS only!")
        sys.exit(1)

    # Check if hdiutil is available
    if not shutil.which("hdiutil"):
        print("❌ hdiutil not found. Please install Xcode Command Line Tools.")
        sys.exit(1)

    # Create DMG
    if create_simple_dmg():
        print("\n🎉 Simple DMG creation completed!")
        print("💡 Users can drag FontMerge.app to Applications to install")
    else:
        print("❌ DMG creation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
