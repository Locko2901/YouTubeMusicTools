import os
from tkinter import messagebox

def calculate_directory_size(directory):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def clear_directory(directory):
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        messagebox.showinfo("Success", "Download directory cleared.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to clear download directory: {str(e)}")

def create_directories(directories):
    for directory in directories:
        os.makedirs(directory, exist_ok=True)