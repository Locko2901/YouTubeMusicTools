from tkinter import Listbox

from customtkinter import *

from frontend.file_management import clear_download_directory, delete_file, list_files, move_file
from tools.logger import get_logger

logger = get_logger()

def create_main_layout(app):
    logger.info("Creating main layout")
    main_frame = CTkFrame(app.root, fg_color="#1e1e28")
    main_frame.pack(padx=1, pady=1, fill="both", expand=True)
    create_playlist_section(app, main_frame)
    create_progress_section(app, main_frame)
    create_file_management_section(app, main_frame)
    create_size_labels(app, main_frame)

def create_playlist_section(app, parent):
    logger.info("Creating playlist section")
    playlist_label = CTkLabel(parent, text="Enter Playlist ID:", text_color="#FF3366", font=("Arial", 12))
    playlist_label.pack(pady=(10, 0))
    app.playlist_entry = CTkEntry(parent, placeholder_text="Playlist ID", width=400, text_color="#F5E6F7")
    app.playlist_entry.pack(pady=(0, 10), padx=15)

def create_progress_section(app, parent):
    logger.info("Creating progress section")
    app.progress_label = CTkLabel(parent, text="Progress:", text_color="#FF3366", font=("Arial", 12))
    app.progress_label.pack(pady=(10, 5))
    app.progress_bar = CTkProgressBar(
        parent,
        orientation='horizontal',
        width=400,
        corner_radius=10
    )
    app.progress_bar.pack(pady=(0, 10))
    download_button = CTkButton(
        parent, 
        text="Process Playlist", 
        command=app.download_and_process, 
        fg_color="#C2185B",
        hover_color="#880E4F",
    )
    download_button.pack(pady=10, padx=15, fill='x')

def create_file_management_section(app, parent):
    logger.info("Creating file management section")
    file_management_frame = CTkFrame(parent, fg_color="#1e1e28", corner_radius=10)
    file_management_frame.pack(padx=10, pady=10, fill="both", expand=True)
    file_management_frame.grid_rowconfigure(0, weight=1)
    file_management_frame.grid_columnconfigure(0, weight=1)

    app.file_listbox = Listbox(
        file_management_frame,
        bg="#1d1d33", 
        font=("Helvetica", 12), 
        selectbackground="#880E4F",
        fg="#FFFFFF",
        selectforeground="#FFFFFF"
    )

    app.file_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    file_scrollbar = CTkScrollbar(
        file_management_frame,
        orientation="vertical",
        command=app.file_listbox.yview,
        button_color="#C2185B",
        button_hover_color="#880E4F"
    )
    file_scrollbar.grid(row=0, column=1, sticky="ns")
    app.file_listbox.configure(yscrollcommand=file_scrollbar.set)

    setup_file_buttons(app, parent)

def setup_file_buttons(app, parent):
    logger.info("Setting up file management buttons")
    refresh_button = CTkButton(
        parent,
        text="Refresh File List",
        command=lambda: list_files(app),
        fg_color="#C2185B",
        hover_color="#880E4F",
    )
    refresh_button.pack(pady=5, padx=15, fill='x')

    move_button = CTkButton(
        parent,
        text="Move Selected File",
        command=lambda: move_file(app),
        fg_color="#C2185B",
        hover_color="#880E4F",
    )
    move_button.pack(pady=5, padx=15, fill='x')

    delete_button = CTkButton(
        parent,
        text="Delete Selected File",
        command=lambda: delete_file(app),
        fg_color="#C2185B",
        hover_color="#880E4F",
    )
    delete_button.pack(pady=5, padx=15, fill='x')

    clear_button = CTkButton(
        parent,
        text="Clear Download Directory",
        command=lambda: clear_download_directory(app),
        fg_color="#C2185B",
        hover_color="#880E4F",
    )
    clear_button.pack(pady=5, padx=15, fill='x')

def create_size_labels(app, parent):
    logger.info("Creating size labels")
    app.download_size_label = CTkLabel(parent, text="", text_color="#FF3366")
    app.download_size_label.pack(pady=5, padx=15)
    app.output_size_label = CTkLabel(parent, text="", text_color="#FF3366")
    app.output_size_label.pack(pady=5, padx=15)
    app.overall_size_label = CTkLabel(parent, text="", text_color="#FF3366")
    app.overall_size_label.pack(pady=5, padx=15)