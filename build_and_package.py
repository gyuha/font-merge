#!/usr/bin/env python3
"""
Complete macOS Build and Package Script for Font Merge
Builds app bundle and creates installer DMG in one go
"""

import os
import sys
import subprocess
import time
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


def get_build_info():
    """Get build information"""
    try:
        # Get git info if available
        try:
            git_hash = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], 
                stderr=subprocess.DEVNULL
            ).decode().strip()
            
            git_tag = subprocess.check_output(
                ["git", "describe", "--tags", "--abbrev=0"], 
                stderr=subprocess.DEVNULL
            ).decode().strip()
        except:
            git_hash = "unknown"
            git_tag = "v1.0.0"
        
        return {
            "version": git_tag,
            "commit": git_hash,
            "platform": "macOS",
            "arch": subprocess.check_output(["uname", "-m"]).decode().strip()
        }
    except:
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
    
    print(f"📱 Application: Font Merge")
    print(f"🏷️  Version: {build_info['version']}")
    print(f"🔧 Commit: {build_info['commit']}")
    print(f"💻 Platform: {build_info['platform']} ({build_info['arch']})")
    
    if success:
        print(f"✅ Status: BUILD SUCCESSFUL")
        
        # Check output files
        app_path = Path("dist/FontMerge.app")
        dmg_path = Path("FontMerge-1.0.0.dmg")
        
        if app_path.exists():
            app_size = sum(f.stat().st_size for f in app_path.rglob('*') if f.is_file())
            print(f"📁 App Bundle: {app_path} ({app_size/1024/1024:.1f} MB)")
        
        if dmg_path.exists():
            dmg_size = dmg_path.stat().st_size
            print(f"📦 DMG Installer: {dmg_path} ({dmg_size/1024/1024:.1f} MB)")
            
        print(f"\n💡 DISTRIBUTION:")
        print(f"   • App Bundle: dist/FontMerge.app")
        print(f"   • Installer: FontMerge-1.0.0.dmg")
        print(f"   • Ready for distribution!")
        
    else:
        print(f"❌ Status: BUILD FAILED")
        print(f"\n💡 TROUBLESHOOTING:")
        print(f"   • Check error messages above")
        print(f"   • Ensure all dependencies are installed")
        print(f"   • Try running individual scripts manually")
    
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
        if not run_script("create_dmg.py", "Creating DMG Installer"):
            success = False
    
    overall_duration = time.time() - overall_start
    
    # Print final summary
    print_build_summary(build_info, success)
    print(f"\n⏱️  Total build time: {overall_duration:.1f}s")
    
    if success:
        print(f"\n🎉 Build and packaging completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💥 Build failed. Check error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()