#!/bin/bash
# Complete macOS Build and Package Script for Font Merge
# Builds app bundle and creates installer DMG

set -e

echo "🏗️  Font Merge - Complete Build & Package Script"
echo "=========================================================="

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only!"
    exit 1
fi

# Check prerequisites
echo "🔍 Checking prerequisites..."

REQUIRED_FILES=(
    "build_macos.py"
    "build_macos.spec"
    "create_dmg.py"
    "src/font_merge/main.py"
    "icon.icns"
)

MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$file" ]]; then
        MISSING_FILES+=("$file")
    fi
done

if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
    echo "❌ Missing required files:"
    printf '   - %s\n' "${MISSING_FILES[@]}"
    echo "💡 Please ensure all required files are present and try again."
    exit 1
fi

echo "✅ All required files found"

# Get build info
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v1.0.0")
COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
ARCH=$(uname -m)

echo "📋 Building Font Merge $VERSION for macOS ($ARCH)"

# Start timer
START_TIME=$(date +%s)

# Step 1: Build macOS app bundle
echo ""
echo "=================================================="
echo "🚀 Building macOS App Bundle"
echo "=================================================="

if python3 build_macos.py; then
    echo "✅ App bundle build completed"
else
    echo "❌ App bundle build failed"
    exit 1
fi

# Step 2: Create DMG installer
echo ""
echo "=================================================="
echo "🚀 Creating DMG Installer" 
echo "=================================================="

if python3 create_dmg.py; then
    echo "✅ DMG creation completed"
else
    echo "❌ DMG creation failed"
    exit 1
fi

# Calculate build time
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Print summary
echo ""
echo "============================================================"
echo "📋 BUILD SUMMARY"
echo "============================================================"
echo "📱 Application: Font Merge"
echo "🏷️  Version: $VERSION"
echo "🔧 Commit: $COMMIT"
echo "💻 Platform: macOS ($ARCH)"
echo "✅ Status: BUILD SUCCESSFUL"

# Check output files
if [[ -d "dist/FontMerge.app" ]]; then
    APP_SIZE=$(du -sh "dist/FontMerge.app" | cut -f1)
    echo "📁 App Bundle: dist/FontMerge.app ($APP_SIZE)"
fi

if [[ -f "FontMerge-1.0.0.dmg" ]]; then
    DMG_SIZE=$(du -sh "FontMerge-1.0.0.dmg" | cut -f1)
    echo "📦 DMG Installer: FontMerge-1.0.0.dmg ($DMG_SIZE)"
fi

echo ""
echo "💡 DISTRIBUTION:"
echo "   • App Bundle: dist/FontMerge.app"
echo "   • Installer: FontMerge-1.0.0.dmg"
echo "   • Ready for distribution!"

echo "============================================================"
echo "⏱️  Total build time: ${DURATION}s"
echo ""
echo "🎉 Build and packaging completed successfully!"

# Make executable
chmod +x "build_and_package.sh"