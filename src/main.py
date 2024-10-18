from frontend.gui import YouTubeDownloaderGUI
from tools.logger import LoggerSetup

def initialize_logging():
    LATEST_LOG_FILE = 'latest.log'
    LOG_DIR = 'logs'
    LoggerSetup.initialize_logger(LATEST_LOG_FILE, LOG_DIR)

if __name__ == '__main__':
    initialize_logging()
    app = YouTubeDownloaderGUI()
    app.run()
    