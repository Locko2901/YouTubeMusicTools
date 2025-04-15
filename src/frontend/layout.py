from tkinter import Listbox

from customtkinter import *
from frontend.file_management import clear_download_directory, delete_file, list_files, move_file
from tools.logger import get_logger

logger = get_logger()

BASE_FONT = ("Arial", 12, "bold")
LABEL_FONT = ("Arial", 12, "bold")
BUTTON_FONT = ("Arial", 12, "bold")
ENTRY_FONT = ("Arial", 12)

def create_main_layout(app):
    logger.info("Creating main layout")
    main_frame = CTkFrame(app.root, fg_color="#1e1e28", border_color="#FF3366", border_width=2)
    main_frame.pack(padx=5, pady=5, fill="both", expand=True)
    create_playlist_section(app, main_frame)
    create_progress_section(app, main_frame)
    create_file_management_section(app, main_frame)
    create_size_labels(app, main_frame)

def create_playlist_section(app, parent):
    logger.info("Creating playlist section")
    playlist_label = CTkLabel(parent, text="Enter Playlist ID:", text_color="#FF3366", font=LABEL_FONT)
    playlist_label.pack(pady=(15, 0))
    app.playlist_entry = CTkEntry(
        parent,
        placeholder_text="Playlist ID",
        width=400,
        text_color="#F5E6F7",
        font=ENTRY_FONT,
        border_width=2,
        border_color="#FF3366"
    )
    app.playlist_entry.pack(pady=(5, 15), padx=15)

def create_progress_section(app, parent):
    logger.info("Creating progress section")
    progress_section = CTkFrame(parent, fg_color="#1e1e28")
    progress_section.pack(pady=10, padx=15, fill="x")

    app.progress_info_frame = CTkFrame(progress_section, fg_color="#1e1e28")
    app.progress_info_frame.pack_forget()

    app.progress_label = CTkLabel(app.progress_info_frame, text="0%", text_color="#FF3366", font=("Arial", 12))
    app.progress_label.pack(pady=(10, 5))
    
    app.progress_bar = CTkProgressBar(
        app.progress_info_frame,
        orientation='horizontal',
        width=400,
        corner_radius=10,
        progress_color="#FF3366"
    )
    app.progress_bar.pack(pady=(0, 10))
    
    app.download_button = CTkButton(
        progress_section, 
        text="Process Playlist", 
        command=app.download_and_process, 
        fg_color="#C2185B",
        hover_color="#880E4F",
    )
    app.download_button.pack(pady=10, fill='x')


def update_scrollbar_visibility(app, scrollbar):
    if app.file_listbox.yview() == (0.0, 1.0):
        scrollbar.grid_remove() 
    else:
        scrollbar.grid() 

def create_file_management_section(app, parent):
    logger.info("Creating file management section")
    file_management_frame = CTkFrame(parent, fg_color="#1e1e28", corner_radius=10, border_color="#FF3366", border_width=2)
    file_management_frame.pack(padx=10, pady=10, fill="both", expand=True)
    file_management_frame.grid_rowconfigure(0, weight=1)
    file_management_frame.grid_columnconfigure(0, weight=1)

    app.file_listbox = Listbox(
        file_management_frame,
        bg="#1d1d33", 
        font=("Helvetica", 12, "bold"), 
        selectbackground="#880E4F",
        fg="#FFFFFF",
        selectforeground="#FFFFFF",
        relief="flat",
        highlightthickness=0
    )

    app.file_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    file_scrollbar = CTkScrollbar(
        file_management_frame,
        orientation="vertical",
        command=app.file_listbox.yview,
        button_color="#C2185B",
        button_hover_color="#880E4F",
    )
    file_scrollbar.grid(row=0, column=1, sticky="ns")
    app.file_listbox.configure(yscrollcommand=file_scrollbar.set)

    app.file_listbox.bind("<Configure>", lambda event: update_scrollbar_visibility(app, file_scrollbar))
    
    setup_file_buttons(app, parent)

def setup_file_buttons(app, parent):
    logger.info("Setting up file management buttons")
    refresh_button = CTkButton(
        parent,
        text="Refresh File List",
        command=lambda: list_files(app),
        fg_color="#C2185B",
        hover_color="#880E4F",
        font=BUTTON_FONT,
        border_width=2,
        border_color="#FF3366"
    )
    refresh_button.pack(pady=5, padx=15, fill='x')

    move_button = CTkButton(
        parent,
        text="Move Selected File",
        command=lambda: move_file(app),
        fg_color="#C2185B",
        hover_color="#880E4F",
        font=BUTTON_FONT,
        border_width=2,
        border_color="#FF3366"
    )
    move_button.pack(pady=5, padx=15, fill='x')

    delete_button = CTkButton(
        parent,
        text="Delete Selected File",
        command=lambda: delete_file(app),
        fg_color="#C2185B",
        hover_color="#880E4F",
        font=BUTTON_FONT,
        border_width=2,
        border_color="#FF3366"
    )
    delete_button.pack(pady=5, padx=15, fill='x')

    clear_button = CTkButton(
        parent,
        text="Clear Download Directory",
        command=lambda: clear_download_directory(app),
        fg_color="#C2185B",
        hover_color="#880E4F",
        font=BUTTON_FONT,
        border_width=2,
        border_color="#FF3366"
    )
    clear_button.pack(pady=5, padx=15, fill='x')

def create_size_labels(app, parent):
    logger.info("Creating size labels")
    app.download_size_label = CTkLabel(parent, text="", text_color="#FF3366", font=LABEL_FONT)
    app.download_size_label.pack(pady=5, padx=15)
    app.output_size_label = CTkLabel(parent, text="", text_color="#FF3366", font=LABEL_FONT)
    app.output_size_label.pack(pady=5, padx=15)
    app.overall_size_label = CTkLabel(parent, text="", text_color="#FF3366", font=LABEL_FONT)
    app.overall_size_label.pack(pady=5, padx=15)
