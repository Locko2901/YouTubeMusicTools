import os
import subprocess
import uuid
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
from utils.logging import get_logger

logger = get_logger()

# =================== Patch Subprocesses for Windows ===================

if os.name == 'nt':
    _orig_popen = subprocess.Popen
    class NoConsolePopen(subprocess.Popen):
        def __init__(self, *args, **kwargs):
            kwargs['creationflags'] = kwargs.get('creationflags', 0) | subprocess.CREATE_NO_WINDOW
            _orig_popen.__init__(self, *args, **kwargs)
    subprocess.Popen = NoConsolePopen

# =================== Audio Downloader ===================
def download_videos(videos, download_dir="./data/downloads"):
    """
    Downloads the best available audio for a list of YouTube videos and saves them as MP3 (320 kbps).
    Args:
        videos (List[Tuple[str, str, str]]): Each tuple is (title, artist, video_id).
        download_dir (str): Directory to save downloads.
    Returns:
        dict: Mapping of downloaded filenames to song titles.
    """
    os.makedirs(download_dir, exist_ok=True)
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }]
    }

    downloaded_files = {}
    for title, artist, video_id in videos:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        unique_id = str(uuid.uuid4())
        ydl_opts['outtmpl'] = os.path.join(download_dir, f"{unique_id}.%(ext)s")
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            downloaded_filename = f"{unique_id}.mp3"
            downloaded_files[downloaded_filename] = title
            logger.info(f"Downloaded: {title} by {artist} as {downloaded_filename}")
        except DownloadError as e:
            logger.error(f"Download Error for {title} by {artist}: {e}")
        except Exception as e:
            logger.error(f"Error downloading {title} by {artist}: {e}")

    return downloaded_files

# =================== Audio Merger ===================

def merge_files(playlist_name, downloaded_files, download_dir="./data/downloads", output_dir="./data/output"):
    """
    Concatenates multiple MP3 files into one playlist MP3 file using ffmpeg.
    Args:
        playlist_name (str): Name for the playlist output file (no extension).
        downloaded_files (dict): Mapping of filenames to titles.
        download_dir (str): Directory containing the MP3s.
        output_dir (str): Output directory for the merged playlist.
    """
    os.makedirs(output_dir, exist_ok=True)
    filelist_path = "filelist.txt"
    logger.info("Merging all files into one...")
    logger.debug(f"Files to merge: {downloaded_files}")

    if downloaded_files:
        try:
            with open(filelist_path, "w") as f:
                for filename in downloaded_files:
                    path = os.path.abspath(os.path.join(download_dir, filename))
                    if os.path.exists(path):
                        f.write(f"file '{path}'\n")
                    else:
                        logger.warning(f"File {path} not found.")

            output_path = os.path.abspath(os.path.join(output_dir, f"{playlist_name}.mp3"))
            subprocess.run(
                ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', filelist_path, '-c', 'copy', output_path],
                check=True
            )
            logger.info(f"All files have been merged into {output_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed with error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during merging: {e}")
        finally:
            if os.path.exists(filelist_path):
                os.remove(filelist_path)
            for filename in downloaded_files:
                mp3_path = os.path.join(download_dir, filename)
                if os.path.exists(mp3_path):
                    os.remove(mp3_path)
    else:
        logger.info("No files found to merge.")
