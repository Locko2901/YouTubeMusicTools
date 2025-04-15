import os
import threading
from tkinter import messagebox

from customtkinter import *

from backend.downloader import download_videos, merge_files
from backend.file_handler import write_to_file
from backend.youtube_service import get_playlist_items, get_playlist_name
from frontend.config import DOWNLOAD_DIR, LATEST_LOG_FILE, LOG_DIR, OUTPUT_DIR, ROOT_DIR
from frontend.file_management import list_files
from frontend.layout import create_main_layout
from frontend.utils import calculate_directory_size, create_directories, trim_logs_directory
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

        # Create main frame for layout
        create_main_layout(self)

        list_files(self)
        self.update_directory_sizes()

    def download_and_process(self):
        playlist_id = self.playlist_entry.get().strip()
        
        if not playlist_id:
            logger.error("Error: Playlist ID cannot be empty.")
            messagebox.showerror("Error", "Playlist ID cannot be empty.")
            return
        
        
        logger.info(f"Retrieving playlist name using Playlist ID: '{playlist_id}'")
        playlist_name = get_playlist_name(playlist_id)
        if not playlist_name:
            logger.error("Error: Failed to retrieve playlist name.")
            messagebox.showerror("Error", "Failed to retrieve playlist name.")
            return
        
        logger.info(f"Playlist '{playlist_name}' found. Retrieving playlist items...")
        videos = get_playlist_items(playlist_id)
        if videos is None:
            logger.error("Error: Failed to retrieve playlist items.")
            messagebox.showerror("Error", "Failed to retrieve playlist items.")
            return
        
        logger.info(f"Retrieved {len(videos)} videos from playlist '{playlist_name}'.")

        write_to_file(videos, playlist_name)
        if messagebox.askyesno("Confirmation", "Do you want to download the songs?"):
            self.progress_bar.pack(pady=10)
            self.progress_label.pack(pady=5)

            def background_task():
                try:
                    total_videos = len(videos)
                    self.progress_bar.set(0)
                    downloaded_files = []
                    for i, video in enumerate(videos, start=1):
                        video_files = download_videos([video])
                        downloaded_files.extend(video_files)
                        self.update_progress(i, total_videos)
                    merge_files(playlist_name, downloaded_files)
                    messagebox.showinfo("Success", "Videos downloaded and processed successfully.")
                    list_files(self)
                    self.update_directory_sizes()
                except Exception as e:
                    logger.error(f"An error occurred: {str(e)}")
                    messagebox.showerror("Error", f"An error occurred: {str(e)}")

            thread = threading.Thread(target=background_task)
            thread.start()
        else:
            messagebox.showinfo("Cancelled", "Download canceled.")
            list_files(self)
            self.update_directory_sizes()

    def update_directory_sizes(self):
        download_size = calculate_directory_size(DOWNLOAD_DIR)
        output_size = calculate_directory_size(OUTPUT_DIR)
        overall_size = calculate_directory_size(ROOT_DIR)
        self.download_size_label.configure(text=f"Download Directory Size: {download_size / (1024 * 1024):.2f} MB")
        self.output_size_label.configure(text=f"Output Directory Size: {output_size / (1024 * 1024):.2f} MB")
        self.overall_size_label.configure(text=f"Overall Size: {overall_size / (1024 * 1024):.2f} MB")

    def update_progress(self, current, total):
        percentage = (current / total) * 100
        self.progress_bar.set(current / total)
        self.progress_label.configure(text=f"{percentage:.2f}% Complete")
        self.root.update_idletasks()

    def run(self):
        self.root.mainloop()

    def get_latest_log_entries(self, num_lines=10):
        """ Retrieve the last few lines from the log file """
        try:
            with open(LATEST_LOG_FILE, 'r') as f:
                return ''.join(f.readlines()[-num_lines:])
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            return f"An error occurred: {str(e)}"

if __name__ == "__main__":
    app = YouTubeDownloaderGUI()
    app.run()