import logging
import os
from sys import platform

import google.cloud.logging
from dotenv import load_dotenv

from Constants import BOT_NAME

load_dotenv()


DEBUG = logging.DEBUG
INFO = logging.INFO
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


def is_server() -> bool:
    dev = os.getenv("DEV")
    if dev is not None and dev == "true":
        return False
    return platform == "linux" or platform == "linux2"


if is_server():
    google_client = google.cloud.logging.Client()
    google_client.setup_logging(log_level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.DEBUG, filename=f'{BOT_NAME}.log')
logger = logging.getLogger(BOT_NAME)


def log(message: str, level: int = INFO):
    logger.log(level, message)
