import os
import threading
from tkinter import messagebox, StringVar
from customtkinter import *
from processing.pipeline import download_and_process_pipeline
from processing.video_encoder import get_available_encoders, make_mp4
from utils.logging import get_logger
from config.settings import DOWNLOAD_DIR, OUTPUT_DIR, LOG_DIR, ROOT_DIR
from services.file_service import list_files, create_directories, trim_logs_directory
from gui.layout import create_main_layout, handle_download_button_click, handle_mp4_button_click

create_directories([DOWNLOAD_DIR, OUTPUT_DIR, LOG_DIR])
trim_logs_directory(LOG_DIR)
logger = get_logger()

class YouTubeDownloaderGUI:
    """
    Main Application GUI for YouTube Music Tools.
    Handles download, process, display, and UI state.
    """

    def __init__(self):
        self.root = CTk()
        set_appearance_mode("dark")
        self.root.title('YouTube Music Tools')
        self._set_icon()
        self.logger = logger

        # Threading and event flags for concurrent operations/cancels
        self.cancel_event = threading.Event()
        self.conversion_cancel_event = threading.Event()
        self.makeMp4_cancel_event = threading.Event()
        self.canceling = False

        # Directory configuration
        self.download_dir = os.path.abspath(DOWNLOAD_DIR)
        self.output_dir = os.path.abspath(OUTPUT_DIR)
        self.overall_dir = os.path.abspath(ROOT_DIR)
        
        # Encoding/Conversion state
        self.encoders = get_available_encoders()
        self.encoder_var = StringVar(value="")
        self.preset_var = StringVar(value="medium")
        self.selected_encoder_info = {"encoder": None, "preset": None}
        self.make_mp4_callback = make_mp4

        # Layout & UI setup
        create_main_layout(self)
        self.reset_progress()
        list_files(self)
        self.update_directory_sizes()

    def _set_icon(self):
        try:
            base_path = os.path.abspath("./assets/icons")
            icon_path = os.path.join(base_path, 'img.ico')
            self.root.iconbitmap(icon_path)
        except Exception as e:
            self.logger.warning(f"Could not set icon - {e}")

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

    def calculate_directory_size(self, path):
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.isfile(fp):
                    total += os.path.getsize(fp)
        return total

    def update_directory_sizes(self):
        download_size = self.calculate_directory_size(self.download_dir)
        output_size = self.calculate_directory_size(self.output_dir)
        overall_size = self.calculate_directory_size(self.overall_dir)
        self.download_size_label.configure(text=f"Download Directory Size: {self.format_size(download_size)}")
        self.output_size_label.configure(text=f"Output Directory Size: {self.format_size(output_size)}")
        self.overall_size_label.configure(text=f"Overall Size: {self.format_size(overall_size)}")

    def cancel_download(self):
        self.cancel_event.set()
        self.canceling = True
        self.download_button.configure(text="Cancelling...", state="disabled")

    def cancel_conversion(self):
        self.conversion_cancel_event.set()
        self.download_button.configure(text="Cancelling...", state="disabled")

    def cancel_make_mp4(self):
        self.makeMp4_cancel_event.set()
        self.makeMp4_button.configure(text="Cancelling...", state="disabled")

    def reset_button(self):
        self.download_button.configure(
            text="Process Playlist",
            command=lambda: handle_download_button_click(self),
            state="normal"
        )
        self.makeMp4_button.configure(
            text="Make MP4",
            state="normal"
        )
        self.canceling = False

    def reset_mp4_button(self):
        self.makeMp4_button.configure(
            text="Make MP4",
            command=lambda: handle_mp4_button_click(self),
            state="normal"
        )
        self.download_button.configure(
            text="Process Playlist",
            state="normal"
        )
        self.canceling = False

    def update_progress(self, current, total):
        percentage = (current / total) * 100 if total else 0
        self.progress_bar.set(current / total if total else 0)
        self.progress_label.configure(text=f"{percentage:.2f}%")
        self.root.update_idletasks()

    def reset_progress(self):
        self.progress_bar.set(0)
        self.progress_label.configure(text="0%")
        self.root.update_idletasks()
        self.progress_info_frame.pack_forget()

    def download_and_process(self):
        # Now delegates the workflow to pipeline.py
        download_and_process_pipeline(self, self.logger)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = YouTubeDownloaderGUI()
    app.run()
