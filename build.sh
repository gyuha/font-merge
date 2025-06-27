#!/bin/bash
# Cross-platform build script for font-merge application

set -e

echo "Font-Merge Build Script"
echo "======================"

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please install uv first."
    exit 1
fi

# Function to clean build artifacts
clean_build() {
    echo "Cleaning previous build artifacts..."
    rm -rf build/ dist/ *.spec __pycache__/
    echo "Clean completed."
}

# Function to install PyInstaller
install_pyinstaller() {
    echo "Installing PyInstaller..."
    uv add pyinstaller
}

# Function to build for current platform
build_app() {
    echo "Building application for $(uname -s)..."
    
    # Determine platform-specific settings
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        ICON_FILE=""
        if [[ -f "assets/icon.icns" ]]; then
            ICON_FILE="--icon=assets/icon.icns"
        fi
        DATA_SEP=":"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows
        ICON_FILE=""
        if [[ -f "assets/icon.ico" ]]; then
            ICON_FILE="--icon=assets/icon.ico"
        fi
        DATA_SEP=";"
    else
        # Linux or other
        ICON_FILE=""
        DATA_SEP=":"
    fi
    
    # Build command
    uv run pyinstaller \
        --onefile \
        --windowed \
        --name "FontMerge" \
        $ICON_FILE \
        --add-data "src${DATA_SEP}src" \
        src/font_merge/main.py
    
    echo "Build completed! Check the dist/ directory."
}

# Main script logic
case "${1:-}" in
    --clean)
        clean_build
        ;;
    --help|-h)
        echo "Usage: $0 [--clean|--help]"
        echo "  --clean  Clean build artifacts"
        echo "  --help   Show this help message"
        ;;
    *)
        install_pyinstaller
        clean_build
        build_app
        ;;
esac