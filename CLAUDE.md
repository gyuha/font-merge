# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Font Merge is a PyQt6 desktop application for merging two fonts into a single font file. The application provides a GUI for selecting fonts, choosing character sets from each font, and combining them with various merge options.

## Key Commands

### Development
- **Run application**: `python -m font_merge.main` or `python main.py`
- **Format code**: `ruff format .`
- **Lint code**: `ruff check .`
- **Fix linting issues**: `ruff check . --fix`

### Building (macOS)
- **Build app bundle**: `python build_macos.py`
- **Create DMG installer**: `python create_simple_dmg.py`
- **Complete build & package**: `python build_and_package.py`

The build process uses PyInstaller with a custom spec file (`build_macos.spec`) configured for onedir mode to maintain fast startup times.

## Architecture

### Core Components

1. **FontMergeApp** (`src/font_merge/main.py`) - Main application window and UI orchestration
2. **FontSelector** (`src/font_merge/font_selector.py`) - Widget for font file selection and character set management
3. **FontMerger** (`src/font_merge/font_merger.py`) - Core font merging logic using fontTools
4. **FontPreview** (`src/font_merge/font_preview.py`) - Font preview and character set visualization

### Import Strategy

The codebase uses a defensive import pattern to handle both development and PyInstaller environments:

```python
try:
    from .module import Class  # Relative import for development
except (ImportError, ValueError):
    from font_merge.module import Class  # Absolute import for PyInstaller
```

### Build System

- **PyInstaller**: Uses onedir mode for better performance than onefile
- **DMG Creation**: Custom script (`create_simple_dmg.py`) preserves symlinks using `cp -R`
- **Spec File**: `build_macos.spec` includes all necessary hidden imports and data files

### Font Processing

The application uses fontTools library for:
- Font subsetting to extract specific character sets
- Font merging with configurable options (default, UPM unification, lenient merging)
- Character set analysis and Unicode range detection
- Ligature support restoration

### UI Structure

- Main window contains two FontSelector widgets (left/right)
- Each FontSelector provides file selection, character set checkboxes, and preview
- Merge options include compatibility modes and custom font naming
- Error handling provides specific suggestions based on merge option and error type

## Important Files

- `build_macos.spec` - PyInstaller configuration for macOS app bundle
- `pyproject.toml` - Project configuration with ruff linting rules
- `create_simple_dmg.py` - DMG creation script that preserves app bundle structure
- `README_BUILD.md` - Comprehensive build documentation

## Development Notes

- The app uses PyQt6 for GUI with Korean language support
- Font files in the root directory are sample fonts for testing
- Build artifacts are created in `dist/` directory
- The application handles various font formats (TTF, OTF) and provides detailed error messages for compatibility issues