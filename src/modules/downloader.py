import subprocess
import os
import uuid
import logging
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

# Configure logger once at the module level
logger = logging.getLogger("YouTubeDownloader")
logger.setLevel(logging.INFO)
if not logger.handlers:  # Ensure no duplicate handlers
    ch = logging.StreamHandler()  # Console handler
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def download_videos(videos, download_dir="./data/downloads"):
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
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            unique_id = str(uuid.uuid4())
            ydl_opts['outtmpl'] = os.path.join(download_dir, f"{unique_id}.%(ext)s")
            
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

def merge_files(playlist_name, downloaded_files, download_dir="./data/downloads", output_dir="./data/output"):
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("Merging all files into one...")
    logger.debug(f"Files to merge: {downloaded_files}")
    
    if downloaded_files:
        try:
            with open("filelist.txt", "w") as f:
                for filename in downloaded_files:
                    path = os.path.abspath(os.path.join(download_dir, filename))
                    if os.path.exists(path):
                        f.write(f"file '{path}'\n")
                    else:
                        logger.warning(f"File {path} not found.")
                        
            output_path = os.path.abspath(os.path.join(output_dir, f"{playlist_name}.mp3"))
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.run(
                ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', 'filelist.txt', '-c', 'copy', output_path],
                check=True,
                creationflags=creationflags
            )
            logger.info(f"All files have been merged into {output_path}")
        
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed with error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during merging: {e}")
        
        finally:
            if os.path.exists("filelist.txt"):
                os.remove("filelist.txt")
        
        for filename in downloaded_files:
            mp3_path = os.path.join(download_dir, filename)
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
    else:
        logger.info("No files found to merge.")