import json
import logging
import os
import sys
import threading
import uuid
from logging.handlers import TimedRotatingFileHandler, QueueHandler, QueueListener
from queue import Queue

from customtkinter import *
from tkinter import Listbox, filedialog, messagebox

from gui.utils import calculate_directory_size, clear_directory, create_directories, trim_logs_directory
from modules.youtube_service import get_playlist_name, get_playlist_items
from modules.file_handler import write_to_file
from modules.downloader import download_videos, merge_files

CONFIG_FILE = './config/config.json'
CONFIG_DIR = './config'
DOWNLOAD_DIR = './data/downloads'
OUTPUT_DIR = './data/output'
LOG_DIR = './logs'
ROOT_DIR = '.'
LATEST_LOG_FILE = os.path.join(LOG_DIR, 'latest.log')

create_directories([CONFIG_DIR, DOWNLOAD_DIR, OUTPUT_DIR, LOG_DIR])
trim_logs_directory(LOG_DIR)

class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, encoding='utf-8', **kwargs)

    def doRollover(self):
        super().doRollover()
        
        baseFilename, ext = os.path.splitext(self.baseFilename)
        unique_id = uuid.uuid4()
        new_filename = f"{baseFilename}_{unique_id}{ext}"
        
        if os.path.exists(self.baseFilename):
            os.remove(self.baseFilename)
        
        # Attempt to create a symbolic link
        try:
            os.symlink(new_filename, self.baseFilename)
        except OSError as e:
            print(f"Symlink creation failed: {e}. Consider running with appropriate privileges.")

class StreamToLogger:
    def __init__(self, logger, log_level):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass

def rename_with_unique_id(log_file):
    if os.path.exists(log_file):
        unique_id = uuid.uuid4()
        base_filename, ext = os.path.splitext(log_file)
        new_name = f"{base_filename}_{unique_id}{ext}"

        while os.path.exists(new_name):
            new_name = f"{base_filename}_{unique_id}{ext}"

        os.rename(log_file, new_name)

rename_with_unique_id(LATEST_LOG_FILE)

logger = logging.getLogger('YouTubeDownloaderLogger')
logger.setLevel(logging.DEBUG)

log_queue = Queue(-1)
queue_handler = QueueHandler(log_queue)
logger.addHandler(queue_handler)

file_handler = CustomTimedRotatingFileHandler(LATEST_LOG_FILE)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

listener = QueueListener(log_queue, file_handler)
listener.start()

sys.stdout = StreamToLogger(logger, logging.INFO)
sys.stderr = StreamToLogger(logger, logging.ERROR)

try:
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)
except Exception:
    pass

sys.stdout = StreamToLogger(logger, logging.INFO)
sys.stderr = StreamToLogger(logger, logging.ERROR)

class YouTubeDownloaderGUI:
    def __init__(self):
        self.root = CTk()
        set_appearance_mode("dark")
        self.root.title('YouTube Playlist Downloader')

        base_path = os.path.abspath("./media")

        icon_path = os.path.join(base_path, 'img.ico')
        self.root.iconbitmap(icon_path)

        self.load_config()
        
        # Create main frame for layout
        self.main_layout()

        self.list_files()
        self.update_directory_sizes()

    def main_layout(self):
        main_frame = CTkFrame(self.root, fg_color="#1e1e28")
        main_frame.pack(padx=1, pady=1, fill="both", expand=True)
        self.create_api_section(main_frame)
        self.create_playlist_section(main_frame)
        self.create_progress_section(main_frame)
        self.create_file_management_section(main_frame)
        self.create_size_labels(main_frame)

    def create_api_section(self, parent):
        # Label and Entry for API Key
        api_label = CTkLabel(parent, text="Enter API Key:", text_color="#FF3366", font=("Arial", 12))
        api_label.pack(pady=(10, 0))
        self.api_entry = CTkEntry(parent, placeholder_text="API Key", width=400, text_color="#F5E6F7")
        self.api_entry.insert(0, self.config.get("API_KEY", ""))
        self.api_entry.pack(pady=(0, 10), padx=15)

    def create_playlist_section(self, parent):
        # Label and Entry for Playlist ID
        playlist_label = CTkLabel(parent, text="Enter Playlist ID:", text_color="#FF3366", font=("Arial", 12))
        playlist_label.pack(pady=(10, 0))
        self.playlist_entry = CTkEntry(parent, placeholder_text="Playlist ID", width=400, text_color="#F5E6F7")
        self.playlist_entry.pack(pady=(0, 10), padx=15)

    def create_progress_section(self, parent):
        # Progress indicator
        self.progress_label = CTkLabel(parent, text="Progress:", text_color="#FF3366", font=("Arial", 12))
        self.progress_label.pack(pady=(10, 5))
        self.progress_bar = CTkProgressBar(
            parent,
            orientation='horizontal',
            width=400,
            corner_radius=10
        )
        self.progress_bar.pack(pady=(0, 10))
        download_button = CTkButton(
            parent, 
            text="Process Playlist", 
            command=self.download_and_process, 
            fg_color="#C2185B",
            hover_color="#880E4F",
        )
        download_button.pack(pady=10, padx=15, fill='x')

    def create_file_management_section(self, parent):
        # File Management Frame
        file_management_frame = CTkFrame(parent, fg_color="#1e1e28", corner_radius=10)
        file_management_frame.pack(padx=10, pady=10, fill="both", expand=True)
        file_management_frame.grid_rowconfigure(0, weight=1)
        file_management_frame.grid_columnconfigure(0, weight=1)

        self.file_listbox = Listbox(
            file_management_frame,
            bg="#1d1d33", 
            font=("Helvetica", 12), 
            selectbackground="#880E4F",
            fg="#FFFFFF",
            selectforeground="#FFFFFF"
        )

        self.file_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        file_scrollbar = CTkScrollbar(
            file_management_frame,
            orientation="vertical",
            command=self.file_listbox.yview,
            button_color="#C2185B",
            button_hover_color="#880E4F"
        )
        file_scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_listbox.configure(yscrollcommand=file_scrollbar.set)

        self.setup_file_buttons(parent)

    def setup_file_buttons(self, parent):
        # File Management Buttons
        refresh_button = CTkButton(
            parent,
            text="Refresh File List",
            command=self.list_files,
            fg_color="#C2185B",
            hover_color="#880E4F",
        )
        refresh_button.pack(pady=5, padx=15, fill='x')

        move_button = CTkButton(
            parent,
            text="Move Selected File",
            command=self.move_file,
            fg_color="#C2185B",
            hover_color="#880E4F",
        )
        move_button.pack(pady=5, padx=15, fill='x')

        delete_button = CTkButton(
            parent,
            text="Delete Selected File",
            command=self.delete_file,
            fg_color="#C2185B",
            hover_color="#880E4F",
        )
        delete_button.pack(pady=5, padx=15, fill='x')

        clear_button = CTkButton(
            parent,
            text="Clear Download Directory",
            command=self.clear_download_directory,
            fg_color="#C2185B",
            hover_color="#880E4F",
        )
        clear_button.pack(pady=5, padx=15, fill='x')

    def create_size_labels(self, parent):
        # Size Labels
        self.download_size_label = CTkLabel(parent, text="", text_color="#FF3366")
        self.download_size_label.pack(pady=5, padx=15)
        self.output_size_label = CTkLabel(parent, text="", text_color="#FF3366")
        self.output_size_label.pack(pady=5, padx=15)
        self.overall_size_label = CTkLabel(parent, text="", text_color="#FF3366")
        self.overall_size_label.pack(pady=5, padx=15)

    def update_directory_sizes(self):
        download_size = calculate_directory_size(DOWNLOAD_DIR)
        output_size = calculate_directory_size(OUTPUT_DIR)
        overall_size = calculate_directory_size(ROOT_DIR)
        self.download_size_label.configure(text=f"Download Directory Size: {download_size / (1024 * 1024):.2f} MB")
        self.output_size_label.configure(text=f"Output Directory Size: {output_size / (1024 * 1024):.2f} MB")
        self.overall_size_label.configure(text=f"Overall Size: {overall_size / (1024 * 1024):.2f} MB")
        
    def load_config(self):
        self.config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
                
    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"API_KEY": self.api_entry.get().strip()}, f)
            
    def download_and_process(self):
        api_key = self.api_entry.get().strip()
        playlist_id = self.playlist_entry.get().strip()
        
        print(f"Received API Key: '{api_key}'")
        print(f"Received Playlist ID: '{playlist_id}'")
        
        if not api_key or not playlist_id:
            print("Error: API Key and Playlist ID cannot be empty.")
            messagebox.showerror("Error", "API Key and Playlist ID cannot be empty.")
            return
        
        print("Saving configuration...")
        self.save_config()
        
        print(f"Retrieving playlist name using API Key: '{api_key}' and Playlist ID: '{playlist_id}'")
        playlist_name = get_playlist_name(api_key, playlist_id)
        if not playlist_name:
            print("Error: Failed to retrieve playlist name.")
            messagebox.showerror("Error", "Failed to retrieve playlist name.")
            return
        
        print(f"Playlist '{playlist_name}' found. Retrieving playlist items...")
        videos = get_playlist_items(api_key, playlist_id)
        if videos is None:
            print("Error: Failed to retrieve playlist items.")
            messagebox.showerror("Error", "Failed to retrieve playlist items.")
            return
        
        print(f"Retrieved {len(videos)} videos from playlist '{playlist_name}'.")
        # Continue processing videos if required

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
                    self.list_files()
                    self.update_directory_sizes()
                except Exception as e:
                    messagebox.showerror("Error", f"An error occurred: {str(e)}")

            thread = threading.Thread(target=background_task)
            thread.start()
        else:
            messagebox.showinfo("Cancelled", "Download canceled.")
            self.list_files()
            self.update_directory_sizes()

    def list_files(self):
        self.file_listbox.delete(0, END)
        pad_spaces = 2
        try:
            files = os.listdir(OUTPUT_DIR)
            for file in files:
                pad = ' ' * pad_spaces
                self.file_listbox.insert(END, f"{pad}{file}")
        except FileNotFoundError:
            messagebox.showerror("Error", f"The directory {OUTPUT_DIR} does not exist.")

    def move_file(self):
        selected_file = self.file_listbox.get(ACTIVE).strip()
        if selected_file:
            dest_dir = filedialog.askdirectory()
            if dest_dir:
                try:
                    shutil.move(os.path.join(OUTPUT_DIR, selected_file), os.path.join(dest_dir, selected_file))
                    messagebox.showinfo("Success", f"File {selected_file} moved successfully.")
                    self.list_files()
                    self.update_directory_sizes()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to download file: {str(e)}")

    def delete_file(self):
        selected_file = self.file_listbox.get(ACTIVE).strip()
        if selected_file:
            try:
                os.remove(os.path.join(OUTPUT_DIR, selected_file))
                messagebox.showinfo("Success", f"File {selected_file} deleted successfully.")
                self.list_files()
                self.update_directory_sizes()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete file: {str(e)}")

    def clear_download_directory(self):
        clear_directory(DOWNLOAD_DIR)
        self.update_directory_sizes()

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
            return f"An error occurred: {str(e)}"

if __name__ == "__main__":
    app = YouTubeDownloaderGUI()
    app.run()