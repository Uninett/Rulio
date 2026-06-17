import logging
import os
import sys

from constants import LOGPATH, ERROR_LOGPATH


def add_file_handler(logger: logging.Logger, file: str, level=logging.INFO, mode='a') -> None:
    """
    Adds a file handler to the existing logger.

    Args:
        logger (logging.Logger): The logger to which the file handler will be added.
        file (str): The path to the log file.
        level: The logging level for the file handler (default is logging.INFO).
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file), exist_ok=True)
    abs_file = os.path.abspath(file)

    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and handler.baseFilename == abs_file:
            return


    file_handler = logging.FileHandler(file, mode = mode) 
    file_handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def set_up_root_logger( level=logging.INFO, all_logs_to_file: bool = True, mode: str = 'a') -> logging.Logger:
    """
    Sets up a logger with the specified name and logging level.

    Args:
        name (str): The name of the logger.
        level: The logging level (default is logging.INFO).
        all_logs_to_file (bool): Whether to save all logs to a file (default is True).
        mode (str): The mode in which to open the log file (default is 'a').
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    

    # Create console handler and set level
    if not logger.handlers:
        channel_handler = logging.StreamHandler(stream=sys.stdout)
        logger.addHandler(channel_handler)
        channel_handler.setLevel(level)
        # Create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        channel_handler.setFormatter(formatter)

    if all_logs_to_file:
        if not os.path.exists(LOGPATH):
            os.makedirs(LOGPATH)
        if not os.path.exists(ERROR_LOGPATH):
            os.makedirs(ERROR_LOGPATH)
        #For testing purposes we wipe the all_logs.log file on each run
        with open(LOGPATH / "all_logs.log", mode):
            pass
        add_file_handler(logger, LOGPATH / "all_logs.log", level=level, mode=mode)
        add_file_handler(logger, ERROR_LOGPATH / "all_errors.log", level=logging.ERROR, mode=mode)

    return logger

def set_up_logger(name: str, level=logging.INFO, save_to_file: bool = True, mode: str = 'a') -> logging.Logger:
    """
    Sets up a logger with the specified name and logging level.

    Args:
        name (str): __name__ for the file that is using the logger.
        level: The logging level (default is logging.INFO).
        save_to_file (bool): Whether to save logs to a file (default is True).
        mode (str): The mode in which to open the log file (default is 'a').

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logfile = f"{name}.log"

    if save_to_file:
        add_file_handler(logger, LOGPATH / logfile, mode=mode)
        add_file_handler(logger, ERROR_LOGPATH / logfile, level=logging.ERROR, mode=mode)
    return logger