# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Font-merge is a PyQt6 desktop application for merging two fonts into a single font file. Users can select character sets from each font and combine them into a new font file.

## Development Commands

### Environment Setup
```bash
uv sync  # Install dependencies and create virtual environment
```

### Running the Application
```bash
uv run python src/font_merge/main.py  # Run the main application
```

## Architecture

### Core Components

- **FontMergeApp**: Main window class that orchestrates the entire application
- **FontSelector**: Reusable widget for font selection, preview, and character set selection
- **FontPreview**: Widget for displaying font previews with sample text

### Application Structure

The application is split into two main font selector panels (left and right) with the following workflow:
1. User selects font files via file dialog (.ttf, .otf, .woff, .woff2)
2. Font preview displays sample text using the selected font
3. Character set checkboxes are dynamically generated based on available characters in the font
4. Character sets are categorized by Unicode ranges (한글, 영문, 숫자, 기호, 한자 등)
5. Merge button combines selected character sets from both fonts

### Key Dependencies

- **PyQt6**: GUI framework for the desktop application
- **fontTools**: Font manipulation and parsing library
- **Pillow**: Image processing (included for potential future image handling)

### Font Processing Logic

Character sets are analyzed using fontTools.ttLib.TTFont to:
- Parse font files and extract character mappings (cmap)
- Categorize characters into Unicode ranges
- Enable/disable checkboxes based on character availability
- Generate counts for each character set category

### Current Implementation Status

The UI framework is complete with font selection, preview, and character set analysis. The actual font merging logic in `merge_fonts()` method is a placeholder that needs implementation.