import logging

def setup_logger(name: str, level=logging.INFO, file=None) -> logging.Logger:
    """
    Sets up a logger with the specified name and logging level.

    Args:
        name (str): The name of the logger.
        level: The logging level (default is logging.INFO).
        save_to_file (str, optional): If provided, the logger will also save logs to the specified file.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create console handler and set level
    channel_handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(channel_handler)
    channel_handler.setLevel(level)

    # If file is provided: create file handler and set level 
    if file is not None:
        file_handler = logging.FileHandler(file)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    channel_handler.setFormatter(formatter)

    # Add the handlers to the logger
    if not logger.hasHandlers():
        logger.addHandler(channel_handler)
    
    if 

    return logger