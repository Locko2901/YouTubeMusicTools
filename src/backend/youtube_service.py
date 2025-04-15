import traceback
from yt_dlp import YoutubeDL

from tools.logger import get_logger

logger = get_logger()

def get_youtube_client():
    """Create and return a YoutubeDL client."""
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
        error_message = f"Error occurred while creating YoutubeDL client: {e.__class__.__name__}: {e}"
        detailed_traceback = traceback.format_exc()
        logger.error(error_message)
        logger.debug(detailed_traceback)
        raise

def get_playlist_name(playlist_id):
    """Fetch the name of a YouTube playlist given its ID."""
    try:
        client = get_youtube_client()
        playlist_url = f'https://www.youtube.com/playlist?list={playlist_id}'
        info = client.extract_info(playlist_url, download=False)
        
        if info and 'title' in info:
            playlist_name = info['title']
            logger.info(f"Playlist name fetched successfully: {playlist_name}")
            return playlist_name
        else:
            logger.warning(f"No playlist found with ID: {playlist_id}")
            return None
    except Exception as e:
        error_message = f"An error occurred while fetching the playlist name: {e.__class__.__name__}: {e}"
        detailed_traceback = traceback.format_exc()
        logger.error(error_message)
        logger.debug(detailed_traceback)
        raise

def get_playlist_items(playlist_id):
    """Fetch the items (videos) from a YouTube playlist."""
    try:
        client = get_youtube_client()
        playlist_url = f'https://www.youtube.com/playlist?list={playlist_id}'
        info = client.extract_info(playlist_url, download=False)

        videos = []

        if 'entries' in info:
            for entry in info['entries']:
                title = entry.get('title', 'Unknown Title')
                artist = entry.get('uploader', 'Unknown Artist')
                video_id = entry.get('id')
                
                if video_id:
                    videos.append((title, artist, video_id))

        if videos:
            logger.info(f"Fetched {len(videos)} videos from playlist ID: {playlist_id}")
            return videos
        else:
            logger.warning(f"No videos found in playlist ID: {playlist_id}")
            return None
    except Exception as e:
        error_message = f"An error occurred while fetching the playlist items: {e.__class__.__name__}: {e}"
        detailed_traceback = traceback.format_exc()
        logger.error(error_message)
        logger.debug(detailed_traceback)
        return None