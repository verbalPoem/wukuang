<br />
<div align="center">
  <img src="assets/app-icon.png" alt="Wukuang Logo" width="120" height="120">

  <h1 align="center" style="margin-top: 0.2em;">Wukuang</h1>

  <p align="center">
    <a href="./README.md">简体中文</a> | English
  </p>

  [![Python][python-badge]][python-url]
  [![PySide6][pyside-badge]][pyside-url]
  [![OpenCV][opencv-badge]][opencv-url]
  [![Pillow][pillow-badge]][pillow-url]
  [![PyInstaller][pyinstaller-badge]][pyinstaller-url]

  <p align="center">
    <h3>A local desktop workstation for batch image blurring and dataset desensitization</h3>
    <br />
    <a href="https://github.com/verbalPoem/wukuang/releases"><strong>Download Latest Release &raquo;</strong></a>
    <br />
    <br />
    <a href="#features">Features</a>
    &middot;
    <a href="#quick-start">Quick Start</a>
    &middot;
    <a href="#development">Development</a>
    &middot;
    <a href="#notes">Notes</a>
    &middot;
    <a href="#license">License</a>
  </p>
</div>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#features">Features</a></li>
    <li><a href="#whats-new-in-v104">What's New in v1.0.4</a></li>
    <li><a href="#why-this-project">Why This Project</a></li>
    <li><a href="#preview">Preview</a></li>
    <li><a href="#quick-start">Quick Start</a></li>
    <li><a href="#shortcuts">Shortcuts</a></li>
    <li><a href="#development">Development</a></li>
    <li><a href="#project-structure">Project Structure</a></li>
    <li><a href="#notes">Notes</a></li>
    <li><a href="#author">Author</a></li>
    <li><a href="#license">License</a></li>
  </ol>
</details>

## Features

<p align="center">
  <img src="assets/release-cover.png" alt="Release Cover" width="48%">
</p>

- **Built for batch workflows**: process one image after another inside a folder, ideal for datasets, screenshots, and review pipelines
- **Three selection modes**: drag-to-confirm, two-click point mode, and fixed-size single-click mode
- **Two masking shapes**: rectangle and circle, with configurable rounded corners for rectangles
- **Three processing modes**: `Gaussian`, `Pixelate`, and `Inpaint`
- **Auto save**: overwrite original files or export to `blurred_output`
- **Fast browsing**: `A / D` for previous and next image, hold keys for continuous flipping
- **Subfolder navigation**: switch through sibling subfolders by name order, useful for large dataset trees
- **Undo and reload**: `Ctrl + Z` to undo, `R` to reload the current image
- **High-DPI friendly**: tuned for Windows high-resolution displays
- **Modern desktop UI**: built with `PySide6`, with light/dark themes, settings panel, and unified controls
- **Performance aware**: preview cache, neighbor prefetch, and in-memory canvas refresh reduce waiting time

## What's New in v1.0.4

- Streamlined subfolder navigation. `Previous Folder / Next Folder` now works only on the direct child folders under the parent directory, sorted by name
- Removed automatic sibling-folder prescan when opening a directory, which greatly improves responsiveness on external drives
- Parent-folder progress is now counted manually through a dedicated button
- Fixed freezes, white screens, and unavailable folder navigation buttons caused by aggressive parent-folder scanning

## What's New in v1.0.3

- Added a third selection mode: fixed-size single-click masking
- Added a live blue preview box that follows the mouse cursor
- The preview box is centered on the cursor, so users always know the exact masking size before clicking
- Fixed width and height can be adjusted in real time, and the preview updates immediately
- Added preset sizes: `64`, `96`, and `128`, while keeping custom size support

## What's New in v1.0.2

- Added `Previous Folder / Next Folder` to navigate sibling subfolders under the same parent folder
- Subfolders are sorted by name for stable navigation
- Added `Shift + A / Shift + D` for folder switching
- App now starts maximized by default for large-batch workflows
- Fixed sidebar layout issues that appeared after switching subfolders
- Refreshed app icon and packaging assets for a cleaner desktop appearance

## Why This Project

`Wukuang` is designed to be a focused tool for batch image desensitization instead of a heavy, general-purpose image editor.

It is optimized for highly repetitive work like this:

- open an image
- mark faces, body parts, text, or privacy-sensitive regions
- process immediately
- save automatically
- move to the next image

The main goal is to reduce repetitive clicks, avoid unnecessary popups, and keep the operator in a steady review rhythm.

## Preview

![Wukuang Preview](./assets/app-preview.png)

## Quick Start

### 1. Prepare an image folder

- Put the images you want to process into one folder
- Supported formats: `jpg`, `jpeg`, `png`, `bmp`, `webp`

### 2. Launch the app and choose a folder

- Start `Wukuang`
- Click `Open Image Folder`
- Select the folder you want to process

### 3. Start masking

- Select the region you want to blur
- Release the mouse or click the second point to confirm
- Press `D` for the next image and `A` for the previous one
- If you need repeated fixed-size masking, switch to `Fixed` mode and click once per target

### 4. Choose the right processing mode

- `Gaussian`: best for faces and body-sensitive areas
- `Pixelate`: better for stronger visual blocking
- `Inpaint`: useful for removing small text, watermarks, or local overlays

### 5. Undo when needed

- Press `Ctrl + Z` to undo the last change immediately
- The status bar will highlight the undo action

## Shortcuts

| Action | Shortcut |
|------|--------|
| Previous image | `A` |
| Next image | `D` |
| Continuous flipping | Hold `A / D` |
| Previous subfolder | `Shift + A` |
| Next subfolder | `Shift + D` |
| Count parent-folder progress | Sidebar button |
| Undo last change | `Ctrl + Z` |
| Reload current image | `R` |
| Open folder | `Ctrl + O` |

## Development

### Recommended environment

- Windows 10 / 11
- Python 3.12
- For high-DPI monitors, keep normal Windows scaling enabled

### Run from source

```powershell
python face_blur_studio.py
```

### Build EXE

```powershell
build_exe.bat
```

### Manual build

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt pyinstaller
python scripts\generate_brand_assets.py
pyinstaller --noconfirm --clean --windowed --icon assets\app-icon.ico --name BlurStudio face_blur_studio.py
```

### Common commands

| Command | Description |
|------|------|
| `python face_blur_studio.py` | Run the desktop app |
| `py -3.12 -m py_compile wukuang_qt.py` | Syntax check |
| `build_exe.bat` | Build Windows EXE |

### Tech stack

| Layer | Technology |
|------|------|
| Desktop GUI | [PySide6](https://doc.qt.io/qtforpython-6/) |
| Image processing | [OpenCV](https://opencv.org/) + [Pillow](https://python-pillow.org/) + [NumPy](https://numpy.org/) |
| System integration | `ctypes` |
| Packaging | [PyInstaller](https://pyinstaller.org/) |
| Language | [Python 3.12](https://www.python.org/) |

### Current architecture

```text
┌─────────────────────────────────────────────────────────┐
│                        Wukuang                          │
│                                                         │
│  ┌──────────────────┐         ┌──────────────────────┐  │
│  │   PySide6 UI     │         │   Image Pipeline     │  │
│  │                  │         │                      │  │
│  │  Sidebar         │         │  Pillow load/save    │  │
│  │  Settings Dialog │◄──────► │  OpenCV blur/inpaint │  │
│  │  Canvas Preview  │         │  NumPy mask process  │  │
│  │  Status Bar      │         │  Preview cache       │  │
│  └──────────────────┘         └──────────────────────┘  │
│                                                         │
│                  Local image folders                    │
└─────────────────────────────────────────────────────────┘
```

### Image save policy

- `PNG` is saved losslessly
- `JPEG / JPG` is saved with high-quality settings:
  `quality=100`, `subsampling=0`, and no extra optimization

Note that `JPEG` is still a lossy format by nature, so strict lossless overwrite is impossible.

## Project Structure

```text
assets/
  app-icon.ico
  app-icon.png
  app-preview.png
  release-cover.png
scripts/
  generate_brand_assets.py
face_blur_studio.py
wukuang_qt.py
build_exe.bat
requirements.txt
LICENSE
README.md
README.en.md
```

## Notes

- `Inpaint` works best for small text, watermarks, and local overlays, not for large-area reconstruction
- If the source image is `JPEG`, overwrite mode is still limited by JPEG's lossy nature
- Very large images may still take some time on first load, though preview caching and delayed prefetch already reduce most of the perceived lag

## Author

Click the logo in the top-left corner inside the app to see the author dialog.

- Developers: `cca&qyx&codex`
- Goal: make batch image masking faster and more comfortable for long review sessions

## License

This project is licensed under the [MIT License](./LICENSE).

## Future roadmap

- Auto face detection and pre-blur
- Multi-box batch confirmation
- Zoom and pan for the canvas
- More shapes, including polygon support
- Custom shortcuts
- A more complete project settings system

[python-badge]: https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white
[python-url]: https://www.python.org/
[pyside-badge]: https://img.shields.io/badge/PySide6-Qt_for_Python-41CD52?style=for-the-badge&logo=qt&logoColor=white
[pyside-url]: https://doc.qt.io/qtforpython-6/
[opencv-badge]: https://img.shields.io/badge/OpenCV-Image_Processing-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white
[opencv-url]: https://opencv.org/
[pillow-badge]: https://img.shields.io/badge/Pillow-Image_IO-8CAAE6?style=for-the-badge
[pillow-url]: https://python-pillow.org/
[pyinstaller-badge]: https://img.shields.io/badge/PyInstaller-Windows_EXE-EE4C2C?style=for-the-badge
[pyinstaller-url]: https://pyinstaller.org/
