import os
import platform
import subprocess
import glob

import sys
from tkinter import ACTIVE, END, messagebox

from config.settings import DOWNLOAD_DIR, OUTPUT_DIR
from utils.logging import get_logger

logger = get_logger()

# =================== File Management ===================

def list_files(app):
    """
    Lists files from OUTPUT_DIR in the application's file_listbox.
    """
    logger.info("Listing files in the output directory.")
    app.file_listbox.delete(0, END)
    pad_spaces = 2
    try:
        files = os.listdir(OUTPUT_DIR)
        for file in files:
            pad = ' ' * pad_spaces
            app.file_listbox.insert(END, f"{pad}{file}")
        logger.info(f"Listed {len(files)} files.")
    except FileNotFoundError:
        logger.error(f"The directory {OUTPUT_DIR} does not exist.")
        messagebox.showerror("Error", f"The directory {OUTPUT_DIR} does not exist.")

def open_file(app):
    """
    Opens the selected file from the listbox using the OS default application.
    """
    selected_file = app.file_listbox.get(ACTIVE).strip()
    if not selected_file:
        logger.warning("No file selected for opening.")
        messagebox.showwarning("No File Selected", "Please select a file to open.")
        return

    file_path = os.path.join(OUTPUT_DIR, selected_file)
    if os.path.isfile(file_path):
        try:
            logger.info(f"Opening file {file_path}")
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', file_path], check=False)
            else:
                subprocess.run(['xdg-open', file_path], check=False)
        except Exception as e:
            logger.error(f"Failed to open file {file_path}: {str(e)}")
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")
    else:
        logger.warning(f"File does not exist: {file_path}")
        messagebox.showwarning("File Not Found", "Selected file does not exist.")

def show_file_in_directory(app):
    selected_file = app.file_listbox.get(ACTIVE).strip()
    if not selected_file:
        logger.warning("No file selected for showing in directory.")
        messagebox.showwarning("No File Selected", "Please select a file to show in directory.")
        return
    file_path = os.path.abspath(os.path.join(OUTPUT_DIR, selected_file))
    if os.path.isfile(file_path):
        try:
            logger.info(f"Showing file {file_path} in directory.")
            if sys.platform.startswith('darwin'):
                subprocess.run(['open', '-R', file_path], check=False)
            elif os.name == 'nt':
                subprocess.run(['explorer', '/select,', file_path], check=False)
            elif os.name == 'posix':
                dir_path = os.path.dirname(file_path)
                subprocess.run(['xdg-open', dir_path], check=False)
        except Exception as e:
            logger.error(f"Failed to show file {file_path} in directory: {str(e)}")
            messagebox.showerror("Error", f"Failed to show file in directory: {str(e)}")
    else:
        logger.warning(f"File does not exist: {file_path}")
        messagebox.showwarning("File Not Found", "Selected file does not exist.")

def delete_file(app):
    """
    Deletes the selected file from OUTPUT_DIR.
    """
    selected_file = app.file_listbox.get(ACTIVE).strip()
    if not selected_file:
        logger.warning("No file selected for deletion.")
        messagebox.showwarning("No File Selected", "Please select a file to delete.")
        return

    file_path = os.path.join(OUTPUT_DIR, selected_file)
    if not os.path.isfile(file_path):
        logger.error(f"File {selected_file} does not exist.")
        messagebox.showerror("Error", "Selected file does not exist.")
        return

    try:
        logger.info(f"Deleting file {selected_file}.")
        os.remove(file_path)
        if not getattr(app, 'encoder_view_active', False):
            list_files(app)
            app.update_directory_sizes()
        logger.info(f"File {selected_file} deleted successfully.")
    except PermissionError:
        logger.warning(f"File {selected_file} is in use by another process.")
        messagebox.showwarning("File In Use", "Selected file is in use by another process and cannot be deleted.")
    except Exception as e:
        logger.error(f"Failed to delete file {selected_file}: {str(e)}")
        messagebox.showerror("Error", f"Failed to delete file: {str(e)}")

def open_directory(directory):
    """
    Opens the specified directory in the OS file manager.
    """
    try:
        if platform.system() == 'Windows':
            os.startfile(directory)
        elif platform.system() == 'Darwin':
            subprocess.call(['open', directory])
        else:
            subprocess.call(['xdg-open', directory])
        logger.info(f"Opened directory: {directory}")
    except Exception as e:
        logger.error(f"Failed to open directory {directory}: {e}")
        messagebox.showerror("Error", f"Failed to open directory: {directory}\n{e}")

# =================== Directory Management ===================

def calculate_directory_size(directory):
    """
    Recursively calculates the size in bytes of a directory.
    Returns:
        int: Total size in bytes.
    """
    logger.info(f"Calculating size for directory: {directory}")
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total_size += os.path.getsize(fp)
            except Exception as e:
                logger.warning(f"Could not get size for {fp}: {e}")
    logger.info(f"Total size for directory {directory}: {total_size} bytes")
    return total_size

def format_size(size_bytes):
    """
    Formats a size in bytes to a MB/GB human-readable string.
    Returns:
        str: Formatted size string.
    """
    size_mb = size_bytes / (1024 * 1024)
    if size_mb >= 1024:
        size_gb = size_mb / 1024
        return f"{size_gb:.2f} GB"
    else:
        return f"{size_mb:.2f} MB"

def clear_directory(directory):
    """
    Deletes all files in a directory.
    Pops up a message box and logs on error.
    """
    try:
        logger.info(f"Clearing directory: {directory}")
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        logger.info(f"Directory {directory} cleared successfully")
    except Exception as e:
        logger.error(f"Failed to clear directory: {str(e)}")
        messagebox.showerror("Error", f"Failed to clear directory: {str(e)}")

def create_directories(directories):
    """
    Creates all directories in the provided list, if they don't exist.
    """
    for directory in directories:
        logger.info(f"Creating directory: {directory}")
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
    logger.info("All directories created successfully")

def trim_logs_directory(directory, keep_last=4):
    """
    Keeps only the most recent N log files in the specified directory.
    Args:
        directory (str): The directory containing log files.
        keep_last (int): The number of newest log files to keep. Older files are deleted.
    """
    logger.info(f"Trimming logs in directory: {directory}")
    try:
        files = glob.glob(os.path.join(directory, "*"))
        files.sort(key=os.path.getmtime)
        while len(files) > keep_last:
            logger.info(f"Removing old log file: {files[0]}")
            os.remove(files[0])
            files.pop(0)
        logger.info("Log directory trimmed successfully")
    except Exception as e:
        logger.error(f"Failed to trim logs directory: {str(e)}")

# =================== High-Level Directory Management ===================

def clear_download_directory(app):
    """
    Empties the DOWNLOAD_DIR and updates UI.
    """
    logger.info("Clearing download directory.")
    clear_directory(DOWNLOAD_DIR)
    app.update_directory_sizes()
    logger.info("Download directory cleared.")

def cleanup_partial_downloads(app):
    """
    Alias for clear_download_directory, for semantic clarity.
    """
    clear_download_directory(app)
