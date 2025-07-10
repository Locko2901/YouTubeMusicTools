import hashlib
import json
import os
import queue
import re
import subprocess
import threading
import time
from tkinter import ACTIVE, filedialog, messagebox

from mutagen.mp3 import MP3
from PIL import Image

import config.settings as cs
from services.file_service import list_files
from utils.logging import get_logger

logger = get_logger()

# =================== Constants ===================
MAIN_PRESETS = [
    "ultrafast", "superfast", "veryfast", "faster", "fast",
    "medium", "slow", "slower", "veryslow"
]
_ENCODER_PRESET_CACHE = {}

# =================== Patch Subprocesses for Windows ===================
if os.name == 'nt':
    _orig_popen = subprocess.Popen
    class NoConsolePopen(subprocess.Popen):
        def __init__(self, *args, **kwargs):
            kwargs['creationflags'] = kwargs.get('creationflags', 0) | subprocess.CREATE_NO_WINDOW
            _orig_popen.__init__(self, *args, **kwargs)
    subprocess.Popen = NoConsolePopen

# =================== FFmpeg Encoder Cache ===================
_ENCODER_DETECTION_CACHE = None
_ENCODER_DETECTION_LOCK = threading.Lock()
def get_encoder_cache_path():
    return os.path.join(cs.APPDATA_DIR, "ffmpeg_encoder_cache.json")

def _get_ffmpeg_version():
    try:
        result = subprocess.run(['ffmpeg', '-version'],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True,
                               check=True)
        lines = result.stdout.splitlines()
        if lines:
            return lines[0].strip()
    except Exception:
        return ""
    return ""

def _get_cache_key():
    version = _get_ffmpeg_version()
    os_id = os.name
    nvidia_drv = ""
    try:
        nv = subprocess.run(
            ['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2
        )
        if nv.returncode == 0:
            nvidia_drv = nv.stdout.strip()
    except Exception:
        pass
    key_str = version + "|" + os_id + "|" + nvidia_drv
    return hashlib.md5(key_str.encode("utf-8")).hexdigest()

def _read_cache_file():
    _ENCODER_CACHE_PATH = get_encoder_cache_path()
    if not os.path.exists(_ENCODER_CACHE_PATH):
        return None, None, None
    try:
        with open(_ENCODER_CACHE_PATH, "r", encoding="utf8") as f:
            data = json.load(f)
            return data.get("cache_key"), data.get("encoders"), data.get("presets", {})
    except Exception as e:
        logger.warning(f"Could not read encoder cache: {e}")
        return None, None, None

def _write_cache_file(encoders, cache_key, presets=None):
    _ENCODER_CACHE_PATH = get_encoder_cache_path()
    try:
        with open(_ENCODER_CACHE_PATH, "w", encoding="utf8") as f:
            json.dump({
                "cache_key": cache_key,
                "encoders": encoders,
                "presets": presets if presets is not None else {}
            }, f)
    except Exception as e:
        logger.warning(f"Could not write encoder cache to {_ENCODER_CACHE_PATH}: {e}")

def clear_encoder_detection_cache():
    """Call this to force re-detect encoders on next run."""
    _ENCODER_CACHE_PATH = get_encoder_cache_path()
    global _ENCODER_DETECTION_CACHE
    with _ENCODER_DETECTION_LOCK:
        _ENCODER_DETECTION_CACHE = None
        try:
            if os.path.exists(_ENCODER_CACHE_PATH):
                os.remove(_ENCODER_CACHE_PATH)
                logger.info("Encoder detection cache cleared")
        except Exception as e:
            logger.warning(f"Could not remove encoder cache file: {e}")

# =================== FFmpeg Encoder Detection ===================

def get_available_encoders(force_refresh=False):
    """
    Detect available hardware and software FFmpeg encoders;
    Use disk+memory cache for performance. Pass force_refresh=True to skip cache.
    Returns:
        dict: {'hardware': [enc..], 'software': [enc..]}
    """
    global _ENCODER_DETECTION_CACHE, _ENCODER_PRESET_CACHE

    cache_key = _get_cache_key()
    with _ENCODER_DETECTION_LOCK:
        if not force_refresh:
            # Memory cache priority
            if _ENCODER_DETECTION_CACHE is not None:
                return _ENCODER_DETECTION_CACHE
            # Disk cache
            file_key, cached, cached_presets = _read_cache_file()
            if file_key == cache_key and cached:
                # TODO: Compiled cache path is wrong
                logger.info("Loaded FFmpeg encoder list from disk.")
                _ENCODER_DETECTION_CACHE = cached
                _ENCODER_PRESET_CACHE = cached_presets if cached_presets else {}
                return cached

        # If got here, detect from scratch
        logger.info("Starting encoder detection process (not cached)")
        ffmpeg_encoders = _get_ffmpeg_encoders()
        hardware = []
        software = []
        hardware.extend(_detect_nvidia_encoders(ffmpeg_encoders))
        hardware.extend(_detect_intel_encoders(ffmpeg_encoders))
        hardware.extend(_detect_amd_encoders(ffmpeg_encoders))
        hardware.extend(_detect_vaapi_encoders(ffmpeg_encoders))
        logger.info("Checking for software encoders")
        for enc in ('libx264', 'libx265', 'libaom-av1', 'librav1e', 'libsvtav1'):
            if enc in ffmpeg_encoders:
                software.append(enc)
        if os.name == 'nt':
            for enc in ('h264_mf', 'hevc_mf', 'av1_mf'):
                if enc in ffmpeg_encoders:
                    software.append(enc)
        if not hardware and not software:
            logger.warning("No encoders detected; falling back on libx264/libx265")
            software = ['libx264', 'libx265']
        result = {'hardware': hardware, 'software': software}
        logger.info(f"Detection complete. Hardware: {hardware}, Software: {software}")
        # write to disk with presets
        _ENCODER_DETECTION_CACHE = result
        _write_cache_file(result, cache_key, _ENCODER_PRESET_CACHE)
        logger.info("Wrote encoder list to disk cache")
        return result

# =================== FFmpeg Encoder Detection Helpers ===================

def _get_ffmpeg_encoders():
    """Run ffmpeg -encoders and return stdout, or empty str on failure."""
    try:
        result = subprocess.run(
            ['ffmpeg', '-hide_banner', '-encoders'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, check=True
        )
        logger.debug(f"FFmpeg encoders list fetched, {len(result.stdout)} bytes")
        return result.stdout
    except FileNotFoundError:
        logger.error("FFmpeg not found. Please install FFmpeg.")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg returned error code {e.returncode}: {e.stderr.strip()}")
    except Exception as e:
        logger.error(f"Unexpected error running ffmpeg: {e}")
    return ""

def _detect_nvidia_encoders(ffmpeg_encoders):
    """Detect NVIDIA hardware encoders."""
    hardware = []
    try:
        nv = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,driver_version', '--format=csv,noheader'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2
        )
        if nv.returncode == 0:
            name, drv = [s.strip() for s in nv.stdout.split(',', 1)]
            logger.info(f"NVIDIA GPU detected: {name} (driver {drv})")
            for enc in ('h264_nvenc', 'hevc_nvenc'):
                if enc in ffmpeg_encoders:
                    hardware.append(enc)
            try:
                major = int(drv.split('.')[0])
                if major >= 525 and 'av1_nvenc' in ffmpeg_encoders:
                    hardware.append('av1_nvenc')
            except ValueError:
                logger.warning(f"Could not parse NVIDIA driver version: {drv}")
        else:
            logger.info("nvidia-smi ran but no GPUs reported")
    except FileNotFoundError:
        logger.info("nvidia-smi not found; skipping NVIDIA detection")
    except Exception as e:
        logger.warning(f"NVIDIA detection error: {e}")
    return hardware

def _detect_intel_encoders(ffmpeg_encoders):
    """Detect Intel Quick Sync Video encoders."""
    hardware = []
    intel_found = False
    if os.name == 'nt':
        try:
            wmi = subprocess.run(
                ['wmic', 'path', 'win32_VideoController', 'get', 'name'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            intel_found = 'Intel' in wmi.stdout
        except Exception as e:
            logger.warning(f"Intel-Windows detection error: {e}")
    else:
        try:
            pci = subprocess.run(['lspci'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            intel_found = 'Intel' in pci.stdout
        except FileNotFoundError:
            logger.info("lspci not found; skipping Intel detection")
        except Exception as e:
            logger.warning(f"Intel-Linux detection error: {e}")
    if intel_found:
        for enc in ('h264_qsv', 'hevc_qsv', 'av1_qsv'):
            if enc in ffmpeg_encoders:
                hardware.append(enc)
    return hardware

def _detect_amd_encoders(ffmpeg_encoders):
    """Detect AMD AMF hardware encoders."""
    hardware = []
    amd_found = False
    av1_capable = False
    if os.name == 'nt':
        try:
            wmi = subprocess.run(
                ['wmic', 'path', 'win32_VideoController', 'get', 'name'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            amd_found = any(x in wmi.stdout for x in ('AMD', 'Radeon', 'ATI'))
            av1_capable = any(x in wmi.stdout for x in ('RX 7', 'RDNA 3'))
        except Exception as e:
            logger.warning(f"AMD-Windows detection error: {e}")
    else:
        try:
            pci = subprocess.run(['lspci'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            amd_found = any(x in pci.stdout for x in ('AMD', 'Radeon', 'ATI'))
            av1_capable = any(x in pci.stdout for x in ('RX 7', 'RDNA 3'))
        except FileNotFoundError:
            logger.info("lspci not found; skipping AMD detection")
        except Exception as e:
            logger.warning(f"AMD-Linux detection error: {e}")
    if amd_found:
        for enc in ('h264_amf', 'hevc_amf'):
            if enc in ffmpeg_encoders:
                hardware.append(enc)
        if av1_capable and 'av1_amf' in ffmpeg_encoders:
            hardware.append('av1_amf')
    return hardware

def _detect_vaapi_encoders(ffmpeg_encoders):
    """Detect VAAPI encoders (primarily Linux)."""
    hardware = []
    if os.name != 'nt':
        try:
            if os.path.isdir('/dev/dri'):
                devs = [d for d in os.listdir('/dev/dri') if d.startswith('render')]
                if devs:
                    for enc in ('h264_vaapi', 'hevc_vaapi', 'av1_vaapi'):
                        if enc in ffmpeg_encoders:
                            hardware.append(enc)
        except Exception as e:
            logger.warning(f"VAAPI detection error: {e}")
    return hardware

def get_ffmpeg_encoder_help(encoder_name):
    try:
        result = subprocess.run(
            ['ffmpeg', '-hide_banner', '-h', f'encoder={encoder_name}'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        helptext = result.stdout + "\n" + result.stderr
        return helptext
    except Exception as e:
        logger.error(f"Error running ffmpeg for encoder {encoder_name}: {e}")
        return ""

# =================== Preset Helpers ===================

def extract_presets_from_help(helptext):
    """
    Parse ffmpeg's encoder help for -preset lines, return detected preset names.
    """
    preset_block = None
    for line_num, line in enumerate(helptext.splitlines()):
        if '-preset' in line and 'Set the encoding preset' in line:
            block = [line]
            for l in helptext.splitlines()[line_num+1:]:
                if not l.strip():
                    break
                block.append(l)
            preset_block = "\n".join(block)
            break
    if not preset_block:
        return []
    presets = []
    for l in preset_block.splitlines():
        m = re.match(r'^\s+([a-zA-Z0-9_]+)\s+\d+\s+E\.\.V', l)
        if m:
            name = m.group(1)
            if name in MAIN_PRESETS and name not in presets:
                presets.append(name)
    return presets

def find_best_preset(presets, main_presets=MAIN_PRESETS):
    """
    Pick the best (slowest/highest-quality) available preset.
    """
    available = set(p.lower() for p in presets)
    for preset in reversed(main_presets):
        if preset in available:
            return preset
    return presets[-1] if presets else "veryslow"

def get_dynamic_presets_for_encoder(encoder_name):
    encoder_name = (encoder_name or "").lower()
    if encoder_name in _ENCODER_PRESET_CACHE:
        logger.debug(f"Using cached presets for encoder {encoder_name}")
        return _ENCODER_PRESET_CACHE[encoder_name]

    helptext = get_ffmpeg_encoder_help(encoder_name)
    presets = extract_presets_from_help(helptext)
    if not presets:
        presets = MAIN_PRESETS[:]
    _ENCODER_PRESET_CACHE[encoder_name] = presets

    # Save to disk, updating global presets cache, if needed
    cache_key = _get_cache_key()
    with _ENCODER_DETECTION_LOCK:
        _, encoders_cached, _ = _read_cache_file()
        _write_cache_file(
            encoders_cached if encoders_cached is not None else (_ENCODER_DETECTION_CACHE or {}),
            cache_key,
            _ENCODER_PRESET_CACHE
        )
    return presets

# =================== GIF Utils ===================

def get_gif_info(gif_path):
    """
    Return (n_frames, total_msec, fps) for a GIF.
    """
    with Image.open(gif_path) as im:
        n_frames = im.n_frames
        durations = [im.info.get('duration', 40)]
        try:
            while True:
                im.seek(im.tell() + 1)
                durations.append(im.info.get('duration', 40))
        except EOFError:
            pass
        total_duration_ms = sum(durations)
        avg_duration = total_duration_ms / n_frames if n_frames else 40
        fps = 1000 / avg_duration if avg_duration else 25
    return n_frames, total_duration_ms / 1000.0, fps

# =================== File Selection / GUI ===================
def make_mp4(app):
    """
    Validates mp3 selection, lets user pick background image, updates encoder choices,
    and swaps to the encoder section if all inputs are valid.
    Returns True on success, False otherwise.
    Handles all view switching and debugging.
    """
    from gui.layout import hide_file_list, show_encoder_section, show_file_list
    # MP3 file selection checks
    if app.file_listbox.curselection() == ():
        messagebox.showwarning("No File Selected", "Please select a file.")
        logger.warning("No file selected.")
        app.reset_button()
        show_file_list(app)
        return False
    selected_file = app.file_listbox.get(ACTIVE).strip()
    if not selected_file.lower().endswith('.mp3'):
        messagebox.showwarning("Invalid File", "Please select an MP3 file.")
        logger.warning(f"Invalid file selected: {selected_file}")
        app.reset_button()
        show_file_list(app)
        return False
    mp3_path = os.path.join(cs.OUTPUT_DIR, selected_file)
    if os.path.exists(os.path.splitext(mp3_path)[0] + '.mp4'):
        logger.warning(f"File already has a .mp4 counterpart: {mp3_path}")
        messagebox.showwarning("File Already Converted", "Selected file already has a .mp4 counterpart.")
        app.reset_button()
        show_file_list(app)
        return False
    # Background image selection
    use_default_bg = messagebox.askyesno(
        "Background Image",
        "Do you want to use the default background image?"
    )
    if use_default_bg:
        background_image = cs.DEFAULT_BG_IMAGE
        if not os.path.exists(background_image):
            messagebox.showerror("Missing Default Image", "Default background image not found.")
            logger.error("Default background image missing.")
            app.reset_button()
            show_file_list(app)
            return False
    else:
        background_image = filedialog.askopenfilename(
            title="Select Background Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        if not background_image:
            messagebox.showwarning("No Image Selected", "Please select a background image.")
            logger.warning("No background image selected.")
            app.reset_button()
            show_file_list(app)
            return False
    # GIF support
    is_gif = background_image.lower().endswith('.gif')
    if is_gif:
        try:
            _, gif_dur, gif_fps = get_gif_info(background_image)
            app.is_gif = True
            app.gif_fps = gif_fps
            app.gif_length = gif_dur
        except Exception as e:
            messagebox.showerror("GIF Error", f"Cannot read GIF framerate: {e}")
            logger.warning(f"GIF parse error: {e}")
            show_file_list(app)
            return False
    else:
        app.is_gif = False
        app.gif_fps = None
        app.gif_length = None
    app.selected_mp3_path = mp3_path
    app.selected_bg_image = background_image
    app.encoders = get_available_encoders()
    hide_file_list(app)
    show_encoder_section(app)
    return True

# =================== Main Conversion ===================

def perform_conversion(app):
    """
    Start video conversion in a thread, monitor progress, and update the GUI.
    """
    mp3_path = getattr(app, 'selected_mp3_path', None)
    background_image = getattr(app, 'selected_bg_image', None)
    is_gif = getattr(app, 'is_gif', False)
    gif_fps = getattr(app, 'gif_fps', None)
    gif_length = getattr(app, 'gif_length', None)
    if not mp3_path or not background_image:
        messagebox.showerror("Missing File", "No MP3 or background image found.")
        logger.error("Missing MP3 or background image.")
        return
    video_encoder = app.selected_encoder_info["encoder"]
    preset = app.selected_encoder_info["preset"]
    if not video_encoder:
        logger.warning("No video encoder selected.")
        return
    output_filename = os.path.splitext(os.path.basename(mp3_path))[0] + '.mp4'
    output_path = os.path.join(cs.OUTPUT_DIR, output_filename)
    app.progress_info_frame.pack(pady=10)
    app.progress_bar.set(0)
    app.progress_label.configure(text="0%")
    app.root.update_idletasks()
    logger.info("Progress frame should now be visible")
    app.makeMp4_cancel_event.clear()
    app.makeMp4_button.configure(
        text="Cancel Conversion",
        command=app.cancel_make_mp4,
        state="normal"
    )

    def conversion_task():
        was_cancelled = False
        ffmpeg_output_lines = []
        height_exceed_error = None
        width_exceed_error = None
        general_encoder_error = None
        try:
            logger.info(f"Converting {mp3_path} to {output_path} using {video_encoder}, preset {preset}")
            total_duration = MP3(mp3_path).info.length
            logger.info(f"Total duration: {total_duration} seconds")
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            # ========== GIF SUPPORT ==========
            if is_gif:
                # loop the gif enough times to cover the audio
                loop_count = int(total_duration // gif_length) + 1 if gif_length else 1

                command = [
                    'ffmpeg', '-y',
                    '-ignore_loop', '0',
                    '-stream_loop', str(loop_count),
                    '-i', background_image,
                    '-i', mp3_path,
                    '-c:a', 'copy',
                    '-shortest',

                    # scale to 1080p (preserve aspect ratio + pad), ensure yuv420p
                    '-vf', (
                        'scale=1920:1080:force_original_aspect_ratio=decrease,'
                        'pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,'
                        'format=yuv420p'
                    ),

                    # preserve the GIF's original per-frame timing
                    '-vsync', '0',
                    '-fflags', '+genpts',
                ]

            else:
                command = [
                    'ffmpeg', '-y',
                    '-loop', '1', '-framerate', '1',
                    '-i', background_image,
                    '-i', mp3_path,
                    '-c:a', 'copy',
                    '-shortest',

                    # scale to 1080p (preserve aspect ratio + pad), ensure yuv420p
                    '-vf', (
                        'scale=1920:1080:force_original_aspect_ratio=decrease,'
                        'pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,'
                        'format=yuv420p'
                    ),
                ]
            # Add video encoder and preset
            if any(hw in video_encoder for hw in ['nvenc', 'qsv', 'amf']):
                command += ['-c:v', video_encoder, '-preset', preset, '-b:v', '1M']
            else:
                command += ['-c:v', video_encoder, '-preset', preset, '-crf', '28']
            command += ['-progress', 'pipe:1', output_path]
            logger.info(f"Running command: {' '.join(command)}")
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True,
                creationflags=creationflags
            )
            progress_queue = queue.Queue()
            # Main reading loop: read lines synchronously, react immediately
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                ffmpeg_output_lines.append(line.strip())
                # Error detection for Height, Width and encoder problems
                m_height = re.search(r'Height (\d+) exceeds (\d+)', line)
                m_width = re.search(r'Width (\d+) exceeds (\d+)', line)
                if m_height and not height_exceed_error:
                    height_exceed_error = (
                        f"Error: Image/video height ({m_height.group(1)}px) exceeds maximum allowed "
                        f"({m_height.group(2)}px) for encoder or container.\n"
                        "Please change image/video size or try a different encoder."
                    )
                if m_width and not width_exceed_error:
                    width_exceed_error = (
                        f"Error: Image/video width ({m_width.group(1)}px) exceeds maximum allowed "
                        f"({m_width.group(2)}px) for encoder or container.\n"
                        "Please change image/video size or try a different encoder."
                    )
                if (
                    ('Error while opening encoder' in line or 'No capable devices found' in line
                    or 'Invalid argument' in line)
                    and not general_encoder_error
                ):
                    general_encoder_error = (
                        "Could not open hardware encoder. Causes include a resolution too large for your GPU/"
                        "hardware, unsupported codec/settings or an outdated driver version.\n"
                        "Try changing image/video size, updating your drivers or use a software encoder (like libx264)."
                    )
                # Check for progress
                if line.startswith("out_time_ms="):
                    val = line.strip().split("=", 1)[1]
                    if val.isdigit():
                        time_ms = int(val)
                        current_time = time_ms / 1_000_000
                        progress = min(current_time / total_duration, 1.0)
                        progress_queue.put(progress)
                        logger.info(f"Progress: {progress:.2%}")
                # -- handle cancel immediately --
                if app.makeMp4_cancel_event.is_set():
                    process.terminate()
                    process.wait()
                    was_cancelled = True
                    logger.info("Conversion canceled by user.")
                    try:
                        if os.path.exists(output_path):
                            os.remove(output_path)
                            logger.info(f"Deleted partial output file: {output_path}")
                    except Exception as del_err:
                        logger.warning(f"Failed to delete partial MP4: {del_err}")
                    app.root.after(0, lambda: list_files(app))
                    app.root.after(0, lambda: app.update_directory_sizes())
                    app.root.after(0, lambda: messagebox.showinfo("Cancelled", "Conversion has been canceled."))
                    app.root.after(0, app.reset_mp4_button)
                    app.root.after(0, app.reset_progress)
                    return
                # -- UI update --
                while not progress_queue.empty():
                    p = progress_queue.get_nowait()
                    percentage = p * 100
                    def update_ui(progress_value, percent):
                        app.progress_bar.set(progress_value)
                        app.progress_label.configure(text=f"{percent:.2f}%")
                        app.root.update_idletasks()
                    app.root.after(0, update_ui, p, percentage)
                time.sleep(0.02)
            retcode = process.wait()
            logger.info(f"Process finished with return code: {retcode}")
            if retcode != 0 and not was_cancelled:
                # DELETE partial output after *any* error
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                        logger.info(f"Deleted partial output file: {output_path}")
                    except Exception as del_err:
                        logger.warning(f"Failed to delete partial MP4: {del_err}")
                app.root.after(0, lambda: list_files(app))
                app.root.after(0, lambda: app.update_directory_sizes())
                # Prioritized error messages
                if width_exceed_error:
                    logger.error(width_exceed_error + "\nTraceback:\n" + "\n".join(ffmpeg_output_lines))
                    app.root.after(0, lambda: messagebox.showerror("Image/video too large!", width_exceed_error))
                elif height_exceed_error:
                    logger.error(height_exceed_error + "\nTraceback:\n" + "\n".join(ffmpeg_output_lines))
                    app.root.after(0, lambda: messagebox.showerror("Image/video too large!", height_exceed_error))
                elif general_encoder_error:
                    logger.error(general_encoder_error + "\nTraceback:\n" + "\n".join(ffmpeg_output_lines))
                    app.root.after(0, lambda: messagebox.showerror("Encoder problem", general_encoder_error))
                else:
                    error_msg = "FFmpeg failed. Check the log for more details."
                    logger.error("FFmpeg failed. Log:\n" + "\n".join(ffmpeg_output_lines))
                    app.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            elif retcode == 0 and not was_cancelled:
                logger.info(f"Conversion complete: {output_path}")
                app.root.after(0, lambda: list_files(app))
                app.root.after(0, lambda: app.update_directory_sizes())
            else:
                logger.info("FFmpeg was cancelled, no error shown.")
        except Exception as e:
            error_message = str(e)
            logger.error(f"Conversion failed: {error_message}")
            app.root.after(0, lambda: list_files(app))
            app.root.after(0, lambda: app.update_directory_sizes())
            app.root.after(0, lambda msg=error_message: messagebox.showerror("Error", msg))
        finally:
            app.root.after(0, app.reset_mp4_button)
            app.root.after(0, app.reset_progress)

    threading.Thread(target=conversion_task, daemon=True).start()
