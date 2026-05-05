import logging
import os

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent adding handlers multiple times if imported multiple times
    if not logger.handlers:
        # Create a formatter for the log file
        file_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s')
        
        # Determine the path for the log file in the project root
        log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cluster.log')
        
        # File handler (writes everything)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        
        # Console handler (for terminal output, preserving visual style)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        # Keep console formatter simple (just the message) so the terminal demo still looks exactly the same
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Also ensure we don't propagate to the root logger to avoid duplicate prints
        logger.propagate = False

    return logger
