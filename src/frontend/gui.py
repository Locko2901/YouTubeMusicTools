import os
import threading
from tkinter import messagebox

from customtkinter import *

from backend.downloader import download_videos, merge_files
from backend.file_handler import write_to_file
from backend.youtube_service import get_playlist_items, get_playlist_name
from frontend.config import DOWNLOAD_DIR, LATEST_LOG_FILE, LOG_DIR, OUTPUT_DIR, ROOT_DIR
from frontend.file_management import cleanup_partial_downloads, list_files
from frontend.layout import create_main_layout
from frontend.utils import calculate_directory_size, cancel_download, create_directories, reset_button, reset_progress, update_progress, trim_logs_directory
from tools.logger import get_logger

create_directories([DOWNLOAD_DIR, OUTPUT_DIR, LOG_DIR])
trim_logs_directory(LOG_DIR)

logger = get_logger()

class YouTubeDownloaderGUI:
    def __init__(self):
        self.root = CTk()
        set_appearance_mode("dark")
        self.root.title('YouTube Music Tools')

        base_path = os.path.abspath("./assets/icons")
        icon_path = os.path.join(base_path, 'img.ico')
        self.root.iconbitmap(icon_path)

        self.cancel_event = threading.Event()

        create_main_layout(self)

        reset_progress(self)
        list_files(self)
        self.update_directory_sizes()

    def download_and_process(self):
        if not hasattr(self, 'canceling') or not self.canceling:
            self.canceling = False
            self.cancel_event.clear()
            self.download_button.configure(text="Cancel Process", command=lambda:cancel_download(self))
            playlist_id = self.playlist_entry.get().strip()
            
            if not playlist_id:
                logger.error("Error: Playlist ID cannot be empty.")
                messagebox.showerror("Error", "Playlist ID cannot be empty.")
                reset_button(self)
                return
            
            logger.info(f"Retrieving playlist name using Playlist ID: '{playlist_id}'")
            playlist_name = get_playlist_name(playlist_id)
            if not playlist_name:
                logger.error("Error: Failed to retrieve playlist name.")
                messagebox.showerror("Error", "Failed to retrieve playlist name.")
                reset_button(self)
                return
            
            logger.info(f"Playlist '{playlist_name}' found. Retrieving playlist items...")
            videos = get_playlist_items(playlist_id)
            if videos is None:
                logger.error("Error: Failed to retrieve playlist items.")
                messagebox.showerror("Error", "Failed to retrieve playlist items.")
                reset_button(self)
                return
            
            logger.info(f"Retrieved {len(videos)} videos from playlist '{playlist_name}'.")
        
            write_to_file(videos, playlist_name)
            if messagebox.askyesno("Confirmation", "Do you want to download the songs?"):
                self.progress_info_frame.pack(pady=10)
                self.download_button.configure(text="Cancel Process", command=lambda: cancel_download(self))
        
                def background_task():
                    try:
                        total_videos = len(videos)
                        self.progress_bar.set(0)
                        downloaded_files = []
                        for i, video in enumerate(videos, start=1):
                            if self.cancel_event.is_set():
                                logger.info("Download canceled by user.")
                                cleanup_partial_downloads(self)
                                messagebox.showinfo("Cancelled", "Download has been canceled.")
                                reset_button(self)
                                reset_progress(self)
                                return
                            
                            video_files = download_videos([video])
                            downloaded_files.extend(video_files)
                            update_progress(self, i, total_videos)
                        merge_files(playlist_name, downloaded_files)
                        messagebox.showinfo("Success", "Videos downloaded and processed successfully.")
                        list_files(self)
                        self.update_directory_sizes()
                        reset_progress(self)
                    except Exception as e:
                        logger.error(f"An error occurred: {str(e)}")
                        messagebox.showerror("Error", f"An error occurred: {str(e)}")
                    finally:
                        reset_button(self)
        
                thread = threading.Thread(target=background_task)
                thread.start()
            else:
                messagebox.showinfo("Cancelled", "Download canceled.")
                list_files(self)
                self.update_directory_sizes()
                reset_button(self)
                reset_progress(self)
        else:
            cancel_download(self)

    def run(self):
        self.root.mainloop()

    def update_directory_sizes(self):
        def format_size(size_bytes):
            size_mb = size_bytes / (1024 * 1024)
            if size_mb >= 1024:
                size_gb = size_mb / 1024
                return f"{size_gb:.2f} GB"
            else:
                return f"{size_mb:.2f} MB"

        download_size = calculate_directory_size(DOWNLOAD_DIR)
        output_size = calculate_directory_size(OUTPUT_DIR)
        overall_size = calculate_directory_size(ROOT_DIR)

        self.download_size_label.configure(text=f"Download Directory Size: {format_size(download_size)}")
        self.output_size_label.configure(text=f"Output Directory Size: {format_size(output_size)}")
        self.overall_size_label.configure(text=f"Overall Size: {format_size(overall_size)}")

    def get_latest_log_entries(self, num_lines=10):
        try:
            with open(LATEST_LOG_FILE, 'r') as f:
                return ''.join(f.readlines()[-num_lines:])
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            return f"An error occurred: {str(e)}"

if __name__ == "__main__":
    app = YouTubeDownloaderGUI()
    app.run()
