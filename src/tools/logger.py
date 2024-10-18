import logging
import os
import sys
import uuid
from logging.handlers import QueueHandler, QueueListener, TimedRotatingFileHandler
from queue import Queue

class LoggerSetup:
    class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
        def __init__(self, filename, **kwargs):
            super().__init__(filename, encoding='utf-8', **kwargs)

        def doRollover(self):
            super().doRollover()
        
            baseFilename, ext = os.path.splitext(self.baseFilename)
            unique_id = uuid.uuid4()
            new_filename = f"{baseFilename}_{unique_id}{ext}"
        
            if os.path.exists(self.baseFilename):
                os.remove(self.baseFilename)
        
            try:
                os.symlink(new_filename, self.baseFilename)
            except OSError as e:
                print(f"Symlink creation failed: {e}. Consider running with appropriate privileges.")

    class StreamToLogger:
        def __init__(self, logger, log_level):
            self.logger = logger
            self.log_level = log_level
            self.linebuf = ''

        def write(self, buf):
            for line in buf.rstrip().splitlines():
                self.logger.log(self.log_level, line.rstrip())

        def flush(self):
            pass

    @staticmethod
    def rename_with_unique_id(log_file):
        if os.path.exists(log_file):
            unique_id = uuid.uuid4()
            base_filename, ext = os.path.splitext(log_file)
            new_name = f"{base_filename}_{unique_id}{ext}"

            while os.path.exists(new_name):
                new_name = f"{base_filename}_{unique_id}{ext}"

            os.rename(log_file, new_name)

    @staticmethod
    def initialize_logger(LATEST_LOG_FILE, LOG_DIR):
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)

        LATEST_LOG_FILE = os.path.join(LOG_DIR, LATEST_LOG_FILE)
        LoggerSetup.rename_with_unique_id(LATEST_LOG_FILE)

        logger = logging.getLogger('YouTubeDownloaderLogger')
        logger.setLevel(logging.DEBUG)

        log_queue = Queue(-1)
        queue_handler = QueueHandler(log_queue)
        logger.addHandler(queue_handler)

        file_handler = LoggerSetup.CustomTimedRotatingFileHandler(LATEST_LOG_FILE)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(message)s'))

        listener = QueueListener(log_queue, file_handler)
        listener.start()

        sys.stdout = LoggerSetup.StreamToLogger(logger, logging.INFO)
        sys.stderr = LoggerSetup.StreamToLogger(logger, logging.ERROR)

        try:
            sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
            sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)
        except Exception:
            pass

        return logger

def get_logger():
    return logging.getLogger('YouTubeDownloaderLogger')