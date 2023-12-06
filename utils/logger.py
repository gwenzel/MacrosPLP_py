import logging
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).parent


def create_logger(logname: str):
    # Gets or creates a logger
    logger = logging.getLogger(logname)

    # set log level
    logger.setLevel(logging.INFO)

    # set formatter
    formatter = logging.Formatter(
        '%(asctime)s : %(levelname)s : %(name)s : %(message)s')

    # define file and stream handlers
    root = get_project_root()
    filepath = root / ('log_%s.log' % logname)
    file_handler = logging.FileHandler(filepath, mode='w')
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # add file and handler to logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def add_file_handler(logger, logname: str, path_log: Path):
    # set formatter
    formatter = logging.Formatter(
        '%(asctime)s : %(levelname)s : %(name)s : %(message)s')

    # define file and set format
    formatter = logging.Formatter(
        '%(asctime)s : %(levelname)s : %(name)s : %(message)s')
    filepath = path_log / ('log_%s.log' % logname)
    file_handler = logging.FileHandler(filepath, mode='w')
    file_handler.setFormatter(formatter)

    # add file and handler to logger
    logger.addHandler(file_handler)
