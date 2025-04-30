import threading
from tkinter import messagebox
from download.audio_downloader import download_videos, merge_files
from processing.file_utils import write_to_file
from services.youtube import get_playlist_items, get_playlist_name
from services.file_service import cleanup_partial_downloads, list_files

def download_and_process_pipeline(app, logger):
    """
    Orchestrates the playlist download, merge, and process.
    app: instance of YouTubeDownloaderGUI (provides access to UI & state)
    """
    if app.canceling:
        app.cancel_download()
        return

    app.canceling = False
    app.cancel_event.clear()
    app.download_button.configure(text="Cancel Process", command=app.cancel_download)

    playlist_id = app.playlist_entry.get().strip()
    if not playlist_id:
        logger.error("Error: Playlist ID or URL cannot be empty.")
        messagebox.showerror("Error", "Playlist ID or URL cannot be empty.")
        app.reset_button()
        return

    logger.info(f"Retrieving playlist name using: '{playlist_id}'")
    playlist_name = get_playlist_name(playlist_id)
    if not playlist_name:
        logger.error("Error: Failed to retrieve playlist name.")
        messagebox.showerror("Error", "Failed to retrieve playlist name.")
        app.reset_button()
        return

    logger.info(f"Playlist '{playlist_name}' found. Retrieving playlist items...")
    videos = get_playlist_items(playlist_id)
    if videos is None:
        logger.error("Error: Failed to retrieve playlist items.")
        messagebox.showerror("Error", "Failed to retrieve playlist items.")
        app.reset_button()
        return

    logger.info(f"Retrieved {len(videos)} videos from playlist '{playlist_name}'.")
    write_to_file(videos, playlist_name)

    if not messagebox.askyesno("Confirmation", "Do you want to download the songs?"):
        messagebox.showinfo("Cancelled", "Download canceled.")
        list_files(app)
        app.update_directory_sizes()
        app.reset_mp4_button()
        app.reset_button()
        app.reset_progress()
        return

    app.progress_info_frame.pack(pady=10)
    app.download_button.configure(text="Cancel Process", command=app.cancel_download)

    def background_task():
        try:
            total_videos = len(videos)
            app.progress_bar.set(0)
            downloaded_files = []
            for i, video in enumerate(videos, start=1):
                if app.cancel_event.is_set():
                    logger.info("Download canceled by user.")
                    cleanup_partial_downloads(app)
                    messagebox.showinfo("Cancelled", "Download has been canceled.")
                    app.reset_button()
                    app.reset_progress()
                    return
                video_files = download_videos([video])
                downloaded_files.extend(video_files)
                app.update_directory_sizes()
                app.update_progress(i, total_videos)
            merge_files(playlist_name, downloaded_files)
            list_files(app)
            app.update_directory_sizes()
            app.reset_progress()
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            app.reset_button()

    threading.Thread(target=background_task).start()
