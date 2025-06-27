#!/usr/bin/env python3
"""
DMG Creation Script for Font Merge macOS App
Creates a professional installer DMG with custom background and layout
"""

import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path


def check_dependencies():
    """Check if required tools are available"""
    tools = ["hdiutil", "SetFile"]
    
    for tool in tools:
        if not shutil.which(tool):
            print(f"❌ {tool} not found. Please install Xcode Command Line Tools.")
            return False
    
    print("✓ All required tools found")
    return True


def create_dmg_background():
    """Create DMG background image"""
    bg_path = Path("dmg_background.png")
    
    if bg_path.exists():
        print("✓ DMG background already exists")
        return str(bg_path)
    
    print("🎨 Creating DMG background...")
    
    # Create a simple background using Python PIL if available
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create background image (600x400)
        width, height = 600, 400
        background = Image.new('RGB', (width, height), color='#f0f0f0')
        draw = ImageDraw.Draw(background)
        
        # Try to use a system font
        try:
            font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 24)
        except:
            font = ImageFont.load_default()
        
        # Draw title
        title = "Font Merge"
        title_bbox = draw.textbbox((0, 0), title, font=font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((width - title_width) // 2, 50), title, fill='#333333', font=font)
        
        # Draw instructions
        instructions = [
            "Drag Font Merge.app to Applications folder",
            "to install the application"
        ]
        
        try:
            inst_font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 16)
        except:
            inst_font = ImageFont.load_default()
        
        y_offset = 120
        for line in instructions:
            line_bbox = draw.textbbox((0, 0), line, font=inst_font)
            line_width = line_bbox[2] - line_bbox[0]
            draw.text(((width - line_width) // 2, y_offset), line, fill='#666666', font=inst_font)
            y_offset += 25
        
        background.save(bg_path, 'PNG')
        print(f"✓ Background created: {bg_path}")
        
    except ImportError:
        print("⚠️  PIL not available, creating simple background...")
        # Create a simple solid color background using ImageMagick if available
        if shutil.which('convert'):
            subprocess.run([
                'convert', '-size', '600x400', 'xc:#f0f0f0',
                '-pointsize', '24', '-fill', '#333333',
                '-gravity', 'center', '-annotate', '+0-50', 'Font Merge',
                '-pointsize', '16', '-fill', '#666666',
                '-annotate', '+0+20', 'Drag to Applications folder to install',
                str(bg_path)
            ])
        else:
            print("⚠️  No image tools available, DMG will use default background")
            return None
    
    return str(bg_path) if bg_path.exists() else None


def create_dmg(app_path, dmg_name, dmg_path):
    """Create DMG file with proper layout"""
    print(f"📦 Creating DMG: {dmg_name}")
    
    # Create temporary directory for DMG contents
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy app to temp directory
        app_dest = temp_path / "FontMerge.app"
        shutil.copytree(app_path, app_dest)
        print(f"✓ Copied app to: {app_dest}")
        
        # Create Applications folder symlink
        apps_link = temp_path / "Applications"
        os.symlink("/Applications", apps_link)
        print("✓ Created Applications symlink")
        
        # Create DMG from temp directory
        temp_dmg = temp_path / "temp.dmg"
        
        # Calculate DMG size (app size + 20MB buffer)
        app_size = sum(f.stat().st_size for f in Path(app_dest).rglob('*') if f.is_file())
        dmg_size_mb = (app_size // 1024 // 1024) + 20  # MB
        dmg_size = max(50, dmg_size_mb)  # 최소 50MB, 최대는 실제 크기 + 20MB
        
        # Create DMG
        cmd = [
            "hdiutil", "create",
            "-volname", "Font Merge",
            "-srcfolder", str(temp_path),
            "-ov", "-format", "UDRW",
            "-size", f"{dmg_size}m",
            str(temp_dmg)
        ]
        
        try:
            subprocess.check_call(cmd)
            print("✓ DMG created successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create DMG: {e}")
            return False
        
        # Mount DMG for customization
        print("🔧 Customizing DMG...")
        mount_point = temp_path / "mount"
        mount_point.mkdir()
        
        try:
            # Mount
            subprocess.check_call([
                "hdiutil", "attach", str(temp_dmg),
                "-mountpoint", str(mount_point),
                "-nobrowse"
            ])
            
            # Set background if available
            bg_path = create_dmg_background()
            if bg_path:
                bg_dest = mount_point / ".background"
                bg_dest.mkdir(exist_ok=True)
                shutil.copy2(bg_path, bg_dest / "background.png")
                
                # Set folder view options using AppleScript
                applescript = f'''
                tell application "Finder"
                    tell disk "Font Merge"
                        open
                        set current view of container window to icon view
                        set toolbar visible of container window to false
                        set statusbar visible of container window to false
                        set the bounds of container window to {{100, 100, 700, 500}}
                        set viewOptions to the icon view options of container window
                        set arrangement of viewOptions to not arranged
                        set icon size of viewOptions to 128
                        set background picture of viewOptions to file ".background:background.png"
                        set position of item "FontMerge.app" of container window to {{150, 200}}
                        set position of item "Applications" of container window to {{450, 200}}
                        close
                        open
                        update without registering applications
                        delay 2
                    end tell
                end tell
                '''
                
                try:
                    subprocess.run(["osascript", "-e", applescript], check=True)
                    print("✓ DMG layout configured")
                except subprocess.CalledProcessError:
                    print("⚠️  Could not set DMG layout (optional)")
            
            # Unmount
            subprocess.check_call(["hdiutil", "detach", str(mount_point)])
            
        except Exception as e:
            print(f"⚠️  DMG customization failed: {e}")
            # Try to unmount if still mounted
            try:
                subprocess.check_call(["hdiutil", "detach", str(mount_point)])
            except:
                pass
        
        # Convert to compressed read-only DMG
        print("🗜️  Compressing DMG...")
        try:
            subprocess.check_call([
                "hdiutil", "convert", str(temp_dmg),
                "-format", "UDZO",
                "-imagekey", "zlib-level=9",
                "-o", str(dmg_path)
            ])
            print(f"✅ Final DMG created: {dmg_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to compress DMG: {e}")
            return False


def main():
    """Main DMG creation function"""
    print("📦 Font Merge DMG Creation Script")
    print("=" * 40)
    
    # Check if we're on macOS
    if sys.platform != "darwin":
        print("❌ This script is for macOS only!")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check if app exists
    app_path = Path("dist/FontMerge.app")
    if not app_path.exists():
        print("❌ FontMerge.app not found in dist/")
        print("💡 Run build_macos.py first to build the app")
        sys.exit(1)
    
    # DMG settings
    dmg_name = "FontMerge-1.0.0"
    dmg_path = Path(f"{dmg_name}.dmg")
    
    # Remove existing DMG
    if dmg_path.exists():
        dmg_path.unlink()
        print(f"✓ Removed existing {dmg_path}")
    
    # Create DMG
    if create_dmg(app_path, dmg_name, dmg_path):
        file_size = dmg_path.stat().st_size / 1024 / 1024  # MB
        print(f"\n🎉 DMG creation completed successfully!")
        print(f"📁 DMG file: {dmg_path}")
        print(f"📏 File size: {file_size:.1f} MB")
        print("\n💡 You can now distribute this DMG file")
        print("   Users can drag FontMerge.app to Applications to install")
    else:
        print("❌ DMG creation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()