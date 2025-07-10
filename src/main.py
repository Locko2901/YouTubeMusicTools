import config.settings as cs

from gui.app import YouTubeDownloaderGUI
from utils.logging import LoggerSetup
from config.settings import initialize_paths

def initialize_logging():
    LATEST_LOG_FILE = cs.LATEST_LOG_FILE
    LOG_DIR = cs.LOG_DIR
    LoggerSetup.initialize_logger(LATEST_LOG_FILE, LOG_DIR)

if __name__ == '__main__':
    initialize_paths()
    initialize_logging()
    app = YouTubeDownloaderGUI()
    app.run()
