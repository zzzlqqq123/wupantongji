# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

误判统计小程序 (Misjudgment Statistics Application) is a Python desktop application for quality inspectors to statistically analyze image defect misjudgment rates. Built with Tkinter + ttkbootstrap, featuring an industrial-style UI and a sophisticated viewport rendering system that enables smooth image zooming up to 50,000x.

## Development Commands

### Running the Application
```bash
python main.py
```

### Building Executable
```bash
# Windows (automated)
build.bat

# Manual build (all platforms)
pyinstaller --onefile --windowed --name "误判统计小程序" main.py
```

The executable is output to `dist/误判统计小程序.exe` (~25MB).

### Installing Dependencies
```bash
pip install -r requirements.txt
```

Only dependency is Pillow>=10.0.0. ttkbootstrap is also required but not listed in requirements.txt.

## Architecture

### Module Structure
- **main.py**: Orchestrates all managers, handles business logic flow
- **modules/gui_manager.py**: UI creation and viewport rendering system (the core technical complexity)
- **modules/image_loader.py**: Image loading, navigation, and file discovery
- **modules/statistics.py**: Real-time calculation of misjudgment/detection rates
- **modules/data_handler.py**: JSON persistence and TXT export
- **modules/config_manager.py**: Misjudgment type configuration management
- **utils/version_utils.py**: Git-based version string generation

### Manager Pattern
The application uses a manager pattern where `MisjudgmentApp` in main.py owns instances of each manager. GUIManager calls back into app methods for business logic (e.g., `on_misjudgment()` → `app.handle_misjudgment()`).

### Viewport Rendering System (Critical)

This is the most technically significant part of the codebase, located in `gui_manager.py`. Reference comments mention C# implementations (`CvDisplayGraphicsMat.cs`, `U_DisPlay.cs`).

**Core Concepts:**
- `pixel_size_x/y`: Scaling factor (screen pixels per image pixel)
- `display_origin_x/y`: Position of image's top-left corner on canvas
- `calculate_visible_rect()`: Determines which portion of source image is visible
- `screen_to_image()` / `image_to_screen()`: Coordinate transformation

**How It Works:**
1. Only crop and render the visible rectangle from the source image
2. Scale only that cropped portion to display size
3. This enables constant memory usage regardless of zoom level

**When Modifying Image Display:**
- Always work with `visible_rect` for rendering decisions
- Use coordinate transformation methods for mouse interaction
- Maintain the separation between image coordinates and screen coordinates
- Test at extreme zoom levels (5000%+) to verify performance

### Configuration Files

**config.json** - Created on first run, stores user's misjudgment types
**results.json** - Auto-generated after each session, contains statistics

Both are in the project root and should be in `.gitignore`.

## Version Management

Version strings are generated from Git:
- Format: `YYYYMMDD/commit_count` (e.g., "20250112/142")
- Display format: `vYYYY.MM.DD (build N)` (e.g., "v2025.01.12 (build 142)")
- If not in a git repo, commit count shows as 0 or "dev"

The version is displayed in the window title and bottom-right corner of the statistics panel.

## UI Framework

Uses ttkbootstrap with "superhero" theme (dark industrial style). All UI components are created in `gui_manager.py`. When modifying UI:
- Use `ttkb.Button`, `ttkb.Label`, `ttkb.Frame` etc. (not tk equivalents)
- Bootstyle options: `danger`, `success`, `info`, `secondary`, and `-outline` variants
- The app runs maximized (`root.state('zoomed')`)

## Statistics Calculation

All formulas are in `modules/statistics.py`:
- `misjudgment_rate = misjudgment_count / total_capacity * 100`
- `detection_rate = detection_count / total_capacity * 100`
- `type_rate = type_count / total_capacity * 100`

**Important:** `total_capacity` defaults to total image count but can be manually set by user via menu.

## Image Navigation

- Images are loaded once and paths stored in a list
- Navigation maintains a current index
- Users can go backward/forward and re-label images
- When re-labeling, old statistics are removed before adding new ones

## Common Modifications

### Adding a New Misjudgment Type
Edit config.json directly or use the UI: `配置 → 设置误判类型`

### Changing UI Theme
Modify the theme in `gui_manager.py:setup_window()`:
```python
style = ttkb.Style(theme="superhero")  # Change "superhero" to other theme name
```

### Adding Keyboard Shortcuts
Add bindings in `gui_manager.py:setup_window()`:
```python
self.root.bind('<key>', lambda e: method_name())
```

## Packaging Notes

The build script (`build.bat`) handles PyInstaller installation automatically. The spec file is auto-generated but can be customized if needed (currently `misjudgment_app.spec` exists but `build.bat` uses command-line args instead).
