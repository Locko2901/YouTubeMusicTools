import os
import sys
import inspect

ROOT_DIR = ""
DOWNLOAD_DIR = ""
OUTPUT_DIR = ""
LOG_DIR = ""
APPDATA_DIR = ""
IS_COMPILED = False
IS_INSTALLED = False
LATEST_LOG_FILE = ""
DEFAULT_BG_IMAGE = ""

PATHS_INIT_LOGS = []

def initialize_paths():
    global ROOT_DIR, APPDATA_DIR, DOWNLOAD_DIR, OUTPUT_DIR, LOG_DIR, \
        DEFAULT_BG_IMAGE, IS_COMPILED, IS_INSTALLED, LATEST_LOG_FILE, PATHS_INIT_LOGS

    # Check if running in compiled or development mode
    is_compiled = '__compiled__' in globals() # Nuitka specific check
    IS_COMPILED = is_compiled
    PATHS_INIT_LOGS.append(f"Running in {'compiled' if is_compiled else 'development'} mode")

    if is_compiled:
        ROOT_DIR = os.path.dirname(sys.executable)
        PATHS_INIT_LOGS.append(f"Using executable directory for ROOT_DIR: {ROOT_DIR}")
    else:
        main_module = sys.modules['__main__']
        main_module_file = inspect.getfile(main_module)
        ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(main_module_file)))
        PATHS_INIT_LOGS.append(f"Using main module parent directory for ROOT_DIR: {ROOT_DIR}")

    is_portable = True
    
    # Check for a marker file
    installed_marker_file = os.path.join(ROOT_DIR, '.installed')
    if os.path.exists(installed_marker_file):
        is_portable = False
        PATHS_INIT_LOGS.append("Installation marker file found, using installed mode")
    else:
        PATHS_INIT_LOGS.append("No installation marker found, using portable/dev mode")
    
    IS_INSTALLED = not is_portable

    # Set app_data_dir based on installation status
    if is_compiled and not is_portable:
        # Only use AppData if marker file exists
        if sys.platform == 'win32':
            app_data_dir = os.path.join(
                os.environ.get('LOCALAPPDATA', os.path.expanduser('~')),
                'YouTubeMusicTools'
            )
            PATHS_INIT_LOGS.append(f"Installed mode: Using LOCALAPPDATA: {app_data_dir}")
        elif sys.platform == 'darwin':
            app_data_dir = os.path.join(
                os.path.expanduser('~'),
                'Library',
                'Application Support',
                'YouTubeMusicTools'
            )
            PATHS_INIT_LOGS.append(f"Installed mode: Using Application Support: {app_data_dir}")
        else:
            app_data_dir = os.path.join(os.path.expanduser('~'), '.YouTubeMusicTools')
            PATHS_INIT_LOGS.append(f"Installed mode: Using home directory: {app_data_dir}")
    else:
        # For development mode or portable mode, use local directories
        app_data_dir = ROOT_DIR
        PATHS_INIT_LOGS.append(f"Development/Portable mode: using ROOT_DIR as app_data_dir: {app_data_dir}")

    # Define directories relative to the appropriate base
    DOWNLOAD_DIR = os.path.join(app_data_dir, 'data', 'downloads')
    OUTPUT_DIR = os.path.join(app_data_dir, 'data', 'output')
    LOG_DIR = os.path.join(app_data_dir, 'logs')
    APPDATA_DIR = app_data_dir
    LATEST_LOG_FILE = os.path.join(LOG_DIR, 'latest.log')
    
    PATHS_INIT_LOGS.append(f"DOWNLOAD_DIR: {DOWNLOAD_DIR}")
    PATHS_INIT_LOGS.append(f"OUTPUT_DIR: {OUTPUT_DIR}")
    PATHS_INIT_LOGS.append(f"LOG_DIR: {LOG_DIR}")
    PATHS_INIT_LOGS.append(f"LATEST_LOG_FILE: {LATEST_LOG_FILE}")

    DEFAULT_BG_IMAGE = os.path.join(ROOT_DIR, 'assets', 'images', 'default.png')
    PATHS_INIT_LOGS.append(f"DEFAULT_BG_IMAGE: {DEFAULT_BG_IMAGE}")
    PATHS_INIT_LOGS.append(f"DEFAULT_BG_IMAGE exists: {os.path.exists(DEFAULT_BG_IMAGE)}")

    # Create directories if they don't exist
    for directory in [APPDATA_DIR, DOWNLOAD_DIR, OUTPUT_DIR, LOG_DIR]:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                PATHS_INIT_LOGS.append(f"Created directory: {directory}")
            except Exception as e:
                PATHS_INIT_LOGS.append(f"Error creating directory {directory}: {str(e)}")
        else:
            PATHS_INIT_LOGS.append(f"Directory already exists: {directory}")
