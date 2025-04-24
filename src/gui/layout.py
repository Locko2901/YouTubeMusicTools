from tkinter import Listbox, messagebox, StringVar
from customtkinter import (
    CTkFrame, CTkLabel, CTkEntry, CTkButton, CTkProgressBar,
    CTkScrollbar, CTkOptionMenu, CTkRadioButton, CTkTabview
)
from services.file_service import (
    delete_file, list_files,
    open_directory, open_file, show_file_in_directory
)
from processing.video_encoder import clear_encoder_detection_cache, find_best_preset, get_dynamic_presets_for_encoder, make_mp4, perform_conversion
from utils.logging import get_logger

logger = get_logger()

# ──────────────────────
# Fonts and Colors
# ──────────────────────
BASE_FONT = ("Arial", 12, "bold")
LABEL_FONT = ("Arial", 12, "bold")
BUTTON_FONT = ("Arial", 12, "bold")
ENTRY_FONT = ("Arial", 12)
BG_COLOR = "#1e1e28"
BORDER_COLOR = "#FF3366"
FG_BUTTON = "#C2185B"
HOVER_BUTTON = "#880E4F"
TEXT_COLOR = "#FF3366"
ENTRY_TEXT_COLOR = "#F5E6F7"
LISTBOX_BG = "#1d1d33"
LISTBOX_FG = "#FFFFFF"
LISTBOX_SELECT_BG = "#880E4F"
LISTBOX_SELECT_FG = "#FFFFFF"

# ──────────────────────
# Main Application Layout
# ──────────────────────
def create_main_layout(app):
    """Master layout stacking all sections."""
    logger.info("Creating main layout")
    main_frame = CTkFrame(app.root, fg_color=BG_COLOR, border_color=BORDER_COLOR, border_width=2)
    main_frame.pack(padx=5, pady=5, fill="both", expand=True)
    create_playlist_section(app, main_frame)
    create_progress_section(app, main_frame)
    create_file_management_section(app, main_frame)
    create_video_encoder_section(app)
    create_size_labels(app, main_frame)

def create_playlist_section(app, parent):
    """Playlist ID entry section."""
    logger.info("Creating playlist section")
    playlist_label = CTkLabel(parent, text="Enter Playlist ID or URL:", text_color=TEXT_COLOR, font=LABEL_FONT)
    playlist_label.pack(pady=(15, 0))
    app.playlist_entry = CTkEntry(
        parent, placeholder_text="Playlist ID/URL", width=400,
        text_color=ENTRY_TEXT_COLOR, font=ENTRY_FONT,
        border_width=2, border_color=BORDER_COLOR
    )
    app.playlist_entry.pack(pady=(5, 15), padx=15)

def create_progress_section(app, parent):
    """Progress buttons and indicators."""
    logger.info("Creating progress section")
    progress_section = CTkFrame(parent, fg_color=BG_COLOR)
    progress_section.pack(pady=10, padx=15, fill="x")
    
    app.download_button = CTkButton(
        progress_section, text="Process Playlist", 
        command=lambda: handle_download_button_click(app),
        fg_color=FG_BUTTON, hover_color=HOVER_BUTTON,
        font=BUTTON_FONT, border_width=2, border_color=BORDER_COLOR
    )
    app.download_button.pack(pady=5, fill='x')

    app.makeMp4_button = CTkButton(
        progress_section, text="Make MP4",
        command=lambda: handle_mp4_button_click(app),
        fg_color=FG_BUTTON, hover_color=HOVER_BUTTON,
        font=BUTTON_FONT, border_width=2, border_color=BORDER_COLOR
    )
    app.makeMp4_button.pack(pady=5, fill='x')

    app.progress_info_frame = CTkFrame(progress_section, fg_color=BG_COLOR)
    app.progress_info_frame.pack_forget()
    app.progress_label = CTkLabel(app.progress_info_frame, text="0%",
                                  text_color=TEXT_COLOR, font=("Arial", 12))
    app.progress_label.pack(pady=(10, 5))
    app.progress_bar = CTkProgressBar(
        app.progress_info_frame, orientation='horizontal', width=400,
        corner_radius=10, progress_color=TEXT_COLOR
    )
    app.progress_bar.pack(pady=(0, 10))

def handle_download_button_click(app):
    """Handle download button click with mutual exclusivity."""
    app.makeMp4_button.configure(
        state="disabled", 
        text="Unavailable During Download"
    )
    app.download_and_process()

def handle_mp4_button_click(app):
    """Handle MP4 button click with mutual exclusivity."""
    app.download_button.configure(
        state="disabled", 
        text="Unavailable During Conversion"
    )
    make_mp4(app)

def update_scrollbar_visibility(app, scrollbar):
    """Auto-show/hide the scrollbar based on visible items."""
    if app.file_listbox.yview() == (0.0, 1.0):
        scrollbar.grid_remove()
    else:
        scrollbar.grid()

def create_file_management_section(app, parent):
    """Section with file list and actions."""
    logger.info("Creating file management section")
    file_management_frame = CTkFrame(parent, fg_color=BG_COLOR, border_color=BORDER_COLOR, border_width=2)
    file_management_frame.pack(padx=10, pady=10, fill="both", expand=True)
    app.file_management_frame = file_management_frame
    app.display_frame = CTkFrame(file_management_frame, fg_color=BG_COLOR)
    app.display_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    file_management_frame.grid_rowconfigure(0, weight=1)
    file_management_frame.grid_columnconfigure(0, weight=1)
    app.file_listbox = Listbox(
        app.display_frame, bg=LISTBOX_BG, font=("Helvetica", 12, "bold"),
        selectbackground=LISTBOX_SELECT_BG, fg=LISTBOX_FG,
        selectforeground=LISTBOX_SELECT_FG, relief="flat", highlightthickness=0
    )
    app.file_listbox.bind("<Double-Button-1>", lambda _event: open_file(app))
    app.file_listbox.pack(fill="both", expand=True, padx=5, pady=5)
    file_scrollbar = CTkScrollbar(
        file_management_frame, orientation="vertical", command=app.file_listbox.yview,
        button_color=FG_BUTTON, button_hover_color=HOVER_BUTTON
    )
    file_scrollbar.grid(row=0, column=1, sticky="ns")
    app.file_listbox.configure(yscrollcommand=file_scrollbar.set)
    app.file_listbox.bind("<Configure>", lambda event: update_scrollbar_visibility(app, file_scrollbar))
    setup_file_buttons(app, parent)

def setup_file_buttons(app, parent):
    """Side buttons for file operations."""
    logger.info("Setting up file management buttons")
    buttons = [
        ("Refresh File List", lambda: list_files(app)),
        ("Show File in Directory", lambda: show_file_in_directory(app)),
        ("Delete Selected File", lambda: delete_file(app)),
        ("Remove FFMPEG Cache", lambda: clear_encoder_detection_cache()),
    ]
    for text, command in buttons:
        CTkButton(
            parent, text=text, command=command,
            fg_color=FG_BUTTON, hover_color=HOVER_BUTTON,
            font=BUTTON_FONT, border_width=2, border_color=BORDER_COLOR
        ).pack(pady=5, padx=15, fill='x')

# ──────────────────────
# Encoder Section
# ──────────────────────
def create_video_encoder_section(app):
    logger.info("Creating video encoder section")
    app.encoder_section = CTkFrame(app.display_frame, fg_color=BG_COLOR)
    app.encoder_section.pack_forget()
    frame = CTkFrame(app.encoder_section, fg_color=BG_COLOR)
    frame.pack(fill="both", expand=True, padx=15, pady=(15, 5))
    hw_encoders = app.encoders.get("hardware", [])
    sw_encoders = app.encoders.get("software", [])
    all_encoders = hw_encoders + sw_encoders
    first_encoder = all_encoders[0] if all_encoders else None

    # ---- VARIABLES MUST BE INITIALIZED *ONCE* HERE ----
    app.encoder_var = StringVar(value=first_encoder)
    app.preset_var = StringVar()

    def on_encoder_change(app, encoder_name):
        presets = get_dynamic_presets_for_encoder(encoder_name)
        best_preset = find_best_preset(presets)
        app.preset_optionmenu.configure(values=presets or ["veryslow"])
        app.preset_var.set(best_preset)
        logger.info(
            f"Preset options for encoder '{encoder_name}' updated. "
            f"Best(default): {best_preset}. Available: {presets}"
        )

    def add_encoders(container, encoder_list):
        for enc in encoder_list:
            label_text = (
                f"h264 ({enc})" if "h264" in enc else
                f"h265 ({enc})" if "hevc" in enc else
                f"av1 ({enc})" if "av1" in enc else
                enc
            )
            CTkRadioButton(
                master=container,
                text=label_text,
                variable=app.encoder_var,
                value=enc,
                font=ENTRY_FONT,
                text_color=ENTRY_TEXT_COLOR,
                fg_color=HOVER_BUTTON,
                hover_color=HOVER_BUTTON,
                command=lambda enc_name=enc: on_encoder_change(app, enc_name)
            ).pack(anchor="w", pady=5, padx=5)

    # --- Draw encoder tabs/buttons ---
    if hw_encoders and sw_encoders:
        tabview = CTkTabview(
            frame,
            fg_color=BG_COLOR,
            border_color=BORDER_COLOR,
            border_width=2,
            segmented_button_fg_color=BG_COLOR,
            segmented_button_selected_color=HOVER_BUTTON,
            segmented_button_selected_hover_color=HOVER_BUTTON,
            segmented_button_unselected_color=BG_COLOR,
            segmented_button_unselected_hover_color=HOVER_BUTTON,
            text_color=ENTRY_TEXT_COLOR
        )
        tabview.pack(fill="both", padx=5, pady=5)
        tabview.add("Hardware Encoders")
        add_encoders(tabview.tab("Hardware Encoders"), hw_encoders)
        tabview.add("Software Encoders")
        add_encoders(tabview.tab("Software Encoders"), sw_encoders)
    else:
        add_encoders(frame, hw_encoders or sw_encoders)

    CTkLabel(
        app.encoder_section,
        text="Preset (Optional — changing may reduce image quality)",
        font=LABEL_FONT,
        text_color=TEXT_COLOR
    ).pack(pady=(15, 5), padx=15, anchor="center")
    preset_frame = CTkFrame(
        app.encoder_section, fg_color=BG_COLOR, corner_radius=8
    )
    preset_frame.pack(pady=10, padx=15, fill="x")
    preset_inner_frame = CTkFrame(preset_frame, fg_color=BG_COLOR)
    preset_inner_frame.pack(pady=8, padx=8, anchor="center", expand=True)
    app.preset_optionmenu = CTkOptionMenu(
        preset_inner_frame,
        values=[],
        variable=app.preset_var,
        font=ENTRY_FONT,
        text_color=ENTRY_TEXT_COLOR,
        fg_color=FG_BUTTON,
        button_color=FG_BUTTON,
        button_hover_color=HOVER_BUTTON,
        dropdown_fg_color=BG_COLOR,
        dropdown_hover_color=HOVER_BUTTON,
        dropdown_text_color=ENTRY_TEXT_COLOR,
    )
    app.preset_optionmenu.pack(pady=5)
    if first_encoder:
        on_encoder_change(app, first_encoder)
        button_frame = CTkFrame(app.encoder_section, fg_color=BG_COLOR)
        button_frame.pack(pady=10, padx=15)
    def on_ok():
        selected = app.encoder_var.get()
        if not selected:
            messagebox.showerror("Invalid Selection", "No encoder selected.")
            return
        app.selected_encoder_info["encoder"] = selected
        app.selected_encoder_info["preset"] = app.preset_var.get()
        logger.info(f"Encoder chosen: {selected}, Preset: {app.preset_var.get()}")
        hide_encoder_section(app)
        show_file_list(app)
        perform_conversion(app)
    def on_cancel():
        logger.info("Encoder selection canceled.")
        app.encoder_var.set("")
        app.preset_var.set("medium")
        app.selected_encoder_info["encoder"] = None
        app.selected_encoder_info["preset"] = None
        app.reset_button()
        hide_encoder_section(app)
        show_file_list(app)
    CTkButton(
        button_frame,
        text="OK", command=on_ok,
        fg_color=FG_BUTTON, hover_color=HOVER_BUTTON,
        font=BUTTON_FONT, border_width=2, border_color=BORDER_COLOR
    ).pack(side="left", padx=5, anchor="center")
    CTkButton(
        button_frame,
        text="Cancel", command=on_cancel,
        fg_color=FG_BUTTON, hover_color=HOVER_BUTTON,
        font=BUTTON_FONT, border_width=2, border_color=BORDER_COLOR
    ).pack(side="left", padx=5, anchor="center")

# ──────────────────────
# Encoder View Swapping
# ──────────────────────
def hide_file_list(app):
    try:
        app.file_listbox.pack_forget()
    except Exception as e:
        logger.debug(f"hide_file_list EXCEPTION: {e}")

def hide_encoder_section(app):
    try:
        app.encoder_section.pack_forget()
    except Exception as e:
        logger.error(f"hide_encoder_section EXCEPTION: {e}")

def show_file_list(app):
    hide_encoder_section(app)
    app.file_listbox.pack(fill="both", expand=True, padx=5, pady=5)
    app.encoder_view_active = False

def show_encoder_section(app):
    hide_file_list(app)
    app.encoder_section.pack(fill="both", expand=True, padx=5, pady=5)
    app.encoder_view_active = True

# ──────────────────────
# Size Labels Section
# ──────────────────────
def create_size_labels(app, parent):
    """Show size info labels."""
    logger.info("Creating size labels")
    app.download_size_label = CTkLabel(parent, text="", text_color=TEXT_COLOR, font=LABEL_FONT)
    app.download_size_label.pack(pady=5, padx=15)
    app.download_size_label.bind("<Button-1>", lambda event: open_directory(app.download_dir))
    app.output_size_label = CTkLabel(parent, text="", text_color=TEXT_COLOR, font=LABEL_FONT)
    app.output_size_label.pack(pady=5, padx=15)
    app.output_size_label.bind("<Button-1>", lambda event: open_directory(app.output_dir))
    app.overall_size_label = CTkLabel(parent, text="", text_color=TEXT_COLOR, font=LABEL_FONT)
    app.overall_size_label.pack(pady=5, padx=15)
    app.overall_size_label.bind("<Button-1>", lambda event: open_directory(app.overall_dir))
