# YouTube (Music) Playlist Tools

A simple application to process YouTube (music) playlists.

## Overview

This app requires the YouTube Data API v3 key and a playlist ID. It will generate a `.txt` file containing the title, artist, and video ID of each song in the playlist. The app then offers the option to download all songs and use `ffmpeg` to combine them into one large MP3 file.

## Preview

![Project Screenshot](https://github.com/Locko2901/YouTubeMusicTools/blob/main/media/preview.png)

## Prerequisites

- YouTube Data API v3 key
- `ffmpeg` installed on your system

### Getting the YouTube Data API v3 Key

1. Visit the [Google Developers Console](https://console.developers.google.com/).
2. Create a new project.
3. Navigate to "APIs & Services" > "Library", and enable the "YouTube Data API v3".
4. Go to "Credentials" and create an API key.

For a detailed guide, refer to [this tutorial](https://developers.google.com/youtube/registering_an_application).

### Installing FFmpeg

- Visit the [FFmpeg official website](https://ffmpeg.org/download.html) for installation instructions on your operating system.

### Finding the Playlist ID

1. Go to the YouTube playlist in a browser.
2. The playlist ID is the string after `list=` in the URL. For example, in `https://www.youtube.com/playlist?list=PLxyz123456`, `PLxyz123456` is the playlist ID.

## Usage

1. Ensure `ffmpeg` is installed and accessible from the command line.
2. Obtain your API key and playlist ID as described above.
3. Run the application. The first time you use it, you will be prompted to provide your API key and playlist ID. The API key will be saved for future use.
4. The app will generate a `.txt` file and ask if you'd like to download the playlist.
5. If you answer "yes", the app will download the playlist and combine it into an MP3 file.

## Downloading and Compiling

You can download the zip containing the executable from [Releases](https://github.com/Locko2901/YouTubeMusicTools/releases). However, the CI is currently broken, so it is pretty much a trust-me-bro. If you don't want to risk it, I suggest compiling yourself (alternatively just run it locally from the main.py file):

1. Ensure you have the necessary build tools installed.
2. Clone the repository:

    ```bash
    git clone https://github.com/Locko2901/YouTubeMusicTools.git
    ```
3. Build the project:

    ```bash
    cd YouTubeMusicTools
    ```

    - Choose the build command depending on whether you need a standalone application:

        **For a standalone build:**

        ```bash
        python -m nuitka --mingw64 --standalone --windows-console-mode=disable \
        --include-data-files=media/img.ico=media/img.ico --enable-plugin=tk-inter \
        --nofollow-import-to=yt_dlp.extractor.lazy_extractors \
        --windows-icon-from-ico=media/img.ico --output-dir=ytmtools.dist \
        --output-filename=ytmtools src/main.py
        ```

        **For a non-standalone build:**

        ```bash
        python -m nuitka --mingw64 --enable-plugin=tk-inter --follow-imports \
        --nofollow-import-to=yt_dlp.extractor.lazy_extractors \
        --windows-icon-from-ico=media/img.ico --output-filename=ytmtools src/main.py
        ```

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/Locko2901/YouTubeMusicTools/blob/main/LICENSE) file for details.