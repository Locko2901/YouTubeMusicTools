[![Made with Python](https://img.shields.io/badge/Made%20with-Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Built with Nuitka](https://img.shields.io/badge/Built%20with-Nuitka-blue)](https://nuitka.net/)
[![Latest Release](https://img.shields.io/github/v/release/Locko2901/YouTubeMusicTools)](https://github.com/Locko2901/YouTubeMusicTools/releases)
[![MIT License](https://img.shields.io/github/license/Locko2901/YouTubeMusicTools)](LICENSE)

# YouTube (Music) Playlist Tools

A simple application to process YouTube (and YouTube Music) playlists and export them as audio or video files - or just grab the track list.

## Table of Contents
- [Preview](#preview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Credits](#credits)
- [License](#license)

## Preview

![Preview of the GUI](https://raw.githubusercontent.com/Locko2901/YouTubeMusicTools/main/assets/images/preview.png)

## Features

- **Export playlist**: Save a `.txt` file with the title, artist, and video ID for each track.
- **Audio compilation** (optional): Downloads all tracks and merges them into a single MP3 using `ffmpeg`.
- **Video compilation** (optional): Creates an MP4 with static image or GIF background and audio.
- **Flexible input**: Accepts both full playlist URLs and plain playlist IDs.
- **Encoder caching**: Caches available `ffmpeg` encoders and presets for faster future runs.
- **Cache management**: Includes a button to clear the encoder cache if needed.

> On first launch, building the encoder cache may take a second.

## Prerequisites

- [FFmpeg](https://ffmpeg.org/download.html) installed and available in your system `PATH`.

> **Tip for Windows users:**  
> 
> The easiest (and safest) way to install FFmpeg on Windows is with [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/), the official Windows Package Manager.  
>  
> With winget, you get:
> - Automatic download of the latest official FFmpeg release from trusted sources
> - System-wide installation - no manual unzipping, copying, or adding to PATH
> - Easy updates and uninstalls in the future  
>
> **To install FFmpeg via winget, open PowerShell or Command Prompt and run:**  
> ```
> winget install ffmpeg
> ```
> This is *way* easier and safer than manually downloading and extracting the binaries. 

## Finding Your Playlist ID

1. Open the playlist in your browser (YouTube or YouTube Music).
2. In the URL, locate the `list=` parameter. For example, in
   `https://www.youtube.com/playlist?list=PLxyz123456`, the playlist ID is `PLxyz123456`.

Paste either the full URL or just the ID - both work.

## Installation

### Option 1: Windows Installer

Download the latest installer (YTMTools-Setup.exe) from [Releases](https://github.com/Locko2901/YouTubeMusicTools/releases) for a standard Windows installation.

### Option 2: Portable Version

Download the latest zip from [Releases](https://github.com/Locko2901/YouTubeMusicTools/releases).

> Note: All binaries are unsigned - if you prefer, build from source.

### Option 3: Build from Source

1. Clone the repo:

    ```bash
    git clone https://github.com/Locko2901/YouTubeMusicTools.git
    cd YouTubeMusicTools
    ```

2. Compile with Nuitka:

- **For a standalone build:**

    ```bash
    python -m nuitka --mingw64 --standalone --windows-console-mode=disable --include-data-files=assets/icons/img.ico=assets/icons/img.ico --include-data-files=assets/images/default.png=assets/images/default.png --enable-plugin=tk-inter --nofollow-import-to=yt_dlp.extractor.lazy_extractors --windows-icon-from-ico=assets/icons/img.ico --output-dir=ytmtools.dist --output-filename=ytmtools src/main.py
    ```

- **For a non-standalone build:**

    ```bash
    python -m nuitka --mingw64 --enable-plugin=tk-inter --follow-imports --nofollow-import-to=yt_dlp.extractor.lazy_extractors --windows-icon-from-ico=assets/icons/img.ico --output-filename=ytmtools src/main.py
    ```

Or just run directly: `python src/main.py`

## Usage

Launch the tool and follow the labels. It’s mostly self-explanatory.
If not, yell at your screen (or check the logs).

> Note: Playlist has to be public or unlisted.

## Troubleshooting
 
If something breaks:
- Try clearing the encoder cache
- Check the logs
- Open an issue
- Or hey, maybe fix it yourself
- Or don't. It's your time.

## Roadmap

- [ ] Parallel download (maybe someday)
- [ ] Better threading, so GUI is less laggy (also maybe someday)

## Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - handles all the downloading
- [Nuitka](https://nuitka.net/) - compiles Python into binaries
- [FFmpeg](https://ffmpeg.org/) - the audio/video backend hero

_This app is, aside from one core feature, essentially a GUI wrapper around `yt-dlp` - shoutout to the legends behind it._

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
