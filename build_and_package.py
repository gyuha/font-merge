#!/usr/bin/env python3
"""
Complete macOS Build and Package Script for Font Merge
Builds app bundle and creates installer DMG in one go
"""

import subprocess
import sys
import time
import tomllib
from pathlib import Path


def run_script(script_path, description):
    """Run a Python script and handle errors"""
    print(f"\n{'='*50}")
    print(f"🚀 {description}")
    print(f"{'='*50}")

    start_time = time.time()

    try:
        result = subprocess.run([sys.executable, str(script_path)],
                              check=True,
                              capture_output=False)

        duration = time.time() - start_time
        print(f"\n✅ {description} completed in {duration:.1f}s")
        return True

    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"\n❌ {description} failed after {duration:.1f}s")
        print(f"Error code: {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Script not found: {script_path}")
        return False


def check_prerequisites():
    """Check if all required files exist"""
    print("🔍 Checking prerequisites...")

    required_files = [
        "build_macos.py",
        "build_macos.spec",
        "create_dmg.py",
        "src/font_merge/main.py",
        "icon.icns"
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False

    print("✅ All required files found")
    return True


def get_version_from_pyproject():
    """Get version from pyproject.toml"""
    try:
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
            return data["project"]["version"]
    except Exception:
        return "1.0.0"


def get_build_info():
    """Get build information"""
    try:
        # Get version from pyproject.toml
        version = get_version_from_pyproject()
        
        # Get git info if available
        try:
            git_hash = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            git_hash = "unknown"

        return {
            "version": f"v{version}",
            "commit": git_hash,
            "platform": "macOS",
            "arch": subprocess.check_output(["uname", "-m"]).decode().strip()
        }
    except Exception:
        return {
            "version": "v1.0.0",
            "commit": "unknown",
            "platform": "macOS",
            "arch": "unknown"
        }


def print_build_summary(build_info, success=True):
    """Print build summary"""
    print(f"\n{'='*60}")
    print("📋 BUILD SUMMARY")
    print(f"{'='*60}")

    print("📱 Application: Font Merge")
    print(f"🏷️  Version: {build_info['version']}")
    print(f"🔧 Commit: {build_info['commit']}")
    print(f"💻 Platform: {build_info['platform']} ({build_info['arch']})")

    if success:
        print("✅ Status: BUILD SUCCESSFUL")

        # Check output files
        app_path = Path("dist/FontMerge.app")
        version_num = build_info['version'].lstrip('v')  # Remove 'v' prefix
        dmg_path = Path(f"FontMerge-{version_num}.dmg")

        if app_path.exists():
            app_size = sum(f.stat().st_size for f in app_path.rglob("*") if f.is_file())
            print(f"📁 App Bundle: {app_path} ({app_size/1024/1024:.1f} MB)")

        if dmg_path.exists():
            dmg_size = dmg_path.stat().st_size
            print(f"📦 DMG Installer: {dmg_path} ({dmg_size/1024/1024:.1f} MB)")

        print("\n💡 DISTRIBUTION:")
        print("   • App Bundle: dist/FontMerge.app")
        print(f"   • Installer: FontMerge-{version_num}.dmg")
        print("   • Ready for distribution!")

    else:
        print("❌ Status: BUILD FAILED")
        print("\n💡 TROUBLESHOOTING:")
        print("   • Check error messages above")
        print("   • Ensure all dependencies are installed")
        print("   • Try running individual scripts manually")

    print(f"{'='*60}")


def main():
    """Main build and package function"""
    print("🏗️  Font Merge - Complete Build & Package Script")
    print("=" * 60)

    # Check if we're on macOS
    if sys.platform != "darwin":
        print("❌ This script is for macOS only!")
        sys.exit(1)

    # Get build info
    build_info = get_build_info()
    print(f"📋 Building Font Merge {build_info['version']} for {build_info['platform']}")

    # Check prerequisites
    if not check_prerequisites():
        print("\n💡 Please ensure all required files are present and try again.")
        sys.exit(1)

    overall_start = time.time()
    success = True

    # Step 1: Build macOS app bundle
    if not run_script("build_macos.py", "Building macOS App Bundle"):
        success = False

    # Step 2: Create DMG installer (only if app build succeeded)
    if success:
        if not run_script("create_simple_dmg.py", "Creating DMG Installer"):
            success = False

    overall_duration = time.time() - overall_start

    # Print final summary
    print_build_summary(build_info, success)
    print(f"\n⏱️  Total build time: {overall_duration:.1f}s")

    if success:
        print("\n🎉 Build and packaging completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Build failed. Check error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
