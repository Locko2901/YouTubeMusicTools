import os
import re

def sanitize_filename(name, max_length=255):
    """Sanitize a string to be used as a safe file name."""
    name = name.lower()
    sanitized_name = re.sub(r'[^\w\s]', '', name)
    sanitized_name = re.sub(r'\s+', '_', sanitized_name).strip('_')
    return sanitized_name[:max_length]

def write_to_file(videos, playlist_name):
    """Write video information to a file."""
    sanitized_name = sanitize_filename(playlist_name)
    filename = sanitized_name + '.txt'
   
    output_dir = './data/output'
    os.makedirs(output_dir, exist_ok=True)
   
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(f'{playlist_name}\n\n')
            for title, artist, video_id in videos:
                file.write(f'Title: {title}\nArtist: {artist}\nVideo ID: {video_id}\n\n')
        
        print(f'Playlist titles and artists have been written to {os.path.abspath(filepath)}.')
    except IOError as e:
        print(f"An error occurred while writing to the file: {e}")