import os
import shutil
from tkinter import ACTIVE, END, filedialog, messagebox

from frontend.config import DOWNLOAD_DIR, OUTPUT_DIR
from frontend.utils import clear_directory
from tools.logger import get_logger

logger = get_logger()

def list_files(app):
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

def move_file(app):
    selected_file = app.file_listbox.get(ACTIVE).strip()
    if selected_file:
        dest_dir = filedialog.askdirectory()
        if dest_dir:
            try:
                logger.info(f"Moving file {selected_file} to {dest_dir}.")
                shutil.move(os.path.join(OUTPUT_DIR, selected_file), os.path.join(dest_dir, selected_file))
                messagebox.showinfo("Success", f"File {selected_file} moved successfully.")
                list_files(app)
                app.update_directory_sizes()
                logger.info(f"File {selected_file} moved successfully.")
            except Exception as e:
                logger.error(f"Failed to move file {selected_file}: {str(e)}")
                messagebox.showerror("Error", f"Failed to move file: {str(e)}")

def delete_file(app):
    selected_file = app.file_listbox.get(ACTIVE).strip()
    if selected_file:
        try:
            logger.info(f"Deleting file {selected_file}.")
            os.remove(os.path.join(OUTPUT_DIR, selected_file))
            messagebox.showinfo("Success", f"File {selected_file} deleted successfully.")
            list_files(app)
            app.update_directory_sizes()
            logger.info(f"File {selected_file} deleted successfully.")
        except Exception as e:
            logger.error(f"Failed to delete file {selected_file}: {str(e)}")
            messagebox.showerror("Error", f"Failed to delete file: {str(e)}")

def clear_download_directory(app):
    logger.info("Clearing download directory.")
    clear_directory(DOWNLOAD_DIR)
    app.update_directory_sizes()
    logger.info("Download directory cleared.")

def cleanup_partial_downloads(self):
        clear_download_directory(self)
