
# logger_config.py

import logging
import sys

def setup_logger(level=logging.INFO):
    """
    Configures the root logger for the application.
    """
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(level)  # Set the minimum level of logs to capture

    # Create a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create a handler for console output (stdout)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    
    # Clear existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.addHandler(stream_handler)

    # Optional: To prevent third-party library logs from being too verbose
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return logger
