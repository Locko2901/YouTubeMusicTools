import subprocess
import os
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

def download_videos(videos, download_dir="./data/downloads"):
    os.makedirs(download_dir, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
    }
    
    downloaded_files = []
    for title, artist, video_id in videos:
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            sanitized_title = ''.join(e for e in title if e.isalnum() or e in ' _-')
            ydl_opts['outtmpl'] = os.path.join(download_dir, f"{sanitized_title}.%(ext)s")
            
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            downloaded_filename = f"{sanitized_title}.mp3"
            downloaded_files.append(downloaded_filename)
            print(f"Downloaded: {title} by {artist}")
        except DownloadError as e:
            print(f"Download Error for {title} by {artist}: {e}")
        except Exception as e:
            print(f"Error downloading {title} by {artist}: {e}")
    
    return downloaded_files

def merge_files(playlist_name, downloaded_files, download_dir="./data/downloads", output_dir="./data/output"):
    os.makedirs(output_dir, exist_ok=True)
    
    print("Merging all files into one...")
    print(f"Files to merge: {downloaded_files}")  # Debug line to verify the list
    
    if downloaded_files:
        try:
            with open("filelist.txt", "w") as f:
                for filename in downloaded_files:
                    path = os.path.abspath(os.path.join(download_dir, filename))
                    f.write(f"file '{path}'\n")

            output_path = os.path.abspath(os.path.join(output_dir, f"{playlist_name}.mp3"))

            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

            subprocess.run(
                ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', 'filelist.txt', '-c', 'copy', output_path],
                check=True,
                creationflags=creationflags
            )
            print(f"All files have been merged into {output_path}")
        
        except Exception as e:
            print(f"An error occurred during merging: {e}")
        
        finally:
            if os.path.exists("filelist.txt"):
                os.remove("filelist.txt")
        
        for filename in downloaded_files:
            mp3_path = os.path.join(download_dir, filename)
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
    else:
        print("No files found to merge.")