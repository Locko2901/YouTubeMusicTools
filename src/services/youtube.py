import re
import traceback
from yt_dlp import YoutubeDL
from utils.logging import get_logger

logger = get_logger()

def normalize_playlist_url(playlist_input):
    """
    Accepts a YouTube playlist ID or URL and returns a canonical playlist URL.
    Args:
        playlist_input (str): Playlist ID or URL.
    Returns:
        str: Canonical playlist URL.
    Raises:
        ValueError: If input is invalid.
    """
    url_regex = (
        r"(?:https?://)?"
        r"(?:[\w\-]+\.)?"
        r"youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)"
    )
    m = re.match(url_regex, playlist_input.strip())
    if m:
        playlist_id = m.group(1)
    else:
        playlist_id = playlist_input.strip()
        if not re.match(r"^[a-zA-Z0-9_-]{10,}$", playlist_id):
            raise ValueError(f"Invalid playlist ID or URL: {playlist_input}")
    return f"https://www.youtube.com/playlist?list={playlist_id}"

def get_youtube_client():
    """
    Create and return a YoutubeDL client instance with specified options.

    Returns:
        YoutubeDL: Configured YoutubeDL client.
    Raises:
        Exception: If client creation fails.
    """
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
        }
        client = YoutubeDL(ydl_opts)
        logger.info("YoutubeDL client created successfully.")
        return client
    except Exception as e:
        logger.error(f"Error occurred while creating YoutubeDL client: {type(e).__name__}: {e}")
        logger.debug(traceback.format_exc())
        raise


def get_playlist_name(playlist_input):
    """
    Fetch the title (name) of a YouTube playlist.

    Args:
        playlist_input (str): YouTube playlist ID or URL.
    Returns:
        str or None: Playlist title, or None if not found.
    Raises:
        Exception: Re-raises critical errors.
    """
    try:
        client = get_youtube_client()
        playlist_url = normalize_playlist_url(playlist_input)
        info = client.extract_info(playlist_url, download=False)
        if info and 'title' in info:
            playlist_name = info['title']
            logger.info(f"Playlist name fetched successfully: {playlist_name}")
            return playlist_name
        else:
            logger.warning(f"No playlist found with input: {playlist_input}")
            return None
    except Exception as e:
        logger.error(f"An error occurred while fetching the playlist name: {type(e).__name__}: {e}")
        logger.debug(traceback.format_exc())
        raise


def get_playlist_items(playlist_input):
    """
    Fetch all video items (title, uploader, id) from a YouTube playlist.

    Args:
        playlist_input (str): YouTube playlist ID or URL.
    Returns:
        list of tuples or []: Each tuple is (title, artist/uploader, video_id), or [] if empty or failed.
    """
    try:
        client = get_youtube_client()
        playlist_url = normalize_playlist_url(playlist_input)
        info = client.extract_info(playlist_url, download=False)
        videos = []
        if info and 'entries' in info:
            for entry in info['entries']:
                title = entry.get('title', 'Unknown Title')
                artist = entry.get('uploader', 'Unknown Artist')
                video_id = entry.get('id')
                if video_id:
                    videos.append((title, artist, video_id))
        if videos:
            logger.info(f"Fetched {len(videos)} videos from playlist input: {playlist_input}")
            return videos
        else:
            logger.warning(f"No videos found in playlist input: {playlist_input}")
            return []
    except Exception as e:
        logger.error(f"An error occurred while fetching the playlist items: {type(e).__name__}: {e}")
        logger.debug(traceback.format_exc())
        return []
