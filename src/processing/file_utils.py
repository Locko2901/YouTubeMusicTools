import os
import re

import config.settings as cs

from utils.logging import get_logger

logger = get_logger()

def sanitize_filename(name: str, max_length: int = 255) -> str:
    """
    Sanitize a string to be safely used as a file name.
    
    Args:
        name (str): The raw string input to sanitize.
        max_length (int): Maximum allowed length for the sanitized name.
    Returns:
        str: Sanitized file name.
    """
    name = name.lower()
    sanitized_name = re.sub(r'[^\w\s]', '', name)
    sanitized_name = re.sub(r'\s+', '_', sanitized_name).strip('_')
    return sanitized_name[:max_length]

def write_to_file(videos, playlist_name):
    """
    Write video information (title, artist, video_id) to a text file named after the playlist.

    Args:
        videos (List[Tuple[str, str, str]]): A list of tuples (title, artist, video_id).
        playlist_name (str): The display/name of the playlist.
        output_dir (str): Directory where the output file will be placed.
    """
    output_dir = cs.OUTPUT_DIR
    sanitized_name = sanitize_filename(playlist_name)
    filename = sanitized_name + '.txt'
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(f'{playlist_name}\n\n')
            for title, artist, video_id in videos:
                file.write(f'Title: {title}\nArtist: {artist}\nVideo ID: {video_id}\n\n')
        logger.info(f'Playlist titles and artists have been written to {os.path.abspath(filepath)}.')
    except IOError as e:
        logger.error(f"An error occurred while writing to the file: {e}")
