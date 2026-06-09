import logging

def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """
    Sets up a logger with the specified name and logging level.

    Args:
        name (str): The name of the logger.
        level: The logging level (default is logging.INFO).
        

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create console handler and set level
    channel_handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(channel_handler)
    channel_handler.setLevel(level)


    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    channel_handler.setFormatter(formatter)

    # Add the handlers to the logger
    if not logger.hasHandlers():
        logger.addHandler(channel_handler)
    return logger

def add_file_handler(logger: logging.Logger, file: str, level=logging.INFO) -> None:
    """
    Adds a file handler to the existing logger.

    Args:
        logger (logging.Logger): The logger to which the file handler will be added.
        file (str): The path to the log file.
        level: The logging level for the file handler (default is logging.INFO).
    """
    file_handler = logging.FileHandler(file)
    file_handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)