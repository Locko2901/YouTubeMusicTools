import os
import glob
from tkinter import messagebox

from tools.logger import get_logger

logger = get_logger()

def calculate_directory_size(directory):
    logger.info(f"Calculating size for directory: {directory}")
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    logger.info(f"Total size for directory {directory}: {total_size} bytes")
    return total_size

def clear_directory(directory):
    try:
        logger.info(f"Clearing directory: {directory}")
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        messagebox.showinfo("Success", "Download directory cleared.")
        logger.info(f"Directory {directory} cleared successfully")
    except Exception as e:
        logger.error(f"Failed to clear download directory: {str(e)}")
        messagebox.showerror("Error", f"Failed to clear download directory: {str(e)}")

def create_directories(directories):
    for directory in directories:
        logger.info(f"Creating directory: {directory}")
        os.makedirs(directory, exist_ok=True)
    logger.info("All directories created successfully")

def trim_logs_directory(directory):
    logger.info(f"Trimming logs in directory: {directory}")
    files = glob.glob(os.path.join(directory, "*"))
    files.sort(key=os.path.getmtime)
    
    while len(files) > 4:
        logger.info(f"Removing old log file: {files[0]}")
        os.remove(files[0])
        files.pop(0)
    logger.info("Log directory trimmed successfully")