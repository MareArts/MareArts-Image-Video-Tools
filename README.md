# MareArts Image and Video Tools

## Overview
This project provides a comprehensive toolset for media manipulation:

1. **`download_youtube.py`** - Downloads videos from YouTube.
2. **`16_9_video_gen.py`** - Converts videos to a 16:9 aspect ratio.
3. **`image-tool.py`** - Image viewer with mosaic functionality for privacy protection.

## Features

### YouTube Video Tools
- Download YouTube videos using a URL.
- Resize videos while maintaining quality.
- Automatically adjust black bars or crop videos to fit 16:9.
- Output in standard video formats.

### Image Viewer Tool
- Browse and view images from folders
- Navigate with keyboard shortcuts
- Apply mosaic effect to selected regions for privacy
- Save, move, and delete images
- Quick folder organization with keyboard shortcuts
- Dynamic resizing and responsive UI

## Requirements
Make sure you have Python installed along with the necessary dependencies.

### Install dependencies
```bash
pip install -r requirements.txt
```

## Usage

### 1. Download a YouTube Video
```bash
python download_youtube.py <YouTube_URL>
```
This will save the video locally.

### 2. Convert Video to 16:9
```bash
python 16_9_video_gen.py <input_video> <output_video>
```
This will process the video and output a 16:9 formatted version.

### 3. Image Viewer with Mosaic Tool
```bash
python image-tool.py
```

#### Image Tool Features:
- **Open Folder**: Browse and select image directories
- **Navigation**: Use Page Up/Down keys or arrow keys to navigate images
- **Selection Tool**: Draw rectangles to create mosaic regions for privacy
- **Keyboard Shortcuts**:
  - `Ctrl+S` / `Cmd+S`: Save changes
  - `Delete`: Remove current image
  - `a`: Move current image to "a" subfolder (creates if needed)
  - `f`: Move current image to "f" subfolder (creates if needed)
- **Window Resizing**: UI dynamically adjusts to window size
- **Focus Management**: Automatically regains focus after dialogs

## Dependencies
The project requires the following Python libraries:
- `pytube` (for downloading YouTube videos)
- `ffmpeg` (for video processing)
- `opencv-python` (for video handling)
- `pillow` (for image processing)
- `tkinter` (included with Python, for the GUI)

You can install them manually if not using `requirements.txt`:
```bash
pip install pytube opencv-python ffmpeg-python pillow
```

## License
This project is open-source under the MIT License.

## Author
MareArts
