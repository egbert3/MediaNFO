# MediaNFO

A portable, GUI-based tool for generating and editing [Kodi](https://kodi.tv/) / Emby / Jellyfin compatible `.nfo` files for movies and TV shows. It also imports cover images and renames them to standard filenames (poster.jpg, fanart.jpg, etc.).

Built with Python + Tkinter. **No TMDB or IMDb required** — all metadata can be entered manually, or loaded from existing scraper NFO files and then edited.

[中文文档](README_CN.md) · [Detailed Chinese manual (使用说明.md)](使用说明.md)

## Features

- Create and edit movie / TV show metadata and generate NFO files compatible with mainstream media libraries
- Detect and read existing NFO scraper metadata (any filename), then edit, modify, or delete it
- Scan folders for videos, images and TXT files; import covers with standardized names; import plot summaries from TXT
- Manage season and episode counts and the episode list; auto-generate episodes from `SxxExx` filenames
- Switch between movie and TV show modes while keeping all entered information
- Import and preview images, rotate covers, and assign them to poster / fanart / banner and other slots

## Getting Started

Requirements: **Windows + Python 3.9 (64-bit)**.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch (either way)
python main.py
# or double-click "启动 MediaNFO.bat"
```

Windows users can simply double-click `启动 MediaNFO.bat`; the script automatically locates Python 3.9.

## Quick Start

1. Select a media folder. The app scans it and loads any existing NFO (or uses the folder name as the title if none is found).
2. Fill in or edit the title, plot, cast & crew, and other fields in the form.
3. Click **Save NFO**. Files are written back into the media folder:
   - TV show: `tvshow.nfo` + one `SxxExx.nfo` per episode
   - Movie: `movie.nfo`
   - Cover images named to Kodi / Emby / Jellyfin conventions (poster.jpg, fanart.jpg, ...)

The **NFO Scraper Info** list on the left shows all `.nfo` files in the folder — click one to load it into the form, or delete it. See [使用说明.md](使用说明.md) for the full Chinese manual.

## Project Structure

| File | Description |
| --- | --- |
| `main.py` | Application entry point |
| `ui.py` | Main GUI (scanning, form, episode/cast management, image & synopsis import) |
| `media.py` | Image and text processing |
| `models.py` | Data models (movie / TV show / episode / person) |
| `nfo.py` | NFO generation, parsing and scraper metadata discovery |
| `README.md` | English overview (this file) |
| `README_CN.md` | Chinese overview |
| `使用说明.md` | Detailed Chinese user manual |
| `启动 MediaNFO.bat` | Windows one-click launcher |

## License

For personal learning and use only.
